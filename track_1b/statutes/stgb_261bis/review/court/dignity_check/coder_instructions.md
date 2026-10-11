# Dignity check: coder instructions (A20)

You get `packet.txt`: short, neutral summaries of real public statements about a group of people (the facts only).
For each block `[Dxx]`, decide one question: does the statement, read in its whole context, reach the threshold of
Art. 261bis Abs. 4 StGB (first half) as the Federal Supreme Court defines it in BGE 131 IV 23 E. 3?

Regeste (binding test, verbatim):

> Als Herabsetzung oder Diskriminierung im Sinne von Art. 261bis Abs. 4 StGB erscheinen alle Verhaltensweisen, durch
> welche den Angehörigen einer Bevölkerungsgruppe aufgrund ihrer Rasse, Ethnie oder Religion die Gleichwertigkeit als
> menschliche Wesen oder die Gleichberechtigung in Bezug auf die Menschenrechte abgesprochen oder zumindest in Frage
> gestellt werden. Die Freiheit der Meinungsäusserung verbietet es, in der politischen Auseinandersetzung eine
> Herabsetzung oder Diskriminierung im Sinne von Art. 261bis Abs. 4 StGB leichthin zu bejahen. Den Tatbestand erfüllt
> nicht bereits, wer über eine geschützte Bevölkerungsgruppe etwas Unvorteilhaftes äussert, solange die Kritik im
> Gesamtzusammenhang sachlich bleibt und sich auf objektive Umstände stützt (E. 3).

Values (corresponding to the three values of the `dignity` element in `statute.yaml`):

- `degrading`: the statement denies, or at least calls into question, the members' equal worth as human beings or their
  equal human rights.
- `not_degrading`: unfavourable, offensive or crude, but it does not reach that threshold (for example, it targets a
  concrete incident, an institution or a doctrine, or it is a personal insult that does not attack the person's
  equal worth because of the protected characteristic: Art. 177 StGB rather than Art. 261bis Abs. 4, which also covers
  degrading a single person for that reason).
- `borderline`: the facts given do not let you decide; say which missing fact would decide it.

Judge only this element. Assume every other element (publicity, intent, protected characteristic) is met; do not
reason about them. Do not guess which court decided or what it decided. Work alone; do not search for the cases.

Output: a JSON object `{ "Dxx": {"value": "...", "reason": "one or two sentences tied to the Regeste"} , ... }`
covering every block.
