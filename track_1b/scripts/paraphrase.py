"""Natural-language paraphrase split (A16, exploratory): the same legal facts, told the way people actually write.

The core set is templated so that twins differ in one fact. This split asks whether the findings survive natural text:
a stable sample of 40 twin groups (the same groups in German, French and Italian; settled items only) is rewritten in
everyday genres by writer agents, with the legal facts locked; every paraphrase is then read blind by two fact
extractors of different model families, and kept only if the gold computed from what each extractor read equals the
item's gold (verdict and deciding element). The kept paraphrases are scored like the core set.

    python scripts/paraphrase.py sample                  # writes review/paraphrase/<lang>/write.txt + ids.json
    (writer agents write review/paraphrase/<lang>/written.json: [{"id": "P00000", "genre": ..., "text": ...}])
    python scripts/paraphrase.py extract-packets         # review/paraphrase/<lang>/read.txt (paraphrase only)
    (extractor A: agent -> extract_A.json; extractor B: LLM_* model -> `python scripts/paraphrase.py extract B`)
    python scripts/paraphrase.py check                   # verification report; writes dataset/paraphrase/eval/
    python scripts/paraphrase.py report                  # after scoring: reports/paraphrase.json
"""
import collections
import hashlib
import json
import os
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from statute_twins import statute as _statute  # noqa: E402
from statute_twins.gold.engine import gold  # noqa: E402

REV = ROOT / "statutes/stgb_261bis/review/paraphrase"
OUT = ROOT / "dataset/paraphrase"
LANGS = ("de", "fr", "it")
FAMILIES = {"SET": 10, "CHAR": 10, "CHARX": 3, "DATE_SO": 9, "DATE_CTRL": 8}
GENRES = {
    "de": ["kurze Zeitungsmeldung", "Bericht einer Augenzeugin", "Eintrag im Polizeijournal",
           "Erzählung in einem Online-Forum", "Notiz einer Sozialarbeiterin", "Leserbrief, der den Vorfall schildert"],
    "fr": ["brève de journal", "récit d'une témoin", "entrée du journal de police", "récit sur un forum en ligne",
           "note d'une travailleuse sociale", "courrier de lecteur qui relate l'incident"],
    "it": ["breve di cronaca", "racconto di una testimone", "voce del giornale di polizia", "racconto in un forum online",
           "nota di un'assistente sociale", "lettera al giornale che riferisce l'episodio"],
}
WRITE_TASK = """# Rewrite each scenario as natural text (the legal facts must not change)

Each entry is a short scenario from a legal evaluation set, written in a stiff template. Rewrite it in the requested
genre, in the same language, as a real person would write it: 2-5 sentences, varied wording, concrete, third person.

Keep EXACTLY: the date (month and year; the day if one is given), the place, who acted (role, gender), where and before
whom it happened (the setting and the audience: public or private, how many people, in what relationship), which group
was targeted and why (the characteristic), what was said or done and how severe it was, and that the person acted
deliberately. Show the act concretely instead of using statute words ("bezeichnete sie als Menschen zweiter Klasse",
not "in einer gegen die Menschenwürde verstossenden Weise"), but keep it unmistakably that severe and of the same kind
(a call to hatred stays a call to hatred; a degrading statement stays degrading; spreading an ideology stays that).
Do NOT add or drop facts, do not add a legal assessment, no slurs, no real names. Write each paraphrase on its own.

Return a JSON array: [{"id": "P00000", "genre": "<genre used>", "text": "<paraphrase>"}, ...], every id once.
"""
READ_TASK = """# Read each text and record the legally relevant facts (blind)

For each entry, from the text alone, give:
- `setting`: "public" if said or done in public or before a wider audience outside a circle of personal trust;
  "private" if only among family, close friends or in a setting of personal trust; "unclear" if the text does not say.
- `characteristic`: the characteristic the group was targeted for: race, ethnicity, religion, sexual_orientation,
  gender_identity, sex, canton, occupation, age, disability, political_opinion, or other:<word>.
- `act_date`: the date of the act as YYYY-MM-DD if a day is given, else YYYY-MM.
- `act`: "incite" (calls for hatred or discrimination), "ideology" (spreads an ideology degrading the group), "degrade"
  (degrades or discriminates against people in a way violating human dignity), or "other".
- `severe`: true if the act clearly attacks the group's human dignity or calls for hatred; false if it is mild or vague.
- `deliberate`: true if the text says or clearly implies the person acted deliberately.
Reply with a JSON array: [{"id": "P00000", "setting": ..., "characteristic": ..., "act_date": ..., "act": ...,
"severe": true|false, "deliberate": true|false}, ...].
"""
ACT_OF = {"abs1": "incite", "abs2": "ideology", "abs4": "degrade"}


