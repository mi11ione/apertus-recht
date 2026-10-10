"""Pre-registered held-out read-back test (see prereg/PREREG.md; frozen by prereg/LOCK.json before any model scored
the generated core set).

Read-back ("the law the model applies"): fitted per model, rung and framing on the FIT split (wording families A and
B) of the settled core items of one language. For every legal slot value v (setting value, characteristic, date tag
of the act-date slot combined with the characteristic's coverage class), the model treats v as *satisfied* iff it
convicts at least half of the fit items that carry v and whose other legal values all satisfy the statute (so v is the
only element that could make the statute acquit). Values never observed under that condition default to the statute.
Prediction for an item: convict iff every legal value of the item is treated as satisfied.

Test: on the HELDOUT split (wording family C), compare how well the read-back and the real statute predict the
model's own decisions. Pass iff, in every anchored framing, read-back accuracy - statute accuracy >= 0.15.
A framing is anchored iff the 95% bootstrap CI of the mean log-odds of the held-out base items is above 0.
"""
from __future__ import annotations

from collections import defaultdict

from .stats import bootstrap_ci, mean

THRESHOLD = 0.15
PREREG_FRAMINGS = ("conv", "ver")      # the pre-registered framings; free-text and preference framings never enter the test
LEGAL_SLOTS = ("setting", "group", "date")


def value_keys(item: dict) -> dict:
    """The legal value keys of an item: what the read-back learns a status for."""
    f = item["facts"]
    date_tag = "pre1995" if f["act_date"] < "1995-01-01" else ("pre2020-07" if f["act_date"] < "2020-07-01" else "post2020-07")
    cov = "so" if f["characteristic"] == "sexual_orientation" else "other"
    return dict(setting=f"setting={f['setting']}", group=f"characteristic={f['characteristic']}",
                date=f"date={date_tag}|{cov}")


def statute_ok(item: dict, slot: str) -> bool:
    """Does this slot's value satisfy the statute, given the item's other facts? (from the item's gold trace)"""
    f = item["facts"]
    if slot == "setting":
        return f["setting"] == "public"
    if slot == "group":
        return item["gold_reason"] != "characteristic:not_listed"
    if slot == "date":
        return item["gold_reason"] not in ("characteristic:not_yet_covered", "act_date:not_in_force")
    raise ValueError(slot)


def fit(items: list[dict], decisions: dict) -> dict:
    """{value_key: True/False} learned from fit items (decisions: item_id -> 'convict'/'acquit')."""
    votes = defaultdict(list)
    for it in items:
        d = decisions.get(it["id"])
        if d is None:
            continue
        keys = value_keys(it)
        for slot in LEGAL_SLOTS:
            if all(statute_ok(it, s) for s in LEGAL_SLOTS if s != slot):
                votes[keys[slot]].append(d == "convict")
    return {k: (sum(v) / len(v) >= 0.5) for k, v in votes.items()}


def predict(item: dict, law: dict) -> str:
    keys = value_keys(item)
    for slot in LEGAL_SLOTS:
        sat = law.get(keys[slot])
        if sat is None:
            sat = statute_ok(item, slot)
        if not sat:
            return "acquit"
    return "convict"


def run(items: list[dict], rows: list[dict], lang: str = "de", seed: int = 0) -> dict:
    core = [i for i in items if i["subset"] != "battery162" and i["lang"] == lang and i["label"] == "settled"]
    fit_items = [i for i in core if i["split"] == "fit"]
    held = [i for i in core if i["split"] == "heldout"]
    by_cell = defaultdict(dict)
    lo_cell = defaultdict(dict)
    for r in rows:
        if "error" in r or r.get("lang") != lang or r.get("framing") not in PREREG_FRAMINGS:
            continue
        d = ("convict" if r["lo_conv"] > 0 else "acquit") if r.get("lo_conv") is not None else r.get("decision")
        if d in ("convict", "acquit"):
            by_cell[(r["rung"], r["framing"])][r["item_id"]] = d
            if r.get("lo_conv") is not None:
                lo_cell[(r["rung"], r["framing"])][r["item_id"]] = r["lo_conv"]
    out = []
    for (rung, fr), dec in sorted(by_cell.items()):
        law = fit(fit_items, dec)
        h = [i for i in held if i["id"] in dec]
        if not h:
            continue
        acc_rb = mean(predict(i, law) == dec[i["id"]] for i in h)
        acc_st = mean(i["gold_verdict"] == dec[i["id"]] for i in h)
        base_lo = [lo_cell[(rung, fr)][i["id"]] for i in h if i["variant"] == "base" and i["id"] in lo_cell[(rung, fr)]]
        ci = bootstrap_ci(base_lo, seed=seed) if base_lo else (float("nan"), float("nan"))
        anchored = bool(base_lo) and ci[0] > 0
        out.append(dict(lang=lang, rung=rung, framing=fr, n_fit=sum(i["id"] in dec for i in fit_items), n_heldout=len(h),
                        readback_accuracy=acc_rb, statute_accuracy=acc_st, gain=acc_rb - acc_st, anchored=anchored,
                        base_lo_ci=ci, law={k: v for k, v in sorted(law.items())}))
    verdicts = {}
    for rung in sorted({o["rung"] for o in out}):
        cells = [o for o in out if o["rung"] == rung and o["anchored"]]
        verdicts[rung] = dict(anchored_framings=[o["framing"] for o in cells],
                              passed=bool(cells) and all(o["gain"] >= THRESHOLD for o in cells))
    return dict(threshold=THRESHOLD, cells=out, verdict_by_rung=verdicts)
