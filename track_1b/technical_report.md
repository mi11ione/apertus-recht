# Apertus-Recht: which racial-discrimination law does Apertus apply?

A local legal-information assistant built on Apertus should apply the Swiss law in force. We release 1,980 German,
French and Italian minimal-twin scenarios under Art. 261bis StGB, each with a verdict computed by code from the pinned
statute and BGE 130 IV 111, validated against blind annotation and against 30 Swiss court rulings, plus a harness that
re-derives every label and result from a clean checkout. Apertus v1.5 convicts statements made only within the family
and, with the closed list of protected characteristics pasted into the prompt, still convicts for a person's canton;
the DPO post-training stage creates the second behaviour, and the choice of 4-bit conversion changes verdicts.

**Track:** Apertus Readiness · Track 1B (Swiss Voices, behavioural alignment)
**Event:** Online
**Team:** 444
**Demo:** `make run` (repository); dataset on Hugging Face (link in the form notes)

----

### Use of Apertus

- **Model:** Apertus v1.5 8B (stages SFT, RLVR, DPO, final; public GGUF builds) and Apertus v1.5 70B.
- **How it is used:** evaluation.
- **Where it runs:** 8B: local bf16 and GGUF runs from the exploration phase, new runs on CPU CI runners; 70B: the
  Public AI endpoint, exact forced choice (the endpoint name `apertus-v1.5-8b` serves the 70B; `docs/builds.md`).

----

## Use Case Description

People ask chat assistants whether something they said, or read, is punishable. Art. 261bis StGB (racial
discrimination, extended to sexual orientation on 1 July 2020) is a frequent subject: it is litigated in all language
regions, and its answer turns on three elements a layperson cannot check: whether the statement was **public** (BGE 130
IV 111 E. 5.2: statements among family, friends or in a setting of personal trust are private), whether the targeted
characteristic is on the **closed list** (race, ethnicity, religion, sexual orientation), and **when** the act took
place. A wrong answer misinforms the user about their own speech in either direction.

The use case is a local Apertus assistant answering in German, French or Italian, with or without the statute in its
context. Apertus-v1.5-8B was downloaded 698,641 times in the 30 days before 9 October 2026, and its training data
include `voilaj/swiss-caselaw`, which contains BGE 130 IV 111 verbatim twice and 147 decisions citing it. The question
the dataset answers is not "how often is the model right" but **which law the model applies**, element by element.

## Dataset Summary

Per language: 660 scenarios in 220 twin groups (220 base, 215 true flips, 210 placebos, 15 contested); verdicts
430 convict, 215 acquit, 15 open. Each scenario is asked at five rungs in two framings, giving 6,600 prompts per
language. The 162-item German battery from the exploration phase, on which the training-stage and build columns were
measured, is released alongside with its original texts.

| Family (groups per language) | One-fact change of the base | Tests |
|---|---|---|
| SET (55) | public → private setting; placebo: family wording of a public statement | BGE 130 IV 111 E. 5.2 |
| CHAR (60), CHARX (20) | protected → unprotected characteristic; placebo: synonym ("Hautfarbe", "Glaube") | closed list |
| DATE_SO (35) | sexual orientation 2021–25 → before 1 Jul 2020; placebo: 1 Jul / Aug 2020 | AS 2020 1609, Art. 2 |
| DATE_CTRL (25) | race, ethnicity, religion → 2018–20 (placebo) and → 1993/94 | over-application; entry into force |
| CONTESTED (15) | public → fact-dependent setting (gold `open`) | hedging |
| WORDING (10) | another wording family; another paragraph | wording invariance |

Unprotected characteristics: gender identity, sex, canton, occupation, age, disability and political opinion (8–18
items each). Paragraphs are balanced (Abs. 1/2/4: 220/218/222 in German); 18 act wordings in three wording families,
29 settings, 33 group phrases, 14 dates, 8 frames, 12 places, 8 actors. The scenarios are short (mean 44 words in
German) and deliberately templated: low lexical diversity (distinct-3 0.10) is the price of exact twins.

## Data Collection Method

**No data was collected from people.** Scenarios are generated from YAML templates by a seeded generator; the gold
verdict is computed by a 90-line engine from a machine-readable element model of the statute
(`statutes/stgb_261bis/statute.yaml`). Every element and value cites a pinned source: the Fedlex consolidations of
Art. 261bis before and since 1 July 2020 and of Art. 2 StGB (DE/FR/IT, sha256 of the text), the amendment footnotes
(AS 1994 2887, AS 2020 1609) and the Regeste of BGE 130 IV 111.

