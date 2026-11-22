# Phase 5f: the minority test

*Version française : [phase5f.fr.md](phase5f.fr.md)*

Since phase 4, none of my bots passes the minority test. A player alone against copies of the bot wins money, which means the bot gets exploited when it is numerous at the table. In phase 5e, three players exploited v4b: the phase 4 exploiter (+$4.05 per round with 4 players, +5.85 with 5), v3 (+1.00 and +3.01) and the marginal bot with 5 players (+0.92). This phase looks for why, and tries to fix it.

The diagnosis finds a cause. A copy that buys cards from the exploiter profits from it, but the copies as a whole lose, and my training judged each setting only by the gain of a single copy. So I trained a v4c on tables judged by the mean gain of the copies.

In the tournament, the exploiter now takes only $3.15 per round from its copies with 4 players and $4.65 with 5, against 4.05 and $5.85 from v4b. v3 with 5 players goes from 3.01 to $2.46. But the same three players still exploit it, so does v4b with 5 players (barely), and it wins a little less against the marginal bot. No bot is promoted.

## Step 0: three diagnoses

### No fixed setting holds everyone

I first played each fixed setting against each reference: the reference alone, every other seat held by the site reader with that setting. I took v4b's 6 settings, then 4 more to see if one of them did better. Gain of the lone reference, in dollars per round (200 deals for the first 6 settings, 150 for the other 4):

| Setting | exploiter, 4 p. | exploiter, 5 p. | v3, 4 p. | v3, 5 p. | marginal, 5 p. | sniper, 4 p. |
|---|---|---|---|---|---|---|
| 6,3 | **-1.22** | **-0.77** | +0.37 | +1.67 | +1.40 | +1.60 |
| 8,1 | +2.65 | +4.51 | +4.70 | +5.01 | +0.58 | -4.34 |
| 10,3 | +0.81 | +2.83 | +3.04 | +7.55 | +2.58 | -5.73 |
| 12,3 | +1.60 | +3.43 | +6.54 | +11.97 | +5.49 | -6.23 |
| 8,1 → 3,1 | +4.47 | +6.27 | +1.10 | +3.44 | +1.56 | -2.63 |
| 12,3 → 4,1 | +4.25 | +6.18 | +3.64 | +7.43 | +3.19 | -8.61 |
| 4,3 | +2.45 | +1.40 | +5.38 | +3.41 | +3.61 | +10.03 |
| 6,5 | **-1.54** | **-0.72** | +1.16 | +4.12 | +4.11 | +2.18 |
| 6,3 → 3,1 | +1.05 | +1.68 | +0.61 | +2.27 | +1.92 | +3.08 |
| 4,1 | +3.25 | +2.22 | +4.35 | +3.12 | +2.18 | +9.79 |

The tight settings (6,3 and 6,5) hold the exploiter, but the sniper profits from them. The wide settings hold the sniper, but the exploiter and v3 profit from them. Above all, with 5 players, v3 wins against each of the 10 settings, at least +$1.67 per round. So picking the right setting will not be enough to pass the test with 5 players against v3.

### How the exploiter wins

I then looked at what the exploiter does alone against 3 copies of v4b, over 100 games of 10 rounds, and compared it with a v4b placed in the same seat, on the same deals.

The exploiter does almost nothing but sell: 3.9 cards per round, one of them a goal card, at $9.5 on average for the other suits and $10.8 for the goal suit. It buys almost nothing (0.07 cards per round). It gets $38 of cash out of it, loses $10 of goal cards sold, and gives up on the majority: it collects $3 of it per round, against $25 for a v4b in its seat. In total, it wins +$4.09 per round, against -$1.55 for v4b.

The copies, for their part, choose 8,1 → 3,1 in 91% of rounds. That is the setting that pays the exploiter the most in the table above (+$4.47). If all the copies played 6,3, it would lose $1.22.

### Why the training does not see it

