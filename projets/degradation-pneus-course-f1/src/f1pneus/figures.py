import os

from .config import DATA_DIR, NOMS_GOMMES

# Cache de polices matplotlib dans le projet plutôt que dans ~/.matplotlib.
os.environ.setdefault("MPLCONFIGDIR", str(DATA_DIR / ".matplotlib"))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.ticker import FuncFormatter, MaxNLocator  # noqa: E402

SURFACE, INK, INK_2, MUTED, GRID, AXIS = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
# Pirelli : rouge, jaune, blanc. Le jaune et le blanc disparaissent sur fond clair : rouge framboise, ocre et bleu,
# vérifiés pour les daltoniens, avec en plus une forme de marqueur par gomme.
COULEUR_GOMME = {"SOFT": "#C0445A", "MEDIUM": "#B98510", "HARD": "#2A64B0"}
MARQUEUR_GOMME = {"SOFT": "^", "MEDIUM": "o", "HARD": "s"}
COULEURS_PILOTES = ("#00897B", "#D9661F")

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "axes.edgecolor": AXIS, "axes.labelcolor": INK_2, "xtick.color": MUTED, "ytick.color": MUTED,
    "text.color": INK, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
    "axes.spines.top": False, "axes.spines.right": False, "font.size": 10,
    "axes.titlesize": 11, "axes.titleweight": "bold", "axes.titlelocation": "left",
})


def fr(x: float, nd: int = 2) -> str:
    return f"{x:.{nd}f}".replace(".", ",").replace("-", "−")


def _format_fr(nd: int):
    return FuncFormatter(lambda v, _: fr(v, nd) if abs(v) > 1e-12 else "0")


def _axe_fr(axis, nd: int):
    # Pas de graduation plus fine que ce que le format affiche (sinon 2,5 s'afficherait « 2 »).
    axis.set_major_locator(MaxNLocator(steps=[1, 2, 5, 10], integer=nd == 0))
    axis.set_major_formatter(_format_fr(nd))


def _titre(fig, titre: str, sous_titre: str, y: float = 1.0):
    fig.text(0.01, y, titre, ha="left", va="bottom", fontsize=12.5, fontweight="bold")
    fig.text(0.01, y - 0.005, sous_titre, ha="left", va="top", fontsize=9.5, color=INK_2)


def _note(fig, texte: str, y: float = -0.01):
    fig.text(0.01, y, texte, ha="left", va="top", fontsize=8, color=MUTED)


def _save(fig, dossier, nom: str) -> str:
    dossier.mkdir(parents=True, exist_ok=True)
    path = dossier / nom
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)
    return str(path)


