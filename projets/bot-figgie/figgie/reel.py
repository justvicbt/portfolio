"""Phase 5c : les vraies manches de figgie.com, et les mêmes mesures sur nos manches simulées.

    python3 -m figgie.reel --paper marginal lecteur sniper --calibration

Les journaux viennent de Rasmus Suonio (donnees/rasmus, licence MIT) : 60 manches de son bot contre
trois bots « Hard » du site, avec chaque cotation, retrait et échange, à la seconde près. Le site
n'affiche que la meilleure offre de chaque côté : une cotation du journal est une nouvelle meilleure
offre. Nos manches jouées avec la règle du site (single_quote) se mesurent donc de la même façon.
"""
import argparse
import json
import math
import random
import statistics
from math import comb
from pathlib import Path

from figgie.engine import GOAL_CARD_VALUE, POT, START_CASH, SUITS, TWIN, View, payout
from figgie.valuation import CONFIGS

DATA_DIR = Path(__file__).resolve().parent.parent / "donnees" / "rasmus"
NAMES = {"spades": "S", "clubs": "C", "hearts": "H", "diamonds": "D"}
KINDS = {"b": "bid", "o": "ask", "xb": "cancel", "xo": "cancel"}


def parse_rasmus_round(round_, duration=240):
    """Une manche du journal de Rasmus -> {events, goal, duration, hard}, avec `events` au format de
    notre fil public : (instant, joueur, genre, couleur, prix). `hard` : les sièges des bots du site."""
    events = []
    for entry in round_["log"].split(";"):
        kind, left, suit, price, who = entry.split(",")[:5]
        t, suit, price = duration - int(left), SUITS[int(suit)], int(price)
        if kind == "t":
            buyer, seller = map(int, who.split(">"))
            events += [(t, buyer, "bought", suit, price), (t, seller, "sold", suit, price)]
        else:
            events.append((t, int(who), KINDS[kind], suit, 0 if kind in ("xb", "xo") else price))
    me = round_["me"]
    out = {"events": events, "goal": NAMES[round_["goal"]], "duration": duration, "me": me,
           "hard": [p for p in range(4) if p != me]}
    if "dealt" in round_:
        out["dealt"] = dict(zip(SUITS, round_["dealt"]))  # la donne du bot de Rasmus
    if "pnl" in round_:  # sa vraie part de majorité : son gain, moins la mise, ses échanges et ses cartes
        cash = sum(price * ((who == "sold") - (who == "bought")) for _t, p, who, _s, price in events if p == me)
        out["majority"] = round_["pnl"] + POT / 4 - cash - GOAL_CARD_VALUE * round_["final"][SUITS.index(out["goal"])]
    return out


def load_rasmus(folder=DATA_DIR):
    """Toutes les manches des journaux (live_logs_v*.json), dans l'ordre des versions de son bot.
    `session` : le fichier de la manche ; chaque fichier est une suite de manches à la même table."""
    rounds = []
    for f in sorted(Path(folder).glob("live_logs_v*.json")):
        rounds += [{**parse_rasmus_round(r), "session": f.stem} for r in json.loads(f.read_text())["rounds"]]
    return rounds


def simulated_round(result, hard=None):
    """Une manche de notre moteur (RoundResult) au même format. `hard` : sièges mesurés (tous par défaut)."""
    n = len(result.log["hands"])
    return {"events": result.events, "goal": result.log["goal"], "duration": result.log["duration"],
            "hard": list(range(n)) if hard is None else hard}


