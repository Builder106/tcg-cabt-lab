# Research plan

## First question

Does training against a diverse opponent pool improve a compact CABT policy's win rate on held-out deck families, under the same training and inference budgets?

This is an experimental hypothesis. A measured improvement and a comparison with prior work are required before claiming a contribution. The project covers 60-card TCG in CABT. Pocket and competitive video-game battles use different rules and belong to separate projects.

## Environment and information boundary

Use a pinned CABT distribution and record its package version, source revision when available, and card-catalog hash. The current scaffold only consumes the documented `select.option`, `minCount`, and `maxCount` fields. It has not run a CABT battle.

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
