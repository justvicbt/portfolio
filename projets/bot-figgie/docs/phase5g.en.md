# Phase 5g: copies that play together, and six new references

*Version française : [phase5g.fr.md](phase5g.fr.md)*

Phase 5f ended with two leads. This phase tries the first one: make every copy of the v4c play the same setting, chosen from what all of them see. If the copies looked like the symmetric tables from training, they might pick 6,3 against the exploiter, the only setting that holds it.

The answer is no. Making the copies play the same setting does not reduce what the exploiter takes from them, and one of the variants lets it win more. So I did not write a v4d on this lead.

I used the phase to read what has been published on Figgie since my research in phase 5b: one paper and four repositories. I took six new references for the minority test from them, all rewritten from their description, and one game idea: stay quiet during the first minute. None of the six makes money against copies of my bots, and staying quiet in the first minute costs about $8 per round against the marginal bot. No bot is promoted. A last diagnostic opens a lead for what comes next: describing the table by the average of several rounds reduces what the exploiter takes from the copies.

## Step 0: coherent copies

### Three variants

I wrote three variants of the v4c, which differ only in how they choose the setting for the next round:

- **public**: each copy describes the table from the whole market, without excluding itself, and asks its neighbours for a strong hand as well as a weak one. All copies see the same market, so they should choose the same.
- **shared**: the first copy chooses like the v4c, and the others take its choice. It is cheating, since the copies talk to each other, but it answers the question: if they all played the same, would it help?
- **seats**: each copy describes the table from every seat, and asks its neighbours for all these profiles at once.

### What they choose against the exploiter

I replayed the phase 5f test: the exploiter alone against 3 copies, a 4-round match, on three deals. That makes 27 choices per variant (3 deals, 3 copies, 3 rounds after the first):

| Variant | 6,3 | 8,1 → 3,1 | other |
|---|---|---|---|
| v4c | 11 | 15 | 1 |
| public | 3 | 24 | 0 |
| shared | 15 | 12 | 0 |
| seats | 0 | 27 | 0 |

Making the copies coherent does not make them choose the right setting. The public and seats variants agree, but on 8,1 → 3,1, the setting that pays the exploiter the most. Shared chooses 6,3 a little more often than the v4c, but not always.

I looked at where the neighbours of the seats copies come from. They are scattered over about twenty different training tables. On average, these neighbours make $4.25 per round with 8,1 → 3,1, against $3.37 with 6,3. So they recommend 8,1 → 3,1. The profile of one round does not recognise the exploiter's table, and all the copies get it wrong together.

### What it does to the minority test

