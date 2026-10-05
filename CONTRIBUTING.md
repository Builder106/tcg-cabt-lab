# Contributing

Read [RESEARCH.md](RESEARCH.md) and [ROADMAP.md](ROADMAP.md) first. Keep a change small enough to test and evaluate independently.

## Setup and checks

Use Python 3.12 and uv 0.12.5:

```sh
uv sync --frozen --group dev
uv run tcg-cabt-lab sample examples/selection.json --seed 11
```

Run the same checks as CI:

```sh
uv run mypy
uv run ruff check .
uv run ruff format --check .
uv run pytest
uv build
uv run --isolated --no-project --with ./dist/tcg_cabt_lab-0.1.0-py3-none-any.whl tcg-cabt-lab sample examples/selection.json --seed 11
uv export --quiet --frozen --all-groups --no-emit-project --output-file /tmp/tcg-cabt-lab-requirements.txt
uv run pip-audit --strict --disable-pip --require-hashes --cache-dir /tmp/tcg-cabt-lab-audit-cache --requirement /tmp/tcg-cabt-lab-requirements.txt
```

`sample` prints an action array and exits with code 0 for a supported request. Invalid JSON, a missing file, malformed counts, or unsupported initial deck selection exits with code 2. It does not launch CABT, validate card effects, or check the draft study configuration.

## Research guardrails

Use only agent-visible observations for policies. Keep held-out deck families and final-test seeds separate from tuning. Pin simulator, data, and checkpoint versions. Declare budgets and outcome scoring before final evaluation. Record failure outcomes instead of dropping them.

Add tests for new decision logic, parsers, and scoring invariants. Simulator code needs full-game integration checks. Browser code needs interaction checks. Keep downloaded data, deck CSVs, checkpoints, raw matches, secrets, and generated outputs outside Git. Document the provenance of small tracked fixtures.

## Pull requests

Use a short topic branch from `main` and a Conventional Commit title. Explain the behavior change and validation. Required CI must pass before merge. Squash completed branches and delete them after merging.

Simulator integration, learning, and the showcase follow the roadmap. Add dependencies when their implementation uses them. The project scope is 60-card TCG in CABT; Pocket and video-game battle work belongs elsewhere.
