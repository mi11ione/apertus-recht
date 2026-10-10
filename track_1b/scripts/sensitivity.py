"""Sensitivity of the headline accuracies to the one doctrinal choice a reviewer questioned: an act published online
before 1 July 2020 that may still be accessible afterwards. We follow the view that the offence is complete on
publication (gold: acquit, sexual orientation not yet covered); this script recomputes accuracy without those items
(10 DATE_SO true flips per language) and writes reports/sensitivity.json.

    python scripts/sensitivity.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from statute_twins.analysis.results import accuracy  # noqa: E402
from statute_twins.qc.checks import load_items  # noqa: E402

ONLINE = {"pub_post", "pub_post_fam", "pub_video", "pub_video_fam", "pub_forum", "pub_forum_fam"}


def questioned(i: dict) -> bool:
    return (i["subset"] != "battery162" and i["slots"].get("setting") in ONLINE
            and i["facts"]["act_date"] < "2020-07-01" and i.get("gold_reason") == "characteristic:not_yet_covered")


def main():
    items = load_items(ROOT / "dataset")
    flagged = sorted(i["id"] for i in items if questioned(i))
    keep = [i for i in items if not questioned(i)]
    released = [r for r in json.loads((ROOT / "dataset/MANIFEST.json").read_text())["files"]
                if r.startswith("responses/") and r.endswith(".jsonl")]
    out = dict(flagged=flagged, n_flagged=len(flagged), runs={})
    for f in released:
        rows = [json.loads(l) for l in (ROOT / "dataset" / f).read_text(encoding="utf-8").splitlines() if l.strip()]
        if not any(r.get("framing") in ("conv", "ver") for r in rows):
            continue
        a = {(c["lang"], c["rung"], c["framing"]): c for c in accuracy(items, rows) if c["subset"] == "core"}
        b = {(c["lang"], c["rung"], c["framing"]): c for c in accuracy(keep, rows) if c["subset"] == "core"}
        out["runs"][Path(f).stem] = [dict(lang=k[0], rung=k[1], framing=k[2], accuracy=a[k]["accuracy"],
                                          accuracy_without=b[k]["accuracy"], diff=b[k]["accuracy"] - a[k]["accuracy"])
                                     for k in sorted(a) if k in b]
    out["max_abs_diff"] = max((abs(c["diff"]) for v in out["runs"].values() for c in v), default=0.0)
    (ROOT / "reports" / "sensitivity.json").write_text(json.dumps(out, indent=1) + "\n")
    print(len(flagged), "items flagged; max |Δ accuracy| =", round(out["max_abs_diff"], 4))


if __name__ == "__main__":
    main()
