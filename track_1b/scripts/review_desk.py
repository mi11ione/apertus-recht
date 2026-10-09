"""Generate the reviewer's adjudication page (published as a private claude.ai artifact; judgements are stored in the
artifact's database and read back with `scripts/pull_reviews.py`-style reads). Development tool, not part of make run.

    python scripts/review_desk.py <out.html>
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / "statutes/stgb_261bis/review"


def load():
    queue = [json.loads(l) for l in (R / "annotation/adjudication_queue.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    q = [dict(id=x["item_id"], n=x["n"], lang=x["lang"], text=x["text"], gold=x["gold_verdict"], reason=x["gold_reason"],
              rationale=x["rationale"], ann=x["annotator_label"], ann_el=x["annotator_element"], ann_reason=x["annotator_reason"])
         for x in queue]
    units = json.loads((R / "bt/units.json").read_text(encoding="utf-8"))
    bts = {l: {u["id"]: u for u in json.loads((R / f"bt/bt_{l}_de.json").read_text(encoding="utf-8"))} for l in ("fr", "it")}
    bt = []
    for u in units:
        for l in ("fr", "it"):
            bt.append(dict(id=f"{l}:{u['id']}", lang=l, unit=u["id"], de=u["de"], tr=u[l], back=bts[l][u["id"]]["de"],
                           note=bts[l][u["id"]].get("note", "")))
    court = []
    cp = R / "court/review.jsonl"
    if cp.exists():
        court = [json.loads(l) for l in cp.read_text(encoding="utf-8").splitlines() if l.strip()]
    return q, bt, court


PAGE = r"""<title>Gold Review Desk</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
/* layout: one ruled sheet. Header block as on a federal form; below it a two-column register: list | case. */
:root{
  --paper:#ffffff; --ink:#000000; --ink2:#666666; --rule:#000000; --hair:#c8c8c8; --red:#e1001a; --sel:#000000; --sel-ink:#ffffff;
  --sans:"Source Sans 3","Frutiger","Avenir Next",Arial,sans-serif; --mono:"IBM Plex Mono",Menlo,Consolas,monospace;
}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--paper:#0e0e0e; --ink:#ececec; --ink2:#9a9a9a; --rule:#ececec; --hair:#3a3a3a; --red:#ff3348; --sel:#ececec; --sel-ink:#0e0e0e; color-scheme:dark}}
:root[data-theme="dark"]{--paper:#0e0e0e; --ink:#ececec; --ink2:#9a9a9a; --rule:#ececec; --hair:#3a3a3a; --red:#ff3348; --sel:#ececec; --sel-ink:#0e0e0e; color-scheme:dark}
body{background:var(--paper);color:var(--ink);font:13px/1.5 var(--mono);border-top:5px solid var(--red)}
.sheet{max-width:1200px;margin:0 auto;padding-inline:16px;padding-block:24px 48px}
h1{font:400 34px/1.1 var(--sans);margin:0 0 18px;letter-spacing:-.01em}
.head{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:0 32px;border-top:1px solid var(--rule);border-bottom:1px solid var(--rule);padding-block:10px;margin-bottom:22px}
@media (max-width:760px){.head{grid-template-columns:1fr}}
.kv{display:grid;grid-template-columns:11em minmax(0,1fr);gap:2px 12px}
.kv span:nth-child(odd){color:var(--ink2)}
.note{color:var(--ink2);max-width:62ch}
.register{display:grid;grid-template-columns:minmax(0,5fr) minmax(0,7fr);gap:32px;align-items:start}
@media (max-width:900px){.register{grid-template-columns:1fr}}
.bar{display:flex;flex-wrap:wrap;gap:0;border-bottom:1px solid var(--rule);margin-bottom:0}
.bar button{font:13px var(--mono);background:none;color:var(--ink);border:0;padding:6px 10px 6px 0;margin-right:14px;cursor:pointer}
.bar button[aria-pressed="true"]{text-decoration:underline;text-underline-offset:4px;text-decoration-thickness:2px}
.bar .sep{flex:1}
.list{max-height:68vh;overflow:auto}
table{border-collapse:collapse;width:100%}
th{font:500 11px var(--mono);text-align:left;color:var(--ink2);padding:6px 8px 4px 0;border-bottom:1px solid var(--rule);position:sticky;top:0;background:var(--paper)}
td{padding:5px 8px 5px 0;border-bottom:1px solid var(--hair);vertical-align:top}
td.x{white-space:nowrap;max-width:0;overflow:hidden;text-overflow:ellipsis;width:100%;font-family:var(--sans);font-size:14px}
tr.r{cursor:pointer}
tr.r:hover td{background:color-mix(in srgb,var(--ink) 6%,transparent)}
tr.r[aria-current="true"] td{background:var(--sel);color:var(--sel-ink)}
.mk{white-space:pre}
.mk.bad{color:var(--red)}
tr.r[aria-current="true"] .mk.bad{color:var(--sel-ink)}
.case h2{font:400 22px/1.2 var(--sans);margin:0 0 4px}
.case .ref{color:var(--ink2);margin-bottom:14px}
.text{font:17px/1.6 var(--sans);max-width:68ch;margin:0 0 18px;padding-left:14px;border-left:1px solid var(--rule)}
.facts{display:grid;grid-template-columns:9em minmax(0,1fr);gap:3px 12px;border-top:1px solid var(--rule);padding-top:8px;margin-bottom:18px}
.facts span:nth-child(odd){color:var(--ink2)}
.facts span{min-width:0;overflow-wrap:anywhere}
.convict{color:var(--red)}
.three{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:0 16px;border-top:1px solid var(--rule);padding-top:8px;margin-bottom:18px}
@media (max-width:760px){.three{grid-template-columns:1fr}}
.three div{min-width:0} .three b{display:block;font-weight:500;color:var(--ink2);margin-bottom:4px}
.three p{margin:0;font:15px/1.5 var(--sans);white-space:pre-wrap;overflow-wrap:anywhere}
.choose{display:flex;flex-wrap:wrap;gap:8px;border-top:1px solid var(--rule);padding-top:12px}
.choose button{font:13px var(--mono);background:var(--paper);color:var(--ink);border:1px solid var(--rule);border-radius:0;padding:7px 12px;cursor:pointer}
.choose button[aria-pressed="true"]{background:var(--sel);color:var(--sel-ink)}
.field{display:grid;grid-template-columns:9em minmax(0,1fr);gap:8px 12px;align-items:start;margin-top:12px}
.field label{color:var(--ink2);padding-top:6px}
select,textarea{font:13px var(--mono);background:var(--paper);color:var(--ink);border:1px solid var(--hair);border-radius:0;padding:6px;width:100%}
textarea{min-height:60px;resize:vertical}
.go{display:flex;gap:16px;align-items:center;margin-top:14px;flex-wrap:wrap}
.go button{font:500 13px var(--mono);background:var(--ink);color:var(--paper);border:0;border-radius:0;padding:8px 16px;cursor:pointer}
.msg{color:var(--ink2)}
.empty{color:var(--ink2);padding:12px 0}
a{color:inherit}
button:focus-visible,select:focus-visible,textarea:focus-visible,tr.r:focus-visible{outline:2px solid var(--red);outline-offset:1px}
</style>
<div class="sheet">
<h1>Gold Review Desk</h1>
<div class="head">
 <div class="kv"><span>Statute</span><span>Art. 261bis StGB / CP</span><span>Leading case</span><span>BGE 130 IV 111 E. 5.2</span><span>Reviewer</span><span>R1</span><span>Prepared</span><span>__DATE__</span></div>
 <div><div class="kv"><span>Saved</span><span id="progress">loading …</span></div>
 <p class="note">Decide each entry against the statute and the leading case. Keys: 1 / 2 / 3 choose, Cmd+Enter saves.</p></div>
</div>
<div class="register">
 <section aria-label="Register">
  <div class="bar"><button id="tab-adj" aria-pressed="true">Gold labels</button><button id="tab-bt" aria-pressed="false">Translations</button><button id="tab-court" aria-pressed="false">Court tuples</button></div>
  <div class="bar"><button id="f-open" aria-pressed="true">Open</button><button id="f-done" aria-pressed="false">Done</button><button id="f-all" aria-pressed="false">All</button></div>
  <div class="list" id="list"></div>
 </section>
 <section class="case" id="case" aria-live="polite"></section>
</div></div>
<script id="data" type="application/json">__DATA__</script>
<script>
const DATA = JSON.parse(document.getElementById("data").textContent);
const TASKS = {
 adj: {coll:"verdicts", name:"gold labels", items:DATA.adj, cols:["No.","Lang","Scenario"], cells:x=>[x.n,x.lang.toUpperCase(),x.text], choices:[
   ["gold_correct","Gold correct","1"],["gold_wrong","Gold wrong","2"],["contested","Genuinely contested","3"]],
   causes:["element model","slot encoding (wrong fact recorded)","scenario wording","translation","other"]},
 bt: {coll:"translations", name:"translations", items:DATA.bt, cols:["Lang","Unit","Text"], cells:x=>[x.lang.toUpperCase(),x.unit,x.tr], choices:[
   ["faithful","Faithful","1"],["issue","Legal fact differs","2"]], causes:["setting facts","group / characteristic","act / paragraph","date","prompt or answer","grammar only"]},
 court:{coll:"court", name:"court tuples", items:DATA.court, cols:["Court","Date","Decision"], cells:x=>[x.court,x.date,x.decision_id], choices:[
   ["tuple_correct","Tuple correct","1"],["tuple_wrong","Tuple wrong","2"]], causes:["outcome","setting","characteristic","date","paragraph","acquittal ground","not a 261bis ruling"]},
};
const BAD=new Set(["gold_wrong","issue","tuple_wrong"]);
let task="adj", filter="open", cur=null, saved={adj:{},bt:{},court:{}}, db=null, uid=null;
const $=id=>document.getElementById(id);
function esc(s){return String(s??"").replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]))}
function docId(x){return x.id.replace(/[^A-Za-z0-9_-]/g,"_")}
function mark(d){if(!d)return'<span class="mk">[ ]</span>';if(BAD.has(d.decision))return'<span class="mk bad">[!]</span>';return d.decision==="contested"?'<span class="mk">[~]</span>':'<span class="mk">[x]</span>'}
function visible(){return TASKS[task].items.filter(x=>{const d=saved[task][docId(x)];return filter==="all"||(filter==="done"?!!d:!d)})}
function renderProgress(){$("progress").textContent=Object.entries(TASKS).map(([k,T])=>`${Object.keys(saved[k]).length}/${T.items.length} ${T.name}`).join(" · ")+(db?"":" (read-only here)")}
function renderList(){const T=TASKS[task],L=visible();
 $("list").innerHTML=L.length?`<table><thead><tr><th></th>${T.cols.map((c,i)=>`<th${i===2?' style="width:100%"':""}>${c}</th>`).join("")}</tr></thead><tbody>${L.map(x=>{const c=T.cells(x);
  return `<tr class="r" tabindex="0" data-id="${esc(x.id)}" aria-current="${!!cur&&cur.id===x.id}"><td>${mark(saved[task][docId(x)])}</td><td>${esc(c[0])}</td><td>${esc(c[1])}</td><td class="x">${esc(c[2])}</td></tr>`}).join("")}</tbody></table>`
  :`<p class="empty">${T.items.length?"No entries under this filter.":"None yet. Court tuples arrive after extraction."}</p>`;
 for(const r of $("list").querySelectorAll("tr.r")){r.onclick=()=>open(r.dataset.id);r.onkeydown=e=>{if(e.key==="Enter")open(r.dataset.id)}}}
