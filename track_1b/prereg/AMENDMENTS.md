# Amendments to the pre-registration lock

## A1 (2026-10-09, before any core-set result was looked at): code moved into design.yaml, output unchanged
`statutes/stgb_261bis/design.yaml` gained three declarative sections that were previously hard-coded in
`generator/build.py` and `generator/render.py`: `sample_order`, `render` and `acceptance` (text copied verbatim).
This makes the generator statute-agnostic (needed for the second worked statute). It changes no item, no gold label,
no prompt and no test logic: every file under `dataset/eval/` and every item metadata file is byte-identical before
and after (sha256 lists compared; only the design.yaml snapshot under `dataset/metadata/generator/` differs).

| file | locked sha256 | current sha256 |
|---|---|---|
| statutes/stgb_261bis/design.yaml | 1f8a076c4b5cb537c9cb20272a3fa6d1ff59863298fffda1f650de2db13b7e66 | a3891441e7d059c437efbf02bd9ce156444f29a712b798bf6c0117e3210dc281 |
| dataset/eval/core_de.jsonl | c54f6c3fdb7861b89737258be2d3a8801c824287ad7d9f727349bc491a75f267 | c54f6c3fdb7861b89737258be2d3a8801c824287ad7d9f727349bc491a75f267 |

## A2 (2026-10-09): FR/IT surface fixes from the back-translation review
As allowed by the lock note, `templates/fr.yaml` (religion base form → statutory "appartenance religieuse";
ethnicity base → "appartenance ethnique", synonym → "origine ethnique") and `templates/it.yaml` (a1A2, a4B2) changed
before any FR/IT item was scored. Findings: `statutes/stgb_261bis/review/bt/backtranslation_{fr,it}.md` (0 critical).

## A3 (2026-10-09, 20:38, before any core-set result was analysed): two wording defects found by blind annotation
Blind second annotation (`statutes/stgb_261bis/review/annotation/`) found (1) acts dated 1993/94 set on social media,
video platforms or online forums (an anachronism; verdict unaffected) and (2) the contested setting `cont_assoc`
("15 members who have known each other for years"), which 5/5 annotators read as clearly private, i.e. not genuinely
contested. Fixes: online settings are tagged `online` and excluded from the DATE_CTRL base; `cont_assoc` now reads
"about 25 members, some of whom have known each other for years and some of whom joined only recently" (DE/FR/IT).
Effect: 150 items per language change (DATE_CTRL 75, CONTESTED 45, WORDING 30; the later families are re-drawn by the
seeded sampler). The 70B core run, which had scored 385 of 3,960 DE prompts and whose results had not been looked at,
was stopped and resumed; prompts whose text changed are re-scored (cache key = request hash). The held-out test, the
red/amber rule and the gold engine are unchanged.

| file | sha256 before A3 | after A3 |
|---|---|---|
| dataset/eval/core_de.jsonl | c54f6c3fdb7861b89737258be2d3a8801c824287ad7d9f727349bc491a75f267 | 2428ca73ddadce916ba3e69578f19aeae4ae0ccf94f8a0548caf5a904bd941a6 |
| statutes/stgb_261bis/design.yaml | (A1 value) | df8a364b97438c5c742174ff08d23afd207e60cc1fa52d809dec0b7a6df9f4cc |

## A4 (2026-10-10, 00:05): verification by independent agents instead of a human reviewer
Team decision: no human labelling or adjudication. (1) Court tuples: instead of verification by reviewer R1, all 150
triaged decisions are extracted a second time by independent Claude agents that do not see the first extraction;
per-field agreement is reported, and every decision on which the two extractions disagree on a field that enters the
rule (rules_on_261bis, outcome, setting, characteristic, paragraph, act date, acquittal ground) goes to a third agent
that sees both and the excerpt. The engine-court comparison is then rerun on the reconciled tuples with the
pre-registered rule unchanged. Made after the first-pass result (30/30) had been computed; both results are reported.
(2) Gold adjudication: the queue (every annotator disagreement, every contested item, a seeded 10% sample of agreeing
settled items) is adjudicated by two independent agents, with a third agent on their disagreements.

## A5 (2026-10-10, 01:35, after the German 70B and 8B core results had been analysed): wording fixes from review
A lawyer-persona review (a Claude agent; dogfood round 1) found: frame F08 dated the *recording* of the incident ("wurde aktenkundig",
"consigné au dossier", "messo agli atti"), not the act, which makes the date-boundary items ambiguous; the contested
e-mail setting ("an die 25 Mitarbeitenden ihrer Abteilung") was incoherent for retired or student actors; two FR/IT act
phrasings were clumsy. Fixed in DE/FR/IT templates (F08: "ereignete sich" / "s'est produit" / "si è verificato";
e-mail to "rund 25 frühere und heutige Arbeitskolleginnen und -kollegen"; FR a2C2, IT a2C2/a4B2 word order). No slot,
fact or gold label changes; the item texts change for 88 DE, 123 FR and 151 IT items (880 / 1,230 / 1,510 prompts),
which are re-scored for every model. Because this amendment follows an analysis of the DE results, the pre-amendment
responses and results are kept unchanged in `archive/` and the report states both where they differ.

