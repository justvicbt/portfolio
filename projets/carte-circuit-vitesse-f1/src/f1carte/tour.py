"""Choix du tour, alignement des flux, distance, sections rapides, zones de freinage et indicateurs."""
import re
from dataclasses import dataclass
from datetime import datetime

import numpy as np

from .config import Seuils

# Ex. "CAR 55 (SAI) TIME 1:20.470 DELETED - TRACK LIMITS AT TURN 7 LAP 3 16:03:35"
# ou  "CAR 30 (LAW) LAP DELETED - TRACK LIMITS AT TURN 6 LAP 6 16:16:28 (PIT)"
_DELETED = re.compile(r"CAR (\d+)\b.*?\b(DELETED|REINSTATED)\b")
_TIME = re.compile(r"\bTIME (\d+):(\d+\.\d+)")


def parse_date(s: str) -> float:
    return datetime.fromisoformat(s).timestamp()


def _tour_vise(msg: dict, car: int, temps: float | None, laps: list[dict]) -> int | None:
    # Le "LAP n" des messages vaut le numéro OpenF1 + 1 à Monza 2025 : on ne s'y fie pas.
    # On prend le tour de ce temps, sinon le dernier tour du pilote terminé avant le message.
    date = parse_date(msg["date"])
    finis = [(parse_date(lap["date_start"]) + lap["lap_duration"], lap) for lap in laps
             if lap["driver_number"] == car and lap.get("lap_duration") and lap.get("date_start")]
    finis = [(fin, lap) for fin, lap in finis if fin <= date
             and (temps is None or round(lap["lap_duration"], 3) == temps)]
    return max(finis, key=lambda f: f[0])[1]["lap_number"] if finis else None


def tours_annules(race_control: list[dict], laps: list[dict]) -> set[tuple[int, int]]:
    """(pilote, numéro de tour OpenF1) annulés, après réintégrations."""
    annules = set()
    for msg in sorted(race_control, key=lambda m: m.get("date") or ""):
        text = (msg.get("message") or "").upper()
        m = _DELETED.search(text)
        if not m or not msg.get("date"):
            continue
        car = int(m.group(1))
        tm = _TIME.search(text)
        temps = round(int(tm.group(1)) * 60 + float(tm.group(2)), 3) if tm else None
        lap = _tour_vise(msg, car, temps, laps)
        if lap is None:
            continue
        if m.group(2) == "DELETED":
            annules.add((car, lap))
        else:
            annules.discard((car, lap))
    return annules


def tour_le_plus_rapide(laps: list[dict], annules: set = frozenset(), pilote: int | None = None) -> dict:
    valid = [
        lap for lap in laps
        if lap.get("lap_duration") and lap.get("date_start") and not lap.get("is_pit_out_lap")
        and (pilote is None or lap["driver_number"] == pilote)
        and (lap["driver_number"], lap["lap_number"]) not in annules
    ]
    if not valid:
        raise ValueError("aucun tour chronométré valide pour ce choix")
    return min(valid, key=lambda lap: lap["lap_duration"])


@dataclass
class Tour:
    t: np.ndarray          # s depuis le début du tour
    vitesse: np.ndarray    # km/h
    accel: np.ndarray      # %
    frein: np.ndarray      # bool
    x: np.ndarray
    y: np.ndarray
    distance: np.ndarray   # m, intégrée depuis la vitesse
    retirees: int          # mesures retirées faute de position fiable


def _interp(t_new, t, v, trou_max):
    idx = np.clip(np.searchsorted(t, t_new, side="right"), 1, len(t) - 1)
    ok = (t_new >= t[0]) & (t_new <= t[-1]) & (t[idx] - t[idx - 1] <= trou_max)
    return np.interp(t_new, t, v), ok


