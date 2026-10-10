"""Compute results from items + response rows: accuracy against gold, and the read-back of the law each model applies.

Read-back (per edit, rung, framing). An edit pairs a variant V, which the statute decides differently from (or, for
placebos, the same as) a reference Ref that the statute convicts; the two differ in exactly one slot.
  lo = log-odds in the conviction direction (convict continuation minus acquit continuation), per item.
  Status of a true flip, from 95% item-bootstrap CIs:
    F  in force   CI(V) > 0 and CI(Ref) > 0     the model convicts where the statute acquits
    a  applied    CI(V) < 0 and CI(Ref) > 0     the model follows the statute
    u  unanchored CI(Ref) not > 0               the framing does not convict the reference, so it cannot be read
    ?  undecided  otherwise
  A placebo is "held" when CI(V) > 0 and CI(Ref) > 0 (the irrelevant change left the conviction in place), "broken"
  when CI(V) < 0 and CI(Ref) > 0.
  Colour per edit and rung: red = F in every anchored framing (at least one anchored); amber = F in some; none.
For decision-only rows (generate mode) the same rules use Wilson intervals on the conviction rate against 0.5.
"""
from __future__ import annotations

import collections
from collections import defaultdict

from .stats import bootstrap_ci, mean, paired_bootstrap_ci, wilson

FRAMINGS = ("conv", "ver")


# ------------------------------------------------------------------------------------------------------ helpers

def index(rows: list[dict]) -> dict:
    return {r["prompt_id"]: r for r in rows if "error" not in r}


def lo_or_none(r: dict | None):
    if r is None:
        return None
    return r.get("lo_conv")


def decision(r: dict | None):
    if r is None:
        return None
    if r.get("lo_conv") is not None:
        return "convict" if r["lo_conv"] > 0 else "acquit"
    return r.get("decision")


# ------------------------------------------------------------------------------------------------------ accuracy

def accuracy(items: list[dict], rows: list[dict], by=("subset", "lang", "rung", "framing")) -> list[dict]:
    """Accuracy of decisions against gold on settled items, grouped by `by` (item or row fields)."""
    it = {i["id"]: i for i in items}
    cells = defaultdict(lambda: dict(n=0, correct=0, tp=0, pos=0, tn=0, neg=0, unparsed=0))
    scores = defaultdict(lambda: ([], []))          # log-odds of convict-gold and acquit-gold items (for the AUC)
    for r in rows:
        if "error" in r:
            continue
        i = it.get(r["item_id"])
        if i is None or i["label"] != "settled":
            continue
        key = tuple((k, r.get(k, i.get(k))) for k in by)
        c = cells[key]
        d = decision(r)
        if r.get("lo_conv") is not None:
            scores[key][0 if i["gold_verdict"] == "convict" else 1].append(r["lo_conv"])
        # an unparsed answer counts in every denominator and is never correct
        c["n"] += 1
        c["unparsed"] += d not in ("convict", "acquit")
        ok = d == i["gold_verdict"]
        c["correct"] += ok
        if i["gold_verdict"] == "convict":
            c["pos"] += 1
            c["tp"] += ok
        else:
            c["neg"] += 1
            c["tn"] += ok
    out = []
    for key, c in sorted(cells.items(), key=lambda kv: [str(v) for _, v in kv[0]]):
        acc = c["correct"] / c["n"] if c["n"] else float("nan")
        rec_c = c["tp"] / c["pos"] if c["pos"] else float("nan")
        rec_a = c["tn"] / c["neg"] if c["neg"] else float("nan")
        bal = mean([x for x in (rec_c, rec_a) if x == x]) if c["n"] else float("nan")
        out.append(dict(dict(key), n=c["n"], correct=c["correct"], accuracy=acc, accuracy_ci=wilson(c["correct"], c["n"]),
                        recall_convict=rec_c, recall_acquit=rec_a, balanced_accuracy=bal, unparsed=c["unparsed"],
                        acquit_correct=c["tn"], acquit_n=c["neg"], convict_correct=c["tp"], convict_n=c["pos"],
                        auc=_auc(*scores[key]) if key in scores else None))
    return out


def _auc(pos: list, neg: list):
    """Probability that a convict-gold item has a higher conviction log-odds than an acquit-gold item (ties count
    half): how well the scores rank the cases, whatever the decision threshold."""
    if not pos or not neg:
        return None
    allv = sorted([(v, 1) for v in pos] + [(v, 0) for v in neg])
    rank_sum, k = 0.0, 0
    while k < len(allv):
        j = k
        while j < len(allv) and allv[j][0] == allv[k][0]:
            j += 1
        r = (k + j + 1) / 2                      # average rank (1-based) of the tie block
        rank_sum += r * sum(1 for x in allv[k:j] if x[1] == 1)
        k = j
    return (rank_sum - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg))


