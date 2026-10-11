"""The dignity element against real rulings (A20): statements Swiss courts acquitted on the Abs. 4 dignity threshold,
mixed with Abs. 4 convictions, coded blind under BGE 131 IV 23 and run through the statute model's `dignity` element.

Each case is summarised as facts only (`packet.txt`, withheld from the release since A26 as pseudonymised data on
criminal proceedings; `packet.sha256` and per-case `facts_sha256` pin it): no court, outcome, docket or legal
test). Two Claude coders (A, B) and a model of another family (C, Qwen-SEA-LION via the gateway) assign the element
value (degrading / not_degrading / borderline) from the Regeste alone; the engine maps the value to its verdict
(degrading -> convict, not_degrading -> acquit, borderline -> open) with every other element taken as the court found
it; the verdict is then compared with the court outcome in `cases.jsonl`.

    LLM_BASE_URL=gateway LLM_NAME=aisingapore/Qwen-SEA-LION-v4-32B-IT python scripts/dignity_court.py code-c
    python scripts/dignity_court.py compare          # reports/dignity_court.json
    ... compare --check                              # recompute and compare with the stored report instead
"""
import json
import os
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
DC = ROOT / "statutes/stgb_261bis/review/court/dignity_check"
VERDICT = {"degrading": "convict", "not_degrading": "acquit", "borderline": "open"}
OUTCOME = {"convicted": "convict", "acquitted": "acquit"}


def blocks() -> dict:
    text = (DC / "packet.txt").read_text(encoding="utf-8")
    parts = re.split(r"^\[(D\d+)\]\s*$", text, flags=re.M)
    return {parts[k]: parts[k + 1].strip() for k in range(1, len(parts), 2)}


def code_c():
    from statute_twins.harness.backends.openai_compat import gateway_transport, http_transport
    base, model = os.environ.get("LLM_BASE_URL", ""), os.environ.get("LLM_NAME", "")
    if base == "gateway" and model:
        send = gateway_transport("1b-dignity-court", 0.5)
    elif base.startswith(("http://", "https://")) and model:
        send = http_transport(base, os.environ.get("LLM_API_KEY"))
    else:
        sys.exit("needs LLM_BASE_URL and LLM_NAME (and LLM_API_KEY if the endpoint needs one)")
    task = (DC / "coder_instructions.md").read_text(encoding="utf-8")
    out = {}
    for bid, facts in sorted(blocks().items()):
        msg = (f"{task}\n\n# [{bid}]\n\n{facts}\n\nReply with one JSON object only: "
               '{"value": "degrading|not_degrading|borderline", "reason": "<= 40 words"}')
        for attempt in range(6):
            try:
                r = send(dict(model=model, temperature=0.0, max_tokens=200, messages=[{"role": "user", "content": msg}]))
                break
            except Exception:
                if attempt == 5:
                    raise
                time.sleep(5 * 2 ** attempt)
        text = r["choices"][0]["message"]["content"]
        try:
            x = json.loads(text[text.index("{"): text.rindex("}") + 1])
            out[bid] = x.get(bid, x) if isinstance(x.get(bid), dict) else x   # some replies nest under the block id
        except ValueError:
            out[bid] = dict(value="unparsed", reason=text[:200])
    (DC / "coder_C.json").write_text(json.dumps(dict(model=model, labels=out), indent=1, ensure_ascii=False))
    print(f"{len(out)} cases coded by {model} -> coder_C.json")


def compare():
    cases = [json.loads(l) for l in (DC / "cases.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    coders = {}
    for c in "ABC":
        p = DC / f"coder_{c}.json"
        if p.exists():
            d = json.loads(p.read_text())
            coders[c] = d.get("labels", d)
    rows, agree = [], {c: 0 for c in coders}
    for k in sorted(cases, key=lambda k: k["blind_id"]):
        court = OUTCOME[k["court_outcome"]]
        vals = {c: coders[c].get(k["blind_id"], {}).get("value") for c in coders}
        eng = {c: VERDICT.get(v, "unparsed") for c, v in vals.items()}
        for c in coders:
            agree[c] += eng[c] == court
        rows.append(dict(blind_id=k["blind_id"], decision_id=k["decision_id"], url=k.get("url"), court=court,
                         values=vals, engine=eng, note=k.get("note")))
    n = len(rows)
    pair = (sum(r["values"].get("A") == r["values"].get("B") for r in rows) if {"A", "B"} <= set(coders) else None)
    rep = dict(cases=n, acquittals=sum(r["court"] == "acquit" for r in rows),
               convictions=sum(r["court"] == "convict" for r in rows),
               agree_with_court={c: f"{agree[c]}/{n}" for c in coders},
               convictions_coded_degrading={c: sum(r["court"] == "convict" and r["values"][c] == "degrading"
                                                   for r in rows) for c in coders},
               acquittals_not_coded_degrading={c: sum(r["court"] == "acquit" and r["values"][c] != "degrading"
                                                      for r in rows) for c in coders},
               acquittals_degrading_all_coders=[r["blind_id"] for r in rows if r["court"] == "acquit"
                                                and all(v == "degrading" for v in r["values"].values())],
               acquittals_agree={c: sum(r["court"] == "acquit" and r["engine"][c] == "acquit" for r in rows) for c in coders},
               acquittals_first_instance_convicted=[r["blind_id"] for r in rows
                                                    if "first-instance court had convicted" in (r.get("note") or "")],
               not_final=[r["blind_id"] for r in rows if "not final" in (r.get("note") or "")],
               agree_with_court_final_only={c: f"{sum(r['engine'][c] == r['court'] for r in rows if 'not final' not in (r.get('note') or ''))}"
                                               f"/{sum('not final' not in (r.get('note') or '') for r in rows)}" for c in coders},
               scope=("each coding concerns a facts-only summary read under the Regeste of BGE 131 IV 23, not the persons; "
                      "the courts' acquittals stand"),
               coder_A_B_same_value=pair, models={c: (json.loads((DC / f"coder_{c}.json").read_text()).get("model")
                                                      or "claude agent") for c in coders},
               rows=rows)
    text = json.dumps(rep, indent=1, ensure_ascii=False) + "\n"
    out = ROOT / "reports/dignity_court.json"
    if "--check" in sys.argv:
        same = out.exists() and out.read_text() == text
        print("dignity court check: report " + ("matches the coder files" if same else "is STALE"))
        sys.exit(0 if same else 1)
    out.write_text(text)
    print(json.dumps({k: v for k, v in rep.items() if k != "rows"}, ensure_ascii=False))
    for r in rows:
        print(r["blind_id"], r["court"], r["values"], r["decision_id"])


if __name__ == "__main__":
    {"code-c": code_c, "compare": compare}[sys.argv[1]]()
