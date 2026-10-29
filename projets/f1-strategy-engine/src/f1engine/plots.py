"""Graphiques enregistrés dans docs/ (PNG, fond clair).

Palette : trois premiers slots de la palette catégorielle de référence, validée pour
le daltonisme (toutes paires). L'aqua est sous 3:1 de contraste : chaque point est
donc aussi étiqueté directement.
"""
import os

from .config import DATA_DIR, DOCS_DIR

# Cache de polices matplotlib dans le projet plutôt que dans ~/.matplotlib.
os.environ.setdefault("MPLCONFIGDIR", str(DATA_DIR / ".matplotlib"))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

SERIES = ["#2a78d6", "#eb6834", "#1baf7a"]
COMPOUND_COLOR = {"SOFT": SERIES[0], "MEDIUM": SERIES[1], "HARD": SERIES[2]}
SURFACE, INK, INK_2, MUTED, GRID, AXIS = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
CIRCUIT_LABEL = {"Sakhir": "Bahreïn", "Catalunya": "Espagne", "Hungaroring": "Hongrie", "Monza": "Italie (Monza)"}

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "axes.edgecolor": AXIS, "axes.labelcolor": INK_2, "xtick.color": MUTED, "ytick.color": MUTED,
    "text.color": INK, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
    "axes.spines.top": False, "axes.spines.right": False, "font.size": 10,
    "axes.titlesize": 12, "axes.titleweight": "bold", "axes.titlelocation": "left",
})


def _save(fig, name: str) -> str:
    DOCS_DIR.mkdir(exist_ok=True)
    path = DOCS_DIR / name
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)
    return str(path)


def degradation_chart(table: pd.DataFrame) -> str:
    """Pente de dégradation (s/tour) par course et par composé, avec IC 95 %."""
    table = table[table["model"] == "A"]
    circuits = list(CIRCUIT_LABEL)
    fig, ax = plt.subplots(figsize=(8, 4.6))
    dodge = {"SOFT": -0.22, "MEDIUM": 0.0, "HARD": 0.22}
    for row in table.itertuples():
        y = circuits.index(row.circuit) + dodge[row.compound]
        color = COMPOUND_COLOR[row.compound]
        ax.plot([row.slope_ci_low, row.slope_ci_high], [y, y], color=color, lw=2, solid_capstyle="round")
        ax.plot(row.slope_s_per_lap, y, "o", ms=8, color=color, mec=SURFACE, mew=2)
        ax.annotate(f"{row.compound.capitalize()}  {row.slope_s_per_lap:.3f}", (row.slope_ci_high, y),
                    xytext=(6, 0), textcoords="offset points", va="center", fontsize=8.5, color=INK_2)
    ax.set_yticks(range(len(circuits)), [CIRCUIT_LABEL[c] for c in circuits])
    ax.invert_yaxis()
    ax.axvline(0, color=AXIS, lw=1)
    ax.set_xlim(-0.01, 0.19)
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("Secondes perdues par tour d'âge du pneu (corrigé du carburant)")
    ax.set_title("Dégradation des pneus par course, Grands Prix 2025")
    handles = [plt.Line2D([], [], marker="o", ls="", ms=8, color=COMPOUND_COLOR[c], label=c.capitalize())
               for c in COMPOUND_COLOR]
    ax.legend(handles=handles, loc="lower right", frameon=False, ncol=3)
    fig.text(0.01, -0.07, "Point : estimation OLS (effet fixe pilote). Trait : intervalle de confiance à 95 %, "
             "erreurs clusterisées par relais.\nSource : OpenF1, tours propres uniquement.", fontsize=8, color=MUTED)
    return _save(fig, "degradation.png")