def nuage_age(df: pd.DataFrame, relais: pd.DataFrame, pilotes, sujet: str, note: str, dossier, nom: str) -> str:
    """Temps corrigé du carburant contre âge des pneus, un panneau par pilote, une droite par relais."""
    fig, axes = plt.subplots(1, len(pilotes), figsize=(12, 5.2), sharey=True)
    garde = df[(df["retrait"] == "") & df["pilote"].isin(pilotes)]
    bas, haut = garde["y"].quantile(0.005) - 0.6, garde["y"].quantile(0.995) + 0.9
    for ax, p in zip(np.atleast_1d(axes), pilotes):
        x = df[df["pilote"] == p]
        for gomme, g in x[x["retrait"] == ""].groupby("gomme"):
            c, mk = COULEUR_GOMME.get(gomme, MUTED), MARQUEUR_GOMME.get(gomme, "o")
            libre, trafic = g[~g["trafic"]], g[g["trafic"]]
            ax.plot(libre["age_pneus"], libre["y"], mk, color=c, ms=6, mec=SURFACE, mew=0.6, ls="", zorder=3)
            ax.plot(trafic["age_pneus"], trafic["y"], mk, mfc="none", mec=c, ms=6, mew=1.2, ls="", zorder=3)
        ret = x[(x["retrait"] != "") & x["y"].between(bas, haut)]
        ax.plot(ret["age_pneus"], ret["y"], "x", color=MUTED, ms=5, mew=1, ls="", zorder=2)
        hors = x[(x["retrait"] != "") & ~x["y"].between(bas, haut)]
        r = relais[relais["pilote"] == p].dropna(subset=["pente"])
        for k, s in enumerate(r.itertuples()):
            c = COULEUR_GOMME.get(s.gomme, MUTED)
            a = np.array([s.age_min, s.age_max], float)
            ax.plot(a, s.constante + s.pente * a, color=c, lw=2, ls="-" if s.affichable else ":", zorder=4)
            lab = (f"Relais {s.relais}, {NOMS_GOMMES.get(s.gomme, s.gomme)} : {fr(s.pente, 3)} s/tour "
                   f"[{fr(s.ic_bas, 3)} ; {fr(s.ic_haut, 3)}], {s.tours} tours")
            ax.text(0.02, 0.97 - 0.065 * k, lab + ("" if s.affichable else " (indicatif)"), transform=ax.transAxes,
                    fontsize=8.5, color=INK, va="top",
                    bbox={"boxstyle": "round,pad=0.2", "fc": SURFACE, "ec": c, "lw": 1})
        ax.set_title(p, loc="left")
        ax.set_xlabel("Âge des pneus (tours)")
        ax.set_ylim(bas, haut)
        _axe_fr(ax.yaxis, 1)
        if len(hors):
            ax.text(0.98, 0.02, f"{len(hors)} tours retirés hors de l'échelle (tour 1, arrêts)",
                    transform=ax.transAxes, ha="right", va="bottom", fontsize=8, color=MUTED)
    np.atleast_1d(axes)[0].set_ylabel("Temps au tour corrigé du carburant (s)")
    leg = [plt.Line2D([], [], marker=MARQUEUR_GOMME[g], color=COULEUR_GOMME[g], ls="", ms=6,
                      label=NOMS_GOMMES[g].capitalize()) for g in ("SOFT", "MEDIUM", "HARD")
           if g in set(df.loc[df["pilote"].isin(pilotes), "gomme"])]
    leg += [plt.Line2D([], [], marker="o", mfc="none", mec=INK_2, ls="", ms=6, label="Dans le trafic"),
            plt.Line2D([], [], marker="x", color=MUTED, ls="", ms=5, label="Tour retiré"),
            plt.Line2D([], [], color=INK_2, lw=2, label="Droite du relais (pointillés : moins de 8 tours)")]
    fig.legend(handles=leg, loc="upper center", bbox_to_anchor=(0.5, 0.0), ncol=len(leg), frameon=False,
               fontsize=9)
    fig.tight_layout()
    _titre(fig, "Temps au tour selon l'âge des pneus", sujet, 1.04)
    _note(fig, note, -0.06)
    return _save(fig, dossier, nom)


def forest_relais(relais: pd.DataFrame, gommes: pd.DataFrame, pilotes, sujet: str, note: str, dossier,
                  nom: str) -> str:
    """Pente de chaque relais d'au moins 8 tours propres, et pente commune de chaque gomme."""
    r = relais[relais["affichable"]].dropna(subset=["pente"])
    ordre = [g for g in ("SOFT", "MEDIUM", "HARD") if g in set(r["gomme"])]
    lignes = []
    for g in ordre:
        sous = gommes[gommes["gomme"] == g]
        if len(sous):
            s = sous.iloc[0]
            lignes.append(("gomme", g, f"{NOMS_GOMMES[g].capitalize()} : pente commune ({s.relais} relais)",
                           s.pente, s.ic_bas, s.ic_haut))
        else:
            lignes.append(("gomme", g, f"{NOMS_GOMMES[g].capitalize()} : trop peu de relais pour une pente commune",
                           np.nan, np.nan, np.nan))
        for s in r[r["gomme"] == g].sort_values("pente").itertuples():
            lignes.append(("relais", g, f"{s.pilote} relais {s.relais} (tours {s.premier_tour} à {s.dernier_tour})",
                           s.pente, s.ic_bas, s.ic_haut))
    fig, ax = plt.subplots(figsize=(9, 0.28 * len(lignes) + 1.6))
    y = np.arange(len(lignes))[::-1]
    for yi, (kind, g, lab, pente, lo, hi) in zip(y, lignes):
        c = COULEUR_GOMME[g]
        if kind == "gomme":
            ax.axhspan(yi - 0.45, yi + 0.45, color=c, alpha=0.10, lw=0)
            if np.isnan(pente):
                continue
            ax.errorbar(pente, yi, xerr=[[pente - lo], [hi - pente]], fmt="D", color=c, ms=7, capsize=3, lw=2)
        else:
            ax.errorbar(pente, yi, xerr=[[pente - lo], [hi - pente]], fmt=MARQUEUR_GOMME[g], color=c, ms=5,
                        capsize=2, lw=1, mfc=c if lab.split()[0] in pilotes else SURFACE)
    ax.set_yticks(y, [l[2] for l in lignes], fontsize=8.5)
    for t, l in zip(ax.get_yticklabels(), lignes):
        if l[0] == "gomme" or l[2].split()[0] in pilotes:
            t.set_fontweight("bold")
            t.set_color(INK)
    ax.axvline(0, color=INK_2, lw=0.8)
    ax.set_ylim(-0.7, len(lignes) - 0.3)
    ax.set_xlabel("Pente : temps perdu par tour d'âge des pneus (s/tour), intervalle à 95 %")
    _axe_fr(ax.xaxis, 2)
    ax.grid(axis="y", visible=False)
    fig.tight_layout()
    _titre(fig, "Dégradation par relais et par gomme", sujet, 1.0 + 0.6 / fig.get_figheight())
    _note(fig, note, -0.02)
    return _save(fig, dossier, nom)


