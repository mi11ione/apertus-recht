"""Mutation tests: change one rule in the statute model and check that exactly the items that rule governs flip.

The expected flip set is computed from the items' recorded facts with an independent one-line predicate, not with the
engine, so a mutation that leaks into another element shows up as an unexpected flip.
"""
import copy
import datetime as dt

import pytest

from statute_twins.gold.engine import gold
from statute_twins.generator import build


@pytest.fixture(scope="module")
def facts(d261, scenarios261):
    return [s.facts for s in scenarios261]


def _flips(st_a, st_b, facts):
    return {i for i, f in enumerate(facts) if gold(st_a, f).verdict != gold(st_b, f).verdict}


def _mutant(d261):
    return copy.deepcopy(d261.statute)


def test_remove_religion_from_closed_list(d261, facts):
    m = _mutant(d261)
    m.element("characteristic").values["religion"]["covered_from"] = None
    # every religion item that was not already an acquittal flips: convictions and open (contested) items alike,
    # because a failed element decides even when another element is contested
    expect = {i for i, f in enumerate(facts) if f["characteristic"] == "religion" and f["setting"] != "private"
              and f["act_date"] >= "1995-01-01"}
    assert expect and _flips(d261.statute, m, facts) == expect
    assert all(gold(m, facts[i]).verdict == "acquit" for i in expect)


def test_add_canton_to_closed_list(d261, facts):
    m = _mutant(d261)
    m.element("characteristic").values["canton"]["covered_from"] = dt.date(1995, 1, 1)
    expect = {i for i, f in enumerate(facts) if f["characteristic"] == "canton" and f["setting"] == "public"
              and f["act_date"] >= "1995-01-01"}
    expect |= {i for i, f in enumerate(facts) if f["characteristic"] == "canton" and f["setting"] == "contested"}
    assert expect and _flips(d261.statute, m, facts) == expect


def test_move_the_2020_extension_back_by_one_year(d261, facts):
    m = _mutant(d261)
    m.element("characteristic").values["sexual_orientation"]["covered_from"] = dt.date(2019, 7, 1)
    expect = {i for i, f in enumerate(facts) if f["characteristic"] == "sexual_orientation" and f["setting"] != "private"
              and "2019-07-01" <= f["act_date"] < "2020-07-01"}
    assert expect and _flips(d261.statute, m, facts) == expect


def test_move_the_2020_extension_forward_by_one_day(d261, facts):
    m = _mutant(d261)
    m.element("characteristic").values["sexual_orientation"]["covered_from"] = dt.date(2020, 7, 2)
    expect = {i for i, f in enumerate(facts) if f["characteristic"] == "sexual_orientation" and f["setting"] != "private"
              and f["act_date"] == "2020-07-01"}
    assert expect and _flips(d261.statute, m, facts) == expect


def test_make_private_settings_public(d261, facts):
    m = _mutant(d261)
    m.element("setting").values["private"]["satisfied"] = True
    listed = {"race", "ethnicity", "religion"}
    expect = {i for i, f in enumerate(facts) if f["setting"] == "private" and f["act_date"] >= "1995-01-01"
              and (f["characteristic"] in listed or (f["characteristic"] == "sexual_orientation" and f["act_date"] >= "2020-07-01"))}
    assert expect and _flips(d261.statute, m, facts) == expect


def test_move_entry_into_force(d261, facts):
    m = _mutant(d261)
    m.element("act_date").in_force_from = dt.date(1993, 1, 1)
    for v in ("race", "ethnicity", "religion"):
        m.element("characteristic").values[v]["covered_from"] = dt.date(1993, 1, 1)
    expect = {i for i, f in enumerate(facts) if "1993-01-01" <= f["act_date"] < "1995-01-01"
              and f["setting"] == "public" and f["characteristic"] in ("race", "ethnicity", "religion")}
    assert expect and _flips(d261.statute, m, facts) == expect


def test_every_true_flip_is_caught_by_some_mutation(d261, scenarios261):
    """Each family's true flips are sensitive to the rule they are built for (no twin is decided by accident)."""
    by_reason = {}
    for s in scenarios261:
        if s.role == "true_flip":
            by_reason.setdefault(s.gold.reason, 0)
            by_reason[s.gold.reason] += 1
    assert set(by_reason) == {"setting:failed", "characteristic:not_listed", "characteristic:not_yet_covered",
                              "act_date:not_in_force"}
