# Phase 5e: two questions left by 5d

*Version française : [phase5e.fr.md](phase5e.fr.md)*

Phase 5d left me with two questions. On the real figgie.com rounds replayed on paper, the Bayesian bot won $13.5 more per round than v4, even though all my bots beat it by a wide margin in simulation. Why? And why did v4 win half as much as v3 against the sniper?

This phase answers both. The first lead came from the replay score, which did not count the majority. With an estimated majority, the Bayesian bot drops to the bottom of the ranking and v4 moves to the top. The second came from a gap in v4's training: it had never seen a table where nobody quotes. I filled it, which gives v4b.

In the tournament, v4b wins twice as much as v4 against the sniper (+$27.32 per round against +$13.11) and is level with it everywhere else. It still fails the minority test, against the same three players as in phase 5d. No bot is promoted.

## Step 1: the Bayesian bot and the majority

### The problem

The paper replay puts my bot in the seat of Rasmus's bot, with its real deal, and lets it take the real quotes of the site's bots. Until now, its score counted the money from the takes and $10 per extra goal card at the bell. It did not count the majority, because I do not know the hands of the site's bots.

But the majority is worth $100 or $120 with 4 players. The Bayesian bot values a goal card at about $10 times the probability that it is the right suit: it does not count the majority either. That is almost exactly the scoring rule. So I suspected the score favoured it.

### Estimating the majority

Rasmus's logs contain two things I had not used: the real gain of his bot in each round, majority included, and its hand at the bell. By removing the stake, the money from its trades and $10 per goal card, I get its real share of the majority. It comes out exact in all 60 rounds: $0, $100 or $120 when it won the majority alone, $50 or $60 when it shared it.

I still do not know the hands of the site's bots, but I can draw possible ones. I draw the deck according to Rasmus's deal, then the hands of the three others. I keep only the draws where every sale in the log is of a card the seller had, and where Rasmus gets exactly his real share of the majority. It takes between a few hundred and a few tens of thousands of draws to keep 200 per round.

I then replay the round on paper as before, tracking the goal cards that my takes moved from one hand to another. For each possible hand, I recompute my bot's share of the majority. The new score is the old one, plus the mean share over the 200 hands, minus Rasmus's real share. The drawn hands are the same for every bot.

The test for this step is a hand-written round. Rasmus keeps his 5 hearts and shares the majority ($50). My bot buys 4 hearts from seat 1. With 9 hearts, the deck necessarily has 10 and nobody else can have more than one: it has the majority alone, worth $100. I also checked by hand that a bot that does nothing gets exactly 0 on the 60 real rounds.

### The result

Score per round on the 60 real rounds, counted against what Rasmus's bot really won (about +$60 per round):

| Bot | Without the majority | With the estimated majority | Majority share |
|---|---|---|---|
| adaptive v4 | -4.57 | **-18.72** [-31.15, -6.28] | -14.15 |
| site reader | -15.72 | -32.49 | -16.77 |
| exploiter | **+17.27** | -41.20 | -58.47 |
| adaptive v3 | -18.83 | -43.35 | -24.52 |
| marginal | -26.37 | -48.67 | -22.30 |
| Bayesian | +8.97 | -55.20 | -64.17 |

I redid the computation with two other seeds, which change the drawn hands and the bots' randomness. The scores move by at most $3 per round, and the ranking does not change.

With the majority, the ranking flips. The Bayesian bot loses $64 of majority per round and goes from second place to last. v4 becomes the best, $36.48 per round [+19.23, +53.73] ahead of the Bayesian bot, $24.63 [+9.81, +39.45] ahead of v3, and $22.48 [+5.95, +39.02] ahead of the exploiter. These gaps are paired, round by round.

Breaking down the Bayesian bot's takes shows where its loss comes from. It sells 4.8 goal cards per round on average, at the price the site's bots offer, because to it a goal card is only worth $10. Without the majority, these sales paid off. With it, they often hand the majority to another player. v4, which counts the majority like the marginal bot, sells only 2.4 goal cards per round.

I draw two things from this. The replay without the majority ranked the bots badly, and the Bayesian bot's lead in phases 5c and 5d rested on it. And all my bots are still far behind Rasmus's bot on its own rounds.

The plan was to build a candidate inspired by the Bayesian bot if it kept its lead. It does not, so I did not build it.

## Step 2: v4 against the sniper

### The cause

