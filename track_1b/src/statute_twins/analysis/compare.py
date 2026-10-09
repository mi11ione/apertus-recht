"""Cross-run comparisons on shared prompts: build parity (decision agreement, |Δ lo|) and the training-stage
trajectory of the read-back edits. Reproduces spikes/gguf/results.md (parity table) and spikes/linie9 (stage trace)."""
from __future__ import annotations

from .results import decision, edits, legacy_pairs
from .stats import mean

REFERENCE = "8b-bf16-DPO"
# the exact bf16 path from RLVR to DPO (weight blends in between); 4-bit builds are excluded because conversion, not
# training, moves several of these cells (see build_parity)
STAGES = ["8b-bf16-RLVR", "8b-bf16-blend-RLVR-DPO-a0.25", "8b-bf16-blend-RLVR-DPO-a0.5", "8b-bf16-blend-RLVR-DPO-a0.75",
          "8b-bf16-DPO"]
TRACKED = ["setting:failed", "characteristic:not_listed|canton", "characteristic:not_listed|occupation",
           "characteristic:not_yet_covered", "characteristic:not_listed|gender_identity"]


def parity(a: list[dict], b: list[dict]) -> dict:
    ia = {r["prompt_id"]: r for r in a if "error" not in r}
    ib = {r["prompt_id"]: r for r in b if "error" not in r}
    common = sorted(set(ia) & set(ib))
    agree = sum(decision(ia[p]) == decision(ib[p]) for p in common)
    d = [abs(ia[p]["lo_conv"] - ib[p]["lo_conv"]) for p in common
         if ia[p].get("lo_conv") is not None and ib[p].get("lo_conv") is not None]
    cells = {}
    for p in common:
        k = f"{p.split('/')[-1]}_{p.split('/')[-2]}"
        x = cells.setdefault(k, [0, 0])
        x[0] += decision(ia[p]) == decision(ib[p])
        x[1] += 1
    return dict(n=len(common), agree=agree, mean_abs_diff=mean(d) if d else None,
                median_abs_diff=sorted(d)[len(d) // 2] if d else None, over_2_nats=sum(x > 2 for x in d),
                cells={k: dict(agree=v[0], n=v[1]) for k, v in sorted(cells.items())})


def build_parity(runs: dict) -> dict:
    ref = runs.get(REFERENCE)
    if not ref:
        return {}
    out = {}
    for name, rows in sorted(runs.items()):
        if name != REFERENCE and "completion" not in name:
            p = parity(rows, ref)
            if p["n"]:
                out[name] = p
    return out


def stage_trajectory(items: list[dict], runs: dict) -> list[dict]:
    """Edit statistics along the bf16 RLVR -> DPO path, on the prompts every point of the path has (the blends were
    scored on an 84-item subset), so every point averages over the same items."""
    pairs = legacy_pairs(items)
    present = [n for n in STAGES if n in runs]
    if not present:
        return []
    common = set.intersection(*({r["prompt_id"] for r in runs[n] if "error" not in r} for n in present))
    out = []
    for name in present:
        rows = [r for r in runs[name] if r.get("prompt_id") in common]
        for e in edits(items, rows, pairs):
            if e["edit"] in TRACKED and e["rung"] in ("R0", "R3"):
                out.append(dict(run=name, edit=e["edit"], rung=e["rung"], framing=e["framing"], n=e["n"],
                                v_convicted=e["v_convicted"], mean_v=e.get("mean_v"), ci_v=e.get("ci_v"), status=e["status"]))
    return out


def cross_language(items: list[dict], runs: dict, run_by_lang: dict) -> dict:
    """Same facts, three languages: decision agreement between languages and whether errors fall on the same items.
    run_by_lang = {"de": run_id, "fr": run_id, "it": run_id}; items are matched by twin group + variant index."""
    from .results import decision as dec
    key = {i["id"]: (i["twin_group"], i["variant_index"]) for i in items if i["subset"] != "battery162"}
    gold = {(i["twin_group"], i["variant_index"]): i for i in items if i["subset"] != "battery162" and i["lang"] == "de"}
    per = {}
    for lang, run in run_by_lang.items():
        if run not in runs:
            continue
        for r in runs[run]:
            if "error" in r or r.get("item_id") not in key or not r["item_id"].split("-")[1] == lang:
                continue
            per[(lang, key[r["item_id"]], r["rung"], r["framing"])] = dec(r)
    langs = [l for l in run_by_lang if run_by_lang[l] in runs]
    out = dict(pairs={}, joint_errors={})
    for x in range(len(langs)):
        for y in range(x + 1, len(langs)):
            a, b = langs[x], langs[y]
            common = [k[1:] for k in per if k[0] == a and (b,) + k[1:] in per]
            agree = sum(per[(a,) + c] == per[(b,) + c] for c in common)
            out["pairs"][f"{a}-{b}"] = dict(n=len(common), agree=agree)
    # error overlap on settled items: P(error in FR | error in DE) vs P(error in FR)
    for a, b in (("de", "fr"), ("de", "it"), ("fr", "it")):
        if a not in langs or b not in langs:
            continue
        cells = [k[1:] for k in per if k[0] == a and (b,) + k[1:] in per and gold[k[1]]["label"] == "settled"]
        ea = [per[(a,) + c] != gold[c[0]]["gold_verdict"] for c in cells]
        eb = [per[(b,) + c] != gold[c[0]]["gold_verdict"] for c in cells]
        nb = sum(eb)
        both = sum(x and y for x, y in zip(ea, eb))
        out["joint_errors"][f"{a}-{b}"] = dict(n=len(cells), errors_a=sum(ea), errors_b=nb, both=both,
                                               p_b=nb / len(cells) if cells else None,
                                               p_b_given_a=both / sum(ea) if sum(ea) else None)
    return out
