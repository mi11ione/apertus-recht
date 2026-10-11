"""Build twin groups from a design and render them into evaluation items.

Determinism: one ``random.Random(seed)``; families in YAML order; slot values chosen by least use so far (globally, then
within the family), ties broken by the seeded RNG. Same design files + same seed -> byte-identical output.

Invariants enforced here (the generator refuses to emit a set that breaks them):
  * every variant differs from its base in exactly one slot;
  * the elements whose status changes between base and variant are elements that read the changed slot's facts;
  * the role the gold engine assigns (true_flip / placebo / contested) equals the family's declared ``expect``;
  * month-precision dates give the same verdict on the first and last day of the month;
  * no two scenarios share the same slot assignment.
"""
from __future__ import annotations

import calendar
import datetime as dt
import random
from dataclasses import dataclass, field

from ..gold.engine import Gold, gold, element_status
from .design import Design, DesignError, sample_order
from .render import FRAMINGS, candidates, question, render, rung_names

GENERATOR_VERSION = "1.0.0"


class BuildError(RuntimeError):
    pass


@dataclass
class Scenario:
    group_id: str
    family: str
    k: int                      # 0 = base, 1.. = variants
    slots: dict
    facts: dict
    gold: Gold
    role: str                   # base | true_flip | placebo | contested
    changed_slot: str | None = None
    trap: str | None = None
    meta: dict = field(default_factory=dict)


def _attr(d: Design, slot: str, vid: str, attr: str):
    a = d.slots[slot][vid]
    facts = a.get("facts") or {}
    return facts[attr] if attr in facts else a.get(attr)


def _family_ok(d: Design, slot: str, vid: str, fam: str) -> bool:
    """A slot value with `only_families` is drawn only by those families (A18), so adding one leaves the draws of every
    other family unchanged."""
    only = d.slots[slot][vid].get("only_families")
    return not only or fam in only


def _excluded(d: Design, slot: str, vid: str, slots: dict) -> bool:
    """A slot value with `not_with: {other_slot: [values]}` is never combined with those values of an already drawn
    slot (A22: a criticism whose wording echoes a stereotype about one group is not drawn for that group)."""
    return any(slots.get(s) in vs for s, vs in (d.slots[slot][vid].get("not_with") or {}).items())


def matches(d: Design, slot: str, vid: str, flt: dict, base: dict | None) -> bool:
    a = d.slots[slot][vid]
    for key, want in (flt or {}).items():
        if key == "tags":
            if not set(want) <= set(a.get("tags", [])):
                return False
        elif key == "not_tags":
            if set(want) & set(a.get("tags", [])):
                return False
        elif key == "match":
            if any(_attr(d, slot, vid, x) != _attr(d, slot, base[slot], x) for x in want):
                return False
        elif key == "differ":
            if any(_attr(d, slot, vid, x) == _attr(d, slot, base[slot], x) for x in want):
                return False
        elif want is None:
            if a.get(key) is not None:
                return False
        elif want == "base":
            if base is None or a.get(key) != base[slot]:
                return False
        elif _attr(d, slot, vid, key) != want:
            return False
    return True


def facts_of(d: Design, slots: dict) -> dict:
    f = {}
    for s, v in slots.items():
        f.update(d.slot_facts(s, v))
    return f


def readers(d: Design, slot: str, value: str) -> set[str]:
    """Elements that read the facts carried by a slot value (directly, or through depends_on)."""
    keys = set(d.slot_facts(slot, value))
    out = set(keys)
    for e in d.statute.elements:
        if e.depends_on in keys:
            out.add(e.id)
    return out


def _month_invariant(d: Design, slots: dict, g: Gold) -> None:
    for s, v in slots.items():
        a = d.slots[s][v]
        if a.get("precision") != "month":
            continue
        for k in a.get("facts", {}):
            day = dt.date.fromisoformat(a["facts"][k])
            last = calendar.monthrange(day.year, day.month)[1]
            for probe in (day.replace(day=1), day.replace(day=last)):
                f = facts_of(d, slots)
                f[k] = probe.isoformat()
                if gold(d.statute, f).verdict != g.verdict:
                    raise BuildError(f"{s}.{v}: verdict depends on the day within the month ({probe})")


