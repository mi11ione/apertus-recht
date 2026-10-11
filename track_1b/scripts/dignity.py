"""The dignity threshold of Art. 261bis Abs. 4 (A18, exploratory): the DIGNITY family, kept outside the core set.

Every other scenario stipulates the dignity threshold. Here it decides: in each twin group the same speaker, setting
and religious group appear three times, (0) degrading the believers as humans (gold convict), (1) criticising the
religion's teachings and institutions (gold acquit, BGE 131 IV 23 E. 3: unfavourable but objective criticism does
not fulfil Abs. 4), (2) a crude joke whose exact wording the facts leave open (gold open). Gold by code, as for the
core set (statute.yaml element `dignity`).

    python scripts/dignity.py build      # dataset/dignity/eval/dignity_<lang>.jsonl and prompts_dignity_<lang>.jsonl
    (score: statute-twins eval --dataset dataset/dignity --parts dignity_<lang> ...)
    python scripts/dignity.py report     # reports/dignity.json from dataset/dignity/responses
    ... --check                          # re-derive and compare with the stored files instead of writing
"""
import collections
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from statute_twins.generator import build, design  # noqa: E402

OUT = ROOT / "dataset/dignity"
LANGS = ("de", "fr", "it")
CHECK = "--check" in sys.argv
DIFFS = []


def _emit(path: Path, text: str):
    if CHECK:
        if not path.exists() or path.read_text(encoding="utf-8") != text:
            DIFFS.append(str(path.relative_to(ROOT)))
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _jsonl(rows):
    return "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)


def build_split():
    d = design.load(ROOT / "statutes/stgb_261bis")
    items = [i for i in build.build_items(d, build.build_scenarios(d)) if i["subset"] == "dignity"]
    for lang in LANGS:
        rows = [i for i in items if i["lang"] == lang]
        _emit(OUT / "eval" / f"dignity_{lang}.jsonl", _jsonl(rows))
        _emit(OUT / "eval" / f"prompts_dignity_{lang}.jsonl", _jsonl(build.build_prompts(d, rows)))
        if not CHECK:
            print(lang, len(rows), "items,", collections.Counter(i["gold_verdict"] for i in rows))
    from statute_twins.dataset import item_metadata
    _emit(OUT / "metadata" / "items.jsonl", "".join(json.dumps(item_metadata(d, i, {}), ensure_ascii=False, sort_keys=True)
                                                    + "\n" for i in items))


def report():
    from statute_twins.analysis.results import decision
    out = dict(note="A18, exploratory: the dignity threshold (BGE 131 IV 23 E. 3); 70B, exact forced choice", cells=[])
    for lang in LANGS:
        items = {json.loads(l)["id"]: json.loads(l) for l in (OUT / "eval" / f"dignity_{lang}.jsonl").read_text(encoding="utf-8").splitlines()}
        rp = OUT / "responses" / f"publicai-70b-dignity-{lang}.jsonl"
        if not rp.exists():
            continue
        c = collections.Counter()
        for r in map(json.loads, rp.read_text(encoding="utf-8").splitlines()):
            if "error" in r:
                continue
            i = items[r["item_id"]]
            k = (r["rung"], r["framing"], i["variant"])
            c[k + ("n",)] += 1
            c[k + ("convicted",)] += decision(r) == "convict"
        for rung in ("R0", "R3", "R5"):
            for fr in ("conv", "ver"):
                cell = dict(lang=lang, rung=rung, framing=fr)
                for v, name in (("base", "degrading"), ("true_flip", "criticism"), ("contested", "borderline")):
                    cell[name] = dict(convicted=c[(rung, fr, v, "convicted")], n=c[(rung, fr, v, "n")])
                if any(cell[x]["n"] for x in ("degrading", "criticism", "borderline")):
                    out["cells"].append(cell)
    _emit(ROOT / "reports/dignity.json", json.dumps(out, indent=1) + "\n")
    if not CHECK:
        for c in out["cells"]:
            print(c["lang"], c["rung"], c["framing"], "degrading convicted", f"{c['degrading']['convicted']}/{c['degrading']['n']}",
                  "| criticism convicted", f"{c['criticism']['convicted']}/{c['criticism']['n']}",
                  "| borderline convicted", f"{c['borderline']['convicted']}/{c['borderline']['n']}")


if __name__ == "__main__":
    {"build": build_split, "report": report}[sys.argv[1]]()
    if CHECK:
        print("dignity split: " + ("re-derived identically" if not DIFFS else "DIFFERS: " + ", ".join(DIFFS)))
        sys.exit(1 if DIFFS else 0)
