# Phase 5c: a market closer to the site

*Version française : [phase5c.fr.md](phase5c.fr.md)*

Until now, all my bots learned and were measured on a market I made up. In phase 5b, the logs of real games published by Rasmus Suonio showed how far that market is from figgie.com: 53 trades per round on the site, almost half of them in the last minute, against 6 to 22 on my tables, all in the first minute. A bot tuned on my tables is tuned for a game that does not exist.

This phase brings the simulator closer to the site in four steps: the site's rule for quotes, a simulated opponent tuned on the site's real bots, a replay of the real rounds with our bots, and a tournament on this new market.

The simulated Hard bot looks much more like the site than my earlier tables, without being a copy. On this new market, v3 is still the best of my adaptive bots: it takes $22 to $23 per round at a table of simulated Hard bots, against $20 for v2 and $17 to $19 for the marginal bot. But it still fails the minority test, against the same opponents as in phase 5b, and no bot is promoted. The replay of the real rounds gives another ranking: against the site's real bots, replayed on paper, only the Bayesian bot wins, and v3 and the marginal bot lose.

## Where the data comes from

Rasmus Suonio wrote a bot that plays on figgie.com against the site's "Hard" bots, and he published his logs under the MIT license. There are 60 rounds, played with 4 players: his bot and three Hard bots. Every quote, every cancel and every trade his bot saw is written down, to the second. I copied these files into `donnees/rasmus/`, with his license.

I ran nothing myself on figgie.com. Every measurement in this phase is made on these logs or in my simulator.

## Step 1: the site's rule for quotes

On the site, only one bid and one ask are shown per suit. A new offer has to beat the one shown, and it replaces it. My simulator kept one quote per player. I read the rule in Rasmus's code, which applies it the way the site's interface does, and I added it to the engine as an option (`single_quote`). It is off by default, so that the results of earlier phases do not move, and the golden test checks that.

The first try showed that my bots did not know this rule. When their offer was beaten, they sent it again and again, and the engine refused it every time: a table of marginal bots made about 2,300 refused actions per round, against 4 without the rule. My bots now know that an offer has to beat the one shown. They no longer send an offer that would be refused, and they cancel their quote when they want to move their price back. About fifteen refusals per round are left, caused by the market moving while an action is on its way.

With this rule, a quote my engine accepts is a new best offer, exactly like a quote in the logs. The two can be compared directly.

## Step 2: a simulated Hard bot

### What the real bots do

I measured the three Hard bots in the logs, leaving Rasmus's bot aside:

| Measure | figgie.com | table of 4 marginal bots, site rule |
|---|---|---|
| trades per round and per pair of Hard bots | 9.4 | 1.0 |
| share of trades in each minute | 12 / 19 / 25 / 44 % | 100 / 0 / 0 / 0 % |
| quotes per minute and per bot | 37.8 | 2.8 |
| first quote | 5 s | 0.6 s |
| median trade price, goal suit | $7 | |
| median trade price, other suits | $3 | |
| highest bid of a bot, goal suit | $10 | |
| highest bid of a bot, other suits | $5 | |

Medians per bot, except for the first two rows. I count trades per pair of Hard bots, because the logs have 3 Hard bots and my simulated tables have 4.

The logs also show how the site's bots quote. They raise their bid one dollar at a time above the best one ($1, then $2, then $3), and lower their ask the same way. They quote all the time. They do not agree with each other: 88 % of the cards a Hard bot dumps at $1 or $2 are followed, within 45 seconds, by a bid $2 higher from another Hard bot.

### The bot I wrote

My simulated Hard bot does the same. It estimates what a card of each suit is worth: a base, plus an amount times the probability that this is the goal suit, from its hand and the cards traded. It raises its bid one dollar above the best one, up to its value minus a margin, and lowers its ask down to its value plus the margin. The margin melts over the round. Each value gets a random offset, drawn again after each trade. Finally, it reads the market: a suit where the others bid higher becomes more likely to be the goal, because, according to Rasmus, the highest bids are what gives the goal away on the site.

