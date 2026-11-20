# Phase 5: in-game adaptation

*Version française : [phase5.fr.md](phase5.fr.md)*

Phase 4 ended on one finding: a bot with fixed settings is a target. When the marginal bot quotes $8 from its value, an opponent quoting at $6 takes all the flow. When it tightens, its copies compete with each other and even a random player profits. This phase tries to get out of that dilemma with a bot that picks its spread and edge round after round, depending on the table in front of it.

The outcome is mixed. The adaptive bot beats the marginal bot head to head, with 4 and with 5 players, and the phase 4 exploiter takes much less from it. But it fails the minority test: a sniper alone against three of its copies makes $3.72 per round, whereas it lost against the marginal bot. The automatic search even finds a taker that takes $5.62 per round from it. No bot is promoted. The reason for the failure is instructive: every copy recognizes the same table and makes the same decision at the same moment.

## Why not a bandit on profits

The end of phase 4 suggested a bandit: try a setting, see what it earns, favor what works. Before writing a line, I did the math, and it does not hold. A round's profit varies by about $65 from one deal to the next, because the deal itself largely decides who wins. Two neighboring settings differ by only a few dollars per round. Telling them apart with an honest confidence interval would take about 700 rounds per setting. A game has around ten. A bandit learning from its profits would spend the whole game measuring noise.

So I took the other route: recognizing the table. Other players' behavior is not very noisy. Within one round, you can already see how fast they quote, how wide, whether they stay silent. The bot learns offline, in simulation and on duplicate deals (so without the noise of the deal), which setting works against which kind of table. During a game, it measures the table, looks for the training tables that resemble it most, and plays the setting that worked best there.

## The method

The adaptive bot keeps all of the marginal bot's value calculation. Only two numbers change: its spread and its taking edge. It chooses among four settings: ($6, $3), ($8, $1), ($10, $3) and ($12, $3). The second one is the marginal bot's, and the bot starts every game with it, since it knows nothing about the table yet.

A table's profile fits in six numbers, computed from the public event feed:

- how many quotes per minute the others post, on average and for the most active one;
- the tightest and the median spread when a player quotes both sides of a suit;
- the shortest time a player takes to quote again after a trade;
- the share of players who never quote.

To learn, I drew 80 training tables with 4 or 5 players, with opponents taken from the zoo and the liars (seed 9). Tables full of marginal bots are overrepresented, because that is where copies compete, the case the minority test punishes. On each table, I measured the profit of each of the four settings over 100 duplicate deals. During a game, the bot compares its table's profile with those of the 80 tables, putting every measure on the same scale, takes the 5 nearest ones, and picks the setting that earns the most there on average. The setting is fixed at the start of each round and does not move until the end.

To track quotes, the bot needed to see when a player withdraws theirs. The market's public feed now announces cancellations. This changes nothing in the other bots' play, and the phase 4 golden test confirms it.

## Version 1, then version 2 after review

The first version was validated on 30 unseen tables (seed 10). The fixed setting earns $17.49 per round there, the chosen setting $18.02, and the best possible setting, which can only be known afterwards, $18.89. The gain over the fixed setting is $0.52 per round, with an interval of [+0.05, +0.99]. Small, but clear.

Code review found a problem more serious than all the others. In training, each table's profile was measured over 10 rounds, always playing the reference setting. In a game, the bot has only one or two rounds behind it, and it played them with its own settings. So it was learning from profiles it never sees while playing. The review also flagged six smaller flaws: the liars' table was played twice with several rounds, the model path could not be set, the model cache ignored the file, the exploiter search options were not checked, seeds could overlap beyond 1,000 tables, and one test did not check what it claimed. All are fixed.

For version 2, I measured on each training table 10 profiles of a single round, with each of the four settings. During a game, every round played gives a profile, measured with the setting the bot was playing, and the bot averages the recommendations from each one. I validated it by cross-validation on the 80 tables: each table is judged by a model built on the other 79.

