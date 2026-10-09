"""The encoded law matches the pinned official text it cites (oracle: Fedlex consolidations and their footnotes)."""
import datetime as dt
import json

import pytest

from statute_twins import statute as S

from conftest import statute_dirs


@pytest.mark.parametrize("sdir", statute_dirs(), ids=lambda p: p.name)
def test_pinned_source_hashes(sdir):
    st = S.load(sdir)
    assert S.verify_sources(st) == []


def _rec(st, key, lang):
    return json.loads(st.source_file(key, lang).read_text(encoding="utf-8"))


@pytest.mark.parametrize("sdir", statute_dirs(), ids=lambda p: p.name)
def test_closed_list_anchors_against_official_text(sdir):
    """Every value covered on a consolidation's date has its statutory term in that text; no uncovered value does."""
    st = S.load(sdir)
    checked = 0
    for key, src in st.sources.items():
        if not src.get("anchors"):
            continue
        for lang in src["text_sha256"]:
            rec = _rec(st, key, lang)
            text = " ".join(rec["paragraphs"])
            on = dt.date.fromisoformat(rec["applicability_date"])
            for e in st.elements:
                if e.kind != "covered_set":
                    continue
                for v, spec in e.values.items():
                    anchor = (spec.get("anchor") or {}).get(lang)
                    if not anchor:
                        continue
                    covered = spec.get("covered_from") is not None and spec["covered_from"] <= on
                    assert (anchor in text) == covered, (key, lang, v, anchor, covered)
                    checked += 1
    if any(e.kind == "covered_set" for e in st.elements):
        assert checked > 0


@pytest.mark.parametrize("sdir", statute_dirs(), ids=lambda p: p.name)
def test_amendment_dates_are_stated_in_the_official_footnotes(sdir):
    st = S.load(sdir)
    for key, src in st.sources.items():
        if src.get("kind") != "amendment" or "evidence_in" not in src:
            continue
        for lang, needle in src["evidence_text"].items():
            notes = " ".join(_rec(st, src["evidence_in"], lang)["notes"])
            assert needle in notes, (key, lang, needle)


@pytest.mark.parametrize("sdir", statute_dirs(), ids=lambda p: p.name)
def test_element_dates_equal_amendment_in_force_dates(sdir):
    st = S.load(sdir)
    amend = {k: dt.date.fromisoformat(str(v["in_force"])) for k, v in st.sources.items() if v.get("kind") == "amendment"}
    for e in st.elements:
        if e.kind == "date":
            for a in e.authority:
                if a in amend:
                    assert e.in_force_from == amend[a], (e.id, a)
        if e.kind == "covered_set":
            for v, spec in e.values.items():
                dates = [amend[a] for a in spec.get("authority", []) if a in amend]
                if dates:
                    assert spec["covered_from"] == max(dates), (e.id, v)


def test_261bis_versions_differ_exactly_by_sexual_orientation():
    from conftest import STATUTES
    st = S.load(STATUTES / "stgb_261bis")
    old = " ".join(_rec(st, "fedlex_261bis_2020", "de")["paragraphs"])
    new = " ".join(_rec(st, "fedlex_261bis_2026", "de")["paragraphs"])
    assert "Rasse, Ethnie oder Religion" in old and "sexuellen Orientierung" not in old
    assert "Rasse, Ethnie, Religion oder sexuellen Orientierung" in new
    # publicity is an element of Abs. 1, 2 and 4 (and not of Abs. 5), in force and before
    paras = _rec(st, "fedlex_261bis_2026", "de")["paragraphs"]
    assert [("öffentlich" in p) for p in paras[:5]] == [True, True, False, True, False]
