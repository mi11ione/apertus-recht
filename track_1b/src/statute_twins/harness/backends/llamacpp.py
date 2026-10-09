"""In-process llama.cpp (llama-cpp-python) forced choice over a local GGUF, CPU by default.

Same protocol as the spike scorer ``llscore.cpp``: render the GGUF's own chat template (enable_thinking=False,
add_generation_prompt=True), append the answer prefix, decode the prompt once, then teacher-force each candidate and sum
its token log-probabilities (log-softmax in float64), rewinding the KV cache to the prompt after each candidate.
"""
from __future__ import annotations

import hashlib
import math
import os
from pathlib import Path

from .base import Backend, Score


def sha256_file(path: str | Path, chunk: int = 1 << 24) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def log_softmax_at(logits, token_id: int) -> float:
    """log-softmax of one entry, in float64 (numpy if available)."""
    try:
        import numpy as np
        x = np.asarray(logits, dtype=np.float64)
        m = x.max()
        return float(x[token_id] - m - np.log(np.exp(x - m).sum()))
    except ImportError:
        m = max(logits)
        z = math.fsum(math.exp(x - m) for x in logits)
        return float(logits[token_id] - m - math.log(z))


class LlamaCpp(Backend):
    name = "llamacpp"

    def __init__(self, model_path: str, n_ctx: int = 2048, n_threads: int | None = None, expect_sha256: str | None = None,
                 label: str | None = None, llama=None):
        self.model_path = str(model_path)
        self.n_threads = n_threads or int(os.environ.get("STATUTE_TWINS_THREADS", 0)) or (os.cpu_count() or 4)
        self.sha256 = expect_sha256
        self.label = label or Path(model_path).name
        if llama is None:
            from llama_cpp import Llama
            llama = Llama(model_path=self.model_path, n_ctx=n_ctx, n_threads=self.n_threads, logits_all=False,
                          verbose=False, n_gpu_layers=0)
        self.llm = llama
        self._kv: list[int] = []          # tokens currently in the KV cache (prompt part), for prefix reuse
        meta = getattr(self.llm, "metadata", {}) or {}
        self.template = meta.get("tokenizer.chat_template")
        self.bos = self._piece(int(meta.get("tokenizer.ggml.bos_token_id", 1)))
        self.eos = self._piece(int(meta.get("tokenizer.ggml.eos_token_id", 2)))

    def _piece(self, tid: int) -> str:
        try:
            return self.llm.detokenize([tid], special=True).decode("utf-8", "replace")
        except TypeError:
            return self.llm.detokenize([tid]).decode("utf-8", "replace")

    def describe(self) -> dict:
        import importlib.metadata as md
        try:
            ver = md.version("llama_cpp_python")
        except Exception:
            ver = "unknown"
        return dict(backend=self.name, model=self.label, sha256=self.sha256, llama_cpp_python=ver, threads=self.n_threads)

    def render(self, user: str) -> str:
        if not self.template:
            raise RuntimeError("GGUF has no tokenizer.chat_template")
        import jinja2
        env = jinja2.Environment(loader=jinja2.BaseLoader(), trim_blocks=False, lstrip_blocks=False)
        env.globals["raise_exception"] = lambda m: (_ for _ in ()).throw(jinja2.TemplateError(m))
        return env.from_string(self.template).render(messages=[{"role": "user", "content": user}],
                                                     add_generation_prompt=True, enable_thinking=False,
                                                     bos_token=self.bos, eos_token=self.eos)

    def last_logits(self):
        """Logits after the last evaluated token, read from the context. (llama-cpp-python >= 0.3 no longer copies
        logits into `Llama.scores` unless logits_all=True; reading `scores` there yields zeros.)"""
        import numpy as np
        n_vocab = self.llm.n_vocab()
        ptr = self.llm._ctx.get_logits()
        return np.ctypeslib.as_array(ptr, shape=(n_vocab,)).astype(np.float64)

    def tok(self, s: str) -> list[int]:
        return self.llm.tokenize(s.encode("utf-8"), add_bos=False, special=True)

    def score(self, row: dict) -> Score:
        prompt = self.render(row["user"]) + row["answer_prefix"]
        pre = self.tok(prompt)
        conts = {}
        for side in ("convict", "acquit"):
            full = self.tok(prompt + row[side])
            if full[:len(pre)] != pre:
                raise ValueError(f"tokenisation of prompt+{side!r} does not extend the prompt tokens")
            conts[side] = full[len(pre):]
        # reuse the KV cache for the longest common prefix with the previous prompt (same system prompt and, for
        # consecutive rungs/framings of one item, the same scenario text); at least one token is evaluated so that
        # the logits at the last prompt position are fresh
        lcp = 0
        for x, y in zip(self._kv, pre):
            if x != y:
                break
            lcp += 1
        lcp = min(lcp, len(pre) - 1)
        self.llm.n_tokens = lcp
        self.llm.eval(pre[lcp:])
        self._kv = list(pre)
        n = self.llm.n_tokens
        first = self.last_logits()
        out = {}
        for side, ids in conts.items():
            lp = log_softmax_at(first, ids[0])
            for j in range(1, len(ids)):
                self.llm.n_tokens = n + j - 1
                self.llm.eval([ids[j - 1]])
                lp += log_softmax_at(self.last_logits(), ids[j])
            self.llm.n_tokens = n          # rewind: the next eval drops KV entries beyond n
            out[side] = lp
        return Score(out["convict"], out["acquit"], "llamacpp", self.label, self.sha256,
                     extra=dict(ntok={k: len(v) for k, v in conts.items()}, prompt_tokens=len(pre), reused=lcp))
