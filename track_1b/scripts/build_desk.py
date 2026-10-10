"""Build the gold register (the public review desk) as a static site for Cloudflare: every item with its twins, the
gold derivation, the reference answers, the review records (blind annotation, law-only pass, adjudication), the model's
verdicts at every rung and its free-text answers with the three judges; and the court decisions with the engine's
verdict. Everything is read from the repository's files; nothing is typed by hand.

    python scripts/build_desk.py [--out site]
"""
import argparse
import collections
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from statute_twins.analysis.results import decision  # noqa: E402
from statute_twins.qc.checks import load_items  # noqa: E402

REV = ROOT / "statutes/stgb_261bis/review"
REPO = "https://github.com/mi11ione/apertus-recht"
DATASET = "https://huggingface.co/datasets/mi11ion/apertus-recht"
LANGS = [("de", "Deutsch"), ("fr", "Français"), ("it", "Italiano"), ("de_lay", "Deutsch · user voice")]
RUNS = {"70B": {"de": "publicai-70b-fc-core", "fr": "publicai-70b-fc-core-fr", "it": "publicai-70b-fc-core-it",
                "de_lay": "publicai-70b-fc-lay"},
        "8B": {"de": "8b-gguf-q4_k_m-cpu-core"}}
PREF = {"de": "publicai-70b-pref", "fr": "publicai-70b-pref-fr", "it": "publicai-70b-pref-it"}
# when each language's wording last changed after the annotation passes (amendments); the gold never changed
REWORDED = {"fr": "A7", "it": "A7"}


def jl(p):
    p = Path(p)
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()] if p.exists() else []


def responses(run):
    return jl(ROOT / "dataset/responses" / f"{run}.jsonl")


def review_records():
    ann = collections.defaultdict(list)
    for r in jl(REV / "annotation/labels.jsonl"):
        ann[r["item_id"]].append(dict(round=r["round"], label=r["label"], el=r["deciding_element"], reason=r["reason"],
                                      who=r["annotator"]))
    lawonly = {}
    ids = json.loads((REV / "annotation/blind_ids_lawonly.json").read_text())
    for p in sorted((REV / "annotation/raw_lawonly").glob("*.json")):
        for x in json.loads(p.read_text()):
            if x["id"] in ids:
                lawonly[ids[x["id"]]] = dict(label=x["label"], el=x["deciding_element"], reason=x["reason"])
    adj = collections.defaultdict(list)
    aids = json.loads((REV / "adjudication/adjudication_ids.json").read_text())
    for who in ("A", "B"):
        for x in json.loads((REV / f"adjudication/adj_{who}.json").read_text()):
            if x["id"] in aids:
                adj[aids[x["id"]]].append(dict(who=who, decision=x["decision"], reason=x.get("reason", "")))
    return ann, lawonly, adj


def judges():
    d = REV / "open_judge"
    ids = json.loads((d / "ids.json").read_text())
    out = collections.defaultdict(dict)
    for who in ("A", "B", "C"):
        for p in sorted(d.glob(f"judge_{who}_*.json")):
            for x in json.loads(p.read_text()):
                if x["id"] in ids:
                    out[ids[x["id"]]][who] = dict(p=bool(x.get("pass")), v=x.get("verdict_expressed"), n=x.get("note", ""))
    return out


CHAR = {"race": "race", "ethnicity": "ethnicity", "religion": "religion", "sexual_orientation": "sexual orientation",
        "gender_identity": "gender identity", "sex": "sex", "canton": "canton", "occupation": "occupation", "age": "age",
        "disability": "disability", "political_opinion": "political opinion"}


