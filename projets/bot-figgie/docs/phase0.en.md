# Phase 0: foundations for measuring

*Version française : [phase0.fr.md](phase0.fr.md)*

Before writing a bot that learns, I needed a way to tell whether it actually improves. This phase builds three things: a tested game engine, a family of opponents, and an evaluation method that separates skill from luck. It ends with a first tournament that serves as the starting point for the rest of the project.

## The game in two minutes

Figgie was invented at Jane Street in 2013 to train traders. It is played with 4 or 5 people. Each player starts with $350 and pays part of it into the pot, which always holds $200 ($50 each with 4 players, $40 with 5).

The deck has 40 cards in four suits, but they are not equal: one suit has 12 cards, two have 10 and the last one has 8. Nobody knows which is which. The suit that matters, called the goal suit, is the twin of the 12-card suit, meaning the other suit of the same color. If spades are the 12-card suit, the goal is clubs. So the goal suit always has 8 or 10 cards.

For 4 minutes, everyone buys and sells cards, with no turns. At the end, each goal card pays $10, and what is left of the pot goes to the player holding the most of them. With 10 goal cards, $100 is left for the majority; with 8, $120. Ties split it.

Two market rules matter a lot. A trade moves a single card. And after every trade, every quote from every player is wiped. You cannot leave an order sitting there: each new piece of information resets the market.

## The engine

The engine fits in one file, [`figgie/engine.py`](../figgie/engine.py). It deals the cards, keeps the order book, executes trades and computes the score.

For each suit, the book keeps the best bid (the highest price someone will pay) and the best offer (the lowest price someone will accept). A new quote must beat the previous one. If someone bids at or above a resting offer, the trade happens at the resting price, as on a real exchange. The engine refuses anything impossible: selling a card you do not have, bidding more money than you hold, trading with yourself, sending a malformed action.

Time is simplified for now. A round is cut into 200 "ticks". On each tick, every player acts once, in a random order. Phase 1 will replace this with continuous time, closer to the real site.

A bot sees only what a human player would see: its hand, its cash, the book, the public trade history and how many cards each player holds. Other players' hands stay hidden.

Every round produces a JSON log: the deal, each action in order, and whether it was accepted. Replaying the log without the bots gives exactly the same result. The rest of the project builds on this, because these logs will become the training data for the learning bot. If a log has been tampered with, the replay detects it and stops instead of producing wrong numbers.

## The tests

I wrote the engine test-first: a failing test, then the minimum code to make it pass. The 27 tests run in under a second and cover four entry points.

The full round. The deck has 12, 10, 10 and 8 cards, the goal is the twin of the 12-card suit, and each player gets 10 cards with 4 players and 8 with 5. The score is checked against hand-computed examples, ties included. Over dozens of rounds, the total money never changes: whatever one player wins, another lost.

The order book. A trade moves exactly one card and the agreed price. After a trade, every quote disappears, including in the other suits. Impossible actions are refused.

The log. It goes to JSON and back without loss, replaying it gives the same profits, and tampering is detected.

The evaluation, described below. One test checks that a bot facing copies of itself wins exactly zero on every deal. If the seat rotation skipped a seat, this test would fail.

## The opponents

A bot that beats one kind of opponent can lose to another. So the zoo has five of them, in [`figgie/bots.py`](../figgie/bots.py).

| Bot | How it plays |
|---|---|
| random | Acts one tick in three, at random: a quote between $1 and $20, or it takes someone else's. |
| heuristic | Assumes its longest suit is the 12-card one. It values the twin at $12 and everything else at $0. |
| bayesian | Computes the probability that each suit is the goal, then values a card at probability × ($10 + a $5 bonus). |
| aggressive | Same belief as the heuristic, but pays up to $20, quotes tight and acts on every tick. |
| passive | Same values as the bayesian, but quotes wide, rarely, and never takes a quote. |

The last four share the same mechanics. They estimate what a card of each suit is worth. If they see an offer below that value, they buy. If they see a bid above it, they sell. Otherwise they bid a little below their value and offer a little above.

The bayesian's calculation deserves an explanation, because the whole project will build on it. There are only 12 possible deck compositions: 4 choices for the 12-card suit, then 3 for the 8-card one. For each, you can count how many ways you could have been dealt exactly your hand (the hypergeometric distribution, which describes drawing without replacement). The larger that number, the more plausible the composition. Summing by goal suit gives a probability. With 6 spades in hand, for example, clubs have a 61% chance of being the goal.

I checked on 20,000 deals that these probabilities are honest. When the bot says 30%, the suit is the goal 28% of the time. When it says 50%, 48% of the time. From its hand alone, the suit it rates most likely is right 38% of the time, against 25% by chance.

## How we measure: duplicate deals

In Figgie, the deal weighs a lot. A player dealt 5 goal cards wins almost every time, even playing badly. Comparing two bots on different deals mostly measures their luck.

Duplicate deals fix this, as in tournament bridge. You fix one deal and replay it as many times as there are seats. The bot under test moves through every seat, so it gets each hand in turn, the good ones and the bad ones. Its profits are averaged over these rotations. The luck of the deal cancels out, and what remains is the difference in play. All opponents also face the same deals, which makes comparisons between them fairer.

