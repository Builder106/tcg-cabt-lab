# Research plan

## First question

Does training against a diverse opponent pool improve a compact CABT policy's win rate on held-out deck families, under the same training and inference budgets?

**Empirical Result (Milestone 3)**:
The hypothesis is **not supported**. In a controlled study comparing a 2-layer option-scoring MLP policy (88 input features -> 32 hidden units -> 1 logit, 2,881 parameters) across 3 independent training seeds (11, 29, 47) and evaluated across 360 matched-pair games with reversed player assignments on frozen held-out test families (`psychic-mewtwo` and `colorless-snorlax`):
- `fixed-opponent-pool` (teacher demonstrations collected against greedy `FirstAgent`): mean win rate 55.83% (std 0.030), pooled 55.83% (Wilson 95% CI: [48.53%, 62.89%]).
- `diverse-opponent-pool` (teacher demonstrations collected against `HeuristicAgent`, `FirstAgent`, `RandomAgent`): mean win rate 62.78% (std 0.099), pooled 62.78% (Wilson 95% CI: [55.52%, 69.50%]).
- **Delta (Diverse - Fixed)**: +6.95 points (95% CI: [-3.17, +17.07]).

Zero is inside the interval, so diverse opponent training did not measurably change held-out performance under an equal sample budget. The interval treats every game as independent and ignores clustering within the three training seeds, so the real uncertainty is wider. Pooled over both pools, Snorlax games scored 65.3% and Mewtwo games 53.3%. The diverse pool scored higher on both decks (Mewtwo: diverse 54.4%, fixed 52.2%; Snorlax: diverse 71.1%, fixed 59.4%). Against the `HeuristicAgent` teacher, the fixed pool scored 53.3% and the diverse pool 60.8%. The spread between training seeds (50.0% to 74.2%) is wider than the gap between pools.

These figures come from the run of 14 November 2026, which stores every game and its replay. It is the first run after a fix: until then the teacher always played the `water-kyogre` deck while its decisions were recorded, so Bulbasaur and Pikachu reached only the opponent. The two earlier runs used that code. The logged run of 21 October 2026 reported -0.55 points (95% CI: [-10.74, +9.64]), and an unlogged run before it reported -3.88 points (95% CI: [-14.18, +6.42]). All three runs find no significant effect, and the sign of the delta changed between them, which is what three seeds per arm allow. Training stopped at 400 of the 100,000 planned gradient steps. The full report is `experiments/ml-experiment-report.json`.

A seed-level reanalysis treats each training seed as one observation, with a cluster bootstrap over seeds (`tcg-cabt-lab analyze experiments/ml-experiment-report.json --seed 20261114`). It gives a delta of +6.94 points with a 95% interval of [-5.56, +18.33]. With three seeds per arm the bootstrap is coarse. The scaled follow-up study is specified in [docs/analysis-plan.md](docs/analysis-plan.md).

**Scaled study (14 November 2026, plan frozen before the run)**:
30 new training seeds per arm (1001 to 1030), 120 held-out games per checkpoint, 7,200 games in total. The unit of analysis is the training seed, and the interval is a cluster bootstrap over seeds. Report: `experiments/scaled/report.json`.
- Mean checkpoint score, fixed pool: 56.03% (std 5.42 points across seeds). Diverse pool: 54.81% (std 4.91).
- Delta (diverse minus fixed): -1.22 points, 95% interval [-3.78, +1.33]. The interval includes zero, so no difference is reported.
- The 90% interval is [-3.40, +0.90], inside the preregistered margin of plus or minus 5 points, so the arms are reported as equivalent within that margin.
- The +6.95 points seen in the 3-seed rerun was not reproduced. With 3 seeds per arm the seed-to-seed spread (about 5 points per arm here) is as large as that gap.
- Teacher agreement: on held-out decisions with more than one option, the student's first choice matched the `HeuristicAgent` teacher in 99.92% to 100% of decisions for the fixed pool and 99.80% to 100% for the diverse pool (per-checkpoint range). Both arms are near-exact copies of the teacher, which is the likely reason the demonstration opponent does not change play.
- Baselines under the same protocol (120 games each, Wilson 95%): teacher 56.67% [47.73, 65.19], `FirstAgent` 39.58% [31.29, 48.53], `RandomAgent` 41.67% [33.24, 50.61]. Both student arms score about the same as their teacher, and above the two simpler agents.
- Training decks and held-out decks are unchanged from the 14 November rerun, so deck effects carry over: Snorlax 63.7% and 63.1%, Mewtwo 48.3% and 46.5% (fixed, diverse).

