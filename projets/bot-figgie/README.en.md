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
| 5e. Two questions from 5d | Estimated majority in the replay of the real rounds, then a v4b also trained on tables where nobody quotes | [FR](docs/phase5e.fr.md) · [EN](docs/phase5e.en.md) | Done (no bot promoted) |
| 5f. The minority test | Why the exploiter wins against the copies, then a v4c trained on tables where each setting is judged by the mean gain of the copies | [FR](docs/phase5f.fr.md) · [EN](docs/phase5f.en.md) | Done (no bot promoted) |
| 5g. Copies that play together | Making every copy play the same setting, six new references from a paper and four repositories, staying quiet in the first minute, and a bootstrap check of the intervals | [FR](docs/phase5g.fr.md) · [EN](docs/phase5g.en.md) | Done (no bot promoted) |
| 5h. Describing the table over several rounds | A v4d that averages the profiles of past rounds before asking its neighbours, and references that beat the displayed offer | [FR](docs/phase5h.fr.md) · [EN](docs/phase5h.en.md) | Done (no bot promoted) |
| 5i. What the minority test measures | Where the exploiter's gain against the copies comes from, then a mixed table with simulated Hard bots that replaces the minority test in the entry rule | [FR](docs/phase5i.fr.md) · [EN](docs/phase5i.en.md) | Done (no bot promoted) |
| 5j. A simulated Hard bot that no longer overpays | How sell offers end on the real rounds, a simulated Hard bot recalibrated on the share of offers taken, and the entry rule replayed with it | [FR](docs/phase5j.fr.md) · [EN](docs/phase5j.en.md) | Done (no bot promoted) |
| 5k. Buying nothing in the first minute | What the v4c buys in the first minute and why it overpays, then a v4c that sells but buys nothing for 60 s | [FR](docs/phase5k.fr.md) · [EN](docs/phase5k.en.md) | Done (no bot promoted) |
| 5l. A value that accounts for time | The majority share counted less early in the round, with a weight that rises until 2 minutes, and the settings retrained | [FR](docs/phase5l.fr.md) · [EN](docs/phase5l.en.md) | Done (no bot promoted) |
| 5m. Three flaws fixed | One-sided cancels, the marginal bot's buy value, a table profile that follows the site rule, and the v4c retrained | [FR](docs/phase5m.fr.md) · [EN](docs/phase5m.en.md) | Done (no bot promoted) |
| 5n. The majority weight on the buying side only | The majority counted in full when selling, a weight min(1, t / 240) ^ 0.5 when buying, and a full 300-deal tournament | [FR](docs/phase5n.fr.md) · [EN](docs/phase5n.en.md) | Done (v4c_achat promoted) |
| 5o. Searching for an exploiter | The automatic exploiter search run again against the "buying" v4c, on the site's market and at the mixed table, with 4 and 5 players | [FR](docs/phase5o.fr.md) · [EN](docs/phase5o.en.md) | Done (promotion kept) |
| 5p. What the bot believes about the others | The card that breaks a tie, what the bot believes about the rivals' hands and the goal suit, the site bots' cancels, and a late-round reading stopped because it did no better on the real rounds | [FR](docs/phase5p.fr.md) · [EN](docs/phase5p.en.md) | Done (diagnostics, no bot changed) |
| 5q. A simulated Hard bot whose bids point to the goal | The Hard bots' consensus measured on the real rounds and added to the simulated Hard bot's tuning, and what a stronger reading changes | [FR](docs/phase5q.fr.md) · [EN](docs/phase5q.en.md) | Done (no Hard bot kept) |
| 5r. A simulated Hard bot with a private hint | What the site's bots react to, a Hard v3 that receives a hint about the goal that grows surer, its tuning, and the reduced tournament with it at the mixed table | [FR](docs/phase5r.fr.md) · [EN](docs/phase5r.en.md) | Done (Hard v3 is the mixed table's filler) |
| 5s. Learning the site reading again with the Hard v3 | Where the gains against the Hard v3 come from, the signal model learned again on its tables, a criterion set on the real rounds, and the reduced and full tournaments | [FR](docs/phase5s.fr.md) · [EN](docs/phase5s.en.md) | Done (v4c_achat_v3 promoted) |
| 6. Real site | Only with Jane Street's written consent, otherwise a training and analysis tool | | Upcoming |

figgie.com publishes no terms of use and says nothing about bots. I will not automate any ranked game without written consent from Jane Street.