function body(x){
 if(task==="adj") return `<h2>Entry ${esc(x.n)}</h2><div class="ref">${esc(x.id)}</div><p class="text">${esc(x.text)}</p>
  <div class="facts"><span>Gold</span><span class="${x.gold==="convict"?"convict":""}">${esc(x.gold)}${x.reason!==x.gold&&x.reason!=="convict"?" ("+esc(x.reason)+")":""}</span>
  <span>Derivation</span><span>${esc(x.rationale)}</span>
  <span>Annotator</span><span>${esc(x.ann)}, ${esc(x.ann_el)}: ${esc(x.ann_reason)}</span></div>`;
 if(task==="bt") return `<h2>${esc(x.unit)}</h2><div class="ref">${x.lang==="fr"?"French":"Italian"} against the German source</div>
  <div class="three"><div><b>German source</b><p>${esc(x.de)}</p></div><div><b>${x.lang==="fr"?"French":"Italian"}</b><p>${esc(x.tr)}</p></div>
  <div><b>Blind back-translation</b><p>${esc(x.back)}</p>${x.note?`<p class="msg">Note: ${esc(x.note)}</p>`:""}</div></div>`;
 return `<h2>${esc(x.decision_id)}</h2><div class="ref">${esc(x.court)} · ${esc(x.language)} · ${esc(x.date)}</div>
  <div class="facts">${Object.entries(x.tuple||{}).map(([k,v])=>`<span>${esc(k)}</span><span>${esc(v)}</span>`).join("")}</div>
  ${x.passages?`<p class="text" style="font-size:15px;white-space:pre-wrap">${esc(x.passages)}</p>`:""}
  ${x.url?`<p class="msg">Source: <a href="${esc(x.url)}" target="_blank" rel="noopener">${esc(x.url)}</a></p>`:""}`}
