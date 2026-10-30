"""Paramètres du simulateur : par circuit et communs à la saison, avec exclusions possibles pour la validation."""
from dataclasses import dataclass

import numpy as np
import pandas as pd
import statsmodels.api as sm
from f1engine.cleaning import neutralisation_windows
from f1engine.config import DRY_COMPOUNDS, FuelModel
from f1engine.db import read_sql
from f1engine.degradation import RaceFit, fit_race, load_clean_laps

from .config import SQL_DIR

TRAFFIC_GAP_S = 1.5      # même seuil que le moteur de stratégie : en dessous, la voiture est dans l'air sale
OUTLIER_RATIO = 1.07     # même règle que le moteur de stratégie pour les tours aberrants
RATIO_RANGE = (0.0, 1.5) # ratios de perte sous neutralisation jugés plausibles

ALL_LAPS_SQL = """
SELECT s.circuit, s.session_key, s.total_laps, d.acronym AS driver, l.lap_number, l.date_start,
       l.lap_time_s, l.stint_number, l.compound, l.tyre_age, l.is_pit_in_lap, l.is_pit_out_lap,
       l.track_status, l.gap_ahead_s, l.exclusion
FROM laps l
JOIN sessions s USING (session_key)
JOIN drivers d ON d.session_key = l.session_key AND d.driver_number = l.driver_number
"""

PITS_SQL = """
SELECT s.circuit, d.acronym AS driver, p.lap_number
FROM pit_stops p
JOIN sessions s USING (session_key)
JOIN drivers d ON d.session_key = p.session_key AND d.driver_number = p.driver_number
"""

RC_SQL = """
SELECT s.circuit, r.date, r.lap_number, r.category, r.flag, r.scope, r.sector, r.message
FROM race_control r JOIN sessions s USING (session_key)
ORDER BY s.circuit, r.msg_id
"""


@dataclass
class SeasonData:
    sessions: pd.DataFrame
    laps: pd.DataFrame
    clean: pd.DataFrame        # tours propres, corrigés du carburant (moteur de stratégie)
    pits: pd.DataFrame
    pit_losses: pd.DataFrame
    rc: pd.DataFrame


def load_season(engine) -> SeasonData:
    laps = read_sql(engine, ALL_LAPS_SQL)
    laps["date_start"] = pd.to_datetime(laps["date_start"], utc=True, format="ISO8601")
    rc = read_sql(engine, RC_SQL)
    rc["date"] = pd.to_datetime(rc["date"], utc=True, format="ISO8601")
    return SeasonData(
        sessions=read_sql(engine, "SELECT circuit, session_key, total_laps FROM sessions"),
        laps=laps,
        clean=load_clean_laps(engine, FuelModel()),
        pits=read_sql(engine, PITS_SQL),
        pit_losses=read_sql(engine, (SQL_DIR / "queries" / "pit_losses.sql").read_text()),
        rc=rc,
    )


@dataclass
class CircuitParams:
    circuit: str
    total_laps: int
    compounds: list[str]
    pace_mean: np.ndarray     # [écarts par composé..., pentes par composé..., évolution piste]
    pace_cov: np.ndarray
    lap_noise_s: float        # écart-type des résidus de la régression
    pit_losses: np.ndarray    # pertes observées sous drapeau vert (s)
    rejoin_gaps: np.ndarray   # écart à la voiture devant au 1er tour après la sortie (s)

    def offset(self, compound: str) -> int:
        return self.compounds.index(compound)

    def slope(self, compound: str) -> int:
        return len(self.compounds) + self.compounds.index(compound)

    @property
    def evo(self) -> int:
        return 2 * len(self.compounds)

    def se(self, i: int) -> float:
        return float(np.sqrt(self.pace_cov[i, i]))


def pace_params(fit: RaceFit) -> tuple[np.ndarray, np.ndarray]:
    """Comme RaceFit.pace_params du moteur de stratégie, avec en plus la tendance de course (modèle B)."""
    names = ([fit.offset_name(c) for c in fit.compounds] + [fit.slope_name(c) for c in fit.compounds]
             + ["lap_number"])
    params, cov = fit.result.params, fit.result.cov_params()
    mean = np.array([params[n] if n else 0.0 for n in names])
    full = np.zeros((len(names), len(names)))
    idx = [i for i, n in enumerate(names) if n]
    kept = [names[i] for i in idx]
    full[np.ix_(idx, idx)] = cov.loc[kept, kept].to_numpy()
    return mean, full


