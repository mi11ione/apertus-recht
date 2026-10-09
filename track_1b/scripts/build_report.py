"""Render technical_report.md to the report PDF (A4, at most 6 pages) through print-styled HTML and headless Chrome.

    python scripts/build_report.py [--pdf TeamName_Report.pdf]

Typography: humanist sans for prose (Source Sans 3, vendored), monospace for figures, codes and tables (IBM Plex Mono),
black on white, one red, hairline rules; the layout follows the conventions of a federal report (running header with
document reference and date, numbered sections, captions below figures).
"""
import argparse
import base64
import datetime
import re
import shutil
import subprocess
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
html{font:9.6pt/1.42 'Sans',Arial,sans-serif;color:#000}
body{margin:0}
h1{font:400 21pt/1.1 'Sans';margin:0 0 3mm;letter-spacing:-.01em}
h1+p{font-size:10.5pt;margin-top:0}
h2{font:600 11.5pt/1.25 'Sans';margin:5mm 0 1.5mm;padding-top:1.5mm;border-top:.4pt solid #000;break-after:avoid}
h3{font:600 9.8pt/1.3 'Sans';margin:3mm 0 1mm;break-after:avoid}
p{margin:0 0 2mm;orphans:3;widows:3}
ul,ol{margin:0 0 2mm;padding-left:5mm} li{margin:0 0 .6mm}
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


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--md", default=str(ROOT / "technical_report.md"))
    ap.add_argument("--pdf", default=str(ROOT / "TeamName_Report.pdf"))
    a = ap.parse_args()
    md = Path(a.md).read_text(encoding="utf-8")
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
