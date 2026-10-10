"""Render a scenario (slot assignment) into text in one language, and build its question prompts."""
from __future__ import annotations

import re
import string

from .design import Design, section


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
    """Scenario text for a slot assignment. Non-frame slots are resolved in design.render.order (default: declaration
    order); their surfaces may use earlier slots, the actor's morphology and case-form aliases; the frame comes last."""
    t = d.templates[lang]
    spec = d.raw.get("render") or {}
    aliases = spec.get("aliases") or {}
    ctx: dict = {}
    if "actor" in slots and "morphology" in t:
        ctx.update(t["morphology"][t["actors"][slots["actor"]]["gender"]])
    for slot in spec.get("order") or [s for s in d.slots if s != "frame"]:
        surf = t[section(slot, d)][slots[slot]]
        name = aliases.get(slot, slot)
        if isinstance(surf, dict):
            ctx[name] = surf["surface"] if "surface" in surf else _Group(surf)
        else:
            ctx[name] = _fill(surf, ctx)
    text = _fill(t["frames"][slots["frame"]], ctx)
    for pat, rep in t.get("rewrite") or []:
        text = re.sub(pat, rep, text)
    return re.sub(r"\s+", " ", text).strip()


RUNGS = ["R0", "R1", "R2", "R3", "R4", "R5"]
FRAMINGS = ["conv", "ver"]


def rung_names(d: Design, lang: str) -> list[str]:
    spec = d.prompts[lang].get("rungs")
    return list(spec) if spec else list(RUNGS)


def question(d: Design, lang: str, rung: str, framing: str) -> str:
    """The question appended to the scenario text. If prompts/<lang>.yaml has `rungs: {R0: [parts...]}`, the rung is the
    concatenation of those parts, where `plain` and `tail` mean plain[framing] and tails[framing] and any other name is
    a top-level string of the prompts file. Otherwise the Art. 261bis ladder: R0 plain; R1 elements named; R2 + publicity
    rule and list; R3 + closed list; R4 + temporal clause."""
    p = d.prompts[lang]
    if p.get("rungs"):
        parts = []
        for k in p["rungs"][rung]:
            parts.append(p["plain"][framing] if k == "plain" else p["tails"][framing] if k == "tail" else p[k])
        return "".join(parts)
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
    if rung == "R5":
        lt = p["law_text"]
        return lt["intro"] + law_block(d, lang) + lt["question"] + p["tails"][framing]
    raise ValueError(rung)


def law_block(d: Design, lang: str) -> str:
    """The pinned legal texts, verbatim, as a retrieval pipeline would paste them (prompts/<lang>.yaml: law_text)."""
    import json
    parts = []
    for it in d.prompts[lang]["law_text"]["items"]:
        rec = json.loads(d.statute.source_file(it["source"], lang).read_text(encoding="utf-8"))
        if "regeste" in rec:
            parts.append(f"{it['label']}: {rec['regeste'][lang]}")
            continue
        paras = rec["paragraphs"]
        body = "\n".join(f"{k} {t}" for k, t in enumerate(paras, 1)) if it.get("numbered") else "\n".join(paras)
        notes = rec.get("notes") or []
        mark = "¹" if it.get("footnotes") and notes else ""
        block = f"{it['label']}{mark}\n{body}"
        if mark:
            block += f"\n¹ {notes[0]}"
        parts.append(block)
    return "\n\n".join(parts)


def candidates(d: Design, lang: str, framing: str) -> dict:
    f = d.prompts[lang]["framings"][framing]
    return dict(answer_prefix=f["answer_prefix"], convict=f["convict"], acquit=f["acquit"])
