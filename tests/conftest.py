"""Fixtures partagées."""

from pathlib import Path

import pytest

FIXTURE_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def fixture_html() -> str:
    """HTML de helia.nc capturé à un instant T (offline)."""
    return (FIXTURE_DIR / "etat-du-reseau.html").read_text(encoding="utf-8")


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "integration: tests réseau réels — exécutés uniquement en nightly CI (--run-integration)",
    )


def pytest_collection_modifyitems(config, items):
    if not config.getoption("--run-integration", default=False):
        skip = pytest.mark.skip(reason="Passer --run-integration pour exécuter les tests réseau")
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip)


def pytest_addoption(parser):
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="Inclut les tests d'intégration réseau",
    )