## Results

After phase 2, the new "marginal" bot beats every opponent in the zoo, with a 95% confidence interval entirely above zero, with 4 and with 5 players. Its worst opponent is the passive bot, which nobody had beaten so far: +$15.2 per round with 4 players ([+14.0, +16.5]). It also beats the previous reference bot, the bayesian, by +$20.6 per round.

In phase 3, the "reader" bot, which also reads other players' quotes, guesses the goal suit much better (52% at one minute, against 42%). But it wins only a little more than the marginal bot with 4 players (+$2.7 per round) and does not clearly beat it with 5. So it is not promoted: the marginal bot remains the reference.

In phase 4, an automatic search found opponents that beat the marginal bot when it is in the minority (+$4.35 per round alone against three marginal bots, +$7.22 against four). No candidate passes the full entry rule, minority test included. With fixed settings, every bot has its counter-strategy.

In phase 5, the "adaptive" bot chooses its spread and edge depending on the table it recognizes. It beats the marginal bot head to head (+$2.00 per round with 4 players, +$3.47 with 5), and the phase 4 exploiter now takes only $1.54 per round from it instead of $4.32. But a sniper alone against its copies makes +$3.72 per round: it fails the minority test and is not promoted.

In phase 5b, v3 of the adaptive bot trains against its own copies. It beats the marginal bot by +$8.48 per round with 4 players, and the sniper and the phase 5 taker lose again against its copies. But a "tight quoter" found by the automatic search takes +$6.25 per round from it, and the phase 4 exploiter +$7.79 with 5 players. Every candidate has its exploiter, like rock-paper-scissors. No bot is promoted.

In phase 5c, the simulator moves closer to the site thanks to Rasmus Suonio's logs of real games: the site's quote rule, and a simulated Hard bot whose market looks like figgie.com's. At a table of simulated Hard bots, v3 wins +$22.37 per round with 4 players, against +$20.03 for v2 and +$16.58 for the marginal bot. But it is still exploited by the phase 4 exploiter and by the Bayesian bot, and no bot is promoted. Replayed on paper in place of Rasmus's bot, against the site's real bots, only the Bayesian bot wins (+$8.97 per round), and v3 loses $18.83.

In phase 5d, the market reading learns that, on the site, a bid does not mean the same thing in the first minute and in the last. It no longer does worse than the hand alone early in the round. v4, trained on the site's market with this reading, wins +$35.81 per round at a table of simulated Hard bots, against +$22.37 for v3, and does $14 better than v3 per round on the real rounds replayed on paper. The Bayesian bot no longer exploits it, but the phase 4 exploiter still wins against its copies, and so does v3. No bot is promoted.

In phase 5e, the replay of the real rounds finally counts the majority, estimated from hands of the site's bots that fit the log. The ranking flips: the Bayesian bot, which sells its goal cards at $10, goes from second place to last, and v4 moves to the top. v4b, also trained on tables where nobody quotes, wins +$27.32 per round against the sniper, against +$13.11 for v4, and is level with it elsewhere. It still fails the minority test, against the same three players. No bot is promoted.

In phase 5f, I find why the exploiter wins against copies of my bots: a copy that buys its cards profits from it, but the copies as a whole lose, and my training judged only by the gain of a single copy. v4c, trained by judging each setting by the mean gain of the copies, leaves the exploiter $3.15 per round with 4 players and $4.65 with 5, against 4.05 and $5.85 for v4b. But it still fails the minority test, against the same three players, and no bot is promoted.

In phase 5g, I make every copy play the same setting. It does not reduce what the exploiter takes from them: when they agree, it is on the wrong setting. So I do not write a v4d. I also add six references taken from a paper and four repositories on Figgie: none of them makes money against copies of v4c. Staying quiet in the first minute, an idea from the paper, costs about $8 per round against the marginal bot and takes nothing away from the exploiter. A bootstrap confirms my confidence intervals to within 1.8 %. Describing the table by the average of several rounds takes $0.6 to $0.8 per round away from the exploiter: that is the lead for what comes next.

In phase 5h, I turn it into a v4d. In the tournament, the exploiter takes a little less from it than from the v4c (+$2.77 per round with 4 players against +$3.15), but it still fails the minority test and wins a little less against the marginal bot: it is not promoted.

