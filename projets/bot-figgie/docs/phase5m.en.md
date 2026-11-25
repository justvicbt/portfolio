# Phase 5m: three flaws fixed, and a new starting point

*Version française : [phase5m.fr.md](phase5m.fr.md)*

The full code review after phase 5l found three flaws that change how the bots play. They are mistakes in what I had already written. I fix them before going on, because later phases would otherwise compare against wrong numbers. The price: no earlier number compares directly with this phase's.

At the tournament, on the same deals as phase 5l, the timed v4c still passes the entry rule with 4 players and is still refused with 5. Only one reference refuses it now: the v4c that stays quiet for the first minute, which does $3.05 better than it per round at the mixed table ($2.46 in phase 5l). The reading exploiter no longer refuses it: its gap, +$0.22, has an interval that contains 0. No bot is promoted.

## Cancelling one side

Under the site rule, an offer can only improve: to lower my bid, I first have to cancel it. My bots did this with the engine's only cancel action, which removed both of my quotes in the suit. When a bot only wanted to lower its bid, it also lost its ask, and had to post it again on the next turn if it still could. In the meantime, someone else could have taken its place.

The site does tell the two apart: Rasmus's logs contain bid cancels (`xb`) and ask cancels (`xo`). The engine now accepts `("cancel", suit, "bid")` and `("cancel", suit, "ask")`, and the public feed says which side went away. The old form, with no side, still removes both.

The seams, written with TDD:
- in the engine, cancelling my bid leaves my ask, and the public feed says so. The test fails if cancelling one side removes both;
- a bot that wants to lower its bid under the site rule cancels only that bid. The test failed before the fix: the bot returned a two-sided cancel.

I did not touch phase 5j's recalibrated Hard bot: it still cancels both quotes, and it was recalibrated on the real rounds with that behaviour.

## The marginal bot's buy value

When a player sells me a card, they prove they had one. The marginal bot's Monte Carlo accounts for this: it removes the worlds where that player had no card of the suit. But it only did so in the worlds where the suit is the goal, because it only places goal cards. The worlds where the suit is not the goal were all still counted, even those where the seller could not have the card. Since the card is worth $0 there, they pulled the buy value down.

For those worlds, I do not need to place the cards: I compute directly the probability that the seller has at least one card of the suit, from the number of places they have left (a hypergeometric law). Each world counts with that weight.

The gap is small in general, but it gets large against a player whose hand is almost fully known. The seam compares the fast value with an average computed by hand over whole tables drawn at random, as the test already did. Its reference reproduced the same flaw, and I fixed it. I also made it cover a player who has only one unknown place left: the old fast value gave $1.84 to a spade bought from them, the reference about $5.80. The test fails on the old code and passes on the new one.

This fix changes how the marginal bot plays, and every bot that inherits from it. So the engine's reference test, which replays fixed rounds, changes too. I regenerated it on the same tables and the same seeds: the only table with no marginal-value bot (Bayesian, passive, sniper, aggressive, heuristic) gives exactly the same results as before, which confirms that the engine itself did not move.

## The table profile

The adaptive bots describe the table with a few numbers, among them the gap between each opponent's bid and ask prices. Under the site rule, a new offer erases the one that was shown. The profile did not know this: it kept the erased offer, and could later pair it with an ask from the same player, for a spread that player never showed.

The profile now follows the site rule when the round does, and one-sided cancels too. Two seams, on hand-written feeds: a beaten offer no longer counts in the spread (the test fails if I remove the rule), and a bid cancel lets the ask pair with the new bid.

The v4c's nearest neighbours learned on these profiles. Changing the profile in play without retraining would have shown them profiles they had never seen. So I trained the v4c and phase 5l's timed v4c again on their 188 tables, with the fixed code. The older versions (v3, v4, v4b) keep their models: they play with the fixed profile, on neighbours learned with the old one.

## The retraining

