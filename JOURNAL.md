# Journal

## 2026-10-20: Establish evaluation baselines and freeze study configuration #milestone

Milestone 2 is complete. Implemented a transparent rule-based heuristic agent (`HeuristicAgent`) with damage ranking from the verified 1,755-attack catalog (SHA-256 `1b584ac7e19f85d565c2902d04831bf9b30e5107b51a4ab3bc956db2051a12ce`), and integrated CABT's greedy reference (`FirstAgent`). Formulated 6 elemental deck families and verified split disjointness across training, tuning, and held-out test tiers. Added matched-pair tournament runner with reversed player seats and explicit failure accounting (wins, losses, draws, timeouts, invalids). Executed 24-game baseline pilot benchmark measuring average action latency (~6ms) and frozen study parameters in `experiments/heldout-matchups.json`.

## 2026-10-20: Reproduce CABT and establish simulator boundary #milestone

Milestone 1 is complete. Integrated `kaggle-environments==1.33.0` providing the CABT 1.0.0 simulation engine with native Linux ARM64 (`libcg-arm64.so`), Linux x86_64 (`libcg.so`), and macOS Darwin (`libcg.dylib`) platform binaries. Pinned the 1,431-card catalog at SHA-256 `7fd6c45fcdc2913a1fe19ddb67c01aa9b204718cb760be7582cf4fcc3513de9c`. Verified initial 60-card deck selection, optional choice bounds, special selection contexts, and invalid action penalization (INVALID status with opponent win). Enforced an observation-only agent interface by stripping simulator internal search state (`search_begin_input`) and masking opponent hidden cards. Built CLI commands for full battle simulation, catalog verification, and deck inspection with reproducible structured JSON logging.

## 2026-10-13: Replace the README Mermaid diagram #decision

The current flow is a short linear scaffold, so the README now states it in prose. The former Mermaid block added no relationship that needed a diagram.

## 2026-10-05: Publish the research repository #milestone

The public Builder106/tcg-cabt-lab repository has a signed research baseline that GitHub marks Verified. Main requires a pull request, CI, and secret scanning for subsequent changes. Squash merge and automatic topic-branch deletion are enabled. The first full-game CABT run remains the next research milestone.

## 2026-10-04: Scaffold verification passes #milestone

The scaffold passed strict type checking, lint, formatting, 17 tests, source and wheel builds, installation from the wheel, and a hashed dependency audit on Linux ARM64. The installed CLI returned two distinct indices for the synthetic example. These checks establish package and selection-interface behavior; they do not establish CABT game legality or model performance.

## 2026-10-04: Start with the choice interface #decision

The first executable component samples indices from CABT's documented option array using a caller-owned random generator. Tests check counts, bounds, repeatability, and malformed input. Engine acceptance, initial deck selection, and special choice semantics remain integration work; the scaffold does not claim complete legal gameplay.

## 2026-10-04: Frame the first controlled study #decision

The draft compares fixed and diverse training opponent pools while holding model architecture, training decks, and compute budgets constant. Final-test deck families must be held out, and paired games need explicit failure accounting and uncertainty. PTCG-Bench and public Kaggle solutions are technical prior work to compare before making a novelty claim.

## 2026-10-04: Baseline and dependency boundary #decision

The user requested repository creation and scaffolding. A Python 3.12 package, uv lock, README, license, contributor guide, tests, and CI form the executable baseline. Runtime dependencies stay empty until CABT integration. Deployment, analytics, banners, and demo recordings become relevant when the public browser demo exists.

## 2026-10-04: Separate TCG from competitive battles #decision

TCG CABT Lab covers the standard 60-card game. VGC Rulebreak is a separate repository because the engines, choices, observations, datasets, and evaluation differ. The intended public deliverable is a reproducible agent tournament with a matchup grid and a match viewer built around actual research runs.