def strategy_chart(comparisons: list, pit_loss: pd.DataFrame) -> str:
    """Seuil de rentabilité du 2e arrêt (modèles A et B) vs perte aux stands mesurée."""
    circuits = list(CIRCUIT_LABEL)
    fig, ax = plt.subplots(figsize=(8, 4.2))
    offsets = {"A": -0.13, "B": 0.13}
    colors = {"A": SERIES[0], "B": SERIES[1]}
    labels = {"A": "Seuil, modèle A (carburant fixé)", "B": "Seuil, modèle B (tendance estimée)"}
    for comp in comparisons:
        y = circuits.index(comp.circuit) + offsets[comp.model]
        lo, hi = np.percentile(comp.breakeven_draws, [5, 95])
        ax.plot([lo, hi], [y, y], color=colors[comp.model], lw=2, solid_capstyle="round")
        ax.plot(comp.breakeven_s, y, "o", ms=8, color=colors[comp.model], mec=SURFACE, mew=2)
    loss = pit_loss.set_index("circuit")["median_pit_loss_s"]
    for c in circuits:
        y = circuits.index(c)
        ax.plot(loss[c], y, marker="D", ms=8, color=INK, mec=SURFACE, mew=1.5, ls="")
        ax.annotate(f"{loss[c]:.1f} s", (loss[c], y), xytext=(-9, 0), textcoords="offset points",
                    ha="right", va="center", fontsize=8.5, color=INK)
    ax.set_yticks(range(len(circuits)), [CIRCUIT_LABEL[c] for c in circuits])
    ax.invert_yaxis()
    ax.grid(axis="y", visible=False)
    ax.set_xlim(0, 45)
    ax.set_xlabel("Secondes")
    ax.set_title("Quand un 2e arrêt est-il rentable ?")
    handles = [plt.Line2D([], [], marker="o", ls="-", lw=2, ms=8, color=colors[m], label=labels[m]) for m in "AB"]
    handles.append(plt.Line2D([], [], marker="D", ls="", ms=8, color=INK, label="Perte aux stands mesurée (médiane)"))
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.15), frameon=False, ncol=2, fontsize=8.5)
    fig.text(0.01, -0.16, "Seuil = temps gagné par des pneus plus frais avec 2 arrêts. Si le seuil dépasse la perte "
             "aux stands, 2 arrêts sont plus rapides.\nTrait : intervalle à 90 % (2 000 tirages Monte Carlo).",
             fontsize=8, color=MUTED)
    return _save(fig, "strategy.png")


def telemetry_chart(tel: pd.DataFrame, circuit: str, drivers: tuple[str, str], lap_info: dict) -> str:
    """Vitesse, accélérateur et frein sur le tour le plus rapide de deux pilotes."""
    fig, axes = plt.subplots(3, 1, figsize=(9, 6.2), sharex=True, gridspec_kw={"height_ratios": [3, 1.6, 0.8]})
    for i, drv in enumerate(drivers):
        d = tel[tel["acronym"] == drv]
        color = SERIES[i]
        axes[0].plot(d["distance_m"], d["speed_kmh"], color=color, lw=1.6, label=f"{drv} — {lap_info[drv]}")
        axes[1].plot(d["distance_m"], d["throttle_pct"], color=color, lw=1.4)
        axes[2].fill_between(d["distance_m"], i, i + 0.8 * d["brake_on"], step="post", color=color, lw=0)
    # Limites de secteurs du premier pilote
    first = tel[tel["acronym"] == drivers[0]]
    for s in (2, 3):
        x = first.loc[first["sector"] == s, "distance_m"].min()
        for ax in axes:
            ax.axvline(x, color=AXIS, lw=1, ls=":")
        axes[0].annotate(f"S{s}", (x, 1), xycoords=("data", "axes fraction"), xytext=(3, -12),
                         textcoords="offset points", fontsize=8, color=MUTED)
    axes[0].set_ylabel("Vitesse (km/h)")
    axes[1].set_ylabel("Accélérateur (%)")
    axes[2].set_yticks([0.4, 1.4], list(drivers))
    axes[2].set_ylabel("Frein")
    axes[2].grid(False)
    axes[2].set_xlabel("Distance depuis la ligne (m, intégrée depuis la vitesse)")
    axes[0].legend(loc="lower left", bbox_to_anchor=(0, 1.0), frameon=False, fontsize=9, ncol=2)
    axes[0].set_title(f"Tour le plus rapide, {CIRCUIT_LABEL.get(circuit, circuit)} 2025 : {drivers[0]} vs {drivers[1]}",
                      pad=26)
    fig.text(0.01, -0.01, "Source : OpenF1, ~3,7 mesures par seconde. Les pics très courts (freinages) peuvent "
             "être lissés ou manqués.", fontsize=8, color=MUTED)
    fig.tight_layout()
    return _save(fig, "telemetry.png")
