"""Gold checked by a model of another family: the law-only blind annotation, re-run with any OpenAI-compatible model.

    LLM_BASE_URL=gateway LLM_NAME=aisingapore/Qwen-SEA-LION-v4-32B-IT ANNOT_WORKERS=6 \
        python scripts/annotate_model.py label  [--tag qwen]     # writes review/annotation/raw_model/<tag>.json
    python scripts/annotate_model.py agree [--tag qwen]          # writes reports/annotation_model_<tag>.json

The model sees exactly what the Claude law-only annotators saw: the task (guidelines_lawonly.md), the law in the item's
language rebuilt from the pinned sources (Art. 261bis in its versions before and since 1 July 2020 with Fedlex's
footnotes, Art. 2 StGB, the Regeste of BGE 130 IV 111) and the scenario under an opaque id; never the gold, the family,
the variant or the code. Agreement is computed against the code-computed gold on the same 960 items.
"""
import argparse
import collections
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from statute_twins.analysis.stats import cohen_kappa, wilson  # noqa: E402

ANN = ROOT / "statutes/stgb_261bis/review/annotation"
SRC = ROOT / "statutes/sources"
HEAD = {"de": ("Art. 261bis StGB, Fassung vom 1. Januar 1995 bis 30. Juni 2020", "Art. 261bis StGB, Fassung seit 1. Juli 2020",
               "Art. 2 StGB", "BGE 130 IV 111, Regeste"),
        "fr": ("Art. 261bis CP, version du 1er janvier 1995 au 30 juin 2020", "Art. 261bis CP, version depuis le 1er juillet 2020",
               "Art. 2 CP", "ATF 130 IV 111, regeste"),
        "it": ("Art. 261bis CP, versione dal 1° gennaio 1995 al 30 giugno 2020", "Art. 261bis CP, versione dal 1° luglio 2020",
               "Art. 2 CP", "DTF 130 IV 111, regesto")}


def law(lang: str) -> str:
    def art(name):
        d = json.loads((SRC / name).read_text())
        return "\n".join(d["paragraphs"]) + ("\n" + "\n".join(d.get("notes") or []) if d.get("notes") else "")
    h = HEAD[lang]
    reg = json.loads((SRC / "bge_130_IV_111.json").read_text())["regeste"][lang]
    return (f"## {h[0]}\n{art(f'eli_cc_54_757_781_799__art_261_bis__{lang}__2020-02-01.json')}\n\n"
            f"## {h[1]}\n{art(f'eli_cc_54_757_781_799__art_261_bis__{lang}__2026-10-01.json')}\n\n"
            f"## {h[2]}\n{art(f'eli_cc_54_757_781_799__art_2__{lang}__2026-10-01.json')}\n\n## {h[3]}\n{reg}")


def items() -> dict:
    out = {}
    for lang in ("de", "fr", "it"):
        for l in (ROOT / f"dataset/eval/core_{lang}.jsonl").read_text(encoding="utf-8").splitlines():
            i = json.loads(l)
            out[i["id"]] = i
    return out


FMT = ('Reply with one JSON object only: {"label": "convict|acquit|open", "deciding_element": '
       '"setting|characteristic|act_date|act|other|none", "reason": "<= 25 words"}')


