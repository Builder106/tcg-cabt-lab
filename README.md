# TCG CABT Lab

[![CI](https://github.com/Builder106/tcg-cabt-lab/actions/workflows/ci.yml/badge.svg)](https://github.com/Builder106/tcg-cabt-lab/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](#license)

TCG CABT Lab is a research project about compact agents for the 60-card Pokemon Trading Card Game. The first planned study asks whether training against varied opponents improves performance on deck families the agent has never trained on.

## Project status

The project integrates the CABT 1.0.0 simulation engine (`kaggle-environments==1.33.0`) with verified platform binaries on Linux ARM64, Linux x86_64, and macOS. The card catalog (1,431 cards) and attack catalog (1,755 attacks) are pinned and checksum-verified. The evaluation framework provides 6 canonical elemental deck families with verified split disjointness across training, tuning, and held-out test splits, alongside reference agents (`RandomAgent`, `FirstAgent`, `HeuristicAgent`). The tournament runner executes matched pairs with reversed player seats, explicit failure accounting, and Wilson score 95% confidence intervals. The study configuration is frozen in [`experiments/heldout-matchups.json`](experiments/heldout-matchups.json).

Read the [research plan](RESEARCH.md), [roadmap](ROADMAP.md), and [showcase brief](docs/showcase.md).

## Usage

Use Python 3.12 and uv 0.12.5:

```sh
uv sync --frozen --group dev
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
| `src/tcg_cabt_lab/` | Random selector and CLI |
| `tests/` | Choice invariants, malformed input, and CLI checks |
| `examples/` | Synthetic choice request for the smoke test |
| `experiments/` | Draft study settings, with unresolved fields marked as null |
| `RESEARCH.md` | Question, controls, evaluation, data policy, and sources |
| `ROADMAP.md` | Milestones and completion criteria |
| `docs/showcase.md` | Public tournament and match-viewer brief |
| `JOURNAL.md` | Decisions behind the project |

Runtime dependencies include the pinned CABT simulation environment. Datasets, deck CSVs, checkpoints, raw matches, and generated reports stay outside Git. Small synthetic fixtures are tracked explicitly.

## License

Project code is licensed under [MIT](LICENSE). CABT, competition inputs, Pokemon assets, datasets, and model weights retain their own terms. The project license does not grant rights to redistribute those materials.
