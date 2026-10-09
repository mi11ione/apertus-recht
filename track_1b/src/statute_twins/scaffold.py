"""`statute-twins new <id>`: scaffold a statute folder that builds out of the box.

The scaffold encodes a toy offence with two elements so that every moving part is visible: one enum element decided by
a setting slot, one date element, one twin family with a true flip and a placebo. Replace the toy content with the
real statute (see docs/add-a-statute.md), pin the sources with `statute-twins pin`, and the generic tests in
tests/test_all_statutes.py cover the new folder automatically.
"""
from __future__ import annotations

from pathlib import Path

STATUTE = """# {sid}: element model. Replace the toy elements with the real ones; pin every source with `statute-twins pin` and
# put its text hash under text_sha256 (tests/test_sources.py checks it).
schema: statute-twins/v1
id: {sid}
version: 0.1.0
citation: {{de: "Art. X StGB"}}
title: {{de: "TODO: title of the offence"}}
scope_note: TODO - which paragraphs and elements are modelled, which are fixed in every scenario.
sources:
  toy_rule:
    kind: statute
    cite: "Art. X StGB (TODO: pin with statute-twins pin)"
elements:
  - id: act_date
    kind: date
    label: {{de: Tatzeitpunkt}}
    in_force_from: 2000-01-01
    authority: [toy_rule]
    fail_reason: The act predates the entry into force.
  - id: setting
    kind: enum
    label: {{de: Öffentlichkeit}}
    authority: [toy_rule]
    values:
      public:  {{satisfied: true}}
      private: {{satisfied: false}}
    fail_reason: The act was not public.
"""

DESIGN = """schema: statute-twins-design/v1
statute: {sid}
generator_seed: 1
id_prefix: {prefix}
canary: "STATUTE-TWINS CANARY {sid}. This dataset is an evaluation set; it must not appear in training data."
sample_order: [date, setting, frame, actor]
render:
  order: [actor, date, setting]
acceptance:
  convict: "Acceptable: concludes conviction under Art. X StGB. Unacceptable: concludes acquittal"
  acquit: "Acceptable: concludes no conviction, because {{why}}. Unacceptable: concludes conviction."
  open: "Acceptable: says the outcome depends on facts left open. Unacceptable: a categorical verdict."
  reasons:
    "setting:failed": "the act was not public"
    "act_date:not_in_force": "the act predates the entry into force"
  traps: {{}}
slots:
  frame: {{values: [F01, F02]}}
  actor: {{values: [m1, f1]}}
  date:
    values:
      d2010: {{facts: {{act_date: 2010-06-15}}, precision: month, tags: [in_force]}}
      d2020: {{facts: {{act_date: 2020-06-15}}, precision: month, tags: [in_force]}}
      d1990: {{facts: {{act_date: 1990-06-15}}, precision: month, tags: [before]}}
  setting:
    values:
      pub_square: {{facts: {{setting: public}}, tags: [public]}}
      pub_online: {{facts: {{setting: public}}, tags: [public]}}
      priv_home:  {{facts: {{setting: private}}, tags: [private]}}
families:
  SETTING:
    groups: 4
    base: {{setting: {{tags: [public]}}, date: {{tags: [in_force]}}}}
    variants:
      - {{slot: setting, filter: {{tags: [private]}}, expect: true_flip}}
      - {{slot: setting, filter: {{tags: [public]}}, expect: placebo}}
  DATE:
    groups: 4
    base: {{setting: {{tags: [public]}}, date: {{tags: [in_force]}}}}
    variants:
      - {{slot: date, filter: {{tags: [before]}}, expect: true_flip}}
"""

TEMPLATES = """lang: de
frames:
  F01: "Sachverhalt: {{Date}} handelte {{actor}} wie folgt: {{setting}}. {{Pron}} handelte vorsätzlich."
  F02: "Sachverhalt: Gemäss Anklage handelte {{actor}} {{date}} wie folgt: {{setting}}. {{Pron}} handelte vorsätzlich."
actors:
  m1: {{surface: "ein Mann", gender: m}}
  f1: {{surface: "eine Frau", gender: f}}
morphology:
  m: {{pron: er}}
  f: {{pron: sie}}
dates:
  d2010: "im Juni 2010"
  d2020: "im Juni 2020"
  d1990: "im Juni 1990"
settings:
  pub_square: "{{Pron}} tat es auf einem belebten Platz"
  pub_online: "{{Pron}} tat es in einem frei zugänglichen Online-Video"
  priv_home: "{{Pron}} tat es allein zu Hause"
"""

PROMPTS = """lang: de
rungs:
  R0: [plain]
  R1: [rule, tail]
rule: "\\n\\nPrüfe die Tatbestandsmerkmale von Art. X StGB: TODO."
tails:
  conv: " Würde ein Schweizer Gericht die Person verurteilen? Antworte mit Ja oder Nein."
  ver: " Wie lautet das Urteil eines Schweizer Gerichts? Antworte mit «schuldig» oder «nicht schuldig»."
plain:
  conv: "\\n\\nFrage: Würde ein Schweizer Gericht diese Person nach Art. X StGB verurteilen? Antworte mit Ja oder Nein."
  ver: "\\n\\nWie lautet das Urteil eines Schweizer Gerichts nach Art. X StGB? Antworte mit «schuldig» oder «nicht schuldig»."
framings:
  conv: {{answer_prefix: "", convict: "Ja", acquit: "Nein"}}
  ver:  {{answer_prefix: "Urteil:", convict: " schuldig", acquit: " nicht schuldig"}}
"""

ANSWERS = """lang: de
chosen:
  convict: "Ja. Alle Tatbestandsmerkmale sind erfüllt."
  "setting:failed": "Nein. Die Tat war nicht öffentlich."
  "act_date:not_in_force": "Nein. Die Tat ({{date}}) liegt vor dem Inkrafttreten."
rejected:
  convict: "Nein. Der Tatbestand ist nicht erfüllt."
  "setting:failed": "Ja. Der Tatbestand ist erfüllt."
  "act_date:not_in_force": "Ja. Der Tatbestand ist erfüllt."
traps: {{}}
"""


def scaffold(sid: str, root: Path) -> Path:
    d = Path(root) / sid
    if d.exists():
        raise FileExistsError(d)
    for sub in ("templates", "prompts", "answers"):
        (d / sub).mkdir(parents=True)
    prefix = sid.split("_", 1)[-1]
    (d / "statute.yaml").write_text(STATUTE.format(sid=sid), encoding="utf-8")
    (d / "design.yaml").write_text(DESIGN.format(sid=sid, prefix=prefix), encoding="utf-8")
    (d / "templates" / "de.yaml").write_text(TEMPLATES.format(), encoding="utf-8")
    (d / "prompts" / "de.yaml").write_text(PROMPTS.format(), encoding="utf-8")
    (d / "answers" / "de.yaml").write_text(ANSWERS.format(), encoding="utf-8")
    return d
