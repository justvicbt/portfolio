"""Duel : écart tour par tour entre deux pilotes, cumul, et delta le long du tour le plus rapide."""
import plotly.graph_objects as go
import streamlit as st

from f1cc import ui
from f1cc.analysis import lap_time_delta, mean_difference, telemetry_delta
from f1cc.text import plural

race, lap = ui.sidebar()
sk = int(race["session_key"])
laps = ui.load("race_laps", sk)
results = ui.load("results", sk)
pits = ui.load("pit_stops", sk)
windows = ui.load("neutralisations", sk, laps)

st.title("Duel")
drivers = results["driver"].tolist() or sorted(laps["driver"].unique())
c1, c2 = st.columns(2)
a = c1.selectbox("Pilote A", drivers, index=0, key="duel_a")
b = c2.selectbox("Pilote B", [d for d in drivers if d != a], index=0, key="duel_b")
ca, cb = ui.DUEL_COLOR

duel = lap_time_delta(laps, a, b)
duel = duel[duel["lap_number"] <= lap]
if duel.empty:
    ui.insufficient("comparer ces deux pilotes", "aucun tour commun")
    st.stop()

# Écart réel sur la ligne et cumul des écarts au tour (même grandeur, même axe).
fig = go.Figure()
fig.add_trace(go.Scatter(x=duel["lap_number"], y=duel["gap_s"], mode="lines", name="Écart sur la ligne",
                         line=dict(color=ui.INK_2, width=2.5),
                         hovertemplate="tour %{x}<br>A − B : %{y:+.2f} s<extra></extra>"))
fig.add_trace(go.Scatter(x=duel["lap_number"], y=duel["cum_delta_s"], mode="lines", name="Cumul des écarts au tour",
                         line=dict(color=ui.INK_2, width=1.5, dash="dot"),
                         hovertemplate="tour %{x}<br>cumul : %{y:+.2f} s<extra></extra>"))
for drv, color in ((a, ca), (b, cb)):
    for p in pits[(pits["driver"] == drv) & (pits["lap_number"] <= lap)].itertuples():
        fig.add_vline(x=p.lap_number, line=dict(color=color, width=1.5, dash="dash"))
    fig.add_trace(go.Scatter(x=[None], y=[None], mode="lines", line=dict(color=color, dash="dash"),
                             name=f"Arrêt de {drv}"))
ui.shade_neutralisations(fig, windows, max_lap=lap)
fig.add_hline(y=0, line_color=ui.CONTEXT_GREY)
fig.update_xaxes(title="Tour")
fig.update_yaxes(title=f"Secondes (positif : {a} derrière {b})")
ui.show(ui.style(fig, title=f"{a} contre {b} : écart à la fin de chaque tour"))
missing = int(duel["delta_s"].isna().sum())
st.caption("Écart sur la ligne : différence des heures de passage. Cumul : somme des différences de temps au tour "
           "depuis le départ, il ne compte donc pas l'écart sur la grille."
           + (f" {plural(missing, 'tour sans temps', 'tours sans temps')} pour l'un des deux "
              f"{'sont sautés' if missing > 1 else 'est sauté'} dans le cumul." if missing else ""))

fig = go.Figure(go.Bar(
    x=duel["lap_number"], y=duel["delta_s"], marker_color=[ca if d < 0 else cb for d in duel["delta_s"].fillna(0)],
    marker_line=dict(color="white", width=1), name="A − B",
    hovertemplate="tour %{x}<br>A − B : %{y:+.3f} s<extra></extra>"))
for drv, color in ((a, ca), (b, cb)):
    fig.add_trace(go.Bar(x=[None], y=[None], marker_color=color, name=f"{drv} plus rapide sur le tour"))
fig.update_xaxes(title="Tour")
fig.update_yaxes(title="Secondes", range=[-5, 5])
ui.show(ui.style(fig, height=300, title="Écart de temps au tour (A − B)"))
st.caption("Les tours d'arrêt et de neutralisation donnent de grands écarts. L'axe est coupé à ± 5 s pour rester "
           "lisible ; la valeur exacte est au survol.")

