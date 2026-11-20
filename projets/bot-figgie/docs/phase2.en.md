# Phase 2: what a card is really worth

*Version française : [phase2.fr.md](phase2.fr.md)*

Until now, the bayesian bot valued a card at "probability of being the goal × $15". The $15 was the $10 per-card bonus plus a fixed $5 meant to stand for the majority of the pot. That fixed bonus was a rough approximation. A goal card can change nothing about the majority, or it can tip it and be worth $100 at once. This phase replaces the bonus with a real calculation, and gives birth to a new bot: the marginal bot.

Its first target was to beat the passive bot, which nobody had managed to beat in phases 0 and 1. It does, and it also beats every other opponent in the zoo.

## A card's value depends on who is on the other side

Take an example with 10 goal cards in the deck, so $100 of the pot left for the majority. I hold 3 goal cards, one opponent also holds 3, the other two hold 2. We share the majority: I get $30 plus half of $100, so $80.

If I buy a card from the other leader, I go to 4 and they drop to 2. I am alone at the top: $40 plus $100, so $140. That card is worth $60 to me, six times the $10 bonus.

The other side matters too. If I hold 4 cards and the leading opponent holds 3, I get $140. If I sell a card to a player who holds only one, I drop to 3 and they rise to 2: I am still tied with the leader and get $80. That costs me $60. If I sell it to the leader, they go to 4 and I drop to 3: they take the majority from me and I get only $30. That costs me $110. The same card, at the same moment, is worth different amounts depending on the buyer.

Code review caught this point. The first version of the bot assumed the others stayed put, when the card that changes hands necessarily leaves someone or joins someone. I fixed it before running any tournament.

## Monte Carlo: imagining thousands of possible tables

This calculation would require knowing the opponents' hands. We do not know them, but we can imagine some. The bot draws 300 possible versions of the table at random, consistent with everything it knows, computes in each one what a card would gain or cost it, then takes the average. This is the Monte Carlo method, named after the casino: replace an impossible calculation with many random draws.

For an imagined table to be consistent with what the bot knows, three things must hold:

- the deck composition (which suit has 12 cards, which has 8) is drawn according to its probability, computed from the known cards;
- each opponent has exactly their number of cards, which is public;
- each opponent has at least the cards we know they hold.

That last point is card counting. Every trade is public. If a player buys two hearts, they hold at least two. If they then sell a heart, they still hold at least one. If they sell a heart when we knew of none, that card came from their deal, and we still know nothing. These minimums are used both to draw the tables and to sharpen the probability of each goal suit: if an opponent has bought 4 clubs, clubs are probably numerous, and spades, their twin, become more likely as the goal.

The calculation is redone whenever the bot's hand or the list of trades changes.

## Quoting without knowing who will take it

When the bot takes another player's quote, it knows who is on the other side and uses the exact value for that player. When it posts its own quote, it does not know who will take it. So it stays cautious. It bids at the value of a card coming from the worst possible seller, and offers at the cost of a card going to the worst possible buyer, in practice the one who could take the majority from it.

## Tuning, without cheating

Two parameters remain: the gap between the value and the posted quote (the spread), and the minimum edge needed to take a quote. Tuning them on the tournament deals would mean choosing the combination that got lucky on those deals. So I tuned on a different set of deals (seed 2, 150 deals per opponent), and ran the final tournament on the usual deals (seed 1), which the tuning never saw.

The selection criterion is the project's goal: the chosen combination is the one whose worst result against every opponent in the zoo is the best. For the worst result I use the lower bound of the confidence interval, not the mean. The runs go in parallel on the Mac's 10 cores, about 4 minutes for 15 combinations.

| Spread (edge $1) | $1 | $3 | $5 | $6 | $8 | $10 | $15 | $20 | $100 |
|---|---|---|---|---|---|---|---|---|---|
| Worst lower bound ($/round) | +1.5 | +4.4 | +6.4 | +6.9 | +9.3 | +9.3 | +3.1 | +0.3 | 0.0 |
| Worst opponent | passive | passive | passive | passive | passive | sniper | sniper | sniper | sniper |

