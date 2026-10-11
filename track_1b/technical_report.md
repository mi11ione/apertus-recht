# Apertus-Recht: which version of Art. 261bis StGB does Apertus apply?

People ask chat assistants whether something they said is punishable. Apertus-Recht releases 1,980 German, French and
Italian minimal-twin scenarios under Art. 261bis StGB, each verdict computed by code from pinned Fedlex texts and
consistent with ⟨court_ofk⟩ Swiss court rulings we could code (always-convict: 55). Without the law, Apertus v1.5 70B convicts all but at most
one of 215 lawful German scenarios. Plain rules restore publicity and the exclusions they name, but not canton,
disability, political opinion or the dates; the verbatim law takes the gain back. One command re-derives every number.

**Track:** Apertus Readiness · Track 1B (Swiss Voices, behavioural alignment) · **Event:** Online · **Team:** 444  
**Demo:** https://apertus-recht.mi11ion.io (every scenario, its gold and Apertus's answers) · `make run` (Docker, CPU, no key)

----

### Use of Apertus

- **Model:** Apertus v1.5 70B; Apertus v1.5 8B (public Q4_K_M GGUF; for exploration also the SFT, RLVR, DPO and final
  stages, bf16 blends, Q8_0 and MLX 4-bit builds).
- **How it is used:** evaluation only: forced choice, preference pairs, and free text read by three blind judges.
- **Where it runs:** the 70B on Public AI through a cost-capped gateway; the 8B as the public GGUF on CPU in CI. Public
  AI serves the 70B under the name `apertus-v1.5-8b` (same output as `-70b` on 760 of 792 prompts; `docs/builds.md`).
- **Links:** code https://github.com/mi11ione/apertus-recht · dataset https://huggingface.co/datasets/mi11ion/apertus-recht

----

## Use Case Description

Art. 261bis StGB [1] (Diskriminierung und Aufruf zu Hass) punishes discrimination on grounds of race, ethnicity and
religion; since 1 July 2020 it also covers sexual orientation. Whether a statement is punishable turns on elements a
layperson cannot check:

- **Publicity.** Under BGE 130 IV 111 [2] E. 5.2, statements among family, friends or in a setting of personal trust are
  not public.
- **The closed list.** Only race, ethnicity, religion and sexual orientation are protected.
- **The date.** The article entered into force on 1 January 1995; sexual orientation is covered from 1 July 2020.
- **The dignity threshold.** Under BGE 131 IV 23 [2] E. 3, degrading (Abs. 4) means denying, or at least questioning,
  equal worth as human beings or equal human rights; criticism that stays objective does not suffice.

A wrong answer misinforms people about their own speech, in either direction. The users are Swiss residents asking an
assistant in German, French or Italian, with or without the law in context (Apertus-v1.5-8B: ⟨hf_downloads⟩
downloads in the 30 days before 9 October 2026). The dataset asks not "how often is the model right" but **which law
it applies**, element by element. Every Art. 261bis scenario carries a note fitted to the case: on a lawful one, what "not
punishable under Art. 261bis" does not mean and where to turn; on a punishable one, that this assesses the stated facts,
not legal advice, and where those affected can turn.

## Dataset Summary

Per language: 660 scenarios in 220 twin groups (220 base, 215 true flips, 210 placebos, 15 contested); verdicts
430 convict, 215 acquit, 15 open. Each scenario has an acceptance criterion, an item-specific `chosen` answer, a
`rejected` answer and a length-matched mirror, a settled or contested label, its normative source and its
element-by-element derivation. Released alongside: the scenarios retold in the first person (all three languages),
334 natural paraphrases verified blind, a dignity-threshold family (60 per language), and a second statute
(Art. 179ter, 120 items).

