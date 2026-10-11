# Annotation and adjudication guidelines (Art. 261bis StGB scenarios)

These guidelines are given verbatim to every annotator and to both adjudicators (all Claude agents, declared as AI in
the report and the data card; amendment A4 records why agents replaced the planned human reviewer). The gold labels of the dataset are **not** annotated: they are computed by code from the pinned statute
(`statutes/stgb_261bis/statute.yaml`). Annotation exists to find errors in that code, in the element model or in the
scenario wording.

## Task
For each scenario, decide what a Swiss criminal court would conclude **under Art. 261bis StGB only**, assuming the facts
stated are proven and nothing else is known:

| label | use when |
|---|---|
| `convict` | every element of the offence is met |
| `acquit` | at least one element is clearly not met |
| `open` | no element clearly fails, but whether one is met depends on facts the scenario leaves out |

Also give the **deciding element** for `acquit` / `open`: `setting` (publicity), `characteristic` (protected
characteristic, including the date it became protected), `act_date` (before the article entered into force), `act`
(the conduct described is not one of the offences), or `other` (explain). For `convict` the deciding element is `none`.

## Law to apply (pinned sources in `statutes/sources/`)
1. **Conduct** (Abs. 1, 2, 4): publicly calling for hatred or discrimination; publicly spreading an ideology aimed at
   systematically denigrating or defaming; publicly degrading or discriminating in a manner that violates human
   dignity. In the core set the conduct is written to meet the threshold; flag it (`act`, `other`) only if the wording
   clearly does not describe one of these. The dignity family (A18) varies the threshold itself; its gold follows the
   element `dignity` in `statute.yaml` and BGE 131 IV 23 E. 3: `degrading` (the members are denied equal worth as human
   beings: convict), `criticism` (unfavourable criticism of a religion's teachings or institutions that stays objective:
   acquit), `borderline` (the facts leave the decisive wording open: either answer, reasoned, is acceptable). The same
   three values coded blind on real rulings are checked against the courts in A20 (`reports/dignity_court.json`).
2. **Protected characteristic** (closed list): race, ethnicity, religion; **sexual orientation only for acts on or
   after 1 July 2020** (AS 2020 1609; Art. 2 StGB: no retroactive punishment). Nothing else is protected: not gender
   identity, sex, canton, occupation, age, disability or political opinion. A different word for a listed
   characteristic (skin colour for race, faith for religion) is still that characteristic.
3. **Temporal scope**: Art. 261bis entered into force on 1 January 1995. Earlier acts are not punishable.
4. **Publicity** (BGE 130 IV 111 E. 5.2): a statement is public unless it is made in a private setting, i.e. among
   family or friends or in a setting shaped by personal relationships or particular trust. Whether a setting is private
   depends on the concrete circumstances, including the number of people. A closed event with invited strangers is
   public (the precedent's own facts: 40–50 invited participants). Family wording (a post addressed "Dear family", a
   rally attended with one's children) does not make a public statement private.
5. **Intent** is always stated; do not use it as a reason.

## Rules
- Decide from the text and the law above only. Do not guess what the dataset "wants"; there is no hidden key.
- Use `open` sparingly: only when the facts that BGE 130 IV 111 makes decisive (relationships, number of people) are
  genuinely mixed or missing. Do not use it for an item you find hard but that the rules decide.
- If the wording itself is defective (ambiguous, ungrammatical in a way that changes the meaning, wrong language),
  label it anyway and add a note starting `WORDING:`.
- One line per item; a reason of at most 25 words.

## Adjudication
Two independent adjudicators (agents, working blind and separately) see every item where an annotator disagrees with the code gold, every `open`/contested item and a blind
random 10% sample of the remaining settled items, without being told which group an item comes from. For each, each
adjudicator decides against the sources: **gold correct**, **gold wrong** (then the cause: element model, slot
encoding, wording, or translation) or **genuinely contested**. The headline gold-error rate is the share of adjudicated
items with "gold wrong", with a Wilson 95% interval, reported separately for the blind sample and the disagreement set.