def describe(i):
    """The scenario in a few plain words: what kind of case it is and, for a variant, what changed."""
    f = i["facts"]
    ch = CHAR.get(f.get("characteristic"), f.get("characteristic"))
    if i["variant"] == "base":
        return f"base · {f.get('setting')} · {ch} · {f.get('act_date', '')[:4]}"
    if i["variant"] == "contested":
        return "setting open (contested)"
    r = i.get("gold_reason")
    if r == "setting:failed":
        return "private setting"
    if r == "characteristic:not_listed":
        return f"group defined by {ch} (not listed)"
    if r == "characteristic:not_yet_covered":
        return f"sexual orientation, act {f.get('act_date', '')[:7]} (before 1 Jul 2020)"
    if r == "act_date:not_in_force":
        return f"act {f.get('act_date', '')[:4]} (before 1995)"
    t = i.get("trap")
    if t == "family_wording":
        return "public, worded as family (placebo)"
    if t == "synonym":
        return f"{ch}, other word (placebo)"
    if t == "date_overapplied":
        return f"act {f.get('act_date', '')[:4]}, still covered (placebo)"
    if i.get("changed_slot") == "date":
        return f"sexual orientation, act {f.get('act_date', '')[:7]} (placebo)"
    return f"{i.get('changed_slot') or 'wording'} changed (placebo)"


def build_lang(lang, items, ann, lawonly, adj, jd):
    mine = [i for i in items if i["lang"] == lang and i["subset"] != "battery162"]
    models = {}
    for name, runs in RUNS.items():
        if lang in runs:
            m = collections.defaultdict(dict)
            for r in responses(runs[lang]):
                if "error" in r or r.get("framing") not in ("conv", "ver"):
                    continue
                m[r["item_id"]][f"{r['rung']}{r['framing'][0]}"] = [(decision(r) or "?")[0], round(r["lo_conv"], 1) if r.get("lo_conv") is not None else None]
            models[name] = m
    ft = collections.defaultdict(list)
    if lang == "de":
        for r in responses("publicai-70b-open"):
            ft[r["item_id"]].append(dict(rung=r["rung"], text=(r.get("text") or "").strip(), j=jd.get(r["prompt_id"], {})))
    pref = {}
    if lang in PREF:
        for r in responses(PREF[lang]):
            if "error" not in r and r.get("lp_convict") is not None:
                pref[r["item_id"]] = r["lp_convict"] > r["lp_acquit"]
    out = []
    for i in sorted(mine, key=lambda x: x["id"]):
        rec = dict(id=i["id"], f=i["family"], v=i["variant"], g=i["gold_verdict"], r=i.get("gold_reason"), t=i["text"],
                   d=describe(i), b=i.get("base_id"),
                   tw=i["twin_group"], ra=i["rationale"], ci=i.get("citation", []), ac=i["acceptance_criterion"],
                   ch=i["chosen"], rj=i["rejected"], rm=i.get("rejected_minimal"), lab=i["label"], tr=i.get("trap"),
                   sp=i.get("split"))
        for name, m in models.items():
            if i["id"] in m:
                rec["m" + name] = m[i["id"]]
        if ft.get(i["id"]):
            rec["ft"] = sorted(ft[i["id"]], key=lambda x: x["rung"])
        if i["id"] in pref:
            # pref stores candidates by direction; the chosen answer is on the gold side
            rec["pf"] = pref[i["id"]] == (i["gold_verdict"] == "convict")
        src = i["id"].replace("-de_lay-", "-de-")
        if ann.get(src):
            rec["an"] = ann[src]
        if src in lawonly:
            rec["lo"] = lawonly[src]
        if adj.get(src):
            rec["ad"] = adj[src]
        out.append(rec)
    return out


def court():
    cv = json.loads((ROOT / "reports/court_validation.json").read_text())
    by = {r["decision_id"]: r for r in cv["rows"]}
    rows = []
    for t in jl(REV / "court/tuples.jsonl") + jl(REV / "court/tuples_B.jsonl"):
        r = by.get(t["decision_id"])
        if not r:
            continue
        rows.append(dict(id=t["decision_id"], court=t.get("court"), lang=t.get("language"), date=t.get("date"),
                         outcome=t.get("outcome"), status=r["status"], why=r.get("why"), engine=r.get("engine"),
                         agree=r.get("agree"), ground=t.get("acquittal_ground"), facts=r.get("facts"),
                         notes=t.get("notes", ""), stratum=r.get("stratum")))
    seen, uniq = set(), []
    for x in rows:
        if x["id"] not in seen:
            seen.add(x["id"])
            uniq.append(x)
    return dict(summary=cv["summary"], rows=uniq)


