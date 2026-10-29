"""Transformation : météo, alignement sur les tours, valeurs manquantes, positions, contrôles."""
import numpy as np
import pandas as pd

from f1cc import transform

T0 = pd.Timestamp("2025-07-06T14:00:00Z")


def at(s: float) -> pd.Timestamp:
    return T0 + pd.Timedelta(seconds=s)


def weather(rows):
    """rows : (secondes, température de piste, pluie)."""
    raw = pd.DataFrame([{"date": at(s).isoformat(), "air_temperature": 20.0, "track_temperature": tt,
                         "humidity": 60.0, "pressure": 1000.0, "wind_speed": 1.0, "wind_direction": 90,
                         "rainfall": r} for s, tt, r in rows])
    w, _ = transform.validate_weather(raw)
    return w


def one_lap(start: float, end: float) -> pd.DataFrame:
    return pd.DataFrame({"date_start": [at(start)], "lap_end": [at(end)]})


def test_validate_weather_drops_duplicates_and_out_of_range_values():
    raw = pd.DataFrame([
        {"date": at(0).isoformat(), "air_temperature": 20, "track_temperature": 30, "humidity": 50,
         "pressure": 1000, "wind_speed": 1, "wind_direction": 10, "rainfall": 0},
        {"date": at(0).isoformat(), "air_temperature": 21, "track_temperature": 31, "humidity": 50,
         "pressure": 1000, "wind_speed": 1, "wind_direction": 10, "rainfall": 0},   # doublon
        {"date": at(60).isoformat(), "air_temperature": 20, "track_temperature": 150, "humidity": 120,
         "pressure": 1000, "wind_speed": 1, "wind_direction": 10, "rainfall": 3},   # 3 valeurs absurdes
    ])
    w, rejected = transform.validate_weather(raw)
    assert len(w) == 2
    assert w.loc[0, "track_temp_c"] == 31          # le dernier doublon est gardé
    assert rejected == 3
    assert pd.isna(w.loc[1, "track_temp_c"]) and pd.isna(w.loc[1, "humidity_pct"]) and pd.isna(w.loc[1, "rainfall"])


def test_measurement_nearest_to_mid_lap_is_used():
    w = weather([(0, 30.0, 0), (60, 31.0, 0), (120, 32.0, 0)])
    out = transform.align_weather(one_lap(50, 140), w)   # milieu à 95 s : plus proche de 120 s
    assert out.loc[0, "weather_status"] == "measured"
    assert out.loc[0, "track_temp_c"] == 32.0


def test_short_gap_is_interpolated_linearly():
    w = weather([(0, 30.0, 0), (240, 34.0, 0)])          # 4 min sans mesure
    out = transform.align_weather(one_lap(100, 140), w)  # milieu à 120 s, à plus de 90 s des deux mesures
    assert out.loc[0, "weather_status"] == "interpolated"
    assert np.isclose(out.loc[0, "track_temp_c"], 32.0)


def test_long_gap_stays_missing_and_is_not_extrapolated():
    w = weather([(0, 30.0, 0), (600, 40.0, 0)])          # 10 min sans mesure
    out = transform.align_weather(one_lap(250, 350), w)
    assert out.loc[0, "weather_status"] == "missing"
    assert pd.isna(out.loc[0, "track_temp_c"]) and pd.isna(out.loc[0, "rain"])
    # Avant la première mesure : pas d'extrapolation non plus.
    out = transform.align_weather(one_lap(-400, -300), w)
    assert out.loc[0, "weather_status"] == "missing"


def test_rain_counts_if_signalled_at_any_point_during_the_lap():
    w = weather([(0, 30.0, 0), (60, 30.0, 1), (120, 30.0, 0)])
    out = transform.align_weather(one_lap(10, 100), w)   # milieu à 55 s, la pluie tombe à 60 s
    assert out.loc[0, "rain"] == 1
    out = transform.align_weather(one_lap(100, 170), w)  # milieu à 135 s : la mesure de 120 s dit non
    assert out.loc[0, "rain"] == 0


def test_missing_weather_values_inside_a_sample_stay_missing():
    w = weather([(0, 30.0, 0), (60, 30.0, 0)])
    w.loc[1, "track_temp_c"] = np.nan
    out = transform.align_weather(one_lap(40, 120), w)   # milieu à 80 s : mesure de 60 s, température vide
    assert out.loc[0, "weather_status"] == "measured"
    assert pd.isna(out.loc[0, "track_temp_c"]) and out.loc[0, "humidity_pct"] == 60.0


def laps_two_drivers():
    """A boucle ses tours en 90 s, B en 91 s, B part 1 s derrière. B n'a pas de durée au tour 3."""
    rows = []
    for drv, lap_s, offset in ((1, 90.0, 0.0), (2, 91.0, 1.0)):
        for n in range(1, 4):
            rows.append({"driver_number": drv, "lap_number": n, "date_start": at(offset + (n - 1) * lap_s),
                         "lap_time_s": lap_s})
    df = pd.DataFrame(rows)
    df.loc[(df["driver_number"] == 2) & (df["lap_number"] == 3), "lap_time_s"] = np.nan
    return df


