"""Les pentes du projet 2 doivent retrouver celles publiées par le projet 1 (même code)."""
import warnings

import pandas as pd
import pytest

from f1risk.config import DB_PATH, MAIN_CIRCUITS, ROOT

P1_RESULTS = ROOT.parent / "f1-strategy-engine" / "docs" / "results" / "degradation.csv"


@pytest.mark.skipif(not DB_PATH.exists() or not P1_RESULTS.exists(),
                    reason="base du projet 2 ou résultats du projet 1 absents")
def test_slopes_match_project_1():
    from f1engine.degradation import fit_race, summarize

    from f1risk.config import get_engine
    from f1risk.params import load_season

    data = load_season(get_engine())
    p1 = pd.read_csv(P1_RESULTS)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        mine = pd.concat([summarize(fit_race(race, trend), race)
                          for c in MAIN_CIRCUITS for trend in (False, True)
                          for race in [data.clean[data.clean["circuit"] == c]]])
    m = mine.merge(p1, on=["model", "circuit", "compound"], suffixes=("", "_p1"))
    assert len(m) == len(p1)
    assert (m["n_laps"] == m["n_laps_p1"]).all()
    # OpenF1 a révisé l'âge de départ de 5 trains de pneus depuis le projet 1 : petit écart toléré.
    assert (m["slope_s_per_lap"] - m["slope_s_per_lap_p1"]).abs().max() < 0.002