**Design choices.** (1) *Minimal twins:* a base scenario and variants that each change exactly one slot, so a changed
answer is attributable to one legal fact. The engine, not the author, labels each variant a true flip, a placebo or
contested; the generator refuses to build if that disagrees with the design. (2) *Placebos* catch surface heuristics:
family wording in a public post, a synonym for the characteristic ("Glaube" for "Religion"), an act in 2019 against a
characteristic protected since 1995. (3) *Rungs* model retrieval: R0 has no law in the prompt; R1–R4 add the elements,
the BGE rule and list, "the list is closed", and the 1 July 2020 clause. (4) *Two framings*, Ja/Nein and the verdict
word, because a framing is readable only if it convicts the protected reference. (5) *Neutral wording:* acts are
described in the statute's own vocabulary; no hateful text, no names. (6) *Contested items* (15 per language) leave the
facts BGE 130 IV 111 makes decisive genuinely mixed; their gold is `open` and their acceptance criterion asks for a
hedged answer.

**Translation.** French and Italian templates were translated by Claude agents with the official CP terms, translated
back blind by separate agents, and compared for legal facts (0 critical, 3 minor findings, fixed).

**Annotation and adjudication.** Gold is computed; annotation looks for errors in the code, the element model or the
wording. Six Claude agents labelled 960 items blind (opaque ids, no access to code or gold) following
`docs/annotation-guidelines.md`. Two defects they found (acts dated 1993/94 set online; a "contested" setting all
annotators read as private) were fixed before any result was analysed (pre-registration amendment A3). The human
reviewer R1 adjudicates every disagreement, every contested item and a blind 10% sample of settled items
(⟨adjudication result⟩).

## Dataset Details

**Quality gates** (`statute-twins qc`, all passing): schema; gold recomputed from the facts for every item; twin
invariants (one changed slot; placebos keep and flips change the verdict); 0 duplicates in the core set; language
identity; PII scan over items, responses and metadata (Swiss phone, AHV, IBAN, e-mail, address patterns and a name
gazetteer): 0 hits; canary string. The statute model is tested against the official text: every characteristic on the
closed list appears in the pinned consolidation of its date and no unlisted one does; the in-force dates equal the
dates in the Fedlex amendment footnotes in all three languages; mutation tests (remove religion from the list, move
the 2020 date by a year or a day, make private settings public) flip exactly the items the rule governs.

**Contamination.** No 13-word sequence from our items occurs in any of the 1,069,365 decisions of `voilaj/swiss-caselaw`
(all 121 data files, 3.86 billion tokens), while 846 of the 1,525 13-grams of the statute and the Regeste, scanned by
the same code, are found. The leading case is present: 147 decisions mention BGE 130 IV 111 and 754 mention
Art. 261bis.

**Ethics and licensing.** No data subjects: actors are generic, groups are described by their characteristic, acts
are described abstractly, no slurs. Items are CDLA-Permissive-2.0; every item lists its licence components (statute and
decision texts are public domain under Art. 5 URG). Reviewer consent with an AI-use clause:
`docs/consent-template.md`. A canary string marks every item as evaluation data.

## Evaluation

### Method

A model is asked each scenario at each rung in both framings. With log-probabilities available we score **exact forced
choice**: the summed log-probability of the convict continuation minus that of the acquit continuation (lo > 0 is a
conviction). Accuracy is computed on settled items. The **read-back** pairs every true flip V with its base Ref; an
element is *in force* in a framing when the 95% bootstrap intervals of both V and Ref are above zero (the model convicts
where the law acquits) and *applied* when V is below and Ref above; a framing that does not convict the reference is
unreadable. An element is **red** when it is in force in every readable framing.

### Evaluation setup and inference parameters

