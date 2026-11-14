# Analysis plan: scaled opponent-pool study

Status: frozen on 14 November 2026, before any game in this study was played. The machine-readable version is [`experiments/opponent-pool-scaled.json`](../experiments/opponent-pool-scaled.json), and the runner refuses any plan whose `status` is not `frozen`. Any later change goes in `JOURNAL.md` with its reason, and the report must say so.

## Question

Does collecting the teacher's demonstrations against a diverse opponent pool change a cloned policy's win rate on held-out deck families?

The policy learns by behavioral cloning of `HeuristicAgent`. The opponent pool only decides which opponents the teacher faces while its decisions are recorded: always `FirstAgent` in the fixed arm, and a random pick of `HeuristicAgent`, `FirstAgent` or `RandomAgent` in the diverse arm. The study measures whether that change in the training states changes held-out play. It does not test learning from play against those opponents.

## Design

| Setting | Value | Change from the 14 November run |
| --- | --- | --- |
| Training seeds per arm | 30 (1001 to 1030) | Was 3 (11, 29, 47). New seeds, so no checkpoint is reused. |
| Training steps | 400 | Unchanged. Validation accuracy already reaches 99.75% to 100% at 400 steps, so the 100,000 steps in `experiments/heldout-matchups.json` are dropped. |
| Decisions per checkpoint | 2,000 (1,600 train, 400 validation) | Unchanged |
| Training decks | Kyogre, Bulbasaur, Pikachu | Unchanged; the teacher now plays all three (fixed on 14 November) |
| Held-out decks | Mewtwo, Snorlax (mirror matches) | Unchanged |
| Evaluation opponents | Heuristic, First, Random | Unchanged |
| Games per checkpoint | 120: 2 decks × 3 opponents × 5 evaluation seeds × 2 pairs, seats reversed within each pair | Was 60 |
| Baselines | Heuristic (the teacher), First and Random, each playing the same 120-game protocol | New |
| Replays | Not stored; every game gets a row in the report | The 14 November run stored replays for the showcase |

The CABT engine shuffles with `std::random_device`, so games cannot be replayed from a seed. The per-game rows in the report are the record.

## Primary analysis

1. Score each checkpoint once: the mean of its win rates on the two held-out decks, each deck weighted equally. A draw counts as half a win.
2. Take the difference in mean checkpoint score, diverse minus fixed.
3. Build the interval with a cluster bootstrap. It resamples training seeds within each arm, with 10,000 resamples and bootstrap seed 20261114. Treating the seed as the unit accounts for the games one checkpoint plays sharing its weights, and for the seat-reversed pairs inside each checkpoint's score.
4. Read the result with these rules, fixed in advance:
   - A difference is reported when the 95% interval excludes zero.
   - Equivalence is reported when the 90% interval lies inside ±5 percentage points. This is the bootstrap form of two one-sided tests at the 5% level.
   - Otherwise the result is inconclusive.

The ±5 point margin was chosen before this study produced any data. It is less than half the 12-point gap between the two held-out decks in the 14 November run.

`tcg-cabt-lab analyze <report>` applies the same analysis to any experiment report. On the 14 November run (3 seeds per arm) it gives a delta of +6.94 points with a 95% interval of [-5.56, +18.33]. With three seeds the bootstrap has very few distinct resamples, so that interval is rough.

## Sizing

The 14 November run gives per-seed standard deviations of 0.036 (fixed) and 0.121 (diverse) at 60 games per checkpoint. Taken at face value, 30 seeds per arm give a standard error of about 0.023 for the difference. That puts the half-width of the 90% interval near 3.8 points and the 95% interval near 4.5 points. Those deviations come from three seeds each, so the figures are a rough guide, not a power analysis. Doubling the games per checkpoint lowers the game-to-game part of the noise. Equivalence within ±5 points can be shown only if the true difference is close to zero. If the +6.9 point gap from the small runs is real, the study should detect it instead.

## Secondary analyses

These are descriptive and carry no hypothesis tests.

- Teacher agreement: for each checkpoint, the share of held-out decisions with more than one option where the student's first choice matches what `HeuristicAgent` would choose. It tests the likely explanation for similar arms, that both students copy the same teacher.
- Baselines: the teacher, `FirstAgent` and `RandomAgent` under the same protocol, with Wilson 95% intervals over games.
- Win rates by deck and by opponent.

## Running it

After freezing the plan:

```sh
uv run tcg-cabt-lab experiment --config experiments/opponent-pool-scaled.json
```

The output goes to `experiments/scaled/`, which leaves the showcase's run of record in `experiments/` untouched. From the 14 November run's timings (40 to 50 seconds of training per checkpoint, about 1.15 seconds per game), the run should take about three hours.