def items(lang):
    return [json.loads(l) for l in (ROOT / f"dataset/eval/core_{lang}.jsonl").read_text(encoding="utf-8").splitlines()]


def plain(iid):
    """The twin group of an item without its language ("261bis-de-SET004-1" -> "261bis-SET004")."""
    parts = iid.split("-")
    return parts[0] + "-" + parts[2]


CHECK = "--check" in sys.argv
DIFFS = []


def _meta(d, it: dict, note: str) -> dict:
    """Per-item licence and provenance record, as in the core set's metadata/items.jsonl."""
    from statute_twins.dataset import item_metadata
    m = item_metadata(d, it, {})
    m["licence_components"][0]["note"] = note
    return m


def _emit(path: Path, text: str):
    """Write a file, or with --check compare it with the released one (selfcheck re-derives the split)."""
    if CHECK:
        if not path.exists() or path.read_text(encoding="utf-8") != text:
            DIFFS.append(str(path.relative_to(ROOT)))
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def sample():
    de = [i for i in items("de") if i["label"] == "settled"]
    groups = collections.defaultdict(set)
    for i in de:
        if i["family"] in FAMILIES:
            groups[i["family"]].add(plain(i["id"]))
    pick = set()
    for fam, n in FAMILIES.items():
        g = sorted(groups[fam], key=lambda x: hashlib.sha256(("paraphrase" + x).encode()).hexdigest())
        pick |= set(g[:n])
    for lang in LANGS:
        its = [i for i in items(lang) if plain(i["id"]) in pick and i["label"] == "settled"]
        rng = random.Random(f"paraphrase-{lang}")
        rng.shuffle(its)
        d = REV / lang
        d.mkdir(parents=True, exist_ok=True)
        ids, lines = {}, [WRITE_TASK, ""]
        for k, i in enumerate(its):
            pid = f"P{k:05d}"
            ids[pid] = i["id"]
            genre = GENRES[lang][k % len(GENRES[lang])]
            lines += [f"[{pid}] genre: {genre}", i["text"], ""]
        (d / "ids.json").write_text(json.dumps(ids, indent=0))
        (d / "write.txt").write_text("\n".join(lines), encoding="utf-8")
        print(lang, len(its), "items from", len(pick), "twin groups ->", d / "write.txt")


def extract_packets():
    meta = []
    for lang in LANGS:
        d = REV / lang
        written = {x["id"]: x for x in json.loads((d / "written.json").read_text(encoding="utf-8"))}
        ids = json.loads((d / "ids.json").read_text())
        assert set(written) == set(ids), f"{lang}: written ids differ from the sample"
        lines = [READ_TASK, ""]
        for pid in sorted(written):
            lines += [f"[{pid}]", written[pid]["text"], ""]
        (d / "read.txt").write_text("\n".join(lines), encoding="utf-8")
        print(lang, len(written), "texts ->", d / "read.txt")