With the fixed code, the v4c took 156 minutes to learn its 188 tables again. Its cross-validation is almost what it was in phase 5f: the setting it picks earns +$2.61 per round more than the fixed setting [+2.08; +3.13], against +$2.48 [+1.91; +3.05] with the old code. Its neighbours learn just as well on the fixed profile.

Phase 5l's timed v4c, trained again the same way, took 332 minutes. The setting it picks earns +$4.23 per round more than the fixed setting [+3.67; +4.78], against +$3.76 [+3.24; +4.27] in phase 5l. The two intervals overlap for the most part: I do not read this as progress, only as a sign that learning did not suffer from the fix.

## The tournament

Same format as phase 5l: seed 1, 100 deals of 10 rounds, the same 12 references at the mixed table, with the recalibrated Hard bot as filler. The deals are the same, but most bots changed with the fixes, not only the candidate:
- one-sided cancels change how every fixed-value bot plays under the site rule (heuristic, sniper, Bayesian, exploiter);
- the buy value and the profile change the marginal bot and every adaptive version, and the v4c, the quiet v4c and the selling v4c play with the retrained model.

Only the two simulated Hard bots, the seller and the gambler play exactly as in phase 5l. For them, the gap between the two phases comes from the candidate alone. For the others, I compare numbers, not the same opponent.

