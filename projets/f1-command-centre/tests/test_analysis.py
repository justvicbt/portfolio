"""Calculs d'écarts et d'analyse, sur des données construites à la main au résultat connu."""
import numpy as np
import pandas as pd
import pytest

from f1cc.analysis import (lap_time_delta, mean_difference, negative_slopes, stint_slopes, telemetry_delta,
                           temperature_effect)
from f1cc.strategy import best_lap_statement, season_params_from_p2
from f1cc.config import P2_RESULTS

T0 = pd.Timestamp("2025-01-01T12:00:00Z")


def duel_laps(times_a, times_b, grid_gap=0.5):
    rows = []
    for drv, times, start in (("AAA", times_a, 0.0), ("BBB", times_b, grid_gap)):
        t = T0 + pd.Timedelta(seconds=start)
        for n, lt in enumerate(times, 1):
            t_end = t + pd.Timedelta(seconds=lt)
            rows.append({"driver": drv, "lap_number": n, "lap_time_s": lt, "lap_end": t_end})
            t = t_end
    return pd.DataFrame(rows)


def test_lap_delta_and_cumulative_match_gap_on_the_line():
    a, b = [91.0, 90.5, 90.2, 92.0], [90.0, 90.0, 90.0, 90.0]
    d = lap_time_delta(duel_laps(a, b), "AAA", "BBB")
    assert np.allclose(d["delta_s"], [1.0, 0.5, 0.2, 2.0])
    assert np.allclose(d["cum_delta_s"], [1.0, 1.5, 1.7, 3.7])
    # A part 0,5 s devant B : écart sur la ligne = -0,5 + cumul.
    assert np.allclose(d["gap_s"], d["cum_delta_s"] - 0.5)


def test_missing_lap_time_is_skipped_in_cumulative_but_not_in_gap():
    laps = duel_laps([91.0, 91.0, 91.0], [90.0, 90.0, 90.0], grid_gap=0.0)
    laps.loc[(laps["driver"] == "AAA") & (laps["lap_number"] == 2), "lap_time_s"] = np.nan
    d = lap_time_delta(laps, "AAA", "BBB")
    assert np.isnan(d.loc[1, "delta_s"])
    assert np.isclose(d.loc[2, "cum_delta_s"], 2.0)    # tour 2 sauté
    assert np.isclose(d.loc[2, "gap_s"], 3.0)          # l'écart sur la ligne, lui, est complet


def test_mean_difference_interval_and_minimum_sample():
    v = mean_difference(pd.Series([0.1, 0.3, 0.2, 0.4, 0.0]))
    assert v.ok and np.isclose(v.value["mean"], 0.2)
    # IC de Student à 4 degrés de liberté : t = 2,776, écart-type 0,158
    assert np.isclose(v.value["high"] - 0.2, 2.776 * 0.1581 / np.sqrt(5), atol=1e-3)
    assert not mean_difference(pd.Series([0.1, 0.2])).ok


def test_telemetry_delta_constant_speed():
    # A boucle le tour en 100 s, B en 98 s, vitesses constantes : l'écart croît linéairement jusqu'à 2 s.
    ta = pd.DataFrame({"t_s": np.linspace(0, 100, 101), "distance_m": np.linspace(0, 5000, 101)})
    tb = pd.DataFrame({"t_s": np.linspace(0, 98, 50), "distance_m": np.linspace(0, 4950, 50)})  # distance 1 % courte
    d = telemetry_delta(ta, tb, n_points=11)
    assert np.allclose(d["delta_s"], np.linspace(0, 2, 11))


def clean_stints(slope=0.05, n=12, stints=4):
    rows = []
    for s in range(stints):
        for age in range(n):
            rows.append({"driver": f"D{s % 2}", "stint_number": s + 1, "compound": "MEDIUM", "tyre_age": age,
                         "lap_number": s * n + age + 2, "fuel_corr_s": 80 + slope * age,
                         "stint_id": f"D{s % 2}-{s + 1}"})
    return pd.DataFrame(rows)


