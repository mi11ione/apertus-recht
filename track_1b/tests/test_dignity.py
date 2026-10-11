"""A18: the dignity threshold of Art. 261bis Abs. 4 as an element with a default (BGE 131 IV 23 E. 3)."""
from pathlib import Path

from statute_twins import statute
from statute_twins.generator import build, design
from statute_twins.gold.engine import gold

ROOT = Path(__file__).resolve().parents[1]
ST = statute.load(ROOT / "statutes/stgb_261bis")
BASE = {"act_date": "2023-03-15", "characteristic": "religion", "paragraph": "abs4", "setting": "public"}


def test_default_keeps_existing_gold_and_trace():
    g = gold(ST, BASE)                                   # no dignity fact: the default (degrading) is met
    assert (g.verdict, g.reason) == ("convict", "convict")
    assert all(dict(t)["element"] != "dignity" for t in g.trace)


def test_dignity_values_decide():
    assert gold(ST, dict(BASE, dignity="degrading")).verdict == "convict"
    g = gold(ST, dict(BASE, dignity="criticism"))
    assert (g.verdict, g.reason) == ("acquit", "dignity:failed")
    g = gold(ST, dict(BASE, dignity="borderline"))
    assert (g.verdict, g.reason) == ("open", "dignity:contested")
    # another failing element still decides first where it comes earlier in the element order
    assert gold(ST, dict(BASE, characteristic="canton", dignity="criticism")).reason == "characteristic:not_listed"


def test_dignity_family_is_outside_the_core_set():
    d = design.load(ROOT / "statutes/stgb_261bis")
    items = build.build_items(d, build.build_scenarios(d))
    dig = [i for i in items if i["family"] == "DIGNITY"]
    assert dig and {i["subset"] for i in dig} == {"dignity"}
    assert {i["lang"] for i in dig} == {"de", "fr", "it"}
    assert all(i["subset"] == "core" for i in items if i["family"] != "DIGNITY" and i["subset"] != "battery162")
    assert all("dignity" not in i for i in items if i["family"] != "DIGNITY")


def test_a22_criticism_pairings_and_policy_demand_answers():
    """A22: the finances criticism is never drawn for Judaism (antisemitic stereotype); the four criticisms stay
    balanced; the policy demand (a4D_crit4) has its own answers and acceptance criterion, keyed by act."""
    import collections
    d = design.load(ROOT / "statutes/stgb_261bis")
    items = [i for i in build.build_items(d, build.build_scenarios(d)) if i["family"] == "DIGNITY"]
    crit = [i for i in items if i["variant"] == "true_flip"]
    assert not [i for i in crit if i["slots"]["act"] == "a4D_crit2" and i["slots"]["group"].startswith("rel_jewish")]
    for lang in ("de", "fr", "it"):
        n = collections.Counter(i["slots"]["act"] for i in crit if i["lang"] == lang)
        assert sum(n.values()) == 20 and set(n.values()) == {5}
    other = next(i for i in crit if i["slots"]["act"] != "a4D_crit4" and i["lang"] == "de")
    for i in (i for i in crit if i["slots"]["act"] == "a4D_crit4"):
        same_lang = next(o for o in crit if o["lang"] == i["lang"] and o["slots"]["act"] != "a4D_crit4")
        assert "Kosovo" in i["chosen"] and "Kosovo" in i["rejected_minimal"] and i["chosen"] != same_lang["chosen"]
        assert "policy demand" in i["acceptance_criterion"]
    assert "sich auf objektive Umstände stützt" in other["chosen"]