| Term | Meaning |
|---|---|
| Twin | a variant that changes exactly one fact of its base. A *true flip* changes the verdict; a *placebo* does not. |
| Rung | how much law the prompt carries. **R0** no law · **R3** rules spelled out (the elements, a one-sentence paraphrase of BGE 130 IV 111, the closed list, and that gender identity and sex are not covered) · **R4** R3 plus one sentence on the 2020 extension · **R5** verbatim law (Fedlex text of Art. 261bis and Art. 2 StGB, the Regeste) · **R6** R5 with an instruction to check each element. R1 and R2 are intermediate steps of R3, used in exploration. Controls: **R5a** R3's rules after the verbatim law; **R5e** the same rules after unrelated legal text of equal length. |
| Framing | how the verdict is asked: Ja/Nein, or the verdict word ("Urteil: schuldig / nicht schuldig") |
| Misapplied (red) | the model convicts a variant the law acquits, while it convicts the unchanged base (95% intervals); for a placebo, a change that should not matter, it stops convicting |
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
wording is templated (18 act wordings, 29 settings, 33 group phrases; 44 words on average), which is what makes the
twins exact; the natural paraphrases show the results do not depend on it.

**What is new.** To our knowledge no dataset lets one test which version of a real statute a model applies, element by
element, in the three official languages; the closest work asks when models apply the wrong law [5] (sources in
`docs/prior-art.md`):

| Dataset | Languages | Gold | One-fact twins | Real amendment dates | Checked against courts |
|---|---|---|---|---|---|
| LEXam [3] / SwissLegalEvals | DE, EN / DE, FR, IT | exam keys, LLM judges | no | no | no |
| LawShift [4] | ZH | expert metamorphic relations | yes | hypothetical revisions | no |
| TALD [5] | ZH | statute version cited in judgments | no | which version applies | from judgments |
| OpenExempt [6] | EN | solver over expert encodings | single-factor suites | one deadline rule | no |
| Multilingual HateCheck [7] | DE, FR, IT, … | by construction | templated contrasts | no (not legal) | no |
| **Apertus-Recht** | **DE, FR, IT** | **code from pinned Fedlex texts** | **yes, with placebos** | **1995, 2020, Art. 2 StGB** | **⟨court_agree⟩ rulings (always-convict 55)** |

## Data Collection Method

**No data was collected from people.** A seeded generator renders the scenarios from YAML templates; a 100-line engine
computes each verdict from an element model of the statute whose every element cites a pinned source (Fedlex texts of
Art. 261bis before and since 1 July 2020 and Art. 2 StGB in three languages, the amendment footnotes, the Regestes of
BGE 130 IV 111 and 131 IV 23, each with its sha256). The engine labels each variant a true flip, placebo or contested,
and the generator refuses to build if that disagrees with the design. French and Italian were translated by agents,
back-translated blind and localised (Romandie, Ticino). Every change after the hash-frozen pre-registration is a
timestamped amendment (`prereg/AMENDMENTS.md`).

**Verification by re-runnable checks.** Annotation ran blind, on opaque ids, without code or gold, by Claude agents and
Qwen-SEA-LION-v4-32B; adjudication and legal review then checked the gold itself.
- **Annotation:** six agents labelled 960 items; they agree with the code on ⟨ann_settled⟩ settled items and name the
  deciding element in 315/315 acquittals; a second pass that saw only the law agreed on 939/939. Qwen, given the same
  law-only task, agrees on ⟨qwen_gold⟩; each of its ⟨qwen_gold_dis⟩ disagreements convicts a case the pinned text does
  not cover (pre-2020 sexual orientation, pre-1995, unlisted characteristics), the same errors Apertus makes.
- **Adjudication:** two independent adjudicators reviewed every disagreement, every contested item and a blind 10%
  sample: gold was wrong in 0 of 94 sampled items (Wilson 95% upper bound ⟨gold_ub⟩).
