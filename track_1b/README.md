# Apertus-Recht

**Which racial-discrimination law does Apertus apply?** Not the one in force. Asked whether a statement is punishable
under Art. 261bis StGB, Apertus v1.5 convicts for words said only at a family dinner, for degrading statements about a canton or
a profession, and for acts committed before the law existed. Rules spelled out in the prompt fix some
elements and leave others standing; the verbatim law text, as a retrieval pipeline would paste it, changes nothing at all.

![Synopse: the law in force next to the law Apertus applies](docs/figures/fig1_synopse.png)

*Each row changes one legal fact of a scenario the law punishes. Cells: variants the model convicts (k/n). Red: the
model applies a law that is not in force, in every readable framing. R0: no law in the prompt; R3: the elements, a one-sentence
paraphrase of BGE 130 IV 111 and the closed list; R4: plus a sentence on the 1 July 2020 extension; R5: the verbatim
Fedlex text and the leading case's Regeste instead (German). Light red: in one framing; grey: not readable.*

## What we found

- **No law in the prompt: everything is punishable.** The 70B convicts every scenario we wrote, in German, French and
  Italian (balanced accuracy 0.50). Asked in free text, it calls 74 of 75 scenarios punishable
  that are not punishable under Art. 261bis. Two blind judges agree on 479 of 480 answers. Told in a person's own words instead of a
  charge sheet, the same scenarios fare no better: 2 of 215 acquittals without the law, and the same element profile with the rules
  spelled out.
- **Rules spelled out (R3): publicity is fixed, the closed list and the date are not.** Private settings
  are acquitted. A canton, a disability or a political opinion is still convicted, although the prompt lists the four
  protected characteristics. Acts from 1993/94, before the article existed, are convicted at every rung; no rung
  states the 1995 date, so that one is a gap in what the model knows.
- **The law itself does not help.** Given the verbatim Fedlex text of Art. 261bis and Art. 2 StGB and the Regeste of
  BGE 130 IV 111, as a retrieval pipeline would paste them, the 70B convicts every scenario again: 0 of
  215 acquittals recognised, exactly as with no law in the prompt. Only rules spelled out in plain sentences move it.
- **The date sentence backfires.** One sentence saying that sexual orientation is protected since 1 July 2020 makes the
  70B stop convicting punishable cases from 2021–25: with the verdict word it convicts 0 of 35 in German, 1 in French,
  5 in Italian (with Ja/Nein, Italian holds up: 29 of 35).
- **The pre-registered test fails where it matters, and we say so.** Fitted on two wording families, a read-back of
  the law the model applies beats the statute at predicting the third, but with the rules in the prompt not by the
  pre-registered 15 points in every framing (at R0 it passes trivially: the model convicts everything).
- **A lead on where it comes from.** In the 8B at full precision, the DPO step cuts correct acquittals under stated
  rules from 185 to 146 of 220 while keeping every conviction; a 4-bit MLX conversion changes 100 of 648 verdicts, the
  public Q8_0 GGUF 10.
- **It cost USD 2.00** of Public AI calls to score the 70B in three languages, and the 8B ran on free CI runners.

Hack Apertus 2026 · Track 1B (Swiss Voices, behavioural alignment) · team 444 · report [`444_Report.pdf`](444_Report.pdf)
· dataset: [`dataset/`](dataset/) (the Hugging Face release, with its card)

## Run it

```bash
make run                                 # Docker, CPU, no model, no key: ~25 s
# without Docker (Python >= 3.10):
pip install -e . && statute-twins selfcheck
```

1. **Gold re-derivation.** Regenerates all 2,802 items, gold labels and prompts from `statutes/stgb_261bis/` and compares
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
| Prompts | 6 rungs (R0 no law; R1–R4 the elements, a paraphrase of BGE 130 IV 111, the closed list, the 2020 date; R5 the verbatim Fedlex text and Regeste) × 2 framings (Ja/Nein; "Urteil: schuldig / nicht schuldig") |
| Responses | 24 files: the 70B on Public AI (DE/FR/IT), the 8B public GGUF on CPU, bf16 training stages and weight blends, MLX 4-bit builds, Qwen3-8B ([`docs/builds.md`](docs/builds.md)) |

## How we know the gold is right

- **Against the official text.** Tests check every closed-list term and both amendment dates against the pinned Fedlex
  consolidations and their footnotes in DE, FR and IT; mutation tests change one rule (drop religion, move the 2020 date
  by a day, make private settings public) and check that exactly the items it governs flip.
- **Against blind annotators.** 960 items labelled blind (opaque ids, no access to code or gold) by six agents:
  939/939 settled items agree with the code gold, deciding element 315/315. Two independent adjudicators then reviewed
  every contested item and a blind sample of settled ones: 115/115 gold correct.
- **Against Swiss courts.** 326 decisions from `voilaj/swiss-caselaw`, each coded twice by independent agents with a
  third on conflicts, under a pre-registered rule: the engine agrees with the court in 58/58 rulings on the elements it
  models (Wilson 95% 0.94–1.00). That checks the conviction side well and the acquittal side weakly: an engine that
  always convicts would score 55/58, and only 3 rulings acquit on a modelled ground (all 3 agree). The other rulings turn on
  what the model deliberately leaves out (the dignity threshold, intent, freedom of expression), which maps where the
  next iteration should go.
- **Against the training data.** 0 of 35,241 item 13-grams occur in the 1,069,365 decisions of `voilaj/swiss-caselaw`
  (in the Apertus v1.5 training data); the same scan finds 846 of 1,525 13-grams of the statute itself.
- **Against our own earlier numbers.** The analysis reproduces the published exploration results exactly, and replays
  cached live scores bit for bit (`tests/test_reproduce_spikes.py`).
- **Before seeing results.** The held-out test and the court rule were frozen by hash (`prereg/`); every later change
  is listed with its timing in `prereg/AMENDMENTS.md`.

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
