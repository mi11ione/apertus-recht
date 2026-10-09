---
license: cdla-permissive-2.0
language: [de, fr, it]
pretty_name: "Apertus-Recht: Art. 261bis StGB minimal-twin scenarios"
size_categories: [1K<n<10K]
task_categories: [text-classification]
tags: [legal, switzerland, evaluation, behavioural-alignment, apertus, minimal-pairs]
configs:
  - config_name: core
    data_files:
      - {split: de, path: eval/core_de.jsonl}
      - {split: fr, path: eval/core_fr.jsonl}
      - {split: it, path: eval/core_it.jsonl}
  - config_name: battery162
    data_files: [{split: de, path: eval/battery162.jsonl}]
  - config_name: prompts
    data_files:
      - {split: de, path: eval/prompts_core_de.jsonl}
      - {split: fr, path: eval/prompts_core_fr.jsonl}
      - {split: it, path: eval/prompts_core_it.jsonl}
      - {split: battery162, path: eval/prompts_battery162.jsonl}
  - config_name: metadata
    data_files: [{split: items, path: metadata/items.jsonl}]
---

# Apertus-Recht: Art. 261bis StGB minimal-twin scenarios (DE / FR / IT)

1980 scenarios (660 per language in DE, FR and IT) about the Swiss racial-discrimination offence,
Art. 261bis StGB / CP, plus the 162-item German exploration battery on which the stage and build columns
were measured. Every scenario belongs to a **twin group**: a base case and variants that each change exactly **one
legal fact** (public ↔ private setting, protected ↔ unprotected characteristic, before ↔ after the 1 July 2020
extension, before ↔ after entry into force in 1995) or one irrelevant detail (**placebos**: family wording of a public
statement, a synonym of the characteristic, a date that does not matter). The **gold verdict is computed by code** from
the pinned statute text and BGE 130 IV 111 E. 5.2, never written by hand.

## Dataset Details
- **Curated by:** the Apertus-Recht team (Hack Apertus 2026, Track 1B, Swiss Voices › Behavioural Alignment).
- **Language(s):** German, French, Italian (Swiss legal register; the official statute terms of each language).
- **License:** CDLA-Permissive-2.0 (all items; per-item licence components in `metadata/items.jsonl`).
- **Git repository:** https://github.com/mi11ione/apertus-recht (generator, gold engine, harness, tests; Apache-2.0).
- **Version:** 1.0.0 (generator 1.0.0, seed 261). Changelog at the end.

