import numpy as np
import pandas as pd
import pytest

from f1engine.cleaning import (
    assign_track_status,
    attach_tyres,
    fuel_corrected,
    gap_ahead,
    mark_clean,
    neutralisation_windows,
)
from f1engine.config import CleaningRules, FuelModel

T0 = pd.Timestamp("2025-04-13T15:00:00Z")


def at(seconds: float) -> pd.Timestamp:
    return T0 + pd.to_timedelta(seconds, unit="s")


def rc(rows):
    df = pd.DataFrame(rows, columns=["date", "category", "flag", "scope", "sector", "message"])
    df["date"] = df["date"].map(at)
    return df


def laps_every_100s(n_laps: int, driver: int = 1) -> pd.DataFrame:
    return pd.DataFrame({
        "driver_number": driver,
        "lap_number": np.arange(1, n_laps + 1),
        "date_start": [at(100 * i) for i in range(n_laps)],
        "lap_time_s": 100.0,
    })


def test_safety_car_window_runs_until_track_clear_plus_buffer():
    w = neutralisation_windows(rc([
        (1000, "SafetyCar", None, None, None, "SAFETY CAR DEPLOYED"),
        (1300, "SafetyCar", None, None, None, "SAFETY CAR IN THIS LAP"),
        (1400, "Flag", "CLEAR", "Track", None, "TRACK CLEAR"),
    ]), CleaningRules(sc_buffer_s=30))
    assert len(w) == 1
    row = w.iloc[0]
    assert row["status"] == "SC"
    assert row["start"] == at(1000) and row["end"] == at(1430)


def test_virtual_safety_car_is_not_mistaken_for_safety_car():
    w = neutralisation_windows(rc([
        (500, "SafetyCar", None, None, None, "VIRTUAL SAFETY CAR DEPLOYED"),
        (600, "SafetyCar", None, None, None, "VIRTUAL SAFETY CAR ENDING"),
    ]))
    assert w["status"].tolist() == ["VSC"]


def test_sector_yellow_closed_by_matching_sector_clear_or_fallback():
    w = neutralisation_windows(rc([
        (100, "Flag", "YELLOW", "Sector", 7, "YELLOW IN TRACK SECTOR 7"),
        (130, "Flag", "CLEAR", "Sector", 7, "CLEAR IN TRACK SECTOR 7"),
        (500, "Flag", "DOUBLE YELLOW", "Sector", 3, "DOUBLE YELLOW IN TRACK SECTOR 3"),
    ]), CleaningRules(yellow_fallback_s=60))
    w = w.sort_values("start").reset_index(drop=True)
    assert (w["status"] == "YELLOW").all()
    assert w.loc[0, "end"] == at(130)          # refermé par le CLEAR du même secteur
    assert w.loc[1, "end"] == at(560)          # jamais refermé : durée par défaut


def test_track_status_uses_overlap_and_most_severe_flag():
    laps = laps_every_100s(6)
    windows = pd.DataFrame([
        (at(150), at(160), "YELLOW"),
        (at(120), at(250), "SC"),
    ], columns=["start", "end", "status"])
    status = assign_track_status(laps, windows)
    # tour 2 = [100, 200) : jaune ET SC -> SC ; tour 3 = [200, 300) : SC ; tour 4 : vert
    assert status.tolist() == ["GREEN", "SC", "SC", "GREEN", "GREEN", "GREEN"]


def test_attach_tyres_counts_age_from_used_tyres():
    laps = laps_every_100s(6)
    stints = pd.DataFrame({
        "driver_number": [1, 1], "stint_number": [1, 2], "compound": ["SOFT", "HARD"],
        "lap_start": [1, 4], "lap_end": [3, 6], "tyre_age_at_start": [3, 0],
    })
    out = attach_tyres(laps, stints)
    assert out["compound"].tolist() == ["SOFT"] * 3 + ["HARD"] * 3
    assert out["tyre_age"].tolist() == [3, 4, 5, 0, 1, 2]
    assert out["stint_number"].tolist() == [1, 1, 1, 2, 2, 2]


def test_gap_ahead_takes_last_value_before_lap_and_ignores_lapped_text():
    laps = laps_every_100s(3)
    intervals = pd.DataFrame({
        "date": [at(95), at(105), at(195)],
        "driver_number": [1, 1, 1],
        "interval": [0.8, 5.0, "+1 LAP"],
    })
    gaps = gap_ahead(laps, intervals, tolerance_s=20)
    assert np.isnan(gaps.iloc[0])               # aucune mesure avant le tour 1
    assert gaps.iloc[1] == pytest.approx(0.8)   # mesure à 95 s, pas celle à 105 s
    assert np.isnan(gaps.iloc[2])               # "+1 LAP" n'est pas un écart en secondes


def test_mark_clean_gives_first_exclusion_reason():
    laps = pd.DataFrame({
        "driver_number": 1,
        "lap_number":     [1,       2,       3,       4,            5,         6,         7,         8],
        "lap_time_s":     [100.0,   90.0,    110.0,   90.0,         90.0,      90.0,      120.0,     90.2],
        "is_pit_in_lap":  [0,       0,       1,       0,            0,         0,         0,         0],
        "is_pit_out_lap": [0,       0,       0,       1,            0,         0,         0,         0],
        "track_status":   ["GREEN", "GREEN", "GREEN", "SC",         "SC",      "GREEN",   "GREEN",   "GREEN"],
        "compound":       ["SOFT",  "SOFT",  "SOFT",  "HARD",       "HARD",    "HARD",    "HARD",    "WET"],
        "gap_ahead_s":    [0.5,     3.0,     3.0,     3.0,          3.0,       0.9,       3.0,       3.0],
    })
    out = mark_clean(laps, CleaningRules(min_gap_ahead_s=1.5, outlier_ratio=1.07))
    assert out["exclusion"].astype(object).where(out["exclusion"].notna(), None).tolist() == [
        "lap1", None, "pit_in", "pit_out", "neutralised", "traffic", "outlier", "not_dry"]
    assert out["is_clean"].tolist() == [0, 1, 0, 0, 0, 0, 0, 0]


def test_fuel_correction_is_larger_early_in_the_race():
    fuel = FuelModel(start_kg=100, sec_per_kg=0.03)
    corr = fuel_corrected(np.array([90.0, 90.0]), np.array([1, 50]), 50, fuel)
    # tour 1 : 99 kg en moyenne -> -2,97 s ; dernier tour : 1 kg -> -0,03 s
    assert corr[0] == pytest.approx(90 - 2.97)
    assert corr[1] == pytest.approx(90 - 0.03)
    assert fuel_corrected(90.0, 10, 50, FuelModel(100, 0.0)) == pytest.approx(90.0)