- **Courts:** ⟨court_triaged⟩ citing Art. 261bis were triaged and their elements and outcome extracted twice (Cohen's
  κ 0.83–0.98 per field). The engine agrees with ⟨court_agree⟩ in-scope rulings (Wilson 95% 0.94–1.00; always-convict:
  55), ⟨court_cases⟩ distinct cases; the 10 genocide-denial rulings among them agree on publicity, characteristic and
  date only (the denial clause is not modelled). Of the two acquittals, one agrees on the court's own ground (the
  closed list); in the other the engine reaches the court's acquittal on a different element. Seven further rulings
  read the dignity threshold (A20; agreement ⟨dgc_agree⟩ of 7, always-convict 4; details in the card).
- **Mutation tests** (drop religion from the list, move the 2020 date by a day, make private settings public) flip
  exactly the items each rule governs.

## Dataset Details

**Quality gates** (`statute-twins qc`, all passing): schema; gold recomputed for every item; twin invariants; no
duplicates; language identity; canary; a PII scan of items, responses, metadata and the released review records
(0 hits). Tests check every closed-list term and both in-force dates against the official text in three languages.

**Contamination.** None of the 35,241 distinct 13-grams of the core items (scan of 9 October, before the later
wording amendments) occurs in the 1,069,365 decisions of `voilaj/swiss-caselaw`, a
v1.5 pre-training source in the Apertus data catalogue; the same scan finds 846 of the 1,525 13-grams of the statute and
the Regeste (positive control). The retellings, paraphrases and dignity family were written after that data was
collected.

**Ethics and licensing.** The scenarios have no data subjects; the court-validation records are pseudonymised data on
criminal proceedings from public decisions, cited by docket, naming no private person. CDLA-Permissive-2.0 with per-item licence components and provenance; legal texts public domain (Art. 5
URG); consent form with an AI-use clause; a content warning; a canary string in every item record and a scope note on every Art. 261bis item.

## Evaluation

**Three measurements on one item set.**
- *Forced choice* (all items at R0, R3, R4, R5, both framings; R6 German on all items, French and Italian on 240):
  the log-probability of the convicting answer minus the acquitting one (exact on vLLM; logits in llama.cpp).
- *Preference* (settled items, R0): the same scoring between each item's `chosen` answer and a mirror. Two mirrors:
  the same sentence with the verdict and the deciding legal claim negated, and `chosen` word for word with only the
  verdict flipped.
- *Free text* (240 items per language, R0, R3, R5, greedy), judged against each acceptance criterion by two Claude
  judges (⟨open_judges_agree⟩ German decisions agree, κ ⟨open_kappa⟩), Qwen-SEA-LION-v4-32B (⟨judgec_agree⟩ with their
  consensus; κ ⟨judgec_kappa_acq⟩, ⟨judgec_kappa_acquit⟩ on acquittals, ⟨judgec_kappa_open⟩ on 20 contested answers) and a
  verdict parser (⟨parser_agree⟩ settled answers); a seeded 20% sample is released for audit.

**The read-back.** Each true flip is paired with its base, which the statute convicts. With 95% bootstrap intervals of
the mean log-odds of conviction, an element is *misapplied* when both lie above zero; a framing in which the base itself
is not convicted cannot be read. The pre-registered
test fits the read-back on two wording families and predicts the third; it passes a rung if it beats the statute by at
least 15 points in every readable framing.

**Runs.** The 70B in three languages; the 8B public Q4_K_M GGUF on CPU CI runners in three languages; Art. 179ter (120
items); the 162-item battery for training stages. Released runs record the served model and a request hash per row;
the exploration runs (training stages, builds) are imported with their outputs.

## Results

**Pre-registered test.** The locked result is Figure 2, the law each model applies, element by element. Fitted on two
wording families, this read-back predicts the third better than the statute in ⟨ho_anch⟩ readable cells at R3 and R4
(⟨ho_ci_pos⟩ with the 95% interval above zero); at R3 it predicts ⟨ho_acc⟩ of the 70B's held-out verdicts and
⟨ho_share⟩ of its departures from the statute. The locked 15-point bar is met at R3 only for the 8B in Italian (16.2,
interval 10.6–21.2), while the German and Italian 70B reach 14.8 (10.0–18.6 and 10.5–19.5): pass and near-miss lie
within each other's noise. Everything after this paragraph is exploratory.

