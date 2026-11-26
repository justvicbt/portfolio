# Phase 5p: what the bot believes about the others

*Version française : [phase5p.fr.md](phase5p.fr.md)*

This phase holds only measurements. I wanted to know whether the "buying" v4c, the reference bot since phase 5n, lets slip the card that breaks a majority tie, an idea from Rasmus Suonio's v5. It does let it slip, but not because of how it computes its value, which already counts that gain. It lacks information: which suit is the goal, and how many goal cards its rivals hold. I then tried to read the suit better late in the round, and stopped as the plan foresaw: the new reading did no better on the real rounds. The cause lies in the simulator. The bids of our simulated Hard bots point to the goal far less often than those of the site's real bots.

No bot changes, no tournament is played. Every measurement is made against simulated bots or on Rasmus's 60 real rounds, not on the site.

## Gathering cards

With 4 players, if the goal has 10 cards and two players hold 5 each, they split the rest of the pot. A sixth card gives the whole pot to whoever holds it: it is then worth far more than $10. Rasmus made it a rule of his bot.

I had the "buying" v4c play against recalibrated Hard bots, over 200 games of 10 rounds at each table size (seed 9, site rule, the bot at a different seat depending on the deal). At the end of the round, I classify its position in the goal suit against the best rival:

| Final position | 4 p.: share of rounds | mean gain | 5 p.: share of rounds | mean gain |
|---|---|---|---|---|
| alone in the lead | 37.8% | +$90.27 | 27.9% | +$100.21 |
| tied | 13.4% | +$33.70 | 9.4% | +$44.75 |
| one card behind | 1.1% | -$18.62 | 1.1% | -$12.38 |
| further behind | 47.8% | -$38.93 | 61.7% | -$26.75 |

The bot rarely ends one card short. When it does not win the majority, it has almost no goal card left: 0.23 on average with 4 players, 0.09 with 5. It sold them. Ties, on the other hand, are frequent, mostly when the goal has 10 cards: 17.8% of those rounds with 4 players, 11.9% with 5. That is exactly Rasmus's case.

In a round that ends tied, one more goal card would have brought it about $61, had nothing else changed. And in every one of those rounds, another player showed a sell offer on the goal after 120 s, cheaper than that gain. With 4 players, the cheapest was $16.41 on average, while the bot's best bid on the goal was $10.73. With 5 players, $17.15 against $9.84.

The possible gain is at most about $6 per round with 4 players and $4 with 5. It is an upper bound: I compute it knowing how the round ends, and the rivals would react if the bot bought.

## Why it does not pay for that card

In principle, the bot's value counts that gain: for each world drawn at random, it computes the exact gain of one more card, ties included. So I recomputed that value at the moment of each sell offer on the goal seen after 120 s, in the rounds that ended tied (100 games at each size). I compare four values of the same card, at the same moment:
- A, the bot's;
- B, the same without phase 5n's time weight;
- C, B with the goal known: only the rivals' hands stay hidden;
- D, the exact gain, everyone's hands known, if nothing else is traded.

For the offers cheaper than D:

| | 4 p. | 5 p. |
|---|---|---|
| offers | 2,501 | 2,126 |
| mean price | $27.60 | $27.25 |
| A, the bot | $10.26 | $10.87 |
| B, without the time weight | $10.93 | $11.62 |
| C, goal known | $20.98 | $18.39 |
| D, everything known | $60.46 | $61.59 |
| share of offers it would take with A | 1% | 1% |
| with C | 25% | 14% |

An offer counts here each time the best sell offer on the goal changes, so one round gives several.

The time weight has almost nothing to do with it: it removes less than a dollar. Not knowing which suit is the goal halves the value. The rest comes from the hidden hands: even knowing the goal, the bot does not see that a rival is tied with it, and it values the card at a third of its worth. Gathering is already in the computation. What is missing is the information it relies on.

## What it believes about the others

I recorded what the bot believes at 120, 180 and 225 s, over 100 games at each size, and compared it with the truth. At 225 s, in the rounds that ended tied:

| | 4 p. | 5 p. |
|---|---|---|
| probability given to the true goal suit | 0.73 | 0.79 |
| share of rounds where it ranks it first | 80% | 78% |
| goal cards of the leading rival: true | 4.49 | 4.30 |
| expected by the bot | 3.02 | 2.92 |
| of which cards it knows (purchases and offered sales) | 1.89 | 1.95 |

