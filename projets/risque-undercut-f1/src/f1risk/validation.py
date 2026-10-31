"""Vraies tentatives d'undercut de la saison, et prédictions du simulateur recalibré hors échantillon."""
import numpy as np
import pandas as pd

from f1engine.config import DRY_COMPOUNDS

from .params import SeasonData, circuit_params, neutralisation_events, neutralised_pit_ratios, season_params
from .simulator import Duel, draw, final_gap

MAX_GAP_S = 3.0
MAX_RESPONSE = 3
MIN_TYRE_AGE = 5
COLUMNS = ["circuit", "attacker", "rival", "stop_lap", "rival_stop_lap", "response", "gap_s", "attacker_old",
           "attacker_new", "rival_old", "rival_new", "attacker_age", "rival_age", "neutralised", "final_gap_s"]


def find_attempts(data: SeasonData) -> pd.DataFrame:
    rows = []
    for circuit, laps in data.laps.groupby("circuit"):
        # Ordre et écarts par heures de passage : l'écart OpenF1 vise la voiture précédente au classement.
        start = laps.pivot_table(index="lap_number", columns="driver", values="date_start", aggfunc="first")
        info = laps.set_index(["driver", "lap_number"])
        stops = data.pits[data.pits["circuit"] == circuit].groupby("driver")["lap_number"].apply(sorted).to_dict()

        def get(driver, lap, col):
            return info[col].get((driver, lap))

        for a, a_stops in stops.items():
            for n in a_stops:
                if n < 3 or n not in start.index:
                    continue
                order = start.loc[n].dropna().sort_values()
                if a not in order.index or order.index.get_loc(a) == 0:
                    continue
                r = order.index[order.index.get_loc(a) - 1]
                gap = (order[a] - order[r]).total_seconds()
                r_next = [s for s in stops.get(r, []) if s >= n]
                if not (0 < gap <= MAX_GAP_S) or not r_next or not 1 <= r_next[0] - n <= MAX_RESPONSE:
                    continue
                response = r_next[0] - n
                end = n + response + 2          # début du tour qui suit le tour de sortie de R
                if any(n < s < end for s in a_stops):
                    continue
                if any(get(d, lap, "track_status") != "GREEN" for d in (a, r) for lap in (n - 1, n)):
                    continue
                comp = {d: (get(d, n, "compound"), get(d, n + (1 if d == a else response + 1), "compound"))
                        for d in (a, r)}
                ages = {d: get(d, n, "tyre_age") for d in (a, r)}
                if any(c not in DRY_COMPOUNDS for pair in comp.values() for c in pair):
                    continue
                if any(pd.isna(x) or x < MIN_TYRE_AGE for x in ages.values()):
                    continue
                if end not in start.index or start.loc[end, [a, r]].isna().any():
                    continue                        # abandon pendant la manoeuvre
                window = [get(d, lap, "track_status") for d in (a, r) for lap in range(n, end)]
                rows.append({
                    "circuit": circuit, "attacker": a, "rival": r, "stop_lap": n, "rival_stop_lap": n + response,
                    "response": response, "gap_s": round(gap, 3),
                    "attacker_old": comp[a][0], "attacker_new": comp[a][1],
                    "rival_old": comp[r][0], "rival_new": comp[r][1],
                    "attacker_age": int(ages[a]), "rival_age": int(ages[r]),
                    "neutralised": any(s in ("SC", "VSC", "RED") for s in window),
                    "final_gap_s": round((start.loc[end, a] - start.loc[end, r]).total_seconds(), 3),
                })
    df = pd.DataFrame(rows, columns=COLUMNS)
    df["success"] = df["final_gap_s"] < 0
    return df


def predict(data: SeasonData, attempts: pd.DataFrame, n_sims: int, seed: int) -> pd.DataFrame:
    """Probabilité de réussite donnée par le simulateur, paramètres estimés hors échantillon."""
    events, ratios = neutralisation_events(data), neutralised_pit_ratios(data)
    season_cache = {}
    out = []
    for i, att in enumerate(attempts.itertuples()):
        row = att._asdict()
        row.pop("Index")
        try:
            cp = circuit_params(data, att.circuit, exclude_drivers=(att.attacker, att.rival))
            if att.circuit not in season_cache:
                season_cache[att.circuit] = season_params(data, exclude_circuit=att.circuit,
                                                          events=events, ratios=ratios)
            sp = season_cache[att.circuit]
            needed = {att.attacker_old, att.attacker_new, att.rival_old, att.rival_new}
            if not needed <= set(cp.compounds):
                raise ValueError(f"composé sans estimation de dégradation ({', '.join(sorted(needed - set(cp.compounds)))})")
            if len(cp.pit_losses) < 5 or len(cp.rejoin_gaps) < 5:
                raise ValueError("trop peu d'arrêts observés sur ce circuit")
            duel = Duel(stop_lap=att.stop_lap, gap_s=att.gap_s, rival_age=att.rival_age,
                        age_diff=att.attacker_age - att.rival_age, old=att.attacker_old, new=att.attacker_new,
                        rival_old=att.rival_old, rival_new=att.rival_new)
            rng = np.random.default_rng(seed + i)
            d = draw(cp, sp, duel, n_sims, rng)
            gaps = final_gap(cp, duel, d, 0, att.response)
            row.update(p_sim=float((gaps < 0).mean()), sim_median_gap_s=float(np.median(gaps)), skipped=None)
        except ValueError as exc:
            row.update(p_sim=np.nan, sim_median_gap_s=np.nan, skipped=str(exc))
        out.append(row)
    return pd.DataFrame(out)


def calibration(pred: pd.DataFrame, seed: int, bins=(0, 0.25, 0.5, 0.75, 1.0)) -> tuple[dict, pd.DataFrame]:
    """Succès observés contre attendus, score de Brier, et calibration par tranche."""
    p = pred.dropna(subset=["p_sim"])
    y = p["success"].astype(float).to_numpy()
    prob = p["p_sim"].to_numpy()
    # Distribution du nombre de succès si le simulateur était exact (somme de Bernoulli)
    rng = np.random.default_rng(seed)
    counts = (rng.random((100_000, len(prob))) < prob).sum(axis=1)
    lo, hi = np.percentile(counts, [5, 95])
    summary = {
        "n_attempts": len(pred), "n_evaluated": len(p), "n_skipped": int(pred["p_sim"].isna().sum()),
        "observed_successes": int(y.sum()), "expected_successes": round(float(prob.sum()), 1),
        "expected_90pct_low": int(lo), "expected_90pct_high": int(hi),
        "brier_simulator": round(float(np.mean((prob - y) ** 2)), 3),
        "brier_coin_flip": 0.25,
        "brier_observed_rate": round(float(np.mean((y.mean() - y) ** 2)), 3),
    }
    p = p.assign(bin=pd.cut(p["p_sim"], bins, include_lowest=True))
    table = p.groupby("bin", observed=False).agg(
        n=("success", "size"), mean_p_sim=("p_sim", "mean"), observed_rate=("success", "mean")).reset_index()
    table["bin"] = table["bin"].astype(str)
    return summary, table
