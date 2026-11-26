# Phase 5q: a simulated Hard bot whose bids point to the goal

*Version française : [phase5q.fr.md](phase5q.fr.md)*

Phase 5p found a gap in the simulator. On the site, the Hard bots' consensus finds the goal suit at the bell in 91% of the rounds, between our simulated Hard bots in only 67 to 72%. Everything the bot learns in simulation therefore underrates what bids say. This phase looks for a simulated Hard bot that is more faithful on this point, by adding the consensus to the Hard bot's tuning.

Result: it finds none. The best setting brings the consensus closer to the site at the bell (84% instead of 73%), but it moves the rest of the market away, and overall it does worse than the recalibrated Hard bot. Reading the others' offers harder does not help: the Hard bots all start following the first suit where someone bid high, and the consensus falls to about 30%. The recalibrated Hard bot stays the mixed table's filler, and no bot changes. These measurements are made on Rasmus's 60 real rounds and against simulated bots, not on the site.

## The measure

For each suit, the consensus is the lowest of the highest bids the Hard bots have offered since the start of the round. A suit where all of them bid high is probably the goal. The new function `figgie.reel.consensus_hits` gives, at 120, 180 and 239 s, the share of rounds where this consensus ranks the goal first. A tie between k suits counts as 1/k. On simulated tables, it only takes three Hard bots, as in the real rounds.

A single seam, written with TDD: on two hand-written rounds, the measure gives the value computed by hand. The test failed before the code. It catches two deliberate mistakes: also counting Rasmus's bot, and counting a tie as a full hit.

`figgie.calibrate` gets the `--consensus` option. It adds to a setting's error the gap on these three shares, at one unit of error per 5 points, like phase 5j's shares of offers taken. It also allows higher reading strengths `read` (0.6, 0.8 and 1.2), without changing the draws of phases 5c and 5j's commands.

## The search

Same conditions as in phase 5j: 3,000 settings drawn at random, measured on 30 rounds between 4 simulated Hard bots (seed 31), then the best 10 checked again on 90 other rounds (seed 32), shares of offers taken included.

| Measure | figgie.com | recalibrated Hard (5j) | best setting (5q) |
|---|---|---|---|
| trades per round | 53.27 | 31.73 | 46.36 |
| trades per pair of Hard bots | 9.44 | 5.29 | 7.73 |
| share of trades per minute | 0.12 / 0.19 / 0.25 / 0.44 | 0.06 / 0.16 / 0.33 / 0.46 | 0.16 / 0.23 / 0.29 / 0.32 |
| quotes per minute | 37.75 | 58.75 | 49.50 |
| highest bid, goal | $10 | $8 | $6 |
| highest bid, other suits | $5 | $3 | $3 |
| non-goal asks taken at $1-3 | 30% | 25% | 15% |
| goal asks taken at $7-10 | 12% | 12% | 9% |
| consensus ranks the goal first at 120 / 180 / 239 s | 62 / 85 / 91% | 62 / 69 / 73% | 63 / 71 / 84% |
| gap to the site, without the consensus | | 23.5 | 40.4 |
| gap to the site, with the consensus | | 46.7 | 49.5 |

The recalibrated Hard bot's measures are phase 5j's; its consensus shares and its two gaps are measured here, on the same 90 rounds of seed 32.

The search's best setting trades more, like the site, and its consensus rises to 84% at the bell, against 73%. But it does not move at 180 s, it trades less in the last minute, it bids less for the goal, and it takes half as many cheap cards as the site's bots. Overall, with the consensus counted, it is a little further from the site than the recalibrated Hard bot (49.5 against 46.7). The 3,000 draws did not contain the recalibrated Hard bot's setting, found in phase 5j by another search.

## Reading harder is not enough

The simulated Hard bot already reads the market: a suit where the others bid higher becomes more likely to be the goal, with a weight exp(read × (highest bid offered - mean over the suits)). On the recalibrated Hard bot, I tried other reading strengths and other goal values (90 rounds, seed 32):

| read | goal value | consensus at 120 / 180 / 239 s | gap to the site, without the consensus |
|---|---|---|---|
| 0 | $16 | 40 / 47 / 53% | 255.2 |
| **0.2 (recalibrated Hard)** | **$16** | **62 / 69 / 73%** | **23.5** |
| 0.4 | $16 | 43 / 43 / 43% | 166.1 |
| 0.6 | $16 | 29 / 29 / 29% | 167.8 |
| 1.2 | $16 | 30 / 30 / 30% | 169.4 |
| 0.2 | $30 | 51 / 52 / 52% | 328.4 |

All the rows are in `resultats/phase5q/sonde_lecture.txt`.

Without reading, the consensus finds the goal only half the time at the bell. With a reading stronger than 0.2, it freezes: it no longer moves between 120 and 239 s. The Hard bots all follow the first suit where another bot bid high, push it up together, and never let go. In 70% of the rounds, it is not the goal. The site's real bots, on the other hand, get closer to the goal throughout the round. They must take into account something other than the highest bids, which I do not know how to model yet: trades, sales, or what they infer from their own hand.

## Does the bot progress?

No: this phase changes no bot. It confirms that phase 5p's gap comes from the structure of the simulated Hard bot, not from its tuning. I did not carry out steps 4 and 5 of the plan, which assumed a Hard v3. The "buying" v4c remains the reference bot, and the recalibrated Hard bot the mixed table's filler.

## Limits

The search draws 3,000 settings at random in a fixed space; a better setting may have slipped through. But the probe shows that the reading strength, the only setting that acts directly on the consensus, cannot bring it to the site's level.

The real rounds' consensus comes from a single 4-player table, against Rasmus's bot, over 60 rounds.

The simulated Hard bot only reads the highest bids. I tried no other form of reading.

Everything is still measured on paper or against simulated bots. These numbers are not real gains on figgie.com.

## Reproduce

```bash
cd projets/bot-figgie
python3 -m unittest                                                  # the 146 tests, about 7 s
python3 -m figgie.calibrate --settings 3000 --rounds 30 --keep 10 --lift --consensus --out calibration_hard_v3.json
PYTHONPATH=. python3 resultats/phase5q/sonde_lecture.py
```

On 10 cores, the search and the probe each take a few minutes. The outputs are in `resultats/phase5q/`. To get this phase's exact code back: `git checkout phase5q-figgie`.
