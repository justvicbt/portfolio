# Phase 3: reading the market

*Version française : [phase3.fr.md](phase3.fr.md)*

Until now, the bot drew conclusions from only two sources: its own hand, and the cards that trades reveal in other players' hands. It ignored everything else, in particular how the others quote. A player bidding $12 for a heart probably knows something. This phase learns to read those signals, on simulated games, and gives birth to a new bot, the reader.

It also adds games of several rounds at the same table, as on figgie.com. At the end of each round, the goal suit and everyone's hands are revealed, and the bot can learn whom to trust. This is the first form of learning from one game to the next.

The outcome is mixed, and I report it as it is. The bot guesses the goal suit much better, but that earns few dollars, and the reader fails the entry rule with 5 players. So it is not promoted: the phase 2 marginal bot remains the reference.

## What you see on screen

On figgie.com, every player sees quotes and trades go by. The simulator now keeps that same public feed: every bid or offer posted, every card that changes hands, with its price and the player involved. Bots read it directly from their view.

A first version had the bot rebuild this feed itself, by comparing what it saw from one look to the next. Code review showed the flaw: while the bot's action was on its way, it did not look, and it missed quotes. Yet the model had learned from all quotes. A real player keeps seeing the screen after clicking. The feed kept by the market solves this, and a test checks that at every look the bot sees exactly the start of the feed rebuilt from the log.

## Learning what a quote says

The method is deliberately simple, with no machine-learning library: we count.

We play 4,000 rounds at mixed tables drawn at random from the zoo, with 4 or 5 players. Each event in the feed is filed by type, meaning its nature (bid, offer, buy, sell) and its price range ($1-2, $3-5, $6-9, $10-14, $15 and up). We then count how often each type shows up, per round, in the goal suit, in its twin and in the two other suits. The ratio between these frequencies says how much an event type gives away the goal suit.

During a round, the bot multiplies these ratios for each event it sees and turns them into a probability for each suit. Tests check the calculation on a small hand-written dataset whose answer is known in advance (10/14 for hearts after a $12 bid).

Learning rounds use their own seeds (3), validation measurements other seeds (4). None of them is used for tournaments (seed 1) or for the phase 2 tuning (seed 2).

## Three traps, found by measuring

My old code had already hit this problem: with opponents' quotes, accuracy dropped from 39% to 14%, because the signals drowned everything. I ran into exactly this phenomenon, and found three causes.

First trap, repetition. A player who reposts the same bid ten times does not know ten times more, but a naive model counts ten pieces of evidence. Without care, probabilities became far too sharp. Now each signal counts only once per player and per round (same nature, same suit, same price range).

Second trap, double counting. A trade reveals cards, and phase 2's card counting already uses that. If the model also reads "they bought a club", it counts the same information twice. Code review flagged it. I measured both versions on the validation rounds: reading only quotes, and leaving trades to the card counting, gives better probabilities.

Third trap, the most unexpected one. While checking calibration, I found a flaw that had been there since phase 2. Card counting treated cards bought by others as if they had been drawn at random from the deck. But a player who buys 6 hearts chose them: that does not prove hearts is the 12-card suit. Only my own starting hand is a genuine random draw. Other players' known cards should only rule out impossible decks: a suit cannot have fewer cards than we know of. With the old method, when the bot said 80 to 90%, it was right only 42% of the time. The phase 2 marginal bot keeps this flaw, so it stays a measured reference. The reader uses the corrected version.

## What it changes for guessing the goal

Measured on 1,000 validation rounds, from the point of view of a player who sees only their hand and the public feed. Share of rounds where the suit rated most likely is the right one.

| What the bot uses | 5 s | 15 s | 30 s | 60 s | 120 s | 240 s |
|---|---|---|---|---|---|---|
| Its hand alone | 38-40% | | | | | |
| Phase 2 counting | | | | 42% | | |
| Corrected counting | 39.4% | 43.1% | 44.9% | 47.2% | 48.3% | 49.6% |
| Corrected counting + quotes | 49.2% | 51.6% | 51.3% | 52.4% | 55.1% | 56.8% |

By chance it would be 25%. Reading quotes delivers most of its value in the first 5 seconds: that is when everyone posts their first prices, which reflect their hand.

The probabilities have also become honest. At 60 seconds, when the reader says 20 to 30%, the suit is the goal 26% of the time. At 50-60%, it is 59%. At 70-80%, 84%. The chosen model reads only quotes, with no tempering: once repetition and double counting were removed, there was no overconfidence left to correct.

## Games of several rounds

