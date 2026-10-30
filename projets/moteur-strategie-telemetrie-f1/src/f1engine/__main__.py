"""Point d'entrée : python -m f1engine <commande>

  ingest    télécharge les courses (OpenF1) et reconstruit la base
  queries   exécute les requêtes SQL et enregistre les CSV
  analyze   modèle de dégradation, simulateur, graphiques
  all       les trois à la suite
"""
import argparse

import numpy as np
import pandas as pd

from . import ingest, queries
from .config import RESULTS_DIR, SQL_DIR, fuel_model
from .db import get_engine, read_sql
from .degradation import fit_all, robustness
from .plots import degradation_chart, strategy_chart, telemetry_chart
from .strategy import compare


def analyze(duel_circuit: str = "Monza", duel_drivers: tuple[str, str] = ("VER", "NOR")) -> None:
    engine = get_engine()
    fuel = fuel_model()
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    pd.set_option("display.width", 200)

    fits_a, table_a = fit_all(engine, fuel, estimate_trend=False)
    fits_b, table_b = fit_all(engine, fuel, estimate_trend=True)
    table = pd.concat([table_a, table_b], ignore_index=True)
    table.round(4).to_csv(RESULTS_DIR / "degradation.csv", index=False)
    print("\n== Dégradation (s/tour d'âge, IC 95 %)")
    print(table[["model", "circuit", "compound", "n_laps", "n_stints", "slope_s_per_lap", "slope_ci_low",
                 "slope_ci_high", "offset_vs_ref_s", "residual_trend_s_per_lap"]].round(3).to_string(index=False))

    rob = robustness(engine, fuel)
    rob.round(4).to_csv(RESULTS_DIR / "degradation_robustness.csv", index=False)
    print("\n== Sensibilité des pentes à l'hypothèse carburant (s/kg)")
    print(rob.pivot_table(index=["circuit", "compound"], columns="fuel_sec_per_kg").round(3).to_string())

    pit_loss = read_sql(engine, (SQL_DIR / "queries" / "04_pit_loss.sql").read_text())
    loss = pit_loss.set_index("circuit")["median_pit_loss_s"]
    comparisons, rows = [], []
    for fits in (fits_a, fits_b):
        for circuit, fit in fits.items():
            comp = compare(fit)
            comparisons.append(comp)
            t1, t2 = comp.total_times(loss[circuit])
            lo, hi = np.percentile(comp.breakeven_draws, [5, 95])
            rows.append({
                "model": comp.model, "circuit": circuit, "laps": fit.total_laps,
                "best_1_stop": comp.one_stop.describe(), "best_2_stop": comp.two_stop.describe(),
                "breakeven_pit_loss_s": round(comp.breakeven_s, 1), "breakeven_p5": round(lo, 1),
                "breakeven_p95": round(hi, 1), "measured_pit_loss_s": loss[circuit],
                "two_stop_gain_s": round(t1 - t2, 1),
                "p_two_stop_faster": round(float(comp.prob_two_stop_faster(loss[circuit])[0]), 3),
            })
    strat = pd.DataFrame(rows)
    strat.to_csv(RESULTS_DIR / "strategy.csv", index=False)
    print("\n== 1 arrêt vs 2 arrêts (perte aux stands = médiane mesurée, requête 04)")
    print(strat.to_string(index=False))

    tel = read_sql(engine, """
        SELECT d.acronym, t.distance_m, t.speed_kmh, t.throttle_pct, t.brake_on, t.sector,
               l.lap_time_s, l.compound, l.tyre_age
        FROM telemetry t
        JOIN sessions s USING (session_key)
        JOIN drivers d ON d.session_key = t.session_key AND d.driver_number = t.driver_number
        JOIN laps l ON l.session_key = t.session_key AND l.driver_number = t.driver_number
                   AND l.lap_number = t.lap_number
        WHERE s.circuit = :circuit AND d.acronym IN (:d1, :d2)
        ORDER BY d.acronym, t.sample_idx""", circuit=duel_circuit, d1=duel_drivers[0], d2=duel_drivers[1])
    info = {}
    for drv, g in tel.groupby("acronym"):
        lap_time = g["lap_time_s"].iloc[0]
        info[drv] = (f"{int(lap_time // 60)}:{lap_time % 60:06.3f}, "
                     f"{g['compound'].iloc[0].lower()} {int(g['tyre_age'].iloc[0])} tours")
    paths = [degradation_chart(table), strategy_chart(comparisons, pit_loss),
             telemetry_chart(tel, duel_circuit, duel_drivers, info)]
    print("\nGraphiques :", *paths, sep="\n  ")


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m f1engine", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=["ingest", "queries", "analyze", "all"])
    args = parser.parse_args()
    if args.command in ("ingest", "all"):
        ingest.main()
    if args.command in ("queries", "all"):
        queries.run_all()
    if args.command in ("analyze", "all"):
        analyze()


if __name__ == "__main__":
    main()
