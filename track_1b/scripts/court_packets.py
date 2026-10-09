"""Build triage/extraction packets for the court validation (prereg/PREREG_court.md) from the decisions the
contamination scan collected locally (decision texts never enter the repository).

    python scripts/court_packets.py <candidates_dir> <out_dir> [--n 150] [--per-packet 25]

Order (pre-registered): decisions citing BGE 130 IV 111 first, then the rest by sha256(decision_id). Each packet
entry is an excerpt: the header, every passage around an Art. 261bis mention (±900 characters, merged), and the end of
the decision (where the operative part usually is).
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

P261 = re.compile(r"261[\s ]*bis", re.I)


def excerpt(text: str, head: int = 1500, win: int = 900, tail: int = 2500, max_windows: int = 6) -> str:
    spans = []
    for m in P261.finditer(text):
        a, b = max(0, m.start() - win), min(len(text), m.end() + win)
        if spans and a <= spans[-1][1]:
            spans[-1] = (spans[-1][0], b)
        else:
            spans.append((a, b))
    parts = [text[:head]]
    for a, b in spans[:max_windows]:
        if b > head:
            parts.append(text[max(a, head):b])
    if len(text) > head:
        parts.append(text[-tail:])
    return "\n[…]\n".join(re.sub(r"\s+", " ", p).strip() for p in parts)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("candidates"); ap.add_argument("out")
    ap.add_argument("--n", type=int, default=150); ap.add_argument("--per-packet", type=int, default=25)
    a = ap.parse_args()
    rows = {}
    for p in sorted(Path(a.candidates).glob("*.jsonl")):
        for l in p.read_text(encoding="utf-8").split("\n"):
            if not l.strip():
                continue
            r = json.loads(l)
            rows[r["decision_id"]] = r
    order = sorted(rows.values(), key=lambda r: (not r["mentions_130_IV_111"], hashlib.sha256(r["decision_id"].encode()).hexdigest()))
    chosen = order[: a.n]
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    index = []
    for k in range(0, len(chosen), a.per_packet):
        batch = chosen[k:k + a.per_packet]
        with open(out / f"court_packet_{k // a.per_packet}.txt", "w", encoding="utf-8") as f:
            for r in batch:
                f.write(f"=== DECISION {r['decision_id']} | court {r['court']} | lang {r['language']} | date {r['decision_date']} "
                        f"| docket {r['docket_number']}\n{excerpt(r['full_text'] or '')}\n\n")
        index += [dict(decision_id=r["decision_id"], packet=k // a.per_packet, court=r["court"], language=r["language"],
                       date=r["decision_date"], docket=r["docket_number"], cites_bge_130_IV_111=r["mentions_130_IV_111"])
                  for r in batch]
    (out / "index.json").write_text(json.dumps(dict(pool=len(rows), pool_citing_bge=sum(r["mentions_130_IV_111"] for r in rows.values()),
                                                   chosen=index), indent=1, ensure_ascii=False))
    print(len(rows), "in pool;", len(chosen), "in", (len(chosen) + a.per_packet - 1) // a.per_packet, "packets")


if __name__ == "__main__":
    main()