def rejoin_gaps(data: SeasonData, circuit: str, exclude_drivers=()) -> np.ndarray:
    """Écart à la voiture devant après le tour de sortie (arrêts sous drapeau vert) ; écart manquant = air libre."""
    laps = data.laps[data.laps["circuit"] == circuit].set_index(["driver", "lap_number"])
    pits = data.pits[(data.pits["circuit"] == circuit) & ~data.pits["driver"].isin(exclude_drivers)]
    gaps = []
    for p in pits.itertuples():
        keys = [(p.driver, p.lap_number + i) for i in range(3)]
        if not all(k in laps.index for k in keys):
            continue
        if (laps.loc[keys[:2], "track_status"] != "GREEN").any():
            continue
        g = laps.loc[keys[2], "gap_ahead_s"]
        gaps.append(np.inf if pd.isna(g) else float(g))
    return np.array(gaps)


def circuit_params(data: SeasonData, circuit: str, exclude_drivers=()) -> CircuitParams:
    clean = data.clean[(data.clean["circuit"] == circuit) & ~data.clean["driver"].isin(exclude_drivers)]
    fit = fit_race(clean, estimate_trend=True)   # modèle B du moteur de stratégie
    exog = fit.result.model.exog
    if np.linalg.matrix_rank(exog) < exog.shape[1]:
        # Arrive sur les courses mouillées ou avec trop peu de relais : paramètres non identifiés.
        raise ValueError("régression de dégradation non identifiée (rang déficient)")
    mean, cov = pace_params(fit)
    losses = data.pit_losses[(data.pit_losses["circuit"] == circuit)
                             & ~data.pit_losses["driver"].isin(exclude_drivers)]["loss_s"]
    return CircuitParams(
        circuit=circuit, total_laps=fit.total_laps, compounds=fit.compounds,
        pace_mean=mean, pace_cov=cov, lap_noise_s=float(np.sqrt(fit.result.mse_resid)),
        pit_losses=losses.to_numpy(), rejoin_gaps=rejoin_gaps(data, circuit, exclude_drivers),
    )


@dataclass
class TypicalDuel:
    """Situation la plus courante sur un circuit, pour fixer les scénarios de référence."""
    old: str
    new: str
    start_age: int            # âge des pneus au départ (pneus de qualification)
    window: tuple[int, int]   # tours du 1er arrêt, 10e et 90e centiles
    median_stop: int


def typical_duel(data: SeasonData, cp: CircuitParams) -> TypicalDuel:
    laps = data.laps[data.laps["circuit"] == cp.circuit]
    first_two = (laps[laps["stint_number"].isin([1, 2])]
                 .drop_duplicates(["driver", "stint_number"]).pivot(index="driver", columns="stint_number",
                                                                     values="compound").dropna())
    pairs = first_two[first_two[1].isin(cp.compounds) & first_two[2].isin(cp.compounds)
                      & (first_two[1] != first_two[2])]
    old, new = pairs.value_counts().idxmax() if len(pairs) else (cp.compounds[0], cp.compounds[-1])
    stops = data.pits[data.pits["circuit"] == cp.circuit].groupby("driver")["lap_number"].min()
    lo, hi = np.percentile(stops, [10, 90]).round().astype(int)
    start_age = int(laps.loc[laps["lap_number"] == 1, "tyre_age"].median())
    return TypicalDuel(old, new, start_age, (int(lo), int(hi)), int(stops.median()))


@dataclass
class SeasonParams:
    sc_events: int
    vsc_events: int
    exposure_laps: int         # tours de course hors 1er tour, sommés sur les courses
    sc_ratios: np.ndarray      # perte aux stands sous SC / perte normale, par arrêt observé
    vsc_ratios: np.ndarray
    traffic_cost_s: float
    traffic_cost_se: float

    @property
    def sc_rate(self) -> float:
        return self.sc_events / self.exposure_laps

    @property
    def vsc_rate(self) -> float:
        return self.vsc_events / self.exposure_laps


def neutralisation_events(data: SeasonData) -> pd.DataFrame:
    """Un événement par fenêtre SC, VSC ou drapeau rouge (fonction du moteur de stratégie), avec le tour du leader."""
    rows = []
    for circuit, rc in data.rc.groupby("circuit"):
        windows = neutralisation_windows(rc)
        windows = windows[windows["status"].isin(["SC", "VSC", "RED"])].sort_values("start")
        windows["start"] = pd.to_datetime(windows["start"], utc=True)   # type objet si vide
        lap_at = pd.merge_asof(windows[["start"]], rc[["date", "lap_number"]].dropna().sort_values("date"),
                               left_on="start", right_on="date", direction="backward")
        for w, lap in zip(windows.itertuples(), lap_at["lap_number"]):
            rows.append({"circuit": circuit, "status": w.status, "lap": lap, "start": w.start})
    return pd.DataFrame(rows, columns=["circuit", "status", "lap", "start"])