## A6 (2026-10-10, 01:50): item-specific reference answers, free-text framing, unparsed answers in balanced accuracy
(1) A review found the reference answers too uniform (20 distinct `chosen`, 9 `rejected` per language). `chosen` now
names the item's own setting, characteristic, paragraph and date; `rejected` and the trap answers are drawn
deterministically from two wrong answers of the kind models give (333 distinct `chosen`, 31 `rejected` per language).
Prompts, facts, gold labels and every score are unchanged (`statute-twins verify` and the request hashes of every
released run still match). (2) A third answer framing, `open` (free text, two to three sentences, no forced choice),
added as an **exploratory** measurement, not part of the pre-registered test: a fixed sample of 240 German items
(whole twin groups, the smallest sha256 hashes of the group id: `--sample 240`) at R0 and R3, generated greedily through the gateway and judged blind against each item's
acceptance criterion by two independent agents (`scripts/judge_open.py`). (3) `accuracy()` now counts an unparsed
answer in the class recall denominators as well (before, only in the accuracy denominator); no released run has an
unparsed row, so no published number changes. Hand-computed unit tests for these functions are in
`tests/test_scoring.py`.

## A7 (2026-10-10, 02:20, before any French or Italian result entered the report): FR/IT localisation from review
A French- and Italian-speaking lawyer persona (a Claude agent; dogfood round 2) found that the FR/IT scenarios read as German cases in
translation: every place was a German-speaking town (trams in Thun, communal assemblies in cities with a parliament),
the intent formula of frame F06 was a calque ("savait ce qu'elle faisait et le voulait"), two act phrasings were
calques of German (a4B2, a4C1) and one had German word order (IT a2C2), openings were stilted, and the verdict framing
"coupable / non coupable" is not Swiss usage. Fixed in `templates/{fr,it}.yaml` and `prompts/{fr,it}.yaml`:
places in Romandie and in Ticino / Italian Graubünden; bus instead of tram and a public information evening of the
commune instead of the communal assembly (same facts in all three languages: public, ~120 people); intent "avec
conscience et volonté" / "consapevolmente e volontariamente"; police-report openings; ver framing with nouns
that do not agree with the actor's gender ("Jugement : condamnation / acquittement", "Sentenza: condanna /
proscioglimento"); "a nié / ha negato la dignità umana" for a4C1; formal register in Italian. A second read by the
same reviewer caught that the FR/IT reference answers still named the old settings; fixed before scoring. No slot, fact, gold label or German prompt changes.
Every FR and IT prompt changes and both languages are re-scored in full; the responses to the A5 texts are kept in
`archive/`. Reference answers in all three languages now cite paragraphs in Swiss form ("Art. 261bis Abs. 1
StGB", "art. 261bis al. 1 CP", "art. 261bis cpv. 1 CP") and BGE 130 IV 111 E. 5.2 throughout; the `citation` field is
in the item's language (ATF/DTF, RO/RU, CP). The reviewer also questioned whether an act published online before
1 July 2020 that may still be online later is settled; we keep the view that the offence is complete on publication
and report the accuracies without those 10 items per language (`scripts/sensitivity.py`, `reports/sensitivity.json`).
(The archive moved from `dataset/archive/` to `archive/` at the repository level on 2026-10-10 so that it can never be uploaded with the dataset.)

## A8 (2026-10-10, 02:50, after judge review round 2; the pre-registered test and its verdicts are unchanged)
(1) **R5, verbatim law.** Reviewer agents pointed out that R1–R4 state the law as rules written by us (a one-sentence
paraphrase of BGE 130 IV 111, the closed list, the 2020 date) and that no rung contains the law itself. R5 adds the
pinned Fedlex texts of Art. 261bis (with Fedlex's own footnote) and Art. 2 StGB verbatim and the Regeste of BGE 130 IV
111, as a retrieval pipeline would paste them (`prompts/<lang>.yaml: law_text`, `render.law_block`). R5 is exploratory:
`heldout.py` now restricts the pre-registered test to the pre-registered rungs R0, R3, R4 (`PREREG_RUNGS`), as it already
did to the pre-registered framings (A6). (2) **Length-matched preference pairs.** The A6 pairs compared a long `chosen`
with a short `rejected` answer, so a summed log-probability measured length. Each settled item now also has
`rejected_minimal`: the chosen answer mirrored, same wording and length, with the verdict and the deciding legal claim
negated; preference prompts use it (`answers/<lang>.yaml: minimal`). The A6 preference runs were discarded unanalysed.
(3) **Legal precision from a criminal-law review:** non-retroactivity cited as Art. 1 and 2 StGB and acquittals scoped
to Art. 261bis in the reference answers; the contested items' acceptance criterion accepts a reasoned leaning under
BGE 130 IV 111 (two of the four contested settings lean public); the court validation reports the always-convict
baseline (55/58), acquittals separately (3/3) and records unlisted characteristics as such ("unlisted:foreigners")
instead of the engine stand-in. (4) **Record of earlier code changes to locked files:** `results.py` was fixed on
2026-10-09 23:43 (commit 2c1dfaa, before any core-set result was analysed: legacy pairs overwrote core edits under the
same key; keys now carry the subset) and extended in A6; `heldout.py` filters framings (A6) and rungs (A8); the frozen
`heldout.py` of the lock commit reproduces every pre-registered verdict on the current data (`statute-twins
prereg-verify`). `prereg/CHANGES.json` maps every locked file that differs from `LOCK.json` to its amendments.

## A9 (2026-10-10, 03:00): the same German scenarios in a user's voice (exploratory)
Reviewer agents noted that the scenarios read like charge sheets (the dignity threshold and intent are stated in the statute's
words), while the use case is a person asking about their own conduct. `de_lay` renders the same 660 German scenarios
(same slots, facts and gold, same twin groups) in the first person and in everyday words, with no legal conclusions:
"Im Januar 2024 habe ich in Aarau an einem Stand auf dem Wochenmarkt vor vielen Kundinnen und Kunden ein Weltbild
propagiert, nach dem Muslime minderwertig sind." The group is named without its characteristic. Exploratory: not part
of the pre-registered test (`heldout.py` runs per language; `de_lay` results are reported next to `de`).

## A10 (2026-10-10, 06:40, after judge and dogfood round 3): R6, a control for R5; the user voice at R3
A legal-reviewer agent pointed out that R5 differs from R3 in two ways: it adds the verbatim law and drops R3's instruction
to check the elements. R6 is R5 with R1's instruction ("Prüfe die Tatbestandsmerkmale … in der zur Tatzeit geltenden
Fassung") put back, scored for the German 70B with Ja/Nein. The user-voice German items (A9) are also scored at R3, so
the register comparison is not limited to R0, where the model convicts everything. Both exploratory.

## A11 (2026-10-10, 08:50, after judge round 3): German localisation, free text with the verbatim law, a second judge
Reviewer agents found German items with a tram in towns that have none (only Zürich, Bern and Basel of the twelve do) and a
communal assembly in cities with a parliament, the same defects A7 fixed in French and Italian. `templates/de.yaml`,
`de_lay.yaml` and the German answers now use a bus and a public information evening of the commune (120 people);
both stay public, no fact or gold label changes. The 115 affected German items are re-scored for every model (changed
prompts only; the pre-fix responses are in `archive/*.before-A11.jsonl`). The free-text framing gains R5 (the same
240-item sample with the verbatim law), and every free-text answer is also judged by a judge of another model family
(Qwen-SEA-LION-v4-32B via Public AI) next to the two Claude judges.

## A12 (2026-10-10, 12:40, after judge round 4): post-hoc analyses and provenance repairs (no item, prompt or gold changes)
(1) **Court validation per distinct case (post hoc).** The pre-registered count is per decision: 58 in-scope rulings,
58/58. Four of them are further instances of a case already counted (BGE 149 IV 170 / 6B_777/2022; 6B_627/2015 /
ZH Obergericht SB140436; 6B_350/2019 / two Vaud judgments), and one conviction is superseded: in Perinçek
(6B_398/2007) the ECtHR Grand Chamber (2015) found a violation of Art. 10 ECHR and the Federal Court revised its
judgment (6F_6/2016). Counted per distinct case, the engine agrees with the court in 53/53 (Wilson 0.93–1.00): 6 cases
of genocide denial (10 of the 58 rulings; Abs. 4, second half, which the engine treats with the degradation half),
47 of incitement or degradation; of the 3 acquittals, one is clean (migrants are not on the list),
one agrees on the outcome on another ground (the court acquitted on the setting; the engine's first failing element
is the unlisted characteristic, "foreigners"), and one (BGE 126 IV 176) predates BGE 130 IV 111.
`scripts/court_validation.py` writes `case_level` next to the pre-registered numbers.
(2) **Scores next to decisions (post hoc).** The colour rule stays as locked (a cell is misapplied when the variant's
interval of the conviction log-odds lies above zero). Figure 1 now also marks the cells where the paired difference
variant − reference lies below zero: the model registers the fact but its score stays on the convicting side. For the
German 70B (Ja/Nein) this holds in 32 of 37 misapplied cells; with the verbatim law (R5) the private setting lowers the
score by 6.6 nats (95% CI 5.7–7.4) from 14.7, without changing a decision.
(3) **Judge agreement per gold class.** The judge of another model family (Qwen) agrees with the Claude consensus on
470/473 answers to convict items and 224/245 to acquit or open items (κ 0.73; it passes 57 of these against the
consensus's 40). The headline counts hold by that judge alone: it calls 72 of 75 R0 answers and 70 of 75 R5 answers to
acquittal items misleading (Claude consensus: 73, 75). `reason_ok` is aggregated for answers both Claude judges pass.
The Claude judges were Claude Opus 5.5 (`claude-opus-5-5`) running as Claude Code subagents on the packets with
`instructions.md` as their prompt; only the aggregation is re-runnable as code, the judge model is run by
`statute-twins judge judge` on any endpoint.
(4) **Judgements bound to answers.** `review/open_judge/bindings.json` stores, per judgement id, the request hash of
the prompt and the sha256 of the answer judged; aggregation fails on any mismatch. One declared exception: J00420,
whose prompt A11 changed (tram → bus) while the greedy answer stayed byte-identical; the pre-A11 judgement is kept.
(5) **Provenance.** The history rewrite of 10 Oct 2026 (assistant trailers removed from commit messages) gave the lock
commit d9537fd the new id de35225 with the identical tree; tag `prereg-lock` points to it. The frozen `heldout.py` now
ships in `prereg/frozen/` (sha256 checked against `LOCK.json`, and against the lock commit where the history exists),
so `prereg-verify` runs it in Docker as well. `CHANGES.json` gains A11 for `core_de.jsonl` (the German localisation)
and records each amended file's current hash, so a later change without an amendment fails. Record of earlier changes
to the locked `results.py` not named before: count fields (10 Oct, 04:47) and the AUC (06:38), both additive; no
pre-registered quantity changed.
(6) **Corrections to earlier entries.** A7's heading says "before any French or Italian result entered the report":
French and Italian runs on the A5 texts had been computed by then (`archive/*.before-A7.jsonl`), but not reported.
A4 replaced a planned human reviewer (R1, a team member) by agents; the pre-registration had named that person.
(7) **Which law the misleading answers invoke.** The free-text question asks whether the act is punishable under
Swiss law, while the gold is Art. 261bis; an answer convicting under another offence would not be wrong. Every answer
to an acquittal item that both judges call misleading names Art. 261bis as its basis (R0 73/73, R3 39/39, R5 75/75);
8 of the R0 answers also mention another provision (Art. 173/174 defamation, Art. 261). Counted by code in the
judge aggregation (`misleading_answers_cite`).

## A13 (2026-10-10, 14:50, after judge round 4): controls for agreement bias and for R5 (exploratory, post hoc)
New prompts only (`dataset/eval/prompts_ctrl_core_*.jsonl`); no item, gold or existing prompt changes. All runs: the
70B on Public AI, exact forced choice; `scripts/controls.py` writes `reports/controls_a13.json`.
(1) **The question asked the other way** (framing `rev`: "Würde ein Schweizer Gericht die Person … freisprechen?",
"Ja" = acquit), all 660 items per language. Without the law (R0) it recognises 0 of 215 acquittals in German, French
and Italian, as with the original question; the yes-bias (half the mean score difference between the two directions)
is 1.1–3.1 nats, and the two directions disagree on 0–2 of 645 items. With the verbatim law (R5, German) also 0 of 215.
So "convicts everything" is not agreement bias. With the rules spelled out (R3) the reversed question breaks down: the
German 70B also says "Ja, freisprechen" for half the punishable cases (acquittals 53/215, convictions 220/430,
balanced accuracy 0.38; French 0.45). Averaged over both directions (bias cancels, nothing fitted), R3 recognises
73 (German) and 88 (French) of 215 acquittals, against 107 and 120 with the original question alone. A threshold
calibrated out of fold on twin groups reaches 0.68 at R0 (German, Ja/Nein): the scores carry information that the
decision at zero does not use.
(2) **Which part of R5 hurts** (German, Ja/Nein, a stable sample of 80 twin groups, `--sample 240`). On the same items
R3 recognises 39 of 81 acquittals and R5 0. R3's rules plus the verbatim law (R5a): 12/81. R5 without the Regeste's
closing example (R5b): 1/80. R5 with R1's element-check instruction after the law (R5c): 3/80. R5 plus Art. 1 StGB
(R5d): 3/81. R6 with the verdict word: 1/81. French and Italian R6 (same sample design): 19/74 and 15/78, against
R5 7/74 and 15/78 and R3 39/74 and 30/78 on the same items. No single sentence explains R5: the verbatim legal text
itself cancels most of what the plain rules achieve, and Art. 1 StGB does not restore the closed list.
(3) Three French `rev` rows hit rate-limit errors (HTTP 429) and were re-run. Italian R3 `rev` was not run (dropped to
free the gateway for the French and Italian free text; R0 already settles the agreement-bias question).

## A14 (2026-10-10, 16:30, after judge round 4): free text in French and Italian; a second statute (exploratory)
(1) **Free text in French and Italian.** The same 80 twin groups as the German sample (`statute-twins eval
--same-groups-as publicai-70b-open`), R0, R3 and R5, greedy, 220 tokens, the 70B under its `-70b` name; 720 answers
per language. Judged like German: two blind Claude judges per answer (packets of 240, one agent per packet, scratch
files kept apart after one agent reported stray lines from another agent in a shared scratch file, which it deleted
unread; its packet agrees with the other judge on 238/240), the Qwen judge through the gateway (now with parallel
requests, `JUDGE_WORKERS`), and the deterministic parser. Judge folders `review/open_judge_fr`, `open_judge_it`;
`selfcheck` re-aggregates every language. The article check of the misleading answers is now case- and
language-insensitive ("art.", "articolo"); German counts are unchanged.
(2) **Art. 179ter StGB as a second released statute** (`statutes/stgb_179ter`, `dataset/stgb_179ter`): 120 German items
in five families (conversation public, participant vs. outsider, medium, consent, complaint within three months,
Art. 30/31 StGB). Before any scoring a legal-reviewer agent checked every item: all gold verdicts correct for
"conviction under Art. 179ter"; framing and wording fixed (questions limited to Art. 179ter because an outsider falls
under Art. 179bis; "Polizeirapport" instead of an indictment without complaint; no "Täter" before a verdict; a rent
talk in the landlord's flat instead of a business call, Art. 179quinquies). Scored for the 70B at R0, R1 (elements)
and R2 (+ the complaint rule), both framings; `selfcheck` re-derives and re-scores it. Not pre-registered.

## A15 (2026-10-10, 18:40, after judge round 5): corrections, a length control, Italian R3 polarity, checks
(1) **Court validation, one outcome corrected.** BGE 126 IV 176 (both docket forms) was extracted as an acquittal;
the Kassationshof set the cantonal judgment aside on the publicity element and remanded it (cassation), so it is not
an acquittal and, under the pre-registered rule (outcome remanded), not in scope. The correction is applied from
`review/court/corrections.jsonl` (each entry with its reason; the extracted value is kept as `extracted`), not by
editing the tuples. In scope now: 57 rulings (55 convictions, 2 acquittals), engine agrees in 57/57 (always-convict
baseline 55/57); per distinct case 52/52; of the 2 acquittals, one is clean and one agrees on another ground.
(2) **R5 length control (R5e, German, Ja/Nein).** R3's rules after legal text of the same length that does not bear
on the case (Art. 139, 144, 146, 147 and 160 StGB, pinned; 2,730 characters, as the law block) instead of the law. On
the 75 acquittal items every sampled arm shares: R3 37, R5e 36, R5a (R3's rules after the verbatim law) 11, R5 0. The
law's own text, not prompt length or legal register, cancels the rules. `reports/controls_a13.json` now reports every
sampled arm on this shared item set (earlier A13 figures, 39 of 81 and 12 of 81, used R5a's items only).
(3) **Italian R3 with the reversed question** (the run A13 dropped): the 70B convicts every case (0 of 215
acquittals, 430 of 430 convictions); averaged over both directions, 78 of 215. German and French R3 break the other
way (they also "acquit" punishable cases), so at R3 the answer depends on the question's polarity in every language.
(4) **Art. 179ter, after the legal review of round 5:** acts dated September 2023 instead of May 2023 (after the
1 July 2023 harmonisation of penalty ranges, AS 2023 259; the pinned text is the version of 1 Oct 2026); Art. 179bis,
179quinquies StGB and Art. 329 StPO pinned because the answers cite them; the 16 complaint items are read in the
Ja/Nein framing only (a missing or late complaint leads to discontinuation, so «nicht schuldig» is not a correct
verdict). The 234 prompts the date change touched were re-scored (pre-change responses in
`archive/publicai-70b-179ter.before-A15.jsonl`); R2 balanced accuracy 0.76 (was 0.75).
(5) **Checks.** `selfcheck` step 2f fails when `reports/qc.json` differs from a fresh run of the gates; the judge
aggregation fails when a judge folder has no `bindings.json`; the German bindings are labelled as written after the
judgements (A12). A numeric slip in the report ("the 8B convicts 13 of 35") is corrected to 14 (Ja/Nein) and 19
(verdict word) and now claim-checked.
(6) **Wording** (legal review of round 5): "recording a non-public conversation without consent" instead of "secretly
recording"; Abs. 2 limitation sentence rewritten; reference dates of the pinned Fedlex consolidations; the register's
findings say "not yet in force" and "not covered by Art. 261bis", list gender identity in every language, and carry a
legal notice in German, French and Italian.
(7) **Gold checked by a model of another family.** `scripts/annotate_model.py` re-runs the law-only blind annotation
(same task text, the law rebuilt from the pinned sources, the same 960 items under opaque ids) with
Qwen-SEA-LION-v4-32B through the gateway: 910 of 939 settled items agree with the code gold (κ 0.93), and the deciding
element on 281 of 286 agreed acquittals. All 29 disagreements convict a case the pinned text does not cover (19 sexual
orientation before 1 July 2020, 5 acts before 1995, 3 canton, 2 gender identity), the errors Apertus makes; none
points to a gold error. Raw labels in `review/annotation/raw_model/qwen.json`, agreement in
`reports/annotation_model_qwen.json`.

## A16 (2026-10-11, after judge round 8): natural text and the user voice in every language (exploratory)
(1) **First-person retellings in French and Italian** (`fr_lay`, `it_lay`; templates, prompts and answers mirror
`de_lay`, localised from fr.yaml / it.yaml, acts described in everyday words): same slots, facts and gold as the core
items. The 70B (Ja/Nein) recognises 4 and 0 of 215 acquittals without the law and 136 and 143 with the rules
spelled out (charge sheet: 120 and 97); German first person 2 and 119. No core item or prompt changed.
(2) **Natural paraphrases** (`scripts/paraphrase.py`, `dataset/paraphrase/`): a stable sample of 40 twin groups (the
same in all three languages; settled items; families SET 10, CHAR 10, CHARX 3, DATE_SO 9, DATE_CTRL 8), 120 items per
language, rewritten by Claude writer agents in six everyday genres with the legal facts locked; each paraphrase read
blind by a Claude agent and by Qwen-SEA-LION-v4-32B, and kept only if the gold computed from what each reader
extracted equals the item's gold (verdict and deciding element) and the date, act kind, severity and intent match:
334 of 360 kept (every drop is the Qwen reader classing the act as degradation rather than incitement or ideology).
The 70B on the kept paraphrases (R0, R3, R5, both framings) behaves as on their templated originals: Ja/Nein, of 117
lawful scenarios, 3 acquitted without the law (templated 2) and 47 with the rules (templated 44).
`selfcheck` step 2g re-derives the verification and the scores. Not pre-registered.

## A17 (2026-10-11, after judge and dogfood round 9): scope note on every acquittal (no gold, prompt or result change)
A responsible-AI juror agent and an agent in the role of a counsellor of an advice centre for people affected by
racism found that "not punishable
under Art. 261bis" reads as "allowed" and that the reference answers for acquittals end at a bare "Nein", which, used
as training data, would teach an assistant to reassure. Every acquittal item now carries `scope_note` (in its
language: «not punishable under Art. 261bis» means neither «allowed» nor «not discrimination»; personality protection,
Art. 28 ZGB / CC; defamation or threat offences, Art. 173 ff., 180 StGB / CP; employment or tenancy law; the
counselling network for victims of racism) and `chosen_with_scope` (`chosen` followed by the note), the answer to train
on. `chosen`, `rejected`, `rejected_minimal`, the acceptance criteria and every prompt are unchanged, so no response,
judgement or result changes; the locked item files change by the two added fields. The register shows the note on
every acquittal, labels verdicts "under Art. 261bis", and is localised (German, French, Italian); the README opens
with the scope note.

## A18 (2026-10-11, after round 9): the dignity threshold as an element (exploratory)
Every juror agent noted that the core set stipulates the dignity threshold of Abs. 4, where most real acquittals turn. A new
element `dignity` (Abs. 4 first half; authority BGE 131 IV 23 E. 3, Regeste pinned verbatim in DE/FR/IT from bger.ch:
degrading means denying equal worth as human beings; objective criticism does not) with the values `degrading` (met),
`criticism` (failed: criticism of a religion's teachings, practices or institutions without degrading its members) and
`borderline` (contested: a crude "joke" whose wording is not established), declared with the default `degrading`, so
every existing item keeps its gold, id and prompts (all prompt files byte-identical; results unchanged; the locked
item files change only in `provenance.statute_sha256`; the engine gains generic element defaults). A family DIGNITY of
20 twin groups per language (the four religion groups; spoken public settings; 60 items per language) is written to
`dataset/dignity/`, outside the core set, and scored for the 70B at R0, R3 and R5 in both framings
(`scripts/dignity.py`, `reports/dignity.json`; selfcheck step 2h re-derives items, prompts and scores). Degrading
statements are convicted throughout; legitimate criticism is recognised without the law in French and Italian
(Ja/Nein, 18 of 20) but convicted once the rules or the verbatim law are in the prompt, in every language. A
legal-reviewer agent checked the family before release. Not pre-registered.
After the legal review (same day, before release): the borderline variant no longer says the wording "could not be
established" (an unprovable fact means acquittal, in dubio pro reo) but that the facts do not give it, and its
criterion accepts an acquittal reasoned on unproven wording; the criticism variants rotate four institution-level
criticisms (refusal of reform, opaque finances, a teaching on the role of women called outdated, no religious
instruction in public schools) instead of one sentence for all four religions; the acquittal rests on the target
("Art. 261bis protects persons, not religions"); the verbatim-law rungs of this family also paste the Regeste of BGE
131 IV 23. All changed prompts were re-scored (pre-review responses in `archive/*.before-review.jsonl`). Final
results (criticism convicted as racial discrimination, of 20, Ja/Nein, no law / rules spelled out / verbatim law):
German 11 / 20 / 18, French 3 / 8 / 8, Italian 6 / 15 / 10; degrading statements 20 of 20 throughout; the borderline
remark is convicted in most cells (a forced choice cannot hedge, and acquitting would be the defensible answer).

## A19 (2026-10-11, after judge round 10): case-specific scope notes; dignity answers restate the authority's test
A legal-reviewer agent and a responsible-AI juror agent found the A17 note too generic: it sent trans, disabled or older people to
the counselling network for victims of racism, named honour and personality claims (Art. 173 ff. StGB, Art. 28 ZGB)
without saying they need an identifiable person, addressed victims in the first-person items (told by the speaker),
and warned "not discrimination" on legitimate criticism of a religion. `scope_note` is now looked up per case
(`<reason>|<characteristic>`, `<reason>`, verdict): the racism network only for race, ethnicity and religion; the LGBTIQ
Helpline for sexual orientation and gender identity; Inclusion Handicap for disability; the Gender Equality Act and
equality offices for sex at work; no referral for canton, occupation, age or political opinion; honour and personality
claims only for an identifiable person, on complaint within three months (Art. 31 StGB); acts before 1995 and before
July 2020: other offences are time-barred today (Art. 178 StGB); criticism of a religion: protected speech (Art. 15 and
16 BV, Art. 9 and 10 ECHR), with Art. 261 StGB (public, vile mockery of religious convictions) as the limit;
first-person items: a speaker-facing note without a victim referral. The DIGNITY answers and criteria restate BGE 131
IV 23's own test (degrading means denying equal worth as human beings) instead of "Art. 261bis protects persons, not
religions", which the pinned Regeste does not say, and the joke's criterion accepts a reference to Art. 261 StGB. The
DIGNITY headline now uses R5 (the verbatim law with BGE 131 IV 23 pasted), since R3 states no dignity rule. No prompt,
response or result changed.

## A20 (2026-10-11): the dignity element against court rulings
Exploratory, not pre-registered. The court check (57 rulings) leaves out acquittals on the dignity threshold, because
the core set stipulates it. A18 models that threshold as the element `dignity`, so we ran a separate check against
real rulings: the four statement-based acquittals in the court pool whose main ground is the Abs. 4 dignity threshold (
BS AG.2017.79, NE CPEN.2021.9, a Zurich first-instance judgment, and the election-flyer count of BS AG.2024.375), mixed with the first
four public Abs. 4 convictions in sha256(decision_id) order (genocide denial and repeat dockets skipped). An agent
summarised each case as facts only, with no court, outcome, docket or legal test (`review/court/dignity_check/
packet.txt`, leak-searched). Three coders assigned the element value from the Regeste of BGE 131 IV 23 alone
(`coder_instructions.md`): two Claude agents working blind and separately (A, B) and Qwen-SEA-LION-v4-32B via the
gateway (C). The engine maps degrading to convict, not_degrading to acquit and borderline to open. Results as revised in A21
(coders re-run on the redacted packet; `scripts/dignity_court.py`, `reports/dignity_court.json`, selfcheck step 2i):
every coder codes all four convictions degrading; on the acquittals the coders are stricter than the courts (agreement
with the courts 5, 5 and 4 of 8; always-convict: 4). One acquittal (the Zurich first-instance judgment) is under
appeal; one (BS AG.2017.79) rested partly on the subjective side. No sampled ruling concerns criticism of a religion's
doctrine or institutions, so the check is consistent with the A18 gold but does not test it; the A18 gold rests on
BGE 131 IV 23 itself. No item, prompt, response or prior result changed.

## A21 (2026-10-11, after judge round 11): legal and responsible-use fixes; A20 restated; dataset 1.7.0
Juror agents (strict, responsible-AI, Swiss criminal law, ML evaluation) reviewed release 1.6.0. Changes:
- **A20 restated** as above. The case summaries named roles, a party, exact dates and small places that could
  re-identify anonymised people; they were redacted and all three coders re-run on the redacted packet, which is the
  one released.
- **Gold answers state BGE 131 IV 23 in full**: degrading means denying, *or at least calling into question*, equal
  worth as human beings or equal human rights; criticism that stays objective does not suffice (chosen answers,
  criteria, statute model). The criticism scope note cites freedom of expression (Art. 16 BV, Art. 10 ECHR) only.
- **Time bar** in the first-person note on sexual-orientation acts before July 2020: only honour offences are
  time-barred (four years, Art. 178 StGB), not "other offences" (other misdemeanours prescribe after ten or seven years, depending on the maximum penalty, Art. 97
  Abs. 1 lit. c–d StGB); the note adds the civil remedy against a post still online (Art. 28 ZGB), as do the charge-sheet notes.
- **Scope notes on every item**: convictions and open items now carry a note too (an assessment of the stated facts,
  not legal advice; a court also weighs intent and evidence), so `chosen_with_scope` exists for every item.
- **Statute model**: German title "Diskriminierung und Aufruf zu Hass" (since 1 July 2020); the quoted court texts are
  labelled as Regestes; the borderline joke's `open` label documented as a modelling choice; the policy-demand
  criticism tagged `policy_demand`. The pin step dropped paragraphs made of lettered lists; it now keeps them, and
  Art. 179quinquies StGB and Art. 329 StPO are re-pinned (neither appears in a prompt). Art. 139 StGB, the unrelated
  legal text of the R5e length control, keeps its earlier pin (Abs. 3 lit. a–d missing): it is filler of matched
  length, and re-pinning would change a scored prompt.
- **Documentation**: per-item licence and provenance records for the dignity and paraphrase splits (paraphrases name
  their Claude writer); licences for the agent and Qwen-SEA-LION outputs in `review/`; source list completed; a
  content warning replaces "no hateful text"; training guidance consistent with the canary (train on freshly
  generated scenarios, not on the evaluation items); consent template with contact, controller, retention and
  irrevocability; every reviewer, juror, counsellor or lawyer named in these amendments is a Claude agent given that
  role. The PII gate now also scans the released review records and the exploratory splits.
No prompt changed, so no response was re-collected; every result is unchanged except the A20 coding.

## A22 (2026-10-11, after judge round 12): repaired controls, statistics, dignity wording, names; dataset 1.8.0
Exploratory, post hoc. Juror agents (strict, responsible-AI, Swiss criminal law, ML evaluation) reviewed release 1.7.0.
- **Verdict-only preference mirror** (70B, DE/FR/IT, 645 settled items each, R0): `chosen` word for word with only the
  verdict word flipped, next to the released mirror that also negates the reasoning. German 0.85 overall, 35 of 55
  private settings, 64 of 100 unlisted characteristics; Italian 0.50 on punishable items (`reports/controls_a22.json`).
- **R5a ablations** (German, the A13 sample): A13's R5b–d were built on R5, which acquits nothing; rebuilt on R5a
  (the rules after the verbatim law, 11 of 75): without the Regeste's example 14, with an element check 14, with
  Art. 1 StGB 16; rules before the law 21, with all 19 private settings and fewer unlisted characteristics.
- **Statistics from stored responses** (`reports/stats_a22.json`, selfcheck step 2j): a twin-group bootstrap of the
  read-back colours changes 0 of 582 cells; Wilson intervals for the headline counts; exact McNemar R5a vs R5e on the
  same 75 items, p = 6·10⁻⁸; twin-group bootstrap intervals for every held-out gain (German 70B R3 Ja/Nein 0.148,
  0.100–0.186); reversed-question counts per element at R3 (private settings 0 of 55 in every language).
- **Dignity family, criticism variants** (after a Swiss-criminal-law agent's review): the "opaque finances" criticism
  is never paired with Judaism (an act value can now exclude group values); every criticism cites an objective basis
  (a published report, the institutions' own statements or texts, the state's confessional neutrality); the chosen
  answer states both limbs of the Regeste ("sachlich bleibt und sich auf objektive Umstände stützt"); the policy demand
  (no religious instruction in public schools) has its own answer and criterion, citing BGE 131 IV 23 E. 3.1, 3.3 and
  3.4.2 (verified against the decision text). The 360 changed prompts were re-scored on the 70B; superseded rows in
  `archive/dignity-before-a22/`. Criticism convicted (Ja/Nein, no law / law with BGE 131 IV 23): DE 6 / 15, FR 1 / 5,
  IT 2 / 8 (before: 11 / 18, 3 / 8, 6 / 10); degrading 20 of 20.
- **Dignity court check (A20)**: the coder instructions now say that Abs. 4 also covers degrading one person because
  of the protected characteristic (a mere insult falls under Art. 177 StGB); the D05 summary adds the facts the court
  relied on (post deleted, public apology, complaint withdrawn); all three coders re-run; only the values are released.
  Agreement with the courts 6, 6 and 4 of 8; the two Claude coders agree with each other on 8 of 8.
- **Scope notes**: punishable items name the route for those affected (prosecution ex officio, report to the police
  or prosecutor, the counselling network that fits the group); the pre-1995 note limits the time bar to the expression
  offences that come into question (honour offences, Art. 178 StGB).
- **Data protection**: the court-extraction notes named five people; the names are replaced. The PII gate now scans
  every released review file (JSON, JSONL, TSV). The unredacted A20 summaries were removed from the public git history.
- **Documentation**: content warning on the card and the register; training guidance (reference answers recur across
  seeds, so generator output is not training data either); consent template with a content clause and a licence
  warranty for human-written scenarios; inline agent labels in these amendments; court-check report records whether a
  ruling is final and whether the first instance convicted.
No core prompt changed; every core result is unchanged.

## A23 (2026-10-11, after judge round 13): wording, notes, pins; dataset 1.8.1
Juror agents (told it is a one-week hackathon) reviewed release 1.8.0. Changes, none to a scored prompt or result:
- **CI from a clean clone**: the A22 statistics read one response file from a git-ignored folder; they now read the
  identical released copy (`dataset/responses/publicai-70b-r5x-de.jsonl`, same sha256).
- **BGE 131 IV 23 considerations pinned**: E. 1.1, 3.1, 3.3 and 3.4.2 verbatim with sha256 in
  `statutes/sources/bge_131_IV_23.json` (fetched from bger.ch), so the pinpoints cited in the answers are pinned too.
- **Policy demand** (a4D_crit4): its chosen answer adds that it is no call to discrimination under Abs. 1 (BGE 131 IV 23
  E. 3.3); its own scope note (political demands are protected speech; the limit is Abs. 1 and 4).
- **Open items**: one scope note per reason (publicity contested: who was present and how many; dignity contested:
  the wording), instead of one note for both.
- **Wording**: court checks state their always-convict baselines; the dignity court check describes the two acquittals
  the Claude coders read as degrading exactly (one reversed first-instance conviction, and one ruling since removed, A24) and
  discloses the earlier round (5, 5 and 4 of 8); the verdict-only preference result no longer speaks of the model's own
  reasoning; the dignity result reports every rung and both framings; the pre-registered test reports the readable
  cells (21 of 22), the read-back's accuracy and share of departures explained, and the cells where the bar was out of
  reach; the twin-group bootstrap is no longer cited as a robustness result (in this design no cell has more than one
  pair per twin group); user advice no longer recommends a plain-rule prompt as reliable.
- **History**: the five names removed from the court notes in A22 were also removed from every earlier commit (git
  history rewritten; the pre-registration lock commit de35225 is unchanged), and the Hugging Face history was
  squashed to one commit; earlier dataset versions remain described in the changelog.

## A24 (2026-10-11, after judge round 14): non-final ruling removed; public history replaced; wording; dataset 1.8.2
- **Dignity court check**: the first-instance acquittal still under appeal is removed from the released
  records; the check now reads seven final rulings (four convictions, three acquittals): agreement 6, 6 and 4 of 7,
  always-convict 4.
- **Public history**: GitHub kept serving pre-rewrite commits by their id; the old repository was made private and
  renamed, and a new public repository with the rewritten history (pre-registration lock commit de35225 unchanged)
  now carries the name. Old commit ids return 404.
- **Statistics added** (`reports/stats_a22.json`, selfcheck 2j): the R4 date sentence by characteristic (German 70B,
  punishable items convicted at R3 / R4: sexual orientation 123 / 22 of 125, race, ethnicity and religion 297 / 296 of
  305); objective criticism convicted without the law vs with the rules, paired by item (exact McNemar per language and
  framing).
- **Wording**: the closed-list claim is limited to the characteristics the prompt does not name as excluded; the
  dignity claim is limited to Ja/Nein; the forced-choice coverage is stated per rung and language; the pass and the
  near-misses of the pre-registered bar are given with intervals; genocide-denial rulings are reported apart from
  incitement and degradation; canary and scope-note coverage stated per file; court records described as pseudonymised
  data on criminal proceedings; the PII gate also reads scope notes and the mirrored answers.

## A25 (2026-10-11, after judge round 15): figure encoding, wording; dataset 1.8.3
- **Figure 2** marks a cell whose interval spans zero as undetermined (grey square with a dot) instead of as applying
  the law in force; **Figure 1** no longer joins R4 to R5 (R5 replaces the rules).
- **Report**: the R5 result is stated as a threshold shift (the scores still separate the cases: AUC per rung); the
  abstract names the characteristics the rules do not fix; the pre-registered test reports how many gains have their
  interval above zero; the dignity rows are split; the dignity court check is summarised (details in the card).
- **Legal precision**: the BGE 131 IV 23 Regeste quoted in full in the statute model; the dignity answers cite E. 1.1
  and 3; the French and Italian notes on Art. 261 StGB limited to statements; the policy-demand note names its limits
  "namentlich"; the Art. 179ter complaint answer names non-opening and discontinuation (Art. 310, 319 StPO).
- **Card**: the dignity family's share of court acquittals stated (6 of 23); the court summaries described as
  pseudonymised; the content warning extended to quoted court records; the contamination scan dated; the docket of
  the removed non-final ruling dropped from these amendments.

