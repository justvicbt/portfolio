"""Stratégie : un enseignement s'affiche avec ses chiffres et son incertitude, ou pas du tout."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from f1cc import ui
from f1cc.analysis import negative_slopes
from f1cc.config import MAX_UNDERCUT_GAP_S, MIN_PIT_STOPS, P2_RESULTS, db_path
from f1cc.strategy import best_lap_statement, undercut_by_lap
from f1cc.text import at_laps, pct, plural

race, lap = ui.sidebar()
sk, circuit = int(race["session_key"]), race["circuit"]
path = str(db_path())
laps = ui.load("race_laps", sk)
pits = ui.load("pit_stops", sk)
results = ui.load("results", sk)

st.title("Stratégie")
st.warning("Analyse a posteriori. Les paramètres sont estimés sur toute la course, y compris les tours qui suivent "
           "le moment étudié : ce n'est pas ce que le muret savait en direct. Rien ici n'est une consigne de course.")

st.header("1 ou 2 arrêts, et quand (simulateur du moteur de stratégie)")
deg = ui.degradation(path, sk)
loss_table = ui.load("pit_loss_summary").set_index("circuit")
if not deg.ok:
    ui.insufficient("simuler les stratégies", deg.reason)
elif negative_slopes(deg.value[1]):
    ui.insufficient("simuler les stratégies", "au moins un composé a une pente négative (piste qui s'améliore plus vite "
                    "que le pneu ne s'use), le simulateur la prendrait pour un pneu qui rajeunit")
elif len(deg.value[0].compounds) < 2:
    ui.insufficient("simuler les stratégies", "un seul composé a une dégradation estimée, or le règlement en impose deux")
elif circuit not in loss_table.index or loss_table.loc[circuit, "n_stops_used"] < MIN_PIT_STOPS:
    n = 0 if circuit not in loss_table.index else int(loss_table.loc[circuit, "n_stops_used"])
    ui.insufficient("simuler les stratégies", f"{plural(n, 'arrêt mesurable', 'arrêts mesurables')} sous drapeau vert, il en faut {MIN_PIT_STOPS}")
else:
    loss, n_loss = float(loss_table.loc[circuit, "median_pit_loss_s"]), int(loss_table.loc[circuit, "n_stops_used"])
    ins = ui.stop_windows(path, sk, loss)
    c1, c2, c3 = st.columns(3)
    for col, w in ((c1, ins.one), (c2, ins.two)):
        col.metric(f"Meilleure stratégie à {w.n_stops} arrêt{'s' if w.n_stops > 1 else ''}", w.plan,
                   f"1er arrêt au tour {w.first_stop}, fenêtre {w.window[0]} à {w.window[1]}", delta_color="off")
    c3.metric("2 arrêts plus rapides que 1", f"{pct(ins.p_two_faster)} des tirages",
              f"gain estimé : {ui.fmt(ins.gain_two_s, 1, 's', signed=True)}", delta_color="off",
              help="Temps gagné par la meilleure stratégie à 2 arrêts sur la meilleure à 1 arrêt, aux paramètres "
                   "estimés et avec la perte aux stands mesurée. Négatif : 2 arrêts font perdre du temps.")

    favoured = ins.two if ins.p_two_faster >= 0.5 else ins.one
    share = max(ins.p_two_faster, 1 - ins.p_two_faster)
    if 0.2 < ins.p_two_faster < 0.8:
        st.write(f"Les deux familles de stratégies sont proches : 2 arrêts gagnent dans {pct(ins.p_two_faster)} des "
                 f"{ui.thousands(ins.n_draws)} tirages, avec une perte aux stands de {ui.fmt(loss, 1, 's')} (médiane de {plural(n_loss, 'arrêt')}). "
                 "Le modèle ne tranche pas.")
    else:
        st.write(f"Avec une perte aux stands de {ui.fmt(loss, 1, 's')} (médiane de {plural(n_loss, 'arrêt mesuré', 'arrêts mesurés')}), "
                 f"{plural(favoured.n_stops, 'arrêt')} l'emporte{'nt' if favoured.n_stops > 1 else ''}"
                 f" dans {pct(share)} des {ui.thousands(ins.n_draws)} tirages. Le premier arrêt optimal tombe entre les tours {favoured.window[0]} et "
                 f"{favoured.window[1]} dans 80 % des tirages (tour {favoured.first_stop} aux paramètres estimés).")

    classified = set(results.loc[results["status"] == "FINISHED", "driver"])
    real = pits[pits["driver"].isin(classified)]
    first = real.groupby("driver")["lap_number"].min()
    n_stops = real.groupby("driver").size().reindex(sorted(classified), fill_value=0)
    if len(first):
        st.write(f"En course : premier arrêt médian au tour {int(first.median())} "
                 f"(10e à 90e centile : {int(np.percentile(first, 10))} à {int(np.percentile(first, 90))}), "
                 + ", ".join(f"{plural(int(v), 'pilote')} à {plural(int(k), 'arrêt')}"
                             for k, v in n_stops.value_counts().sort_index().items()) + " parmi les classés.")
        med = int(first.median())
        if not favoured.window[0] <= med <= favoured.window[1]:
            side = "plus tôt" if med < favoured.window[0] else "plus tard"
            st.write(f"Le modèle et la course ne concordent pas : les pilotes se sont arrêtés {side} que la fenêtre du "
                     f"modèle (tour {med} contre {favoured.window[0]} à {favoured.window[1]}). Le modèle ignore ce qui "
                     "décide souvent du moment en course : la chute brutale du pneu, la position en piste, l'undercut "
                     "des voisins, les safety cars. Sa fenêtre ne doit pas être lue comme le bon moment pour s'arrêter.")
        model = pd.Series(favoured.draws_first_stop).value_counts(normalize=True).sort_index()
        seen = first.value_counts(normalize=True).sort_index()
        fig = go.Figure()
        fig.add_trace(go.Bar(x=model.index, y=model.values, name=f"Modèle ({plural(favoured.n_stops, 'arrêt')}), tirages",
                             marker_color=ui.DUEL_COLOR[0], marker_line=dict(color="white", width=1),
                             hovertemplate="tour %{x}<br>%{y:.0%} des tirages<extra></extra>"))
        fig.add_trace(go.Bar(x=seen.index, y=seen.values, name="Premiers arrêts réels (pilotes classés)",
                             marker_color=ui.DUEL_COLOR[1], marker_line=dict(color="white", width=1),
                             hovertemplate="tour %{x}<br>%{y:.0%} des pilotes<extra></extra>"))
        fig.update_xaxes(title="Tour du premier arrêt")
        fig.update_yaxes(title="Part", tickformat=".0%")
        ui.show(ui.style(fig, height=320, barmode="group", title="Premier arrêt : modèle contre course"))
    st.caption("Limites héritées du moteur de stratégie : dégradation linéaire sans falaise, pneus neufs à chaque "
               "relais, aucune safety car, position en piste ignorée. Le modèle propose donc parfois des relais plus longs "
               "que ce que les pneus tiennent vraiment. Incertitude : tirages des paramètres de la régression "
               "(covariance clusterisée par relais).")

st.header("Undercut sur un rival (simulateur d'undercut)")
drivers = results["driver"].tolist() or sorted(laps["driver"].unique())
cp, td, sp, err = ui.undercut_params(path, circuit)


def default_pair() -> tuple[str, str]:
    """Paire restée le plus de tours de la fenêtre à moins de 3 s l'un de l'autre, sinon 2e et 1er à l'arrivée."""
    if td is None:
        return drivers[min(1, len(drivers) - 1)], drivers[0]
    w = laps[laps["lap_number"].between(*td.window) & (laps["track_status"] == "GREEN")].sort_values(
        ["lap_number", "position"])
    w = w.assign(ahead=w.groupby("lap_number")["driver"].shift(), gap=w.groupby("lap_number")["gap_to_leader_s"].diff())
    close = w[(w["gap"] > 0) & (w["gap"] <= MAX_UNDERCUT_GAP_S)]
    if close.empty:
        return drivers[min(1, len(drivers) - 1)], drivers[0]
    a, r = close.groupby(["driver", "ahead"]).size().idxmax()
    return a, r