In phase 5i, I find what the minority test measures: the copies do not overpay for the exploiter's cards, they lose the majority they take from each other. I replace it with a mixed table, the reference and the candidate with simulated Hard bots. The v4c is refused there even more clearly: the exploiter does about $10 better than it per round, mostly by selling non-goal cards to the Hard bots.

In phase 5j, I check that point on the real rounds: the site's bots almost never take a non-goal ask at $7 or more (1 % of cases), while my simulated Hard bots took 9 to 36 %. I recalibrate the simulated Hard bot on this measurement. Against it, the exploiter loses $12 per round, and the v4c that stays quiet in the first minute earns $12.56. In the tournament, the v4c is refused by the recalibrated Hard bot itself, and the quiet v4c no longer beats the marginal bot against its copies: no bot is promoted.

In phase 5k, I find why the v4c overpays in the first minute: it does not know yet which suit is the goal, and its value counts the majority as if nothing else would be traded. A v4c that sells but buys nothing for 60 s beats both the marginal bot (+$7.26 per round with 4 players) and the recalibrated Hard bot (+$10.06). It is refused: at the mixed table, the quiet v4c does $1.57 to $1.81 better than it, and the reading exploiter $3.43 with 5 players. It wins its trades, but leaves the majority to the others. No bot is promoted.

In phase 5l, I fix the value itself: the majority share counts with a weight min(1, t / 120) ^ 0.5, zero at the start of the round and full at 2 minutes. The new v4c beats the marginal bot (+$9.74 per round with 4 players) and the recalibrated Hard bot (+$15.18) by more than any earlier candidate, and it is the first to pass the entry rule with 4 players. It is refused with 5: the quiet v4c does $2.46 better than it at the mixed table, and the reading exploiter $1.66. It sells its goal cards too early, because the weight also applies when selling. Retraining its settings brings nothing clear. No bot is promoted.

In phase 5m, I fix three mistakes found in review: under the site rule, the bot cancelled both of its offers when it only wanted to lower one; the marginal bot's buy value forgot that a seller proves they hold the card when the suit is not the goal; and the table profile kept offers the site had erased. I retrained the v4c and the timed v4c on the fixed code. At the tournament, the timed v4c still passes with 4 players and is still refused with 5, by one reference instead of two: the quiet v4c, which does $3.05 better than it. Almost every bot changed with these fixes, so the numbers do not compare directly with phase 5l's. No bot is promoted.

In phase 5n, I keep the majority weight on buying and remove it from selling, so the bot stops giving away its goal cards early in the round. With T = 240 s, chosen on another seed, the "buying" v4c passes the entry rule with 4 and with 5 players, in the reduced tournament and in the full 300-deal one: no candidate had done so since the mixed table. It beats phase 5l's timed v4c by $3.90 per round with 4 players and by $4.25 with 5. It becomes the reference bot, in place of the marginal bot. It only ties with the reading exploiter with 5 players, and gains less against marginal bots with 5 players (+$9.16 per round against +$12.40). These gains are measured against simulated bots.

In phase 5o, I run the automatic exploiter search again against the "buying" v4c, for the first time since phase 5b, this time on the site's market and at the entry rule's mixed table. It finds no exploiter. With 4 players, the best of 60 settings ends $9.11 per round behind it. With 5 players, the best one ties (-$0.36 [-1.27; +0.55]): it is a cousin of the reading exploiter, a marginal bot that quotes tight and fast. The promotion holds. These gaps are measured against simulated bots.

In phase 5p, I look at the card that breaks a majority tie, the idea from Rasmus's v5. The "buying" v4c ends tied in 13.4% of the rounds with 4 players, and lets slip goal cards at $27 that would bring it about $60. Yet its value counts that gain: what it lacks is information. It values the card at $10, at $21 if it knew the goal, and does not see that a rival is tied with it. Reading the suit better late in the round, tuned in simulation, does no better on the real rounds. The cause lies in the simulator: the consensus of bids finds the goal in 91% of the real rounds at the bell, but in only 67% between our simulated Hard bots. No bot is changed.

In phase 5q, I add this consensus to the simulated Hard bot's tuning. The search finds nothing better than the recalibrated Hard bot: its best setting finds the goal at the bell in 84% of the rounds instead of 73%, but it moves the rest of the market away from the site. And reading the others' offers harder freezes the consensus at about 30%: the Hard bots all follow the first suit where someone bid high. The site's real bots read something other than the highest bids. No bot is changed.

