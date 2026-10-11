"""Generator invariants, determinism, and byte-identity of the German question strings with the spike batteries."""
import collections
import hashlib
import json
import re

from statute_twins.generator import build, design, legacy, render

from conftest import ROOT, STATUTES


def _digest(items):
    return hashlib.sha256(json.dumps(items, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def test_deterministic(d261):
    a = build.build_items(d261, build.build_scenarios(d261))
    b = build.build_items(d261, build.build_scenarios(design.load(STATUTES / "stgb_261bis")))
    assert _digest(a) == _digest(b)


def test_family_sizes_and_roles(d261, scenarios261):
    groups = collections.defaultdict(list)
    for s in scenarios261:
        groups[s.group_id].append(s)
    for fam, spec in d261.families.items():
        gs = [g for gid, g in groups.items() if g[0].family == fam]
        assert len(gs) == spec["groups"]
        for g in gs:
            assert [s.k for s in g] == list(range(len(spec["variants"]) + 1))
            assert g[0].role == "base"
            for s, vs in zip(g[1:], spec["variants"]):
                assert s.role == vs["expect"]


def test_each_variant_changes_exactly_one_slot(scenarios261):
    groups = collections.defaultdict(list)
    for s in scenarios261:
        groups[s.group_id].append(s)
    for g in groups.values():
        base = g[0].slots
        for s in g[1:]:
            diff = [k for k in base if base[k] != s.slots[k]]
            assert diff == [s.changed_slot]


def _rendered(d, s, lang):
    """A family may be rendered in some languages only (A18: DIGNITY in de, fr, it)."""
    langs = (d.families.get(s.family) or {}).get("langs")
    return not langs or lang in langs


def test_no_duplicate_scenarios_or_texts(d261, scenarios261):
    sigs = [tuple(sorted(s.slots.items())) for s in scenarios261]
    assert len(set(sigs)) == len(sigs)
    for lang in d261.langs:
        texts = [render.render(d261, lang, s.slots) for s in scenarios261 if _rendered(d261, s, lang)]
        assert len(set(texts)) == len(texts), lang


def test_rendered_text_is_clean(d261, scenarios261):
    bad = re.compile(r"[{}]|\s[,.;:]|,,|\.\.(?!\.)|\s{2,}|^\s|\s$")
    for lang in d261.langs:
        for s in scenarios261:
            if not _rendered(d261, s, lang):
                continue
            t = render.render(d261, lang, s.slots)
            assert not bad.search(t.replace(" :", ":").replace(" ;", ";") if lang.split("_")[0] == "fr" else t), (lang, s.group_id, s.k, t)


def test_every_slot_value_is_used(d261, scenarios261):
    used = collections.defaultdict(set)
    for s in scenarios261:
        for k, v in s.slots.items():
            used[k].add(v)
    for slot, vals in d261.slots.items():
        assert set(vals) == used[slot], (slot, set(vals) - used[slot])


def test_german_questions_are_byte_identical_to_the_spike_batteries(d261):
    fx = json.loads((ROOT / "tests/fixtures/legacy_questions.json").read_text(encoding="utf-8"))
    for fr in ("conv", "ver"):
        for r in ("R0", "R3"):
            assert render.question(d261, "de", r, fr) == fx["stage9"][fr][r]
        for r in ("R0", "R3", "R4"):
            assert render.question(d261, "de", r, fr) == fx["live"][fr][r]


def test_legacy_battery_gold_matches_the_spike_labels(d261):
    items = legacy.build_legacy_items(d261)
    assert len(items) == 162
    assert all((i["gold_verdict"] == "convict") == (i["legacy"]["spike_gold"] == 1) for i in items)


def test_legacy_duplicates_are_exactly_the_documented_overlap(d261):
    """The S-NEVER sexual-orientation and gender-identity frames reuse ladder texts by design (30 duplicates)."""
    items = legacy.build_legacy_items(d261)
    c = collections.Counter(i["text"] for i in items)
    assert sum(n - 1 for n in c.values() if n > 1) == 30
    core = {render.render(d261, "de", s.slots) for s in build.build_scenarios(d261)}
    assert not core & set(c)
