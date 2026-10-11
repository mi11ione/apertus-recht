"""Automated quality control over a released dataset folder. Every check returns (name, passed, details); any gate
failure makes ``statute-twins qc`` exit non-zero, and the Hugging Face upload script refuses to run.

Gates: schema, gold recomputation, twin invariants, duplicates, language identity, PII, canary.
Reports (no gate): descriptive statistics, diversity, answer-token mass per run.
"""
from __future__ import annotations

import collections
import json
import math
import re
from pathlib import Path

from ..gold.engine import gold
from ..statute import Statute

REQUIRED = {
    "id": str, "lang": str, "subset": str, "statute": str, "twin_group": str, "family": str, "variant": str,
    "text": str, "gold_verdict": str, "deciding_element": str, "gold_reason": str, "label": str, "facts": dict,
    "acceptance_criterion": str, "chosen": str, "rejected": str, "rationale": str, "citation": list,
    "normative_source": list, "licence": str, "canary": str, "base_id": str,
}
ENUMS = {"variant": {"base", "true_flip", "placebo", "contested"}, "gold_verdict": {"convict", "acquit", "open"},
         "label": {"settled", "contested"}, "lang": {"de", "fr", "it", "de_lay", "fr_lay", "it_lay"}}   # *_lay: user voice (A9, A16)


