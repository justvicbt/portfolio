"""Calculs d'écarts (lap delta), dégradation et lien entre conditions et rythme.

Quatre écarts, du moins au plus coûteux en données :
- A. écart au leader à la fin de chaque tour (calculé à l'ETL, transform.positions_and_gaps) ;
- B. duel entre deux pilotes : différence de temps au tour et son cumul, plus l'écart réel
  sur la ligne (lap_time_delta) ;
- C. écart à une référence : temps corrigé du carburant moins le temps prédit par le modèle
  de dégradation du projet 1 (pace_residuals) ;
- D. delta le long du tour, à partir de la télémétrie du tour le plus rapide (telemetry_delta).

Chaque résultat qui sert à un enseignement porte ses effectifs et son intervalle. Quand les
données ne suffisent pas, les fonctions renvoient `None` avec la raison, au lieu d'un chiffre.
"""
import warnings
from dataclasses import dataclass

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from f1engine.degradation import RaceFit, fit_race, summarize
from scipy import stats

from .config import MIN_STINT_LAPS
from .text import num, plural


@dataclass
class Verdict:
    """Résultat d'un calcul sensible aux données : soit une valeur, soit la raison de l'absence."""
    value: object = None
    reason: str | None = None

    @property
    def ok(self) -> bool:
        return self.reason is None


# --- B. Duel ---------------------------------------------------------------------------------

def lap_time_delta(laps: pd.DataFrame, a: str, b: str) -> pd.DataFrame:
    """Tour par tour, A contre B. Positif : A plus lent (ou derrière).

    - delta_s : temps au tour de A moins celui de B ;
    - cum_delta_s : cumul de delta_s depuis le 1er tour (les tours sans temps sont sautés) ;
    - gap_s : écart réel sur la ligne à la fin du tour (passage de A moins passage de B).
    Sans tour manquant, gap_s(n) = écart au départ + cum_delta_s(n).
    Attend driver, lap_number, lap_time_s, lap_end.
    """
    cols = ["lap_number", "lap_time_s", "lap_end"]
    da = laps.loc[laps["driver"] == a, cols].set_index("lap_number")
    db = laps.loc[laps["driver"] == b, cols].set_index("lap_number")
    df = da.join(db, lsuffix="_a", rsuffix="_b", how="inner").sort_index()
    df["delta_s"] = df["lap_time_s_a"] - df["lap_time_s_b"]
    df["cum_delta_s"] = df["delta_s"].cumsum()
    df["gap_s"] = (df["lap_end_a"] - df["lap_end_b"]).dt.total_seconds()
    return df[["lap_time_s_a", "lap_time_s_b", "delta_s", "cum_delta_s", "gap_s"]].reset_index()


def mean_difference(diff: pd.Series, min_n: int = 5, level: float = 0.95) -> Verdict:
    """Moyenne d'une série d'écarts avec intervalle de Student. Les tours consécutifs ne sont
    pas indépendants : l'intervalle est un peu trop étroit (signalé dans l'interface)."""
    d = diff.dropna().to_numpy(dtype=float)
    if len(d) < min_n:
        return Verdict(reason=f"{plural(len(d), 'tour comparable', 'tours comparables')}, il en faut au moins {min_n}")
    m, se = d.mean(), d.std(ddof=1) / np.sqrt(len(d))
    h = stats.t.ppf(0.5 + level / 2, len(d) - 1) * se
    return Verdict({"mean": m, "low": m - h, "high": m + h, "n": len(d)})


# --- D. Télémétrie ---------------------------------------------------------------------------

