# Reviewer consent and AI-use template

The scenarios have **no data subjects**: every scenario is synthetic, generated from templates; actors are generic ("a
man", "a student"); no real person, name, address or identifier occurs in them (PII gate in `statute-twins qc`). The
validation records cite real, public court decisions by docket and URL; their notes name no person. Court
decisions used for validation are public-domain judgments (Swiss Copyright Act Art. 5), referenced by id and URL; the
fact summaries written for the dignity check (A20) leave out roles, party names, exact dates and small places, so that
no anonymised person can be re-identified.

Versions 1.0 to 1.7 of the dataset involved no human reviewers: every label was produced by reproducible agent runs
(Claude agents, and Qwen-SEA-LION-v4-32B as an independent model). This form
is for anyone who extends the set with human reviewers or human-written scenarios; each such person signs it before
reviewing. The signed forms are kept by the team and are not published; reviewers appear in the dataset only
under a pseudonym (R1, R2, …).

---
**Consent to act as a reviewer for the dataset "Apertus-Recht" (statute-twins, Art. 261bis StGB)**

1. I review synthetic legal scenarios, model outputs and machine translations and record my judgement (agree /
   disagree with the computed label, cause, free-text note). If I write scenarios, they are my own work, describe no
   real case or person, contain no personal data, and I license them under CDLA-Permissive-2.0.
2. **Content.** I have been told that the material describes discriminatory and degrading statements about groups
   (for example, a group called vermin or second-class people). I may skip any item and stop at any time without giving
   a reason.
3. My judgements are published under the pseudonym ________ in the dataset (licence CDLA-Permissive-2.0) and may be
   reproduced, modified and redistributed under that licence. My name is not published.
4. **AI use.** I understand and agree that: (a) the scenarios, translations and first-pass annotations I review were
   produced with AI systems (Claude agents, and Qwen-SEA-LION-v4-32B as an independent annotator and judge; Apertus
   models are evaluated, not used to label); (b) my judgements may be
   used to evaluate and to train AI systems, including by third parties, as permitted by the licence; (c) I will not
   enter personal data of anyone into the review notes.
5. I may withdraw at any time through the contact below; my judgements are removed from the next version. I understand
   that copies already published under CDLA-Permissive-2.0 can be redistributed by others and cannot be recalled.
6. **Data protection.** Controller: team 444 (maintainers of github.com/mi11ione/apertus-recht); contact: an issue or a
   private security advisory on that repository. Legal basis: my consent (Swiss revDSG). My name and this signed form
   are kept only to document consent, separately from the dataset, and deleted two years after the last version that
   contains my judgements; I may ask for access or deletion through the same contact.
7. I receive no compensation / compensation of ________.

Name: ______________________  Date: ____________  Signature: ______________________
