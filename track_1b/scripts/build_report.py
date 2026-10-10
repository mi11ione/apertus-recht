"""Render technical_report.md to the report PDF (A4, at most 6 pages) through print-styled HTML and headless Chrome.

    python scripts/build_report.py [--pdf TeamName_Report.pdf]

Typography: humanist sans for prose (Source Sans 3, vendored), monospace for figures, codes and tables (IBM Plex Mono),
black on white, one red, hairline rules; the layout follows the conventions of a federal report (running header with
document reference and date, numbered sections, captions below figures).
"""
import argparse
import base64
import json
import datetime
import re
import shutil
import subprocess
import sys
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parents[1]
CHROME = ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "google-chrome", "chromium", "chromium-browser"]


def font_face(name, file, weight):
    data = base64.b64encode((ROOT / "docs/fonts" / file).read_bytes()).decode()
    return f"@font-face{{font-family:'{name}';src:url(data:font/ttf;base64,{data}) format('truetype');font-weight:{weight}}}"


CSS = """
@page{size:A4;margin:16mm 16mm 16mm 16mm;
  @top-left{content:"Apertus-Recht · Technical report · Hack Apertus 2026, Track 1B";font:7.5pt 'Plex';color:#666}
  @top-right{content:"__DATE__";font:7.5pt 'Plex';color:#666}
  @bottom-right{content:counter(page) " / " counter(pages);font:7.5pt 'Plex';color:#666}}
html{font:9.3pt/1.38 'Sans',Arial,sans-serif;color:#000}
body{margin:0}
h1{font:400 21pt/1.1 'Sans';margin:0 0 3mm;letter-spacing:-.01em}
h1+p{font-size:10.5pt;margin-top:0}
h2{font:600 11pt/1.25 'Sans';margin:4mm 0 1.2mm;padding-top:1.5mm;border-top:.4pt solid #000;break-after:avoid}
h3{font:600 9.8pt/1.3 'Sans';margin:3mm 0 1mm;break-after:avoid}
p{margin:0 0 2mm;orphans:3;widows:3}
ul,ol{margin:0 0 1.6mm;padding-left:4.5mm} li{margin:0 0 .3mm}
code{font:8.4pt 'Plex'}
pre{font:7.8pt/1.35 'Plex';border-left:.4pt solid #000;padding-left:3mm;white-space:pre-wrap;break-inside:avoid}
table{border-collapse:collapse;width:100%;margin:1mm 0 3mm;font:7.9pt/1.3 'Plex';break-inside:avoid}
th{text-align:left;font-weight:500;color:#555;border-bottom:.6pt solid #000;padding:1mm 2mm 1mm 0}
td{border-bottom:.3pt solid #c8c8c8;padding:.8mm 2mm .8mm 0;vertical-align:top}
td:first-child,th:first-child{font-family:'Sans';font-size:8.6pt}
img{width:100%;display:block;margin:2mm 0 1mm;break-inside:avoid}
figure{margin:0 0 3mm;break-inside:avoid}
blockquote{margin:0 0 2mm;padding-left:3mm;border-left:2pt solid #dc0018}
strong{font-weight:600}
a{color:#000;text-decoration:none}
.red{color:#dc0018}
hr{border:0;border-top:.4pt solid #000;margin:3mm 0}
"""


MODELS = [("publicai-70b-fc-core", "70B", "de"), ("publicai-70b-fc-lay", "70B, user voice", "de_lay"),
          ("publicai-70b-fc-core-fr", "70B", "fr"), ("publicai-70b-fc-core-it", "70B", "it"),
          ("8b-gguf-q4_k_m-cpu-core", "8B Q4_K_M", "de")]
RUNGS = ("R0", "R3", "R4", "R5")
PREF = [("publicai-70b-pref", "70B", "de"), ("publicai-70b-pref-fr", "70B", "fr"), ("publicai-70b-pref-it", "70B", "it"),
        ("8b-gguf-q4_k_m-cpu-pref", "8B Q4_K_M", "de")]
OPEN = [("publicai-70b-open", "70B")]


def _pair(c, v, key):
    f = lambda x: f"{x[key]:.2f}" if x else "–"
    return "–" if not c and not v else f"{f(c)} / {f(v)}"


