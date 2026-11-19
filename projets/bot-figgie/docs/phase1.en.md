# Phase 1: a more faithful simulator

*Version française : [phase1.fr.md](phase1.fr.md)*

Phase 0 played Figgie in turns: on each "tick", every bot acted once, and the order book kept a single quote per suit. The real game does not work like that. Everyone acts at the same time, and the fastest player gets the good deal. This phase brings the simulator closer to figgie.com, then replays the tournament to see whether the ranking holds.

The reference bot has not changed. This phase does not try to improve it: it changes the ground it is measured on.

## What the site says, and what it does not

I reread the figgie.com rules page and FAQ. They confirm the essentials: one card per trade, every quote cancelled after each trade, $350 to start, a $200 pot. You buy by clicking the "buy" button of any offer, "for the displayed amount".

Four points stay unclear, and I could not settle them by playing. So I made a choice for each one, and the simulator lets you change it.

| Question | What the site says | Simulator choice |
|---|---|---|
| Round length | 4 minutes in the rules, 2 minutes in the FAQ | 4 minutes, adjustable. I tested both. |
| How many quotes per suit | The site mentions "any offer" without details | One bid and one offer per player and per suit |
| Opponents' card counts and trade history | Not stated | Visible, as in phase 0 |
| Cancelling your own quote | Not stated | Allowed |

## What changed in the engine

The book now keeps one quote per player. Someone can bid $5 for hearts while someone else bids $4: both bids coexist. When a player sells, they hit the best bid, and at equal prices the oldest one. This is the "price, then time" priority of real exchanges.

Time becomes continuous. A round lasts 240 seconds. Each bot has two settings: its reaction time (the delay between what it sees and its action reaching the market) and how often it looks at the market when nothing moves. As soon as the market changes, everyone sees it, and the race starts. If two bots want the same card offered at $1, the one reacting in 0.1 seconds beats the one reacting in 0.5 seconds. The slower player's action reaches a market that has already changed, and it is refused.

This realism exposed a problem, caught during code review. At first, a "buy" order carried no price. A bot that saw a $17 bid and decided to sell could end up selling at $3, because the book had moved while its order was on its way. Out of 2,592 takes measured, 11 filled at a worse price than the bot had seen. On figgie.com you click a specific quote, so this cannot happen. Now every take carries the price the bot saw, and the market refuses it if that price got worse in the meantime. I had started a first tournament before noticing. I stopped it and ran it again after the fix.

Each round's log also records when the bot looked at the market, on top of when its action arrived. The gap between the two is the latency. It will be useful when the bot learns from its games. The log now carries a format number, so an old phase 0 log is refused with a clear message instead of an obscure error.

## A new opponent: the sniper

Phase 0 had a weakness: the entry rule only required beating the heuristic, a fairly easy opponent. I added the sniper. It has the same estimates as the bayesian, but it never quotes. It waits, and as soon as a quote is mispriced compared to its value, it takes it. With a 0.15-second reaction time, it is the fastest bot in the zoo.

From now on, a candidate must beat both the heuristic and the sniper, with a confidence interval entirely above zero in both cases.

Two settings of the older opponents were also revised. The random bot started looking at the market on every change and ran away with it: over 1,000 actions per round, sometimes ending with $16. It now follows its own pace, calibrated to make about 67 actions per round as in phase 0. The passive bot acts at most once every 5 seconds on average, however busy the table is.

## The tests

The 38 tests run in under a second. The new ones check in particular:

- that two players can each have their own bid in the same suit, and that the best one is served first, then the oldest at equal prices;
- that a take is refused if the quote got worse, and fills at the displayed price if it is better than expected;
- that the fastest player wins the race for a cheap card, and the slower player's action is refused;
- that all actions fall within the round, in order;
- that a zoo bot is never refused for no reason: for every refusal, another player acted between the bot's look and its action's arrival.

## Results

Same method as phase 0: 1,000 duplicate deals per opponent, average profit in dollars per round for the row bot facing copies of the column bot. Confidence intervals are in [`resultats/phase1/`](../resultats/phase1/).

### With 4 players

| Candidate \ opponents | random | heuristic | bayesian | aggressive | passive | sniper |
|---|---|---|---|---|---|---|
| random | | -24.7 | -35.1 | +89.9 | -28.4 | -58.6 |
| heuristic | +16.1 | | -26.0 | +61.2 | -37.5 | -37.9 |
| bayesian | +53.5 | +33.5 | | +105.2 | -0.0 | +4.0 |
| aggressive | -103.6 | -58.4 | -97.2 | | -96.4 | -116.6 |
| passive | +49.4 | +35.2 | -6.0 | +84.3 | | +0.7 |
| sniper | +105.5 | +73.1 | +0.4 | +178.4 | -0.0 | |

### With 5 players

