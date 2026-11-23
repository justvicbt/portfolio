# Phase 5h: describe the table over several rounds

*Version française : [phase5h.fr.md](phase5h.fr.md)*

Phase 5g ended on a lead. The v4c asks its neighbours round by round, with the profile of a single round, and that profile does not recognise the exploiter's table. Averaging the profiles of the past rounds first, then asking the neighbours once, reduced what the exploiter takes from the copies on 100 diagnostic deals. This phase turns it into a v4d and puts it through the full tournament.

The v4d does not pass the entry rule. The exploiter takes a little less from it than from the v4c, and so does the v3, but not enough to pass the minority test, and it wins a little less against the marginal bot. It is not promoted, and the v4c remains my best bot.

## The v4d

The v4d changes only one line of the v4c: how it chooses the setting for the next round. The v4c takes each past profile, looks for its 5 nearest neighbours among the training tables, pools all these neighbours and picks the setting that paid them the most. The v4d averages the past profiles and looks for the 5 neighbours of that average profile. It takes its hand into account like the v4c, and it reuses the v4c's model as it is, without retraining.

The seam test checks, in real matches, that after a single round the v4d chooses exactly like the v4c: the average of a single profile is that profile. To make sure it can fail, I broke it on purpose by flipping the hand strength, and it failed. It does not see a mistake that would only show up from two profiles on.

## Before the tournament: three cells on 300 deals

Phase 5g had measured the v4d on 100 deals from seed 7. I measured it on 200 more deals, only on the cells that decide, in paired gaps with the v4c. Over the 300 deals:

| Gap v4d − v4c | 4 p. | 5 p. |
|---|---|---|
| exploiter alone | **-0.62** [-0.89 ; -0.35] | **-0.59** [-0.81 ; -0.36] |
| v3 alone | -0.37 [-0.84 ; +0.11] | -0.45 [-0.96 ; +0.06] |
| marginal alone | +0.06 [-0.47 ; +0.59] | -0.11 [-0.63 ; +0.41] |
| against the marginal bot | **-0.67** [-1.09 ; -0.26] | -0.23 [-0.61 ; +0.15] |

The 200 added deals go the same way as the first 100. What the exploiter takes drops by about $0.6 per round, and clearly so. In exchange, the v4d wins about $0.7 less against the marginal bot with 4 players. If I applied the threshold I had set for the quiet v4c in phase 5g, a lower bound above -$1 against the marginal bot, it would fail by 9 cents. That threshold was for deciding whether a variant deserved a full tournament. For the v4d, the tournament was part of the phase plan anyway.

## The references' refused orders

The phase 5g code review had found a flaw in two references. With the site rule, a new offer must beat the displayed one. The imitator and the fundamentalists drew their price without taking it into account. About half of their orders were refused, and each refusal cost them their turn.

They now beat the displayed offer by $1 when their drawn price is not enough, as long as it stays within their value. Otherwise they do nothing. Three tests check this on a hand-written book. In a check match, only 3 refusals out of 215 orders remain for the imitator and 3 out of 147 for the fundamentalist, all due to latency: the market moved between the moment they looked and the moment their order arrived.

So these references are a little stronger, and their phase 5g numbers are no longer comparable. I replayed the v4c against them on the same 300 deals. Gain of the reference alone against the copies, in dollars per round:

| Reference alone against the v4c | 4 p., phase 5g | 4 p., fixed | 5 p., phase 5g | 5 p., fixed |
|---|---|---|---|---|
| imitator | -27.13 | -25.56 [-26.59 ; -24.53] | -24.24 | -20.37 [-21.46 ; -19.29] |
| fundamentalist (r = 1.7) | -10.93 | -9.59 [-10.30 ; -8.88] | -6.88 | -5.47 [-6.12 ; -4.81] |
| fundamentalist (r = 3.5) | -14.63 | -13.73 [-14.44 ; -13.03] | -11.23 | -10.89 [-11.42 ; -10.37] |

They lose less than before, by $0.3 to $3.9 per round, but they still lose a lot. None of them exploits the v4c.

## The tournament

The tournament is the same as in phase 5f: the same 300 deals (seed 1), the site rule, 10-round matches. I added the v4c to the opponents, and all the references from phase 5g. The v4c has not changed since phase 5f, and the engine is deterministic, so I compare the v4d with the v4c's phase 5f numbers.

In the minority test, each number is the gain of the reference alone against the copies: the lower it is, the better my copies defend themselves.

