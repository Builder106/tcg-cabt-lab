# Journal

## 2026-11-19: TechRxiv closed, arXiv hard #decision

TechRxiv shows a notice that it is moving to a new platform and that submissions are temporarily closed, with no reopening date. arXiv has not endorsed new authors by institutional email since 21 January 2026, so a first-time author needs a personal endorsement, and its content policy lists undergraduate research as typically not accepted. IEEE allows a preprint on an author's own or employer's website, so that is the route with no gatekeeper.

## 2026-11-19: Zenodo ruled out for the preprint #decision

IEEE author support replied that Zenodo is not an approved preprint site for a paper submitted to an IEEE conference. The preprint will go on TechRxiv, which IEEE names in its policies, or arXiv. The Publications Board manual (June 2026, section 8.1.9) keeps the approved-server list with IEEE and does not name Zenodo. Zenodo suits a code and data archive after review, since that is not an IEEE article.

## 2026-11-18: Preprint policy answered #decision

The CoG organizers replied by email that IEEE's preprint policy applies to CoG papers and that posting a preprint is allowed, with the policy details to be checked. They also said a submission is a single PDF with no attachments, and that a URL in a footnote is fine. The paper now points to the anonymized repository in a footnote, still a placeholder until the link exists. The IEEE Author Center rules for conference preprints (statement on the first screen, replacement after acceptance) are in `docs/paper/README.md`. The anonymized submission must not link to the preprint.

## 2026-11-17: Paper reports four studies #milestone

`docs/paper/` now covers the long learning-from-play study as study D: a table row, a figure group, a results paragraph and updated abstract, discussion, limitations and conclusion. Exploratory per-deck gaps for study D come from a 10,000-resample bootstrap in `make_results.py` (seed 1), so the paper and `RESEARCH.md` quote the same bounds. The paper cites the 20th-place Kaggle write-up for its roughly 20 million training games. Figure tick labels changed to fix and div, since study D collided with the old D label. The paper is 5 pages.

## 2026-11-17: Long learning-from-play study reports equivalence, narrowly #milestone

The frozen long plan ran with 30 new seeds per arm, 2,000 games per checkpoint from random weights at learning rate 0.03. Delta (diverse minus fixed) is +0.15 points, 95% seed-level interval [-5.04, +5.29], 90% interval [-4.29, +4.51], so the pools are equivalent within the preregistered plus or minus 5 points, with little room. The seed spread was 10.8 and 10.6 points, below the 15 I had feared in the plan. The policies learned (training score up from 44.7% to 49.9% fixed and from 54.5% to 63.2% diverse, in 25 of 30 seeds per arm) but score 54% on held-out decks, below the imitation students at 65% to 67% and near `HeuristicAgent`. Exploratory: the arms differ by deck in opposite directions (-6.4 on Mewtwo, +6.8 on Snorlax, both intervals including zero) and cancel in the primary score. Report: `experiments/rl-long/report.json`.

## 2026-11-17: Long learning-from-play run, frozen after a failed pilot #decision

An 800-game pilot from the imitation start (two seeds per arm, tuning deck) showed no learning at any rate: the rise in training score was -1.75, -0.4 and -4.75 points at 0.003, 0.01 and 0.03, and the tuning-deck score fell by 4.2, 17.9 and 10.8 points. My declared fallback was 0.01, the worst rate. I asked and the user chose to start from random weights at 0.03, the only pilot setting in which training scores rose. `experiments/rl-long.json` freezes 2,000 games per checkpoint, seeds 4001 to 4030. The change was made after the pilot and before any study game. The plan states that 30 seeds probably cannot show equivalence within plus or minus 5 points if the seed spread is near 15 points.

## 2026-11-16: Paper gaps filled #milestone

The paper now has a per-deck and per-opponent table, an end-reason audit, the pilot caveat for the learning-from-play study, and a conclusion on what a stronger study needs. The audit is a separate 600-game run, since the 30-seed reports store no replays: 266 of 300 colorless-snorlax games ended with a player having no Pokémon left (median 12 turns), and 205 of 300 psychic-mewtwo games ended by deck-out (median 57 turns). Only 34 and 89 games per deck ended by taking all prize cards. The wider literature search found no controlled test of the training opponent for imitation, and added VGC-Bench for context. Hoover et al. appeared in print in March 2020, so its year changed. The CoG call for papers confirms double-blind review, IEEE two-column, up to 8 pages including references, and is silent on preprints. The one open marker is the anonymized artifact link. The paper is 5 pages.