def label(tag: str):
    from statute_twins.harness.backends.openai_compat import gateway_transport, http_transport
    base, model = os.environ.get("LLM_BASE_URL", ""), os.environ.get("LLM_NAME", "")
    if base == "gateway" and model:
        send = gateway_transport(f"1b-annot-{tag}", float(os.environ.get("ANNOT_CAP_USD", "2.0")))
    elif base.startswith(("http://", "https://")) and model:
        send = http_transport(base, os.environ.get("LLM_API_KEY"))
    else:
        sys.exit("needs LLM_BASE_URL and LLM_NAME (and LLM_API_KEY if the endpoint needs one)")
    task = (ANN / "guidelines_lawonly.md").read_text()
    ids = json.loads((ANN / "blind_ids_lawonly.json").read_text())
    its = items()
    laws = {lang: law(lang) for lang in ("de", "fr", "it")}

    def one(bid):
        i = its[ids[bid]]
        msg = (f"{task}\n\n# law.md\n\n{laws[i['lang']]}\n\n# Scenario [{bid}]\n\n{i['text']}\n\n{FMT}")
        import time
        for attempt in range(6):          # transient network errors (DNS, 429, timeouts) are retried with backoff
            try:
                r = send(dict(model=model, temperature=0.0, max_tokens=160, messages=[{"role": "user", "content": msg}]))
                break
            except Exception:
                if attempt == 5:
                    raise
                time.sleep(5 * 2 ** attempt)
        text = r["choices"][0]["message"]["content"]
        try:
            x = json.loads(text[text.index("{"): text.rindex("}") + 1])
        except ValueError:
            x = dict(label="unparsed", deciding_element="other", reason="unparseable reply")
        return dict(id=bid, label=x.get("label"), deciding_element=x.get("deciding_element"), reason=x.get("reason", ""))

    with ThreadPoolExecutor(max_workers=int(os.environ.get("ANNOT_WORKERS", "1"))) as ex:
        out = list(ex.map(one, sorted(ids)))
    (ANN / "raw_model").mkdir(exist_ok=True)
    (ANN / "raw_model" / f"{tag}.json").write_text(json.dumps(dict(model=model, labels=out), indent=0, ensure_ascii=False))
    print(f"{len(out)} items labelled by {model} -> raw_model/{tag}.json")


ELEMENT = {"setting": "setting", "characteristic": "characteristic", "act_date": "act_date"}


def agree(tag: str):
    raw = json.loads((ANN / "raw_model" / f"{tag}.json").read_text())
    ids = json.loads((ANN / "blind_ids_lawonly.json").read_text())
    its = items()
    settled = [(x, its[ids[x["id"]]]) for x in raw["labels"] if its[ids[x["id"]]]["label"] == "settled"]
    ok = sum(x["label"] == i["gold_verdict"] for x, i in settled)
    acq = [(x, i) for x, i in settled if i["gold_verdict"] == "acquit" and x["label"] == "acquit"]
    # sexual orientation before 1 Jul 2020 turns on the characteristic and the date together: either element counts
    want = lambda i: ({"characteristic", "act_date"} if i.get("gold_reason") == "characteristic:not_yet_covered"
                      else {(i.get("gold_reason") or "").split(":")[0]})
    el_ok = sum(x["deciding_element"] in want(i) for x, i in acq)
    by = collections.defaultdict(lambda: [0, 0])
    for x, i in settled:
        k = f"{i['lang']}|{i['gold_verdict']}"
        by[k][0] += x["label"] == i["gold_verdict"]
        by[k][1] += 1
    mis = [dict(id=ids[x["id"]], gold=i["gold_verdict"], model=x["label"], reason=x["reason"])
           for x, i in settled if x["label"] != i["gold_verdict"]]
    rep = dict(model=raw["model"], items=len(raw["labels"]), settled=len(settled), agree_with_gold=ok,
               ci=wilson(ok, len(settled)),
               kappa=round(cohen_kappa([x["label"] for x, _ in settled], [i["gold_verdict"] for _, i in settled]), 3),
               deciding_element_on_agreed_acquittals=dict(agree=el_ok, n=len(acq)),
               by_lang_gold={k: dict(agree=v[0], n=v[1]) for k, v in sorted(by.items())},
               disagreements=mis,
               note="law-only blind annotation (same task, law and items as the Claude law-only pass) by a model of "
                    "another family; disagreements are listed for adjudication, not counted as gold errors")
    out = ROOT / "reports" / f"annotation_model_{tag}.json"
    out.write_text(json.dumps(rep, indent=1, ensure_ascii=False) + "\n")
    print(json.dumps({k: rep[k] for k in ("model", "settled", "agree_with_gold", "kappa", "deciding_element_on_agreed_acquittals")}))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["label", "agree"])
    ap.add_argument("--tag", default="qwen")
    a = ap.parse_args()
    label(a.tag) if a.step == "label" else agree(a.tag)
