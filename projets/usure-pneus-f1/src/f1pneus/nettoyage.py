import re

import numpy as np
import pandas as pd

from .config import GOMMES_SECHES, Carburant, Seuils

ORDRE_RETRAITS = ("tour 1", "sans temps", "entrée aux stands", "sortie des stands", "neutralisation",
                  "drapeau jaune", "tour annulé", "pluie", "gomme pluie ou inconnue", "aberrant")
GRAVITE = {"JAUNE": 1, "VSC": 2, "SC": 3, "ROUGE": 4}


def _date(s) -> pd.Series:
    return pd.to_datetime(s, utc=True, format="ISO8601")


def construire_tours(laps: list[dict], stints: list[dict], pit: list[dict], drivers: list[dict]) -> pd.DataFrame:
    codes = {d["driver_number"]: d["name_acronym"] for d in drivers}
    df = pd.DataFrame(laps)
    df = pd.DataFrame({
        "numero": df["driver_number"].astype(int),
        "tour": df["lap_number"].astype(int),
        "debut": _date(df["date_start"]),
        "duree": pd.to_numeric(df["lap_duration"], errors="coerce"),
        "sortie_stands": df["is_pit_out_lap"].fillna(False).astype(bool),
    })
    df["pilote"] = df["numero"].map(codes).fillna(df["numero"].astype(str))
    df = df.sort_values(["numero", "tour"]).reset_index(drop=True)
    # Fin du tour : début du tour suivant quand il existe, sinon début + durée.
    suivant = df.groupby("numero")["debut"].shift(-1)
    df["fin"] = suivant.fillna(df["debut"] + pd.to_timedelta(df["duree"], unit="s"))
    entrees = {(p["driver_number"], p["lap_number"]) for p in pit if p.get("lap_number") is not None}
    df["entree_stands"] = [(n, t) in entrees for n, t in zip(df["numero"], df["tour"])]
    return ajouter_pneus(df, pd.DataFrame(stints))


def ajouter_pneus(df: pd.DataFrame, stints: pd.DataFrame) -> pd.DataFrame:
    """Relais, gomme et âge des pneus au tour (tours déjà faits par le train de pneus au début du tour)."""
    st = stints.rename(columns={"driver_number": "numero"})[
        ["numero", "stint_number", "compound", "lap_start", "lap_end", "tyre_age_at_start"]]
    m = df[["numero", "tour"]].reset_index().merge(st, on="numero")
    m = m[(m["tour"] >= m["lap_start"]) & (m["tour"] <= m["lap_end"])]
    # Relais qui se chevauchent dans OpenF1 : le plus récent l'emporte.
    m = m.sort_values("stint_number").drop_duplicates("index", keep="last").set_index("index")
    df = df.copy()
    df["relais"] = m["stint_number"].reindex(df.index).astype("Int64")
    df["gomme"] = m["compound"].reindex(df.index)
    df["age_pneus"] = (m["tyre_age_at_start"] + m["tour"] - m["lap_start"]).reindex(df.index).astype("Int64")
    return df