def test_lap_end_uses_next_lap_start_then_duration_then_nothing():
    df = laps_two_drivers()
    end = transform.lap_end_times(df)
    a = df["driver_number"] == 1
    assert end[a & (df["lap_number"] == 1)].iloc[0] == at(90)    # début du tour suivant
    assert end[a & (df["lap_number"] == 3)].iloc[0] == at(270)   # début + durée
    assert pd.isna(end[~a & (df["lap_number"] == 3)].iloc[0])    # ni tour suivant, ni durée


def test_positions_and_gap_to_leader():
    df = laps_two_drivers()
    df["lap_end"] = transform.lap_end_times(df)
    out = transform.positions_and_gaps(df)
    b2 = (df["driver_number"] == 2) & (df["lap_number"] == 2)
    assert out.loc[b2, "position"].iloc[0] == 2
    assert np.isclose(out.loc[b2, "gap_to_leader_s"].iloc[0], 3.0)   # 1 s au départ + 1 s par tour x 2
    assert out.loc[df["driver_number"] == 1, "gap_to_leader_s"].eq(0).all()


def test_lapped_car_is_behind_with_gap_above_one_lap():
    rows = [{"driver_number": 1, "lap_number": n, "lap_end": at(90 * n)} for n in (1, 2, 3)]
    rows += [{"driver_number": 2, "lap_number": n, "lap_end": at(140 * n)} for n in (1, 2)]
    df = pd.DataFrame(rows)
    out = transform.positions_and_gaps(df)
    assert out.loc[4, "position"] == 2 and out.loc[4, "gap_to_leader_s"] == 280 - 180
    # Classement final : plus de tours d'abord.
    assert transform.derived_classification(df).index.tolist() == [1, 2]


def test_checks_flag_missing_laps_and_weather():
    df = laps_two_drivers()
    df["lap_end"] = transform.lap_end_times(df)
    df["is_clean"] = 1
    cond = pd.DataFrame({"weather_status": ["measured"] * 4 + ["missing"] * 2})
    results = pd.DataFrame({"driver_number": [1, 2], "position": [1, 2], "number_of_laps": [3, 4]})
    checks = {c["check_name"]: c for c in transform.consistency_checks(df, cond, results, weather_rejected=0)}
    assert checks["laps_missing"]["value"] == 1 and checks["laps_missing"]["status"] == "warning"
    assert checks["weather_coverage"]["status"] == "fail"          # 67 % < 80 %
    assert checks["final_order_vs_results"]["status"] == "ok"


def test_disqualified_driver_does_not_shift_the_order_comparison():
    df = pd.DataFrame([{"driver_number": d, "lap_number": 1, "lap_end": at(s)} for d, s in ((1, 90), (9, 91), (2, 92))])
    df["date_start"], df["lap_time_s"], df["is_clean"] = at(0), 90.0, 1
    results = pd.DataFrame({"driver_number": [1, 9, 2], "position": [1, None, 2], "number_of_laps": [1, 1, 1]})
    cond = pd.DataFrame({"weather_status": ["measured"] * 3})
    checks = {c["check_name"]: c for c in transform.consistency_checks(df, cond, results, 0)}
    assert checks["final_order_vs_results"]["value"] == 2


def test_results_table_status():
    raw = [{"driver_number": 1, "position": 1, "number_of_laps": 50, "points": 25, "dnf": False, "dns": False,
            "dsq": False},
           {"driver_number": 2, "position": None, "number_of_laps": 10, "points": 0, "dnf": True, "dns": False,
            "dsq": False},
           {"driver_number": 99, "position": None, "number_of_laps": 0, "points": 0, "dnf": False, "dns": True,
            "dsq": False}]
    out = transform.results_table(raw, known_drivers={1, 2})
    assert out["status"].tolist() == ["FINISHED", "DNF"]   # pilote inconnu retiré


def test_isolated_wrong_lap_start_is_repaired_from_neighbours():
    # Cas réel (Russell, Bahreïn 2025, tour 38) : début publié 70 s trop tard, durées cohérentes.
    df = pd.DataFrame({"driver_number": 63, "lap_number": [36, 37, 38, 39],
                       "date_start": [at(0), at(95.5), at(95.5 + 95.8 + 70), at(95.5 + 95.8 + 96.2)],
                       "lap_time_s": [95.5, 95.8, 96.2, 96.4]})
    fixed = transform.repair_date_starts(df)
    assert fixed.iloc[2] == at(95.5 + 95.8)
    assert (fixed.drop(index=2) == df["date_start"].drop(index=2)).all()   # le reste ne bouge pas
    df["date_start"] = fixed
    df["lap_end"] = transform.lap_end_times(df)
    assert (df["lap_end"].diff().dt.total_seconds().dropna() < 100).all()


def test_consistent_but_slow_lap_is_not_touched():
    # Un tour lent (arrêt aux stands) garde ses heures : début et durées restent cohérents.
    df = pd.DataFrame({"driver_number": 1, "lap_number": [1, 2, 3],
                       "date_start": [at(0), at(90), at(90 + 115)], "lap_time_s": [90.0, 115.0, 90.0]})
    assert (transform.repair_date_starts(df) == df["date_start"]).all()


def test_repair_needs_both_neighbours_to_agree():
    # Durée du tour précédent manquante : on ne sait pas qui a tort, on ne corrige pas.
    df = pd.DataFrame({"driver_number": 1, "lap_number": [1, 2, 3],
                       "date_start": [at(0), at(160), at(180)], "lap_time_s": [np.nan, 90.0, 90.0]})
    assert (transform.repair_date_starts(df) == df["date_start"]).all()
