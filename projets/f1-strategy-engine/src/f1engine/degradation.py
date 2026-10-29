"""Modèle de dégradation des pneus : temps au tour (corrigé du carburant) contre âge du pneu.

Modèle principal, une régression OLS par course :

    temps_corrigé ~ effet pilote + écart par composé + pente par composé × âge du pneu

- L'effet fixe pilote absorbe le niveau de chaque voiture.
- Les erreurs standard sont "clusterisées" par relais : les tours d'un même relais
  ne sont pas indépendants (ils partagent le même train de pneus, le même trafic...).
  Les intervalles utilisent une loi de Student (G - 1 degrés de liberté) : avec une
  vingtaine de relais par composé, la loi normale les rendrait trop étroits.
- Les pentes sont en secondes perdues par tour d'âge du pneu.

Variante B (`estimate_trend=True`) : on ajoute un terme linéaire en numéro de tour.
Il capte ce que la correction carburant n'a pas retiré (erreur sur l'hypothèse,
évolution de la piste). C'est identifiable parce que l'âge du pneu repart à zéro
à chaque arrêt alors que le numéro de tour continue.

Contrôle de robustesse : effet fixe par relais au lieu de l'effet pilote. La pente n'est
alors identifiée qu'à l'intérieur des relais, sans comparer des relais entre eux.
"""
from dataclasses import dataclass

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from sqlalchemy.engine import Engine

from .cleaning import fuel_corrected
from .config import DRY_COMPOUNDS, FuelModel
from .db import read_sql

MIN_LAPS = 30
MIN_STINTS = 3

CLEAN_LAPS_SQL = """
SELECT s.circuit, s.session_key, s.total_laps, d.acronym AS driver, l.lap_number, l.stint_number,
       l.compound, l.tyre_age, l.lap_time_s
FROM laps l
JOIN sessions s USING (session_key)
JOIN drivers d ON d.session_key = l.session_key AND d.driver_number = l.driver_number
WHERE l.is_clean = 1
"""


@dataclass
class RaceFit:
    circuit: str
    total_laps: int
    compounds: list[str]
    reference: str
    result: object  # statsmodels RegressionResults
    model: str = "A"

    def slope_name(self, compound: str) -> str:
        return f"C(compound, Treatment('{self.reference}'))[{compound}]:tyre_age"

    def offset_name(self, compound: str) -> str | None:
        if compound == self.reference:
            return None
        return f"C(compound, Treatment('{self.reference}'))[T.{compound}]"

    def pace_params(self) -> tuple[np.ndarray, np.ndarray, list[str]]:
        """Moyenne et covariance de (écarts par composé, pentes par composé), pour le simulateur.

        L'écart du composé de référence vaut 0 par construction (variance nulle).
        """
        names = [self.offset_name(c) for c in self.compounds] + [self.slope_name(c) for c in self.compounds]
        params, cov = self.result.params, self.result.cov_params()
        mean = np.array([params[n] if n else 0.0 for n in names])
        full = np.zeros((len(names), len(names)))
        idx = [i for i, n in enumerate(names) if n]
        kept = [names[i] for i in idx]
        full[np.ix_(idx, idx)] = cov.loc[kept, kept].to_numpy()
        return mean, full, self.compounds


def load_clean_laps(engine: Engine, fuel: FuelModel = FuelModel()) -> pd.DataFrame:
    df = read_sql(engine, CLEAN_LAPS_SQL)
    df = df[df["compound"].isin(DRY_COMPOUNDS)].copy()
    df["fuel_corr_s"] = fuel_corrected(df["lap_time_s"], df["lap_number"], df["total_laps"], fuel)
    df["stint_id"] = df["driver"] + "-" + df["stint_number"].astype(str)
    return df


def usable_compounds(race: pd.DataFrame) -> list[str]:
    """Composés avec assez de tours et de relais pour estimer une pente."""
    g = race.groupby("compound").agg(n_laps=("lap_number", "size"), n_stints=("stint_id", "nunique"))
    ok = g[(g["n_laps"] >= MIN_LAPS) & (g["n_stints"] >= MIN_STINTS)].index
    return [c for c in DRY_COMPOUNDS if c in ok]