def ecart_physique(df: pd.DataFrame) -> pd.DataFrame:
    """Écart sur la ligne avec la dernière voiture passée avant, retardataires compris, au début et à la fin du tour."""
    p = df.dropna(subset=["debut"])[["numero", "tour", "debut", "sortie_stands"]].rename(columns={"debut": "t"})
    derniers = df.sort_values("tour").groupby("numero").tail(1).dropna(subset=["fin"])
    arrivees = pd.DataFrame({"numero": derniers["numero"], "tour": derniers["tour"] + 1, "t": derniers["fin"],
                             "sortie_stands": False})
    p = pd.concat([p, arrivees]).sort_values("t").reset_index(drop=True)
    # Au début d'un tour de sortie, la voiture passe la ligne dans la voie des stands, pas devant sur la piste.
    en_piste = ~p["sortie_stands"].to_numpy()
    t = p["t"].to_numpy()
    num, tr = p["numero"].to_numpy(), p["tour"].to_numpy()
    ecart, devant_tour = np.full(len(p), np.nan), np.full(len(p), np.nan)
    for i in range(len(p)):
        j = i - 1
        while j >= 0 and (num[j] == num[i] or not en_piste[j]):
            j -= 1
        if j >= 0:
            ecart[i] = (t[i] - t[j]) / np.timedelta64(1, "s")
            devant_tour[i] = tr[j]
    p["ecart"], p["devant_tour"] = ecart, devant_tour
    cle = p.set_index(["numero", "tour"])
    out = df.copy()
    idx_debut = pd.MultiIndex.from_arrays([out["numero"], out["tour"]])
    idx_fin = pd.MultiIndex.from_arrays([out["numero"], out["tour"] + 1])
    out["ecart_phys_debut"] = cle["ecart"].reindex(idx_debut).to_numpy()
    out["ecart_phys_fin"] = cle["ecart"].reindex(idx_fin).to_numpy()
    devant = cle["devant_tour"].reindex(idx_debut).to_numpy()
    out["devant"] = np.select([devant == out["tour"], devant < out["tour"], devant > out["tour"]],
                              ["même tour", "retardataire", "voiture qui prend un tour"], default="")
    return out


def ecart_openf1(df: pd.DataFrame, intervals: list[dict], tolerance_s: float = 20) -> pd.DataFrame:
    """Écart OpenF1 à la voiture qui précède au classement ; le 0 renvoyé pour le leader devient vide."""
    iv = pd.DataFrame(intervals)
    out = df.copy()
    if iv.empty:
        out["ecart_openf1_debut"] = out["ecart_openf1_fin"] = np.nan
        return out
    iv = pd.DataFrame({"date": _date(iv["date"]), "numero": iv["driver_number"].astype(int),
                       "interval": pd.to_numeric(iv["interval"], errors="coerce"),
                       "au_leader": pd.to_numeric(iv["gap_to_leader"], errors="coerce")})
    iv.loc[iv["au_leader"] == 0, "interval"] = np.nan
    iv = iv.dropna(subset=["date"]).sort_values("date")
    for col, nom in (("debut", "ecart_openf1_debut"), ("fin", "ecart_openf1_fin")):
        g = out[["numero", col]].dropna().reset_index().sort_values(col)
        m = pd.merge_asof(g, iv[["date", "numero", "interval"]], left_on=col, right_on="date", by="numero",
                          direction="backward", tolerance=pd.Timedelta(seconds=tolerance_s))
        out[nom] = m.set_index("index")["interval"].reindex(out.index)
    return out


def fenetres_neutralisation(rc: list[dict], seuils: Seuils = Seuils()) -> pd.DataFrame:
    """Fenêtres [debut, fin, type] de SC, VSC, drapeau rouge et drapeau jaune, d'après les messages de course."""
    rc = sorted(rc, key=lambda r: r["date"])
    marge = pd.Timedelta(seconds=seuils.marge_neutralisation_s)
    defaut_jaune = pd.Timedelta(seconds=seuils.jaune_par_defaut_s)
    fen, sc, sc_rentre, vsc, rouge, jaunes = [], None, False, None, None, {}
    for r in rc:
        t, msg = pd.Timestamp(r["date"]), str(r.get("message") or "").upper()
        flag, scope = r.get("flag"), r.get("scope")
        if r.get("category") == "SafetyCar":
            if "VIRTUAL" in msg and "DEPLOYED" in msg:
                vsc = t
            elif "VIRTUAL" in msg and "ENDING" in msg and vsc is not None:
                fen.append((vsc, t + marge, "VSC"))
                vsc = None
            elif "DEPLOYED" in msg and sc is None:
                sc = t
            elif "IN THIS LAP" in msg:
                sc_rentre = True
            continue
        if flag == "RED":
            rouge = rouge or t
        elif flag == "GREEN" and rouge is not None:
            fen.append((rouge, t, "ROUGE"))
            rouge = None
        if flag in ("YELLOW", "DOUBLE YELLOW"):
            jaunes.setdefault(r.get("sector") if scope == "Sector" else "piste", t)
        elif flag in ("CLEAR", "GREEN") and scope == "Track":
            for debut in jaunes.values():
                fen.append((debut, t, "JAUNE"))
            jaunes.clear()
            if sc is not None and sc_rentre:
                fen.append((sc, t + marge, "SC"))
                sc, sc_rentre = None, False
        elif flag == "CLEAR" and r.get("sector") in jaunes:
            fen.append((jaunes.pop(r.get("sector")), t, "JAUNE"))
    for debut in jaunes.values():
        fen.append((debut, debut + defaut_jaune, "JAUNE"))
    if sc is not None:
        fen.append((sc, sc + pd.Timedelta(minutes=10) + marge, "SC"))
    if vsc is not None:
        fen.append((vsc, vsc + pd.Timedelta(minutes=5), "VSC"))
    return pd.DataFrame(fen, columns=["debut", "fin", "type"])