## Uses
### Direct Use
Evaluating whether a language model applies the Swiss law in force when a user asks a local legal-information
assistant whether a statement is punishable under Art. 261bis. The model answers each scenario at five prompt rungs
(R0: plain question; R1: elements named; R2: + publicity rule of BGE 130 IV 111 and the list; R3: + "the list is
closed"; R4: + the 1 July 2020 date clause) in two answer framings (Ja/Nein; "Urteil: schuldig / nicht schuldig"). The
twins read back **which element** a model gets wrong, not only how often.
### Out-of-Scope Use
Not legal advice and not a model of every element of the offence: intent is fixed, the Abs. 4 dignity threshold is
written to be met, Abs. 3 and 5 are not covered. Not a training set (canary string in every item). Contains no hateful
text; acts are described abstractly in the statute's vocabulary.
### Specifications
- **Use case → specification:** the question a person asks about their own or someone else's speech; the elements the
  answer turns on (publicity, characteristic, date) are exactly the slots the twins vary.
- **Languages** follow where the article is litigated: of the decisions that cite BGE 130 IV 111, most are French- and
  German-language (court-validation pool: {'de': 67, 'fr': 79, 'it': 4}).
- **Prompt rungs** model the retrieval levels of an assistant (no law in context → statute and leading case pasted in).
- **Acceptance criteria, chosen / rejected answers, settled / contested labels and a normative source** are given for
  every item (Track 1B behavioural-alignment requirements).

## Dataset Structure
`eval/core_<lang>.jsonl` (one row per scenario), `eval/battery162.jsonl`, `eval/prompts_*.jsonl` (one row per scenario
× rung × framing: the exact user message, the assistant prefix and the two candidate answers), `metadata/items.jsonl`,
`metadata/sources.json`, `metadata/generator/` (the YAML the items were generated from), `responses/` (model responses,
one file per model build), `MANIFEST.json` (sha256 of every file).

Main fields: `id`, `lang`, `twin_group`, `family`, `variant` (base / true_flip / placebo / contested), `changed_slot`,
`base_id`, `slots` (template ids), `facts` (the legal facts), `text`, `gold_verdict` (convict / acquit / open),
`deciding_element`, `gold_reason`, `label` (settled / contested), `trap`, `acceptance_criterion`, `chosen`, `rejected`,
`rationale` (the element-by-element derivation), `citation`, `normative_source`, `split` (fit / heldout wording family),
`licence`, `canary`.

| family (DE count) | what changes | twin groups |
|---|---|---|
| SET | public → private setting; family-worded public placebo | 55 |
| CHAR | protected → unprotected characteristic; synonym placebo | 60 |
| CHARX | protected → two unprotected characteristics | 20 |
| DATE_SO | sexual orientation 2021–25 → before 1 Jul 2020; boundary placebo (1 Jul / Aug 2020) | 35 |
| DATE_CTRL | race/ethnicity/religion 2021–25 → 2018–20 (placebo: still protected) and → 1993/94 (before entry into force) | 25 |
| CONTESTED | public → fact-dependent setting (open); family-worded placebo | 15 |
| WORDING | other wording of the same paragraph; another paragraph | 10 |

Per language: 220 base, 215 true flips, 210 placebos,
15 contested. Verdicts: 430 convict, 215 acquit,
15 open. Characteristics: sexual_orientation 175, ethnicity 154, religion 137, race 94, sex 18, age 17, gender_identity 16, canton 16, occupation 16, disability 9, political_opinion 8.
Paragraphs: abs1 220, abs2 218, abs4 222. Diversity (DE): 8 frames,
18 act wordings in 3 wording families, 29 settings,
33 group phrases, 14 dates, 12 places,
8 actors; mean 44.1 words; distinct-2 0.0522, distinct-3 0.099 (templated by design).

## Dataset Creation
### Curation Rationale
Apertus is trained on Swiss court decisions, including BGE 130 IV 111 itself, yet plain-chat answers convict for
statements made only within the family and for characteristics outside the closed list (see the technical report). A
minimal-twin set with computed gold separates *which* element of the law a model applies from how often it is right,
and makes each wrong element measurable across training stages and model builds.
### Source Data
Normative sources only (all public domain, Swiss Copyright Act Art. 5): Art. 261bis StGB in the versions before and since
1 July 2020 and Art. 2 StGB (Fedlex ELI eli/cc/54/757_781_799, DE/FR/IT, sha256-pinned, `metadata/sources.json`), the
amendment footnotes (AS 1994 2887; AS 2020 1609), and the Regeste of BGE 130 IV 111 (DE/FR/IT).
#### Data Collection
No data was collected from people. Scenarios are generated from YAML templates (`metadata/generator/`) by a seeded,
deterministic generator: `statute-twins build` reproduces every file byte for byte (checked by `make run`).
#### Source Data Producers and Data Subjects
Templates: written by the team with Claude Code agents (German), translated by Claude agents (French, Italian),
reviewed as described below. There are **no data subjects**: actors are generic ("a man", "a student"), places are
cities, groups are described by their characteristic.
#### Ownership and Consent Management
The team owns the generated text and releases it under CDLA-Permissive-2.0. No personal data and no people: there are
no data subjects, and no human annotators or reviewers took part (all labelling steps are reproducible agent runs).
Anyone who extends the set with human reviewers or human-written scenarios uses the consent and AI-use form in
`docs/consent-template.md` (pseudonymised reviewers, signed forms kept by the maintainers, withdrawal before each
release). **AI permissions:** generated with AI assistance (declared); may be used to evaluate and
to train AI systems under the licence; the canary string asks crawlers to exclude it from training corpora.
#### Data Processing and Quality Control
Automated gates (`statute-twins qc`, all passing for this release): schema; **gold recomputed** from the facts for every
item; twin invariants (each variant differs from its base in exactly one slot; placebos keep and true flips change the
verdict); duplicates (0 in the core set); language identity; **PII scan**
(Swiss phone, AHV, IBAN, e-mail, addresses, name gazetteer) over items, responses and metadata:
0 hits; canary. The generator refuses to build if a variant changes more than one slot, if the
gold engine's role differs from the design, or if a month-precision date's verdict depends on the day. Statute tests
check the closed-list terms and the amendment dates against the official Fedlex text and footnotes, and mutation tests
check that changing one rule flips exactly the items that rule governs.
- **Translation:** FR/IT by Claude agents with the official CP terms; blind back-translation into German by separate
  agents; comparison for legal facts: 0 critical, 3 minor findings, all fixed (`metadata/generator/` reflects the fixes).
- **Contamination** against `voilaj/swiss-caselaw` (listed in the Apertus v1.5 training data; revision
  c4158e6; 1,069,365 decisions, all 121 data files including GE, VD and BVGer): of
  35,241 distinct word 13-grams of our items, 0 scenario 13-grams occur in the corpus
  (0 statute-derived). Exposure of the law itself: 147
  decisions mention BGE 130 IV 111, 754 mention Art. 261bis.
#### Data Instance Licenses
Every item: CDLA-Permissive-2.0 (original text). Components cited by each item (statute, amendment, BGE) are public
domain under URG Art. 5; listed per item in `metadata/items.jsonl` (`licence_components`). Model responses in
`responses/` are outputs of Apertus (Apache-2.0 model licence) and Qwen3 (Apache-2.0), released under CDLA-Permissive-2.0.

### Annotations
#### Annotation Process
Gold labels are computed, not annotated. Annotation checks them: 960 items (all 660 German items and
a stratified sample in FR and IT) were labelled blind (opaque ids, no access to the code or the gold) by six Claude
agents following `docs/annotation-guidelines.md` (in the repository). Agreement with the code gold on settled items:
939/939; deciding element on acquittals: 315/315; Cohen's κ
(3 classes, all items) 1.000. In the first round 7 of 21 contested items were labelled with a verdict and one
contested setting was read as clearly private by 5/5 annotators; that setting and an anachronism the annotators found
(acts in 1993/94 posted online) were fixed before any model result was analysed (pre-registration amendment A3) and the
changed items re-annotated.
**Adjudication** of every annotator disagreement, every contested item and a blind 10% sample of settled items by
two independent agent adjudicators, 115 items (blind sample 94, contested 21, annotator disagreements 0); adjudicators agree on 115/115; gold wrong: 0/94 in the blind sample of settled items (Wilson 95% upper bound 3.9%), 0/21 contested items.
**Court validation** of the gold engine against real decisions: 150 decisions triaged; 30 in scope; engine agrees with the court in 30/30 (Wilson 95% 0.89-1.00); 8 out of scope (unmodelled grounds), 27 unextractable, 85 excluded; every tuple extracted twice by independent agents, conflicts settled by a third (amendment A4).
#### Annotator Details
All annotation, adjudication and court-tuple extraction was done by Claude agents (Anthropic), declared as AI, working
blind (opaque ids, no access to code or gold). No human labels: every label in this release can be regenerated by
anyone with the same instructions (`docs/annotation-guidelines.md` and the scripts in the repository). The agents share a
model family with the generator's author, so their agreement rules out reading errors, not a shared misconception of the
law; the statute tests against the official text and the court validation check the law itself.

## Risks, Bias, and Limitations
- One statute; templated scenarios (low lexical diversity by design); intent and the dignity threshold are fixed.
- Contested items are few (15 per language) and their verdict is open by construction.
- FR/IT are translations, checked by blind back-translation and spot checks, not native-written.
- Model responses come from specific builds; the Public AI endpoint named `swiss-ai/apertus-v1.5-8b` serves the 70B
  (evidence in the repository's `docs/builds.md`); its rows are labelled 70B.
### Personally Identifiable Information
None: no names, no identifiers; PII gate result above.
### Sensitive Information
The scenarios mention protected characteristics (race, ethnicity, religion, sexual orientation, gender identity, etc.)
of **groups**, as the statute requires; no individual's characteristic is described and no hateful wording is quoted.
### Recommendations
Score with both framings and read the element table, not a single accuracy; report the build (precision, conversion)
alongside results, since 4-bit conversions changed verdicts in our measurements.

## Model responses in this release
19 runs (`responses/<run>.jsonl` with `<run>.meta.json`): 8b-bf16-DPO, 8b-bf16-RLVR, 8b-bf16-blend-RLVR-DPO-a0.25, 8b-bf16-blend-RLVR-DPO-a0.5, 8b-bf16-blend-RLVR-DPO-a0.75, 8b-gguf-q4_k_m, 8b-gguf-q4_k_m-cpu-core, 8b-gguf-q8_0, 8b-mlx4-DPO, 8b-mlx4-RLVR, 8b-mlx4-SFT, 8b-mlx4-base-completion, 8b-mlx4-final, publicai-70b-fc, publicai-70b-fc-core, publicai-70b-fc-core-fr, publicai-70b-fc-core-it, publicai-70b-gen, qwen3-8b-mlx4.

## Changelog
- 1.0.0 (2026-10): first release. Generator 1.0.0, seed 261. Files and hashes: `MANIFEST.json` (63 files).

## Dataset Card Contact
Via the Git repository's issue tracker: https://github.com/mi11ione/apertus-recht.