a0, r0 = default_pair()
c1, c2 = st.columns(2)
attacker = c1.selectbox("Attaquant (derrière)", drivers, index=drivers.index(a0) if a0 in drivers else 0, key=f"uc_a_{circuit}")
others = [d for d in drivers if d != attacker]
rival = c2.selectbox("Rival (devant)", others, index=others.index(r0) if r0 in others else 0, key=f"uc_r_{circuit}")
st.caption("Paire proposée par défaut : celle qui a passé le plus de tours de la fenêtre d'arrêt à moins de 3 s "
           "l'une de l'autre.")

if err:
    ui.insufficient("simuler un undercut sur cette course", err)
    st.stop()
if len(cp.pit_losses) < MIN_PIT_STOPS or len(cp.rejoin_gaps) < MIN_PIT_STOPS:
    ui.insufficient("simuler un undercut", f"{plural(len(cp.pit_losses), 'arrêt mesuré', 'arrêts mesurés')}, il en faut {MIN_PIT_STOPS}")
    st.stop()


def situations() -> tuple[pd.DataFrame, list[str]]:
    """Situations réelles dans la fenêtre d'arrêt habituelle du circuit, jusqu'au tour courant."""
    idx = laps.set_index(["driver", "lap_number"])
    rows, skipped = [], []
    for n in range(td.window[0], min(td.window[1], lap) + 1):
        try:
            ea, er = idx.loc[(attacker, n - 1), "lap_end"], idx.loc[(rival, n - 1), "lap_end"]
            sa, sr = idx.loc[(attacker, n)], idx.loc[(rival, n)]
        except KeyError:
            skipped.append(f"tour {n} : un des deux pilotes n'a pas de données")
            continue
        gap = (ea - er).total_seconds()
        if not 0 < gap <= MAX_UNDERCUT_GAP_S:
            skipped.append(f"tour {n} : écart de {ui.fmt(gap, 1, 's', signed=True)}, hors du domaine 0 à 3 s")
        elif sa["compound"] not in cp.compounds or sr["compound"] not in cp.compounds:
            skipped.append(f"tour {n} : composé sans estimation de dégradation")
        elif sa["track_status"] != "GREEN":
            skipped.append(f"tour {n} : piste neutralisée")
        else:
            rows.append({"stop_lap": n, "gap_s": gap, "attacker_age": int(sa["tyre_age"]),
                         "rival_age": int(sr["tyre_age"]), "attacker_compound": sa["compound"],
                         "rival_compound": sr["compound"]})
    return pd.DataFrame(rows), skipped


