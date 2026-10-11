"""Pin statute text from Fedlex (the official Swiss federal law platform).

Fedlex publishes every consolidated version of an act as Akoma Ntoso XML. This module finds the consolidation in force on
a given date through the public SPARQL endpoint, downloads the XML, extracts one article by its AKN ``eId`` and stores

    {eli, eid, lang, applicability_date, url, xml_sha256, paragraphs[], text_sha256, fetched}

so that the statute YAML can cite the exact text it encodes and a test can check that the cited text has not drifted.
Standard library only; one request per second; User-Agent ``hackapertus-research/0.1``.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

SPARQL = "https://fedlex.data.admin.ch/sparqlendpoint"
UA = "hackapertus-research/0.1"
LANGS = {"de": "DEU", "fr": "FRA", "it": "ITA", "en": "ENG", "rm": "ROH"}
AKN = "{http://docs.oasis-open.org/legaldocml/ns/akn/3.0}"
_last = [0.0]

QUERY = """PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
SELECT ?d ?f WHERE {{ ?c jolux:isMemberOf <https://fedlex.data.admin.ch/{eli}> ; jolux:dateApplicability ?d .
 ?c jolux:isRealizedBy ?e . ?e jolux:language <http://publications.europa.eu/resource/authority/language/{lang}> .
 ?e jolux:isEmbodiedBy ?m . ?m jolux:userFormat <https://fedlex.data.admin.ch/vocabulary/user-format/xml> .
 ?m jolux:isExemplifiedBy ?f . }} ORDER BY ?d"""


def _get(url: str, data: bytes | None = None, accept: str | None = None) -> bytes:
    wait = 1.0 - (time.time() - _last[0])
    if wait > 0:
        time.sleep(wait)
    headers = {"User-Agent": UA}
    if accept:
        headers["Accept"] = accept
    req = urllib.request.Request(url, data=data, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return r.read()
    finally:
        _last[0] = time.time()


def consolidations(eli: str, lang: str) -> list[tuple[str, str]]:
    """All (applicability_date, xml_url) pairs of an act in one language, oldest first."""
    q = QUERY.format(eli=eli, lang=LANGS[lang])
    body = _get(SPARQL, urllib.parse.urlencode({"query": q}).encode(), "application/sparql-results+json")
    rows = json.loads(body)["results"]["bindings"]
    return [(r["d"]["value"], r["f"]["value"]) for r in rows]


def in_force_on(eli: str, lang: str, date: str) -> tuple[str, str]:
    """The consolidation applicable on ``date`` (ISO): the latest one whose applicability date is <= date."""
    cands = [c for c in consolidations(eli, lang) if c[0] <= date]
    if not cands:
        raise LookupError(f"no {lang} consolidation of {eli} on or before {date}")
    return cands[-1]


def _text(el: ET.Element) -> str:
    """Visible text of an AKN element, without footnotes (authorialNote)."""
    parts: list[str] = []

    def walk(e: ET.Element) -> None:
        if e.tag == AKN + "authorialNote":
            if e.tail:
                parts.append(e.tail)
            return
        if e.text:
            parts.append(e.text)
        for c in e:
            walk(c)
        if e.tail:
            parts.append(e.tail)

    walk(el)
    return re.sub(r"\s+", " ", "".join(parts)).strip()


def _block_list(bl: ET.Element) -> str:
    """One lettered/numbered list (AKN <blockList>) as a single string: the list introduction, then every item as
    "num text" (nested lists rendered recursively), then any wrap-up text, separated by single spaces. Example:
    "Die Verfahrensleitung prüft, ob: a. die Anklageschrift ...; b. die Prozessvoraussetzungen ...; c. ..."."""
    parts: list[str] = []
    for ch in bl:
        if ch.tag in (AKN + "listIntroduction", AKN + "listWrapUp"):
            parts.append(_text(ch))
        elif ch.tag == AKN + "item":
            item: list[str] = []
            for sub in ch:
                if sub.tag == AKN + "num":
                    item.append(_text(sub))
                elif sub.tag == AKN + "blockList":
                    item.append(_block_list(sub))
                else:
                    item.append(_text(sub))
            parts.append(" ".join(t for t in item if t))
    return " ".join(t for t in parts if t)


def extract_article(xml: bytes, eid: str) -> tuple[list[str], list[str]]:
    """(content paragraphs, footnotes) of one article. Paragraphs are the <p> under <content> with footnotes removed;
    a lettered list (<blockList>: introduction plus lit. a, b, c ...) is one paragraph that includes all its items, so a
    paragraph with a list is never dropped and the array stays aligned with the Abs. numbers. Footnotes (amendment
    history: inserting act, in-force date, AS reference) are kept separately. Whitespace normalised."""
    root = ET.fromstring(xml)
    for art in root.iter(AKN + "article"):
        if art.get("eId") == eid:
            paras = []
            for content in art.iter(AKN + "content"):
                for ch in content:
                    if ch.tag == AKN + "p":
                        t = _text(ch)
                    elif ch.tag == AKN + "blockList":
                        t = _block_list(ch)
                    else:
                        continue
                    if t:
                        paras.append(t)
            notes = [re.sub(r"\s+", " ", "".join(n.itertext())).strip() for n in art.iter(AKN + "authorialNote")]
            return paras, notes
    raise KeyError(f"article {eid} not found")


def sha256(b: bytes | str) -> str:
    return hashlib.sha256(b.encode("utf-8") if isinstance(b, str) else b).hexdigest()


def pin(eli: str, eid: str, lang: str, date: str, out_dir: Path) -> dict:
    """Fetch and store one article as in force on ``date``. Returns the stored record."""
    applicability, url = in_force_on(eli, lang, date)
    xml = _get(url)
    paras, notes = extract_article(xml, eid)
    rec = dict(eli=eli, eid=eid, lang=lang, requested_date=date, applicability_date=applicability, url=url,
               xml_sha256=sha256(xml), paragraphs=paras, text_sha256=sha256("\n".join(paras)), notes=notes,
               fetched=time.strftime("%Y-%m-%d"))
    out_dir.mkdir(parents=True, exist_ok=True)
    name = f"{eli.replace('/', '_')}__{eid}__{lang}__{applicability}.json"
    (out_dir / name).write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return rec


def text_hash(paragraphs: list[str]) -> str:
    return sha256("\n".join(paragraphs))
