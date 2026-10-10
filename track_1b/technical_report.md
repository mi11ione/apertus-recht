# Apertus-Recht: which racial-discrimination law does Apertus apply?

People ask chat assistants whether something they said is punishable. We release 1,980 German, French and Italian
scenarios under Art. 261bis StGB, built as minimal twins that change one legal fact at a time. Intent and the dignity
threshold are stipulated, so the set tests how a model applies the elements, not whether it predicts a conviction.
Each verdict is computed by code from pinned Fedlex texts and agrees with ⟨court_ofk⟩ Swiss court rulings we could
code. Without the law, Apertus v1.5 70B convicts every German scenario and, in free text, calls ⟨open_r0_mislead⟩ of 75
lawful ones punishable. Rules spelled out in plain sentences make it apply the publicity rule, but not the closed list
of protected groups or the date the article took effect. Pasting the verbatim law undoes even that. A second statute
fails in another shape. One command re-derives every label and number.

**Track:** Apertus Readiness · Track 1B (Swiss Voices, behavioural alignment) · **Event:** Online · **Team:** 444  
**Demo:** https://apertus-recht.mi11ion.io (every scenario, its gold and Apertus's answers) · `make run` (Docker, CPU, no key)

----

### Use of Apertus

- **Model:** Apertus v1.5 70B; Apertus v1.5 8B (public Q4_K_M GGUF; for exploration also the SFT, RLVR, DPO and final
  stages, bf16 blends, Q8_0 and MLX 4-bit builds).
- **How it is used:** evaluation only: forced choice, preference pairs, and free text read by three blind judges.
- **Where it runs:** the 70B on Public AI through a cost-capped gateway. Public AI's name `apertus-v1.5-8b` currently
  serves the 70B (same output as `-70b` on 760 of 792 test prompts, `docs/builds.md`), so every hosted number is the
  70B. The 8B runs as the public GGUF on CPU in GitHub Actions.
- **Links:** code https://github.com/mi11ione/apertus-recht · dataset https://huggingface.co/datasets/mi11ion/apertus-recht

----

## Use Case Description

Art. 261bis StGB punishes racial discrimination; since 1 July 2020 it also covers sexual orientation. Whether a
statement is punishable turns on three elements a layperson cannot check:

- **Publicity.** Under BGE 130 IV 111 E. 5.2, statements among family, friends or in a setting of personal trust are
  not public.
- **The closed list.** Only race, ethnicity, religion and sexual orientation are protected.
- **The date.** The article entered into force on 1 January 1995; sexual orientation is covered from 1 July 2020.

A wrong answer misinforms people about their own speech, in either direction. The users are Swiss residents asking an
assistant in German, French or Italian, with or without the law in context (Apertus-v1.5-8B: ⟨hf_downloads⟩
downloads in the 30 days before 9 October 2026). The article was adopted by referendum in 1994 and extended by
referendum in 2020; Apertus's training data contain BGE 130 IV 111 verbatim. The dataset asks not "how often is the
model right" but **which law it applies**, element by element.

## Dataset Summary

Per language: 660 scenarios in 220 twin groups (220 base, 215 true flips, 210 placebos, 15 contested); verdicts
430 convict, 215 acquit, 15 open. Each scenario has an acceptance criterion, an item-specific `chosen` answer, a
`rejected` answer and a length-matched mirror, a settled or contested label, its normative source and its
element-by-element derivation. The 660 German scenarios are also retold in the first person (`de_lay`).

| Term | Meaning |
|---|---|
| Twin | a variant that changes exactly one fact of its base. A *true flip* changes the verdict; a *placebo* does not. |
| Rung | how much law the prompt carries. **R0** no law · **R3** rules spelled out (the elements, a one-sentence paraphrase of BGE 130 IV 111, the closed list) · **R4** R3 plus one sentence on the 2020 extension · **R5** verbatim law (Fedlex text of Art. 261bis and Art. 2 StGB, the Regeste) · **R6** R5 with an instruction to check each element |
| Framing | how the verdict is asked: Ja/Nein, or the verdict word ("Urteil: schuldig / nicht schuldig") |
| Misapplied (red) | the model convicts a variant the law acquits, while it convicts the unchanged base (95% intervals) |
| Read-back | the law the model applies, element by element, read off the twins |

