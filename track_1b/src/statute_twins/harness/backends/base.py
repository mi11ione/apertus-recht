"""Backend interface and the forced-choice protocol shared by all backends.

A backend scores one prompt row (see generator.build.build_prompts): it returns the log-probability of the convict
continuation and of the acquit continuation, each summed over all its tokens, given

    chat(user = row["user"]) + assistant prefix row["answer_prefix"]

which is exactly the protocol of the spike scorers (stage9.py / llscore.cpp / live.py). ``lo_conv = lp_convict -
lp_acquit``; a decision is "convict" iff lo_conv > 0.

Backends that cannot return log-probabilities (``generate``) instead return the generated text and a parsed decision.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field


@dataclass
class Score:
    lp_convict: float | None
    lp_acquit: float | None
    method: str                         # exact_prefill | top_logprobs | llamacpp | generate | replay
    served_model: str | None = None
    fingerprint: str | None = None
    text: str | None = None             # generate mode
    decision: str | None = None         # convict | acquit | unparsed (generate mode)
    extra: dict = field(default_factory=dict)

    @property
    def lo_conv(self) -> float | None:
        if self.lp_convict is None or self.lp_acquit is None:
            return None
        return self.lp_convict - self.lp_acquit

    def decided(self) -> str | None:
        if self.lo_conv is not None:
            return "convict" if self.lo_conv > 0 else "acquit"
        return self.decision


class Backend:
    name = "base"

    def describe(self) -> dict:
        """Everything that identifies the build being scored (goes into the cache key and every response row)."""
        raise NotImplementedError

    def score(self, row: dict) -> Score:
        raise NotImplementedError


def request_key(backend_desc: dict, row: dict, params: dict) -> str:
    """Cache key: sha256 over the backend identity, the exact user message, prefix, candidates and parameters."""
    payload = dict(backend=backend_desc, user=row["user"], answer_prefix=row["answer_prefix"],
                   convict=row["convict"], acquit=row["acquit"], params=params)
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


# ------------------------------------------------------------------ generate-and-parse decision parser (DE/FR/IT)

_STRIP = re.compile(r"[*«»\"“”„'`]")
PARSE = {
    "de": dict(yes=r"ja", no=r"nein", guilty=r"schuldig", not_guilty=r"nicht\s+schuldig", head=r"(urteil|das urteil lautet)"),
    "fr": dict(yes=r"oui", no=r"non", guilty=r"coupable", not_guilty=r"non\s+coupable", head=r"(jugement|verdict|le jugement est)"),
    "it": dict(yes=r"s[iì]", no=r"no", guilty=r"colpevole", not_guilty=r"non\s+colpevole", head=r"(sentenza|verdetto|la sentenza è)"),
}


def parse_decision(lang: str, framing: str, text: str) -> str:
    """Deterministic parse of a free-text answer into convict / acquit / unparsed."""
    p = PARSE[lang]
    s = _STRIP.sub("", (text or "").strip().lower())
    if framing == "conv":
        m = re.match(rf"^\W*({p['yes']}|{p['no']})\b", s)
        if m:
            return "convict" if re.fullmatch(p["yes"], m.group(1)) else "acquit"
        has_y, has_n = re.search(rf"\b{p['yes']}\b", s), re.search(rf"\b{p['no']}\b", s)
        if has_n and not has_y:
            return "acquit"
        if has_y and not has_n:
            return "convict"
        return "unparsed"
    s = re.sub(rf"^\W*{p['head']}\s*:?\s*", "", s)
    if re.match(rf"^\W*{p['not_guilty']}", s):
        return "acquit"
    if re.match(rf"^\W*{p['guilty']}", s):
        return "convict"
    if re.search(p["not_guilty"], s):
        return "acquit"
    if re.search(rf"\b{p['guilty']}\b", s):
        return "convict"
    return "unparsed"
