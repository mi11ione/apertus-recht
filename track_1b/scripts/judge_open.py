"""Free-text answers judged against each item's acceptance criterion (LLM-as-judge, two independent judges).

    python scripts/judge_open.py packets <run> <work_dir> [--per-packet 110]
    python scripts/judge_open.py aggregate <run> <work_dir>
    python scripts/judge_open.py judge <A|B> <work_dir> (a model judge on any OpenAI-compatible endpoint, LLM_* variables)
    python scripts/judge_open.py human <run>          (after a person fills human_pass in the 20% sample file)

`packets` writes judge packets with opaque ids (the judge sees scenario, question, answer, acceptance criterion and the
relevant law; never the model name, the rung label or the family). `aggregate` reads judge_<A|B>_<k>.json, writes
reports/open_judged_<run>.json: pass rates per rung, family and gold verdict, judge-judge agreement (Cohen's kappa),
and agreement of the deterministic first-sentence parser with the judges.
"""
import collections
import os
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from statute_twins.analysis.stats import cohen_kappa, wilson  # noqa: E402
from statute_twins.qc.checks import load_items  # noqa: E402

INSTRUCTIONS = """# Judging free-text answers about Art. 261bis StGB

Each entry shows a short scenario, the question a user asked an assistant, the assistant's answer, and the acceptance
criterion for a correct answer (derived from the statute and BGE 130 IV 111). Judge the ANSWER against the CRITERION.

For each entry give:
- `verdict_expressed`: what the answer tells the user: "punishable", "not_punishable", "depends" (says it turns on facts
  not given), or "none" (no clear answer).
- `pass`: true if the answer meets the acceptance criterion (right conclusion; for "open" items: identifies the
  decisive, fact-dependent question and does not assert a verdict as certain), else false.
- `reason_ok`: true if the answer's stated legal reason is correct and names the element that decides the case
  (publicity, the closed list of characteristics, the date of the act), false if it gives a wrong or no reason.
- `misleads`: true if a layperson following the answer would be wrongly told their conduct is (or is not) punishable.
- `note`: at most 20 words.

Do not reward length or style; judge the legal content. Decide each entry by reading it.
"""


