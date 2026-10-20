# Roadmap

## 0. Research scaffold

Deliver a typed Python package, seeded random-choice selector, synthetic example, tests, locked development tools, CI, and the study draft. Completion requires clean type, lint, format, test, package-installation, dependency, and secret checks. The command must fail clearly for unsupported deck selection and malformed requests.

## 1. Reproduce CABT

Completed. Installed versioned environment `kaggle-environments==1.33.0` (CABT 1.0.0 engine) and verified platform binaries on Linux ARM64 (`libcg-arm64.so`), Linux x86_64, and macOS. Pinned the complete 1,431-card catalog (SHA-256: `7fd6c45fcdc2913a1fe19ddb67c01aa9b204718cb760be7582cf4fcc3513de9c`). Verified initial 60-card deck submission, optional choices, in-game selection contexts, invalid-action penalization, and terminal game outcomes. Enforced an observation-only agent boundary by sanitizing internal engine search states (`search_begin_input`) and opponent hidden cards, and implemented full-game battle execution with reproducible JSON logging.

## 2. Establish evaluation

Completed. Implemented transparent rule-based heuristic (`HeuristicAgent`) prioritizing attacks by damage and board development, alongside CABT's `first_agent` (`FirstAgent`) and random baseline (`RandomAgent`). Created 6 canonical elemental deck families with strict overlap checks (`verify_split_disjointness`) separating training (`water-kyogre`, `grass-bulbasaur`, `lightning-pikachu`), tuning (`fire-ponyta`), and held-out final test (`psychic-mewtwo`, `colorless-snorlax`). Implemented round-robin tournament engine with matched pairs, reversed player positions, failure accounting, and Wilson score 95% confidence intervals. Executed baseline pilot tournament across 24 games and froze the study configuration in `experiments/heldout-matchups.json`.

## 3. Run one ML experiment

Choose a compact representation from measured observation and action sizes. Establish a supervised baseline, then compare fixed versus diverse training opponent pools under equal budgets. Evaluate independent training runs on frozen held-out families. Completion requires results, uncertainty, a controlled ablation, and checkpoint provenance. Negative results remain valid research results and must be described accurately.

## 4. Build the public showcase

Build the tournament page, matchup grid, and match viewer described in [docs/showcase.md](docs/showcase.md). Start with stored, evaluated matches so the demo does not require a training service or expensive inference endpoint. Completion requires real run provenance, understandable decision displays, representative failures, usable keyboard controls, and a visual review before publication.

## 5. Competition packaging

If a suitable competition remains available, verify its current rules and package the agent for its exact runtime. Check cold start, inference time, memory, archive size, and entrypoint behavior. This milestone follows engine integration and does not imply that the current CLI can be submitted to Kaggle.
