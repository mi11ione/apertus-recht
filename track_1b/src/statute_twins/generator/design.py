"""Load a statute's design (slots, families) and its per-language templates, prompts and reference answers."""
from __future__ import annotations

import hashlib
import string
from dataclasses import dataclass
from pathlib import Path

import yaml

from .. import statute as statute_mod

DEFAULT_SECTIONS = {"frame": "frames", "actor": "actors", "place": "places", "date": "dates", "group": "groups",
                    "act": "acts", "setting": "settings"}


def section(slot: str, d: "Design | None" = None) -> str:
    """Name of the template section holding a slot's surfaces: design.yaml `sections` override, else the default
    plural of the slot name."""
    if d is not None and slot in (d.raw.get("sections") or {}):
        return d.raw["sections"][slot]
    return DEFAULT_SECTIONS.get(slot, slot + "s")


def sample_order(d: "Design") -> list[str]:
    return list(d.raw.get("sample_order") or d.slots)


class DesignError(ValueError):
    pass


@dataclass
class Design:
    root: Path
    statute: statute_mod.Statute
    raw: dict
    slots: dict            # slot -> {value_id: attrs}
    families: dict
    templates: dict        # lang -> templates yaml
    prompts: dict          # lang -> prompts yaml
    answers: dict          # lang -> answers yaml

    @property
    def langs(self) -> list[str]:
        return sorted(self.templates)

    @property
    def seed(self) -> int:
        return int(self.raw["generator_seed"])

    def files_sha256(self) -> dict:
        """sha256 of every input file; recorded in each item's provenance."""
        out = {}
        for p in sorted(self.root.rglob("*.yaml")):
            out[str(p.relative_to(self.root))] = hashlib.sha256(p.read_bytes()).hexdigest()
        return out

    def slot_facts(self, slot: str, value: str) -> dict:
        return dict(self.slots[slot][value].get("facts") or {})


def _yaml(p: Path) -> dict:
    return yaml.safe_load(p.read_text(encoding="utf-8"))


def _norm_values(v) -> dict:
    if isinstance(v, list):
        return {k: {} for k in v}
    return {k: dict(a or {}) for k, a in v.items()}


def load(root: str | Path, langs: list[str] | None = None) -> Design:
    root = Path(root)
    st = statute_mod.load(root / "statute.yaml")
    raw = _yaml(root / "design.yaml")
    slots = {s: _norm_values(d["values"]) for s, d in raw["slots"].items()}
    for s, vals in slots.items():
        for vid, a in vals.items():
            for k, v in (a.get("facts") or {}).items():
                a["facts"][k] = str(v)
    templates, prompts, answers = {}, {}, {}
    for p in sorted((root / "templates").glob("*.yaml")):
        lang = p.stem
        if langs and lang not in langs:
            continue
        templates[lang] = _yaml(p)
        prompts[lang] = _yaml(root / "prompts" / f"{lang}.yaml")
        answers[lang] = _yaml(root / "answers" / f"{lang}.yaml")
    d = Design(root=root, statute=st, raw=raw, slots=slots, families=raw["families"], templates=templates,
               prompts=prompts, answers=answers)
    problems = validate(d)
    if problems:
        raise DesignError("; ".join(problems[:20]) + (f" (+{len(problems) - 20} more)" if len(problems) > 20 else ""))
    return d




def placeholders(s: str) -> set[str]:
    return {f for _, f, _, _ in string.Formatter().parse(s) if f}


