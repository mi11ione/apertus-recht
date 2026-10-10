"""Any OpenAI-compatible chat endpoint (``LLM_BASE_URL`` / ``LLM_API_KEY`` / ``LLM_NAME``).

Three methods, chosen with ``mode`` (``auto`` probes once and picks the best the endpoint supports):

* ``exact_prefill`` (vLLM): one request per candidate, with the candidate prefilled as the assistant turn
  (``continue_final_message=True, add_generation_prompt=False, prompt_logprobs=1, max_tokens=1``). The candidate's
  log-probability is read token by token from ``prompt_logprobs``. Identical to the local scorers.
* ``top_logprobs``: one request without prefill (``max_tokens=1, logprobs=True, top_logprobs=20``); the first token of
  each candidate is looked up among the top 20. Only for framings without an answer prefix (``conv``); a candidate
  outside the top 20 gets the 20th log-probability as an upper bound and the row is flagged ``censored``.
* ``generate``: plain user message, free generation, decision parsed deterministically (no log-probabilities).

Every response's ``model`` field is compared with the requested model. A mismatch (e.g. a provider silently routing to
another model) raises ``ServedModelMismatch``; such rows are never scored.
"""
from __future__ import annotations

import json
import os
import random
import time
import urllib.error
import urllib.request

from .base import Backend, Score, parse_decision

UA = "statute-twins/1.0 (hackapertus-research/0.1)"


class ServedModelMismatch(RuntimeError):
    pass


def http_transport(base_url: str, api_key: str | None, timeout: int = 180):
    url = base_url.rstrip("/") + "/chat/completions"

    def send(payload: dict) -> dict:
        req = urllib.request.Request(url, data=json.dumps(payload).encode(), method="POST",
                                     headers={"Content-Type": "application/json", "User-Agent": UA,
                                              **({"Authorization": f"Bearer {api_key}"} if api_key else {})})
        for attempt in range(6):
            try:
                with urllib.request.urlopen(req, timeout=timeout) as r:
                    return json.loads(r.read())
            except urllib.error.HTTPError as e:
                if e.code in (429, 500, 502, 503, 504) and attempt < 5:
                    time.sleep(min(60, 2 ** attempt * 3) + random.random())
                    continue
                body = ""
                try:
                    body = e.read().decode("utf-8", "replace")[:300]
                except Exception:
                    pass
                raise RuntimeError(f"HTTP {e.code} from {url}: {body or e.reason}") from None
            except urllib.error.URLError as e:
                # connection refused / DNS failure: the endpoint is not there; retrying will not help
                if isinstance(getattr(e, "reason", None), (ConnectionRefusedError, OSError)) and attempt >= 1:
                    raise RuntimeError(f"cannot reach {url}: {e.reason}") from None
                time.sleep(2)
                continue
            except TimeoutError:
                if attempt < 3:
                    time.sleep(5)
                    continue
                raise
        raise RuntimeError("unreachable")

    return send


def _actual_token_entry(pos: dict) -> dict:
    """vLLM prompt_logprobs position: {token_id: {logprob, rank, decoded_token}} with the actual token, plus the
    rank-1 token when the actual token is not rank 1."""
    vals = list(pos.values())
    if len(vals) == 1:
        return vals[0]
    others = [v for v in vals if v.get("rank") != 1]
    return others[0] if others else vals[0]


def candidate_logprob(prompt_logprobs: list, target: str) -> tuple[float, list[str]]:
    """Sum the log-probabilities of the trailing prompt tokens whose decoded text is exactly ``target``."""
    toks, lp = [], 0.0
    for pos in reversed(prompt_logprobs):
        if pos is None:
            break
        e = _actual_token_entry(pos)
        toks.insert(0, e["decoded_token"])
        lp += e["logprob"]
        joined = "".join(toks)
        if joined == target:
            return lp, toks
        if len(joined) >= len(target):
            break
    raise ValueError(f"trailing prompt tokens {toks!r} do not spell the candidate {target!r}")


def _unreachable(e: Exception) -> bool:
    """The endpoint is not there (connection refused, DNS, bad URL): no scoring method will work, so stop."""
    return isinstance(e, RuntimeError) and str(e).startswith("cannot reach")