function open(id){const T=TASKS[task];cur=T.items.find(x=>x.id===id);if(!cur)return;const d=saved[task][docId(cur)]||{};
 $("case").innerHTML=body(cur)+`<div class="choose" role="group" aria-label="Decision">${T.choices.map(([v,l,k])=>`<button id="c-${v}" data-v="${v}" aria-pressed="${d.decision===v}">(${k}) ${l}</button>`).join("")}</div>
  <div class="field"><label for="cause">Cause</label><select id="cause"><option value="">none</option>${T.causes.map(c=>`<option ${d.cause===c?"selected":""}>${esc(c)}</option>`).join("")}</select>
  <label for="note">Note</label><textarea id="note" placeholder="What differs, and what the source says">${esc(d.note||"")}</textarea></div>
  <div class="go"><button id="save">Save, next</button><span class="msg" id="msg">${d.decision?"Saved: "+esc(d.decision):(db?"":"Saving is unavailable in this view.")}</span></div>`;
 for(const b of $("case").querySelectorAll(".choose button"))b.onclick=()=>{for(const o of $("case").querySelectorAll(".choose button"))o.setAttribute("aria-pressed",o===b)};
 $("save").onclick=save;renderList()}
async function save(){const btn=$("case").querySelector('.choose button[aria-pressed="true"]');if(!btn){$("msg").textContent="Choose a decision first.";return}
 if(!db){$("msg").textContent="Saving is unavailable in this view.";return}
 const rec={item:cur.id,task,decision:btn.dataset.v,cause:$("cause").value||null,note:$("note").value.trim(),reviewer:uid,ts:Date.now()};
 try{await db.doc(`${TASKS[task].coll}/${docId(cur)}`).set(rec);$("msg").textContent="Saved.";next()}catch(e){$("msg").textContent="Not saved: "+(e&&e.message||e)+". Try again."}}