def validate(d: Design) -> list[str]:
    """Static checks: facts name real elements and values; every slot value has a surface in every language; every
    placeholder in every surface is resolvable; references (synonym_of, placebo_of) point at existing values."""
    problems = []
    st = d.statute
    for slot, vals in d.slots.items():
        for vid, a in vals.items():
            for el, v in (a.get("facts") or {}).items():
                try:
                    e = st.element(el)
                except KeyError:
                    problems.append(f"{slot}.{vid}: fact for unknown element {el}")
                    continue
                if e.kind in ("enum", "covered_set") and v not in e.values:
                    problems.append(f"{slot}.{vid}: {el}={v} is not a value of the element")
            for ref in ("synonym_of", "placebo_of"):
                if a.get(ref) and a[ref] not in vals:
                    problems.append(f"{slot}.{vid}: {ref} {a[ref]} does not exist")
    for fam, spec in (d.families or {}).items():
        for slot in (spec.get("base") or {}):
            if slot not in d.slots:
                problems.append(f"family {fam}: base filter names unknown slot {slot!r} (slots: {sorted(d.slots)})")
        for vs in spec.get("variants") or []:
            if vs.get("slot") not in d.slots:
                problems.append(f"family {fam}: variant changes unknown slot {vs.get('slot')!r} (slots: {sorted(d.slots)})")
    for slot in d.raw.get("sample_order") or []:
        if slot not in d.slots:
            problems.append(f"sample_order names unknown slot {slot!r}")
    elements_covered = {k for vals in d.slots.values() for a in vals.values() for k in (a.get("facts") or {})}
    missing = set(st.element_ids) - elements_covered
    if missing:
        problems.append(f"no slot carries a fact for elements {sorted(missing)}")
    # A18: a value with `only_families` is rendered only where one of those families is rendered (a family may list
    # `langs`); its surface may use group forms that only the groups that family draws provide (rendering fails loudly
    # if a drawn group lacks one)
    def restricted(slot, vid):
        return bool(d.slots[slot][vid].get("only_families"))

    def rendered_in(slot, vid, lang):
        only = d.slots[slot][vid].get("only_families")
        return not only or any(not (d.families.get(f) or {}).get("langs") or lang in d.families[f]["langs"] for f in only)

    for lang, t in d.templates.items():
        morph_keys = set()
        for g in t.get("morphology", {}).values():
            morph_keys |= set(g)
        aliases = (d.raw.get("render") or {}).get("aliases") or {}
        names = {aliases.get(s, s) for s in d.slots if s != "frame"}
        allowed = names | {n[:1].upper() + n[1:] for n in names}
        allowed |= morph_keys | {k[:1].upper() + k[1:] for k in morph_keys}
        for slot, alias in aliases.items():
            forms_used = {ph[len(alias) + 1:] for s_ in d.slots for vid_, x in (t.get(section(s_, d)) or {}).items()
                          if not (vid_ in d.slots[s_] and restricted(s_, vid_))
                          for ph in placeholders(str(x)) if ph.startswith(alias + ".")}
            restricted_forms = {ph[len(alias) + 1:] for s_ in d.slots for vid_, x in (t.get(section(s_, d)) or {}).items()
                                if vid_ in d.slots[s_] and restricted(s_, vid_)
                                for ph in placeholders(str(x)) if ph.startswith(alias + ".")}
            allowed |= {f"{alias}.{f}" for f in forms_used | restricted_forms}
            for gid, forms in (t.get(section(slot, d)) or {}).items():
                missing_forms = forms_used - set(forms)
                if missing_forms:
                    problems.append(f"{lang}: {slot} {gid} lacks case forms {sorted(missing_forms)}")
        for slot in d.slots:
            key = section(slot, d)
            surf = t.get(key) or {}
            for vid in d.slots[slot]:
                if vid not in surf and rendered_in(slot, vid, lang):
                    problems.append(f"{lang}: no surface for {slot}.{vid}")
            for vid, s in surf.items():
                if vid not in d.slots[slot]:
                    problems.append(f"{lang}: surface for unknown {slot}.{vid}")
                texts = [s] if isinstance(s, str) else ([s["surface"]] if "surface" in s else list(s.values()))
                for x in texts:
                    for ph in placeholders(str(x)):
                        if ph not in allowed:
                            problems.append(f"{lang}: {slot}.{vid}: unknown placeholder {{{ph}}}")
        for aid, a in (t.get("actors") or {}).items():
            if a.get("gender") not in t.get("morphology", {}):
                problems.append(f"{lang}: actor {aid} has no morphology for gender {a.get('gender')}")
    return problems
