"""Point d'entrée : python -m f1risk <commande>

  ingest    télécharge la saison (OpenF1, code du projet 1) et construit la base
  analyze   paramètres, simulations, validation, graphiques et CSV
  all       les deux à la suite
"""
import argparse
from dataclasses import replace

import numpy as np
import pandas as pd

from . import ingest
from .config import MAIN_CIRCUITS, N_SIMS, RESULTS_DIR, SEED, get_engine
from .params import (circuit_params, load_season, neutralisation_events, neutralised_pit_ratios,
                     season_params, typical_duel)
from .simulator import SCENARIOS, Assumptions, Duel, run, summarize
from .validation import calibration, find_attempts, predict

REFERENCE = "undercut_rival_responds"


def save(df: pd.DataFrame, name: str) -> None:
    df.to_csv(RESULTS_DIR / name, index=False, float_format="%.4g")


def sensitivity_factors(sp) -> dict[str, tuple[dict, dict]]:
    """Chaque levier : (réglage bas, réglage haut). Les clés `pace_diff_s` modifient le duel."""
    lo, hi = np.percentile(sp.sc_ratios, [10, 90])
    return {
        "Variabilité des arrêts (fixe / x2)": ({"loss_spread": 0.0}, {"loss_spread": 2.0}),
        "Probabilité de SC/VSC (0 / x2)": ({"sc_scale": 0.0}, {"sc_scale": 2.0}),
        f"Perte aux stands sous SC ({lo * 100:.0f} % / {hi * 100:.0f} % de la normale)": ({"sc_ratio": lo}, {"sc_ratio": hi}),
        "Air sale à la sortie (0 / x2)": ({"traffic_scale": 0.0}, {"traffic_scale": 2.0}),
        "Pente du pneu usé (bas / haut de l'IC 95 %)": ({"slope_shift": -1.96}, {"slope_shift": 1.96}),
        "Gain du pneu neuf (bas / haut de l'IC 95 %)": ({"offset_shift": 1.96}, {"offset_shift": -1.96}),
        "Bruit tour par tour (0 / x2)": ({"noise_scale": 0.0}, {"noise_scale": 2.0}),
        "Évolution de la piste (0 / x3)": ({"evo_scale": 0.0}, {"evo_scale": 3.0}),
        "Rythme de l'attaquant (0,2 s/tour plus lent / plus rapide)": ({"pace_diff_s": 0.2}, {"pace_diff_s": -0.2}),
    }


def simulate(cp, sp, duel, seed, a=Assumptions(), n=N_SIMS) -> dict[str, np.ndarray]:
    return run(cp, sp, duel, n, np.random.default_rng(seed), a)


