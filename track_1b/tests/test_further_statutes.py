"""A second statute released next to the main one (dataset/stgb_179ter): found by the self-check, regenerated
byte-identically from its YAML, and scored by the same results code."""
import json
import shutil
from pathlib import Path

from statute_twins import dataset
from statute_twins.cli import compute_results, further_statutes

ROOT = Path(__file__).resolve().parents[1]


def test_further_statute_is_found_with_its_results_file(monkeypatch):
    monkeypatch.chdir(ROOT)
    found = {x["name"]: x for x in further_statutes(Path("dataset"))}
    assert "179ter" in found
    assert found["179ter"]["statute"] == Path("statutes/stgb_179ter")
    assert found["179ter"]["results"] == Path("results/results_179ter.json")


def test_179ter_release_regenerates_from_its_yaml():
    assert dataset.verify(ROOT / "statutes/stgb_179ter", ROOT / "dataset/stgb_179ter") == []


def test_results_code_scores_the_second_statute(tmp_path):
    # a perfect responder: lo = +4 where the law convicts, -4 where it acquits; every rung and framing
    shutil.copytree(ROOT / "dataset/stgb_179ter/eval", tmp_path / "eval")
    items = {json.loads(l)["id"]: json.loads(l) for l in (tmp_path / "eval/core_de.jsonl").read_text().splitlines()}
    rows = []
    for l in (tmp_path / "eval/prompts_core_de.jsonl").read_text().splitlines():
        p = json.loads(l)
        g = items[p["item_id"]]["gold_verdict"]
        rows.append(dict(prompt_id=p["prompt_id"], item_id=p["item_id"], lang="de", rung=p["rung"],
                         framing=p["framing"], lo_conv=4.0 if g == "convict" else -4.0))
    (tmp_path / "responses").mkdir()
    (tmp_path / "responses/perfect.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    res = compute_results(tmp_path, None, tmp_path / "responses")["runs"]["perfect"]
    acc = [a for a in res["accuracy"] if a.get("subset") == "core"]
    assert acc and all(a["balanced_accuracy"] == 1.0 for a in acc)
    assert {a["rung"] for a in acc} == {"R0", "R1", "R2"}
