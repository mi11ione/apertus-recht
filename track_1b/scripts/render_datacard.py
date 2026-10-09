"""Render dataset/README.md (the Hugging Face data card) from the result files, so every number in the card comes
from a file. Fails (exit 1) if any input is missing or the rendered card contains a placeholder.

    python scripts/render_datacard.py
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO_URL = "https://github.com/mi11ione/apertus-recht"
HF_URL = "https://huggingface.co/datasets/<team>/apertus-recht"


def J(p):
    return json.loads((ROOT / p).read_text(encoding="utf-8"))


def pct(x, d=1):
    return f"{100 * x:.{d}f}%"


def main() -> int:
    qc = J("reports/qc.json")
    ds = qc["describe"]
    ag = J("statutes/stgb_261bis/review/annotation/agreement.json")
    ct = J("reports/contamination.json")
    cv = J("reports/court_validation.json")
    adj = J("reports/adjudication.json")
    man = J("dataset/MANIFEST.json")
    runs = sorted(p.stem for p in (ROOT / "dataset/responses").glob("*.jsonl"))
    a = ag["all"]
    settled = {k: v for k, v in ag.items() if k.startswith("variant:") and k != "variant:contested"}
    n_settled = sum(v["n"] for v in settled.values())
    k_settled = sum(v["agree"] for v in settled.values())
    div = ds["diversity"]
    fam = ds["by_family"]
    card = f"""---
license: cdla-permissive-2.0
language: [de, fr, it]
pretty_name: "Apertus-Recht: Art. 261bis StGB minimal-twin scenarios"
size_categories: [1K<n<10K]
task_categories: [text-classification]
tags: [legal, switzerland, evaluation, behavioural-alignment, apertus, minimal-pairs]
configs:
  - config_name: core
    data_files:
      - {{split: de, path: eval/core_de.jsonl}}
      - {{split: fr, path: eval/core_fr.jsonl}}
      - {{split: it, path: eval/core_it.jsonl}}
  - config_name: battery162
    data_files: [{{split: de, path: eval/battery162.jsonl}}]
  - config_name: prompts
    data_files:
      - {{split: de, path: eval/prompts_core_de.jsonl}}
      - {{split: fr, path: eval/prompts_core_fr.jsonl}}
      - {{split: it, path: eval/prompts_core_it.jsonl}}
      - {{split: battery162, path: eval/prompts_battery162.jsonl}}
  - config_name: metadata
    data_files: [{{split: items, path: metadata/items.jsonl}}]
---

# Apertus-Recht: Art. 261bis StGB minimal-twin scenarios (DE / FR / IT)

{ds['core']} scenarios ({ds['by_lang']['fr']} per language in DE, FR and IT) about the Swiss racial-discrimination offence,
Art. 261bis StGB / CP, plus the {ds['battery162']}-item German exploration battery on which the stage and build columns
were measured. Every scenario belongs to a **twin group**: a base case and variants that each change exactly **one
legal fact** (public ↔ private setting, protected ↔ unprotected characteristic, before ↔ after the 1 July 2020
extension, before ↔ after entry into force in 1995) or one irrelevant detail (**placebos**: family wording of a public
statement, a synonym of the characteristic, a date that does not matter). The **gold verdict is computed by code** from
the pinned statute text and BGE 130 IV 111 E. 5.2, never written by hand.

## Dataset Details
- **Curated by:** the Apertus-Recht team (Hack Apertus 2026, Track 1B, Swiss Voices › Behavioural Alignment).
- **Language(s):** German, French, Italian (Swiss legal register; the official statute terms of each language).
- **License:** CDLA-Permissive-2.0 (all items; per-item licence components in `metadata/items.jsonl`).
- **Git repository:** {REPO_URL} (generator, gold engine, harness, tests; Apache-2.0).
- **Version:** 1.0.0 (generator 1.0.0, seed 261). Changelog at the end.

