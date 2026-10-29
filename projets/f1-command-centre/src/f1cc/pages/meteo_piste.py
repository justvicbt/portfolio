"""Météo et piste : conditions pendant la course, et lien entre température de piste et rythme."""
import plotly.graph_objects as go
import streamlit as st

from f1cc import ui
from f1cc.analysis import pace_residuals, rain_comparison, temperature_effect
from f1cc.config import db_path
from f1cc.data import leader_lap_at
from f1cc.text import plural

race, lap = ui.sidebar()
sk = int(race["session_key"])
laps = ui.load("race_laps", sk)
weather = ui.load("weather", sk)
windows = ui.load("neutralisations", sk, laps)

st.title("Météo et piste")
st.caption("OpenF1 donne une mesure météo par minute environ. La pluie n'est qu'un indicateur oui / non, "
           "sans quantité. Il n'existe pas de mesure d'état de la piste : on la déduit des messages de la "
           "direction de course (bandes grises) et de la température de piste.")

if weather.empty:
    ui.insufficient("afficher la météo", "aucune mesure météo pour cette course")
    st.stop()

w = weather.assign(lap=leader_lap_at(laps, weather["date"]))
w = w[w["lap"] <= lap]

# Températures : même unité, même axe.
fig = go.Figure()
for col, name, color in (("track_temp_c", "Piste", ui.DUEL_COLOR[1]), ("air_temp_c", "Air", ui.DUEL_COLOR[0])):
    fig.add_trace(go.Scatter(x=w["date"], y=w[col], mode="lines", name=name, line=dict(color=color, width=2),
                             customdata=w[["lap"]], hovertemplate=f"{name} : %{{y:.1f}} °C<br>tour du leader "
                                                                  "%{customdata[0]}<extra></extra>"))
ui.shade_neutralisations(fig, windows[windows["lap_from"] <= lap], x="time")
fig.update_yaxes(title="°C")
fig.update_xaxes(title="Heure (UTC)")
ui.show(ui.style(fig, title="Température de l'air et de la piste"))

c1, c2 = st.columns(2)
with c1:
    fig = go.Figure(go.Scatter(x=w["date"], y=w["humidity_pct"], mode="lines", line=dict(color=ui.INK_2, width=2),
                               name="Humidité", hovertemplate="%{y:.0f} %<extra></extra>"))
    fig.update_yaxes(title="%")
    ui.show(ui.style(fig, height=260, title="Humidité"))
with c2:
    fig = go.Figure(go.Scatter(x=w["date"], y=w["wind_speed_ms"], mode="lines", line=dict(color=ui.INK_2, width=2),
                               name="Vent", hovertemplate="%{y:.1f} m/s<extra></extra>"))
    fig.update_yaxes(title="m/s")
    ui.show(ui.style(fig, height=260, title="Vitesse du vent"))

rainy = w[w["rainfall"] == 1]
fig = go.Figure(go.Bar(x=w["date"], y=w["rainfall"].fillna(0), marker_color=ui.DUEL_COLOR[0], name="Pluie",
                       hovertemplate="%{x|%H:%M}<br>pluie signalée : %{y}<extra></extra>"))
fig.update_yaxes(tickvals=[0, 1], ticktext=["non", "oui"], range=[0, 1.1])
ui.show(ui.style(fig, height=180, title="Pluie signalée (indicateur par mesure)"))
st.caption(f"{plural(len(rainy), 'mesure')} sur {len(w)} {'signalent' if len(rainy) > 1 else 'signale'} de la pluie "
           f"jusqu'au tour {lap}.")

# Lien entre température de piste et rythme
st.subheader("La température de piste change-t-elle le rythme ?")
path = str(db_path())
clean = ui.load("clean_laps", sk)
deg = ui.degradation(path, sk)
if not deg.ok:
    ui.insufficient("relier température et rythme", deg.reason)
