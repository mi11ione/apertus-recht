# Apertus-Recht

**Which racial-discrimination law does Apertus apply?** Not the one in force. Asked whether a statement is punishable
under Art. 261bis StGB, Apertus v1.5 convicts for words said only at a family dinner, for degrading statements about a canton or
a profession, and for acts before the article entered into force (1 Jan 1995). Rules spelled out in the prompt fix
some elements and leave others standing; in German, the verbatim law text, as a retrieval pipeline would paste it,
changes no verdict. Intent and the dignity threshold are stated in the charge-sheet scenarios, so this measures how the model
applies the elements, not whether it predicts a conviction.

![Synopse: the law in force next to the law Apertus applies](docs/figures/fig1_synopse.png)

*Each row changes one legal fact of a scenario the law punishes (above the rule) or a detail that changes nothing
(below). Filled square: the model applies a law that is not in force, in both framings; half-filled: in one; open: it
applies the law in force; dash: the unchanged base is not convicted either, so the element cannot be read. R0: no law
in the prompt; R3: the rules spelled out (the elements, a one-sentence paraphrase of BGE 130 IV 111, the closed list);
R4: plus a sentence on the 1 July 2020 extension; R5: the verbatim Fedlex text and the leading case's Regeste.*

## What we found

- **No law in the prompt: everything is punishable.** The 70B convicts every scenario we wrote in German, and all but
  2 (French) and 1 (Italian) of 215 non-punishable ones (balanced accuracy 0.50). Asked in free text, it calls 73 of 75 scenarios punishable (French and Italian: 75 of 75)
  that are not punishable under Art. 261bis; every German answer names that article, and most French and Italian ones
  do (59 and 57; the rest invoke the anti-racism provision without its number). Two Claude judges agree on nearly every
  answer; a judge of another model family, on its own, counts 72 of 75. Retold as a first-person paraphrase instead of a
  charge sheet, the same scenarios fare no better: 2 of 215 acquittals without the law, and the same element profile with the rules
  spelled out.
