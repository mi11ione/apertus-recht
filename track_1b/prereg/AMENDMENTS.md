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
