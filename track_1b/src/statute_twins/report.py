"""`statute-twins report`: one readable page for one model run, for people who will not read JSON.

    statute-twins report --run runs/my-model.jsonl [--out runs/my-model-report.md] [--max-wrong 40]

Sections: run health (errors, unparsed, served models); accuracy by language, rung and framing with Wilson intervals;
the element read-back (which legal element the model applies against the statute, per rung); the wrong decisions on
settled items with scenario, gold verdict, derivation and citation; contested items (where the model leans).
Writes Markdown and, next to it, a print-ready HTML page.
"""
from __future__ import annotations

import collections
import html
import json
from pathlib import Path

from .analysis import results as R
from .harness.run import read_jsonl
from .qc.checks import load_items

EDIT_LABEL = {
    "setting:failed": "statement only in a private setting",
    "characteristic:not_yet_covered": "sexual orientation, act before 1 Jul 2020",
    "act_date:not_in_force": "act before Art. 261bis entered into force (1995)",
    "placebo|family_wording": "public statement in family wording (placebo)",
    "placebo|synonym": "listed characteristic, other word (placebo)",
    "placebo|date_overapplied": "race / ethnicity / religion, act 2018-20 (placebo)",
    "placebo|date": "sexual orientation, 1 Jul or Aug 2020 (placebo)",
    "placebo|act": "other wording or paragraph (placebo)",
}


def _label(edit: str) -> str:
    if edit.startswith("characteristic:not_listed|"):
        return "group defined by " + edit.split("|", 1)[1].replace("_", " ")
    return EDIT_LABEL.get(edit, edit)


def build(run_path: Path, dataset: Path, max_wrong: int = 40) -> str:
    rows = read_jsonl(run_path)
    items = {i["id"]: i for i in load_items(dataset)}
    item_list = list(items.values())
    res = R.run_results(item_list, rows)
    meta_p = run_path.with_name(run_path.name.replace(".jsonl", ".meta.json"))
    meta = json.loads(meta_p.read_text()) if meta_p.exists() else {}
    errors = [r for r in rows if "error" in r]
    ok = [r for r in rows if "error" not in r]
    unparsed = [r for r in ok if R.decision(r) not in ("convict", "acquit")]
    served = collections.Counter(r.get("served_model") or "local engine" for r in ok)
    L = [f"# {run_path.stem}: Art. 261bis evaluation report", ""]
    L += ["## Run", "",
          f"- backend: `{json.dumps(meta.get('backend', {}), ensure_ascii=False)}`",
          f"- prompts: {len(rows)} ({len(ok) - len(unparsed)} decided, {len(unparsed)} unparsed, {len(errors)} errors)",
          f"- served models: " + ", ".join(f"{k} ({v})" for k, v in served.items()), ""]
    if errors or unparsed:
        L += ["> **Check before using these numbers:** "
              f"{len(errors)} prompts errored and {len(unparsed)} answers could not be parsed; they are excluded below.", ""]
    L += ["## Accuracy against the statute (settled items)", "",
          "| subset | lang | rung | framing | n | accuracy | 95% interval | convict recall | acquit recall |", "|---|---|---|---|---|---|---|---|---|"]
    for a in res["accuracy"]:
        lo, hi = a["accuracy_ci"]
        L.append(f"| {a['subset']} | {a['lang']} | {a['rung']} | {a['framing']} | {a['n']} | {a['accuracy']:.3f} | "
                 f"{lo:.3f}–{hi:.3f} | {a['recall_convict']:.2f} | {a['recall_acquit']:.2f} |")
    L += ["", "Rungs: R0 no law in the prompt; R1 elements named; R2 + publicity rule and list; R3 + closed list; "
          "R4 + 1 July 2020 clause. A model that always says 'convict' scores about 0.67.", ""]
    L += ["## Which law does the model apply? (element read-back)", "",
          "Each row changes one legal fact of a scenario the statute punishes. **red**: the model convicts where the "
          "statute acquits in every readable framing; **amber**: in one framing; **none**: it follows the statute; "
          "**unreadable**: no framing convicts the base case.", "",
          "| one fact changed | lang | rung | colour | Ja/Nein | verdict word |", "|---|---|---|---|---|---|"]
    for c in res["colours"]:
        if c["subset"] != "core":
            continue
        L.append(f"| {_label(c['edit'])} | {c['lang']} | {c['rung']} | **{c['colour']}** | {c['cells'].get('conv', '')} | "
                 f"{c['cells'].get('ver', '')} |")
    wrong = []
    for r in ok:
        i = items.get(r["item_id"])
        d = R.decision(r)
        if i and i["label"] == "settled" and d in ("convict", "acquit") and d != i["gold_verdict"]:
            wrong.append((i, r, d))
    wrong.sort(key=lambda x: (x[0]["family"], x[0]["id"], x[1]["rung"], x[1]["framing"]))
    L += ["", f"## Wrong decisions ({len(wrong)} on settled items; first {min(len(wrong), max_wrong)} shown)", ""]
    for i, r, d in wrong[:max_wrong]:
        L += [f"**{i['id']}** · {r['rung']} · {r['framing']} · model: **{d}** · statute: **{i['gold_verdict']}** "
              f"({i['gold_reason']})", "",
              f"> {i['text']}", "",
              f"- derivation: {i['rationale']}",
              f"- sources: {'; '.join(i['citation'])}",
              f"- acceptable answer: {i['chosen']}", ""]
    if res["contested"]:
        L += ["## Contested items (fact-dependent publicity; no gold verdict)", "",
              "| lang | rung | framing | convicted | n |", "|---|---|---|---|---|"]
        L += [f"| {c['lang']} | {c['rung']} | {c['framing']} | {c['convicted']} | {c['n']} |" for c in res["contested"]]
    return "\n".join(L) + "\n"


CSS = """body{max-width:980px;margin:0 auto;padding:24px 16px 48px;font:14px/1.5 'Source Sans 3',Frutiger,Arial,sans-serif;color:#000;
background:#fff;border-top:5px solid #dc0018}h1{font-weight:400;font-size:26px}h2{font-size:16px;border-top:1px solid #000;padding-top:6px}
table{border-collapse:collapse;font:12px 'IBM Plex Mono',Menlo,monospace;width:100%}th{text-align:left;border-bottom:1px solid #000;color:#555}
td,th{padding:3px 8px 3px 0}td{border-bottom:1px solid #ddd}blockquote{margin:0;padding-left:12px;border-left:1px solid #000}
code{font-family:'IBM Plex Mono',Menlo,monospace;font-size:12px}"""


def to_html(md: str) -> str:
    try:
        import markdown
        body = markdown.markdown(md, extensions=["tables"])
    except ImportError:
        body = "<pre>" + html.escape(md) + "</pre>"
    return f"<!doctype html><meta charset=utf-8><title>Evaluation report</title><style>{CSS}</style>{body}"


def main(run: str, dataset: str = "dataset", out: str | None = None, max_wrong: int = 40) -> Path:
    run_path = Path(run)
    md = build(run_path, Path(dataset), max_wrong)
    out_p = Path(out) if out else run_path.with_name(run_path.stem + "-report.md")
    out_p.write_text(md, encoding="utf-8")
    out_p.with_suffix(".html").write_text(to_html(md), encoding="utf-8")
    return out_p
