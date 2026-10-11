"""A22 (exploratory, post hoc, after review): repaired controls and stronger statistics.

1. Verdict-only preference mirror (70B, DE/FR/IT, settled items, R0). The released preference test pits `chosen`
   against `rejected_minimal`, which negates both the verdict and the deciding claim (and often contradicts itself).
   Here the mirror keeps `chosen` word for word and flips only its opening verdict word (Ja/Nein, Oui/Non, Sì/No).
   The user message and the `chosen` continuation are byte-identical to prompts_pref_core_<lang>.jsonl; scoring is
   statute_twins.analysis.results.preference (the forced choice on summed log-probabilities, plus per token).
2. R5a ablations (German, Ja/Nein, the same stable 80-twin-group sample as A13, `--sample 240`). A13's R5b/R5c/R5d
   were built on R5 (which acquits 0), so they could not show a part of the law that helps. Rebuilt on R5a
   (R3's rules after the verbatim law):
     R5ab = R5a without the Regeste's closing example (consid. 6)
     R5ac = R5a with R1's element-check instruction after the law (before R3's rules, which repeat its opening)
     R5ag = R3's rules before the law, R1's element-check instruction after it (the R6/R5c order contrast on R5a)
     R5ad = R5a with Art. 1 StGB before Art. 2
   R5a itself is re-sent (identical request: a gateway cache hit, a check that the sample and prompts match A13).
3. Statistics from stored responses only (no model calls): twin-group bootstrap of the read-back colours, Wilson
   intervals, exact McNemar, twin-group bootstrap of the held-out gains, reversed-question per-element counts.

Prompts go to runs_a22/eval/ (not dataset/eval/, so the released manifest and its generator check stay untouched);
responses to runs_a22/.

    python scripts/controls_a22.py build     # writes runs_a22/eval/prompts_{ctrl2_core_de,prefv_core_*}.jsonl
    sh runs_a22/run.sh                       # statute-twins eval --backend gateway ... (see that file)
    python scripts/controls_a22.py report    # writes reports/controls_a22.json
    python scripts/controls_a22.py stats     # writes reports/stats_a22.json (CPU only)
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

A22 = ROOT / "runs_a22"
EVAL = A22 / "eval"
FLIP = {"de": {"Ja.": "Nein.", "Nein.": "Ja."}, "fr": {"Oui.": "Non.", "Non.": "Oui."}, "it": {"Sì.": "No.", "No.": "Sì."}}
NEW_RUNGS = ["R5a", "R5ab", "R5ac", "R5ag", "R5ad"]
REASONS = [("all", "all"), ("convict", "convict"), ("setting:failed", "private setting"),
           ("characteristic:not_listed", "not listed"), ("characteristic:not_yet_covered", "SO before 1 Jul 2020"),
           ("act_date:not_in_force", "act before 1995")]


def jl(p):
    p = Path(p)
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()] if p.exists() else []


def wjl(p, rows):
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    Path(p).write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")


# ------------------------------------------------------------------------------------------------------------ build

def question_a22(d, lang: str, rung: str, framing: str) -> str:
    from statute_twins.generator.render import law_block, question
    p = d.prompts[lang]
    lt, head, closed, tail = p["law_text"], p["heads"]["R2"], p["closed_list"], p["tails"][framing]
    if rung == "R5a":
        return question(d, lang, "R5a", framing)
    if rung == "R5ab":
        return lt["intro"] + law_block(d, lang, exemplar=False) + head + closed + tail
    if rung == "R5ac":
        return lt["intro"] + law_block(d, lang) + p["heads"]["R1"] + head + closed + tail
    if rung == "R5ag":
        return head + closed + lt["intro"] + law_block(d, lang) + p["heads"]["R1"] + tail
    if rung == "R5ad":
        return lt["intro"] + law_block(d, lang, art1=True) + head + closed + tail
    raise ValueError(rung)


def flip_verdict(lang: str, text: str) -> str:
    first, sep, rest = text.partition(" ")
    if first not in FLIP[lang]:
        raise ValueError(f"{lang}: answer does not open with a verdict word: {text[:40]!r}")
    return FLIP[lang][first] + sep + rest


def cmd_build(_a):
    from statute_twins.generator import design
    from statute_twins.generator.render import candidates
    d = design.load(ROOT / "statutes/stgb_261bis")
    ds = ROOT / "dataset/eval"
    items = jl(ds / "core_de.jsonl")
    # 1. the R5a ablations; R5a and R3 are checked byte for byte against the released prompt files
    old = {r["prompt_id"]: r for r in jl(ds / "prompts_ctrl_core_de.jsonl") + jl(ds / "prompts_core_de.jsonl")}
    from statute_twins.generator.render import question
    for it in items:
        for rung in ("R5a", "R3"):
            pid = f"{it['id']}/{rung}/conv"
            if it["text"] + question(d, "de", rung, "conv") != old[pid]["user"]:
                raise SystemExit(f"{pid}: re-rendered prompt differs from the released file")
    rows = []
    for it in items:
        for rung in NEW_RUNGS:
            rows.append(dict(prompt_id=f"{it['id']}/{rung}/conv", item_id=it["id"], lang="de", rung=rung, framing="conv",
                             user=it["text"] + question_a22(d, "de", rung, "conv"), **candidates(d, "de", "conv")))
    wjl(EVAL / "prompts_ctrl2_core_de.jsonl", rows)
    ex = {r: next(x["user"] for x in rows if x["rung"] == r) for r in NEW_RUNGS}
    print(f"ctrl2_core_de: {len(rows)} prompts; prompt length (chars) of the first item:",
          {r: len(u) for r, u in ex.items()})
    # 2. verdict-only preference mirror
    for lang in ("de", "fr", "it"):
        out = []
        for r in jl(ds / f"prompts_pref_core_{lang}.jsonl"):
            side = r["chosen_side"]
            other = "acquit" if side == "convict" else "convict"
            out.append(dict(prompt_id=r["prompt_id"].replace("/pref", "/prefv"), item_id=r["item_id"], lang=lang,
                            rung="R0", framing="prefv", user=r["user"], answer_prefix="",
                            **{side: r[side], other: flip_verdict(lang, r[side])}, chosen_side=side))
        wjl(EVAL / f"prompts_prefv_core_{lang}.jsonl", out)
        print(f"prefv_core_{lang}: {len(out)} prompts")


# ------------------------------------------------------------------------------------------------------------ report

def items_by_id():
    from statute_twins.qc.checks import load_items
    return {i["id"]: i for i in load_items(ROOT / "dataset")}


def mcnemar_exact(b: int, c: int) -> float:
    """Two-sided exact McNemar p-value: 2 * P(X <= min(b, c)), X ~ Bin(b + c, 1/2), capped at 1."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n)