def load_items(ds: Path) -> list[dict]:
    rows = []
    for p in sorted((Path(ds) / "eval").glob("*.jsonl")):
        if p.name.startswith("prompts_"):
            continue
        rows += [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
    return rows


# ------------------------------------------------------------------------------------------------------ gates

def check_schema(items):
    bad = []
    for i in items:
        for k, t in REQUIRED.items():
            if not isinstance(i.get(k), t):
                bad.append((i.get("id"), k))
        for k, allowed in ENUMS.items():
            if i.get(k) not in allowed:
                bad.append((i.get("id"), f"{k}={i.get(k)}"))
        if (i.get("label") == "contested") != (i.get("gold_verdict") == "open"):
            bad.append((i.get("id"), "label/verdict mismatch"))
    ids = collections.Counter(i["id"] for i in items)
    bad += [(k, "duplicate id") for k, n in ids.items() if n > 1]
    return "schema", not bad, dict(items=len(items), problems=bad[:20], n_problems=len(bad))


def check_gold(items, statute: Statute):
    bad = []
    for i in items:
        g = gold(statute, i["facts"])
        if (g.verdict, g.deciding_element, g.reason, g.label) != (i["gold_verdict"], i["deciding_element"], i["gold_reason"], i["label"]):
            bad.append(i["id"])
    return "gold_recomputed", not bad, dict(checked=len(items), mismatches=bad[:20], n_mismatches=len(bad))


def check_twins(items):
    """Variants share every slot with their base except changed_slot; roles agree with the verdicts."""
    by = {i["id"]: i for i in items}
    bad = []
    for i in items:
        b = by.get(i["base_id"])
        if b is None:
            bad.append((i["id"], "missing base"))
            continue
        if i["variant"] == "base":
            continue
        if i["subset"] != "battery162":
            diff = sorted(k for k in b["slots"] if b["slots"][k] != i["slots"].get(k))
            if diff != [i["changed_slot"]]:
                bad.append((i["id"], f"slots differ in {diff}"))
        if i["variant"] == "placebo" and i["gold_verdict"] != b["gold_verdict"]:
            bad.append((i["id"], "placebo changes the verdict"))
        if i["variant"] == "true_flip" and i["gold_verdict"] == b["gold_verdict"]:
            bad.append((i["id"], "true flip keeps the verdict"))
        if i["variant"] == "contested" and i["gold_verdict"] != "open":
            bad.append((i["id"], "contested but not open"))
    return "twin_invariants", not bad, dict(problems=bad[:20], n_problems=len(bad))


def check_duplicates(items, allowed_legacy: int = 30):
    c = collections.Counter((i["lang"], i["text"]) for i in items if i["subset"] != "battery162")
    core_dups = sum(n - 1 for n in c.values() if n > 1)
    lc = collections.Counter(i["text"] for i in items if i["subset"] == "battery162")
    leg_dups = sum(n - 1 for n in lc.values() if n > 1)
    cross = {t for (_, t) in c} & set(lc)
    ok = core_dups == 0 and leg_dups <= allowed_legacy and not cross
    return "duplicates", ok, dict(core_duplicates=core_dups, legacy_duplicates=leg_dups,
                                  legacy_documented=allowed_legacy, core_legacy_overlap=len(cross))


STOP = {
    "de": "der die das und ist nicht ein eine einer einem sich auf mit von zu im in wie dass er sie wurde seine ihre".split(),
    "fr": "le la les et est pas un une des du de en au aux qui que il elle son sa ses a été dans pour par sur".split(),
    "it": "il lo la le gli e è non un una dei delle degli del della di in a al alla che ha suo sua per con".split(),
}


def detect_lang(text: str) -> tuple[str, float]:
    toks = re.findall(r"[a-zàâäéèêëïîôöùûüçì]+", text.lower())
    scores = {l: sum(t in set(w) for t in toks) for l, w in STOP.items()}
    best = max(scores, key=scores.get)
    tot = sum(scores.values()) or 1
    return best, scores[best] / tot


def check_language(items):
    bad = []
    margins = []
    for i in items:
        l, conf = detect_lang(i["text"])
        margins.append(conf)
        if l != i["lang"].split("_")[0]:
            bad.append((i["id"], l, round(conf, 2)))
    return "language_id", not bad, dict(checked=len(items), mismatches=bad[:20], min_share=round(min(margins), 3))


PII_PATTERNS = {
    "email": r"[\w.+-]+@[\w-]+\.[\w.]+",
    "phone_ch": r"(?<![\d.])(?:\+41|0041|\b0)\s?\d{2}\s?\d{3}\s?\d{2}\s?\d{2}\b",
    "ahv": r"\b756[.\s]?\d{4}[.\s]?\d{4}[.\s]?\d{2}\b",
    "iban_ch": r"\bCH\d{2}\s?(?:\d{4}\s?){4}\d\b",
    "street_address": r"\b[A-ZÄÖÜ][a-zäöüé]+(?:strasse|gasse|weg|platz)\s+\d+\b|\b(?:rue|avenue|chemin|via|viale|piazza)\s+[A-Z][a-zàâçéèêëîïôûùü][\w'-]*\s+\d+\b",
    "postcode_town": r"\b[1-9]\d{3}\s+[A-ZÄÖÜ][a-zäöüé]+\b",
    "url": r"https?://\S+",
}
# A gazetteer of frequent Swiss given names and surnames (Federal Statistical Office top lists, abbreviated). A hit on a
# capitalised token outside the allow-list fails the gate; the allow-list below records each token cleared and why.
# A gazetteer cannot catch every name: free-text notes in the review records are also checked by reading (A22).
NAMES = set("""Daniel Peter Thomas Martin Christian Hans Michael Andreas Marco David Stefan Markus Urs Bruno Walter Luca
Maria Anna Ursula Sandra Ruth Elisabeth Monika Barbara Claudia Nicole Laura Sarah Julia Lea Marie Sophie Emma Mia Noah Leon
Müller Meier Schmid Keller Weber Huber Schneider Meyer Steiner Fischer Gerber Brunner Baumann Frei Zimmermann Moser Widmer
Wyss Graf Roth Bianchi Rossi Ferrari Russo Colombo Bernasconi Martin Favre Rochat Bonvin Morel Dubois Girard Mercier
Erwin Kurt Werner Ernst Rolf Heinz Fritz Paul Josef Beat Reto Roger Rene René Pierre Jean Jacques Michel Philippe Alain
Giuseppe Mario Franco Ruth Verena Heidi Rosa Esther Marianne Christine Silvia Brigitte""".split())
# Tokens that are ordinary words in this domain, not names: "Christian" is the religion adjective in English review
# text (the dataset's actors are generic and never named).
ALLOW: set[str] = {"Christian"}


# Words that follow a year in the court notes and are not towns ("2013 Muslims", "2019 Facebook").
NOT_TOWNS = {"Muslims", "Jews", "Facebook", "Twitter", "Instagram", "YouTube", "TikTok", "Telegram"}


def pii_hits(text: str) -> list[tuple[str, str]]:
    hits = [(k, m.group(0)) for k, p in PII_PATTERNS.items() for m in re.finditer(p, text)
            if not (k == "postcode_town" and m.group(0).split()[-1] in NOT_TOWNS)]
    for tok in re.findall(r"\b[A-ZÄÖÜ][a-zäöüéèàì]+\b", text):
        if tok in NAMES and tok not in ALLOW:
            hits.append(("name_gazetteer", tok))
    return hits


def check_pii(items, responses: list[dict] | None = None, metadata: list[dict] | None = None):
    hits = []
    for i in items:
        for f in ("text", "chosen", "rejected", "rejected_minimal", "acceptance_criterion", "rationale", "scope_note",
                  "chosen_with_scope"):
            for h in pii_hits(i.get(f) or ""):
                hits.append((i["id"], f, *h))
    for r in responses or []:
        for h in pii_hits(r.get("text") or ""):
            hits.append((r.get("prompt_id"), "response", *h))
    for m in metadata or []:
        for h in pii_hits(json.dumps(m, ensure_ascii=False)):
            if h[0] != "url":
                hits.append((m.get("id"), "metadata", *h))
    return "pii", not hits, dict(hits=hits[:30], n_hits=len(hits),
                                 scanned=dict(items=len(items), responses=len(responses or []), metadata=len(metadata or [])))


def check_canary(items):
    c = {i["canary"] for i in items}
    return "canary", len(c) == 1 and all("CANARY" in x for x in c), dict(values=sorted(c))


# ------------------------------------------------------------------------------------------------------ reports

def distinct_n(texts: list[str], n: int) -> float:
    grams, total = set(), 0
    for t in texts:
        toks = t.lower().split()
        g = list(zip(*[toks[k:] for k in range(n)]))
        grams.update(g)
        total += len(g)
    return len(grams) / total if total else float("nan")


def describe(items):
    """Descriptive statistics (any statute): counts per family, variant, verdict, reason, label and per element value,
    computed on the first language (the others are translations of the same scenarios)."""
    core = [i for i in items if i["subset"] != "battery162"]
    first = sorted({i["lang"] for i in core})[0] if core else None
    ref = [i for i in core if i["lang"] == first]
    out = dict(
        items=len(items), core=len(core), battery162=len(items) - len(core),
        by_lang=dict(collections.Counter(i["lang"] for i in items)),
        by_family=dict(collections.Counter(i["family"] for i in ref)),
        by_variant=dict(collections.Counter(i["variant"] for i in ref)),
        by_verdict=dict(collections.Counter(i["gold_verdict"] for i in ref)),
        by_reason=dict(collections.Counter(i["gold_reason"] for i in ref)),
        by_label=dict(collections.Counter(i["label"] for i in ref)),
        by_wording_family=dict(collections.Counter(i.get("wording_family") for i in ref)),
        twin_groups=len({i["twin_group"] for i in core}),
    )
    for el in sorted({k for i in ref for k in i.get("facts", {})}):
        if el != "act_date":
            out[f"by_{el}"] = dict(collections.Counter(i["facts"][el] for i in ref))
    div = {}
    for l in sorted({i["lang"] for i in core}):
        texts = [i["text"] for i in core if i["lang"] == l]
        lens = [len(t.split()) for t in texts]
        slot_cov = collections.defaultdict(set)
        for i in core:
            if i["lang"] == l:
                for k, v in i["slots"].items():
                    slot_cov[k].add(v)
        cells = collections.defaultdict(set)
        for i in core:
            if i["lang"] == l and "act" in i.get("slots", {}) and "paragraph" in i.get("facts", {}):
                cells[(i["facts"]["paragraph"], i["facts"].get("characteristic"))].add(i["slots"]["act"])
        div[l] = dict(items=len(texts), distinct_1=round(distinct_n(texts, 1), 4), distinct_2=round(distinct_n(texts, 2), 4),
                      distinct_3=round(distinct_n(texts, 3), 4), mean_words=round(sum(lens) / len(lens), 1),
                      min_words=min(lens), max_words=max(lens),
                      slot_values_used={k: len(v) for k, v in slot_cov.items()},
                      wordings_per_paragraph_characteristic_cell=dict(
                          min=min(len(v) for v in cells.values()), median=sorted(len(v) for v in cells.values())[len(cells) // 2]) if cells else None)
    out["diversity"] = div
    return out


def mass_report(responses_dir: Path) -> dict:
    out = {}
    for p in sorted(Path(responses_dir).glob("*.jsonl")):
        ms = [r["extra"]["mass"] for r in (json.loads(l) for l in p.read_text().splitlines() if l.strip())
              if isinstance(r.get("extra"), dict) and isinstance(r["extra"].get("mass"), (int, float))]
        if ms:
            out[p.stem] = dict(n=len(ms), min=round(min(ms), 6), median=round(sorted(ms)[len(ms) // 2], 6))
    return out


def check_sources(statute: Statute):
    """Every normative source is pinned: no TODO left from the scaffold, every statute text (an `eli` source) has a
    stored file and text hash, and the stored texts still match their hashes."""
    from ..statute import verify_sources
    todo, unpinned = [], []

    def walk(key, v):
        if isinstance(v, str) and "TODO" in v:
            todo.append(key)
        elif isinstance(v, dict):
            for x in v.values():
                walk(key, x)
        elif isinstance(v, list):
            for x in v:
                walk(key, x)
    for k, src in statute.sources.items():
        walk(k, src)
        if "eli" in src and not ("file" in src and src.get("text_sha256")):
            unpinned.append(k)
    problems = verify_sources(statute)
    return "sources", not (todo or unpinned or problems), dict(todo=sorted(set(todo)), unpinned=unpinned,
                                                                  hash_problems=problems)


def run_all(ds: Path, statute: Statute) -> dict:
    ds = Path(ds)
    items = load_items(ds)
    resp = []
    for p in sorted((ds / "responses").glob("*.jsonl")):
        resp += [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
    meta_p = ds / "metadata" / "items.jsonl"
    meta = [json.loads(l) for l in meta_p.read_text(encoding="utf-8").splitlines() if l.strip()] if meta_p.exists() else []
    # released review records (judgements, annotations, court checks) and the exploratory splits are scanned too
    for p in sorted((ds / "review").rglob("*")) if (ds / "review").exists() else []:
        if p.suffix in (".json", ".jsonl", ".tsv"):
            meta.append(dict(id=str(p.relative_to(ds)), record=p.read_text(encoding="utf-8")))
    for sub in ("dignity", "paraphrase"):
        for p in sorted((ds / sub).rglob("*.jsonl")) if (ds / sub).exists() else []:
            meta += [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
    gates = [check_schema(items), check_gold(items, statute), check_twins(items), check_duplicates(items),
             check_language(items), check_pii(items, resp, meta), check_canary(items), check_sources(statute)]
    return dict(passed=all(g[1] for g in gates), gates={g[0]: dict(passed=g[1], **g[2]) for g in gates},
                describe=describe(items), answer_token_mass=mass_report(ds / "responses"))
