"""Publish dataset/ to the Hugging Face Hub as a public dataset (CDLA-Permissive-2.0).

    python scripts/upload_hf.py --repo <user>/apertus-recht [--private] --i-have-approval

Refuses to run unless: every QC gate passes (including the PII scan over items, responses and metadata), the dataset
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
    run(sys.executable, "scripts/render_datacard.py")
    from huggingface_hub import HfApi
    api = HfApi()
    api.create_repo(a.repo, repo_type="dataset", private=a.private, exist_ok=True)
    api.upload_folder(repo_id=a.repo, repo_type="dataset", folder_path=str(ROOT / "dataset"),
                      commit_message="Apertus-Recht v1.0: Art. 261bis minimal-twin set, responses, metadata",
                      ignore_patterns=["archive/*"])
    print(f"published https://huggingface.co/datasets/{a.repo}")


if __name__ == "__main__":
    main()
