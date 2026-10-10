"""statute-twins command line.

    statute-twins build      --statute statutes/stgb_261bis --out dataset        write eval/ + metadata/ + MANIFEST
    statute-twins verify     --statute statutes/stgb_261bis --dataset dataset    regenerate and compare hashes (no model)
    statute-twins qc         --statute ... --dataset dataset [--out reports/qc.json]
    statute-twins eval       --backend openai|llamacpp|gateway --run-id ID [--parts core_de,battery162] [--rungs R0,R3]
                             [--framings conv,ver] [--sample N] [--model ...] [--gguf PATH --gguf-sha256 ...]
    statute-twins results    --dataset dataset --out results/results.json        recompute results from responses
    statute-twins selfcheck  --statute ... --dataset dataset --results results/results.json [--live ...]
    statute-twins new        <statute_id> [--dir statutes]                      scaffold a new statute folder
    statute-twins pin        --eli eli/cc/54/757_781_799 --eid art_261_bis --lang de --date 2026-10-09
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


def _load_jsonl(p: Path) -> list[dict]:
    return [json.loads(l) for l in Path(p).read_text(encoding="utf-8").splitlines() if l.strip()]


def _reviews(statute_dir: Path) -> dict:
    p = Path(statute_dir) / "review" / "adjudication.jsonl"
    return {r["id"]: r for r in _load_jsonl(p)} if p.exists() else {}


def cmd_build(a) -> int:
    from . import dataset, statute as statute_mod
    probs = statute_mod.verify_sources(statute_mod.load(a.statute))
    if probs:
        for p in probs:
            print("FAIL source:", p)
        print("The pinned sources do not match statute.yaml; re-pin with `statute-twins pin` and update text_sha256.")
        return 1
    counts = dataset.write_eval(Path(a.statute), Path(a.out), _reviews(a.statute))
    dataset.manifest(Path(a.out), set(a.exclude_runs.split(",")) if a.exclude_runs else None)
    print(json.dumps(counts))
    return 0


def cmd_verify(a) -> int:
    from . import dataset
    probs = dataset.verify(Path(a.statute), Path(a.dataset), _reviews(a.statute))
    for p in probs:
        print("FAIL", p)
    print("PASS dataset regenerates byte-identically from the statute files" if not probs else f"FAIL {len(probs)} problems")
    return 1 if probs else 0


def cmd_qc(a) -> int:
    from . import statute
    from .qc import checks
    rep = checks.run_all(Path(a.dataset), statute.load(a.statute))
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(json.dumps(rep, ensure_ascii=False, indent=1, default=str) + "\n", encoding="utf-8")
    for name, g in rep["gates"].items():
        print(("PASS " if g["passed"] else "FAIL ") + name)
    return 0 if rep["passed"] else 1


def _prompt_rows(ds: Path, parts: list[str], rungs: list[str], framings: list[str], sample: int | None) -> list[dict]:
    from .harness.run import stable_sample
    rows = []
    for part in parts:
        rows += _load_jsonl(ds / "eval" / f"prompts_{part}.jsonl")
    rows = [r for r in rows if r["rung"] in rungs and r["framing"] in framings]
    if sample:
        # sample whole twin groups (a base with all its variants), so the element read-back stays computable
        group = lambda iid: iid.rsplit("-", 1)[0]
        groups = sorted({group(r["item_id"]) for r in rows})
        per_group = max(1, round(len({r["item_id"] for r in rows}) / max(1, len(groups))))
        n_groups = max(1, round(sample / per_group))
        keep = {x["prompt_id"] for x in stable_sample([dict(prompt_id=g) for g in groups], n_groups)}
        rows = [r for r in rows if group(r["item_id"]) in keep]
    return rows


def make_backend(a):
    if a.backend == "llamacpp":
        from .harness.backends.llamacpp import LlamaCpp
        return LlamaCpp(a.gguf, n_ctx=a.n_ctx, n_threads=a.threads, expect_sha256=a.gguf_sha256, label=a.label)
    from .harness.backends.openai_compat import OpenAICompat, gateway_transport
    if a.backend == "gateway":
        return OpenAICompat(base_url="gateway:" + (a.model or ""), api_key="", model=a.model, mode=a.mode, seed=a.seed,
                            transport=gateway_transport(a.tag, a.cap), label=a.label, max_tokens_generate=a.max_tokens)
    return OpenAICompat(base_url=a.base_url, model=a.model, mode=a.mode, seed=a.seed, label=a.label,
                        max_tokens_generate=a.max_tokens)


def cmd_eval(a) -> int:
    from .harness import run
    ds = Path(a.dataset)
    rows = _prompt_rows(ds, a.parts.split(","), a.rungs.split(","), a.framings.split(","), a.sample)
    if a.shard:
        import hashlib
        k, n = (int(x) for x in a.shard.split("/"))
        rows = [r for r in rows if int(hashlib.sha256(r["item_id"].encode()).hexdigest(), 16) % n == k]
    rows.sort(key=lambda r: (r["item_id"], r["rung"], r["framing"]))   # consecutive prompts share prefixes
    if a.limit:
        rows = rows[: a.limit]
    be = make_backend(a)
    if a.seed_from:
        # pre-load rows of an earlier run for the selected prompts; rows whose request hash still matches are skipped,
        # so only prompts that changed (or failed) are scored again
        out_dir = Path(a.out or "runs")
        out_dir.mkdir(parents=True, exist_ok=True)
        want = {r["prompt_id"] for r in rows}
        seed = [r for r in _load_jsonl(Path(a.seed_from)) if r.get("prompt_id") in want and "error" not in r]
        with open(out_dir / f"{a.run_id}.jsonl", "a", encoding="utf-8") as f:
            for r in seed:
                f.write(json.dumps(dict(r, run=a.run_id), ensure_ascii=False) + "\n")
        print(f"[{a.run_id}] seeded {len(seed)} rows from {a.seed_from}", flush=True)
    print(f"[{a.run_id}] {len(rows)} prompts on {be.describe()}", flush=True)
    out_dir = Path(a.out or "runs")
    stats = run.run(be, rows, out_dir, a.run_id, workers=a.workers,
                    meta=dict(parts=a.parts, rungs=a.rungs, framings=a.framings, sample=a.sample, label=a.label,
                              model=a.model or a.gguf))
    done = [r for r in run.read_jsonl(out_dir / f"{a.run_id}.jsonl") if r.get("prompt_id") in {x["prompt_id"] for x in rows}]
    errors = [r for r in done if "error" in r]
    unparsed = [r for r in done if "error" not in r and r.get("decision") not in ("convict", "acquit")]
    served = sorted({r.get("served_model") for r in done if r.get("served_model")})
    print(f"[{a.run_id}] {len(done)}/{len(rows)} prompts: {len(done) - len(errors) - len(unparsed)} decided, "
          f"{len(unparsed)} unparsed, {len(errors)} errors; served by {served or 'local engine'}; "
          f"file {out_dir / (a.run_id + '.jsonl')} ({stats['secs']} s)")
    for e in errors[:3]:
        print(f"  error {e['prompt_id']}: {e['error'][:300]}")
    for u in unparsed[:3]:
        print(f"  unparsed {u['prompt_id']}: {str(u.get('text'))[:120]!r}")
    bad = (len(errors) + len(unparsed)) / max(1, len(rows))
    if bad > a.max_error_rate:
        print(f"[{a.run_id}] FAIL: {bad:.1%} of prompts errored or could not be parsed (allowed {a.max_error_rate:.1%}); "
              f"re-running the same command retries only those prompts")
        return 1
    print(f"[{a.run_id}] next: statute-twins report --run {out_dir / (a.run_id + '.jsonl')}")
    return 0


def all_items(ds: Path) -> list[dict]:
    from .qc.checks import load_items
    return load_items(ds)


def released_runs(ds: Path) -> list[str] | None:
    """The response runs listed in MANIFEST.json (a run still being written is not released yet)."""
    m = ds / "MANIFEST.json"
    if not m.exists():
        return None
    from .dataset import run_of
    return sorted({run_of(Path(f).name) for f in json.loads(m.read_text())["files"] if f.startswith("responses/")})


def compute_results(ds: Path, runs: list[str] | None = None, responses: Path | None = None) -> dict:
    from .analysis import results as R
    from .harness.run import read_jsonl
    from .analysis import compare, heldout
    items = all_items(ds)
    out = dict(schema="statute-twins-results/v1", runs={})
    loaded, metas = {}, {}
    rdir = Path(responses) if responses else ds / "responses"
    for p in sorted(rdir.glob("*.jsonl")):
        if runs and p.stem not in runs:
            continue
        rows = read_jsonl(p)
        loaded[p.stem] = rows
        meta = json.loads((rdir / f"{p.stem}.meta.json").read_text()) if (rdir / f"{p.stem}.meta.json").exists() else {}
        metas[p.stem] = meta
        res = R.run_results(items, rows)
        core_ids = {i["id"]: i["lang"] for i in items if i["subset"] != "battery162"}
        langs = sorted({core_ids[r["item_id"]] for r in rows if r.get("item_id") in core_ids})
        res["heldout"] = {l: heldout.run(items, rows, lang=l) for l in langs}
        out["runs"][p.stem] = dict(meta=meta, **res)
    out["comparisons"] = dict(reference=compare.REFERENCE, build_parity=compare.build_parity(loaded),
                              stage_trajectory=compare.stage_trajectory(items, loaded),
                              cross_language={m: compare.cross_language(items, loaded, by_lang)
                                              for m, by_lang in compare.language_groups(items, loaded, metas).items()})
    return out


def _round(o, nd=6):
    if isinstance(o, float):
        return round(o, nd) if o == o else None
    if isinstance(o, dict):
        return {k: _round(v, nd) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_round(v, nd) for v in o]
    return o


def cmd_results(a) -> int:
    # default: the released runs (this is how results/results.json is made); with --responses: every run in that folder
    if a.runs:
        runs = a.runs.split(",")
    elif a.responses:
        runs = None
    else:
        runs = released_runs(Path(a.dataset))
    if not a.out:
        a.out = str(Path(a.responses) / "results.json") if a.responses else "results/results.json"
    res = _round(compute_results(Path(a.dataset), runs, Path(a.responses) if a.responses else None))
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(res, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {a.out}: {len(res['runs'])} runs")
    return 0


def _compare(a, b, tol, path="") -> list[str]:
    """Recursive comparison with an absolute tolerance on numbers."""
    if isinstance(a, dict) and isinstance(b, dict):
        out = []
        for k in sorted(set(a) | set(b)):
            if k not in a or k not in b:
                out.append(f"{path}/{k}: missing on one side")
            else:
                out += _compare(a[k], b[k], tol, f"{path}/{k}")
        return out
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            return [f"{path}: length {len(a)} != {len(b)}"]
        out = []
        for i, (x, y) in enumerate(zip(a, b)):
            out += _compare(x, y, tol, f"{path}[{i}]")
        return out
    if isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool):
        return [] if abs(a - b) <= tol else [f"{path}: {a} != {b}"]
    return [] if a == b else [f"{path}: {a!r} != {b!r}"]


def cmd_selfcheck(a) -> int:
    """make run: (1) dataset regenerates from the statute files; (2) results recompute from the stored responses;
    (3) optional live slice against reference bands. Exit 1 on any FAIL."""
    from . import dataset
    ok = True
    print("== step 1: re-derive every item and gold label from the statute YAML (no model)")
    probs = dataset.verify(Path(a.statute), Path(a.dataset), _reviews(a.statute))
    if probs:
        ok = False
        for p in probs[:20]:
            print("  FAIL", p)
    print("  PASS" if not probs else f"  FAIL ({len(probs)} problems)")
    print("== step 2: re-score the stored responses and compare with the published results")
    stored = json.loads(Path(a.results).read_text())
    fresh = _round(compute_results(Path(a.dataset), released_runs(Path(a.dataset))))
    diffs = _compare(stored, json.loads(json.dumps(fresh)), a.tol)
    if diffs:
        ok = False
        for d in diffs[:20]:
            print("  FAIL", d)
    print("  PASS" if not diffs else f"  FAIL ({len(diffs)} differences)")
    print("== step 2b: every stored response belongs to the current prompt (request hash recomputed)")
    stale = check_request_hashes(Path(a.dataset))
    for line in stale["report"]:
        print("  " + line)
    if stale["mismatches"]:
        ok = False
    print("  PASS" if not stale["mismatches"] else f"  FAIL ({stale['mismatches']} responses do not match their prompt)")
    if a.live:
        from .harness import selfcheck_live
        print(f"== step 3: live slice ({a.live})")
        ok = selfcheck_live.run(a) and ok
    print("SELF-CHECK", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def cmd_report(a) -> int:
    from .report import main as report_main
    out = report_main(a.run, a.dataset, a.out, a.max_wrong)
    print(f"wrote {out} and {out.with_suffix('.html')}")
    return 0


def cmd_preview(a) -> int:
    """Print a few generated items as readable text: twin group, variant, verdict, derivation, reference answers."""
    from .generator import build, design
    d = design.load(Path(a.statute))
    items = build.build_items(d, build.build_scenarios(d))
    items = [i for i in items if i["lang"] == (a.lang or d.langs[0])]
    groups = []
    for i in items:
        if i["twin_group"] not in groups:
            groups.append(i["twin_group"])
    for g in groups[: a.groups]:
        print(f"== twin group {g} ({next(i['family'] for i in items if i['twin_group'] == g)})")
        for i in (x for x in items if x["twin_group"] == g):
            print(f"-- {i['id']}  {i['variant']}" + (f" (changed: {i['changed_slot']})" if i["changed_slot"] else "")
                  + f"  gold: {i['gold_verdict']}  [{i['gold_reason']}]")
            print("   " + i["text"])
            print("   derivation: " + i["rationale"])
            print("   chosen:   " + i["chosen"])
            print("   rejected: " + i["rejected"])
        print()
    return 0


def check_request_hashes(ds: Path) -> dict:
    """For every released run that records its backend, recompute each row's request hash from the current prompt."""
    from .harness.backends.base import request_key
    from .harness.run import read_jsonl
    prompts = {}
    for p in (ds / "eval").glob("prompts_*.jsonl"):
        for r in _load_jsonl(p):
            prompts[r["prompt_id"]] = r
    report, bad = [], 0
    for run in released_runs(ds) or []:
        mp = ds / "responses" / f"{run}.meta.json"
        meta = json.loads(mp.read_text()) if mp.exists() else {}
        if not isinstance(meta.get("backend"), dict):
            report.append(f"{run}: imported exploration measurement (no request hashes; each row records the sha256 of its "
                          f"source file, which is not part of this repository): replayed, not re-verified")
            continue
        n = m = 0
        for r in read_jsonl(ds / "responses" / f"{run}.jsonl"):
            if "request_sha256" not in r or r["prompt_id"] not in prompts:
                continue
            n += 1
            if request_key(meta["backend"], prompts[r["prompt_id"]], meta.get("params") or {}) != r["request_sha256"]:
                m += 1
        bad += m
        report.append(f"{run}: {n - m}/{n} rows match their prompt")
    return dict(mismatches=bad, report=report)


