"""Qualité des données : contrôles de l'ETL, tours écartés, couverture météo."""
import streamlit as st

from f1cc import ui

race, lap = ui.sidebar()
sk = int(race["session_key"])
laps = ui.load("race_laps", sk)
checks = ui.load("checks", sk)

st.title("Qualité des données")
st.caption("Contrôles calculés à chaque ETL. Ils signalent ce qui doit être lu avec prudence ; un « à vérifier » "
           "n'empêche pas l'affichage.")

STATUS = {"ok": "OK", "warning": "À vérifier", "fail": "Échec"}
NAMES = {
    "weather_coverage": "Couverture météo des tours",
    "weather_interpolated": "Météo interpolée",
    "weather_out_of_range": "Valeurs météo hors plage",
    "laps_missing": "Tours manquants",
    "lap_time_vs_crossings": "Durée du tour contre passages sur la ligne",
    "final_order_vs_results": "Classement recalculé contre officiel",
    "clean_laps_share": "Part de tours propres",
    "lap_start_repaired": "Heures de début de tour corrigées",
}
st.dataframe(checks.assign(check_name=checks["check_name"].map(NAMES).fillna(checks["check_name"]),
                           status=checks["status"].map(STATUS))[["check_name", "status", "detail"]],
             hide_index=True, width="stretch",
             column_config={"check_name": "Contrôle", "status": "État", "detail": "Détail"})

c1, c2 = st.columns(2)
with c1:
    st.subheader("Pourquoi des tours sont écartés")
    reasons = {"lap1": "1er tour", "no_time": "sans temps", "pit_in": "tour d'entrée aux stands",
               "pit_out": "tour de sortie des stands", "neutralised": "neutralisation (SC, VSC, jaune, rouge)",
               "not_dry": "pneus pluie ou inconnus", "traffic": "trafic (< 1,5 s)", "outlier": "aberrant (> 107 %)"}
    ex = laps["exclusion"].map(reasons).fillna("tour propre").value_counts().rename_axis("motif").reset_index()
    ex["part"] = ex["count"] / ex["count"].sum()
    st.dataframe(ex, hide_index=True, width="stretch", column_config={
        "motif": "Motif (le premier rencontré)", "count": "Tours",
        "part": st.column_config.NumberColumn("Part", format="percent")})
with c2:
    st.subheader("Rattachement de la météo")
    labels = {"measured": "mesure à moins de 90 s", "interpolated": "interpolée (trou de 5 min au plus)",
              "missing": "manquante"}
    wx = laps["weather_status"].map(labels).fillna("manquante").value_counts().rename_axis("source").reset_index()
    st.dataframe(wx, hide_index=True, width="stretch", column_config={"source": "Source", "count": "Tours"})
    st.caption("Chaque tour reçoit la mesure la plus proche de son milieu. Sans mesure à moins de 90 s, on "
               "interpole entre les deux voisines si elles sont à moins de 5 minutes l'une de l'autre ; sinon la "
               "valeur reste vide.")

st.subheader("Classement officiel")
st.dataframe(ui.load("results", sk), hide_index=True, width="stretch", column_config={
    "position": "Pos.", "driver": "Pilote", "team": "Écurie", "number_of_laps": "Tours",
    "status": "Statut", "points": "Points"})