The most surprising part comes next. For each card a copy buys from the exploiter, I counted what it is worth at the bell to that copy: its gain with the card, minus its gain without it. On average, a card bought from the exploiter brings +$3.75 to the copy that buys it. So buying pays off for each copy taken one at a time. What it wins comes mostly from the majority, which it takes from the other copies. The copies as a whole lose what the exploiter wins.

Yet the training of my adaptive bots judges each setting by the gain of a single copy. At the tables that look like the minority test, it therefore rewards the copy that buys from the exploiter, while the test measures what the exploiter takes from all the copies together.

## Step 1: training on the right criterion

### Symmetric tables

I added "symmetric" tables to v4b's training. A single bot plays there against copies that all have the same setting, and each setting is judged by the mean gain of the copies. The opponents are the 11 league bots, the simulated Hard bot, v3 and v4b, with 4 then 5 players. The rest of the model does not change. I call the result v4c.

The labels of these tables are right. At the exploiter's tables, 6,3 is the best setting for the copies, with 4 as with 5 players: +$0.20 per round with 4 players, against -$1.85 for 8,1 → 3,1 (mean of the three tables).

### The seam

This step's test plays a game of 4 rounds, the exploiter alone against 3 copies of v4c. After the first round, all the copies must play 6,3. v4b fails it: two copies move to 8,1 → 3,1.

v4c fails it too. With 28 symmetric tables (one per opponent and per number of players), two copies play 6,3 throughout, but the third goes back to 8,1 → 3,1 after a strong hand. I looked for why. Its five nearest neighbours almost all come from the old minority-like tables, which judge by the gain of a single copy and recommend 8,1 → 3,1. These old tables give the model 2,100 rows, barely more than the 1,680 of the symmetric tables.

So I tried three things, without success:

- **84 symmetric tables**, three per opponent and per number of players, on other deals. The copy still goes back to 8,1 → 3,1, with the same neighbours.
- **Removing the old minority-like tables.** It is worse: on three deals, most copies play 8,1 → 3,1.
- **Counting each row of the symmetric tables three times** among the neighbours. One or two copies out of three still move to 8,1 → 3,1. I removed this weight.

The cause seems deeper than the number of rows: with 84 tables, the symmetric tables give 5,040 rows, more than twice the old ones, and the copy is still wrong. The profile of a single round is very noisy: at the same table, the median spread a copy observes goes from $8 to $26 from one round to the next. And in a game, the copies do not all play the same setting, whereas at the symmetric tables they do. So their profiles fall outside those of the training: they quote more often, with tighter spreads.

I kept v4c with 84 tables and no weight. The seam test now checks the known failure. It will fail if there is an error, and also on the day all the copies play 6,3, so that it gets turned back the right way.

### What v4c changes in the minority test

Before the tournament, I measured the lone reference against copies of v4c and of v4b, on 100 deals from another seed than the tournament's:

| Lone reference | v4c, 4 p. | v4b, 4 p. | gap | v4c, 5 p. | v4b, 5 p. | gap |
|---|---|---|---|---|---|---|
| exploiter | +2.91 | +3.36 | **-0.45** [-0.87, -0.04] | +4.86 | +5.93 | **-1.07** [-1.52, -0.62] |
| v3 | +0.87 | +1.00 | -0.12 [-1.11, +0.87] | +2.72 | +3.70 | **-0.98** [-1.94, -0.02] |
| marginal | -0.69 | -0.69 | +0.00 [-0.88, +0.88] | +0.77 | +1.65 | **-0.89** [-1.72, -0.06] |
| sniper | -4.83 | -3.22 | **-1.61** [-2.21, -1.01] | -3.16 | -2.32 | **-0.83** [-1.43, -0.24] |

v4c leaves a little less to each reference, but the exploiter still wins clearly, and so does v3 with 5 players.

## Step 2: v3 and the marginal bot with 5 players

I compared v3, the marginal bot and a copy of v4c, each in the same seat against 4 copies of v4c, on the same 200 deals. Paired gaps per round, relative to the v4c copy:

| | v3 | marginal |
|---|---|---|
| gain | **+2.22** [+0.45, +4.00] | -1.34 [-3.06, +0.37] |
| majority share | **+2.26** [+0.75, +3.77] | **+2.56** [+1.05, +4.06] |
| goal cards at the bell | -0.01 [-0.06, +0.05] | -0.02 [-0.07, +0.04] |
| goal cards bought from the copies | +0.13 [+0.09, +0.16] | +0.09 [+0.06, +0.13] |
| goal cards sold to the copies | +0.13 [+0.10, +0.17] | +0.11 [+0.07, +0.15] |

v3 wins through the majority, without ending with more goal cards. It trades a few more of them, in both directions, and wins the majority a little more often. The marginal bot takes as much extra majority, but loses it in the cash from trades. This diagnosis does not show a cause precise enough for a targeted fix, so I did not make one.

## Step 3: the tournament

I replayed the phase 5e tournament, on the same 300 deals (seed 1), with the site rule and in games of 10 rounds. The candidate is v4c. v4b replaces v4 among the opponents and the references. v4b's numbers come from the phase 5e tournament. The tournament took 4 h 30 on 10 cores.

### Against tables of copies

Mean gain per round, in dollars, of each bot against copies of the opponent. All 95% CIs are at most ±$1.1.

| Opponent | v4b, 4 p. | v4c, 4 p. | v4b, 5 p. | v4c, 5 p. |
|---|---|---|---|---|
| simulated Hard | +35.77 | +35.86 | +34.51 | +34.67 |
| heuristic | +43.13 | +43.18 | +44.51 | +44.41 |
| sniper | +27.32 | +27.32 | +25.76 | +25.76 |
| Bayesian | +26.57 | +26.74 | +27.81 | +27.79 |
| marginal | +8.46 | +7.75 | +4.94 | +4.59 |
| v3 | -0.95 | -1.03 | -0.06 | -0.02 |
| v4 | -0.15 | | +0.08 | |
| v4b | | +0.13 | | -0.09 |

The two versions are within $0.2 of each other everywhere, except against the marginal bot: v4c wins $0.71 less there with 4 players (+7.75 [+7.24, +8.25] against +8.46 [+7.92, +9.01]) and $0.35 less with 5. Head to head, they are level: +0.13 [-0.19, +0.45] with 4 players, -0.09 [-0.38, +0.21] with 5.

### The minority test

Gain of a lone reference against copies of the bot. A positive number whose interval does not touch 0 means the bot gets exploited when it is numerous at the table.

| Lone reference | v4b, 4 p. | v4c, 4 p. | v4b, 5 p. | v4c, 5 p. |
|---|---|---|---|---|
| simulated Hard | -14.03 | -14.68 | -10.71 | -12.60 |
| heuristic | -26.82 | -26.75 | -26.78 | -26.96 |
| sniper | -3.23 | -4.87 | -2.75 | -3.80 |
| Bayesian | -2.13 | -2.54 | -0.39 | -1.20 |
| marginal | -1.02 | -0.80 | **+0.92** | **+0.77** |
| v3 | **+1.00** | **+0.94** | **+3.01** | **+2.46** |
| v4 | -0.25 | | +0.10 | |
| v4b | | +0.16 | | **+0.32** |
| exploiter | **+4.05** | **+3.15** | **+5.85** | **+4.65** |
| reading exploiter | -4.72 | -5.05 | -1.29 | -1.96 |

In bold, the gains whose interval is entirely above 0. For v4c: exploiter +3.15 [+2.69, +3.60] and +4.65 [+4.31, +4.99], v3 +0.94 [+0.42, +1.45] and +2.46 [+1.93, +2.99], marginal with 5 players +0.77 [+0.25, +1.29], v4b with 5 players +0.32 [+0.00, +0.63] (the lower bound is +0.002).