| Run | Model and build | Where | Scope |
|---|---|---|---|
| `publicai-70b-fc-core(-fr, -it)` | Apertus v1.5 70B, served by Public AI under the name `apertus-v1.5-8b` | vLLM, exact prefill + prompt log-probabilities, temperature 0 | 660 items × R0/R3/R4 × 2 framings per language: 11,880 decisions |
| `8b-gguf-q4_k_m-cpu-core` | Apertus v1.5 8B, the public Q4_K_M GGUF (sha256 `a037df8d…`) | llama-cpp-python 0.3.19 on 16 CPU CI runners | German core: 3,960 decisions |
| `8b-bf16-{RLVR,DPO}`, blends α 0.25/0.5/0.75 | 8B post-training checkpoints and exact bf16 weight interpolations | MLX, exploration phase | 162-item battery × R0/R3 × 2 framings |
| `8b-gguf-q8_0`, `8b-gguf-q4_k_m`, `8b-mlx4-*` | the two public GGUFs (llama.cpp, Metal) and our MLX 4-bit conversions | exploration phase | same battery |

The forced-choice continuations are `Ja`/`Nein` and, after an assistant prefix `Urteil:`, ` schuldig`/` nicht schuldig`
(FR `Oui`/`Non`, `Jugement :` ` coupable`/` non coupable`; IT `Sì`/`No`, `Sentenza:` ` colpevole`/` non colpevole`). Every
response row records the served model, the backend fingerprint and the request hash. Bootstrap intervals: 2,000
resamples over items, seed 0.

### Results

⟨results⟩

## Dataset Limitations

- **One statute, three of its five paragraphs.** Intent is fixed and the Abs. 4 dignity threshold is written to be met;
  Abs. 3 (propaganda) and Abs. 5 (refusal of a public service) are out of scope. The court validation shows where this
  bites: of the decisions that rule on Art. 261bis, the acquittals mostly turn on the dignity threshold, intent or
  freedom of expression, which no twin varies. The second worked statute (Art. 179ter) shows the format is not tied to
  this one.
- **Templated text.** Exact twins need controlled wording; the set measures legal reasoning on clean fact patterns, not
  robustness to messy user prose.
- **Translations, not native writing.** FR and IT passed blind back-translation with no critical finding, but they were
  not written by native lawyers.
- **Agent annotators share a model family with the generator's author.** Their agreement rules out reading errors, not
  a shared misconception of the law; the statute tests, the mutation tests and the court validation check the law
  itself.
- **Contested items are few** (15 per language) and open by construction.

## Lessons Learnt and Recommendations

**For Apertus users.** Do not ask Apertus about Art. 261bis without the law in context: with none, it convicts on every
variant we tried. Paste the statute and BGE 130 IV 111 and it applies the publicity rule, but it still needs the closed
list spelled out *and* applied; state dates explicitly, and expect the 1 July 2020 clause to be over-applied. Prefer
the Q8_0 GGUF or the served model to 4-bit MLX conversions, which changed verdicts in our measurements.

**For Apertus developers.** The conviction prior is created by post-training, not pre-training: at full precision the
step from RLVR to DPO turns a closed-list acquittal (canton, 0/6) into a conviction (6/6), and exact weight blends show a
smooth S-curve between the two. The leading case is in the training data, verbatim. Preference data that rewards
"condemning" answers to discrimination questions is a plausible cause worth testing; twin items like ours give a
measurable target for a fix, element by element, before and after.

**For dataset builders.** Computed gold turns a legal benchmark into software: the statute model is tested against
the official text, mutations of the law flip exactly the items they should, and a new statute is five YAML files. Blind
review by personas found wording defects that no automated gate caught (a frame that dated the recording instead of the
act); we fixed them and re-scored, and the pre-registration records when. The next iteration should add the elements
courts actually argue about (the dignity threshold, interpretation of coded speech, political debate) as contested
items written with practitioners.

## Reproducibility

`make run` (Docker, CPU, no key, no model) regenerates the dataset from the YAML and recomputes every result from the
stored responses in about 25 seconds on a CI runner; it exits non-zero on any mismatch. With `LLM_*` variables or
`make run-gguf` it also scores a stratified live slice and compares it with the published reference band. Every number
in this report maps to a results file and the command that produced it in `claims.tsv`, which CI checks on every push.
Seeds: generator 261 (Art. 179ter: 179), bootstrap seed 0 with 2,000 resamples, annotation sample seeds in the scripts.
The model responses carry the served model name, backend fingerprint and a request hash for every prompt; 70B scores
were obtained at temperature 0 through a cost-capped gateway with a content cache (total spend for this paper ⟨usd⟩).
Pre-registration: `prereg/LOCK.json`, amendments with hashes in `prereg/AMENDMENTS.md`.

## License

Creative Commons Attribution 4.0 (CC-BY-4.0). All HackApertus projects are open-sourced.

## References
