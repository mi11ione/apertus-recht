# Back-translation review: Italian (art. 261bis CP)

**Summary.** I checked all 195 units in `units.json` against the German source, using the blind back-translation (`bt_it_de.json`) and then the Italian text itself. There are **0 critical findings** and **2 minor findings**. In every unit the Italian carries the same legal facts as the German:
- **Publicity:** the same numbers (300, 40, 120, 30, 20, 25, 15), relationships, accessibility and open/closed character. The family placebos stay plainly public, private settings stay private, and contested settings keep the same mix of facts.
- **Group and characteristic:** the statutory words are used (razza, etnia, religione, orientamento sessuale). Synonym forms use a different word for the same characteristic (colore della pelle, appartenenza etnica, fede, omosessualità).
- **Act:** each act stays in its paragraph. "Sistematicamente" is kept in cpv. 2, "lesivo/lede la dignità umana" in cpv. 4, and wording families A/B/C stay distinct.
- **Date and intent:** dates are exact, including 30 giugno / 1° luglio 2020, and intent is stated in every frame.
- **Prompts and answers:** prompts keep the same rule statements, closed list, date clause and question, with clear Sì/No and colpevole/non colpevole pairs. Answers keep the same verdict and the same legal reason.

All digits match across DE/IT in every unit (checked by script). Everything else the back-translator flagged is Italian usage, not a legal difference: "fratelli" (brothers or siblings, family either way), "di Zurigo", "studente", "docenti", "L'intenzione non è contestata", and the conditional "pronuncerebbe".

Side note, not counted as a finding because the German has the same ambiguity: in `setting.cont_clubchat` ("chat di gruppo chiusa della sua società sportiva con circa 30 membri"), "con circa 30 membri" can attach to the club rather than the chat. The German source ("Chatgruppe seines Sportvereins mit rund 30 Mitgliedern") reads the same way. The French version settles it ("réunissant environ 30 membres"). Clarifying the German and the Italian would make the number of recipients unambiguous in this contested setting.

| id | severity | what differs | IT text (excerpt) | suggested fix |
|---|---|---|---|---|
| act.a4B2 | minor | German "in menschenverachtender Weise" (contempt for human beings, which is the dignity element) became "in modo disumano" ("inhumanly, cruelly"). The back-translator flagged it. The act stays cpv. 4 and "vilipeso" is strong, so the verdict is unaffected, but the explicit reference to human worth is weaker than in German and in the French version ("empreinte de mépris pour l'être humain"). | "ha vilipeso in modo disumano i musulmani a causa della loro religione" | A native reviewer should consider "ha vilipeso in modo sprezzante della persona umana" or "con disprezzo per l'essere umano". Avoid "lesivo/lede la dignità umana", which belongs to family A. |
| act.a1A2 | minor | The group is attached by a genitive ("discriminazione dei musulmani") rather than the statute's "alla discriminazione **contro**". Read as a subjective genitive, it could mean discrimination carried out *by* the group. The objective reading is the natural one, and the back-translator took it, so the verdict is unaffected. | "ha incitato alla discriminazione dei musulmani a causa della loro religione" | Follow the statute: "ha incitato alla discriminazione contro {g.def}" (or "nei confronti di {g.def}"). This removes the only use of `{g.di}` in the acts. |

**Checked and found faithful (193 units):**
- frame.F01–F08 and their .f variants (16)
- actor.m1–m4, f1–f4 (8)
- place.zh, be, bs, lu, sg, wi, bi, ch, aa, th, sh, zg (12)
- date.d1993_05 through d2025_06 (14), including d2020_06_30 and d2020_07_01
- group.*: all 33
- act.a1A1, a1B1, a1B2, a1C1, a1C2, a2A1–a2C2, a4A1, a4A2, a4B1, a4C1, a4C2 (16)
- setting.* (58): all public, family-placebo, private and contested values, each with its .f variant
- prompt.R0–R4 .conv/.ver (10)
- answer.chosen.* (6), answer.rejected.* (6), answer.traps.* (3)
- char_label.* (11)
