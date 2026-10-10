# Pre-registration: held-out read-back test and red/amber rule

Frozen on 2026-10-09 before any model scored the generated core set (`dataset/eval/core_*.jsonl`). The hashes of every
file named below are in `LOCK.json`; the commit that adds this file is its timestamp. Any later change to these files
is a new, separately reported analysis, and the frozen result is reported as well.

## Hypothesis
Apertus applies a law that differs from Art. 261bis StGB in identifiable elements. A read-back of that applied law,
fitted on wording families A and B, predicts the model's own verdicts on the held-out wording family C better than the
statute does.

## Data
* Items: `dataset/eval/core_de.jsonl`, settled items only (`label == "settled"`). FIT split = wording families A, B;
  HELDOUT split = family C (`split` field, set by `design.yaml: heldout_wording_family`).
* Model runs (planned, in this order): Apertus v1.5 70B via Public AI, exact forced choice (requested model name
  `swiss-ai/apertus-v1.5-8b`, which serves the 70B; see `docs/builds.md`), rungs R0, R3, R4, framings conv and ver,
  temperature 0, through the team's cost-capped gateway. FR and IT runs follow the same protocol after the
  translation review. 8B runs on a CPU CI runner (GGUF Q4_K_M) follow when available.

## Read-back and test (code: `src/statute_twins/analysis/heldout.py`)
* Per model × rung × framing, each legal slot value is "treated as satisfied" iff the model convicts at least half of
  the FIT items that carry the value and whose other legal values satisfy the statute. Unobserved values default to the
  statute. Prediction: convict iff all legal values are treated as satisfied.
* Metric: accuracy in predicting the model's decisions on HELDOUT items; baseline: the statute's gold verdict.
* Anchored framing: the 95% bootstrap CI (2,000 resamples, seed 0) of the mean log-odds of the HELDOUT base items is
  above 0.
* **Pass criterion, per rung: read-back accuracy − statute accuracy ≥ 0.15 in every anchored framing.**
* If a rung fails, its headline is the per-element effect table (below), not the read-back.

## Red / amber rule (code: `src/statute_twins/analysis/results.py`)
Per edit (one-slot change that the statute decides differently), rung and framing, from 95% item-bootstrap CIs of the
mean log-odds of the variant V and the reference Ref: F (in force) iff CI(V) > 0 and CI(Ref) > 0; a (applied) iff
CI(V) < 0 and CI(Ref) > 0; u (unanchored) iff CI(Ref) is not above 0; ? otherwise. Red = F in every anchored framing,
amber = F in some, none = F in none.

## Gold
Computed by `src/statute_twins/gold/engine.py` from `statutes/stgb_261bis/statute.yaml`. Gold-error rate: from human
adjudication (Roman) of every annotator disagreement, every contested item and a blind 10% sample of settled items,
reported with a Wilson 95% interval.
