# Phase 5s: learning the site reading again with the Hard v3

*Version française : [phase5s.fr.md](phase5s.fr.md)*

The site reading is used by the whole v4 family, and so by the "buying" v4c, the reference bot. It relies on a signal model learned in phase 5d, on tables where phase 5c's simulated Hard bots played. But those Hard bots bid prices that pointed poorly to the goal (phase 5p). Since phase 5r, the Hard v3 is closer: its bids point to the goal almost as often as the site's bots' bids. In this phase, I learn that model again on tables where the Hard v3 plays, without changing anything else.

Result: on Rasmus's 60 real rounds, which are never used for learning, the new reading finds the goal at the bell in 98% of the rounds, against 85%. The "buying" v4c with this reading, `v4c_achat_v3`, passes the entry rule in the reduced and in the full tournament, with 4 and with 5 players. It makes about $10.5 per round more than the "buying" v4c when both play at the same table. It becomes the reference bot. On the other hand, it makes less than the old one against the simulated Hard bots of phases 5c and 5j. The tournament gains are measured against simulated bots, not on the site.

## Where the $35 against the Hard v3 come from

In phase 5r, the "buying" v4c beat three Hard v3 bots by $35 per round, twice as much as three recalibrated Hard bots. Before learning anything on those tables, I wanted to know whether this gain came from a flaw of the Hard v3. The stopping rule was set in the plan: if it gave away the goal early in the round, for example, I would stop there.

A player's gain splits exactly into three parts:
- the deal: $10 per goal card received, minus the ante;
- the trades, each card counted at its end value, $10 for the goal and 0 for the others: buying the goal at $7 brings $3, selling another suit at $4 brings $4;
- the majority bonus, the share of the rest of the pot.

I played the same 500 games of 10 rounds (site rule, the "buying" v4c at seat 0) against three recalibrated Hard bots, then against three Hard v3 bots. The script checks in every round that the three parts add up to the exact gain.

| Per round, "buying" v4c | against recalibrated Hard | against Hard v3 | gap |
|---|---|---|---|
| total gain | $18.07 | $35.99 | +$17.92 |
| deal | -$26.41 | -$26.41 | 0 |
| majority bonus | $45.91 | $57.14 | +$11.23 |
| goal buys and sales | -$4.86 | -$1.51 | +$3.35 |
| sales of other suits | $13.30 | $16.09 | +$2.79 |
| buys of other suits | -$9.87 | -$9.32 | +$0.55 |
| goal cards bought / sold | 0.90 / 0.78 | 1.15 / 0.53 | |
| alone in the lead on the goal at the end of the round | 36% | 48% | |

Over these 500 games, the gap is $18 rather than $17 as in the tournament: the deals and the seats are not the same.

Most of it, about $14.6, comes from the goal. Against the Hard v3, the "buying" v4c buys more goal cards, sells fewer, and more often ends alone in the lead. The Hard v3 does not give the goal away: what the bot makes buying it in the first minute only goes from $0.26 to $0.91. It reads the goal better because the Hard v3's bids point to it, which also happens on the site. About $2.8 comes from the non-goal cards it sells to the Hard v3 at higher prices, mostly in the last minute (+$2.27). That is the flaw already noted in phase 5r: the Hard v3 takes too many non-goal asks at $4-6. It inflates the gains against the Hard v3 a little without explaining them, and the stopping rule did not apply.

## The model learned again

`figgie.learn --site` gets the `--hard` option, which picks the simulated Hard bot of the learning tables. Everything else stays the same: the same 4- or 5-player tables, the same neighbour at the same seat, the same seeds (51 to learn, 52 to validate), 2,400 learning rounds and 600 validation rounds. The new model goes into `modeles/signaux_site_v3.json`. The old one is not touched, and no existing bot changes.

A single seam, written with TDD: a new function `site_table` gives each table's seed and players. The test checks that with the Hard v3, the table is the same as before, with the Hard bot replaced. It failed before the code. It catches two deliberate mistakes: ignoring the requested Hard bot, and changing the table draws when the Hard bot changes.

