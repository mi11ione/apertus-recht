# 8b-gguf-q4_k_m-cpu-core: evaluation report (stgb_261bis)

## Run

- backend: `{"backend": "llamacpp", "model": "Colby/apertus-v1.5-8b-text-Q4_K_M-GGUF (CPU, llama-cpp-python 0.3.19)", "sha256": "a037df8d87ff6caacee794ee85f55342f2152e0d359b7389033300c3bee5f299", "llama_cpp_python": "0.3.19", "threads": 2}`
- prompts: 3960 (3960 decided, 0 unparsed, 0 errors)
- served models: Colby/apertus-v1.5-8b-text-Q4_K_M-GGUF (CPU, llama-cpp-python 0.3.19) (3960)

## Accuracy against the statute (settled items)

| subset | lang | rung | framing | n | accuracy | 95% interval | convict recall | acquit recall |
|---|---|---|---|---|---|---|---|---|
| core | de | R0 | conv | 645 | 0.665 | 0.628–0.700 | 0.97 | 0.07 |
| core | de | R0 | ver | 645 | 0.668 | 0.631–0.703 | 1.00 | 0.00 |
| core | de | R3 | conv | 645 | 0.850 | 0.820–0.875 | 0.99 | 0.57 |
| core | de | R3 | ver | 645 | 0.805 | 0.772–0.833 | 0.97 | 0.47 |
| core | de | R4 | conv | 645 | 0.750 | 0.716–0.782 | 0.67 | 0.91 |
| core | de | R4 | ver | 645 | 0.788 | 0.754–0.817 | 0.81 | 0.74 |

Rungs: R0 no law in the prompt; R1 elements named; R2 + publicity rule and list; R3 + closed list; R4 + 1 July 2020 clause. A model that always says 'convict' scores about 0.67.

## Which law does the model apply? (element read-back)

Each row changes one legal fact of a scenario the statute punishes. **red**: the model convicts where the statute acquits in every readable framing; **amber**: in one framing; **none**: it follows the statute; **unreadable**: the base cases of these pairs are not convicted either, so the change cannot be read; **too few pairs**: fewer than 5 pairs in this run (use a larger `--sample`). n = pairs.

| one fact changed | lang | rung | n | colour | Ja/Nein | verdict word |
|---|---|---|---|---|---|---|
| act before Art. 261bis entered into force (1995) | de | R0 | 25 | **red** | F | F |
| act before Art. 261bis entered into force (1995) | de | R3 | 25 | **red** | F | F |
| act before Art. 261bis entered into force (1995) | de | R4 | 25 | **amber** | ? | F |
| group defined by age | de | R0 | 17 | **red** | F | F |
| group defined by age | de | R3 | 17 | **none** | a | a |
| group defined by age | de | R4 | 17 | **none** | a | a |
| group defined by canton | de | R0 | 16 | **red** | F | F |
| group defined by canton | de | R3 | 16 | **none** | ? | ? |
| group defined by canton | de | R4 | 16 | **none** | a | ? |
| group defined by disability | de | R0 | 9 | **red** | F | F |
| group defined by disability | de | R3 | 9 | **none** | a | ? |
| group defined by disability | de | R4 | 9 | **none** | a | a |
| group defined by gender identity | de | R0 | 16 | **red** | F | F |
| group defined by gender identity | de | R3 | 16 | **none** | a | a |
| group defined by gender identity | de | R4 | 16 | **none** | a | a |
| group defined by occupation | de | R0 | 16 | **red** | F | F |
| group defined by occupation | de | R3 | 16 | **none** | a | ? |
| group defined by occupation | de | R4 | 16 | **none** | a | ? |
| group defined by political opinion | de | R0 | 8 | **red** | F | F |
| group defined by political opinion | de | R3 | 8 | **none** | ? | ? |
| group defined by political opinion | de | R4 | 8 | **none** | ? | ? |
| group defined by sex | de | R0 | 18 | **red** | F | F |
| group defined by sex | de | R3 | 18 | **none** | a | a |
| group defined by sex | de | R4 | 18 | **none** | u | a |
| sexual orientation, act before 1 Jul 2020 | de | R0 | 35 | **red** | F | F |
| sexual orientation, act before 1 Jul 2020 | de | R3 | 35 | **red** | F | F |
| sexual orientation, act before 1 Jul 2020 | de | R4 | 35 | **unreadable** | u | u |
| statement only in a private setting | de | R0 | 55 | **red** | F | F |
| statement only in a private setting | de | R3 | 55 | **none** | a | a |
| statement only in a private setting | de | R4 | 55 | **none** | a | a |

## Wrong decisions (951 on settled items; first 40 shown)

**261bis-de-CHAR001-1** · R0 · conv · model: **convict** · statute: **acquit** (characteristic:not_listed)

> Sachverhalt: Im Juni 2025 ereignete sich in Luzern ein Vorfall, an dem eine Rentnerin beteiligt war: An einer bewilligten Kundgebung auf einem öffentlichen Platz vor rund 300 Personen bezeichnete sie trans Personen wegen ihrer Geschlechtsidentität als Menschen zweiter Klasse. Dass sie vorsätzlich handelte, ist erstellt.

- derivation: act_date=2025-06-15: met (in force from 1995-01-01); characteristic=gender_identity: failed (not on the closed list); paragraph=abs4: met; setting=public: met -> acquit (characteristic:not_listed)
- sources: Art. 261bis StGB (SR 311.0; Fedlex eli/cc/54/757_781_799, version 2026-10-01); Pa.Iv. 13.407 (legislative history)
- acceptable answer: Nein. Die Geschlechtsidentität gehört nicht zur abschliessenden Liste von Art. 261bis StGB; mit der Revision von 2020 wurde nur die sexuelle Orientierung aufgenommen.

**261bis-de-CHAR001-1** · R0 · ver · model: **convict** · statute: **acquit** (characteristic:not_listed)

> Sachverhalt: Im Juni 2025 ereignete sich in Luzern ein Vorfall, an dem eine Rentnerin beteiligt war: An einer bewilligten Kundgebung auf einem öffentlichen Platz vor rund 300 Personen bezeichnete sie trans Personen wegen ihrer Geschlechtsidentität als Menschen zweiter Klasse. Dass sie vorsätzlich handelte, ist erstellt.

- derivation: act_date=2025-06-15: met (in force from 1995-01-01); characteristic=gender_identity: failed (not on the closed list); paragraph=abs4: met; setting=public: met -> acquit (characteristic:not_listed)
- sources: Art. 261bis StGB (SR 311.0; Fedlex eli/cc/54/757_781_799, version 2026-10-01); Pa.Iv. 13.407 (legislative history)
- acceptable answer: Nein. Die Geschlechtsidentität gehört nicht zur abschliessenden Liste von Art. 261bis StGB; mit der Revision von 2020 wurde nur die sexuelle Orientierung aufgenommen.

