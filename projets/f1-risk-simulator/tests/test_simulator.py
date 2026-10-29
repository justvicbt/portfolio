import numpy as np
import pytest

from f1risk.params import CircuitParams, SeasonParams
from f1risk.simulator import MAX_WINDOW, NONE, SC, Assumptions, Draws, Duel, draw, final_gap, run, summarize

# Medium : pente 0,08 s/tour. Dur : 0,2 s plus rapide neuf, pente 0,04. Piste : -0,01 s/tour.
CP = CircuitParams(
    circuit="Test", total_laps=60, compounds=["MEDIUM", "HARD"],
    pace_mean=np.array([0.0, -0.2, 0.08, 0.04, -0.01]), pace_cov=np.diag([0.0, 0.01, 1e-4, 1e-4, 1e-6]),
    lap_noise_s=0.4, pit_losses=np.array([20.0, 21.0, 22.0, 23.0, 30.0]),
    rejoin_gaps=np.array([0.5, 2.0, 5.0, np.inf]),
)
SP = SeasonParams(sc_events=10, vsc_events=10, exposure_laps=1000, sc_ratios=np.array([0.5, 0.6]),
                  vsc_ratios=np.array([0.7]), traffic_cost_s=0.4, traffic_cost_se=0.05)
DUEL = Duel(stop_lap=20, gap_s=1.0, rival_age=19, old="MEDIUM", new="HARD")
NO_VARIANCE = Assumptions(sc_scale=0, loss_spread=0, traffic_scale=0, noise_scale=0, param_uncertainty=False)


def draws(n=4000, seed=0, a=Assumptions(), duel=DUEL):
    return draw(CP, SP, duel, n, np.random.default_rng(seed), a)


def test_without_variance_matches_hand_calculation():
    # Perte aux stands fixée à la médiane : 22 s pour les deux.
    # Undercut, rival au tour suivant (tours 20, 21, 22) :
    #   A : 0,08x19 + 22 | -0,2 (dur neuf, âge 0) | -0,2 + 0,04 = 23,16
    #   R : 0,08x19      | 0,08x20 + 22           | -0,2         = 24,92
    #   écart final = 1,0 + 23,16 - 24,92 = -0,76 : A passe devant.
    # Rival qui reste 3 tours de plus : A = 22,96 ; R = 1,52 + 1,60 + 1,68 + 1,76 + 22 - 0,2 = 28,36.
    d = draws(n=10, a=NO_VARIANCE)
    assert final_gap(CP, DUEL, d, 0, 1) == pytest.approx(np.full(10, -0.76))
    assert final_gap(CP, DUEL, d, 0, 3) == pytest.approx(np.full(10, 1.0 + 22.96 - 28.36))
    assert final_gap(CP, DUEL, d, 1, 1) == pytest.approx(np.full(10, 1.0))   # même tour : rien ne change


def test_zero_safety_car_probability_equals_no_safety_car_case():
    with_zero = draws(a=Assumptions(sc_scale=0))
    forced = draws(a=Assumptions(sc_scale=1))   # mêmes tirages (même graine), puis on retire les SC
    forced.neutral[:] = NONE
    for stops in [(0, 1), (0, 3), (1, 1)]:
        assert final_gap(CP, DUEL, with_zero, *stops) == pytest.approx(final_gap(CP, DUEL, forced, *stops))


def test_faster_stop_never_hurts_the_attacker():
    d = draws()
    base = final_gap(CP, DUEL, d, 0, 1)
    d.loss_a = d.loss_a - 1.5
    assert np.all(final_gap(CP, DUEL, d, 0, 1) <= base + 1e-9)


def test_safety_car_between_the_two_stops_favours_the_rival():
    d = draws(n=10, a=NO_VARIANCE)
    clean = final_gap(CP, DUEL, d, 0, 1)
    d.neutral[:, 1] = SC     # SC au tour 21 : A s'est arrêté, R pas encore
    d.sc_ratio[:] = 0.5
    with_sc = final_gap(CP, DUEL, d, 0, 1)
    # R ne perd plus que 11 s au lieu de 22 et les écarts sont gelés : A reste derrière.
    assert np.all(with_sc > clean + 5) and np.all(with_sc > 0)


def test_track_evolution_cancels_out_between_the_two_cars():
    flat = run(CP, SP, DUEL, 2000, np.random.default_rng(3), Assumptions(evo_scale=0))
    steep = run(CP, SP, DUEL, 2000, np.random.default_rng(3), Assumptions(evo_scale=50))
    for name in flat:
        assert flat[name] == pytest.approx(steep[name])


def test_pit_loss_is_not_noised_twice():
    # La perte mesurée contient déjà le bruit des tours d'entrée et de sortie :
    # le bruit tiré sur ces tours-là ne doit pas compter.
    d = draws(n=10, a=NO_VARIANCE)
    base = final_gap(CP, DUEL, d, 0, 1)
    d.noise_a[:, [0, 1]] = 5.0   # tours d'entrée et de sortie de A (arrêt au tour N)
    d.noise_r[:, [1, 2]] = -5.0  # tours d'entrée et de sortie de R (arrêt au tour N+1)
    assert final_gap(CP, DUEL, d, 0, 1) == pytest.approx(base)
    d.noise_a[:, 2] = 1.0        # 1er tour lancé de A en pneus neufs : compte normalement
    assert final_gap(CP, DUEL, d, 0, 1) == pytest.approx(base + 1.0)


def test_traffic_only_costs_the_attacker_time():
    d = draws(a=Assumptions(traffic_scale=0))
    d_traffic = draws(a=Assumptions(traffic_scale=1))
    assert np.all(final_gap(CP, DUEL, d_traffic, 0, 1) >= final_gap(CP, DUEL, d, 0, 1) - 1e-9)


def test_bigger_initial_gap_lowers_success():
    p = [summarize(g, run(CP, SP, Duel(20, g, 19, "MEDIUM", "HARD"), 4000, np.random.default_rng(1))
                   ["undercut_rival_responds"])["p_success"] for g in (0.5, 1.5, 3.0)]
    assert p[0] > p[1] > p[2]


def test_summary_tail_is_below_the_mean():
    gaps = np.random.default_rng(0).normal(0, 3, 10_000)
    s = summarize(1.0, gaps)
    assert s["cvar5_gain_s"] < s["p5_gain_s"] < s["mean_gain_s"]
    assert s["p_success"] == pytest.approx(0.5, abs=0.02)


def test_draw_shapes():
    d = draws(n=7)
    assert isinstance(d, Draws) and d.n == 7
    assert d.noise_a.shape == d.neutral.shape == (7, MAX_WINDOW)