def rythme_course(df: pd.DataFrame, pilotes, sujet: str, note: str, dossier, nom: str) -> str:
    """Temps au tour bruts des deux pilotes et écart sur la ligne, tour par tour."""
    fig, (ax, ax2) = plt.subplots(2, 1, figsize=(12, 7.2), sharex=True, gridspec_kw={"height_ratios": [3, 2]})
    a, b = pilotes
    garde = df[df["pilote"].isin(pilotes) & (df["tour"] > 1) & ~df["entree_stands"] & ~df["sortie_stands"]]
    # Marge en bas pour les bandes de gomme de chaque pilote, sous les points.
    bas, haut = garde["duree"].quantile(0.01) - 1.1, garde["duree"].quantile(0.99) + 1.2
    fins = []
    for p, c in zip(pilotes, COULEURS_PILOTES):
        x = df[df["pilote"] == p].sort_values("tour")
        ax.plot(x["tour"], x["duree"].clip(upper=haut), color=c, lw=1.4, zorder=2)
        libre = x[~x["trafic"] & x["duree"].lt(haut)]
        traf = x[x["trafic"] & x["duree"].lt(haut)]
        ax.plot(libre["tour"], libre["duree"], "o", color=c, ms=4, ls="", zorder=3)
        ax.plot(traf["tour"], traf["duree"], "o", mfc=SURFACE, mec=c, mew=1.2, ms=5, ls="", zorder=3)
        dernier = x[x["duree"].lt(haut)].iloc[-1]
        fins.append((dernier["duree"], dernier["tour"], p, c))
        for t in x.loc[x["entree_stands"], "tour"]:
            for axe in (ax, ax2):
                axe.axvline(t + 0.5, color=c, lw=1, ls="--", alpha=0.8, zorder=1)
            ax.text(t + 0.5, haut, f"arrêt {p}", color=INK_2, fontsize=8.5, va="bottom", ha="center", clip_on=False)
        yb = bas + (0.55 if p == a else 0.2)
        for _, g in x.dropna(subset=["relais"]).groupby("relais"):
            gm = g["gomme"].iloc[0]
            debut, fin = g["tour"].min() - 0.4, g["tour"].max() + 0.4
            ax.plot([debut, fin], [yb, yb], color=COULEUR_GOMME.get(gm, MUTED), lw=6, solid_capstyle="butt")
            ax.text(debut + 0.6, yb + 0.12, f"{p}, {NOMS_GOMMES.get(gm, gm)}", fontsize=8, color=INK_2,
                    va="bottom")
    # Noms en bout de courbe, écartés d'au moins 0,35 s pour ne pas se chevaucher.
    fins.sort()
    for i, (v, t, p, c) in enumerate(fins):
        yv = v if i == 0 else max(v, prec + 0.35)
        prec = yv
        ax.annotate(p, (t, v), xytext=(t + 1.2, yv), color=INK, fontweight="bold", va="center",
                    arrowprops={"arrowstyle": "-", "color": c, "lw": 1})
        ax.plot([], [], color=c, lw=2, label=p)
    ax.set_ylim(bas, haut)
    ax.set_xlim(-1, len(df["tour"].unique()) + 4)
    ax.set_ylabel("Temps au tour brut (s)")
    _axe_fr(ax.yaxis, 0)
    fins = df[df["pilote"].isin(pilotes)].pivot(index="tour", columns="pilote", values="fin")
    ecart = (fins[b] - fins[a]).dt.total_seconds()
    ax2.axhline(0, color=INK_2, lw=0.8)
    ax2.plot(ecart.index, ecart.values, color=INK, lw=1.6)
    ax2.set_ylabel(f"Retard de {b} sur {a}\nsur la ligne (s)")
    ax2.set_xlabel("Tour")
    _axe_fr(ax2.yaxis, 0)
    ax2.text(ecart.index[-1], ecart.values[-1], f"  {fr(ecart.values[-1], 2)} s", va="center", fontsize=9)
    leg = [plt.Line2D([], [], marker="o", color=INK_2, ls="", ms=4, label="Air libre"),
           plt.Line2D([], [], marker="o", mfc=SURFACE, mec=INK_2, ls="", ms=5, label="Dans le trafic"),
           plt.Line2D([], [], color=INK_2, ls="--", lw=1, label="Arrêt aux stands (tour d'entrée)")]
    leg = [plt.Line2D([], [], color=c, lw=2, label=p) for p, c in zip(pilotes, COULEURS_PILOTES)] + leg
    fig.legend(handles=leg, loc="upper center", bbox_to_anchor=(0.5, 0.0), frameon=False, fontsize=9, ncol=5)
    fig.tight_layout()
    _titre(fig, "Le rythme sur toute la course", sujet, 1.06)
    _note(fig, note, -0.04)
    return _save(fig, dossier, nom)


