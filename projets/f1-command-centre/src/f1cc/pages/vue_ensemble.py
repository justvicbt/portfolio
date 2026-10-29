"""Vue d'ensemble : classement au tour courant, positions et écart au leader tour par tour."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from f1cc import ui
from f1cc.text import join_and

race, lap = ui.sidebar()
sk = int(race["session_key"])
laps = ui.load("race_laps", sk)
windows = ui.load("neutralisations", sk, laps)
results = ui.load("results", sk)

st.title(f"{ui.CIRCUIT_LABEL.get(race['circuit'], race['circuit'])} 2025")
st.caption("Rejeu à partir des données OpenF1 de la course. Positions et écarts recalculés à partir des heures "
           "de passage sur la ligne.")

now = laps[laps["lap_number"] == lap].sort_values("position")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Tour courant", f"{lap} / {int(race['total_laps'])}")
leader = now.iloc[0]["driver"] if len(now) else "inconnu"
c2.metric("En tête à la fin du tour", leader)
past = windows[windows["lap_from"] <= lap]
c3.metric("Neutralisations jusqu'ici", f"{(past['status'] == 'SC').sum()} SC, {(past['status'] == 'VSC').sum()} VSC")
temp = now["track_temp_c"].dropna()
rain = now["rain"].dropna()
c4.metric("Piste à ce tour", f"{ui.fmt(temp.median(), 1, '°C')}" if len(temp) else "non mesurée",
          "pluie signalée" if len(rain) and rain.max() == 1 else "pas de pluie signalée", delta_color="off")

# Classement au tour courant
st.subheader(f"Classement à la fin du tour {lap}")
pits = ui.load("pit_stops", sk)
table = now[["position", "driver", "team", "gap_to_leader_s", "compound", "tyre_age"]].copy()
table["interval_s"] = table["gap_to_leader_s"].diff()
table["arrets"] = table["driver"].map(pits[pits["lap_number"] <= lap].groupby("driver").size()).fillna(0).astype(int)
table["compound"] = table["compound"].map(ui.COMPOUND_LABEL)
table["position"] = table["position"].astype("Int64")
table["tyre_age"] = table["tyre_age"].astype("Int64")
# Texte plutôt que nombre : virgule décimale, et un tiret pour le leader (pas de voiture devant).
for col in ("gap_to_leader_s", "interval_s"):
    table[col] = table[col].map(lambda x: "-" if pd.isna(x) else ui.fmt(x, 1))
st.dataframe(
    table[["position", "driver", "team", "gap_to_leader_s", "interval_s", "compound", "tyre_age", "arrets"]],
    hide_index=True, width="stretch",
    column_config={
        "position": "Pos.", "driver": "Pilote", "team": "Écurie",
        "gap_to_leader_s": st.column_config.TextColumn("Écart au leader (s)"),
        "interval_s": st.column_config.TextColumn("Écart à la voiture devant (s)"),
        "compound": "Pneu", "tyre_age": "Âge du pneu (tours)", "arrets": "Arrêts",
    })
st.caption("Un pilote doublé apparaît avec un écart supérieur à un tour. Les pilotes qui ont abandonné "
           "avant ce tour ne figurent plus dans le tableau.")

# Graphiques : tout le peloton en gris, les pilotes choisis en couleur (au plus 3).
finish_order = results["driver"].tolist() or now["driver"].tolist()
chosen = st.multiselect("Pilotes à mettre en avant (3 au plus)", finish_order, default=finish_order[:2],
                        max_selections=3)
palette = dict(zip(chosen, [ui.DUEL_COLOR[0], ui.DUEL_COLOR[1], "#1baf7a"]))
shown = laps[laps["lap_number"] <= lap]


def lines(y: str, title: str, y_title: str, reverse: bool = False) -> go.Figure:
    fig = go.Figure()
    for drv, g in shown.groupby("driver"):
        if drv in palette:
            continue
        fig.add_trace(go.Scatter(x=g["lap_number"], y=g[y], mode="lines", line=dict(color=ui.CONTEXT_GREY, width=1),
                                 name=drv, showlegend=False, hovertemplate=f"{drv}<br>tour %{{x}}<br>%{{y}}<extra></extra>"))
    for drv in chosen:
        g = shown[shown["driver"] == drv]
        fig.add_trace(go.Scatter(x=g["lap_number"], y=g[y], mode="lines", line=dict(color=palette[drv], width=2.5),
                                 name=drv, hovertemplate=f"{drv}<br>tour %{{x}}<br>%{{y:.1f}}<extra></extra>"))
    ui.shade_neutralisations(fig, windows, max_lap=lap)
    fig.update_xaxes(title="Tour")
    fig.update_yaxes(title=y_title, autorange="reversed" if reverse else True)
    return ui.style(fig, title=title)


ui.show(lines("position", "Positions tour par tour", "Position", reverse=True))
ui.show(lines("gap_to_leader_s", "Écart au leader à la fin de chaque tour", "Secondes"))
repaired = laps[laps["timing_repaired"] == 1]
if len(repaired):
    st.caption("Heures de passage corrigées : OpenF1 publie pour "
               + join_and([f"{r.driver} au tour {r.lap_number}" for r in repaired.itertuples()])
               + " un début de tour incohérent avec les tours voisins (de 3 à 70 s d'écart sur ces courses). Je "
               "le remplace par le début du tour précédent plus sa durée ; sans cette correction, la position et "
               "l'écart de ces tours seraient faux. Détail sur la page Qualité des données.")
st.caption("Bandes grises : safety car, VSC ou drapeau rouge, reconstruits à partir des messages de la direction "
           "de course (code du projet 1). Leurs bornes sont exprimées en tours du leader.")