## Uses
### Direct Use
Evaluating whether a language model applies the Swiss law in force when a user asks a local legal-information
assistant whether a statement is punishable under Art. 261bis. The model answers each scenario at five prompt rungs
(R0: plain question; R1: elements named; R2: + publicity rule of BGE 130 IV 111 and the list; R3: + "the list is
closed"; R4: + the 1 July 2020 date clause) in two answer framings (Ja/Nein; "Urteil: schuldig / nicht schuldig"). The
twins read back **which element** a model gets wrong, not only how often.
### Out-of-Scope Use
Not legal advice and not a model of every element of the offence: intent is fixed, the Abs. 4 dignity threshold is
written to be met, Abs. 3 and 5 are not covered. Not a training set (canary string in every item). Contains no hateful
text; acts are described abstractly in the statute's vocabulary.
### Specifications
- **Use case → specification:** the question a person asks about their own or someone else's speech; the elements the
  answer turns on (publicity, characteristic, date) are exactly the slots the twins vary.
- **Languages** follow where the article is litigated: of the decisions that cite BGE 130 IV 111, most are French- and
  German-language (court-validation pool: {cv['pool']['by_language']}).
- **Prompt rungs** model the retrieval levels of an assistant (no law in context → statute and leading case pasted in).
- **Acceptance criteria, chosen / rejected answers, settled / contested labels and a normative source** are given for
  every item (Track 1B behavioural-alignment requirements).

## Dataset Structure
`eval/core_<lang>.jsonl` (one row per scenario), `eval/battery162.jsonl`, `eval/prompts_*.jsonl` (one row per scenario
× rung × framing: the exact user message, the assistant prefix and the two candidate answers), `metadata/items.jsonl`,
`metadata/sources.json`, `metadata/generator/` (the YAML the items were generated from), `responses/` (model responses,
one file per model build), `MANIFEST.json` (sha256 of every file).

Main fields: `id`, `lang`, `twin_group`, `family`, `variant` (base / true_flip / placebo / contested), `changed_slot`,
`base_id`, `slots` (template ids), `facts` (the legal facts), `text`, `gold_verdict` (convict / acquit / open),
`deciding_element`, `gold_reason`, `label` (settled / contested), `trap`, `acceptance_criterion`, `chosen`, `rejected`,
`rationale` (the element-by-element derivation), `citation`, `normative_source`, `split` (fit / heldout wording family),
`licence`, `canary`.

| family (DE count) | what changes | twin groups |
|---|---|---|
| SET | public → private setting; family-worded public placebo | {fam['SET'] // 3} |
| CHAR | protected → unprotected characteristic; synonym placebo | {fam['CHAR'] // 3} |
| CHARX | protected → two unprotected characteristics | {fam['CHARX'] // 3} |
| DATE_SO | sexual orientation 2021–25 → before 1 Jul 2020; boundary placebo (1 Jul / Aug 2020) | {fam['DATE_SO'] // 3} |
| DATE_CTRL | race/ethnicity/religion 2021–25 → 2018–20 (placebo: still protected) and → 1993/94 (before entry into force) | {fam['DATE_CTRL'] // 3} |
| CONTESTED | public → fact-dependent setting (open); family-worded placebo | {fam['CONTESTED'] // 3} |
| WORDING | other wording of the same paragraph; another paragraph | {fam['WORDING'] // 3} |

Per language: {ds['by_variant']['base']} base, {ds['by_variant']['true_flip']} true flips, {ds['by_variant']['placebo']} placebos,
{ds['by_variant']['contested']} contested. Verdicts: {ds['by_verdict']['convict']} convict, {ds['by_verdict']['acquit']} acquit,
{ds['by_verdict']['open']} open. Characteristics: {', '.join(f'{k} {v}' for k, v in sorted(ds['by_characteristic'].items(), key=lambda x: -x[1]))}.
Paragraphs: {', '.join(f'{k} {v}' for k, v in sorted(ds['by_paragraph'].items()))}. Diversity (DE): {div['de']['slot_values_used']['frame']} frames,
{div['de']['slot_values_used']['act']} act wordings in 3 wording families, {div['de']['slot_values_used']['setting']} settings,
{div['de']['slot_values_used']['group']} group phrases, {div['de']['slot_values_used']['date']} dates, {div['de']['slot_values_used']['place']} places,
{div['de']['slot_values_used']['actor']} actors; mean {div['de']['mean_words']} words; distinct-2 {div['de']['distinct_2']}, distinct-3 {div['de']['distinct_3']} (templated by design).

## Dataset Creation
### Curation Rationale
Apertus is trained on Swiss court decisions, including BGE 130 IV 111 itself, yet plain-chat answers convict for
statements made only within the family and for characteristics outside the closed list (see the technical report). A
minimal-twin set with computed gold separates *which* element of the law a model applies from how often it is right,
and makes each wrong element measurable across training stages and model builds.
### Source Data
Normative sources only (all public domain, Swiss Copyright Act Art. 5): Art. 261bis StGB in the versions before and since
1 July 2020 and Art. 2 StGB (Fedlex ELI eli/cc/54/757_781_799, DE/FR/IT, sha256-pinned, `metadata/sources.json`), the
amendment footnotes (AS 1994 2887; AS 2020 1609), and the Regeste of BGE 130 IV 111 (DE/FR/IT).
#### Data Collection
No data was collected from people. Scenarios are generated from YAML templates (`metadata/generator/`) by a seeded,
deterministic generator: `statute-twins build` reproduces every file byte for byte (checked by `make run`).
#### Source Data Producers and Data Subjects
Templates: written by the team with Claude Code agents (German), translated by Claude agents (French, Italian),
reviewed as described below. There are **no data subjects**: actors are generic ("a man", "a student"), places are
cities, groups are described by their characteristic.
#### Ownership and Consent Management
The team owns the generated text and releases it under CDLA-Permissive-2.0. No personal data and no people: there are
no data subjects, and no human annotators or reviewers took part (all labelling steps are reproducible agent runs).
Anyone who extends the set with human reviewers or human-written scenarios uses the consent and AI-use form in
`docs/consent-template.md` (pseudonymised reviewers, signed forms kept by the maintainers, withdrawal before each
release). **AI permissions:** generated with AI assistance (declared); may be used to evaluate and
to train AI systems under the licence; the canary string asks crawlers to exclude it from training corpora.
#### Data Processing and Quality Control
Automated gates (`statute-twins qc`, all passing for this release): schema; **gold recomputed** from the facts for every
item; twin invariants (each variant differs from its base in exactly one slot; placebos keep and true flips change the
verdict); duplicates ({qc['gates']['duplicates']['core_duplicates']} in the core set); language identity; **PII scan**
(Swiss phone, AHV, IBAN, e-mail, addresses, name gazetteer) over items, responses and metadata:
{qc['gates']['pii']['n_hits']} hits; canary. The generator refuses to build if a variant changes more than one slot, if the
gold engine's role differs from the design, or if a month-precision date's verdict depends on the day. Statute tests
check the closed-list terms and the amendment dates against the official Fedlex text and footnotes, and mutation tests
check that changing one rule flips exactly the items that rule governs.
- **Translation:** FR/IT by Claude agents with the official CP terms; blind back-translation into German by separate
  agents; comparison for legal facts: 0 critical, {3} minor findings, all fixed (`metadata/generator/` reflects the fixes).
- **Contamination** against `voilaj/swiss-caselaw` (listed in the Apertus v1.5 training data; revision
  {ct['revision'][:7]}; {ct['rows']:,} decisions, all {ct['files']} data files including GE, VD and BVGer): of
  {ct['item_ngrams']:,} distinct word 13-grams of our items, {ct['matching_scenario']} scenario 13-grams occur in the corpus
  ({ct['matching_statute_derived']} statute-derived). Exposure of the law itself: {ct['exposure']['docs_bge_130_IV_111']}
  decisions mention BGE 130 IV 111, {ct['exposure']['docs_261bis']} mention Art. 261bis.
#### Data Instance Licenses
Every item: CDLA-Permissive-2.0 (original text). Components cited by each item (statute, amendment, BGE) are public
domain under URG Art. 5; listed per item in `metadata/items.jsonl` (`licence_components`). Model responses in
`responses/` are outputs of Apertus (Apache-2.0 model licence) and Qwen3 (Apache-2.0), released under CDLA-Permissive-2.0.

### Annotations
#### Annotation Process
Gold labels are computed, not annotated. Annotation checks them: {a['n']} items (all {div['de']['items']} German items and
a stratified sample in FR and IT) were labelled blind (opaque ids, no access to the code or the gold) by six Claude
agents following `docs/annotation-guidelines.md` (in the repository). Agreement with the code gold on settled items:
{k_settled}/{n_settled}; deciding element on acquittals: {a['deciding_element_agree']}/{a['deciding_element_n']}; Cohen's κ
(3 classes, all items) {a['kappa']:.3f}. In the first round 7 of 21 contested items were labelled with a verdict and one
contested setting was read as clearly private by 5/5 annotators; that setting and an anachronism the annotators found
(acts in 1993/94 posted online) were fixed before any model result was analysed (pre-registration amendment A3) and the
changed items re-annotated.
**Adjudication** of every annotator disagreement, every contested item and a blind 10% sample of settled items by
{adj['summary']}.
**Court validation** of the gold engine against real decisions: {cv['summary']}.
#### Annotator Details
All annotation, adjudication and court-tuple extraction was done by Claude agents (Anthropic), declared as AI, working
blind (opaque ids, no access to code or gold). No human labels: every label in this release can be regenerated by
anyone with the same instructions (`docs/annotation-guidelines.md` and the scripts in the repository). The agents share a
model family with the generator's author, so their agreement rules out reading errors, not a shared misconception of the
law; the statute tests against the official text and the court validation check the law itself.

## Risks, Bias, and Limitations
- One statute; templated scenarios (low lexical diversity by design); intent and the dignity threshold are fixed.
- Contested items are few ({ds['by_label'].get('contested', 0)} per language) and their verdict is open by construction.
- FR/IT are translations, checked by blind back-translation and spot checks, not native-written.
- Model responses come from specific builds; the Public AI endpoint named `swiss-ai/apertus-v1.5-8b` serves the 70B
  (evidence in the repository's `docs/builds.md`); its rows are labelled 70B.
### Personally Identifiable Information
None: no names, no identifiers; PII gate result above.
### Sensitive Information
The scenarios mention protected characteristics (race, ethnicity, religion, sexual orientation, gender identity, etc.)
of **groups**, as the statute requires; no individual's characteristic is described and no hateful wording is quoted.
### Recommendations
Score with both framings and read the element table, not a single accuracy; report the build (precision, conversion)
alongside results, since 4-bit conversions changed verdicts in our measurements.

## Model responses in this release
{len(runs)} runs (`responses/<run>.jsonl` with `<run>.meta.json`): {', '.join(runs)}.

## Changelog
- 1.0.0 (2026-10): first release. Generator 1.0.0, seed 261. Files and hashes: `MANIFEST.json` ({len(man['files'])} files).

## Dataset Card Contact
Via the Git repository's issue tracker: {REPO_URL}.
"""
    bad = re.findall(r"More Information Needed|TODO|<team>|⟨", card)
    if bad:
        print("placeholder in card:", bad)
        return 1
    (ROOT / "dataset" / "README.md").write_text(card, encoding="utf-8")
    print("wrote dataset/README.md", len(card), "chars")
    return 0


if __name__ == "__main__":
    sys.exit(main())