st.subheader("Écart de rythme sur les tours propres communs")
both = laps[(laps["is_clean"] == 1) & (laps["lap_number"] <= lap)].pivot_table(
    index="lap_number", columns="driver", values="lap_time_s")
diff = (both[a] - both[b]) if {a, b} <= set(both.columns) else both.iloc[:, :0].sum(axis=1)
res = mean_difference(diff)
if not res.ok:
    ui.insufficient("comparer le rythme", res.reason)
else:
    r = res.value
    faster = a if r["mean"] < 0 else b
    st.metric(f"{a} − {b}, moyenne par tour", ui.fmt(r["mean"], 3, "s", signed=True),
              f"IC 95 % [{ui.fmt(r['low'], 3)} ; {ui.fmt(r['high'], 3)}], {plural(r['n'], 'tour')}", delta_color="off")
    if r["low"] <= 0 <= r["high"]:
        st.write("L'intervalle contient 0 : sur ces tours, on ne peut pas dire lequel des deux était plus rapide.")
    else:
        st.write(f"{faster} a été plus rapide en moyenne sur les {plural(r['n'], 'tour')} où les deux étaient en air libre et "
                 "sous drapeau vert. Les pneus (composé, âge) ne sont pas forcément les mêmes sur ces tours.")
    st.caption("Intervalle de Student sur les écarts tour par tour. Des tours consécutifs ne sont pas indépendants : "
               "l'intervalle est un peu trop étroit.")

st.subheader("Le long du tour le plus rapide (télémétrie)")
tel = ui.load("telemetry", sk)
ta, tb = tel[tel["driver"] == a], tel[tel["driver"] == b]
if ta.empty or tb.empty:
    ui.insufficient("comparer la télémétrie", "pas de tour le plus rapide enregistré pour l'un des deux pilotes")
else:
    def info(t):
        r = t.iloc[0]
        lab = ui.COMPOUND_LABEL.get(r["compound"], r["compound"]).lower()
        return (f"tour {int(r['lap_number'])}, {int(r['lap_time_s'] // 60)}:{r['lap_time_s'] % 60:06.3f}, "
                f"{lab} de {plural(int(r['tyre_age']), 'tour')}")
    st.write(f"{a} : {info(ta)}. {b} : {info(tb)}.")
    delta = telemetry_delta(ta, tb)
    fig = go.Figure(go.Scatter(x=delta["lap_fraction"] * 100, y=delta["delta_s"], mode="lines",
                               line=dict(color=ui.INK_2, width=2), name="Écart cumulé",
                               hovertemplate="%{x:.0f} % du tour<br>A − B : %{y:+.3f} s<extra></extra>"))
    fig.add_hline(y=0, line_color=ui.CONTEXT_GREY)
    fig.update_xaxes(title="Position dans le tour (% de la distance)")
    fig.update_yaxes(title=f"Secondes (positif : {a} a perdu du temps)")
    ui.show(ui.style(fig, height=300, title="Écart de temps cumulé le long du tour"))

    fig = go.Figure()
    for t, drv, color in ((ta, a, ca), (tb, b, cb)):
        frac = t["distance_m"] / t["distance_m"].max() * 100
        fig.add_trace(go.Scatter(x=frac, y=t["speed_kmh"], mode="lines", name=drv, line=dict(color=color, width=1.8),
                                 hovertemplate=f"{drv}<br>%{{x:.0f}} %<br>%{{y:.0f}} km/h<extra></extra>"))
    fig.update_xaxes(title="Position dans le tour (% de la distance)")
    fig.update_yaxes(title="km/h")
    ui.show(ui.style(fig, height=300, title="Vitesse"))
    st.caption("Lecture descriptive. Ce sont deux tours différents, souvent à des moments de la course et sur des "
               "pneus différents. La télémétrie OpenF1 compte environ 3,7 mesures par seconde et la distance est "
               "intégrée depuis la vitesse (1 à 1,5 % trop courte) : je la ramène en pourcentage du tour, ce qui "
               "aligne mal les points précis comme les freinages.")
