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
A lawyer-persona review (dogfood round 1) found: frame F08 dated the *recording* of the incident ("wurde aktenkundig",
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
A French- and Italian-speaking lawyer persona (dogfood round 2) found that the FR/IT scenarios read as German cases in
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
(1) **R5, verbatim law.** Reviewers pointed out that R1–R4 state the law as rules written by us (a one-sentence
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
Reviewers noted that the scenarios read like charge sheets (the dignity threshold and intent are stated in the statute's
words), while the use case is a person asking about their own conduct. `de_lay` renders the same 660 German scenarios
(same slots, facts and gold, same twin groups) in the first person and in everyday words, with no legal conclusions:
"Im Januar 2024 habe ich in Aarau an einem Stand auf dem Wochenmarkt vor vielen Kundinnen und Kunden ein Weltbild
propagiert, nach dem Muslime minderwertig sind." The group is named without its characteristic. Exploratory: not part
of the pre-registered test (`heldout.py` runs per language; `de_lay` results are reported next to `de`).

## A10 (2026-10-10, 06:40, after judge and dogfood round 3): R6, a control for R5; the user voice at R3
A legal reviewer pointed out that R5 differs from R3 in two ways: it adds the verbatim law and drops R3's instruction
to check the elements. R6 is R5 with R1's instruction ("Prüfe die Tatbestandsmerkmale … in der zur Tatzeit geltenden
Fassung") put back, scored for the German 70B with Ja/Nein. The user-voice German items (A9) are also scored at R3, so
the register comparison is not limited to R0, where the model convicts everything. Both exploratory.

## A11 (2026-10-10, 08:50, after judge round 3): German localisation, free text with the verbatim law, a second judge
Reviewers found German items with a tram in towns that have none (only Zürich, Bern and Basel of the twelve do) and a
communal assembly in cities with a parliament, the same defects A7 fixed in French and Italian. `templates/de.yaml`,
`de_lay.yaml` and the German answers now use a bus and a public information evening of the commune (120 people);
both stay public, no fact or gold label changes. The 115 affected German items are re-scored for every model (changed
prompts only; the pre-fix responses are in `archive/*.before-A11.jsonl`). The free-text framing gains R5 (the same
240-item sample with the verbatim law), and every free-text answer is also judged by a judge of another model family
(Qwen-SEA-LION-v4-32B via Public AI) next to the two Claude judges.
