# Phase 5i: what the minority test measures

*Version française : [phase5i.fr.md](phase5i.fr.md)*

Since phase 4, none of my bots has passed the minority test: a reference plays alone against three copies of the candidate, and if it clearly makes money, the candidate is refused. Phases 5f, 5g and 5h tried to change how the copies choose their setting, and the exploiter kept winning. Phase 5h proposed changing the lever. Before touching the bot, I wanted to know exactly where the money the exploiter takes from the copies comes from.

The diagnostic shows that the copies do not overpay for the exploiter's cards. Each purchase pays off for the copy that makes it. What they lose is the majority they take from each other. So I replaced the minority test with a mixed table: the reference, the candidate and simulated Hard bots at the same table. With this new test, the v4c is refused even more clearly: at a table close to the site, the exploiter does about $10 better than it per round. No bot is promoted.

## Where the exploiter's gain comes from

I replayed 40 matches of 10 rounds, the exploiter alone against three copies of the v4c, with 4 players, and sorted each of its trades: buy or sell, goal suit or not. Each card is counted at its end-of-round value, $10 if it is of the goal suit, 0 otherwise. What remains of the gain, once the trades and the starting cards are removed, is the majority. Per round:

| Exploiter alone against 3 v4c | $ per round | trades per round |
|---|---|---|
| sales of non-goal cards | +23.90 | 2.46 |
| sales of goal cards | +0.49 | 1.12 |
| purchases | -0.11 | 0.06 |
| starting cards minus the ante | -26.90 | |
| majority | +3.88 | |
| total | +1.26 | |

These are plain matches, without duplicate deals: the total is noisy, but the breakdown is clear. The exploiter almost never buys. It sells the copies, at around $10, cards that are worth nothing at the end seven times out of ten.

## Why the copies buy

I then replaced the copies with a probe, the v4c logging each of its buying decisions: the value it gave the card, and the probability it read from the market that the suit was the goal. For each card bought, I also computed what it really brought in, majority included, by giving it back to the seller at the end of the round and recomputing the gains. Average per card sold by the exploiter:

| | $ per card |
|---|---|
| price paid | 9.93 |
| value the copy gave it | 16.12 |
| what the card brings the copy that buys it | 17.32 |
| what the card brings the three copies together | 4.50 |

Two things stand out. The copies read the goal suit well: they give it about a 25 % chance, and 29 % of the cards bought in that bracket were goal cards. So they do not overestimate the suit. And each purchase does pay off for the copy that makes it, about $7 above the price. But most of that gain is majority taken from another copy. For the group, a card paid $9.93 only brings $4.50. The v3 gives the same picture: $9.55 paid, $17.76 for the buyer, $4.29 for the copies.

This calculation ignores the trades the card would have changed later in the round. It gives an order of magnitude, not an exact measure.

So the minority test punishes a behaviour that pays when the bot plays alone. Three copies fighting for the same majority lose together, even if each one plays well for itself. Making the copies more careful when buying would probably let them pass the test, but would cost the bot when it is alone.

## The new test: the mixed table

With 4 players, the mixed table brings together the reference, the candidate and two simulated Hard bots, which imitate the site's bots. With 5 players, three Hard bots. For each deal, I play every rotation of [reference, candidate, Hard, Hard], then those of [candidate, reference, Hard, Hard]: each one goes through every seat, in front of and behind the other. In each game, I read the reference's gain and the candidate's, and keep the gap. The candidate is refused if the gap for one reference has a confidence interval entirely above 0. The rest of the entry rule does not change. The minority test can still be computed, and I give its verdict alongside.

I am changing the rule after a bot failed it, and that is the kind of thing that makes it easy to prove yourself right. That is why I write it here, with the diagnostic that justifies it and the old verdict next to the new one. As it turns out, the new test is stricter on the v4c than the old one.

The tests go through two seams. The first checks that the entry rule refuses a candidate as soon as a gap at the mixed table is clearly positive, on hand-written intervals. The second covers how the gap is computed: with an identical reference and candidate, each game has a twin where the two bots swapped seats, so the gap must be exactly 0 on every deal. This test caught a real bug in my first version: when both bots were of the same class, the seat swap was not detected. One last test checks the sign: a Bayesian bot against a random bot gives a positive gap, and the test does fail when I flip the sign on purpose.