def market_stats(rounds):
    """Mesures du marché, sur les bots `hard` de chaque manche :
    trades : échanges par manche (tous joueurs) ; hard_trades_per_pair : échanges entre bots mesurés,
    par manche et par paire de bots ; by_minute : part de ces échanges dans chaque quart de la manche ;
    quotes_per_min, first_quote : cotations par minute et instant de la première, médianes par bot ;
    goal_price, other_price : prix médian des échanges entre bots mesurés ; goal_top_bid,
    other_top_bid : médiane, par bot et par couleur, de son plus haut prix d'achat proposé."""
    trades, per_pair, by_minute = [], [], [0, 0, 0, 0]
    rates, firsts, prices, tops = [], [], {True: [], False: []}, {True: [], False: []}
    for r in rounds:
        events, hard, goal, duration = r["events"], set(r["hard"]), r["goal"], r["duration"]
        bought = [e for e in events if e[2] == "bought"]
        sold = [e for e in events if e[2] == "sold"]
        trades.append(len(bought))
        between = 0
        for (t, buyer, _k, suit, price), (_t, seller, *_rest) in zip(bought, sold):
            if buyer in hard and seller in hard:
                between += 1
                by_minute[min(3, int(4 * t / duration))] += 1
                prices[suit == goal].append(price)
        per_pair.append(between / comb(len(hard), 2))
        for p in hard:
            quotes = [e for e in events if e[1] == p and e[2] in ("bid", "ask")]
            rates.append(len(quotes) / (duration / 60))
            if quotes:
                firsts.append(quotes[0][0])
            for s in SUITS:
                tops[s == goal].append(max((e[4] for e in quotes if e[2] == "bid" and e[3] == s), default=0))
    total = sum(by_minute) or 1

    def median(values):
        return statistics.median(values) if values else None
    return {
        "rounds": len(rounds), "trades": statistics.fmean(trades), "hard_trades_per_pair": statistics.fmean(per_pair),
        "by_minute": [n / total for n in by_minute], "quotes_per_min": median(rates), "first_quote": median(firsts),
        "goal_price": median(prices[True]), "other_price": median(prices[False]),
        "goal_top_bid": median(tops[True]), "other_top_bid": median(tops[False]),
    }


def hidden_goal_counts(rnd, samples=200, seed=0, max_tries=500_000):
    """Phase 5e : des mains possibles pour les bots du site. Tire le paquet (selon la donne de Rasmus)
    et les mains des autres, et ne garde que les tirages où chaque vente du journal porte sur une carte
    que le vendeur a, et où Rasmus touche sa vraie part de majorité. Renvoie, pour chaque tirage gardé,
    {siège: cartes objectif à la cloche}."""
    me, goal, dealt = rnd["me"], rnd["goal"], rnd["dealt"]
    others = [p for p in range(4) if p != me]
    events = rnd["events"]
    trades = [(b[1], s[1], b[3]) for b, s in zip(*([e for e in events if e[2] == k] for k in ("bought", "sold")))]
    configs = [sizes for twelve, _e, sizes in CONFIGS if twelve == TWIN[goal]]
    weights = [math.prod(comb(sizes[s], dealt[s]) for s in SUITS) for sizes in configs]
    rng, kept = random.Random(f"{seed}:mains"), []
    for _ in range(max_tries):
        sizes = rng.choices(configs, weights)[0]
        deck = [s for s in SUITS for _ in range(sizes[s] - dealt[s])]
        rng.shuffle(deck)
        hands = {p: {s: deck[10 * i:10 * i + 10].count(s) for s in SUITS} for i, p in enumerate(others)}
        hands[me] = dict(dealt)
        for buyer, seller, s in trades:
            if hands[seller][s] < 1:
                break
            hands[seller][s] -= 1
            hands[buyer][s] += 1
        else:
            mine = hands[me][goal]
            if abs(payout(mine, [hands[p][goal] for p in others]) - GOAL_CARD_VALUE * mine - rnd["majority"]) < 0.5:
                kept.append({p: hands[p][goal] for p in others})
                if len(kept) == samples:
                    break
    return kept


ACTIONS_PER_LOOK = 8  # un bot qui cote dans plusieurs couleurs doit pouvoir aussi prendre dans une autre


