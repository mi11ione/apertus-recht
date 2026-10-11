"""Write and verify the released dataset (the exact content of the Hugging Face dataset repository).

    dataset/
      eval/core_<lang>.jsonl        generated twin items, one file per language
      eval/battery162.jsonl         the legacy battery (German, verbatim spike texts)
      eval/prompts_<part>.jsonl     every (item, rung, framing) user message with its forced-choice candidates
      eval/prompts_ctrl_<part>.jsonl  A13 controls: the acquittal-direction question (`rev`) and rungs R5a-R5c
      metadata/items.jsonl          per-item licence, provenance and review status
      metadata/sources.json         pinned normative sources with hashes and licences
      metadata/generator/           snapshot of the statute, design, templates, prompts and answers files
      responses/<run>.jsonl         model responses (+ <run>.meta.json)
      MANIFEST.json                 sha256 of every file above

``verify`` regenerates eval/ and metadata/ from the statute folder into a temporary directory and compares hashes, so
a judge can check that every released item and every gold label follows from the pinned YAML.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
from pathlib import Path

from .generator import build, design, legacy

LICENCE_ITEM = "CDLA-Permissive-2.0"
SOURCE_LICENCES = {
    "statute": "public domain (Swiss Copyright Act, Art. 5 para. 1 lit. a: enactments)",
    "amendment": "public domain (URG Art. 5 para. 1 lit. a)",
    "decision": "public domain (URG Art. 5 para. 1 lit. c: decisions); text via voilaj/swiss-caselaw (CC0)",
    "legislative_history": "public domain (URG Art. 5 para. 1 lit. b/c: official reports)",
}


def _jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows), encoding="utf-8")


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def all_items(statute_dir: Path) -> tuple[design.Design, list[dict], list[dict]]:
    d = design.load(statute_dir)
    core = build.build_items(d, build.build_scenarios(d))
    leg = legacy.build_legacy_items(d) if (Path(statute_dir) / "legacy").exists() else []
    return d, core, leg


def item_metadata(d: design.Design, it: dict, reviews: dict) -> dict:
    lic = [dict(component="scenario text, labels, reference answers", licence=LICENCE_ITEM,
                note="original work generated from the templates in metadata/generator")]
    for k in it["normative_source"]:
        src = d.statute.sources[k]
        lic.append(dict(component=f"normative source {k} ({src.get('cite', k)})",
                        licence=SOURCE_LICENCES.get(src.get("kind"), "public domain")))
    prov = dict(it.get("provenance") or {})
    rv = reviews.get(it["id"]) or {}
    return dict(id=it["id"], licence=LICENCE_ITEM, licence_components=lic, provenance=prov,
                template_id=it["template_id"], slots=it["slots"], wording_family=it["wording_family"],
                review=dict(status=rv.get("status", "not_sampled"), reviewer=rv.get("reviewer"), outcome=rv.get("outcome")),
                personal_data="none: no real persons, names or identifiers; actors are generic ('a man', 'a student')",
                canary=it["canary"])


def write_eval(statute_dir: Path, out: Path, reviews: dict | None = None) -> dict:
    statute_dir, out = Path(statute_dir), Path(out)
    d, core, leg = all_items(statute_dir)
    core = [i for i in core if i["subset"] == "core"]    # exploratory subsets (A18: dignity) live in their own folder
    reviews = reviews or {}
    parts = {f"core_{l}": [i for i in core if i["lang"] == l] for l in d.langs}
    if leg:
        parts["battery162"] = leg
    for name, rows in parts.items():
        _jsonl(out / "eval" / f"{name}.jsonl", rows)
        _jsonl(out / "eval" / f"prompts_{name}.jsonl", build.build_prompts(d, rows))
        if name != "battery162" and all("open" in (d.prompts[l].get("framings") or {}) for l in d.langs):
            # free-text questions (generate + judge), kept in their own file so forced-choice prompt files never change
            _jsonl(out / "eval" / f"prompts_open_{name}.jsonl", build.build_prompts(d, rows, rungs=["R0", "R3", "R5"], framings=["open"]))
            # forced choice between each settled item's chosen and rejected reference answer (preference accuracy)
            _jsonl(out / "eval" / f"prompts_pref_{name}.jsonl", build.build_pref_prompts(d, rows))
        lang = rows[0]["lang"] if rows else None
        if name != "battery162" and "rev" in (d.prompts.get(lang, {}).get("framings") or {}):
            # A13 controls (exploratory): the question in the acquittal direction, and the R5 factorial
            from .generator.render import control_rungs
            _jsonl(out / "eval" / f"prompts_ctrl_{name}.jsonl",
                   build.build_prompts(d, rows, rungs=["R0", "R3", "R4", "R5", "R6"], framings=["rev"])
                   + build.build_prompts(d, rows, rungs=control_rungs(d, lang), framings=["conv", "ver"]))
    _jsonl(out / "metadata" / "items.jsonl", [item_metadata(d, i, reviews) for rows in parts.values() for i in rows])
    srcs = {k: dict(v, licence=SOURCE_LICENCES.get(v.get("kind"), "public domain")) for k, v in d.statute.sources.items()}
    (out / "metadata").mkdir(parents=True, exist_ok=True)
    (out / "metadata" / "sources.json").write_text(json.dumps(srcs, ensure_ascii=False, indent=1, sort_keys=True, default=str) + "\n",
                                                  encoding="utf-8")
    gen = out / "metadata" / "generator"
    if gen.exists():
        shutil.rmtree(gen)
    for p in sorted(statute_dir.rglob("*")):
        if p.is_file() and p.suffix in (".yaml", ".json") and "review" not in p.parts:
            q = gen / p.relative_to(statute_dir)
            q.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(p, q)
    src_dir = statute_dir.parent / "sources"
    for k, v in d.statute.sources.items():
        if "file" in v:
            for lang in (v.get("text_sha256") or {"de": None}):
                f = d.statute.source_file(k, lang)
                q = gen / "sources" / f.name
                q.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(f, q)
    return {k: len(v) for k, v in parts.items()}


def run_of(filename: str) -> str:
    """Run id of a response file name (run ids may contain dots, e.g. ...-a0.25.jsonl)."""
    for suf in (".meta.json", ".jsonl"):
        if filename.endswith(suf):
            return filename[: -len(suf)]
    return filename


def manifest(out: Path, exclude_runs: set | None = None) -> dict:
    """sha256 of every released file; `exclude_runs` leaves out response runs still being written."""
    out = Path(out)
    files = {}
    for sub in ("eval", "metadata", "responses", "docs", "review"):
        for p in sorted((out / sub).rglob("*")):
            if p.is_file() and not (exclude_runs and run_of(p.name) in exclude_runs):
                files[str(p.relative_to(out))] = _sha(p)
    m = dict(files=files)
    (out / "MANIFEST.json").write_text(json.dumps(m, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return m


def verify(statute_dir: Path, out: Path, reviews: dict | None = None) -> list[str]:
    """Regenerate eval/ and metadata/ and compare with the released files and the manifest. Returns problems."""
    out = Path(out)
    problems = []
    man = json.loads((out / "MANIFEST.json").read_text())["files"]
    for rel, h in man.items():
        p = out / rel
        if not p.exists():
            problems.append(f"missing {rel}")
        elif _sha(p) != h:
            problems.append(f"hash mismatch {rel}")
    with tempfile.TemporaryDirectory() as tmp:
        write_eval(statute_dir, Path(tmp), reviews)
        for p in sorted(Path(tmp).rglob("*")):
            if p.is_file():
                rel = str(p.relative_to(tmp))
                if rel not in man:
                    problems.append(f"regenerated file not in release: {rel}")
                elif _sha(p) != man[rel]:
                    problems.append(f"regenerated {rel} differs from release")
        released = {r for r in man if r.startswith(("eval/", "metadata/"))}
        regen = {str(p.relative_to(tmp)) for p in Path(tmp).rglob("*") if p.is_file()}
        for r in sorted(released - regen):
            problems.append(f"released file not produced by the generator: {r}")
    return problems