I tuned its eight parameters with a random search. I drew 3,000 settings and played each one on 30 rounds with 4 simulated Hard bots (seed 31). I kept the 10 closest to the site and checked them again on 90 other rounds (seed 32). The distance to the site is a sum of squares, where each measure is divided by a scale I set by hand (for example 2 trades per pair, 8 quotes per minute, $1 for a price).

It took three versions of the bot. Without the random offset, my simulated Hard bots almost always agreed and barely traded: 0.7 trades per pair, against 9.4 on the site. With the offset, the number of trades went up, but prices fell to $1 or $2 and the goal suit no longer stood out. Reading the market from trade prices helped a little. Reading the highest bids, as Rasmus describes, does hardly better: the best setting reads the market only very slightly (read = 0.05), and the second one, almost as close to the site, does not read it at all. Here is the setting I kept:

| Measure | figgie.com | simulated Hard |
|---|---|---|
| trades per round and per pair of bots | 9.4 | 6.5 |
| share of trades in each minute | 12 / 19 / 25 / 44 % | 16 / 19 / 25 / 40 % |
| quotes per minute and per bot | 37.8 | 53.3 |
| first quote | 5.0 s | 5.6 s |
| median price, goal suit | $7 | $9 |
| median price, other suits | $3 | $3 |
| highest bid, goal suit | $10 | $8 |
| highest bid, other suits | $5 | $6 |

Measured on the 90 check rounds.

The simulated Hard bot is not a copy of the site's bots. It trades a third less, quotes more often, and a trade-off remains: the more it trades, the worse it tells the goal suit apart. But it looks much more like the site than my earlier tables. Trades spread over the whole round and speed up towards the end, the goal suit sells higher than the others, and every measure is between 0.6 and 1.5 times the site's. A test checks these two conditions on other deals, and also checks that a table of marginal bots fails them.

## Step 3: replaying the real rounds

### On paper

Rasmus's paper_bot replays a real round with another bot in place of his. I wrote the same thing for my bots. My bot takes Rasmus's seat, with his real hand. The book is the one in the log, and my bot can take the real quotes of the site's bots. Its own quotes are never filled, and the market does not react to what it does.

The score of a round is the money won or lost on these takes, plus $10 per extra goal card at the bell. It has two flaws, which Rasmus also points out. The majority, worth $100 or $120, is not counted, because we do not know the other players' hands. And every take is filled, while in reality a bot on the site would sometimes be faster. This score is for comparing bots with each other, not for saying how much they would win.

Replaying a market that does not react also creates impossible situations. My bot can buy a card that a site bot will later really sell to another player. I had to refuse purchases that would give my bot more cards than the deck holds, and strike the real trades of Rasmus that can no longer happen (selling a card already sold on paper, for example).

| Bot, in place of Rasmus's | Score per round | Takes per round |
|---|---|---|
| Bayesian | +8.97 [+0.43, +17.50] | 23.5 |
| adaptive v3 | -18.83 [-27.28, -10.39] | 20.5 |
| marginal | -26.37 [-35.33, -17.41] | 23.1 |
| reader | -26.88 [-34.02, -19.75] | 19.9 |
| simulated Hard | -37.15 [-45.51, -28.79] | 17.4 |
| heuristic | -41.83 [-56.72, -26.95] | 23.4 |

On the 60 real rounds. The v3 keeps its memory from one round to the next, within each of the 6 series of rounds played at the same table.

The Bayesian bot is the only one that clearly wins on paper. The marginal bot and the reader lose, but this score is unfair to them: they pay more for the cards that can give them the majority, and the majority is not counted. The v3 loses less than the marginal bot, although both use the same value calculation. Over the rounds, it therefore picked settings that suit these real bots better. My simulated Hard bot loses a lot: the random offset that makes it look like the site's bots also makes it take bad prices.

### Are the probabilities right?

