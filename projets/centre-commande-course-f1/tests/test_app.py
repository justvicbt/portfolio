"""Chaque page se charge sans erreur (AppTest), sur la base de test et sur la vraie base si elle existe."""
import pytest
from streamlit.testing.v1 import AppTest

from f1cc.config import DEFAULT_DB, ROOT

APP = ROOT / "src" / "f1cc" / "app.py"
PAGES = ["vue_ensemble", "rythme_pneus", "meteo_piste", "duel", "strategie", "qualite"]


def run_page(page: str, circuit: str | None = None) -> AppTest:
    at = AppTest.from_file(str(APP), default_timeout=120)
    at.run()
    if page != PAGES[0]:
        at.switch_page(f"pages/{page}.py")
        at.run()
    if circuit is not None:
        at.sidebar.selectbox("circuit").set_value(circuit)
        at.run()
    return at


@pytest.mark.parametrize("page", PAGES)
def test_page_loads_on_synthetic_db(page, synthetic_db, monkeypatch):
    monkeypatch.setenv("F1CC_DB", str(synthetic_db))
    at = run_page(page)
    assert not at.exception, at.exception
    assert at.title


@pytest.mark.skipif(not DEFAULT_DB.exists(), reason="base réelle absente (lancer python -m f1cc etl)")
@pytest.mark.parametrize("page", PAGES)
def test_page_loads_on_real_db_for_every_race(page, monkeypatch):
    monkeypatch.delenv("F1CC_DB", raising=False)
    from f1cc import data
    from f1cc.config import get_engine
    for circuit in data.sessions(get_engine())["circuit"]:
        at = run_page(page, circuit)
        assert not at.exception, (circuit, at.exception)