I measured the reference alone against the copies of each variant, on 100 deals from seed 7 (not the tournament's). Gain of the reference in dollars per round, and in brackets the paired gap with the v4c. A negative gap is good for my copies.

| Reference alone | v4c, 4 p. | shared | seats | v4c, 5 p. | shared | seats |
|---|---|---|---|---|---|---|
| exploiter | +2.91 | -0.44 [-0.96 ; +0.08] | **+0.57** [+0.09 ; +1.05] | +4.86 | -0.00 [-0.43 ; +0.43] | **+0.96** [+0.50 ; +1.42] |
| v3 | +0.87 | +0.26 [-0.73 ; +1.26] | +0.25 [-0.73 ; +1.24] | +2.72 | **+1.04** [+0.09 ; +1.98] | **+1.14** [+0.16 ; +2.11] |
| marginal | -0.69 | -0.19 [-1.17 ; +0.79] | -0.08 [-0.96 ; +0.80] | +0.77 | +0.24 [-0.61 ; +1.10] | +0.95 [-0.07 ; +1.97] |
| sniper | -4.83 | **-1.14** [-1.75 ; -0.53] | **-3.71** [-4.32 ; -3.09] | -3.16 | **-1.23** [-1.79 ; -0.68] | -0.45 [-1.07 ; +0.18] |

In bold, the gaps whose interval does not touch 0. Against the exploiter, shared does no better than the v4c, and seats does worse. Against the v3 with 5 players, both do worse. The only clear gain is against the sniper, which was already losing to the v4c.

My plan said to write a v4d only if this diagnostic showed an effect. It shows none, so I stopped there. The variants stayed diagnostic scripts, outside the repository.

## Step 1: what others have published

### What I read

| Source | What it is | Licence | What I took from it |
|---|---|---|---|
| DiSilvio, Luo and Ozerov, "Traders in a Strange Land" (arXiv 2110.00879, 2021) | a 4-player Figgie simulation, with hand-written agents | CC BY 4.0 | the imitator, the fundamentalist, the idea of the quiet v4c, the bootstrap |
| LSeaburg/FiggieServer | a server that imitates the site, with the paper's agents | none | two site rules to check, the value r = 1.7 |
| CornellDataScience/FiggieBot (2022) | a server and an unfinished counting agent | none | the value r = 3.5 |
| 0xDub/figgie-auto, and its fork Pranay0302/figgie | a Rust engine with 7 strategies, then a transformer trained on it | none | three strategies, rewritten |
| parmarsuraj99/figgie-python-rl (2024) | a server and LLM agents | none | nothing |

Without a licence, I took no code, only ideas described in words. Several of these projects depart from the rules on points that matter. At Cornell, in figgie-auto and in figgie-python-rl, the goal suit has 8 cards one time in 2 or one time in 4, instead of one time in 3. figgie-python-rl does not even pay the majority. Pranay0302's transformer claims 75 % wins, but that is the share of rounds where it wins something, with no interval and no duplicate deals, on 30 s rounds and against opponents that its own README calls broken (three copies of the same bot share a single inventory there). So I do not use it as a point of comparison.

### The imitator

Among the paper's agents is a "bottom feeder", which I call the imitator. It does not look for the goal suit. It watches the prices at which the other players offer to buy and sell, averages them, then offers to buy below that value or to sell above it. It lives off other people's prices, which makes it a natural candidate for the minority test.

I rewrote it from the paper. It looks at the market every 2 seconds on average, picks a suit and a side at random, and draws a price between $1 and its value to buy, or between its value and twice that to sell. If the price reaches the best offer on the other side, it takes it. Two differences with the paper: there, it waits for 4 prices on each side before acting, and it follows a hand-picked prey. On our tables it would almost never act, so I take the last 4 prices as soon as there is one on each side, and its prey are all the other players. The seam test checks that it never buys above its value and never sells below it.

### The fundamentalists

In the paper, the fundamentalist is the most profitable strategy in every combination tested. It weighs each of the 12 possible decks by the number of ways to find in it the cards it has seen: its hand and the cards that changed hands in trades. A card of a suit is then worth, for each deck where that suit is the goal, $10 plus a geometric share of the majority: p (1 − r) r^h / (1 − r^x), where h is its number of cards of the suit, x the safe majority (5 cards if the goal has 8, 6 otherwise) and p what is left of the pot ($120 or $100). Selling a card is worth the same with h − 1. It quotes like the imitator.

The paper gives no value for r, only r > 1. I took two: 1.7, like FiggieServer, and 3.5, like the Cornell repository. The seam test checks its value on an example worked out by hand: with the hand S4 C1 H3 D2 and no trade, a heart is worth $5.93 to buy and $4.32 to sell.

The paper insists on one point: cancel the offers that the new value no longer justifies. I do not. With the site rule, its value only changes after a trade, which already clears the book.

One detail struck me when rereading the paper. The fundamentalist counts every card it has seen as if it had been drawn at random. But a card that was bought was chosen: counting this way makes the bot overconfident. It is exactly the calculation of my phase 2, which I fixed in phase 3. I kept it as it is, since it is the paper's agent I want to measure.

### Three strategies from figgie-auto

figgie-auto describes 7 strategies. I did not rewrite four of them: Noisy looks like my random bot, PickOff like my sniper, Spread is a naive market maker, and TheHoarder, which wants 6 cards of each suit, is described by its own author as risky and not very profitable. I rewrote the other three:

- **the seller** ("Seller") only sells. It offers each suit it holds at a floor price that drops over time ($8 in the first minute, then 6, 6 and $4), and takes buy offers that are high enough. It looks like my exploiter, which wins precisely by selling.
- **the mantis** ("PrayingMantis") sells everything for 3 minutes, $1 below the displayed sell offer if it is worth $7 or more. In the last minute, it buys, at $9 at most, the suit whose last trade was the most expensive. On the site, almost half of the trades happen in the last minute.
- **the gambler** ("TiltInventory") bets on the suit it had the most cards of at the start. It buys it up to $8 and sells the others.

All three look at the market every 2 to 4 s, as in figgie-auto, and only quote to beat the displayed offer. One difference: there, they send all their orders at once, here a single action drawn at random each time. Each has its seam test.

### At the tournament

I put the five new references through the minority test, alone against copies of the v4c, the v4b and the marginal bot, on the 300 deals of the tournament (seed 1), with the site rule and in 10-round matches. Each number is the reference's average gain per round, with its 95 % interval.

| Reference alone against | v4c 4 p. | v4c 5 p. | v4b 4 p. | v4b 5 p. | marginal 4 p. | marginal 5 p. |
|---|---|---|---|---|---|---|
| fundamentalist (r = 1.7) | -10.93 [-11.71 ; -10.14] | -6.88 [-7.56 ; -6.20] | -11.01 [-11.77 ; -10.24] | -7.25 [-7.91 ; -6.59] | -8.10 [-8.85 ; -7.36] | -7.03 [-7.71 ; -6.36] |
| fundamentalist (r = 3.5) | -14.63 [-15.34 ; -13.91] | -11.23 [-11.79 ; -10.67] | -14.29 [-15.02 ; -13.56] | -11.53 [-12.05 ; -11.01] | -11.68 [-12.37 ; -10.99] | -11.00 [-11.52 ; -10.48] |
| seller | -6.65 [-7.06 ; -6.24] | -2.49 [-2.79 ; -2.18] | -5.94 [-6.35 ; -5.53] | -1.42 [-1.72 ; -1.12] | -5.73 [-6.17 ; -5.30] | -4.53 [-4.85 ; -4.21] |
| mantis | -7.95 [-8.38 ; -7.53] | -5.63 [-5.98 ; -5.28] | -6.51 [-6.92 ; -6.11] | -3.95 [-4.33 ; -3.58] | -11.85 [-12.25 ; -11.44] | -9.49 [-9.81 ; -9.18] |
| gambler | -5.82 [-6.32 ; -5.32] | -3.08 [-3.52 ; -2.65] | -4.12 [-4.61 ; -3.62] | -1.71 [-2.21 ; -1.21] | -11.09 [-11.52 ; -10.66] | -9.44 [-9.77 ; -9.11] |

All 30 cells are negative, intervals included: none of the five references makes money against the copies. The exploiter remains the only known bot that exploits the v4c (+$3.15 and +$4.65). The most dangerous of the new ones is the seller, with 5 players, and that is no accident: it wins like the exploiter, by selling. It just does not know what to sell.

Three things surprised me. The paper's fundamentalist, the most profitable there, is among the worst here: it pays for its overconfidence, and the larger r is, the more it pays. The v4c leaves less than the v4b to the three figgie-auto strategies, by $0.7 to $1.7 depending on the cell, which I had not looked for. And the marginal bot punishes the mantis and the gambler much harder than the adaptive bots do: $9 to $12 per round, against $2 to $8.

## Step 2: stay quiet in the first minute

The paper measures something I did not expect (table 3). Among four identical fundamentalists, the one with no latency ends with less money than the three slow ones: against each of them, the 95 % interval of the gap falls between $12 and $41. The authors explain it this way: it trades more often early on, when its values still move a lot. That matches my phase 5d, where the site reader learned not to trust the offers of the first minute.

So I tried the quiet v4c: the v4c that sends no order during the first 30 or 60 seconds of each round, then plays normally. It still reads the market, so its choice of setting does not change. The seam test checks this in a real match.

Before running the diagnostic, I fixed the decision rule. A quiet variant helps if three conditions hold: the exploiter's paired gap has an interval entirely below 0, with 4 or with 5 players; no other reference has a gap entirely above 0; and against the marginal bot, the lower bound of the gap stays above -$1. If a variant helped, it went to the full tournament.

I measured it as in step 0, on 100 deals from seed 7, in paired gaps with the v4c. A negative gap is good for my copies in the "alone" rows, and bad in the "against the marginal bot" row, where it is my bot's gain.

| | v4c, 4 p. | quiet 30 s | quiet 60 s | v4c, 5 p. | quiet 30 s | quiet 60 s |
|---|---|---|---|---|---|---|
| exploiter alone | +2.91 | +0.31 [-0.25 ; +0.86] | -0.24 [-0.79 ; +0.32] | +4.86 | **+0.55** [+0.10 ; +1.00] | -0.10 [-0.60 ; +0.40] |
| v3 alone | +0.87 | **+2.18** [+1.30 ; +3.07] | +0.39 [-0.67 ; +1.45] | +2.72 | **+2.14** [+1.05 ; +3.22] | **+1.17** [+0.10 ; +2.24] |
| marginal alone | -0.69 | **+2.37** [+1.23 ; +3.50] | **+1.22** [+0.13 ; +2.31] | +0.77 | **+2.00** [+0.99 ; +3.01] | **+1.66** [+0.64 ; +2.68] |
| sniper alone | -4.83 | **+1.12** [+0.38 ; +1.86] | **+1.20** [+0.52 ; +1.89] | -3.16 | **+0.82** [+0.21 ; +1.43] | **+1.81** [+1.13 ; +2.49] |
| fundamentalist alone | -10.08 | +0.04 [-1.11 ; +1.19] | **-1.15** [-2.23 ; -0.08] | -5.90 | -0.51 [-1.57 ; +0.55] | +0.41 [-0.85 ; +1.68] |
| against the marginal bot | +7.94 | **-8.29** [-9.31 ; -7.27] | **-7.59** [-8.70 ; -6.47] | +5.08 | **-7.95** [-8.89 ; -7.02] | **-7.62** [-8.48 ; -6.76] |

Neither variant helps, by a long way. Staying quiet takes nothing away from the exploiter, none of whose intervals goes below 0. The v3, the marginal bot and the sniper all take more from the quiet copies. Above all, against the marginal bot, my bot loses about $8 per round, almost everything it was winning: it goes from +$7.94 to -$0.34 with 4 players, and from +$5.08 to -$2.88 with 5.

I did not expect such a strong effect, and I have not explained it. What the number says is that the v4c makes a good part of its money in the first minute, and a competitor who stays quiet then leaves the best deals to the others. So the paper's result does not carry over: there, all four players were overconfident fundamentalists, misled by early trades. Mine have counted bought cards correctly since phase 3.

The quiet v4c stays in the code as a measured candidate, but it is not promoted.

## Step 3: describe the table over several rounds

The rule fixed before the diagnostic said that, if no quiet variant helped, I would test another idea from step 0. The profile of a single round does not recognise the exploiter's table. Today, the v4c asks its neighbours round by round, then averages their advice. I tried the reverse: first average the profiles of the past rounds, then ask the neighbours once with that average profile. One variant takes all past rounds, the other the last 3. It is a diagnostic script, outside the repository.

In the 27-choice test, nothing moves: 12 times 6,3, against 11 for the v4c. Both variants make the same choices there, which is expected over 4 rounds, where there are at most 3 profiles to average. The minority test, in 10-round matches, says something else (100 deals from seed 7, paired gaps with the v4c):

| | v4c, 4 p. | all rounds | last 3 | v4c, 5 p. | all rounds | last 3 |
|---|---|---|---|---|---|---|
| exploiter alone | +2.91 | **-0.82** [-1.30 ; -0.34] | **-0.71** [-1.18 ; -0.25] | +4.86 | **-0.62** [-1.02 ; -0.22] | **-0.65** [-1.06 ; -0.24] |
| v3 alone | +0.87 | -0.43 [-1.19 ; +0.34] | -0.13 [-0.86 ; +0.61] | +2.72 | -0.56 [-1.43 ; +0.31] | -0.56 [-1.41 ; +0.30] |
| marginal alone | -0.69 | -0.03 [-0.91 ; +0.85] | -0.18 [-1.05 ; +0.68] | +0.77 | -0.25 [-1.23 ; +0.73] | **-0.93** [-1.83 ; -0.03] |
| sniper alone | -4.83 | -0.35 [-0.94 ; +0.24] | -0.26 [-0.81 ; +0.29] | -3.16 | +0.12 [-0.40 ; +0.64] | -0.08 [-0.57 ; +0.41] |
| fundamentalist alone | -10.08 | -0.41 [-1.40 ; +0.58] | **-0.93** [-1.83 ; -0.03] | -5.90 | -0.09 [-1.04 ; +0.85] | -0.46 [-1.33 ; +0.41] |
| against the marginal bot | +7.94 | -0.69 [-1.42 ; +0.03] | **-1.00** [-1.74 ; -0.26] | +5.08 | -0.36 [-0.89 ; +0.18] | -0.38 [-1.07 ; +0.30] |

It is the first time a variant clearly reduces what the exploiter takes from the copies, with 4 and with 5 players: by $0.6 to $0.8 per round, that is 28 % of its gain with 4 players and 13 % with 5. No other reference gains from it. The price is a little less gain against the marginal bot. If I applied the rule fixed for the quiet v4c, the "all rounds" variant would narrowly fail: the lower bound of its gap against the marginal bot is -$1.42 with 4 players, under the -$1 threshold. And even with this gain, the exploiter keeps +$2.09 and +$4.24: the minority test would still fail.

I did not turn it into a v4d tonight. It was not in the approved plan, and 100 deals from a single seed are not enough to promote a bot.

## Two rules of the site

FiggieServer contains two observations about the site that affect my engine.

**Cancellations.** Do the site's bots cancel their offers? In Rasmus Suonio's logs, the Hard bots have 233 cancellations. 97 % fall in the same second as a trade or the second after (164 in the same second, 63 one second later). They are not deliberate cancellations: after a trade, the site clears the suit's book, and the log records it as cancellations. That is what the FiggieServer author says. My simulated Hard never cancels an offer, which is consistent.

**Crossing your own offer.** If a player offers to buy at the price of their own sell offer, my engine refuses the action, like FiggieServer. According to its author, the site instead cancels all of that player's offers in the suit. I could not check this in the logs. I think the effect is small, without having measured it, so I leave the engine as it is and note it in the limits.

## Check: my confidence intervals

In a zero-sum game, the gains of players in the same match are not independent, and their distribution often has two humps: you guessed the goal suit, or you did not. So the paper compares its strategies with a bootstrap. My duplicate deals already deal with the dependence, since each value is one deal and the deals are independent. But my intervals assume a normal distribution, and I had never checked it.

So I recomputed every interval of the step 2 diagnostic with a percentile bootstrap: 10,000 draws with replacement of the 100 values, keeping the means at 2.5 % and 97.5 %. Over the 60 cells, raw values and paired gaps, the largest difference between a normal bound and a bootstrap bound is $0.03, or 1.8 % of the interval's width. No conclusion changes. With 100 deals or more, the mean is already close enough to a normal distribution for my intervals to hold, despite the two humps.

## The tournament

The v4c has not changed since phase 5f, and the engine is deterministic: replaying the whole tournament would give the same numbers. So I replayed only what is new, on the same 300 deals (seed 1), with the site rule, in 10-round matches. I added checks, which land exactly on the previous phases: the v4c makes +$7.75 and +$4.59 against the marginal bot, as in phase 5f, the v4b +$8.46 and +$4.94, as in phase 5e, and the exploiter still takes +$3.15 and +$4.65 from the v4c copies.

The imitator alone against the copies:

| Imitator alone against | 4 p. | 5 p. |
|---|---|---|
| v4c | -27.13 [-28.10 ; -26.16] | -24.24 [-25.32 ; -23.15] |
| v4b | -27.07 [-27.99 ; -26.15] | -24.03 [-25.07 ; -23.00] |

No new candidate entered the full tournament, since the quiet v4c failed the diagnostic. So the v4c remains the best bot, with the same numbers as in phase 5f, and it still fails the entry rule because of the minority test: the exploiter takes +$3.15 and +$4.65 per round from it. The entry rules shown in this phase's result files only cover the opponents and references replayed here, not the whole zoo. The bot does not progress in this phase.

All these numbers are measured against simulated bots: they are not real gains.

## What I take from it

I thought the copies lost because they did not all play the same. The diagnostic says something else: they recognise the table badly. When they agree, it is on the wrong setting, and they lose together. The problem is further upstream, in the profile of a single round, which does not tell the exploiter's table apart from the twenty training tables that look like it.

The references found elsewhere taught me nothing new about my weaknesses: none does better than the exploiter, which remains my worst opponent. They are still useful: they widen the minority test to styles I would not have written, and they show that the v4c holds better than the v4b against the three figgie-auto strategies.

The quiet v4c taught me that the first minute is worth a lot. An idea that works for someone else does not carry over when their bots do not make the same mistake as mine.

The average profile goes in the direction of the step 0 diagnostic: the problem is recognising the table, and looking at several rounds at once helps a little.

## Next

The clearest lead is the average profile from step 3. I propose to measure it on more deals, then, if it holds, to turn it into a v4d and put it through the full tournament and the entry rule. The gap with the marginal bot will still need closing, and much more will need to be taken away from the exploiter, which would still keep $2 to $4 per round. The other lead from phase 5f remains open: change the lever, for example how the bot sells its goal-suit cards. I will propose a plan before starting.

## Limits

The variants of steps 0, 2 and 3 were measured on only 100 deals, from a different seed than the tournament. The public variant was played only in the 27-choice test, not in the minority test, because it chose 8,1 → 3,1 even more often than the v4c.

The six references are rewrites from descriptions. The imitator and the fundamentalists depart from the paper on the points noted above, and the figgie-auto strategies do not send their orders the same way there. With the site rule, some of their offers are refused because they do not beat the displayed offer. A refusal has the same effect on the market as doing nothing, but it costs the bot its turn. For the imitator and the fundamentalists, that is about half of their orders (234 out of 475 and 291 out of 706 in a check match): they trade about half as often as intended, which probably weakens them. So they do not play exactly as in their source.

On the site, crossing your own offer would cancel all your offers in the suit, according to the FiggieServer author. My engine refuses the action. I have not checked this on the site.

Everything is still measured against simulated bots. These gains are not real gains on figgie.com.

## Reproduce

```bash
cd projets/bot-figgie
python3 -m unittest                                                  # the 124 tests, about 15 s
python3 -m figgie.tournoi --site --candidates adaptatif_v4c --rounds 10 --deals 300 --no-tables \
    --opponents marginal --references exploiteur imitateur --out tournoi_v4c.json
python3 -m figgie.tournoi --site --candidates adaptatif_v4b --rounds 10 --deals 300 --no-tables \
    --opponents marginal --references imitateur --out tournoi_v4b.json
python3 -m figgie.tournoi --site --candidates adaptatif_v4c adaptatif_v4b marginal --rounds 10 --deals 300 --no-tables \
    --opponents inactif --references fondamentaliste fondamentaliste_35 vendeur mante parieur \
    --out tournoi_references.json
```

The tournament now shows its progress while it runs. To get back to the exact code of this phase: `git checkout phase5g-figgie`.
