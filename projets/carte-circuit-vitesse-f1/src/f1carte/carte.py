"""Figures PNG dans docs/ : carte colorée selon la vitesse, carte des zones, profil de vitesse."""
import os

from .config import DATA_DIR, DOCS_DIR, Seuils

# Cache de polices matplotlib dans le projet plutôt que dans ~/.matplotlib.
os.environ.setdefault("MPLCONFIGDIR", str(DATA_DIR / ".matplotlib"))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.collections import LineCollection  # noqa: E402

from .tour import Tour  # noqa: E402

RAPIDE, FREIN = "#2a78d6", "#eb6834"
SURFACE, INK, INK_2, MUTED, GRID, AXIS = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
CMAP = "viridis"

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


def _carte_vide(tour: Tour, titre: str, extra_largeur: float = 0.0, bas: float = 0.02):
    # Taille de figure calée sur les proportions du tracé, pour éviter les grandes marges vides.
    ratio = np.ptp(tour.y) / np.ptp(tour.x)
    largeur = 6.0 if ratio >= 1 else 8.0
    fig, ax = plt.subplots(figsize=(largeur + extra_largeur, float(np.clip(0.95 * largeur * ratio, 4.5, 9.0))))
    fig.subplots_adjust(left=0.02, right=0.98, top=0.93, bottom=bas)
    ax.set_aspect("equal")
    ax.axis("off")
    titre, _, sous_titre = titre.partition("\n")
    fig.text(0.02, 0.995, titre, ha="left", va="top", fontsize=12, fontweight="bold")
    fig.text(0.02, 0.965, sous_titre, ha="left", va="top", fontsize=10, color=INK_2)
    span = max(np.ptp(tour.x), np.ptp(tour.y))
    pad = 0.08 * span
    ax.set_xlim(tour.x.min() - pad, tour.x.max() + pad)
    ax.set_ylim(tour.y.min() - pad, tour.y.max() + pad)
    return fig, ax, span


def _normale_ext(tour: Tour, i: int) -> np.ndarray:
    """Normale au tracé au point i, tournée vers l'extérieur (loin du centre du circuit)."""
    a, b = max(i - 2, 0), min(i + 2, len(tour.x) - 1)
    tangente = np.array([tour.x[b] - tour.x[a], tour.y[b] - tour.y[a]])
    n = np.array([-tangente[1], tangente[0]]) / (np.hypot(*tangente) or 1.0)
    centre = np.array([tour.x.mean(), tour.y.mean()])
    return n if np.dot(n, [tour.x[i], tour.y[i]] - centre) >= 0 else -n


def placer_etiquettes(tour: Tour, indices: list[int], span: float, eviter=()) -> list[np.ndarray]:
    """Position de chaque étiquette : vers l'extérieur, éloignée du tracé, des autres étiquettes et de `eviter`."""
    pts = np.column_stack([tour.x, tour.y])
    base, places = 0.055 * span, []
    occupes = [np.asarray(q, float) for q in eviter]
    for i in indices:
        p, n = pts[i], _normale_ext(tour, i)
        candidats = [p + sign * k * base * n for sign in (1, -1) for k in (1, 1.5, 2, 2.5, 3)]
        choix = candidats[0]
        for c in candidats:
            loin_trace = np.hypot(*(pts - c).T).min() >= 0.6 * base
            loin_autres = all(np.hypot(*(c - q)) >= 0.9 * base for q in places + occupes)
            if loin_trace and loin_autres:
                choix = c
                break
        places.append(choix)
    return places


def _segments(tour: Tour) -> np.ndarray:
    pts = np.column_stack([tour.x, tour.y]).reshape(-1, 1, 2)
    return np.concatenate([pts[:-1], pts[1:]], axis=1)


def _depart_et_sens(ax, tour: Tour, span: float) -> list[np.ndarray]:
    """Marque la ligne et le sens du tour ; renvoie les points occupés, à éviter pour les autres étiquettes."""
    p0 = np.array([tour.x[0], tour.y[0]])
    ax.plot(*p0, "o", ms=9, color=SURFACE, mec=INK, mew=2, zorder=5)
    n = _normale_ext(tour, 0)
    # Flèche longue de 8 % de la taille du tracé, quel que soit le circuit.
    k = int(np.argmax(np.hypot(tour.x - p0[0], tour.y - p0[1]) >= 0.08 * span))
    off = 0.04 * span * n
    pk = np.array([tour.x[k], tour.y[k]])
    ax.annotate("", xy=pk + off, xytext=p0 + off, arrowprops={"arrowstyle": "-|>", "color": INK, "lw": 1.6},
                zorder=5)
    lab = p0 - 0.07 * span * n
    ax.annotate("Ligne", p0, xytext=lab, ha="center", va="center", fontsize=9, color=INK,
                arrowprops={"arrowstyle": "-", "color": MUTED, "lw": 0.8})
    return [p0, p0 + off, (p0 + pk) / 2 + off, pk + off, lab]


