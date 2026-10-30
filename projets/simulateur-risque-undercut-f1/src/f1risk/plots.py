"""Graphiques PNG dans docs/, style du moteur de stratégie sans sa fonction d'enregistrement (son propre dossier)."""
from . import config  # noqa: F401  (fixe MPLCONFIGDIR avant l'import de matplotlib)

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from f1engine.plots import AXIS, CIRCUIT_LABEL, INK, INK_2, MUTED, SERIES, SURFACE  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402

from .config import DOCS_DIR, MAIN_CIRCUITS  # noqa: E402

BLUES = LinearSegmentedColormap.from_list(
    "blues", ["#e9f1fc", "#b7d3f6", "#86b6ef", "#5598e7", "#2a78d6", "#1c5cab", "#104281"])
SCENARIO_LABEL = {
    "undercut_rival_responds": "Undercut, le rival répond au tour suivant",
    "undercut_rival_extends": "Undercut, le rival reste 3 tours de plus",
    "do_nothing": "Ne rien faire (arrêt au même tour que le rival)",
}
SCENARIO_COLOR = {"undercut_rival_responds": SERIES[0], "undercut_rival_extends": SERIES[1], "do_nothing": MUTED}


def _save(fig, name: str) -> str:
    DOCS_DIR.mkdir(exist_ok=True)
    path = DOCS_DIR / name
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)
    return str(path)


def risk_reward_chart(by_lap: pd.DataFrame, circuits: dict, gap: float) -> str:
    fig, axes = plt.subplots(2, 4, figsize=(13, 6.4), sharey="row", gridspec_kw={"hspace": 0.35})
    for j, c in enumerate(MAIN_CIRCUITS):
        df = by_lap[by_lap["circuit"] == c]
        top, bottom = axes[0, j], axes[1, j]
        for name in ("undercut_rival_extends", "undercut_rival_responds", "do_nothing"):
            s = df[df["scenario"] == name]
            top.plot(s["stop_lap"], s["p_success"], color=SCENARIO_COLOR[name], lw=2,
                     ls="--" if name == "do_nothing" else "-")
        for name in ("undercut_rival_responds", "do_nothing"):
            s = df[df["scenario"] == name]
            bottom.plot(s["stop_lap"], s["mean_gain_s"], color=SCENARIO_COLOR[name], lw=2)
            bottom.plot(s["stop_lap"], s["cvar5_gain_s"], color=SCENARIO_COLOR[name], lw=2, ls=":")
        bottom.axhline(0, color=AXIS, lw=1)
        top.set_title(CIRCUIT_LABEL[c], fontsize=11)
        top.set_ylim(0, 1)
        bottom.set_xlabel("Tour d'arrêt de l'attaquant")
        bottom.set_ylim(-16, 4)
    axes[0, 0].set_ylabel("Probabilité de passer devant")
    axes[1, 0].set_ylabel("Secondes reprises au rival")
    handles = [plt.Line2D([], [], color=SCENARIO_COLOR[n], lw=2, ls="--" if n == "do_nothing" else "-",
                          label=SCENARIO_LABEL[n]) for n in SCENARIO_LABEL]
    handles += [plt.Line2D([], [], color=INK_2, lw=2, label="En bas, trait plein : gain moyen"),
                plt.Line2D([], [], color=INK_2, lw=2, ls=":", label="En bas, pointillé : moyenne des 5 % pires scénarios")]
    fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, -0.1), ncol=2, frameon=False, fontsize=8.5)
    fig.suptitle(f"Risque et gain d'un undercut selon le tour d'arrêt (écart initial {gap:.1f} s, pneus du même âge)".replace(".", ","),
                 x=0.07, ha="left", fontweight="bold", fontsize=12)
    fig.text(0.07, -0.14, "20 000 scénarios par point. Fenêtre = 10e à 90e centile des 1ers arrêts observés en 2025.",
             fontsize=8, color=MUTED)
    return _save(fig, "risk_reward.png")


def decision_map_chart(grid: pd.DataFrame) -> str:
    fig, axes = plt.subplots(1, 4, figsize=(13, 4.2), sharey=True)
    for ax, c in zip(axes, MAIN_CIRCUITS):
        g = grid[grid["circuit"] == c].pivot(index="gap_s", columns="age_diff", values="p_success")
        im = ax.imshow(g.to_numpy(), origin="lower", aspect="auto", cmap=BLUES, vmin=0, vmax=1,
                       extent=[g.columns.min() - 0.5, g.columns.max() + 0.5,
                               g.index.min() - 0.125, g.index.max() + 0.125])
        cs = ax.contour(g.columns, g.index, g.to_numpy(), levels=[0.5], colors=INK, linewidths=1.2)
        ax.clabel(cs, fmt={0.5: "50 %"}, fontsize=8)
        ax.set_title(f"{CIRCUIT_LABEL[c]} (tour {int(grid.loc[grid['circuit'] == c, 'stop_lap'].iloc[0])})",
                     fontsize=11)
        ax.set_xlabel("Âge pneus attaquant - rival (tours)")
        ax.grid(False)
    axes[0].set_ylabel("Écart initial avec le rival (s)")
    cbar = fig.colorbar(im, ax=axes, fraction=0.02, pad=0.02)
    cbar.set_label("Probabilité de passer devant", color=INK_2)
    cbar.outline.set_visible(False)
    fig.suptitle("Carte de décision : undercut, le rival répond au tour suivant", x=0.07, ha="left",
                 fontweight="bold", fontsize=12, y=1.02)
    fig.text(0.07, -0.08, "À gauche, l'attaquant a des pneus plus frais que le rival. Trait noir : 50 % de réussite. "
             "5 000 scénarios par case.", fontsize=8, color=MUTED)
    return _save(fig, "decision_map.png")


