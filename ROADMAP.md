# Roadmap

## 0. Research scaffold

Deliver a typed Python package, seeded random-choice selector, synthetic example, tests, locked development tools, CI, and the study draft. Completion requires clean type, lint, format, test, package-installation, dependency, and secret checks. The command must fail clearly for unsupported deck selection and malformed requests.

## 1. Reproduce CABT

Completed. Installed versioned environment `kaggle-environments==1.33.0` (CABT 1.0.0 engine) and verified platform binaries on Linux ARM64 (`libcg-arm64.so`), Linux x86_64, and macOS. Pinned the complete 1,431-card catalog (SHA-256: `7fd6c45fcdc2913a1fe19ddb67c01aa9b204718cb760be7582cf4fcc3513de9c`). Verified initial 60-card deck submission, optional choices, in-game selection contexts, invalid-action penalization, and terminal game outcomes. Enforced an observation-only agent boundary by sanitizing internal engine search states (`search_begin_input`) and opponent hidden cards, and implemented full-game battle execution with reproducible JSON logging.

## 2. Establish evaluation

Completed. Implemented transparent rule-based heuristic (`HeuristicAgent`) prioritizing attacks by damage and board development, alongside CABT's `first_agent` (`FirstAgent`) and random baseline (`RandomAgent`). Created 6 canonical elemental deck families with strict overlap checks (`verify_split_disjointness`) separating training (`water-kyogre`, `grass-bulbasaur`, `lightning-pikachu`), tuning (`fire-ponyta`), and held-out final test (`psychic-mewtwo`, `colorless-snorlax`). Implemented round-robin tournament engine with matched pairs, reversed player positions, failure accounting, and Wilson score 95% confidence intervals. Executed baseline pilot tournament across 24 games and froze the study configuration in `experiments/heldout-matchups.json`.

## 3. Run one ML experiment

Completed. Engineered an 88-dimensional compact representation (72-dim normalized game state, 16-dim candidate action vector with normalized attack damage, bench, energy, trainer, and targeting signals) verified at 0.0285 ms inference latency (<50 ms budget) and 1.8 KB footprint (<512 MiB budget). Established a supervised behavioral cloning baseline using a 2-layer option-scoring MLP (88 -> 32 -> 1, 2,881 parameters) with Adam optimization, proving validation loss reduction and >85% top-1 action prediction accuracy. Executed the controlled experiment comparing `fixed-opponent-pool` (FirstAgent) vs. `diverse-opponent-pool` (Heuristic, First, Random) across 3 independent training seeds (11, 29, 47) under identical training decks (water-kyogre, grass-bulbasaur, lightning-pikachu) and step budgets. Evaluated 6 checkpoints across 360 matched-pair games with reversed player assignments on frozen held-out test families (psychic-mewtwo, colorless-snorlax). The logged re-run observed a pooled held-out win rate of 58.33% (95% CI: [51.03%, 65.29%]) for fixed-opponent training and 57.78% (95% CI: [50.47%, 64.76%]) for diverse-opponent training, a delta of -0.55 points (95% CI: [-10.74, +9.64]); an earlier, unlogged run gave -3.88 points (95% CI: [-14.18, +6.42]). Recorded complete checkpoint provenance and ablation metrics in `experiments/ml-experiment-report.json`. Negative result confirmed: diverse opponent training did not yield a statistically significant improvement over fixed-opponent training on held-out deck families under equal sample budgets.

## 4. Build the public showcase

Built, not yet deployed. The static site in `web/` lays the 360 stored held-out games out as cards on a table that readers re-sort by training pool, deck, opponent, seat, ending, checkpoint, or the full matchup grid, and replays any game decision by decision. The replay keeps the information boundary: the AI's view shows only what the policy could see, and the spectator view marks every hidden card. Policy scores are shown as preferences, never as win chances, and no move is labelled a mistake. Keyboard stepping, turn jumps, deep links to any decision, and reduced-motion fallbacks are in place, and all artwork is original. Remaining before publication: a production domain, an independent visual and accessibility review of the final build, and deployment.

## 5. Competition packaging

If a suitable competition remains available, verify its current rules and package the agent for its exact runtime. Check cold start, inference time, memory, archive size, and entrypoint behavior. This milestone follows engine integration and does not imply that the current CLI can be submitted to Kaggle.