class OpenAICompat(Backend):
    name = "openai"

    def __init__(self, base_url: str | None = None, api_key: str | None = None, model: str | None = None,
                 mode: str = "auto", seed: int | None = None, transport=None, label: str | None = None,
                 max_tokens_generate: int = 24, lang_of=None):
        self.base_url = base_url or os.environ.get("LLM_BASE_URL", "")
        self.model = model or os.environ.get("LLM_NAME", "")
        self.send = transport or http_transport(self.base_url, api_key if api_key is not None else os.environ.get("LLM_API_KEY"))
        self.mode = mode
        self.seed = seed
        self.label = label or self.model
        self.max_tokens_generate = max_tokens_generate

    def describe(self) -> dict:
        d = dict(backend=self.name, base_url=self.base_url, model=self.model, mode=self.mode, seed=self.seed)
        if self.mode == "generate":
            d["max_tokens"] = self.max_tokens_generate     # generation length changes the answer, so it is part of the key
        return d

    # -------------------------------------------------------------------------------------------------------- utils
    def _check(self, resp: dict) -> tuple[str | None, str | None]:
        served = resp.get("model")
        if served and self.model and served != self.model:
            raise ServedModelMismatch(f"requested {self.model}, served {served}")
        return served, resp.get("system_fingerprint")

    def _base(self, **kw) -> dict:
        p = dict(model=self.model, temperature=0.0, **kw)
        if self.seed is not None:
            p["seed"] = self.seed
        return p

    def probe(self, row: dict) -> str:
        """Pick the best supported method for this endpoint."""
        if self.mode != "auto":
            return self.mode
        try:
            self._exact(row)
            self.mode = "exact_prefill"
            return self.mode
        except ServedModelMismatch:
            raise
        except Exception as e:
            if _unreachable(e):
                raise
        try:
            self._top(dict(row, answer_prefix=""))
            self.mode = "top_logprobs"
        except ServedModelMismatch:
            raise
        except Exception as e:
            if _unreachable(e):
                raise
            self.mode = "generate"
        print(f"[auto] endpoint does not support exact prefill scoring; using {self.mode}", flush=True)
        return self.mode

    # ------------------------------------------------------------------------------------------------------ methods
    def _exact(self, row: dict) -> Score:
        out, served, fp = {}, None, None
        for side in ("convict", "acquit"):
            cand = row[side]
            msgs = [{"role": "user", "content": row["user"]}, {"role": "assistant", "content": row["answer_prefix"] + cand}]
            resp = self.send(self._base(messages=msgs, max_tokens=1, continue_final_message=True,
                                        add_generation_prompt=False, prompt_logprobs=1))
            served, fp = self._check(resp)
            pl = resp.get("prompt_logprobs") or resp["choices"][0].get("prompt_logprobs")
            if not pl:
                raise ValueError("endpoint returned no prompt_logprobs")
            lp, toks = candidate_logprob(pl, cand)
            out[side] = dict(lp=lp, toks=toks)
        return Score(out["convict"]["lp"], out["acquit"]["lp"], "exact_prefill", served, fp,
                     extra=dict(tokens={k: v["toks"] for k, v in out.items()}))

    def _top(self, row: dict) -> Score:
        if row["answer_prefix"]:
            raise ValueError("top_logprobs mode cannot score a framing with an answer prefix")
        resp = self.send(self._base(messages=[{"role": "user", "content": row["user"]}], max_tokens=1,
                                    logprobs=True, top_logprobs=20))
        served, fp = self._check(resp)
        lp = (resp["choices"][0].get("logprobs") or {}).get("content")
        if not lp or not lp[0].get("top_logprobs"):
            raise ValueError("endpoint returned no top_logprobs")
        top = lp[0]["top_logprobs"]
        floor = min(t["logprob"] for t in top)
        res, censored = {}, []
        for side in ("convict", "acquit"):
            cand = row[side].strip()
            hits = [t["logprob"] for t in top if t["token"].strip() and cand.startswith(t["token"].strip())]
            if hits:
                res[side] = max(hits)
            else:
                res[side] = floor
                censored.append(side)
        return Score(res["convict"], res["acquit"], "top_logprobs", served, fp, extra=dict(censored=censored))

    def _generate(self, row: dict) -> Score:
        resp = self.send(self._base(messages=[{"role": "user", "content": row["user"]}], max_tokens=self.max_tokens_generate))
        served, fp = self._check(resp)
        text = resp["choices"][0]["message"].get("content") or ""
        return Score(None, None, "generate", served, fp, text=text,
                     decision=parse_decision(row["lang"], row["framing"], text))

    def score(self, row: dict) -> Score:
        mode = self.mode if self.mode != "auto" else self.probe(row)
        if mode == "exact_prefill":
            return self._exact(row)
        if mode == "top_logprobs":
            return self._top(row) if not row["answer_prefix"] else self._generate(row)
        return self._generate(row)


def gateway_transport(tag: str, cap_usd: float, gw_path: str | None = None):
    """Development transport through the team's budget gateway (cost caps, ledger, content cache). Not used by
    `make run`; judges use http_transport with their own LLM_BASE_URL."""
    import importlib.util
    import sys
    path = gw_path or os.environ.get("STATUTE_TWINS_GATEWAY")
    if not path:
        raise SystemExit("--backend gateway needs STATUTE_TWINS_GATEWAY=/path/to/gw.py (the team's cost-capped gateway)")
    spec = importlib.util.spec_from_file_location("gw", path)
    gw = importlib.util.module_from_spec(spec)
    sys.modules["gw"] = gw
    spec.loader.exec_module(gw)

    def send(payload: dict) -> dict:
        p = dict(payload)
        msgs = p.pop("messages")
        model = p.pop("model")
        max_tokens = p.pop("max_tokens")
        temperature = p.pop("temperature", 0.0)
        for attempt in range(6):
            try:
                choice, meta = gw.chat(msgs, model=model, max_tokens=max_tokens, temperature=temperature, tag=tag,
                                       tag_cap_usd=cap_usd, full=True, **p)
                break
            except Exception as e:
                if "BUDGET" in str(e) or attempt == 5:
                    raise
                time.sleep(20 * (attempt + 1) + random.random() * 10)
        resp = dict(meta.get("resp") or {})
        resp["choices"] = [choice]
        resp["_gateway"] = dict(cached=meta.get("cached"), usd=meta.get("usd"))
        return resp

    return send