The code review also found a flaw in my very first version: I computed the reference's gain and the candidate's in two different sets of games, where they did not sit in the same seats. So the gap was not paired. I stopped the running tournament, fixed it, and ran everything again.

## Calibration: does the test still catch the marginal bot?

The minority test was born in phase 4, when the exploiter was winning against copies of the marginal bot. Before the tournament, I checked that the mixed table still sees that case, on 100 deals from seed 7. Gap reference minus candidate, in dollars per round:

| | marginal, 4 p. | marginal, 5 p. | v4c, 4 p. | v4c, 5 p. |
|---|---|---|---|---|
| exploiter | +22.36 [+21.00 ; +23.73] | +23.78 [+22.70 ; +24.87] | +10.06 [+8.62 ; +11.50] | +9.78 [+8.42 ; +11.14] |
| v3 | +4.15 [+3.07 ; +5.24] | +5.00 [+4.17 ; +5.83] | -7.56 [-8.95 ; -6.16] | -11.71 [-13.12 ; -10.29] |

The test does catch the marginal bot. But it also refuses the v4c, by $10, three times what the minority test showed.

To find out who takes money from whom, I counted 30 games at the table [exploiter, v4c, Hard, Hard], in a single seating, each trade counted at the card's final value, without the majority. Per round, the exploiter makes a net $38.97 from the two Hard bots and $10.84 from the v4c. The v4c makes $10.37 from the Hard bots. Even as the only one of its kind at the table, the v4c keeps buying the exploiter's non-goal cards, although part of that money surely comes back to it through the majority. Above all, the exploiter takes almost four times more from the Hard bots than the v4c does.

## The tournament

The same 300 deals as in the previous phases (seed 1), the site rule, 10-round matches. Against the zoo, I get exactly the v4c's phase 5f numbers back: +$7.75 and +$4.59 against the marginal bot, with 4 and 5 players. The engine is indeed deterministic, and the entry rule without any exploitation test still passes.

At the mixed table, the gain gap reference minus candidate, in dollars per round, next to the gain of the reference alone against the copies in the phase 5f minority test:

| Reference | mixed table, 4 p. | mixed table, 5 p. | minority 5f, 4 p. | minority 5f, 5 p. |
|---|---|---|---|---|
| exploiter | **+10.43** [+9.67 ; +11.20] | **+8.81** [+8.17 ; +9.46] | +3.15 | +4.65 |
| Bayesian | **+3.65** [+2.79 ; +4.52] | **+7.13** [+6.44 ; +7.81] | -2.54 | -1.20 |
| v4b | -0.44 [-0.91 ; +0.04] | -0.38 [-0.70 ; -0.06] | +0.16 | +0.32 |
| seller | -7.46 [-8.21 ; -6.70] | -10.08 [-10.74 ; -9.41] | | |
| v3 | -7.91 [-8.69 ; -7.14] | -11.90 [-12.64 ; -11.15] | +0.94 | +2.46 |
| marginal | -12.58 [-13.33 ; -11.83] | -16.45 [-17.14 ; -15.76] | -0.80 | +0.77 |
| reader exploiter | -13.91 [-14.71 ; -13.12] | -16.50 [-17.25 ; -15.75] | -5.05 | -1.96 |
| gambler | -21.10 [-22.11 ; -20.09] | -24.57 [-25.42 ; -23.73] | | |
| mantis | -31.08 [-32.02 ; -30.14] | -35.20 [-35.98 ; -34.42] | | |
| sniper | -34.09 [-35.03 ; -33.15] | -31.88 [-32.59 ; -31.17] | -4.87 | -3.80 |
| fundamentalist (r = 1.7) | -35.98 [-37.06 ; -34.90] | -32.49 [-33.30 ; -31.67] | | |
| fundamentalist (r = 3.5) | -39.82 [-40.85 ; -38.79] | -37.79 [-38.45 ; -37.13] | | |
| imitator | -44.72 [-45.85 ; -43.59] | -42.06 [-43.00 ; -41.11] | | |
| simulated Hard | -47.82 [-49.20 ; -46.45] | -43.22 [-44.19 ; -42.25] | -14.68 | -12.60 |
| heuristic | -69.35 [-70.59 ; -68.11] | -71.32 [-72.36 ; -70.27] | -26.75 | -26.96 |

The two columns do not measure the same thing. The mixed table compares two gains at the same table, the minority test gives the gain of the reference alone against the copies: the orders of magnitude cannot be compared, only the signs can be read together. The empty cells are references added after phase 5f.