def neutralised_pit_ratios(data: SeasonData) -> pd.DataFrame:
    """Perte aux stands sous SC/VSC (pilote moins médiane des voitures restées en piste), rapportée à la perte en vert."""
    green = data.pit_losses.groupby("circuit")["loss_s"].median()
    rows = []
    for circuit, laps in data.laps.groupby("circuit"):
        if circuit not in green:
            continue
        t = laps.pivot_table(index="driver", columns="lap_number", values="lap_time_s")
        pit_flag = laps.pivot_table(index="driver", columns="lap_number",
                                    values=["is_pit_in_lap", "is_pit_out_lap"], aggfunc="max").fillna(0)
        status = laps.set_index(["driver", "lap_number"])["track_status"]
        for p in data.pits[data.pits["circuit"] == circuit].itertuples():
            s = p.lap_number
            kind = status.get((p.driver, s))
            if kind not in ("SC", "VSC") or s + 1 not in t.columns:
                continue
            busy = (pit_flag["is_pit_in_lap"][[s, s + 1]].max(axis=1)
                    + pit_flag["is_pit_out_lap"][[s, s + 1]].max(axis=1)) > 0
            others = t.loc[~busy.reindex(t.index, fill_value=True), [s, s + 1]].dropna().sum(axis=1)
            own = t.loc[p.driver, [s, s + 1]] if p.driver in t.index else None
            if own is None or own.isna().any() or len(others) < 5:
                continue
            loss = own.sum() - others.median()
            rows.append({"circuit": circuit, "driver": p.driver, "lap": s, "status": kind,
                         "loss_s": loss, "green_loss_s": green[circuit], "ratio": loss / green[circuit]})
    df = pd.DataFrame(rows, columns=["circuit", "driver", "lap", "status", "loss_s", "green_loss_s", "ratio"])
    # Arrêts des tours 1 et 2 écartés (dégâts au départ), comme les ratios hors RATIO_RANGE.
    df["kept"] = (df["lap"] > 2) & df["ratio"].between(*RATIO_RANGE)
    return df


def traffic_cost(laps: pd.DataFrame) -> tuple[float, float]:
    """Coût de l'air sale (écart < TRAFFIC_GAP_S) : effet fixe par relais (within), erreurs clusterisées par relais."""
    df = laps[(laps["track_status"] == "GREEN") & (laps["is_pit_in_lap"] == 0) & (laps["is_pit_out_lap"] == 0)
              & (laps["lap_number"] > 1) & laps["compound"].isin(DRY_COMPOUNDS)
              & (laps["exclusion"].isna() | (laps["exclusion"] == "traffic"))
              & laps["lap_time_s"].notna()].copy()
    df["stint"] = df["circuit"] + "-" + df["driver"] + "-" + df["stint_number"].astype(str)
    median = df.groupby(["circuit", "driver"])["lap_time_s"].transform("median")
    df = df[df["lap_time_s"] <= OUTLIER_RATIO * median]
    df["traffic"] = (df["gap_ahead_s"] < TRAFFIC_GAP_S).astype(float)
    cols = ["traffic"]
    for c in df["compound"].unique():
        df[f"age_{c}"] = df["tyre_age"].astype(float) * (df["compound"] == c)
        cols.append(f"age_{c}")
    within = df[["lap_time_s"] + cols] - df.groupby("stint")[["lap_time_s"] + cols].transform("mean")
    res = sm.OLS(within["lap_time_s"], within[cols]).fit(cov_type="cluster", cov_kwds={"groups": df["stint"]})
    return float(res.params["traffic"]), float(res.bse["traffic"])


def season_params(data: SeasonData, exclude_circuit: str | None = None,
                  events: pd.DataFrame | None = None, ratios: pd.DataFrame | None = None) -> SeasonParams:
    """Paramètres communs, éventuellement sans une course (validation)."""
    events = neutralisation_events(data) if events is None else events
    ratios = neutralised_pit_ratios(data) if ratios is None else ratios
    sessions = data.sessions[data.sessions["circuit"] != exclude_circuit]
    events = events[(events["circuit"] != exclude_circuit) & (events["lap"] > 1)]
    ratios = ratios[(ratios["circuit"] != exclude_circuit) & ratios["kept"]]
    cost, se = traffic_cost(data.laps[data.laps["circuit"] != exclude_circuit])
    return SeasonParams(
        sc_events=int((events["status"] == "SC").sum()),
        vsc_events=int((events["status"] == "VSC").sum()),
        exposure_laps=int((sessions["total_laps"] - 1).sum()),
        sc_ratios=ratios.loc[ratios["status"] == "SC", "ratio"].to_numpy(),
        vsc_ratios=ratios.loc[ratios["status"] == "VSC", "ratio"].to_numpy(),
        traffic_cost_s=cost, traffic_cost_se=se,
    )
