# Apertus-Recht: which racial-discrimination law does Apertus apply?

People ask chat assistants whether something said at dinner, in a chat or at a rally is punishable. We release 1,980
German, French and Italian minimal-twin scenarios under Art. 261bis StGB. Each verdict is computed by code from pinned
Fedlex texts and BGE 130 IV 111 and agrees with ⟨court_agree⟩ in-scope Swiss court rulings. A harness re-derives every
label and number from a clean checkout. Asked without the law, Apertus v1.5 70B convicts every scenario we wrote
(balanced accuracy 0.50). In free text it tells ⟨open_r0_mislead⟩ of 75 users whose conduct is not punishable that it
is. With the statute pasted in, it applies the publicity rule. It still convicts for a canton, a disability or a
political opinion, and for acts committed before the law existed. Told when sexual orientation became protected, it
stops protecting it.

**Track:** Apertus Readiness · Track 1B (Swiss Voices, behavioural alignment) · **Event:** Online · **Team:** 444  
**Demo:** `make run` in the repository (Docker, CPU, no key, ~25 s); dataset on Hugging Face (link in the form notes)

----

### Use of Apertus

- **Model:** Apertus v1.5 70B; Apertus v1.5 8B (public Q4_K_M GGUF; exploration phase: SFT, RLVR, DPO and final stages,
  bf16 weight blends, Q8_0 and MLX 4-bit builds).
- **How it is used:** evaluation (forced choice, preference pairs, free text with two blind LLM judges).
- **Where it runs:** the 70B on the Public AI endpoint through a cost-capped gateway. The endpoint name
  `apertus-v1.5-8b` serves the 70B: its greedy output is byte-identical to the `-70b` name in 760/792 cells, and it
  scores 84.4% vs 70.8% on 250 MMLU items against the v1 8B route (`docs/builds.md`). The 8B GGUF runs on CPU in GitHub
  Actions. Total Public AI spend for this release: ⟨usd⟩.
- **Links:** code https://github.com/mi11ione/apertus-recht · dataset on Hugging Face (URL in the form notes).

----

## Use Case Description

Art. 261bis StGB (racial discrimination; extended to sexual orientation on 1 July 2020) is litigated in every language
region. Whether a statement is punishable turns on three elements a layperson cannot check:
- whether it was **public**: under BGE 130 IV 111 E. 5.2, statements among family, friends or in a setting of personal
  trust are not;
- whether the targeted characteristic is on the **closed list**: race, ethnicity, religion, sexual orientation;
- **when** the act took place.

A wrong answer misinforms people about their own speech in either direction. The user community is Swiss residents
asking a local assistant in German, French or Italian, with or without the law in its context. Apertus-v1.5-8B was
downloaded ⟨hf_downloads⟩ times in the 30 days before 9 October 2026. Its training data include `voilaj/swiss-caselaw`,
which contains BGE 130 IV 111 verbatim, plus 147 decisions citing it. The dataset asks not "how often is the model
right" but **which law it applies**, element by element.

## Dataset Summary

Per language: 660 scenarios in 220 twin groups (220 base, 215 true flips, 210 placebos, 15 contested). Verdicts:
430 convict, 215 acquit, 15 open. Each scenario comes with:
- an acceptance criterion;
- an item-specific `chosen` answer and a `rejected` answer of the kind models give;
- a settled or contested label;
- the normative source and the element-by-element derivation;
- prompts at five rungs (R0 no law → R4 statute, leading case, closed list and date clause) in two forced-choice
  framings (Ja/Nein; "Urteil: schuldig / nicht schuldig");
- a free-text question and a chosen-versus-rejected preference prompt.

