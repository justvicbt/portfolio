"""Ingestion OpenF1 -> nettoyage -> SQLite ; base reconstruite à chaque lancement, réponses gardées dans data/raw/."""
import pandas as pd
from sqlalchemy.engine import Engine

from . import openf1
from .cleaning import (
    CleaningRules,
    assign_track_status,
    attach_tyres,
    gap_ahead,
    mark_clean,
    neutralisation_windows,
)
from .config import circuits, season
from .db import create_schema, get_engine


def _dt(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, utc=True, format="ISO8601")


def _iso(series: pd.Series) -> pd.Series:
    return series.dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")  # UTC, lisible par julianday()


def find_race(year: int, circuit: str) -> dict:
    races = openf1.get("sessions", year=year, session_name="Race", circuit_short_name=circuit)
    if not races:
        raise ValueError(f"Aucune course trouvée pour {circuit} {year} dans OpenF1")
    return races[0]


def build_laps(raw_laps, stints, pits, rc, intervals, rules: CleaningRules) -> pd.DataFrame:
    laps = pd.DataFrame(raw_laps).rename(columns={
        "lap_duration": "lap_time_s", "duration_sector_1": "s1_s", "duration_sector_2": "s2_s",
        "duration_sector_3": "s3_s", "st_speed": "speed_trap_kmh",
    })
    laps["date_start"] = _dt(laps["date_start"])
    laps["is_pit_out_lap"] = laps["is_pit_out_lap"].fillna(False).astype(int)

    laps = attach_tyres(laps, stints)
    # Tour de sortie : signalé par OpenF1 ou premier tour d'un relais (hors départ).
    first_of_stint = stints.loc[stints["stint_number"] > 1, ["driver_number", "lap_start"]]
    out_keys = set(zip(first_of_stint["driver_number"], first_of_stint["lap_start"]))
    in_keys = set(zip(pits["driver_number"], pits["lap_number"])) if len(pits) else set()
    keys = list(zip(laps["driver_number"], laps["lap_number"]))
    laps.loc[[k in out_keys for k in keys], "is_pit_out_lap"] = 1
    laps["is_pit_in_lap"] = [int(k in in_keys) for k in keys]

    laps["track_status"] = assign_track_status(laps, neutralisation_windows(rc, rules))
    laps["gap_ahead_s"] = gap_ahead(laps, intervals)
    return mark_clean(laps, rules)


def build_telemetry(lap: pd.Series, car_data: list[dict]) -> pd.DataFrame:
    """Télémétrie d'un tour : temps relatif, distance intégrée, secteur de chrono."""
    if not car_data:
        return pd.DataFrame()
    tel = pd.DataFrame(car_data)
    tel["date"] = _dt(tel["date"])
    tel = tel.sort_values("date").reset_index(drop=True)
    tel["t_s"] = (tel["date"] - lap["date_start"]).dt.total_seconds()
    tel = tel[(tel["t_s"] >= 0) & (tel["t_s"] <= lap["lap_time_s"])].reset_index(drop=True)
    # Distance = intégrale (trapèzes) de la vitesse ; approximative à ~3,7 Hz.
    v = tel["speed"] / 3.6
    tel["distance_m"] = ((v + v.shift()).fillna(0) / 2 * tel["t_s"].diff().fillna(0)).cumsum()
    s1_end, s2_end = lap["s1_s"], lap["s1_s"] + lap["s2_s"]
    tel["sector"] = 1 + (tel["t_s"] >= s1_end).astype(int) + (tel["t_s"] >= s2_end).astype(int)
    return pd.DataFrame({
        "session_key": int(lap["session_key"]), "driver_number": int(lap["driver_number"]),
        "lap_number": int(lap["lap_number"]), "sample_idx": tel.index, "t_s": tel["t_s"],
        "distance_m": tel["distance_m"], "sector": tel["sector"], "speed_kmh": tel["speed"],
        "throttle_pct": tel["throttle"], "brake_on": (tel["brake"] > 0).astype(int),
        "drs": tel["drs"], "gear": tel["n_gear"], "rpm": tel["rpm"],
    })