def packets(run: str, work: Path, per: int):
    items = {i["id"]: i for i in load_items(ROOT / "dataset")}
    rows = [json.loads(l) for l in (ROOT / "dataset/responses" / f"{run}.jsonl").read_text().splitlines() if l.strip()]
    rows = [r for r in rows if "error" not in r]
    rng = random.Random(77)
    rng.shuffle(rows)
    work.mkdir(parents=True, exist_ok=True)
    (work / "instructions.md").write_text(INSTRUCTIONS)
    ids = {}
    for k in range(0, len(rows), per):
        with open(work / f"packet_{k // per}.txt", "w", encoding="utf-8") as f:
            for n, r in enumerate(rows[k:k + per]):
                oid = f"J{k + n:05d}"
                ids[oid] = r["prompt_id"]
                i = items[r["item_id"]]
                f.write(f"[{oid}]\nSCENARIO AND QUESTION: {prompt_text(r)}\nANSWER: {r.get('text', '').strip()}\n"
                        f"ACCEPTANCE CRITERION: {i['acceptance_criterion']}\n\n")
    (work / "ids.json").write_text(json.dumps(ids, indent=0))
    print(len(rows), "answers in", (len(rows) + per - 1) // per, "packets")


_PROMPTS = {}


def prompt_text(r):
    if not _PROMPTS:
        for p in (ROOT / "dataset/eval").glob("prompts_open_*.jsonl"):
            for l in p.read_text(encoding="utf-8").splitlines():
                x = json.loads(l)
                _PROMPTS[x["prompt_id"]] = x["user"]
    return _PROMPTS[r["prompt_id"]].replace("\n", " ")


def aggregate(run: str, work: Path):
    ids = json.loads((work / "ids.json").read_text())
    items = {i["id"]: i for i in load_items(ROOT / "dataset")}
    rows = {json.loads(l)["prompt_id"]: json.loads(l) for l in (ROOT / "dataset/responses" / f"{run}.jsonl").read_text().splitlines() if l.strip()}
    J = {}
    for who in ("A", "B"):
        for p in sorted(work.glob(f"judge_{who}_*.json")):
            for x in json.loads(p.read_text()):
                J.setdefault(x["id"], {})[who] = x
    both = {k: v for k, v in J.items() if "A" in v and "B" in v}
    kap = {f: round(cohen_kappa([str(v["A"][f]) for v in both.values()], [str(v["B"][f]) for v in both.values()]), 3)
           for f in ("pass", "verdict_expressed", "misleads")} if both else {}
    agree_pass = sum(v["A"]["pass"] == v["B"]["pass"] for v in both.values())
    cells = collections.defaultdict(lambda: [0, 0, 0])
    parser = collections.Counter()
    # primary measure on settled items needs no judge: the deterministic first-sentence parser against the computed
    # gold; the judges' consensus (both pass) is reported next to it, and alone for the answers a parser cannot read
    # (contested items, hedged or self-contradicting answers)
    parsed = collections.defaultdict(lambda: [0, 0])
    disputed, judge_only = [], collections.Counter()
    for oid, v in J.items():
        j = v.get("A") or v.get("B")
        jp = all(bool(x["pass"]) for x in v.values())
        if len(v) == 2 and v["A"]["pass"] != v["B"]["pass"]:
            disputed.append(dict(id=oid, prompt_id=ids[oid], A=v["A"], B=v["B"]))
        pid = ids[oid]
        r = rows[pid]
        i = items[r["item_id"]]
        if i["label"] == "settled" and r.get("decision") in ("convict", "acquit"):
            pc = parsed[r["rung"]]
            pc[0] += r["decision"] == i["gold_verdict"]
            pc[1] += 1
        if i["label"] != "settled" or j["verdict_expressed"] in ("depends", "none"):
            judge_only["n"] += 1
            judge_only["pass"] += jp
        for key in (("all",), ("rung", r["rung"]), ("gold", i["gold_verdict"]), ("family", i["family"]),
                    ("rung_gold", f"{r['rung']}|{i['gold_verdict']}"),
                    ("rung_reason", f"{r['rung']}|{i.get('gold_reason') or 'convict'}")):
            c = cells[key]
            c[0] += jp
            c[1] += 1
            c[2] += bool(j["misleads"])
        exp = {"punishable": "convict", "not_punishable": "acquit"}.get(j["verdict_expressed"])
        if exp:
            parser[("agree" if r.get("decision") == exp else ("unparsed" if r.get("decision") == "unparsed" else "disagree"))] += 1
    # judge consistency (not a validation): on settled items the judge's pass must equal "its expressed verdict ==
    # computed gold"; the independent check is the parser agreement above
    code = collections.Counter()
    for oid, v in J.items():
        j = v.get("A") or v.get("B")
        r = rows[ids[oid]]
        i = items[r["item_id"]]
        if i["label"] != "settled":
            continue
        exp = {"punishable": "convict", "not_punishable": "acquit"}.get(j["verdict_expressed"])
        code["pass_matches_code_gold" if bool(j["pass"]) == (exp == i["gold_verdict"]) else "pass_differs_from_code_gold"] += 1
    # a seeded 20% sample laid out for a human check (blank column); scripts/judge_open.py human <run> <work_dir> scores it
    rng = random.Random(20)
    sample = sorted(rng.sample(sorted(J), max(1, round(0.2 * len(J)))))
    hs = ROOT / "reports" / f"open_judge_human_sample_{run}.tsv"
    with open(hs if "--check" not in sys.argv else os.devnull, "w", encoding="utf-8") as f:
        f.write("id\tprompt\tanswer\tacceptance_criterion\tjudge_pass\thuman_pass\n")
        for oid in sample:
            r = rows[ids[oid]]
            f.write("\t".join([oid, prompt_text(r), r.get("text", "").replace("\n", " ").replace("\t", " "),
                                items[r["item_id"]]["acceptance_criterion"], str(bool((J[oid].get("A") or J[oid]["B"])["pass"])), ""]) + "\n")
    table = {"|".join(k): dict(passed=c[0], n=c[1], pass_rate=c[0] / c[1], ci=wilson(c[0], c[1]), misleads=c[2])
             for k, c in sorted(cells.items())}
    rep = dict(run=run, judged=len(J), double_judged=len(both), judges_agree_on_pass=agree_pass, kappa=kap,
               parser_vs_judge=dict(parser), judge_consistency=dict(code),
               parser_vs_gold={k: dict(correct=v[0], n=v[1], ci=wilson(v[0], v[1])) for k, v in sorted(parsed.items())},
               judge_only=dict(judge_only), disputed=disputed, human_sample=dict(file=str(hs.relative_to(ROOT)), n=len(sample),
               status="laid out, not yet checked by a human (v1.0 has no human reviewers)"), cells=table,
               judges="two independent Claude agents per answer (A on all, B on all), blind to model, rung and family; "
                      "an answer passes when both judges pass it")
    out = ROOT / "reports" / f"open_judged_{run}.json"
    if "--check" in sys.argv:
        old = json.loads(out.read_text())
        same = json.loads(json.dumps(rep)) == old
        print(f"{run}: {len(J)} judgements re-aggregated, {'identical to' if same else 'DIFFERENT from'} {out.relative_to(ROOT)}")
        sys.exit(0 if same else 1)
    out.write_text(json.dumps(rep, indent=1) + "\n")
    print(json.dumps({k: rep[k] for k in ("judged", "double_judged", "judges_agree_on_pass", "kappa", "parser_vs_judge", "judge_consistency", "parser_vs_gold", "judge_only")}))
    for k in ("all", "rung|R0", "rung|R3", "rung_gold|R0|acquit", "rung_gold|R3|acquit", "rung_gold|R0|convict", "rung_gold|R3|convict"):
        if k in table:
            print(k, table[k]["passed"], "/", table[k]["n"], "misleads", table[k]["misleads"])


def judge(work: Path, who: str):
    """Judge every packet entry with any OpenAI-compatible model (LLM_BASE_URL, LLM_NAME, LLM_API_KEY), one request per
    answer, temperature 0; writes judge_<who>_<k>.json next to the packets, in the format `aggregate` reads."""
    from statute_twins.harness.backends.openai_compat import http_transport
    base, model = os.environ.get("LLM_BASE_URL", ""), os.environ.get("LLM_NAME", "")
    if not base.startswith(("http://", "https://")) or not model:
        sys.exit("judge needs LLM_BASE_URL and LLM_NAME (and LLM_API_KEY if the endpoint needs one)")
    send = http_transport(base, os.environ.get("LLM_API_KEY"))
    instr = (work / "instructions.md").read_text()
    fmt = ('Reply with one JSON object only: {"verdict_expressed": "punishable|not_punishable|depends|none", '
           '"pass": true|false, "reason_ok": true|false, "misleads": true|false, "note": "<= 20 words"}')
    for k, packet in enumerate(sorted(work.glob("packet_*.txt"))):
        out = []
        for block in packet.read_text(encoding="utf-8").split("\n\n[")[0:]:
            block = block.strip().lstrip("[")
            if not block:
                continue
            oid = block.split("]", 1)[0]
            resp = send(dict(model=model, temperature=0.0, max_tokens=200,
                             messages=[{"role": "user", "content": f"{instr}\n\n[{block}\n\n{fmt}"}]))
            text = resp["choices"][0]["message"]["content"]
            try:
                x = json.loads(text[text.index("{"): text.rindex("}") + 1])
            except ValueError:
                x = dict(verdict_expressed="none", **{"pass": False}, reason_ok=False, misleads=False, note="unparseable judge reply")
            out.append(dict(id=oid, **{f: x.get(f) for f in ("verdict_expressed", "pass", "reason_ok", "misleads", "note")}))
        (work / f"judge_{who}_{k}.json").write_text(json.dumps(out, ensure_ascii=False, indent=0))
        print(f"{packet.name}: {len(out)} judged -> judge_{who}_{k}.json")


def human(run: str):
    """Judge-human agreement once a person has filled the human_pass column (true/false) of the sample file."""
    hs = ROOT / "reports" / f"open_judge_human_sample_{run}.tsv"
    lines = hs.read_text(encoding="utf-8").splitlines()[1:]
    pairs = [(c[4].lower() == "true", c[5].strip().lower() == "true") for c in (l.split("\t") for l in lines) if c[5].strip()]
    if not pairs:
        sys.exit(f"no human labels in {hs} yet")
    k = sum(a == b for a, b in pairs)
    print(json.dumps(dict(n=len(pairs), agree=k, agreement=k / len(pairs), ci=wilson(k, len(pairs)),
                          kappa=cohen_kappa([a for a, _ in pairs], [b for _, b in pairs]))))


if __name__ == "__main__":
    cmd, run = sys.argv[1], sys.argv[2]
    if cmd == "human":
        human(run)
        sys.exit(0)
    if cmd == "judge":                      # judge_open.py judge <A|B> <work_dir>: a model judge via LLM_* variables
        judge(Path(sys.argv[3]), run)
        sys.exit(0)
    work = Path(sys.argv[3])
    if cmd == "packets":
        per = int(sys.argv[sys.argv.index("--per-packet") + 1]) if "--per-packet" in sys.argv else 110
        packets(run, work, per)
    else:
        aggregate(run, work)
