# Phase 5o: searching for an exploiter of the "buying" v4c

*Version française : [phase5o.fr.md](phase5o.fr.md)*

In phase 5n, the "buying" v4c became the reference bot. It passes the entry rule, but that rule only tests opponents I wrote or borrowed. The automatic exploiter search had not run since phase 5b, against the v3, and back then it found, every time, an opponent that took $4 to $8 per round from the candidate. This phase runs it again against the new reference bot, on the site's market and at the entry rule's mixed table.

Result: the search finds no exploiter. With 4 players, the best of 60 settings ends $9.11 per round behind the "buying" v4c. With 5 players, the best one ties with it: -$0.36 per round, with an interval that contains 0. It is a cousin of the reading exploiter, which already tied in phase 5n. The promotion holds. These gaps are measured against simulated bots, not on the site.

## The change

The search, `figgie/exploit.py`, dates from phase 4. It played without the site rule, and it scored each setting alone against three copies of the target, that is with the minority test, which phase 5i replaced. It gets two options:
- `--site` plays with the site rule: a new offer must beat the one shown;
- `--filler` scores each setting at the mixed table. The score is then the gap between the setting's gain and the target's, sitting at the same table with recalibrated Hard bots, exactly as in the entry rule.

I also added the site reader to the possible value sources, next to the heuristic, the Bayesian and the marginal bot: on the site's market, an exploiter that reads the others' offers had a chance to do better. And the search now shows its progress, stage by stage, with the time left.

A single seam, written with TDD: with a filler, a setting's score is exactly `evaluate.mixed_gap` on the same deals, under the site rule. The test also checks that, on these deals, the site rule changes the gap: otherwise it could not see a forgotten rule. It failed before the code. I then checked that it catches two deliberate mistakes: forgetting the site rule, and keeping the old score instead of the mixed table. This test checks what the search measures, not the space it searches.

## The search

The same three stages as in phase 5b, each on its own deals so as not to keep a setting that was merely lucky:
1. 60 settings drawn at random, measured on 20 deals (seed 5);
2. the best 6, measured again on 100 other deals (seed 6);
3. the best of the 6, measured on the tournament's 300 deals (seed 1).

Games of 10 rounds, site rule, recalibrated Hard bots as fillers, with 4 then 5 players. A setting chooses its value source (heuristic, Bayesian, marginal or site reader), its spread ($1 to $12), its edge ($0 to $3), its reaction time (0.1 to 0.4 s), whether it quotes or only takes, and its pace. The 60 settings drawn are the same at both table sizes.

Gap setting minus "buying" v4c at the mixed table, in dollars per round. A gap whose whole interval is above 0 would be an exploiter.

With 4 players, stages 2 and 3:

| Setting | stage 2 (100 deals) | stage 3 (300 deals) |
|---|---|---|
| **marginal, spread 4, edge 1, reaction 0.4 s, pace 5 s** | **-8.50 [-10.28; -6.72]** | **-9.11 [-10.19; -8.04]** |
| site reader, spread 8, edge 2, reaction 0.4 s, pace 5 s | -11.55 [-12.79; -10.31] | |
| marginal, spread 6, edge 1, reaction 0.1 s, pace 5 s | -11.61 [-13.42; -9.80] | |
| marginal, spread 3, edge 2, reaction 0.2 s, pace 2 s | -12.04 [-13.73; -10.35] | |
| marginal, spread 8, edge 3, reaction 0.2 s, pace 5 s | -12.78 [-14.34; -11.23] | |
| site reader, spread 10, edge 3, reaction 0.3 s, pace 2 s | -14.19 [-15.34; -13.04] | |

With 5 players:

| Setting | stage 2 (100 deals) | stage 3 (300 deals) |
|---|---|---|
| **marginal, spread 3, edge 2, reaction 0.2 s, pace 2 s** | **+0.93 [-0.68; +2.54]** | **-0.36 [-1.27; +0.55]** |
| marginal, spread 4, edge 1, reaction 0.4 s, pace 5 s | -2.26 [-3.98; -0.54] | |
| marginal, spread 3, edge 3, reaction 0.15 s | -3.13 [-4.78; -1.47] | |
| marginal, spread 6, edge 1, reaction 0.1 s, pace 5 s | -5.25 [-7.01; -3.49] | |
| site reader, spread 8, edge 2, reaction 0.4 s, pace 5 s | -8.12 [-9.17; -7.07] | |
| marginal, spread 8, edge 3, reaction 0.2 s, pace 5 s | -8.30 [-9.65; -6.94] | |

All the settings, stage 1 included, are in `resultats/phase5o/`.

With 4 players, no setting comes close to the "buying" v4c. The best one ends $9 per round behind it, about like the reading exploiter in phase 5n's full tournament (-$10.10).

With 5 players, the best setting ties. It looks a lot like phase 4's reading exploiter: the marginal bot's value, a tight spread, a 0.2 s reaction and a 2 s pace (the reading exploiter quotes with a $4 spread and a $3 edge). So the search finds again the only weakness the tournament already showed: with 5 players, a marginal bot that quotes tight and fast holds its own against the "buying" v4c. It finds no other.

The site reader brings nothing. Its best setting ends at -$11.55 with 4 players and -$8.12 with 5. Reading the others' offers does not help it against this bot.

## Does the bot progress?

This phase has no new candidate: it tests the reference bot. It resists better than its predecessors. In phase 5b, with the old measure, the search found against each candidate an opponent that took $4 to $8 per round from it. Here, the best of 60 settings loses $9 per round with 4 players and ties with 5. The two measures are not the same, and I do not compare their numbers directly. The promotion of the "buying" v4c holds: the rule planned to withdraw it, a gap whose whole interval is above 0, is not met.

These gaps are measured against simulated bots: they are not real gains on figgie.com.

## Limits

The search tried only 60 of the 3,840 possible settings, drawn at random. A stronger setting may have slipped through.

The space only holds fixed-value bots of the common mechanics. An adaptive exploiter, or a bot that does something other than quote and take (stay quiet, lie, gather its cards), is not in it.

The fillers are always recalibrated Hard bots. An exploiter could win at other tables.

The setting that ties with 5 players does not join the mixed-table references: the plan only added it if it beat the target.

Since this phase, the space holds the site reader: the search commands of phases 4 and 5b now draw other settings. To get their numbers back, go back to their git tag.

The durations below exclude a 2 h 34 hibernation of the Mac during stage 3 with 4 players. It delayed the search without changing its result.

Everything is still measured against simulated bots. These gains are not real gains on figgie.com.

## Reproduce

```bash
cd projets/bot-figgie
python3 -m unittest                                                  # the 145 tests, about 7 s
python3 -m figgie.exploit --target v4c_achat --players 4 --rounds 10 --site --filler hard_simule_v2 \
    --candidates 60 --keep 6 --deals 20 100 300 --out recherche_4j.json
python3 -m figgie.exploit --target v4c_achat --players 5 --rounds 10 --site --filler hard_simule_v2 \
    --candidates 60 --keep 6 --deals 20 100 300 --out recherche_5j.json
```

On 10 cores, the search took about 1 h 20 with 4 players and 2 h 10 with 5. To get this phase's exact code back: `git checkout phase5o-figgie`.
