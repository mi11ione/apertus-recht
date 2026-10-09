"""Render a scenario (slot assignment) into text in one language, and build its question prompts."""
from __future__ import annotations

import re
import string

from .design import Design


class _Group:
    """Exposes a group's case forms as attributes for str.format ({g.nom}, {g.dat}, ...)."""

    def __init__(self, forms: dict):
        self.__dict__.update(forms)


def _cap(s: str) -> str:
    return s[:1].upper() + s[1:] if s else s


def _fill(template: str, ctx: dict) -> str:
    out = []
    for lit, field, spec, conv in string.Formatter().parse(template):
        out.append(lit)
        if field is None:
            continue
        if field.startswith("g."):
            out.append(getattr(ctx["g"], field[2:]))
        elif field in ctx:
            out.append(ctx[field])
        elif field[:1].isupper() and field[:1].lower() + field[1:] in ctx:
            out.append(_cap(ctx[field[:1].lower() + field[1:]]))
        else:
            raise KeyError(f"unresolved placeholder {{{field}}}")
    return "".join(out)


def render(d: Design, lang: str, slots: dict) -> str:
    """Scenario text for a slot assignment {date, group, act, setting, frame, actor, place}."""
    t = d.templates[lang]
    actor = t["actors"][slots["actor"]]
    morph = dict(t["morphology"][actor["gender"]])
    ctx = dict(morph)
    ctx["actor"] = actor["surface"]
    ctx["g"] = _Group(t["groups"][slots["group"]])
    ctx["date"] = t["dates"][slots["date"]]
    ctx["place"] = t["places"][slots["place"]]
    ctx["act"] = _fill(t["acts"][slots["act"]], ctx)
    ctx["setting"] = _fill(t["settings"][slots["setting"]], ctx)
    text = _fill(t["frames"][slots["frame"]], ctx)
    for pat, rep in t.get("rewrite") or []:
        text = re.sub(pat, rep, text)
    return re.sub(r"\s+", " ", text).strip()


RUNGS = ["R0", "R1", "R2", "R3", "R4"]
FRAMINGS = ["conv", "ver"]


def question(d: Design, lang: str, rung: str, framing: str) -> str:
    """The question appended to the scenario text. R0 plain; R1 elements named; R2 + publicity rule and list;
    R3 + closed list; R4 + temporal clause."""
    p = d.prompts[lang]
    if rung == "R0":
        return p["plain"][framing]
    if rung == "R1":
        return p["heads"]["R1"] + p["tails"][framing]
    head = p["heads"]["R2"]
    if rung == "R2":
        return head + p["tails"][framing]
    if rung == "R3":
        return head + p["closed_list"] + p["tails"][framing]
    if rung == "R4":
        return head + p["closed_list"] + p["date_clause"] + p["tails"][framing]
    raise ValueError(rung)


def candidates(d: Design, lang: str, framing: str) -> dict:
    f = d.prompts[lang]["framings"][framing]
    return dict(answer_prefix=f["answer_prefix"], convict=f["convict"], acquit=f["acquit"])
