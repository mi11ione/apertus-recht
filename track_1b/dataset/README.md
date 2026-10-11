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
  - config_name: user_voice
    data_files:
      - {split: de, path: eval/core_de_lay.jsonl}
      - {split: fr, path: eval/core_fr_lay.jsonl}
      - {split: it, path: eval/core_it_lay.jsonl}
  - config_name: battery162
    data_files: [{split: de, path: eval/battery162.jsonl}]
  - config_name: prompts
    data_files:
      - {split: de, path: eval/prompts_core_de.jsonl}
      - {split: fr, path: eval/prompts_core_fr.jsonl}
      - {split: it, path: eval/prompts_core_it.jsonl}
      - {split: de_user_voice, path: eval/prompts_core_de_lay.jsonl}
      - {split: fr_user_voice, path: eval/prompts_core_fr_lay.jsonl}
      - {split: it_user_voice, path: eval/prompts_core_it_lay.jsonl}
      - {split: battery162, path: eval/prompts_battery162.jsonl}
  - config_name: prompts_free_text
    data_files:
      - {split: de, path: eval/prompts_open_core_de.jsonl}
      - {split: fr, path: eval/prompts_open_core_fr.jsonl}
      - {split: it, path: eval/prompts_open_core_it.jsonl}
      - {split: de_user_voice, path: eval/prompts_open_core_de_lay.jsonl}
      - {split: fr_user_voice, path: eval/prompts_open_core_fr_lay.jsonl}
      - {split: it_user_voice, path: eval/prompts_open_core_it_lay.jsonl}
  - config_name: prompts_preference
    data_files:
      - {split: de, path: eval/prompts_pref_core_de.jsonl}
      - {split: fr, path: eval/prompts_pref_core_fr.jsonl}
      - {split: it, path: eval/prompts_pref_core_it.jsonl}
      - {split: de_user_voice, path: eval/prompts_pref_core_de_lay.jsonl}
      - {split: fr_user_voice, path: eval/prompts_pref_core_fr_lay.jsonl}
      - {split: it_user_voice, path: eval/prompts_pref_core_it_lay.jsonl}
  - config_name: metadata
    data_files: [{split: items, path: metadata/items.jsonl}]
  - config_name: dignity_threshold
    data_files:
      - {split: de, path: dignity/eval/dignity_de.jsonl}
      - {split: fr, path: dignity/eval/dignity_fr.jsonl}
      - {split: it, path: dignity/eval/dignity_it.jsonl}
  - config_name: natural_paraphrases
    data_files:
      - {split: de, path: paraphrase/eval/paraphrase_de.jsonl}
      - {split: fr, path: paraphrase/eval/paraphrase_fr.jsonl}
      - {split: it, path: paraphrase/eval/paraphrase_it.jsonl}
  - config_name: stgb_179ter
    data_files: [{split: de, path: stgb_179ter/eval/core_de.jsonl}]
  - config_name: stgb_179ter_prompts
    data_files: [{split: de, path: stgb_179ter/eval/prompts_core_de.jsonl}]
  - config_name: stgb_179ter_responses
    data_files:
      - {split: publicai_70b_179ter, path: stgb_179ter/responses/publicai-70b-179ter.jsonl}

  - config_name: responses
    data_files:
      - {split: 8b_bf16_DPO, path: responses/8b-bf16-DPO.jsonl}
      - {split: 8b_bf16_RLVR, path: responses/8b-bf16-RLVR.jsonl}
      - {split: 8b_bf16_blend_RLVR_DPO_a0_25, path: responses/8b-bf16-blend-RLVR-DPO-a0.25.jsonl}
      - {split: 8b_bf16_blend_RLVR_DPO_a0_5, path: responses/8b-bf16-blend-RLVR-DPO-a0.5.jsonl}
      - {split: 8b_bf16_blend_RLVR_DPO_a0_75, path: responses/8b-bf16-blend-RLVR-DPO-a0.75.jsonl}
      - {split: 8b_gguf_q4_k_m, path: responses/8b-gguf-q4_k_m.jsonl}
      - {split: 8b_gguf_q4_k_m_cpu_core, path: responses/8b-gguf-q4_k_m-cpu-core.jsonl}
      - {split: 8b_gguf_q4_k_m_cpu_core_fr, path: responses/8b-gguf-q4_k_m-cpu-core-fr.jsonl}
      - {split: 8b_gguf_q4_k_m_cpu_core_it, path: responses/8b-gguf-q4_k_m-cpu-core-it.jsonl}
      - {split: 8b_gguf_q4_k_m_cpu_pref, path: responses/8b-gguf-q4_k_m-cpu-pref.jsonl}
      - {split: 8b_gguf_q8_0, path: responses/8b-gguf-q8_0.jsonl}
      - {split: 8b_mlx4_DPO, path: responses/8b-mlx4-DPO.jsonl}
      - {split: 8b_mlx4_RLVR, path: responses/8b-mlx4-RLVR.jsonl}
      - {split: 8b_mlx4_SFT, path: responses/8b-mlx4-SFT.jsonl}
      - {split: 8b_mlx4_base_completion, path: responses/8b-mlx4-base-completion.jsonl}
      - {split: 8b_mlx4_final, path: responses/8b-mlx4-final.jsonl}
      - {split: publicai_70b_ctrl_de, path: responses/publicai-70b-ctrl-de.jsonl}
      - {split: publicai_70b_ctrl_fr, path: responses/publicai-70b-ctrl-fr.jsonl}
      - {split: publicai_70b_ctrl_it, path: responses/publicai-70b-ctrl-it.jsonl}
      - {split: publicai_70b_fc, path: responses/publicai-70b-fc.jsonl}
      - {split: publicai_70b_fc_core, path: responses/publicai-70b-fc-core.jsonl}
      - {split: publicai_70b_fc_core_fr, path: responses/publicai-70b-fc-core-fr.jsonl}
      - {split: publicai_70b_fc_core_it, path: responses/publicai-70b-fc-core-it.jsonl}
      - {split: publicai_70b_fc_lay, path: responses/publicai-70b-fc-lay.jsonl}
      - {split: publicai_70b_fc_lay_fr, path: responses/publicai-70b-fc-lay-fr.jsonl}
      - {split: publicai_70b_fc_lay_it, path: responses/publicai-70b-fc-lay-it.jsonl}
      - {split: publicai_70b_gen, path: responses/publicai-70b-gen.jsonl}
      - {split: publicai_70b_open, path: responses/publicai-70b-open.jsonl}
      - {split: publicai_70b_open_fr, path: responses/publicai-70b-open-fr.jsonl}
      - {split: publicai_70b_open_it, path: responses/publicai-70b-open-it.jsonl}
      - {split: publicai_70b_pref, path: responses/publicai-70b-pref.jsonl}
      - {split: publicai_70b_pref_fr, path: responses/publicai-70b-pref-fr.jsonl}
      - {split: publicai_70b_pref_it, path: responses/publicai-70b-pref-it.jsonl}
      - {split: publicai_70b_r5x_de, path: responses/publicai-70b-r5x-de.jsonl}
      - {split: publicai_70b_r6_fr, path: responses/publicai-70b-r6-fr.jsonl}
      - {split: publicai_70b_r6_it, path: responses/publicai-70b-r6-it.jsonl}
      - {split: qwen3_8b_mlx4, path: responses/qwen3-8b-mlx4.jsonl}

