# Apertus-Recht: which racial-discrimination law does Apertus apply?

People ask chat assistants whether something said at dinner, in a chat or at a rally is punishable. We release 1,980
German, French and Italian minimal-twin scenarios under Art. 261bis StGB. Intent and the dignity threshold are
stipulated, so the set tests how a model applies the elements, not whether it predicts a conviction. Each verdict is
computed by code from pinned Fedlex texts and BGE 130 IV 111, and agrees with all 58 Swiss court rulings we could code
on the modelled elements (53 distinct cases, mostly convictions). A harness re-derives every label and number from a
clean checkout. Asked without the law, Apertus v1.5 70B convicts every German scenario we wrote (balanced accuracy 0.50). In
free text it calls ⟨open_r0_mislead⟩ of 75 non-punishable scenarios punishable, each time under Art. 261bis. With the
verbatim Fedlex text and the Regeste of the leading case pasted in, it still convicts everything in German; only
rules spelled out in plain sentences make it apply the publicity rule. It still convicts for a canton, a disability
or a political opinion, and for acts before the article entered into force (1 Jan 1995). One sentence on when sexual
orientation became protected makes it stop convicting such cases in German and French.

**Track:** Apertus Readiness · Track 1B (Swiss Voices, behavioural alignment) · **Event:** Online · **Team:** 444  
**Demo:** https://apertus-recht.mi11ion.io (every scenario, its gold and Apertus's answers) · `make run` (Docker, CPU, no key)

----

### Use of Apertus

- **Model:** Apertus v1.5 70B; Apertus v1.5 8B (public Q4_K_M GGUF; exploration phase: SFT, RLVR, DPO and final stages,
  bf16 weight blends, Q8_0 and MLX 4-bit builds).
- **How it is used:** evaluation (forced choice, preference pairs, free text with three blind LLM judges, two Claude and one Qwen).
- **Where it runs:** the 70B on Public AI through a cost-capped gateway. Public AI's name `apertus-v1.5-8b` currently
  serves the 70B (same output as `-70b` on 760 of 792 test prompts, `docs/builds.md`), so every hosted number is the
  70B; the 8B runs as the public GGUF on CPU in GitHub Actions.
- **Links:** code https://github.com/mi11ione/apertus-recht · dataset https://huggingface.co/datasets/mi11ion/apertus-recht

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
question; and a preference prompt. The same 660 German scenarios are also retold as a first-person paraphrase (`de_lay`).

**Terms.** *Rung*: how much law the prompt carries (R0–R6). *Framing*: how the verdict is asked (Ja/Nein, or the
verdict word). A framing is *readable* for a set of twins when it convicts their unchanged reference. An element is
*misapplied* (red) when the model also convicts the variant the law acquits. The *read-back* is the law the model
applies, element by element, read off these pairs.

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
| **Apertus-Recht** | **DE, FR, IT** | **code from pinned Fedlex texts and BGE** | **yes, with placebos** | **1 Jan 1995, 1 Jul 2020, Art. 2 StGB** | **58/58 rulings, 53 cases** |

## Data Collection Method

**No data was collected from people.** A seeded generator renders the scenarios from YAML templates. A 97-line engine
computes the gold verdict from a machine-readable element model of the statute (`statutes/stgb_261bis/statute.yaml`).
Every element and value cites a pinned source: the Fedlex consolidations of Art. 261bis before and since 1 July 2020
and of Art. 2 StGB (DE/FR/IT, sha256 of the text), the amendment footnotes (AS 1994 2887, AS 2020 1609) and the Regeste
of BGE 130 IV 111. The engine, not the author, labels each variant a true flip, a placebo or contested. The generator refuses to build if
the label disagrees with the design.

**Design choices.** Placebos catch surface heuristics; rungs model retrieval levels; statute vocabulary, no slurs or
names; contested items leave BGE 130 IV 111's decisive facts mixed (gold `open`, hedged answer expected).

**Translation and localisation.** FR/IT by Claude agents with the official CP terms, blind back-translation (0
critical findings), then a lawyer-persona review that localised what back-translation cannot see (A7): Romandie and
Ticino places, "avec conscience et volonté", "condamnation / acquittement", Swiss citation forms.

**Verification without human labels.** Gold is computed, so review looks for errors in the code, the element model or
the wording. All review was done by Claude agents working blind on opaque ids, without access to code or gold.
- **Annotation:** six agents labelled 960 items. They agreed with the code on ⟨ann_settled⟩ settled items and on the
  deciding element in 315/315 acquittals. A second pass that gave the agents only the law (statute texts and Regeste,
  no rule summary) agreed on 939/939.
- **Wording fixes:** two defects found before any result was analysed (A3), four after (A5); all fixed, re-scored,
  pre-fix responses archived.