def contested_lean(items: list[dict], rows: list[dict]) -> list[dict]:
    it = {i["id"]: i for i in items}
    cells = defaultdict(lambda: [0, 0])
    for r in rows:
        i = it.get(r.get("item_id"))
        if i is None or i["label"] != "contested" or "error" in r:
            continue
        d = decision(r)
        c = cells[(i["lang"], r["rung"], r["framing"])]
        c[0] += d == "convict"
        c[1] += 1
    return [dict(lang=k[0], rung=k[1], framing=k[2], convicted=v[0], n=v[1]) for k, v in sorted(cells.items())]


def _ntok(r: dict, side: str):
    x = r.get("extra") or {}
    if "tokens" in x:
        return len(x["tokens"][side])
    if "ntok" in x:
        return x["ntok"][side]
    return None


def preference(items: list[dict], rows: list[dict]) -> list[dict]:
    """Preference accuracy on the `pref` framing: does the model give its item's chosen answer a higher log-probability
    than the rejected one? Reported for the summed log-probability (the forced choice) and per token (length-normalised,
    since chosen answers are longer), by language and by the reason the statute gives (gold reason; `convict`)."""
    it = {i["id"]: i for i in items}
    cells = defaultdict(lambda: dict(n=0, sum_ok=0, tok_ok=0, tok_n=0))
    for r in rows:
        if r.get("framing") != "pref" or "error" in r or r.get("lp_convict") is None:
            continue
        i = it.get(r["item_id"])
        if i is None or i["label"] != "settled":
            continue
        chosen = i["gold_verdict"]
        other = "acquit" if chosen == "convict" else "convict"
        lp = {"convict": r["lp_convict"], "acquit": r["lp_acquit"]}
        for key in ((i["lang"], "all"), (i["lang"], i.get("gold_reason") or "convict")):
            c = cells[key]
            c["n"] += 1
            c["sum_ok"] += lp[chosen] > lp[other]
            n_c, n_o = _ntok(r, chosen), _ntok(r, other)
            if n_c and n_o:
                c["tok_n"] += 1
                c["tok_ok"] += lp[chosen] / n_c > lp[other] / n_o
    return [dict(lang=k[0], reason=k[1], n=c["n"], accuracy=c["sum_ok"] / c["n"], accuracy_ci=wilson(c["sum_ok"], c["n"]),
                 per_token_n=c["tok_n"], per_token_accuracy=(c["tok_ok"] / c["tok_n"]) if c["tok_n"] else float("nan"),
                 per_token_ci=wilson(c["tok_ok"], c["tok_n"]))
            for k, c in sorted(cells.items())]


# ------------------------------------------------------------------------------------------------------ edits

def edit_name(item: dict) -> str:
    if item["variant"] == "true_flip":
        r = item["gold_reason"]
        if r == "characteristic:not_listed":
            return f"{r}|{item['characteristic']}"
        return r
    if item["variant"] == "placebo":
        return f"placebo|{item.get('trap') or item.get('changed_slot')}"
    if item["variant"] == "contested":
        return "contested|setting"
    raise ValueError(item["variant"])


def core_pairs(items: list[dict]) -> dict:
    """{edit: [(variant_item_id, ref_item_id)]} for the generated twin groups; Ref = the group's base."""
    out = defaultdict(list)
    for i in items:
        if i["subset"] != "battery162" and i["variant"] != "base":
            out[(i["lang"], edit_name(i), "core")].append((i["id"], i["base_id"]))
    return out


def legacy_pairs(items: list[dict]) -> dict:
    """The linie9 edit definitions on the legacy battery (reproduces spikes/linie9/analyze9.py)."""
    by = {(i["legacy"]["set"], i["legacy"]["item"], i["legacy"]["variant"]): i["id"]
          for i in items if i["subset"] == "battery162"}
    out = defaultdict(list)
    for (s, item, var), iid in by.items():
        if s == "ladder" and var in ("true", "group", "time"):
            name = {"true": "setting:failed", "group": "characteristic:not_listed|gender_identity",
                    "time": "characteristic:not_yet_covered"}[var]
            out[("de", name, "battery162")].append((iid, by[(s, item, "placebo")]))
        if s == "never" and var == "base":
            trait, frame = item.split("-", 1)
            if trait in ("canton", "occupation", "age"):
                out[("de", f"characteristic:not_listed|{trait}", "battery162")].append((iid, by[("never", f"sexual_orientation-{frame}", "base")]))
    return out