I played each fixed setting against three snipers, on 40 tournament deals and in games of 10 rounds, with the site rule:

| Setting (spread, edge → late in the round) | played by the marginal bot | played by the site reader |
|---|---|---|
| 6,3 | +17.00 | +17.59 |
| 8,1 | +15.24 | +15.95 |
| 10,3 | +13.18 | +12.53 |
| 12,3 | +11.30 | +9.92 |
| 8,1 → 3,1 | +23.56 | +25.91 |
| 12,3 → 4,1 | +27.16 | **+28.50** |

Against snipers, you need a wide spread that tightens late in the round. v3 always picks 12,3 → 4,1 and wins +26.24. v4 always picks 10,3 and wins only +12.75.

The reason lies in the table profile. A sniper never quotes: at a table of snipers, 100 % of the opponents are silent. None of v4's training tables was entirely silent, and the closest ones had only one silent player in three. So v4 extrapolates, and its five nearest neighbours all come from the same training table, where the best setting was 10,3. v3 had not seen one either, but its nearest neighbours gave it the right setting, by luck.

### The fix: v4b

The test I had planned for this step ("v4 does not pick the same settings against snipers and against simulated Hard bots") already passed without changing anything: it picks 6,3 against simulated Hard bots. So it measured nothing. I replaced it before writing the fix, with this one: at a table of snipers, v4b must pick one of the two settings that tighten late in the round. v4 fails it.

v4b is v4 with 24 more training tables: "full" tables, where all the opponents are copies of the same league bot (the 11 league bots and the simulated Hard bot, with 4 then 5 players). They are played like v4's, on deals that v4's training never used. I added their rows to the round-2 model, without retraining the rest. The build took 11 minutes on 10 cores.

Against snipers, v4b now picks 12,3 → 4,1. Its choices also change at other full tables, those of the aggressive, passive and random bots. At the minority-test-like tables, they change little. In cross-validation over all tables, choosing the setting brings in $4.52 per round [+3.67, +5.38] more than the fixed setting.

On the real rounds, v4b is level with v4: +$0.78 per round [-1.81, +3.38] without the majority, +2.63 [-1.94, +7.20] with it.

## Step 3: the tournament

I replayed the phase 5d tournament, on the same 300 deals (seed 1), with the site rule and in games of 10 rounds. The candidate is v4b. I added v4 to the opponents and to the references, to get the head-to-head both ways. The v4 numbers come from the phase 5d tournament, played on the same deals. The tournament took 4 h 10 on 10 cores.

### Against tables of copies

Mean gain per round, in dollars, of each bot against copies of the opponent. All 95 % CIs are at most ±$1.1.

| Opponent | v4, 4 p. | v4b, 4 p. | v4, 5 p. | v4b, 5 p. |
|---|---|---|---|---|
| simulated Hard | +35.81 | +35.77 | +34.41 | +34.51 |
| heuristic | +43.00 | +43.13 | +45.62 | +44.51 |
| sniper | +13.11 | **+27.32** | +11.48 | **+25.76** |
| Bayesian | +25.42 | +26.57 | +27.36 | +27.81 |
| marginal | +8.29 | +8.46 | +4.91 | +4.94 |
| v3 | -1.02 | -0.95 | +0.17 | -0.06 |
| v4 | | -0.15 | | +0.08 |

Against the sniper, v4b wins $14 more per round than v4, with 4 as with 5 players: +27.32 [+26.53, +28.11] against +13.11 [+12.46, +13.76]. It does better than v3 (+26.07), which held the best score against the sniper until now. Everywhere else, the two versions are within $1.2 of each other. Head to head, they are level: -0.15 [-0.42, +0.13] with 4 players.

### The minority test

Gain of a reference alone against copies of the bot. A positive number whose interval does not touch 0 means the bot gets exploited when there are many of it at the table.

| Reference alone | v4, 4 p. | v4b, 4 p. | v4, 5 p. | v4b, 5 p. |
|---|---|---|---|---|
| simulated Hard | -14.25 | -14.03 | -11.45 | -10.71 |
| heuristic | -26.66 | -26.82 | -26.83 | -26.78 |
| sniper | -3.26 | -3.23 | -2.79 | -2.75 |
| Bayesian | -2.01 | -2.13 | -0.52 | -0.39 |
| marginal | -0.73 | -1.02 | **+0.91** | **+0.92** |
| v3 | **+1.05** | **+1.00** | **+2.87** | **+3.01** |
| v4 | | -0.25 | | +0.10 |
| exploiter | **+3.93** | **+4.05** | **+5.78** | **+5.85** |
| reading exploiter | -4.53 | -4.72 | -2.08 | -1.29 |

