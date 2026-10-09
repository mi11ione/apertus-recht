"""Court validation of the gold engine (pre-registered in prereg/PREREG_court.md).

    python scripts/court_validation.py statutes/stgb_261bis/review/court/tuples.jsonl

Input rows (one per triaged decision; no quotations are stored in the repository):
  decision_id, court, language, date, docket, rules_on_261bis (bool), outcome (convicted / acquitted / remanded /
  not_decided), act_date (YYYY-MM-DD or YYYY), setting (public / private / unclear), characteristic (race / ethnicity /
  religion / sexual_orientation / other:<name> / unclear), paragraph (abs1..abs5 / unclear), acquittal_ground
  (setting / characteristic / act_date / dignity / intent / justification / procedure / other / null),
  verified (null / "R1"), extractor, notes
Output: reports/court_validation.json
"""
import collections
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from statute_twins import statute  # noqa: E402
from statute_twins.analysis.stats import wilson  # noqa: E402
from statute_twins.gold.engine import gold  # noqa: E402

MODELLED_GROUNDS = {"setting", "characteristic", "act_date"}
CHARS = {"race", "ethnicity", "religion", "sexual_orientation"}


def classify(t: dict, st) -> dict:
    out = dict(decision_id=t["decision_id"], court=t["court"], language=t["language"], outcome=t["outcome"],
               verified=t.get("verified"))
    if not t.get("rules_on_261bis") or t["outcome"] not in ("convicted", "acquitted"):
        return dict(out, status="excluded", why="does not rule on a 261bis charge" if not t.get("rules_on_261bis") else t["outcome"])
    if t.get("paragraph") in ("abs3", "abs5"):
        return dict(out, status="out_of_scope", why=f"{t['paragraph']} not modelled")
    if t["outcome"] == "acquitted" and t.get("acquittal_ground") not in MODELLED_GROUNDS:
        return dict(out, status="out_of_scope", why=f"acquitted on unmodelled ground: {t.get('acquittal_ground')}")
    if "unclear" in (t.get("setting"), t.get("characteristic"), t.get("paragraph")) or not t.get("act_date"):
        return dict(out, status="unextractable", why="a modelled element is unclear")
    ch = t["characteristic"]
    values = st.element("characteristic").values
    if ch not in values:
        # a characteristic the model does not name (e.g. nationality): outside the closed list, so it behaves exactly like
        # any never-covered value; we pass the first such value and record the substitution
        ch = next(v for v, spec in values.items() if spec.get("covered_from") is None)
        out["characteristic_substituted"] = t["characteristic"]
    date = t["act_date"] if len(t["act_date"]) == 10 else f"{t['act_date'][:4]}-07-01"
    facts = dict(act_date=date, characteristic=ch, paragraph=t["paragraph"] if t["paragraph"] in ("abs1", "abs2", "abs4") else "abs1",
                 setting=t["setting"])
    g = gold(st, facts)
    court = "convict" if t["outcome"] == "convicted" else "acquit"
    agree = g.verdict == court
    return dict(out, status="in_scope", engine=g.verdict, engine_reason=g.reason, court_verdict=court, agree=agree,
                acquittal_ground=t.get("acquittal_ground"), facts=facts)


def main(path: str) -> None:
    st = statute.load(ROOT / "statutes/stgb_261bis")
    tuples = [json.loads(l) for l in Path(path).read_text(encoding="utf-8").splitlines() if l.strip()]
    rows = [classify(t, st) for t in tuples]
    ins = [r for r in rows if r["status"] == "in_scope"]
    k = sum(r["agree"] for r in ins)
    ver = [r for r in ins if r.get("verified")]
    kv = sum(r["agree"] for r in ver)
    status = collections.Counter(r["status"] for r in rows)
    lo, hi = wilson(k, len(ins))
    summary = (f"{len(tuples)} decisions triaged; {len(ins)} in scope; engine agrees with the court in {k}/{len(ins)} "
               f"(Wilson 95% {lo:.2f}-{hi:.2f}); {status['out_of_scope']} out of scope (unmodelled grounds), "
               f"{status['unextractable']} unextractable, {status['excluded']} excluded; human-verified tuples: "
               f"{len(ver)} ({kv} agree)")
    pool = json.loads((ROOT / "statutes/stgb_261bis/review/court/pool.json").read_text()) if (ROOT / "statutes/stgb_261bis/review/court/pool.json").exists() else {}
    rep = dict(summary=summary, pool=pool, counts=dict(status), in_scope=len(ins), agree=k, agreement_ci=[lo, hi],
               verified=len(ver), verified_agree=kv,
               confusion={f"court {a} / engine {b}": n for (a, b), n in sorted(collections.Counter((r["court_verdict"], r["engine"]) for r in ins).items())},
               by_ground=dict(collections.Counter(r.get("acquittal_ground") for r in ins if r["court_verdict"] == "acquit")),
               disagreements=[r for r in ins if not r["agree"]], rows=rows)
    (ROOT / "reports").mkdir(exist_ok=True)
    (ROOT / "reports/court_validation.json").write_text(json.dumps(rep, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(summary)


if __name__ == "__main__":
    main(sys.argv[1])