def _satisfiable(d: Design, spec: dict, slot: str, v: str) -> bool:
    """Can every variant that changes `slot` be built from base value `v`? (enough distinct candidates)"""
    vs_here = [vs for vs in spec["variants"] if vs["slot"] == slot]
    if not vs_here:
        return True
    pool = set()
    for vs in vs_here:
        c = {u for u in d.slots[slot] if u != v and matches(d, slot, u, vs.get("filter"), {slot: v})}
        if not c:
            return False
        pool |= c
    return len(pool) >= len(vs_here)


class _Picker:
    def __init__(self, rng: random.Random):
        self.rng = rng
        self.use_global: dict = {}
        self.use_family: dict = {}

    def pick(self, family: str, slot: str, cands: list[str], excluded=lambda v: False) -> str:
        # `excluded` values still take part in the seeded tie-break (one draw per candidate), so excluding a value
        # changes only the pick it would have won, not the random draws of any later pick
        keyed = sorted(cands, key=lambda v: (self.use_global.get((slot, v), 0), self.use_family.get((family, slot, v), 0),
                                             self.rng.random()))
        keyed = [v for v in keyed if not excluded(v)]
        if not keyed:
            raise LookupError
        return keyed[0]

    def commit(self, family: str, slots_list: list[dict]) -> None:
        for slots in slots_list:
            for s, v in slots.items():
                self.use_global[(s, v)] = self.use_global.get((s, v), 0) + 1
                self.use_family[(family, s, v)] = self.use_family.get((family, s, v), 0) + 1


def build_scenarios(d: Design, seed: int | None = None) -> list[Scenario]:
    rng = random.Random(d.seed if seed is None else seed)
    picker = _Picker(rng)
    seen: set = set()
    out: list[Scenario] = []
    for fam, spec in d.families.items():
        made = 0
        tries = 0
        while made < int(spec["groups"]):
            tries += 1
            if tries > 50 * int(spec["groups"]) + 500:
                raise BuildError(f"family {fam}: could not build {spec['groups']} distinct groups (made {made}). Every "
                                 "scenario must be unique across all families and satisfy the family's slot constraints: "
                                 "add surface values to the slots this family samples (templates/<lang>.yaml), relax its "
                                 "constraints in design.yaml, or lower `groups`.")
            try:
                base = {}
                for slot in sample_order(d):
                    flt = (spec.get("base") or {}).get(slot, {})
                    cands = [v for v in d.slots[slot] if matches(d, slot, v, flt, None) and _satisfiable(d, spec, slot, v)
                             and _family_ok(d, slot, v, fam)]
                    base[slot] = picker.pick(fam, slot, cands, lambda v, s=slot: _excluded(d, s, v, base))
                variants = []
                for vs in spec["variants"]:
                    slot = vs["slot"]
                    used = {base[slot]} | {x[slot] for x, _ in variants}
                    cands = [v for v in d.slots[slot] if v not in used and matches(d, slot, v, vs.get("filter"), base)
                             and _family_ok(d, slot, v, fam)]
                    vslots = dict(base)
                    vslots[slot] = picker.pick(fam, slot, cands, lambda v, s=slot: _excluded(d, s, v, base))
                    variants.append((vslots, vs))
            except LookupError:
                continue
            sigs = [tuple(sorted(base.items()))] + [tuple(sorted(v.items())) for v, _ in variants]
            if any(s in seen for s in sigs) or len(set(sigs)) != len(sigs):
                continue
            seen.update(sigs)
            picker.commit(fam, [base] + [v for v, _ in variants])
            made += 1
            gid = f"{fam}{made:03d}"
            bfacts = facts_of(d, base)
            bg = gold(d.statute, bfacts)
            _month_invariant(d, base, bg)
            group = [Scenario(gid, fam, 0, base, bfacts, bg, "base")]
            for k, (vslots, vs) in enumerate(variants, start=1):
                slot = vs["slot"]
                vfacts = facts_of(d, vslots)
                vg = gold(d.statute, vfacts)
                _month_invariant(d, vslots, vg)
                if vg.verdict == "open":
                    role = "contested"
                elif vg.verdict == bg.verdict:
                    role = "placebo"
                else:
                    role = "true_flip"
                if vs.get("expect") and vs["expect"] != role:
                    raise BuildError(f"{gid}/{k}: design expects {vs['expect']}, gold engine says {role} ({vg.reason})")
                changed = {e.id for e in d.statute.elements
                           if element_status(d.statute, e.id, bfacts)[0] != element_status(d.statute, e.id, vfacts)[0]}
                allowed = readers(d, slot, base[slot]) | readers(d, slot, vslots[slot])
                if not changed <= allowed:
                    raise BuildError(f"{gid}/{k}: elements {sorted(changed - allowed)} changed but do not read slot {slot}")
                trap = vs.get("trap") or d.slots[slot][vslots[slot]].get("trap")
                group.append(Scenario(gid, fam, k, vslots, vfacts, vg, role, slot, trap if role == "placebo" else None))
            out.extend(group)
    return out