def pref_table(items, rows):
    from statute_twins.analysis.results import preference
    rows = [dict(r, framing="pref") for r in rows]
    out = {}
    for c in preference(items, rows):
        out[c["reason"]] = dict(n=c["n"], correct=round(c["accuracy"] * c["n"]), accuracy=round(c["accuracy"], 4),
                                ci=[round(x, 4) for x in c["accuracy_ci"]],
                                per_token=round(c["per_token_accuracy"], 4), per_token_ci=[round(x, 4) for x in c["per_token_ci"]])
    return out


def cmd_report(a):
    from controls import by_reason, cell_stats
    items = items_by_id()
    res = json.loads((ROOT / "results/results.json").read_text())["runs"]
    out = dict(note="A22, exploratory (post hoc, after review): verdict-only preference mirror and R5a ablations; 70B via "
                    "Public AI (gateway name swiss-ai/apertus-v1.5-8b), exact forced choice; settled items",
               preference_verdict_only={}, r5a_ablations={})
    # 1. preference
    for lang, run in (("de", "publicai-70b-pref"), ("fr", "publicai-70b-pref-fr"), ("it", "publicai-70b-pref-it")):
        new_rows = jl(A22 / f"publicai-70b-prefv-{lang}.jsonl")
        new_rows = [r for r in new_rows if "error" not in r]
        old_rows = jl(ROOT / "dataset/responses" / f"{run}.jsonl")
        new, old = pref_table(list(items.values()), new_rows), pref_table(list(items.values()), old_rows)
        stored = {c["reason"]: c for c in res[run]["preference"]}
        assert all(abs(old[k]["accuracy"] - stored[k]["accuracy"]) < 1e-4 for k in old), "re-scored minimal mirror != results.json"
        # the chosen continuation is the same request in both runs: its log-probability must agree
        lp_old = {r["item_id"]: r for r in old_rows}
        same_chosen = sum(abs((r["lp_convict"] if r["chosen_side"] == "convict" else r["lp_acquit"]) -
                              (lp_old[r["item_id"]]["lp_convict"] if r["chosen_side"] == "convict" else lp_old[r["item_id"]]["lp_acquit"])) < 1e-6
                          for r in [dict(x, chosen_side=items[x["item_id"]]["gold_verdict"]) for x in new_rows])
        # per item: which mirror loses
        both = defaultdict(int)
        for r in new_rows:
            i = items[r["item_id"]]
            ch = i["gold_verdict"]
            ot = "acquit" if ch == "convict" else "convict"
            o = lp_old[r["item_id"]]
            k = (("v" if r[f"lp_{ch}"] > r[f"lp_{ot}"] else "-") + ("m" if o[f"lp_{ch}"] > o[f"lp_{ot}"] else "-"))
            both[k] += 1
        out["preference_verdict_only"][lang] = dict(
            run=f"publicai-70b-prefv-{lang}", rows=len(new_rows), chosen_logprob_identical_to_released=same_chosen,
            by_reason={lab: dict(verdict_only=new.get(k), minimal_released=old.get(k)) for k, lab in REASONS},
            per_item_cross={"chosen beats both mirrors": both["vm"], "beats verdict-only only": both["v-"],
                            "beats minimal only": both["-m"], "beats neither": both["--"]})
    # 2. R5a ablations
    rows = [r for r in jl(A22 / "publicai-70b-r5a-ablation-de.jsonl") if "error" not in r and r.get("lo_conv") is not None]
    settled = {k for k, i in items.items() if i["label"] == "settled"}
    cells = defaultdict(dict)
    for r in rows:
        if r["item_id"] in settled:
            cells[r["rung"]][r["item_id"]] = r["lo_conv"]
    a13 = defaultdict(dict)
    for r in jl(ROOT / "runs_a13/publicai-70b-r5x-de.jsonl"):
        if "error" not in r and r.get("lo_conv") is not None and r["item_id"] in settled and r["framing"] == "conv":
            a13[r["rung"]][r["item_id"]] = r["lo_conv"]
    ref75 = set(a13["R5a"]) & set(a13["R5e"])            # the same_items of reports/controls_a13.json
    acq75 = sorted(i for i in ref75 if items[i]["gold_verdict"] == "acquit")
    rep = {}
    common = set(cells.get("R5a", {})) & set(a13["R5a"])
    r5a_match = sum(abs(cells["R5a"][i] - a13["R5a"][i]) < 1e-6 for i in common)
    for rung in NEW_RUNGS:
        sc = cells.get(rung)
        if not sc:
            continue
        rec = dict(sampled=cell_stats(items, sc), acquit_by_reason=by_reason(items, sc))
        rec["sampled"].pop("auc", None)
        same = {i: v for i, v in sc.items() if i in ref75}
        rec["same_items"] = cell_stats(items, same)
        rec["same_items"].pop("auc", None)
        # exact McNemar against R5a on the 75 acquittal items
        b = sum((sc[i] <= 0) and not (cells["R5a"][i] <= 0) for i in acq75 if i in sc)
        c = sum((cells["R5a"][i] <= 0) and not (sc[i] <= 0) for i in acq75 if i in sc)
        rec["vs_R5a_on_75"] = dict(only_variant_acquits=b, only_R5a_acquits=c, p_exact=round(mcnemar_exact(b, c), 4))
        rep[rung] = rec
    out["r5a_ablations"] = dict(
        definitions={"R5a": "R3's rules after the verbatim law (A13, re-sent)",
                     "R5ab": "R5a without the Regeste's closing example (consid. 6)",
                     "R5ac": "R5a with R1's element-check instruction after the law, before R3's rules",
                     "R5ag": "R3's rules before the law; R1's element-check instruction after the law",
                     "R5ad": "R5a with Art. 1 StGB before Art. 2"},
        sample_items=len(cells.get("R5a", {})), same_items_n=len(ref75), same_items_acquit_n=len(acq75),
        r5a_rows_identical_to_a13=f"{r5a_match}/{len(common)}",
        a13_reference_same_items={r: dict(acquit=f"{s['acquit_correct']}/{s['acquit_n']}", convict=f"{s['convict_correct']}/{s['convict_n']}")
                                  for r in ("R3", "R5", "R5a", "R5b", "R5c", "R5d", "R5e")
                                  for s in [next(f["same_items"] for f in json.loads((ROOT / "reports/controls_a13.json").read_text())["factorial"]
                                                 if (f["lang"], f["rung"], f["framing"]) == ("de", r, "conv"))]},
        cells=rep)
    _out("reports/controls_a22.json", json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps(out, ensure_ascii=False, indent=1))


