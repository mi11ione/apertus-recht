"""Reconcile two independent court-tuple extractions (amendment A4).

    python scripts/court_reconcile.py <first_dir> <second_dir> <work_dir> [--tiebreak <tiebreak.jsonl>]

Without --tiebreak: writes per-field agreement to statutes/stgb_261bis/review/court/extraction_agreement.json and a
tie-break packet (<work_dir>/tiebreak_packet.txt) with every decision on which a rule-relevant field differs.
With --tiebreak: writes the reconciled tuples to statutes/stgb_261bis/review/court/tuples.jsonl (normalisation of
duplicates and non-prosecution orders as in normalisation.json; no quotations).
"""
import argparse
import collections
import glob
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from statute_twins.analysis.stats import cohen_kappa  # noqa: E402

D = ROOT / "statutes/stgb_261bis/review/court"
FIELDS = ["rules_on_261bis", "outcome", "setting", "characteristic", "paragraph", "acquittal_ground", "act_year"]


def load(pattern):
    out = {}
    for f in sorted(glob.glob(pattern)):
        for l in Path(f).read_text(encoding="utf-8").split("\n"):
            if l.strip():
                r = json.loads(l)
                out[r["decision_id"]] = r
    return out


def norm(r, f):
    if f == "act_year":
        return (str(r.get("act_date") or "")[:4]) or None
    v = r.get(f)
    if f == "rules_on_261bis":
        return bool(v)
    if f == "characteristic" and isinstance(v, str) and v.startswith("other"):
        return "other"
    return v


def relevant(a, b):
    """Fields that enter the pre-registered rule for this decision."""
    fs = ["rules_on_261bis"]
    if a.get("rules_on_261bis") or b.get("rules_on_261bis"):
        fs += ["outcome", "setting", "characteristic", "paragraph", "act_year"]
        if "acquitted" in (a.get("outcome"), b.get("outcome")):
            fs.append("acquittal_ground")
    return fs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("first"); ap.add_argument("second"); ap.add_argument("work")
    ap.add_argument("--tiebreak", default=None)
    a = ap.parse_args()
    A = load(f"{a.first}/tuples_*.jsonl")
    B = load(f"{a.second}/second_*.jsonl")
    ids = sorted(set(A) & set(B))
    agree = {}
    for f in FIELDS:
        pa = [str(norm(A[i], f)) for i in ids]
        pb = [str(norm(B[i], f)) for i in ids]
        agree[f] = dict(agree=sum(x == y for x, y in zip(pa, pb)), n=len(ids), kappa=round(cohen_kappa(pa, pb), 3))
    conflicts = {i: [f for f in relevant(A[i], B[i]) if norm(A[i], f) != norm(B[i], f)] for i in ids}
    conflicts = {i: fs for i, fs in conflicts.items() if fs}
    (D / "extraction_agreement.json").write_text(json.dumps(dict(decisions=len(ids), per_field=agree,
        decisions_with_rule_relevant_conflict=len(conflicts), conflicts=conflicts), indent=1) + "\n")
    print(json.dumps(agree), len(conflicts), "decisions with conflicts")
    work = Path(a.work)
    if not a.tiebreak:
        pk = {}
        for p in sorted(glob.glob(f"{a.first}/court_packet_*.txt")):
            for block in Path(p).read_text(encoding="utf-8").split("=== DECISION ")[1:]:
                pk[block.split(" |", 1)[0].strip()] = "=== DECISION " + block
        with open(work / "tiebreak_packet.txt", "w", encoding="utf-8") as f:
            for i, fs in conflicts.items():
                f.write(pk[i])
                f.write(f"\n--- CODER 1: " + json.dumps({k: A[i].get(k) for k in FIELDS[:-1] + ['act_date']}, ensure_ascii=False))
                f.write(f"\n--- CODER 2: " + json.dumps({k: B[i].get(k) for k in FIELDS[:-1] + ['act_date']}, ensure_ascii=False))
                f.write(f"\n--- FIELDS IN DISPUTE: {', '.join(fs)}\n\n")
        print("tie-break packet:", work / "tiebreak_packet.txt")
        return
    T = load(a.tiebreak)
    old = {json.loads(l)["decision_id"]: json.loads(l) for l in (D / "tuples.jsonl").read_text(encoding="utf-8").split("\n") if l.strip()}
    out = []
    for i in ids:
        r = dict(old[i])
        src = T.get(i) or A[i]
        for k in ("rules_on_261bis", "outcome", "act_date", "setting", "characteristic", "paragraph", "acquittal_ground"):
            r[k] = src.get(k)
        r["extractor"] = "two independent claude agents" + ("; third agent on conflicts" if i in T else "; agreed")
        r["notes"] = re.sub(r"['\"«“‘][^'\"»”’]{3,}['\"»”’]", "[quote removed]", (src.get("notes") or ""))
        if (r.get("normalisation") or "").startswith(("duplicate", "confirmation")):
            r["rules_on_261bis"] = False
        r["verified"] = "second extraction" + (" + tie-break" if i in T else "")
        out.append(r)
    (D / "tuples.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in out), encoding="utf-8")
    print("reconciled", len(out), "tie-broken", len(T))


if __name__ == "__main__":
    main()
