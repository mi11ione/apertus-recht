"""Generic checks that run on every statute folder (so a new statute is covered the moment it exists), plus the
`statute-twins new` scaffold."""
import collections
import re
import subprocess
import sys

import pytest

from statute_twins.generator import build, design, render
from statute_twins.scaffold import scaffold

from conftest import design_dirs


@pytest.mark.parametrize("sdir", design_dirs(), ids=lambda p: p.name)
def test_builds_with_valid_invariants(sdir):
    d = design.load(sdir)
    sc = build.build_scenarios(d)       # raises on any broken invariant
    groups = collections.defaultdict(list)
    for s in sc:
        groups[s.group_id].append(s)
    for g in groups.values():
        for s in g[1:]:
            assert [k for k in g[0].slots if g[0].slots[k] != s.slots[k]] == [s.changed_slot]
    items = build.build_items(d, sc)
    for lang in d.langs:
        texts = [i["text"] for i in items if i["lang"] == lang]
        assert len(set(texts)) == len(texts)
        assert not any(re.search(r"[{}]|\s{2,}", t) for t in texts)
    for p in build.build_prompts(d, items[:3]):
        assert "{" not in p["user"]


@pytest.mark.parametrize("sdir", design_dirs(), ids=lambda p: p.name)
def test_every_reason_has_reference_answers(sdir):
    d = design.load(sdir)
    reasons = {s.gold.reason for s in build.build_scenarios(d)}
    for lang in d.langs:
        assert reasons <= set(d.answers[lang]["chosen"]) and reasons <= set(d.answers[lang]["rejected"])
    accept = d.raw["acceptance"]
    assert {r for r in reasons if r != "convict" and not r.endswith(":contested")} <= set(accept["reasons"])


def test_scaffold_builds_out_of_the_box(tmp_path):
    p = scaffold("stgb_example", tmp_path)
    d = design.load(p)
    items = build.build_items(d, build.build_scenarios(d))
    assert len(items) == 4 * 3 + 4 * 2
    assert {i["variant"] for i in items} == {"base", "true_flip", "placebo"}
    out = tmp_path / "ds"
    r = subprocess.run([sys.executable, "-m", "statute_twins.cli", "build", "--statute", str(p), "--out", str(out)],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    r = subprocess.run([sys.executable, "-m", "statute_twins.cli", "verify", "--statute", str(p), "--dataset", str(out)],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


@pytest.mark.parametrize("sdir", design_dirs(), ids=lambda p: p.name)
def test_qc_gates_pass_for_every_statute(sdir, tmp_path):
    """Regression (dogfood round 1): qc crashed on statutes without a `characteristic` element."""
    out = tmp_path / "ds"
    for cmd in (["build", "--statute", str(sdir), "--out", str(out)],
                ["qc", "--statute", str(sdir), "--dataset", str(out), "--out", str(tmp_path / "qc.json")]):
        r = subprocess.run([sys.executable, "-m", "statute_twins.cli", *cmd], capture_output=True, text=True)
        assert r.returncode == 0, r.stdout + r.stderr
