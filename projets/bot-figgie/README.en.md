# Figgie bot

*A bot for Figgie, the market card game invented at Jane Street, built step by step: first a simulator and a way to measure, then a bot that learns from every game.*

*Version française : [README.md](README.md)*

## Why this project

Figgie feels like a miniature trading floor. Nobody knows what the cards are worth, everyone buys and sells at once, and other players' prices give away what they know. I wanted to see how far a program can learn to play it: estimating value under uncertainty, avoiding selling to someone who knows more, and improving game after game.

The end goal is a bot whose average profit per round stays positive against every type of opponent, with a confidence interval that excludes zero, and that keeps improving as it plays. Winning every round is impossible: the deal is random and part of the information stays hidden. What can keep improving is the average profit and the rating.

## What I did

The project moves in phases. Each one has its own doc, in French and English, and ends with a tournament compared against the previous phase.

| Phase | Content | Doc | Status |
|---|---|---|---|
| 0. Foundations | Tested engine, zoo of 5 opponents, duplicate-deal evaluation, log of every game | [FR](docs/phase0.fr.md) · [EN](docs/phase0.en.md) | Done |
| 1. Faithful simulator | One quote per player, continuous time, latency, takes at the price seen, new "sniper" opponent | [FR](docs/phase1.fr.md) · [EN](docs/phase1.en.md) | Done |
| 2. Marginal value | Card value by Monte Carlo depending on the other side, card counting, tuning on separate deals | [FR](docs/phase2.fr.md) · [EN](docs/phase2.en.md) | Done |
| 3. Reading the market | Signal model learned on simulated games, corrected card counting, multi-round games with opponent memory | [FR](docs/phase3.fr.md) · [EN](docs/phase3.en.md) | Done (bot not promoted) |
| 4. League and robustness | Faster engine, minority test, exploiters found by search, league, idle player, spammer and liars | [FR](docs/phase4.fr.md) · [EN](docs/phase4.en.md) | Done (no bot promoted) |
| 5. In-game adaptation | Recognizing the table by nearest neighbors and choosing its spread and edge round after round, tournament in 10-round games | [FR](docs/phase5.fr.md) · [EN](docs/phase5.en.md) | Done (no bot promoted) |
| 5b. Playing against its copies | Counting with offered sales, a spread that tightens over time, training against its own copies, hand strength | [FR](docs/phase5b.fr.md) · [EN](docs/phase5b.en.md) | Done (no bot promoted) |
| 5c. A market closer to the site | The site's quote rule, a simulated Hard bot tuned on 60 real rounds, paper replay of the real rounds, tournament on this market | [FR](docs/phase5c.fr.md) · [EN](docs/phase5c.en.md) | Done (no bot promoted) |
| 5d. Reading the site's market | Market reading by one-minute windows, with the consensus and trust per player, then a v4 trained on the site's market | [FR](docs/phase5d.fr.md) · [EN](docs/phase5d.en.md) | Done (no bot promoted) |
| 6. Real site | Only with Jane Street's written consent, otherwise a training and analysis tool | | Upcoming |

figgie.com publishes no terms of use and says nothing about bots. I will not automate any ranked game without written consent from Jane Street.

## Results

After phase 2, the new "marginal" bot beats every opponent in the zoo, with a 95% confidence interval entirely above zero, with 4 and with 5 players. Its worst opponent is the passive bot, which nobody had beaten so far: +$15.2 per round with 4 players ([+14.0, +16.5]). It also beats the previous reference bot, the bayesian, by +$20.6 per round.

In phase 3, the "reader" bot, which also reads other players' quotes, guesses the goal suit much better (52% at one minute, against 42%). But it wins only a little more than the marginal bot with 4 players (+$2.7 per round) and does not clearly beat it with 5. So it is not promoted: the marginal bot remains the reference.

In phase 4, an automatic search found opponents that beat the marginal bot when it is in the minority (+$4.35 per round alone against three marginal bots, +$7.22 against four). No candidate passes the full entry rule, minority test included. With fixed settings, every bot has its counter-strategy.

In phase 5, the "adaptive" bot chooses its spread and edge depending on the table it recognizes. It beats the marginal bot head to head (+$2.00 per round with 4 players, +$3.47 with 5), and the phase 4 exploiter now takes only $1.54 per round from it instead of $4.32. But a sniper alone against its copies makes +$3.72 per round: it fails the minority test and is not promoted.

