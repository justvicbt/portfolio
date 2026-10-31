"""Transformation en fonctions pures : validation météo, alignement sur les tours, positions, contrôles (dates UTC)."""
import numpy as np
import pandas as pd

from .config import WEATHER_MAX_GAP_S, WEATHER_TOLERANCE_S
from .text import num, pct, plural

# Plages physiquement plausibles ; une valeur en dehors est traitée comme manquante.
WEATHER_RANGES = {
    "air_temp_c": (-10, 50), "track_temp_c": (5, 70), "humidity_pct": (0, 100),
    "pressure_hpa": (800, 1100), "wind_speed_ms": (0, 40), "wind_direction_deg": (0, 360),
}
WEATHER_NUMERIC = ["air_temp_c", "track_temp_c", "humidity_pct", "wind_speed_ms"]
OPENF1_WEATHER = {
    "air_temperature": "air_temp_c", "track_temperature": "track_temp_c", "humidity": "humidity_pct",
    "pressure": "pressure_hpa", "wind_speed": "wind_speed_ms", "wind_direction": "wind_direction_deg",
}


def validate_weather(raw: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Renomme, retire les doublons d'horodatage, vide les valeurs hors plage ; renvoie aussi le nombre écarté."""
    w = raw.rename(columns=OPENF1_WEATHER).copy()
    w["date"] = pd.to_datetime(w["date"], utc=True, format="ISO8601")
    w = w.dropna(subset=["date"]).sort_values("date").drop_duplicates("date", keep="last")
    rejected = 0
    for col, (lo, hi) in WEATHER_RANGES.items():
        values = pd.to_numeric(w[col], errors="coerce")
        bad = values.notna() & ~values.between(lo, hi)
        rejected += int(bad.sum())
        w[col] = values.where(~bad)
    rain = pd.to_numeric(w["rainfall"], errors="coerce")
    bad = rain.notna() & ~rain.isin([0, 1])
    rejected += int(bad.sum())
    w["rainfall"] = rain.where(~bad).astype("Int64")
    return w[["date", *WEATHER_RANGES, "rainfall"]].reset_index(drop=True), rejected


def repair_date_starts(laps: pd.DataFrame, tolerance_s: float = 2.0) -> pd.Series:
    """Corrige un début de tour isolé quand les deux tours voisins s'accordent entre eux mais pas avec lui."""
    s = laps.sort_values(["driver_number", "lap_number"])
    g = s.groupby("driver_number")
    dur = pd.to_timedelta(s["lap_time_s"], unit="s")
    prev_ok = g["lap_number"].shift(1) == s["lap_number"] - 1
    next_ok = g["lap_number"].shift(-1) == s["lap_number"] + 1
    from_prev = (g["date_start"].shift(1) + pd.to_timedelta(g["lap_time_s"].shift(1), unit="s")).where(prev_ok)
    from_next = (g["date_start"].shift(-1) - dur).where(next_ok)
    tol = pd.Timedelta(seconds=tolerance_s)
    bad = (((s["date_start"] - from_prev).abs() > tol) & ((s["date_start"] - from_next).abs() > tol)
           & ((from_prev - from_next).abs() <= tol))
    return s["date_start"].where(~bad, from_prev).reindex(laps.index)


def lap_end_times(laps: pd.DataFrame) -> pd.Series:
    """Fin de chaque tour : début du tour suivant, sinon début + durée, sinon NaT."""
    laps = laps.sort_values(["driver_number", "lap_number"])
    nxt = laps.groupby("driver_number")["date_start"].shift(-1)
    consecutive = laps.groupby("driver_number")["lap_number"].shift(-1) == laps["lap_number"] + 1
    end = nxt.where(consecutive)
    return end.fillna(laps["date_start"] + pd.to_timedelta(laps["lap_time_s"], unit="s")).reindex(laps.index)


def positions_and_gaps(laps: pd.DataFrame) -> pd.DataFrame:
    """Calcul A : position et écart au leader par heure de passage ; un pilote doublé a plus d'un tour d'écart."""
    done = laps.dropna(subset=["lap_end"])
    pos = done.groupby("lap_number")["lap_end"].rank(method="first").astype(int)
    gap = (done["lap_end"] - done.groupby("lap_number")["lap_end"].transform("min")).dt.total_seconds()
    return pd.DataFrame({"position": pos, "gap_to_leader_s": gap}).reindex(laps.index)


def align_weather(laps: pd.DataFrame, weather: pd.DataFrame,
                  tolerance_s: float = WEATHER_TOLERANCE_S, max_gap_s: float = WEATHER_MAX_GAP_S) -> pd.DataFrame:
    """Météo au milieu du tour (measured, interpolated ou missing, sans extrapolation) ; pluie si signalée pendant le tour."""
    start = laps["date_start"]
    end = laps["lap_end"].fillna(start)
    mid = start + (end - start) / 2
    left = pd.DataFrame({"mid": mid, "start": start, "end": end}).reset_index().dropna(subset=["mid"])
    left = left.sort_values("mid")
    w = weather.sort_values("date").reset_index(drop=True)
    w = w.assign(w_idx=np.arange(len(w)))
    cols = WEATHER_NUMERIC + ["rainfall"]

    near = pd.merge_asof(left, w[["date", "w_idx"]], left_on="mid", right_on="date", direction="nearest",
                         tolerance=pd.to_timedelta(tolerance_s, unit="s"))
    prev = pd.merge_asof(left, w[["date", "w_idx"]], left_on="mid", right_on="date", direction="backward")
    nxt = pd.merge_asof(left, w[["date", "w_idx"]], left_on="mid", right_on="date", direction="forward")

    out = pd.DataFrame(index=near["index"], columns=cols + ["weather_status"], dtype=object)
    out["weather_status"] = "missing"
    for i in range(len(near)):
        idx = near.at[i, "index"]
        if pd.notna(near.at[i, "w_idx"]):
            row = w.loc[int(near.at[i, "w_idx"])]
            out.loc[idx, cols] = row[cols].to_numpy()
            out.at[idx, "weather_status"] = "measured"
        elif pd.notna(prev.at[i, "w_idx"]) and pd.notna(nxt.at[i, "w_idx"]):
            a, b = w.loc[int(prev.at[i, "w_idx"])], w.loc[int(nxt.at[i, "w_idx"])]
            span = (b["date"] - a["date"]).total_seconds()
            if span <= max_gap_s:
                frac = (near.at[i, "mid"] - a["date"]).total_seconds() / span if span else 0.0
                for c in WEATHER_NUMERIC:
                    out.at[idx, c] = a[c] + frac * (b[c] - a[c]) if pd.notna(a[c]) and pd.notna(b[c]) else np.nan
                out.at[idx, "rainfall"] = max(a["rainfall"], b["rainfall"]) if pd.notna(a["rainfall"]) \
                    and pd.notna(b["rainfall"]) else np.nan
                out.at[idx, "weather_status"] = "interpolated"

    # Pluie pendant le tour : n'importe quelle mesure entre le début et la fin.
    if len(w):
        dates = pd.DatetimeIndex(w["date"])
        rain = w["rainfall"].astype("float").to_numpy()
        for row in left.itertuples():
            lo, hi = dates.searchsorted(row.start), dates.searchsorted(row.end, side="right")
            during = rain[lo:hi]
            during = during[~np.isnan(during)]
            if len(during):
                out.at[row.index, "rainfall"] = float(during.max())

    out = out.reindex(laps.index)
    out["weather_status"] = out["weather_status"].fillna("missing")
    for c in cols:
        out[c] = pd.to_numeric(out[c], errors="coerce")
    out["rain"] = out.pop("rainfall").astype("Int64")
    return out


def derived_classification(laps: pd.DataFrame) -> pd.Series:
    """Classement final recalculé : plus de tours bouclés d'abord, puis passage le plus tôt."""
    last = laps.dropna(subset=["lap_end"]).sort_values("lap_number").groupby("driver_number").last()
    order = last.sort_values(["lap_number", "lap_end"], ascending=[False, True])
    return pd.Series(np.arange(1, len(order) + 1), index=order.index, name="derived_position")


def results_table(raw: list[dict], known_drivers: set) -> pd.DataFrame:
    df = pd.DataFrame(raw, columns=["driver_number", "position", "number_of_laps", "points", "dnf", "dns", "dsq"])
    df = df[df["driver_number"].isin(known_drivers)].drop_duplicates("driver_number")
    status = np.select([df["dsq"].fillna(False).astype(bool), df["dns"].fillna(False).astype(bool),
                        df["dnf"].fillna(False).astype(bool)], ["DSQ", "DNS", "DNF"], "FINISHED")
    return df.assign(status=status, position=df["position"].astype("Int64"))[
        ["driver_number", "position", "number_of_laps", "status", "points"]]


def consistency_checks(laps: pd.DataFrame, cond: pd.DataFrame, results: pd.DataFrame,
                       weather_rejected: int) -> list[dict]:
    """Contrôles de cohérence d'une course, une ligne par contrôle : check_name, status, value, detail."""
    checks = []

    def add(name, status, value, detail):
        checks.append({"check_name": name, "status": status, "value": value, "detail": detail})

    n = len(laps)
    covered = (cond["weather_status"] != "missing").mean() if n else 0.0
    add("weather_coverage", "ok" if covered >= 0.95 else "warning" if covered >= 0.8 else "fail", covered,
        f"{pct(covered, 1)} des tours ont une mesure météo (directe ou interpolée)")
    interp = (cond["weather_status"] == "interpolated").mean() if n else 0.0
    add("weather_interpolated", "ok" if interp <= 0.1 else "warning", interp,
        f"{pct(interp, 1)} des tours ont une météo interpolée")
    add("weather_out_of_range", "ok" if weather_rejected == 0 else "warning", weather_rejected,
        f"{plural(weather_rejected, 'valeur')} météo hors plage physique, "
        f"{'mises' if weather_rejected > 1 else 'mise'} à vide")

    expected = results.set_index("driver_number")["number_of_laps"].fillna(0)
    present = laps.groupby("driver_number").size().reindex(expected.index, fill_value=0)
    missing = int((expected - present).clip(lower=0).sum())
    add("laps_missing", "ok" if missing == 0 else "warning", missing,
        f"{plural(missing, 'tour annoncé', 'tours annoncés')} par le classement mais "
        f"{'absents' if missing > 1 else 'absent'} des données de tours")

    # Durée du tour contre écart entre deux passages sur la ligne (deux sources OpenF1).
    s = laps.sort_values(["driver_number", "lap_number"])
    nxt = s.groupby("driver_number")["date_start"].shift(-1)
    diff = ((nxt - s["date_start"]).dt.total_seconds() - s["lap_time_s"]).abs().dropna()
    med = float(diff.median()) if len(diff) else np.nan
    add("lap_time_vs_crossings", "ok" if med < 0.05 else "warning", med,
        f"écart médian de {num(med, 3)} s entre durée du tour et écart entre deux passages sur la ligne"
        f" ({plural(int((diff > 1).sum()), 'tour')} à plus de 1 s)")

    # On ne compare que les pilotes classés : un disqualifié ou un abandon décalerait tout le reste.
    official = results.dropna(subset=["position"]).set_index("driver_number")["position"].rank().astype(int)
    derived = derived_classification(laps[laps["driver_number"].isin(official.index)]).reindex(official.index)
    agree = int((derived == official).sum())
    add("final_order_vs_results", "ok" if agree == len(official) else "warning", agree,
        f"{agree} pilote{'s' if agree > 1 else ''} sur {plural(len(official), 'classé')} à la même place que le classement officiel"
        " (un écart vient en général d'une pénalité en temps ajoutée au classement)")

    clean = float(laps["is_clean"].mean()) if n else 0.0
    add("clean_laps_share", "ok" if clean >= 0.3 else "warning", clean,
        f"{pct(clean)} des tours sont propres au sens du moteur de stratégie")
    return checks