For each opponent, the tournament plays 1,000 deals, which is 4,000 rounds with 4 players and 5,000 with 5. From those I get the average profit per round and a 95% confidence interval. If the experiment were repeated many times, the interval would contain the true average 95 times out of 100. When it sits entirely above zero, we can say the bot really wins. When it contains zero, we cannot claim anything.

The project has an entry rule. A new bot is accepted only if its interval against the heuristic is entirely above zero. The long-term goal is stricter: a positive profit against every opponent in the zoo, including the worst one.

## Results

Average profit in dollars per round for the row bot, facing copies of the column bot (3 copies with 4 players, 4 with 5). Confidence intervals are in the [`resultats/phase0/`](../resultats/phase0/) folder. Their half-width is under ±$4 everywhere.

### With 4 players

| Candidate \ opponents | random | heuristic | bayesian | aggressive | passive |
|---|---|---|---|---|---|
| random | | -43.2 | -92.0 | +35.7 | -32.2 |
| heuristic | +40.0 | | -27.1 | +57.6 | -5.2 |
| bayesian | +120.7 | +41.4 | | +107.9 | +0.0 |
| aggressive | -35.6 | -54.2 | -95.1 | | -0.2 |
| passive | +29.5 | +4.2 | -6.1 | -13.2 | |

### With 5 players

| Candidate \ opponents | random | heuristic | bayesian | aggressive | passive |
|---|---|---|---|---|---|
| random | | -54.2 | -90.1 | +21.5 | -26.5 |
| heuristic | +47.4 | | -25.5 | +58.7 | +2.4 |
| bayesian | +126.3 | +43.1 | | +104.1 | -0.0 |
| aggressive | -29.7 | -58.3 | -95.5 | | +1.1 |
| passive | +27.6 | -1.9 | -6.5 | -11.5 | |

The bayesian is the strongest bot in the zoo. It passes the entry rule with 4 and 5 players: +$41.4 per round against the heuristic with 4 players, interval [+38.4, +44.3]. It is the reference bot that later phases will have to beat.

It does not meet the final goal, though. Against the passive bot it makes +$0.02 per round, with an interval of [-0.12, +0.17] that contains zero. In practice almost nothing happens: barely 0.2 trades per round between them. The passive bot quotes too wide for the bayesian to come and take it, and it never takes anything itself. With no trades, duplicate deals bring everyone back to zero. Winning against a cautious player will require spotting when its quotes are mispriced and taking them. That is the job of phases 2 and 4.

## What I took away

The bayesian does not win because it guesses better. I measured both on 20,000 deals: the heuristic finds the right goal suit 38.5% of the time, the bayesian 38.1%. The difference is in the pricing. The heuristic is sure of itself, so it sells every card it considers useless at $2, including cards that have a 30% chance of being the goal. The bayesian knows how uncertain it is and does not dump those cards.

The opponents do not rank on a single scale. The aggressive bot loses to the random one (-$35.6 with 4 players), probably because it pays $20 for cards the random bot sells it blindly, which are often the wrong ones. The passive bot beats the heuristic with 4 players (+$4.2) but loses to it with 5 (-$1.9). That is why testing against the whole zoo, with 4 and with 5 players, matters.

A measurement script nearly fooled me. My first comparison gave the heuristic a 45% hit rate. I had created the random generator for its tie-break with the same seed as the deal. Its first draw therefore reproduced the one that picks the 12-card suit, and the heuristic was cheating without knowing it. The engine does not have this flaw: each bot has its own generator, seeded differently from the deal. But it shows that a number that looks too good always deserves a check.

## Limits

All these opponents are bots I wrote myself. Beating them says nothing about the level against humans on figgie.com. These numbers only measure how strong the bots are relative to each other.

The heuristic in this project is a rewrite, simpler than the one in my old code. In the old version, the bayesian lost to the heuristic. Here it wins comfortably, partly because this heuristic dumps its cards. The two results are not comparable, and the entry bar is probably too low. Tougher opponents will need to be added.

Time cut into ticks is unrealistic. On the real site speed matters: the first player to take a mispriced quote gets it. Phase 1 deals with that.

Tables do not mix styles. Each match puts the candidate against copies of a single opponent. A real figgie.com table mixes different players.

When there is a tie, the pot split is not rounded ($33.33 each for $100 split three ways). I do not know yet how figgie.com rounds it.

## Reproduce

The code has changed since. To get exactly the phase 0 code back, first check out its git tag: `git checkout phase0-figgie`.

```bash
cd projets/bot-figgie
python3 -m unittest                      # the 27 tests, under a second
python3 -m figgie.evaluate --candidate bayesien --deals 1000 --seed 1
```

One candidate's tournament against the zoo takes about twenty seconds. The 10 configurations in the tables (5 candidates, with 4 and 5 players) take about 4 minutes on a MacBook. Adding `--logs games.jsonl` saves the log of every round.

## Next

Phase 1 will make the simulator closer to figgie.com: one quote per player and per suit, cash limits, continuous time with latency. The tournament will be replayed under those conditions to see whether the ranking holds.
