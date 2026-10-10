"""Free-text answers judged against each item's acceptance criterion (LLM-as-judge, two independent judges).

    statute-twins judge packets <run> <work_dir> [--per-packet 110]
    statute-twins judge aggregate <run> <work_dir>
    statute-twins judge judge <A|B> <work_dir>   (a model judge on any OpenAI-compatible endpoint, LLM_* variables)
    statute-twins judge human <run>              (after a person fills human_pass in the 20% sample file)

Paths (dataset/, reports/) are relative to the project root: the current directory, or STATUTE_TWINS_ROOT.

`packets` writes judge packets with opaque ids (the judge sees scenario, question, answer, acceptance criterion and the
relevant law; never the model name, the rung label or the family). `aggregate` reads judge_<A|B>_<k>.json, writes
reports/open_judged_<run>.json: pass rates per rung, family and gold verdict, judge-judge agreement (Cohen's kappa),
and agreement of the deterministic first-sentence parser with the judges.
"""
import collections
import hashlib
import os
import json
import random
import re
import sys
from pathlib import Path

from .analysis.stats import cohen_kappa, wilson
from .qc.checks import load_items

ROOT = Path(os.environ.get("STATUTE_TWINS_ROOT", ".")).resolve()

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
    ids, bind = {}, {}
    for k in range(0, len(rows), per):
        with open(work / f"packet_{k // per}.txt", "w", encoding="utf-8") as f:
            for n, r in enumerate(rows[k:k + per]):
                oid = f"J{k + n:05d}"
                ids[oid] = r["prompt_id"]
                bind[oid] = _binding(r)
                i = items[r["item_id"]]
                f.write(f"[{oid}]\nSCENARIO AND QUESTION: {prompt_text(r)}\nANSWER: {r.get('text', '').strip()}\n"
                        f"ACCEPTANCE CRITERION: {i['acceptance_criterion']}\n\n")
    (work / "ids.json").write_text(json.dumps(ids, indent=0))
    (work / "bindings.json").write_text(json.dumps(bind, indent=0))
    print(len(rows), "answers in", (len(rows) + per - 1) // per, "packets")


_PROMPTS = {}


def _binding(r: dict) -> dict:
    """What a judgement is bound to: the request hash of the prompt and the sha256 of the answer text it judged. Written
    with the packets (French, Italian); the German bindings were written afterwards from the judged answers (A12)."""
    return dict(request_sha256=r.get("request_sha256"), answer_sha256=hashlib.sha256(r.get("text", "").encode()).hexdigest())


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
                if x["id"] in ids:          # ids of answers that were regenerated later are retired
                    J.setdefault(x["id"], {})[who] = x
    C = {}
    for p in sorted(work.glob("judge_C_*.json")):
        for x in json.loads(p.read_text()):
            if x["id"] in ids:
                C[x["id"]] = x
    # every judgement must belong to the answer and prompt it was made on (bindings.json, written with the packets);
    # a declared exception keeps a judgement whose prompt changed while the answer stayed byte-identical
    bp = work / "bindings.json"
    binding = dict(checked=0, mismatched=[], exceptions={})
    if not bp.exists():
        # every judge folder written by `packets` has bindings; a folder without them cannot be checked
        binding["mismatched"].append("bindings.json missing")
    else:
        for oid, b in json.loads(bp.read_text()).items():
            if oid not in J or not isinstance(b, dict):      # "_note" and retired ids
                continue
            now = _binding(rows[ids[oid]])
            binding["checked"] += 1
            if now["answer_sha256"] != b["answer_sha256"]:
                binding["mismatched"].append(oid)
            elif now["request_sha256"] != b["request_sha256"]:
                if b.get("exception"):
                    binding["exceptions"][oid] = b["exception"]
                else:
                    binding["mismatched"].append(oid)
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
    cons = {k: v["A"]["pass"] for k, v in both.items() if v["A"]["pass"] == v["B"]["pass"] and k in C}
    third = None
    if cons:
        kc = sum(bool(C[k]["pass"]) == bool(p_) for k, p_ in cons.items())
        sample_ids = set(sample)
        ks = [k for k in cons if k in sample_ids]
        third = dict(judge=os.environ.get("JUDGE_C_NAME", "Qwen-SEA-LION-v4-32B-IT (another model family, via Public AI)"),
                     judged=len(C), agree_with_consensus=kc, n=len(cons), ci=wilson(kc, len(cons)),
                     kappa=round(cohen_kappa([str(bool(C[k]["pass"])) for k in cons], [str(bool(p_)) for p_ in cons.values()]), 3),
                     on_20pct_sample=dict(agree=sum(bool(C[k]["pass"]) == bool(cons[k]) for k in ks), n=len(ks),
                                          note="sampled answers on which the two Claude judges agree"))
        # by gold class: the acquit and open items carry every finding, so agreement is reported there separately
        by_gold = {}
        for g in ("convict", "acquit", "open"):
            kg = [k for k in cons if items[rows[ids[k]]["item_id"]]["gold_verdict"] == g]
            if kg:
                by_gold[g] = dict(n=len(kg), agree=sum(bool(C[k]["pass"]) == bool(cons[k]) for k in kg),
                                  consensus_pass=sum(bool(cons[k]) for k in kg), judge_c_pass=sum(bool(C[k]["pass"]) for k in kg),
                                  kappa=round(cohen_kappa([str(bool(C[k]["pass"])) for k in kg], [str(bool(cons[k])) for k in kg]), 3))
        kn = [k for k in cons if items[rows[ids[k]]["item_id"]]["gold_verdict"] != "convict"]
        by_gold["acquit_or_open"] = dict(n=len(kn), agree=sum(bool(C[k]["pass"]) == bool(cons[k]) for k in kn),
                                         consensus_pass=sum(bool(cons[k]) for k in kn), judge_c_pass=sum(bool(C[k]["pass"]) for k in kn),
                                         kappa=round(cohen_kappa([str(bool(C[k]["pass"])) for k in kn], [str(bool(cons[k])) for k in kn]), 3))
        third["by_gold"] = by_gold
        # the headline counts by this judge alone: answers to acquittal items it calls misleading, per rung
        mis = collections.Counter()
        for k, x in C.items():
            r = rows[ids[k]]
            if items[r["item_id"]]["gold_verdict"] == "acquit":
                mis[r["rung"] + "|n"] += 1
                mis[r["rung"] + "|misleads"] += bool(x["misleads"])
        third["acquit_misleads_by_rung"] = dict(sorted(mis.items()))
    # the question asks "strafbar nach Schweizer Recht", the gold is Art. 261bis: an answer that convicts under another
    # offence would not be wrong. Which article do the misleading answers to acquittal items name as their basis?
    cites = collections.defaultdict(lambda: dict(n=0, name_261bis=0, also_other_offence=0))
    for k, v in both.items():
        r = rows[ids[k]]
        if items[r["item_id"]]["gold_verdict"] == "acquit" and v["A"]["misleads"] and v["B"]["misleads"]:
            t = r.get("text", "")
            # "Art. 173", "art. 173", "Artikel", "article", "articolo"; Art. 1-3 StGB (legality, time) are not offences
            other = [o for o in re.findall(r"\bart(?:\.|ikel|icle|icolo)?\s*(\d+\s*[a-z]*)", t, flags=re.I)
                     if not o.replace(" ", "").lower().startswith("261bis") and o.strip() not in ("1", "2", "3")]
            cc = cites[r["rung"]]
            cc["n"] += 1
            cc["name_261bis"] += bool(re.search(r"261\s*bis", t, flags=re.I))
            cc["also_other_offence"] += bool(other)
    # reasoning: among answers both Claude judges pass, how many give a correct legal reason in both judges' view
    reason = collections.defaultdict(lambda: dict(passed=0, reason_ok=0))
    for k, v in both.items():
        if v["A"]["pass"] and v["B"]["pass"]:
            rr = reason[rows[ids[k]]["rung"]]
            rr["passed"] += 1
            rr["reason_ok"] += bool(v["A"].get("reason_ok")) and bool(v["B"].get("reason_ok"))
    rep = dict(run=run, judged=len(J), double_judged=len(both), judges_agree_on_pass=agree_pass, kappa=kap,
               independent_judge=third, misleading_answers_cite=dict(sorted(cites.items())),
               reason_ok_among_passes=dict(sorted(reason.items())), bindings=binding,
               parser_vs_judge=dict(parser), judge_consistency=dict(code),
               parser_vs_gold={k: dict(correct=v[0], n=v[1], ci=wilson(v[0], v[1])) for k, v in sorted(parsed.items())},
               judge_only=dict(judge_only), disputed=disputed, human_sample=dict(file=str(hs.relative_to(ROOT)), n=len(sample),
               by_gold=dict(collections.Counter(items[rows[ids[k]]["item_id"]]["gold_verdict"] for k in sample)),
               status="laid out for a human check; not yet checked (v1.0 has no human reviewers)"), cells=table,
               judges="two independent Claude agents per answer (A on all, B on all; Claude Opus 5.5, claude-opus-5-5, as "
                      "Claude Code subagents, one packet per agent, instructions.md as the prompt), blind to model, rung "
                      "and family; an answer passes when both judges pass it")
    out = ROOT / "reports" / f"open_judged_{run}.json"
    if "--check" in sys.argv:
        old = json.loads(out.read_text())
        same = json.loads(json.dumps(rep)) == old
        bad = len(binding["mismatched"])
        print(f"{run}: {len(J)} judgements re-aggregated, {'identical to' if same else 'DIFFERENT from'} {out.relative_to(ROOT)}"
              + (f"; bound to their answers: {binding['checked'] - bad}/{binding['checked']}" if binding["checked"] else ""))
        sys.exit(0 if same and not bad else 1)
    out.write_text(json.dumps(rep, indent=1) + "\n")
    print(json.dumps({k: rep[k] for k in ("judged", "double_judged", "judges_agree_on_pass", "kappa", "parser_vs_judge", "judge_consistency", "parser_vs_gold", "judge_only")}))
    for k in ("all", "rung|R0", "rung|R3", "rung_gold|R0|acquit", "rung_gold|R3|acquit", "rung_gold|R0|convict", "rung_gold|R3|convict"):
        if k in table:
            print(k, table[k]["passed"], "/", table[k]["n"], "misleads", table[k]["misleads"])


def judge(work: Path, who: str):
    """Judge every packet entry with any OpenAI-compatible model (LLM_BASE_URL, LLM_NAME, LLM_API_KEY), one request per
    answer, temperature 0; writes judge_<who>_<k>.json next to the packets, in the format `aggregate` reads."""
    from statute_twins.harness.backends.openai_compat import gateway_transport, http_transport
    base, model = os.environ.get("LLM_BASE_URL", ""), os.environ.get("LLM_NAME", "")
    if base == "gateway" and model:          # the team's cost-capped gateway (development); else any OpenAI-compatible URL
        send = gateway_transport(f"1b-judge-{who}", float(os.environ.get("JUDGE_CAP_USD", "2.0")))
    elif base.startswith(("http://", "https://")) and model:
        send = http_transport(base, os.environ.get("LLM_API_KEY"))
    else:
        sys.exit("judge needs LLM_BASE_URL and LLM_NAME (and LLM_API_KEY if the endpoint needs one)")
    instr = (work / "instructions.md").read_text()
    fmt = ('Reply with one JSON object only: {"verdict_expressed": "punishable|not_punishable|depends|none", '
           '"pass": true|false, "reason_ok": true|false, "misleads": true|false, "note": "<= 20 words"}')
    from concurrent.futures import ThreadPoolExecutor

    def one(block):
        oid = block.split("]", 1)[0]
        resp = send(dict(model=model, temperature=0.0, max_tokens=200,
                         messages=[{"role": "user", "content": f"{instr}\n\n[{block}\n\n{fmt}"}]))
        text = resp["choices"][0]["message"]["content"]
        try:
            x = json.loads(text[text.index("{"): text.rindex("}") + 1])
        except ValueError:
            x = dict(verdict_expressed="none", **{"pass": False}, reason_ok=False, misleads=False, note="unparseable judge reply")
        return dict(id=oid, **{f: x.get(f) for f in ("verdict_expressed", "pass", "reason_ok", "misleads", "note")})

    workers = int(os.environ.get("JUDGE_WORKERS", "1"))   # requests are independent; order is kept
    for k, packet in enumerate(sorted(work.glob("packet_*.txt"))):
        blocks = [b.strip().lstrip("[") for b in packet.read_text(encoding="utf-8").split("\n\n[")]
        blocks = [b for b in blocks if b]
        with ThreadPoolExecutor(max_workers=workers) as ex:
            out = list(ex.map(one, blocks))
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


def main(argv: list[str]) -> int:
    sys.argv = ["statute-twins judge", *argv]
    cmd, run = sys.argv[1], sys.argv[2]
    if cmd == "human":
        human(run)
        return 0
    if cmd == "judge":                      # judge_open.py judge <A|B> <work_dir>: a model judge via LLM_* variables
        judge(Path(sys.argv[3]), run)
        return 0
    work = Path(sys.argv[3])
    if cmd == "packets":
        per = int(sys.argv[sys.argv.index("--per-packet") + 1]) if "--per-packet" in sys.argv else 110
        packets(run, work, per)
    else:
        aggregate(run, work)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