In phase 5b, v3 of the adaptive bot trains against its own copies. It beats the marginal bot by +$8.48 per round with 4 players, and the sniper and the phase 5 taker lose again against its copies. But a "tight quoter" found by the automatic search takes +$6.25 per round from it, and the phase 4 exploiter +$7.79 with 5 players. Every candidate has its exploiter, like rock-paper-scissors. No bot is promoted.

In phase 5c, the simulator moves closer to the site thanks to Rasmus Suonio's logs of real games: the site's quote rule, and a simulated Hard bot whose market looks like figgie.com's. At a table of simulated Hard bots, v3 wins +$22.37 per round with 4 players, against +$20.03 for v2 and +$16.58 for the marginal bot. But it is still exploited by the phase 4 exploiter and by the Bayesian bot, and no bot is promoted. Replayed on paper in place of Rasmus's bot, against the site's real bots, only the Bayesian bot wins (+$8.97 per round), and v3 loses $18.83.

In phase 5d, the market reading learns that, on the site, a bid does not mean the same thing in the first minute and in the last. It no longer does worse than the hand alone early in the round. v4, trained on the site's market with this reading, wins +$35.81 per round at a table of simulated Hard bots, against +$22.37 for v3, and does $14 better than v3 per round on the real rounds replayed on paper. The Bayesian bot no longer exploits it, but the phase 4 exploiter still wins against its copies, and so does v3. No bot is promoted. Full tables are in each phase's doc.

## What I took away

The bayesian does not guess the goal suit better than the heuristic (38.1% against 38.5%). It wins because it knows how uncertain it is and does not dump cards that have a one-in-three chance of being valuable.

In continuous time, speed changes everything: the sniper, which only takes mispriced quotes, became the second-best bot. And between bots that never change their minds, the market dies after about twenty seconds. Learning by watching other players will probably be the biggest gain ahead.

A goal card is not worth $10: it can tip the majority and be worth $60 or $110, depending on who sells it and who buys it. The bot that calculates this best wins mainly by waiting for other players' mistakes, with cautious quotes $8 away from its value.

Guessing better is not enough to win more: the information arrives when the market is already almost dead. And measuring calibration ("when the bot says 80%, is it right 80% of the time?") revealed a reasoning flaw that had been there since phase 2.

A bot with fixed settings is a target: when it is numerous at the table, its copies compete with each other and a different player profits. Hence phase 5, a bot that adapts its play during the game.

A bandit learning from its profits sees only noise: a round's profit varies by about $65 from one deal to the next. Recognizing how the others play works better. But when every copy of the bot recognizes the same table, they switch settings together and fall back into the same price war.

Training against its own copies fixes that price war, but each version fixes the previous one's weakness and opens another. And logs of real games show the simulator is far from the site: 53 trades per round on figgie.com, between 6 and 22 at our tables.

Bringing the simulator closer to the site barely changes how my bots rank in simulation, but the replay of the real rounds ranks them differently. And market reading, learned only on my bots, finds the right goal suit in 88 % of the real rounds at the bell, but goes wrong early in the round.

On the site, when a bid arrives matters as much as its price: by separating the minutes, the market reading learned not to believe the bids of the first one. Against the simulated Hard bots, this brings the reader $9 per round, but it does not solve the minority test.

## Limits

All opponents are bots I wrote. No number in this project measures the level against humans until phase 6 (real site) has happened. The simulator rests on assumptions: four rules the site does not specify, and made-up reaction times. Tables do not mix styles yet.

## Run it

Python 3.14, no external dependencies.

```bash
cd projets/bot-figgie
python3 -m unittest                      # 115 tests, about 5 seconds
python3 -m figgie.evaluate --candidate marginal --deals 1000 --seed 1
```

One candidate against the whole zoo takes a few minutes, the phase 4 tournament (`python3 -m figgie.tournoi`) about 1 h 15 on 10 cores. Each phase has a git tag (`phase0-figgie` to `phase5d-figgie`) to get the exact code back.

## Stack

- Python 3.14, standard library only
- unittest for the tests

## Status

In progress: phases 0 to 5d done. Next step: understanding why the Bayesian bot wins on the real rounds, and why v4 leaves so much to the sniper. Phase 6 (real site) waits for written consent from Jane Street.
