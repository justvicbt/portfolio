import pandas as pd
import pytest

from f1risk.params import SeasonData
from f1risk.validation import find_attempts

T0 = pd.Timestamp("2025-04-13T15:00:00Z")


def season(fresh_lap_a: float, offset_a: float = 1.0) -> SeasonData:
    """R mène A de `offset_a` s. A s'arrête au tour 10, R au tour 11 (20 s perdues).

    Avant l'arrêt : 90 s au tour. Après : R roule en 89 s, A en `fresh_lap_a`.
    Une troisième voiture, loin derrière, ne s'arrête pas.
    """
    plans = {"RIV": (0.0, 11, 89.0), "ATT": (offset_a, 10, fresh_lap_a), "OTH": (30.0, None, 90.0)}
    rows = []
    for driver, (offset, stop, fresh) in plans.items():
        t = offset
        for lap in range(1, 21):
            rows.append({"circuit": "Test", "driver": driver, "lap_number": lap,
                         "date_start": T0 + pd.to_timedelta(t, unit="s"), "track_status": "GREEN",
                         "compound": "MEDIUM" if stop is None or lap <= stop else "HARD",
                         "tyre_age": lap + 2 if stop is None or lap <= stop else lap - stop - 1})
            t += 90.0 + (20.0 if lap == stop else 0.0) if stop is None or lap <= stop else fresh
    pits = pd.DataFrame({"circuit": "Test", "driver": ["RIV", "ATT"], "lap_number": [11, 10]})
    empty = pd.DataFrame()
    return SeasonData(sessions=empty, laps=pd.DataFrame(rows), clean=empty, pits=pits, pit_losses=empty, rc=empty)


@pytest.mark.parametrize("fresh_lap, success", [(88.5, True), (89.5, False)])
def test_undercut_attempt_is_detected_and_scored(fresh_lap, success):
    # Début du tour 13 : A = 1 + 9x90 + 110 + 2x fresh ; R = 10x90 + 110 + 89 = 1099.
    att = find_attempts(season(fresh_lap))
    assert len(att) == 1
    row = att.iloc[0]
    assert (row["attacker"], row["rival"], row["stop_lap"], row["response"]) == ("ATT", "RIV", 10, 1)
    assert row["gap_s"] == pytest.approx(1.0)
    assert (row["attacker_old"], row["attacker_new"]) == ("MEDIUM", "HARD")
    assert row["success"] == success
    assert row["final_gap_s"] == pytest.approx(1 + 810 + 110 + 2 * fresh_lap - 1099)


def test_large_gap_is_not_an_undercut_attempt():
    assert find_attempts(season(88.5, offset_a=4.0)).empty
