# Paper readiness assessment

Assessed on 14 November 2026 against the repository at commit `e918838`, then updated the same day after the training-deck fix and rerun (section 2, "Training decks as described"). This is a desk review only: no experiments were run, no code was changed, and nothing was committed. Every number below comes from a file in this repository or from a live web page cited with its access date. Counts marked "tallied" were computed by reading `experiments/ml-experiment-report.json`, without running any agent or game.

## 1. Summary

The project asks whether training a compact Pokémon TCG policy against a diverse opponent pool improves its win rate on deck families it never trained on, with the same training and inference budgets ([RESEARCH.md:5](../RESEARCH.md#L5)). The policy is a 2,881-parameter option-scoring MLP (88 input features, 32 hidden units, 1 logit) running in the CABT 1.0.0 engine from `kaggle-environments==1.33.0`. It is trained by behavioral cloning. The demonstrator is the rule-based `HeuristicAgent`, and the only difference between the two arms is which opponent the teacher plays while its decisions are recorded: always `FirstAgent` in the fixed arm, or a random pick of Heuristic, First, or Random in the diverse arm ([training.py:124-150](../src/tcg_cabt_lab/training.py#L124-L150)). Each arm trains on 2,000 recorded decisions for 400 Adam steps per seed, with seeds 11, 29 and 47. Evaluation uses 360 stored games on two held-out deck families (Mewtwo and Snorlax), with seats reversed, against the three reference agents. In the run of record (14 November 2026, after the training-deck fix), the fixed pool scored 100.5 points in 180 games, with a draw counted as half a point (55.83%, Wilson 95% CI [48.53%, 62.89%]). The diverse pool scored 113 points (62.78%, CI [55.52%, 69.50%]). The delta is +6.95 points with a 95% CI of [-3.17, +17.07] ([ml-experiment-report.json:55-114](../experiments/ml-experiment-report.json#L55-L114)). Per-seed win rates range from 50.00% to 74.17%, so the seeds differ by more than the two pools do. The logged run of 21 October, made before the fix, gave 58.33% and 57.78% (delta -0.55, CI [-10.74, +9.64]). A frozen, 30-seed-per-arm follow-up later the same day gave a delta of -1.22 points (seed-level 95% interval [-3.78, +1.33], 90% interval [-3.40, +0.90]) and reports the arms as equivalent within the preregistered plus or minus 5 points; the +6.95 points above did not replicate.

## 2. Readiness checklist

| Item | Status | Evidence |
| --- | --- | --- |
| Research question and contribution | Partial | The question is clear ([RESEARCH.md:5](../RESEARCH.md#L5), [heldout-matchups.json:4](../experiments/heldout-matchups.json#L4)). The docs describe the arms as "trained against" an opponent pool ([RESEARCH.md:9-10](../RESEARCH.md#L9-L10)), but the code imitates one fixed teacher, and the pool only changes which states the teacher visits ([training.py:124-150](../src/tcg_cabt_lab/training.py#L124-L150)). No contribution statement says what a reader learns that PTCG-Bench or the Kaggle write-ups do not already show ([RESEARCH.md:53](../RESEARCH.md#L53)). |
| Related work (verified citations only) | Missing | [RESEARCH.md:47-55](../RESEARCH.md#L47-L55) lists five sources. Only one, PTCG-Bench, is a paper; the others are engine docs, the Kaggle environment, competition pages, and one competition write-up. Nothing is cited on opponent diversity, population training, imitation learning, generalization, card-game AI, or RL evaluation statistics. Section 6 lists candidate papers whose metadata I verified. |
| Baselines | Done | The scaled study scores the `HeuristicAgent` teacher (56.67%, Wilson 95% [47.73, 65.19]), `FirstAgent` (39.58%) and `RandomAgent` (41.67%) under the same 120-game protocol as the students ([RESEARCH.md](../RESEARCH.md), `experiments/scaled/report.json`). Per-checkpoint agreement with the teacher on held-out decisions is 99.80% to 100%. |
| Seeds | Done | 30 new training seeds per arm (1001 to 1030) in the frozen plan ([experiments/opponent-pool-scaled.json](../experiments/opponent-pool-scaled.json)). The 3-seed runs are kept as pilots. |
| Sample size | Done | 120 held-out games per checkpoint, 7,200 in total, with the sizing argument in [docs/analysis-plan.md](analysis-plan.md). The plan sizing assumed per-seed standard deviations from 3 seeds; the run gave 5.4 and 4.9 points, and the 90% interval half-width came out at about 2.2 points, narrower than the 3.8 predicted. |
| Statistical tests | Done | Training seed as the unit, percentile cluster bootstrap (10,000 resamples), difference rule at 95% and equivalence rule at 90% inside plus or minus 5 points, all fixed before the run ([docs/analysis-plan.md](analysis-plan.md), [stats.py](../src/tcg_cabt_lab/stats.py)). Result: delta -1.22 points, 95% interval [-3.78, +1.33], 90% interval [-3.40, +0.90], equivalent. The margin is an unvalidated judgment, and a reviewer may ask for another. |
| Protocol adherence | Partial | Training ran 400 of the 100,000 planned steps ([heldout-matchups.json:32](../experiments/heldout-matchups.json#L32), [RESEARCH.md:15](../RESEARCH.md#L15)). The tuning split (`fire-ponyta`) is defined but never used ([training.py:19](../src/tcg_cabt_lab/training.py#L19)). The frozen config is not read by any code ([RESEARCH.md:29](../RESEARCH.md#L29)). |
| Training decks as described | Fixed and rerun on 14 Nov 2026 ([JOURNAL.md](../JOURNAL.md)); the description below is the defect in the two earlier runs | `collect_game_decisions` accepts `deck_p0` and never uses it ([training.py:51-98](../src/tcg_cabt_lab/training.py#L51-L98)). The teacher is built once as `HeuristicAgent()` ([training.py:124](../src/tcg_cabt_lab/training.py#L124)), so it plays `REFERENCE_DECK` ([agent.py:99](../src/tcg_cabt_lab/agent.py#L99)), which is the `water-kyogre` list ([manifest.py:18](../src/tcg_cabt_lab/manifest.py#L18)). Every recorded decision therefore comes from the Kyogre deck, and the Bulbasaur and Pikachu decks reach only the opponent. Both arms share the defect, so the comparison is not biased by it. The statement "identical training decks (water-kyogre, grass-bulbasaur, lightning-pikachu)" ([ROADMAP.md:17](../ROADMAP.md#L17)) is inaccurate for the learner. |
| Test environment validity | Partial | Each deck family is 4 + 4 Pokémon, 4 + 4 Trainers, and 44 basic Energy ([manifest.py:20-58](../src/tcg_cabt_lab/manifest.py#L20-L58)), and every evaluation game is a mirror match ([experiment.py:151-152](../src/tcg_cabt_lab/experiment.py#L151-L152)). Tallied end reasons in the 14 November run: 157 of 180 Snorlax games ended with a player having no Pokémon left, and 123 of 180 Mewtwo games ended by deck-out. The median game length was 9 turns for "no Pokémon" endings and 59 turns for deck-outs. Reviewers will ask whether these games test strategy. |
| Reproducibility: code, configs, logs | Partial (strong base) | One CLI command reruns the study ([README.md:49](../README.md#L49)). Checkpoints carry weight hashes, all 360 games are stored as replays, catalog hashes are pinned ([RESEARCH.md:19](../RESEARCH.md#L19)), and CI runs mypy, ruff and pytest (62 test functions). Gaps: the engine shuffles with `std::random_device`, so games cannot be replayed from a seed ([ml-experiment-report.json:41](../experiments/ml-experiment-report.json#L41)). The training datasets are not saved. Earlier runs gave -0.55 and -3.88 points ([RESEARCH.md:15](../RESEARCH.md#L15)), so reruns do not reproduce exact numbers. The CABT and Kaggle terms for redistributing replays still need checking ([RESEARCH.md:43](../RESEARCH.md#L43)). |
| Negative or null result framed as a finding | Partial | The scaled study supports a stated claim: within plus or minus 5 points, the demonstration opponent does not change a behavior-cloned policy, and the students match the teacher on at least 99.8% of held-out decisions. That is a measured explanation, but the paper still has to frame it as a result about imitation, because the study never tested learning from play against opponents. |

## 3. Work needed for a submittable draft

The items are ordered by their effect on whether the paper would survive review. Effort figures are my planning estimates for one person working part time, not measurements. Compute is cheap: the logged run spent 47 to 58 seconds training each checkpoint and about 402 seconds of game time on all 360 evaluation games.

| # | Work item | Why it matters | Effort |
| --- | --- | --- | --- |
| 1 | Restate the method and choose the question. Option A keeps behavioral cloning and asks whether diversifying the opponents during demonstration collection changes a cloned policy's held-out play. Option B adds a learning signal from play (RL or self-play) so that "training against" an opponent is literally true. | The current wording describes a different method from the code. Reviewers will treat that as an error. | A: half a day. B: 1 to 3 weeks. |
| 2 | Done on 14 Nov 2026: the training-deck fix, its regression test, and the rerun. | The method section can now describe three training decks. | Done. |
| 3 | Done on 14 Nov 2026: baselines under the held-out protocol and student-teacher agreement. | This tests the likely mechanism of the null (both students copy the teacher) and gives readers a reference point. | Done. |
| 4 | Done on 14 Nov 2026: analysis plan frozen before the run, with a config the runner reads and refuses unless frozen. | This turns "no detectable difference" into a claim with a stated bound. | Done. |
| 5 | Done on 14 Nov 2026: seed-level cluster bootstrap and an equivalence test. A mixed-effects model and rliable-style per-seed intervals could be added as a robustness check. | The earlier CI treated correlated games as independent. | Done; robustness check 1 day. |
| 6 | Replace or justify the toy decks. At minimum, report end reasons and game lengths per deck; better, add more realistic decks if the CABT and Kaggle terms permit. | 157 of 180 Snorlax games end with no Pokémon left, which weakens any claim about generalization. | 2 to 5 days. |
| 7 | Write a related-work section from verified sources (section 6). | It is missing entirely. | 1 to 2 days. |
| 8 | Draft the paper in the venue template with figures (per-seed results, matchup grid, end-reason breakdown) and a limitations section. | This is the deliverable. | 4 to 6 days. |
| 9 | Prepare a reproducibility package: save the training datasets, tag a release, archive it with a DOI, and confirm the replay license terms. | Reviewers and the application both benefit from a citable artifact. | 1 day. |
| 10 | Ask a Wesleyan faculty member to read the draft. | An outside reader catches framing problems the author cannot see. | 1 to 2 weeks of calendar time. |

Items 2 to 5 are done. The remaining work for Option A is items 1 and 6 to 10: roughly two to three weeks of part-time work.

Update, 15 November 2026: the novelty search ([docs/paper/novelty-search.md](paper/novelty-search.md)) found that Option A's null result is fixed by the design. `HeuristicAgent` scores options only from features the student already receives and never reads the game state, so the demonstration opponent cannot change what the student learns. Item 1 now also needs a choice between a state-dependent teacher, a methods framing and adding RL from play. The search note sets out all three.

Update, 16 November 2026: the state-dependent teacher option was taken. In the preregistered board-teacher study (30 seeds per arm, [analysis-plan-board.md](analysis-plan-board.md)), students agree with the teacher on only 52% to 69% of held-out decisions, yet the delta is +1.40 points (95% interval [-0.67, +3.58], 90% interval [-0.33, +3.21]), equivalent within plus or minus 5 points. The null is no longer an artifact of copying the teacher, so the paper can state it as a result about imitation. What remains: toy decks and mirror matches, a margin a reviewer may contest, and the fact that the pool changes only the teacher's opponent, not a learning signal.

## 4. Venue options

All pages were accessed on 14 November 2026. "Not stated" means the page I read did not say. I did not estimate any deadline that has not been announced.

| Venue | Topic fit | Submission deadline | Page limit | Anonymity | Public preprint |
| --- | --- | --- | --- | --- | --- |
| AAAI-27 workshops, general ([program page](https://aaai.org/conference/aaai/aaai-27/aaai-27-workshop-program/)) | None of the 47 listed workshops is about games or game-playing agents. | Most are due 20 Nov 2026, with notification by 2 Dec 2026. Workshops run 22 to 23 Feb 2027 in Montréal. Some workshops set their own dates. | Set by each workshop | Set by each workshop | Set by each workshop |
| AAAI-27 Multi-Objective and Multi-Task Optimization for Robust AI ([site](https://robust-ai-2027.github.io/aaai27_workshop)) | Weak. Topics are multi-objective optimization and multi-task learning. The AAAI program page quotes it as welcoming "negative results, benchmark studies, and reproducibility analyses". | 20 Nov 2026 AoE; notification 2 Dec 2026 | 4 pages short, 8 pages full, excluding references and appendices; AAAI format | Double-blind per the AAAI program page; not stated on the workshop site | Not stated. The AAAI program page lists it as non-archival. |
| AAAI-27 Effective and Efficient Evaluation for AI Scientists ([site](https://eval-ai-scientists.github.io/aaai27/)) | Out of scope: "Submissions should directly address the evaluation of autonomous scientific discovery." | 20 Nov 2026, 06:00 UTC | 2 to 4 pages for negative-result reports | Double-blind | Work under review elsewhere is welcome where that venue permits; non-archival |
| AAAI-27 Student Abstract and Undergraduate Consortium ([abstract call](https://aaai.org/conference/aaai/aaai-27/student-abstract-and-poster-program-call-for-proposals/), [UC call](https://aaai.org/conference/aaai/aaai-27/undergraduate-consortium-call-for-participation/)) | Good fit for an undergraduate | Closed: abstracts were due 28 Sep 2026 and UC applications on 5 Oct 2026 | 2 pages for the abstract | Not checked (closed) | Not checked (closed) |
| NeurIPS 2026 workshops ([call](https://neurips.cc/Conferences/2026/CallForWorkshops)) | Depends on the workshop | Closed. The suggested contribution date was 29 Aug 2026, and the mandatory accept/reject date was 29 Sep 2026. | Not stated on the call page | Not stated on the call page | Not stated on the call page |
| ICLR 2027 workshops ([call](https://iclr.cc/Conferences/2027/CallForWorkshops)) | Unknown until the list is out. Accepted workshops are announced 29 Nov 2026. I found no 2027 call for the "I Can't Believe It's Not Better" negative-results workshop. | Per-workshop deadlines are not yet announced. The suggested contribution deadline is 1 Feb 2027, and the mandatory notification date is 26 Feb 2027. The page gives the workshop dates as "April 29 and 30, 2026", which looks like a typo for 2027. | Set by each workshop | Set by each workshop | Set by each workshop |
| ICML 2027 workshops ([dates](https://icml.cc/Conferences/2027/Dates)) | Unknown | Not announced. Workshops run 5 to 6 Aug 2027 in Rio de Janeiro. | Not announced | Not announced | Not announced |
| IEEE CoG 2027, Track 01 "AI for Game-Playing" ([site](https://cog2027.u-aizu.ac.jp/); dates and submission sections) | Strong. The track covers "general game-playing AI", and Track 05 lists benchmarks. | Portal opens 27 Nov 2026. Full papers are due 1 Mar 2027 with notification on 3 May 2027. Auxiliary (short) papers are due 15 May 2027 with notification on 11 Jun 2027. All times 23:59 AoE; the page marks the dates "subject to confirmation". | 8 pages full, 4 pages short, references and appendices included; IEEE two-column | Double-blind (Microsoft CMT) | Not stated. Ask the program chairs before posting a preprint. Camera-ready papers go to IEEE Xplore. |
| TMLR (journal) ([author guide](https://jmlr.org/tmlr/author-guide.html), [acceptance criteria](https://jmlr.org/tmlr/acceptance-criteria.html), [editorial policies](https://jmlr.org/tmlr/editorial-policies.html)) | Moderate. It accepts papers whose claims are "supported by accurate and convincing evidence", and "novelty of the studied method is not a necessary criterion". A two-arm, two-deck study may be judged too small. | No deadline is listed on the author guide | No fixed limit | Double-blind | arXiv and other preprint servers allowed "at any time" |

TMLR's editorial policy says an action editor is assigned "within a week" and that reviewers can submit final recommendations once "at least two weeks have elapsed". The pages give no total time to a decision.

I did not check AIIDE, AAMAS 2027 workshops, or the Reinforcement Learning Conference 2027.

## 5. Recommendation and timeline

Target IEEE CoG 2027, Track 01 (AI for Game-Playing), as a full paper. It is the only option with a strong topic fit, it is peer-reviewed and archival in IEEE Xplore, and its double-blind review suits a first-time author.

No venue that fits this work can return a peer-reviewed acceptance before a December or January application. The only decisions due before January come from AAAI-27 workshops (2 December), and none of those fits the topic. The CoG full-paper notification is 3 May 2027. What the application can truthfully list in January is a public preprint, the code and showcase, and "submitted to IEEE CoG 2027" once the paper is in CMT. The portal opens on 27 November, so you can submit well before the 1 March deadline.

| Dates (2026 to 2027) | Step |
| --- | --- |
| 15 to 22 Nov | Settle the Option A framing. Add the teacher and baseline evaluation, and write and freeze the analysis plan (items 1 to 4). |
| 23 Nov to 6 Dec | Rerun at scale on the VM. Run the seed-level and equivalence statistics and the agreement analysis (items 3 and 5). Add the deck diagnostics (item 6). |
| 27 Nov | The CoG submission portal opens. Email the program chairs to ask about the preprint policy under double-blind review. |
| 7 to 20 Dec | Write the related work and the full 8-page draft in IEEE two-column format, with references counted in the limit (items 7 and 8). |
| 21 Dec to 3 Jan | Faculty read-through and revision. Build the reproducibility release with a DOI (items 9 and 10). |
| By 8 Jan | Submit to CoG. If the chairs allow it, post the preprint and link it in the application. Apply. |

An optional fast path is the AAAI-27 MultiRobust workshop (deadline 20 November, decision 2 December). It is non-archival, so it would not block a later CoG submission. I do not recommend it: the topic fit is weak, and six days is not enough to correct the method description, scale up the seeds, and redo the statistics.

## 6. Verified related-work candidates

I checked titles, authors, and venues on arXiv, Crossref, or the publisher on 14 November 2026. That confirms the citations exist; it does not confirm what each paper says. Read each one before citing it for a specific claim.

- Vinyals, O., et al. (2019). Grandmaster level in StarCraft II using multi-agent reinforcement learning. *Nature*, 575, 350-354. https://doi.org/10.1038/s41586-019-1724-z
- Lanctot, M., et al. (2017). A Unified Game-Theoretic Approach to Multiagent Reinforcement Learning. NIPS 2017. arXiv:1711.00832
- Strouse, D. J., et al. (2021). Collaborating with Humans without Human Data. NeurIPS 2021. arXiv:2110.08176
- Ross, S., Gordon, G. J., & Bagnell, J. A. (2011). A Reduction of Imitation Learning and Structured Prediction to No-Regret Online Learning. AISTATS 2011. arXiv:1011.0686
- Kirk, R., Zhang, A., Grefenstette, E., & Rocktäschel, T. (2023). A Survey of Zero-shot Generalisation in Deep Reinforcement Learning. *JAIR*, 76, 201-264. https://doi.org/10.1613/jair.1.14174
- Cobbe, K., et al. (2018). Quantifying Generalization in Reinforcement Learning. arXiv:1812.02341 (venue not confirmed on the arXiv record)
- Agarwal, R., et al. (2021). Deep Reinforcement Learning at the Edge of the Statistical Precipice. NeurIPS 2021. arXiv:2108.13264
- Henderson, P., et al. (2018). Deep Reinforcement Learning that Matters. AAAI 2018. arXiv:1709.06560
- Hoover, A. K., Togelius, J., Lee, S., & de Mesentier Silva, F. (2019). The Many AI Challenges of Hearthstone. arXiv:1907.06562 (described as a journal paper; venue not confirmed)
- Xi, W., et al. (2023). Mastering Strategy Card Game (Legends of Code and Magic) via End-to-End Policy and Optimistic Smooth Fictitious Play. arXiv:2303.04096
- Hua, D., et al. (2026). PTCG-Bench: Can LLM Agents Master Pokémon Trading Card Game? arXiv:2605.29653

## Sources

All accessed 14 November 2026.

- AAAI-27 workshop program: https://aaai.org/conference/aaai/aaai-27/aaai-27-workshop-program/
- AAAI-27 MultiRobust workshop: https://robust-ai-2027.github.io/aaai27_workshop
- AAAI-27 Evaluation for AI Scientists workshop: https://eval-ai-scientists.github.io/aaai27/
- AAAI-27 Student Abstract call: https://aaai.org/conference/aaai/aaai-27/student-abstract-and-poster-program-call-for-proposals/
- AAAI-27 Undergraduate Consortium call: https://aaai.org/conference/aaai/aaai-27/undergraduate-consortium-call-for-participation/
- NeurIPS 2026 call for workshops: https://neurips.cc/Conferences/2026/CallForWorkshops
- ICLR 2027 call for workshops: https://iclr.cc/Conferences/2027/CallForWorkshops
- ICML 2027 dates: https://icml.cc/Conferences/2027/Dates
- IEEE CoG 2027: https://cog2027.u-aizu.ac.jp/ (sections `sections/dates.html` and `sections/submit.html`)
- TMLR author guide, acceptance criteria, editorial policies: https://jmlr.org/tmlr/author-guide.html, https://jmlr.org/tmlr/acceptance-criteria.html, https://jmlr.org/tmlr/editorial-policies.html
- arXiv API and Crossref records for the papers in section 6
