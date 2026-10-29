"""Accès à la base locale via SQLAlchemy."""
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine

from .config import SQL_DIR, database_url


def get_engine() -> Engine:
    url = database_url()
    if url.startswith("sqlite:///"):
        Path(url.removeprefix("sqlite:///")).parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(url)
    if engine.dialect.name == "sqlite":
        @event.listens_for(engine, "connect")
        def _fk_on(dbapi_conn, _):
            dbapi_conn.execute("PRAGMA foreign_keys = ON")
    return engine


def split_statements(sql: str) -> list[str]:
    """Découpe un script en instructions (les commentaires -- sont retirés)."""
    lines = [line.split("--", 1)[0] for line in sql.splitlines()]
    return [s.strip() for s in "\n".join(lines).split(";") if s.strip()]


def create_schema(engine: Engine) -> None:
    sql = (SQL_DIR / "schema.sql").read_text()
    with engine.begin() as conn:
        for stmt in split_statements(sql):
            conn.execute(text(stmt))


def read_sql(engine: Engine, sql: str, **params) -> pd.DataFrame:
    with engine.connect() as conn:
        return pd.read_sql(text(sql), conn, params=params)
