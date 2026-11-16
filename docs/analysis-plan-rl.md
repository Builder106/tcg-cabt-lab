# Analysis plan: learning from play

Status: frozen on 16 November 2026, before any game with the study's training seeds was played in this form. The machine-readable version is [`experiments/rl-pool.json`](../experiments/rl-pool.json), and the runner refuses any plan whose `status` is not `frozen`. Any later change goes in `JOURNAL.md` with its reason, and the report must say so.

## Why a third study

The first two studies ([analysis-plan.md](analysis-plan.md), [analysis-plan-board.md](analysis-plan-board.md)) copy a teacher. The opponent pool there only decides which game states the teacher visits. Both found the pools equivalent within ±5 points. That leaves open the case where the opponent is part of the learning signal: the policy plays its opponent, wins or loses, and learns from the result. This study tests that case.

## Question

When a compact policy learns from play, does the opponent pool it plays against change its win rate on held-out deck families?

## Method

`rl.py` trains the same 88 → 32 → 1 option-scoring network with REINFORCE:

- the policy samples each choice from the softmax of its option scores and plays a full game;
- the outcome is +1 for a win, 0 for a draw and -1 for a loss, and the baseline is the mean outcome of the batch of 8 games, so a batch where every game has the same outcome makes no update;
- the gradient is averaged over decisions, and Adam (learning rate 0.003) applies it;
- the learner takes a random seat, and a random training deck, in every game;
- evaluation is unchanged: greedy play on the held-out decks.

Both arms start from the same weights. Each checkpoint starts from the imitation checkpoint of the same seed from the board-teacher study (`experiments/board/checkpoints/fixed-opponent-pool-seed-<seed>.json`). Those checkpoints already carry held-out scores, so the change RL makes is measurable seed by seed. The pool is the only difference between the arms:

| Arm | Opponent in each training game |
| --- | --- |
| Fixed | `FirstAgent` |
| Diverse | `HeuristicAgent`, `FirstAgent` or `RandomAgent`, picked at random |

## Design

| Setting | Value |
| --- | --- |
| Training seeds per arm | 30 (2001 to 2030), the seeds of the board-teacher study |
| Training games per checkpoint | 400, in 50 updates of 8 games |
| Learning rate | 0.003 (chosen in the pilot below) |
| Training decks | Kyogre, Bulbasaur, Pikachu, for both seats |
| Held-out decks | Mewtwo, Snorlax (mirror matches) |
| Evaluation opponents | Heuristic, First, Random |
| Games per checkpoint | 120: 2 decks × 3 opponents × 5 evaluation seeds × 2 pairs, seats reversed within each pair |
| Baselines | Board, Heuristic, First and Random, each playing the same 120-game protocol |

## Pilot

The pilot used four seeds (3001 to 3004), excluded from the study, and measured win rate on the tuning deck `fire-ponyta` (never used for the held-out comparison). The reference scores on that deck, in 60 games each, are `BoardAgent` 93.3%, `FirstAgent` 70.0%, `RandomAgent` 41.7% and `HeuristicAgent` 25.0%.

From a random start (two seeds per arm, 400 games), the three learning rates scored a mean of 20.0% (0.003), 36.7% (0.01) and 56.7% (0.03). Only the 0.03 runs improved their training score from the first to the last quarter. The seed-to-seed spread was large, from 15% to 82% for one rate and arm. That start is too noisy for a 30-seed comparison with this budget, so the study starts from the imitation checkpoints.

From the imitation start (four seeds per arm, 400 games), the imitation checkpoints scored a mean of 67.9% on `fire-ponyta`. The change after RL, in points of win rate, was:

| Learning rate | Fixed pool | Diverse pool |
| --- | --- | --- |
| 0.001 | -2.1 | +2.9 |
| 0.003 | +11.7 | +5.0 |
| 0.01 | -2.9 | -0.8 |

The learning rate 0.003 is the only one with a clear gain, so it is the study's rate. At that rate the per-seed standard deviation of the score was about 11.7 points (fixed) and 8.3 (diverse) on 60 games. The held-out evaluation uses 120 games, so the study's spread should be smaller, but the two earlier studies had 4 to 5 points and this one is likely to be larger. At 8 points per arm, 30 seeds give a standard error of about 2.1 for the difference and a 90% half-width of about 3.5, which fits inside ±5 only if the true difference is near zero. These figures come from four seeds, so they are a rough guide, not a power analysis. If the interval is too wide to show equivalence, the result is reported as inconclusive.

## Primary analysis

The primary analysis is the same as in the earlier studies:

1. Score each checkpoint once, as the mean of its win rates on the two held-out decks. A draw counts as half a win.
2. Take the difference, diverse minus fixed.
3. Build a percentile cluster-bootstrap interval over training seeds: 10,000 resamples, bootstrap seed 20261116.
4. Read the result with these rules:
   - A difference is reported when the 95% interval excludes zero.
   - Equivalence is reported when the 90% interval lies inside ±5 percentage points.
   - Otherwise the result is inconclusive.

## Secondary analyses

These are descriptive only.

- The change from the starting checkpoint, seed by seed, using the held-out scores in `experiments/board/report.json`.
- The training score in the first and last quarter of the 400 games.
- Baselines with Wilson 95% intervals over games.
- Win rates by deck and by opponent.

## Limits stated in advance

- The budget is small: 400 games, about 24,000 decisions, against 2,000 for the imitation studies. A larger budget could change the result.
- Both arms start from a policy that imitated `BoardAgent` against `FirstAgent`. The result applies to fine-tuning from that start, not to learning from scratch.
- The learning rate was chosen on one deck with four seeds.
- The held-out decks are still simplified mirror matches.

## Running it

```sh
uv run tcg-cabt-lab experiment --config experiments/rl-pool.json
```

From the pilot's timings (about 10 to 13 minutes per checkpoint, four at a time) training should take about three hours, followed by about two hours of evaluation.