| Family (groups per language) | One-fact change of the base | Tests |
|---|---|---|
| SET (55) | public → private setting; placebo: family wording of a public statement | BGE 130 IV 111 E. 5.2 |
| CHAR (60), CHARX (20) | protected → unprotected characteristic; placebo: synonym ("Hautfarbe", "Glaube") | closed list |
| DATE_SO (35) | sexual orientation 2021–25 → before 1 Jul 2020; placebo: 1 Jul / Aug 2020 | AS 2020 1609, Art. 2 StGB |
| DATE_CTRL (25) | race, ethnicity, religion → 2018–20 (placebo) and → 1993/94 | over-application; entry into force |
| CONTESTED (15) | public → fact-dependent setting (gold `open`) | hedging |
| WORDING (10) | another wording family; another paragraph | wording invariance |

Unprotected characteristics: gender identity, sex, canton, occupation, age, disability, political opinion. The
wording is templated (18 act wordings, 29 settings, 33 group phrases; 44 words on average): that is the price of exact
twins.

**What is new.** To our knowledge no dataset lets one test which version of a real statute a model applies, element by
element, in the three official languages (sources in `docs/prior-art.md`):

| Dataset | Languages | Gold | One-fact twins | Real amendment dates | Checked against courts |
|---|---|---|---|---|---|
| LEXam / SwissLegalEvals | DE, EN / DE, FR, IT | exam keys, LLM judges | no | no | no |
| LawShift (NeurIPS 2025) | ZH | expert metamorphic relations | yes | hypothetical revisions | no |
| TALD (2026) | ZH | statute version cited in judgments | no | which version applies | from judgments |
| OpenExempt (2026) | EN | solver over expert encodings | single-factor suites | one deadline rule | no |
| Multilingual HateCheck | DE, FR, IT, … | by construction | templated contrasts | no (not legal) | no |
| **Apertus-Recht** | **DE, FR, IT** | **code from pinned Fedlex texts** | **yes, with placebos** | **1995, 2020, Art. 2 StGB** | **⟨court_agree⟩ rulings** |

## Data Collection Method

**No data was collected from people.** A seeded generator renders the scenarios from YAML templates. A 97-line engine
computes each verdict from a machine-readable element model of the statute (`statutes/stgb_261bis/statute.yaml`).
Every element cites a pinned source: the Fedlex texts of Art. 261bis before and since 1 July 2020 and of Art. 2 StGB in
three languages (sha256 of each text), the amendment footnotes, and the Regeste of BGE 130 IV 111. The engine, not the
author, labels each variant a true flip, a placebo or contested; the generator refuses to build if that disagrees with
the design. French and Italian were translated by Claude agents with the official terms, back-translated blind (0
critical findings) and localised by a lawyer-persona review (places in Romandie and Ticino, Swiss formulas).

**Verification without human labels.** Because gold is computed, review looks for errors in the code, the element model
or the wording. Every review step was done by Claude agents working blind on opaque ids, without code or gold.
- **Annotation:** six agents labelled 960 items; they agree with the code on ⟨ann_settled⟩ settled items and name the
  deciding element in 315/315 acquittals. A second pass that saw only the law agreed on 939/939.
- **Adjudication:** two independent adjudicators reviewed every disagreement, every contested item and a blind 10%
  sample. Gold was wrong in 0 of 94 sampled items.
- **Court validation:** ⟨court_triaged⟩ citing Art. 261bis were triaged and coded twice (κ 0.83–0.98). The engine
  agrees with ⟨court_agree⟩ in-scope rulings, ⟨court_cases⟩ distinct cases (repeat instances merged, Perinçek left out
  as revised after Strasbourg). This tests the conviction rules well and the acquittal rules thinly: an engine that
  always convicts would score 55/57. One of the two acquittals is clean; one agrees on another ground (A15).
- **Wording fixes:** two defects were found before any result was analysed (A3) and four after (A5). All were fixed and
  re-scored; the pre-fix responses are archived.

## Dataset Details

**Quality gates** (`statute-twins qc`, all passing): schema; gold recomputed for every item; twin invariants; no
duplicates; language identity; canary; a PII scan of items, responses and metadata (0 hits). Tests check every
closed-list term and both in-force dates against the official text in three languages. Mutation tests (drop religion
from the list, move the 2020 date by a day, make private settings public) flip exactly the items each rule governs.