def extract(who: str):
    """A model extractor on any OpenAI-compatible endpoint (LLM_* variables, or LLM_BASE_URL=gateway)."""
    from concurrent.futures import ThreadPoolExecutor
    import time
    from statute_twins.harness.backends.openai_compat import gateway_transport, http_transport
    base, model = os.environ.get("LLM_BASE_URL", ""), os.environ.get("LLM_NAME", "")
    send = (gateway_transport(f"1b-para-{who}", float(os.environ.get("PARA_CAP_USD", "2.0"))) if base == "gateway"
            else http_transport(base, os.environ.get("LLM_API_KEY")))
    fmt = ('Reply with one JSON object only: {"setting": ..., "characteristic": ..., "act_date": ..., "act": ..., '
           '"severe": true|false, "deliberate": true|false}')
    meta = []
    for lang in LANGS:
        d = REV / lang
        written = json.loads((d / "written.json").read_text(encoding="utf-8"))

        def one(x):
            msg = f"{READ_TASK}\n\n[{x['id']}]\n{x['text']}\n\n{fmt}"
            for attempt in range(6):
                try:
                    r = send(dict(model=model, temperature=0.0, max_tokens=160, messages=[{"role": "user", "content": msg}]))
                    break
                except Exception:
                    if attempt == 5:
                        raise
                    time.sleep(5 * 2 ** attempt)
            t = r["choices"][0]["message"]["content"]
            try:
                y = json.loads(t[t.index("{"): t.rindex("}") + 1])
            except ValueError:
                y = {}
            return dict(id=x["id"], **{k: y.get(k) for k in ("setting", "characteristic", "act_date", "act", "severe", "deliberate")})

        with ThreadPoolExecutor(max_workers=int(os.environ.get("PARA_WORKERS", "4"))) as ex:
            out = list(ex.map(one, written))
        (d / f"extract_{who}.json").write_text(json.dumps(dict(model=model, labels=out), indent=0, ensure_ascii=False))
        print(lang, len(out), "read by", model)


def _verdict(st, item, ex):
    """The gold computed from what an extractor read, and whether it matches the item (verdict, element, date, act)."""
    f = dict(item["facts"])
    why = []
    s = ex.get("setting")
    if s not in ("public", "private"):
        why.append(f"setting {s}")
    else:
        f["setting"] = s
    c = str(ex.get("characteristic") or "")
    if c.startswith("other:") or not c:
        why.append(f"characteristic {c}")
    else:
        f["characteristic"] = c
    dt, orig = str(ex.get("act_date") or ""), item["facts"]["act_date"]
    if not orig.startswith(dt[:7]) or (len(dt) == 10 and dt != orig):
        why.append(f"date {dt} vs {orig}")
    if ex.get("act") != ACT_OF.get(item["facts"]["paragraph"]):
        why.append(f"act {ex.get('act')}")
    if not ex.get("severe"):
        why.append("not severe")
    if not ex.get("deliberate"):
        why.append("intent not stated")
    try:
        g = gold(st, f)
    except Exception as e:      # an extracted value the element model does not know
        return False, why + [f"engine: {e}"]
    if (g.verdict, g.reason) != (item["gold_verdict"], item["gold_reason"]):
        why.append(f"gold {g.verdict}/{g.reason} vs {item['gold_verdict']}/{item['gold_reason']}")
    return not why, why


