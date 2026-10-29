import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError

from f1engine.db import create_schema, split_statements


@pytest.fixture
def engine():
    eng = create_engine("sqlite://")
    create_schema(eng)
    with eng.begin() as conn:
        conn.execute(text("INSERT INTO sessions VALUES (1, 1, 2025, 'Test', 'X', '2025-01-01', 50)"))
        conn.execute(text("INSERT INTO drivers VALUES (1, 4, 'NOR', 'Lando Norris', 'McLaren')"))
    return eng


def test_split_statements_ignores_comments():
    sql = "-- a; b\nSELECT 1; -- c;\nSELECT 2;"
    assert split_statements(sql) == ["SELECT 1", "SELECT 2"]


@pytest.mark.parametrize("compound, age", [("SUPERSOFT", 0), ("SOFT", -1)])
def test_stint_constraints_reject_bad_rows(engine, compound, age):
    with pytest.raises(IntegrityError), engine.begin() as conn:
        conn.execute(text(f"INSERT INTO stints VALUES (1, 4, 1, '{compound}', 1, 10, {age})"))


def test_lap_track_status_must_be_known(engine):
    with pytest.raises(IntegrityError), engine.begin() as conn:
        conn.execute(text("INSERT INTO laps (session_key, driver_number, lap_number, track_status) "
                          "VALUES (1, 4, 2, 'PURPLE')"))
