"""POST HOC context for the pre-registered held-out test (not part of the test; heldout.py is unchanged).

Per run, language, rung and framing on the held-out split:
  constant      accuracy of always predicting the model's majority decision (an always-convict model is predicted
                perfectly by it, so the read-back adds nothing at R0)
  ceiling       read-back fitted on the held-out items themselves (an upper bound for the transferred read-back)
  max_gain      1 - statute accuracy: the largest gain any predictor can show; the pre-registered 0.15 needs a model
                that deviates from the statute on at least 15% of held-out items
  error_reduction  gain / max_gain
  gain_ci       95% bootstrap interval of the gain, resampling twin groups (items of one group move together)
  mcnemar       b = read-back right and statute wrong, c = the reverse
"""
from __future__ import annotations

import random

from . import heldout


def _decisions(rows: list[dict], lang: str) -> dict:
    cells: dict = {}
    for r in rows:
        if "error" in r or r.get("lang") != lang or r.get("framing") not in heldout.PREREG_FRAMINGS \
                or r.get("rung") not in heldout.PREREG_RUNGS:
            continue
        d = ("convict" if r["lo_conv"] > 0 else "acquit") if r.get("lo_conv") is not None else r.get("decision")
        if d in ("convict", "acquit"):
            cells.setdefault((r["rung"], r["framing"]), {})[r["item_id"]] = d
    return cells


def run(items: list[dict], rows: list[dict], lang: str = "de", b: int = 2000, seed: int = 0) -> list[dict]:
    core = [i for i in items if i["subset"] != "battery162" and i["lang"] == lang and i["label"] == "settled"]
    fit_items = [i for i in core if i["split"] == "fit"]
    held = [i for i in core if i["split"] == "heldout"]
    out = []
    for (rung, fr), dec in sorted(_decisions(rows, lang).items()):
        h = [i for i in held if i["id"] in dec]
        if not h:
            continue
        law = heldout.fit(fit_items, dec)
        own = heldout.fit(h, dec)
        rb = {i["id"]: heldout.predict(i, law) == dec[i["id"]] for i in h}
        st = {i["id"]: i["gold_verdict"] == dec[i["id"]] for i in h}
        n = len(h)
        acc_rb, acc_st = sum(rb.values()) / n, sum(st.values()) / n
        share = sum(dec[i["id"]] == "convict" for i in h) / n
        groups: dict = {}
        for i in h:
            groups.setdefault(i["twin_group"], []).append(i["id"])
        keys = sorted(groups)
        rng = random.Random(seed)
        gains = []
        for _ in range(b):
            ids = [x for _k in range(len(keys)) for x in groups[keys[rng.randrange(len(keys))]]]
            gains.append((sum(rb[x] for x in ids) - sum(st[x] for x in ids)) / len(ids))
        gains.sort()
        mx = 1 - acc_st
        out.append(dict(lang=lang, rung=rung, framing=fr, n_heldout=n, twin_groups=len(keys), readback=acc_rb,
                        statute=acc_st, gain=acc_rb - acc_st, constant=max(share, 1 - share),
                        ceiling=sum(heldout.predict(i, own) == dec[i["id"]] for i in h) / n, max_gain=mx,
                        error_reduction=(acc_rb - acc_st) / mx if mx else None,
                        gain_ci=[gains[int(0.025 * b)], gains[int(0.975 * b) - 1]],
                        mcnemar=dict(b=sum(rb[x] and not st[x] for x in rb), c=sum(st[x] and not rb[x] for x in rb)),
                        items_short_of_threshold=max(0.0, (heldout.THRESHOLD - (acc_rb - acc_st)) * n)))
    return out