def fit_race(race: pd.DataFrame, estimate_trend: bool = False) -> RaceFit:
    compounds = usable_compounds(race)
    if not compounds:
        raise ValueError(f"Pas assez de tours propres pour {race['circuit'].iloc[0]}")
    race = race[race["compound"].isin(compounds)]
    reference = "MEDIUM" if "MEDIUM" in compounds else compounds[0]
    formula = (f"fuel_corr_s ~ C(driver) + C(compound, Treatment('{reference}'))"
               f" + C(compound, Treatment('{reference}')):tyre_age")
    if estimate_trend:
        formula += " + lap_number"
    result = smf.ols(formula, data=race).fit(cov_type="cluster", cov_kwds={"groups": race["stint_id"]}, use_t=True)
    return RaceFit(race["circuit"].iloc[0], int(race["total_laps"].iloc[0]), compounds, reference, result,
                   model="B" if estimate_trend else "A")


def summarize(fit: RaceFit, race: pd.DataFrame) -> pd.DataFrame:
    ci = fit.result.conf_int(alpha=0.05)
    rows = []
    for c in fit.compounds:
        sub = race[race["compound"] == c]
        s, o = fit.slope_name(c), fit.offset_name(c)
        rows.append({
            "model": fit.model, "circuit": fit.circuit, "compound": c, "n_laps": len(sub), "n_stints": sub["stint_id"].nunique(),
            "max_tyre_age": int(sub["tyre_age"].max()),
            "slope_s_per_lap": fit.result.params[s], "slope_ci_low": ci.loc[s, 0], "slope_ci_high": ci.loc[s, 1],
            "offset_vs_ref_s": fit.result.params[o] if o else 0.0,
            "offset_ci_low": ci.loc[o, 0] if o else 0.0, "offset_ci_high": ci.loc[o, 1] if o else 0.0,
            "reference": fit.reference,
            "residual_trend_s_per_lap": fit.result.params.get("lap_number", np.nan),
        })
    return pd.DataFrame(rows)


def stint_fe_slopes(race: pd.DataFrame, compounds: list[str]) -> pd.Series:
    """Pentes avec effet fixe par relais (contrôle de robustesse)."""
    race = race[race["compound"].isin(compounds)]
    res = smf.ols("fuel_corr_s ~ C(stint_id) + C(compound):tyre_age", data=race).fit(
        cov_type="cluster", cov_kwds={"groups": race["stint_id"]})
    return pd.Series({c: res.params[f"C(compound)[{c}]:tyre_age"] for c in compounds})


def fit_all(engine: Engine, fuel: FuelModel = FuelModel(),
            estimate_trend: bool = False) -> tuple[dict[str, RaceFit], pd.DataFrame]:
    laps = load_clean_laps(engine, fuel)
    fits, tables = {}, []
    for circuit, race in laps.groupby("circuit"):
        fit = fit_race(race, estimate_trend)
        fits[circuit] = fit
        tables.append(summarize(fit, race))
    return fits, pd.concat(tables, ignore_index=True)


def robustness(engine: Engine, fuel: FuelModel = FuelModel(), sec_per_kg_grid=(0.02, 0.03, 0.04)) -> pd.DataFrame:
    """Sensibilité des pentes à l'hypothèse carburant et à la spécification du modèle."""
    rows = []
    for k in sec_per_kg_grid:
        laps = load_clean_laps(engine, FuelModel(fuel.start_kg, k))
        for circuit, race in laps.groupby("circuit"):
            fit = fit_race(race)
            fe = stint_fe_slopes(race, fit.compounds)
            for c in fit.compounds:
                rows.append({"circuit": circuit, "compound": c, "fuel_sec_per_kg": k,
                             "slope_driver_fe": fit.result.params[fit.slope_name(c)],
                             "slope_stint_fe": fe[c]})
    return pd.DataFrame(rows)
