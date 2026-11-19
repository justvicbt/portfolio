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
| 2. Bayesian teacher | Marginal card value by Monte Carlo, card counting, execution | | Upcoming |
| 3. Continual learning | Logs, model updates, a new version promoted only if it beats the old one | | Upcoming |
| 4. League and robustness | Self-play, opponents trained to beat the bot, abnormal behavior | | Upcoming |
| 5. Real site | Only with Jane Street's written consent, otherwise a training and analysis tool | | Upcoming |

figgie.com publishes no terms of use and says nothing about bots. I will not automate any ranked game without written consent from Jane Street.

## Results

After phase 1, in continuous time, the bayesian bot is still the reference bot. It beats the heuristic by +$33.5 per round with 4 players (95% interval: [+30.7, +36.3]) and the sniper, the fastest opponent, by +$4.0. Against a passive player, who quotes wide and never takes anything, it makes nothing: -$0.05 with 4 players, and with 5 it even loses 6 cents per round, a statistically clear loss. Full tables are in the [phase 0](docs/phase0.en.md) and [phase 1](docs/phase1.en.md) docs.

## What I took away

The bayesian does not guess the goal suit better than the heuristic (38.1% against 38.5%). It wins because it knows how uncertain it is and does not dump cards that have a one-in-three chance of being valuable.

In continuous time, speed changes everything: the sniper, which only takes mispriced quotes, became the second-best bot. And between bots that never change their minds, the market dies after about twenty seconds. Learning by watching other players will probably be the biggest gain ahead.

## Limits

All opponents are bots I wrote. No number in this project measures the level against humans until phase 5 has happened. The simulator rests on assumptions: four rules the site does not specify, and made-up reaction times. Tables do not mix styles yet.

## Run it

Python 3.14, no external dependencies.

```bash
cd projets/bot-figgie
python3 -m unittest                      # 38 tests, under a second
python3 -m figgie.evaluate --candidate bayesien --deals 1000 --seed 1
```

One candidate against the whole zoo takes 2 to 4 minutes, the full phase 1 tournament about 40 minutes. Each phase has a git tag (`phase0-figgie`, `phase1-figgie`) to get the exact code back.

## Stack

- Python 3.14, standard library only
- unittest for the tests

## Status

In progress: phases 0 and 1 done. Next step: computing what a card is really worth, to beat the passive player.