**261bis-de-CHAR002-1** · R0 · conv · model: **convict** · statute: **acquit** (characteristic:not_listed)

> Sachverhalt: Ein Mann lebt in Chur. Im September 2021 geschah Folgendes: In einem Video, das er auf einer frei zugänglichen Videoplattform veröffentlichte, stellte er Mitglieder einer politischen Partei wegen ihrer politischen Überzeugung als Menschen minderen Werts dar. Er wusste, was er tat, und wollte es so.

- derivation: act_date=2021-09-15: met (in force from 1995-01-01); characteristic=political_opinion: failed (not on the closed list); paragraph=abs4: met; setting=public: met -> acquit (characteristic:not_listed)
- sources: Art. 261bis StGB (SR 311.0; Fedlex eli/cc/54/757_781_799, version 2026-10-01)
- acceptable answer: Nein. Das Merkmal «politische Überzeugung» gehört nicht zur abschliessenden Liste von Art. 261bis StGB (Rasse, Ethnie, Religion, sexuelle Orientierung); die Äusserung ist nach dieser Bestimmung nicht strafbar, auch wenn sie öffentlich erfolgte.

**261bis-de-CHAR002-1** · R0 · ver · model: **convict** · statute: **acquit** (characteristic:not_listed)

> Sachverhalt: Ein Mann lebt in Chur. Im September 2021 geschah Folgendes: In einem Video, das er auf einer frei zugänglichen Videoplattform veröffentlichte, stellte er Mitglieder einer politischen Partei wegen ihrer politischen Überzeugung als Menschen minderen Werts dar. Er wusste, was er tat, und wollte es so.

- derivation: act_date=2021-09-15: met (in force from 1995-01-01); characteristic=political_opinion: failed (not on the closed list); paragraph=abs4: met; setting=public: met -> acquit (characteristic:not_listed)
- sources: Art. 261bis StGB (SR 311.0; Fedlex eli/cc/54/757_781_799, version 2026-10-01)
- acceptable answer: Nein. Das Merkmal «politische Überzeugung» gehört nicht zur abschliessenden Liste von Art. 261bis StGB (Rasse, Ethnie, Religion, sexuelle Orientierung); die Äusserung ist nach dieser Bestimmung nicht strafbar, auch wenn sie öffentlich erfolgte.

**261bis-de-CHAR002-1** · R3 · conv · model: **convict** · statute: **acquit** (characteristic:not_listed)

> Sachverhalt: Ein Mann lebt in Chur. Im September 2021 geschah Folgendes: In einem Video, das er auf einer frei zugänglichen Videoplattform veröffentlichte, stellte er Mitglieder einer politischen Partei wegen ihrer politischen Überzeugung als Menschen minderen Werts dar. Er wusste, was er tat, und wollte es so.

- derivation: act_date=2021-09-15: met (in force from 1995-01-01); characteristic=political_opinion: failed (not on the closed list); paragraph=abs4: met; setting=public: met -> acquit (characteristic:not_listed)
- sources: Art. 261bis StGB (SR 311.0; Fedlex eli/cc/54/757_781_799, version 2026-10-01)
- acceptable answer: Nein. Das Merkmal «politische Überzeugung» gehört nicht zur abschliessenden Liste von Art. 261bis StGB (Rasse, Ethnie, Religion, sexuelle Orientierung); die Äusserung ist nach dieser Bestimmung nicht strafbar, auch wenn sie öffentlich erfolgte.

**261bis-de-CHAR002-1** · R3 · ver · model: **convict** · statute: **acquit** (characteristic:not_listed)

> Sachverhalt: Ein Mann lebt in Chur. Im September 2021 geschah Folgendes: In einem Video, das er auf einer frei zugänglichen Videoplattform veröffentlichte, stellte er Mitglieder einer politischen Partei wegen ihrer politischen Überzeugung als Menschen minderen Werts dar. Er wusste, was er tat, und wollte es so.

- derivation: act_date=2021-09-15: met (in force from 1995-01-01); characteristic=political_opinion: failed (not on the closed list); paragraph=abs4: met; setting=public: met -> acquit (characteristic:not_listed)
- sources: Art. 261bis StGB (SR 311.0; Fedlex eli/cc/54/757_781_799, version 2026-10-01)
- acceptable answer: Nein. Das Merkmal «politische Überzeugung» gehört nicht zur abschliessenden Liste von Art. 261bis StGB (Rasse, Ethnie, Religion, sexuelle Orientierung); die Äusserung ist nach dieser Bestimmung nicht strafbar, auch wenn sie öffentlich erfolgte.

**261bis-de-CHAR002-1** · R4 · conv · model: **convict** · statute: **acquit** (characteristic:not_listed)

> Sachverhalt: Ein Mann lebt in Chur. Im September 2021 geschah Folgendes: In einem Video, das er auf einer frei zugänglichen Videoplattform veröffentlichte, stellte er Mitglieder einer politischen Partei wegen ihrer politischen Überzeugung als Menschen minderen Werts dar. Er wusste, was er tat, und wollte es so.

- derivation: act_date=2021-09-15: met (in force from 1995-01-01); characteristic=political_opinion: failed (not on the closed list); paragraph=abs4: met; setting=public: met -> acquit (characteristic:not_listed)
- sources: Art. 261bis StGB (SR 311.0; Fedlex eli/cc/54/757_781_799, version 2026-10-01)
- acceptable answer: Nein. Das Merkmal «politische Überzeugung» gehört nicht zur abschliessenden Liste von Art. 261bis StGB (Rasse, Ethnie, Religion, sexuelle Orientierung); die Äusserung ist nach dieser Bestimmung nicht strafbar, auch wenn sie öffentlich erfolgte.

**261bis-de-CHAR002-1** · R4 · ver · model: **convict** · statute: **acquit** (characteristic:not_listed)

> Sachverhalt: Ein Mann lebt in Chur. Im September 2021 geschah Folgendes: In einem Video, das er auf einer frei zugänglichen Videoplattform veröffentlichte, stellte er Mitglieder einer politischen Partei wegen ihrer politischen Überzeugung als Menschen minderen Werts dar. Er wusste, was er tat, und wollte es so.

- derivation: act_date=2021-09-15: met (in force from 1995-01-01); characteristic=political_opinion: failed (not on the closed list); paragraph=abs4: met; setting=public: met -> acquit (characteristic:not_listed)
- sources: Art. 261bis StGB (SR 311.0; Fedlex eli/cc/54/757_781_799, version 2026-10-01)
- acceptable answer: Nein. Das Merkmal «politische Überzeugung» gehört nicht zur abschliessenden Liste von Art. 261bis StGB (Rasse, Ethnie, Religion, sexuelle Orientierung); die Äusserung ist nach dieser Bestimmung nicht strafbar, auch wenn sie öffentlich erfolgte.

