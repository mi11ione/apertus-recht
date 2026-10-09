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
    from . import dataset
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
        ids = sorted({r["item_id"] for r in rows})
        keep = {x["item_id"] for x in stable_sample([dict(item_id=i, prompt_id=i) for i in ids], sample)}
        rows = [r for r in rows if r["item_id"] in keep]
    return rows


def make_backend(a):
    if a.backend == "llamacpp":
        from .harness.backends.llamacpp import LlamaCpp
        return LlamaCpp(a.gguf, n_ctx=a.n_ctx, n_threads=a.threads, expect_sha256=a.gguf_sha256, label=a.label)
    from .harness.backends.openai_compat import OpenAICompat, gateway_transport
    if a.backend == "gateway":
        return OpenAICompat(base_url="gateway:" + (a.model or ""), api_key="", model=a.model, mode=a.mode, seed=a.seed,
                            transport=gateway_transport(a.tag, a.cap), label=a.label)
    return OpenAICompat(base_url=a.base_url, model=a.model, mode=a.mode, seed=a.seed, label=a.label)


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
    print(f"[{a.run_id}] {len(rows)} prompts on {be.describe()}", flush=True)
    stats = run.run(be, rows, a.out or ds / "responses", a.run_id, workers=a.workers,
                    meta=dict(parts=a.parts, rungs=a.rungs, framings=a.framings, sample=a.sample, label=a.label,
                              model=a.model or a.gguf))
    print(json.dumps(stats))
    return 1 if stats["errors"] and a.strict else 0


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


def compute_results(ds: Path, runs: list[str] | None = None) -> dict:
    from .analysis import results as R
    from .harness.run import read_jsonl
    from .analysis import compare, heldout
    items = all_items(ds)
    out = dict(schema="statute-twins-results/v1", runs={})
    loaded = {}
    for p in sorted((ds / "responses").glob("*.jsonl")):
        if runs and p.stem not in runs:
            continue
        rows = read_jsonl(p)
        loaded[p.stem] = rows
        meta = json.loads((ds / "responses" / f"{p.stem}.meta.json").read_text()) if (ds / "responses" / f"{p.stem}.meta.json").exists() else {}
        res = R.run_results(items, rows)
        core_ids = {i["id"]: i["lang"] for i in items if i["subset"] != "battery162"}
        langs = sorted({core_ids[r["item_id"]] for r in rows if r.get("item_id") in core_ids})
        res["heldout"] = {l: heldout.run(items, rows, lang=l) for l in langs}
        out["runs"][p.stem] = dict(meta=meta, **res)
    out["comparisons"] = dict(reference=compare.REFERENCE, build_parity=compare.build_parity(loaded),
                              stage_trajectory=compare.stage_trajectory(items, loaded),
                              cross_language=compare.cross_language(items, loaded, {"de": "publicai-70b-fc-core",
                                                                                     "fr": "publicai-70b-fc-core-fr",
                                                                                     "it": "publicai-70b-fc-core-it"}))
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
    res = _round(compute_results(Path(a.dataset), a.runs.split(",") if a.runs else released_runs(Path(a.dataset))))
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
    if a.live:
        from .harness import selfcheck_live
        print(f"== step 3: live slice ({a.live})")
        ok = selfcheck_live.run(a) and ok
    print("SELF-CHECK", "PASS" if ok else "FAIL")
    return 0 if ok else 1


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

    p = sub.add_parser("eval")
    p.add_argument("--backend", choices=["openai", "llamacpp", "gateway"], default="openai")
    p.add_argument("--dataset", default="dataset"); p.add_argument("--out", default=None)
    p.add_argument("--run-id", required=True); p.add_argument("--label", default=None)
    p.add_argument("--parts", default="core_de"); p.add_argument("--rungs", default="R0,R3"); p.add_argument("--framings", default="conv,ver")
    p.add_argument("--sample", type=int, default=None, help="stable sample of N items (all chosen rungs/framings)")
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--shard", default=None, help="k/n: score only items whose sha256(id) mod n == k")
    p.add_argument("--model", default=os.environ.get("LLM_NAME")); p.add_argument("--base-url", default=os.environ.get("LLM_BASE_URL"))
    p.add_argument("--mode", default="auto", choices=["auto", "exact_prefill", "top_logprobs", "generate"])
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--gguf", default=None); p.add_argument("--gguf-sha256", default=None); p.add_argument("--n-ctx", type=int, default=2048)
    p.add_argument("--threads", type=int, default=None)
    p.add_argument("--tag", default="1b-eval"); p.add_argument("--cap", type=float, default=1.0)
    p.add_argument("--workers", type=int, default=1); p.add_argument("--strict", action="store_true")
    p.set_defaults(f=cmd_eval)

    p = sub.add_parser("results"); p.add_argument("--dataset", default="dataset"); p.add_argument("--out", default="results/results.json")
    p.add_argument("--runs", default=None); p.set_defaults(f=cmd_results)

    p = sub.add_parser("selfcheck"); p.add_argument("--statute", default=S); p.add_argument("--dataset", default="dataset")
    p.add_argument("--results", default="results/results.json"); p.add_argument("--tol", type=float, default=1e-6)
    p.add_argument("--live", default=None, choices=[None, "api", "gguf"]); p.add_argument("--bands", default="results/reference_bands.json")
    p.add_argument("--live-items", type=int, default=30)
    p.set_defaults(f=cmd_selfcheck)

    p = sub.add_parser("new"); p.add_argument("statute_id"); p.add_argument("--dir", default="statutes"); p.set_defaults(f=cmd_new)
    p = sub.add_parser("pin"); p.add_argument("--eli", required=True); p.add_argument("--eid", required=True)
    p.add_argument("--lang", default="de"); p.add_argument("--date", required=True); p.add_argument("--out", default="statutes/sources")
    p.set_defaults(f=cmd_pin)

    a = ap.parse_args(argv)
    return a.f(a)


if __name__ == "__main__":
    sys.exit(main())
