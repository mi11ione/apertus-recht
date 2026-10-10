"""Scoring functions against values computed by hand (independent of any run data)."""
import math

import pytest

from statute_twins.analysis import heldout
from statute_twins.analysis.results import accuracy
from statute_twins.analysis.stats import cohen_kappa, wilson


def test_wilson_hand_values():
    # 8/10: centre (0.8 + 1.96²/20) / (1 + 1.96²/10) = 0.71674, half-width 0.22658
    lo, hi = wilson(8, 10)
    assert lo == pytest.approx(0.49016, abs=1e-4) and hi == pytest.approx(0.94332, abs=1e-4)
    # 0/94 (adjudication blind sample): upper = 2 · (1.96²/188) / (1 + 1.96²/94) = 0.03926
    assert wilson(0, 94) == pytest.approx((0.0, 0.03926), abs=1e-4)
    # 58/58 (court validation): lower = n / (n + z²) = 58 / 61.8415
    assert wilson(58, 58)[0] == pytest.approx(58 / (58 + 1.959963984540054 ** 2), abs=1e-9)
    assert all(math.isnan(x) for x in wilson(0, 0))


def test_cohen_kappa_hand_values():
    # po = 3/4, pe = (2/4)(1/4) + (2/4)(3/4) = 1/2  ->  kappa = (3/4 - 1/2) / (1/2) = 1/2
    assert cohen_kappa([1, 1, 0, 0], [1, 0, 0, 0]) == pytest.approx(0.5)
    assert cohen_kappa(["a", "b"], ["a", "b"]) == 1.0
    assert cohen_kappa(["a", "a"], ["a", "a"]) == 1.0  # pe = 1: perfect agreement on a single label


def _item(i, gold, label="settled"):
    return dict(id=i, label=label, gold_verdict=gold, subset="core", lang="de")


def test_accuracy_and_balanced_accuracy_by_hand():
    items = [_item("c1", "convict"), _item("c2", "convict"), _item("a1", "acquit"), _item("a2", "acquit"),
             _item("x", "convict", label="contested")]
    row = lambda i, **k: dict(prompt_id=i + "/R0/conv", item_id=i, rung="R0", framing="conv", **k)
    rows = [row("c1", lo_conv=1.0),           # convict, correct
            row("c2", decision="unparsed"),   # unparsed: counted, never correct
            row("a1", lo_conv=2.0),           # convict, wrong
            row("a2", lo_conv=-1.0),          # acquit, correct
            row("x", lo_conv=5.0),            # contested: not scored for accuracy
            row("a1", error="timeout")]       # failed request: not scored
    (c,) = accuracy(items, rows)
    assert (c["n"], c["correct"], c["unparsed"]) == (4, 2, 1)
    assert c["accuracy"] == 0.5
    assert c["recall_convict"] == 0.5 and c["recall_acquit"] == 0.5   # 1/2 each; the unparsed c2 is a miss
    assert c["balanced_accuracy"] == 0.5
    # a model that convicts everything: accuracy = share of convict gold, balanced accuracy = 0.5
    rows = [row(i, lo_conv=3.0) for i in ("c1", "c2", "a1", "a2")]
    (c,) = accuracy(items, rows)
    assert (c["accuracy"], c["balanced_accuracy"]) == (0.5, 0.5)


def _core(i, split, setting, char, date, gold, reason, variant="v"):
    return dict(id=i, subset="core", lang="de", label="settled", split=split, variant=variant, gold_verdict=gold,
                gold_reason=reason, facts=dict(setting=setting, characteristic=char, act_date=date))


ITEMS = [
    _core("f1", "fit", "public", "religion", "2021-03-01", "convict", None, "base"),
    _core("f2", "fit", "private", "religion", "2021-03-01", "acquit", "setting:failed"),
    _core("f3", "fit", "public", "age", "2021-03-01", "acquit", "characteristic:not_listed"),
    _core("h1", "heldout", "public", "religion", "2021-03-01", "convict", None, "base"),
    _core("h2", "heldout", "private", "religion", "2021-03-01", "acquit", "setting:failed"),
    _core("h3", "heldout", "public", "age", "2021-03-01", "acquit", "characteristic:not_listed"),
]


def test_heldout_fit_and_predict_by_hand():
    convict_all = {i["id"]: "convict" for i in ITEMS}
    law = heldout.fit([i for i in ITEMS if i["split"] == "fit"], convict_all)
    # f3 is not evidence about the setting (its characteristic already fails), f2 is not evidence about the group
    assert law == {"setting=public": True, "setting=private": True, "characteristic=religion": True,
                   "characteristic=age": True, "date=post2020-07|other": True}
    assert heldout.predict(ITEMS[4], law) == "convict"            # the read-back convicts the private setting
    assert heldout.predict(ITEMS[4], {}) == "acquit"              # unseen values default to the statute


def test_heldout_run_gain_by_hand():
    rows = [dict(item_id=i["id"], lang="de", rung="R0", framing="conv", lo_conv=1.0) for i in ITEMS]
    r = heldout.run(ITEMS, rows)
    (c,) = r["cells"]
    # held-out: the model convicts h1..h3; read-back predicts convict for all (3/3); the statute only h1 (1/3)
    assert (c["readback_accuracy"], c["statute_accuracy"]) == (1.0, pytest.approx(1 / 3))
    assert c["gain"] == pytest.approx(2 / 3) and c["anchored"]
    assert r["verdict_by_rung"]["R0"]["passed"]
    # a model that follows the statute: gain 0, test fails
    rows = [dict(item_id=i["id"], lang="de", rung="R0", framing="conv",
                 lo_conv=1.0 if i["gold_verdict"] == "convict" else -1.0) for i in ITEMS]
    r = heldout.run(ITEMS, rows)
    assert r["cells"][0]["gain"] == 0 and not r["verdict_by_rung"]["R0"]["passed"]
    # unanchored (the base item is acquitted): no framing can be read, the test cannot pass
    rows = [dict(item_id=i["id"], lang="de", rung="R0", framing="conv", lo_conv=-1.0) for i in ITEMS]
    assert not heldout.run(ITEMS, rows)["verdict_by_rung"]["R0"]["passed"]
