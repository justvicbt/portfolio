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
| 4. League and robustness | Self-play, opponents trained to beat the bot, abnormal behavior | | Upcoming |
| 5. Real site | Only with Jane Street's written consent, otherwise a training and analysis tool | | Upcoming |

figgie.com publishes no terms of use and says nothing about bots. I will not automate any ranked game without written consent from Jane Street.

## Results

After phase 2, the new "marginal" bot beats every opponent in the zoo, with a 95% confidence interval entirely above zero, with 4 and with 5 players. Its worst opponent is the passive bot, which nobody had beaten so far: +$15.2 per round with 4 players ([+14.0, +16.5]). It also beats the previous reference bot, the bayesian, by +$20.6 per round.

In phase 3, the "reader" bot, which also reads other players' quotes, guesses the goal suit much better (52% at one minute, against 42%). But it wins only a little more than the marginal bot with 4 players (+$2.7 per round) and does not clearly beat it with 5. So it is not promoted: the marginal bot remains the reference. Full tables are in each phase's doc.

## What I took away

The bayesian does not guess the goal suit better than the heuristic (38.1% against 38.5%). It wins because it knows how uncertain it is and does not dump cards that have a one-in-three chance of being valuable.

In continuous time, speed changes everything: the sniper, which only takes mispriced quotes, became the second-best bot. And between bots that never change their minds, the market dies after about twenty seconds. Learning by watching other players will probably be the biggest gain ahead.

A goal card is not worth $10: it can tip the majority and be worth $60 or $110, depending on who sells it and who buys it. The bot that calculates this best wins mainly by waiting for other players' mistakes, with cautious quotes $8 away from its value.

Guessing better is not enough to win more: the information arrives when the market is already almost dead. And measuring calibration ("when the bot says 80%, is it right 80% of the time?") revealed a reasoning flaw that had been there since phase 2.

## Limits

All opponents are bots I wrote. No number in this project measures the level against humans until phase 5 has happened. The simulator rests on assumptions: four rules the site does not specify, and made-up reaction times. Tables do not mix styles yet.

## Run it

Python 3.14, no external dependencies.

```bash
cd projets/bot-figgie
python3 -m unittest                      # 74 tests, one second
python3 -m figgie.evaluate --candidate marginal --deals 1000 --seed 1
```

One candidate against the whole zoo takes a few minutes, the full phase 3 tournament almost 2 hours on 10 cores. Each phase has a git tag (`phase0-figgie` to `phase3-figgie`) to get the exact code back.

## Stack

- Python 3.14, standard library only
- unittest for the tests

## Status

In progress: phases 0 to 3 done. Next step: a self-play league, so the bot stops getting exploited when it is numerous at the table.