- **Adjudication:** two independent adjudicators covered every disagreement, every contested item and a blind 10%
  sample. Gold was wrong in 0/94 sampled items (Wilson upper bound 3.9%).
- **Court validation:** ⟨court_triaged⟩ citing Art. 261bis triaged, each extracted twice (κ 0.83–0.98, a third
  agent on conflicts): the engine agrees with ⟨court_agree⟩ in-scope rulings. Counted per distinct case (repeat
  instances merged; Perinçek left out, revised after Strasbourg; post hoc, A12): ⟨court_cases⟩, 6 of them genocide
  denial. A strong test of the conviction rules, a thin one of the acquittal rules: an always-convict engine scores
  55/58, and of 3 acquittals one is clean, one agrees on another ground, one predates BGE 130 IV 111.

## Dataset Details

**Quality gates** (`statute-twins qc`, all passing): schema; gold recomputed for every item; twin invariants (one
changed slot; placebos keep the verdict, flips change it); 0 duplicates; language identity; canary; a PII scan over
items, responses and metadata (0 hits). Tests check every closed-list term and both in-force dates against the official text in three languages. Mutation
tests (drop religion from the list, move the 2020 date by a day, make private settings public) flip exactly the items
each rule governs.

**Contamination.** None of our 35,241 distinct 13-grams occurs in the 1,069,365 decisions of `voilaj/swiss-caselaw`;
the same code finds 846 of the 1,525 13-grams of the statute and the Regeste (positive control).

**Ethics and licensing.** No data subjects: generic actors, groups named by their characteristic, abstract acts.
CDLA-Permissive-2.0 with per-item licence components; statute and decision texts are public domain (Art. 5 URG). A
consent form with an AI-use clause is ready for human reviewers. Every item carries a canary string.

## Evaluation

**Three measurements, one item set.**
- *Forced choice* (all items, R0/R3/R4/R5; two framings): the summed log-probability of the convict continuation minus
  the acquit one, exact on vLLM (prefilled answer, prompt log-probabilities), from the logits in llama.cpp.
- *Preference accuracy* (settled items, R0): the same exact scoring between each item's `chosen` answer and its
  length-matched mirror, the same sentence with the verdict and the deciding legal claim negated (median length ratio
  1.0; a first design with a shorter `rejected` answer measured length and was discarded before analysis, A8).
- *Free text* (a fixed sample of 240 German items, R0, R3 and R5, greedy, 220 tokens): every answer is judged against its
  acceptance criterion by two independent Claude judges and one Qwen judge, blind to model, rung and family.

**The read-back** pairs every true flip (variant V) with its base (reference Ref, which the statute convicts), with
95% item-bootstrap intervals of the mean log-odds of conviction: readable when Ref's interval lies above zero,
misapplied when V's does too, applied when V's lies below; **red** when misapplied in every readable framing. The
pre-registered test fits it on wording families A and B and predicts family C; it passes if it beats the statute by
at least 0.15 in every readable framing. R1 and R2 are released for finer retrieval studies.

Runs: the 70B on Public AI (vLLM, temperature 0) in three languages at R0/R3/R4/R5; the 8B public Q4_K_M GGUF
(sha256 `a037df8d…`) on CPU CI runners, German R0–R5; preference on 645 settled items per language; free text on 720
German answers; the 162-item battery for training stages. Every row records the served model and a request hash.

## Results

**Without the law, the 70B convicts everything** (R0: recall of convictions 1.00, of acquittals at most 0.01, in every
language and framing). It is not blind to the facts: its conviction scores still rank punishable above non-punishable
cases (AUC ⟨auc_r0⟩), but the threshold sits so far on the convicting side that no case falls below it. Free text agrees with the forced choice. The judges failed ⟨open_r0_mislead⟩ of 75 R0 answers to
acquittal items as misleading, every one of them naming Art. 261bis as the basis, and every one of the 14
contested-item answers gave a flat verdict. The two Claude judges agree on ⟨open_judges_agree⟩ pass decisions
(κ ⟨open_kappa⟩). A judge of another model family (Qwen-SEA-LION-v4-32B) agrees with their consensus on
⟨judgec_agree⟩, less on acquittal and open items (κ ⟨judgec_kappa_acq⟩; it is more lenient at R3), and on its own counts
⟨judgec_r0⟩ of 75 misleading answers at R0. A deterministic parser of each answer's verdict agrees with the judges'
reading on ⟨parser_agree⟩ settled answers. A seeded 20% sample is laid out for a human check.

⟨table:accuracy⟩

*Table 1. Balanced accuracy (mean of the recall of convictions and of acquittals; 0.50 = no discrimination), Ja/Nein /
verdict framing, and the recall of acquittals at R3. The user voice was run in German only, at R0 and R3.*