**261bis-de-CHAR003-0** · R4 · conv · model: **acquit** · statute: **convict** (convict)

> Sachverhalt: Im Mai 2022 äusserte sich eine Studentin in Biel/Bienne wie folgt: An einer Versammlung in einer Waldhütte vor rund 40 Teilnehmenden, die über einen allgemeinen Aufruf eingeladen worden waren und die sie zum grössten Teil nicht persönlich kannte, würdigte sie Angehörige der Roma wegen ihrer Ethnie in einer Weise herab, die gegen die Menschenwürde verstösst. Sie handelte vorsätzlich.

- derivation: act_date=2022-05-15: met (in force from 1995-01-01); characteristic=ethnicity: met (covered from 1995-01-01); paragraph=abs4: met; setting=public: met -> convict (convict)
- sources: Art. 2 StGB (Fedlex eli/cc/54/757_781_799, version 2026-10-01); AS 1994 2887 (in force 1 Jan 1995); Art. 261bis StGB, version before 1 Jul 2020 (Fedlex eli/cc/54/757_781_799, version 2020-02-01); Art. 261bis StGB (SR 311.0; Fedlex eli/cc/54/757_781_799, version 2026-10-01); BGE 130 IV 111 E. 5.2
- acceptable answer: Ja. Die Äusserung erfolgte öffentlich im Sinne von BGE 130 IV 111 E. 5.2 (eine Versammlung von rund 40 über einen allgemeinen Aufruf eingeladenen, grösstenteils unbekannten Personen); sie richtet sich gegen eine Gruppe wegen eines geschützten Merkmals (Ethnie) und erfüllt den Tatbestand von Art. 261bis Abs. 4 StGB (Herabsetzung in einer gegen die Menschenwürde verstossenden Weise). Die Tat im Mai 2022 fällt in den zeitlichen Geltungsbereich.

**261bis-de-CHAR003-1** · R0 · conv · model: **convict** · statute: **acquit** (characteristic:not_listed)

> Sachverhalt: Im Mai 2022 äusserte sich eine Studentin in Biel/Bienne wie folgt: An einer Versammlung in einer Waldhütte vor rund 40 Teilnehmenden, die über einen allgemeinen Aufruf eingeladen worden waren und die sie zum grössten Teil nicht persönlich kannte, würdigte sie Männer wegen ihres Geschlechts in einer Weise herab, die gegen die Menschenwürde verstösst. Sie handelte vorsätzlich.

- derivation: act_date=2022-05-15: met (in force from 1995-01-01); characteristic=sex: failed (not on the closed list); paragraph=abs4: met; setting=public: met -> acquit (characteristic:not_listed)
- sources: Art. 261bis StGB (SR 311.0; Fedlex eli/cc/54/757_781_799, version 2026-10-01)
- acceptable answer: Nein. Das Merkmal «Geschlecht» gehört nicht zur abschliessenden Liste von Art. 261bis StGB (Rasse, Ethnie, Religion, sexuelle Orientierung); die Äusserung ist nach dieser Bestimmung nicht strafbar, auch wenn sie öffentlich erfolgte.

**261bis-de-CHAR003-1** · R0 · ver · model: **convict** · statute: **acquit** (characteristic:not_listed)

> Sachverhalt: Im Mai 2022 äusserte sich eine Studentin in Biel/Bienne wie folgt: An einer Versammlung in einer Waldhütte vor rund 40 Teilnehmenden, die über einen allgemeinen Aufruf eingeladen worden waren und die sie zum grössten Teil nicht persönlich kannte, würdigte sie Männer wegen ihres Geschlechts in einer Weise herab, die gegen die Menschenwürde verstösst. Sie handelte vorsätzlich.

- derivation: act_date=2022-05-15: met (in force from 1995-01-01); characteristic=sex: failed (not on the closed list); paragraph=abs4: met; setting=public: met -> acquit (characteristic:not_listed)
- sources: Art. 261bis StGB (SR 311.0; Fedlex eli/cc/54/757_781_799, version 2026-10-01)
- acceptable answer: Nein. Das Merkmal «Geschlecht» gehört nicht zur abschliessenden Liste von Art. 261bis StGB (Rasse, Ethnie, Religion, sexuelle Orientierung); die Äusserung ist nach dieser Bestimmung nicht strafbar, auch wenn sie öffentlich erfolgte.

**261bis-de-CHAR003-2** · R4 · conv · model: **acquit** · statute: **convict** (convict)

> Sachverhalt: Im Mai 2022 äusserte sich eine Studentin in Biel/Bienne wie folgt: An einer Versammlung in einer Waldhütte vor rund 40 Teilnehmenden, die über einen allgemeinen Aufruf eingeladen worden waren und die sie zum grössten Teil nicht persönlich kannte, würdigte sie Angehörige der Roma wegen ihrer ethnischen Zugehörigkeit in einer Weise herab, die gegen die Menschenwürde verstösst. Sie handelte vorsätzlich.

- derivation: act_date=2022-05-15: met (in force from 1995-01-01); characteristic=ethnicity: met (covered from 1995-01-01); paragraph=abs4: met; setting=public: met -> convict (convict)
- sources: Art. 2 StGB (Fedlex eli/cc/54/757_781_799, version 2026-10-01); AS 1994 2887 (in force 1 Jan 1995); Art. 261bis StGB, version before 1 Jul 2020 (Fedlex eli/cc/54/757_781_799, version 2020-02-01); Art. 261bis StGB (SR 311.0; Fedlex eli/cc/54/757_781_799, version 2026-10-01); BGE 130 IV 111 E. 5.2
- acceptable answer: Ja. Die Äusserung erfolgte öffentlich im Sinne von BGE 130 IV 111 E. 5.2 (eine Versammlung von rund 40 über einen allgemeinen Aufruf eingeladenen, grösstenteils unbekannten Personen); sie richtet sich gegen eine Gruppe wegen eines geschützten Merkmals (Ethnie) und erfüllt den Tatbestand von Art. 261bis Abs. 4 StGB (Herabsetzung in einer gegen die Menschenwürde verstossenden Weise). Die Tat im Mai 2022 fällt in den zeitlichen Geltungsbereich.

**261bis-de-CHAR004-1** · R0 · conv · model: **convict** · statute: **acquit** (characteristic:not_listed)

> Sachverhalt: Ein Rentner aus Zug steht unter folgendem Vorwurf: In einem Leserbrief, der in einer Regionalzeitung abgedruckt wurde, forderte er dazu auf, Zürcherinnen und Zürcher wegen ihrer Kantonszugehörigkeit zu hassen, und zwar im März 2023. Er handelte vorsätzlich.

