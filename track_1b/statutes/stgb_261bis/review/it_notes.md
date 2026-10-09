# Italian (it) translation: notes for the human reviewer

Files: `templates/it.yaml`, `prompts/it.yaml`, `answers/it.yaml` (translated from the `de.yaml` files, with the same ids
and keys). The Italian statutory wording comes from the CP text (art. 261bis, art. 2), and the publicity wording comes
from the Italian regesto of DTF 130 IV 111.

## Grammar mechanics
- **Group forms.** Every group has `def` ("le persone nere …"), `di` ("delle persone nere …") and `a` ("alle persone
  nere …"). Acts use `{g.def}`, `{g.di}` (a1A2 only) and `{g.a}` (a1C2, a4C1).
- **Characteristic phrase.** Every group ends with "a causa del/della/delle loro <characteristic>". I chose this over
  the statute's "per la loro …" because "per" can be misread as "on behalf of / for" in several acts (for example
  "negare alloggi … alle persone nere per la loro razza").
- **Possessives.** Italian possessives agree with the thing possessed, not with its owner, so suo/sua/suoi need no
  morphology. The only actor-dependent items are the participles `{espresso}`, `{coinvolto}` and `{accusato}` (in
  frames) and `{spouse}` ("sua moglie" / "suo marito", used without an article as Italian requires).
- **Pro-drop.** Acts start with the verb in the passato prossimo ("ha incitato …") and have no pronoun. In every frame
  the actor is the last-named singular subject. "{Pron} handelte vorsätzlich" became "Ha agito intenzionalmente." (the
  CP art. 12 term is "intenzionalmente"). F04 became "L'intenzione non è contestata."
- **Commas.** Settings never end with a comma. Every frame joins them as "{setting}, {act}". A grep of all 660
  scenarios plus a full frame×setting and act×group cross (1,962 texts) found no doubled spaces, ",,", " ,", "..",
  unresolved braces, or "di le"/"a gli"-type preposition errors.
- **Object position.** In a2B1, a2C1, a4A1, a4B1, a4B2 and a4C2 the group phrase comes last ("ha definito esseri umani di
  seconda categoria le persone nere a causa della loro razza"). Placed mid-sentence, the long "a causa della loro …"
  phrase was hard to read. a4A1 now also follows the statute's own order ("in modo … lesivo della dignità umana,
  discredita … una persona").

## Terms
- "Sachverhalt" became **Fatti:**. "Anklageschrift" became **atto d'accusa** (CPP). "aktenkundig" became "messo agli
  atti".
- "Äusserung" became **esternazione** in the prompts and answers. The publicity element is **carattere pubblico**, and
  "pubblicità" is avoided as ambiguous. "Tathandlung" became **comportamento punibile**. "geschütztes Merkmal" became
  **caratteristica protetta**. "Tatbestand erfüllt" became **la fattispecie è adempiuta**. Citations use the forms
  "art. 261bis CP", "art. 2 CP" and "DTF 130 IV 111 consid. 5.2".
- **famigliare** (the regesto's spelling) is used everywhere: "cerchia famigliare", "azienda famigliare".
- `pub_hut`: "Waldhütte" became **rifugio forestale** and "Versammlung" became **riunione**, both from the regesto
  (consid. 6). The setting keeps all its facts: about 40 participants, invited through a general call, mostly not known
  personally.
- `priv_dinner` is "nella più stretta cerchia famigliare … alla sola presenza di {spouse} e dei suoi due figli adulti",
  so the restriction ("nur") is kept.
- **Geschwister** became "fratelli", the usual Italian collective for siblings. It could be read as "brothers" only.
  The legal facts are unaffected because these are family members either way.
- **Acts, by wording family**:
  - Cpv. 1, A: incitato all'odio contro / alla discriminazione di. B: esortato a odiare / fomentato l'odio. C: invitato
    a svantaggiare ed emarginare / incitato a negare alloggi e posti di lavoro. a1C2 reuses "incitare" because German
    A1 and C2 both use "aufrufen".
  - Cpv. 2, A: propagato un'ideologia intesa a discreditare sistematicamente / scritti di una dottrina che discredita
    sistematicamente. B: visione del mondo secondo cui sono da considerare inferiori / propaganda per un'ideologia che
    mira a calunniare. C: dottrina che presenta come inferiori / tesi secondo cui varrebbero meno.
  - Cpv. 4, A: discreditato in modo lesivo della dignità umana / denigrato in un modo che lede la dignità umana. B:
    descritto come esseri umani di minor valore / vilipeso in modo disumano. C: negato il pari valore in quanto esseri
    umani / definito esseri umani di seconda categoria.
  - No two German wordings share one Italian wording. Please check that "vilipeso in modo disumano" (for "verunglimpfte
    in menschenverachtender Weise") reads as cpv. 4 conduct.
- **Synonyms**: colore della pelle, appartenenza etnica, fede and omosessualità, against the statutory razza, etnia,
  religione and orientamento sessuale.
- **Groups not on the list**: identità di genere, sesso, appartenenza cantonale, professione, età, disabilità and
  convinzioni politiche. The last is plural, as is idiomatic; German has the singular "Überzeugung".
- **Group wording**: "Schwarze Menschen" became "persone nere". "Angehörige der Roma/Jenischen" became "membri della
  comunità rom/jenisch" (the Swiss federal usage "jenisch"). "Freikirche" became "chiesa cristiana libera".
  "Lehrpersonen" became "docenti" (Ticino usage). The cantonal groups use paired forms ("le zurighesi e gli zurighesi"),
  mirroring the German.

## Unsure / please check
1. **"a Aarau"**: euphony would prefer "ad Aarau". Place surfaces are bare strings and the frames add "a", so this
   can't be fixed per place without renderer support. It affects only `aa`, and the form is grammatical but marked.
2. **pub_post_fam** reads "…sul suo profilo sui social media, rivolto alla sua famiglia («Cara famiglia, …») e letto
   anche dai suoi genitori e dai suoi fratelli". German "lesen" (present) became the participle "letto" to avoid a
   relative "che" that could attach to "profilo". **pub_forum_fam** ("in un commento in un forum …, che ha firmato
   con …") has the same masculine-noun attachment issue, but only "commento" makes sense as the thing signed.
3. **"lettera alla redazione"** for "Leserbrief" (gender-neutral; "lettera di un lettore" would clash with female
   actors).
4. **The ver framing** is "Quale sentenza pronuncerebbe un tribunale svizzero?". German "Wie lautet das Urteil" is
   indicative; the conditional fits a hypothetical case better.
5. **Mitarbeitende (`cont_office`)** became "collaboratori", the generic masculine. The count (25) and the "suo reparto"
   relationship are kept, so the setting stays contested.
