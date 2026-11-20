# Phase 4: league and robustness

*Version française : [phase4.fr.md](phase4.fr.md)*

Earlier phases always measured a candidate alone against copies of one opponent. Phase 3 showed this is not enough: when readers are numerous at the table, a lone opponent exploits them. This phase looks for that kind of weakness systematically. It adds a minority test to the entry rule, has the machine search for the opponents that beat our bots best, retrains the reader on games where it plays against itself and against those opponents, then confronts it with abnormal behavior: an idle player, a spammer, liars.

The outcome is clear, and it is negative. No candidate passes the full entry rule with 4 and with 5 players. Even the reference bot, the marginal bot, gets exploited when it is in the minority. Tuning does not get out of this: when the spread is tightened, the bot gets exploited, and when it is widened, it loses to the others. That is the phase's main lesson. With fixed settings, there is probably no bot that cannot be exploited, because the right strategy depends on what the others do.

## A faster engine, with nothing changed

The phase 3 tournament took almost two hours. Before running more, I profiled the engine. The bottleneck was not the engine itself: half the time went into computing the gain from one card, called more than a million times for 8 rounds, while the same situations keep coming back. The program now keeps every result it has already computed. The slowest rounds go from 49 to 30 milliseconds, the others from 23 to 16.

To check that nothing changed, I first recorded, with the phase 3 engine, the profits and the full log fingerprint of several rounds and of one three-round game. A so-called golden test replays those rounds and requires the same values, to the cent. It also checks that the learned model has not changed, so that a failure points at the engine and not at a model relearned in the meantime.

## The minority test

The entry rule required clearly beating every reference: a confidence interval entirely above zero, playing alone against three or four copies of it. It now also requires the reverse: each reference, alone against copies of the candidate, must not clearly win. A bot that gets exploited when it is numerous at the table is rejected, even if it wins head to head.

## Exploiters found by the machine

To find our bots' weaknesses, I had the machine search automatically for the opponent that takes the most from them. An exploiter is a bot of the common mechanics, defined by six settings:

- where its values come from (heuristic, bayesian or marginal);
- its spread and its taking edge;
- its reaction speed;
- whether it quotes or only takes;
- its pace.

The search has three stages, each on its own deals, so as not to keep a setting that was simply lucky. First, 60 randomly drawn settings are tried on 60 deals (seed 5). The 6 best are measured again on 300 other deals (seed 6). Finally the winner is measured on the 1,000 tournament deals (seed 1), which no earlier stage saw. Every measurement puts the exploiter alone against copies of the target bot.

| Target bot | 4 players | 5 players |
|---|---|---|
| marginal | +$4.35 [+3.54, +5.15] | +$7.22 [+6.56, +7.88] |
| reader | +$2.78 [+1.88, +3.69] | +$8.50 [+6.89, +10.11] |

The exploiter's profit per round. Both of our best bots are exploitable.

Three of the four searches found the same exploiter: bayesian values, a $6 spread, a $3 edge and a 0.3-second reaction. It quotes closer to its value than the marginal bot, which quotes at $8, so its prices are the best in the book and it is the one others come to. But it is more demanding about taking a quote ($3 minimum edge instead of $1). Against three marginal bots, it becomes the table's market maker. Against the reader with 5 players, the best exploiter uses marginal values, a $4 spread, a $3 edge, and acts at most every 2 seconds.

These two exploiters join the zoo. That is the league: they serve both as opponents in the entry rule and as players in the learning games. Alone against copies they win. The other way round, against copies of them, the marginal bot beats them comfortably (+$19.9 and +$12.8 with 4 players).

## The league: relearning the reader

The phase 3 reader had learned at tables where nobody read the market. I relearned its signal model on 4,000 league rounds, with new seeds (7 for learning, 8 for validation). Those tables were drawn from the whole zoo, readers, exploiters and liars included. The new model finds the goal suit 51.5% of the time at one minute, as much as the phase 3 one, but on much more varied tables. Its probabilities stay well calibrated.

I then tuned the spread and edge of this "league reader" with 5 players, where the reader had failed. I included the minority test against the 10 zoo opponents, with 12 combinations at first, then two wider spreads. With a $3 edge, the best one:

| Spread | Against the marginal bot | Marginal alone against readers | Random alone against readers | Worst lower bound |
|---|---|---|---|---|
| $3 | -1.1 | +43.2 | +44.2 | -52.5 |
| $4 | +0.8 | +34.5 | +26.6 | -40.2 |
| $6 | +2.8 | +21.1 | -4.7 | -25.9 |
| $8 | +0.8 | +9.0 | -34.9 | -12.6 |
| $10 | -2.9 | +5.9 | -55.5 | -9.0 |
| $12 | -5.5 | +5.2 | -68.8 | -10.2 |

Profits in dollars per round, with 5 players, on the training deals (seed 2, 150 deals). The "alone" columns give the profit of the lone opponent against four readers: the higher it is, the more the readers get exploited.

The table shows the dilemma. With a tight spread, four readers compete for the same customers by undercutting each other, and even a lone random player takes $44 per round from them. With a wide spread, exploitation goes down, but the reader then loses to the marginal bot. No setting wins on both sides. The criterion set in advance, the best worst case, picks a $10 spread.

## Abnormal behavior

Three abnormal bots, outside the zoo:

- the idle player never does anything, like a disconnected player;
- the spammer posts random quotes as fast as it can;
- the liar plays like the marginal bot, but every 6 seconds posts a $12 bid in the suit it considers least useful, and withdraws it 1.5 seconds later. It targets bots that read the market.