- derivation: act_date=2023-03-15: met (in force from 1995-01-01); characteristic=canton: failed (not on the closed list); paragraph=abs1: met; setting=public: met -> acquit (characteristic:not_listed)
- sources: Art. 261bis StGB (SR 311.0; Fedlex eli/cc/54/757_781_799, version 2026-10-01)
- acceptable answer: Nein. Das Merkmal «Kantonszugehörigkeit» gehört nicht zur abschliessenden Liste von Art. 261bis StGB (Rasse, Ethnie, Religion, sexuelle Orientierung); die Äusserung ist nach dieser Bestimmung nicht strafbar, auch wenn sie öffentlich erfolgte.

**261bis-de-CHAR004-1** · R0 · ver · model: **convict** · statute: **acquit** (characteristic:not_listed)

> Sachverhalt: Ein Rentner aus Zug steht unter folgendem Vorwurf: In einem Leserbrief, der in einer Regionalzeitung abgedruckt wurde, forderte er dazu auf, Zürcherinnen und Zürcher wegen ihrer Kantonszugehörigkeit zu hassen, und zwar im März 2023. Er handelte vorsätzlich.

- derivation: act_date=2023-03-15: met (in force from 1995-01-01); characteristic=canton: failed (not on the closed list); paragraph=abs1: met; setting=public: met -> acquit (characteristic:not_listed)
- sources: Art. 261bis StGB (SR 311.0; Fedlex eli/cc/54/757_781_799, version 2026-10-01)
- acceptable answer: Nein. Das Merkmal «Kantonszugehörigkeit» gehört nicht zur abschliessenden Liste von Art. 261bis StGB (Rasse, Ethnie, Religion, sexuelle Orientierung); die Äusserung ist nach dieser Bestimmung nicht strafbar, auch wenn sie öffentlich erfolgte.

**261bis-de-CHAR004-1** · R3 · conv · model: **convict** · statute: **acquit** (characteristic:not_listed)

> Sachverhalt: Ein Rentner aus Zug steht unter folgendem Vorwurf: In einem Leserbrief, der in einer Regionalzeitung abgedruckt wurde, forderte er dazu auf, Zürcherinnen und Zürcher wegen ihrer Kantonszugehörigkeit zu hassen, und zwar im März 2023. Er handelte vorsätzlich.

- derivation: act_date=2023-03-15: met (in force from 1995-01-01); characteristic=canton: failed (not on the closed list); paragraph=abs1: met; setting=public: met -> acquit (characteristic:not_listed)
- sources: Art. 261bis StGB (SR 311.0; Fedlex eli/cc/54/757_781_799, version 2026-10-01)
- acceptable answer: Nein. Das Merkmal «Kantonszugehörigkeit» gehört nicht zur abschliessenden Liste von Art. 261bis StGB (Rasse, Ethnie, Religion, sexuelle Orientierung); die Äusserung ist nach dieser Bestimmung nicht strafbar, auch wenn sie öffentlich erfolgte.

**261bis-de-CHAR004-1** · R3 · ver · model: **convict** · statute: **acquit** (characteristic:not_listed)

> Sachverhalt: Ein Rentner aus Zug steht unter folgendem Vorwurf: In einem Leserbrief, der in einer Regionalzeitung abgedruckt wurde, forderte er dazu auf, Zürcherinnen und Zürcher wegen ihrer Kantonszugehörigkeit zu hassen, und zwar im März 2023. Er handelte vorsätzlich.

- derivation: act_date=2023-03-15: met (in force from 1995-01-01); characteristic=canton: failed (not on the closed list); paragraph=abs1: met; setting=public: met -> acquit (characteristic:not_listed)
- sources: Art. 261bis StGB (SR 311.0; Fedlex eli/cc/54/757_781_799, version 2026-10-01)
- acceptable answer: Nein. Das Merkmal «Kantonszugehörigkeit» gehört nicht zur abschliessenden Liste von Art. 261bis StGB (Rasse, Ethnie, Religion, sexuelle Orientierung); die Äusserung ist nach dieser Bestimmung nicht strafbar, auch wenn sie öffentlich erfolgte.

**261bis-de-CHAR005-1** · R0 · conv · model: **convict** · statute: **acquit** (characteristic:not_listed)

> Sachverhalt: Im Januar 2024 hielt sich ein Unternehmer in Aarau auf. In einer Rede an einer Gemeindeversammlung vor rund 120 Stimmberechtigten setzte er Bauarbeiter wegen ihres Berufs in einer gegen die Menschenwürde verstossenden Weise herab. Er handelte vorsätzlich.

- derivation: act_date=2024-01-15: met (in force from 1995-01-01); characteristic=occupation: failed (not on the closed list); paragraph=abs4: met; setting=public: met -> acquit (characteristic:not_listed)
- sources: Art. 261bis StGB (SR 311.0; Fedlex eli/cc/54/757_781_799, version 2026-10-01)
- acceptable answer: Nein. Das Merkmal «Beruf» gehört nicht zur abschliessenden Liste von Art. 261bis StGB (Rasse, Ethnie, Religion, sexuelle Orientierung); die Äusserung ist nach dieser Bestimmung nicht strafbar, auch wenn sie öffentlich erfolgte.

**261bis-de-CHAR005-1** · R0 · ver · model: **convict** · statute: **acquit** (characteristic:not_listed)

> Sachverhalt: Im Januar 2024 hielt sich ein Unternehmer in Aarau auf. In einer Rede an einer Gemeindeversammlung vor rund 120 Stimmberechtigten setzte er Bauarbeiter wegen ihres Berufs in einer gegen die Menschenwürde verstossenden Weise herab. Er handelte vorsätzlich.

- derivation: act_date=2024-01-15: met (in force from 1995-01-01); characteristic=occupation: failed (not on the closed list); paragraph=abs4: met; setting=public: met -> acquit (characteristic:not_listed)
- sources: Art. 261bis StGB (SR 311.0; Fedlex eli/cc/54/757_781_799, version 2026-10-01)
- acceptable answer: Nein. Das Merkmal «Beruf» gehört nicht zur abschliessenden Liste von Art. 261bis StGB (Rasse, Ethnie, Religion, sexuelle Orientierung); die Äusserung ist nach dieser Bestimmung nicht strafbar, auch wenn sie öffentlich erfolgte.

**261bis-de-CHAR005-1** · R3 · ver · model: **convict** · statute: **acquit** (characteristic:not_listed)