def analyze() -> None:
    from .plots import decision_map_chart, risk_reward_chart, sensitivity_chart, validation_chart

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    pd.set_option("display.width", 200)
    data = load_season(get_engine())

    # 1. Paramètres de saison
    events, ratios = neutralisation_events(data), neutralised_pit_ratios(data)
    sp = season_params(data, events=events, ratios=ratios)
    save(events.drop(columns="start"), "neutralisations.csv")
    save(ratios, "neutralised_pit_losses.csv")
    season_table = pd.DataFrame([
        {"parameter": "sc_rate_per_lap", "value": sp.sc_rate, "detail": f"{sp.sc_events} SC / {sp.exposure_laps} tours"},
        {"parameter": "vsc_rate_per_lap", "value": sp.vsc_rate, "detail": f"{sp.vsc_events} VSC / {sp.exposure_laps} tours"},
        {"parameter": "sc_pit_loss_ratio_median", "value": np.median(sp.sc_ratios), "detail": f"{len(sp.sc_ratios)} arrêts"},
        {"parameter": "vsc_pit_loss_ratio_median", "value": np.median(sp.vsc_ratios), "detail": f"{len(sp.vsc_ratios)} arrêts"},
        {"parameter": "dirty_air_cost_s_per_lap", "value": sp.traffic_cost_s, "detail": f"erreur standard {sp.traffic_cost_se:.3f}"},
    ])
    save(season_table, "season_parameters.csv")
    print("\n== Paramètres de saison")
    print(season_table.to_string(index=False))

    # 2. Vraies tentatives d'undercut (leur écart médian sert de scénario de référence)
    attempts = find_attempts(data)
    ref_gap = float(np.round(attempts["gap_s"].median() * 2) / 2)

    # 3. Paramètres par circuit et scénario de référence
    circuits, rows = {}, []
    for c in MAIN_CIRCUITS:
        cp = circuit_params(data, c)
        td = typical_duel(data, cp)
        circuits[c] = (cp, td)
        rows.append({
            "circuit": c, "compounds": " > ".join([td.old, td.new]),
            "slope_old_s_per_lap": cp.pace_mean[cp.slope(td.old)], "slope_old_se": cp.se(cp.slope(td.old)),
            "offset_new_vs_old_s": cp.pace_mean[cp.offset(td.new)] - cp.pace_mean[cp.offset(td.old)],
            "track_evolution_s_per_lap": cp.pace_mean[cp.evo], "track_evolution_se": cp.se(cp.evo),
            "lap_noise_s": cp.lap_noise_s, "n_pit_stops": len(cp.pit_losses),
            "pit_loss_median_s": np.median(cp.pit_losses), "pit_loss_p10_s": np.percentile(cp.pit_losses, 10),
            "pit_loss_p90_s": np.percentile(cp.pit_losses, 90),
            "p_rejoin_in_traffic": (cp.rejoin_gaps < 1.5).mean(), "n_rejoins": len(cp.rejoin_gaps),
            "stop_window": f"{td.window[0]}-{td.window[1]}", "median_first_stop": td.median_stop,
        })
    circuit_table = pd.DataFrame(rows)
    save(circuit_table, "circuit_parameters.csv")
    print(f"\n== Paramètres par circuit (écart de référence : {ref_gap} s)")
    print(circuit_table.round(3).to_string(index=False))

    def base_duel(td, stop_lap, gap=ref_gap, age_diff=0):
        return Duel(stop_lap=stop_lap, gap_s=gap, rival_age=stop_lap - 1 + td.start_age,
                    age_diff=age_diff, old=td.old, new=td.new)

    # 4. Risque et gain par tour d'arrêt
    rows = []
    for c, (cp, td) in circuits.items():
        for n in range(td.window[0], td.window[1] + 1):
            res = simulate(cp, sp, base_duel(td, n), SEED + n)
            for name, gaps in res.items():
                rows.append({"circuit": c, "stop_lap": n, "scenario": name, **summarize(ref_gap, gaps),
                             "p_better_than_nothing": float((gaps < res["do_nothing"]).mean())})
    by_lap = pd.DataFrame(rows)
    save(by_lap, "risk_by_stop_lap.csv")
    print("\n== Undercut, rival qui répond au tour suivant (tour d'arrêt médian)")
    med = by_lap[by_lap["stop_lap"] == by_lap["circuit"].map({c: td.median_stop for c, (_, td) in circuits.items()})]
    print(med.round(3).to_string(index=False))

    # 5. Carte de décision : écart initial x différence d'âge des pneus, au tour d'arrêt médian
    gaps_grid = np.round(np.arange(0.25, 4.01, 0.25), 2)
    ages_grid = np.arange(-6, 7)
    rows = []
    for c, (cp, td) in circuits.items():
        for g in gaps_grid:
            for da in ages_grid:
                duel = base_duel(td, td.median_stop, gap=g, age_diff=int(da))
                if duel.attacker_age < 0:
                    continue
                res = simulate(cp, sp, duel, SEED, n=5_000)
                rows.append({"circuit": c, "gap_s": g, "age_diff": int(da), "stop_lap": td.median_stop,
                             **summarize(g, res[REFERENCE])})
    grid = pd.DataFrame(rows)
    save(grid, "decision_map.csv")

    # 6. Sensibilité, au scénario de référence
    rows = []
    for c, (cp, td) in circuits.items():
        duel = base_duel(td, td.median_stop)
        ref = summarize(ref_gap, simulate(cp, sp, duel, SEED)[REFERENCE])
        for factor, settings in sensitivity_factors(sp).items():
            for level, s in zip(("low", "high"), settings):
                s = dict(s)
                d = replace(duel, pace_diff_s=s.pop("pace_diff_s")) if "pace_diff_s" in s else duel
                out = summarize(ref_gap, simulate(cp, sp, d, SEED, Assumptions(**s))[REFERENCE])
                rows.append({"circuit": c, "factor": factor, "level": level,
                             "p_success": out["p_success"], "p_success_ref": ref["p_success"],
                             "cvar5_gain_s": out["cvar5_gain_s"], "cvar5_gain_ref_s": ref["cvar5_gain_s"]})
    sens = pd.DataFrame(rows)
    save(sens, "sensitivity.csv")
    spread = (sens.groupby(["factor", "circuit"])["p_success"].agg(lambda x: x.max() - x.min())
              .unstack().assign(mean=lambda t: t.mean(axis=1)).sort_values("mean", ascending=False))
    print("\n== Sensibilité : amplitude de P(succès) entre réglage bas et haut")
    print(spread.round(3).to_string())

    # 7. Évolution de la piste : effet sur l'écart entre deux voitures
    evo = circuit_table[["circuit", "track_evolution_s_per_lap", "track_evolution_se", "pit_loss_median_s"]].copy()
    lap_time = data.clean.groupby("circuit")["lap_time_s"].median()
    evo["median_lap_s"] = evo["circuit"].map(lap_time)
    # Les deux voitures roulent les mêmes tours : l'effet est nul dans le modèle. En réalité,
    # A passe au plus (écart + perte aux stands) secondes après R : borne de l'effet sur 3 tours.
    evo["max_time_offset_s"] = ref_gap + evo["pit_loss_median_s"]
    evo["bound_effect_3_laps_s"] = (3 * evo["track_evolution_s_per_lap"].abs()
                                    * evo["max_time_offset_s"] / evo["median_lap_s"])
    save(evo, "track_evolution.csv")
    print("\n== Évolution de la piste")
    print(evo.round(4).to_string(index=False))

    # 8. Validation sur les vraies tentatives (paramètres estimés hors échantillon)
    pred = predict(data, attempts, n_sims=5_000, seed=SEED)
    save(pred, "validation_attempts.csv")
    summary, calib = calibration(pred, seed=SEED)
    save(pd.DataFrame([summary]), "validation_summary.csv")
    save(calib, "validation_calibration.csv")
    print("\n== Validation")
    print(pd.Series(summary).to_string())
    print(calib.round(3).to_string(index=False))
    skipped = pred["skipped"].dropna().value_counts()
    if len(skipped):
        print("Tentatives non évaluées :\n" + skipped.to_string())

    paths = [risk_reward_chart(by_lap, circuits, ref_gap), decision_map_chart(grid),
             sensitivity_chart(sens), validation_chart(pred, calib)]
    print("\nGraphiques :", *paths, sep="\n  ")


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m f1risk", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=["ingest", "analyze", "all"])
    args = parser.parse_args()
    if args.command in ("ingest", "all"):
        ingest.main()
    if args.command in ("analyze", "all"):
        analyze()


if __name__ == "__main__":
    main()