---

# Apertus-Recht: Art. 261bis StGB minimal-twin scenarios (DE / FR / IT)

1980 scenarios (660 per language in DE, FR and IT) about the Swiss racial-discrimination
offence, Art. 261bis StGB / CP; the same scenarios retold as a first-person paraphrase
by a user asking about their own conduct, in all three languages (`user_voice`, language codes `de_lay`, `fr_lay`,
`it_lay`; 660 each; the German acts keep the statute's vocabulary, the French and Italian ones (A16) describe the act
in everyday words); and the 162-item German exploration battery on which
the stage and build columns were measured. Every scenario belongs to a **twin group**: a base case and variants that each change exactly **one
legal fact** (public ↔ private setting, protected ↔ unprotected characteristic, before ↔ after the 1 July 2020
extension, before ↔ after entry into force in 1995) or one irrelevant detail (**placebos**: family wording of a public
statement, a synonym of the characteristic, a date that does not matter). The **gold verdict is computed by code** from
the pinned statute text and BGE 130 IV 111 E. 5.2, never written by hand.

## Dataset Details
- **Curated by:** the Apertus-Recht team (Hack Apertus 2026, Track 1B, Swiss Voices › Behavioural Alignment).
- **Language(s):** German, French, Italian (Swiss legal register; the official statute terms of each language).
- **License:** CDLA-Permissive-2.0 (all items; per-item licence components in `metadata/items.jsonl`).
- **Git repository:** https://github.com/mi11ione/apertus-recht (generator, gold engine, harness, tests; Apache-2.0).
- **Version:** 1.5.0 (generator 1.0.0, seed 261). Changelog at the end.