> Sachverhalt: Im Januar 2024 hielt sich ein Unternehmer in Aarau auf. In einer Rede an einer Gemeindeversammlung vor rund 120 Stimmberechtigten setzte er Bauarbeiter wegen ihres Berufs in einer gegen die Menschenwürde verstossenden Weise herab. Er handelte vorsätzlich.

- derivation: act_date=2024-01-15: met (in force from 1995-01-01); characteristic=occupation: failed (not on the closed list); paragraph=abs4: met; setting=public: met -> acquit (characteristic:not_listed)
- sources: Art. 261bis StGB (SR 311.0; Fedlex eli/cc/54/757_781_799, version 2026-10-01)
- acceptable answer: Nein. Das Merkmal «Beruf» gehört nicht zur abschliessenden Liste von Art. 261bis StGB (Rasse, Ethnie, Religion, sexuelle Orientierung); die Äusserung ist nach dieser Bestimmung nicht strafbar, auch wenn sie öffentlich erfolgte.

**261bis-de-CHAR005-1** · R4 · ver · model: **convict** · statute: **acquit** (characteristic:not_listed)

> Sachverhalt: Im Januar 2024 hielt sich ein Unternehmer in Aarau auf. In einer Rede an einer Gemeindeversammlung vor rund 120 Stimmberechtigten setzte er Bauarbeiter wegen ihres Berufs in einer gegen die Menschenwürde verstossenden Weise herab. Er handelte vorsätzlich.

- derivation: act_date=2024-01-15: met (in force from 1995-01-01); characteristic=occupation: failed (not on the closed list); paragraph=abs4: met; setting=public: met -> acquit (characteristic:not_listed)
- sources: Art. 261bis StGB (SR 311.0; Fedlex eli/cc/54/757_781_799, version 2026-10-01)
- acceptable answer: Nein. Das Merkmal «Beruf» gehört nicht zur abschliessenden Liste von Art. 261bis StGB (Rasse, Ethnie, Religion, sexuelle Orientierung); die Äusserung ist nach dieser Bestimmung nicht strafbar, auch wenn sie öffentlich erfolgte.

**261bis-de-CHAR006-1** · R0 · conv · model: **convict** · statute: **acquit** (characteristic:not_listed)

> Sachverhalt: Im März 2023 kam es in Zürich zu folgendem Vorfall, an dem ein Student beteiligt war: In einem Kommentar in einem frei zugänglichen Online-Forum rief er zur Diskriminierung von jungen Erwachsenen wegen ihres Alters auf. Er handelte vorsätzlich.

- derivation: act_date=2023-03-15: met (in force from 1995-01-01); characteristic=age: failed (not on the closed list); paragraph=abs1: met; setting=public: met -> acquit (characteristic:not_listed)
- sources: Art. 261bis StGB (SR 311.0; Fedlex eli/cc/54/757_781_799, version 2026-10-01)
- acceptable answer: Nein. Das Merkmal «Alter» gehört nicht zur abschliessenden Liste von Art. 261bis StGB (Rasse, Ethnie, Religion, sexuelle Orientierung); die Äusserung ist nach dieser Bestimmung nicht strafbar, auch wenn sie öffentlich erfolgte.

**261bis-de-CHAR006-1** · R0 · ver · model: **convict** · statute: **acquit** (characteristic:not_listed)

> Sachverhalt: Im März 2023 kam es in Zürich zu folgendem Vorfall, an dem ein Student beteiligt war: In einem Kommentar in einem frei zugänglichen Online-Forum rief er zur Diskriminierung von jungen Erwachsenen wegen ihres Alters auf. Er handelte vorsätzlich.

- derivation: act_date=2023-03-15: met (in force from 1995-01-01); characteristic=age: failed (not on the closed list); paragraph=abs1: met; setting=public: met -> acquit (characteristic:not_listed)
- sources: Art. 261bis StGB (SR 311.0; Fedlex eli/cc/54/757_781_799, version 2026-10-01)
- acceptable answer: Nein. Das Merkmal «Alter» gehört nicht zur abschliessenden Liste von Art. 261bis StGB (Rasse, Ethnie, Religion, sexuelle Orientierung); die Äusserung ist nach dieser Bestimmung nicht strafbar, auch wenn sie öffentlich erfolgte.

**261bis-de-CHAR007-1** · R0 · conv · model: **convict** · statute: **acquit** (characteristic:not_listed)

> Sachverhalt: In Thun äusserte sich eine Frau im Mai 2022 wie folgt: In einem vollbesetzten Tram, laut und an alle Fahrgäste gerichtet, stachelte sie zum Hass gegen Menschen mit einer Behinderung wegen ihrer Behinderung an. Der Vorsatz ist unbestritten.

- derivation: act_date=2022-05-15: met (in force from 1995-01-01); characteristic=disability: failed (not on the closed list); paragraph=abs1: met; setting=public: met -> acquit (characteristic:not_listed)
- sources: Art. 261bis StGB (SR 311.0; Fedlex eli/cc/54/757_781_799, version 2026-10-01)
- acceptable answer: Nein. Das Merkmal «Behinderung» gehört nicht zur abschliessenden Liste von Art. 261bis StGB (Rasse, Ethnie, Religion, sexuelle Orientierung); die Äusserung ist nach dieser Bestimmung nicht strafbar, auch wenn sie öffentlich erfolgte.

**261bis-de-CHAR007-1** · R0 · ver · model: **convict** · statute: **acquit** (characteristic:not_listed)

> Sachverhalt: In Thun äusserte sich eine Frau im Mai 2022 wie folgt: In einem vollbesetzten Tram, laut und an alle Fahrgäste gerichtet, stachelte sie zum Hass gegen Menschen mit einer Behinderung wegen ihrer Behinderung an. Der Vorsatz ist unbestritten.

- derivation: act_date=2022-05-15: met (in force from 1995-01-01); characteristic=disability: failed (not on the closed list); paragraph=abs1: met; setting=public: met -> acquit (characteristic:not_listed)
- sources: Art. 261bis StGB (SR 311.0; Fedlex eli/cc/54/757_781_799, version 2026-10-01)
- acceptable answer: Nein. Das Merkmal «Behinderung» gehört nicht zur abschliessenden Liste von Art. 261bis StGB (Rasse, Ethnie, Religion, sexuelle Orientierung); die Äusserung ist nach dieser Bestimmung nicht strafbar, auch wenn sie öffentlich erfolgte.

**261bis-de-CHAR008-0** · R4 · ver · model: **acquit** · statute: **convict** (convict)

> Sachverhalt: Gemäss Anklageschrift äusserte sich eine Unternehmerin im Januar 2024 in Schaffhausen wie folgt: In einem öffentlich einsehbaren Beitrag auf ihrem Social-Media-Profil verbreitete sie eine Ideologie, die auf die systematische Herabsetzung von homosexuellen Personen wegen ihrer sexuellen Orientierung gerichtet ist. Sie handelte vorsätzlich.