| Family (groups per language) | One-fact change of the base | Tests |
|---|---|---|
| SET (55) | public → private setting; placebo: family wording of a public statement | BGE 130 IV 111 E. 5.2 |
| CHAR (60), CHARX (20) | protected → unprotected characteristic; placebo: synonym ("Hautfarbe", "Glaube") | closed list |
| DATE_SO (35) | sexual orientation 2021–25 → before 1 Jul 2020; placebo: 1 Jul / Aug 2020 | AS 2020 1609, Art. 2 StGB |
| DATE_CTRL (25) | race, ethnicity, religion → 2018–20 (placebo) and → 1993/94 | over-application; entry into force |
| CONTESTED (15) | public → fact-dependent setting (gold `open`) | hedging |
| WORDING (10) | another wording family; another paragraph | wording invariance |

Unprotected characteristics: gender identity, sex, canton, occupation, age, disability and political opinion. Paragraphs
are balanced (Abs. 1/2/4: 220/218/222 in German). The wording is deliberately templated: 18 act wordings in three
families, 29 settings, 33 group phrases. A mean of 44 words is the price of exact twins.

**What is new.** To our knowledge no existing dataset lets one test which version of a real statute a model applies,
element by element, in the three official languages (comparison with sources in `docs/prior-art.md`):

| Dataset | Languages | Gold | One-fact twins | Real amendment dates, non-retroactivity | Checked against courts |
|---|---|---|---|---|---|
| LEXam / SwissLegalEvals | DE, EN / DE, FR, IT | exam keys, LLM judges | no | no | no |
| LawShift (NeurIPS 2025) | ZH | expert metamorphic relations | yes | hypothetical revisions only | no |
| TALD (2026) | ZH | statute version cited in judgments | no | which version applies | from judgments |
| OpenExempt (2026) | EN | solver over expert encodings | single-factor suites | one deadline rule | no |
| Multilingual HateCheck | DE, FR, IT, … | by construction | templated contrasts | no (not legal) | no |
| **Apertus-Recht** | **DE, FR, IT** | **code from pinned Fedlex texts and BGE** | **yes, with placebos** | **1 Jan 1995, 1 Jul 2020, Art. 2 StGB** | **58/58** |

## Data Collection Method

**No data was collected from people.** A seeded generator renders the scenarios from YAML templates. A 97-line engine
computes the gold verdict from a machine-readable element model of the statute (`statutes/stgb_261bis/statute.yaml`).
Every element and value cites a pinned source: the Fedlex consolidations of Art. 261bis before and since 1 July 2020
and of Art. 2 StGB (DE/FR/IT, sha256 of the text), the amendment footnotes (AS 1994 2887, AS 2020 1609) and the Regeste
of BGE 130 IV 111. The engine, not the author, labels each variant a true flip, a placebo or contested. The generator refuses to build if
the label disagrees with the design.

**Design choices.** *Placebos* catch surface heuristics; *rungs* model the retrieval levels of an assistant; *two
framings* are used because a framing is readable only if it convicts the protected reference; acts are described in
the statute's own vocabulary (no slurs, no names); the 15 contested items per language leave the facts BGE 130 IV 111
makes decisive genuinely mixed, so their gold is `open` and their criterion asks for a hedged answer.

**Translation and localisation.** Claude agents translated the templates into French and Italian with the official
CP terms, and separate agents back-translated them blind (legal facts: 0 critical findings, 3 minor, all fixed). A
review by a French- and Italian-speaking lawyer persona then found what back-translation cannot: the cases read as
German cases in translation. Fixed before any French or Italian result was analysed (amendment A7): French items are set in Romandie, Italian ones
in Ticino and Italian Graubünden; intent reads "avec conscience et volonté" / "consapevolmente e volontariamente"; the
verdict words are "condamnation / acquittement" and "condanna / proscioglimento"; citations take each language's Swiss
form (art. 261bis al. 1 CP, ATF / DTF … consid. 5.2).

**Verification without human labels.** Gold is computed, so review looks for errors in the code, the element model or
the wording. All review was done by Claude agents working blind on opaque ids, without access to code or gold.
- **Annotation:** six agents labelled 960 items. They agreed with the code on ⟨ann_settled⟩ settled items and on the
  deciding element in 315/315 acquittals. A second pass that gave the agents only the law (statute texts and Regeste,
  no rule summary) agreed on 939/939.