# ------------------------------------------------------------------------------------------------------------ stats

B = 2000


def pct(reps):
    """Same percentile convention as statute_twins.analysis.stats."""
    reps = sorted(reps)
    b = len(reps)
    return (float(reps[int(math.floor(0.025 * b))]), float(reps[min(b - 1, int(math.ceil(0.975 * b)) - 1)]))


def group_of(items, iid):
    i = items[iid]
    return f"{i['lang']}|{i.get('twin_group') or iid}"


def cluster_edit_cis(los, groups, rng, np, cluster=True):
    """Percentile CIs of mean(v), mean(ref) for pairs; resampling twin groups (cluster) or pairs (items)."""
    v = np.array([x for x, _ in los], float)
    r = np.array([y for _, y in los], float)
    if cluster:
        ug = sorted(set(groups))
        gi = np.array([ug.index(g) for g in groups])
        G = len(ug)
        sv, sr, n = np.bincount(gi, v, G), np.bincount(gi, r, G), np.bincount(gi, None, G)
        idx = rng.integers(0, G, size=(B, G))
        cnt = np.zeros((B, G))
        np.add.at(cnt, (np.repeat(np.arange(B), G), idx.ravel()), 1)
        tot = cnt @ n
        mv, mr = (cnt @ sv) / tot, (cnt @ sr) / tot
    else:
        N = len(v)
        idx = rng.integers(0, N, size=(B, N))
        mv, mr = v[idx].mean(1), r[idx].mean(1)
    return pct(mv), pct(mr)


