# Back-translation review: French (art. 261bis CP)

**Summary.** I checked all 195 units in `units.json` against the German source, using the blind back-translation (`bt_fr_de.json`) and then the French text itself. There are **0 critical findings** and **1 minor finding**. In every unit the French carries the same legal facts as the German:
- **Publicity:** the same numbers (300, 40, 120, 30, 20, 25, 15), relationships, accessibility and open/closed character. The family placebos stay plainly public, private settings stay private, and contested settings keep the same mix of facts.
- **Group and characteristic:** both are kept. Synonym forms use a different word for the same characteristic.
- **Act:** each act stays in its paragraph. "Systematic" is kept in Abs. 2, the dignity element is kept in Abs. 4, and wording families A/B/C stay distinct.
- **Date and intent:** dates are exact, including 30 June / 1 July 2020, and intent is stated in every frame.
- **Prompts and answers:** prompts keep the same rule statements, closed list, date clause and question, with clear Oui/Non and coupable/non coupable pairs. Answers keep the same verdict and the same legal reason.

All digits match across DE/FR in every unit (checked by script). Everything else the back-translator flagged is French usage, not a legal difference: "appartenance raciale/ethnique" read as statutory terms, "ses parents" disambiguated by "et ses frères et sœurs", "domicilié à" for "aus", and "consigné au dossier".

Side note, not counted as a finding: `../fr_notes.md` says the ethnicity base form is "ethnie" and the synonym is "appartenance ethnique". The units actually use base **"appartenance ethnique"** (the statutory wording) and synonym **"origine ethnique"**, which is the alternative the notes suggest. That is the better choice, but the notes should be updated to match.

| id | severity | what differs | FR text (excerpt) | suggested fix |
|---|---|---|---|---|
| group.rel_jewish, group.rel_muslim, group.rel_free, group.rel_hindu (the same surface is reused in all 127 units with group = rel_muslim) | minor | The base religion form does not use the statutory French wording. The CP says "appartenance … religieuse", and the French base forms for race and ethnicity follow the statute ("appartenance raciale", "appartenance ethnique"), but religion uses the plain noun. The synonym placebo ("foi") is still a different word, so the verdict is unaffected. The contrast between statutory word and synonym is weaker in French than in German, though, and `char_label.religion` ("appartenance religieuse") does not match the scenario wording. | "… envers les musulmans en raison de leur religion" | A native reviewer should decide whether to change the base to "en raison de leur appartenance religieuse" (keeping "foi" for `rel_*_syn`) or to keep "religion" and record the asymmetry in fr_notes.md. |

**Checked and found faithful (194 units, plus the 4 group units above, which are faithful apart from the minor nuance):**
- frame.F01–F08 and their .f variants (16)
- actor.m1–m4, f1–f4 (8)
- place.zh, be, bs, lu, sg, wi, bi, ch, aa, th, sh, zg (12)
- date.d1993_05 through d2025_06 (14), including d2020_06_30 and d2020_07_01
- group.*: all 33. Base race/ethnicity/sexual-orientation forms are statutory; race_black_syn, eth_roma_syn, rel_muslim_syn, rel_jewish_syn and so_homo_syn are true synonyms; the 12 unprotected groups are kept.
- act.a1A1–a1C2, a2A1–a2C2, a4A1–a4C2 (18). Paragraphs and families are kept. a4B2 "empreinte de mépris pour l'être humain" is at the Abs. 4 level.
- setting.* (58): all public, family-placebo, private and contested values, each with its .f variant
- prompt.R0–R4 .conv/.ver (10)
- answer.chosen.* (6), answer.rejected.* (6), answer.traps.* (3)
- char_label.* (11)