The engine can now play a game of N rounds at the same table. Each bot has a memory that survives from one round to the next. At the end of each round it learns the goal suit and sees everyone's hands, as on the site. Duplicate deals still work: the whole game is replayed at each seat rotation. The first round of a game uses the same deal as a single round with the same seed. Later rounds use seeds that cannot collide with any seed from the other experiments.

The reader uses this to judge its opponents. At the end of a round, it checks whether each player's signals pointed to the real goal suit better than chance. A player quoting at random sees their trust go down, a reliable player sees it go up. On synthetic players, after 20 rounds, a reliable player gets a weight of 1.33 and a random player 0.18.

## The tests

The 74 tests run in one second. The new ones cover:

- the event feed, which must be identical live and rebuilt from the log;
- the signal model: hand-computed ratios, a repeated quote counting once, my own events ignored, reading limited to quotes;
- corrected counting: bought cards ruling out impossible decks without weighing like a draw;
- games of several rounds: memory, hands revealed, money conserved, a bot against itself always at zero;
- the opponent model, on synthetic players.

## Results

Same method as earlier phases: 1,000 duplicate deals per opponent, on seed 1, single rounds. Average profit in dollars per round for the row bot facing copies of the column bot. The full tournament took 1 h 52 on 10 cores.

### With 4 players

| Candidate \ opponents | random | heuristic | bayesian | aggressive | passive | sniper | marginal | reader |
|---|---|---|---|---|---|---|---|---|
| random | | -24.7 | -35.1 | +89.9 | -28.4 | -58.6 | -80.0 | -67.8 |
| heuristic | +16.1 | | -26.0 | +61.2 | -37.5 | -37.9 | -27.1 | -22.4 |
| bayesian | +53.5 | +33.5 | | +105.2 | -0.0 | +4.0 | +1.4 | -0.9 |
| aggressive | -103.6 | -58.4 | -97.2 | | -96.4 | -116.6 | -81.0 | -66.4 |
| passive | +49.4 | +35.2 | -6.0 | +84.3 | | +0.7 | -6.6 | -4.6 |
| sniper | +105.5 | +73.1 | +0.4 | +178.4 | -0.0 | | -1.0 | -2.0 |
| marginal | +83.2 | +42.1 | +20.6 | +87.3 | +15.2 | +15.5 | | -0.5 |
| reader | +70.9 | +44.9 | +29.8 | +88.2 | +19.8 | +15.5 | +2.7 | |

### With 5 players

| Candidate \ opponents | random | heuristic | bayesian | aggressive | passive | sniper | marginal | reader |
|---|---|---|---|---|---|---|---|---|
| random | | -35.0 | -29.2 | +81.0 | -24.1 | -54.2 | -80.2 | -49.7 |
| heuristic | +26.1 | | -24.0 | +59.7 | -29.8 | -37.0 | -27.1 | -20.0 |
| bayesian | +49.2 | +31.3 | | +100.7 | -0.1 | +6.1 | +0.2 | +2.9 |
| aggressive | -105.6 | -58.4 | -96.8 | | -99.7 | -118.4 | -86.8 | -57.8 |
| passive | +42.3 | +29.0 | -6.5 | +81.0 | | +0.1 | -4.2 | +0.7 |
| sniper | +95.9 | +79.2 | +0.4 | +183.0 | -0.1 | | -1.0 | -1.1 |
| marginal | +82.0 | +43.0 | +21.7 | +81.7 | +13.7 | +17.3 | | +7.3 |
| reader | +66.5 | +47.3 | +34.6 | +82.0 | +18.7 | +15.0 | +0.7 | |

The cells between the older bots are identical to phase 2. I also checked, deal by deal, that the marginal bot plays exactly like the code at the `phase2-figgie` tag.

### The reference, phase 2 against phase 3

| Against | Marginal (4 p.) | Reader (4 p.) | Marginal (5 p.) | Reader (5 p.) |
|---|---|---|---|---|
| random | +83.2 | +70.9 | +82.0 | +66.5 |
| heuristic | +42.1 | +44.9 | +43.0 | +47.3 |
| bayesian | +20.6 | +29.8 | +21.7 | +34.6 |
| aggressive | +87.3 | +88.2 | +81.7 | +82.0 |
| passive | +15.2 | +19.8 [+18.5, +21.2] | +13.7 | +18.7 [+17.6, +19.8] |
| sniper | +15.5 | +15.5 | +17.3 | +15.0 |
| marginal | | +2.7 [+1.8, +3.7] | | +0.7 [-0.3, +1.7] |