def cluster_rate_ci(decs, groups, np):
    """Wilson interval on a design-effect-adjusted sample size (decision-only rows), mapped to rate - 0.5."""
    from statute_twins.analysis.stats import wilson
    y = np.array([d == "convict" for d in decs], float)
    n = len(y)
    p = y.mean()
    ug = sorted(set(groups))
    if p in (0.0, 1.0) or len(ug) < 2:
        deff = 1.0
    else:
        gi = np.array([ug.index(g) for g in groups])
        res = np.bincount(gi, y - p, len(ug))
        var_cl = (res ** 2).sum() / n ** 2 * len(ug) / (len(ug) - 1)
        deff = max(1.0, var_cl / (p * (1 - p) / n))
    ne = n / deff
    lo, hi = wilson(round(p * ne), max(1, round(ne)))
    return (lo - 0.5, hi - 0.5)


def colour_check(items, np):
    from statute_twins.analysis import results as R
    from statute_twins.cli import released_runs
    stored = json.loads((ROOT / "results/results.json").read_text())["runs"]
    pairs = R.core_pairs(list(items.values()))
    pairs.update(R.legacy_pairs(list(items.values())))
    out = {}
    tot = dict(cells=0, cluster_changed=0, item_np_changed=0)
    for run in released_runs(ROOT / "dataset"):
        if run not in stored or not stored[run]["colours"]:
            continue
        rows = jl(ROOT / "dataset/responses" / f"{run}.jsonl")
        rx = R.index(rows)
        rungs = sorted({r["rung"] for r in rx.values()})
        rec_c, rec_i = [], []
        for (lang, name, subset), prs in sorted(pairs.items()):
            kind = "placebo" if name.startswith("placebo") else ("contested" if name.startswith("contested") else "flip")
            if kind != "flip":
                continue
            for rung in rungs:
                for fr in R.FRAMINGS:
                    vr = [(rx.get(f"{v}/{rung}/{fr}"), rx.get(f"{r}/{rung}/{fr}"), v) for v, r in prs]
                    vr = [(a, b, v) for a, b, v in vr if a is not None and b is not None]
                    if not vr:
                        continue
                    groups = [group_of(items, v) for _, _, v in vr]
                    los = [(R.lo_or_none(a), R.lo_or_none(b)) for a, b, _ in vr]
                    base = dict(lang=lang, subset=subset, edit=name, kind=kind, rung=rung, framing=fr)
                    if all(x is not None and y is not None for x, y in los):
                        civ, cir = cluster_edit_cis(los, groups, np.random.default_rng(0), np, cluster=True)
                        iv, ir = cluster_edit_cis(los, groups, np.random.default_rng(0), np, cluster=False)
                    else:
                        civ = cluster_rate_ci([R.decision(a) for a, _, _ in vr], groups, np)
                        cir = cluster_rate_ci([R.decision(b) for _, b, _ in vr], groups, np)
                        iv, ir = R._rate_ci([R.decision(a) for a, _, _ in vr])[0], R._rate_ci([R.decision(b) for _, b, _ in vr])[0]
                    rec_c.append(dict(base, status=R._status(kind, civ, cir), n=len(vr), groups=len(set(groups))))
                    rec_i.append(dict(base, status=R._status(kind, iv, ir)))
        old = {(c["subset"], c["lang"], c["edit"], c["rung"]): c for c in stored[run]["colours"]}
        changes, changes_i = [], []
        for new, lst in ((R.colours(rec_c), changes), (R.colours(rec_i), changes_i)):
            for c in new:
                o = old.get((c["subset"], c["lang"], c["edit"], c["rung"]))
                if o and o["colour"] != c["colour"]:
                    lst.append(dict(subset=c["subset"], lang=c["lang"], edit=c["edit"], rung=c["rung"], stored=o["colour"],
                                    new=c["colour"], stored_cells=o["cells"], new_cells=c["cells"]))
        multi = sum(r["n"] > r["groups"] for r in rec_c)
        out[run] = dict(cells=len(old), cluster_changed=len(changes), item_bootstrap_numpy_changed=len(changes_i),
                        edit_cells_with_several_pairs_per_group=multi, changes=changes, item_bootstrap_changes=changes_i)
        tot["cells"] += len(old)
        tot["cluster_changed"] += len(changes)
        tot["item_np_changed"] += len(changes_i)
    return dict(note="Colour per (subset, lang, edit, rung) recomputed with 95% percentile intervals from a bootstrap over "
                     "twin groups (B=2000, numpy seed 0; a group's pairs enter together, means are pair-weighted). "
                     "Decision-only runs: Wilson interval on a design-effect-adjusted n. Control: the same code "
                     "resampling pairs (the original item bootstrap, different random stream) shows how many changes "
                     "Monte Carlo noise alone produces.", total=tot, runs=out)


