"""Rythme et pneus : relais, rythme sur tours propres, dégradation avec incertitude."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from f1cc import ui
from f1cc.analysis import negative_slopes, stint_slopes
from f1cc.config import MIN_LAPS, MIN_STINT_LAPS, MIN_STINTS, db_path

race, lap = ui.sidebar()
sk = int(race["session_key"])
laps = ui.load("race_laps", sk)
stints = ui.load("stints", sk)
results = ui.load("results", sk)
clean = ui.load("clean_laps", sk)

st.title("Rythme et pneus")

# Chronologie des relais, pilotes dans l'ordre d'arrivée.
st.subheader("Relais de chaque pilote")
order = [d for d in results["driver"] if d in set(stints["driver"])] or sorted(stints["driver"].unique())
fig = go.Figure()
for compound, g in stints.groupby("compound"):
    g = g[g["lap_start"] <= lap]
    end = g["lap_end"].clip(upper=lap)
    fig.add_trace(go.Bar(
        y=g["driver"], x=end - g["lap_start"] + 1, base=g["lap_start"] - 0.5, orientation="h",
        marker=dict(color=ui.COMPOUND_COLOR.get(compound, "#898781"), line=dict(color="white", width=2)),
        name=ui.COMPOUND_LABEL.get(compound, compound),
        customdata=g[["stint_number", "lap_start", "lap_end", "tyre_age_at_start"]],
        hovertemplate="%{y}, relais %{customdata[0]}<br>tours %{customdata[1]} à %{customdata[2]}"
                      "<br>âge au départ : %{customdata[3]} tours<extra></extra>"))
fig.update_yaxes(categoryorder="array", categoryarray=order[::-1], title=None)
fig.update_xaxes(title="Tour", range=[0.5, int(race["total_laps"]) + 0.5])
ui.show(ui.style(fig, height=max(380, 22 * len(order)), barmode="overlay"))

# Rythme d'un pilote : tours propres corrigés du carburant, et tours écartés.
st.subheader("Rythme d'un pilote")
driver = st.selectbox("Pilote", order, key="pace_driver")
d_laps = laps[(laps["driver"] == driver) & (laps["lap_number"] <= lap)]
d_clean = clean[(clean["driver"] == driver) & (clean["lap_number"] <= lap)]
fig = go.Figure()
excluded = d_laps[d_laps["is_clean"] == 0]
fig.add_trace(go.Scatter(x=excluded["lap_number"], y=excluded["lap_time_s"], mode="markers", name="Tour écarté (brut)",
                         marker=dict(color=ui.CONTEXT_GREY, size=8, symbol="circle-open"),
                         customdata=excluded[["exclusion"]],
                         hovertemplate="tour %{x}<br>%{y:.3f} s<br>écarté : %{customdata[0]}<extra></extra>"))
for compound, g in d_clean.groupby("compound"):
    fig.add_trace(go.Scatter(x=g["lap_number"], y=g["fuel_corr_s"], mode="markers",
                             name=f"{ui.COMPOUND_LABEL[compound]}, corrigé du carburant",
                             marker=dict(color=ui.COMPOUND_COLOR[compound], size=8, line=dict(color="white", width=1)),
                             customdata=g[["tyre_age", "lap_time_s"]],
                             hovertemplate="tour %{x}<br>corrigé : %{y:.3f} s<br>brut : %{customdata[1]:.3f} s"
                                           "<br>âge du pneu : %{customdata[0]}<extra></extra>"))
fig.update_xaxes(title="Tour")
fig.update_yaxes(title="Temps au tour (s)")
# Les tours très lents (stands, SC) écraseraient l'échelle : on cadre sur les tours propres.
if len(d_clean):
    lo, hi = d_clean["fuel_corr_s"].min(), max(d_clean["lap_time_s"].max(), d_clean["fuel_corr_s"].max())
    fig.update_yaxes(range=[lo - 1, hi + 2])
ui.show(ui.style(fig))
st.caption("Tour propre (règles du projet 1) : hors 1er tour, arrêts, neutralisations, pneus pluie, trafic à moins "
           "de 1,5 s et tours au-delà de 107 % de la médiane. Correction carburant : 0,03 s par kg, 100 kg au départ, "
           "hypothèse du projet 1.")

# Dégradation par composé : modèles A et B du projet 1
st.subheader("Dégradation par composé (modèle du projet 1)")
path = str(db_path())
fits = {m: ui.degradation(path, sk, trend) for m, trend in (("A", False), ("B", True))}
if not fits["A"].ok:
    ui.insufficient("estimer la dégradation", fits["A"].reason)
else:
    rows = [v.value[1] for v in fits.values() if v.ok]
    table = pd.concat(rows, ignore_index=True)
    fig = go.Figure()
    for m, dash, offset in (("A", "solid", -0.12), ("B", "dot", 0.12)):
        t = table[table["model"] == m]
        fig.add_trace(go.Scatter(
            x=t["slope_s_per_lap"], y=[list(ui.COMPOUND_LABEL).index(c) + offset for c in t["compound"]],
            mode="markers", name=f"Modèle {m}" + (" (carburant fixé)" if m == "A" else " (tendance de course estimée)"),
            marker=dict(size=10, color=[ui.COMPOUND_COLOR[c] for c in t["compound"]],
                        symbol="circle" if m == "A" else "diamond", line=dict(color="white", width=1.5)),
            error_x=dict(type="data", symmetric=False, array=t["slope_ci_high"] - t["slope_s_per_lap"],
                         arrayminus=t["slope_s_per_lap"] - t["slope_ci_low"], color=ui.INK_2, thickness=1.5),
            customdata=t[["compound", "slope_ci_low", "slope_ci_high", "n_laps", "n_stints"]],
            hovertemplate="%{customdata[0]}<br>pente %{x:.3f} s/tour<br>IC 95 % [%{customdata[1]:.3f} ; "
                          "%{customdata[2]:.3f}]<br>%{customdata[3]} tours, %{customdata[4]} relais<extra></extra>"))
    used = [c for c in ui.COMPOUND_LABEL if c in set(table["compound"])]
    fig.update_yaxes(tickvals=[list(ui.COMPOUND_LABEL).index(c) for c in used],
                     ticktext=[ui.COMPOUND_LABEL[c] for c in used], title=None)
    fig.update_xaxes(title="Secondes perdues par tour d'âge du pneu (IC 95 %)", zeroline=True)
    ui.show(ui.style(fig, height=300))
    show = table[["model", "compound", "slope_s_per_lap", "slope_ci_low", "slope_ci_high", "n_laps", "n_stints",
                  "max_tyre_age"]].assign(compound=lambda t: t["compound"].map(ui.COMPOUND_LABEL))
    st.dataframe(show, hide_index=True, width="stretch", column_config={
        "model": "Modèle", "compound": "Composé",
        "slope_s_per_lap": st.column_config.NumberColumn("Pente (s/tour)", format="%.3f"),
        "slope_ci_low": st.column_config.NumberColumn("IC 95 % bas", format="%.3f"),
        "slope_ci_high": st.column_config.NumberColumn("IC 95 % haut", format="%.3f"),
        "n_laps": "Tours propres", "n_stints": "Relais", "max_tyre_age": "Âge max"})
    for m in ("A", "B"):
        neg = negative_slopes(table[table["model"] == m])
        if neg:
            st.warning(f"Modèle {m} : pente négative et significative pour {', '.join(ui.COMPOUND_LABEL[c].lower() for c in neg)}. "
                       "Un pneu ne rajeunit pas : la piste s'est améliorée plus vite que le pneu ne s'usait (piste qui "
                       "sèche, gomme déposée). Cette pente ne mesure pas l'usure et ne doit pas servir à décider.")
    missing = sorted(set(clean["compound"]) - set(table["compound"]))
    if missing:
        st.caption("Composés sans estimation (moins de {} tours propres ou de {} relais) : {}.".format(
            MIN_LAPS, MIN_STINTS, ", ".join(ui.COMPOUND_LABEL[c] for c in missing)))
    st.caption("Modèle A : effet fixe pilote, pente par composé, erreurs clusterisées par relais, loi de Student. "
               "Modèle B : idem avec un terme en numéro de tour (évolution de la piste et erreur sur le carburant). "
               "Estimé sur toute la course, indépendamment du tour courant.")

# Pente par relais
st.subheader("Pente de chaque relais")
slopes = stint_slopes(clean)
ok = slopes.dropna(subset=["slope_s_per_lap"])
if ok.empty:
    ui.insufficient("une pente par relais", f"aucun relais n'a {MIN_STINT_LAPS} tours propres")
else:
    ok = ok.sort_values(["compound", "slope_s_per_lap"])
    fig = go.Figure()
    for compound, g in ok.groupby("compound", sort=False):
        label = g["driver"] + " R" + g["stint_number"].astype(str)
        fig.add_trace(go.Scatter(
            x=g["slope_s_per_lap"], y=label, mode="markers", name=ui.COMPOUND_LABEL[compound],
            marker=dict(size=9, color=ui.COMPOUND_COLOR[compound], line=dict(color="white", width=1)),
            error_x=dict(type="data", symmetric=False, array=g["ci_high"] - g["slope_s_per_lap"],
                         arrayminus=g["slope_s_per_lap"] - g["ci_low"], color=ui.INK_2, thickness=1.2),
            customdata=g[["n_laps", "first_lap", "last_lap"]],
            hovertemplate="%{y}<br>pente %{x:.3f} s/tour<br>%{customdata[0]} tours propres, tours "
                          "%{customdata[1]} à %{customdata[2]}<extra></extra>"))
    fig.update_xaxes(title="Pente dans le relais (s/tour, IC 95 %)", zeroline=True)
    fig.update_yaxes(title=None)
    ui.show(ui.style(fig, height=max(320, 18 * len(ok))))
    st.caption(f"{len(ok)} relais sur {len(slopes)} ont au moins {MIN_STINT_LAPS} tours propres. Une pente par relais "
               "mélange usure, carburant mal corrigé et gestion du pilote : les intervalles sont larges et se "
               "lisent comme un ordre de grandeur, pas comme une mesure d'usure propre.")