## 2026-11-16: Paper skeleton #milestone

`docs/paper/` holds a four-page IEEEtran skeleton for CoG 2027 that reports the three studies. `make_results.py` writes every number, table and figure series from the three reports, so the text has no typed results. Bibliography authors use only the forms verified in `related-work.md`; a first draft of `refs.bib` had full first names filled in from memory, and they were replaced with the verified initials before the build. Compilation runs on the VM with `TEXINPUTS` pointing at the vendored IEEE files, since the Mac lacks pgfplots and IEEEtran. Open items are marked `\todo` in the text and listed in `docs/paper/README.md`.

## 2026-11-16: Learning-from-play study reports equivalence, weakly #milestone

The frozen RL plan ran with the board-teacher study's 30 seeds per arm. Delta (diverse minus fixed) is -1.60 points, 95% seed-level interval [-3.69, +0.61], 90% interval [-3.40, +0.25], so the pools are equivalent within the preregistered plus or minus 5 points. RL barely changed the policies: mean change from the starting checkpoint is +0.6 (fixed) and -1.0 points (diverse), with a spread of 5 to 6 points that matches the evaluation noise of a 120-game score, and the training scores stay flat. The pilot gain on the tuning deck (+11.7 and +5.0) did not carry over, so the pilot's choice of learning rate was unreliable. The finding is therefore no effect at a 400-game budget. A larger budget, a higher learning rate or a longer run would be a new, separately frozen study. Report: `experiments/rl/report.json`.

## 2026-11-16: Learning from play, frozen plan #decision

The imitation studies copy a teacher, so the opponent pool only picks the teacher's game states. `rl.py` adds REINFORCE: the policy plays the pool, learns from win, draw or loss, and uses a batch-mean baseline. In a two-seed pilot from random weights, 400 games barely moved the policy at learning rates 0.003 and 0.01, and at 0.03 the seed-to-seed spread ran from 15% to 82% on the tuning deck. The study therefore starts both arms from the board-teacher imitation checkpoint of the same seed. A four-seed warm-start pilot on `fire-ponyta` (seeds 3001 to 3004, outside the study) gave +11.7 and +5.0 points at learning rate 0.003 (fixed, diverse), about zero at 0.001 and slightly negative at 0.01, so 0.003 is frozen in `experiments/rl-pool.json`. The held-out decks played no part in that choice. Also: `training_opponent` now holds the pool choice that imitation training and RL share, with the random draws in the same order as before. The VM matrix runner refused at 85% disk, so checks ran one at a time.

## 2026-11-15: Board-teacher study reports equivalence #milestone

The frozen board-teacher plan ran with 30 new training seeds per arm and 120 held-out games per checkpoint. Delta (diverse minus fixed) is +1.40 points, 95% seed-level interval [-0.67, +3.58], 90% interval [-0.33, +3.21], so the pools are equivalent within the preregistered plus or minus 5 points. Students agree with `BoardAgent` on 52% to 69% of held-out decisions (the old teacher: at least 99.8%), and score 65.18% (fixed) and 66.58% (diverse) against 74.58% for the teacher. The null therefore holds when the student cannot copy the teacher exactly. Report: `experiments/board/report.json`. Open: the toy decks (157 of 180 Snorlax games ended with no Pokémon in the earlier run), a state-dependent opponent effect that only RL from play could show, and a check that the margin of plus or minus 5 points is defensible to reviewers.

## 2026-11-15: Board-reading teacher and CABT option types #decision

The novelty search showed the first scaled study could not find an effect. `HeuristicAgent` never reads the board, and the student's features hold every input it uses, so any set of demonstrations teaches the whole rule. `BoardAgent` replaces it as the teacher for a second study, frozen in `experiments/board-teacher.json` before its seeds were run. The CABT API docs also showed that the code had option types 8 and 9 swapped (8 is ATTACH, 9 is EVOLVE) and treated 7 as Trainers only (it is PLAY, any card from the hand). `HeuristicAgent` changed in comments only, so earlier runs reproduce. The feature encoder's bench flag checked area 4 and never fired; it now checks area 5, the bench. Checkpoints trained before this see different inputs on bench-target options, and earlier reports were computed with the old encoder. In a 3-seed pilot (seeds 901 to 903, not part of the study), students reached 72.5% to 77.5% validation accuracy against the new teacher and agreed with it on 52% to 67% of held-out decisions.

## 2026-11-14: Scaled study reports equivalence #milestone

