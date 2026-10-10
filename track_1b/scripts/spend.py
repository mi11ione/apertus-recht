"""Summarise the gateway ledger (Public AI spend) for this release into reports/spend.json.

    python scripts/spend.py [--ledger ~/.config/hackapertus/ledger.jsonl]

Counts the tags of the Track 1B runs (prefix `1b-`); the ledger holds tag, model, token counts and USD per request,
nothing else. Requests answered from the gateway's content cache are not in the ledger and cost nothing.
"""
import argparse
import collections
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

ap = argparse.ArgumentParser()
ap.add_argument("--ledger", default=str(Path.home() / ".config/hackapertus/ledger.jsonl"))
a = ap.parse_args()
by = collections.defaultdict(lambda: dict(requests=0, prompt_tokens=0, completion_tokens=0, usd=0.0))
for line in Path(a.ledger).read_text().splitlines():
    r = json.loads(line)
    if not r.get("tag", "").startswith("1b-"):
        continue
    c = by[r["tag"]]
    c["requests"] += 1
    c["prompt_tokens"] += r.get("pt", 0)
    c["completion_tokens"] += r.get("ct", 0)
    c["usd"] += r.get("usd", 0.0)
total = dict(requests=sum(c["requests"] for c in by.values()), usd=round(sum(c["usd"] for c in by.values()), 2))
rep = dict(source="gateway ledger, tags 1b-*", by_tag={k: dict(v, usd=round(v["usd"], 3)) for k, v in sorted(by.items())},
           total=total, usd_text=f"USD {total['usd']:.2f}")
(ROOT / "reports" / "spend.json").write_text(json.dumps(rep, indent=1) + "\n")
print(json.dumps(total))
