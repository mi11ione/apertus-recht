# Apertus-Recht

**Which racial-discrimination law does Apertus apply?** Not the one in force. Asked whether a statement is punishable
under Art. 261bis StGB, Apertus v1.5 convicts for words said only at a family dinner, for insults against a canton or a
profession, and for acts committed before the law existed. Pasting the statute and the leading case into the prompt
fixes some elements and leaves others standing.

![Synopse: the law in force next to the law Apertus applies](docs/figures/fig1_synopse.png)

*Each row changes one legal fact of a scenario the law punishes. Cells: variants the model convicts (k/n). Red: the
model applies a law that is not in force, in every readable framing. R0: no law in the prompt; R3: statute, leading
case and closed list pasted in; R4: plus the 1 July 2020 clause.*

⟨findings⟩

Hack Apertus 2026 · Track 1B (Swiss Voices, behavioural alignment) · team 444 · report [`444_Report.pdf`](444_Report.pdf)
· dataset: [`dataset/`](dataset/) (the Hugging Face release, with its card)

## Run it

```bash
make run                                 # Docker, CPU, no model, no key: ~25 s
# without Docker (Python >= 3.10):
pip install -e . && statute-twins selfcheck
```

1. **Gold re-derivation.** Regenerates all 2,142 items, gold labels and prompts from `statutes/stgb_261bis/` and compares
   every file with the released dataset by sha256.
2. **Re-scoring.** Recomputes every result (accuracy, element read-back with bootstrap intervals, build parity, stage
   trace, held-out test) from the stored model responses and compares it with `results/results.json`.
3. **Live slice** (optional). `LLM_NAME=… LLM_BASE_URL=… LLM_API_KEY=… make run` scores a stratified slice on any
   OpenAI-compatible endpoint; `make run-gguf` downloads the public Q4_K_M GGUF of Apertus v1.5 8B (5.1 GB,
   sha256-checked) and scores it on CPU. Models we published must reproduce their reference band; a new model gets its
   first numbers.

Non-zero exit on any mismatch. `make test` runs the test suite in the same image.

## Score your own model

```bash
statute-twins eval --backend openai --run-id my-model --parts core_de,core_fr,core_it --rungs R0,R3,R4
statute-twins results && statute-twins selfcheck
```
Exact forced choice on vLLM endpoints, first-token log-probabilities elsewhere, or generate-and-parse
([`docs/backends.md`](docs/backends.md)); a GGUF scores in-process on CPU (`--backend llamacpp --gguf …`).

## What is in the set

| | |
|---|---|
| Items | 660 scenarios per language (DE, FR, IT) in 220 twin groups, plus the 162-item German exploration battery |
| Twins | each variant changes exactly one fact of its base: public ↔ private setting; protected ↔ unprotected characteristic; sexual orientation before ↔ after 1 Jul 2020; before ↔ after entry into force (1995); placebos that change nothing legally (family wording of a public statement, a synonym of the characteristic, a date that does not matter) |
| Gold | `convict` / `acquit` / `open` with the deciding element, computed by `src/statute_twins/gold/engine.py` from an element model that cites Fedlex texts pinned by sha256 and BGE 130 IV 111 |
| Per item | acceptance criterion, chosen / rejected answers, settled / contested label, normative source, element-by-element derivation, licence |
| Prompts | 5 rungs (no law → statute, leading case, closed list and date clause in the prompt) × 2 framings (Ja/Nein; "Urteil: schuldig / nicht schuldig") |
| Responses | ⟨n_runs⟩ files: the 70B on Public AI (DE/FR/IT), the 8B public GGUF on CPU, bf16 training stages and weight blends, MLX 4-bit builds, Qwen3-8B ([`docs/builds.md`](docs/builds.md)) |

## How we know the gold is right

⟨checks⟩

## Use it for another statute

```bash
statute-twins new stgb_<id>          # scaffold that builds out of the box
statute-twins pin --eli eli/cc/54/757_781_799 --eid art_<n> --lang de --date 2026-10-09
statute-twins preview --statute statutes/stgb_<id>
```
Five YAML files define a statute ([`docs/add-a-statute.md`](docs/add-a-statute.md)). `statutes/stgb_179ter/`
(unauthorised recording of conversations, with a complaint deadline) is a second worked example; every generic test
and QC gate runs on any statute folder.

## Layout

`src/statute_twins/` package (generator, gold engine, QC, harness, analysis, CLI) · `statutes/` element models,
templates, pinned sources, review records · `dataset/` the released dataset · `results/` · `reports/` (QC,
contamination, court validation, adjudication) · `prereg/` · `tests/` · `docs/` · `scripts/`.

## Declarations

Built by the team with Claude Code agents (Anthropic): code, German templates, French and Italian translations, blind
back-translations, annotations, adjudications and court-tuple extractions are agent work, each step reproducible from
the instructions in this repository; no step depends on a human label. Maturity: proof of concept for the method,
release quality for the dataset and harness. Apertus 70B was queried only through Public AI; new 8B runs ran on CPU CI
runners (`.github/workflows/gguf-8b.yml`).

Licences: code Apache-2.0, report CC-BY-4.0, dataset CDLA-Permissive-2.0.
