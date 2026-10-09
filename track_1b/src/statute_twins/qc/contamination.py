"""Contamination and exposure scan against voilaj/swiss-caselaw (listed in the Apertus v1.5 training data).

For every released item we take all word 13-grams of the scenario text and of the reference answers, and look for them
in the full text of every decision in the corpus (all 121 data/*.parquet files, including GE, VD and BVGer, which the
exploration scan skipped). A matching 13-gram is classed as
  * statute-derived  if it also occurs in the pinned statute texts, the BGE 130 IV 111 Regeste or our prompt rungs
                     (those phrases are supposed to be known: they are the law), or
  * scenario         otherwise (a fact pattern or answer phrasing of ours that a model could have memorised).
The same pass counts exposure (decisions mentioning BGE 130 IV 111 and Art. 261bis) and collects the decisions that
mention both as court-validation candidates. Decision texts are kept only in the local work directory; the report and
the repository store decision ids, never quotes.

    python -m statute_twins.qc.contamination --dataset dataset --statute statutes/stgb_261bis \
        --revision <sha> --workdir /tmp/caselaw --out reports/contamination.json --workers 4
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import re
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

N = 13
TOK = re.compile(r"\w+", re.UNICODE)
P130 = re.compile(r"130[\s ]*IV[\s ]*111(?!\d)")
P261 = re.compile(r"261[\s ]*bis", re.I)
COLS = ["decision_id", "court", "canton", "language", "decision_date", "docket_number", "full_text", "regeste", "outcome", "title"]


def toks(s: str) -> list[str]:
    return TOK.findall(s.lower())


def grams(s: str, n: int = N) -> set[tuple]:
    t = toks(s)
    return {tuple(t[i:i + n]) for i in range(len(t) - n + 1)}


def item_grams(dataset: Path) -> dict[tuple, set[str]]:
    from .checks import load_items
    out: dict[tuple, set[str]] = collections.defaultdict(set)
    for i in load_items(dataset):
        for f in ("text", "chosen", "rejected"):
            for g in grams(i[f]):
                out[g].add(i["id"])
    return out


def reference_grams(statute_dir: Path, dataset: Path) -> set[tuple]:
    """13-grams of the law itself: pinned statute paragraphs, BGE Regeste, and every prompt rung string."""
    from ..generator import design, render
    d = design.load(statute_dir)
    ref: set[tuple] = set()
    for k, v in d.statute.sources.items():
        if "file" not in v:
            continue
        for lang in (v.get("text_sha256") or {"de": None}):
            rec = json.loads(d.statute.source_file(k, lang).read_text(encoding="utf-8"))
            for p in rec.get("paragraphs", []):
                ref |= grams(p)
            for t in (rec.get("regeste") or {}).values():
                ref |= grams(t)
    for lang in d.langs:
        for r in render.RUNGS:
            for f in render.FRAMINGS:
                ref |= grams(render.question(d, lang, r, f))
    return ref


def _scan_file(args) -> dict:
    fname, revision, workdir, tri, gram_keys, cand_dir = args
    import pyarrow.parquet as pq
    from huggingface_hub import hf_hub_download
    t0 = time.time()
    for attempt in range(5):
        try:
            p = hf_hub_download("voilaj/swiss-caselaw", fname, repo_type="dataset", revision=revision, local_dir=workdir)
            break
        except Exception:
            if attempt == 4:
                raise
            time.sleep(10 * (attempt + 1))
    res = dict(file=fname, rows=0, tokens=0, docs_130=0, docs_261=0, docs_both=0, by_lang=collections.Counter(),
               hits=collections.defaultdict(set), candidates=[])
    cand_path = Path(cand_dir) / (fname.replace("/", "__") + ".jsonl")
    pf = pq.ParquetFile(p)
    cols = [c for c in COLS if c in pf.schema_arrow.names]
    with open(cand_path, "w", encoding="utf-8") as cf:
        for batch in pf.iter_batches(batch_size=1000, columns=cols):
            for r in batch.to_pylist():
                res["rows"] += 1
                txt = (r.get("full_text") or "") + "\n" + (r.get("regeste") or "")
                h130, h261 = bool(P130.search(txt)), bool(P261.search(txt))
                res["docs_130"] += h130
                res["docs_261"] += h261
                if h130 and h261:
                    res["docs_both"] += 1
                    res["by_lang"][r.get("language") or "?"] += 1
                if h261:
                    rec = {k: r.get(k) for k in cols}
                    rec["mentions_130_IV_111"] = h130
                    cf.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    res["candidates"].append(r["decision_id"])
                tt = TOK.findall(txt.lower())
                res["tokens"] += len(tt)
                for i in range(len(tt) - N + 1):
                    if (tt[i], tt[i + 1], tt[i + 2]) in tri:
                        g = tuple(tt[i:i + N])
                        if g in gram_keys:
                            res["hits"][g].add(r["decision_id"])
    os.remove(p)
    res["secs"] = round(time.time() - t0, 1)
    res["hits"] = {" ".join(g): sorted(v)[:20] + ([f"+{len(v) - 20} more"] if len(v) > 20 else []) for g, v in res["hits"].items()}
    res["by_lang"] = dict(res["by_lang"])
    return res


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="dataset"); ap.add_argument("--statute", default="statutes/stgb_261bis")
    ap.add_argument("--revision", required=True); ap.add_argument("--workdir", required=True)
    ap.add_argument("--out", default="reports/contamination.json"); ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--limit-files", type=int, default=None)
    a = ap.parse_args(argv)
    from huggingface_hub import HfApi
    info = HfApi().dataset_info("voilaj/swiss-caselaw", revision=a.revision, files_metadata=True)
    files = sorted(((s.rfilename, s.size or 0) for s in info.siblings
                    if s.rfilename.startswith("data/") and s.rfilename.endswith(".parquet")), key=lambda x: -x[1])
    if a.limit_files:
        files = files[-a.limit_files:]
    ig = item_grams(Path(a.dataset))
    ref = reference_grams(Path(a.statute), Path(a.dataset))
    tri = {g[:3] for g in ig}
    work = Path(a.workdir)
    cand_dir = work / "candidates"
    cand_dir.mkdir(parents=True, exist_ok=True)
    keys = set(ig)
    print(f"{len(files)} files, {sum(s for _, s in files) / 1e9:.2f} GB; {len(keys)} item 13-grams ({len(keys & ref)} statute-derived)", flush=True)
    results = []
    with ProcessPoolExecutor(a.workers) as ex:
        futs = [ex.submit(_scan_file, (f, a.revision, str(work), tri, keys, str(cand_dir))) for f, _ in files]
        for fu in as_completed(futs):
            r = fu.result()
            results.append(r)
            print(f"{r['file']}: {r['rows']} rows, {len(r['hits'])} matching 13-grams, {r['secs']}s", flush=True)
    hits: dict[str, set] = collections.defaultdict(set)
    for r in results:
        for g, ids in r["hits"].items():
            hits[g].update(ids)
    rows = []
    for g, dec in sorted(hits.items()):
        gt = tuple(g.split())
        rows.append(dict(ngram=g, kind="statute-derived" if gt in ref else "scenario", decisions=sorted(dec)[:10],
                         n_decisions=len(dec), n_items=len(ig[gt])))
    scen = [r for r in rows if r["kind"] == "scenario"]
    items_hit = sorted({i for r in scen for i in ig[tuple(r["ngram"].split())]})
    rep = dict(corpus="voilaj/swiss-caselaw", revision=a.revision, files=len(results),
               rows=sum(r["rows"] for r in results), tokens=sum(r["tokens"] for r in results),
               n=N, item_ngrams=len(keys), item_ngrams_statute_derived=len(keys & ref),
               matching_ngrams=len(rows), matching_statute_derived=len(rows) - len(scen), matching_scenario=len(scen),
               items_with_scenario_match=len(items_hit), items_with_scenario_match_ids=items_hit[:50],
               exposure=dict(docs_bge_130_IV_111=sum(r["docs_130"] for r in results),
                             docs_261bis=sum(r["docs_261"] for r in results),
                             docs_both=sum(r["docs_both"] for r in results),
                             docs_both_by_language=dict(sum((collections.Counter(r["by_lang"]) for r in results), collections.Counter()))),
               matches=rows, per_file=[{k: r[k] for k in ("file", "rows", "tokens", "docs_130", "docs_261", "docs_both", "secs")}
                                       for r in sorted(results, key=lambda r: r["file"])],
               finished=time.strftime("%Y-%m-%d %H:%M"))
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(rep, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("CONTAMINATION_DONE", json.dumps({k: rep[k] for k in ("rows", "matching_ngrams", "matching_scenario", "items_with_scenario_match")}), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