- **Wording fixes:** reviewers found two wording defects before any result was analysed (amendment A3) and four after
  (A5). All were fixed, the affected prompts re-scored, and the pre-fix responses archived.
- **Adjudication:** two independent adjudicators covered every disagreement, every contested item and a blind 10%
  sample. Gold was wrong in 0/94 sampled items (Wilson upper bound 3.9%).
- **Court validation:** we triaged ⟨court_triaged⟩ citing Art. 261bis. Each was extracted twice
  (κ 0.83–0.98) and conflicts went to a third agent. The engine agrees with the court in ⟨court_agree⟩ in-scope
  decisions (Wilson 95% ⟨court_ci⟩), 55 convictions and 3 acquittals, under a pre-registered rule.

## Dataset Details

**Quality gates** (`statute-twins qc`, all passing): schema; gold recomputed for every item; twin invariants (one
changed slot; placebos keep the verdict, flips change it); 0 duplicates; language identity; canary; a PII scan over
items, responses and metadata (0 hits). Tests check every closed-list term and both in-force dates against the official text in three languages. Mutation
tests (drop religion from the list, move the 2020 date by a day, make private settings public) flip exactly the items
each rule governs.

**Contamination.** None of our 35,241 distinct 13-grams occurs in the 1,069,365 decisions of `voilaj/swiss-caselaw`;
the same code finds 846 of the 1,525 13-grams of the statute and the Regeste. The law itself is well represented: 147
decisions mention BGE 130 IV 111 and 754 mention Art. 261bis.

**Ethics and licensing.** No data subjects: actors are generic, groups are named by their characteristic, acts are
abstract. Items are CDLA-Permissive-2.0 with per-item licence components; statute and decision texts are public domain
(Art. 5 URG). AI use is declared throughout; a consent form with an AI-use clause is ready for anyone who adds human
reviewers. Every item carries a canary string.

## Evaluation

**Three measurements, one item set.**
- *Forced choice* (all items, R0/R3/R4, two framings): the summed log-probability of the convict continuation minus the
  acquit one. On vLLM this is exact (prefilled answer, prompt log-probabilities); in llama.cpp it is read from the
  logits.
- *Preference accuracy* (settled items, R0): the same exact scoring between each item's `chosen` and `rejected` answer.
  We report it per token, because chosen answers are longer, and summed.
- *Free text* (a fixed sample of 240 German items, R0 and R3, greedy, 220 tokens): every answer is judged against its
  acceptance criterion by two independent Claude judges, blind to model, rung and family.

**The read-back** pairs every true flip (variant V) with its base (reference Ref, which the statute convicts) and
takes 95% item-bootstrap intervals of the mean log-odds of conviction. A framing is *readable* (anchored) for that pair
set when the interval of Ref lies above zero, i.e. the model convicts the reference at all. An element is *in force*
when V's interval also lies above zero (the model convicts where the law acquits), *applied* when it lies below. It is
**red** when in force in every readable framing. The pre-registered test fits this read-back on wording families A and
B and predicts family C; it passes if it beats the statute by at least 0.15 in every readable framing. R1 and R2 (the
elements named; the publicity rule added) are released for finer retrieval studies; we score R0, R3 and R4.

| Run | Model and build | Where | Scope |
|---|---|---|---|
| `publicai-70b-fc-core(-fr,-it)` | Apertus v1.5 70B | Public AI (vLLM), temperature 0 | 660 items × R0/R3/R4 × 2 framings × 3 languages: 11,880 decisions |
| `8b-gguf-q4_k_m-cpu-core` | Apertus v1.5 8B, public Q4_K_M GGUF (sha256 `a037df8d…`) | llama-cpp-python 0.3.19, CPU CI runners | German: 3,960 decisions |
| `*-pref` | both of the above | as above | 645 settled items per language at R0 |
| `publicai-70b-open` | 70B, free text | Public AI, greedy | 480 answers, 960 judgements |
| `8b-bf16-*`, `8b-gguf-*`, `8b-mlx4-*` | post-training stages, weight blends, builds | exploration phase | 162-item German battery |