def effet_corrections(scen: pd.DataFrame, sujet: str, note: str, dossier, nom: str) -> str:
    """Pente de chaque gomme sous chaque hypothèse : ce qui bouge et ce qui ne bouge pas."""
    # Seules les gommes estimables dans le scénario de référence : les autres n'ont pas de point de comparaison.
    ref_gommes = set(scen.loc[scen["groupe"] == "référence", "gomme"])
    gommes = [g for g in ("SOFT", "MEDIUM", "HARD") if g in ref_gommes]
    noms = list(dict.fromkeys(scen["scenario"]))
    groupes = scen.drop_duplicates("scenario").set_index("scenario")["groupe"]
    fig, axes = plt.subplots(1, len(gommes), figsize=(5.2 * len(gommes) + 2.5, 0.36 * len(noms) + 1.8), sharey=True)
    y = np.arange(len(noms))[::-1]
    for ax, g in zip(np.atleast_1d(axes), gommes):
        s = scen[scen["gomme"] == g].set_index("scenario").reindex(noms)
        ref = s.iloc[0]
        ax.axvspan(ref.ic_bas, ref.ic_haut, color=COULEUR_GOMME[g], alpha=0.10, lw=0)
        ax.axvline(ref.pente, color=COULEUR_GOMME[g], lw=1, ls="--")
        ok = s["pente"].notna().to_numpy()
        ax.errorbar(s["pente"][ok], y[ok], xerr=[(s["pente"] - s["ic_bas"])[ok], (s["ic_haut"] - s["pente"])[ok]],
                    fmt=MARQUEUR_GOMME[g], color=COULEUR_GOMME[g], ms=6, capsize=2.5, lw=1.2)
        ax.set_title(f"{NOMS_GOMMES[g].capitalize()}", color=INK)
        ax.set_xlabel("Pente (s/tour), intervalle à 95 %")
        _axe_fr(ax.xaxis, 2)
        ax.grid(axis="y", visible=False)
        prec = None
        for yi, n in zip(y, noms):
            if prec is not None and groupes[n] != prec:
                ax.axhline(yi + 0.5, color=AXIS, lw=0.8)
            prec = groupes[n]
    np.atleast_1d(axes)[0].set_yticks(y, noms, fontsize=9)
    fig.tight_layout()
    _titre(fig, "Ce que chaque hypothèse change à la pente", sujet, 1.0 + 0.55 / fig.get_figheight())
    _note(fig, note, -0.01)
    return _save(fig, dossier, nom)


