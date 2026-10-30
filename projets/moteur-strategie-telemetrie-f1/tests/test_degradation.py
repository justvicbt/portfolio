import numpy as np
import pandas as pd

from f1engine.degradation import fit_race, usable_compounds

TRUE_SLOPES = {"SOFT": 0.09, "MEDIUM": 0.05, "HARD": 0.02}
TRUE_OFFSETS = {"SOFT": -0.6, "MEDIUM": 0.0, "HARD": 0.4}


def synthetic_race(seed: int = 0, trend: float = 0.0) -> pd.DataFrame:
    """60 tours, 12 pilotes, deux relais chacun, bruit de 0,25 s."""
    rng = np.random.default_rng(seed)
    rows = []
    for d in range(12):
        driver_level = rng.normal(0, 0.5)
        first, second = [("SOFT", "HARD"), ("MEDIUM", "HARD"), ("MEDIUM", "SOFT")][d % 3]
        pit = int(rng.integers(20, 35))
        for lap in range(2, 61):
            compound, stint, age = (first, 1, lap - 1) if lap <= pit else (second, 2, lap - pit - 1)
            t = (80 + driver_level + TRUE_OFFSETS[compound] + TRUE_SLOPES[compound] * age
                 + trend * lap + rng.normal(0, 0.25))
            rows.append({"circuit": "Test", "total_laps": 60, "driver": f"D{d}", "lap_number": lap,
                         "stint_id": f"D{d}-{stint}", "compound": compound, "tyre_age": age,
                         "fuel_corr_s": t})
    return pd.DataFrame(rows)


def test_model_recovers_known_slopes():
    fit = fit_race(synthetic_race())
    ci = fit.result.conf_int()
    for compound, slope in TRUE_SLOPES.items():
        name = fit.slope_name(compound)
        assert abs(fit.result.params[name] - slope) < 0.015, compound
        assert 0 < ci.loc[name, 1] - ci.loc[name, 0] < 0.05, compound
    for compound in ("SOFT", "HARD"):
        assert abs(fit.result.params[fit.offset_name(compound)] - TRUE_OFFSETS[compound]) < 0.25


def test_model_b_absorbs_a_residual_race_trend():
    race = synthetic_race(seed=1, trend=-0.02)   # piste qui s'améliore, non corrigée
    biased = fit_race(race).result.params
    fit_b = fit_race(race, estimate_trend=True)
    assert abs(fit_b.result.params["lap_number"] - (-0.02)) < 0.006
    # Sans terme de tendance, la pente du dur est biaisée vers le bas ; avec, elle est retrouvée.
    name = fit_b.slope_name("HARD")
    assert biased[name] < TRUE_SLOPES["HARD"] - 0.01
    assert abs(fit_b.result.params[name] - TRUE_SLOPES["HARD"]) < 0.015


def test_compounds_with_too_few_laps_are_dropped():
    race = synthetic_race()
    few_soft = race[(race["compound"] != "SOFT") | (race["stint_id"] == race.loc[race["compound"] == "SOFT", "stint_id"].iloc[0])]
    assert usable_compounds(few_soft) == ["MEDIUM", "HARD"]


def test_pace_params_put_reference_compound_at_zero():
    fit = fit_race(synthetic_race())
    mean, cov, compounds = fit.pace_params()
    ref = compounds.index("MEDIUM")
    assert mean[ref] == 0 and cov[ref, ref] == 0
    assert np.allclose(cov, cov.T)