def wilson_rec(k, n):
    from statute_twins.analysis.stats import wilson
    lo, hi = wilson(k, n)
    return dict(k=k, n=n, rate=round(k / n, 4), ci=[round(lo, 4), round(hi, 4)])


def wilson_table(items):
    c13 = json.loads((ROOT / "reports/controls_a13.json").read_text())
    fac = {(f["lang"], f["rung"], f["framing"]): f for f in c13["factorial"]}
    out = {}
    for r in ("R3", "R5", "R5a", "R5e"):
        s = fac[("de", r, "conv")]["same_items"]
        out[f"de {r} acquittals, same 75 items"] = wilson_rec(s["acquit_correct"], s["acquit_n"])
        out[f"de {r} convictions, same items"] = wilson_rec(s["convict_correct"], s["convict_n"])
    dg = json.loads((ROOT / "reports/dignity.json").read_text())
    for c in dg["cells"]:
        if c["rung"] in ("R0", "R5"):
            out[f"dignity criticism convicted {c['lang']} {c['rung']} {c['framing']}"] = wilson_rec(c["criticism"]["convicted"], c["criticism"]["n"])
    pa = json.loads((ROOT / "reports/paraphrase.json").read_text())
    for rung in ("R0", "R3", "R5"):
        cs = [c for c in pa["cells"] if c["rung"] == rung and c["framing"] == "conv"]
        out[f"paraphrase acquittals {rung} conv (DE+FR+IT, para_{rung.lower()})"] = wilson_rec(
            sum(c["para_acquit_ok"] for c in cs), sum(c["para_acquit_n"] for c in cs))
        out[f"original-wording acquittals {rung} conv (same items)"] = wilson_rec(
            sum(c["orig_acquit_ok"] for c in cs), sum(c["orig_acquit_n"] for c in cs))
    for run, lang in (("publicai-70b-open", "de"), ("publicai-70b-open-fr", "fr"), ("publicai-70b-open-it", "it")):
        J = json.loads((ROOT / f"reports/open_judged_{run}.json").read_text())
        for rung in ("R0", "R3", "R5"):
            c = J["cells"][f"rung_gold|{rung}|acquit"]
            out[f"free text misleading {lang} {rung} (acquittal items)"] = wilson_rec(c["misleads"], c["n"])
    return out


