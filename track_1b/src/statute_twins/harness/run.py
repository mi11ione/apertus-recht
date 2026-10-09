"""Run a backend over prompt rows with a resumable, hash-keyed response file.

    responses/<run_id>.jsonl        one row per scored prompt (append-only; resumable)
    responses/<run_id>.meta.json    backend identity, dataset hash, selection, counts, sha256 of the jsonl

Each row carries ``request_sha256`` (backend identity + exact prompt + candidates + parameters). Re-running skips rows
whose key is already present, so an interrupted run resumes and an unchanged prompt is never paid for twice. Replaying
a run checks that every stored key still equals the key of the prompt the current dataset produces.
"""
from __future__ import annotations

import hashlib
import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .backends.base import Backend, request_key


def stable_sample(rows: list[dict], n: int, key: str = "prompt_id", salt: str = "statute-twins") -> list[dict]:
    """Deterministic, order-independent sample: the n rows with the smallest sha256(salt + key)."""
    if n is None or n >= len(rows):
        return list(rows)
    return sorted(rows, key=lambda r: hashlib.sha256((salt + r[key]).encode()).hexdigest())[:n]


def read_jsonl(path: str | Path) -> list[dict]:
    p = Path(path)
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def sha256_file(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(backend: Backend, rows: list[dict], out_dir: str | Path, run_id: str, workers: int = 1, params: dict | None = None,
        meta: dict | None = None, progress_every: int = 50, stop_on_error: bool = False) -> dict:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{run_id}.jsonl"
    params = params or {}
    desc = backend.describe()
    done = {r["request_sha256"] for r in read_jsonl(path) if "error" not in r}
    todo = [(r, request_key(desc, r, params)) for r in rows]
    todo = [(r, k) for r, k in todo if k not in done]
    lock = threading.Lock()
    stats = dict(scored=0, errors=0, skipped=len(rows) - len(todo))
    t0 = time.time()

    def work(job):
        r, k = job
        try:
            s = backend.score(r)
            rec = dict(prompt_id=r["prompt_id"], item_id=r["item_id"], lang=r["lang"], rung=r["rung"], framing=r["framing"],
                       run=run_id, method=s.method, served_model=s.served_model, fingerprint=s.fingerprint,
                       lp_convict=s.lp_convict, lp_acquit=s.lp_acquit, lo_conv=s.lo_conv, decision=s.decided(),
                       text=s.text, extra=s.extra, request_sha256=k, ts=round(time.time(), 1))
            err = None
        except Exception as e:                      # recorded, never silently dropped
            rec = dict(prompt_id=r["prompt_id"], item_id=r["item_id"], run=run_id, request_sha256=k,
                       error=f"{type(e).__name__}: {e}"[:400], ts=round(time.time(), 1))
            err = e
        with lock:
            with open(path, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            stats["errors" if err else "scored"] += 1
            n = stats["scored"] + stats["errors"]
            if progress_every and n % progress_every == 0:
                print(f"[{run_id}] {n}/{len(todo)} scored, {stats['errors']} errors, {time.time() - t0:.0f}s", flush=True)
        if err and stop_on_error:
            raise err

    if workers <= 1:
        for j in todo:
            work(j)
    else:
        with ThreadPoolExecutor(workers) as ex:
            list(ex.map(work, todo))
    finalize(out_dir, run_id, desc, params, meta)
    stats["secs"] = round(time.time() - t0, 1)
    return stats


def finalize(out_dir: Path, run_id: str, desc: dict, params: dict, meta: dict | None) -> dict:
    """Deduplicate (last good row per prompt wins), sort, and write the meta file."""
    path = Path(out_dir) / f"{run_id}.jsonl"
    rows = read_jsonl(path)
    best: dict = {}
    for r in rows:
        if "error" in r and r["prompt_id"] in best and "error" not in best[r["prompt_id"]]:
            continue
        best[r["prompt_id"]] = r
    rows = sorted(best.values(), key=lambda r: r["prompt_id"])
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    m = dict(run=run_id, backend=desc, params=params, rows=len(rows), errors=sum("error" in r for r in rows),
             served_models=sorted({r.get("served_model") for r in rows if r.get("served_model")}),
             jsonl_sha256=sha256_file(path), **(meta or {}))
    (Path(out_dir) / f"{run_id}.meta.json").write_text(json.dumps(m, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return m
