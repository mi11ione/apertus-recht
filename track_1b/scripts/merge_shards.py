"""Merge sharded response files (CI artifacts of .github/workflows/gguf-8b.yml) into one run in dataset/responses/.

    python scripts/merge_shards.py <artifacts_dir> <run_id>
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main(art: str, run_id: str) -> None:
    rows, metas = {}, []
    for p in sorted(Path(art).rglob("*.jsonl")):
        if not p.stem.startswith(run_id + "-s"):
            continue
        for l in p.read_text(encoding="utf-8").splitlines():
            r = json.loads(l)
            r["run"] = run_id
            rows[r["prompt_id"]] = r
        m = p.with_suffix("").with_suffix(".meta.json")
        if m.exists():
            metas.append(json.loads(m.read_text()))
    out = ROOT / "dataset" / "responses" / f"{run_id}.jsonl"
    out.write_text("".join(json.dumps(rows[k], ensure_ascii=False) + "\n" for k in sorted(rows)), encoding="utf-8")
    meta = dict(run=run_id, rows=len(rows), errors=sum("error" in r for r in rows.values()), shards=len(metas),
                backend=metas[0]["backend"] if metas else None, jsonl_sha256=hashlib.sha256(out.read_bytes()).hexdigest())
    (out.parent / f"{run_id}.meta.json").write_text(json.dumps(meta, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(meta))


if __name__ == "__main__":
    main(*sys.argv[1:3])