- derivation: act_date=2024-01-15: met (in force from 1995-01-01); characteristic=sexual_orientation: met (covered from 2020-07-01); paragraph=abs2: met; setting=public: met -> convict (convict)
- sources: Art. 2 StGB (Fedlex eli/cc/54/757_781_799, version 2026-10-01); AS 1994 2887 (in force 1 Jan 1995); AS 2020 1609 (in force 1 Jul 2020); Art. 261bis StGB (SR 311.0; Fedlex eli/cc/54/757_781_799, version 2026-10-01); BGE 130 IV 111 E. 5.2
- acceptable answer: Ja. Die Äusserung erfolgte öffentlich im Sinne von BGE 130 IV 111 E. 5.2 (ein öffentlich einsehbarer Beitrag in den sozialen Medien); sie richtet sich gegen eine Gruppe wegen eines geschützten Merkmals (sexuelle Orientierung) und erfüllt den Tatbestand von Art. 261bis Abs. 2 StGB (Verbreiten einer Ideologie der systematischen Herabsetzung). Die Tat im Januar 2024 fällt in den zeitlichen Geltungsbereich.

**261bis-de-CHAR008-1** · R0 · conv · model: **convict** · statute: **acquit** (characteristic:not_listed)

> Sachverhalt: Gemäss Anklageschrift äusserte sich eine Unternehmerin im Januar 2024 in Schaffhausen wie folgt: In einem öffentlich einsehbaren Beitrag auf ihrem Social-Media-Profil verbreitete sie eine Ideologie, die auf die systematische Herabsetzung von Lehrpersonen wegen ihres Berufs gerichtet ist. Sie handelte vorsätzlich.

- derivation: act_date=2024-01-15: met (in force from 1995-01-01); characteristic=occupation: failed (not on the closed list); paragraph=abs2: met; setting=public: met -> acquit (characteristic:not_listed)
- sources: Art. 261bis StGB (SR 311.0; Fedlex eli/cc/54/757_781_799, version 2026-10-01)
- acceptable answer: Nein. Das Merkmal «Beruf» gehört nicht zur abschliessenden Liste von Art. 261bis StGB (Rasse, Ethnie, Religion, sexuelle Orientierung); die Äusserung ist nach dieser Bestimmung nicht strafbar, auch wenn sie öffentlich erfolgte.

**261bis-de-CHAR008-1** · R0 · ver · model: **convict** · statute: **acquit** (characteristic:not_listed)

> Sachverhalt: Gemäss Anklageschrift äusserte sich eine Unternehmerin im Januar 2024 in Schaffhausen wie folgt: In einem öffentlich einsehbaren Beitrag auf ihrem Social-Media-Profil verbreitete sie eine Ideologie, die auf die systematische Herabsetzung von Lehrpersonen wegen ihres Berufs gerichtet ist. Sie handelte vorsätzlich.

- derivation: act_date=2024-01-15: met (in force from 1995-01-01); characteristic=occupation: failed (not on the closed list); paragraph=abs2: met; setting=public: met -> acquit (characteristic:not_listed)
- sources: Art. 261bis StGB (SR 311.0; Fedlex eli/cc/54/757_781_799, version 2026-10-01)
- acceptable answer: Nein. Das Merkmal «Beruf» gehört nicht zur abschliessenden Liste von Art. 261bis StGB (Rasse, Ethnie, Religion, sexuelle Orientierung); die Äusserung ist nach dieser Bestimmung nicht strafbar, auch wenn sie öffentlich erfolgte.

**261bis-de-CHAR009-1** · R0 · conv · model: **convict** · statute: **acquit** (characteristic:not_listed)

> Sachverhalt: Im September 2021 ereignete sich in Winterthur ein Vorfall, an dem eine Rentnerin beteiligt war: Auf Flugblättern, die sie in einer belebten Fussgängerzone an Passanten verteilte, propagierte sie eine Weltanschauung, nach der ältere Menschen wegen ihres Alters als minderwertig gelten. Dass sie vorsätzlich handelte, ist erstellt.

- derivation: act_date=2021-09-15: met (in force from 1995-01-01); characteristic=age: failed (not on the closed list); paragraph=abs2: met; setting=public: met -> acquit (characteristic:not_listed)
- sources: Art. 261bis StGB (SR 311.0; Fedlex eli/cc/54/757_781_799, version 2026-10-01)
- acceptable answer: Nein. Das Merkmal «Alter» gehört nicht zur abschliessenden Liste von Art. 261bis StGB (Rasse, Ethnie, Religion, sexuelle Orientierung); die Äusserung ist nach dieser Bestimmung nicht strafbar, auch wenn sie öffentlich erfolgte.

**261bis-de-CHAR009-1** · R0 · ver · model: **convict** · statute: **acquit** (characteristic:not_listed)

> Sachverhalt: Im September 2021 ereignete sich in Winterthur ein Vorfall, an dem eine Rentnerin beteiligt war: Auf Flugblättern, die sie in einer belebten Fussgängerzone an Passanten verteilte, propagierte sie eine Weltanschauung, nach der ältere Menschen wegen ihres Alters als minderwertig gelten. Dass sie vorsätzlich handelte, ist erstellt.

- derivation: act_date=2021-09-15: met (in force from 1995-01-01); characteristic=age: failed (not on the closed list); paragraph=abs2: met; setting=public: met -> acquit (characteristic:not_listed)
- sources: Art. 261bis StGB (SR 311.0; Fedlex eli/cc/54/757_781_799, version 2026-10-01)
- acceptable answer: Nein. Das Merkmal «Alter» gehört nicht zur abschliessenden Liste von Art. 261bis StGB (Rasse, Ethnie, Religion, sexuelle Orientierung); die Äusserung ist nach dieser Bestimmung nicht strafbar, auch wenn sie öffentlich erfolgte.

**261bis-de-CHAR010-1** · R0 · conv · model: **convict** · statute: **acquit** (characteristic:not_listed)

> Sachverhalt: Eine Studentin aus St. Gallen steht unter folgendem Vorwurf: An einem Stand auf einem gut besuchten Wochenmarkt, vor zahlreichen Kundinnen und Kunden, sprach sie Walliserinnen und Wallisern wegen ihrer Kantonszugehörigkeit die Gleichwertigkeit als Menschen ab, und zwar im Juni 2025. Sie handelte vorsätzlich.