def telemetry_delta(tel_a: pd.DataFrame, tel_b: pd.DataFrame, n_points: int = 400) -> pd.DataFrame:
    """Écart de temps cumulé le long du tour, A moins B (positif : A a perdu du temps).

    La distance OpenF1 est intégrée depuis la vitesse et sort 1 à 1,5 % trop courte, de façon
    différente pour chaque tour. On la ramène donc en fraction du tour (0 à 1) avant de comparer.
    Attend t_s et distance_m pour chaque tour.
    """
    grid = np.linspace(0, 1, n_points)

    def time_at(tel):
        tel = tel.sort_values("t_s")
        frac = tel["distance_m"].to_numpy() / tel["distance_m"].max()
        return np.interp(grid, frac, tel["t_s"].to_numpy())

    return pd.DataFrame({"lap_fraction": grid, "delta_s": time_at(tel_a) - time_at(tel_b)})


# --- Dégradation (projet 1) et C. résidus de rythme --------------------------------------------

def identifiable(fit: RaceFit) -> bool:
    exog = fit.result.model.exog
    return np.linalg.matrix_rank(exog) == exog.shape[1]


def degradation(clean: pd.DataFrame, trend: bool = False) -> Verdict:
    """Modèle de dégradation du projet 1 (A sans tendance, B avec tendance de course)."""
    try:
        with warnings.catch_warnings():   # le rang est vérifié juste après, explicitement
            warnings.simplefilter("ignore")
            fit = fit_race(clean, estimate_trend=trend)
    except (ValueError, IndexError) as exc:
        return Verdict(reason=f"aucun composé n'a 30 tours propres et 3 relais ({exc})")
    if not identifiable(fit):
        return Verdict(reason="régression non identifiable (trop peu de relais ou de composés distincts)")
    return Verdict((fit, summarize(fit, clean[clean["compound"].isin(fit.compounds)])))


def negative_slopes(table: pd.DataFrame) -> list[str]:
    """Composés dont la pente est négative et son intervalle entièrement sous 0.

    Un pneu ne rajeunit pas : une telle pente veut dire que la piste s'améliore plus vite que
    le pneu ne s'use (piste qui sèche, gomme déposée), et la pente ne mesure plus l'usure.
    """
    return table.loc[table["slope_ci_high"] < 0, "compound"].tolist()


def pace_residuals(fit: RaceFit, clean: pd.DataFrame) -> pd.DataFrame:
    """Calcul C : temps corrigé moins temps prédit (pilote, composé, âge du pneu).

    Négatif : tour plus rapide que ce que le modèle attend pour ce pilote et ce pneu.
    """
    used = clean[clean["compound"].isin(fit.compounds)].copy()
    used["residual_s"] = fit.result.resid.reindex(used.index)
    return used.dropna(subset=["residual_s"])


def stint_slopes(clean: pd.DataFrame, min_laps: int = MIN_STINT_LAPS) -> pd.DataFrame:
    """Pente de chaque relais (temps corrigé ~ âge du pneu), IC 95 % de Student.

    Indépendante du modèle de course : elle ne compare pas les relais entre eux.
    Les relais trop courts sont gardés avec `slope_s_per_lap` vide et la raison.
    """
    rows = []
    for (driver, stint), g in clean.groupby(["driver", "stint_number"]):
        row = {"driver": driver, "stint_number": int(stint), "compound": g["compound"].iloc[0],
               "n_laps": len(g), "first_lap": int(g["lap_number"].min()), "last_lap": int(g["lap_number"].max()),
               "slope_s_per_lap": np.nan, "ci_low": np.nan, "ci_high": np.nan, "note": None}
        if len(g) < min_laps or g["tyre_age"].nunique() < 3:
            row["note"] = f"{plural(len(g), 'tour propre', 'tours propres')}, il en faut {min_laps}"
        else:
            res = stats.linregress(g["tyre_age"].astype(float), g["fuel_corr_s"])
            h = stats.t.ppf(0.975, len(g) - 2) * res.stderr
            row.update(slope_s_per_lap=res.slope, ci_low=res.slope - h, ci_high=res.slope + h)
        rows.append(row)
    return pd.DataFrame(rows)


# --- Conditions et rythme --------------------------------------------------------------------