def carte_vitesse(tour: Tour, titre: str, source: str, nom: str) -> str:
    fig, ax, span = _carte_vide(tour, titre, extra_largeur=1.3)
    ax.plot(tour.x, tour.y, color=INK_2, lw=6.5, solid_capstyle="round", zorder=1)
    # Vitesse moyenne de chaque segment, pour que la couleur suive le trait.
    v = (tour.vitesse[1:] + tour.vitesse[:-1]) / 2
    lc = LineCollection(_segments(tour), cmap=CMAP, lw=4.5, capstyle="round", zorder=2)
    lc.set_array(v)
    ax.add_collection(lc)
    _depart_et_sens(ax, tour, span)
    cb = fig.colorbar(lc, ax=ax, shrink=0.75, pad=0.03, aspect=25)
    cb.set_label("Vitesse (km/h)")
    cb.outline.set_edgecolor(AXIS)
    fig.text(0.02, 0.0, f"Flèche : sens du tour. Coordonnées OpenF1 brutes, non géoréférencées.\n{source}",
             fontsize=8, color=MUTED, va="top")
    return _save(fig, nom)


def carte_zones(tour: Tour, rapides: list, freinages: list[dict], titre: str, source: str, seuils: Seuils,
                nom: str) -> str:
    fig, ax, span = _carte_vide(tour, titre, bas=0.09)
    ax.plot(tour.x, tour.y, color=AXIS, lw=5, solid_capstyle="round", zorder=1)
    for a, b in rapides:
        ax.plot(tour.x[a:b + 1], tour.y[a:b + 1], color=RAPIDE, lw=5, solid_capstyle="butt", zorder=2)
    # Freinage : un point par mesure, forme distincte du trait plein des sections rapides.
    for z in freinages:
        a, b = z["debut"], z["fin"]
        ax.plot(tour.x[a:b + 1], tour.y[a:b + 1], "o", ms=6, color=FREIN, mec=INK, mew=0.7, ls="", zorder=3)
    occupes = _depart_et_sens(ax, tour, span)
    positions = placer_etiquettes(tour, [z["debut"] for z in freinages], span, occupes)
    for num, (z, pos) in enumerate(zip(freinages, positions), start=1):
        p = (tour.x[z["debut"]], tour.y[z["debut"]])
        ax.annotate(str(num), p, xytext=pos, ha="center", va="center", fontsize=9, fontweight="bold",
                    color=INK, zorder=6,
                    bbox={"boxstyle": "circle,pad=0.25", "fc": SURFACE, "ec": FREIN, "lw": 1.5},
                    arrowprops={"arrowstyle": "-", "color": FREIN, "lw": 1, "shrinkA": 0, "shrinkB": 3})
    handles = [
        plt.Line2D([], [], color=RAPIDE, lw=5, label=f"Section rapide (≥ {seuils.rapide_ratio:.0%} de la vitesse "
                   f"max, ≥ {seuils.rapide_duree_s:g} s)".replace(".", ",").replace("%", " %")),
        plt.Line2D([], [], marker="o", ms=6, ls="", color=FREIN, mec=INK, mew=0.7,
                   label=f"Zone de freinage numérotée, un point par mesure (frein et baisse ≥ "
                   f"{seuils.freinage_baisse_kmh:g} km/h)"),
    ]
    ax.legend(handles=handles, loc="upper left", bbox_to_anchor=(0.0, 0.0), frameon=False, ncol=1, fontsize=9,
              handlelength=3)
    fig.text(0.02, 0.005, f"Numéros dans l'ordre du tour, placés au début du freinage.\n{source}",
             fontsize=8, color=MUTED, va="top")
    return _save(fig, nom)


def profil_vitesse(tour: Tour, rapides: list, freinages: list[dict], titre: str, source: str, nom: str) -> str:
    fig, ax = plt.subplots(figsize=(10, 4.4))
    d = tour.distance - tour.distance[0]
    for a, b in rapides:
        ax.axvspan(d[a], d[b], color=RAPIDE, alpha=0.16, lw=0, zorder=0)
    vmax = tour.vitesse.max()
    top = vmax * 1.08
    derniers = []
    for num, z in enumerate(freinages, start=1):
        a, b = z["debut"], z["fin"]
        ax.axvspan(d[a], d[b], facecolor="none", edgecolor=FREIN, hatch="////", lw=0, zorder=1)
        # Deux numéros trop proches : le second monte d'un cran.
        rang = 1 if derniers and d[a] - derniers[-1][0] < 0.025 * d[-1] and derniers[-1][1] == 0 else 0
        derniers.append((d[a], rang))
        ax.text((d[a] + d[b]) / 2, top + rang * 0.05 * vmax, str(num), ha="center", va="bottom", fontsize=8.5,
                fontweight="bold", color=INK,
                bbox={"boxstyle": "circle,pad=0.2", "fc": SURFACE, "ec": FREIN, "lw": 1.2})
    ax.plot(d, tour.vitesse, color=INK, lw=1.5, zorder=3)
    ax.set_ylim(0, vmax * 1.22)
    ax.set_xlim(0, d[-1])
    ax.set_xlabel("Distance depuis la ligne (m, intégrée depuis la vitesse)")
    ax.set_ylabel("Vitesse (km/h)")
    titre, _, sous_titre = titre.partition("\n")
    ax.set_title(f"{titre}\n", pad=10)
    ax.text(0, 1.035, sous_titre, transform=ax.transAxes, fontsize=10, color=INK_2)
    handles = [plt.Rectangle((0, 0), 1, 1, color=RAPIDE, alpha=0.16, label="Section rapide"),
               plt.Rectangle((0, 0), 1, 1, fc="none", ec=FREIN, hatch="////", lw=0, label="Zone de freinage"),
               plt.Line2D([], [], color=INK, lw=1.5, label="Vitesse")]
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.17), frameon=False, ncol=3, fontsize=9)
    fig.text(0.01, -0.06, source, fontsize=8, color=MUTED)
    fig.tight_layout()
    return _save(fig, nom)