**Board-teacher study (15 November 2026, plan frozen before the run)**:
A review of the code showed that the study above could not find an effect: `HeuristicAgent` scores options by type and damage alone, the student's features hold those inputs, and so any demonstrations teach the whole rule. The follow-up changes only the teacher, to `BoardAgent`, whose choices depend on HP, energy, bench size and knockout chances. It uses 30 new seeds per arm (2001 to 2030) and the same budget, decks and protocol. The plan is [docs/analysis-plan-board.md](docs/analysis-plan-board.md), and the report is `experiments/board/report.json`.
- Mean checkpoint score, fixed pool: 65.18% (std 3.75 points across seeds). Diverse pool: 66.58% (std 4.70).
- Delta (diverse minus fixed): +1.40 points, 95% interval [-0.67, +3.58]. The interval includes zero, so no difference is reported.
- The 90% interval is [-0.33, +3.21], inside the preregistered margin of plus or minus 5 points, so the arms are reported as equivalent within that margin.
- Teacher agreement: on held-out decisions with more than one option, the students' first choice matched `BoardAgent` on 52% to 69% of decisions (fixed mean 60.8%, diverse 61.8%). The students no longer copy the teacher, yet the demonstration opponent still does not move their play.
- Baselines under the same protocol (120 games each, Wilson 95%): `BoardAgent` 74.58% [66.11, 81.53], `HeuristicAgent` 58.33% [49.39, 66.76], `FirstAgent` 52.08% [43.22, 60.82], `RandomAgent` 53.75% [44.85, 62.42]. Both student arms sit between the teacher and the other three agents. The teacher is 8 to 9 points stronger than either student arm.
- Deck effects: Snorlax 80.4% and 81.4%, Mewtwo 49.9% and 51.7% (fixed, diverse). Both are mirror matches on simplified decks (see the limits in [docs/paper-readiness.md](docs/paper-readiness.md)).
- Note: this study also uses the corrected bench flag in the feature encoder (JOURNAL, 15 November), so its students are not directly comparable with the earlier checkpoints.

**Learning-from-play study (16 November 2026, plan frozen before the run)**:
The policy plays its opponent pool and learns from win, draw or loss (REINFORCE, 400 games, 50 updates, learning rate 0.003). Each checkpoint starts from the imitation checkpoint of the same seed in the board-teacher study, so both arms share a start and the pool is the only difference. It uses the same 30 seeds (2001 to 2030) and protocol. The plan is [docs/analysis-plan-rl.md](docs/analysis-plan-rl.md), and the report is `experiments/rl/report.json`.
- Mean checkpoint score, fixed pool: 65.76% (std 3.84 points across seeds). Diverse pool: 64.17% (std 4.87).
- Delta (diverse minus fixed): -1.60 points, 95% interval [-3.69, +0.61]. The interval includes zero, so no difference is reported.
- The 90% interval is [-3.40, +0.25], inside the preregistered margin of plus or minus 5 points, so the arms are reported as equivalent within that margin.
- RL changed little. The starting checkpoints averaged 65.18%. Per-seed change after RL: +0.6 points (fixed, 17 of 30 seeds up) and -1.0 (diverse, 11 of 30 up), with a standard deviation of 5.1 and 5.9 points. A 120-game score alone has a standard error near 4.5 points, so the per-seed changes are about what evaluation noise produces. The mean training score did not rise either: 58.0% to 57.9% (fixed) and 69.4% to 69.7% (diverse), first to last quarter. The two pools' training scores differ because the opponents differ.
- So the equivalence here is weak evidence about the pool. Both arms barely left the shared start, and a 400-game budget may be too small for RL to matter. The result supports "no effect at this budget", not "no effect".
- The pilot's gain did not carry over. On the tuning deck, with four seeds and 60 games per checkpoint, learning rate 0.003 gained +11.7 and +5.0 points. On the held-out decks, with 30 seeds and 120 games, the gain is about zero. The pilot was too small to select a rate reliably.
- Baselines under the same protocol (120 games each, Wilson 95%): `BoardAgent` 75.00% [66.56, 81.89], `HeuristicAgent` 57.08% [48.14, 65.58], `FirstAgent` 45.42% [36.79, 54.33], `RandomAgent` 50.42% [41.60, 59.21]. These differ from the board-teacher study's baselines by up to 8 points for the same agents (for example `FirstAgent` 52.08%), which shows how noisy 120 games are.
- Deck effects: Snorlax 81.0% and 78.6%, Mewtwo 50.5% and 49.7% (fixed, diverse).