def etat_piste(df: pd.DataFrame, fenetres: pd.DataFrame) -> pd.Series:
    """Neutralisation la plus grave qui chevauche le tour, ou chaîne vide."""
    niveau = pd.Series(0, index=df.index)
    for f in fenetres.itertuples(index=False):
        touche = (df["debut"] < f.fin) & (df["fin"] > f.debut)
        niveau = niveau.where(~touche, np.maximum(niveau, GRAVITE[f.type]))
    noms = {v: k for k, v in GRAVITE.items()} | {0: ""}
    return niveau.map(noms)


_ANNULE_TEMPS = re.compile(r"CAR (\d+) \(\w+\) TIME (\d+):(\d+\.\d+) (DELETED|REINSTATED)")
_ANNULE_TOUR = re.compile(r"CAR (\d+) \(\w+\) LAP DELETED")


def tours_annules(rc: list[dict], df: pd.DataFrame) -> set[tuple[int, int]]:
    """Tours annulés (numéro, tour), par le temps publié ou l'heure du message : le « LAP n » n'est pas fiable."""
    annules = set()
    for r in sorted(rc, key=lambda r: r["date"]):
        msg = str(r.get("message") or "")
        if m := _ANNULE_TEMPS.search(msg):
            num, temps = int(m[1]), int(m[2]) * 60 + float(m[3])
            cand = df[(df["numero"] == num) & ((df["duree"] - temps).abs() < 0.0015)]
            for tour in cand["tour"]:
                (annules.add if m[4] == "DELETED" else annules.discard)((num, int(tour)))
        elif m := _ANNULE_TOUR.search(msg):
            num = int(m[1])
            finis = df[(df["numero"] == num) & (df["fin"] <= pd.Timestamp(r["date"]))]
            if not finis.empty:
                annules.add((num, int(finis["tour"].max())))
    return annules


def ajouter_meteo(df: pd.DataFrame, weather: list[dict], tolerance_s: float = 90) -> pd.DataFrame:
    """Température de piste au milieu du tour ; pluie si une mesure du tour (ou la plus proche) la signale."""
    out = df.copy()
    w = pd.DataFrame(weather)
    if w.empty:
        out["temp_piste"], out["pluie"] = np.nan, False
        return out
    w = pd.DataFrame({"date": _date(w["date"]), "temp_piste": w["track_temperature"],
                      "pluie": pd.to_numeric(w["rainfall"], errors="coerce").fillna(0) > 0}).sort_values("date")
    milieu = (out["debut"] + (out["fin"] - out["debut"]) / 2).rename("milieu")
    g = milieu.dropna().reset_index().sort_values("milieu")
    m = pd.merge_asof(g, w, left_on="milieu", right_on="date", direction="nearest",
                      tolerance=pd.Timedelta(seconds=tolerance_s)).set_index("index")
    out["temp_piste"] = m["temp_piste"].reindex(out.index)
    pluie = m["pluie"].reindex(out.index).astype("boolean").fillna(False).astype(bool)
    for t in w.loc[w["pluie"], "date"]:
        pluie |= (out["debut"] <= t) & (out["fin"] >= t)
    out["pluie"] = pluie
    return out