# ------------------------------------------------------------------------------------------------ items

def _cite(d: Design, keys, lang: str | None = None) -> list[str]:
    """Citations of the sources, in the item's language where the statute file gives one (`cite_lang`)."""
    out = []
    for k in keys:
        src = d.statute.sources[k]
        c = (src.get("cite_lang") or {}).get(lang) or src.get("cite") or src.get("ref") or k
        if c not in out:
            out.append(c)
    return out


def _authorities(g: Gold) -> list[str]:
    tr = [dict(t) for t in g.trace]
    if g.verdict == "convict":
        keys = [a for t in tr for a in t["authority"]]
    else:
        keys = [a for t in tr if t["element"] == g.deciding_element for a in t["authority"]]
    out = []
    for k in keys:
        if k not in out:
            out.append(k)
    return out


def acceptance(d: Design, sc: Scenario) -> str:
    """English acceptance criterion from design.yaml `acceptance` (statute-specific wording, generic logic)."""
    spec = d.raw["acceptance"]
    g = sc.gold
    kw = {k: str(v).replace("_", " ") for k, v in sc.facts.items()}
    kw["char"] = kw.get("characteristic", "")
    if g.verdict == "convict":
        trap = (spec.get("traps") or {}).get(sc.trap)
        return spec["convict"].format(**kw) + (f", {trap}." if trap else ".")
    if g.verdict == "acquit":
        reasons = spec.get("reasons") or {}
        # most specific first: "<reason>|act=<act id>" (A22), "<reason>|<value of the deciding element>", "<reason>"
        keys = [f"{g.reason}|act={sc.slots['act']}"] if "act" in sc.slots else []
        keys += [f"{g.reason}|{sc.facts.get(g.deciding_element)}", g.reason]
        why = next((reasons[k] for k in keys if k in reasons), g.reason).format(**kw)
        return spec["acquit"].format(why=why, **kw)
    return ((spec.get("open_reasons") or {}).get(g.reason) or spec["open"]).format(**kw)


def rationale(d: Design, sc: Scenario) -> str:
    parts = []
    for t in (dict(x) for x in sc.gold.trace):
        e = d.statute.element(t["element"])
        note = ""
        if e.kind == "covered_set":
            cf = e.values[t["value"]].get("covered_from")
            note = f" (covered from {cf})" if cf else " (not on the closed list)"
        elif e.kind == "date" and e.in_force_from:
            note = f" (in force from {e.in_force_from})"
        parts.append(f"{t['element']}={t['value']}: {t['status']}{note}")
    return "; ".join(parts) + f" -> {sc.gold.verdict} ({sc.gold.reason})"


