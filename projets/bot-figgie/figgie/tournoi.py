"""Le tournoi d'une phase, découpé en petites tâches réparties sur tous les cœurs.

Trois sortes de tâches, toutes en donnes dupliquées sur les donnes des tournois (graine 1) :
- un candidat face à des copies d'un adversaire du zoo ;
- le test de minorité : une référence seule face à des copies du candidat ;
- un candidat face à une table mixte précise (comportements anormaux), sur une ou plusieurs manches.

Usage : python3 -m figgie.tournoi --candidates marginal lecteur lecteur_ligue --out resultats/phase4/tournoi.json
"""
import argparse
import json
from multiprocessing import Pool

from figgie.bots import ZOO
from figgie.evaluate import CANDIDATES, GATE_REFERENCES, duplicate_match, gate, mean_ci

TABLES = {  # comportements anormaux, à 4 joueurs : (adversaires, manches par partie)
    "inactif": (("inactif", "heuristique", "marginal"), 1),
    "spammeur": (("spammeur", "heuristique", "marginal"), 1),
    "menteurs": (("menteur", "menteur", "heuristique"), 1),
    "menteurs, 10 manches": (("menteur", "menteur", "heuristique"), 10),
}
CHUNK = 100  # donnes par tâche


def _run(job):
    kind, cand, other, players, first, deals, seed = job
    if kind == "zoo":
        return duplicate_match(CANDIDATES[cand], ZOO[other], deals, players, seed=seed, first_deal=first)
    if kind == "minority":  # gain de la référence seule face aux copies du candidat
        return duplicate_match(CANDIDATES[other], CANDIDATES[cand], deals, players, seed=seed, first_deal=first)
    names, rounds = TABLES[other]
    return duplicate_match(CANDIDATES[cand], [CANDIDATES[n] for n in names], deals, seed=seed,
                           first_deal=first, rounds=rounds)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--candidates", nargs="+", required=True, choices=sorted(CANDIDATES))
    parser.add_argument("--deals", type=int, default=1000)
    parser.add_argument("--table-deals", type=int, default=300, help="donnes par table anormale")
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    keys, jobs = [], []
    def add(key, kind, cand, other, players, deals):
        for first in range(0, deals, CHUNK):
            keys.append(key)
            jobs.append((kind, cand, other, players, first, min(CHUNK, deals - first), args.seed))
    for cand in args.candidates:
        for p in (4, 5):
            for opp in ZOO:
                if ZOO[opp] is not CANDIDATES[cand]:
                    add((cand, p, "zoo", opp), "zoo", cand, opp, p, args.deals)
            for ref in GATE_REFERENCES:
                if CANDIDATES[ref] is not CANDIDATES[cand]:
                    add((cand, p, "minority", ref), "minority", cand, ref, p, args.deals)
        for table in TABLES:
            add((cand, 4, "table", table), "table", cand, table, 4, args.table_deals)

    with Pool() as pool:
        parts = pool.map(_run, jobs, chunksize=1)
    values = {}
    for key, part in zip(keys, parts):
        values.setdefault(key, []).extend(part)  # morceaux dans l'ordre des donnes : même résultat qu'en un bloc

    results = {}
    for cand in args.candidates:
        results[cand] = {}
        for p in (4, 5):
            zoo = {k[3]: mean_ci(v) for k, v in values.items() if k[:3] == (cand, p, "zoo")}
            minority = {k[3]: mean_ci(v) for k, v in values.items() if k[:3] == (cand, p, "minority")}
            results[cand][p] = {"zoo": zoo, "minority": minority, "gate": gate(zoo, minority),
                                "gate_without_minority": gate(zoo)}
        results[cand]["tables"] = {k[3]: mean_ci(v) for k, v in values.items() if k[:3] == (cand, 4, "table")}

    for cand, res in results.items():
        print(f"\n## {cand}")
        for p in (4, 5):
            r = res[p]
            print(f"\n{p} joueurs | règle d'entrée : {r['gate']} (sans le test de minorité : {r['gate_without_minority']})")
            for opp, (m, lo, hi) in r["zoo"].items():
                print(f"  contre {opp:20s} {m:+7.2f} [{lo:+.2f} ; {hi:+.2f}]")
            for ref, (m, lo, hi) in r["minority"].items():
                print(f"  {ref + ' seul':27s} {m:+7.2f} [{lo:+.2f} ; {hi:+.2f}]  (gain de la référence)")
        for table, (m, lo, hi) in res["tables"].items():
            print(f"  table {table:20s} {m:+7.2f} [{lo:+.2f} ; {hi:+.2f}]")
    with open(args.out, "w") as f:
        json.dump({"args": vars(args), "results": {c: {str(k): v for k, v in r.items()} for c, r in results.items()}},
                  f, indent=2)


if __name__ == "__main__":
    main()
