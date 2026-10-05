# Roadmap

## 0. Research scaffold

Deliver a typed Python package, seeded random-choice selector, synthetic example, tests, locked development tools, CI, and the study draft. Completion requires clean type, lint, format, test, package-installation, dependency, and secret checks. The command must fail clearly for unsupported deck selection and malformed requests.

## 1. Reproduce CABT

Install a versioned environment, check its platform support and distribution terms, obtain a permitted valid deck, and run a complete random-agent battle. Record the engine version and card catalog. Check initial deck selection, optional choices, special selection contexts, end-of-game behavior, and invalid-action reporting. Completion requires reproducible full-game logs and an observation-only agent boundary.

## 2. Establish evaluation

Implement a transparent heuristic and reproduce an accessible stronger reference. Create deck-family manifests for training, tuning, and final test, with overlap checks. Run a pilot to choose matched game counts, inference limits, failure scoring, and confidence intervals. Completion requires a frozen study configuration and a replayable baseline tournament with no silently excluded failures.

## 3. Run one ML experiment

Choose a compact representation from measured observation and action sizes. Establish a supervised baseline, then compare fixed versus diverse training opponent pools under equal budgets. Evaluate independent training runs on frozen held-out families. Completion requires results, uncertainty, a controlled ablation, and checkpoint provenance. Negative results remain valid research results and must be described accurately.

## 4. Build the public showcase

Build the tournament page, matchup grid, and match viewer described in [docs/showcase.md](docs/showcase.md). Start with stored, evaluated matches so the demo does not require a training service or expensive inference endpoint. Completion requires real run provenance, understandable decision displays, representative failures, usable keyboard controls, and a visual review before publication.

## 5. Competition packaging

If a suitable competition remains available, verify its current rules and package the agent for its exact runtime. Check cold start, inference time, memory, archive size, and entrypoint behavior. This milestone follows engine integration and does not imply that the current CLI can be submitted to Kaggle.