PAGE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Apertus-Recht · Gold register</title>
<meta name="description" content="Every Art. 261bis StGB minimal-twin scenario with its computed gold, its review records and what Apertus answered.">
<style>
@font-face{font-family:Sans;src:url(fonts/SourceSans3-Regular.ttf);font-weight:400}
@font-face{font-family:Sans;src:url(fonts/SourceSans3-Semibold.ttf);font-weight:600}
@font-face{font-family:Mono;src:url(fonts/IBMPlexMono-Regular.ttf);font-weight:400}
@font-face{font-family:Mono;src:url(fonts/IBMPlexMono-Medium.ttf);font-weight:500}
:root{--ink:#000;--ink2:#5c5c5c;--ink3:#8a8a8a;--hair:#d9d9d9;--rule:#000;--paper:#fff;--red:#dc0018;--pink:#f6c5cb;--grey:#e6e6e3;--sel:#f4f4f2;color-scheme:light}
*{box-sizing:border-box}
html,body{margin:0;height:100%;background:var(--paper);color:var(--ink);font:15px/1.45 Sans,Arial,sans-serif}
body{display:flex;flex-direction:column;overflow-x:hidden}
a{color:var(--ink)}
button{font:inherit;color:inherit}
.mono{font-family:Mono,monospace}
header{border-top:5px solid var(--red);border-bottom:1px solid var(--rule);padding:10px 20px;display:flex;flex-wrap:wrap;gap:4px 24px;align-items:baseline}
header h1{font:600 17px Sans,Arial,sans-serif;margin:0}
header .sub{font-size:14px;color:var(--ink2)}
header nav{margin-left:auto;font:13px Mono,monospace;display:flex;gap:16px}
.bar{display:flex;flex-wrap:wrap;gap:8px 22px;align-items:center;padding:10px 20px;border-bottom:1px solid var(--hair)}
.seg{display:inline-flex;flex-wrap:wrap;border:1px solid var(--ink);max-width:100%}
.seg button{background:#fff;border:0;border-right:1px solid var(--ink);padding:4px 10px;cursor:pointer;font:13px Mono,monospace}
.seg button:last-child{border-right:0}
.seg button[aria-pressed=true]{background:var(--ink);color:#fff}
.bar label{font:13px Mono,monospace;color:var(--ink2);display:inline-flex;gap:6px;align-items:center}
.bar select,.bar input{font:13px Mono,monospace;border:1px solid var(--hair);border-radius:0;padding:4px 6px;background:#fff;max-width:240px}
.bar input{width:190px}
main{display:grid;grid-template-columns:minmax(300px,400px) minmax(0,1fr);flex:1;min-height:0}
main>*{min-width:0}
#side{display:flex;flex-direction:column;border-right:1px solid var(--rule);min-height:0}
#search{padding:10px 20px 0}#search input{width:100%;font:13px Mono,monospace;border:1px solid var(--hair);border-radius:0;padding:5px 8px}
#count{padding:8px 20px;font:12px Mono,monospace;color:var(--ink2);border-bottom:1px solid var(--rule);display:flex;justify-content:space-between}
#list{overflow:auto;flex:1}
#list button{all:unset;box-sizing:border-box;display:grid;grid-template-columns:1fr auto;gap:2px 10px;width:100%;padding:9px 20px;border-bottom:1px solid var(--hair);cursor:pointer}
#list button:hover{background:#fafafa}
#list button[aria-current=true]{background:var(--sel);box-shadow:inset 3px 0 0 var(--ink)}
#list .d{font-size:15px}
#list .id{font:12px Mono,monospace;color:var(--ink3);grid-column:1}
#list .g{font:12px Mono,monospace;color:var(--ink2);text-align:right}
.strip{display:inline-flex;gap:2px;vertical-align:middle}
.strip i{display:inline-block;width:12px;height:12px;border:1px solid var(--ink3)}
.strip i.bad{background:var(--pink);border-color:var(--red)}
.strip i.na{border-style:dotted;border-color:var(--hair)}
#case{overflow:auto;padding:22px 32px 80px}
.intro{max-width:760px;color:var(--ink2);font-size:15px}
.crumb{font:12px Mono,monospace;color:var(--ink3);margin:0 0 6px}
.text{font-size:21px;line-height:1.45;max-width:880px;margin:0;overflow-wrap:anywhere}
.text mark{background:none;color:inherit;border-bottom:2px solid var(--red)}
.verdict{display:grid;grid-template-columns:max-content 1fr;gap:6px 18px;margin:18px 0 6px;padding:12px 0;border-top:1px solid var(--rule);border-bottom:1px solid var(--rule);max-width:880px}
.verdict dt{font:13px Mono,monospace;color:var(--ink2);padding-top:2px}
.verdict dd{margin:0}
.rungs{display:flex;flex-wrap:wrap;gap:6px}
.rungs span{font:13px Mono,monospace;border:1px solid var(--hair);padding:2px 8px}
.rungs span.bad{border-color:var(--red);background:var(--pink);color:var(--red)}
.rungs span b{font-weight:500;margin-right:6px;color:var(--ink2)}
.rungs span.bad b{color:var(--red)}
h2{font:600 13px Mono,monospace;margin:26px 0 8px;padding-top:6px;border-top:1px solid var(--hair);max-width:880px}
.twins{max-width:880px}
.twins a{display:grid;grid-template-columns:150px 1fr auto;gap:12px;padding:6px 0;border-bottom:1px solid var(--hair);text-decoration:none;font-size:14px}
.twins a:hover{background:#fafafa}
.twins a .i{font:12px Mono,monospace;color:var(--ink3)}
.twins a .g{font:12px Mono,monospace;color:var(--ink2)}
.twins a.me{font-weight:600}
table.m{border-collapse:collapse;font:13px Mono,monospace;display:block;overflow-x:auto;max-width:100%}
table.m th,table.m td{padding:5px 16px 5px 0;border-bottom:1px solid var(--hair);text-align:left;vertical-align:top}
table.m th{color:var(--ink2);font-weight:500;border-bottom:1px solid var(--rule)}
.bad{color:var(--red)}
.q{border-left:2px solid var(--hair);padding:4px 0 4px 14px;margin:8px 0;max-width:880px}
.q.bad{border-left-color:var(--red);color:inherit}
.small{font-size:13px;color:var(--ink2)}
details{max-width:880px;border-top:1px solid var(--hair);margin-top:10px}
details summary{cursor:pointer;font:600 13px Mono,monospace;padding:8px 0;list-style:none}
details summary::before{content:"+ ";color:var(--ink3)}
details[open] summary::before{content:"− "}
.kv{display:grid;grid-template-columns:max-content 1fr;gap:4px 16px;font-size:14px;margin:0 0 12px}
.kv dt{font:13px Mono,monospace;color:var(--ink2)}
.kv dd{margin:0}
.empty{color:var(--ink2);padding:24px 0}
.key{font:12px Mono,monospace;color:var(--ink3)}
@media (max-width:820px){body{height:auto}main{grid-template-columns:minmax(0,1fr);flex:none}.verdict{grid-template-columns:1fr}.bar{padding:10px 16px}header{padding:10px 16px}#count,#list button{padding-left:16px;padding-right:16px}.bar input{width:100%}#side{border-right:0;border-bottom:1px solid var(--rule)}#list{max-height:42vh}#case{padding:16px}.text{font-size:18px}.twins a{grid-template-columns:1fr auto}.twins a .i{display:none}header nav{margin-left:0}}
</style>
</head>
<body>
<header>
<h1>Apertus-Recht · Gold register</h1>
<span class="sub">Every Art. 261bis StGB scenario, the verdict the law gives, and what Apertus answered</span>
<nav><a href="__REPORT__">Report</a><a href="__VIDEO__">Video</a><a href="__REPO__">Code</a><a href="__DATASET__">Dataset</a></nav>
</header>
<div class="bar">
<span class="seg" id="tabs"><button data-tab="items" aria-pressed="true">Scenarios</button><button data-tab="court" aria-pressed="false">Court decisions</button></span>
<span id="filters" style="display:contents">
<span class="seg" id="langs"></span>
<label>show <select id="show">
<option value="">all scenarios</option>
<option value="any">Apertus 70B wrong somewhere</option>
<option value="R0">wrong with no law</option>
<option value="R3">wrong with the rules spelled out</option>
<option value="R4">wrong with the 2020 sentence</option>
<option value="R5">wrong with the law text</option>
<option value="acq">the law acquits</option>
<option value="open">contested</option>
</select></label>
<label>family <select id="fam"><option value="">all</option></select></label>
</span>
</div>
<main><div id="side"><div id="search"><input id="q" type="search" placeholder="search the text or an id" aria-label="Search"></div><div id="count"><span id="n"></span><span class="key">■ R0 R3 R4 R5 · pink = wrong</span></div><div id="list" tabindex="0"></div></div><div id="case"></div></main>
<script>
const LANGS = __LANGS__, COURT = __COURT__, REWORDED = __REWORDED__;
const FAM = {SET:"setting (public / private)", CHAR:"characteristic", CHARX:"characteristic, unlisted", DATE_SO:"date, sexual orientation", DATE_CTRL:"date, other groups", CONTESTED:"contested setting", WORDING:"wording"};
const RUNG = {R0:"no law", R3:"rules", R4:"+ 2020 sentence", R5:"law text", R6:"law text + check"};
const LAW = {acquit:"not punishable", convict:"punishable", open:"depends on facts left open"};
const $ = id => document.getElementById(id);
const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
let tab = "items", lang = LANGS[0][0], data = {}, view = [], cur = null;
async function load(l) { if (!data[l]) data[l] = await (await fetch(`data/items_${l}.json`)).json(); return data[l]; }
const said = (it, r) => { const m = (it.m70B || {})[r + "c"]; return m ? (m[0] === "c" ? "convict" : "acquit") : null; };
const wrong = (it, r) => { const s = said(it, r); return s && it.g !== "open" && s !== it.g; };
function strip(it) { return '<span class="strip">' + ["R0","R3","R4","R5"].map(r => `<i class="${said(it, r) == null ? "na" : wrong(it, r) ? "bad" : ""}" title="${r} ${RUNG[r]}"></i>`).join("") + "</span>"; }
function words(t) { return t.split(/(\s+)/); }
function diff(a, b) {            // words of b that are not in the longest common subsequence with a
  const A = a.split(/\s+/), B = b.split(/\s+/), n = A.length, m = B.length, L = Array.from({length: n + 1}, () => new Array(m + 1).fill(0));
  for (let i = n - 1; i >= 0; i--) for (let j = m - 1; j >= 0; j--) L[i][j] = A[i] === B[j] ? L[i+1][j+1] + 1 : Math.max(L[i+1][j], L[i][j+1]);
  const keep = new Set(); let i = 0, j = 0;
  while (i < n && j < m) { if (A[i] === B[j]) { keep.add(j); i++; j++; } else if (L[i+1][j] >= L[i][j+1]) i++; else j++; }
  return B.map((w, k) => keep.has(k) ? esc(w) : `<mark>${esc(w)}</mark>`).join(" ");
}
async function refresh() {
  const items = await load(lang);
  const fs = $("fam"), keep = fs.value, fams = [...new Set(items.map(i => i.f))];
  fs.innerHTML = '<option value="">all</option>' + fams.map(f => `<option value="${f}"${f === keep ? " selected" : ""}>${FAM[f] || f}</option>`).join("");
  const sh = $("show").value, q = $("q").value.trim().toLowerCase(), f = fs.value;
  view = items.filter(i => (!f || i.f === f) && (!q || i.t.toLowerCase().includes(q) || i.id.toLowerCase().includes(q)) &&
    (!sh || (sh === "any" ? ["R0","R3","R4","R5"].some(r => wrong(i, r)) : sh === "acq" ? i.g === "acquit" : sh === "open" ? i.g === "open" : wrong(i, sh))));
  $("n").textContent = `${view.length} of ${items.length}`;
  $("list").innerHTML = view.map((i, k) => `<button data-k="${k}"><span class="d">${esc(i.d)}</span><span class="g">${LAW[i.g].split(" ")[0] === "not" ? "not punishable" : i.g === "open" ? "open" : "punishable"}</span><span class="id">${esc(i.id.replace("261bis-", ""))}</span><span>${strip(i)}</span></button>`).join("");
  $("list").querySelectorAll("button").forEach(b => b.onclick = () => show(view[+b.dataset.k]));
  if (!cur || !view.find(i => i.id === cur.id)) show(view[0], false); else mark(true);
}
function mark(scroll) { $("list").querySelectorAll("button").forEach(b => { const on = view[+b.dataset.k].id === cur.id; b.setAttribute("aria-current", on); if (on && scroll) b.scrollIntoView({block: "nearest"}); }); }
const lab = l => [l === "convict" ? "c" : l === "acquit" ? "a" : l, null];
function dec(x, gold) { if (!x) return "–"; const d = x[0] === "c" ? "convict" : x[0] === "a" ? "acquit" : x; const b = gold !== "open" && d !== gold; return `<span class="${b ? "bad" : ""}">${d}</span>${x[1] != null ? ` <span class="small">${x[1] > 0 ? "+" : ""}${x[1]}</span>` : ""}`; }
function show(it, scroll = true) {
  cur = it;
  if (!it) { $("case").innerHTML = '<p class="empty">Nothing matches. Clear a filter.</p>'; return; }
  mark(scroll); history.replaceState(null, "", "#" + it.id);
  const all = data[lang], base = all.find(i => i.id === it.b), sib = all.filter(i => i.tw === it.tw);
  let h = `<p class="crumb">${esc(it.id)} · ${esc(FAM[it.f] || it.f)} · ${esc(it.v.replace("_", " "))}</p>`;
  h += `<p class="text">${base && base.id !== it.id ? diff(base.t, it.t) : esc(it.t)}</p>`;
  if (base && base.id !== it.id) h += `<p class="small">Underlined: what differs from its base case.</p>`;
  h += `<dl class="verdict"><dt>the law</dt><dd><b>${esc(LAW[it.g])}</b>${it.r ? ` <span class="small mono">· ${esc(it.r)}</span>` : ""}</dd>`;
  if (it.m70B) h += `<dt>Apertus 70B</dt><dd><span class="rungs">${["R0","R3","R4","R5","R6"].filter(r => it.m70B[r + "c"]).map(r => `<span class="${wrong(it, r) ? "bad" : ""}"><b>${r}</b>${RUNG[r]}: ${said(it, r) === "convict" ? "convicts" : "acquits"}</span>`).join("")}</span></dd>`;
  h += `</dl><p class="small">R0 no law in the prompt · R3 the rules in plain sentences · R4 plus a sentence on the 2020 extension · R5 the verbatim Fedlex text and the leading case · R6 R5 plus an instruction to check the elements. Ja/Nein answers; pink = differs from the law.</p>`;
  if (sib.length > 1) h += `<h2>Its twins: the same case with one fact changed</h2><div class="twins">` + sib.map(s => `<a href="#${esc(s.id)}" data-id="${esc(s.id)}" class="${s.id === it.id ? "me" : ""}"><span class="i">${esc(s.id.replace("261bis-", ""))}</span><span>${esc(s.d)}</span><span class="g">${esc(LAW[s.g])} ${strip(s)}</span></a>`).join("") + "</div>";
  h += `<h2>Why: the element-by-element derivation</h2><p class="mono small">${esc(it.ra)}</p>`;
  for (const name of ["70B", "8B"]) {
    const m = it["m" + name]; if (!m) continue;
    const rs = ["R0","R3","R4","R5","R6"].filter(r => m[r + "c"] || m[r + "v"]);
    h += `<h2>Apertus ${name}, forced choice</h2><table class="m"><tr><th></th><th>prompt</th><th>Ja / Nein</th><th>verdict word</th></tr>` + rs.map(r => `<tr><td>${r}</td><td>${RUNG[r]}</td><td>${dec(m[r + "c"], it.g)}</td><td>${dec(m[r + "v"], it.g)}</td></tr>`).join("") + `</table><p class="small">Numbers: log-odds of conviction (above zero = convicts).</p>`;
  }
  if (it.ft) h += `<h2>Apertus 70B in its own words</h2>` + it.ft.map(x => { const J = Object.entries(x.j), bad = J.length && J.filter(([k, v]) => !v.p).length > J.length / 2; return `<div class="q ${bad ? "bad" : ""}"><div class="small mono">${x.rung} · ${RUNG[x.rung]}${J.length ? " · judges " + J.map(([k, v]) => `${k} ${v.p ? "pass" : "fail"}`).join(", ") : ""}</div>${esc(x.text)}</div>`; }).join("");
  h += `<details><summary>Reference answers</summary><dl class="kv"><dt>chosen</dt><dd>${esc(it.ch)}</dd><dt>rejected</dt><dd>${esc(it.rj)}</dd>${it.rm ? `<dt>mirror</dt><dd>${esc(it.rm)}${it.pf != null ? ` <span class="small mono">· 70B prefers ${it.pf ? "the chosen answer" : "the mirror"}</span>` : ""}</dd>` : ""}<dt>criterion</dt><dd class="small">${esc(it.ac)}</dd></dl></details>`;
  if (it.an || it.lo || it.ad) h += `<details><summary>Review records (blind)</summary>${REWORDED[lang] ? `<p class="small">Annotated on the wording before amendment ${REWORDED[lang]}; no fact or gold changed since.</p>` : ""}<table class="m"><tr><th>pass</th><th>label</th><th>element</th><th>reason</th></tr>` + (it.an || []).map(a => `<tr><td>annotation ${a.round}</td><td>${dec(lab(a.label), it.g)}</td><td>${esc(a.el)}</td><td style="font-family:Sans">${esc(a.reason)}</td></tr>`).join("") + (it.lo ? `<tr><td>law only</td><td>${dec(lab(it.lo.label), it.g)}</td><td>${esc(it.lo.el)}</td><td style="font-family:Sans">${esc(it.lo.reason)}</td></tr>` : "") + (it.ad || []).map(a => `<tr><td>adjudicator ${a.who}</td><td>${esc(a.decision.replace("_", " "))}</td><td></td><td style="font-family:Sans">${esc(a.reason)}</td></tr>`).join("") + `</table></details>`;
  h += `<details><summary>Sources</summary><p class="small">${it.ci.map(esc).join("<br>")}</p></details>`;
  $("case").innerHTML = h; $("case").scrollTop = 0;
  $("case").querySelectorAll("a[data-id]").forEach(a => a.onclick = e => { e.preventDefault(); const t = all.find(i => i.id === a.dataset.id); if (!view.includes(t)) { $("show").value = ""; $("fam").value = ""; $("q").value = ""; refresh().then(() => show(t)); } else show(t); });
}
function court() {
  $("n").textContent = `${COURT.rows.length} decisions triaged`;
  $("list").innerHTML = COURT.rows.map((r, k) => `<button data-k="${k}"><span class="d">${esc(r.court)} · ${esc(r.date || "")}</span><span class="g">${esc(r.outcome)}</span><span class="id">${esc(r.id)}</span><span class="g">${r.status === "in_scope" ? (r.agree ? "engine agrees" : '<span class="bad">engine disagrees</span>') : esc(r.status.replace("_", " "))}</span></button>`).join("");
  $("list").querySelectorAll("button").forEach(b => b.onclick = () => {
    const r = COURT.rows[+b.dataset.k];
    $("list").querySelectorAll("button").forEach(x => x.setAttribute("aria-current", x === b));
    $("case").innerHTML = `<p class="crumb">${esc(r.id)} · stratum ${esc(r.stratum)}</p><dl class="verdict"><dt>court</dt><dd><b>${esc(r.outcome)}</b>${r.ground ? ` · on ${esc(r.ground)}` : ""}</dd><dt>status</dt><dd>${esc(r.status.replace("_", " "))}${r.why ? " · " + esc(r.why) : ""}</dd>${r.engine ? `<dt>engine</dt><dd>${esc(r.engine)} · ${r.agree ? "agrees" : '<span class="bad">disagrees</span>'}</dd>` : ""}</dl>${r.facts ? `<p class="mono small">${esc(Object.entries(r.facts).map(([k, v]) => k + " " + v).join(" · "))}</p>` : ""}<p>${esc(r.notes)}</p>`;
  });
  $("case").innerHTML = `<p class="intro">${esc(COURT.summary)}</p>`;
}
function setTab(t) {
  tab = t; $("search").style.display = t === "items" ? "" : "none"; $("tabs").querySelectorAll("button").forEach(b => b.setAttribute("aria-pressed", b.dataset.tab === t));
  $("filters").style.display = t === "items" ? "contents" : "none"; document.querySelector(".key").style.display = t === "items" ? "" : "none";
  if (t === "court") court(); else { cur = null; refresh(); }
}
$("tabs").querySelectorAll("button").forEach(b => b.onclick = () => setTab(b.dataset.tab));
$("langs").innerHTML = LANGS.map(([l, n]) => `<button data-l="${l}" aria-pressed="${l === lang}">${n}</button>`).join("");
$("langs").querySelectorAll("button").forEach(b => b.onclick = () => { lang = b.dataset.l; $("langs").querySelectorAll("button").forEach(x => x.setAttribute("aria-pressed", x === b)); cur = null; refresh(); });
["show", "fam"].forEach(id => $(id).onchange = () => { cur = null; refresh(); });
$("q").oninput = () => refresh();
document.addEventListener("keydown", e => {
  if (tab !== "items" || e.target.tagName === "INPUT" || e.target.tagName === "SELECT" || !cur) return;
  if (e.key !== "ArrowDown" && e.key !== "ArrowUp") return;
  e.preventDefault(); const k = view.indexOf(cur) + (e.key === "ArrowDown" ? 1 : -1); if (view[k]) show(view[k]);
});
(async () => {
  const h = decodeURIComponent(location.hash.slice(1));
  const l = LANGS.map(x => x[0]).find(x => h.includes(`-${x}-`));
  if (l) { lang = l; $("langs").querySelectorAll("button").forEach(x => x.setAttribute("aria-pressed", x.dataset.l === l)); }
  await refresh();
  const it = h && data[lang].find(i => i.id === h);
  if (it) show(it); else $("case").insertAdjacentHTML("afterbegin", `<p class="intro">Each scenario is one case under Art. 261bis StGB. Its twins change exactly one legal fact; the law's verdict is computed from the pinned statute text and BGE 130 IV 111. Pick a scenario on the left, or show only those where Apertus is wrong. Arrow keys move through the list.</p>`);
})();
</script>
</body>
</html>
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "site"))
    a = ap.parse_args()
    out = Path(a.out)
    if out.exists():
        shutil.rmtree(out)
    (out / "fonts").mkdir(parents=True)
    (out / "data").mkdir()
    for f in ("SourceSans3-Regular.ttf", "SourceSans3-Semibold.ttf", "IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf"):
        shutil.copyfile(ROOT / "docs/fonts" / f, out / "fonts" / f)
    shutil.copyfile(ROOT / "444_Report.pdf", out / "444_Report.pdf")
    video = ROOT / "docs/demo/apertus-recht-demo.mp4"
    if video.exists():
        shutil.copyfile(video, out / video.name)
    items = load_items(ROOT / "dataset")
    ann, lawonly, adj = review_records()
    jd = judges()
    sizes = {}
    for lang, _ in LANGS:
        recs = build_lang(lang, items, ann, lawonly, adj, jd)
        p = out / "data" / f"items_{lang}.json"
        p.write_text(json.dumps(recs, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        sizes[lang] = (len(recs), p.stat().st_size // 1024)
    page = (PAGE.replace("__LANGS__", json.dumps(LANGS))
            .replace("__COURT__", json.dumps(court(), ensure_ascii=False))
            .replace("__REWORDED__", json.dumps(REWORDED))
            .replace("__REPORT__", "444_Report.pdf").replace("__VIDEO__", video.name)
            .replace("__REPO__", REPO).replace("__DATASET__", DATASET))
    (out / "index.html").write_text(page, encoding="utf-8")
    print("wrote", out, {k: f"{n} items, {kb} KB" for k, (n, kb) in sizes.items()})


if __name__ == "__main__":
    main()