In bold, the references that do clearly better than the v4c at the mixed table: the entry rule fails with 4 and with 5 players, because of the exploiter and the Bayesian bot. With the old rule, it also failed, because of the exploiter, the v3 and the marginal bot with 5 players. So the bot does not progress: the v4c has not changed, and the new rule refuses it like the old one. No bot is promoted, and the v4c remains my best bot. All these numbers are measured against simulated bots: they are not real gains.

## What I take from it

The two tests do not see the same opponents. The v3 and the marginal bot were winning against the v4c's copies, but at a mixed table they make $8 to $16 less than it per round: they mostly profited from the majority race between copies. Conversely, the Bayesian bot was losing against the copies, but at a table with Hard bots it does $4 to $7 better than the v4c.

The exploiter and the Bayesian bot have one thing in common: both are Bayesian bots, which value a card from their own hand only, without the majority Monte Carlo. The exploiter just quotes tighter. At a table of simulated Hard bots, this simple bot does better than my best bot. The minority test hid it behind the majority race between copies.

A first diagnostic, the exploiter then the v4c alone against three simulated Hard bots, over 40 matches of 10 rounds, shows where the difference comes from. The exploiter makes +$46.68 per round, almost all of it by selling non-goal cards to the Hard bots: 6.6 cards per round at around $9.94, for +$65.83. It wins the majority in only 2 % of rounds. The v4c makes +$32.81. It wins the majority in 40 % of rounds (+$36.33), but it buys 1.9 non-goal cards per round, mostly in the first minute, and loses $18 on them. It also sells fewer non-goal cards, and cheaper: 4.6 cards per round at $8.72 on average, when the Hard bots take its quotes.

## Next

Phase 5j will start from there: why the v4c cannot sell to the Hard bots the way the exploiter does, and whether its first-minute purchases are worth what they cost. Before changing the bot, I will check on Rasmus's real rounds whether the site's real bots really buy non-goal cards at around $10, like my simulated Hard bots. In phase 5e, the Bayesian bot, which sells its cards at $10, finished last on the replayed real rounds. The simulated Hard bot may be too generous a buyer. A first look points that way: over the 60 real rounds, the site's bots pay Rasmus's bot $4.19 on average for a non-goal card, and only 6 % of these purchases are at $9 or more. In my simulation, the simulated Hard bots pay the exploiter $9.81 for these cards, at $9 or more 83 % of the time. This is not proof yet, since Rasmus's bot may simply ask less. I will propose a plan before starting.

## Limits

The purchase diagnostic counts each card by giving it back to the seller at the end of the round. It does not see the trades this card would have changed afterwards. The count of who takes money from whom at the mixed table covers a single seating and 30 games, so it is noisier than the tournament.

The new test depends on the filler. With simulated Hard bots, it measures who plays best against them as much as what the reference takes from the candidate. If the simulated Hard bot is far from the site's real bots, so is the test.

At the mixed table, the reference and the candidate are always neighbours, one right in front of the other. With 5 players, the seatings where a Hard bot sits between them are never played. The zero-gap test checks that the seat swap is tracked, not which seats are read: the sign test, and a check by hand, cover that point.

The tournament keeps only the mean of each cell. For the mixed table, this is not a problem, since the gap is paired deal by deal before being averaged.

Everything is still measured against simulated bots. These gains are not real gains on figgie.com.

## Reproduce

```bash
cd projets/bot-figgie
python3 -m unittest                                                  # the 131 tests, about 5 s
python3 -m figgie.tournoi --site --candidates adaptatif_v4c --rounds 10 --deals 300 --no-tables \
    --opponents heuristique sniper bayesien marginal --references \
    --mixed hard_simule heuristique sniper bayesien marginal adaptatif_v3 adaptatif_v4b exploiteur \
        exploiteur_lecteur imitateur fondamentaliste fondamentaliste_35 vendeur mante parieur \
    --out tournoi_mixte.json
python3 -m figgie.tournoi --site --seed 7 --candidates marginal adaptatif_v4c --rounds 10 --deals 100 --no-tables \
    --opponents --references --mixed exploiteur adaptatif_v3 --out calibration.json
```

The tournament takes about 6 h 20 on 10 cores, the calibration 20 min. `--references` with no name skips recomputing the minority test. To get back to the exact code of this phase: `git checkout phase5i-figgie`.