The spammer forced a limit into the engine, as on a real site: at least 0.05 seconds between two actions of the same player, so at most 20 actions per second. No existing bot is that fast, and the golden test confirmed it. Code review flagged two flaws in the liar. The first was real: its fake bid could be refused because it crossed its own offer, and it then stopped lying for 6 seconds. It is fixed. The second was only half true: when it withdraws its fake bid, it also withdraws its real offer in that suit, but it reposts it as soon as the lie is over. A test checks both.

| Table (4 players, 300 deals) | marginal | reader | league reader |
|---|---|---|---|
| idle, heuristic, marginal | +21.7 | +20.7 | +15.3 |
| spammer, heuristic, marginal | +122.8 | +109.6 | +99.1 |
| liar, liar, heuristic | +19.1 | +16.1 | +18.3 |
| the same, 10-round games | +19.4 | +16.8 | +19.7 |

All three candidates clearly win at every one of these tables. The spammer gets emptied out by everyone.

The liar barely fools the reader, and memory is not the reason. Over 200 games of 10 rounds, the reader that remembers its opponents makes on average $0.75 per round less than the one that forgets, with an interval of [-1.82, +0.32] that contains zero. At the end of a game it gives the liars only 0.84 trust, against 0.95 for the heuristic. The explanation is probably phase 3's deduplication: each signal counts only once per player, suit and price range. A liar who repeats its lie every 6 seconds therefore weighs no more than a single lie, and the rest of its quotes, those of a marginal bot, are useful.

## Results

The three candidates were measured against the 10 zoo opponents, with the minority test against the 4 references, on 1,000 duplicate deals (seed 1). The tournament took 1 h 12 on 10 cores.

| Candidate | 4 players, no minority | 4 players, with | 5 players, no minority | 5 players, with |
|---|---|---|---|---|
| marginal | accepted | rejected: bayesian alone +1.35 [+0.34, +2.36] | accepted | accepted |
| reader | accepted | accepted | rejected: against marginal +0.7 [-0.3, +1.7] | rejected: marginal alone +7.35 [+6.0, +8.7] |
| league reader | accepted | accepted | rejected: against marginal -1.34 [-2.24, -0.43] | rejected: marginal alone +4.67 [+3.4, +5.9] |

A few more rows, in dollars per round:

| | marginal | reader | league reader |
|---|---|---|---|
| against the exploiter, 4 p. | +19.9 | +26.5 | +27.2 |
| against the reader's exploiter, 5 p. | +9.5 | +8.0 | +7.9 |
| against the passive bot, 4 p. | +15.2 | +19.8 | +21.3 |
| league reader against reader | | | -1.6 (4 p.), -1.9 (5 p.) |

No candidate passes the full entry rule. So none is promoted, and the marginal bot remains the reference, now known not to be unexploitable. With 4 players, a bayesian alone against three marginal bots makes +$1.35 per round, and the exploiter found by the machine +$4.35. The league reader does no better than the reader: it even loses a little to it, with 4 and with 5 players. Relearning on the league and tuning for the minority test did not solve the problem.

## What I took away

A bot with fixed settings is a target. Every setting has its counter-strategy, and the machine finds it in minutes. Against marginal bots quoting $8 from their value, quoting at $6 is enough to take all the flow. Against tight readers, even a random player wins. In game theory, a bot that no lone opponent could exploit would be a symmetric Nash equilibrium. Such a thing exists, but nothing guarantees finding it by picking two numbers once and for all.

Copies compete with each other. Four identical bots want the same cards, at the same price, and fight for the same majority. A different player profits from this price war. To avoid it, a bot would have to notice it has competitors that look like it and adjust its play during the game, for example by quoting less tightly when others already quote at the same price.

That is the strongest argument for the rest of the project. A bot that adjusts its settings during the game, to the table in front of it, is no longer a fixed target. It is also what the project asked for from the start: a bot that learns from every game. Phase 3's memory learned whom to trust, and that earned nothing. Learning how to play against this particular table should earn more, and the minority test will tell whether it does.

Actively looking for weaknesses beats waiting for them. The starting zoo was written by hand, and the marginal bot beat all of it. A 20-minute search was enough to find two opponents that beat it in the minority.

## Limits

All opponents are still bots, whether written by hand or found by search. The exploiter search only explores the common-mechanics family, with six settings. Opponents from another family might find other weaknesses.

The minority test uses only the four references (heuristic, sniper, bayesian, marginal). The exploiters are not part of it, although they are the best exploiters. With them, the marginal bot would also be rejected with 5 players.

Settings were chosen on 150 training deals per opponent, which leaves intervals of a few dollars. The choice between two neighboring settings remains fragile.

The limits of earlier phases still hold: made-up reaction times, four assumed site rules, money resetting to $350 each round.

## Reproduce

```bash
cd projets/bot-figgie
python3 -m unittest                                              # the 87 tests, about 2 s
python3 -m figgie.exploit --target marginal --players 4          # one exploiter search, about 5 min
python3 -m figgie.learn --train 4000 --valid 1000 --league       # the league model, about 40 s
python3 -m figgie.tune --bot lecteur_ligue --players 5 --minority --spreads 3 4 6 8 --edges 1 2 3
python3 -m figgie.memoire --deals 200 --rounds 10 --table menteur,menteur,heuristique
python3 -m figgie.tournoi --candidates marginal lecteur lecteur_ligue --out tournoi.json   # about 1 h 15
```

To get exactly this phase's code back: `git checkout phase4-figgie`.

## Next

The logical next step is a bot that adapts its play during the game. It would keep the marginal bot's value calculation and the market reading, but choose its spread and edge round after round, according to what pays against the table in front of it. This is a bandit problem: try, measure, favor what works without ever stopping exploring. It will be measured with the same entry rule, minority test included, and against this phase's exploiters.
