"""Oracle test: the harness analysis, run on the imported responses, reproduces the numbers published by the spike
analyses (spikes/gguf/results.md "Red edits" table; spikes/live/results.md section (b)). Values: V convicted k/n and
mean log-odds of V, rounded to one decimal as published."""
import pytest

from statute_twins.analysis import results as R
from statute_twins.generator import legacy
from statute_twins.harness.run import read_jsonl

from conftest import ROOT

PUBLISHED = [
    # run, edit, rung, framing, k, n, mean_v
    ("8b-bf16-DPO", "setting:failed", "R3", "conv", 2, 20, -12.9),
    ("8b-bf16-DPO", "setting:failed", "R3", "ver", 2, 20, -9.5),
    ("8b-bf16-DPO", "characteristic:not_listed|canton", "R3", "conv", 6, 6, 9.8),
    ("8b-bf16-DPO", "characteristic:not_listed|canton", "R3", "ver", 6, 6, 23.0),
    ("8b-bf16-DPO", "characteristic:not_yet_covered", "R3", "conv", 6, 6, 25.9),
    ("8b-bf16-DPO", "characteristic:not_yet_covered", "R3", "ver", 6, 6, 25.3),
    ("8b-gguf-q8_0", "setting:failed", "R3", "conv", 2, 20, -12.2),
    ("8b-gguf-q8_0", "setting:failed", "R3", "ver", 4, 20, -8.8),
    ("8b-gguf-q8_0", "characteristic:not_listed|canton", "R3", "conv", 5, 6, 14.0),
    ("8b-gguf-q8_0", "characteristic:not_listed|canton", "R3", "ver", 6, 6, 24.1),
    ("8b-gguf-q8_0", "characteristic:not_yet_covered", "R3", "conv", 6, 6, 25.4),
    ("8b-gguf-q8_0", "characteristic:not_yet_covered", "R3", "ver", 6, 6, 25.5),
    ("8b-gguf-q4_k_m", "setting:failed", "R3", "conv", 2, 20, -9.5),
    ("8b-gguf-q4_k_m", "setting:failed", "R3", "ver", 3, 20, -10.9),
    ("8b-gguf-q4_k_m", "characteristic:not_listed|canton", "R3", "conv", 3, 6, 2.0),
    ("8b-gguf-q4_k_m", "characteristic:not_listed|canton", "R3", "ver", 6, 6, 11.2),
    ("8b-gguf-q4_k_m", "characteristic:not_yet_covered", "R3", "conv", 6, 6, 23.1),
    ("8b-gguf-q4_k_m", "characteristic:not_yet_covered", "R3", "ver", 6, 6, 19.4),
    ("8b-mlx4-final", "setting:failed", "R3", "conv", 15, 20, 5.8),
    ("8b-mlx4-final", "setting:failed", "R3", "ver", 13, 20, 1.3),
    ("8b-mlx4-final", "characteristic:not_listed|canton", "R3", "conv", 3, 6, 6.8),
    ("8b-mlx4-final", "characteristic:not_listed|canton", "R3", "ver", 6, 6, 13.6),
    ("publicai-70b-fc", "setting:failed", "R3", "conv", 0, 20, -16.1),
    ("publicai-70b-fc", "setting:failed", "R3", "ver", 0, 20, -17.3),
    ("publicai-70b-fc", "characteristic:not_listed|canton", "R3", "conv", 3, 6, 0.9),
    ("publicai-70b-fc", "characteristic:not_listed|canton", "R3", "ver", 6, 6, 12.0),
    ("publicai-70b-fc", "characteristic:not_yet_covered", "R4", "conv", 0, 6, -6.9),
    ("publicai-70b-fc", "characteristic:not_yet_covered", "R4", "ver", 0, 6, -12.7),
    ("publicai-70b-fc", "characteristic:not_yet_covered", "R3", "conv", 6, 6, 14.5),
    ("publicai-70b-fc", "characteristic:not_yet_covered", "R3", "ver", 6, 6, 16.5),
]

# reference (Ref) conviction counts published for the live run (spikes/live/results.md (b))
PUBLISHED_REF = [("publicai-70b-fc", "setting:failed", "R3", "conv", 12), ("publicai-70b-fc", "setting:failed", "R3", "ver", 20),
                 ("publicai-70b-fc", "characteristic:not_yet_covered", "R4", "conv", 1),
                 ("publicai-70b-fc", "characteristic:not_yet_covered", "R4", "ver", 0)]


@pytest.fixture(scope="module")
def edits(d261):
    items = legacy.build_legacy_items(d261)
    out = {}
    for run in sorted({p[0] for p in PUBLISHED}):
        rows = read_jsonl(ROOT / "dataset/responses" / f"{run}.jsonl")
        for e in R.edits(items, rows, R.legacy_pairs(items)):
            out[(run, e["edit"], e["rung"], e["framing"])] = e
    return out


@pytest.mark.parametrize("run, edit, rung, fr, k, n, m", PUBLISHED, ids=lambda x: str(x))
def test_published_red_edit_numbers(edits, run, edit, rung, fr, k, n, m):
    e = edits[(run, edit, rung, fr)]
    assert (e["v_convicted"], e["n"]) == (k, n)
    assert round(e["mean_v"], 1) == m


@pytest.mark.parametrize("run, edit, rung, fr, k", PUBLISHED_REF, ids=lambda x: str(x))
def test_published_reference_counts(edits, run, edit, rung, fr, k):
    assert edits[(run, edit, rung, fr)]["ref_convicted"] == k
