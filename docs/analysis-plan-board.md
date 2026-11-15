# Analysis plan: board-reading teacher

Status: frozen on 15 November 2026, before any game with the study's training seeds was played. The machine-readable version is [`experiments/board-teacher.json`](../experiments/board-teacher.json), and the runner refuses any plan whose `status` is not `frozen`. Any later change goes in `JOURNAL.md` with its reason, and the report must say so.

## Why a second study

The first scaled study ([analysis-plan.md](analysis-plan.md)) found the two arms equivalent within ±5 points. The novelty search ([paper/novelty-search.md](paper/novelty-search.md)) then showed that this result was fixed by the design. `HeuristicAgent` scores each option by its type and attack damage alone and never reads the board. The student's features include every one of those inputs, so any training set teaches the whole rule, and the demonstration opponent cannot matter. The students matched that teacher on at least 99.8% of held-out decisions.

This study changes only the teacher. `BoardAgent` ([board.py](../src/tcg_cabt_lab/board.py)) reads the board:

- it takes a knockout when one is on offer;
- it evolves, and keeps two Pokémon on the bench;
- it attaches energy where that brings an attack closest;
- it retreats an Active that cannot attack, or that the opponent can knock out next turn;
- it handles switch-ins, searches and discards by board value.

It uses only its own observation and the public card catalog.

## Question

When the teacher's choices depend on the board, does collecting its demonstrations against a diverse opponent pool change a cloned policy's win rate on held-out deck families?

## Design

| Setting | Value | Change from the first scaled study |
| --- | --- | --- |
| Teacher | `BoardAgent` | Was `HeuristicAgent` |
| Training seeds per arm | 30 (2001 to 2030) | New seeds |
| Training steps | 400 | Unchanged |
| Decisions per checkpoint | 2,000 (1,600 train, 400 validation) | Unchanged |
| Training decks | Kyogre, Bulbasaur, Pikachu | Unchanged |
| Held-out decks | Mewtwo, Snorlax (mirror matches) | Unchanged |
| Opponent pool while recording | Fixed: `FirstAgent`. Diverse: `HeuristicAgent`, `FirstAgent` or `RandomAgent`, picked at random per game | Unchanged |
| Evaluation opponents | Heuristic, First, Random | Unchanged |
| Games per checkpoint | 120: 2 decks × 3 opponents × 5 evaluation seeds × 2 pairs, seats reversed within each pair | Unchanged |
| Baselines | Board (the teacher), Heuristic, First and Random, each playing the same 120-game protocol | Board added |
| Student features | 88 inputs; the bench-target flag now fires for CABT area 5 | The flag was never set before (see `JOURNAL.md`, 15 November) |

The student's architecture, training budget and features are otherwise identical. The CABT engine shuffles with `std::random_device`, so games cannot be replayed from a seed. The per-game rows in the report are the record.

## Primary analysis

The primary analysis is the same as in the first study:

1. Score each checkpoint once, as the mean of its win rates on the two held-out decks. A draw counts as half a win.
2. Take the difference, diverse minus fixed.
3. Build a percentile cluster-bootstrap interval over training seeds: 10,000 resamples, bootstrap seed 20261115.
4. Read the result with these rules:
   - A difference is reported when the 95% interval excludes zero.
   - Equivalence is reported when the 90% interval lies inside ±5 percentage points.
   - Otherwise the result is inconclusive.

## Pilot and sizing

The pilot used seeds 901 to 903 per arm. They are excluded from this study, and their results are not part of it. The pilot gave the following:

- Validation accuracy against the teacher: 72.5% to 77.5%, against 99.75% to 100% for `HeuristicAgent`.
- Agreement with the teacher on held-out decisions: 52% to 67% of decisions with more than one option.
- Held-out win rates per checkpoint: 56.7% to 69.2% (fixed) and 65.0% to 70.8% (diverse).
- The teacher scored 66.7% under the same protocol in a separate 120-game check.

Taken at face value, the pilot's per-seed standard deviations (about 7.1 points fixed, 3.0 diverse) give a standard error near 1.4 points for the difference at 30 seeds per arm. That puts the 90% half-width near 2.3 points. They come from three seeds each, so this is a rough guide, not a power analysis.

## Secondary analyses

These are descriptive only.

- Teacher agreement per checkpoint, against `BoardAgent`.
- Baselines with Wilson 95% intervals over games.
- Win rates by deck and by opponent.

## Running it

```sh
uv run tcg-cabt-lab experiment --config experiments/board-teacher.json
```

From the pilot's timings (about 30 to 35 seconds of training per checkpoint and about 1 second per game), the run should take about three hours.
