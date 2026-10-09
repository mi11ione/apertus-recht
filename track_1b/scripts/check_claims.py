"""CI check: every number in the README, the report and the form notes maps to a results file (claims.tsv).

claims.tsv columns (tab-separated, header row):
  id        short identifier
  value     the exact string as written in the documents (e.g. "622/648", "0.97", "15/20")
  source    JSON file the value comes from (relative to track_1b/)
  expr      Python expression over `J` (the loaded JSON) that reproduces the value (string or number)
  fmt       Python format spec applied to a numeric result ("" = str())
  used_in   comma-separated files that must contain `value` verbatim near the claim (README.md, technical_report.md, ...)
  command   the command that produced `source`
Exit 1 if any expression does not reproduce its value or a document no longer contains it.
"""
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    p = ROOT / "claims.tsv"
    rows = list(csv.DictReader(p.open(encoding="utf-8"), delimiter="\t"))
    bad = 0
    cache = {}
    for r in rows:
        src = ROOT / r["source"]
        if src not in cache:
            cache[src] = json.loads(src.read_text(encoding="utf-8"))
        got = eval(r["expr"], {"J": cache[src], "len": len, "sum": sum, "round": round, "min": min, "max": max})
        s = format(got, r["fmt"]) if r["fmt"] else str(got)
        if s != r["value"]:
            print(f"FAIL {r['id']}: claims.tsv says {r['value']!r}, {r['source']} gives {s!r}")
            bad += 1
        for doc in filter(None, (x.strip() for x in r["used_in"].split(","))):
            if r["value"] not in (ROOT / doc).read_text(encoding="utf-8"):
                print(f"FAIL {r['id']}: {doc} no longer contains {r['value']!r}")
                bad += 1
    print(f"{len(rows)} claims checked, {bad} failures")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
