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
responses and results are kept unchanged in `dataset/archive/` and the report states both where they differ.

## A6 (2026-10-10, 02:10): item-specific reference answers, free-text framing, unparsed answers in balanced accuracy
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
