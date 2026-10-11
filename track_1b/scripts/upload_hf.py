"""Publish dataset/ to the Hugging Face Hub as a public dataset (CDLA-Permissive-2.0).

    python scripts/upload_hf.py --repo <user>/apertus-recht [--private] --i-have-approval

Refuses to run unless: every QC gate passes (for Art. 261bis and the second statute, Art. 179ter, in dataset/stgb_179ter) (including the PII scan over items, responses and metadata), the dataset
regenerates byte-identically from the statute files, the card renders without placeholders, and the caller passes
--i-have-approval (publishing is outward-facing). The token is read by huggingface_hub from its usual location and is
never printed.
"""
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(*cmd):
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    print(r.stdout.strip()[-800:])
    if r.returncode:
        print(r.stderr.strip()[-800:])
        sys.exit(f"gate failed: {' '.join(cmd)}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True); ap.add_argument("--private", action="store_true")
    ap.add_argument("--i-have-approval", action="store_true")
    a = ap.parse_args()
    if not a.i_have_approval:
        sys.exit("publishing needs explicit approval: pass --i-have-approval")
    run(sys.executable, "-m", "statute_twins.cli", "verify")
    run(sys.executable, "-m", "statute_twins.cli", "qc", "--out", "reports/qc.json")
    # the second statute released next to the main one: the same two gates, its own QC report
    run(sys.executable, "-m", "statute_twins.cli", "verify", "--statute", "statutes/stgb_179ter", "--dataset", "dataset/stgb_179ter")
    run(sys.executable, "-m", "statute_twins.cli", "qc", "--statute", "statutes/stgb_179ter", "--dataset", "dataset/stgb_179ter",
        "--out", "reports/qc_179ter.json")
    run(sys.executable, "scripts/render_datacard.py")
    import json
    from huggingface_hub import HfApi
    # exactly the files in the manifest (released runs only) plus the card and the manifest itself
    allow = sorted(json.loads((ROOT / "dataset/MANIFEST.json").read_text())["files"]) + ["README.md", "MANIFEST.json"]
    m2 = ROOT / "dataset/stgb_179ter/MANIFEST.json"
    if m2.exists():
        allow += sorted(f"stgb_179ter/{f}" for f in json.loads(m2.read_text())["files"]) + ["stgb_179ter/MANIFEST.json"]
    # the natural-paraphrase split (A16): verified items, prompts and responses; scanned for personal data first
    para = ROOT / "dataset/paraphrase"
    if para.exists():
        sys.path.insert(0, str(ROOT / "src"))
        from statute_twins.qc.checks import check_pii
        rows = [json.loads(l) for f in sorted(para.glob("eval/paraphrase_*.jsonl")) for l in f.read_text().splitlines()]
        resp = [json.loads(l) for f in sorted(para.glob("responses/*.jsonl")) for l in f.read_text().splitlines()]
        name, ok, info = check_pii(rows, resp)
        if not ok:
            sys.exit(f"paraphrase split: personal data found: {info['hits'][:5]}")
        allow += sorted(str(f.relative_to(ROOT / "dataset")) for f in para.rglob("*") if f.is_file())
    # the dignity family (A18): its own items, prompts and responses, scanned like the paraphrases
    dign = ROOT / "dataset/dignity"
    if dign.exists():
        from statute_twins.qc.checks import check_pii
        rows = [json.loads(l) for f in sorted(dign.glob("eval/*.jsonl")) if not f.name.startswith("prompts_")
                for l in f.read_text().splitlines()]
        resp = [json.loads(l) for f in sorted(dign.glob("responses/*.jsonl")) for l in f.read_text().splitlines()]
        name, ok, info = check_pii(rows, resp)
        if not ok:
            sys.exit(f"dignity family: personal data found: {info['hits'][:5]}")
        allow += sorted(str(f.relative_to(ROOT / "dataset")) for f in dign.rglob("*") if f.is_file())
    api = HfApi()
    api.create_repo(a.repo, repo_type="dataset", private=a.private, exist_ok=True)
    api.upload_folder(repo_id=a.repo, repo_type="dataset", folder_path=str(ROOT / "dataset"),
                      commit_message="Apertus-Recht v1.0: Art. 261bis minimal-twin set, Art. 179ter set, responses, metadata",
                      allow_patterns=allow)
    print(f"published https://huggingface.co/datasets/{a.repo}")


if __name__ == "__main__":
    main()
