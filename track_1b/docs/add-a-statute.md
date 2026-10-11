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

## Conventions you will need (learned the hard way by our first test user)
- **Template sections are the plural of the slot name**: slot `place` → section `places:`, `date` → `dates:`. Irregular
  plurals are declared in `design.yaml`: `sections: {medium: media}`.
- **Placeholders**: `{slot}` inserts a slot's surface; `{Slot}` the same with a capital first letter; actor morphology
  keys (`{pron}`, `{poss_dat_f}`, …) come from `templates/<lang>.yaml: morphology`; a slot whose surface is a dict of
  case forms is exposed under an alias (`render: {aliases: {group: g}}` → `{g.dat}`).
- **Render order** (`render: {order: [...]}`) matters when a surface uses another slot (an act uses the group).
- **Expectations**: `expect` is `true_flip`, `placebo` or `contested`; the generator stops if the gold engine disagrees.
  A contested value is declared as `satisfied: contested` and still needs the element's `fail_reason` and
  `contested_reason`.
- **Traps** (`trap:` on a slot value or a variant) mark placebos a model is expected to fall for and select a
  trap-specific rejected answer. Keep trap values out of base scenarios with `trap: null` in the base filter, otherwise a
  base silently contains the trap wording.
- **Reference answers** are keyed by the gold reason (`setting:failed`, `characteristic:not_listed`, `convict`, …). If
  one element can fail for different reasons, refine by value: `"content:failed|allegation"` wins over
  `"content:failed"`. The same refinement works for `acceptance.reasons` in `design.yaml`.
- **Wording families**: give acts a `family` attribute and set `heldout_wording_family` to enable the held-out read-back
  test; without it every item has `split: all`.
- **Every scenario is unique across all families.** A family that asks for more groups than its slots can fill stops
  the build with "could not build N distinct groups": add surface values to the slots it samples, relax its filters or
  lower `groups`.
- **Pin before you trust it**: the `sources` QC gate fails while any source still says TODO or a statute text has no
  stored file and hash (`statute-twins pin`).
- **Check as you go**: `statute-twins preview --statute statutes/stgb_<id>` prints a few twin groups with their gold,
  derivation and reference answers; `statute-twins build` refuses to run if a pinned source no longer matches its hash;
  `statute-twins qc` runs every gate on any statute.

## Translating
Add `templates/fr.yaml` etc. with the same ids. Recommended procedure: translate with the official
terminology of the statute in that language, blind back-translation by a second translator, comparison against the
source for legal facts (`statutes/stgb_261bis/review/bt/`), and a spot check (here: a localisation review by an agent; a
human spot check where reviewers are available).