**Contamination.** None of our 35,241 distinct 13-grams occurs in the 1,069,365 decisions of `voilaj/swiss-caselaw`;
the same scan finds 846 of the 1,525 13-grams of the statute and the Regeste (positive control).

**Ethics and licensing.** No data subjects: generic actors, groups named by their characteristic, abstract acts.
CDLA-Permissive-2.0 with per-item licence components; statute and decision texts are public domain (Art. 5 URG). A
consent form with an AI-use clause is ready for human reviewers. Every item carries a canary string.

## Evaluation

**Three measurements on one item set.**
- *Forced choice* (all items, R0 to R5, two framings): the log-probability of the convicting answer minus the
  acquitting one, exact on vLLM (prefilled answer), from the logits in llama.cpp.
- *Preference* (settled items, R0): the same scoring between each item's `chosen` answer and its mirror, the same
  sentence with the verdict and the deciding legal claim negated (median length ratio 1.0).
- *Free text* (the same 240 items in each language, R0, R3, R5, greedy): each answer is judged against its acceptance
  criterion by three blind judges. Two are Claude judges; they agree on ⟨open_judges_agree⟩ pass decisions
  (κ ⟨open_kappa⟩), which measures self-consistency of one model. The independent judge is Qwen-SEA-LION-v4-32B: it agrees
  with their consensus on ⟨judgec_agree⟩ (κ ⟨judgec_kappa_acq⟩ on acquittal and open items). A deterministic parser of
  each answer's verdict agrees on ⟨parser_agree⟩ settled answers. A seeded 20% sample is laid out for a human check.

**The read-back.** Each true flip is paired with its base, which the statute convicts. With 95% item-bootstrap
intervals of the mean log-odds of conviction, an element is *misapplied* when both lie above zero. A framing in which
the base itself is not convicted cannot be read. The pre-registered test fits the read-back on two wording families
and predicts the third; it passes if it beats the statute by at least 0.15 in every readable framing.

**Runs.** The 70B on Public AI (vLLM, temperature 0) in three languages at R0 to R5; the 8B public Q4_K_M GGUF
(sha256 `a037df8d…`) on CPU CI runners, German R0 to R5; preference on 645 settled items per language; free text on
720 answers per language; Art. 179ter (120 items); the 162-item battery for training stages. Every row records the
served model and a request hash.

## Results

⟨table:twin⟩

