"""Gold engine: verdict and deciding element, computed from the statute YAML and a scenario's element facts.

    facts = {"act_date": "2023-03-15", "characteristic": "sexual_orientation", "paragraph": "abs1", "setting": "public"}
    g = gold(statute, facts)   # Gold(verdict="convict", deciding_element="all_met", ...)

Rules (generic over any statute file):
  * ``date``         met iff the date is on or after ``in_force_from``.
  * ``covered_set``  met iff the value has a ``covered_from`` date and the date element it depends on is on or after it.
  * ``enum``/``bool`` met, failed or contested as declared for the value.
An element may declare a `default` value, used when a scenario's facts do not mention it (A18: the dignity
threshold of Abs. 4 defaults to met, so scenarios that stipulate it keep their gold); a defaulted element that is met
is left out of the trace. Elements are checked in YAML order. Any failed element -> "acquit", decided by the first failed element. Otherwise any
contested element -> "open" (label "contested"). Otherwise "convict" (deciding element "all_met").
The engine never sees scenario text; it only reads the slot facts the generator recorded.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field

from ..statute import Statute

MET, FAILED, CONTESTED = "met", "failed", "contested"


@dataclass(frozen=True)
class Gold:
    verdict: str                    # convict | acquit | open
    deciding_element: str           # element id, or "all_met"
    label: str                      # settled | contested
    reason: str = "convict"         # "convict" or "<deciding element>:<code>"; codes: not_in_force (date),
                                    # not_listed / not_yet_covered (covered_set), failed (enum), contested
    failing: tuple = ()
    contested: tuple = ()
    trace: tuple = field(default=(), compare=False)

    def as_dict(self) -> dict:
        return dict(verdict=self.verdict, deciding_element=self.deciding_element, label=self.label, reason=self.reason,
                    failing=list(self.failing), contested=list(self.contested), trace=[dict(t) for t in self.trace])


class FactError(ValueError):
    pass


def _d(v) -> dt.date:
    if isinstance(v, dt.date):
        return v
    try:
        return dt.date.fromisoformat(str(v))
    except ValueError as e:
        raise FactError(f"not an ISO date: {v!r}") from e


def element_status(statute: Statute, eid: str, facts: dict) -> tuple[str, list[str]]:
    status, auth, _ = _status(statute, eid, facts)
    return status, auth


def _status(statute: Statute, eid: str, facts: dict) -> tuple[str, list[str], str]:
    """(status, authorities, reason code) of one element."""
    e = statute.element(eid)
    if eid not in facts and e.raw.get("default") is None:
        raise FactError(f"missing fact for element {eid!r}")
    v = facts.get(eid, e.raw.get("default"))
    if e.kind == "date":
        ok = e.in_force_from is None or _d(v) >= e.in_force_from
        return (MET, e.authority, "") if ok else (FAILED, e.authority, "not_in_force")
    if v not in e.values:
        raise FactError(f"{eid}: unknown value {v!r} (known: {sorted(e.values)})")
    spec = e.values[v]
    auth = spec.get("authority") or e.authority
    if e.kind == "covered_set":
        cf = spec.get("covered_from")
        if cf is None:
            return FAILED, auth, "not_listed"
        return (MET, auth, "") if _d(facts[e.depends_on]) >= cf else (FAILED, auth, "not_yet_covered")
    s = spec.get("satisfied")
    status = {True: MET, False: FAILED, "contested": CONTESTED}[s]
    return status, auth, {MET: "", FAILED: "failed", CONTESTED: "contested"}[status]


def gold(statute: Statute, facts: dict) -> Gold:
    trace, failing, contested, codes = [], [], [], {}
    for e in statute.elements:
        status, auth, code = _status(statute, e.id, facts)
        if e.id not in facts and status == MET:
            continue                     # a defaulted element that is met does not appear in the derivation
        v = facts.get(e.id, e.raw.get("default"))
        trace.append((("element", e.id), ("value", str(v)), ("status", status), ("authority", tuple(auth))))
        codes[e.id] = code
        if status == FAILED:
            failing.append(e.id)
        elif status == CONTESTED:
            contested.append(e.id)
    if failing:
        d = failing[0]
        return Gold("acquit", d, "settled", f"{d}:{codes[d]}", tuple(failing), tuple(contested), tuple(trace))
    if contested:
        d = contested[0]
        return Gold("open", d, "contested", f"{d}:contested", (), tuple(contested), tuple(trace))
    return Gold("convict", "all_met", "settled", "convict", (), (), tuple(trace))