I also looked, from Rasmus's seat, at the probability each method gives to the true goal suit, over the round:

| Method | 0 s | 60 s | 120 s | 180 s | 239 s |
|---|---|---|---|---|---|
| hand only | 0.30 (45 %) | 0.30 (45 %) | 0.30 (45 %) | 0.30 (45 %) | 0.30 (45 %) |
| card counting (marginal) | 0.30 (45 %) | 0.30 (45 %) | 0.31 (47 %) | 0.31 (47 %) | 0.31 (45 %) |
| counting and market reading (reader) | 0.30 (45 %) | 0.29 (33 %) | 0.39 (45 %) | 0.54 (68 %) | 0.71 (88 %) |

Mean probability of the true suit, and in brackets the share of rounds where it is the suit judged most likely.

Three things come out of this. Card counting learns almost nothing on the real market, as on mine in phase 5b. Market reading works on the site even though it only learned on my bots: at the bell, it finds the right suit in 88 % of rounds. Rasmus's bot, which reads the market with rules made for these bots, finds it in 58 rounds out of 60. Finally, the reading goes wrong early in the round: at one minute, it does worse than the hand alone, because the site's bots often bid $10 to $15 for dead suits.

## Step 4: the tournament on the new market

I replayed the phase 5b tournament with the site rule, on the same 300 duplicate deals (seed 1), in games of 10 rounds. To make it fit in an afternoon (3 h 25 on 10 cores), I only kept the simulated Hard bot, the heuristic, the sniper, the Bayesian and the marginal bot as opponents, and I skipped the tables of abnormal behaviors. The minority test keeps all its references, plus the simulated Hard bot.

### Against tables of copies

Mean gain per round, in dollars, of each bot against copies of the opponent. All 95 % CIs are narrower than ±$1.6.

| Opponent | marginal, 4 p. | v2, 4 p. | v3, 4 p. | marginal, 5 p. | v2, 5 p. | v3, 5 p. |
|---|---|---|---|---|---|---|
| simulated Hard | +16.58 | +20.03 | +22.37 | +19.11 | +19.79 | +23.26 |
| heuristic | +38.23 | +38.16 | +38.06 | +42.11 | +42.11 | +42.88 |
| sniper | +15.73 | +16.80 | +26.07 | +17.06 | +17.70 | +25.27 |
| Bayesian | +21.71 | +21.71 | +21.73 | +22.31 | +22.19 | +21.95 |
| marginal | | +1.95 | +8.57 | | +3.09 | +4.70 |

At a table of simulated Hard bots, v3 wins more than v2, which wins more than the marginal bot. With 4 players, the intervals do not touch: +22.37 [+21.61, +23.13] for v3, +20.03 [+19.17, +20.89] for v2, +16.58 [+15.75, +17.40] for the marginal bot.

### The minority test

Gain of a reference alone against copies of the bot. A positive number whose interval does not touch 0 means the bot gets exploited when there are many of it at the table.

| Reference alone | marginal, 4 p. | v2, 4 p. | v3, 4 p. | marginal, 5 p. | v2, 5 p. | v3, 5 p. |
|---|---|---|---|---|---|---|
| simulated Hard | -13.90 | -13.79 | -18.64 | -15.97 | -16.27 | -17.58 |
| heuristic | -26.74 | -26.66 | -27.03 | -28.75 | -28.60 | -28.84 |
| sniper | -0.97 | **+3.71** | -4.94 | -1.15 | **+2.93** | -1.04 |
| Bayesian | **+1.29** | **+0.90** | **+1.69** | -0.26 | -0.60 | **+0.52** |
| marginal | | **+1.36** | -3.18 | | -0.00 | -2.02 |
| exploiter | **+4.04** | **+1.46** | **+4.96** | **+6.99** | **+3.12** | **+7.77** |
| reading exploiter | -2.03 | -4.65 | -7.09 | -3.75 | -5.62 | -6.39 |

