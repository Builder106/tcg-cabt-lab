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