def paper_replay(rnd, bot, seed=0, memory=None, majority=False):
    """Rejoue une vraie manche avec notre bot à la place de celui de Rasmus (sa donne, son siège).

    Comme le paper_bot de Rasmus Suonio : le carnet est celui du journal, et notre bot peut prendre
    les cotations des bots du site. Ses propres cotations restent affichées pour lui seul et ne sont
    jamais servies, et le marché ne réagit pas à ses prises. Les vrais échanges du bot de Rasmus
    restent (ils ont eu lieu), sauf la vente d'une carte que notre bot a déjà vendue, ou l'achat d'une
    carte qui rendrait sa main impossible : ils sont rayés, avec leur prix. Notre bot regarde le marché après chaque événement du journal.

    Renvoie (score, prises). Score : argent des prises, moins les ventes rayées, plus 10 $ par carte
    objectif de plus (ou de moins) à la cloche ; la majorité n'est pas comptée, faute de connaître les
    mains des autres. Chaque prise est servie, ce qui est optimiste : comparer des bots entre eux.
    `memory` : la mémoire du bot, à garder d'une manche à l'autre d'une même session (bots adaptatifs).
    `majority` (phase 5e) : ajoute la part de majorité attendue sur le papier, moins la vraie part de
    Rasmus, sur des mains possibles des autres (`rnd["hidden"]`, sinon hidden_goal_counts).
    shortcut: une prise retire seulement la cotation prise, alors que le site vide tout le carnet ;
    un retrait (xb ou xo) retire les deux côtés du joueur dans la couleur, comme dans notre moteur."""
    me, n, duration, goal = rnd["me"], 4, rnd["duration"], rnd["goal"]
    hand, live = dict(rnd["dealt"]), dict(rnd["dealt"])
    cash = START_CASH - POT / n
    counts = [10] * n
    book = {s: {"bid": None, "ask": None} for s in SUITS}  # cotation affichée des autres : (prix, joueur)
    mine = {s: {"bid": None, "ask": None} for s in SUITS}  # mes cotations, vues de moi seul
    trades, feed, takes = [], [], []
    player = bot()
    player.memory = {} if memory is None else memory
    rng = random.Random(f"{seed}:papier")
    delta = 0
    moved = dict.fromkeys(range(n), 0)  # cartes objectif des autres, déplacées par le papier

    def possible(s):
        """Une carte de plus en `s` laisse-t-elle ma main possible avec au moins un paquet ?"""
        return any(all(hand[x] + (x == s) <= sizes[x] for x in SUITS) for *_c, sizes in CONFIGS)

    def clear():
        for sides in (*book.values(), *mine.values()):
            sides["bid"] = sides["ask"] = None

    def trade(t, buyer, seller, s, price):
        counts[buyer] += 1
        counts[seller] -= 1
        trades.append((buyer, seller, s, price))
        feed.extend([(t, buyer, "bought", s, price), (t, seller, "sold", s, price)])

    def view(t):
        shown = {s: {side: {**({book[s][side][1]: (book[s][side][0], 0)} if book[s][side] else {}),
                            **({me: (mine[s][side], 1)} if mine[s][side] else {})} for side in ("bid", "ask")}
                 for s in SUITS}
        return View(me, n, dict(hand), cash, shown, list(trades), list(counts), t, duration, feed, True)

    def look(t):
        nonlocal cash, delta
        for _ in range(ACTIONS_PER_LOOK):
            action = player.act(view(t), rng)
            if not action:
                return
            kind, s = action[0], action[1]
            if kind in ("bid", "ask"):
                mine[s][kind] = action[2]
                continue
            if kind == "cancel":
                mine[s]["bid"] = mine[s]["ask"] = None
                continue
            q = book[s]["ask" if kind == "buy" else "bid"]
            if not q or (q[0] > action[2] or q[0] > cash if kind == "buy" else q[0] < action[2] or hand[s] < 1):
                return  # refusée, comme dans le moteur ; le bot réessaiera au prochain événement
            if kind == "buy" and not possible(s):
                return  # cette carte n'existe pas : le vendeur l'a déjà vendue pour de vrai
            sign = 1 if kind == "buy" else -1
            hand[s] += sign
            cash -= sign * q[0]
            delta -= sign * q[0]
            buyer, seller = (me, q[1]) if kind == "buy" else (q[1], me)
            trade(t, buyer, seller, s, q[0])
            takes.append((t, buyer, seller, s, q[0]))
            if s == goal:
                moved[q[1]] -= sign
            book[s]["ask" if kind == "buy" else "bid"] = None
            for side in ("bid", "ask"):
                mine[s][side] = None

    events = rnd["events"]
    i = 0
    while i < len(events):
        t, who, kind, s, price = events[i]
        if kind == "bought":
            seller = events[i + 1][1]
            i += 2
            if seller == me and hand[s] < 1:
                delta -= price  # vente réelle impossible : la carte est déjà partie sur le papier
                live[s] -= 1
                moved[who] -= s == goal
            elif who == me and not possible(s):
                delta += price  # achat réel impossible : j'ai déjà cette carte, achetée sur le papier
                live[s] += 1
                moved[seller] += s == goal
            else:
                if me in (who, seller):
                    sign = 1 if who == me else -1
                    hand[s] += sign
                    live[s] += sign
                    cash -= sign * price
                trade(t, who, seller, s, price)
            clear()
        else:
            i += 1
            if who == me:
                continue  # les cotations du bot de Rasmus sont remplacées par celles du nôtre
            if kind == "cancel":
                for side in ("bid", "ask"):
                    if book[s][side] and book[s][side][1] == who:
                        book[s][side] = None
            else:
                book[s][kind] = (price, who)
                if mine[s][kind] is not None and (price >= mine[s][kind] if kind == "bid" else price <= mine[s][kind]):
                    mine[s][kind] = None  # règle du site : une offre au moins aussi bonne efface la mienne
            feed.append(events[i - 1])
        look(t)
    if hasattr(player, "end_round"):  # comme sur le site : l'objectif est révélé à la fin
        player.end_round({"seat": me, "goal": goal, "hands": None})
    score = delta + 10 * (hand[goal] - live[goal])
    if majority:
        held = hand[goal]
        hidden = rnd["hidden"] if "hidden" in rnd else hidden_goal_counts(rnd, seed=seed)
        if not hidden:
            raise ValueError("aucune main possible des autres n'explique cette manche")
        # un bot du site ne vend sur le papier que des cartes qu'il a : on écarte les autres mains.
        # shortcut: vérifié à la cloche seulement, pas au fil de la manche ; si aucune main ne convient,
        # on ramène à 0 (le total de cartes objectif est alors faussé).
        after = [[c + moved[p] for p, c in h.items()] for h in hidden]
        fine = [a for a in after if min(a) >= 0]
        shares = [payout(held, [max(0, c) for c in a]) - GOAL_CARD_VALUE * held for a in fine or after]
        score += statistics.fmean(shares) - rnd["majority"]
    return score, takes


