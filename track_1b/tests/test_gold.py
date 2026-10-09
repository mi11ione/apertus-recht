"""Gold engine: hand-checked cases, boundaries, and properties over the full fact space."""
import itertools

import pytest

from statute_twins import statute as S
from statute_twins.gold.engine import FactError, gold

from conftest import STATUTES


@pytest.fixture(scope="module")
def st():
    return S.load(STATUTES / "stgb_261bis")


def F(date="2023-03-15", ch="religion", para="abs1", setting="public"):
    return dict(act_date=date, characteristic=ch, paragraph=para, setting=setting)


@pytest.mark.parametrize("facts, verdict, reason", [
    (F(), "convict", "convict"),
    (F(setting="private"), "acquit", "setting:failed"),
    (F(setting="contested"), "open", "setting:contested"),
    (F(ch="canton"), "acquit", "characteristic:not_listed"),
    (F(ch="gender_identity"), "acquit", "characteristic:not_listed"),
    (F(ch="sex"), "acquit", "characteristic:not_listed"),
    (F(ch="sexual_orientation"), "convict", "convict"),
    (F(ch="sexual_orientation", date="2019-03-15"), "acquit", "characteristic:not_yet_covered"),
    (F(ch="sexual_orientation", date="2020-06-30"), "acquit", "characteristic:not_yet_covered"),
    (F(ch="sexual_orientation", date="2020-07-01"), "convict", "convict"),
    (F(ch="race", date="2019-03-15"), "convict", "convict"),
    (F(ch="race", date="1995-01-01"), "convict", "convict"),
    (F(ch="race", date="1994-12-31"), "acquit", "act_date:not_in_force"),
    # a failed element decides even when another is contested
    (F(ch="canton", setting="contested"), "acquit", "characteristic:not_listed"),
    (F(ch="sexual_orientation", date="2019-03-15", setting="private"), "acquit", "characteristic:not_yet_covered"),
])
def test_cases(st, facts, verdict, reason):
    g = gold(st, facts)
    assert (g.verdict, g.reason) == (verdict, reason)
    assert g.label == ("contested" if verdict == "open" else "settled")


def test_unknown_values_raise(st):
    with pytest.raises(FactError):
        gold(st, F(ch="nationality"))
    with pytest.raises(FactError):
        gold(st, F(date="März 2023"))
    with pytest.raises(FactError):
        gold(st, {"act_date": "2023-01-01"})


DATES = ["1990-01-01", "1994-12-31", "1995-01-01", "2019-12-31", "2020-06-30", "2020-07-01", "2026-01-01"]


def test_properties_over_the_full_fact_space(st):
    chars = list(st.element("characteristic").values)
    n = 0
    for date, ch, para, setting in itertools.product(DATES, chars, ["abs1", "abs2", "abs4"], ["public", "private", "contested"]):
        g = gold(st, F(date, ch, para, setting))
        n += 1
        cf = st.element("characteristic").values[ch]["covered_from"]
        listed_then = cf is not None and date >= cf.isoformat()
        expect_fail = date < "1995-01-01" or not listed_then or setting == "private"
        if expect_fail:
            assert g.verdict == "acquit"
        elif setting == "contested":
            assert g.verdict == "open"
        else:
            assert g.verdict == "convict"
        # the paragraph never decides in this model (all three modelled paragraphs require publicity)
        assert g.deciding_element != "paragraph"
        # privacy alone can only remove a conviction, never create one
        if setting == "private":
            assert g.verdict == "acquit"
    assert n == len(DATES) * len(chars) * 9