def reference_answers(d: Design, lang: str, sc: Scenario) -> tuple[str, str, str | None]:
    """(chosen, rejected) in the item language. Placeholders: {char_label} (answers.char_labels of the characteristic),
    {date} (the date slot's surface), {<element>_label} for elements listed under answers.labels, {<slot>_label} for
    slots listed under answers.slot_labels (e.g. the setting); a capitalised placeholder ({Setting_label}) capitalises
    the first letter. An answer may be a list of variants; one is chosen deterministically per item."""
    import hashlib
    a = d.answers[lang]
    kw = {}
    if "characteristic" in sc.facts:
        kw["char_label"] = (a.get("char_labels") or {}).get(sc.facts["characteristic"], "")
    if "date" in sc.slots:
        kw["date"] = d.templates[lang]["dates"][sc.slots["date"]]
    for el, labels in (a.get("labels") or {}).items():
        if el in sc.facts:
            kw[f"{el}_label"] = labels.get(sc.facts[el], "")
    for slot, labels in (a.get("slot_labels") or {}).items():
        if slot in sc.slots:
            kw[f"{slot}_label"] = labels.get(sc.slots[slot], "")
    kw.update({k[:1].upper() + k[1:]: (v[:1].upper() + v[1:] if isinstance(v, str) else v) for k, v in list(kw.items())})
    key = sc.gold.reason
    # a reason may be refined by the value of the deciding element: "<reason>|<value>" wins over "<reason>"; an
    # act-specific key "<reason>|act=<act id>" (A22) wins over both
    detail = f"{key}|{sc.facts.get(sc.gold.deciding_element)}" if sc.gold.deciding_element in sc.facts else None
    keys = ([f"{key}|act={sc.slots['act']}"] if "act" in sc.slots else []) + ([detail] if detail else []) + [key]
    seed = int(hashlib.sha256(f"{sc.group_id}/{sc.k}".encode()).hexdigest(), 16)

    def choose(v, salt):
        return v[(seed + salt) % len(v)] if isinstance(v, list) else v

    def pick(section):
        sec = a.get(section) or {}
        for k in keys:
            if k in sec:
                return sec[k]
        raise DesignError(f"answers/{lang}.yaml: no {section!r} answer for gold reason {key!r}"
                          + (f" (or {detail!r})" if detail else "") + "; add one (see docs/add-a-statute.md)")
    chosen = choose(pick("chosen"), 0)
    rejected = choose(a["traps"][sc.trap], 1) if (sc.trap and sc.trap in (a.get("traps") or {})) else choose(pick("rejected"), 1)
    # `minimal`: the chosen answer mirrored, with the verdict and the deciding legal claim negated, of about the same
    # length and wording; used for preference accuracy, where a longer chosen answer would otherwise lose on length
    mins = a.get("minimal") or {}
    minimal = next((mins[k] for k in keys if k in mins), None)
    return chosen.format(**kw), rejected.format(**kw), (choose(minimal, 0).format(**kw) if minimal else None)


def _scope(d: Design, lang: str, sc: Scenario, chosen: str) -> dict:
    """answers/<lang>.yaml `scope_note` (A17, made case-specific in A19): what "not punishable under this article" does
    not mean and where else to turn. Looked up like the answers: "<reason>|act=<act>", "<reason>|<characteristic>", "<reason>", then
    "<verdict>|<characteristic>" (punishable items: the referral that fits the group), then the verdict. Kept apart from `chosen`, which stays the scored reference answer; `chosen_with_scope` is the answer an
    assistant should give."""
    notes = d.answers[lang].get("scope_note") or {}
    reason, char = sc.gold.reason, sc.facts.get("characteristic")
    act = sc.slots.get("act")
    note = (notes.get(f"{reason}|act={act}") or notes.get(f"{reason}|{char}") or notes.get(reason)
            or notes.get(f"{sc.gold.verdict}|{char}") or notes.get(sc.gold.verdict))
    return dict(scope_note=note, chosen_with_scope=f"{chosen} {note}") if note else {}


def item_id(d: Design, lang: str, sc: Scenario) -> str:
    prefix = d.raw.get("id_prefix") or d.statute.id.split("_", 1)[-1]
    return f"{prefix}-{lang}-{sc.group_id}-{sc.k}"


