"""Le tournoi d'une phase, découpé en petites tâches réparties sur tous les cœurs.

Trois sortes de tâches, toutes en donnes dupliquées sur les donnes des tournois (graine 1) :
- un candidat face à des copies d'un adversaire du zoo ;
- le test de minorité : une référence seule face à des copies du candidat ;
- un candidat face à une table mixte précise (comportements anormaux), sur une ou plusieurs manches ;
- phase 5i, --mixed : une référence et le candidat à la même table, avec des Hard simulés (--filler, le Hard recalé de
  la phase 5j par défaut ; hard_simule pour refaire la phase 5i) ; on garde l'écart
  référence - candidat, lu dans les mêmes parties (evaluate.mixed_gap). Il remplace le test de minorité dans la
  règle d'entrée ; ajouter --references sans nom pour ne pas calculer aussi le test de minorité.

Usage : python3 -m figgie.tournoi --candidates marginal lecteur lecteur_ligue --out resultats/phase4/tournoi.json
        python3 -m figgie.tournoi --candidates marginal adaptatif --rounds 10 --deals 300 --out resultats/phase5/tournoi.json
Phase 5c : --site joue avec la règle du site (une offre doit battre celle qui est affichée), et
--opponents remplace le zoo par une liste d'adversaires, le Hard simulé par exemple.
"""
import argparse
import json
import sys
import time
from multiprocessing import Pool

from figgie.bots import ZOO
from figgie.evaluate import CANDIDATES, GATE_REFERENCES, duplicate_match, gate, mean_ci, mixed_gap

TABLES = {  # comportements anormaux, à 4 joueurs : (adversaires, manches par partie)
    "inactif": (("inactif", "heuristique", "marginal"), 1),
    "spammeur": (("spammeur", "heuristique", "marginal"), 1),
    "menteurs": (("menteur", "menteur", "heuristique"), 1),
    "menteurs, 10 manches": (("menteur", "menteur", "heuristique"), 10),
}
CHUNK = 25  # donnes par tâche


