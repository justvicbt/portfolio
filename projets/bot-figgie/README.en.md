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
| 1. Faithful simulator | figgie.com rules, continuous time, latency, 4 and 5 players | | Upcoming |
| 2. Bayesian teacher | Marginal card value by Monte Carlo, card counting, execution | | Upcoming |
| 3. Continual learning | Logs, model updates, a new version promoted only if it beats the old one | | Upcoming |
| 4. League and robustness | Self-play, opponents trained to beat the bot, abnormal behavior | | Upcoming |
| 5. Real site | Only with Jane Street's written consent, otherwise a training and analysis tool | | Upcoming |

figgie.com publishes no terms of use and says nothing about bots. I will not automate any ranked game without written consent from Jane Street.

## Results

After phase 0, the bayesian bot is the strongest of the five. Against the heuristic it makes +$41.4 per round with 4 players (95% interval: [+38.4, +44.3]) and +$43.1 with 5. Against a passive player, who quotes wide and never takes anything, it makes nothing at all: +$0.02, for lack of trades. Details and full tables are in the [phase 0 doc](docs/phase0.en.md).

## What I took away

The bayesian does not guess the goal suit better than the heuristic (38.1% against 38.5%). It wins because it knows how uncertain it is and does not dump cards that have a one-in-three chance of being valuable.

## Limits

All opponents are bots I wrote. No number in this project measures the level against humans until phase 5 has happened. The simulator is still simplified (time cut into ticks, tables without mixed styles).

## Run it

Python 3.14, no external dependencies.

```bash
cd projets/bot-figgie
python3 -m unittest                      # 27 tests, under a second
python3 -m figgie.evaluate --candidate bayesien --deals 1000 --seed 1
```

One candidate's tournament against the whole zoo takes about twenty seconds, the 10 phase 0 configurations about 4 minutes.

## Stack

- Python 3.14, standard library only
- unittest for the tests

## Status

In progress: phase 0 done. Next step: a simulator closer to figgie.com.