In phase 5r, I look at what the site's Hard bots react to: almost nothing public. Yet each of them finds the goal better and better as the round goes on, from chance at 60 s up to 80% at 180 s. The Hard v3 models this information as it appears: the engine gives it the goal, with a weight that grows with time. Tuned on the real rounds, it is twice as close to the site as the recalibrated Hard bot (gap 23.5 against 46.7, consensus included). The "buying" v4c still passes the entry rule with it at the mixed table, and it becomes that table's filler. No playing bot is changed.

In phase 5s, I learn the site reading's signal model again on tables where the Hard v3 plays. On the 60 real rounds, which are never used for learning, the new reading finds the goal at the bell in 98% of the rounds, against 85%. The "buying" v4c with this reading passes the entry rule in the reduced and the full tournament, with 4 and with 5 players, and makes $10.33 and $10.96 per round more than the "buying" v4c at the same table. It becomes the reference bot. On the other hand, it makes $4 to $8 less against the old simulated Hard bots. These gains are measured against simulated bots.

Full tables are in each phase's doc.

## What I took away

The bayesian does not guess the goal suit better than the heuristic (38.1% against 38.5%). It wins because it knows how uncertain it is and does not dump cards that have a one-in-three chance of being valuable.

In continuous time, speed weighs a lot: the sniper, which only takes mispriced quotes, became the second-best bot. And between bots that never change their minds, the market dies after about twenty seconds. Learning by watching other players will probably be the biggest gain ahead.

A goal card is not worth $10: it can tip the majority and be worth $60 or $110, depending on who sells it and who buys it. The bot that calculates this best wins mainly by waiting for other players' mistakes, with cautious quotes $8 away from its value.

Guessing better is not enough to win more: the information arrives when the market is already almost dead. And measuring calibration ("when the bot says 80%, is it right 80% of the time?") revealed a reasoning flaw that had been there since phase 2.

A bot with fixed settings is a target: when it is numerous at the table, its copies compete with each other and a different player profits. Hence phase 5, a bot that adapts its play during the game.

A bandit learning from its profits sees only noise: a round's profit varies by about $65 from one deal to the next. Recognizing how the others play works better. But when every copy of the bot recognizes the same table, they switch settings together and fall back into the same price war.

Training against its own copies fixes that price war, but each version fixes the previous one's weakness and opens another. And logs of real games show the simulator is far from the site: 53 trades per round on figgie.com, between 6 and 22 at our tables.

Bringing the simulator closer to the site barely changes how my bots rank in simulation, but the replay of the real rounds ranks them differently. And market reading, learned only on my bots, finds the right goal suit in 88 % of the real rounds at the bell, but goes wrong early in the round.

On the site, when a bid arrives matters as much as its price: by separating the minutes, the market reading learned not to believe the bids of the first one. Against the simulated Hard bots, this brings the reader $9 per round, but it does not solve the minority test.

A score that leaves out part of the game favours the bots that leave it out too: without the majority, the replay put the Bayesian bot ahead for two phases. And nearest neighbours answer even at a table that looks like nothing they know: a table of snipers, never seen in training, cost v4 $14 per round.

What the training measures must be what the test measures: buying from the exploiter brings $3.75 per card to the copy that buys, and costs the copies as a whole. Changing the criterion reduces what it takes, but the copies of an adaptive bot do not all play the same setting, and their tables do not look like the training's.

Copies that agree do not win for all that: if they recognise the table badly, they all make the same mistake together. The profile of a single round does not tell the exploiter's table apart from about twenty training tables.

## Limits

All opponents are bots I wrote. No number in this project measures the level against humans until phase 6 (real site) has happened. The simulator rests on assumptions: four rules the site does not specify, and made-up reaction times. Tables do not mix styles yet.

## Run it

Python 3.14, no external dependencies.

```bash
cd projets/bot-figgie
python3 -m unittest                      # 149 tests, about 15 seconds
python3 -m figgie.evaluate --candidate marginal --deals 1000 --seed 1
```

One candidate against the whole zoo takes a few minutes, the phase 4 tournament (`python3 -m figgie.tournoi`) about 1 h 15 on 10 cores. Each phase has a git tag (`phase0-figgie` to `phase5s-figgie`) to get the exact code back.

## Stack

- Python 3.14, standard library only
- unittest for the tests

## Status

In progress: phases 0 to 5s done. Next step to be chosen: learn the v4c's settings again with the new reading, or fix the Hard v3, which overpays for non-goal cards. Phase 6 (real site) waits for written consent from Jane Street.