def test_stint_slope_recovers_known_slope_and_skips_short_stints():
    df = clean_stints(slope=0.05)
    df = pd.concat([df, pd.DataFrame([{"driver": "D9", "stint_number": 1, "compound": "HARD", "tyre_age": a,
                                       "lap_number": a, "fuel_corr_s": 81.0, "stint_id": "D9-1"} for a in range(3)])])
    out = stint_slopes(df, min_laps=8)
    long = out.dropna(subset=["slope_s_per_lap"])
    assert len(long) == 4 and np.allclose(long["slope_s_per_lap"], 0.05)
    short = out[out["driver"] == "D9"].iloc[0]
    assert np.isnan(short["slope_s_per_lap"]) and "3 tours propres" in short["note"]


def test_negative_slope_is_flagged():
    t = pd.DataFrame({"compound": ["MEDIUM", "HARD"], "slope_ci_high": [-0.1, 0.02]})
    assert negative_slopes(t) == ["MEDIUM"]


def temperature_data(effect, corr_with_laps, seed=0):
    """Temps = 80 + 0,05 x âge + effect x température + bruit."""
    rng = np.random.default_rng(seed)
    df = clean_stints(n=15, stints=6)
    df["driver"] = "D" + (df["stint_number"] % 3).astype(str)
    df["stint_id"] = df["driver"] + "-" + df["stint_number"].astype(str)
    if corr_with_laps:
        df["track_temp_c"] = 40 - 0.1 * df["lap_number"]          # la piste refroidit avec la course
    else:
        df["track_temp_c"] = 30 + rng.uniform(0, 8, len(df))      # variations indépendantes du déroulé
    df["fuel_corr_s"] = 80 + 0.05 * df["tyre_age"] + effect * df["track_temp_c"] + rng.normal(0, 0.05, len(df))
    return df


def test_temperature_effect_is_conclusive_when_independent_of_race_progress():
    v = temperature_effect(temperature_data(0.05, corr_with_laps=False), ["MEDIUM"], "MEDIUM")
    assert v.ok and v.value.conclusive
    assert v.value.ci[0] < 0.05 < v.value.ci[1]


def test_temperature_effect_is_not_conclusive_when_confounded_with_laps():
    v = temperature_effect(temperature_data(0.05, corr_with_laps=True), ["MEDIUM"], "MEDIUM")
    assert v.ok and not v.value.conclusive
    assert any("déroulé de la course" in r for r in v.value.reasons)


def test_temperature_effect_needs_variation():
    df = temperature_data(0.0, corr_with_laps=False)
    df["track_temp_c"] = 35.0 + 0.001 * np.arange(len(df)) / len(df)
    v = temperature_effect(df, ["MEDIUM"], "MEDIUM")
    assert not v.ok and "ne varie que" in v.reason


def test_best_lap_only_named_when_beyond_monte_carlo_noise():
    clear = pd.DataFrame({"stop_lap": [10, 11], "p_success": [0.60, 0.40], "mc_se": [0.007, 0.007]})
    assert best_lap_statement(clear).startswith("Le tour 10 ressort")
    close = pd.DataFrame({"stop_lap": [10, 11], "p_success": [0.50, 0.49], "mc_se": [0.007, 0.007]})
    assert best_lap_statement(close).startswith("Aucun tour ne se détache")
    # Au-delà du bruit, mais moins de 5 points : pas de tour désigné.
    small = pd.DataFrame({"stop_lap": [10, 11], "p_success": [0.54, 0.51], "mc_se": [0.007, 0.007]})
    assert best_lap_statement(small).startswith("Aucun tour à privilégier")


@pytest.mark.skipif(not (P2_RESULTS / "season_parameters.csv").exists(), reason="résultats du projet 2 absents")
def test_season_parameters_read_from_project_2_results():
    sp = season_params_from_p2()
    assert (sp.sc_events, sp.vsc_events, sp.exposure_laps) == (13, 13, 1421)
    assert len(sp.sc_ratios) == 36 and len(sp.vsc_ratios) == 11      # « 36 arrêts », « 11 arrêts » dans le CSV
    assert np.isclose(np.median(sp.sc_ratios), 0.6552, atol=1e-3)
    assert np.isclose(sp.traffic_cost_s, 0.3381) and np.isclose(sp.traffic_cost_se, 0.025)