def marquer(df: pd.DataFrame, annules: set, seuils: Seuils = Seuils()) -> pd.DataFrame:
    """Colonne `retrait` (premier motif, vide sinon) et colonne `trafic`, à part car l'hypothèse testée décide."""
    out = df.copy()
    motif = pd.Series("", index=out.index, dtype=object)

    def retirer(masque, nom):
        nonlocal motif
        motif = motif.where((motif != "") | ~masque.fillna(False).astype(bool), nom)

    retirer(out["tour"] == 1, "tour 1")
    retirer(out["duree"].isna(), "sans temps")
    retirer(out["entree_stands"], "entrée aux stands")
    retirer(out["sortie_stands"], "sortie des stands")
    retirer(out["neutralisation"].isin(["SC", "VSC", "ROUGE"]), "neutralisation")
    if seuils.retirer_jaunes:
        retirer(out["neutralisation"] == "JAUNE", "drapeau jaune")
    if seuils.retirer_annules:
        retirer(pd.Series([(n, t) in annules for n, t in zip(out["numero"], out["tour"])], index=out.index),
                "tour annulé")
    retirer(out["pluie"], "pluie")
    retirer(~out["gomme"].isin(GOMMES_SECHES), "gomme pluie ou inconnue")
    out["retrait"] = motif
    out["aberrant"] = aberrants(out, seuils)
    out["retrait"] = out["retrait"].where((out["retrait"] != "") | ~out["aberrant"], "aberrant")

    debut, fin = (("ecart_phys_debut", "ecart_phys_fin") if seuils.source_ecart == "physique"
                  else ("ecart_openf1_debut", "ecart_openf1_fin"))
    # Une voiture rattrapée pendant le tour n'apparaît qu'à la fin : on regarde les deux bouts du tour.
    ecart = out[[debut, fin]].min(axis=1)
    out["ecart_devant"] = ecart
    out["trafic"] = ecart < seuils.air_libre_s
    return out


def aberrants(df: pd.DataFrame, seuils: Seuils) -> pd.Series:
    """Tour à plus de `aberrant_s` de la médiane glissante (centrée) des tours encore valides du même relais."""
    res = pd.Series(False, index=df.index)
    if seuils.aberrant_s is None:
        return res
    ok = df[df["retrait"] == ""]
    for _, g in ok.sort_values("tour").groupby(["numero", "relais"]):
        med = g["duree"].rolling(seuils.fenetre_aberrant, center=True, min_periods=3).median()
        res.loc[g.index] = (g["duree"] - med).abs() > seuils.aberrant_s
    return res


def tableau_retraits(df: pd.DataFrame) -> pd.DataFrame:
    """Tours retirés par motif et par pilote (chaque tour compte une fois, pour le premier motif), puis le trafic."""
    t = pd.crosstab(df["pilote"], df["retrait"].replace("", "gardé"))
    cols = [c for c in ORDRE_RETRAITS if c in t.columns]
    t = t.reindex(columns=cols + ["gardé"], fill_value=0)
    t["dont trafic"] = df[df["retrait"] == ""].groupby("pilote")["trafic"].sum().reindex(t.index).fillna(0).astype(int)
    t["air libre"] = t["gardé"] - t["dont trafic"]
    t.insert(0, "tours", df.groupby("pilote").size().reindex(t.index))
    return t


def carburant_kg(tour, total_tours: int, carb: Carburant = Carburant()):
    # Débit constant ; masse au milieu du tour n.
    return np.clip(carb.depart_kg * (1 - (np.asarray(tour, float) - 0.5) / total_tours), 0, None)


def corriger_carburant(duree, tour, total_tours: int, carb: Carburant = Carburant()):
    """Temps ramené à un réservoir vide : on retire le temps que coûte le carburant encore à bord."""
    return np.asarray(duree, float) - carb.s_par_kg * carburant_kg(tour, total_tours, carb)
