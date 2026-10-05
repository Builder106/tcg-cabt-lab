# Journal

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
