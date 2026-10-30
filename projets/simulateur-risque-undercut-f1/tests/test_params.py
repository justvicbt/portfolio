import numpy as np
import pandas as pd
import pytest

from f1risk.ingest import valid_stint
from f1risk.params import traffic_cost


def synthetic_laps(cost=0.4, seed=0):
    """12 relais de 20 tours, pente 0,05 s/tour, air sale un tour sur trois."""
    rng = np.random.default_rng(seed)
    rows = []
    for s in range(12):
        level = rng.normal(90, 0.5)
        for age in range(20):
            gap = 0.8 if (age + s) % 3 == 0 else 3.0
            rows.append({"circuit": "Test", "driver": f"D{s}", "stint_number": 1, "lap_number": age + 2,
                         "track_status": "GREEN", "is_pit_in_lap": 0, "is_pit_out_lap": 0, "compound": "MEDIUM",
                         "exclusion": "traffic" if gap < 1.5 else None, "tyre_age": age, "gap_ahead_s": gap,
                         "lap_time_s": level + 0.05 * age + cost * (gap < 1.5) + rng.normal(0, 0.2)})
    return pd.DataFrame(rows)


def test_traffic_cost_recovers_known_value():
    cost, se = traffic_cost(synthetic_laps(cost=0.4))
    assert cost == pytest.approx(0.4, abs=3 * se) and se < 0.05


def test_inconsistent_stints_are_dropped():
    assert valid_stint({"lap_start": 1, "lap_end": 20})
    assert valid_stint({"lap_start": 30, "lap_end": None})   # relais en cours en fin de course
    assert not valid_stint({"lap_start": 3, "lap_end": 1})
