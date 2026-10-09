# FR translation notes (Art. 261bis StGB / art. 261bis CP), for the human reviewer

Files: `templates/fr.yaml`, `prompts/fr.yaml`, `answers/fr.yaml`. Source: the German files with the same ids. Terminology follows the
official CP text (Fedlex, version 2026-10-01) and the French Regeste of ATF 130 IV 111.

## Grammar mechanics
- **Comma rule.** Settings have no leading or trailing comma and start in lower case, because they follow a colon. Frames join
  them as `{setting}, {act}`, and acts start with the subject pronoun (`{pron} a incité …`). F05 opens a sentence with the
  setting and uses `{Setting}`. In German some settings end with a comma; in French the comma always comes from the frame.
- **Morphology** has only `pron` (il/elle), `e` (past-participle agreement: `s'est exprimé{e}`, `domicilié{e}`) and
  `spouse` ("son épouse" / "son mari"). French possessives (son/sa/ses) agree with the possessed noun, not with the owner, so
  they are written out directly in the settings. The German `poss_*` keys have no French equivalent.
- **Group forms:** `def` (les …), `de` (des …), `a` (aux …), all written out for every group, so "de les" or "à les" can never
  be produced. Acts never use a participle or adjective that agrees with the group, because the groups have mixed genders.
  For a heavy object, French word order puts the group last ("a présenté comme des êtres humains de moindre valeur les …",
  "a qualifié d'êtres humains de seconde zone les …"). a4A1 follows the statute's own order ("abaisse … d'une façon qui
  porte atteinte à la dignité humaine [un groupe] en raison de …").
- `qu'{pron}` always gives "qu'il" or "qu'elle". F03 uses "domicilié(e) à {place}" instead of "de {place}", which avoids
  "de Aarau". All places take "à".
- Typography: "Faits :", " ; ", " ? " and « … » use a normal space (render.py turns any whitespace into a normal space
  anyway). Apostrophes are straight ('), while Fedlex uses ’. "1er juillet".

## Terms
- Statute wording: "publiquement", "incite à la haine / à la discrimination envers", "propage une idéologie visant à rabaisser …
  de façon systématique", "abaisse … d'une façon qui porte atteinte à la dignité humaine". Citations: "art. 261bis CP",
  "art. 2 CP", "ATF 130 IV 111 consid. 5.2".
- Vorsatz → "a agi intentionnellement" / "L'intention n'est pas contestée" (vocabulary of art. 12 CP).
- Tatbestand erfüllt → "l'infraction est réalisée". Tathandlung → "comportement incriminé". Merkmal → "critère protégé"
  (the same label as statute.yaml). "in der zur Tatzeit geltenden Fassung" → "dans sa teneur en vigueur au moment des faits".
- Prompts address the model as "vous" (Examinez, Répondez), not as "tu". "Répondez par Oui ou par Non" keeps the capital
  letters so that the instruction matches the answer candidates "Oui" / "Non".
- Swiss usage: Abendessen → "repas du soir" (in Switzerland "dîner" means lunch and "souper" means dinner, so both are
  ambiguous). Gemeindeversammlung → "assemblée communale". Stimmberechtigte → "ayants droit au vote". Waldhütte → "refuge
  forestier", as in the Regeste. Leserbrief → "lettre de lecteur". E-Mail → "courriel". Tram → "tram".

## Groups and characteristics (needs a decision)
- Statutory words: race → "appartenance raciale" (the CP has no noun "race"). Religion → "religion". Sexual orientation →
  "orientation sexuelle".
- **Ethnicity:** following the brief, the base form is "en raison de leur **ethnie**" (= Ethnie) and the synonym form
  (`eth_roma_syn`) is "en raison de leur **appartenance ethnique**". The French statute actually says "appartenance …
  ethnique", so in French the *synonym* form is the closer one to the statute. The synonym placebo is therefore weaker in
  French than in German. A possible alternative is base "appartenance ethnique" and synonym "origine ethnique".
- The other synonyms: "couleur de peau", "foi", "homosexualité".
- char_labels use statutory phrases (appartenance raciale/ethnique/religieuse). Because of this, the label of `rel_*` is
  "appartenance religieuse" while the scenario text says "religion" or "foi".
- "les juifs", "les musulmans", "les hindous" are in lower case, because they name members of a religion. "Kosovo-Albaner" →
  "Albanais du Kosovo". "christliche Freikirche" → "Église libre chrétienne". "schwule Männer" → "hommes gays". "Menschen
  mit Behinderung" → "personnes en situation de handicap". "politische Überzeugung" → "opinions politiques" (plural, so the
  text says "leurs"). Lehrpersonen and cantons use the two-gender form ("les enseignantes et les enseignants").

## Acts (wording families must stay distinct)
- Abs. 1: A "a incité à la haine / à la discrimination envers" (statutory). B "a appelé à haïr", "a attisé la haine contre".
  C "a préconisé de défavoriser et d'exclure", "a exhorté à refuser des logements et des emplois aux …".
- Abs. 2: A "a propagé une idéologie visant à rabaisser de façon systématique" (statutory) and "a diffusé les écrits d'une
  doctrine qui rabaisse systématiquement". B "a promu une vision du monde qui assigne un rang inférieur aux …" and "a fait la
  promotion d'une idéologie qui a pour but de dénigrer systématiquement". German B2 "verleumden" is rendered as "dénigrer",
  the French statute's equivalent of "Verleumdung". C "doctrine qui présente systématiquement comme des êtres
  inférieurs", "thèses selon lesquelles … vaudraient moins que les autres êtres humains".
- Abs. 4: A "a abaissé d'une façon qui porte atteinte à la dignité humaine" (statutory) and "a dévalorisé … d'une manière
  contraire à la dignité humaine". The more literal "rabaisser" is avoided because it is the Abs. 2 statutory verb.
  B "a présenté comme des êtres humains de moindre valeur", "a vilipendé … d'une manière empreinte de mépris pour l'être
  humain". Unsure: "menschenverachtend" has no settled French equivalent. C "a nié l'égale valeur humaine des …", "a qualifié
  d'êtres humains de seconde zone".
- In a2C2, a4A2 and a4B2 the clause "en raison de leur …" sits in the middle of the sentence. This is grammatical, but a native
  speaker should check that it reads well.

## Settings (legal facts kept)
- Family placebos keep the family wording and stay plainly public: 300 people, "consultable publiquement", a printed letter,
  40 participants invited by "un appel général" whom the actor mostly did not know personally, passers-by, 120 voters,
  "librement accessible", every passenger, numerous customers.
- pub_hut_fam: "dans un refuge forestier de sa famille", with "son épouse/mari et ses enfants étant également présents".
- Contested settings keep the same mix of facts: about 30 members, a few known well and most only superficially; about 20
  guests who are friends, neighbours and acquaintances of acquaintances; 25 staff; 15 members who have known each other for
  years. In cont_clubchat, "réunissant environ 30 membres de son club sportif" makes the number belong to the chat group
  and not to the club.
- priv_dinner: "dans le cercle familial le plus étroit … en présence uniquement de son épouse/mari et de ses deux enfants
  adultes".