With 4 players, the reader passes the entry rule, which now requires beating the heuristic, the sniper, the bayesian and the marginal bot. It wins against the whole zoo, and its worst case is the marginal bot, at +$2.7 per round.

With 5 players, it fails. Against the marginal bot it makes only +$0.7, and the interval contains zero. Worse, the table flips when readers are numerous: a single marginal bot facing four readers makes +$7.3 per round ([+6.0, +8.7]), and a single bayesian facing four readers +$2.9.

So the reader is not promoted. The marginal bot remains the reference. The reader joins the zoo as an opponent.

### Where the gains come from: the corrected marginal bot

To separate the reader's two improvements, I measured a third bot: the marginal bot with the corrected counting only, without market reading. Against the original marginal bot it makes +$0.5 with 4 players and -$0.3 with 5, both with intervals that contain zero. Corrected counting guesses the goal suit much better but earns almost nothing on its own. So the reader's small gain with 4 players comes mostly from reading quotes.

### Memory

The most important experiment for the project's goal compares two readers over games of 10 rounds. The table is mixed: a random bot, a heuristic bot, a marginal bot. The first reader keeps its memory of opponents from one round to the next, the second forgets everything each round. 200 games, with duplicate deals.

| Round | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| With memory | +41.6 | +40.2 | +41.2 | +40.9 | +40.7 | +35.9 | +44.9 | +41.3 | +40.0 | +39.5 |
| Without memory | +41.6 | +39.5 | +37.4 | +40.3 | +42.5 | +34.9 | +41.8 | +39.6 | +41.1 | +39.3 |
| Gap | 0.0 | +0.7 | +3.8 | +0.6 | -1.8 | +1.0 | +3.1 | +1.7 | -1.2 | +0.3 |

In the first round both versions get exactly the same result, since neither has learned anything yet. After that, the average gap over rounds 2 to 10 is +$0.92 per round, with an interval of [-0.33, +2.18] that contains zero. The reader does learn to judge its opponents: at the end of a game it gives 0.62 trust to the random bot, against 0.96 to the heuristic and 0.91 to the marginal bot. But that does not translate into dollars in any measurable way.

## What I took away

Guessing better is not enough to win more. The reader finds the goal suit 52% of the time at one minute, against 42% for the marginal bot, and that earns only $2.7 per round with 4 players. The reason is probably the one from phase 2: the marginal bot wins mainly by taking other players' mistakes in the first seconds, and the market still dies around 16 seconds. Better information arrives when there is almost nothing left to trade.

Readers get in each other's way. When they are the majority at the table, they read each other's signals, and those signals come from bots that themselves read the market. The model learned at tables where nobody read the market. At a table of readers, what it learned no longer matches what it sees. A marginal bot that ignores all of this takes advantage. That is exactly the problem a self-play league, in phase 4, has to handle: relearning the model on games where the reader plays against itself.

Learning whom to trust works, but earns little here. In the zoo, almost every opponent's signals are useful, and even the random bot is probably not that misleading: it can only offer to sell cards it holds, which reveals a bit of its hand. Memory will matter more against misleading opponents, and those will arrive in phase 4.

Measuring calibration paid off more than anything else. Without the table "when the bot says 80%, is it right 80% of the time?", I would never have found the counting flaw that had been there since phase 2.

## Limits

All opponents are bots I wrote, and the signal model learned on them. Against humans, who quote differently, the learned ratios would be wrong. They will have to be relearned on real games if phase 5 allows it.

The model treats events as independent, which they are not: a player who bids $10 then $12 for a heart is following the same idea. Deduplication limits this problem without removing it.

The reader uses the $8 spread tuned for the marginal bot. I did not retune it, and a different setting could change the 5-player verdict.

Games of several rounds start again from $350 every round, whereas on figgie.com money accumulates.

The limits of earlier phases still hold: made-up reaction times, four assumed site rules.

## Reproduce

```bash
cd projets/bot-figgie
python3 -m unittest                                         # the 74 tests, one second
python3 -m figgie.learn --train 4000 --valid 1000           # learn the model, about 30 s on 10 cores
python3 -m figgie.memoire --deals 200 --rounds 10           # the memory experiment, about 5 minutes
python3 -m figgie.evaluate --candidate lecteur --deals 1000 --seed 1
```

The learned model is saved in `modeles/signaux.json`. To get exactly this phase's code back: `git checkout phase3-figgie`.

## Next

Phase 4 has to deal with what phase 3 revealed: bots that get exploited when they are numerous at the table. It will make the bot play against its own versions and against opponents trained to beat it, and relearn the signal model on those games.