| Candidate \ opponents | random | heuristic | bayesian | aggressive | passive | sniper |
|---|---|---|---|---|---|---|
| random | | -35.0 | -29.2 | +81.0 | -24.1 | -54.2 |
| heuristic | +26.1 | | -24.0 | +59.7 | -29.8 | -37.0 |
| bayesian | +49.2 | +31.3 | | +100.7 | -0.1 | +6.1 |
| aggressive | -105.6 | -58.4 | -96.8 | | -99.7 | -118.4 |
| passive | +42.3 | +29.0 | -6.5 | +81.0 | | +0.1 |
| sniper | +95.9 | +79.2 | +0.4 | +183.0 | -0.1 | |

### The reference bot, phase 0 against phase 1

| Bayesian against | Phase 0, 4 players | Phase 1, 4 players | Phase 1, 5 players |
|---|---|---|---|
| random | +120.7 | +53.5 | +49.2 |
| heuristic | +41.4 | +33.5 [+30.7, +36.3] | +31.3 [+29.2, +33.4] |
| aggressive | +107.9 | +105.2 | +100.7 |
| passive | +0.0 | -0.05 [-0.20, +0.10] | -0.06 [-0.11, -0.01] |
| sniper | | +4.0 [+3.3, +4.6] | +6.1 [+5.5, +6.7] |

The bayesian still passes the entry rule, which is now stricter: it beats the heuristic and the sniper, with 4 and with 5 players. It remains the reference bot.

It did not improve, and that was not the goal of this phase. Its profits drop against the random bot (from +$120.7 to +$53.5) because the random bot can no longer buy anything at any price: its takes carry a limit price, which is often refused. They also drop a little against the heuristic.

The final goal is still out of reach, and the worst case even got slightly worse. Against the passive bot the bayesian still makes nothing, and with 5 players it loses 6 cents per round, with an interval entirely below zero. It is tiny, but it is the first time it clearly loses to an opponent in the zoo.

Two-minute rounds give the same results as 4-minute ones, to the cent, except against the random bot (+$36.5 instead of +$53.5). The next section explains why.

## What I took away

The market dies after 20 seconds. Between the bayesian and three heuristics, half the rounds have finished trading after 21 seconds, out of 240. Against snipers it is 4 seconds. These bots compute their value once at the start and never change it. Once everyone has taken what they wanted, nothing moves. Only the random bot keeps some activity going until the end, which is why round length matters only against it. A real player keeps learning by watching the others: someone buying a lot of clubs probably knows something. That is the topic of phase 3, and it is probably where the biggest gain lies.

Speed turned the ranking upside down. The sniper, which never quotes and only takes, became the second-best bot: +$73.1 against the heuristic, +$178.4 against the aggressive bot. The aggressive bot collapsed, from -$35.6 to -$103.6 against the random bot. It reacts fast and pays up to $20 for cards that are rarely worth that much: in continuous time it jumps on every bad deal before anyone else. The passive bot went the other way. It now beats the heuristic by +$35.2, against +$4.2 in phase 0, because the heuristic and the aggressive bots come and take its wide quotes and pay for its caution.

The bayesian and the sniper each beat the other a little, depending on who is in the minority. Alone against three snipers, the bayesian makes +$4.0. Alone against three bayesians, the sniper makes +$0.4. This is not a contradiction: the two tables are not the same. With three snipers, nobody else quotes, so the bayesian's quotes are the only ones in the market. It sets the prices, which is probably what gives it the edge.

Code review caught two bugs before they reached the results: takes filled at the wrong price, and the random bot's pace, 18% slower than stated. A third one was mine: the random bot running away at 1,000 actions per round, spotted because a +$350 profit per round looked too good. As in phase 0, a number that looked too good deserved a check.

## Limits

All opponents are still bots I wrote. These numbers say nothing about the level against humans.

Reaction times are made up: 0.15 seconds for the sniper, 0.4 for the bayesian, 1 second for the passive bot. I measured neither figgie.com's real latency nor a human player's speed. A human takes roughly a quarter of a second to react to what they see, then has to click. The sniper is probably faster than a human. If the bot ever plays on the real site, its speed will have to stay human, otherwise its wins would come from reflexes, not from its play.

The four unclear rules remain assumptions. If figgie.com keeps only the best quote per suit, or hides opponents' card counts, some results will change.

Tables still do not mix styles: each match puts the candidate against copies of a single opponent.

The full tournament now takes 39 minutes, against 4 in phase 0, because every look by every bot copies the book. That is enough for now, but the engine will need to be faster before the learning phase, which will need hundreds of thousands of rounds.

## Reproduce

```bash
cd projets/bot-figgie
python3 -m unittest                                    # the 38 tests, under a second
python3 -m figgie.evaluate --candidate bayesien --deals 1000 --seed 1
python3 -m figgie.evaluate --candidate bayesien --deals 1000 --seed 1 --duration 120   # 2-minute rounds
```

One candidate against the whole zoo takes 2 to 4 minutes. To get exactly this phase's code back: `git checkout phase1-figgie`.

## Next

Phase 2 replaces the bayesian's fixed bonus with a real calculation of what one more card is worth: $10, plus what it changes to my chances of winning the rest of the pot. It also adds card counting and finer execution. The first target is to beat the passive bot, currently its worst opponent.
