# TCG CABT Lab

[![CI](https://github.com/Builder106/tcg-cabt-lab/actions/workflows/ci.yml/badge.svg)](https://github.com/Builder106/tcg-cabt-lab/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](#license)

TCG CABT Lab is a research project about compact agents for the 60-card Pokemon Trading Card Game. The first planned study asks whether training against varied opponents improves performance on deck families the agent has never trained on.

## Project status

The project integrates the CABT 1.0.0 simulation engine (`kaggle-environments==1.33.0`) with verified platform binaries on Linux ARM64, Linux x86_64, and macOS. The card catalog (1,431 cards) and attack catalog (1,755 attacks) are pinned and checksum-verified. The evaluation framework provides 6 canonical elemental deck families with verified split disjointness across training, tuning, and held-out test splits, alongside reference agents (`RandomAgent`, `FirstAgent`, `HeuristicAgent`).

The first controlled ML study (Milestone 3) is complete. It evaluates an 88-dimensional compact option-scoring MLP policy ($88 \to 32 \to 1$, 2,881 parameters) with He-normal initialization and Adam optimization. Resource benchmarks confirm 0.0285 ms inference latency (<50 ms budget) and 1.8 KB footprint (<512 MiB budget). Checkpoints trained under `fixed-opponent-pool` vs. `diverse-opponent-pool` were evaluated across 360 matched-pair games with reversed seating on frozen held-out test families (`psychic-mewtwo`, `colorless-snorlax`). In the logged re-run, pooled win rates were 58.33% (95% CI: [51.03%, 65.29%]) for fixed-opponent training and 57.78% (95% CI: [50.47%, 64.76%]) for diverse-opponent training (delta: -0.55 points, 95% CI: [-10.74, +9.64]). Diverse opponent training did not measurably improve play on held-out decks under an equal sample budget; an earlier, unlogged run reached the same conclusion.

The public showcase (Milestone 4) lives in [`web/`](web/). It lays the 360 held-out games out as cards on a table, lets readers re-sort them by training pool, deck, opponent, seat, ending or checkpoint, and replays any game decision by decision, from the AI's view or as a spectator. It is a static Astro site built from `experiments/` at build time:

```sh
cd web
npm ci
npm run build
npm run preview
```

All artwork on the site is original (drawn in Glaxnimate and rendered in Blender); see [`web/design/README.md`](web/design/README.md). Complete metrics and checkpoint weights are recorded in [`experiments/ml-experiment-report.json`](experiments/ml-experiment-report.json).

Read the [research plan](RESEARCH.md), [roadmap](ROADMAP.md), and [showcase brief](docs/showcase.md).

## Usage

Use Python 3.12 and uv 0.12.5:

```sh
uv sync --frozen --group dev
```

### Run the controlled ML experiment

Execute the full training suite and evaluate checkpoints on held-out deck families:

```sh
uv run tcg-cabt-lab experiment --checkpoints-dir experiments/checkpoints --report-out experiments/ml-experiment-report.json
```

### Profile representation and resource budgets

Measure representation extraction latency, dimensionalities, and memory footprints:

```sh
uv run tcg-cabt-lab profile
```

### Train a policy checkpoint

Train a compact policy against an opponent pool variant:

```sh
uv run tcg-cabt-lab train --variant fixed-opponent-pool --seed 11 --steps 400 --out ckpt.json
```

### Run a tournament

Execute a paired tournament across agents and deck families, generating a leaderboard and matchup grid:

```sh
uv run tcg-cabt-lab tournament --pilot --out experiments/baseline-pilot-report.json
```

### Inspect deck family splits

Verify disjointness across training, tuning, and held-out test splits:

```sh
uv run tcg-cabt-lab splits
```

### Run a simulated battle

Simulate a full game between two random agents with reproducible seeds and export the structured game log:

```sh
uv run tcg-cabt-lab battle --seed-p0 11 --seed-p1 22 --bo 1 --out battle.json
```

### Inspect the card catalog

Verify the 1,431 cards in the pinned CABT catalog:

```sh
uv run tcg-cabt-lab catalog
```

### Validate a deck

Validate a 60-card deck and display its composition:

```sh
uv run tcg-cabt-lab deck
```

### Smoke test synthetic selection

Sample choice indices from a standalone observation JSON without starting the simulator:

```sh
uv run tcg-cabt-lab sample examples/selection.json --seed 11
```

The sampler can also be imported with a caller-owned random generator:

```python
from random import Random

from tcg_cabt_lab.baseline import choose_random_action

action = choose_random_action(observation, Random(11))
```

Keep the generator alive across decisions when integrating an agent. The CLI creates a fresh generator for each invocation. Full simulator runs must check that actions are accepted by the pinned engine.

## Current flow

The CLI reads an observation JSON file, validates the requested selection bounds, uses a seeded random selector, and returns a JSON array of choice indices.

## Repository layout

| Path | Contents |
| --- | --- |
| `src/tcg_cabt_lab/` | Feature representations, policy models, training, battle runner, tournament evaluation, and CLI |
| `tests/` | Unit and integration tests for representation, policy, training, battle, deck, catalog, and CLI |
| `examples/` | Synthetic choice request for the smoke test |
| `experiments/` | Frozen study settings, checkpoints with weights provenance, baseline reports, and ML experiment results |
| `RESEARCH.md` | Question, empirical findings, controls, evaluation, data policy, and sources |
| `ROADMAP.md` | Milestones and completion criteria |
| `docs/showcase.md` | Public tournament and match-viewer brief |
| `JOURNAL.md` | Decisions behind the project |

Runtime dependencies include the pinned CABT simulation environment and NumPy. Checkpoint JSON weights and experiment reports are tracked with full provenance.

## License

Project code is licensed under [MIT](LICENSE). CABT, competition inputs, Pokemon assets, datasets, and model weights retain their own terms. The project license does not grant rights to redistribute those materials.