def sensitivity_chart(sens: pd.DataFrame) -> str:
    order = (sens.groupby("factor")["p_success"].agg(lambda x: x.max() - x.min()).sort_values().index)
    fig, axes = plt.subplots(1, 4, figsize=(13, 4.6), sharey=True)
    for ax, c in zip(axes, MAIN_CIRCUITS):
        s = sens[sens["circuit"] == c].set_index(["factor", "level"])["p_success"]
        ref = sens.loc[sens["circuit"] == c, "p_success_ref"].iloc[0]
        for y, f in enumerate(order):
            lo, hi = s[(f, "low")] - ref, s[(f, "high")] - ref
            ax.barh(y, lo, color=SERIES[1], height=0.6)
            ax.barh(y, hi, color=SERIES[0], height=0.6)
        ax.axvline(0, color=INK, lw=1)
        ax.set_title(f"{CIRCUIT_LABEL[c]} (réf. {ref * 100:.0f} %)", fontsize=11)
        ax.set_xlim(-0.35, 0.35)
        ax.set_xticks([-0.3, -0.15, 0, 0.15, 0.3], ["-30", "-15", "0", "+15", "+30"])
        ax.set_xlabel("Écart de P(succès), points")
        ax.grid(axis="y", visible=False)
    axes[0].set_yticks(range(len(order)), order, fontsize=8.5)
    handles = [plt.Rectangle((0, 0), 1, 1, color=SERIES[1], label="1re valeur entre parenthèses"),
               plt.Rectangle((0, 0), 1, 1, color=SERIES[0], label="2e valeur entre parenthèses")]
    fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.55, -0.08), ncol=2, frameon=False, fontsize=8.5)
    fig.suptitle("Ce qui fait bouger la probabilité de réussite", x=0.07, ha="left", fontweight="bold", fontsize=12)
    return _save(fig, "sensitivity.png")


def validation_chart(pred: pd.DataFrame, calib: pd.DataFrame) -> str:
    p = pred.dropna(subset=["p_sim"]).sort_values("p_sim").reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(8, 4.2))
    rng = np.random.default_rng(0)
    jitter = rng.uniform(-0.06, 0.06, len(p))
    ax.scatter(p["p_sim"], p["success"].astype(float) + jitter, s=28, color=SERIES[0], edgecolor=SURFACE,
               linewidth=1, zorder=3)
    c = calib[calib["n"] > 0]
    mid = c["mean_p_sim"]
    ax.plot([0, 1], [0, 1], color=AXIS, lw=1, ls=":")
    ax.plot(mid, c["observed_rate"], "D-", color=SERIES[1], ms=8, lw=2, mec=SURFACE, mew=1.5, zorder=4)
    for row in c.itertuples():
        ax.annotate(f"n = {row.n}", (row.mean_p_sim, row.observed_rate), xytext=(8, -4), textcoords="offset points",
                    fontsize=8.5, color=INK_2)
    ax.set_xlim(0, 1)
    ax.set_ylim(-0.12, 1.12)
    ax.set_yticks([0, 0.25, 0.5, 0.75, 1], ["Échec", "25 %", "50 %", "75 %", "Réussite"])
    ax.set_xlabel("Probabilité de réussite donnée par le simulateur")
    ax.set_title(f"Validation sur {len(p)} vraies tentatives d'undercut (saison 2025)")
    handles = [plt.Line2D([], [], marker="o", ls="", color=SERIES[0], label="Une tentative (résultat réel)"),
               plt.Line2D([], [], marker="D", color=SERIES[1], lw=2, label="Taux de réussite observé par tranche"),
               plt.Line2D([], [], color=AXIS, ls=":", label="Calibration parfaite")]
    ax.legend(handles=handles, loc="upper left", frameon=False, fontsize=8.5)
    fig.text(0.01, -0.06, "Paramètres estimés sans les deux pilotes concernés (circuit) et sans la course (saison).",
             fontsize=8, color=MUTED)
    return _save(fig, "validation.png")