- derivation: act_date=2025-06-15: met (in force from 1995-01-01); characteristic=canton: failed (not on the closed list); paragraph=abs4: met; setting=public: met -> acquit (characteristic:not_listed)
- sources: Art. 261bis StGB (SR 311.0; Fedlex eli/cc/54/757_781_799, version 2026-10-01)
- acceptable answer: Nein. Das Merkmal «Kantonszugehörigkeit» gehört nicht zur abschliessenden Liste von Art. 261bis StGB (Rasse, Ethnie, Religion, sexuelle Orientierung); die Äusserung ist nach dieser Bestimmung nicht strafbar, auch wenn sie öffentlich erfolgte.

**261bis-de-CHAR010-1** · R0 · ver · model: **convict** · statute: **acquit** (characteristic:not_listed)

> Sachverhalt: Eine Studentin aus St. Gallen steht unter folgendem Vorwurf: An einem Stand auf einem gut besuchten Wochenmarkt, vor zahlreichen Kundinnen und Kunden, sprach sie Walliserinnen und Wallisern wegen ihrer Kantonszugehörigkeit die Gleichwertigkeit als Menschen ab, und zwar im Juni 2025. Sie handelte vorsätzlich.

- derivation: act_date=2025-06-15: met (in force from 1995-01-01); characteristic=canton: failed (not on the closed list); paragraph=abs4: met; setting=public: met -> acquit (characteristic:not_listed)
- sources: Art. 261bis StGB (SR 311.0; Fedlex eli/cc/54/757_781_799, version 2026-10-01)
- acceptable answer: Nein. Das Merkmal «Kantonszugehörigkeit» gehört nicht zur abschliessenden Liste von Art. 261bis StGB (Rasse, Ethnie, Religion, sexuelle Orientierung); die Äusserung ist nach dieser Bestimmung nicht strafbar, auch wenn sie öffentlich erfolgte.

**261bis-de-CHAR010-1** · R3 · conv · model: **convict** · statute: **acquit** (characteristic:not_listed)

> Sachverhalt: Eine Studentin aus St. Gallen steht unter folgendem Vorwurf: An einem Stand auf einem gut besuchten Wochenmarkt, vor zahlreichen Kundinnen und Kunden, sprach sie Walliserinnen und Wallisern wegen ihrer Kantonszugehörigkeit die Gleichwertigkeit als Menschen ab, und zwar im Juni 2025. Sie handelte vorsätzlich.

- derivation: act_date=2025-06-15: met (in force from 1995-01-01); characteristic=canton: failed (not on the closed list); paragraph=abs4: met; setting=public: met -> acquit (characteristic:not_listed)
- sources: Art. 261bis StGB (SR 311.0; Fedlex eli/cc/54/757_781_799, version 2026-10-01)
- acceptable answer: Nein. Das Merkmal «Kantonszugehörigkeit» gehört nicht zur abschliessenden Liste von Art. 261bis StGB (Rasse, Ethnie, Religion, sexuelle Orientierung); die Äusserung ist nach dieser Bestimmung nicht strafbar, auch wenn sie öffentlich erfolgte.

**261bis-de-CHAR010-1** · R3 · ver · model: **convict** · statute: **acquit** (characteristic:not_listed)

> Sachverhalt: Eine Studentin aus St. Gallen steht unter folgendem Vorwurf: An einem Stand auf einem gut besuchten Wochenmarkt, vor zahlreichen Kundinnen und Kunden, sprach sie Walliserinnen und Wallisern wegen ihrer Kantonszugehörigkeit die Gleichwertigkeit als Menschen ab, und zwar im Juni 2025. Sie handelte vorsätzlich.

- derivation: act_date=2025-06-15: met (in force from 1995-01-01); characteristic=canton: failed (not on the closed list); paragraph=abs4: met; setting=public: met -> acquit (characteristic:not_listed)
- sources: Art. 261bis StGB (SR 311.0; Fedlex eli/cc/54/757_781_799, version 2026-10-01)
- acceptable answer: Nein. Das Merkmal «Kantonszugehörigkeit» gehört nicht zur abschliessenden Liste von Art. 261bis StGB (Rasse, Ethnie, Religion, sexuelle Orientierung); die Äusserung ist nach dieser Bestimmung nicht strafbar, auch wenn sie öffentlich erfolgte.

**261bis-de-CHAR010-1** · R4 · ver · model: **convict** · statute: **acquit** (characteristic:not_listed)

> Sachverhalt: Eine Studentin aus St. Gallen steht unter folgendem Vorwurf: An einem Stand auf einem gut besuchten Wochenmarkt, vor zahlreichen Kundinnen und Kunden, sprach sie Walliserinnen und Wallisern wegen ihrer Kantonszugehörigkeit die Gleichwertigkeit als Menschen ab, und zwar im Juni 2025. Sie handelte vorsätzlich.

- derivation: act_date=2025-06-15: met (in force from 1995-01-01); characteristic=canton: failed (not on the closed list); paragraph=abs4: met; setting=public: met -> acquit (characteristic:not_listed)
- sources: Art. 261bis StGB (SR 311.0; Fedlex eli/cc/54/757_781_799, version 2026-10-01)
- acceptable answer: Nein. Das Merkmal «Kantonszugehörigkeit» gehört nicht zur abschliessenden Liste von Art. 261bis StGB (Rasse, Ethnie, Religion, sexuelle Orientierung); die Äusserung ist nach dieser Bestimmung nicht strafbar, auch wenn sie öffentlich erfolgte.

**261bis-de-CHAR011-1** · R0 · conv · model: **convict** · statute: **acquit** (characteristic:not_listed)

> Sachverhalt: Im Juni 2025 hielt sich ein Unternehmer in Bern auf. In einer Rede an einer Gemeindeversammlung vor rund 120 Stimmberechtigten verbreitete er systematisch Thesen, wonach nichtbinäre Personen wegen ihrer Geschlechtsidentität weniger wert seien als andere Menschen. Er handelte vorsätzlich.

- derivation: act_date=2025-06-15: met (in force from 1995-01-01); characteristic=gender_identity: failed (not on the closed list); paragraph=abs2: met; setting=public: met -> acquit (characteristic:not_listed)
- sources: Art. 261bis StGB (SR 311.0; Fedlex eli/cc/54/757_781_799, version 2026-10-01); Pa.Iv. 13.407 (legislative history)
- acceptable answer: Nein. Die Geschlechtsidentität gehört nicht zur abschliessenden Liste von Art. 261bis StGB; mit der Revision von 2020 wurde nur die sexuelle Orientierung aufgenommen.

**261bis-de-CHAR011-1** · R0 · ver · model: **convict** · statute: **acquit** (characteristic:not_listed)

> Sachverhalt: Im Juni 2025 hielt sich ein Unternehmer in Bern auf. In einer Rede an einer Gemeindeversammlung vor rund 120 Stimmberechtigten verbreitete er systematisch Thesen, wonach nichtbinäre Personen wegen ihrer Geschlechtsidentität weniger wert seien als andere Menschen. Er handelte vorsätzlich.