In bold, the gains whose interval lies entirely above 0. For v4b: exploiter +4.05 [+3.58, +4.52] and +5.85 [+5.53, +6.17], v3 +1.00 [+0.48, +1.53] and +3.01 [+2.47, +3.54], marginal with 5 players +0.92 [+0.41, +1.44].

The minority test does not move: the same three players exploit v4b, by the same amounts to within a few cents. The fix aimed at tables of snipers, and that is all it changed. So v4b does not pass the entry rule, and the marginal bot stays the reference.

### Compared with phase 5d

| | v4 (phase 5d) | v4b (phase 5e) |
|---|---|---|
| against the sniper, 4 p. / 5 p. | +13.11 / +11.48 | **+27.32 / +25.76** |
| against simulated Hard, 4 p. / 5 p. | +35.81 / +34.41 | +35.77 / +34.51 |
| replay of the real rounds, with the majority | -18.72 | -16.09 (gap +2.63 [-1.94, +7.20]) |
| exploiter alone, 4 p. / 5 p. | +3.93 / +5.78 | +4.05 / +5.85 |
| exploited by | exploiter, v3, marginal (5 p.) | exploiter, v3, marginal (5 p.) |

The bot improves against the sniper, where the fix aimed, and only there. On the real rounds, the gap with v4 is too small to measure. It does not improve on the minority test. These gains are measured against simulated bots, or against real bots replayed on paper without the market reacting: they are not real gains.

## What I take from it

The most useful lesson of this phase is about measurement. For two phases, I believed the Bayesian bot did something better than my bots against the site's real bots. In fact, the replay score left out the majority, and the Bayesian bot is precisely the bot that leaves it out too. A score that ignores part of the game favours the bots that ignore it.

The second lesson is about nearest neighbours. They cannot tell that a table looks like nothing they have seen: they answer anyway, with the least distant neighbours. A single measurement never seen in training, a 100 % share of silent opponents, cost $14 per round against the sniper. Covering the extreme tables matters more than adding ordinary ones.

The minority test is still the wall, unchanged since phase 5d.

## Next

The minority test is the question left. Since phase 4, the exploiter wins against the copies of every one of my bots, and v3 and the marginal bot both win against v4b's copies. Before proposing what comes next, I want to know whether some fixed setting resists it, or whether the problem lies elsewhere. I will propose a precise plan before starting.

## Limits

The estimated majority rests on hands drawn at random among those that explain the log. I only check at the bell that the site's bots really had the cards my bot takes from them on paper, not during the round. The estimate is therefore a little optimistic for a bot that buys many goal cards. The replay still does not make the market react, and fills every take.

v4b fixes one precise gap in the training, tables where nobody quotes. Other tables that v4 has never seen can fool it the same way.

The real rounds come from a single table, against Rasmus's bot. Everything is still measured against bots, simulated or replayed on paper. These gains are not real gains on figgie.com.

## Reproduce

```bash
cd projets/bot-figgie
python3 -m unittest                                                  # the 117 tests, about 5 s
python3 -m figgie.reel --paper bayesien adaptatif_v4 adaptatif_v3 lecteur_site lecteur marginal sniper hard_simule \
    heuristique exploiteur --majority
python3 -m figgie.adapt --v4b resultats/phase5d/entrainement_v4_2.json --previous adaptatif_v3 adaptatif_v4_1 \
    --tables 24 --deals 40 --rounds 3 --arms 6,3,6,3 8,1,8,1 10,3,10,3 12,3,12,3 8,1,3,1 12,3,4,1 \
    --report entrainement_v4b.json
python3 -m figgie.tournoi --site --candidates adaptatif_v4b --rounds 10 --deals 300 --no-tables \
    --opponents hard_simule heuristique sniper bayesien marginal adaptatif_v3 adaptatif_v4 \
    --references hard_simule heuristique sniper bayesien marginal adaptatif_v3 adaptatif_v4 exploiteur exploiteur_lecteur \
    --out tournoi_site.json
```

Building v4b takes 11 minutes on 10 cores, the replay of the real rounds with the majority about twenty seconds, the tournament a little over 4 hours. To go back to exactly this phase's code: `git checkout phase5e-figgie`.