CHECK_TIMES = (0, 60, 120, 180, 239)


def goal_calibration(rounds, times=CHECK_TIMES, per_round=False):
    """Probabilité de la vraie couleur objectif, vue du siège de Rasmus (sa main et les vrais échanges),
    à chaque instant de `times`, selon trois méthodes : la donne seule, le comptage des cartes du
    marginal, et le comptage avec la lecture du marché du lecteur (modèle de signaux de la phase 3).
    Phase 5d, « lecture site » : le lecteur du site (figgie.learn --site), avec la confiance par joueur
    et par fenêtre de temps apprise sur les manches précédentes de la même session.
    Renvoie {méthode: {instant: (P moyenne de la vraie couleur, part des manches où elle est la plus
    probable, perte logarithmique moyenne)}}. Avec `per_round`, les mêmes trois nombres pour chaque manche."""
    from figgie.bots import UNIFORM, ReaderBot, SiteReaderBot
    from figgie.signals import MarketReading, OpponentModel
    from figgie.valuation import goal_probabilities, known_minimums
    model, temper = ReaderBot.model()
    site_model, site_temper = SiteReaderBot.model()
    empty = [dict.fromkeys(SUITS, 0) for _ in range(4)]
    out = {m: {t: [] for t in times} for m in ("donne", "comptage", "lecture", "lecture site")}
    trust, session = None, None
    for r in rounds:
        me, goal = r["me"], r["goal"]
        if r.get("session") != session:  # nouvelle table : la confiance repart de zéro
            trust, session = OpponentModel(site_model), r.get("session")
        others = [p for p in range(4) if p != me]
        for t in times:
            seen = [e for e in r["events"] if e[0] <= t]
            bought = [e for e in seen if e[2] == "bought"]
            sold = [e for e in seen if e[2] == "sold"]
            trades = [(b[1], sl[1], b[3], b[4]) for b, sl in zip(bought, sold)]
            hand = dict(r["dealt"])
            for buyer, seller, suit, _price in trades:
                hand[suit] += (buyer == me) - (seller == me)
            mins = known_minimums(trades, 4)
            market = model.posterior(UNIFORM, seen, temper=temper, me=me)
            reading = MarketReading(site_model, site_temper, r["duration"], me, range(4), trust.weights())
            reading.update(seen)
            site = reading.posterior(UNIFORM, t)
            for method, probs in (("donne", goal_probabilities(r["dealt"], empty, me)),
                                  ("comptage", goal_probabilities(hand, mins, me, drawn=r["dealt"])),
                                  ("lecture", goal_probabilities(hand, mins, me, goal_weights=market, drawn=r["dealt"])),
                                  ("lecture site", goal_probabilities(hand, mins, me, goal_weights=site, drawn=r["dealt"]))):
                out[method][t].append((probs[goal], max(probs, key=probs.get) == goal, -math.log(max(probs[goal], 1e-9))))
        trust.observe_round(site_model.round_features(r["events"], r["duration"], others, me=me), goal, me=None)
    if per_round:
        return out
    return {m: {t: tuple(statistics.fmean(x[i] for x in v) for i in range(3)) for t, v in by_t.items()}
            for m, by_t in out.items()}


