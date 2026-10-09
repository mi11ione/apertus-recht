# Apertus-Recht

**Does Apertus apply the Swiss law in force, or a law of its own?** A minimal-twin evaluation set for the
racial-discrimination offence, Art. 261bis StGB / CP, in German, French and Italian. Every gold verdict is computed by
code from the pinned statute text and the leading case (BGE 130 IV 111 E. 5.2), and the harness checks its own outputs
from a clean checkout.

Hack Apertus 2026 · Track 1B (Swiss Voices › behavioural alignment) · team 444 ·
report: [`444_Report.pdf`](444_Report.pdf) · dataset: Hugging Face (link in the report) · challenge text:
[`docs/challenge-README.md`](docs/challenge-README.md)

## Run it

```bash
make run                 # Docker, CPU, no model, no key: ~25 s on a CI runner
```

1. **Gold re-derivation.** Regenerates all 2,142 items, their gold labels and prompts from `statutes/stgb_261bis/` and
   compares every file with the released dataset by sha256.
2. **Re-scoring.** Recomputes every result (accuracy, per-element read-back with bootstrap CIs, build parity, stage
   trace, held-out test) from the stored model responses and compares it with `results/results.json`.
3. **Live slice** (optional). `LLM_NAME=… LLM_BASE_URL=… LLM_API_KEY=… make run` scores a stratified slice on any
   OpenAI-compatible endpoint; `make run-gguf` downloads the public Q4_K_M GGUF of Apertus v1.5 8B (5.1 GB,
   sha256-checked) and scores it on CPU. A model with a published reference band must reproduce it; a new model gets its
   first numbers.

Non-zero exit on any mismatch. `make test` runs the test suite in the same image.

## What is in the set

| | |
|---|---|
| Items | 660 scenarios per language (DE, FR, IT) in 220 twin groups, plus the 162-item German exploration battery |
| Twins | each variant changes exactly one fact of its base: public ↔ private setting; protected ↔ unprotected characteristic; sexual orientation before ↔ after 1 Jul 2020; before ↔ after entry into force (1995); placebos that change nothing legally (family wording of a public statement, a synonym of the characteristic, a date that does not matter) |
| Gold | `convict` / `acquit` / `open` with the deciding element, computed by `src/statute_twins/gold/engine.py`; the element model cites Fedlex texts pinned by sha256 and BGE 130 IV 111 |
| Per item | acceptance criterion, chosen / rejected answers, settled / contested label, normative source, rationale (element-by-element derivation), licence |
| Prompts | 5 rungs (no law → statute, leading case, closed list and date clause pasted in) × 2 framings (Ja/Nein; "Urteil: schuldig / nicht schuldig") |
| Responses | 18 response files: bf16 training stages, weight blends, both public GGUFs, MLX 4-bit builds, the 70B on Public AI, Qwen3-8B (`docs/builds.md`) |

## How it was checked

- **Gold against the official text.** Tests check the closed-list terms and the amendment dates against the pinned
  Fedlex consolidations and their footnotes (DE/FR/IT), and mutation tests check that changing one rule flips exactly
  the items that rule governs.
- **Gold against blind annotators.** 960 items labelled blind (opaque ids) by Claude agents: 939/939 settled items
  agree with the code gold, deciding element 315/315.
- **Gold against courts.** 150 decisions from `voilaj/swiss-caselaw` triaged under a pre-registered rule: the engine
  agrees with the court in 30/30 in-scope rulings (Wilson 95% 0.89–1.00).
- **Translations.** FR/IT translated with the official CP terms, blind back-translation, comparison for legal facts:
  0 critical findings.
- **Contamination.** 0 of 35,241 item 13-grams occur in 1,069,365 decisions of `voilaj/swiss-caselaw` (listed in the
  Apertus v1.5 training data); a positive control finds 846 of 1,525 statute 13-grams in the same scan.
- **The harness against published numbers.** Its analysis reproduces the exploration spikes' published results
  exactly (`tests/test_reproduce_spikes.py`), and it reproduces cached live scores bit for bit.
- **Pre-registration.** The held-out read-back test and the court-validation rule were frozen (`prereg/`) before any
  result they test existed; amendments are listed with hashes in `prereg/AMENDMENTS.md`.

## Use it for another statute

```bash
statute-twins new stgb_<id>        # scaffold that builds out of the box
```
Five YAML files define a statute (`docs/add-a-statute.md`); `statutes/stgb_179ter/` (unauthorised recording of
conversations, with a complaint deadline) is a second worked example. Any OpenAI-compatible endpoint or GGUF can be
scored (`docs/backends.md`).

## Layout

`src/statute_twins/` package (generator, gold engine, QC, harness, analysis, CLI) · `statutes/` element models,
templates, pinned sources, review records · `dataset/` the released dataset (= the Hugging Face repository) ·
`results/` · `reports/` (QC, contamination, court validation) · `prereg/` · `tests/` · `docs/` · `scripts/`.

## Declarations

Built by the team with Claude Code agents (Anthropic). Agents wrote code, German templates, FR/IT translations,
blind back-translations, second annotations and court-tuple extractions; what a human checked is listed in the report.
Maturity: proof of concept for the method, feasibility-level for the dataset. Apertus was run only through Public AI
(70B) and from existing local measurements (8B); new 8B runs use the CPU runner workflow.

Licences: code Apache-2.0, report CC-BY-4.0, dataset CDLA-Permissive-2.0.