**With the rules spelled out, publicity is applied but the list and the date are not.** Figure 1 shows the read-back.
For the German 70B:
- **R3** (the elements, a one-sentence paraphrase of BGE 130 IV 111, the list and "the list is closed"): private
  settings are acquitted, but every private variant names family or friends, the words of the paraphrase, so this
  shows uptake of a stated example more than application of BGE 130 IV 111. Canton, disability and political
  opinion stay red, convicted although the prompt lists the four protected characteristics.
- **Gender identity** is applied once the prompt names it as excluded.
- **R4** adds the sentence "sexual orientation is protected since 1 July 2020". The 70B then acquits the cases
  before that date, but also stops convicting punishable cases from 2021–25. With the verdict word it convicts 0, 1
  and 5 of 35 in German, French and Italian; with Ja/Nein, 3 (German), 11 (French) and 29 (Italian) of 35. The 8B
  convicts 13 of 35. The clause does not
  teach the date; it takes the characteristic off the list. Recall of convictions falls to 0.74 (grey cells in
  Figure 1).
- **Acts from 1993/94**, before the article entered into force (1 Jan 1995), are convicted at every rung. No rung states the 1995 date, and
  Fedlex's own footnote omits it, so this is a gap in what the model knows.
- **R5** pastes the law itself, as a retrieval pipeline would: the Fedlex text of Art. 261bis and Art. 2 StGB with
  Fedlex's footnote, and the Regeste of BGE 130 IV 111. The German 70B convicts everything again, exactly as with no law at
  all (acquittals recognised: ⟨r5_acq_conv⟩ of 215 with Ja/Nein, ⟨r5_acq_ver⟩ with the verdict word). The verbatim text enumerates the four characteristics and the
  Regeste states the publicity rule, yet they help less than our one-sentence paraphrases. The scores move, the
  decisions do not: the private setting lowers the conviction score by 6.6 nats from 14.7. R5 also lacks R3's
  instruction to check the elements; a control with that instruction added (R6, Ja/Nein) recognises ⟨r6_acq⟩ of 215
  acquittals, against 107 at R3. In free text with the verbatim law, ⟨open_r5_mislead⟩ of 75 answers to non-punishable
  scenarios say they are punishable. In French and Italian the verbatim law recognises ⟨r5_fr⟩ and ⟨r5_it⟩ of 215 acquittals
  with Ja/Nein, against 120 and 97 with the rules spelled out.

