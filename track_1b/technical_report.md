# Apertus-Recht: which racial-discrimination law does Apertus apply?

People ask chat assistants whether something said at dinner, in a chat or at a rally is punishable. We release 1,980
German, French and Italian minimal-twin scenarios under Art. 261bis StGB. Each verdict is computed by code from pinned
Fedlex texts and BGE 130 IV 111, and agrees with the 58 Swiss court rulings we could code on the modelled elements (55 convictions,
3 acquittals; a check of the rules' conjunction, not of how courts classify facts). A harness re-derives every
label and number from a clean checkout. Asked without the law, Apertus v1.5 70B convicts every scenario we wrote
(balanced accuracy 0.50). In free text it calls ⟨open_r0_mislead⟩ of 75 scenarios punishable that are not punishable under Art. 261bis. With the verbatim Fedlex text and the Regeste of the leading case pasted in, it still convicts everything; only rules
spelled out in plain sentences make it apply the publicity rule. It still convicts for a canton, a disability or a
political opinion, and for acts committed before the law existed. One sentence on when sexual orientation became
protected makes it stop convicting such cases in German and French.

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
  Actions.
- **Links:** code https://github.com/mi11ione/apertus-recht · dataset on Hugging Face (URL in the form notes).

----

## Use Case Description

Art. 261bis StGB (racial discrimination; extended to sexual orientation on 1 July 2020) is litigated in every language
region. Whether a statement is punishable turns on three elements a layperson cannot check: whether it was **public** (under
BGE 130 IV 111 E. 5.2, statements among family, friends or in a setting of personal trust are not), whether the
targeted characteristic is on the **closed list** (race, ethnicity, religion, sexual orientation), and **when** the act
took place.

A wrong answer misinforms people about their own speech in either direction. The user community is Swiss residents
asking a local assistant in German, French or Italian, with or without the law in its context. Apertus-v1.5-8B was
downloaded ⟨hf_downloads⟩ times in the 30 days before 9 October 2026. The article itself was adopted by referendum
in 1994 (54.6% yes) and extended to sexual orientation by referendum in 2020 (63.1% yes). Its training data include `voilaj/swiss-caselaw`,
which contains BGE 130 IV 111 verbatim, plus 147 decisions citing it. The dataset asks not "how often is the model
right" but **which law it applies**, element by element.

## Dataset Summary

Per language: 660 scenarios in 220 twin groups (220 base, 215 true flips, 210 placebos, 15 contested). Verdicts:
430 convict, 215 acquit, 15 open. Each scenario comes with an acceptance criterion, an item-specific `chosen` answer, a `rejected`
answer of the kind models give and a length-matched mirror, a settled or contested label, the normative source and
the element-by-element derivation; prompts at six rungs (R0 no law; R1–R4 the elements, a one-sentence paraphrase of
BGE 130 IV 111, the closed list, the 2020 date; R5 the verbatim Fedlex text of Art. 261bis and Art. 2 with Fedlex's
footnote, and the Regeste) in two forced-choice framings (Ja/Nein; "Urteil: schuldig / nicht schuldig"); a free-text
question; and a preference prompt. The same 660 German scenarios are also told in a user's own words (`de_lay`).

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
| **Apertus-Recht** | **DE, FR, IT** | **code from pinned Fedlex texts and BGE** | **yes, with placebos** | **1 Jan 1995, 1 Jul 2020, Art. 2 StGB** | **58/58 (3 acquittals)** |

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
  (κ 0.83–0.98) and conflicts went to a third agent. Under a pre-registered rule the engine agrees with the court in
  ⟨court_agree⟩ in-scope decisions. That is a weak test of the acquittal rules: an engine that always convicts would
  score 55/58, and the 3 acquittals (Wilson 95% 0.44–1.00) agree on the verdict and on a failing element, one of them
  decided under the publicity test that BGE 130 IV 111 replaced. Its value is the other direction: of the rulings
  that acquit, most turn on grounds no twin varies (dignity threshold, intent, freedom of expression).

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
- *Forced choice* (all items, R0/R3/R4 and, in German, R5; two framings): the summed log-probability of the convict continuation minus the
  acquit one. On vLLM this is exact (prefilled answer, prompt log-probabilities); in llama.cpp it is read from the
  logits.
- *Preference accuracy* (settled items, R0): the same exact scoring between each item's `chosen` answer and its
  length-matched mirror, the same sentence with the verdict and the deciding legal claim negated (median length ratio
  1.0; a first design with a shorter `rejected` answer measured length and was discarded before analysis, A8).
- *Free text* (a fixed sample of 240 German items, R0 and R3, greedy, 220 tokens): every answer is judged against its
  acceptance criterion by two independent Claude judges, blind to model, rung and family.

**The read-back** pairs every true flip (variant V) with its base (reference Ref, which the statute convicts) and
takes 95% item-bootstrap intervals of the mean log-odds of conviction. A framing is *readable* (anchored) for that pair
set when the interval of Ref lies above zero, i.e. the model convicts the reference at all. An element is *misapplied*
when V's interval also lies above zero (the model convicts where the law acquits), *applied* when it lies below. It is
**red** when misapplied in every readable framing. The pre-registered test fits this read-back on wording families A and
B and predicts family C; it passes if it beats the statute by at least 0.15 in every readable framing. R1 and R2 (the
elements named; the publicity rule added) are released for finer retrieval studies; we score R0, R3 and R4.

Runs: the 70B on Public AI (vLLM, temperature 0) on all three languages at R0/R3/R4 and on German at R5 (13,200
decisions), plus the German user voice at R0; the 8B public Q4_K_M GGUF (sha256 `a037df8d…`) on CPU CI runners,
German R0/R3/R4/R5 (5,280); preference on 645 settled items per language; free text on 480 German answers; the
exploration battery (162 items) for training stages and builds. Every row records the served model and a request hash.

## Results

**Without the law, the 70B convicts everything** (R0: recall of convictions 1.00, of acquittals 0.00, in every
language and framing). It is not blind to the facts: its conviction scores still rank punishable above non-punishable
cases (AUC ⟨auc_r0⟩), but the threshold sits so far on the convicting side that no case falls below it. Free text agrees with the forced choice. The judges failed ⟨open_r0_mislead⟩ of 75 R0 answers to
acquittal items as misleading, and every one of the 14 contested-item answers gave a flat verdict. The judges agreed on
479 of 480 pass decisions (κ 0.995), and a deterministic parser of each answer's verdict agrees with their reading in
464 of 466 settled answers, so the judges are needed only for the hedged and contested ones.

⟨table:accuracy⟩

*Table 1. Balanced accuracy (mean of the recall of convictions and of acquittals; 0.50 = no discrimination), Ja/Nein /
verdict framing, and the recall of acquittals at R3. R5 (verbatim law) and the user voice were run in German only.*

**With the rules spelled out, publicity is applied but the list and the date are not.** Figure 1 shows the read-back.
For the German 70B:
- **R3** (the elements, a one-sentence paraphrase of BGE 130 IV 111, the list and "the list is closed"): private settings are acquitted. Canton, disability and political
  opinion stay red, convicted although the prompt lists the four protected characteristics.
- **Gender identity** is applied once the prompt names it as excluded.
- **R4** adds the sentence "sexual orientation is protected since 1 July 2020". The 70B then acquits the cases
  before that date, but also stops convicting punishable cases from 2021–25. With the verdict word it convicts 0, 1
  and 5 of 35 in German, French and Italian; with Ja/Nein, 3 (German), 11 (French) and 29 (Italian) of 35. The 8B
  convicts 13 of 35. The clause does not
  teach the date; it takes the characteristic off the list. Recall of convictions falls to 0.74 (grey cells in
  Figure 1).
- **Acts before 1995**, when the article did not exist, are convicted at every rung. No rung states the 1995 date, and
  Fedlex's own footnote omits it, so this is a gap in what the model knows.
- **R5** pastes the law itself, as a retrieval pipeline would: the Fedlex text of Art. 261bis and Art. 2 StGB with
  Fedlex's footnote, and the Regeste of BGE 130 IV 111. The 70B convicts everything again, exactly as with no law at
  all (acquittals recognised: ⟨r5_acq_conv⟩ of 215 with Ja/Nein, ⟨r5_acq_ver⟩ with the verdict word). The verbatim text enumerates the four characteristics and the
  Regeste states the publicity rule, yet they help less than our one-sentence paraphrases. R5 also lacks R3's
  instruction to check the elements; a control with that instruction added (R6, Ja/Nein) recognises ⟨r6_acq⟩ of 215
  acquittals, against 108 at R3. Forced choice only; free text was not run with the verbatim law.

**Not an artefact of legal register.** The same German scenarios told in a person's own words ("Im Januar 2024 habe
ich in Aarau an einem Stand auf dem Wochenmarkt … ein Weltbild propagiert, nach dem Muslime minderwertig sind") give
the same profile: ⟨lay_acq⟩ of 215 acquittals at R0; at R3 balanced accuracy ⟨lay_r3_bal⟩ (charge-sheet form 0.74), with
private settings acquitted, the closed list half applied and the dates not at all (Ja/Nein; the prompt still names
the article).

Italian shows the same profile. In French the closed list holds better at R3 (canton 12/16, disability 6/9 convicted),
and R5 was run in German only.

![](docs/figures/fig1_synopse.png)

*Figure 1. Synopse: the law in force (column "Law") next to the law Apertus applies. Each row changes one legal fact
of a scenario the statute punishes (above the rule) or a detail that changes nothing (below). Cells: variants convicted
(k/n, Ja/Nein framing). Red: the model applies a law that is not in force, in both framings; light red: in one; grey:
the unchanged reference is not convicted either, so the element cannot be read.*

⟨table:preference⟩

*Table 2. Preference accuracy: share of settled items where the model gives the item's `chosen` answer a higher
log-probability than its length-matched mirror. Free text: answers that meet the acceptance criterion (both judges
agree; 240 German items, R0 and R3). Columns: the element that decides the item.*

**Recognising the law is not applying it.** Shown an item's correct answer and its mirror, the 70B prefers the correct
one for nearly every German item (share ⟨pref_de_all⟩). The clean evidence is in the closed-list and date columns,
where both answers make a legal claim of the same form: there it picks the right one for nearly all items in all
three languages, although its own verdicts convict those cases. For conviction and setting items the mirror
contradicts the stated facts, so those columns also measure consistency; there French drops to ⟨pref_fr_convict⟩.

**Pre-registered held-out test.** At R0 the test passes, but trivially: a model that convicts everything is predicted
perfectly by a read-back that marks every element satisfied, and the gain (+33 points) equals the share of acquittal
items. The informative rungs are R3 and R4, where the model applies part of the law. There the read-back still beats
the statute in every cell (+0.5 to +22 points), but not by the pre-registered 0.15 in every framing. The test fails,
and by our own rule these rungs report the per-element table (Figure 1), not the read-back.

⟨table:heldout⟩

*Table 3. Held-out read-back test at the informative rungs (fit: wording families A, B; test: family C; R0 passes
trivially for every model). Pass: gain ≥ 0.15 in every anchored
framing.*

**Post-training and builds** (exploration battery, 8B):
- At full precision, the step from RLVR to DPO costs acquittals once the rules are stated: at R3, correct acquittals
  fall from ⟨stage_rlvr⟩ to ⟨stage_dpo⟩ of 220 (both framings), while convictions stay at 104/104. Without the law
  both stages convict almost everything, so DPO amplifies a prior that RLVR already has. Exact weight blends between
  the two checkpoints move smoothly between them (canton items: 0/6 → 6/6).
- The public Q8_0 GGUF agrees with bf16 on 638 of 648 decisions, the Q4_K_M on 622 and our MLX 4-bit conversion on 548.

## Dataset Limitations

- **Depth over breadth.** One statute modelled exactly, three of its five paragraphs; intent is fixed and the Abs. 4
  dignity threshold is written to be met, which is where most court acquittals turn. The format is not tied to this
  statute: a second one (Art. 179ter) builds from five YAML files.
- **Exact twins need controlled wording.** The text is templated so that one fact changes at a time; the user-voice
  retelling shows the findings hold in everyday words.
- **Two legal choices a practitioner may contest, kept and stated.** The act is fixed as proven, so an Abs. 2 act
  ("propagating an ideology", which needs recruiting intent under BGE 140 IV 67) can occur in a one-off or private
  setting; and an online post from before 1 July 2020 counts as completed on publication (dropping those 10 items per
  language moves no accuracy by more than ⟨sens_max⟩ points, `scripts/sensitivity.py`). Acquittals are acquittals under
  Art. 261bis: a 1993/94 act is today also time-barred.
- **Every review is re-runnable.** Annotation, adjudication, court extraction and judging are agent runs with their
  instructions in the repository, so anyone can audit or repeat them; no private human judgment sits in the gold.
  Shared misconceptions of one model family are checked from outside it: the gold against the official text,
  mutation tests and 58 court decisions; the free-text judges by a judge of another model family (Qwen) and a
  deterministic parser (⟨judgec_line⟩).
- **Contested items are few** (15 per language). Two of the four contested settings (an e-mail to 25 colleagues, a club
  chat of 30) lean public after BGE 130 IV 111, so their criterion accepts a reasoned leaning; only a certain verdict
  without the publicity criteria fails.
- **Intervals.** Wilson intervals treat items as independent although they cluster in 220 twin groups; the held-out
  gains carry twin-group bootstrap intervals (post hoc, `analysis/heldout_context.py`).

## Lessons Learnt and Recommendations

**For Apertus users.**
- Do not ask about Art. 261bis without the law in context. With none, Apertus convicts every case we wrote, and its
  prose explains why.
- Do not count on retrieval: the pasted statute and leading case changed nothing. State the rule the case turns on
  in a plain sentence; the publicity rule is then applied. Still check characteristics against the
  closed list yourself, and state the date of the act.
- Prefer the Q8_0 GGUF or the served model to 4-bit MLX conversions.

**For Apertus developers.**
- In the 8B, DPO costs acquittals under stated rules (⟨stage_rlvr⟩ → ⟨stage_dpo⟩ of 220 at R3); preference pairs that
  reward condemning discrimination are a plausible cause worth checking. The model also obeys exclusions it is told
  (gender identity) but does not apply "the list is closed" to traits nobody named: an instruction-following target
  that needs no legal data.
- The leading case is in the training data, and pasting its Regeste with the statute does not change a single verdict.
  The model reads plain rules but not the law as written; long-context legal reading is a training target.
- Twin items give a target that can be measured element by element before and after a fix. The `chosen` / `rejected`
  pairs are in the format preference training uses, so keep them out of training if you evaluate on them.

**For dataset builders.** Computed gold turns a legal benchmark into software (tested against the official text,
mutation-tested, a new statute is five YAML files), but blind persona review still found what no gate caught. Next:
the elements courts argue about (dignity threshold, coded speech, political debate), written with practitioners.

## Reproducibility

`make run` (Docker, CPU, no key, no model) regenerates the dataset from the YAML (sha256 per file), recomputes every
result from the stored responses, checks every request hash against its prompt, re-aggregates the judges, checks the
pre-registration (`prereg-verify`: locked files, amendments A1–A10, the frozen held-out code) and the `claims.tsv`
numbers, and exits non-zero on any mismatch. `LLM_*` variables or `make run-gguf` add a live slice against the
published reference band. Seeds: generator 261, bootstrap 0 (2,000 resamples).

## License

Code Apache-2.0; dataset CDLA-Permissive-2.0; this report CC-BY-4.0.

## References

Art. 261bis and Art. 2 StGB, SR 311.0 (Fedlex, versions of 1 Jan 1995 and 1 Jul 2020); AS 1994 2887; AS 2020 1609.
BGE 130 IV 111. Fan et al., LEXam, ICLR 2026. Han et al., LawShift, NeurIPS 2025 D&B. Servantez et al., OpenExempt,
ACL Findings 2026. Huang et al., When Do LLMs Apply the Wrong Law?, arXiv 2608.14610. Röttger et al., Multilingual
HateCheck, WOAH 2022.