Edges of $0 and $2 were tested for each spread from $1 to $5, and $1 was always the best or close to it. Full tables are in [`resultats/phase2/`](../resultats/phase2/).

The best setting is far from what I first imagined. Quoting close to your value, with a $1 or $2 spread, gets exploited by fast opponents: the sniper takes quotes as soon as they are slightly mispriced. Never quoting ($100 spread) earns nothing against players who do not quote either, like the sniper: nobody trades. The peak is in between, around $8 to $10. The bot posts cautious prices and wins mainly by taking other players' mistakes. I chose $8: the two settings are equal, but at $10 the worst opponent becomes the sniper, and that is the result that collapses as soon as the spread widens further.

## The tests

The 50 tests run in under a second. The new ones cover:

- the gain from one card, on hand-computed cases: breaking a tie, catching up with the leader, selling to the leader or to another player, the 8-goal-card case;
- card counting, on a hand-written sequence of trades;
- randomly drawn tables: they respect card counts, known minimums and the deck composition;
- the probability with no trades, which matches the phase 0 value (60.9% for clubs with 6 spades in hand), and moves the right way when an opponent reveals cards;
- the fast version of the calculation, compared on 4,000 tables with a slow, readable version.

The fast version came from profiling. At first, the marginal bot was 6 times slower than the others, and almost all the time went into dealing the unknown cards. But the calculation needs only one thing: how many goal cards each opponent gets. So the fast version places only those 8 or 10 cards instead of dealing the whole table.

## Results

Same method as earlier phases: 1,000 duplicate deals per opponent, on seed 1. Average profit in dollars per round for the row bot facing copies of the column bot.

### With 4 players

| Candidate \ opponents | random | heuristic | bayesian | aggressive | passive | sniper | marginal |
|---|---|---|---|---|---|---|---|
| random | | -24.7 | -35.1 | +89.9 | -28.4 | -58.6 | -80.0 |
| heuristic | +16.1 | | -26.0 | +61.2 | -37.5 | -37.9 | -27.1 |
| bayesian | +53.5 | +33.5 | | +105.2 | -0.0 | +4.0 | +1.4 |
| aggressive | -103.6 | -58.4 | -97.2 | | -96.4 | -116.6 | -81.0 |
| passive | +49.4 | +35.2 | -6.0 | +84.3 | | +0.7 | -6.6 |
| sniper | +105.5 | +73.1 | +0.4 | +178.4 | -0.0 | | -1.0 |
| marginal | +83.2 | +42.1 | +20.6 | +87.3 | +15.2 | +15.5 | |

### With 5 players

| Candidate \ opponents | random | heuristic | bayesian | aggressive | passive | sniper | marginal |
|---|---|---|---|---|---|---|---|
| random | | -35.0 | -29.2 | +81.0 | -24.1 | -54.2 | -80.2 |
| heuristic | +26.1 | | -24.0 | +59.7 | -29.8 | -37.0 | -27.1 |
| bayesian | +49.2 | +31.3 | | +100.7 | -0.1 | +6.1 | +0.2 |
| aggressive | -105.6 | -58.4 | -96.8 | | -99.7 | -118.4 | -86.8 |
| passive | +42.3 | +29.0 | -6.5 | +81.0 | | +0.1 | -4.2 |
| sniper | +95.9 | +79.2 | +0.4 | +183.0 | -0.1 | | -1.0 |
| marginal | +82.0 | +43.0 | +21.7 | +81.7 | +13.7 | +17.3 | |

The cells between the older bots are identical to phase 1, to the cent. Their code has not changed, and the deals are the same.

### The reference, phase 1 against phase 2