## Results

**Without the law, the 70B convicts everything** (R0: recall of convictions 1.00, of acquittals 0.00, in every
language and framing). Free text agrees with the forced choice. The judges failed ⟨open_r0_mislead⟩ of 75 R0 answers to
acquittal items as misleading, and every one of the 14 contested-item answers gave a flat verdict. The judges agreed on
479 of 480 pass decisions (κ 0.995). On every settled answer, the judge's pass equals its expressed verdict compared
with the computed gold (466/466), and that verdict matches a deterministic parser in 464 of 466 cases.

⟨table:accuracy⟩

*Table 1. Forced-choice accuracy and balanced accuracy, Ja/Nein / verdict framing. 70B: Public AI; 8B: public Q4_K_M
GGUF on CPU.*

**With the law in the prompt, publicity is applied but the list and the date are not.** Figure 1 shows the read-back.
For the German 70B:
- **R3** (statute, BGE rule, "the list is closed"): private settings are acquitted. Canton, disability and political
  opinion stay red, convicted although the prompt lists the four protected characteristics.
- **Gender identity** is applied once the prompt names it as excluded.
- **R4** adds the sentence "sexual orientation is protected since 1 July 2020". The 70B then acquits the cases
  before that date, but also convicts only 3 of 35 punishable cases from 2021–25 (8B: 13 of 35). The clause does not
  teach the date; it takes the characteristic off the list. Recall of convictions falls to 0.74 (grey cells in
  Figure 1).
- **Acts before 1995**, when the article did not exist, are convicted at every rung.

French and Italian show the same profile (Table 1; per-language Synopse in the repository).

![](docs/figures/fig1_synopse.png)

*Figure 1. Synopse: the law in force (column "Law") next to the law Apertus applies. Each row changes one legal fact
of a scenario the statute punishes (above the rule) or a detail that changes nothing (below). Cells: variants convicted
(k/n, Ja/Nein framing). Red: the model applies a law that is not in force, in both framings; light red: in one; grey:
the unchanged reference is not convicted either, so the element cannot be read.*

⟨table:preference⟩

*Table 2. Preference accuracy: share of settled items where the model gives the item's `chosen` answer a higher
log-probability than the `rejected` one (per token; summed in the repository). Free text: share of answers that meet
the acceptance criterion (two judges, 240 German items).*

**Pre-registered held-out test.** At R0 the test passes, but trivially: a model that convicts everything is predicted
perfectly by a read-back that marks every element satisfied, and the gain (+33 points) equals the share of acquittal
items. The informative rungs are R3 and R4, where the model applies part of the law. There the read-back still beats
the statute in every cell (+0.5 to +22 points), but not by the pre-registered 0.15 in every framing. The test fails,
and by our own rule these rungs report the per-element table (Figure 1), not the read-back.

⟨table:heldout⟩

*Table 3. Held-out read-back test (fit: wording families A, B; test: family C). Pass: gain ≥ 0.15 in every anchored
framing.*

**Post-training and builds** (exploration battery, 8B):
- At full precision, the step from RLVR to DPO turns the canton items of the battery from acquittal (0/6) to
  conviction (6/6), and exact weight blends between the two checkpoints move monotonically between them. Six items
  are a lead for the developers, not a finding about all of post-training.
- The public Q8_0 GGUF agrees with bf16 on 638 of 648 decisions, the Q4_K_M on 622 and our MLX 4-bit conversion on 548.

## Dataset Limitations