def cmd_new(a) -> int:
    from .scaffold import scaffold
    p = scaffold(a.statute_id, Path(a.dir))
    print(f"created {p}")
    return 0


def cmd_pin(a) -> int:
    from .sources import fedlex
    rec = fedlex.pin(a.eli, a.eid, a.lang, a.date, Path(a.out))
    print(json.dumps({k: rec[k] for k in ("applicability_date", "text_sha256", "url")}))
    return 0


def _check_paths(a) -> None:
    """Friendly error when run outside the project folder (defaults are relative to track_1b/)."""
    for attr in ("statute", "dataset"):
        v = getattr(a, attr, None)
        if v and not Path(v).exists():
            raise SystemExit(f"statute-twins: {attr} folder {v!r} not found. Run from the project folder (track_1b/) "
                             f"or pass --{attr} PATH.")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="statute-twins", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    S = "statutes/stgb_261bis"

    p = sub.add_parser("build"); p.add_argument("--statute", default=S); p.add_argument("--out", default="dataset")
    p.add_argument("--exclude-runs", default=None, help="response runs still being written (left out of the manifest)")
    p.set_defaults(f=cmd_build)
    p = sub.add_parser("verify"); p.add_argument("--statute", default=S); p.add_argument("--dataset", default="dataset"); p.set_defaults(f=cmd_verify)
    p = sub.add_parser("qc"); p.add_argument("--statute", default=S); p.add_argument("--dataset", default="dataset")
    p.add_argument("--out", default="reports/qc.json"); p.set_defaults(f=cmd_qc)

    p = sub.add_parser("eval", help="score a model on the set (resumable)")
    p.add_argument("--backend", choices=["openai", "llamacpp", "gateway"], default="openai",
                   help="openai: any OpenAI-compatible endpoint (LLM_BASE_URL/LLM_API_KEY/LLM_NAME); llamacpp: a local GGUF")
    p.add_argument("--dataset", default="dataset", help="dataset folder")
    p.add_argument("--out", default=None, help="output folder for <run-id>.jsonl (default: runs/)")
    p.add_argument("--run-id", required=True, help="name of this run (file name)"); p.add_argument("--label", default=None, help="free-text model label")
    p.add_argument("--parts", default="core_de", help="comma-separated: core_de, core_fr, core_it, battery162")
    p.add_argument("--rungs", default="R0,R3", help="comma-separated rungs R0..R4")
    p.add_argument("--framings", default="conv,ver", help="conv (Ja/Nein) and/or ver (verdict word)")
    p.add_argument("--sample", type=int, default=None, help="about N items, sampled as whole twin groups (stable)")
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--shard", default=None, help="k/n: score only items whose sha256(id) mod n == k")
    p.add_argument("--model", default=os.environ.get("LLM_NAME")); p.add_argument("--base-url", default=os.environ.get("LLM_BASE_URL"))
    p.add_argument("--mode", default="auto", choices=["auto", "exact_prefill", "top_logprobs", "generate"],
                   help="scoring method for openai backends (auto probes the endpoint once)")
    p.add_argument("--seed", type=int, default=None, help="sampling seed sent to the endpoint (fresh samples on caching providers)")
    p.add_argument("--max-tokens", type=int, default=24, help="generation length in generate mode (open questions: 250)")
    p.add_argument("--gguf", default=None); p.add_argument("--gguf-sha256", default=None); p.add_argument("--n-ctx", type=int, default=2048)
    p.add_argument("--threads", type=int, default=None)
    p.add_argument("--tag", default="1b-eval"); p.add_argument("--cap", type=float, default=1.0)
    p.add_argument("--workers", type=int, default=1, help="parallel requests")
    p.add_argument("--max-error-rate", type=float, default=0.0, help="exit 1 if more than this share of prompts errored or was unparsed")
    p.add_argument("--seed-from", default=None, help="earlier responses file; only prompts whose request changed are re-scored")
    p.set_defaults(f=cmd_eval)

    p = sub.add_parser("results", help="recompute results from response files")
    p.add_argument("--dataset", default="dataset", help="dataset folder (items)")
    p.add_argument("--responses", default=None, help="folder with <run>.jsonl files (default: <dataset>/responses)")
    p.add_argument("--out", default=None, help="default: results/results.json (released runs) or <responses>/results.json")
    p.add_argument("--runs", default=None, help="comma-separated run ids")
    p.set_defaults(f=cmd_results)

    p = sub.add_parser("selfcheck"); p.add_argument("--statute", default=S); p.add_argument("--dataset", default="dataset")
    p.add_argument("--results", default="results/results.json"); p.add_argument("--tol", type=float, default=1e-6)
    p.add_argument("--live", default=None, choices=[None, "api", "gguf"]); p.add_argument("--bands", default="results/reference_bands.json")
    p.add_argument("--live-items", type=int, default=30)
    p.set_defaults(f=cmd_selfcheck)

    p = sub.add_parser("report", help="one readable page (Markdown + HTML) for one run")
    p.add_argument("--run", required=True, help="a <run>.jsonl file written by eval"); p.add_argument("--dataset", default="dataset")
    p.add_argument("--out", default=None, help="Markdown output path (HTML is written next to it)")
    p.add_argument("--max-wrong", type=int, default=40, help="wrong decisions to list")
    p.set_defaults(f=cmd_report)
    p = sub.add_parser("preview", help="print a few generated twin groups as readable text")
    p.add_argument("--statute", default=S); p.add_argument("--lang", default=None); p.add_argument("--groups", type=int, default=3)
    p.set_defaults(f=cmd_preview)
    p = sub.add_parser("new"); p.add_argument("statute_id"); p.add_argument("--dir", default="statutes"); p.set_defaults(f=cmd_new)
    p = sub.add_parser("pin"); p.add_argument("--eli", required=True); p.add_argument("--eid", required=True)
    p.add_argument("--lang", default="de"); p.add_argument("--date", required=True); p.add_argument("--out", default="statutes/sources")
    p.set_defaults(f=cmd_pin)

    a = ap.parse_args(argv)
    if a.cmd not in ("new", "pin"):
        _check_paths(a)
    return a.f(a)


if __name__ == "__main__":
    sys.exit(main())