@dataclass
class TemperatureEffect:
    coef_s_per_deg: float          # spécification sans tendance de course
    ci: tuple[float, float]
    coef_with_trend: float         # même chose avec un terme linéaire en numéro de tour
    ci_with_trend: tuple[float, float]
    corr_temp_lap: float           # corrélation température de piste / numéro de tour
    temp_range: tuple[float, float]
    n_laps: int
    n_stints: int
    conclusive: bool
    reasons: list[str]


def temperature_effect(clean: pd.DataFrame, compounds: list[str], reference: str,
                       min_range_c: float = 2.0, max_corr: float = 0.7) -> Verdict:
    """Effet de la température de piste sur le temps corrigé, dans une course.

    temps_corrigé ~ pilote + composé + composé x âge + b x température_piste   (projet 1 + température)
    Erreurs clusterisées par relais, loi de Student. On refait l'estimation avec un terme en
    numéro de tour : si b change beaucoup ou perd sa significativité, la température ne se
    distingue pas de l'évolution de la piste et du carburant pendant la course.

    Concluant seulement si : la température varie d'au moins `min_range_c`, sa corrélation
    avec le numéro de tour reste sous `max_corr`, et les deux intervalles excluent 0 avec le
    même signe.
    """
    df = clean[clean["compound"].isin(compounds)].dropna(subset=["track_temp_c"])
    if len(df) < 30 or df["stint_id"].nunique() < 3:
        return Verdict(reason=f"{plural(len(df), 'tour propre', 'tours propres')} avec une mesure de température, il en faut au moins 30")
    lo, hi = df["track_temp_c"].min(), df["track_temp_c"].max()
    if hi - lo < min_range_c:
        return Verdict(reason=f"la température de piste ne varie que de {num(hi - lo)} °C sur les tours propres")
    base = (f"fuel_corr_s ~ C(driver) + C(compound, Treatment('{reference}'))"
            f" + C(compound, Treatment('{reference}')):tyre_age + track_temp_c")
    fits = [smf.ols(f, data=df).fit(cov_type="cluster", cov_kwds={"groups": df["stint_id"]}, use_t=True)
            for f in (base, base + " + lap_number")]
    (c1, c2), (ci1, ci2) = [f.params["track_temp_c"] for f in fits], \
        [tuple(f.conf_int().loc["track_temp_c"]) for f in fits]
    corr = float(np.corrcoef(df["track_temp_c"], df["lap_number"])[0, 1])

    reasons = []
    if abs(corr) > max_corr:
        reasons.append(f"la température suit le déroulé de la course (corrélation de {num(corr, 2, True)} avec le numéro"
                       " de tour), donc on ne peut pas la séparer du carburant et de la gomme déposée")
    for name, (a, b) in (("sans tendance", ci1), ("avec tendance", ci2)):
        if a <= 0 <= b:
            reasons.append(f"l'intervalle {name} contient 0")
    if np.sign(c1) != np.sign(c2):
        reasons.append("le signe change quand on ajoute la tendance de course")
    return Verdict(TemperatureEffect(c1, ci1, c2, ci2, corr, (lo, hi), len(df), df["stint_id"].nunique(),
                                     not reasons, reasons))


def rain_comparison(laps: pd.DataFrame) -> pd.DataFrame:
    """Descriptif : temps médian des tours en vert, avec et sans pluie signalée, par composé.

    Aucune correction (pilote, pneu, carburant) : simple lecture des données.
    """
    df = laps[(laps["track_status"] == "GREEN") & laps["rain"].notna() & laps["lap_time_s"].notna()
              & (laps["is_pit_in_lap"] == 0) & (laps["is_pit_out_lap"] == 0) & (laps["lap_number"] > 1)]
    return (df.groupby(["compound", "rain"])["lap_time_s"].agg(["median", "size"])
            .rename(columns={"median": "median_lap_s", "size": "n_laps"}).reset_index())