- **One statute, three of its five paragraphs.** Intent is fixed and the Abs. 4 dignity threshold is written to be
  met. In the court sample, acquittals mostly turn on those grounds, which no twin varies. A second worked statute
  (Art. 179ter, five YAML files) shows the format is not tied to this one.
- **Templated text.** The set measures legal reasoning on clean fact patterns, not robustness to messy user prose.
- **Translations, not native writing.** FR and IT passed blind back-translation and a localisation review, but no
  native lawyer wrote them. Two choices a practitioner may contest are kept and stated:
  - the act is fixed as proven, so an Abs. 2 act ("propagating an ideology") or "distributing writings" can occur in a
    one-off spoken setting such as a bus;
  - an online post from before 1 July 2020 counts as completed on publication. Dropping those 10 items per language
    changes no accuracy by more than ⟨sens_max⟩ points (`scripts/sensitivity.py`).
- **Agents, not people, reviewed it.** Every review step is a reproducible agent run with its instructions in the
  repository. Agents of one model family can share a misconception of the law. The checks against the official text,
  the mutation tests and the 58 court decisions test the law itself. The track's 20% human check of the judges is
  laid out as a file and a script (`scripts/judge_open.py human`) for a reviewer to fill. Until then every judgement
  is checked against code instead.
- **Contested items are few** (15 per language), and the free-text sample is German only.

## Lessons Learnt and Recommendations

**For Apertus users.**
- Do not ask about Art. 261bis without the law in context. With none, Apertus convicts every case we wrote, and its
  prose explains why.
- Paste the statute and BGE 130 IV 111, and it applies the publicity rule. Still check characteristics against the
  closed list yourself, and state the date of the act.
- Prefer the Q8_0 GGUF or the served model to 4-bit MLX conversions.

**For Apertus developers.**
- The 8B exploration points at the DPO step for the canton conviction (6 items; worth testing at scale).
- The leading case is in the training data. The model still does not apply it without being told.
- Twin items give a target that can be measured element by element before and after a fix. The `chosen` / `rejected`
  pairs are in the format preference training uses, so keep them out of training if you evaluate on them.

**For dataset builders.** Computed gold turns a legal benchmark into software:
- the statute model is tested against the official text;
- mutations of the law flip exactly the items they should;
- a new statute is five YAML files.

Blind persona review still found defects no gate caught, such as a frame that dated the recording instead of the act.
We fixed them, re-scored, and recorded when in the pre-registration. The next iteration should add the elements courts
argue about (the dignity threshold, coded speech, political debate) as contested items written with practitioners.

## Reproducibility

`make run` (Docker, CPU, no key, no model) regenerates the dataset from the YAML and checks every file by sha256. It
recomputes every result from the stored responses, checks every stored request hash against the current prompt, and
exits non-zero on any mismatch.
- **Live checks:** `LLM_*` variables or `make run-gguf` also score a live slice against the published reference band.
- **Traceability:** every number in this report maps to a results file and the command that produced it in
  `claims.tsv`, which CI checks on every push.
- **Seeds:** generator 261; bootstrap seed 0, 2,000 resamples.
- **Pre-registration:** `prereg/LOCK.json`, before any model saw the core set. Amendments A1–A7, with their timing
  relative to the analysis, are in `prereg/AMENDMENTS.md`.

## License

Code Apache-2.0; dataset CDLA-Permissive-2.0; this report CC-BY-4.0.

## References

Art. 261bis and Art. 2 StGB, SR 311.0 (Fedlex, versions of 1 Jan 1995 and 1 Jul 2020); AS 1994 2887; AS 2020 1609.
BGE 130 IV 111. Fan et al., LEXam, ICLR 2026. Han et al., LawShift, NeurIPS 2025 D&B. Servantez et al., OpenExempt,
ACL Findings 2026. Huang et al., When Do LLMs Apply the Wrong Law?, arXiv 2608.14610. Röttger et al., Multilingual
HateCheck, WOAH 2022.