*Table 1. One twin pair (German, Apertus 70B): a speech at an authorised rally before about 300 people, and the same
words in a private message to her sister. Only the setting differs; the law convicts the first and acquits the second.
Red: an answer the law does not support. Apertus convicts the private message without the law (R0) and again with the
verbatim law (R5); only the rules spelled out (R3) fix it. Its free-text answer ("Yes, the woman's conduct is
punishable under Swiss law") is misleading for all three judges.*

**Without the law, the 70B convicts everything.** At R0 the recall of acquittals is at most 0.01 in every language and
framing. The model is not blind to the facts: its scores still rank punishable above lawful cases (AUC ⟨auc_r0⟩).
But the threshold sits so far on the convicting side that no case falls below it. Asking the other way round ("would a
court acquit?") changes nothing: ⟨rev_r0⟩ of 215 acquittals in every language, so this is not a bias towards "yes".
In free text the judges fail ⟨open_r0_mislead⟩ of 75 answers to lawful scenarios as misleading; every one names
Art. 261bis. The independent judge alone counts ⟨judgec_r0⟩.

⟨table:accuracy⟩

*Table 2. Balanced accuracy (mean of the recall of convictions and of acquittals; 0.50 = no discrimination), Ja/Nein /
verdict word, and the recall of acquittals at R3. The first-person retelling was run at R0 and R3 only.*

**With the rules spelled out (R3), publicity is applied; the closed list and the date are not.** Figure 1 shows each
element for the German 70B:
- **Private settings** are acquitted. Every private variant names family or friends, the words of the paraphrase, so
  this shows uptake of a stated example more than application of BGE 130 IV 111.
- **Canton, disability and political opinion** stay red: convicted although the prompt lists the four protected
  characteristics. Gender identity is applied once the prompt names it as excluded.
- **The R3 gain is fragile.** Asked whether a court would acquit, the 70B also acquits half the punishable cases, and
  its scores rank the cases backwards (AUC ⟨r3_rev_auc⟩). Averaged over both question directions, private settings
  still hold; most other acquittals do not (Table 3).
- **The date sentence (R4) backfires.** One sentence saying that sexual orientation is protected since 1 July 2020
  makes the 70B acquit the earlier cases, but also stop convicting punishable cases from 2021–25: 0 of 35 with the
  verdict word in German. The 8B convicts ⟨so8b_conv⟩ of 35 with Ja/Nein (⟨so8b_ver⟩ with the verdict word). The
  sentence does not teach the date; it takes the characteristic off the list.
- **Acts from 1993/94**, before the article entered into force, are convicted at every rung. No rung states the 1995
  date, so this is a gap in what the model knows.

**The verbatim law (R5) undoes the rules.** Given the Fedlex text and the Regeste, as a retrieval pipeline would paste
them, the German 70B convicts everything again: ⟨r5_acq_conv⟩ of 215 acquittals with Ja/Nein, ⟨r5_acq_ver⟩ with the
verdict word. In French and Italian it recognises ⟨r5_fr⟩ and ⟨r5_it⟩, against 120 and 97 with the rules spelled out.
In free text, ⟨open_r5_mislead⟩ of 75 answers to lawful scenarios call them punishable. The scores do register the
facts (a private setting lowers the conviction score by 6.6 nats, from 14.7), but never below the threshold. No single
part of the law text explains it (Table 3).

![](docs/figures/fig1_synopse.png)

*Figure 1. The law in force (column "Law") next to the law Apertus applies. Each row changes one legal fact of a
scenario the statute punishes (above the rule) or a detail that changes nothing (below). Cells: variants convicted
(k/n, Ja/Nein). Red: a law that is not in force is applied, in both framings; light red: in one; grey: the base is not
convicted either, so the element cannot be read. ↓: the variant's score is below the base's (paired 95% interval).*

![](docs/figures/fig2_rungs.png)

*Figure 2. Acquittals recognised and convictions kept by rung (Ja/Nein): the rules move every model; the verbatim law
undoes it.*

| Check | Result | What it rules out |
|---|---|---|
| Question reversed ("… freisprechen?"), R0 | ⟨rev_r0⟩ of 215 acquittals, every language | a bias towards "yes" |
| Question reversed, R3 | German: balanced accuracy ⟨r3_rev_bal⟩, averaged over both directions ⟨r3_avg⟩ of 215 (private settings ⟨r3_avg_set⟩ of 55); Italian: convicts all | nothing: part of the R3 gain is answer format |
| R3's rules after the verbatim law · after legal text of the same length that does not apply | ⟨r5a_same⟩ · ⟨r5e_same⟩ acquittals (R3 alone ⟨r3_same⟩, same items) | prompt length: it is the law's own text |
| R6: element check plus the verbatim law | ⟨r6_acq⟩ of 215 | a missing instruction in R5 |
| Free text, French / Italian (misleading of 75, R0 · R5) | ⟨ft_fr_r0⟩ · ⟨ft_fr_r5⟩ / ⟨ft_it_r0⟩ · ⟨ft_it_r5⟩ | a German-only effect |
| First-person retelling (German) | R0: ⟨lay_acq⟩ of 215 acquittals; R3: balanced accuracy ⟨lay_r3_bal⟩ | an artefact of legal register |
| Art. 179ter, a second statute (German, 120 items) | R0: "Nein" to all ⟨r179_r0_nein⟩ (Ja/Nein), "schuldig" to ⟨r179_r0_ver⟩ (verdict word); with the rules: ⟨r179_r2⟩ | an effect of one article |

*Table 3. Controls (A13–A15; details in `prereg/AMENDMENTS.md` and `reports/controls_a13.json`). Art. 179ter: with
its elements and the complaint rule stated, a public debate and an outsider (whose act falls under Art. 179bis) are
still convicted.*

⟨table:preference⟩

*Table 4. Preference: share of settled items where the model scores the `chosen` answer above its length-matched
mirror. Free text: answers that meet the acceptance criterion (240 German items). Columns: the deciding element.*

**Recognising the law is not applying it.** Shown an item's correct answer and its mirror, the 70B picks the correct
one (German ⟨pref_de_all⟩), most cleanly in the closed-list and date columns, although its own verdicts convict those
cases. In French it prefers the mirror for half the punishable cases (0.53); we have not isolated why.

**Pre-registered held-out test.** At R0 it passes trivially: a model that convicts everything is predicted perfectly.
At R3 and R4 the read-back beats the statute in every cell, but not by the pre-registered 0.15 in every framing. The
test fails, and by our rule these rungs report Figure 1, not the read-back. Two cells could not pass at all, and the
split varies only the wording, so it tests wording invariance.

⟨table:heldout⟩

*Table 5. Held-out read-back test at the informative rungs (fit: wording families A, B; test: C). Pass: gain ≥ 0.15
in every readable framing.*

**Post-training and builds** (8B, 162-item battery; one checkpoint pair, so a lead): RLVR → DPO cuts correct
acquittals under stated rules from ⟨stage_rlvr⟩ to ⟨stage_dpo⟩ of 220 while keeping 104/104 convictions. The public
Q8_0 GGUF agrees with bf16 on 638 of 648 decisions, the Q4_K_M on 622, our MLX 4-bit conversion on 548.

## Dataset Limitations

- **Depth over breadth.** One statute modelled exactly, three of its five paragraphs. Intent, the characteristic and
  the dignity threshold are stated in the facts, where most court acquittals turn, so the set measures element
  application, not conviction prediction. A second statute (Art. 179ter) is released in the same five-file format.
- **Exact twins need controlled wording.** The first-person retelling shows the findings hold outside the charge-sheet
  register.
- **Two contestable legal choices, stated.** An Abs. 2 act ("propagating an ideology") is also told as a one-off
  statement; an online post before 1 July 2020 counts as completed on publication (dropping those items moves no
  accuracy by more than ⟨sens_max⟩ points).
- **Every review is re-runnable**: agent runs with their instructions in the repository, no private human judgment in
  the gold. One model family's blind spots are checked from outside it: the gold against the official text, mutation
  tests and court decisions; the free text by an independent judge and a parser.
- **Contested items are few** (15 per language). Accuracy intervals treat items as independent; held-out gains use
  twin-group bootstraps.

## Lessons Learnt and Recommendations

- **Users:** do not ask about Art. 261bis without the law in context, and do not count on pasting the statute. State
  the rule the case turns on in a plain sentence, and check the characteristic and the date yourself. Prefer the Q8_0
  GGUF or the served model to 4-bit MLX conversions.
- **Developers:** in our one checkpoint pair, DPO costs acquittals under stated rules (8B: ⟨stage_rlvr⟩ → ⟨stage_dpo⟩ of
  220). The model obeys exclusions it is told but not "the list is closed", and reads plain rules but not the law as
  written: instruction-following and long-context legal reading are training targets. Keep the `chosen` / `rejected`
  pairs out of training if you evaluate on them.

## Reproducibility

`make run` (Docker, CPU, no key, no model) regenerates the dataset from the YAML (sha256 per file), recomputes every
result from the stored responses, checks every request hash against its prompt, re-aggregates the judges, checks the
pre-registration (`prereg-verify`: locked files, amendments A1–A15, the frozen held-out code) and the `claims.tsv`
numbers for both statutes, and exits non-zero on any mismatch. `LLM_*` variables or `make run-gguf` add a live slice.
Seeds: generator 261, bootstrap 0 (2,000 resamples). **License:** code Apache-2.0; dataset CDLA-Permissive-2.0; this
report CC-BY-4.0.

## References

Art. 261bis, 179ter, 1, 2, 30, 31 StGB, SR 311.0 (Fedlex consolidations of 1 Feb 2020 and 1 Oct 2026); AS 1994 2887;
AS 2020 1609. BGE 130 IV 111. Fan et al., LEXam, ICLR 2026. Han et al., LawShift, NeurIPS 2025 D&B. Servantez et al.,
OpenExempt, ACL Findings 2026. Huang et al., When Do LLMs Apply the Wrong Law?, arXiv 2608.14610. Röttger et al.,
Multilingual HateCheck, WOAH 2022.