def mcnemar_r5a_r5e(items):
    lo = defaultdict(dict)
    for r in jl(ROOT / "runs_a13/publicai-70b-r5x-de.jsonl"):
        if "error" not in r and r.get("lo_conv") is not None and r["framing"] == "conv" and items[r["item_id"]]["label"] == "settled":
            lo[r["rung"]][r["item_id"]] = r["lo_conv"]
    same = sorted(set(lo["R5a"]) & set(lo["R5e"]))
    out = {}
    for name, ids in (("acquittal items (75)", [i for i in same if items[i]["gold_verdict"] == "acquit"]),
                      ("convict items", [i for i in same if items[i]["gold_verdict"] == "convict"])):
        ok = lambda rung, i: (lo[rung][i] > 0) == (items[i]["gold_verdict"] == "convict")
        both = sum(ok("R5a", i) and ok("R5e", i) for i in ids)
        b = sum(ok("R5e", i) and not ok("R5a", i) for i in ids)
        c = sum(ok("R5a", i) and not ok("R5e", i) for i in ids)
        out[name] = dict(n=len(ids), R5a_correct=both + c, R5e_correct=both + b, both_correct=both,
                         only_R5e_correct=b, only_R5a_correct=c, neither=len(ids) - both - b - c,
                         p_exact_two_sided=mcnemar_exact(b, c))
    return out


def heldout_boot(items, np):
    from statute_twins.analysis import heldout as H
    from statute_twins.cli import released_runs
    stored = json.loads((ROOT / "results/results.json").read_text())["runs"]
    allitems = list(items.values())
    out = []
    for run in released_runs(ROOT / "dataset"):
        hs = stored.get(run, {}).get("heldout") or {}
        cells = [c for l in hs.values() for c in l["cells"] if c["rung"] in ("R3", "R4")]
        if not cells:
            continue
        rows = jl(ROOT / "dataset/responses" / f"{run}.jsonl")
        for cell in cells:
            lang, rung, fr = cell["lang"], cell["rung"], cell["framing"]
            dec = {}
            for r in rows:
                if "error" in r or r.get("lang") != lang or r.get("framing") != fr or r.get("rung") != rung:
                    continue
                d = ("convict" if r["lo_conv"] > 0 else "acquit") if r.get("lo_conv") is not None else r.get("decision")
                if d in ("convict", "acquit"):
                    dec[r["item_id"]] = d
            core = [i for i in allitems if i["subset"] != "battery162" and i["lang"] == lang and i["label"] == "settled"]
            fit_i = [i for i in core if i["split"] == "fit"]
            held = [i for i in core if i["split"] == "heldout" and i["id"] in dec]
            law = H.fit(fit_i, dec)
            g_rb = sum(H.predict(i, law) == dec[i["id"]] for i in held) / len(held)
            g_st = sum(i["gold_verdict"] == dec[i["id"]] for i in held) / len(held)
            assert abs((g_rb - g_st) - cell["gain"]) < 1e-5, (run, lang, rung, fr)
            byg = defaultdict(list)
            for i in core:
                byg[i["twin_group"]].append(i)
            gs = sorted(byg)
            rng = np.random.default_rng(0)
            reps_full, reps_fixed = [], []
            # fixed fit: per-group held-out sums, so the second bootstrap is vectorised
            okrb = {i["id"]: H.predict(i, law) == dec[i["id"]] for i in held}
            for _ in range(B):
                pick = [gs[k] for k in rng.integers(0, len(gs), len(gs))]
                its = [i for g in pick for i in byg[g]]
                fi = [i for i in its if i["split"] == "fit"]
                he = [i for i in its if i["split"] == "heldout" and i["id"] in dec]
                if not he:
                    continue
                lw = H.fit(fi, dec)
                st = sum(i["gold_verdict"] == dec[i["id"]] for i in he) / len(he)
                reps_full.append(sum(H.predict(i, lw) == dec[i["id"]] for i in he) / len(he) - st)
                reps_fixed.append(sum(okrb[i["id"]] for i in he) / len(he) - st)
            gain = g_rb - g_st
            mx = 1 - g_st
            out.append(dict(run=run, lang=lang, rung=rung, framing=fr, anchored=cell["anchored"], n_heldout=len(held),
                            readback_accuracy=round(g_rb, 4), statute_accuracy=round(g_st, 4), gain=round(gain, 4),
                            ci_twin_group_refit=[round(x, 4) for x in pct(reps_full)],
                            ci_twin_group_fit_fixed=[round(x, 4) for x in pct(reps_fixed)],
                            max_gain=round(mx, 4), gain_share_of_max=round(gain / mx, 4) if mx > 0 else None,
                            passes_015=gain >= 0.15, ci_lower_above_015=pct(reps_full)[0] >= 0.15))
    return dict(note="Twin-group bootstrap (B=2000, numpy seed 0) over the settled core items of the language: groups are "
                     "resampled, the read-back is re-fitted on the resampled fit split and scored on the resampled held-out "
                     "split (ci_twin_group_refit); ci_twin_group_fit_fixed keeps the fitted law and resamples only the "
                     "held-out groups. max_gain = 1 - statute_accuracy.", cells=out)