else:
    fit, _ = deg.value
    res = temperature_effect(clean, fit.compounds, fit.reference)
    resid = pace_residuals(fit, clean).dropna(subset=["track_temp_c"])
    if not res.ok:
        ui.insufficient("relier température et rythme", res.reason)
    else:
        e = res.value
        fig = go.Figure()
        for compound, g in resid.groupby("compound"):
            fig.add_trace(go.Scatter(x=g["track_temp_c"], y=g["residual_s"], mode="markers",
                                     name=ui.COMPOUND_LABEL[compound],
                                     marker=dict(color=ui.COMPOUND_COLOR[compound], size=8, opacity=0.7),
                                     customdata=g[["driver", "lap_number"]],
                                     hovertemplate="%{customdata[0]}, tour %{customdata[1]}<br>piste %{x:.1f} °C"
                                                   "<br>écart au modèle %{y:+.2f} s<extra></extra>"))
        fig.add_hline(y=0, line_color=ui.CONTEXT_GREY)
        fig.update_xaxes(title="Température de piste pendant le tour (°C)")
        fig.update_yaxes(title="Écart au temps prédit (s)")
        ui.show(ui.style(fig, title="Écart de chaque tour propre au modèle de dégradation (calcul C)"))

        c1, c2, c3 = st.columns(3)
        c1.metric("Effet par °C, sans tendance", ui.fmt(e.coef_s_per_deg, 3, "s", signed=True),
                  f"IC 95 % [{ui.fmt(e.ci[0], 3)} ; {ui.fmt(e.ci[1], 3)}]", delta_color="off")
        c2.metric("Effet par °C, avec tendance de course", ui.fmt(e.coef_with_trend, 3, "s", signed=True),
                  f"IC 95 % [{ui.fmt(e.ci_with_trend[0], 3)} ; {ui.fmt(e.ci_with_trend[1], 3)}]", delta_color="off")
        c3.metric("Corrélation température / numéro de tour", ui.fmt(e.corr_temp_lap, 2, signed=True),
                  f"piste de {ui.fmt(e.temp_range[0])} à {ui.fmt(e.temp_range[1], 1, '°C')}", delta_color="off")
        if e.conclusive:
            st.success(f"Résultat concluant sur cette course : un degré de plus sur la piste change le temps au tour de "
                       f"{ui.fmt(e.coef_s_per_deg, 3, 's', signed=True)} (IC 95 % [{ui.fmt(e.ci[0], 3)} ; "
                       f"{ui.fmt(e.ci[1], 3)}]), sur {plural(e.n_laps, 'tour propre', 'tours propres')} et {e.n_stints} relais.")
        else:
            reasons = " ; ".join(e.reasons)
            st.warning(f"Résultat non concluant : {reasons}.")
        st.caption("Modèle : celui du projet 1 (pilote, composé, âge du pneu, carburant corrigé) auquel j'ajoute la "
                   "température de piste, puis la même chose avec un terme en numéro de tour. Erreurs clusterisées "
                   "par relais. Dans une seule course, la température évolue avec l'heure, donc avec le carburant "
                   "brûlé et la gomme déposée : ces effets sont difficiles à séparer.")

st.subheader("Tours avec et sans pluie signalée (descriptif)")
rain = rain_comparison(laps)
if rain.empty or rain["rain"].nunique() < 2:
    st.caption("Pas de tours en vert à la fois avec et sans pluie signalée : pas de comparaison possible.")
else:
    rain = rain.assign(compound=rain["compound"].map(ui.COMPOUND_LABEL),
                       rain=rain["rain"].map({0: "non", 1: "oui"}))
    st.dataframe(rain, hide_index=True, width="stretch", column_config={
        "compound": "Composé", "rain": "Pluie signalée",
        "median_lap_s": st.column_config.NumberColumn("Temps médian (s)", format="%.3f"), "n_laps": "Tours"})
    st.caption("Temps bruts, tours en vert hors arrêts et 1er tour, sans correction de pilote, de pneu ni de "
               "carburant. C'est une lecture des données, pas un effet mesuré.")