- **Rules spelled out (R3): publicity is taken up, the closed list and the date are not.** Private settings
  are acquitted (they name family or friends, as the rule's paraphrase does). A canton, a disability or a political
  opinion is still convicted, although the prompt lists the four protected characteristics. Acts from 1993/94, before
  the article entered into force, are convicted at every rung; no rung states the 1995 date, so that one is a gap in
  what the model knows.
- **The law itself does not help.** Given the verbatim Fedlex text of Art. 261bis and Art. 2 StGB and the Regeste of
  BGE 130 IV 111, as a retrieval pipeline would paste them, the German 70B convicts every scenario again: 0 of
  215 acquittals recognised, exactly as with no law in the prompt. Its scores do register the facts (a private
  setting lowers the conviction score), but never below the threshold. In French it recognises 12 and in Italian 43, against 120 and 97 with
  the rules spelled out; in free text it calls every one of 75 non-punishable scenarios punishable. Only rules spelled out in plain sentences move it.
- **Not a yes-bias.** Asked the other way round ("Würde ein Gericht freisprechen?"), the 70B still recognises 0 of 215
  acquittals in every language. With the rules spelled out, the reversed question breaks down instead: it then
  "acquits" half the punishable cases too, so part of that gain is answer-format, not law. Pasting the verbatim law
  after the plain rules cancels most of their effect; no single sentence of it is to blame, and it is not the length:
  legal text of the same length that does not apply leaves the rules' effect intact (36 against 37 of 75; A13, A15).
- **Not the template, not the register.** Rewritten as natural text (a news brief, a witness account, a forum post),
  with every legal fact verified blind by two model families, the scenarios give the same picture: 3 of 117 lawful
  ones acquitted without the law, 47 with the rules, against 2 and 44 for the templated originals. Told in a person's
  own words, in German, French and Italian, it is the same again without the law (0 to 4 of 215), and the rules
  then work somewhat better than on the charge sheet.
- **Not only this article.** A second statute in the same five-file format, Art. 179ter StGB (recording a non-public
  conversation, with a complaint deadline), fails in another shape: without the law the 70B answers "Nein" to all 120
  cases when asked Ja/Nein and "schuldig" to 117 when asked for a verdict, so it reads no element at all; with the
  elements and the complaint rule stated, a public debate is still convicted, and so is an outsider, whose act falls
  under Art. 179bis instead.
- **The date sentence backfires.** One sentence saying that sexual orientation is protected since 1 July 2020 makes the
  70B stop convicting punishable cases from 2021–25: with the verdict word it convicts 0 of 35 in German, 1 in French,
  5 in Italian (with Ja/Nein, Italian holds up: 29 of 35).
- **The pre-registered test fails where it matters, and we say so.** Fitted on two wording families, a read-back of
  the law the model applies beats the statute at predicting the third, but with the rules in the prompt not by the
  pre-registered 15 points in every framing (at R0 it passes trivially: the model convicts everything).
- **A lead on where it comes from.** In the 8B at full precision, the DPO step cuts correct acquittals under stated
  rules from 185 to 146 of 220 while keeping every conviction; a 4-bit MLX conversion changes 100 of 648 verdicts, the
  public Q8_0 GGUF 10.

Hack Apertus 2026 · Track 1B (Swiss Voices, behavioural alignment) · team 444 · report [`444_Report.pdf`](444_Report.pdf)
· dataset: [huggingface.co/datasets/mi11ion/apertus-recht](https://huggingface.co/datasets/mi11ion/apertus-recht)
· gold register: [apertus-recht.mi11ion.io](https://apertus-recht.mi11ion.io)

## Run it

```bash
make run                                 # Docker, CPU, no model, no key: ~25 s
# without Docker (Python >= 3.10):
pip install -e ".[dev]" && statute-twins selfcheck
```

1. **Gold re-derivation.** Regenerates all 4,122 items, gold labels and prompts from `statutes/stgb_261bis/` and compares
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
| Prompts | 7 rungs (R0 no law; R1–R4 the elements, a paraphrase of BGE 130 IV 111, the closed list, the 2020 date; R5 the verbatim Fedlex text and Regeste; R6 R5 with the element check) × 2 framings (Ja/Nein; "Urteil: schuldig / nicht schuldig") |
| Responses | 37 files: the 70B on Public AI (DE/FR/IT, first-person retellings and free text in all three, the A13 controls), the 8B public GGUF on CPU (DE/FR/IT), bf16 training stages and weight blends, MLX 4-bit builds, Qwen3-8B ([`docs/builds.md`](docs/builds.md)) |

## How we know the gold is right

- **Against the official text.** Tests check every closed-list term and both amendment dates against the pinned Fedlex
  consolidations and their footnotes in DE, FR and IT; mutation tests change one rule (drop religion, move the 2020 date
  by a day, make private settings public) and check that exactly the items it governs flip.
- **Against blind annotators.** 960 items labelled blind (opaque ids, no access to code or gold) by six agents:
  939/939 settled items agree with the code gold, deciding element 315/315. A model of another
  family (Qwen), given the same law-only task, agrees on 910/939; each of its 29 disagreements convicts a case the
  pinned text does not cover (sexual orientation before 1 July 2020, acts before 1995, a canton, gender identity): the
  errors Apertus makes. Two independent adjudicators then reviewed
  every contested item and a blind sample of settled ones: 115/115 gold correct.
- **Against Swiss courts.** 326 decisions from `voilaj/swiss-caselaw`, each coded twice by independent agents with a
  third on conflicts, under a pre-registered rule: the engine agrees with the court in 57/57 rulings on the elements it
  models (Wilson 95% 0.94–1.00). Counted per distinct case, with repeat instances merged and the Perinçek conviction
  left out (revised after the ECtHR found a violation of Art. 10 ECHR), it is 52/52, 6 of them genocide denial (post
  hoc, A12, A15). That checks the conviction side well and the acquittal side weakly: an engine that always convicts would
  score 55/57, and of the 2 acquittals on a modelled ground one is clean and one agrees on another ground (a third,
  BGE 126 IV 176, was a cassation and remand, not an acquittal; corrected in A15). The other rulings turn on
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
back-translations, annotations, adjudications, court-tuple extractions and the two free-text judges (Claude Opus 5.5)
are agent work, each step reproducible from the instructions in this repository; no step depends on a human label.
The pre-registration had planned a team member as reviewer for court tuples and adjudication; amendment A4 replaced
that with independent agents, and both results are reported. Maturity: proof of concept for the method,
release quality for the dataset and harness. Apertus 70B was queried only through Public AI; new 8B runs ran on CPU CI
runners (`.github/workflows/gguf-8b.yml`).

Licences: code Apache-2.0, report CC-BY-4.0, dataset CDLA-Permissive-2.0.