| Choice of setting | Average profit | Gap to fixed setting |
|---|---|---|
| fixed (8, 1) | +16.88 | |
| v1, 10-round profile (what was validated) | +17.13 | +0.25 [-0.04, +0.54] |
| v1, after 1 round (what it actually sees) | +17.00 | +0.12 [-0.20, +0.44] |
| v1, after 3 rounds | +16.95 | +0.07 [-0.30, +0.44] |
| v2, after 1 round | +17.00 | +0.11 [-0.24, +0.47] |
| v2, after 3 rounds | +17.27 | +0.38 [+0.13, +0.64] |
| best setting, known afterwards | +17.77 | +0.89 [+0.65, +1.12] |

In dollars per round. The review was right: v1, as it actually plays, no longer clearly beats the fixed setting. After three rounds, v2 recovers a bit less than half of what could be earned by knowing the answer.

## The tournament

The adaptive bot needs several rounds to adapt. So the tournament is played in 10-round games, on 300 duplicate deals (seed 1), which makes 3,000 rounds per opponent. The marginal bot was measured again under the same conditions, for a direct comparison. The two phase 4 exploiters also join the minority test.

| | marginal | adaptive v1 | adaptive v2 |
|---|---|---|---|
| against marginal, 4 p. | | +1.94 [+1.58, +2.30] | +2.00 [+1.64, +2.37] |
| against marginal, 5 p. | | +3.45 [+3.13, +3.78] | +3.47 [+3.15, +3.79] |
| against reader, 4 p. | +0.97 | +2.33 | +2.21 |
| against reader, 5 p. | +5.52 | +8.52 | +8.33 |
| against exploiter, 4 p. | +19.84 | +18.53 | +17.14 |
| sniper alone, 4 p. | -0.94 [-1.39, -0.48] | +3.55 [+3.06, +4.03] | +3.72 [+3.24, +4.21] |
| sniper alone, 5 p. | -1.28 [-1.64, -0.91] | +2.66 [+2.27, +3.05] | +2.80 [+2.42, +3.19] |
| bayesian alone, 4 p. | +1.14 [+0.56, +1.72] | +0.99 [+0.41, +1.57] | +0.10 [-0.47, +0.67] |
| marginal alone, 4 p. | | +1.25 [+0.91, +1.58] | +1.29 [+0.95, +1.64] |
| marginal alone, 5 p. | | -0.32 [-0.64, -0.00] | -0.26 [-0.56, +0.04] |
| exploiter alone, 4 p. | +4.32 [+3.85, +4.80] | +1.63 [+1.14, +2.11] | +1.54 [+1.06, +2.02] |
| exploiter alone, 5 p. | +7.24 [+6.85, +7.64] | +3.16 [+2.79, +3.54] | +3.02 [+2.64, +3.39] |

In dollars per round. The "alone" rows give the profit of the opponent alone against copies of the candidate: the higher it is, the more the candidate gets exploited.

Against the rest of the zoo, nothing moves: all three bots clearly beat every opponent, within a few tens of cents. At the abnormal tables (100 deals, 10 rounds), the numbers are close too: +$20.4 with the idle player for all three, +$20.4 with the liars for the marginal bot and v2 (+$19.3 for v1), and +$119.6 with the spammer for the marginal bot and v2 (+$112.4 for v1).

**The entry rule's verdict.** All three bots clearly beat the whole zoo. None passes the minority test. The marginal bot fails with 4 players (bayesian alone, +$1.14), and with 5 players because of the exploiter, now that exploiters count in the test. Both adaptive bots fail with 4 and 5 players because of the lone sniper, and with 4 players also because of the lone marginal bot. No bot is promoted, and the marginal bot remains the reference.

**Is the bot improving?** Partly, yes. It beats the marginal bot head to head, by $2 per round with 4 players and $3.5 with 5. It earns more against the reader. The phase 4 exploiter takes less than half of what it took from the marginal bot. But it opened a new weakness: the sniper, which earned nothing alone against marginal bots, now clearly wins against adaptive ones. v2 is roughly even with v1 everywhere. Its better offline validation does not show in the tournament.

## Why the sniper wins