def check():
    st = _statute.load(ROOT / "statutes/stgb_261bis")
    rep, keep_all = dict(by_lang={}), {}
    for lang in LANGS:
        d = REV / lang
        ids = json.loads((d / "ids.json").read_text())
        written = {x["id"]: x for x in json.loads((d / "written.json").read_text(encoding="utf-8"))}
        its = {i["id"]: i for i in items(lang)}
        ex = {}
        for who in ("A", "B"):
            p = d / f"extract_{who}.json"
            raw = json.loads(p.read_text(encoding="utf-8"))
            ex[who] = {x["id"]: x for x in (raw["labels"] if isinstance(raw, dict) else raw)}
        kept, dropped = [], []
        for pid, iid in sorted(ids.items()):
            res = {w: _verdict(st, its[iid], ex[w].get(pid, {})) for w in ex}
            if all(ok for ok, _ in res.values()):
                kept.append((pid, iid))
            else:
                dropped.append(dict(id=pid, item=iid, why={w: why for w, (ok, why) in res.items() if not ok}))
        keep_all[lang] = kept
        rep["by_lang"][lang] = dict(written=len(ids), kept=len(kept), dropped=dropped,
                                    kept_by_gold=dict(collections.Counter(its[i]["gold_verdict"] for _, i in kept)))
        if not CHECK:
            print(lang, f"kept {len(kept)} of {len(ids)}")
    # the kept paraphrases become items of their own (id <item>-P), with the original's gold, facts and provenance
    from statute_twins.generator import build, design
    dz = design.load(ROOT / "statutes/stgb_261bis")
    (OUT / "eval").mkdir(parents=True, exist_ok=True)
    meta = []
    for lang in LANGS:
        d = REV / lang
        written = {x["id"]: x for x in json.loads((d / "written.json").read_text(encoding="utf-8"))}
        its = {i["id"]: i for i in items(lang)}
        rows = []
        for pid, iid in keep_all[lang]:
            i = dict(its[iid])
            prov = dict(i.get("provenance") or {}, text_source=(
                "paraphrase written by a Claude agent from the original item's facts (A16); facts verified blind by a "
                "Claude reader and Qwen-SEA-LION-v4-32B (reports/paraphrase_verification.json); gold, facts and "
                "reference answers are the original item's"))
            i.update(id=iid + "-P", text=written[pid]["text"], subset="paraphrase", paraphrase_of=iid,
                     genre=written[pid]["genre"], paraphrase_id=pid, provenance=prov)
            rows.append(i)
            meta.append(_meta(dz, i, "paraphrase written by a Claude agent (A16) from the original item; gold and "
                                     "reference answers from the templates in metadata/generator"))
        _emit(OUT / "eval" / f"paraphrase_{lang}.jsonl", "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
        prompts = build.build_prompts(dz, rows, rungs=["R0", "R3", "R5"], framings=["conv", "ver"])
        _emit(OUT / "eval" / f"prompts_paraphrase_{lang}.jsonl", "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in prompts))
    _emit(OUT / "metadata" / "items.jsonl", "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in meta))
    _emit(ROOT / "reports/paraphrase_verification.json", json.dumps(rep, indent=1, ensure_ascii=False) + "\n")


def report():
    """Acquittals recognised and convictions kept on the paraphrases and on their templated originals (same items)."""
    from statute_twins.analysis.results import decision
    out = dict(note="A16, exploratory: kept paraphrases vs their templated originals, the 70B, same prompts otherwise",
               cells=[])
    core = {"de": "publicai-70b-fc-core", "fr": "publicai-70b-fc-core-fr", "it": "publicai-70b-fc-core-it"}
    for lang in LANGS:
        para = [json.loads(l) for l in (OUT / "eval" / f"paraphrase_{lang}.jsonl").read_text(encoding="utf-8").splitlines()]
        orig_of = {p["id"]: p["paraphrase_of"] for p in para}
        gold_of = {p["id"]: p["gold_verdict"] for p in para}
        rp = OUT / "responses" / f"publicai-70b-paraphrase-{lang}.jsonl"
        if not rp.exists():
            continue
        dec_p = {(r["item_id"], r["rung"], r["framing"]): decision(r)
                 for r in map(json.loads, rp.read_text().splitlines()) if "error" not in r}
        dec_o = {(r["item_id"], r["rung"], r["framing"]): decision(r)
                 for r in map(json.loads, (ROOT / "dataset/responses" / f"{core[lang]}.jsonl").read_text().splitlines())
                 if "error" not in r}
        for rung in ("R0", "R3", "R5"):
            for fr in ("conv", "ver"):
                c = collections.Counter()
                for pid, oid in orig_of.items():
                    g = gold_of[pid]
                    for which, dec, iid in (("para", dec_p, pid), ("orig", dec_o, oid)):
                        d = dec.get((iid, rung, fr))
                        if d is None:
                            continue
                        c[f"{which}_{g}_n"] += 1
                        c[f"{which}_{g}_ok"] += d == g
                if c:
                    out["cells"].append(dict(lang=lang, rung=rung, framing=fr, **dict(sorted(c.items()))))
    _emit(ROOT / "reports/paraphrase.json", json.dumps(out, indent=1) + "\n")
    for c in ([] if CHECK else out["cells"]):
        print(c["lang"], c["rung"], c["framing"], "acquit para", c.get("para_acquit_ok"), "/", c.get("para_acquit_n"),
              "orig", c.get("orig_acquit_ok"), "/", c.get("orig_acquit_n"), "| convict para", c.get("para_convict_ok"),
              "/", c.get("para_convict_n"))


if __name__ == "__main__":
    cmd = sys.argv[1]
    {"sample": sample, "extract-packets": extract_packets, "check": check, "report": report}.get(
        cmd, lambda: extract(sys.argv[2]))()
    if CHECK:
        print("paraphrase split: " + ("re-derived identically" if not DIFFS else "DIFFERS: " + ", ".join(DIFFS)))
        sys.exit(1 if DIFFS else 0)