In bold, the gains whose interval is entirely above 0. For v3: Bayesian +1.69 [+1.06, +2.32] and +0.52 [+0.10, +0.93], exploiter +4.96 [+4.51, +5.41] and +7.77 [+7.45, +8.09].

None of the three bots passes the entry rule. All of them clearly beat every reference, but all of them get exploited. The simulated Hard bot, for its part, loses a lot when it is alone: $14 to $19 per round.

### Compared with phase 5b

v3 is the same bot as in phase 5b, with the same model. What changes is the market. Against the zoo, the site rule changes almost nothing, on the same deals:

| v3, 4 players | phase 5b, without the rule | phase 5c, site rule |
|---|---|---|
| against the marginal bot | +8.48 | +8.57 |
| against the sniper | +26.23 | +26.07 |
| exploiter alone | +5.27 | +4.96 |
| Bayesian alone | +1.43 | +1.69 |
| sniper alone | -4.86 | -4.94 |

It is the same for the marginal bot (exploiter alone: +4.32 in phase 5, +4.04 here) and for v2 (sniper alone: +3.72 and +3.71). Only one result changes sides: with 5 players, the Bayesian bot alone against copies of v3 goes from +0.27 [-0.12, +0.67] to +0.52 [+0.10, +0.93]. It is a small gap, but it puts the Bayesian bot among the exploiters with 5 players too.

So the bot does not improve in this phase: I changed nothing in v3, and it is still refused for the same reasons. What the phase brings is a test market closer to the site, on which v3 stays ahead of v2 and the marginal bot. These gains are still measured against simulated bots: they are not real gains.

## What I take away

The simulator looks more like the site, but the ranking of my bots on simulated tables does not move. The replay of the real rounds gives another one: the Bayesian bot first, then v3, then the marginal bot. The Bayesian bot, which all my bots beat by about $22 per round in simulation, is the only one that wins on paper against the site's real bots. I see two explanations and I cannot decide between them yet: either my simulator rewards things the site does not, or the paper score favors the Bayesian bot because it does not count the majority.

Market reading, learned on my bots, works on the real bots late in the round: 88 % right suits at the bell. Early in the round it goes wrong, because the site's bots bid high for dead suits. That is the most concrete lead this phase gave me.

Finally, v3 is still exploited by the phase 4 exploiter and by the Bayesian bot, as in phase 5b. Changing the quote rule does not change that.

## What next

The next step will be to retrain v3 on this market, with the site rule and simulated Hard bots at the table, to fix market reading early in the round, and to measure each change both on the replay of the real rounds and in a tournament. I will propose a precise plan before starting.

## Limits

The simulated Hard bot is tuned on 60 rounds, all played against Rasmus's bot, at a single table. These logs therefore also contain the way his bot plays, and say nothing about 5-player tables or the site's other bot levels. Clear gaps with the real bots also remain, described in step 2.

The paper replay does not count the majority, fills every take, and does not make the market react. Its scores are for comparing bots, nothing more.

Everything is still measured against bots: simulated bots, or the site's real bots replayed on paper. Nothing here measures the level against humans, nor what my bots would really win on figgie.com.

## Reproduce

```bash
cd projets/bot-figgie
python3 -m unittest                                                  # the 113 tests, about 15 s
python3 -m figgie.calibrate --settings 3000 --rounds 30 --keep 10 --out calibration_hard.json
python3 -m figgie.reel --stats --paper marginal adaptatif_v3 lecteur bayesien heuristique hard_simule --calibration
python3 -m figgie.tournoi --site --candidates marginal adaptatif_v2 adaptatif_v3 --rounds 10 --deals 300 --no-tables \
    --opponents hard_simule heuristique sniper bayesien marginal \
    --references hard_simule heuristique sniper bayesien marginal exploiteur exploiteur_lecteur --out tournoi_site.json
```

The settings search takes about 7 minutes on 10 cores, the replay of the real rounds 10 seconds. To get back to exactly this phase's code: `git checkout phase5c-figgie`.
