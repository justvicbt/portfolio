"""Mise en forme des textes en français : virgule décimale, vrai signe moins, singulier pour 0 et 1."""
MINUS = "−"


def num(x: float, digits: int = 1, signed: bool = False) -> str:
    s = f"{x:+.{digits}f}" if signed else f"{x:.{digits}f}"
    return s.replace(".", ",").replace("-", MINUS)


def pct(x: float, digits: int = 0) -> str:
    return f"{num(x * 100, digits)} %"


def plural(n: int, singular: str, plural_form: str | None = None) -> str:
    """« 1 tour », « 0 tour », « 3 tours » (en français, 0 et 1 prennent le singulier)."""
    word = singular if abs(n) < 2 else (plural_form or singular + "s")
    return f"{n} {word}"


def join_and(items: list) -> str:
    items = [str(i) for i in items]
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " et " + items[-1]


def at_laps(laps: list[int]) -> str:
    laps = [int(x) for x in laps]
    return f"au tour {laps[0]}" if len(laps) == 1 else f"aux tours {join_and(laps)}"