Learning takes 32 s on 10 cores. On the simulated validation rounds, the damping kept is 0.5, and the reading finds the goal at 240 s in 97.5% of the rounds. The full output is in `resultats/phase5s/apprentissage.txt`.

## The criterion on the real rounds

I set it before learning. On the 60 real rounds, at 180, 225 and 239 s, the new reading must have a lower log loss than the current one, and a share of rounds where the true suit is ranked first at least as high. `figgie.reel --calibration` gets the `--signals` option to measure another model; with the old one, it gives back exactly the numbers of the previous phases.

| Real rounds: probability of the true suit; share ranked first; log loss | 60 s | 120 s | 180 s | 225 s | 239 s |
|---|---|---|---|---|---|
| phase 5d model | 0.31; 43%; 1.281 | 0.41; 53%; 1.031 | 0.63; 77%; 0.610 | 0.78; 85%; 0.406 | 0.81; 85%; 0.360 |
| model learned with the Hard v3 | 0.31; 43%; 1.295 | 0.52; 62%; 0.999 | **0.90; 95%; 0.188** | **0.95; 95%; 0.146** | **0.98; 98%; 0.098** |

The criterion is met by a wide margin. At the bell, the raw consensus of the bids found the goal in 91% of the real rounds (phase 5p). The new reading does better, by adding card counting and per-player trust. In phase 5p, a reading tuned in simulation did worse on the real rounds; this time, what the bot learns in simulation holds on real data. At 60 s nothing changes, which the criterion did not look at.

## The reduced tournament

The candidate `v4c_achat_v3` is the "buying" v4c with this single change: the new signal model and its damping. Its settings stay the v4c's. It played phase 5r's reduced tournament (10 rounds, 100 deals, site rule, Hard v3 at the mixed table), with the "buying" v4c added to the references. It passes the entry rule at both sizes and beats the "buying" v4c at the same table: -$10.70 [-11.77; -9.63] with 4 players, -$11.39 [-12.44; -10.34] with 5 (gap reference minus candidate). The tournament took 2 h 50.

## The full tournament

As in phase 5n: seed 1, 300 deals of 10 rounds, site rule, and all of phase 5n's references at the mixed table, plus the "buying" v4c. The Hard v3 fills the mixed table. The tournament took 12 h 50 on 10 cores.

The entry rule passes with 4 and with 5 players: the 21 references all have their whole interval below 0. The closest ones, as the gap reference minus candidate, in dollars per round:

| Reference | 4 p. | 5 p. |
|---|---|---|
| "buying" v4c (reference until now) | -10.33 [-10.93; -9.74] | -10.96 [-11.52; -10.40] |
| quiet v4c | -13.25 [-13.93; -12.58] | -12.67 [-13.25; -12.09] |
| selling v4c | -13.54 [-14.23; -12.86] | -13.90 [-14.44; -13.37] |
| timed v4c | -14.47 [-15.08; -13.86] | -13.81 [-14.34; -13.29] |
| v4c | -16.35 [-17.13; -15.57] | -13.45 [-14.17; -12.73] |
| v4b | -18.39 [-19.20; -17.57] | -11.02 [-11.75; -10.29] |
| reading exploiter | -47.13 [-48.19; -46.08] | -37.60 [-38.50; -36.70] |

Against three copies of one opponent, compared with the "buying" v4c in phase 5n's full tournament, on the same deals:

| Opponent | v4c_achat_v3, 4 p. | "buying" v4c, 4 p. | v4c_achat_v3, 5 p. | "buying" v4c, 5 p. |
|---|---|---|---|---|
| Hard v3 | +54.52 [+53.66; +55.38] | | +50.41 [+49.68; +51.13] | |
| bayesian | +32.18 | +25.73 | +33.87 | +25.45 |
| marginal | +13.43 | +13.00 | +10.03 | +9.16 |
| heuristic | +41.26 | +41.39 | +38.51 | +39.23 |
| sniper | +32.24 | +32.24 | +30.05 | +30.05 |
| recalibrated Hard (5j) | +13.83 [+12.81; +14.86] | +17.83 [+16.91; +18.75] | +11.80 [+10.94; +12.66] | +16.55 [+15.75; +17.34] |
| phase 5c Hard | +33.78 | +41.71 | +32.39 | +38.00 |

