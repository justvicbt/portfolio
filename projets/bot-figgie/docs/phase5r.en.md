# Phase 5r: a simulated Hard bot with a private hint

*Version française : [phase5r.fr.md](phase5r.fr.md)*

Phase 5q showed that making our simulated Hard bot read the others' highest bids harder does not make it more faithful to the site. In this phase, I first look at what the site's Hard bots actually react to. Then I model what I see, without knowing where it comes from: each of them seems to know better and better, as the round goes on, which suit is the goal.

So the Hard v3 receives a private hint about the goal, whose weight grows with time. Tuned on the real rounds, it is twice as close to the site as the recalibrated Hard bot, consensus included. The "buying" v4c still passes the entry rule with it at the mixed table, and it becomes that table's filler for the next phases. No playing bot changes. The measurements are made on Rasmus's 60 real rounds and against simulated bots, not on the site.

## What the site's bots react to

I look at one precise moment: a Hard bot bids in a suit a higher price than anything it had bid there since the start of the round, a "record". After each event from another player in the same suit, I count the other Hard bots' records in the next 10 s. I divide that number by what chance would give, at that bot's rate of records in that suit and in that minute. A ratio of 1 means "no reaction".

| Event in the suit | real rounds: goal | other suit | recalibrated Hard: goal | other suit |
|---|---|---|---|---|
| trade at $1-3 | none | 1.12 | 1.34 | 1.33 |
| trade at $4-6 | 1.24 | 1.01 | 1.10 | 0.89 |
| trade at $7 and more | 0.99 | 0.96 | 0.76 | 0.76 |
| ask shown | 1.00 | 0.93 | 0.97 | 0.98 |
| offer cancelled | 1.15 | 1.42 | 1.42 | 1.70 |
| table record bid | 1.00 | 1.13 | 1.39 | 1.57 |

Here the recalibrated Hard bots play 200 simulated rounds against the "buying" v4c, with the site rule (seed 9). The number of cases in each cell is in `resultats/phase5r/reactions.txt`.

The site's bots react to almost nothing public. Their ratios stay close to 1, except after a cancel, a rare event: 233 in 60 rounds (phase 5p). Our recalibrated Hard bots, on the other hand, follow the others' records: 1.39 and 1.57. That is their reading of the market, and it is what freezes the consensus when it is made stronger (phase 5q). One more detail: on the site, no goal card is traded at $1-3 in 60 rounds.

## Each bot on its own

If the site's bots do not read the others, where does their consensus come from? I took each Hard bot on its own. At each moment, I look at the suit where it bid its highest price over the last 30 seconds, and I count the share of cases where it is the goal. A tie between k suits counts as 1/k, and chance gives 25%.

| A bot's highest bid over the last 30 s | 60 s | 120 s | 180 s | 239 s |
|---|---|---|---|---|
| real rounds | 27% | 57% | 80% | 76% |
| recalibrated Hard | 51% | 55% | 57% | 64% |

A site bot knows no more than chance at 60 s, then finds the goal better and better, up to 80% at 180 s. Our recalibrated Hard bots know more at the start, from their hand, and then almost nothing changes. So each real bot receives, as the round goes on, information about the goal that ours do not have. According to the previous table, it does not come from the public market. I do not know what it is: a site rule, a reading of trades I have not spotted, something else. So I modelled it as it appears, without claiming to know how the site does it.

## The Hard v3

The engine now gives the goal only to the bots that ask for it (`sees_goal`). The Hard v3 (`HardBotV3`, `hard_simule_v3`) uses it as a hint. The simulated Hard bot already estimates the probability that each suit is the goal, from its hand and the others' bids. The Hard v3 multiplies these weights by:

- (1 - λ) / 4 + λ for the goal;
- (1 - λ) / 4 for the other suits;
- with λ = min(1, t / hint_time) ^ hint_power.

At t = 0, the hint says nothing. At t = hint_time, it points to the goal for certain. In between, it rises later the larger hint_power is.

A single seam, written with TDD, with two tests:
- at t = 0, the Hard v3 gives the same values as an ordinary Hard bot with the same setting, and at t = hint_time, it knows the goal;
- the engine gives the goal only to the bots that ask for it.

Both tests failed before the code. They catch three deliberate mistakes: ignoring the hint, giving λ a fixed value, not passing the goal on. The Hard v1 and v2 do not change, and the recorded games test still passes.

## The tuning