def build_items(d: Design, scenarios: list[Scenario], subset: str = "core") -> list[dict]:
    heldout = d.raw.get("heldout_wording_family")
    prov = dict(generator_version=GENERATOR_VERSION, seed=d.seed, statute_id=d.statute.id,
                statute_version=d.statute.version, statute_sha256=d.statute.sha256())
    items = []
    for lang in d.langs:
        for sc in scenarios:
            fspec = d.families.get(sc.family) or {}
            if fspec.get("langs") and lang not in fspec["langs"]:
                continue                 # a family may be rendered in some languages only (A18)
            text = render(d, lang, sc.slots)
            chosen, rejected, minimal = reference_answers(d, lang, sc)
            auth = _authorities(sc.gold)
            fam = d.slots["act"][sc.slots["act"]].get("family") if "act" in sc.slots else None
            items.append(dict(
                id=item_id(d, lang, sc), lang=lang, subset=fspec.get("subset", subset), statute=d.statute.id,
                twin_group=sc.group_id, family=sc.family, variant=sc.role, variant_index=sc.k,
                changed_slot=sc.changed_slot, base_id=item_id(d, lang, Scenario(sc.group_id, sc.family, 0, {}, {}, sc.gold, "base")),
                template_id=sc.slots.get("frame"), wording_family=fam,
                split=("heldout" if fam == heldout else "fit") if (heldout and fam) else "all",
                slots=dict(sc.slots), facts=dict(sc.facts),
                **{e: sc.facts.get(e) for e in d.statute.element_ids if e in sc.facts},
                text=text,
                gold_verdict=sc.gold.verdict, deciding_element=sc.gold.deciding_element, gold_reason=sc.gold.reason,
                label=sc.gold.label, trap=sc.trap,
                acceptance_criterion=acceptance(d, sc), chosen=chosen, rejected=rejected,
                **({'rejected_minimal': minimal} if minimal else {}),
                **_scope(d, lang, sc, chosen),
                rationale=rationale(d, sc), citation=_cite(d, auth, lang), normative_source=auth,
                licence="CDLA-Permissive-2.0", canary=d.raw.get("canary"),
                provenance=dict(prov, translation="source" if lang == "de" else "claude-agents+back-translation"),
            ))
    return items


def build_pref_prompts(d: Design, items: list[dict]) -> list[dict]:
    """Preference prompts: the plain free-text question (R0) of every settled item, with the item's `chosen` answer and
    its length-matched mirror `rejected_minimal` (same wording, verdict and deciding claim negated) as the two
    continuations. They are stored by direction (`convict` = the answer that
    says punishable, `acquit` = the one that says not punishable), so a forced choice between them is scored exactly
    like the Ja/Nein framings; `chosen_side` records which of the two is the item's chosen answer."""
    rows = []
    for it in items:
        if it["label"] != "settled":
            continue
        side = it["gold_verdict"]
        other = "acquit" if side == "convict" else "convict"
        if not it.get("rejected_minimal"):
            continue
        rows.append(dict(prompt_id=f"{it['id']}/R0/pref", item_id=it["id"], lang=it["lang"], rung="R0", framing="pref",
                         user=it["text"] + question(d, it["lang"], "R0", "open"), answer_prefix="",
                         **{side: it["chosen"], other: it["rejected_minimal"]}, chosen_side=side))
    return rows


def build_prompts(d: Design, items: list[dict], rungs=None, framings=FRAMINGS) -> list[dict]:
    """One row per (item, rung, framing): the exact user message and the forced-choice candidates."""
    rows = []
    for it in items:
        for r in (rungs or rung_names(d, it["lang"])):
            for f in framings:
                c = candidates(d, it["lang"], f)
                rows.append(dict(prompt_id=f"{it['id']}/{r}/{f}", item_id=it["id"], lang=it["lang"], rung=r, framing=f,
                                 user=it["text"] + question(d, it["lang"], r, f, family=it.get("family")), **c))
    return rows