I looked at which settings three adaptive bots choose against a lone sniper. From the second round on, all three switch to the $6 spread, and they stay there. From their point of view, it makes sense: their table looks like the training tables full of marginal bots, and on those tables, quoting at $6 is exactly what the phase 4 exploiter did. Except that on the training tables, the bot was the only one tightening. Here, its three copies do it at the same time. We are back in phase 4's price war: three bots quoting tight fight over the same cards, and the sniper, which only takes badly placed prices, profits.

The flaw comes from training. The bot never saw a table where the others adapt like it does. It learned the best response to fixed opponents, and it applies it to opponents that change at the same moment it does.

## Exploiters

I ran the phase 4 exploiter search again against v2, with 4 players, in 10-round games. Every stage costs ten times more than before, so I reduced the number of deals: 20 in stage 1 (seed 5), 100 in stage 2 (seed 6) and 300 in stage 3 (seed 1). The 60 settings tried are the same.

The winner is a pure taker. It computes its values like the marginal bot, never quotes, takes any quote that leaves it at least a $2 edge, and reacts in 0.2 seconds. It is a better-informed sniper. Alone against three copies of v2, it makes +$5.62 per round [+5.16, +6.08]. That is more than the phase 4 exploiter took from the marginal bot (+$4.32).

I then measured it against the other candidates, on the same 300 deals:

| Alone against copies of | 4 players | 5 players |
|---|---|---|
| marginal | -0.70 [-1.11, -0.29] | -1.30 [-1.69, -0.92] |
| adaptive v1 | +5.44 [+4.98, +5.90] | +4.14 [+3.70, +4.58] |
| adaptive v2 | +5.62 [+5.16, +6.08] | |

The taker's profit, in dollars per round.

This table confirms the diagnosis. Against the marginal bot, which keeps its $8 spread, the taker loses. Against the adaptive bots, it clearly wins. The adaptation itself, when every copy tightens at once, creates the weakness. I did not have time to run the search with 5 players.

## What I took away

Doing the math before coding saved me from a bandit that would have learned nothing. With $65 of noise per round, a 10-round game says almost nothing about the setting you played. What can be measured quickly is how the others play.

Code review found the phase's most important flaw, and it was a flaw of method. A bot trained on measurements it will never see while playing looks good in validation. Training has to be measured exactly the way the bot will experience it.

Adapting to the table is not enough when the table adapts too. A best response learned against fixed opponents becomes a weakness as soon as the other players follow the same rule. In game theory, that is the difference between responding best to known strategies and looking for an equilibrium. The logical next step would be to train the bot on tables that also contain its own copies, then start again with the new version, until its choices stop changing.

## Limits

All opponents are still bots. Profits measured here, against simulated bots, say nothing about the level against humans.

The bot chooses among only four settings, with a model learned on 80 tables. It learns nothing from one game to the next: it adapts within a game, with a model built once offline. It does not read the market the way the phase 3 reader does either.

The tournament uses 300 deals instead of 1,000, because each deal is now a 10-round game. Intervals stay around a dollar.

The limits of earlier phases still hold: made-up reaction times, four assumed site rules, money resetting to $350 each round.

## Reproduce

```bash
cd projets/bot-figgie
python3 -m unittest                                                  # the 97 tests, about 5 s
python3 -m figgie.adapt --tables 80 --valid 30 --deals 100 --report adaptation.json   # version 1
python3 -m figgie.adapt --tables 80 --deals 100 --v2-from adaptation.json --report adaptation_v2.json
python3 -m figgie.tournoi --candidates marginal adaptatif adaptatif_v2 --rounds 10 --deals 300 --table-deals 100 \
    --references heuristique sniper bayesien marginal exploiteur exploiteur_lecteur --out tournoi.json
python3 -m figgie.exploit --target adaptatif_v2 --players 4 --rounds 10 --deals 20 100 300
```

The tournament takes about an hour and a half per candidate on 10 cores. To get exactly this phase's code back: `git checkout phase5-figgie`.

## Next

Phase 6 is the real site, and it waits for written consent from Jane Street. Until then, two leads remain open locally. The first fixes the flaw found here: train the adaptive bot on tables that contain its own copies, and repeat until its choices settle. The second combines adaptation with phase 3's market reading, which the adaptive bot does not use yet.
