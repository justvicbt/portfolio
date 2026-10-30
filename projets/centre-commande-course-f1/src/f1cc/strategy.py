"""Enseignements de stratégie (moteur de stratégie, simulateur d'undercut), calculés a posteriori sur toute la course."""
import re
from dataclasses import dataclass

import numpy as np
import pandas as pd
from f1engine.degradation import RaceFit
from f1engine.strategy import best_strategies
from f1risk.params import SeasonParams
from f1risk.simulator import Duel, draw, final_gap

from .config import P2_RESULTS, SEED
from .text import pct


@dataclass
class StopWindow:
    n_stops: int
    plan: str                    # meilleure stratégie aux paramètres estimés, ex. "M20 - H37"
    first_stop: int
    window: tuple[int, int]      # 10e et 90e centiles du 1er arrêt optimal sur les tirages
    draws_first_stop: np.ndarray


@dataclass
class StrategyInsight:
    one: StopWindow
    two: StopWindow
    pit_loss_s: float
    p_two_faster: float          # part des tirages où 2 arrêts battent 1 arrêt, à cette perte aux stands
    gain_two_s: float            # temps gagné par 2 arrêts aux paramètres estimés (négatif : perdu)
    n_draws: int


def stop_windows(fit: RaceFit, pit_loss_s: float, n_draws: int = 1000, min_stint: int = 8,
                 seed: int = SEED) -> StrategyInsight:
    mean, cov, compounds = fit.pace_params()
    k, n_laps = len(compounds), fit.total_laps
    rng = np.random.default_rng(seed)
    draws = rng.multivariate_normal(mean, cov, size=n_draws, method="svd")
    out = {}
    for n_stops in (1, 2):
        (best,), (strat,) = best_strategies(mean[None, :k], mean[None, k:], compounds, n_laps, n_stops, min_stint)
        times, strats = best_strategies(draws[:, :k], draws[:, k:], compounds, n_laps, n_stops, min_stint)
        first = np.array([s.stint_laps[0] for s in strats])
        lo, hi = np.percentile(first, [10, 90]).round().astype(int)
        out[n_stops] = (best, times, StopWindow(n_stops, strat.describe(), strat.stint_laps[0], (int(lo), int(hi)), first))
    (b1, t1, w1), (b2, t2, w2) = out[1], out[2]
    p_two = float(((t1 + pit_loss_s) > (t2 + 2 * pit_loss_s)).mean())
    return StrategyInsight(w1, w2, pit_loss_s, p_two, float((b1 + pit_loss_s) - (b2 + 2 * pit_loss_s)), n_draws)


def season_params_from_p2(results_dir=P2_RESULTS) -> SeasonParams:
    """Reconstitue les paramètres de saison du simulateur d'undercut à partir de ses CSV versionnés."""
    table = pd.read_csv(results_dir / "season_parameters.csv").set_index("parameter")
    ratios = pd.read_csv(results_dir / "neutralised_pit_losses.csv")
    ratios = ratios[ratios["kept"].astype(str) == "True"]

    def events(name):   # "13 SC / 1421 tours"
        m = re.match(r"(\d+) \w+ / (\d+) tours", table.loc[name, "detail"])
        return int(m.group(1)), int(m.group(2))

    sc, exposure = events("sc_rate_per_lap")
    vsc, _ = events("vsc_rate_per_lap")
    se = float(re.search(r"([\d.]+)$", table.loc["dirty_air_cost_s_per_lap", "detail"]).group(1))
    return SeasonParams(
        sc_events=sc, vsc_events=vsc, exposure_laps=exposure,
        sc_ratios=ratios.loc[ratios["status"] == "SC", "ratio"].to_numpy(),
        vsc_ratios=ratios.loc[ratios["status"] == "VSC", "ratio"].to_numpy(),
        traffic_cost_s=float(table.loc["dirty_air_cost_s_per_lap", "value"]), traffic_cost_se=se,
    )


def undercut_by_lap(cp, sp: SeasonParams, situations: pd.DataFrame, new_compound: str,
                    n_sims: int = 5000, seed: int = SEED) -> pd.DataFrame:
    """P(réussite) d'un undercut par situation réelle ; le rival répond au tour suivant avec le même composé."""
    rows = []
    for s in situations.itertuples():
        duel = Duel(stop_lap=int(s.stop_lap), gap_s=float(s.gap_s), rival_age=int(s.rival_age),
                    age_diff=int(s.attacker_age - s.rival_age), old=s.attacker_compound, new=new_compound,
                    rival_old=s.rival_compound, rival_new=new_compound)
        d = draw(cp, sp, duel, n_sims, np.random.default_rng(seed + int(s.stop_lap)))
        gaps = final_gap(cp, duel, d, 0, 1)
        p = float((gaps < 0).mean())
        gain = s.gap_s - gaps
        rows.append({"stop_lap": int(s.stop_lap), "gap_s": float(s.gap_s), "p_success": p,
                     "mc_se": float(np.sqrt(p * (1 - p) / n_sims)), "mean_gain_s": float(gain.mean()),
                     "p5_gain_s": float(np.percentile(gain, 5)), "n_sims": n_sims})
    return pd.DataFrame(rows)


def best_lap_statement(table: pd.DataFrame, min_margin: float = 0.05) -> str:
    """Désigne un tour seulement s'il bat le suivant au-delà du bruit Monte Carlo et d'au moins min_margin."""
    if table.empty:
        return ""
    t = table.sort_values("p_success", ascending=False).reset_index(drop=True)
    t["stop_lap"] = t["stop_lap"].astype(int)
    best = t.iloc[0]
    if len(t) == 1:
        return (f"Seul tour évaluable : tour {int(best.stop_lap)}, réussite dans {pct(best.p_success)} des scénarios"
                f" (erreur Monte Carlo ± {pct(2 * best.mc_se, 1)}).")
    second = t.iloc[1]
    margin = best.p_success - second.p_success
    noise = 2 * np.hypot(best.mc_se, second.mc_se)
    head = (f"le meilleur (tour {int(best.stop_lap)}, {pct(best.p_success)}) et le suivant"
            f" (tour {int(second.stop_lap)}, {pct(second.p_success)})")
    if margin <= noise:
        return f"Aucun tour ne se détache : {head} sont dans le bruit Monte Carlo (± {pct(noise, 1)})."
    if margin < min_margin:
        return (f"Aucun tour à privilégier : {head} ne diffèrent que de {pct(margin, 1)}. C'est au-delà du bruit "
                f"Monte Carlo (± {pct(noise, 1)}), mais sous le seuil de {pct(min_margin)} que je retiens, faute de "
                "connaître l'erreur propre du modèle.")
    return (f"Le tour {int(best.stop_lap)} ressort : réussite dans {pct(best.p_success)} des scénarios,"
            f" contre {pct(second.p_success)} au tour {int(second.stop_lap)}, le suivant"
            f" (écart de {pct(margin, 1)}, au-delà du bruit Monte Carlo de ± {pct(noise, 1)} et du seuil de "
            f"{pct(min_margin)}).")