- derivation: act_date=2025-06-15: met (in force from 1995-01-01); characteristic=gender_identity: failed (not on the closed list); paragraph=abs2: met; setting=public: met -> acquit (characteristic:not_listed)
- sources: Art. 261bis StGB (SR 311.0; Fedlex eli/cc/54/757_781_799, version 2026-10-01); Pa.Iv. 13.407 (legislative history)
- acceptable answer: Nein. Die Geschlechtsidentität gehört nicht zur abschliessenden Liste von Art. 261bis StGB; mit der Revision von 2020 wurde nur die sexuelle Orientierung aufgenommen.

**261bis-de-CHAR012-1** · R0 · conv · model: **convict** · statute: **acquit** (characteristic:not_listed)

> Sachverhalt: Im Januar 2024 äusserte sich ein Student in Basel wie folgt: An einer bewilligten Kundgebung auf einem öffentlichen Platz vor rund 300 Personen warb er für eine Ideologie, die darauf abzielt, Frauen wegen ihres Geschlechts systematisch zu verleumden. Er handelte vorsätzlich.

- derivation: act_date=2024-01-15: met (in force from 1995-01-01); characteristic=sex: failed (not on the closed list); paragraph=abs2: met; setting=public: met -> acquit (characteristic:not_listed)
- sources: Art. 261bis StGB (SR 311.0; Fedlex eli/cc/54/757_781_799, version 2026-10-01)
- acceptable answer: Nein. Das Merkmal «Geschlecht» gehört nicht zur abschliessenden Liste von Art. 261bis StGB (Rasse, Ethnie, Religion, sexuelle Orientierung); die Äusserung ist nach dieser Bestimmung nicht strafbar, auch wenn sie öffentlich erfolgte.

**261bis-de-CHAR012-1** · R0 · ver · model: **convict** · statute: **acquit** (characteristic:not_listed)

> Sachverhalt: Im Januar 2024 äusserte sich ein Student in Basel wie folgt: An einer bewilligten Kundgebung auf einem öffentlichen Platz vor rund 300 Personen warb er für eine Ideologie, die darauf abzielt, Frauen wegen ihres Geschlechts systematisch zu verleumden. Er handelte vorsätzlich.

- derivation: act_date=2024-01-15: met (in force from 1995-01-01); characteristic=sex: failed (not on the closed list); paragraph=abs2: met; setting=public: met -> acquit (characteristic:not_listed)
- sources: Art. 261bis StGB (SR 311.0; Fedlex eli/cc/54/757_781_799, version 2026-10-01)
- acceptable answer: Nein. Das Merkmal «Geschlecht» gehört nicht zur abschliessenden Liste von Art. 261bis StGB (Rasse, Ethnie, Religion, sexuelle Orientierung); die Äusserung ist nach dieser Bestimmung nicht strafbar, auch wenn sie öffentlich erfolgte.

**261bis-de-CHAR013-0** · R4 · conv · model: **acquit** · statute: **convict** (convict)

> Sachverhalt: In Zug äusserte sich eine Unternehmerin im März 2023 wie folgt: An einer Versammlung in einer Waldhütte vor rund 40 Teilnehmenden, die über einen allgemeinen Aufruf eingeladen worden waren und die sie zum grössten Teil nicht persönlich kannte, rief sie zu Hass gegen Muslime wegen ihrer Religion auf. Der Vorsatz ist unbestritten.

- derivation: act_date=2023-03-15: met (in force from 1995-01-01); characteristic=religion: met (covered from 1995-01-01); paragraph=abs1: met; setting=public: met -> convict (convict)
- sources: Art. 2 StGB (Fedlex eli/cc/54/757_781_799, version 2026-10-01); AS 1994 2887 (in force 1 Jan 1995); Art. 261bis StGB, version before 1 Jul 2020 (Fedlex eli/cc/54/757_781_799, version 2020-02-01); Art. 261bis StGB (SR 311.0; Fedlex eli/cc/54/757_781_799, version 2026-10-01); BGE 130 IV 111 E. 5.2
- acceptable answer: Ja. Die Äusserung erfolgte öffentlich im Sinne von BGE 130 IV 111 E. 5.2 (eine Versammlung von rund 40 über einen allgemeinen Aufruf eingeladenen, grösstenteils unbekannten Personen); sie richtet sich gegen eine Gruppe wegen eines geschützten Merkmals (Religion) und erfüllt den Tatbestand von Art. 261bis Abs. 1 StGB (Aufruf zu Hass oder Diskriminierung). Die Tat im März 2023 fällt in den zeitlichen Geltungsbereich.

**261bis-de-CHAR013-0** · R4 · ver · model: **acquit** · statute: **convict** (convict)

> Sachverhalt: In Zug äusserte sich eine Unternehmerin im März 2023 wie folgt: An einer Versammlung in einer Waldhütte vor rund 40 Teilnehmenden, die über einen allgemeinen Aufruf eingeladen worden waren und die sie zum grössten Teil nicht persönlich kannte, rief sie zu Hass gegen Muslime wegen ihrer Religion auf. Der Vorsatz ist unbestritten.

- derivation: act_date=2023-03-15: met (in force from 1995-01-01); characteristic=religion: met (covered from 1995-01-01); paragraph=abs1: met; setting=public: met -> convict (convict)
- sources: Art. 2 StGB (Fedlex eli/cc/54/757_781_799, version 2026-10-01); AS 1994 2887 (in force 1 Jan 1995); Art. 261bis StGB, version before 1 Jul 2020 (Fedlex eli/cc/54/757_781_799, version 2020-02-01); Art. 261bis StGB (SR 311.0; Fedlex eli/cc/54/757_781_799, version 2026-10-01); BGE 130 IV 111 E. 5.2
- acceptable answer: Ja. Die Äusserung erfolgte öffentlich im Sinne von BGE 130 IV 111 E. 5.2 (eine Versammlung von rund 40 über einen allgemeinen Aufruf eingeladenen, grösstenteils unbekannten Personen); sie richtet sich gegen eine Gruppe wegen eines geschützten Merkmals (Religion) und erfüllt den Tatbestand von Art. 261bis Abs. 1 StGB (Aufruf zu Hass oder Diskriminierung). Die Tat im März 2023 fällt in den zeitlichen Geltungsbereich.

## Contested items (fact-dependent publicity; no gold verdict)

| lang | rung | framing | convicted | n |
|---|---|---|---|---|
| de | R0 | conv | 14 | 15 |
| de | R0 | ver | 14 | 15 |
| de | R3 | conv | 8 | 15 |
| de | R3 | ver | 11 | 15 |
| de | R4 | conv | 0 | 15 |
| de | R4 | ver | 9 | 15 |