Against three copies of one opponent (candidate's gain, in dollars per round):

| Opponent | 5m, 4 p. | 5m, 5 p. | 5l, 4 p. | 5l, 5 p. |
|---|---|---|---|---|
| heuristic | +42.48 [+40.07; +44.89] | +37.54 [+35.67; +39.40] | +42.09 | +36.78 |
| sniper | +33.81 [+32.47; +35.15] | +31.51 [+30.28; +32.75] | +30.85 | +27.50 |
| Bayesian | +24.31 [+22.43; +26.18] | +23.41 [+21.91; +24.90] | +23.68 | +22.20 |
| marginal | +12.19 [+11.18; +13.19] | +12.40 [+11.46; +13.34] | +9.74 | +8.04 |
| phase 5c Hard (unchanged) | +38.24 [+36.80; +39.67] | +34.40 [+33.04; +35.77] | +37.40 | +31.86 |
| recalibrated Hard (unchanged) | +15.26 [+13.49; +17.04] | +13.13 [+11.62; +14.63] | +15.18 | +12.78 |

At the mixed table (gap reference minus candidate, in dollars per round; a gap whose whole interval is above 0 refuses the candidate):

| Reference | 5m, 4 p. | 5m, 5 p. | 5l, 4 p. | 5l, 5 p. |
|---|---|---|---|---|
| recalibrated Hard (unchanged) | -20.61 [-22.98; -18.23] | -16.28 [-18.23; -14.33] | -19.96 | -16.36 |
| Bayesian | -21.94 [-23.70; -20.19] | -18.97 [-20.29; -17.64] | -24.55 | -20.14 |
| marginal | -14.67 [-16.28; -13.05] | -10.54 [-12.24; -8.84] | -15.13 | -11.80 |
| v3 | -9.96 [-11.88; -8.03] | -6.30 [-7.74; -4.86] | -10.65 | -8.66 |
| v4b | -8.36 [-9.94; -6.79] | -1.68 [-3.12; -0.24] | -7.64 | -1.79 |
| v4c | -8.08 [-9.43; -6.73] | -2.64 [-3.98; -1.29] | -7.27 | -1.74 |
| quiet v4c, 60 s | -1.09 [-2.24; +0.06] | **+3.05 [+1.97; +4.13]** | -1.33 | **+2.46** |
| selling v4c (5k) | -3.07 [-4.22; -1.92] | +0.02 [-0.83; +0.87] | -3.49 | +0.45 |
| exploiter | -17.24 [-18.89; -15.59] | -15.90 [-17.13; -14.66] | -17.50 | -14.69 |
| reading exploiter | -6.64 [-8.56; -4.71] | +0.22 [-1.07; +1.51] | -6.97 | **+1.66** |
| seller (unchanged) | -15.42 [-16.67; -14.17] | -10.25 [-11.32; -9.18] | -14.35 | -9.55 |
| gambler (unchanged) | -13.02 [-15.13; -10.92] | -12.77 [-14.23; -11.30] | -13.53 | -12.82 |

With 4 players, the timed v4c passes as in phase 5l. Its gap closest to 0, -$1.09 against the quiet v4c, now has an interval that goes 6 cents above 0. The rule only refuses gaps whose whole interval is above 0, so it passes, but by a smaller margin than in phase 5l.

With 5 players, one refusal is left. The reading exploiter goes from +$1.66 to +$0.22, with an interval that contains 0. The quiet v4c goes from +$2.46 to +$3.05. Its two intervals overlap widely: I cannot say the gap grew, only that it did not close.

Against the zoo, the numbers go up a little almost everywhere, most of all against the marginal bot (+$12.19 and +$12.40 per round, against +$9.74 and +$8.04). But the marginal bot changed too: its buy value is fixed, and I do not know whether the rise comes from the candidate or from its opponent. Against the two simulated Hard bots, which did not change, the gain is stable with 4 players and rises with 5, from +$31.86 to +$34.40 against the phase 5c Hard bot. The two tournaments are not paired with each other: they are two separate measurements on the same deals.

## Is the bot making progress?

Not in the sense of the entry rule: the timed v4c is still refused with 5 players, and the marginal bot stays the reference bot. It now has one reference against it instead of two, but its worst gap is a bit larger. This phase fixes mistakes and gives a sound starting point to phase 5n, which will keep the majority weight on the buying side only. That is where the quiet v4c's refusal is decided, since phase 5l's diagnostic showed the bot hands its goal cards over too early.

These gains are measured against simulated bots: they are not real gains on figgie.com.

## Limits

Phase 5j's recalibrated Hard bot still cancels both of its quotes in a suit at once. I did not change it, because it was calibrated on the real rounds with that behaviour. But the site allows cancelling one side, and the Hard bot is our filler at the mixed table.

The v3, v4 and v4b models were not retrained. They play with the fixed profile, on neighbours learned with the old one.

Almost every bot changed between 5l and 5m. The comparison between the two phases therefore mixes the effect of the fixes on the candidate and on its opponents.

The tournament is reduced like those of phases 5j to 5l: 100 deals instead of 300, and part of the references.

Everything is still measured against simulated bots. These gains are not real gains on figgie.com.

## Reproduce

```bash
cd projets/bot-figgie
python3 -m unittest                                                  # the 142 tests, about 7 s
python3 -m figgie.adapt --v4t sans --deals 40 --rounds 3 \
    --arms 6,3,6,3 8,1,8,1 10,3,10,3 12,3,12,3 8,1,3,1 12,3,4,1 --report entrainement_v4c.json
python3 -m figgie.adapt --v4t 120,0.5 --deals 40 --rounds 3 \
    --arms 6,3,6,3 8,1,8,1 10,3,10,3 12,3,12,3 8,1,3,1 12,3,4,1 --report entrainement_v4t.json
python3 -m figgie.tournoi --site --candidates v4c_temps --rounds 10 --deals 100 --no-tables \
    --opponents heuristique sniper bayesien marginal hard_simule hard_simule_v2 --references \
    --mixed hard_simule_v2 bayesien marginal adaptatif_v3 adaptatif_v4b adaptatif_v4c v4c_calme_60 v4c_vente_60 \
        exploiteur exploiteur_lecteur vendeur parieur --out tournoi.json
```

On 10 cores, retraining the v4c took 2 h 36 and rewrites `modeles/adaptation_v4c.json`. Retraining the timed v4c took 5 h 32 and rewrites `modeles/adaptation_v4t.json`. The tournament took 2 h 11. To get back exactly this phase's code: `git checkout phase5m-figgie`.
