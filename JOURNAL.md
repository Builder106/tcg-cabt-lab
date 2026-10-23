# Journal

## 2026-10-22: README banner from the showcase art #decision

The README opens with light and dark banners in `assets/`, written by `assets/banner.py`. They reuse the Glaxnimate mark, card back, Psychic and Water faces, and hex tile, and set the type as outlines from the site's Exo 2 and Archivo files, because GitHub shows README SVGs as images that cannot load web fonts. The pool chips use a deeper blue and red than the site so their 14 px white labels pass 4.5:1. PNG copies sit beside the SVGs for clients that do not draw SVG.

## 2026-10-22: Limit the first card deal on slower devices #decision

A live mobile trace showed several seconds of main-thread work while the table initialized. Touch devices now show the cards without the first-deal animation or the decorative lamp and hand tickers. Desktop keeps a short deal of at most eight cards. In a paired throttled Chromium run, mobile startup long tasks fell from 4.8 seconds on production to 1.8 seconds in the changed build; this is lab evidence, not a field INP result. All 360 game links remain in the table.

## 2026-10-22: Deploy the showcase from GitHub #decision

The first deploy uploaded prebuilt files with the Vercel CLI, so merges to `main` did not reach the site. The Vercel project is now connected to the repository with `web/` as its root directory and access to files outside it, which is all the build needs to read `experiments/`. Pushes to `main` deploy to production and pull requests get previews. Commits that change neither `web/` nor `experiments/` skip the build.

## 2026-10-22: Deploy the showcase as prebuilt static files #decision

The showcase is live at https://tcg-cabt-lab.vercel.app, a project in the SankofaForge Vercel team. The build reads `experiments/` from outside `web/`, so a Vercel build of `web/` alone could not find the games. The site is built locally and the static output is deployed with the Vercel CLI, using `web/vercel.json` for trailing-slash redirects and long caching of hashed assets. Pushing to `main` does not deploy; each release is a CLI deploy.

## 2026-10-22: Build the showcase as a card table #milestone

The showcase is a static Astro site in `web/`. It reads `experiments/` at build time and emits one page and one compressed replay per game, so it needs no server or inference endpoint. The 360 games appear as cards on a table, and a hand of Trainer cards re-sorts them; the played card states the finding for that sort in plain language. Each replay steps through every decision with the board animated between steps.

## 2026-10-22: Original artwork only #decision

Research into the Kaggle competition rules and the Pokémon Company's legal and press terms found no permission to show official card art, logos, or card backs on a public site. Every image is therefore original: card faces, sort art, Pokémon art motifs, and icons were drawn in Glaxnimate, and the card renders were made in Blender. Card and attack names appear as text from the engine catalog, and the footer states that the project is not affiliated with the Pokémon Company.

## 2026-10-22: Keep the replay's information boundary #decision

Replays store the full spectator record, so the viewer rebuilds the policy's view from it: own hand, public board, and counts. The opponent's hand, its options, its draws and searches, and every Prize card stay face down in that view, and the board animation compares only what the current view shows. Policy scores are labelled as preferences, not win chances. No move is called a mistake, because that would need counterfactual rollouts the study did not run.

## 2026-10-21: Report the logged re-run #decision

The milestone 3 numbers now come from a re-run that logs every game: fixed pool 58.33%, diverse pool 57.78%, delta -0.55 points (95% CI: [-10.74, +9.64]). The earlier run was not logged, so its games cannot be shown or checked; its numbers (-3.88 points) stay in the record as an earlier run that reached the same conclusion.

## 2026-10-20: Execute controlled ML experiment on held-out deck families #milestone

Milestone 3 is complete. Implemented an 88-dimensional compact numerical representation (72-dim game state, 16-dim option vector with attack damage from the 1,755-attack catalog, benching, energy attachment, trainer flags, targeting, and relative ordering). Empirically verified resource budgets: 0.0285 ms inference latency (<50 ms budget) and 1.8 KB footprint (<512 MiB budget). Established a behavioral cloning baseline using a 2-layer option-scoring MLP (88 -> 32 -> 1, 2,881 parameters) with Adam optimization, verifying validation loss reduction and >85% top-1 action prediction accuracy. Executed the controlled experiment comparing `fixed-opponent-pool` (FirstAgent) vs. `diverse-opponent-pool` (Heuristic, First, Random) across 3 independent training seeds (11, 29, 47) under identical training decks (water-kyogre, grass-bulbasaur, lightning-pikachu) and step budgets. Evaluated 6 checkpoints across 360 matched-pair games with reversed player assignments on frozen held-out test families (psychic-mewtwo, colorless-snorlax). Observed a pooled held-out win rate of 55.56% (95% CI: [48.26%, 62.62%]) for fixed-opponent training and 51.67% (95% CI: [44.41%, 58.86%]) for diverse-opponent training, yielding a delta of -3.88% (95% CI: [-14.18%, +6.42%]). Recorded complete checkpoint provenance and ablation metrics in `experiments/ml-experiment-report.json`. Negative result confirmed: diverse opponent training did not yield a statistically significant improvement over fixed-opponent training on held-out deck families under equal sample budgets.

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
