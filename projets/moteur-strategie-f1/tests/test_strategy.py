import numpy as np
import pytest

from f1engine.strategy import best_strategies, stint_cost


def test_stint_cost_matches_lap_by_lap_sum():
    offsets, slopes = np.array([[0.3, -0.2]]), np.array([[0.05, 0.11]])
    S = stint_cost(offsets, slopes, 30)
    for c in range(2):
        for n in (0, 1, 7, 30):
            brute = sum(offsets[0, c] + slopes[0, c] * age for age in range(n))
            assert S[0, c, n] == pytest.approx(brute)


def test_no_degradation_means_extra_stop_gains_nothing():
    offsets, slopes = np.array([[0.0, 0.0]]), np.array([[0.0, 0.0]])
    b1, _ = best_strategies(offsets, slopes, ["MEDIUM", "HARD"], 50, n_stops=1)
    b2, _ = best_strategies(offsets, slopes, ["MEDIUM", "HARD"], 50, n_stops=2)
    assert b1[0] == pytest.approx(0) and b2[0] == pytest.approx(0)


def test_equal_compounds_split_the_race_evenly():
    offsets, slopes = np.array([[0.0, 0.0]]), np.array([[0.1, 0.1]])
    _, (s1,) = best_strategies(offsets, slopes, ["MEDIUM", "HARD"], 50, n_stops=1)
    _, (s2,) = best_strategies(offsets, slopes, ["MEDIUM", "HARD"], 51, n_stops=2)
    assert s1.stint_laps == (25, 25)
    assert s2.stint_laps == (17, 17, 17)


def test_two_compound_rule_is_enforced():
    # Le tendre est bien meilleur partout, mais il faut quand même utiliser un 2e composé.
    offsets, slopes = np.array([[-1.0, 0.0]]), np.array([[0.01, 0.01]])
    _, (s1,) = best_strategies(offsets, slopes, ["SOFT", "HARD"], 40, n_stops=1, min_stint=8)
    _, (s2,) = best_strategies(offsets, slopes, ["SOFT", "HARD"], 40, n_stops=2, min_stint=8)
    assert set(s1.compounds) == {"SOFT", "HARD"} and min(s1.stint_laps) == 8
    assert len(set(s2.compounds)) >= 2


def test_breakeven_grows_with_degradation():
    comps = ["MEDIUM", "HARD"]
    gains = []
    for slope in (0.02, 0.05, 0.10):
        o, s = np.array([[0.0, 0.0]]), np.array([[slope, slope]])
        b1, _ = best_strategies(o, s, comps, 60, 1)
        b2, _ = best_strategies(o, s, comps, 60, 2)
        gains.append(b1[0] - b2[0])
    assert gains[0] < gains[1] < gains[2]
    # 1 arrêt 30/30 contre 2 arrêts 20/20/20, pente 0,1 : 0,1 * (2*435 - 3*190) = 30 s
    assert gains[2] == pytest.approx(30.0)
