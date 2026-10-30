"""Nettoyage des tours : état de la piste, pneus, trafic, tours aberrants, carburant."""
import numpy as np
import pandas as pd

from .config import DRY_COMPOUNDS, CleaningRules, FuelModel

STATUS_PRIORITY = {"GREEN": 0, "YELLOW": 1, "VSC": 2, "SC": 3, "RED": 4}


def neutralisation_windows(rc: pd.DataFrame, rules: CleaningRules = CleaningRules()) -> pd.DataFrame:
    """Fenêtres [start, end, status] SC, VSC, rouge et jaune ; SC/VSC prolongés de sc_buffer_s (tour de relance)."""
    rc = rc.sort_values("date")
    buffer = pd.to_timedelta(rules.sc_buffer_s, unit="s")
    windows: list[tuple] = []
    open_sc = open_vsc = open_red = sc_in_lap = None
    open_yellow: dict = {}  # clé : numéro de secteur, ou "TRACK"

    for row in rc.itertuples(index=False):
        msg = str(row.message).upper()
        flag = row.flag if isinstance(row.flag, str) else None
        scope = row.scope if isinstance(row.scope, str) else None
        t = row.date

        if row.category == "SafetyCar":
            if "VIRTUAL" in msg and "DEPLOYED" in msg:
                open_vsc = t
            elif "VIRTUAL" in msg and "ENDING" in msg and open_vsc is not None:
                windows.append((open_vsc, t + buffer, "VSC"))
                open_vsc = None
            elif "DEPLOYED" in msg and open_sc is None:
                open_sc = t
            elif "IN THIS LAP" in msg:
                sc_in_lap = t
            continue

        if flag == "RED":
            open_red = t
        elif flag == "GREEN" and open_red is not None:
            windows.append((open_red, t, "RED"))
            open_red = None

        if flag in ("YELLOW", "DOUBLE YELLOW"):
            key = row.sector if scope == "Sector" and pd.notna(row.sector) else "TRACK"
            open_yellow.setdefault(key, t)
        elif flag == "CLEAR":
            if scope == "Track":
                for start in open_yellow.values():
                    windows.append((start, t, "YELLOW"))
                open_yellow.clear()
                if open_sc is not None and sc_in_lap is not None:
                    windows.append((open_sc, t + buffer, "SC"))
                    open_sc = sc_in_lap = None
            elif pd.notna(row.sector) and row.sector in open_yellow:
                windows.append((open_yellow.pop(row.sector), t, "YELLOW"))

    # Fenêtres jamais refermées dans les messages : durée par défaut.
    fallback = pd.to_timedelta(rules.yellow_fallback_s, unit="s")
    for start in open_yellow.values():
        windows.append((start, start + fallback, "YELLOW"))
    if open_sc is not None:
        end = sc_in_lap + pd.to_timedelta(120, unit="s") if sc_in_lap is not None else open_sc + pd.to_timedelta(600, unit="s")
        windows.append((open_sc, end + buffer, "SC"))
    if open_vsc is not None:
        windows.append((open_vsc, open_vsc + pd.to_timedelta(300, unit="s"), "VSC"))

    return pd.DataFrame(windows, columns=["start", "end", "status"])


def assign_track_status(laps: pd.DataFrame, windows: pd.DataFrame) -> pd.Series:
    """État de piste le plus grave rencontré pendant chaque tour (chevauchement temporel)."""
    laps = laps.sort_values(["driver_number", "lap_number"])
    next_start = laps.groupby("driver_number")["date_start"].shift(-1)
    lap_end = next_start.fillna(laps["date_start"] + pd.to_timedelta(laps["lap_time_s"], unit="s"))
    lap_end = lap_end.fillna(laps["date_start"] + pd.to_timedelta(120, unit="s"))

    level = pd.Series(0, index=laps.index)
    for w in windows.itertuples(index=False):
        overlap = (laps["date_start"] < w.end) & (lap_end > w.start)
        level = level.where(~overlap, np.maximum(level, STATUS_PRIORITY[w.status]))
    names = {v: k for k, v in STATUS_PRIORITY.items()}
    return level.map(names).reindex(laps.index)