The bot places the cards it does not see at random in the rivals' hands. On average over the rivals, that is right, since the total is known. But the leading rival was often dealt many goal cards, and nothing in the computation shows it. The bot thinks it has 3 cards when it has 4 or 5.

To estimate these hands better, one would have to read what a rival's offers say about its deal. Rasmus's logs do not give the hands of the site's bots: such a model could only be checked against our simulated Hard bots, at the risk of learning their quirks. The goal suit, on the other hand, can be checked on the real rounds. So I started there.

## Do the site's bots cancel their offers?

This was the last check from the phase 5m audit. In the 60 real rounds, the three Hard bots cancel 233 offers, in 40 rounds out of 60. That is 0.86% of their 27,009 quotes. They almost always cancel one side (227 times, against 3 times both at once), more often a bid (146) than an ask (87), and late: half of them after 204 s.

Our recalibrated Hard bots cancel about as many, 220 over 60 simulated rounds, but always both sides at once. They also quote about 1.5 times more (41,229 quotes). I did not change them: they fill the entry rule's mixed table, they are tuned on these logs, and changing them would move every measurement.

## Reading the suit late in the round

The consensus is one of Rasmus's ideas, already in our market reading since phase 5d: for each suit, the lowest of the highest bids offered by the other players. Taken alone, with no model, it often points to the goal better than our full reading:

| Suit ranked first | 180 s | 225 s | 239 s |
|---|---|---|---|
| real rounds, our reading | 77% | 85% | 85% |
| real rounds, raw consensus | 85% | 89% | 91% |
| simulated rounds, our reading | 68% | 71% | 72% |
| simulated rounds, raw consensus | 62% | 66% | 67% |

The simulated rounds are 1,000 rounds of the "buying" v4c against recalibrated Hard bots, with 4 or 5 players (seed 53).

Our reading has a single damping, 0.2, for the whole round. My hypothesis was that it damps late offers too much. I wrote a prototype, outside the repository, with one damping per one-minute window. It gives back today's numbers exactly with 0.2 everywhere. The stopping rule was set in the plan: if the new reading does no better on the real rounds from 180 s on, I stop there.

Chosen one window after another, at the best log-score on phase 5d's 1,000 simulated validation rounds, the dampings are 0.5 for the first minute and 0.2 for the other three. The end of the round does not change. On the real rounds, the reading does a little worse:

| Real rounds: probability of the true suit, share ranked first, log loss | 180 s | 225 s | 239 s |
|---|---|---|---|
| today (0.2 everywhere) | 0.63; 77%; 0.610 | 0.78; 85%; 0.406 | 0.81; 85%; 0.360 |
| per window (0.5; 0.2; 0.2; 0.2) | 0.62; 78%; 0.645 | 0.77; 82%; 0.436 | 0.80; 83%; 0.387 |

So I stopped there, without coding anything in the repository.

The first table explains the failure. On the site, the consensus finds the goal at the bell in 91% of the rounds. Between our simulated Hard bots, in only 67%. Our Hard bots' bids say much less about the goal than the real bots' bids. A setting chosen in simulation cannot learn to trust them more, since in the simulation they do not deserve it.

## Does the bot progress?

No: this phase does not change the bot. It explains why the bot lets slip the card that breaks a tie, and it shows a gap in the simulator that affects everything I learn in simulation. The "buying" v4c remains the reference bot.

## Limits

The gain from gathering, at most $6 per round with 4 players and $4 with 5, is computed knowing how the round ends. The real gain would be smaller.

The diagnostics put the bot against simulated Hard bots only, and the last section shows that their offers differ from the site's.

The 60 real rounds come from a single 4-player table, against Rasmus's bot. They say nothing about 5-player tables.

The prototype tried only one kind of change, a damping per window, with seven values per window.

Everything is still measured against simulated bots or on paper. These numbers are not real gains on figgie.com.

## Reproduce

```bash
cd projets/bot-figgie
python3 -m unittest                                                  # the 145 tests, about 7 s
PYTHONPATH=. python3 resultats/phase5p/regroupement.py 200
PYTHONPATH=. python3 resultats/phase5p/valeur.py 100
PYTHONPATH=. python3 resultats/phase5p/croyances.py 100
PYTHONPATH=. python3 resultats/phase5p/retraits.py
PYTHONPATH=. python3 resultats/phase5p/mesure_lecture.py 1000
PYTHONPATH=. python3 resultats/phase5p/attenuation.py 1000
```

The scripts and their outputs are in `resultats/phase5p/`. On 10 cores, each takes a few minutes at most. To get this phase's exact code back: `git checkout phase5p-figgie`.
