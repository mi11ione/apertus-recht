from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
STATUTES = ROOT / "statutes"


def statute_dirs():
    return sorted(p.parent for p in STATUTES.glob("*/statute.yaml"))


def design_dirs():
    return sorted(p.parent for p in STATUTES.glob("*/design.yaml"))


@pytest.fixture(scope="session")
def d261():
    from statute_twins.generator import design
    return design.load(STATUTES / "stgb_261bis")


@pytest.fixture(scope="session")
def scenarios261(d261):
    from statute_twins.generator import build
    return build.build_scenarios(d261)