The frozen plan ran with 30 new training seeds per arm and 120 held-out games per checkpoint. Delta (diverse minus fixed) is -1.22 points, 95% seed-level interval [-3.78, +1.33], 90% interval [-3.40, +0.90], so the pools are equivalent within the preregistered plus or minus 5 points. The +6.95 points in the 3-seed rerun did not replicate. Students match the teacher on at least 99.8% of held-out decisions and score about as well as it (teacher baseline 56.67%), so the study measures how little the demonstration opponent changes a near-exact copy. The run used the committed code from a build directory, because verify-on-vm refused to start at 7% free disk.

## 2026-11-14: Seed-level analysis and a pre-registered scaled study #decision

The delta interval in the experiment report treats all 180 games per arm as independent, though they come from three checkpoints. The new `stats` module scores each checkpoint once (held-out decks weighted equally) and builds the interval with a cluster bootstrap over training seeds. The runner adds the teacher and the other reference agents as baselines and counts how often each student's first choice matches the teacher on held-out decisions. The scaled study is written down before it runs, in `experiments/opponent-pool-scaled.json` and `docs/analysis-plan.md`, and `tcg-cabt-lab experiment --config` refuses a plan that is not frozen. The old report fields stay as they are, because the showcase copy reads them.

## 2026-11-14: Remove the ignore-build command #decision

The rerun commits were pushed together with a docs-only commit on top, and Vercel canceled every deployment in 2 seconds, so the live site kept the old results. The project's ignore-build command diffed `VERCEL_GIT_PREVIOUS_SHA` against `HEAD` and skipped builds that contained real changes. The command is removed through the project settings and the site was redeployed with the CLI. The build takes about 5 seconds, so skipping docs-only commits saved nothing. The 29 October entry describes the same failure.

## 2026-11-14: Rerun after the teacher-deck fix #decision

The study was rerun with the same settings (seeds 11, 29 and 47, 400 steps, 2,000 decisions per checkpoint) after the teacher-deck fix, and it replaces the 21 October run as the run of record. Fixed pool 55.83% (95% CI [48.53%, 62.89%]), diverse pool 62.78% (95% CI [55.52%, 69.50%]), delta +6.95 points (95% CI [-3.17, +17.07]). Zero is still inside the interval. The sign flipped from the 21 October run (-0.55), and the diverse pool now leads on both decks, so the showcase copy that said each style won one deck was rewritten. Per-seed win rates range from 50.0% to 74.2%, which is the main reason to add seeds before a write-up.

## 2026-11-14: Teacher now plays the sampled training deck #fix

`collect_training_dataset` sampled a deck for the teacher but built the teacher once as `HeuristicAgent()`, so it always submitted the default deck, which is the `water-kyogre` list. `collect_game_decisions` accepted `deck_p0` and `deck_p1` and ignored both, because each agent submits its own deck to the engine. The teacher is now built per game with the sampled deck, and the unused parameters are gone. Both arms shared the defect, so the logged comparison is not biased by it. But the six checkpoints in `experiments/checkpoints/` and the 21 October results were trained only on Kyogre-deck decisions, with Bulbasaur and Pikachu seen only from the opponent's side. They need a rerun before any write-up describes three training decks.

## 2026-10-29: Restore the production deployment #decision

The `main` commit `9dc7532` had no ready production deployment. Vercel skipped its two latest Git deployments because the ignored-build command found no changes in `web/` or `experiments/`. A forced CLI production deploy built 371 static pages and now serves HTTP 200 at https://tcg-cabt-lab.vercel.app. Vercel Authentication uses Standard Protection (`prod_deployment_urls_and_all_previews`), which leaves the production domain public and protects preview and deployment URLs.

## 2026-10-27: Check the Astro showcase in CI #ci #decision

The Python checks covered the research package, while the Astro showcase had no CI check. The workflow now installs the locked web dependencies, checks the Astro project, audits npm dependencies, and builds the site.

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

## 2026-10-23: Reject Any annotations in CI #decision

Ruff checks function arguments and returns for Any. Line-level exceptions remain at dynamic CABT and JSON record boundaries that still need schema types. Pytest treats warnings as errors, and strict mypy stays enabled.

## 2026-10-28: Override litellm and filelock for audit #decision

kaggle-environments caps litellm below 1.94, and litellm caps filelock below 4. Every fixed release of both is above those caps, so pip-audit failed with no resolver path. pyproject now overrides litellm to 1.104 or newer and filelock to 4.2.1 or newer. The repository imports neither package, and the full test suite, wheel check, and audit pass with the overrides. Drop the overrides once kaggle-environments and litellm raise their own caps.