@st.cache_data(show_spinner="Simulation de l'undercut...")
def simulate(path: str, circuit: str, attacker: str, rival: str, lap: int, table: pd.DataFrame, new: str):
    return undercut_by_lap(cp, sp, table, new)


table, skipped = situations()
st.caption(f"Fenêtre étudiée : tours {td.window[0]} à {td.window[1]} (10e à 90e centile des premiers arrêts sur ce "
           f"circuit), limitée au tour courant ({lap}).")
if table.empty:
    ui.insufficient("simuler cet undercut", "aucun tour de la fenêtre où l'attaquant est à moins de 3 s derrière "
                    "le rival, sous drapeau vert")
else:
    old = table["attacker_compound"].iloc[0]
    new = td.new if td.new != old else next(c for c in cp.compounds if c != old)
    res = simulate(path, circuit, attacker, rival, lap, table, new)
    fig = go.Figure(go.Scatter(
        x=res["stop_lap"], y=res["p_success"], mode="markers+lines", name="P(réussite)",
        line=dict(color=ui.DUEL_COLOR[0], width=2), marker=dict(size=9, line=dict(color="white", width=1.5)),
        error_y=dict(type="data", array=2 * res["mc_se"], color=ui.INK_2, thickness=1.2),
        customdata=res[["gap_s", "mean_gain_s", "p5_gain_s"]],
        hovertemplate="arrêt au tour %{x}<br>écart initial %{customdata[0]:.2f} s<br>réussite %{y:.0%}"
                      "<br>gain moyen %{customdata[1]:+.2f} s<br>5e centile %{customdata[2]:+.2f} s<extra></extra>"))
    fig.add_hline(y=0.5, line=dict(color=ui.CONTEXT_GREY, dash="dot"))
    fig.update_xaxes(title=f"Tour d'arrêt de {attacker}")
    fig.update_yaxes(title=f"Probabilité de ressortir devant {rival}", range=[0, 1], tickformat=".0%")
    ui.show(ui.style(fig, height=320, title=f"Undercut de {attacker} sur {rival}, le rival répond au tour suivant"))
    st.write(best_lap_statement(res))
    st.dataframe(res.drop(columns="n_sims"), hide_index=True, width="stretch", column_config={
        "stop_lap": "Tour d'arrêt", "gap_s": st.column_config.NumberColumn("Écart initial (s)", format="%.2f"),
        "p_success": st.column_config.NumberColumn("P(réussite)", format="percent"),
        "mc_se": st.column_config.NumberColumn("Erreur Monte Carlo", format="percent"),
        "mean_gain_s": st.column_config.NumberColumn("Gain moyen (s)", format="%+.2f"),
        "p5_gain_s": st.column_config.NumberColumn("5e centile du gain (s)", format="%+.2f")})
    real_a = pits[(pits["driver"] == attacker) & pits["lap_number"].between(*td.window)]["lap_number"].tolist()
    real_r = pits[(pits["driver"] == rival) & pits["lap_number"].between(*td.window)]["lap_number"].tolist()
    def stopped(drv, stops):
        return f"{drv} s'est arrêté {at_laps(stops)}" if stops else f"{drv} ne s'est pas arrêté"
    st.caption(f"En course, dans cette fenêtre : {stopped(attacker, real_a)}, {stopped(rival, real_r)}. "
               f"Chaque point repose sur {ui.thousands(int(res['n_sims'].iloc[0]))} "
               f"scénarios ; barres : ± 2 erreurs Monte Carlo. Pneu chaussé à l'arrêt : "
               f"{ui.COMPOUND_LABEL[new].lower()} pour les deux.")
if skipped:
    with st.expander(f"{plural(len(skipped), 'tour')} de la fenêtre non "
                     f"{'simulés' if len(skipped) > 1 else 'simulé'}"):
        st.write("\n".join(f"- {s}" for s in skipped))

try:
    v = pd.read_csv(P2_RESULTS / "validation_summary.csv").iloc[0]
    st.caption(f"Fiabilité du simulateur d'undercut : sur {int(v['n_evaluated'])} vraies tentatives de 2025, score de "
               f"Brier de {ui.fmt(v['brier_simulator'], 3)} contre {ui.fmt(v['brier_observed_rate'], 3)} pour une "
               "probabilité constante. La différence n'est pas significative : les données ne contredisent pas le "
               "simulateur, sans prouver qu'il prédit bien. Paramètres de saison (safety cars, air sale) issus des "
               "24 courses du simulateur d'undercut ; paramètres du circuit estimés sur cette course, pilotes compris.")
except (OSError, KeyError):
    st.caption("Résultats de validation du simulateur d'undercut introuvables.")