def attach_tyres(laps: pd.DataFrame, stints: pd.DataFrame) -> pd.DataFrame:
    """Ajoute stint_number, compound et tyre_age (tours déjà effectués par le train)."""
    merged = laps.merge(
        stints[["driver_number", "stint_number", "compound", "lap_start", "lap_end", "tyre_age_at_start"]],
        on="driver_number", how="left",
    )
    in_stint = (merged["lap_number"] >= merged["lap_start"]) & (merged["lap_number"] <= merged["lap_end"])
    merged = merged[in_stint].copy()
    merged["tyre_age"] = merged["tyre_age_at_start"] + merged["lap_number"] - merged["lap_start"]
    # Si deux relais se chevauchent (erreur de données), on garde le plus récent.
    merged = merged.sort_values("stint_number").drop_duplicates(["driver_number", "lap_number"], keep="last")
    out = laps.merge(
        merged[["driver_number", "lap_number", "stint_number", "compound", "tyre_age"]],
        on=["driver_number", "lap_number"], how="left",
    )
    out["stint_number"] = out["stint_number"].astype("Int64")
    out["tyre_age"] = out["tyre_age"].astype("Int64")
    return out


def gap_ahead(laps: pd.DataFrame, intervals: pd.DataFrame, tolerance_s: float = 20) -> pd.Series:
    """Écart à la voiture devant, dernière mesure avant le début du tour ; "+1 LAP" (OpenF1) devient NaN."""
    iv = intervals[["date", "driver_number", "interval"]].copy()
    iv["interval"] = pd.to_numeric(iv["interval"], errors="coerce")
    iv = iv.dropna(subset=["date"]).sort_values("date")
    left = laps[["driver_number", "date_start"]].reset_index().dropna(subset=["date_start"]).sort_values("date_start")
    merged = pd.merge_asof(
        left, iv, left_on="date_start", right_on="date", by="driver_number",
        direction="backward", tolerance=pd.to_timedelta(tolerance_s, unit="s"),
    )
    return merged.set_index("index")["interval"].reindex(laps.index)


def mark_clean(laps: pd.DataFrame, rules: CleaningRules = CleaningRules()) -> pd.DataFrame:
    """Renseigne `exclusion` (première raison d'écarter le tour) et `is_clean`."""
    laps = laps.copy()
    reason = pd.Series(pd.NA, index=laps.index, dtype="object")

    def flag(mask, label):
        nonlocal reason
        reason = reason.where(reason.notna() | ~mask.fillna(False).astype(bool), label)

    flag(laps["lap_number"] == 1, "lap1")
    flag(laps["lap_time_s"].isna(), "no_time")
    flag(laps["is_pit_in_lap"] == 1, "pit_in")
    flag(laps["is_pit_out_lap"] == 1, "pit_out")
    flag(laps["track_status"] != "GREEN", "neutralised")
    flag(~laps["compound"].isin(DRY_COMPOUNDS), "not_dry")
    flag(laps["gap_ahead_s"] < rules.min_gap_ahead_s, "traffic")

    # Aberrants : comparés à la médiane des tours encore valides du même pilote.
    candidate = reason.isna()
    median = laps["lap_time_s"].where(candidate).groupby(laps["driver_number"]).transform("median")
    flag(candidate & (laps["lap_time_s"] > rules.outlier_ratio * median), "outlier")

    laps["exclusion"] = reason
    laps["is_clean"] = reason.isna().astype(int)
    return laps


def fuel_corrected(lap_time_s, lap_number, total_laps, fuel: FuelModel = FuelModel()):
    """Retire l'effet du carburant restant, débit constant : masse au tour n = start_kg * (1 - (n - 0.5) / total_laps)."""
    fuel_kg = fuel.start_kg * (1 - (np.asarray(lap_number) - 0.5) / total_laps)
    return np.asarray(lap_time_s) - fuel.sec_per_kg * np.clip(fuel_kg, 0, None)