Almost every reference wins less against copies of v4c than against copies of v4b. The exploiter loses $0.90 per round with 4 players and $1.20 with 5, v3 with 5 players $0.55. This is consistent with the step 1 measurement, made on other deals. But the exploiter, v3 and the marginal bot with 5 players still win, and v4b alone against copies of v4c wins too, by very little. So v4c does not pass the entry rule, and the marginal bot stays the reference.

### Compared with phase 5e

| | v4b (phase 5e) | v4c (phase 5f) |
|---|---|---|
| lone exploiter, 4 p. / 5 p. | +4.05 / +5.85 | **+3.15 / +4.65** |
| lone v3, 4 p. / 5 p. | +1.00 / +3.01 | +0.94 / +2.46 |
| against the marginal bot, 4 p. / 5 p. | +8.46 / +4.94 | +7.75 / +4.59 |
| head to head with v4b, 4 p. / 5 p. | | +0.13 / -0.09 |
| exploited by | exploiter, v3, marginal (5 p.) | exploiter, v3, marginal (5 p.), v4b (5 p., barely) |

The bot improves a little in the minority test, where the phase aimed, without passing it. It does not improve elsewhere: it is level with v4b and wins a little less against the marginal bot. The two tournaments use the same deals, but I have no paired gap between them: only the paired measurements of step 1 give an interval on the difference. These gains are measured against simulated bots: they are not real gains.

## What I take from it

The main lesson is about what the training measures. The minority test asks whether the copies as a whole get money taken from them. My training asked whether one copy won money. Against the exploiter, the two questions have opposite answers: buying its cards brings $3.75 to the copy that buys, and costs the copies as a whole. Judging by the right criterion reduced what the exploiter takes, by about $1 per round, but not enough.

The second lesson is about nearest neighbours. Adding correct rows is not enough when the test's tables fall outside the training's. The profile of a single round is very noisy, and the copies of an adaptive bot do not all play the same setting, whereas at the symmetric tables they do.

Finally, with 5 players, none of my 10 fixed settings holds v3. Choosing better among the settings will not be enough: it will take another lever than the spread and the margin.

## Next

I see two leads. The first: make all the copies play the same way, by choosing the setting from what they all see, the public market, rather than from each one's hand. They would then look like the symmetric tables of the training. The second: change the lever, for example how the bot sells its goal cards or fights for the majority, since the spread and the margin do not hold v3 with 5 players. I will propose a precise plan before starting.

## Limits

The step 0 diagnoses were played on the first 200 deals of the tournament's seed. No bot was trained on them, but the choice of step 1's criterion relies on them. The step 1 measurement and the step 2 diagnosis use another seed.

The opponents at the symmetric tables are also the references of the minority test. The deals differ, but the tournament measures v4c against bots it saw in training, like v4 before it.

At the symmetric tables, the copies play a fixed setting for the whole game. In reality, v4c's copies all start at 8,1, then each changes setting on its own. So the training never sees exactly the table it prepares for.

Everything is still measured against simulated bots. These gains are not real gains on figgie.com.

## Reproduce

```bash
cd projets/bot-figgie
python3 -m unittest                                                  # the 118 tests, about 5 s
python3 -m figgie.adapt --v4c resultats/phase5e/entrainement_v4b.json --previous adaptatif_v3 adaptatif_v4_1 \
    --tables 84 --deals 40 --rounds 3 --arms 6,3,6,3 8,1,8,1 10,3,10,3 12,3,12,3 8,1,3,1 12,3,4,1 \
    --report entrainement_v4c.json
python3 -m figgie.tournoi --site --candidates adaptatif_v4c --rounds 10 --deals 300 --no-tables \
    --opponents hard_simule heuristique sniper bayesien marginal adaptatif_v3 adaptatif_v4b \
    --references hard_simule heuristique sniper bayesien marginal adaptatif_v3 adaptatif_v4b exploiteur exploiteur_lecteur \
    --out tournoi_site.json
```

Building v4c takes 51 minutes on 10 cores, the tournament 4 h 30. To go back to exactly this phase's code: `git checkout phase5f-figgie`.