def paper_report(names, rounds, seed=0, majority=False):
    """Rejeu de toutes les manches pour chaque bot, avec sa mémoire gardée d'une manche à l'autre
    d'une même session. {nom: (scores par manche, prises par manche)}. `majority` : voir paper_replay ;
    les mains possibles des autres sont tirées une fois par manche, les mêmes pour tous les bots."""
    from figgie.evaluate import CANDIDATES
    if majority:
        rounds = [{**r, "hidden": hidden_goal_counts(r, seed=seed * 1000 + i)} for i, r in enumerate(rounds)]
    out = {}
    for name in names:
        scores, takes, memory, session = [], [], None, None
        for i, r in enumerate(rounds):
            if r.get("session") != session:
                memory, session = {}, r.get("session")
            score, t = paper_replay(r, CANDIDATES[name], seed=seed * 1000 + i, memory=memory, majority=majority)
            scores.append(score)
            takes.append(len(t))
        out[name] = (scores, takes)
    return out


def main():
    from figgie.evaluate import CANDIDATES, mean_ci
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--paper", nargs="*", default=[], choices=sorted(CANDIDATES), help="bots à rejouer sur les vraies manches")
    parser.add_argument("--calibration", action="store_true", help="probabilité de la vraie couleur objectif")
    parser.add_argument("--majority", action="store_true", help="phase 5e : compter la majorité estimée au rejeu")
    parser.add_argument("--stats", action="store_true", help="mesures du marché des vraies manches")
    args = parser.parse_args()
    rounds = load_rasmus()
    print(f"{len(rounds)} vraies manches (journaux de Rasmus Suonio, son bot contre 3 bots Hard de figgie.com)")
    if args.stats:
        print("\nMesures du marché (bots Hard seulement) :")
        for k, v in market_stats(rounds).items():
            print(f"  {k:22s} {v}")
    if args.paper:
        print("\nRejeu sur le papier, notre bot à la place de celui de Rasmus : score moyen par manche [IC 95 %]")
        print("(argent des prises + 10 $ par carte objectif de plus ; " + ("majorité estimée sur des mains possibles des autres"
              if args.majority else "la majorité n'est pas comptée") + ", toutes les prises sont servies)")
        for name, (scores, takes) in paper_report(args.paper, rounds, majority=args.majority).items():
            m, lo, hi = mean_ci(scores)
            print(f"  {name:16s} {m:+7.2f} [{lo:+.2f} ; {hi:+.2f}]   prises par manche {statistics.fmean(takes):.1f}")
    if args.calibration:
        print("\nProbabilité de la vraie couleur objectif, vue du siège de Rasmus : P moyenne / part des manches où elle est la plus probable / perte log")
        for method, by_t in goal_calibration(rounds).items():
            print(f"  {method:9s} " + "   ".join(f"t={t:3d} s : {p:.2f} / {acc:.0%} / {ll:.2f}" for t, (p, acc, ll) in by_t.items()))


if __name__ == "__main__":
    main()
