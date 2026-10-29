"""Monte Carlo d'un undercut entre deux voitures.

L'attaquant A roule `gap_s` secondes derrière le rival R au début du tour N.
On simule les tours N, N+1, ... jusqu'au tour de sortie du dernier des deux à s'arrêter,
et on mesure l'écart sur la ligne à la fin de ce tour. A réussit s'il est alors devant.

Temps d'un tour, pour chaque voiture (en secondes, à une constante commune près) :

    écart_composé + pente_composé x âge   (pneu usé avant l'arrêt, pneu neuf après)
    + évolution_piste x numéro du tour
    + bruit ~ N(0, sigma), sauf au tour d'entrée et au tour de sortie
    + perte aux stands, sur le tour d'entrée. Elle est mesurée comme
      (tour d'entrée + tour de sortie) - 2 x tour normal : c'est le surcoût par rapport
      à deux tours normaux, bruit de ces deux tours compris. Le tour de sortie est donc
      simulé comme un tour normal en pneus neufs, sans bruit supplémentaire.
    + coût de l'air sale, pour A, sur ses tours après le tour de sortie s'il ressort
      à moins de 1,5 s d'une autre voiture (le tour de sortie lui-même est déjà
      compris dans la perte aux stands mesurée)
    + écart de rythme entre pilotes, pour A

Safety car ou VSC déclenché au tour k de la fenêtre :
- toute voiture qui ne s'est pas encore arrêtée s'arrête au tour k, avec une perte
  réduite (perte normale x ratio observé sous neutralisation) ;
- à partir du tour k, les écarts sont gelés : seuls les arrêts comptent encore.
  On ne modélise pas le regroupement du peloton derrière la voiture de sécurité.

L'évolution de la piste touche les deux voitures sur les mêmes tours : dans ce
modèle elle s'annule exactement dans l'écart. Elle est gardée pour le montrer.
"""
from dataclasses import dataclass

import numpy as np

from .params import TRAFFIC_GAP_S, CircuitParams, SeasonParams

MAX_WINDOW = 5   # assez pour un rival qui s'arrête jusqu'à 3 tours après l'attaquant

NONE, SC, VSC = 0, 1, 2


@dataclass
class Duel:
    stop_lap: int                 # N : tour d'entrée aux stands de l'attaquant (undercut)
    gap_s: float                  # écart initial, attaquant derrière (> 0)
    rival_age: int                # âge des pneus du rival au début du tour N
    old: str                      # composé usé de l'attaquant
    new: str                      # composé chaussé à l'arrêt par l'attaquant
    age_diff: int = 0             # âge attaquant - âge rival
    rival_old: str | None = None  # par défaut, mêmes composés que l'attaquant
    rival_new: str | None = None
    pace_diff_s: float = 0.0      # rythme propre de A - rythme de R, par tour

    @property
    def attacker_age(self) -> int:
        return self.rival_age + self.age_diff


@dataclass
class Assumptions:
    """Leviers de l'analyse de sensibilité. Les valeurs par défaut = modèle de référence."""
    sc_scale: float = 1.0          # multiplie les taux de SC et de VSC
    loss_spread: float = 1.0       # 0 : perte aux stands fixée à la médiane ; 2 : dispersion doublée
    traffic_scale: float = 1.0     # multiplie le coût de l'air sale
    noise_scale: float = 1.0       # multiplie le bruit tour par tour
    evo_scale: float = 1.0         # multiplie l'évolution de la piste
    param_uncertainty: bool = True # tirer les paramètres estimés dans leur loi
    slope_shift: float = 0.0       # décale la pente du pneu usé, en écarts-types
    offset_shift: float = 0.0      # décale l'écart de rythme neuf - usé, en écarts-types
    sc_ratio: float | None = None  # remplace les ratios observés de perte sous neutralisation


@dataclass
class Draws:
    """Tirages Monte Carlo, partagés par tous les scénarios (comparaison appariée)."""
    pace: np.ndarray        # (n, 2k+1) : écarts, pentes, évolution
    noise_a: np.ndarray     # (n, MAX_WINDOW)
    noise_r: np.ndarray
    loss_a: np.ndarray      # (n,)
    loss_r: np.ndarray
    neutral: np.ndarray     # (n, MAX_WINDOW) : NONE, SC ou VSC déclenché pendant ce tour
    sc_ratio: np.ndarray    # (n,)
    vsc_ratio: np.ndarray
    traffic: np.ndarray     # (n,) coût de l'air sale si A ressort dans le trafic, sinon 0

    @property
    def n(self) -> int:
        return len(self.loss_a)


def _spread(values: np.ndarray, factor: float) -> np.ndarray:
    med = np.median(values)
    return med + factor * (values - med)