**Without the law, the 70B convicts nearly everything.** At R0 the recall of acquittals is at most 0.01 in every
language and framing (Table 2; Figure 1 shows every model by rung); Table 1 shows one twin pair. The model is not blind
to the facts: its scores still rank punishable above lawful cases (AUC ⟨auc_r0⟩); the threshold sits so far on the
convicting side that no case falls below it. Asking the other way round ("would a court acquit?") gives ⟨rev_r0⟩ of
215 acquittals in every language, so this is not a bias towards "yes". In free text the judges fail ⟨open_r0_mislead⟩
of 75 answers to lawful scenarios as misleading (the independent judge alone: ⟨judgec_r0⟩); every one names Art. 261bis.

⟨table:twin⟩

*Table 1. One twin pair (German, Apertus 70B): a speech at an authorised rally before about 300 people, and the same
words in a private message to her sister. Only the setting differs; the law convicts the first and acquits the second.
Red: an answer the law does not support. Apertus convicts the private message without the law (R0) and with the
verbatim law (R5); only the rules spelled out (R3) fix it. Its free-text answer ("Yes, the woman's conduct is
punishable under Swiss law") is misleading for all three judges.*

⟨table:accuracy⟩

*Table 2. Balanced accuracy (mean of the recall of convictions and of acquittals; 0.50 = no discrimination), Ja/Nein /
verdict word, and the recall of acquittals at R3. The first-person retelling was run at R0 and R3 only.*

![](docs/figures/fig2_rungs.png)

*Figure 1. Share of the 215 lawful scenarios acquitted (solid) and of the 430 punishable ones convicted (dashed), by
rung, Ja/Nein. R5 replaces the rules with the verbatim law; it is not a further step of R3.*

**With the rules spelled out (R3), publicity and the named exclusions are applied; the rest of the closed list and the
dates are not** (Figure 2):
- **Private settings** are acquitted (German 70B 50 of 55), and the family-worded public placebos are still convicted
  (⟨plc_r3_set⟩): the model reads the setting, not the words "family" or "friends". Asked the other way round ("would a
  court acquit?"), it acquits ⟨rev_r3_priv⟩ of them: with the rules, the answer leans towards "yes" whichever way the
  question is put, a bias that cancels when both directions are averaged (Table 3).
- **Gender identity and sex**, which the prompt names as excluded, are acquitted; **canton, disability and political
  opinion** stay red in German although the prompt lists the four protected characteristics.
- **The date sentence (R4) backfires.** One sentence saying that sexual orientation is protected since 1 July 2020
  makes the 70B acquit the earlier cases, but also stop convicting punishable cases from 2021–25: 0 of 35 with the
  verdict word in German (3 with Ja/Nein). The 8B convicts ⟨so8b_conv⟩ of 35 with Ja/Nein (⟨so8b_ver⟩ with the verdict
  word). Across all punishable German scenarios the 70B convicts ⟨so_r4⟩ about sexual orientation (R3: ⟨so_r3⟩), against
  ⟨oth_r4⟩ about race, ethnicity and religion: the sentence does not teach the date; it takes the characteristic off the
  list.
- **Acts from 1993/94**, before the article entered into force, are convicted by the 70B at every rung.

![](docs/figures/fig1_synopse.png)

*Figure 2. The law in force (column "Law") next to the law Apertus applies. Each row changes one legal fact of a
scenario the statute punishes (above the rule) or a detail that changes nothing (below); each column is a rung of one
model. Filled square: the model applies a law that is not in force (both framings, 95% intervals); half-filled: in one
framing; open: it applies the law in force; grey with a dot: undetermined (the interval spans zero); dash: the base
itself is not convicted, so the row cannot be read.*

**The verbatim law (R5) takes the gain back.** Given the Fedlex text and the Regeste, as a retrieval pipeline would
paste them, the German 70B acquits ⟨r5_acq_conv⟩ of the 215 lawful scenarios with Ja/Nein, ⟨r5_acq_ver⟩ with the verdict
word; French and Italian acquit ⟨r5_fr⟩ and ⟨r5_it⟩ (Italian keeps most private settings). The scores still separate the
cases (AUC ⟨auc_r5⟩, against ⟨auc_r0⟩ at R0 and ⟨auc_r3⟩ at R3): the law moves the threshold back to "convict". In free text,
⟨open_r5_mislead⟩ of 75 German answers to lawful scenarios call them punishable. It is the law's text, not its length:
on the same 75 lawful items, unrelated legal text of equal length leaves ⟨r5e_same⟩ acquitted, the verbatim law before
the same rules ⟨r5a_same⟩ (McNemar p = ⟨mcn_p⟩). No single part of the text explains it: without the Regeste's example,
with an element check or with Art. 1 StGB, at most ⟨r5a_abl_max⟩; with the rules placed before the law, private settings
come back (⟨r5ag_priv⟩) and the unlisted characteristics are lost.

| Control | Result | Shows |
|---|---|---|
| Question reversed ("acquit?"), no law | ⟨rev_r0⟩ of 215 lawful acquitted, every language | not a yes-bias |
| Question reversed, rules spelled out | German balanced accuracy ⟨r3_rev_bal⟩ (AUC ⟨r3_rev_auc⟩); both directions averaged: ⟨r3_avg⟩ of 215 acquitted, ⟨r3_avg_set⟩ of 55 private | the R3 gain depends on the question's direction |
| Rules alone (R3), of 75 lawful German | ⟨r3_same⟩ acquitted | baseline |
| Verbatim law, then the same rules (R5a) | ⟨r5a_same⟩ acquitted | the law's text hurts |
| Unrelated legal text of equal length, then the rules (R5e) | ⟨r5e_same⟩ acquitted | not the length |
| Verbatim law + element check (R6), of 215 | ⟨r6_acq⟩ acquitted, every one a private setting | an instruction helps little |
| Free text, French · Italian (misleading of 75, R0 / R5) | ⟨ft_fr_r0⟩ / ⟨ft_fr_r5⟩ · ⟨ft_it_r0⟩ / ⟨ft_it_r5⟩ | not German-only |
| First person, of 215 lawful, acquitted | no law DE ⟨lay_acq⟩ · FR ⟨layfr_r0⟩ · IT ⟨layit_r0⟩; rules ⟨lay_r3⟩ · ⟨layfr_r3⟩ · ⟨layit_r3⟩ (third person: 107 · 120 · 97) | not legal register |
| Natural paraphrases, ⟨para_acq_n⟩ lawful | no law ⟨para_r0⟩, rules ⟨para_r3⟩ (templated: ⟨orig_r0⟩, ⟨orig_r3⟩) | not the template |
| Art. 179ter, 120 items | no law: "Nein" to all ⟨r179_r0_nein⟩ (Ja/Nein), "schuldig" to ⟨r179_r0_ver⟩; rules: balanced ⟨r179_r2⟩ | a second statute fails in another shape |
| Lawful criticism of a religion, of 20, convicted (Ja/Nein): no law · rules | DE ⟨dg_de_r0⟩ · ⟨dg_de_r3⟩, FR ⟨dg_fr_r0⟩ · ⟨dg_fr_r3⟩, IT ⟨dg_it_r0⟩ · ⟨dg_it_r3⟩ | the rules raise convictions (German McNemar p = ⟨dg_mcn_de⟩) |
| The same, law + BGE 131 IV 23; degrading statements | DE ⟨dg_de_r5⟩, FR ⟨dg_fr_r5⟩, IT ⟨dg_it_r5⟩; degrading 20 of 20 everywhere | mixed across framings |

*Table 3. Controls (exploratory; `reports/controls_a13.json`, `reports/controls_a22.json`). Art. 179ter: even with its
rules stated, a public debate and an outsider (whose act falls under Art. 179bis) are still convicted.*

**The correct reasoning does not carry the verdict.** Given an item's correct answer and the same answer with only its
opening verdict word flipped, the German 70B prefers the correct one on ⟨prefv_de_all⟩ of items, but on only
⟨prefv_de_priv⟩ private settings and ⟨prefv_de_nl⟩ unlisted characteristics: with the correct legal reasoning following,
it still favours "punishable" for about a third of them. In Italian it is at chance on punishable items
(⟨prefv_it_conv⟩). Against a mirror that also negates the reasoning, it picks the correct answer on ⟨pref_de_all⟩
(Table 4); in French it prefers that mirror on half the punishable items (0.53), and the 8B prefers today's list for
acts before July 2020 (0.00), as its verdicts do.

⟨table:preference⟩

*Table 4. Preference against the mirror that negates verdict and reasoning, and free text (answers that meet the
acceptance criterion, 240 German items). Columns: the deciding element.*

**Post-training and builds** (8B, 162-item battery). From RLVR to DPO (one checkpoint pair), correct acquittals under
stated rules fall from ⟨stage_rlvr⟩ to ⟨stage_dpo⟩ of 220 (110 acquittals, two framings), all convictions kept; of 648 decisions, the Q8_0 GGUF matches
bf16 on 638, the Q4_K_M on 622, an MLX 4-bit conversion on 548.

## Dataset Limitations

- **Depth over breadth.** One statute modelled exactly (three of its five paragraphs, the denial clause of Abs. 4 not
  included), with intent stated in the facts; a second statute in the same format shows the method carries over.
- **Two legal modelling choices, stated.** An Abs. 2 act is also told as a one-off statement; an online post before
  July 2020 counts as completed on publication (dropping those items moves accuracy by ⟨sens_max⟩ points at most).
- **Agent-run review**, re-runnable from its instructions; courts, mutation tests, Qwen and the parser check from outside.

## Lessons Learnt and Recommendations

- **Users:** neither the bare question nor the pasted statute gives a reliable answer; plain rules help with publicity
  but make lawful criticism of a religion look punishable. For your own case, ask a counselling service or a lawyer.
- **Developers:** "the list is closed", the in-force dates and the law as written are concrete training targets.

## Reproducibility

`make run` (Docker, CPU, no key, no model) regenerates the dataset from the YAML (sha256 per file), recomputes every
result and the A22 controls and statistics from the stored responses, checks every request hash of the released runs, re-aggregates
the judges, checks the pre-registration (`prereg-verify`: locked files, amendments, the frozen held-out code) and every
`claims.tsv` number, and exits non-zero on any mismatch. `LLM_*` variables or `make run-gguf` add a live slice.
Seeds: generator 261, bootstrap 0 (2,000 resamples). **License:** code Apache-2.0; dataset CDLA-Permissive-2.0; this
report CC-BY-4.0.

## References

[1] StGB (SR 311.0), Art. 1, 2, 30, 31, 179bis–quinquies, 261, 261bis; Fedlex, 1 Feb 2020 and 1 Oct 2026; AS 1994 2887,
AS 2020 1609. [2] BGE 130 IV 111; BGE 131 IV 23. [3] Fan et al., LEXam, ICLR 2026. [4] Han et al., LawShift, NeurIPS 2025
D&B. [5] Huang et al., TALD, arXiv 2608.14610. [6] Servantez et al., OpenExempt, ACL Findings 2026. [7] Röttger et al.,
Multilingual HateCheck, WOAH 2022.
