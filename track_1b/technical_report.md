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

⟨dataset table and figure: generated in the final pass⟩

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

⟨quality, ethics, licensing: generated in the final pass⟩

## Evaluation

### Method

A model is asked each scenario at each rung in both framings. With log-probabilities available we score **exact forced
choice**: the summed log-probability of the convict continuation minus that of the acquit continuation (lo > 0 is a
conviction). Accuracy is computed on settled items. The **read-back** pairs every true flip V with its base Ref; an
element is *in force* in a framing when the 95% bootstrap intervals of both V and Ref are above zero (the model convicts
where the law acquits) and *applied* when V is below and Ref above; a framing that does not convict the reference is
unreadable. An element is **red** when it is in force in every readable framing.

### Evaluation setup and inference parameters

⟨runs, parameters, seeds⟩

### Results

⟨results⟩

## Dataset Limitations

## Lessons Learnt and Recommendations

## Reproducibility

## License

Creative Commons Attribution 4.0 (CC-BY-4.0). All HackApertus projects are open-sourced.

## References