def _status(kind: str, ci_v, ci_r) -> str:
    anchored = ci_r[0] > 0
    if kind == "placebo":
        if not anchored:
            return "u"
        return "held" if ci_v[0] > 0 else ("broken" if ci_v[1] < 0 else "?")
    if not anchored:
        return "u"
    if ci_v[0] > 0:
        return "F"
    if ci_v[1] < 0:
        return "a"
    return "?"


def _rate_ci(decs):
    k = sum(d == "convict" for d in decs)
    lo, hi = wilson(k, len(decs))
    # map to the log-odds sign convention: interval of (rate - 0.5)
    return (lo - 0.5, hi - 0.5), k


def edits(items: list[dict], rows: list[dict], pairs: dict, seed: int = 0) -> list[dict]:
    rx = index(rows)
    rungs = sorted({r["rung"] for r in rx.values()})
    out = []
    for (lang, name, subset), prs in sorted(pairs.items()):
        kind = "placebo" if name.startswith("placebo") else ("contested" if name.startswith("contested") else "flip")
        for rung in rungs:
            for fr in FRAMINGS:
                v_rows = [(rx.get(f"{v}/{rung}/{fr}"), rx.get(f"{r}/{rung}/{fr}")) for v, r in prs]
                v_rows = [(a, b) for a, b in v_rows if a is not None and b is not None]
                if not v_rows:
                    continue
                los = [(lo_or_none(a), lo_or_none(b)) for a, b in v_rows]
                rec = dict(lang=lang, subset=subset, edit=name, kind=kind, rung=rung, framing=fr, n=len(v_rows),
                           v_convicted=sum(decision(a) == "convict" for a, _ in v_rows),
                           ref_convicted=sum(decision(b) == "convict" for _, b in v_rows))
                if all(x is not None and y is not None for x, y in los):
                    ci_v, ci_r, ci_d = paired_bootstrap_ci(los, seed=seed)
                    rec.update(mean_v=mean(x for x, _ in los), mean_ref=mean(y for _, y in los),
                               mean_diff=mean(x - y for x, y in los), ci_v=ci_v, ci_ref=ci_r, ci_diff=ci_d, basis="logodds")
                else:
                    ci_v, _ = _rate_ci([decision(a) for a, _ in v_rows])
                    ci_r, _ = _rate_ci([decision(b) for _, b in v_rows])
                    rec.update(ci_v=ci_v, ci_ref=ci_r, basis="decision_rate")
                rec["status"] = "open" if kind == "contested" else _status(kind, ci_v, ci_r)
                out.append(rec)
    return out


def colours(edit_rows: list[dict]) -> list[dict]:
    """red / amber / none per (subset, lang, edit, rung) over the anchored framings (true flips only)."""
    by = defaultdict(list)
    for e in edit_rows:
        if e["kind"] == "flip":
            by[(e["subset"], e["lang"], e["edit"], e["rung"])].append(e)
    out = []
    for (subset, lang, name, rung), es in sorted(by.items()):
        anchored = [e for e in es if e["status"] != "u"]
        f = [e for e in anchored if e["status"] == "F"]
        colour = "unreadable" if not anchored else ("red" if len(f) == len(anchored) else ("amber" if f else "none"))
        out.append(dict(subset=subset, lang=lang, edit=name, rung=rung, colour=colour,
                        cells={e["framing"]: e["status"] for e in es}))
    return out


def run_results(items: list[dict], rows: list[dict], seed: int = 0) -> dict:
    pairs = core_pairs(items)
    pairs.update(legacy_pairs(items))       # keys carry the subset, so the two never collide
    core_ids = {i["id"] for i in items if i["subset"] != "battery162"}
    sub = [r for r in rows if r.get("item_id") in core_ids]
    leg = [r for r in rows if r.get("item_id") not in core_ids]
    e = edits(items, rows, pairs, seed=seed)
    return dict(
        rows=len(rows), errors=sum("error" in r for r in rows),
        accuracy=accuracy(items, [r for r in rows if r.get("framing") != "pref"]),
        preference=preference(items, rows),
        accuracy_by_family=accuracy(items, sub, by=("lang", "family", "variant", "rung", "framing")) if sub else [],
        contested=contested_lean(items, rows),
        edits=e, colours=colours(e),
        legacy_rows=len(leg), core_rows=len(sub),
    )
