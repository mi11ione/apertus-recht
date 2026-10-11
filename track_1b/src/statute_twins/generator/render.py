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


RUNGS = ["R0", "R1", "R2", "R3", "R4", "R5", "R6"]
FRAMINGS = ["conv", "ver"]
# A13 (exploratory controls, written to eval/prompts_ctrl_<part>.jsonl so the released prompt files stay unchanged):
# R5a = R3's question block after the verbatim law; R5b = R5 without the Regeste's closing example (consid. 6, a
# closed meeting where publicity was affirmed); R5c = R5 with R1's element-check instruction after the law instead of
# the "Frage:" label (R6 puts it before the law); R5d = R5 with Art. 1 StGB (no penalty without law) before Art. 2.
# A15: R5e = R5a with legal text of the same length that does not bear on the case instead of the law (German only).
# Framing `rev` asks for an acquittal ("yes" = acquit).
CONTROL_RUNGS = ["R5a", "R5b", "R5c", "R5d", "R5e"]


def rung_names(d: Design, lang: str) -> list[str]:
    spec = d.prompts[lang].get("rungs")
    return list(spec) if spec else list(RUNGS)


def question(d: Design, lang: str, rung: str, framing: str, family: str | None = None) -> str:
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
        return lt["intro"] + law_block(d, lang, family=family) + lt["question"] + p["tails"][framing]
    if rung == "R6":
        # control for R5: the same verbatim law, preceded by the element-check instruction of R1 (A10)
        lt = p["law_text"]
        return p["heads"]["R1"] + lt["intro"] + law_block(d, lang, family=family) + lt["question"] + p["tails"][framing]
    if rung == "R5a":
        return p["law_text"]["intro"] + law_block(d, lang) + head + p["closed_list"] + p["tails"][framing]
    if rung == "R5b":
        lt = p["law_text"]
        return lt["intro"] + law_block(d, lang, exemplar=False) + lt["question"] + p["tails"][framing]
    if rung == "R5c":
        return p["law_text"]["intro"] + law_block(d, lang) + p["heads"]["R1"] + p["tails"][framing]
    if rung == "R5d":
        lt = p["law_text"]
        return lt["intro"] + law_block(d, lang, art1=True) + lt["question"] + p["tails"][framing]
    if rung == "R5e":
        return p["law_text"]["intro"] + _length_control(d, lang) + head + p["closed_list"] + p["tails"][framing]
    raise ValueError(rung)


def control_rungs(d: Design, lang: str) -> list[str]:
    """The A13/A15 control rungs this language defines (R5d needs Art. 1, R5e the length-control texts)."""
    lt = d.prompts[lang].get("law_text") or {}
    return [r for r in CONTROL_RUNGS if (r != "R5d" or "art1_control" in lt) and (r != "R5e" or "length_control" in lt)]


def _length_control(d: Design, lang: str) -> str:
    """Pinned legal texts of about the law block's length that do not bear on the case (control R5e, A15)."""
    import hashlib
    import json
    parts = []
    for spec in d.prompts[lang]["law_text"]["length_control"]:
        rec = json.loads((d.statute.path.parent / spec["file"]).read_text(encoding="utf-8"))
        text = "\n".join(rec["paragraphs"])
        if hashlib.sha256(text.encode()).hexdigest() != spec["text_sha256"]:
            raise ValueError(f"{spec['file']}: text does not match its pinned sha256")
        parts.append(f"{spec['label']}\n{text}")
    return "\n\n".join(parts)


def drop_exemplar(regeste: str) -> str:
    """The Regeste without its closing sentence (the decided case: publicity affirmed, consid. 6)."""
    head, _, last = regeste.rstrip().rpartition("). ")
    if not head or "6)" not in last:
        raise ValueError("Regeste does not end with the consid. 6 example")
    return head + ")."


def law_block(d: Design, lang: str, exemplar: bool = True, art1: bool = False, family: str | None = None) -> str:
    """The pinned legal texts, verbatim, as a retrieval pipeline would paste them (prompts/<lang>.yaml: law_text).
    exemplar=False drops the Regeste's closing example sentence (control R5b, A13); art1=True puts Art. 1 StGB
    before Art. 2 (control R5d, A13)."""
    import json
    parts = []
    src_lang = lang.split("_")[0]          # a register variant (de_lay) uses the official texts of its language
    # A18: a family may add the authority that decides it (prompts/<lang>.yaml law_text.family_items), so the
    # verbatim-law rungs give the DIGNITY items BGE 131 IV 23 as well; every other item's law block is unchanged
    extra = ((d.prompts[lang]["law_text"].get("family_items") or {}).get(family) or []) if family else []
    for it in list(d.prompts[lang]["law_text"]["items"]) + list(extra):
        if art1 and it["source"] == "fedlex_art2":
            parts.append(_art1_control(d, lang))
        rec = json.loads(d.statute.source_file(it["source"], src_lang).read_text(encoding="utf-8"))
        if "regeste" in rec:
            reg = rec["regeste"][src_lang]
            parts.append(f"{it['label']}: {reg if exemplar else drop_exemplar(reg)}")
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


def _art1_control(d: Design, lang: str) -> str:
    """Art. 1 StGB for control R5d: pinned in prompts/<lang>.yaml (law_text.art1_control), outside statute.yaml, because
    no gold element cites it and the statute file's hash is recorded in every item."""
    import hashlib
    import json
    spec = d.prompts[lang]["law_text"]["art1_control"]
    rec = json.loads((d.statute.path.parent / spec["file"]).read_text(encoding="utf-8"))
    text = "\n".join(rec["paragraphs"])
    if hashlib.sha256(text.encode()).hexdigest() != spec["text_sha256"]:
        raise ValueError(f"{spec['file']}: text does not match its pinned sha256")
    return f"{spec['label']}\n{text}"


def candidates(d: Design, lang: str, framing: str) -> dict:
    f = d.prompts[lang]["framings"][framing]
    return dict(answer_prefix=f["answer_prefix"], convict=f["convict"], acquit=f["acquit"])