## Uses
### Direct Use
Evaluating whether a language model applies the Swiss law in force when a user asks a local legal-information
assistant whether a statement is punishable under Art. 261bis. The model answers each scenario at six prompt rungs
(R0: plain question; R1: elements named; R2: + a one-sentence paraphrase of BGE 130 IV 111 and the list; R3: + "the
list is closed" and that gender identity and sex are not covered; R4: + "sexual orientation only from 1 July 2020"; R5: the verbatim Fedlex text of Art. 261bis and
Art. 2 StGB with Fedlex's footnote and the Regeste of BGE 130 IV 111) in two answer framings (Ja/Nein; "Urteil:
schuldig / nicht schuldig", and the French and Italian equivalents). The
twins read back **which element** a model gets wrong, not only how often. The same items support the two other
behavioural-alignment measurements: **preference accuracy** (forced choice between each item's `chosen` and `rejected`
answer) and **free generation** judged against the item's acceptance criterion (`scripts/judge_open.py` in the
repository: two blind Claude judges, a judge of another model family (Qwen), a deterministic parser, every judgement
hash-bound to the answer it judged, and a seeded 20% sample laid out for a human check, not yet filled).
### The dignity threshold (A18)
Where most real acquittals turn: 20 twin groups per language in which a public statement about a religious group is
either degrading (denying the believers equal worth as human beings: convict), a criticism of the religion's
institutions or teachings (acquit: Art. 261bis protects persons, not religions; BGE 131 IV 23 E. 3, Regeste pinned in
DE/FR/IT), or a crude joke whose wording the facts do not give (open; an acquittal reasoned on unproven wording is
acceptable). Gold comes from the element `dignity` in the statute model; reviewed by a legal-reviewer agent before
release. Files `dignity/eval/` (items, prompts with the BGE 131 IV 23 Regeste at the verbatim-law rungs) and
`dignity/responses/`; results in the repository (`reports/dignity.json`). Scope: the degrading variant uses the
Regeste's own formula, so it marks the clear ends of the line; Art. 261 StGB (disturbing freedom
of belief) is out of scope. Exploratory, not pre-registered.