| | v4c, 4 p. | v4d, 4 p. | v4c, 5 p. | v4d, 5 p. |
|---|---|---|---|---|
| against the marginal bot | +7.75 | +7.05 [+6.55 ; +7.54] | +4.59 | +4.39 [+3.93 ; +4.86] |
| against the v3 | -1.03 | -1.09 [-1.55 ; -0.62] | -0.02 | +0.12 [-0.30 ; +0.53] |
| against the v4b | +0.13 | -0.02 [-0.35 ; +0.31] | -0.09 | -0.19 [-0.52 ; +0.14] |
| against the v4c | | -0.12 [-0.44 ; +0.20] | | -0.12 [-0.42 ; +0.18] |
| exploiter alone | +3.15 | **+2.77** [+2.31 ; +3.23] | +4.65 | **+4.42** [+4.05 ; +4.78] |
| v3 alone | +0.94 | **+0.60** [+0.11 ; +1.09] | +2.46 | **+2.00** [+1.44 ; +2.55] |
| v4b alone | +0.16 | **+0.49** [+0.18 ; +0.81] | +0.32 | **+0.46** [+0.13 ; +0.79] |
| v4c alone | | +0.17 [-0.15 ; +0.48] | | +0.23 [-0.08 ; +0.54] |
| marginal alone | -0.80 | -0.76 [-1.28 ; -0.24] | +0.77 | +0.22 [-0.32 ; +0.75] |

In bold, the references that make money against copies of the v4d: the entry rule fails with 4 and with 5 players, because of the minority test. Without that test, it would pass, like the v4c.

Against the other bots of the zoo, the v4d does about as well as the v4c: within $1 per round against the simulated Hard, the heuristic, the sniper and the Bayesian bot. The six references found in phase 5g all lose against its copies, by $3 to $26 per round.

Compared with the v4c, the v4d has a mixed record. The exploiter takes $0.38 less from it with 4 players and $0.23 less with 5, the v3 $0.34 and $0.46 less, the marginal bot alone $0.55 less with 5 players. But the v4b takes a little more, by $0.14 to $0.33, and it wins $0.70 less against the marginal bot with 4 players. Head to head, neither beats the other: every interval touches 0.

These gaps need to be read with care. The tournament keeps only the means, not the deal-by-deal values, so I cannot compute paired gaps. The intervals shown are each bot's own, and those of the v4c and the v4d overlap in every cell. It is on seed 7, in paired gaps, that the effect on the exploiter is clear.

So the bot does not clearly progress. No bot is promoted, and the v4c remains the best. All these numbers are measured against simulated bots: they are not real gains.

## What I take from it

Looking at several rounds at once helps the copies recognise the exploiter's table a little, but only a little: it still takes $2.77 and $4.42 per round from them. The phase 5g diagnostic said that their neighbours came from about twenty different training tables. Averaging the profiles reduces the noise of a single round, but it does not create a training table that looks like the exploiter's.

For the cost against the marginal bot, I have a hypothesis that I have not checked: an average profile changes slowly, so the v4d would react more slowly than the v4c when the table changes its behaviour from one round to the next.

## Next

These two phases tried to improve how the copies choose their setting, and the exploiter keeps about the same gains. I think it is now time to change the lever, the second lead from phase 5f: how the bot sells its goal-suit cards, or fights for the majority. The exploiter wins by selling to the copies, and no spread or margin setting stops it. Another idea would be to add tables with an exploiter to the training tables, so that the neighbours recognise it. I will propose a plan before starting.

## Limits

The tournament does not keep deal-by-deal values: the comparison between the v4c and the v4d is not paired, and its intervals overlap. The paired diagnostic covers 300 deals from another seed, and only four cells.

The v4d reuses the v4c's model, learned on single-round profiles, and queries it with an average profile, which is more regular than a single-round profile. A model learned on average profiles might fit better, but it would need retraining.

The fixed references are no longer those of phase 5g. Their new numbers hold for both versions of the v4, but not for the phase 5g tables.

Everything is still measured against simulated bots. These gains are not real gains on figgie.com.

## Reproduce

```bash
cd projets/bot-figgie
python3 -m unittest                                                  # the 128 tests, about 5 s
python3 -m figgie.tournoi --site --candidates adaptatif_v4d --rounds 10 --deals 300 --no-tables \
    --opponents hard_simule heuristique sniper bayesien marginal adaptatif_v3 adaptatif_v4b adaptatif_v4c \
    --references hard_simule heuristique sniper bayesien marginal adaptatif_v3 adaptatif_v4b adaptatif_v4c \
        exploiteur exploiteur_lecteur imitateur fondamentaliste fondamentaliste_35 vendeur mante parieur \
    --out tournoi_site.json
python3 -m figgie.tournoi --site --candidates adaptatif_v4c --rounds 10 --deals 300 --no-tables \
    --opponents inactif --references imitateur fondamentaliste fondamentaliste_35 --out tournoi_v4c_references.json
```

The first tournament takes 3 h 30 on 10 cores, the second 1 h 15. To get back to the exact code of this phase: `git checkout phase5h-figgie`.
