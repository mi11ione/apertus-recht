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


def test_pin_keeps_paragraphs_with_lettered_lists():
    """A paragraph made of a list (introduction + lit. a, b ...) is one entry with its items, nested lists included."""
    from statute_twins.sources.fedlex import extract_article
    xml = b"""<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"><body><article eId="art_9">
    <paragraph eId="art_9/para_1"><num>1</num><content><blockList><listIntroduction> Strafbar ist, wer:</listIntroduction>
    <item><num>a. </num><p>erstens;</p></item><item><num>b. </num><blockList><listIntroduction>zweitens:</listIntroduction>
    <item><num>1. </num><p>unter eins,</p></item></blockList></item></blockList></content></paragraph>
    <paragraph eId="art_9/para_2"><num>2</num><content><p> Zweiter Absatz.<authorialNote><p>Fn.</p></authorialNote></p>
    </content></paragraph></article></body></akomaNtoso>"""
    paras, notes = extract_article(xml, "art_9")
    assert paras == ["Strafbar ist, wer: a. erstens; b. zweitens: 1. unter eins,", "Zweiter Absatz."]
    assert notes == ["Fn."]


def test_pinned_list_paragraphs_are_present():
    """Regression: Art. 179quinquies Abs. 1 (lit. a/b, the exemption the 179ter answers cite) and Art. 329 Abs. 1 StPO."""
    from conftest import STATUTES
    st = S.load(STATUTES / "stgb_179ter")
    q = _rec(st, "fedlex_179quinquies", "de")["paragraphs"]
    assert len(q) == 2 and "a. mit Hilfs-, Rettungs- und Sicherheitsdiensten" in q[0] and "b. im Geschäftsverkehr" in q[0]
    p = _rec(st, "fedlex_stpo_329", "de")["paragraphs"]
    assert len(p) == 5 and p[0].startswith("Die Verfahrensleitung prüft, ob: a.") and "c. Verfahrenshindernisse" in p[0]
