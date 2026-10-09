# Pre-registration: validation of the gold engine against Swiss court decisions

Frozen before any element tuple was extracted (commit timestamp; hash in `LOCK_court.json`).

## Population and sample
Decisions in `voilaj/swiss-caselaw` (revision c4158e6a49f9bcfcec3eb17e0277501c3a1f6f17) whose text mentions Art. 261bis
StGB/CP. Triage (Claude agents, on excerpts around each mention) keeps decisions that **rule on an Art. 261bis charge
against a specific act** (conviction, acquittal, or confirmation/annulment of either on appeal). Target: 30-50 decisions,
taken in a fixed order: first all decisions that also cite BGE 130 IV 111, then the rest ordered by sha256(decision_id).
Decisions that only mention the article in passing, civil/administrative matters, and procedural rulings are excluded
and counted.

## Element tuple (extracted by Claude agents with a supporting passage, verified by the human reviewer R1)
act date; setting (public / private / unclear, per BGE 130 IV 111 E. 5.2); characteristic (race, ethnicity, religion,
sexual orientation, other: named, unclear); paragraph (Abs. 1-5); the court's outcome on Art. 261bis
(convicted / acquitted / remanded); and, for acquittals, the ground the court gives.

## Rule
* **In scope:** convictions, and acquittals whose ground is a modelled element (publicity, characteristic, temporal
  scope). Acquittals on unmodelled grounds (dignity threshold of Abs. 4, intent, justification, procedure) and
  Abs. 3/5 cases are **out of scope** and counted, not compared. Tuples with an `unclear` modelled element are counted
  as unextractable.
* **Prediction:** the gold engine's verdict on the tuple (`statutes/stgb_261bis/statute.yaml`, unchanged).
* **Disagreement:** in-scope decision where the engine's verdict differs from the court's. Every disagreement is
  catalogued with its cause. Headline: engine-court agreement on in-scope decisions with a Wilson 95% interval, plus the
  counts of out-of-scope and unextractable decisions.
