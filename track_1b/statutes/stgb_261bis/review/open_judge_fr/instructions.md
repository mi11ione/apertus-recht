# Judging free-text answers about Art. 261bis StGB

Each entry shows a short scenario, the question a user asked an assistant, the assistant's answer, and the acceptance
criterion for a correct answer (derived from the statute and BGE 130 IV 111). Judge the ANSWER against the CRITERION.

For each entry give:
- `verdict_expressed`: what the answer tells the user: "punishable", "not_punishable", "depends" (says it turns on facts
  not given), or "none" (no clear answer).
- `pass`: true if the answer meets the acceptance criterion (right conclusion; for "open" items: identifies the
  decisive, fact-dependent question and does not assert a verdict as certain), else false.
- `reason_ok`: true if the answer's stated legal reason is correct and names the element that decides the case
  (publicity, the closed list of characteristics, the date of the act), false if it gives a wrong or no reason.
- `misleads`: true if a layperson following the answer would be wrongly told their conduct is (or is not) punishable.
- `note`: at most 20 words.

Do not reward length or style; judge the legal content. Decide each entry by reading it.
