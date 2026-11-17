# Analysis plan: learning from play, longer run

Status: frozen on 17 November 2026, before any game with the study's training seeds was played. The machine-readable version is [`experiments/rl-long.json`](../experiments/rl-long.json), and the runner refuses any plan whose `status` is not `frozen`. Any later change goes in `JOURNAL.md` with its reason, and the report must say so.

## Why a fourth study

The 400-game learning-from-play study ([analysis-plan-rl.md](analysis-plan-rl.md)) found the pools equivalent within ±5 points, but REINFORCE barely moved the policies from their imitation start (+0.6 and -1.0 points on average, training scores flat). So it said little about whether the opponent matters when the policy learns from play. This study gives learning more room: a budget of 2,000 games per checkpoint, five times larger, from random weights.

## Question

When a compact policy learns from play from random weights, does the opponent pool it plays against change its win rate on held-out deck families?

## Method

The method is that of [analysis-plan-rl.md](analysis-plan-rl.md): REINFORCE with a batch-mean baseline and Adam, a random seat and training deck in every game, and greedy play on the held-out decks at evaluation. Two settings change:

| Setting | 400-game study | This study |
| --- | --- | --- |
| Start | Imitation checkpoint of the same seed | Random weights from the training seed |
| Training games | 400 (50 updates) | 2,000 (250 updates) |
| Learning rate | 0.003 | 0.03 |
| Training seeds per arm | 2001 to 2030 | 4001 to 4030, new seeds |

Everything else is unchanged: 30 seeds per arm, decks, evaluation opponents, 120 games per checkpoint, and the same four baselines. The pool is the only difference between arms: always `FirstAgent` (fixed), or a random pick of `HeuristicAgent`, `FirstAgent` or `RandomAgent` per game (diverse).

## How the settings were chosen

Three pilots on the tuning deck `fire-ponyta` (never part of the held-out comparison) preceded the plan. Reference scores on that deck, in 60 games each: `BoardAgent` 93.3%, `FirstAgent` 70.0%, `RandomAgent` 41.7% and `HeuristicAgent` 25.0%.

1. **Warm start, 400 games** (4 seeds per arm, seeds 3001 to 3004): learning rate 0.003 gained 11.7 points (fixed) and 5.0 (diverse) over the imitation start. That gain did not carry over to the held-out decks in the 400-game study.
2. **Warm start, 800 games** (2 seeds per arm, seeds 3001 and 3002, scored in 120 tuning-deck games each). Before this pilot I fixed a rule: pick the rate with the largest rise in training score from the first to the last quarter, and use 0.01 if none gained 3 points. Over four checkpoints the rise was -1.75 (0.003), -0.4 (0.01) and -4.75 points (0.03), and the tuning-deck score changed by -4.2, -17.9 and -10.8 points against the starting checkpoints. No rate learned. REINFORCE does not improve a good imitation start at this budget, and larger steps hurt.
3. **From random weights, 400 games** (2 seeds per arm, seeds 3001 and 3002): only learning rate 0.03 raised training scores in all four runs (0.44 to 0.53, 0.35 to 0.51, 0.47 to 0.52 and 0.51 to 0.63, first to last quarter). The mean tuning-deck score was 20.0% (0.003), 36.7% (0.01) and 56.7% (0.03). The spread between seeds was very large: one diverse-pool run scored 15% and another 82%.

The fallback rule would have run the warm start at 0.01, the worst rate on the tuning deck. I changed the design after seeing the pilot results and before any study game, to a start from random weights at 0.03, the only setting in which training scores rose. Pilots 2 and 3 used few seeds, so the choice rests on little evidence.

## Primary analysis

The primary analysis is the same as in the earlier studies:

1. Score each checkpoint once, as the mean of its win rates on the two held-out decks. A draw counts as half a win.
2. Take the difference, diverse minus fixed.
3. Build a percentile cluster-bootstrap interval over training seeds: 10,000 resamples, bootstrap seed 20261117.
4. Read the result with these rules:
   - A difference is reported when the 95% interval excludes zero.
   - Equivalence is reported when the 90% interval lies inside ±5 percentage points.
   - Otherwise the result is inconclusive.

## Sizing and the expected outcome

I cannot size this study well. The imitation studies had a seed-to-seed standard deviation of 4 to 5 points. Learning from random weights varied far more in the pilot (15% to 82% on one rate and arm, in 60 games). If the spread across seeds is near 15 points, 30 seeds per arm give a standard error near 3.9 for the difference, and the 90% interval would be about ±6.4 points wide, which cannot fit inside ±5 whatever the true difference. In that case the study can still report a difference larger than about 8 points, and otherwise reports inconclusive. The margin is kept at ±5 for consistency with the earlier studies and was not adjusted to the pilot.

## Secondary analyses

These are descriptive only.

- The training score in the first and last quarter of the 2,000 games, per checkpoint, as a check that the policies learned.
- A comparison with the imitation students of the board-teacher study.
- Baselines with Wilson 95% intervals over games.
- Win rates by deck and by opponent.

## Limits stated in advance

- The budget is 2,000 games, about 120,000 decisions. Kaggle entries used millions of games.
- The learning rate and start were chosen on tuning-deck pilots with two to four seeds.
- The held-out decks are still simplified mirror matches, and the evaluation opponents are the three agent types that make up the diverse pool.
- The policy has 2,881 parameters and no memory.

## Running it

```sh
uv run tcg-cabt-lab experiment --config experiments/rl-long.json
```

From the pilot's timings (about 1.1 seconds per game per worker with four workers), training should take about nine hours and evaluation about two. Heavy load on the shared VM could stretch that to more than twice as long.