`figgie.calibrate` gets the `--hint` option, which tunes the Hard v3 with two more parameters: hint_time among 60, 120, 180, 240, 300 and 400 s, and hint_power among 0.5, 1, 2 and 3. The conditions are phase 5q's: 3,000 settings drawn at random, measured on 30 rounds between 4 Hard v3 bots (seed 31), then the best 10 checked again on 90 other rounds (seed 32), shares of offers taken and consensus included.

Before running the search, I had set the criterion: the Hard v3 is kept only if its gap to the site, consensus included, falls below the recalibrated Hard bot's 46.7, with a consensus of at least 85% at the bell.

| Measure | figgie.com | recalibrated Hard (5j) | Hard v3 (5r) |
|---|---|---|---|
| trades per round | 53.27 | 31.73 | 36.23 |
| trades per pair of Hard bots | 9.44 | 5.29 | 6.04 |
| share of trades per minute | 0.12 / 0.19 / 0.25 / 0.44 | 0.06 / 0.16 / 0.33 / 0.46 | 0.17 / 0.20 / 0.25 / 0.38 |
| quotes per minute | 37.75 | 58.75 | 57.38 |
| highest bid, goal | $10 | $8 | $9 |
| highest bid, other suits | $5 | $3 | $4 |
| non-goal asks taken at $1-3 | 30% | 25% | 21% |
| goal asks taken at $7-10 | 12% | 12% | 10% |
| consensus ranks the goal first at 120 / 180 / 239 s | 62 / 85 / 91% | 62 / 69 / 73% | 59 / 76 / 96% |
| gap to the site, with the consensus | | 46.7 | **23.5** |

The criterion is met. The setting kept is in `figgie/bots.py` and in `resultats/phase5r/calibration_hard_v3.md`: hint_time = 400 s and hint_power = 2. At the bell, the hint therefore weighs only (240 / 400)² = 0.36. The search chose a slow hint and almost no reading of the others (read = 0.05 instead of 0.2). The next best setting is at 34.4.

On its own, the Hard v3 also gets closer to the site in the previous table:

| A bot's highest bid over the last 30 s | 60 s | 120 s | 180 s | 239 s |
|---|---|---|---|---|
| real rounds | 27% | 57% | 80% | 76% |
| Hard v3 | 41% | 58% | 75% | 86% |

Gaps remain. It knows too much at 60 s, from its hand, and a little too much at the bell. It still trades less than the site. It also takes twice as many non-goal asks at $4-6 (13% against 6%).

## What it changes for the site reading

Phase 5p stopped on a reading with one damping per minute, chosen in simulation, that did no better on the real rounds. I ran the same prototype again, with validation rounds played with the Hard v3 (1,000 rounds, seed 52). The dampings chosen rise at the end of the round: 0.5, 0.5, 0.5 then 1.0. The table gives the probability of the true suit, the share ranked first and the log loss, on the real rounds:

| Real rounds | 120 s | 180 s | 225 s | 239 s |
|---|---|---|---|---|
| today (0.2 everywhere) | 0.41; 53%; 1.031 | 0.63; 77%; 0.610 | 0.78; 85%; 0.406 | 0.81; 85%; 0.360 |
| chosen with the Hard v3 | 0.49; 63%; 1.053 | 0.76; 83%; 0.547 | 0.86; 87%; 0.621 | 0.86; 85%; 0.547 |

With the Hard v3, the reading chosen in simulation does better on the real rounds at 120 and 180 s, which did not happen in 5p. At the end of the round, it finds the right suit a little more often but is wrong with too much confidence: its log loss rises from 0.360 to 0.547 at the bell. The signal model it uses was learned in phase 5d, on tables with phase 5c's Hard bot. It will probably have to be learned again before anything changes in the bot. I coded nothing in the repository for this reading.

## The tournament with the Hard v3 at the mixed table

I played phase 5n's reduced tournament again for the "buying" v4c (10 rounds, 100 deals, site rule), with the Hard v3 as the mixed table's filler instead of the recalibrated Hard bot. The tables with no filler keep phase 5n's numbers, since the deals are the same. Against three Hard bots of the same kind:

| "buying" v4c against | 4 p. | 5 p. |
|---|---|---|
| hard_simule_v2 | +17.58 [+16.00; +19.16] | +15.91 [+14.55; +17.27] |
| hard_simule_v3 | +34.76 [+33.31; +36.21] | +33.38 [+31.94; +34.82] |

At the mixed table, the gap reference minus "buying" v4c, in dollars per round (negative: the "buying" v4c does better):