def decomposition(table_ref: pd.DataFrame, toutes: pd.DataFrame, pilotes, ecart: float, sujet: str, note: str,
                  dossier, nom: str) -> str:
    """À gauche : l'écart final découpé en composantes. À droite : l'effet de la stratégie sous chaque hypothèse."""
    a, b = pilotes
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(13, 5.0), gridspec_kw={"width_ratios": [1.15, 1]})
    t = table_ref.set_index("composante")
    ordre = ["arrêts", "niveau de la gomme", "usure des pneus", "effet de la stratégie", "trafic",
             "pilotage et non expliqué", "départ et tour 1"]
    libelles = {"arrêts": "Arrêts aux stands", "niveau de la gomme": "Niveau de la gomme",
                "usure des pneus": "Usure des pneus", "effet de la stratégie": "= Effet de la stratégie",
                "trafic": "Trafic (non comparable)", "pilotage et non expliqué": "Pilotage et non expliqué",
                "départ et tour 1": "Départ et tour 1"}
    y = np.arange(len(ordre))[::-1]
    for yi, k in zip(y, ordre):
        v, lo, hi = t.loc[k, ["valeur_s", "ic_bas", "ic_haut"]]
        strat = k == "effet de la stratégie"
        ax.barh(yi, v, height=0.6, color=INK if strat else ("#8a8a84" if v >= 0 else "#bdbcb4"), zorder=2)
        if hi - lo > 1e-6:
            ax.errorbar(v, yi, xerr=[[v - lo], [hi - v]], fmt="none", ecolor="#8a8a84" if strat else INK_2,
                        capsize=3, lw=1.2, zorder=3)
        ax.text(max(v, hi) + 0.6 if v >= 0 else min(v, lo) - 0.6, yi, f"{'+' if v > 0 else ''}{fr(v, 1)} s",
                va="center", ha="left" if v >= 0 else "right", fontsize=9, color=INK)
    ax.set_yticks(y, [libelles[k] for k in ordre])
    for tl, k in zip(ax.get_yticklabels(), ordre):
        if k == "effet de la stratégie":
            tl.set_fontweight("bold")
    ax.axhline(y[ordre.index("effet de la stratégie")] - 0.5, color=AXIS, lw=0.8)
    ax.axvline(0, color=INK_2, lw=0.8)
    lim = np.nanmax(np.abs(t.loc[ordre, ["ic_bas", "ic_haut", "valeur_s"]].to_numpy())) * 1.45
    ax.set_xlim(-lim, lim)
    _axe_fr(ax.xaxis, 0)
    ax.set_xlabel(f"Secondes (positif : {b} perd du temps sur {a})")
    ax.set_title(f"Écart final de {fr(ecart, 2)} s, hypothèse de référence", fontsize=10.5)
    ax.grid(axis="y", visible=False)

    s = toutes[toutes["composante"] == "effet de la stratégie"].reset_index(drop=True)
    noms_var = {"pilote": "niveaux par pilote et gomme", "relais": "niveaux par relais",
                "tendance": "tendance estimée"}
    labels = [f"{noms_var[v]}, {fr(k, 2) + ' s/kg' if pd.notna(k) else 'sans hypothèse'}"
              for v, k in zip(s["variante"], s["carburant_s_par_kg"])]
    y2 = np.arange(len(s))[::-1]
    ax2.axvline(0, color=INK_2, lw=0.8)
    ax2.errorbar(s["valeur_s"], y2, xerr=[s["valeur_s"] - s["ic_bas"], s["ic_haut"] - s["valeur_s"]], fmt="o",
                 color=INK, ms=6, capsize=3, lw=1.2)
    for yi, v in zip(y2, s["valeur_s"]):
        ax2.text(v, yi + 0.22, f"{'+' if v > 0 else ''}{fr(v, 1)}", ha="center", fontsize=8.5)
    ax2.set_yticks(y2, labels, fontsize=9)
    _axe_fr(ax2.xaxis, 0)
    ax2.set_xlabel("Effet de la stratégie (s), intervalle à 95 %")
    ax2.set_title("Effet de la stratégie selon l'hypothèse", fontsize=10.5)
    ax2.grid(axis="y", visible=False)
    fig.tight_layout()
    _titre(fig, f"D'où vient l'écart entre {a} et {b} ?", sujet, 1.06)
    _note(fig, note, -0.01)
    return _save(fig, dossier, nom)