def aligner(car: dict, loc: dict, duree: float, trou_max: float = 1.0) -> Tour:
    """car : t, speed, throttle, brake ; loc : t, x, y. Temps en s depuis le début du tour.

    Les instants de car_data servent de référence (le frein, binaire, ne s'interpole pas),
    plus deux points interpolés au début et à la fin exacts du tour.
    """
    ct = np.asarray(car["t"], float)
    inside = (ct > 0) & (ct < duree)
    t = np.concatenate([[0.0], ct[inside], [duree]])

    vitesse, ok_v = _interp(t, ct, np.asarray(car["speed"], float), trou_max)
    accel, _ = _interp(t, ct, np.asarray(car["throttle"], float), trou_max)
    prev = np.clip(np.searchsorted(ct, t, side="right") - 1, 0, len(ct) - 1)
    frein = np.asarray(car["brake"], float)[prev] > 0
    # Les bornes ne comptent que si car_data les encadre ; à l'intérieur, la mesure est exacte.
    ok_v[1:-1] = True

    lt = np.asarray(loc["t"], float)
    x, ok_x = _interp(t, lt, np.asarray(loc["x"], float), trou_max)
    y, _ = _interp(t, lt, np.asarray(loc["y"], float), trou_max)

    # La distance s'intègre sur toutes les vitesses fiables, même là où la position manque.
    tv, v = t[ok_v], vitesse[ok_v] / 3.6
    distance = np.full(len(t), np.nan)
    distance[ok_v] = np.concatenate([[0.0], np.cumsum((v[1:] + v[:-1]) / 2 * np.diff(tv))])

    keep = ok_v & ok_x
    t, vitesse, accel, frein, x, y, distance = (a[keep] for a in (t, vitesse, accel, frein, x, y, distance))
    return Tour(t, vitesse, accel, frein, x, y, distance, retirees=int((~keep).sum()))


def _plages(mask: np.ndarray) -> list[tuple[int, int]]:
    """Plages [début, fin] (indices inclus) où mask est vrai."""
    edges = np.diff(np.concatenate([[0], mask.astype(int), [0]]))
    return list(zip(np.flatnonzero(edges == 1), np.flatnonzero(edges == -1) - 1))


def _durees(t: np.ndarray) -> np.ndarray:
    # Chaque mesure représente l'intervalle jusqu'à la suivante ; la dernière, rien.
    return np.append(np.diff(t), 0.0)


def sections_rapides(tour: Tour, s: Seuils = Seuils()) -> list[tuple[int, int]]:
    mask = tour.vitesse >= s.rapide_ratio * tour.vitesse.max()
    dt = _durees(tour.t)
    return [(a, b) for a, b in _plages(mask) if dt[a:b + 1].sum() >= s.rapide_duree_s]


def zones_freinage(tour: Tour, s: Seuils = Seuils()) -> list[dict]:
    plages = _plages(tour.frein)
    # Une seule mesure sans frein au milieu d'un freinage est du bruit : on fusionne.
    fusion = []
    for a, b in plages:
        if fusion and a - fusion[-1][1] <= 2:
            fusion[-1] = (fusion[-1][0], b)
        else:
            fusion.append((a, b))
    zones = []
    for a, b in fusion:
        if b - a + 1 < s.freinage_mesures:
            continue
        entree = tour.vitesse[max(a - 1, 0):a + 1].max()
        # La vitesse minimale est au point bas qui suit, souvent une mesure après le relâchement du frein.
        fin = b
        while fin + 1 < len(tour.t) and tour.vitesse[fin + 1] <= tour.vitesse[fin]:
            fin += 1
        mini = tour.vitesse[a:fin + 1].min()
        if entree - mini < s.freinage_baisse_kmh:
            continue
        zones.append({"debut": a, "fin": b, "vitesse_entree": float(entree), "vitesse_min": float(mini),
                      "distance_m": float(tour.distance[a]), "duree_s": float(tour.t[fin] - tour.t[a])})
    return zones


def indicateurs(tour: Tour, s: Seuils = Seuils()) -> dict:
    dt = _durees(tour.t)
    total = float(tour.t[-1] - tour.t[0])
    parcouru = float(tour.distance[-1] - tour.distance[0])
    longueur_xy = float(np.hypot(np.diff(tour.x), np.diff(tour.y)).sum())
    return {
        "mesures": len(tour.t),
        "mesures_retirees": tour.retirees,
        "frequence_hz": (len(tour.t) - 1) / total,
        "ecart_max_s": float(np.diff(tour.t).max()),
        "vitesse_max_kmh": float(tour.vitesse.max()),
        "vitesse_min_kmh": float(tour.vitesse.min()),
        "vitesse_moyenne_kmh": parcouru / total * 3.6,
        "part_fond": float(dt[tour.accel >= s.fond_pct].sum() / total),
        "part_freinage": float(dt[tour.frein].sum() / total),
        "distance_vitesse_m": parcouru,
        "longueur_xy": longueur_xy,
        "ratio_xy_sur_m": longueur_xy / parcouru,
    }
