"""Tableau de bord : streamlit run src/f1cc/app.py (ou python -m f1cc app)."""
import streamlit as st

st.set_page_config(page_title="Centre de commande F1", layout="wide")

pages = st.navigation([
    st.Page("pages/vue_ensemble.py", title="Vue d'ensemble", default=True),
    st.Page("pages/rythme_pneus.py", title="Rythme et pneus"),
    st.Page("pages/meteo_piste.py", title="Météo et piste"),
    st.Page("pages/duel.py", title="Duel"),
    st.Page("pages/strategie.py", title="Stratégie"),
    st.Page("pages/qualite.py", title="Qualité des données"),
])
pages.run()
