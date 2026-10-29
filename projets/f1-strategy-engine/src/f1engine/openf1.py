"""Client minimal pour l'API publique OpenF1 (https://openf1.org), avec cache disque.

Les données historiques sont accessibles sans compte. L'API limite le débit
(3 requêtes/s et environ 30/min) : on espace les appels et on réessaie en cas de 429.
"""
import hashlib
import json
import time
from urllib.parse import quote

import requests

from .config import RAW_DIR

BASE_URL = "https://api.openf1.org/v1"
MIN_INTERVAL_S = 2.1  # ~28 requêtes/min
_last_call = 0.0


def _build_url(endpoint: str, params: dict) -> str:
    # OpenF1 attend les opérateurs dans la clé (ex. "date>"), on ne les encode pas.
    query = "&".join(f"{k}={quote(str(v), safe=':')}" for k, v in params.items())
    return f"{BASE_URL}/{endpoint}?{query}" if query else f"{BASE_URL}/{endpoint}"


def get(endpoint: str, retries: int = 6, **params) -> list[dict]:
    """GET avec cache : une même requête n'est téléchargée qu'une fois."""
    global _last_call
    url = _build_url(endpoint, params)
    cache_file = RAW_DIR / f"{endpoint}_{hashlib.sha1(url.encode()).hexdigest()[:16]}.json"
    if cache_file.exists():
        return json.loads(cache_file.read_text())

    for attempt in range(retries):
        wait = MIN_INTERVAL_S - (time.monotonic() - _last_call)
        if wait > 0:
            time.sleep(wait)
        _last_call = time.monotonic()
        resp = requests.get(url, timeout=60)
        if resp.status_code == 429 or resp.status_code >= 500:
            retry_after = resp.headers.get("Retry-After", "")
            time.sleep(float(retry_after) if retry_after.isdigit() else 15 * (attempt + 1))
            continue
        resp.raise_for_status()
        data = resp.json()
        # OpenF1 renvoie un objet {"detail": ...} quand aucune donnée ne correspond.
        if isinstance(data, dict):
            data = []
        RAW_DIR.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(json.dumps(data))
        return data
    raise RuntimeError(f"OpenF1 indisponible après {retries} essais : {url}")
