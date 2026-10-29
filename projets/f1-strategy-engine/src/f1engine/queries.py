"""Exécute les requêtes de sql/queries/ et enregistre les résultats en CSV (docs/results/)."""
import pandas as pd

from .config import RESULTS_DIR, SQL_DIR
from .db import get_engine, read_sql


def run_all(show: int = 8) -> dict[str, pd.DataFrame]:
    engine = get_engine()
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    results = {}
    for path in sorted((SQL_DIR / "queries").glob("*.sql")):
        df = read_sql(engine, path.read_text())
        df.to_csv(RESULTS_DIR / f"{path.stem}.csv", index=False)
        results[path.stem] = df
        print(f"\n== {path.name} ({len(df)} lignes)")
        print(df.head(show).to_string(index=False))
    return results
