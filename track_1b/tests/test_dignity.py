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
