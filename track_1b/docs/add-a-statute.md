# Adding a statute

A statute folder is five small YAML files. The generator, gold engine, QC gates, harness and the generic tests work on
any folder without code changes; `statutes/stgb_179ter/` (unauthorised recording of conversations) is a complete second
example with a complaint requirement and a role element.

```bash
statute-twins new stgb_<id>                     # scaffold that builds out of the box (toy content)
statute-twins pin --eli eli/cc/54/757_781_799 --eid art_<n> --lang de --date 2026-10-09   # pin the official text
python -m pytest -q tests/test_all_statutes.py  # generic invariants run on the new folder automatically
statute-twins build --statute statutes/stgb_<id> --out dataset_<id> && statute-twins verify --statute statutes/stgb_<id> --dataset dataset_<id>
```

## The five files
| file | holds | checked by |
|---|---|---|
| `statute.yaml` | elements in deciding order; each value's legal status; the pinned sources with text hashes | `test_sources.py` (hashes, statutory anchor terms, amendment dates against Fedlex footnotes) |
| `design.yaml` | slots and the legal fact each value carries; twin families (base filter + one-slot variants + expected role); acceptance criteria | the generator refuses to build if a variant changes more than one slot, if the engine's role differs from `expect`, or if a month-precision date's verdict depends on the day |
| `templates/<lang>.yaml` | surfaces for every slot value, frames, actor morphology, case forms | validator: every value has a surface, every placeholder resolves, every case form used exists |
| `prompts/<lang>.yaml` | question rungs (`rungs: {R0: [plain], R1: [rule, tail]}`) and the two answer framings | `test_all_statutes.py` |
| `answers/<lang>.yaml` | chosen / rejected reference answers per gold reason, trap-specific rejected answers | every reason the engine produces must have both |

## Element kinds
- `date`: met iff on or after `in_force_from`.
- `covered_set`: a value is covered from `covered_from` (null: never), checked against the date element it `depends_on`;
  give each value its statutory `anchor` term so the test can check it against the official text.
- `enum`: each value `satisfied: true | false | contested`. A contested value makes the verdict `open` unless another
  element fails.

## Twin families
A family draws a base scenario with filters (`tags`, `attr: null`, `attr: base`, `match`, `differ`) and builds each
variant by changing exactly one slot. The gold engine, not the author, decides whether a variant is a true flip, a
placebo or contested; `expect` is a guard against design mistakes. Value selection is balanced by least use and seeded,
so the output is byte-reproducible.

## Translating
Add `templates/fr.yaml` etc. with the same ids. Recommended procedure (used here): translate with the official
terminology of the statute in that language, blind back-translation by a second translator, comparison against the
source for legal facts (`statutes/stgb_261bis/review/bt/`), human spot check.
