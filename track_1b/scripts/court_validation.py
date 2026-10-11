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
        if t.get("rules_on_261bis"):
            why = t["outcome"]
        elif t["outcome"] in ("convicted", "acquitted"):
            why = "not counted here: a duplicate instance of a case counted elsewhere, or a ruling the coders did not treat as deciding the charge (see the tuple's notes)"
        else:
            why = "no final ruling on a 261bis charge"
        return dict(out, status="excluded", why=why)
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
    shown = dict(facts, characteristic=f"unlisted:{t['characteristic'].split(':', 1)[-1]}") if "characteristic_substituted" in out else facts
    # does the element the court acquitted on also fail in the engine? (the engine reports the first failing element)
    ground = t.get("acquittal_ground")
    ground_fails = None
    if court == "acquit":
        ground_fails = {"setting": facts["setting"] != "public",
                        "characteristic": g.reason.startswith("characteristic"),
                        "act_date": g.reason.startswith(("act_date", "characteristic:not_yet"))}.get(ground)
    # BGE 130 IV 111 (2004) changed the publicity test; an earlier acquittal on publicity applied the old test
    old_test = court == "acquit" and ground == "setting" and (t.get("date") or "9999") < "2004"
    return dict(out, status="in_scope", engine=g.verdict, engine_reason=g.reason, court_verdict=court, agree=agree,
                acquittal_ground=ground, ground_fails_in_engine=ground_fails, before_bge_130_iv_111=old_test, facts=shown,
                engine_input=facts if shown is not facts else None)


def summarise(rows, label):
    ins = [r for r in rows if r["status"] == "in_scope"]
    k = sum(r["agree"] for r in ins)
    status = collections.Counter(r["status"] for r in rows)
    lo, hi = wilson(k, len(ins))
    conf = collections.Counter((r["court_verdict"], r["engine"]) for r in ins)
    acq = [r for r in ins if r["court_verdict"] == "acquit"]
    con = [r for r in ins if r["court_verdict"] == "convict"]
    ka, kc = sum(r["agree"] for r in acq), sum(r["agree"] for r in con)
    by_class = dict(convictions=dict(agree=kc, n=len(con), ci=list(wilson(kc, len(con)))),
                    acquittals=dict(agree=ka, n=len(acq), ci=list(wilson(ka, len(acq))),
                                    ground_fails_in_engine=sum(bool(r.get("ground_fails_in_engine")) for r in acq),
                                    before_bge_130_iv_111=[r["decision_id"] for r in acq if r.get("before_bge_130_iv_111")]),
                    always_convict_baseline=f"{len(con)}/{len(ins)}")
    return dict(label=label, decisions=len(rows), in_scope=len(ins), agree=k, ci=[lo, hi], counts=dict(status), by_class=by_class,
                court_convict=sum(r["court_verdict"] == "convict" for r in ins),
                court_acquit=sum(r["court_verdict"] == "acquit" for r in ins),
                confusion={f"court {a} / engine {b}": n for (a, b), n in sorted(conf.items())})