### Natural paraphrases (A16)
To test whether the findings depend on the templated wording, a stable sample of 40 twin groups (the same in DE, FR and
IT; 120 items per language) was rewritten in everyday genres (news brief, witness account, police journal entry,
forum post, social worker's note, letter to the editor) with the legal facts locked. Every paraphrase was read blind by
a Claude agent and by Qwen-SEA-LION-v4-32B; it is kept only if the gold computed from each reader's extraction equals
the item's gold (verdict and deciding element) and the date, act, severity and intent match: 334
of 360 kept (`paraphrase/eval/paraphrase_<lang>.jsonl`, each with `paraphrase_of`, `genre` and the original's gold;
prompts and the 70B's responses alongside; verification in the repository, `reports/paraphrase_verification.json`).
The 70B behaves on them as on the templated originals (`reports/paraphrase.json`). Exploratory, not pre-registered.
### Out-of-Scope Use
Not legal advice and not a model of every element of the offence: intent is fixed, the Abs. 4 dignity threshold is
written to be met, Abs. 3 and 5 are not covered, so the items measure how a model applies the elements, not whether
it predicts a conviction. The free-text question asks whether the act is punishable under Swiss law, while the gold is
Art. 261bis; every answer judged misleading names Art. 261bis as its basis. The Italian verdict framing uses
"proscioglimento", which is wider than an acquittal on the merits ("assoluzione"). Not an evaluation-and-training set: never train on items you evaluate on (canary string in every item); if you use the
answers to train assistant behaviour outside this evaluation, use `chosen_with_scope`. Contains no hateful
text; acts are described abstractly in the statute's vocabulary.
### Specifications
- **Use case → specification:** the question a person asks about their own or someone else's speech; the elements the
  answer turns on (publicity, characteristic, date) are exactly the slots the twins vary.
- **Languages** follow where the article is litigated: of the decisions that cite BGE 130 IV 111, most are French- and
  German-language (court-validation pool: 67 DE, 79 FR, 4 IT decisions).
- **Localisation:** each language is set where it is spoken: German items in German-speaking towns, French items in
  Romandie (Lausanne, Genève, Sion, …), Italian items in Ticino and Italian Graubünden (Lugano, Bellinzona, Poschiavo,
  …), with each language's official legal terms and citation forms (StGB / CP, BGE / ATF / DTF, AS / RO / RU).
- **Prompt rungs** model the retrieval levels of an assistant: R0 no law; R1–R4 the elements, a one-sentence paraphrase
  of BGE 130 IV 111, the closed list and the 2020 date as rules; R5 the verbatim Fedlex text of Art. 261bis (with
  Fedlex's footnote) and Art. 2 StGB plus the Regeste of BGE 130 IV 111, as a retrieval pipeline would paste them.
- **Acceptance criteria, chosen / rejected answers, settled / contested labels and a normative source** are given for
  every item (Track 1B behavioural-alignment requirements).

## Dataset Structure
`eval/core_<lang>.jsonl` (one row per scenario), `eval/battery162.jsonl`, `eval/prompts_core_*.jsonl` (one row per
scenario × rung × framing: the exact user message, the assistant prefix and the two candidate answers),
`eval/prompts_open_core_*.jsonl` (free-text question at R0, R3 and R5, for generation and judging against the acceptance
criterion), `eval/prompts_pref_core_*.jsonl` (settled items: the item's `chosen` and `rejected` answers as the two
candidates, stored by direction, with `chosen_side`; preference accuracy), `metadata/items.jsonl`,
`metadata/sources.json`, `metadata/generator/` (the YAML the items were generated from), `responses/` (model responses,
one file per model build), `MANIFEST.json` (sha256 of every file).

Main fields: `id`, `lang`, `twin_group`, `family`, `variant` (base / true_flip / placebo / contested), `changed_slot`,
`base_id`, `slots` (template ids), `facts` (the legal facts), `text`, `gold_verdict` (convict / acquit / open),
`deciding_element`, `gold_reason`, `label` (settled / contested), `trap`, `acceptance_criterion`, `chosen` (the
answer the law supports, specific to the item), `rejected` (a wrong answer phrased as models argue, for preference
data), `rejected_minimal` (settled items: the chosen answer mirrored, same wording and length, verdict and deciding
claim negated; the preference prompts use this one, because a shorter `rejected` lets a likelihood comparison measure
length), `scope_note` and `chosen_with_scope` (acquittals, A17: what "not punishable under Art. 261bis" does not mean
and where else to turn, and the chosen answer with that note; **train on `chosen_with_scope`**, so that an assistant
does not learn to reassure; `chosen` stays the scored reference),
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
8 actors; mean 44.4 words; distinct-2 0.0516, distinct-3 0.0981 (templated by design).


### Second statute: Art. 179ter StGB (`stgb_179ter/`, exploratory)
The same generator, gold engine, QC gates and harness on a different kind of offence: recording a non-public
conversation one takes part in, without the other participants' consent (Art. 179ter StGB), prosecuted only on a
complaint filed within three months of learning of the act and the offender (Art. 30 and 31 StGB). Five elements:
non-public conversation, the recorder is a participant (a third party falls under Art. 179bis instead), sound
recording, no consent, timely complaint (a procedural element 261bis does not have). 120 German scenarios in
40 twin groups (COMPLAINT 32, CONSENT 24, CONV 24, MEDIUM 24, ROLE 16); verdicts
72 convict, 48 acquit. Sources pinned like 261bis: the
Fedlex texts of Art. 179ter, 30 and 31 StGB (version of 1 Oct 2026, sha256 in `stgb_179ter/metadata/sources.json`),
and, for the scope notes the answers make, Art. 179bis and 179quinquies StGB and Art. 329 StPO (A15). Acts are dated
from September 2023, after the harmonised penalty ranges entered into force (1 Jul 2023).
Prompts at three rungs (R0 no law; R1 the elements named; R2 plus the complaint rule) in the two framings; every
question asks about a conviction *under Art. 179ter alone*, since a court is not bound by the legal qualification of
the charge. German only, not pre-registered and not part of the held-out test: it shows that the method carries to a
second statute, not a second headline. A legal-reviewer persona (a Claude agent) found all 120 gold labels correct and
asked for wording fixes, applied before any model was scored: the question restricted to the article, a police report
instead of an indictment (no indictment of a complaint offence without a complaint), no legal conclusions in the facts
("Täter", "betroffen"), a rent talk in the landlord's flat instead of a phone call (business calls are exempt under
Art. 179quinquies). Scope of the gold: it answers only "conviction under Art. 179ter". An outsider who records may be
punishable under Art. 179bis; without a timely complaint the proceedings are discontinued (Art. 329 Abs. 4 StPO), so for the 16 complaint items
the verdict framing has no correct answer and they are read in the Ja/Nein framing only; this
is not an acquittal on the merits; justification, Art. 179quinquies and intent are assumed; a video with sound counts
as a sound recording (only handwritten notes are tested as a medium that is not); «schuldig / nicht schuldig» are
answer tokens, not Swiss dispositive wording. Files: `stgb_179ter/eval/`, `stgb_179ter/metadata/`,
`stgb_179ter/responses/`, `stgb_179ter/MANIFEST.json`; results in the repository (`results/results_179ter.json`).

Apertus v1.5 70B (`publicai-70b-179ter`):

| rung | framing | acquittals recognised | convictions kept | balanced accuracy |
|---|---|---|---|---|
| R0 | Ja/Nein | 48/48 | 0/72 | 0.50 |
| R0 | schuldig / nicht schuldig | 3/48 | 72/72 | 0.53 |
| R1 | Ja/Nein | 11/48 | 72/72 | 0.61 |
| R1 | schuldig / nicht schuldig | 0/48 | 72/72 | 0.50 |
| R2 | Ja/Nein | 34/48 | 58/72 | 0.76 |
| R2 | schuldig / nicht schuldig | 22/48 | 72/72 | 0.73 |

| acquittal decided by (Ja/Nein) | R0 | R1 | R2 |
|---|---|---|---|
| complaint:failed | 16/16 | 0/16 | 16/16 |
| consent:failed | 8/8 | 3/8 | 7/8 |
| conversation:failed | 8/8 | 0/8 | 2/8 |
| medium:failed | 8/8 | 8/8 | 6/8 |
| role:failed | 8/8 | 0/8 | 3/8 |

A framing that answers one way for every scenario reads no element: with no law (R0), Ja/Nein says "Nein" to all 120
(all acquittals "recognised", no conviction kept), while the verdict word convicts all. Only with the complaint rule
stated (R2) do both framings separate the cases; the public setting and the outsider are still convicted there.

## Dataset Creation
### Curation Rationale
Apertus is trained on Swiss court decisions, including BGE 130 IV 111 itself, yet plain-chat answers convict for
statements made only within the family and for characteristics outside the closed list (see the technical report). A
minimal-twin set with computed gold separates *which* element of the law a model applies from how often it is right,
and makes each wrong element measurable across training stages and model builds.

**How it differs from existing datasets** (sources and details: `docs/prior-art.md` in the repository). Swiss legal
benchmarks (LEXam, SwissLegalEvals, Swiss Judgment Prediction, SCALE) score exam answers or judgment outcomes, with no
one-fact variants and no statute versions. LawShift (Chinese) pairs minimal case edits with *hypothetical* statute
revisions graded by experts; TALD (Chinese) asks which statute version applies, without twins; OpenExempt (US) computes
gold with a solver but has no amendment dates; Multilingual HateCheck has templated contrasts but no law. To our
knowledge this is the first set that combines one-legal-fact twins and placebos, real amendment dates with
non-retroactivity (1 Jan 1995, 1 Jul 2020, Art. 2 StGB), gold computed from pinned official texts and checked against
court decisions, in German, French and Italian.
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
[`docs/consent-template.md`](docs/consent-template.md) (pseudonymised reviewers, signed forms kept by the maintainers, withdrawal before each
release). **AI permissions:** generated with AI assistance (declared). The licence permits any use, training included;
the set is built for evaluation, so we ask that a model trained on it (for instance on the chosen / rejected pairs) is
not evaluated on it, and the canary string in every item lets corpus builders exclude it from pre-training data.
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
  agents; comparison for legal facts: 0 critical, 3 minor findings, all fixed. A localisation review by a French- and
  Italian-speaking lawyer persona then fixed what back-translation cannot see (German places, calqued intent formula
  and verdict words, citation form); amendment A7, before any French or Italian result was analysed.
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
agents following [`docs/annotation-guidelines.md`](docs/annotation-guidelines.md). Agreement with the code gold on settled items:
939/939; deciding element on acquittals: 315/315; Cohen's κ
(3 classes, all items) 1.000. In the first round 7 of 21 contested items were labelled with a verdict and one
contested setting was read as clearly private by 5/5 annotators; that setting and an anachronism the annotators found
(acts in 1993/94 posted online) were fixed before any model result was analysed (pre-registration amendment A3) and the
changed items re-annotated. A second blind pass with new opaque ids gave the annotators **only the law** (statute texts,
Art. 2 StGB, the Regeste of BGE 130 IV 111; no rule summary): 939/939 settled items agree with the
code gold, κ against gold 1.000. The same law-only task given to a model of another family
(Qwen-SEA-LION-v4-32B, amendment A15): 910/939 settled items agree (κ 0.93); each of its
29 disagreements convicts a case the pinned text does not cover (sexual orientation before 1 July 2020, acts
before 1995, an unlisted characteristic), the errors Apertus makes, not gold errors. All labels: [`review/`](review/).
**Adjudication** of every annotator disagreement, every contested item and a blind 10% sample of settled items by
two independent agent adjudicators, 115 items (blind sample 94, contested 21, annotator disagreements 0); adjudicators agree on 115/115; gold wrong: 0/94 in the blind sample of settled items (Wilson 95% upper bound 3.9%), 0/21 contested items.
**Court validation** of the gold engine against real decisions: 326 decisions triaged (stratum A: 150, stratum B: 176); 57 in scope (55 convictions, 2 acquittals); engine agrees with the court in 57/57 (Wilson 95% 0.94-1.00; an engine that always convicts would agree in 55/57; acquittals 2/2, Wilson 0.34-1.00); 24 out of scope (unmodelled grounds), 50 unextractable, 195 excluded; every tuple extracted twice by independent agents, conflicts settled by a third (amendment A4). Counted per distinct case (post hoc,
amendment A12: repeat instances of one case merged; the Perinçek conviction, 6B_398/2007, left out because the ECtHR
found a violation of Art. 10 ECHR and the Federal Court revised it, 6F_6/2016): 52/52,
6 of them genocide denial; of the 2 acquittals
one is clean and one agrees on the outcome on another ground (amendment A15 reclassified BGE 126 IV 176, a cassation
and remand, as not an acquittal).
#### Annotator Details
All annotation, adjudication and court-tuple extraction was done by Claude agents (Anthropic), declared as AI, working
blind (opaque ids, no access to code or gold). No human labels: every label in this release can be regenerated by
anyone with the same instructions ([`docs/annotation-guidelines.md`](docs/annotation-guidelines.md) and the scripts in the repository). The agents share a
model family with the generator's author, so their agreement rules out reading errors, not a shared misconception of the
law; the statute tests against the official text and the court validation check the law itself.

## Risks, Bias, and Limitations
- One statute; templated scenarios (low lexical diversity by design); intent and the dignity threshold are fixed.
- Contested items are few (15 per language) and their verdict is open by construction.
- FR/IT are translations, checked by blind back-translation and a localisation review, not written by native lawyers.
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
37 runs (`responses/<run>.jsonl` with `<run>.meta.json`): 8b-bf16-DPO, 8b-bf16-RLVR, 8b-bf16-blend-RLVR-DPO-a0.25, 8b-bf16-blend-RLVR-DPO-a0.5, 8b-bf16-blend-RLVR-DPO-a0.75, 8b-gguf-q4_k_m, 8b-gguf-q4_k_m-cpu-core, 8b-gguf-q4_k_m-cpu-core-fr, 8b-gguf-q4_k_m-cpu-core-it, 8b-gguf-q4_k_m-cpu-pref, 8b-gguf-q8_0, 8b-mlx4-DPO, 8b-mlx4-RLVR, 8b-mlx4-SFT, 8b-mlx4-base-completion, 8b-mlx4-final, publicai-70b-ctrl-de, publicai-70b-ctrl-fr, publicai-70b-ctrl-it, publicai-70b-fc, publicai-70b-fc-core, publicai-70b-fc-core-fr, publicai-70b-fc-core-it, publicai-70b-fc-lay, publicai-70b-fc-lay-fr, publicai-70b-fc-lay-it, publicai-70b-gen, publicai-70b-open, publicai-70b-open-fr, publicai-70b-open-it, publicai-70b-pref, publicai-70b-pref-fr, publicai-70b-pref-it, publicai-70b-r5x-de, publicai-70b-r6-fr, publicai-70b-r6-it, qwen3-8b-mlx4.

## Changelog
- 1.5.0 (2026-10-11): amendment A19, case-specific scope notes (referral by characteristic, limits of honour and
  personality claims, time bars, criticism as protected speech, speaker-facing notes for first-person items); the
  dignity answers restate BGE 131 IV 23's test; no prompt or result changed.
- 1.4.0 (2026-10-11): amendment A18, the dignity threshold as an element and the DIGNITY family (60 items per
  language, `dignity/`); no core item, prompt or result changed.
- 1.3.0 (2026-10-11): amendment A17, a scope note and `chosen_with_scope` on every acquittal; no gold, prompt or
  result changed.
- 1.2.0 (2026-10-11): amendment A16 (first-person retellings in French and Italian, natural paraphrases verified
  blind by two model families, the 8B in French and Italian); no item or gold label of 1.1.0 changed.
- 1.1.0 (2026-10-10): amendments A12–A15: post-hoc court recount per distinct case, judgements bound to answers and
  provenance repairs (A12); controls for agreement bias and for R5 (A13, `review/controls_a13.json`); free text in
  French and Italian and Art. 179ter as a second statute (A14); corrections, a length control, an other-family gold
  check (A15);
  no item or gold label of 1.0.0 changed. Files and hashes: `MANIFEST.json` (201 files).
- 1.0.0 (2026-10-10): first release. Generator 1.0.0, seed 261.
  Pre-registration ([`docs/PREREG.md`](docs/PREREG.md)) was locked before any model scored the core set; every later
  change is an amendment in [`docs/AMENDMENTS.md`](docs/AMENDMENTS.md):
  A1 design moved into YAML, output byte-identical; A2 FR/IT surface fixes from back-translation; A3 one contested
  setting and an anachronism (online acts in 1993/94) fixed after blind annotation, before any result was analysed;
  A4 agent verification (double extraction, two adjudicators) instead of a human reviewer; A5 four wording fixes found
  in review after the German results had been analysed, all affected prompts re-scored, the pre-A5 responses kept in
  the Git repository (`archive/`) so the effect of the fix is visible; A6 item-specific reference answers (setting,
  characteristic, paragraph and date of each scenario; 333 distinct `chosen` per language), the free-text and
  preference prompts, and unparsed answers counted in every recall denominator; A7 French and Italian localisation
  (places in Romandie and Ticino, intent formula, verdict nouns, citation forms), before any French or Italian result
  was analysed, with both languages re-scored in full; A8 R5 (the verbatim law), length-matched preference pairs
  (`rejected_minimal`), Art. 1 and 2 StGB in the answers, a contested criterion that accepts a reasoned leaning, and
  the court-validation baseline; A9 the German scenarios as a first-person paraphrase (`de_lay`); A10 R6, the control
  for R5; A11 German localisation (bus, public information evening), free text with the verbatim law, a Qwen judge.

## Citation
```bibtex
@misc{apertus_recht_2026,
  title  = {Apertus-Recht: Art. 261bis StGB minimal-twin scenarios (DE/FR/IT)},
  author = {Team 444},
  year   = {2026},
  note   = {Hack Apertus 2026, Track 1B. Dataset version 1.5.0},
  url    = {https://github.com/mi11ione/apertus-recht}
}
```

## Glossary
- **Twin group:** a base scenario and its variants; each variant changes exactly one slot of the base.
- **True flip / placebo / contested:** the statute decides the variant differently from the base / the same / not
  without facts the scenario leaves open (gold `open`). Assigned by the gold engine, not by hand.
- **Deciding element, gold reason:** the element of Art. 261bis that decides an acquittal (`setting:failed`,
  `characteristic:not_listed`, `characteristic:not_yet_covered`, `act_date:not_in_force`).
- **Rung R0–R6:** how much law the prompt contains: R0 none; R1 the elements named; R2 + a one-sentence paraphrase of
  BGE 130 IV 111 and the list; R3 + "the list is closed"; R4 + "sexual orientation since 1 July 2020"; R5 the verbatim
  Fedlex text of Art. 261bis and Art. 2 StGB with Fedlex's footnote and the Regeste of BGE 130 IV 111; R6 = R5 with
  R1's instruction to check the elements (control).
- **Framing:** `conv` (Ja/Nein), `ver` ("Urteil:" schuldig / nicht schuldig; FR condamnation / acquittement, IT
  condanna / proscioglimento), `open` (free text), `pref` (chosen vs rejected_minimal).
- **Read-back status:** F the model convicts where the statute acquits (element *in force* in the model); a applied;
  u unreadable (the unchanged reference is not convicted either); ? undecided. Red: F in every readable framing.
- **Wording family A/B/C:** three sets of act wordings; A and B fit the read-back, C is held out.

## Dataset Card Authors
Team 444 (Hack Apertus 2026), with Claude Code agents as declared above.

## Dataset Card Contact
Via the Git repository's issue tracker: https://github.com/mi11ione/apertus-recht.