def reversed_by_element():
    c13 = json.loads((ROOT / "reports/controls_a13.json").read_text())
    out = {}
    for c in c13["cells"]:
        if c["rung"] == "R3" and c["framing"] == "rev":
            out[c["lang"]] = dict(reversed_question=c["acquit_by_reason"])
    for p in c13["polarity"]:
        if p["rung"] == "R3":
            out.setdefault(p["lang"], {})["polarity_averaged"] = p["averaged_by_reason"]
    return out


def conv_r3_by_element(items):
    from controls import by_reason
    out = {}
    for lang, run in (("de", "publicai-70b-fc-core"), ("fr", "publicai-70b-fc-core-fr"), ("it", "publicai-70b-fc-core-it")):
        sc = {r["item_id"]: r["lo_conv"] for r in jl(ROOT / "dataset/responses" / f"{run}.jsonl")
              if "error" not in r and r.get("rung") == "R3" and r.get("framing") == "conv" and r.get("lo_conv") is not None
              and items[r["item_id"]]["label"] == "settled" and items[r["item_id"]]["subset"] != "battery162"}
        out[lang] = by_reason(items, sc)
    return out


def cmd_stats(_a):
    import numpy as np
    items = items_by_id()
    import hashlib
    out = dict(note="A22 statistics, from stored responses only (no model calls)")
    # the inputs this was computed from (other files are edited in parallel; a later change shows up as a hash mismatch)
    ins = ["reports/controls_a13.json", "reports/dignity.json", "reports/paraphrase.json", "results/results.json",
           "runs_a13/publicai-70b-r5x-de.jsonl"] + [f"reports/open_judged_{r}.json" for r in
                                                     ("publicai-70b-open", "publicai-70b-open-fr", "publicai-70b-open-it")]
    out["inputs_sha256"] = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in ins}
    out["wilson"] = wilson_table(items)
    out["mcnemar_R5a_vs_R5e"] = mcnemar_r5a_r5e(items)
    out["reversed_question_R3_by_element"] = reversed_by_element()
    out["original_question_R3_by_element"] = conv_r3_by_element(items)
    out["heldout_gain_bootstrap"] = heldout_boot(items, np)
    out["colour_cluster_bootstrap"] = colour_check(items, np)
    _out("reports/stats_a22.json", json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print("wrote reports/stats_a22.json")


CHECK = "--check" in sys.argv


def _out(rel: str, text: str):
    """Write a report, or with --check compare it with the stored one (selfcheck step 2j)."""
    path = ROOT / rel
    if CHECK:
        same = path.exists() and path.read_text(encoding="utf-8") == text
        print(f"{rel}: " + ("matches the stored responses" if same else "STALE"))
        if not same:
            sys.exit(1)
        return
    path.write_text(text, encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, f in (("build", cmd_build), ("report", cmd_report), ("stats", cmd_stats)):
        sp = sub.add_parser(name)
        sp.add_argument("--check", action="store_true", help="compare with the stored report instead of writing")
        sp.set_defaults(f=f)
    a = ap.parse_args()
    a.f(a)


if __name__ == "__main__":
    main()