**Long learning-from-play study (17 November 2026, plan frozen before the run)**:
The policy starts from random weights, plays its pool for 2,000 games (250 updates, learning rate 0.03) and learns from win, draw or loss. It uses 30 new seeds per arm (4001 to 4030) and the same decks, evaluation and baselines as the studies above. The plan is [docs/analysis-plan-rl-long.md](docs/analysis-plan-rl-long.md), and the report is `experiments/rl-long/report.json`. It followed a pilot in which no learning rate improved the imitation start, and the plan records that the design changed after the pilot and before any study game.
- Mean checkpoint score, fixed pool: 53.92% (std 10.84 points across seeds). Diverse pool: 54.07% (std 10.58).
- Delta (diverse minus fixed): +0.15 points, 95% interval [-5.04, +5.29]. The interval includes zero, so no difference is reported.
- The 90% interval is [-4.29, +4.51], inside the preregistered margin of plus or minus 5 points, so the arms are reported as equivalent within that margin. It fits with little room: the 95% interval leaves the margin on both sides.
- The policies learned. The mean training score rose from 44.7% to 49.9% (fixed) and from 54.5% to 63.2% (diverse), first to last quarter of the 2,000 games, and rose in 25 of 30 seeds in each arm. The two pools' training scores differ because the opponents differ.
- Learned policies are weaker than imitation students. Held-out scores of 53.9% and 54.1% compare with 65.2% and 66.6% for the board-teacher imitation students, and sit near `HeuristicAgent`.
- Baselines under the same protocol (120 games each, Wilson 95%): `BoardAgent` 70.42% [61.72, 77.85], `HeuristicAgent` 53.75% [44.85, 62.42], `FirstAgent` 49.17% [40.39, 58.00], `RandomAgent` 44.17% [35.60, 53.10].
- Exploratory, not preregistered: by deck, the fixed arm scores 54.3% on Mewtwo and 53.6% on Snorlax, and the diverse arm 47.8% and 60.3%. The diverse-minus-fixed gaps are -6.4 points on Mewtwo (95% interval [-13.9, +1.2]) and +6.8 on Snorlax ([-2.2, +15.7]), with opposite signs and both intervals including zero. They cancel in the primary score. Whether the pool changes which deck a learned policy plays better would need a study built to test it.

## Environment and information boundary

Use a pinned CABT distribution and record its package version, source revision when available, and card-catalog hash. The project integrates `kaggle-environments==1.33.0` with the 1,431-card catalog pinned at SHA-256 `7fd6c45fcdc2913a1fe19ddb67c01aa9b204718cb760be7582cf4fcc3513de9c`. Environment simulation runs on native Linux ARM64, Linux x86_64, and macOS binaries. Note that while agent decision policies accept deterministic seeds, the engine's internal state transitions (deck shuffles, coin flips, prize cards) are initialized via `std::random_device`.

Agent inputs must contain only the observations available at decision time. Do not expose hidden opponent cards, future events, or evaluator-only state to a learned policy. Keep spectator views and training inputs separate. Verify deck selection and special choice contexts against the engine before evaluating full games.

