"""Éléments communs aux pages ; chaque page appelle sidebar() et fonctionne donc seule (tests AppTest)."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from . import data, text
from .config import CIRCUIT_LABEL, db_path, get_engine

# Palette du moteur de stratégie (testée pour les daltoniens), mêmes couleurs pour les mêmes composés.
COMPOUND_COLOR = {"SOFT": "#2a78d6", "MEDIUM": "#eb6834", "HARD": "#1baf7a",
                  "INTERMEDIATE": "#008300", "WET": "#6250d6", "UNKNOWN": "#898781"}
COMPOUND_LABEL = {"SOFT": "Tendre", "MEDIUM": "Medium", "HARD": "Dur", "INTERMEDIATE": "Intermédiaire",
                  "WET": "Pluie", "UNKNOWN": "Inconnu"}
DUEL_COLOR = ("#2a78d6", "#eb6834")
CONTEXT_GREY = "#c3c2b7"
INK_2 = "#52514e"
NEUTRAL_FILL = {"SC": "rgba(137,135,129,0.22)", "VSC": "rgba(137,135,129,0.12)", "RED": "rgba(227,73,72,0.15)"}
NEUTRAL_LABEL = {"SC": "Safety car", "VSC": "VSC", "RED": "Drapeau rouge"}


@st.cache_resource
def engine(path: str):
    return get_engine()


def _eng():
    return engine(str(db_path()))


# Le chemin de la base fait partie de la clé de cache : les tests utilisent une base séparée.
@st.cache_data(show_spinner=False)
def cached(name: str, path: str, *args):
    return getattr(data, name)(_eng(), *args)


def load(name: str, *args):
    return cached(name, str(db_path()), *args)


def sidebar() -> tuple[pd.Series, int] | tuple[None, None]:
    """Sélection de la course et du tour courant, partagée par toutes les pages."""
    if not db_path().exists():
        st.error("Base absente. Lancez d'abord `python -m f1cc etl` (voir le README).")
        st.stop()
    sessions = load("sessions")
    if sessions.empty:
        st.error("La base ne contient aucune course. Relancez `python -m f1cc etl`.")
        st.stop()
    labels = {r.circuit: f"{CIRCUIT_LABEL.get(r.circuit, r.circuit)}, {r.date_start[:10]}"
              for r in sessions.itertuples()}
    with st.sidebar:
        st.caption("Rejeu d'une course passée, données OpenF1. Pas de temps réel.")
        circuit = st.selectbox("Course", list(labels), format_func=labels.get, key="circuit")
        race = sessions.set_index("circuit").loc[circuit]
        total = int(race["total_laps"])
        key = f"lap_{circuit}"
        lap = st.slider("Tour courant", 1, total, total, key=key,
                        help="Les vues s'arrêtent à ce tour. Les modèles, eux, sont estimés sur toute la course.")
    race = race.copy()
    race["circuit"] = circuit
    return race, lap


def insufficient(what: str, reason: str) -> None:
    st.info(f"Données insuffisantes pour {what} : {reason}. Pas d'enseignement affiché.")


def fmt(x: float, digits: int = 1, unit: str = "", signed: bool = False) -> str:
    """Nombre à la française : virgule décimale, espace avant l'unité."""
    return f"{text.num(x, digits, signed)} {unit}".strip()


def shade_neutralisations(fig: go.Figure, windows: pd.DataFrame, x: str = "lap", max_lap: int | None = None) -> None:
    """Bandes grises pour SC / VSC / drapeau rouge, sur un axe en tours ou en heures."""
    for w in windows.itertuples():
        if x == "lap":
            if max_lap is not None and w.lap_from > max_lap:
                continue
            x0, x1 = w.lap_from - 0.5, w.lap_to + 0.5
        else:
            x0, x1 = w.start, w.end
        fig.add_vrect(x0=x0, x1=x1, fillcolor=NEUTRAL_FILL[w.status], line_width=0, layer="below",
                      annotation_text=NEUTRAL_LABEL[w.status], annotation_position="top left",
                      annotation_font_size=10, annotation_font_color=INK_2)


TITLE_BAND_PX = 34
LEGEND_BAND_PX = 56   # place pour une légende sur deux lignes, sous le titre


def style(fig: go.Figure, height: int = 380, title: str | None = None, **layout) -> go.Figure:
    """Mise en page commune ; avec un titre, la légende passe dans une bande réservée sous le titre."""
    fig.update_layout(separators=", ")   # virgule décimale et espace pour les milliers, axes et infobulles
    if title is None:
        fig.update_layout(height=height, margin=dict(l=10, r=10, t=40, b=10), hovermode="closest",
                          legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0), **layout)
        return fig
    # Plotly n'affiche la légende qu'à partir de deux séries nommées : sinon, pas de bande à réserver.
    named = [t for t in fig.data if t.name and t.showlegend is not False]
    has_legend = len(named) >= 2 or any(t.showlegend for t in fig.data)
    top = TITLE_BAND_PX + (LEGEND_BAND_PX if has_legend else 6)
    fig.update_layout(
        height=height, margin=dict(l=10, r=10, t=top, b=10), hovermode="closest",
        title=dict(text=title, x=0, xanchor="left", xref="container", y=1, yanchor="top", yref="container",
                   pad=dict(t=8, l=10)),
        legend=dict(orientation="h", x=0, xanchor="left", y=1 - TITLE_BAND_PX / height, yanchor="top",
                    yref="container"),
        **layout)
    return fig


def show(fig: go.Figure) -> None:
    st.plotly_chart(fig, width="stretch", config={"displaylogo": False})


# cache_resource plutôt que cache_data : les résultats statsmodels ne se copient pas bien.

@st.cache_resource(show_spinner="Estimation du modèle de dégradation...")
def degradation(path: str, sk: int, trend: bool = False):
    from .analysis import degradation as fit
    return fit(load("clean_laps", sk), trend)


@st.cache_resource(show_spinner="Simulation des stratégies (moteur de stratégie)...")
def stop_windows(path: str, sk: int, pit_loss_s: float):
    from .strategy import stop_windows as run
    verdict = degradation(path, sk)
    return run(verdict.value[0], pit_loss_s)


@st.cache_resource(show_spinner="Paramètres du simulateur d'undercut...")
def undercut_params(path: str, circuit: str):
    """Paramètres du circuit (code du simulateur d'undercut, base de ce projet) et de saison (ses CSV versionnés)."""
    from f1risk.params import circuit_params, load_season, typical_duel

    from .strategy import season_params_from_p2
    season = load_season(_eng())
    try:
        cp = circuit_params(season, circuit)
    except (ValueError, IndexError) as exc:
        return None, None, None, str(exc)
    return cp, typical_duel(season, cp), season_params_from_p2(), None


def thousands(n: int) -> str:
    return f"{n:,}".replace(",", " ")
