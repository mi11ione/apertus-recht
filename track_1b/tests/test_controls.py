"""A13 controls: the acquittal-direction question (`rev`) and the R5 factorial rungs (values computed by hand)."""
import pytest

from statute_twins.analysis import heldout
from statute_twins.analysis.results import accuracy
from statute_twins.generator import build, render
from statute_twins.harness.backends.base import Score


def test_rev_framing_maps_yes_to_acquittal(d261):
    for lang, yes, no in (("de", "Ja", "Nein"), ("fr", "Oui", "Non"), ("it", "Sì", "No")):
        c = render.candidates(d261, lang, "rev")
        assert (c["convict"], c["acquit"]) == (no, yes)
        assert render.candidates(d261, lang, "conv")["convict"] == yes      # the pre-registered framing is the mirror


def test_rev_score_by_hand():
    # "Ja" (= acquit under rev) at log p -0.1, "Nein" (= convict) at -3.0: lo_conv = -3.0 - (-0.1) = -2.9 -> acquit
    s = Score(lp_convict=-3.0, lp_acquit=-0.1, method="exact_prefill")
    assert s.lo_conv == pytest.approx(-2.9) and s.decided() == "acquit"
    items = [dict(id="a1", label="settled", gold_verdict="acquit", subset="core", lang="de"),
             dict(id="c1", label="settled", gold_verdict="convict", subset="core", lang="de")]
    rows = [dict(prompt_id="a1/R0/rev", item_id="a1", rung="R0", framing="rev", lo_conv=s.lo_conv),
            dict(prompt_id="c1/R0/rev", item_id="c1", rung="R0", framing="rev", lo_conv=-0.5)]   # convict item acquitted
    (cell,) = accuracy(items, rows)
    assert (cell["framing"], cell["recall_acquit"], cell["recall_convict"], cell["balanced_accuracy"]) == ("rev", 1.0, 0.0, 0.5)


def test_rev_never_enters_the_preregistered_test():
    assert "rev" not in heldout.PREREG_FRAMINGS
    assert not set(render.CONTROL_RUNGS) & set(heldout.PREREG_RUNGS)


def test_control_rungs_are_built_from_the_released_parts(d261):
    p = d261.prompts["de"]
    r3, r5 = render.question(d261, "de", "R3", "conv"), render.question(d261, "de", "R5", "conv")
    law = render.law_block(d261, "de")
    # R5a: the law, then exactly R3's question block
    assert render.question(d261, "de", "R5a", "conv") == p["law_text"]["intro"] + law + r3
    # R5b: R5 minus the Regeste's closing example, and nothing else
    r5b = render.question(d261, "de", "R5b", "conv")
    assert "Waldhütte" in r5 and "Waldhütte" not in r5b
    assert r5b.endswith("(Änderung der Rechtsprechung; E. 5.2).\n\nFrage:" + p["tails"]["conv"])
    assert len(r5) - len(r5b) == len(" Öffentlichkeit bejaht im Falle von Äusserungen an einem Vortrag, der im Rahmen einer "
                                     "geschlossenen Veranstaltung in einer Waldhütte gehalten wurde, an welcher 40 bis 50 "
                                     "geladene Skinheads teilnahmen, die verschiedenen Gruppierungen angehörten (E. 6).")
    # R5c: the law, then R1's element-check instruction in place of the "Frage:" label
    assert render.question(d261, "de", "R5c", "conv") == p["law_text"]["intro"] + law + p["heads"]["R1"] + p["tails"]["conv"]
    for lang in ("fr", "it"):
        assert "40" not in render.law_block(d261, lang, exemplar=False).split("261bis")[-1][-200:]


def test_released_prompt_files_carry_no_control_rows(d261, scenarios261):
    items = [i for i in build.build_items(d261, scenarios261[:3]) if i["lang"] == "de"]
    rows = build.build_prompts(d261, items)
    assert {r["framing"] for r in rows} == {"conv", "ver"}
    assert not {r["rung"] for r in rows} & set(render.CONTROL_RUNGS)


def test_r5d_pastes_pinned_art1_before_art2(d261):
    for lang, art1, art2 in (("de", "Art. 1 StGB\nEine Strafe oder Massnahme darf nur wegen einer Tat verhängt werden, "
                                    "die das Gesetz ausdrücklich unter Strafe stellt.", "\n\nArt. 2 StGB\n"),
                             ("fr", "Art. 1 CP\nUne peine ou une mesure", "\n\nArt. 2 CP\n"),
                             ("it", "Art. 1 CP\nUna pena o misura", "\n\nArt. 2 CP\n")):
        r5, r5d = (render.question(d261, lang, r, "conv") for r in ("R5", "R5d"))
        assert art1 in r5d and "Art. 1 " + ("StGB" if lang == "de" else "CP") + "\n" not in r5
        assert r5d.index(art1) < r5d.index(art2)
        start = r5d.index(art1)
        block = r5d[start: r5d.index(art2, start) + 2]          # "Art. 1 …\n<text>\n\n": the only addition to R5
        assert r5d.replace(block, "", 1) == r5