The "buying" v4c had not played the Hard v3 in 5n; in phase 5r's reduced tournament, it beat it by $34.76 with 4 players and $33.38 with 5. All the numbers are in `resultats/phase5s/tournoi_complet.md`.

## Does the bot progress?

Yes, in the sense of the entry rule and on the real rounds. `v4c_achat_v3` passes the entry rule at both sizes, in the reduced tournament as in the full one. Against the "buying" v4c, at the same table, it makes $10.33 per round more with 4 players and $10.96 with 5. That is the largest gap of any promotion since the rule has been played at the mixed table. Its reading of the goal also improves on the real rounds, the only measure in this phase that does not depend on the simulator. So I promote it: it becomes the reference bot, in place of the "buying" v4c.

It comes at a price. Against the simulated Hard bots of phases 5c and 5j, it makes $4 to $8 less per round than the "buying" v4c. Its reading trusts bids more, which pays when they point to the goal and costs when they do not. The promotion therefore bets that the site looks more like the Hard v3 than like the old ones. The real rounds point that way.

## Limits

The gain at the mixed table is measured with the Hard v3, and the reading was learned with it. The tournament therefore favours a bot that learned on that same Hard bot. The check on the real rounds is about reading the goal, not about gains.

The Hard v3 overpays for non-goal cards. Part of what the "buying" v4c takes from it, about $2.8 per round, comes from there, and `v4c_achat_v3` probably benefits from it too.

The Hard v3 and the new reading both come from a single 4-player table, against Rasmus's bot, over 60 rounds. Nothing says the site behaves the same way with 5 players.

The v4c's settings were learned again in phase 5m with the old reading. I did not learn them again with the new one.

Everything is still measured on paper or against simulated bots. These numbers are not real gains on figgie.com.

## Reproduce

```bash
cd projets/bot-figgie
python3 -m unittest                                                  # the 149 tests, about 7 s
PYTHONPATH=. python3 resultats/phase5s/gain_v3.py 500
python3 -m figgie.learn --site --hard hard_simule_v3 --train 2400 --valid 600 --out modeles/signaux_site_v3.json --report resultats/phase5s/signaux_site_v3.json
PYTHONPATH=. python3 resultats/phase5s/mesure_reelle.py
python3 -m figgie.tournoi --site --candidates v4c_achat_v3 --rounds 10 --deals 100 --no-tables --filler hard_simule_v3 \
  --opponents heuristique sniper bayesien marginal hard_simule hard_simule_v2 hard_simule_v3 --references \
  --mixed v4c_achat hard_simule_v2 bayesien marginal adaptatif_v3 adaptatif_v4b adaptatif_v4c v4c_calme_60 v4c_vente_60 \
          exploiteur exploiteur_lecteur vendeur parieur v4c_temps \
  --out resultats/phase5s/tournoi_reduit.json
python3 -m figgie.tournoi --site --candidates v4c_achat_v3 --rounds 10 --deals 300 --no-tables --filler hard_simule_v3 \
  --opponents heuristique sniper bayesien marginal hard_simule hard_simule_v2 hard_simule_v3 --references \
  --mixed v4c_achat hard_simule heuristique sniper bayesien marginal adaptatif_v3 adaptatif_v4b exploiteur \
          exploiteur_lecteur imitateur fondamentaliste fondamentaliste_35 vendeur mante parieur hard_simule_v2 \
          adaptatif_v4c v4c_calme_60 v4c_vente_60 v4c_temps \
  --out resultats/phase5s/tournoi_complet.json
```

On 10 cores, the diagnostic takes 3 min, learning 32 s, the reduced tournament 2 h 50 and the full tournament 12 h 50. The outputs are in `resultats/phase5s/`. To get this phase's exact code back: `git checkout phase5s-figgie`.
