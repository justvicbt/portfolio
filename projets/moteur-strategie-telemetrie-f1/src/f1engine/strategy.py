"""Simulateur 1 arrêt contre 2 arrêts : seuil de perte aux stands sous lequel 2 arrêts deviennent plus rapides."""
from dataclasses import dataclass
from itertools import product

import numpy as np

from .degradation import RaceFit


@dataclass
class Strategy:
    compounds: tuple[str, ...]
    stint_laps: tuple[int, ...]
    race_time_s: float  # hors pertes aux stands, relatif au niveau de base

    def describe(self) -> str:
        return " - ".join(f"{c[0]}{n}" for c, n in zip(self.compounds, self.stint_laps))


def stint_cost(offsets: np.ndarray, slopes: np.ndarray, total_laps: int) -> np.ndarray:
    """Coût S(c, n) = n * offset_c + slope_c * n (n - 1) / 2 d'un relais de n tours neufs, pour n = 0..total_laps."""
    n = np.arange(total_laps + 1)
    return n * offsets[..., None] + slopes[..., None] * (n * (n - 1) / 2)


def _plans(total_laps: int, n_stops: int, min_stint: int) -> np.ndarray:
    """Toutes les découpes de la course en n_stops + 1 relais d'au moins min_stint tours."""
    if n_stops == 1:
        first = np.arange(min_stint, total_laps - min_stint + 1)
        return np.column_stack([first, total_laps - first])
    n1, n2 = np.meshgrid(np.arange(min_stint, total_laps), np.arange(min_stint, total_laps), indexing="ij")
    n3 = total_laps - n1 - n2
    keep = n3 >= min_stint
    return np.column_stack([n1[keep], n2[keep], n3[keep]])


def best_strategies(offsets, slopes, compounds, total_laps, n_stops, min_stint=8):
    offsets, slopes = np.atleast_2d(offsets), np.atleast_2d(slopes)
    S = stint_cost(offsets, slopes, total_laps)              # (D, C, N+1)
    plans = _plans(total_laps, n_stops, min_stint)            # (P, n_stops+1)
    best = np.full(offsets.shape[0], np.inf)
    best_plan = [None] * offsets.shape[0]
    for combo in product(range(len(compounds)), repeat=n_stops + 1):
        if len(set(combo)) < 2:                                # règle des deux composés
            continue
        total = sum(S[:, c, plans[:, i]] for i, c in enumerate(combo))   # (D, P)
        idx = total.argmin(axis=1)
        val = total[np.arange(len(idx)), idx]
        better = val < best
        best = np.where(better, val, best)
        for d in np.flatnonzero(better):
            best_plan[d] = (combo, plans[idx[d]])
    strategies = [Strategy(tuple(compounds[c] for c in combo), tuple(int(x) for x in plan), float(b))
                  for (combo, plan), b in zip(best_plan, best)]
    return best, strategies


@dataclass
class Comparison:
    circuit: str
    model: str
    one_stop: Strategy
    two_stop: Strategy
    breakeven_s: float
    breakeven_draws: np.ndarray

    def prob_two_stop_faster(self, pit_loss_s) -> np.ndarray:
        return (self.breakeven_draws[:, None] > np.atleast_1d(pit_loss_s)[None, :]).mean(axis=0)

    def total_times(self, pit_loss_s: float) -> tuple[float, float]:
        return self.one_stop.race_time_s + pit_loss_s, self.two_stop.race_time_s + 2 * pit_loss_s


def compare(fit: RaceFit, n_draws: int = 2000, min_stint: int = 8, seed: int = 42) -> Comparison:
    mean, cov, compounds = fit.pace_params()
    k = len(compounds)
    N = fit.total_laps

    b1, (s1,) = best_strategies(mean[None, :k], mean[None, k:], compounds, N, 1, min_stint)
    b2, (s2,) = best_strategies(mean[None, :k], mean[None, k:], compounds, N, 2, min_stint)

    # Incertitude : tirages dans la loi normale estimée par la régression (covariance clusterisée).
    rng = np.random.default_rng(seed)
    draws = rng.multivariate_normal(mean, cov, size=n_draws, method="svd")
    d1, _ = best_strategies(draws[:, :k], draws[:, k:], compounds, N, 1, min_stint)
    d2, _ = best_strategies(draws[:, :k], draws[:, k:], compounds, N, 2, min_stint)
    return Comparison(fit.circuit, fit.model, s1, s2, float(b1[0] - b2[0]), d1 - d2)
