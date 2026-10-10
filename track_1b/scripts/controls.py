"""A13 controls (exploratory, after judge round 4): is "convicts everything" a yes-bias, and which part of R5 hurts?

1. Polarity. Framing `rev` asks the acquittal question ("Würde ein Schweizer Gericht die Person freisprechen?"), so a
   model that leans towards "Ja" now leans towards acquittal. Scores stay in the conviction direction
   (lo = log p(convict answer) - log p(acquit answer)), so conv and rev are directly comparable. Two bias-free reads:
   - polarity-averaged: mean of an item's conv and rev scores, decided at 0. A yes-bias b enters conv as +b and rev
     as -b, so it cancels; no parameter is fitted. `yes_bias` reports b = mean (lo_conv - lo_rev) / 2.
   - calibrated threshold: per (language, rung, framing) the threshold that maximises balanced accuracy, chosen on
     4 of 5 folds of twin groups and applied to the fifth (out-of-fold; a twin group never straddles fit and test).
2. R5 factorial (German, Ja/Nein): R3, R5, R5a (R3's question after the law), R5b (R5 without the Regeste's closing
   example), R5c (R1's instruction after the law), R5d (R5 plus Art. 1 StGB), R6 (R1's instruction before the law),
   and R6 with the verdict word; R6 in French and Italian.

    python scripts/controls.py [--extra runs_a13]      # writes reports/controls_a13.json
"""
import argparse
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from statute_twins.analysis.results import _auc  # noqa: E402
from statute_twins.qc.checks import load_items  # noqa: E402

RUNS = {"de": ["publicai-70b-fc-core", "publicai-70b-ctrl-de", "publicai-70b-r5x-de"],
        "fr": ["publicai-70b-fc-core-fr", "publicai-70b-ctrl-fr", "publicai-70b-r6-fr"],
        "it": ["publicai-70b-fc-core-it", "publicai-70b-ctrl-it", "publicai-70b-r6-it"]}
FOLDS = 5


def load_rows(dirs, run):
    for d in dirs:
        p = Path(d) / f"{run}.jsonl"
        if p.exists():
            return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
    return []


def cell_stats(items, scores, thr=0.0):
    """scores: {item_id: lo}; settled items only."""
    tp = pos = tn = neg = 0
    for iid, lo in scores.items():
        i = items[iid]
        if i["gold_verdict"] == "convict":
            pos += 1
            tp += lo > thr
        else:
            neg += 1
            tn += lo <= thr
    rc, ra = (tp / pos if pos else None), (tn / neg if neg else None)
    return dict(n=pos + neg, convict_correct=tp, convict_n=pos, acquit_correct=tn, acquit_n=neg, recall_convict=rc,
                recall_acquit=ra, balanced_accuracy=(rc + ra) / 2 if pos and neg else None,
                auc=_auc([lo for iid, lo in scores.items() if items[iid]["gold_verdict"] == "convict"],
                         [lo for iid, lo in scores.items() if items[iid]["gold_verdict"] == "acquit"]))


def best_threshold(items, scores):
    vals = sorted(set(scores.values()))
    cands = [vals[0] - 1] + [(a + b) / 2 for a, b in zip(vals, vals[1:])] + [vals[-1] + 1]
    return max(cands, key=lambda t: (cell_stats(items, scores, t)["balanced_accuracy"] or 0, -abs(t)))


def calibrated(items, scores):
    """Out-of-fold balanced accuracy with a threshold fitted on the other folds (folds = twin groups by hash)."""
    fold = lambda iid: int(hashlib.sha256(items[iid]["twin_group"].encode()).hexdigest(), 16) % FOLDS
    decided = {}
    thrs = []
    for k in range(FOLDS):
        fit = {i: s for i, s in scores.items() if fold(i) != k}
        t = best_threshold(items, fit)
        thrs.append(t)
        decided.update({i: s - t for i, s in scores.items() if fold(i) == k})
    st = cell_stats(items, decided)
    st["thresholds"] = [round(t, 3) for t in thrs]
    st.pop("auc")
    return st