def tables(R: dict) -> dict:
    """Markdown tables generated from results/results.json (inserted at ⟨table:NAME⟩ markers)."""
    out = {}
    # balanced accuracy (and recall of acquittals), Ja/Nein / verdict framing, per rung
    L = ["| model | lang | " + " | ".join(f"{r} bal. acc." for r in RUNGS) + " | R3 acquit recall |",
         "|---|---|" + "---|" * (len(RUNGS) + 1)]
    for run, name, lang in MODELS:
        if run not in R["runs"]:
            continue
        acc = {(a["rung"], a["framing"]): a for a in R["runs"][run]["accuracy"] if a["subset"] == "core" and a["lang"] == lang}
        cells = [_pair(acc.get((rung, "conv")), acc.get((rung, "ver")), "balanced_accuracy") for rung in RUNGS]
        cells.append(_pair(acc.get(("R3", "conv")), acc.get(("R3", "ver")), "recall_acquit"))
        L.append(f"| {name} | {lang.split('_')[0].upper()} | " + " | ".join(cells) + " |")
    out["accuracy"] = "\n".join(L)
    # held-out read-back test
    L = ["| model | lang | rung | read-back (Ja/Nein, verdict) | statute | gain | pre-registered verdict |", "|---|---|---|---|---|---|---|"]
    for run, name, lang in MODELS:
        h = (R["runs"].get(run) or {}).get("heldout", {}).get(lang)
        if not h:
            continue
        by = {(c["rung"], c["framing"]): c for c in h["cells"]}
        for rung in ("R3", "R4"):              # R0 passes trivially for a model that convicts everything (text)
            c, v = by.get((rung, "conv")), by.get((rung, "ver"))
            if not c or not v:
                continue
            L.append(f"| {name} | {lang.upper()} | {rung} | {c['readback_accuracy']:.2f}, {v['readback_accuracy']:.2f} | "
                     f"{c['statute_accuracy']:.2f}, {v['statute_accuracy']:.2f} | +{c['gain']*100:.1f}, +{v['gain']*100:.1f} pts | "
                     f"{'**pass**' if h['verdict_by_rung'][rung]['passed'] else 'fail'} |")
    out["heldout"] = "\n".join(L)
    # preference accuracy (per token) and free-text pass rate, by the element that decides the item
    cols = [("all", "all"), ("convict", "convict"), ("setting:failed", "private"), ("characteristic:not_listed", "not listed"),
            ("characteristic:not_yet_covered", "SO < 2020"), ("act_date:not_in_force", "< 1995")]
    L = ["| measure | model | lang | " + " | ".join(c[1] for c in cols) + " |", "|---|---|---|" + "---|" * len(cols)]
    for run, name, lang in PREF:
        pr = {(p["lang"], p["reason"]): p for p in (R["runs"].get(run) or {}).get("preference", [])}
        if (lang, "all") not in pr:
            continue
        L.append(f"| preference | {name} | {lang.upper()} | " +
                 " | ".join(f"{pr[(lang, k)]['accuracy']:.2f}" if (lang, k) in pr else "–" for k, _ in cols) + " |")
    for run, name in OPEN:
        p = ROOT / "reports" / f"open_judged_{run}.json"
        if not p.exists():
            continue
        cells = json.loads(p.read_text())["cells"]
        for rung in ("R0", "R3"):
            def cell(k):
                c = cells.get("all" if k == "all" else f"rung_reason|{rung}|{k}") if k != "all" else cells.get(f"rung|{rung}")
                return f"{c['passed']}/{c['n']}" if c else "–"
            L.append(f"| free text {rung} | {name} | DE | " + " | ".join(cell(k) for k, _ in cols) + " |")
    out["preference"] = "\n".join(L)
    return out


def md_lists(md: str) -> str:
    """Python-Markdown needs a blank line before a list and four-space indentation for nested items; the report is
    written in the GitHub style (list right under its paragraph, two-space nesting)."""
    out, nested = [], False
    for line in md.split("\n"):
        if re.match(r"^- ", line):
            nested = False
            if out and out[-1].strip() and not re.match(r"^\s*- ", out[-1]) and not out[-1].startswith(" "):
                out.append("")
        elif re.match(r"^  - ", line):
            nested, line = True, "    " + line[2:]
        elif nested and re.match(r"^    \S", line):
            line = "      " + line[4:]
        elif not line.startswith(" "):
            nested = False
        out.append(line)
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--md", default=str(ROOT / "technical_report.md"))
    ap.add_argument("--pdf", default=str(ROOT / "TeamName_Report.pdf"))
    a = ap.parse_args()
    md = Path(a.md).read_text(encoding="utf-8")
    R = json.loads((ROOT / "results/results.json").read_text())
    for name, t in tables(R).items():
        md = md.replace(f"⟨table:{name}⟩", t)
    # inline numbers: ⟨claim_id⟩ is filled from claims.tsv (the same expressions CI checks)
    sys.path.insert(0, str(ROOT / "scripts"))
    from check_claims import claim_values
    for c in claim_values():
        md = md.replace(f"⟨{c['id']}⟩", c["got"])
    md = md_lists(md)
    left = re.findall(r"⟨[^⟩]*⟩", md)
    if left:
        raise SystemExit(f"unfilled markers in the report: {left[:5]}")
    # figures: ![caption](docs/figures/x.png) -> inline image (PNG data) so the HTML is self-contained
    def fig(m):
        p = ROOT / m.group(2)
        return f"![{m.group(1)}](data:image/png;base64,{base64.b64encode(p.read_bytes()).decode()})"
    md = re.sub(r"!\[([^\]]*)\]\(([^)]+\.png)\)", fig, md)
    html = markdown.markdown(md, extensions=["tables", "fenced_code", "sane_lists"])
    fonts = "".join([font_face("Sans", "SourceSans3-Regular.ttf", 400), font_face("Sans", "SourceSans3-Semibold.ttf", 600),
                     font_face("Plex", "IBMPlexMono-Regular.ttf", 400), font_face("Plex", "IBMPlexMono-Medium.ttf", 500)])
    css = CSS.replace("__DATE__", datetime.date.today().strftime("%d.%m.%Y"))
    doc = f"<!doctype html><html lang=en><meta charset=utf-8><style>{fonts}{css}</style><body>{html}</body></html>"
    out_html = ROOT / "docs" / "report.html"
    out_html.write_text(doc, encoding="utf-8")
    chrome = next((c for c in CHROME if shutil.which(c) or Path(c).exists()), None)
    if not chrome:
        raise SystemExit("no Chrome/Chromium found for PDF printing")
    subprocess.run([chrome, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", f"--print-to-pdf={a.pdf}",
                    out_html.as_uri()], check=True, capture_output=True)
    pages = len(re.findall(rb"/Type\s*/Page[^s]", Path(a.pdf).read_bytes()))
    print(f"{a.pdf}: {pages} pages")
    if pages > 6:
        raise SystemExit(f"report has {pages} pages; the limit is 6")


if __name__ == "__main__":
    main()