| Reference | 4 p., recalibrated Hard | 4 p., Hard v3 | 5 p., recalibrated Hard | 5 p., Hard v3 |
|---|---|---|---|---|
| marginal | -18.88 | -46.51 | -13.42 | -39.30 |
| adaptatif_v3 | -13.45 | -44.39 | -10.22 | -38.99 |
| exploiteur_lecteur | -10.99 | -37.47 | +0.34 [-1.08; +1.75] | -31.26 [-32.68; -29.85] |
| adaptatif_v4b | -13.25 | -11.31 | -7.53 | -5.00 |
| adaptatif_v4c | -15.64 | -8.55 | -8.82 | -4.84 |
| v4c_calme_60 | -3.85 [-5.12; -2.57] | -4.68 [-5.78; -3.59] | -1.85 [-3.02; -0.67] | -3.79 [-4.73; -2.86] |
| v4c_temps | -4.45 [-5.56; -3.33] | -3.85 [-4.59; -3.12] | -3.29 [-4.15; -2.43] | -2.18 [-2.95; -1.40] |

All the rows, 95% confidence intervals included, are in `resultats/phase5r/tournoi_hard_v3.md`.

The "buying" v4c passes the entry rule at both sizes: no gap has its whole interval above 0. With the Hard v3, bids really point to the goal. The bots that read the market, those of the v4c family, stay close to the "buying" v4c. Those that do not read it, or read it badly, lose $25 to $30 more per round. The clearest case is the reading exploiter at 5 players, the closest bot to it in phase 5n's tournament: it was level with the "buying" v4c, and it now loses $31 per round.

One point worries me. The "buying" v4c beats three Hard v3 bots by $35 per round, twice as much as three recalibrated Hard bots. I have not looked yet at where this gain comes from. The real rounds do not say whether the site's bots let themselves be beaten that much.

## The Hard v3 becomes the filler

Changing the filler moves every measurement of the next phases. I only did it after showing these numbers and asking the question. `figgie.tournoi --mixed` now takes the Hard v3 by default. To replay phases 5j to 5q's tournaments, add `--filler hard_simule_v2`.

## Does the bot progress?

No, this phase changes no playing bot. It brings the simulator closer to the site on the point phase 5p had found. The "buying" v4c remains the reference bot and passes the entry rule with the new filler. The gaps with its variants move by $1 to $7, and it stays ahead of each of them.

## Limits

The Hard v3 cheats: the engine gives it the goal. I reproduce what the site's bots seem to know, without knowing how they know it. If their information comes from somewhere else, for example from their own reading of trades, the Hard v3 may be wrong about how that information reacts to our bot's play.

The tuning is still imperfect. The Hard v3 knows too much early in the round, trades less than the site, and takes too many non-goal asks at $4-6.

The "buying" v4c beats it by $35 per round. If it is easier to exploit than the real bots, the tournaments will overrate the bots that exploit it.

The tuning comes from a single 4-player table, against Rasmus's bot, over 60 rounds. Nothing says the Hard v3 behaves like the site with 5 players.

The site reading's signal model was not learned again with the Hard v3.

Everything is still measured on paper or against simulated bots. These numbers are not real gains on figgie.com.

## Reproduce

```bash
cd projets/bot-figgie
python3 -m unittest                                                  # the 148 tests, about 7 s
PYTHONPATH=. python3 resultats/phase5r/reactions.py
PYTHONPATH=. python3 resultats/phase5r/individuel.py
python3 -m figgie.calibrate --settings 3000 --rounds 30 --keep 10 --lift --consensus --hint --out resultats/phase5r/calibration_hard_v3.json
PYTHONPATH=. python3 resultats/phase5r/attenuation_v3.py 1000
python3 -m figgie.tournoi --site --candidates v4c_achat --rounds 10 --deals 100 --no-tables --filler hard_simule_v3 \
  --opponents heuristique sniper bayesien marginal hard_simule hard_simule_v2 hard_simule_v3 --references \
  --mixed hard_simule_v2 bayesien marginal adaptatif_v3 adaptatif_v4b adaptatif_v4c v4c_calme_60 v4c_vente_60 \
          exploiteur exploiteur_lecteur vendeur parieur v4c_temps \
  --out resultats/phase5r/tournoi_hard_v3.json
```

On 10 cores, the search takes about 5 min, the diagnostics a few minutes each and the tournament about 2 h 30. The outputs are in `resultats/phase5r/`. To get this phase's exact code back: `git checkout phase5r-figgie`.