def main(*paths: str) -> None:
    st = statute.load(ROOT / "statutes/stgb_261bis")
    tuples = []
    for path in paths:
        stratum = "B" if path.endswith("_B.jsonl") else "A"
        for l in Path(path).read_text(encoding="utf-8").split("\n"):
            if l.strip():
                t = json.loads(l)
                t["stratum"] = stratum
                tuples.append(t)
    # corrections found after extraction (each with its amendment and reason); the extracted value is kept as `extracted`
    cpath = ROOT / "statutes/stgb_261bis/review/court/corrections.jsonl"
    corrections = [json.loads(l) for l in cpath.read_text(encoding="utf-8").splitlines() if l.strip()] if cpath.exists() else []
    for c in corrections:
        for t in tuples:
            if t["decision_id"] == c["decision_id"] and t.get(c["field"]) == c["from"]:
                t.setdefault("extracted", {})[c["field"]] = c["from"]
                t[c["field"]] = c["to"]
                t["corrected_by"] = c["amendment"]
    # a decision that appears in both strata (e.g. as BGE and as docket) is counted once, in stratum A
    seen = {t["decision_id"] for t in tuples if t["stratum"] == "A"}
    tuples = [t for t in tuples if t["stratum"] == "A" or t["decision_id"] not in seen]
    rows = []
    for t in tuples:
        r = classify(t, st)
        r["stratum"] = t["stratum"]
        rows.append(r)
    strata = {s_: summarise([r for r in rows if r["stratum"] == s_], s_) for s_ in sorted({r["stratum"] for r in rows})}
    pooled = summarise(rows, "pooled")
    # POST HOC (not pre-registered): decisions whose only missing element is the act date, the characteristic is not
    # sexual orientation and the decision is from 1998 or later; the act date is bounded by the decision date
    ph_rows = []
    for t in tuples:
        r0 = classify(t, st)
        if r0["status"] == "unextractable" and not t.get("act_date") and t.get("characteristic") != "sexual_orientation" \
                and "unclear" not in (t.get("setting"), t.get("characteristic"), t.get("paragraph")) and (t.get("date") or "0") >= "1998":
            r1 = classify(dict(t, act_date=t["date"][:4]), st)
            if r1["status"] == "in_scope":
                ph_rows.append(r1)
    posthoc = dict(note="post hoc, not pre-registered: act date bounded by the decision date (>= 1998), characteristic "
                        "other than sexual orientation", added=len(ph_rows), agree=sum(r["agree"] for r in ph_rows),
                   acquittals=sum(r["court_verdict"] == "acquit" for r in ph_rows),
                   combined=f"{pooled['agree'] + sum(r['agree'] for r in ph_rows)}/{pooled['in_scope'] + len(ph_rows)}")
    ins = [r for r in rows if r["status"] == "in_scope"]
    k = sum(r["agree"] for r in ins)
    ver = [r for r in ins if r.get("verified")]
    kv = sum(r["agree"] for r in ver)
    status = collections.Counter(r["status"] for r in rows)
    lo, hi = wilson(k, len(ins))
    summary = (f"{len(tuples)} decisions triaged ({', '.join(f'stratum {k_}: {v_['decisions']}' for k_, v_ in strata.items())}); "
               f"{len(ins)} in scope ({pooled['court_convict']} convictions, {pooled['court_acquit']} acquittals); engine agrees with the court in {k}/{len(ins)} "
               f"(Wilson 95% {lo:.2f}-{hi:.2f}; an engine that always convicts would agree in {pooled['by_class']['always_convict_baseline']}; "
               f"acquittals {pooled['by_class']['acquittals']['agree']}/{pooled['by_class']['acquittals']['n']}, Wilson "
               f"{pooled['by_class']['acquittals']['ci'][0]:.2f}-{pooled['by_class']['acquittals']['ci'][1]:.2f}); "
               f"{status['out_of_scope']} out of scope (unmodelled grounds), "
               f"{status['unextractable']} unextractable, {status['excluded']} excluded; every tuple extracted twice by "
               f"independent agents, conflicts settled by a third (amendment A4)")
    # POST HOC (A12, after a legal review): count cases, not decision instances; drop a conviction later annulled under
    # Art. 10 ECHR; report genocide denial (Abs. 4, second half) apart from incitement and degradation.
    groups = [{"bge_BGE_149_IV_170", "bger_6B_777_2022"}, {"bger_6B_627_2015", "zh_obergericht_SB140436"},
              {"bger_6B_350_2019", "vd_findinfo_Jug___2019___36", "vd_gerichte_PE16.006073"}]
    superseded = {"bger_6B_398_2007": "Perinçek: ECtHR (Grand Chamber, 2015) found a violation of Art. 10 ECHR; "
                                      "the Federal Court revised the judgment (6F_6/2016)"}
    notes = {t["decision_id"]: (t.get("notes") or "").lower() for t in tuples}
    denial_kw = ("leugn", "négation", "negazion", "genocid", "génocide", "holocaust", "shoah", "völkermord")
    case_of = {}
    for g in groups:
        for d in g:
            case_of[d] = sorted(g)[0]
    cases = {}
    for r in ins:
        if r["decision_id"] in superseded:
            continue
        c = case_of.get(r["decision_id"], r["decision_id"])
        cases.setdefault(c, []).append(r)
    agree_cases = sum(all(x["agree"] for x in v) for v in cases.values())
    acq = [c for c, v in cases.items() if v[0]["court_verdict"] == "acquit"]
    denial = [c for c, v in cases.items() if any(k in notes.get(x["decision_id"], "") for x in v for k in denial_kw)]
    lo_c, hi_c = wilson(agree_cases, len(cases))
    case_level = dict(note="post hoc (A12): distinct cases; one superseded conviction excluded", cases=len(cases),
                      agree=agree_cases, ci=[lo_c, hi_c], acquittal_cases=len(acq),
                      acquittals_before_bge_130=[c for c in acq if any(x.get("before_bge_130_iv_111") for x in cases[c])],
                      genocide_denial_cases=len(denial), incitement_or_degradation_cases=len(cases) - len(denial),
                      genocide_denial_instances=sum(any(k in notes.get(r["decision_id"], "") for k in denial_kw) for r in ins),
                      acquittals={c: ("predates BGE 130 IV 111" if any(x.get("before_bge_130_iv_111") for x in cases[c]) else
                                      "clean" if cases[c][0].get("acquittal_ground", "").split(":")[0] == cases[c][0]["engine_reason"].split(":")[0]
                                      else f"same outcome, other ground (court: {cases[c][0].get('acquittal_ground')}; "
                                           f"engine: {cases[c][0]['engine_reason']})") for c in acq},
                      merged_instances=sum(len(g) for g in groups) - len(groups), superseded=superseded)
    pool = json.loads((ROOT / "statutes/stgb_261bis/review/court/pool.json").read_text()) if (ROOT / "statutes/stgb_261bis/review/court/pool.json").exists() else {}
    rep = dict(summary=summary, pool=pool, strata=strata, pooled=pooled, posthoc_act_date_bound=posthoc, counts=dict(status), in_scope=len(ins), agree=k, agreement_ci=[lo, hi],
               verified=len(ver), verified_agree=kv,
               confusion={f"court {a} / engine {b}": n for (a, b), n in sorted(collections.Counter((r["court_verdict"], r["engine"]) for r in ins).items())},
               by_ground=dict(collections.Counter(r.get("acquittal_ground") for r in ins if r["court_verdict"] == "acquit")),
               disagreements=[r for r in ins if not r["agree"]], case_level=case_level, rows=rows)
    (ROOT / "reports").mkdir(exist_ok=True)
    (ROOT / "reports/court_validation.json").write_text(json.dumps(rep, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(summary)


if __name__ == "__main__":
    main(*sys.argv[1:])