## Baselines and first experiment

Start by integrating the documented random baseline and a transparent heuristic. Reproduce a stronger open reference if its code, environment, and terms permit a faithful comparison. Do not treat a placement or writeup as a reproduced result.

Choose a compact policy representation after inspecting real observation sizes and branching. A supervised baseline can establish whether the representation learns useful action preferences before adding self-play. The first controlled experiment then changes the training opponent pool while keeping architecture, training decks, step budget, and inference budget fixed. All variants train from independent seeds.

The draft settings are in [experiments/heldout-matchups.json](experiments/heldout-matchups.json). Null values represent unresolved experimental choices. The file is not executed or validated by the current CLI. Fill and review the environment pins, split manifests, opponent checkpoints, seeds, sample sizes, and budgets before launching the study.

## Evaluation

Separate training, tuning, and final-test deck families. Group closely related card lists into the same family so minor deck edits cannot leak across splits. Freeze the final-test manifest before tuning. Record deck hashes, family labels, opponent checkpoint hashes, simulator version, and evaluation seeds for each run.

Evaluate matched deck pairs and seeds with player assignments reversed. Verify how the pinned engine controls starting player and random streams; reversing assignments alone must not be called a control for both. Keep crashes, timeouts, rejected actions, ties, and completed losses as distinct outcomes. Declare their contribution to the score before evaluation and never drop failures silently.

The primary result is the difference in held-out win rate between training variants. Report equally weighted deck-family results, a matchup grid, and uncertainty across independent training runs. Choose the sample size and confidence-interval method after a pilot and freeze them before final evaluation. Account for paired games and matchup clustering rather than treating every turn or repeated rollout as independent.

Report performance against the strongest reproduced reference separately. Record inference time, peak memory, and package size on a named platform. Any improvement claim needs a confidence interval supporting the claim and an ablation that identifies what changed. The initial three training seeds are a pilot plan, not evidence that a final study has enough power.

## Data and release policy

Use a documented, permitted source for each dataset and reference policy. Record provenance, access date, version, license, split membership, and release restrictions. Check CABT and Kaggle terms before publishing deck data, traces, competition-derived weights, or card assets. MIT covers this project's original code only.

Keep downloaded datasets, deck CSVs, raw matches, and checkpoints in ignored storage. Publish small result summaries and permitted synthetic fixtures with reproduction instructions. Every selected public replay must identify its run and checkpoint; include representative losses as well as wins.

## Prior work to compare

- [CABT engine documentation](https://matsuoinstitute.github.io/cabt/) documents the observation and choice interface and a random agent.
- [Kaggle's CABT environment](https://github.com/Kaggle/kaggle-environments/tree/master/kaggle_environments/envs/cabt) is the first integration target. Record an exact version before use.
- [Pokemon TCG AI Battle evaluation](https://www.kaggle.com/competitions/pokemon-tcg-ai-battle/overview/evaluation) and [rules](https://www.kaggle.com/competitions/pokemon-tcg-ai-battle/rules) govern the competition path. Verify current runtime and distribution requirements before packaging a submission.
- [20th place: Learning to Play Pokemon TCG](https://www.kaggle.com/competitions/pokemon-tcg-ai-battle/writeups/20th-place-learning-to-play-pokmon-tcg) is a reference for existing learned-agent work. Compare accessible implementations rather than claiming novelty from a new repository name.
- [PTCG-Bench](https://arxiv.org/abs/2605.29653) studies LLM gameplay and self-evolution. Inspect its implementation and scope before defining how this resource-bounded policy study differs.

Sources inspected on 2026-10-04. Competition constraints and engine behavior still need an executable verification milestone.

## Verification tiers

The scaffold checks selection-index bounds, reproducibility, malformed input, and the CLI process boundary through installation from a wheel. Simulator integration adds full-game and special-selection-context checks. Training adds observation-leakage and split-disjointness checks. Evaluation adds paired-outcome and failure-accounting tests. A browser demo adds interaction tests. Add performance gates after a measured workload and ceiling exist.