def _run(job):
    kind, cand, other, players, first, deals, seed, rounds, site, filler = job
    if kind == "zoo":
        return duplicate_match(CANDIDATES[cand], CANDIDATES[other], deals, players, seed=seed, first_deal=first,
                               rounds=rounds, single_quote=site)
    if kind == "minority":  # gain de la référence seule face aux copies du candidat
        return duplicate_match(CANDIDATES[other], CANDIDATES[cand], deals, players, seed=seed, first_deal=first,
                               rounds=rounds, single_quote=site)
    if kind == "mixed":  # écart référence - candidat à la même table, avec des Hard simulés
        return mixed_gap(CANDIDATES[other], CANDIDATES[cand], CANDIDATES[filler], deals, players, seed=seed,
                         first_deal=first, rounds=rounds, single_quote=site)
    names, table_rounds = TABLES[other]
    return duplicate_match(CANDIDATES[cand], [CANDIDATES[n] for n in names], deals, seed=seed,
                           first_deal=first, rounds=max(rounds, table_rounds), single_quote=site)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--candidates", nargs="+", required=True, choices=sorted(CANDIDATES))
    parser.add_argument("--deals", type=int, default=1000)
    parser.add_argument("--table-deals", type=int, default=300, help="donnes par table anormale")
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--rounds", type=int, default=1, help="manches par partie (phase 5 : le bot adaptatif en a besoin)")
    parser.add_argument("--references", nargs="*", default=list(GATE_REFERENCES), choices=sorted(CANDIDATES),
                        help="références du test de minorité")
    parser.add_argument("--mixed", nargs="+", default=[], choices=sorted(CANDIDATES),
                        help="références de la table mixte (avec des Hard simulés) : remplace le test de minorité dans la règle "
                             "d'entrée, qui reste calculé à part sauf avec --references sans nom")
    parser.add_argument("--no-tables", action="store_true", help="sauter les tables anormales")
    parser.add_argument("--filler", default="hard_simule_v2", choices=sorted(CANDIDATES),
                        help="remplissant de la table mixte (phase 5i : hard_simule ; phase 5j : hard_simule_v2)")
    parser.add_argument("--opponents", nargs="*", default=list(ZOO), choices=sorted(CANDIDATES),
                        help="adversaires du tournoi (le zoo par défaut)")
    parser.add_argument("--site", action="store_true", help="règle du site : une offre doit battre celle qui est affichée")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    for cand in args.candidates if args.mixed else []:
        if CANDIDATES[cand] is CANDIDATES[args.filler]:
            parser.error(f"{cand} est le remplissant de la table mixte : la table ne serait plus mixte")
        if all(CANDIDATES[ref] is CANDIDATES[cand] for ref in args.mixed):
            parser.error(f"aucune référence de --mixed autre que {cand} : il serait admis sans test d'exploitation")

    keys, jobs = [], []
    def add(key, kind, cand, other, players, deals):
        for first in range(0, deals, CHUNK):
            keys.append(key)
            jobs.append((kind, cand, other, players, first, min(CHUNK, deals - first), args.seed, args.rounds,
                         args.site, args.filler))
    for cand in args.candidates:
        for p in (4, 5):
            for opp in args.opponents:
                if CANDIDATES[opp] is not CANDIDATES[cand]:
                    add((cand, p, "zoo", opp), "zoo", cand, opp, p, args.deals)
            for ref in args.references:
                if CANDIDATES[ref] is not CANDIDATES[cand]:
                    add((cand, p, "minority", ref), "minority", cand, ref, p, args.deals)
            for ref in args.mixed:
                if CANDIDATES[ref] is not CANDIDATES[cand]:
                    add((cand, p, "mixed", ref), "mixed", cand, ref, p, args.deals)
        scheduled = set()
        for table, (names, table_rounds) in ([] if args.no_tables else TABLES.items()):
            if (names, max(args.rounds, table_rounds)) in scheduled:
                continue  # avec --rounds, la table d'une manche devient la même que celle de 10 manches
            scheduled.add((names, max(args.rounds, table_rounds)))
            add((cand, 4, "table", table), "table", cand, table, 4, args.table_deals)

    parts, start = [], time.time()
    with Pool() as pool:
        for done, part in enumerate(pool.imap(_run, jobs), 1):  # dans l'ordre des tâches, avancement au fil de l'eau
            parts.append(part)
            elapsed = time.time() - start
            print(f"{done}/{len(jobs)} morceaux, {elapsed / 60:.0f} min écoulées, "
                  f"fin dans ~{elapsed / done * (len(jobs) - done) / 60:.0f} min", file=sys.stderr, flush=True)
    values = {}
    for key, part in zip(keys, parts):
        values.setdefault(key, []).extend(part)  # morceaux dans l'ordre des donnes : même résultat qu'en un bloc

    results = {}
    for cand in args.candidates:
        results[cand] = {}
        for p in (4, 5):
            zoo = {k[3]: mean_ci(v) for k, v in values.items() if k[:3] == (cand, p, "zoo")}
            minority = {k[3]: mean_ci(v) for k, v in values.items() if k[:3] == (cand, p, "minority")}
            mixed = {k[3]: mean_ci(v) for k, v in values.items() if k[:3] == (cand, p, "mixed")}
            rule = "table mixte" if args.mixed else "test de minorité"
            results[cand][p] = {"zoo": zoo, "minority": minority, "mixed": mixed, "rule": rule,
                                "gate": gate(zoo, mixed=mixed) if args.mixed else gate(zoo, minority),
                                "gate_minority": gate(zoo, minority) if minority else None,
                                "gate_without_exploitation_test": gate(zoo)}
        results[cand]["tables"] = {k[3]: mean_ci(v) for k, v in values.items() if k[:3] == (cand, 4, "table")}

    for cand, res in results.items():
        print(f"\n## {cand}")
        for p in (4, 5):
            r = res[p]
            print(f"\n{p} joueurs | règle d'entrée ({r['rule']}) : {r['gate']} (avec le test de minorité : "
                  f"{r['gate_minority']}, sans aucun test d'exploitation : {r['gate_without_exploitation_test']})")
            for opp, (m, lo, hi) in r["zoo"].items():
                print(f"  contre {opp:20s} {m:+7.2f} [{lo:+.2f} ; {hi:+.2f}]")
            for ref, (m, lo, hi) in r["minority"].items():
                print(f"  {ref + ' seul':27s} {m:+7.2f} [{lo:+.2f} ; {hi:+.2f}]  (gain de la référence)")
            for ref, (m, lo, hi) in r["mixed"].items():
                print(f"  {ref + ', table mixte':27s} {m:+7.2f} [{lo:+.2f} ; {hi:+.2f}]  (référence - candidat)")
        for table, (m, lo, hi) in res["tables"].items():
            rounds = max(args.rounds, TABLES[table][1])
            print(f"  table {', '.join(TABLES[table][0]):35s} ({rounds} manche(s)) {m:+7.2f} [{lo:+.2f} ; {hi:+.2f}]")
    with open(args.out, "w") as f:
        json.dump({"args": vars(args), "results": {c: {str(k): v for k, v in r.items()} for c, r in results.items()}},
                  f, indent=2)


if __name__ == "__main__":
    main()