def by_reason(items, scores, thr=0.0):
    out = defaultdict(lambda: [0, 0])
    for iid, lo in scores.items():
        i = items[iid]
        if i["gold_verdict"] == "acquit":
            r = i["gold_reason"] + ("|" + i["characteristic"] if i["gold_reason"] == "characteristic:not_listed" else "")
            out[r][0] += lo <= thr
            out[r][1] += 1
    return {k: f"{v[0]}/{v[1]}" for k, v in sorted(out.items())}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--extra", default="runs_a13", help="folder with the A13 runs if not yet released")
    ap.add_argument("--out", default=str(ROOT / "reports/controls_a13.json"))
    a = ap.parse_args()
    dirs = [ROOT / "dataset/responses", ROOT / a.extra]
    items = {i["id"]: i for i in load_items(ROOT / "dataset")}
    settled = {k for k, i in items.items() if i["label"] == "settled" and i["subset"] != "battery162"}
    cells = defaultdict(dict)                     # (lang, rung, framing) -> {item_id: lo}
    for lang, runs in RUNS.items():
        for run in runs:
            for r in load_rows(dirs, run):
                if "error" in r or r.get("lo_conv") is None or r["item_id"] not in settled or r.get("framing") == "pref":
                    continue
                cells[(lang, r["rung"], r["framing"])][r["item_id"]] = r["lo_conv"]
    out = dict(note="A13, exploratory (post hoc, after judge round 4); 70B via Public AI, exact forced choice; settled items",
               cells=[], polarity=[], factorial=[])
    for (lang, rung, fr), sc in sorted(cells.items()):
        if len(sc) < 600:                         # the sampled factorial cells are reported below, not here
            continue
        rec = dict(lang=lang, rung=rung, framing=fr, **cell_stats(items, sc))
        rec["calibrated_oof"] = calibrated(items, sc)
        if fr == "rev" or (rung in ("R0",) and fr == "conv"):
            rec["acquit_by_reason"] = by_reason(items, sc)
        out["cells"].append(rec)
    for (lang, rung, fr), sc in sorted(cells.items()):
        if fr != "rev" or (lang, rung, "conv") not in cells:
            continue
        conv = cells[(lang, rung, "conv")]
        common = sorted(set(sc) & set(conv))
        if len(common) < 600:
            continue
        avg = {i: (conv[i] + sc[i]) / 2 for i in common}
        bias = [(conv[i] - sc[i]) / 2 for i in common]
        flips = sum((conv[i] > 0) != (sc[i] > 0) for i in common)
        out["polarity"].append(dict(lang=lang, rung=rung, n=len(common), yes_bias_mean=sum(bias) / len(bias),
                                    conv_rev_disagree=flips, averaged=cell_stats(items, avg),
                                    averaged_by_reason=by_reason(items, avg)))
    for lang, rung, fr in [("de", r, "conv") for r in ("R3", "R5", "R5a", "R5b", "R5c", "R5d", "R6")] + \
                          [("de", "R5", "ver"), ("de", "R6", "ver"), ("fr", "R3", "conv"), ("fr", "R5", "conv"),
                           ("fr", "R6", "conv"), ("it", "R3", "conv"), ("it", "R5", "conv"), ("it", "R6", "conv")]:
        sc = cells.get((lang, rung, fr))
        if sc:
            rec = dict(lang=lang, rung=rung, framing=fr, **cell_stats(items, sc), acquit_by_reason=by_reason(items, sc))
            # the variants ran on a sample of twin groups; every cell is also given on exactly those items
            ref = cells.get((lang, "R5a" if lang == "de" else "R6", "conv")) or {}
            same = {i: v for i, v in sc.items() if i in ref}
            if same:
                rec["same_items"] = cell_stats(items, same)
            out["factorial"].append(rec)
    Path(a.out).write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    for c in out["cells"]:
        if c["framing"] == "rev" or c["rung"] in ("R0", "R3"):
            print(f"{c['lang']} {c['rung']:4} {c['framing']:4} conv {c['convict_correct']}/{c['convict_n']} acq "
                  f"{c['acquit_correct']}/{c['acquit_n']} bal {c['balanced_accuracy']:.3f} auc {c['auc']:.3f} | "
                  f"calibrated bal {c['calibrated_oof']['balanced_accuracy']:.3f}")
    for p in out["polarity"]:
        av = p["averaged"]
        print(f"polarity {p['lang']} {p['rung']}: yes-bias {p['yes_bias_mean']:.2f} nats, disagree {p['conv_rev_disagree']}/"
              f"{p['n']}, averaged acq {av['acquit_correct']}/{av['acquit_n']} conv {av['convict_correct']}/{av['convict_n']} "
              f"bal {av['balanced_accuracy']:.3f}")
    for f in out["factorial"]:
        print(f"factorial {f['lang']} {f['rung']:4} {f['framing']}: acq {f['acquit_correct']}/{f['acquit_n']} conv "
              f"{f['convict_correct']}/{f['convict_n']} bal {f['balanced_accuracy']:.3f}")


if __name__ == "__main__":
    main()
