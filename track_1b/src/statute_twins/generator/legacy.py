"""The 162-item legacy battery (subset ``battery162``): the exact German texts scored in the exploration spikes.

These items predate the generator. They are kept verbatim (including two dative slips, "von Schwarze Menschen" type,
documented in the data card) because every cached stage, build and live score in ``responses/`` was measured on them.
Their legal facts are reconstructed from the spike metadata, the gold engine recomputes their verdicts, and
``tests/test_legacy.py`` checks those verdicts against the labels assigned by hand in the spikes.
"""
from __future__ import annotations

import json
from pathlib import Path

from ..gold.engine import gold
from .build import Scenario, _authorities, _cite, acceptance, rationale, reference_answers
from .design import Design

CHAR_DE = {"Rasse": "race", "Ethnie": "ethnicity", "Religion": "religion", "sexuelle Orientierung": "sexual_orientation"}
PARA = {"Abs. 1": "abs1", "Abs. 2": "abs2", "Abs. 4": "abs4"}
ROLE_OF = {"base": "base"}
FILES = {"ladder": "ladder_items.json", "never": "never_items.json"}


def _facts(set_name: str, x: dict) -> tuple[dict, str]:
    """(facts, date slot id) of a legacy item."""
    if set_name == "ladder":
        ch = CHAR_DE[x["characteristic"]]
        if x["variant"] == "group":
            ch = "gender_identity"
        date = "d2019_03" if x["variant"] == "time" else "d2023_03"
    else:
        ch = x["characteristic"]
        date = "d2023_03"
    setting = "private" if x["variant"] == "true" else "public"
    iso = {"d2019_03": "2019-03-15", "d2023_03": "2023-03-15"}[date]
    return dict(act_date=iso, characteristic=ch, paragraph=PARA[x["para"]], setting=setting), date


def legacy_id(set_name: str, x: dict) -> str:
    return f"261bis-de-B{set_name}-{x['item']}-{x['variant']}"


def load_legacy(root: Path) -> dict[str, list[dict]]:
    return {s: json.loads((root / "legacy" / f).read_text(encoding="utf-8")) for s, f in FILES.items()}


def build_legacy_items(d: Design) -> list[dict]:
    sets = load_legacy(d.root)
    items = []
    for set_name, rows in sets.items():
        groups: dict[str, list] = {}
        for x in rows:
            groups.setdefault(x["item"], []).append(x)
        for gid, members in groups.items():
            base = [m for m in members if m["variant"] == "base"][0]
            bfacts, _ = _facts(set_name, base)
            bg = gold(d.statute, bfacts)
            for k, x in enumerate(members):
                facts, date = _facts(set_name, x)
                g = gold(d.statute, facts)
                if x["variant"] == "base":
                    role = "base"
                elif g.verdict == "open":
                    role = "contested"
                else:
                    role = "placebo" if g.verdict == bg.verdict else "true_flip"
                trap = "family_wording" if (x["variant"] == "placebo" and g.verdict == "convict") else None
                # the legacy settings are the template settings of the same name (rally, post, letter, hut, flyer)
                setting_slot = "priv_dinner" if x["variant"] == "true" else (f"pub_{x['setting']}_fam" if x["variant"] == "placebo" else f"pub_{x['setting']}")
                sc = Scenario(f"B{set_name}-{gid}", f"LEGACY_{set_name.upper()}", k, {"date": date, "setting": setting_slot}, facts, g, role,
                              None if role == "base" else {"true": "setting", "placebo": "setting", "group": "group",
                                                          "time": "date"}[x["variant"]], trap)
                chosen, rejected = reference_answers(d, "de", sc)
                auth = _authorities(g)
                items.append(dict(
                    id=legacy_id(set_name, x), lang="de", subset="battery162", statute=d.statute.id,
                    twin_group=sc.group_id, family=sc.family, variant=role, variant_index=k,
                    changed_slot=sc.changed_slot, base_id=legacy_id(set_name, base),
                    template_id=f"legacy_{set_name}", wording_family=None, split="legacy",
                    slots={}, facts=facts, setting=facts["setting"], characteristic=facts["characteristic"],
                    paragraph=facts["paragraph"], act_date=facts["act_date"], text=x["text"],
                    gold_verdict=g.verdict, deciding_element=g.deciding_element, gold_reason=g.reason, label=g.label,
                    trap=trap, acceptance_criterion=acceptance(d, sc), chosen=chosen, rejected=rejected,
                    rationale=rationale(d, sc), citation=_cite(d, auth), normative_source=auth,
                    licence="CDLA-Permissive-2.0", canary=d.raw.get("canary"),
                    legacy=dict(set=set_name, item=x["item"], variant=x["variant"], spike_gold=x["gold"]),
                    provenance=dict(source=f"spikes/{'round7/linie_items.json' if set_name == 'ladder' else 'round8/never_items.json'}",
                                    translation="source"),
                ))
    return items