| Against | Bayesian, phase 1 (4 p.) | Marginal, phase 2 (4 p.) | Marginal, phase 2 (5 p.) |
|---|---|---|---|
| random | +53.5 | +83.2 [+81.4, +85.0] | +82.0 [+80.4, +83.7] |
| heuristic | +33.5 | +42.1 [+39.4, +44.9] | +43.0 [+40.8, +45.2] |
| bayesian | | +20.6 [+18.6, +22.6] | +21.7 [+19.5, +23.9] |
| aggressive | +105.2 | +87.3 [+84.2, +90.4] | +81.7 [+79.4, +84.0] |
| passive | -0.05 | +15.2 [+14.0, +16.5] | +13.7 [+12.6, +14.9] |
| sniper | +4.0 | +15.5 [+14.3, +16.8] | +17.3 [+16.2, +18.4] |

The bot clearly improves. The marginal bot passes the entry rule, which now requires beating the heuristic, the sniper and the bayesian. It even beats the bayesian by +$20.6 per round. It becomes the new reference bot.

For the first time, the project's goal is met on the zoo: a positive profit against every opponent, with a confidence interval that excludes zero, with 4 and with 5 players. Its worst opponent is the passive bot, against which it makes +$15.2 per round with 4 players, where the bayesian made nothing.

The only step back is against the aggressive bot (from +$105.2 to +$87.3). That is the price of caution: with quotes $8 away from its value, the marginal bot lets through some of the cards the aggressive bot overpays for.

## What I took away

The marginal bot wins mainly by taking. Against the passive bot it makes only 2.3 trades per round, and earns $15 from them. It waits until the passive bot posts a quote that is mispriced for it, often because one specific card would win it the majority, and takes it. The tuning confirms this: the winning combination quotes far away and takes as soon as the edge exceeds $1.

Position at the table matters. Alone against three bayesians, the marginal bot makes +$20.6. But a bayesian alone against three marginal bots also wins a little, +$1.35, with an interval of [+0.34, +2.36] that excludes zero. When marginal bots are the majority, they all quote far away and compete for the same mistakes, and a bayesian quoting closer takes advantage. The entry rule only tests one candidate against three copies of the same opponent, so it misses this case. The phase 4 league, where the bot will play against its own versions, will have to deal with it.

Recomputing values after each trade does not revive the market. Between the marginal bot and three heuristics, trading stops around 17 seconds in the median. The bot recomputes what a card is worth from the known cards, but it does not yet draw any conclusion from how the others quote. A player bidding $15 for a club probably knows something. That is the topic of phase 3.

Code review paid off again. The flaw about the other side of the trade was a real gap in reasoning, not a typo, and the bot would have paid for it by selling cards to the leader.

## Limits

All opponents are bots I wrote. The tuning used different deals from the tournament, but the same opponents. So the bot is probably somewhat fitted to this particular zoo, and nothing says an $8 spread would suit play against humans. Phase 4 will train opponents whose only goal is to beat it, which will be a harder test.

The value calculation keeps two simplifications. When an opponent holds no goal card in an imagined table, that table is discarded for buying, but for the other suits the bot assumes any opponent can sell to it. And a posted quote reveals that its author holds at least one card of that suit, which the card counting does not use yet.

With 300 draws per calculation, the value varies from one calculation to the next: its standard deviation is $0.85 in the median and goes up to $2.50 in the most uncertain cases (measured on 30 deals). That is enough for an $8 spread, but not for quoting tight.

The limits of earlier phases still hold: made-up reaction times, four assumed site rules, tables without mixed styles.

## Reproduce

```bash
cd projets/bot-figgie
python3 -m unittest                                         # the 50 tests, under a second
python3 -m figgie.tune --deals 150                          # the tuning, about 4 minutes on 10 cores
python3 -m figgie.evaluate --candidate marginal --deals 1000 --seed 1
```

The full phase 2 tournament (7 candidates, with 4 and 5 players) takes 34 minutes when the 14 configurations run in parallel. To get exactly this phase's code back: `git checkout phase2-figgie`.

## Next

Phase 3 learns to read the market: drawing conclusions from other players' quotes and trades, with a likelihood learned from simulated games instead of being set by hand. It will also spot, as the game goes on, which opponents quote according to their beliefs and which quote at random.