def ingest_race(engine: Engine, year: int, circuit: str, rules: CleaningRules = CleaningRules()) -> dict:
    race = find_race(year, circuit)
    sk = race["session_key"]
    raw = {name: openf1.get(name, session_key=sk)
           for name in ("drivers", "laps", "stints", "pit", "race_control", "intervals")}

    drivers = pd.DataFrame(raw["drivers"]).drop_duplicates("driver_number")
    known = set(drivers["driver_number"])

    stints = pd.DataFrame(raw["stints"])
    stints = stints[stints["driver_number"].isin(known)].dropna(subset=["lap_start"])
    stints["compound"] = stints["compound"].fillna("UNKNOWN").str.upper()
    stints["tyre_age_at_start"] = stints["tyre_age_at_start"].fillna(0)
    raw_laps = [lap for lap in raw["laps"] if lap["driver_number"] in known and lap.get("date_start")]
    total_laps = max(lap["lap_number"] for lap in raw_laps)
    stints["lap_end"] = stints["lap_end"].fillna(total_laps)
    stints = stints.drop_duplicates(["driver_number", "stint_number"]).astype(
        {"lap_start": int, "lap_end": int, "tyre_age_at_start": int})

    pits = pd.DataFrame(raw["pit"], columns=["driver_number", "lap_number", "lane_duration", "stop_duration"])
    pits = pits[pits["driver_number"].isin(known)].drop_duplicates(["driver_number", "lap_number"])

    rc = pd.DataFrame(raw["race_control"])
    rc["date"] = _dt(rc["date"])
    rc = rc.sort_values("date").reset_index(drop=True)

    intervals = pd.DataFrame(raw["intervals"])
    intervals["date"] = _dt(intervals["date"])

    laps = build_laps(raw_laps, stints, pits, rc, intervals, rules)
    laps["session_key"] = sk

    # Tour le plus rapide seulement ; trafic autorisé, sinon le DRS (ouvert à < 1 s) n'apparaîtrait presque jamais.
    eligible = laps["exclusion"].isna() | (laps["exclusion"] == "traffic")
    fastest = (laps[eligible & laps["s1_s"].notna() & laps["s2_s"].notna()]
               .sort_values("lap_time_s").drop_duplicates("driver_number"))
    tel_frames = []
    for lap in fastest.to_dict("records"):
        end = lap["date_start"] + pd.to_timedelta(float(lap["lap_time_s"]), unit="s")
        car = openf1.get("car_data", session_key=sk, driver_number=lap["driver_number"],
                         **{"date>": lap["date_start"].isoformat(), "date<": end.isoformat()})
        tel_frames.append(build_telemetry(pd.Series(lap), car))
    telemetry = pd.concat(tel_frames, ignore_index=True) if tel_frames else pd.DataFrame()

    with engine.begin() as conn:
        pd.DataFrame([{
            "session_key": sk, "meeting_key": race["meeting_key"], "year": race["year"],
            "circuit": race["circuit_short_name"], "country": race["country_name"],
            "date_start": race["date_start"], "total_laps": total_laps,
        }]).to_sql("sessions", conn, if_exists="append", index=False)
        drivers.assign(session_key=sk).rename(columns={"name_acronym": "acronym", "team_name": "team"})[
            ["session_key", "driver_number", "acronym", "full_name", "team"]
        ].to_sql("drivers", conn, if_exists="append", index=False)
        stints.assign(session_key=sk)[
            ["session_key", "driver_number", "stint_number", "compound", "lap_start", "lap_end", "tyre_age_at_start"]
        ].to_sql("stints", conn, if_exists="append", index=False)
        pits.assign(session_key=sk).rename(
            columns={"lane_duration": "lane_duration_s", "stop_duration": "stop_duration_s"}
        ).to_sql("pit_stops", conn, if_exists="append", index=False)
        rc.assign(session_key=sk, msg_id=rc.index, date=_iso(rc["date"]))[
            ["session_key", "msg_id", "date", "lap_number", "category", "flag", "scope", "sector", "message"]
        ].to_sql("race_control", conn, if_exists="append", index=False)
        laps.assign(date_start=_iso(laps["date_start"]))[[
            "session_key", "driver_number", "lap_number", "date_start", "lap_time_s", "s1_s", "s2_s", "s3_s",
            "speed_trap_kmh", "stint_number", "compound", "tyre_age", "is_pit_out_lap", "is_pit_in_lap",
            "track_status", "gap_ahead_s", "is_clean", "exclusion",
        ]].to_sql("laps", conn, if_exists="append", index=False)
        if len(telemetry):
            telemetry.to_sql("telemetry", conn, if_exists="append", index=False)

    return {"circuit": circuit, "session_key": sk, "laps": len(laps), "clean_laps": int(laps["is_clean"].sum()),
            "stints": len(stints), "pit_stops": len(pits), "telemetry_rows": len(telemetry)}


def main() -> None:
    engine = get_engine()
    create_schema(engine)
    year = season()
    for circuit in circuits():
        print(f"Chargement {circuit} {year}...", flush=True)
        stats = ingest_race(engine, year, circuit)
        print("  " + ", ".join(f"{k}={v}" for k, v in stats.items()), flush=True)


if __name__ == "__main__":
    main()