**Not an artefact of legal register.** The same German scenarios retold in the first person ("Im Januar 2024 habe
ich in Aarau an einem Stand auf dem Wochenmarkt … ein Weltbild propagiert, nach dem Muslime minderwertig sind") give
the same profile: ⟨lay_acq⟩ of 215 acquittals at R0; at R3 balanced accuracy ⟨lay_r3_bal⟩ (charge-sheet form 0.74), with
private settings acquitted, the closed list half applied and the dates not at all (Ja/Nein; the prompt still names
the article, and the act keeps the statute's vocabulary).

Italian shows the same profile. In French the closed list holds better at R3 (canton 12/16, disability 6/9 convicted).

![](docs/figures/fig1_synopse.png)

*Figure 1. Synopse: the law in force (column "Law") next to the law Apertus applies. Each row changes one legal fact
of a scenario the statute punishes (above the rule) or a detail that changes nothing (below). Cells: variants convicted
(k/n, Ja/Nein framing). Red: the model applies a law that is not in force, in both framings; light red: in one; grey:
the unchanged reference is not convicted either, so the element cannot be read. ↓: the variant's conviction score is
below the reference's (paired 95% interval): the model registers the fact but stays on the convicting side (A12).*

![](docs/figures/fig2_rungs.png)

*Figure 2. Share of acquittals recognised and of convictions kept by rung (Ja/Nein). Rules spelled out (R3, R4) move
every model; the date sentence (R4) costs convictions; the verbatim law (R5) undoes it all.*

⟨table:preference⟩

*Table 2. Preference accuracy: share of settled items where the model gives the item's `chosen` answer a higher
log-probability than its length-matched mirror. Free text: answers that meet the acceptance criterion (both judges
agree; 240 German items). Columns: the element that decides the item.*

**Recognising the law is not applying it.** Shown an item's correct answer and its mirror, the 70B picks the correct
one (German share ⟨pref_de_all⟩), most cleanly in the closed-list and date columns, where both answers make a legal
claim of the same form, although its own verdicts convict those cases. Elsewhere the mirror contradicts the facts.
In French it prefers that mirror for half the punishable cases (0.53), with the pairs built as in German and Italian
(0.98, 0.92); we have not isolated why.

**Pre-registered held-out test.** At R0 the test passes, but trivially: a model that convicts everything is predicted
perfectly by a read-back that marks every element satisfied, and the gain (+33 points) equals the share of acquittal
items. The informative rungs are R3 and R4, where the model applies part of the law. There the read-back still beats
the statute in every cell (+0.5 to +22 points), but not by the pre-registered 0.15 in every framing. The test fails,
and by our own rule these rungs report the per-element table (Figure 1), not the read-back. Two cells could not pass
at all (the model departs from the statute on fewer than 15% of their items), and the split varies the wording only,
so the test measures invariance to wording, not transfer to new legal facts.

⟨table:heldout⟩

*Table 3. Held-out read-back test at the informative rungs (fit: wording families A, B; test: family C; R0 passes
trivially for every model). Pass: gain ≥ 0.15 in every anchored
framing.*

**Post-training and builds** (8B, exploration battery; one checkpoint pair, a lead): RLVR → DPO cuts correct
acquittals under stated rules from ⟨stage_rlvr⟩ to ⟨stage_dpo⟩ of 220 (R3) and keeps 104/104 convictions. The public
Q8_0 GGUF agrees with bf16 on 638 of 648 decisions, the Q4_K_M on 622, our MLX 4-bit conversion on 548.

## Dataset Limitations

- **Depth over breadth.** One statute modelled exactly, three of its five paragraphs; intent, the characteristic and
  the Abs. 4 dignity threshold are stated in the facts, which is where most court acquittals turn, so the set
  measures element application, not conviction prediction. The format is not tied to this
  statute: a second one (Art. 179ter) builds from five YAML files.
- **Exact twins need controlled wording**, templated so that one fact changes at a time; the first-person retelling
  shows the findings hold outside the charge-sheet register.
- **Two contestable legal choices, kept and stated.** An Abs. 2 act ("propagating an ideology", recruiting intent
  under BGE 140 IV 67) can occur in a private setting; an online post before 1 July 2020 counts as completed on
  publication (dropping those items moves no accuracy by more than ⟨sens_max⟩ points). A 1993/94 act is also time-barred.
- **Every review is re-runnable**: agent runs with their instructions in the repository, no private human judgment in
  the gold. One model family's blind spots are checked from outside it: the gold against the official text, mutation
  tests and court decisions; the judges by another model family (Qwen) and a deterministic parser.
- **Contested items are few** (15 per language). Two of the four contested settings (an e-mail to 25 colleagues, a club
  chat of 30) lean public after BGE 130 IV 111, so their criterion accepts a reasoned leaning; only a certain verdict
  without the publicity criteria fails.
- **Intervals** treat items as independent; the held-out gains carry twin-group bootstrap intervals (post hoc).

## Lessons Learnt and Recommendations

**For Apertus users.**
- Do not ask about Art. 261bis without the law in context, and do not count on pasting the statute (no German verdict
  changed). State the rule the case turns on in a plain sentence; check the characteristic against the closed list
  and the date of the act yourself. Prefer the Q8_0 GGUF or the served model to 4-bit MLX conversions.

**For Apertus developers.**
- In our one checkpoint pair, DPO costs acquittals under stated rules (8B: ⟨stage_rlvr⟩ → ⟨stage_dpo⟩ of 220 at R3): check pairs that reward
  condemning discrimination. The model obeys exclusions it is told but not "the list is closed", and it reads plain
  rules but not the law as written: instruction-following and long-context legal reading are training targets.
- Keep the `chosen` / `rejected` pairs out of training if you evaluate on them.

## Reproducibility

`make run` (Docker, CPU, no key, no model) regenerates the dataset from the YAML (sha256 per file), recomputes every
result from the stored responses, checks every request hash against its prompt, re-aggregates the judges, checks the
pre-registration (`prereg-verify`: locked files, amendments A1–A12, the frozen held-out code) and the `claims.tsv`
numbers, and exits non-zero on any mismatch. `LLM_*` variables or `make run-gguf` add a live slice against the
published reference band. Seeds: generator 261, bootstrap 0 (2,000 resamples). **License:** code Apache-2.0; dataset CDLA-Permissive-2.0; this report CC-BY-4.0.

## References

Art. 261bis and Art. 2 StGB, SR 311.0 (Fedlex, versions of 1 Jan 1995 and 1 Jul 2020); AS 1994 2887; AS 2020 1609.
BGE 130 IV 111. Fan et al., LEXam, ICLR 2026. Han et al., LawShift, NeurIPS 2025 D&B. Servantez et al., OpenExempt,
ACL Findings 2026. Huang et al., When Do LLMs Apply the Wrong Law?, arXiv 2608.14610. Röttger et al., Multilingual
HateCheck, WOAH 2022.