def draw(cp: CircuitParams, sp: SeasonParams, duel: Duel, n: int, rng: np.random.Generator,
         a: Assumptions = Assumptions()) -> Draws:
    mean = cp.pace_mean.copy()
    mean[cp.slope(duel.old)] += a.slope_shift * cp.se(cp.slope(duel.old))
    i, j = cp.offset(duel.new), cp.offset(duel.old)
    se_diff = np.sqrt(max(cp.pace_cov[i, i] + cp.pace_cov[j, j] - 2 * cp.pace_cov[i, j], 0.0))
    mean[i] += a.offset_shift * se_diff
    if a.param_uncertainty:
        pace = rng.multivariate_normal(mean, cp.pace_cov, size=n, method="svd")
    else:
        pace = np.repeat(mean[None, :], n, axis=0)
    pace[:, cp.evo] *= a.evo_scale

    # Taux de SC / VSC : loi a posteriori Gamma (Poisson, a priori de Jeffreys)
    if a.param_uncertainty:
        lam_sc = rng.gamma(sp.sc_events + 0.5, 1 / sp.exposure_laps, n)
        lam_vsc = rng.gamma(sp.vsc_events + 0.5, 1 / sp.exposure_laps, n)
    else:
        lam_sc, lam_vsc = np.full(n, sp.sc_rate), np.full(n, sp.vsc_rate)
    lam_sc, lam_vsc = lam_sc * a.sc_scale, lam_vsc * a.sc_scale
    u = rng.random((n, MAX_WINDOW))
    neutral = np.where(u < lam_sc[:, None], SC, np.where(u < (lam_sc + lam_vsc)[:, None], VSC, NONE))

    def ratios(observed):
        if a.sc_ratio is not None:
            return np.full(n, a.sc_ratio)
        return rng.choice(observed, n)

    if a.param_uncertainty:
        cost = rng.normal(sp.traffic_cost_s, sp.traffic_cost_se, n)
    else:
        cost = np.full(n, sp.traffic_cost_s)
    in_traffic = rng.choice(cp.rejoin_gaps, n) < TRAFFIC_GAP_S

    losses = _spread(cp.pit_losses, a.loss_spread)
    return Draws(
        pace=pace,
        noise_a=rng.normal(0, cp.lap_noise_s * a.noise_scale, (n, MAX_WINDOW)),
        noise_r=rng.normal(0, cp.lap_noise_s * a.noise_scale, (n, MAX_WINDOW)),
        loss_a=rng.choice(losses, n), loss_r=rng.choice(losses, n),
        neutral=neutral, sc_ratio=ratios(sp.sc_ratios), vsc_ratio=ratios(sp.vsc_ratios),
        traffic=np.where(in_traffic, cost * a.traffic_scale, 0.0),
    )


def final_gap(cp: CircuitParams, duel: Duel, d: Draws, attacker_stop: int, rival_stop: int) -> np.ndarray:
    """Écart A - R (s) à la fin du tour de sortie du dernier arrêt. Négatif : A est devant.

    attacker_stop, rival_stop : tour d'entrée aux stands, relatif à N (0 = tour N).
    """
    window = max(attacker_stop, rival_stop) + 2
    rows = np.arange(d.n)
    flagged = d.neutral[:, :window] != NONE
    k = np.where(flagged.any(axis=1), flagged.argmax(axis=1), window)   # 1er tour neutralisé
    kind = d.neutral[rows, np.minimum(k, window - 1)]
    ratio = np.where(kind == SC, d.sc_ratio, d.vsc_ratio)
    evo = d.pace[:, cp.evo]

    def lap_times(planned_stop, age0, old, new, loss, noise, extra_after_out):
        neutralised_first = planned_stop >= k          # pas encore arrêté quand la neutralisation arrive
        stop = np.minimum(planned_stop, k)
        loss = np.where(neutralised_first, loss * ratio, loss)
        total = np.zeros(d.n)
        for i in range(window):
            green = i < k
            used = d.pace[:, cp.offset(old)] + d.pace[:, cp.slope(old)] * (age0 + i)
            fresh = d.pace[:, cp.offset(new)] + d.pace[:, cp.slope(new)] * (i - stop - 1)
            tyre = np.where(i <= stop, used, fresh)
            # Pas de bruit au tour d'entrée ni au tour de sortie : la perte mesurée le contient déjà.
            lap_noise = np.where((i == stop) | (i == stop + 1), 0.0, noise[:, i])
            t = np.where(green, tyre + evo * (duel.stop_lap + i) + lap_noise + extra_after_out * (i >= stop + 2), 0)
            total += t + np.where(i == stop, loss, 0)
        return total

    t_a = lap_times(attacker_stop, duel.attacker_age, duel.old, duel.new, d.loss_a, d.noise_a,
                    d.traffic) + duel.pace_diff_s * np.minimum(k, window)
    t_r = lap_times(rival_stop, duel.rival_age, duel.rival_old or duel.old, duel.rival_new or duel.new,
                    d.loss_r, d.noise_r, 0.0)
    return duel.gap_s + t_a - t_r


SCENARIOS = {
    # nom : (tour d'arrêt de A, tour d'arrêt de R), relatifs à N
    "undercut_rival_responds": (0, 1),
    "undercut_rival_extends": (0, 3),
    "do_nothing": (1, 1),
}


def summarize(gap0: float, gaps: np.ndarray) -> dict:
    gain = gap0 - gaps                      # > 0 : A a repris du temps
    p5 = np.percentile(gain, 5)
    return {
        "p_success": float((gaps < 0).mean()),
        "mean_gain_s": float(gain.mean()),
        "p5_gain_s": float(p5),
        "cvar5_gain_s": float(gain[gain <= p5].mean()),   # moyenne des 5 % pires scénarios
    }


def run(cp: CircuitParams, sp: SeasonParams, duel: Duel, n: int, rng: np.random.Generator,
        a: Assumptions = Assumptions()) -> dict[str, np.ndarray]:
    """Écarts finaux pour chaque scénario, sur les mêmes tirages."""
    d = draw(cp, sp, duel, n, rng, a)
    return {name: final_gap(cp, duel, d, *stops) for name, stops in SCENARIOS.items()}
