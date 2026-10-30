"""Les pentes de ce projet doivent retrouver celles publiées par le moteur de stratégie (même code, mêmes courses)."""
import pandas as pd
import pytest

from f1cc.config import DEFAULT_DB, ROOT

P1_RESULTS = ROOT.parent / "moteur-strategie-telemetrie-f1" / "docs" / "results" / "degradation.csv"


@pytest.mark.skipif(not DEFAULT_DB.exists() or not P1_RESULTS.exists(),
                    reason="base de ce projet ou résultats du moteur de stratégie absents")
def test_slopes_match_project_1(monkeypatch):
    monkeypatch.delenv("F1CC_DB", raising=False)
    from f1cc import data
    from f1cc.analysis import degradation
    from f1cc.config import get_engine

    engine = get_engine()
    p1 = pd.read_csv(P1_RESULTS)
    p1 = p1[p1["model"] == "A"]
    common = data.sessions(engine).query("circuit in @p1.circuit")
    assert len(common) == 3   # Sakhir, Hungaroring, Monza
    mine = pd.concat([degradation(data.clean_laps(engine, sk)).value[1] for sk in common["session_key"]])
    m = mine.merge(p1, on=["circuit", "compound"], suffixes=("", "_p1"))
    assert len(m) == len(p1[p1["circuit"].isin(common["circuit"])])
    assert (m["n_laps"] == m["n_laps_p1"]).all()
    # Même tolérance que le simulateur d'undercut : OpenF1 a révisé l'âge de départ de quelques trains de pneus.
    assert (m["slope_s_per_lap"] - m["slope_s_per_lap_p1"]).abs().max() < 0.002