function next(){const L=visible().filter(x=>x.id!==cur.id);if(L.length)open(L[0].id);else{cur=null;$("case").innerHTML=`<p class="empty">This list is complete.</p>`;renderList()}}
function setTask(t){task=t;for(const k of Object.keys(TASKS))$("tab-"+k).setAttribute("aria-pressed",k===t);cur=null;const L=visible();L.length?open(L[0].id):($("case").innerHTML=`<p class="empty">${TASKS[t].items.length?"Nothing open here.":"None yet."}</p>`,renderList())}
function setFilter(f){filter=f;for(const k of ["open","all","done"])$("f-"+k).setAttribute("aria-pressed",k===f);renderList()}
for(const k of Object.keys(TASKS))$("tab-"+k).onclick=()=>setTask(k);
for(const k of ["open","all","done"])$("f-"+k).onclick=()=>setFilter(k);
document.addEventListener("keydown",e=>{if(e.target.matches("textarea,select"))return;const c=TASKS[task].choices.find(c=>c[2]===e.key);
 if(c&&$("c-"+c[0]))$("c-"+c[0]).click();if(e.key==="Enter"&&cur&&(e.metaKey||e.ctrlKey))save()});
setTask("adj");renderProgress();
(async()=>{db=await window.claude?.use?.("db");const user=await window.claude?.use?.("user");try{uid=user?await user.id():null}catch(e){}
 if(!db){renderProgress();return}
 for(const [k,T] of Object.entries(TASKS))db.collection(T.coll).limit(1000).onSnapshot(s=>{saved[k]={};for(const d of s.docs){saved[k][d.id]=d.data()}renderProgress();renderList()});
 renderProgress()})();
</script>
"""


def main(out: str) -> None:
    q, bt, court = load()
    data = json.dumps(dict(adj=q, bt=bt, court=court), ensure_ascii=False).replace("</", "<\\/")
    import datetime
    Path(out).write_text(PAGE.replace("__DATA__", data).replace("__DATE__", datetime.date.today().strftime("%d.%m.%Y")), encoding="utf-8")
    print(out, len(q), "cases,", len(bt), "translation units,", len(court), "court tuples")


if __name__ == "__main__":
    main(sys.argv[1])
