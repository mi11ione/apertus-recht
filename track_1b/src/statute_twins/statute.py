"""Load and validate a statute element model (``statutes/<id>/statute.yaml``)."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

KINDS = {"date", "covered_set", "enum", "bool"}


class StatuteError(ValueError):
    pass


def _date(v: Any) -> dt.date | None:
    if v is None:
        return None
    if isinstance(v, dt.date):
        return v
    return dt.date.fromisoformat(str(v))


@dataclass
class Element:
    id: str
    kind: str
    label: dict
    authority: list[str]
    values: dict = field(default_factory=dict)
    in_force_from: dt.date | None = None
    depends_on: str | None = None
    fail_reason: str = ""
    contested_reason: str = ""
    raw: dict = field(default_factory=dict)


@dataclass
class Statute:
    id: str
    version: str
    citation: dict
    title: dict
    sources: dict
    elements: list[Element]
    path: Path
    raw: dict

    def element(self, eid: str) -> Element:
        for e in self.elements:
            if e.id == eid:
                return e
        raise KeyError(eid)

    @property
    def element_ids(self) -> list[str]:
        return [e.id for e in self.elements]

    def source_file(self, key: str, lang: str) -> Path:
        src = self.sources[key]
        return (self.path.parent / src["file"].format(lang=lang)).resolve()

    def sha256(self) -> str:
        """Hash of the statute file itself; recorded in every generated item (provenance)."""
        return hashlib.sha256(self.path.read_bytes()).hexdigest()


def load(path: str | Path) -> Statute:
    path = Path(path)
    if path.is_dir():
        path = path / "statute.yaml"
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if raw.get("schema") != "statute-twins/v1":
        raise StatuteError(f"{path}: unknown schema {raw.get('schema')!r}")
    sources = raw.get("sources") or {}
    elements = []
    for e in raw["elements"]:
        kind = e["kind"]
        if kind not in KINDS:
            raise StatuteError(f"{e['id']}: unknown kind {kind}")
        auth = e.get("authority") or []
        for a in auth:
            if a not in sources:
                raise StatuteError(f"{e['id']}: authority {a!r} is not a declared source")
        values = {}
        for k, v in (e.get("values") or {}).items():
            v = dict(v or {})
            for a in v.get("authority", []) or []:
                if a not in sources:
                    raise StatuteError(f"{e['id']}.{k}: authority {a!r} is not a declared source")
            if "covered_from" in v:
                v["covered_from"] = _date(v["covered_from"])
            if kind == "enum" and v.get("satisfied") not in (True, False, "contested"):
                raise StatuteError(f"{e['id']}.{k}: satisfied must be true, false or contested")
            values[k] = v
        if kind == "covered_set" and not e.get("depends_on"):
            raise StatuteError(f"{e['id']}: covered_set needs depends_on (a date element)")
        elements.append(Element(id=e["id"], kind=kind, label=e.get("label", {}), authority=auth, values=values,
                                in_force_from=_date(e.get("in_force_from")), depends_on=e.get("depends_on"),
                                fail_reason=e.get("fail_reason", ""), contested_reason=e.get("contested_reason", ""), raw=e))
    ids = [e.id for e in elements]
    if len(set(ids)) != len(ids):
        raise StatuteError("duplicate element ids")
    for e in elements:
        if e.depends_on and e.depends_on not in ids:
            raise StatuteError(f"{e.id}: depends_on {e.depends_on!r} is not an element")
    return Statute(id=raw["id"], version=str(raw.get("version", "0")), citation=raw.get("citation", {}),
                   title=raw.get("title", {}), sources=sources, elements=elements, path=path, raw=raw)


def verify_sources(st: Statute) -> list[str]:
    """Recompute the text hash of every pinned source file and compare it with the YAML. Returns a list of problems."""
    problems = []
    for key, src in st.sources.items():
        if "file" not in src:
            continue
        expected = src.get("text_sha256")
        langs = list(expected) if isinstance(expected, dict) else ["de"]
        for lang in langs:
            f = st.source_file(key, lang)
            if not f.exists():
                problems.append(f"{key}/{lang}: missing {f}")
                continue
            rec = json.loads(f.read_text(encoding="utf-8"))
            if "paragraphs" in rec:
                got = hashlib.sha256("\n".join(rec["paragraphs"]).encode()).hexdigest()
                if rec.get("text_sha256") != got:
                    problems.append(f"{key}/{lang}: stored text_sha256 does not match the stored paragraphs")
                if isinstance(expected, dict) and expected.get(lang) != got:
                    problems.append(f"{key}/{lang}: YAML hash {expected.get(lang)} != text {got}")
            elif "regeste" in rec:
                for l, txt in rec["regeste"].items():
                    if hashlib.sha256(txt.encode()).hexdigest() != rec["regeste_sha256"][l]:
                        problems.append(f"{key}/{l}: regeste hash mismatch")
    return problems
