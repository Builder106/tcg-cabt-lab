# Novelty search

Searched on 15 November 2026 for the paper planned for IEEE CoG 2027. The question was whether earlier work has already tested how the opponents a teacher faces during demonstration collection affect a behavior-cloned policy. The search also covered learned agents for the Pokémon Trading Card Game.

## Summary

1. No paper or competition write-up found here runs a controlled test of the demonstration opponent in imitation learning. That gap is real but narrow.
2. The 2026 Kaggle Pokémon TCG AI Battle (6,807 teams) already covers much of the practical ground. Several teams cloned rule-based or learned teachers. The 24th-place team says outright that teacher-generated games widen the training states but inherit the teacher's weaknesses. The 6th-, 7th- and 15th-place teams relied on reinforcement learning (RL) from play, and the 7th-place team reports that every hand-written rule or mechanical teacher it tested cost win rate. A CoG reviewer who followed the competition will know this.
3. Our null result is mostly fixed by how the study is built. `HeuristicAgent` scores each option from its type, its attack damage and whether it targets the active Pokémon, then breaks ties by option order ([agent.py:105-176](../../src/tcg_cabt_lab/agent.py#L105-L176)). The student's 16 option features encode every one of those inputs ([features.py:132-203](../../src/tcg_cabt_lab/features.py#L132-L203)), and the teacher never reads the game state. The opponent pool can change only the game states the teacher visits, which the teacher ignores, so any training set that contains each option type teaches the student the whole rule. That explains the 99.8% to 100% agreement on held-out decks. A reviewer who reads the code will see that the study could not show an effect.

Point 3 is the decision point. As built, the paper's main experiment tests a question with a forced answer.

## What was searched

- arXiv API, title and abstract queries: behavior cloning with opponents and diversity; imitation with opponent pools; imitation and opponents in card games; Pokémon TCG agents; collectible card games with imitation; Hearthstone with supervised learning; demonstration coverage and generalization in behavior cloning.
- Web search for the same topics and for Kaggle Pokémon TCG AI Battle write-ups.
- Kaggle write-ups, read in full from the rendered pages: 6th, 7th, 15th, 20th and 24th place, plus the first page of the Strategy-track write-up list. The other write-ups were not read.
- Semantic Scholar returned rate-limit errors, so it was not used this time.

The search is not exhaustive. It did not cover the full list of Kaggle write-ups, papers published only in proceedings and missing from arXiv, or non-English sources.

## Closest academic work

| Work | What it shows | Bearing on our study |
| --- | --- | --- |
| Laskey et al., DART, CoRL 2017 (arXiv:1703.09327) | Injecting noise into the supervisor while it demonstrates forces it to show recoveries. DART gave 62% higher performance than behavior cloning on a grasping task. | The nearest precedent for changing demonstration states while keeping the same expert. DART helps because the cloned robot makes errors that take it off the supervisor's path. Our student makes almost none. |
| Belkhale, Cui, Sadigh, "Data Quality in Imitation Learning", NeurIPS 2023 (arXiv:2306.02437) | Defines data quality through distribution shift, separating action divergence from transition diversity, and shows that "state diversity is not always beneficial". | Gives the vocabulary for our result: with near-zero action divergence, wider state coverage has nothing to correct. |
| Lin et al., "Data Scaling Laws in Imitation Learning for Robotic Manipulation", 2024 (arXiv:2410.18647) | The diversity of environments and objects matters far more than the number of demonstrations. | The opposite direction: there, diversity matters. Their expert's behavior depends on the scene, and ours does not depend on the state. |
| Schweighofer et al., "A Dataset Perspective on Offline Reinforcement Learning", 2021 (arXiv:2111.04714) | Measures dataset coverage (SACo) and quality (TQ). Behavior cloning does well on high-quality datasets, and coverage matters more for value-based methods. | Supports the reading that coverage matters less for cloning when the demonstrator is fixed. |
| Lei et al., ELA, 2024 (arXiv:2402.18617) | In zero-sum games, outcomes depend on the opponent, and offline learning from diverse demonstrators improves when trajectories are weighted by how exploited they are. | The closest work on opponents in offline imitation for games. It changes the demonstrators, not only the opponents. |
| Carroll et al., Overcooked, NeurIPS 2019 (arXiv:1910.05789) | Agents trained by self-play coordinate poorly with a behavior-cloned human model. | Partner effects in cooperative play. Background only. |
| Ross et al., DAgger, AISTATS 2011 | Already cited in the related-work draft. | Compounding error is the mechanism a coverage change would act on. |

Card-game papers checked: Haluska and Schmid 2024 (arXiv:2404.16689) beat ByteRL in Legends of Code and Magic with behavior cloning followed by RL. Rubin 2026 (arXiv:2609.06816) clones the runner-up's policy, then adds search, and beats ByteRL in a preregistered 10,000-game test. Świechowski et al. 2018 (arXiv:1808.04794) add supervised evaluation to Hearthstone MCTS. Karten et al. 2026 (arXiv:2603.12145) build TCGJax, a Pokémon TCG Pocket environment. None of them varies the demonstration opponents.

## Kaggle Pokémon TCG AI Battle (2026)

The competition thanks the Matsuo Institute, which publishes CABT. The 7th-place write-up gives the field size: "The submitted agent finished 7th of 6,807 teams."

| Write-up | Approach | Statements relevant to us |
| --- | --- | --- |
| 24th place, "A Population-Based Reinforcement Learning Ecosystem" | A GBDT clones leaderboard replays. The GBDT plays 15,000 to 30,000 games, which are distilled into a Transformer, then PPO against 20 to 40 opponent types. | "Rather than repeating the original replays, the teacher experiences different starting hands, player orders, opponents, and game trajectories. This expands the distribution of training states." Also: "the generated data also inherits the teacher's strengths and weaknesses. More games alone do not eliminate those weaknesses." |
| 7th place, "Reading the Cards" | RL against a league of 70+ frozen exploiters. | "We used no behavioural cloning: ladder-replay cloning was measured and dropped." Hand-written rules and mechanical teachers: "every one we tested cost win rate, by up to 36 points." |
| 6th place, "Seek Inspiration, Not Imitation" | Self-play RL only, one policy per opponent archetype. | "Imitation learning is bounded by the existence and level of its exemplar." Opponent-specific policies raised win rate against that opponent by 12 to 14 points (n = 600, replicated twice). |
| 15th place | Population self-play from random initialization. | "used no behavior cloning or human demonstrations." |
| 20th place, "Learning to Play Pokémon TCG" | Contrastive pretraining, then PPO against a league that includes imitation policies. | Imitation-initialized PPO improved fastest at first. Representation-only PPO caught up after about 16M games. |

The [dezcalimese/pokemon-tcg-agent](https://github.com/dezcalimese/pokemon-tcg-agent) README reports a behavior clone with "76.3% held-out top-action accuracy". Its teacher is far harder to copy than ours.

## What this means for the paper

The claim "varying the demonstration opponent does not change a cloned policy" adds little as it stands. The teacher ignores the state, and practitioners already say a clone is bounded by its teacher. Three options:

1. **A state-dependent teacher (recommended).** Write or adopt a teacher whose choices depend on the board: knockout checks, the opponent's remaining HP, energy needed for the next attack, retreat. Freeze a new plan and rerun the scaled study. Now the demonstration states carry information the student must learn, and the question becomes open. The seed-level protocol, equivalence test and teacher-agreement measure all carry over. Cost: about a week, including one roughly 3-hour run.
2. **A methods paper.** Make the evaluation protocol the contribution: preregistered seed-level analysis in CABT. The case study is our own 3-seed runs, whose delta moved from -0.55 to +6.95, against the 30-seed run at -1.22. The forced null stays as a sanity check, stated openly. This is cheaper, but CoG reviewers may find it thin.
3. **Add RL from play.** Test opponent pools where the Kaggle teams say they matter. This is the strongest question but costs the most: weeks of compute design and a much bigger model.

The toy-deck limitation stays under every option. 157 of 180 Snorlax games end with no Pokémon left. Any rerun should consider at least one competition-style deck, subject to the CABT and Kaggle terms.

## Wider search (16 November 2026)

I repeated the search with broader phrasing: arXiv abstract queries combining opponent diversity, unseen opponents, behavior cloning, imitation, self-play and populations with card games, Hearthstone and Pokémon, and one web search for the same question. None returned a controlled test of the demonstration or training opponent for imitation. New items:

- VGC-Bench ([arXiv:2506.10326](https://arxiv.org/abs/2506.10326), AAMAS 2026) covers the competitive Pokémon video game, not the card game. It has behavior cloning and self-play baselines, and reports that as the number of team configurations grows, the best single-team algorithm does worse and is more exploitable but generalizes better to unseen teams. It is cited in the paper.
- StarCraft+ ([arXiv:2512.16444](https://arxiv.org/abs/2512.16444)) benchmarks multi-agent RL against single and mixed adversaries. Its abstract states no result on opponent diversity, so a web-search summary claiming one is unverified and the paper does not cite it.

The paper's novelty sentence is limited to what was searched: arXiv and the public 2026 competition write-ups. The search is still not exhaustive, and it did not cover proceedings that are missing from arXiv.

## Sources

arXiv records (abstracts read on 15 November 2026): [1703.09327](https://arxiv.org/abs/1703.09327), [2306.02437](https://arxiv.org/abs/2306.02437), [2410.18647](https://arxiv.org/abs/2410.18647), [2111.04714](https://arxiv.org/abs/2111.04714), [2402.18617](https://arxiv.org/abs/2402.18617), [1910.05789](https://arxiv.org/abs/1910.05789), [2404.16689](https://arxiv.org/abs/2404.16689), [2609.06816](https://arxiv.org/abs/2609.06816), [1808.04794](https://arxiv.org/abs/1808.04794), [2603.12145](https://arxiv.org/abs/2603.12145).

Kaggle write-ups (rendered text read on 15 November 2026):

- [24th place](https://www.kaggle.com/competitions/pokemon-tcg-ai-battle/writeups/24th-solution-a-population-based-rl-ecosystem)
- [7th place](https://www.kaggle.com/competitions/pokemon-tcg-ai-battle-challenge-strategy/writeups/7th-place-solution-for-the-ptcg-ai-battle-challeng)
- [6th place](https://www.kaggle.com/competitions/pokemon-tcg-ai-battle-challenge-strategy/writeups/new-writeup-1787373273295)
- [15th place](https://www.kaggle.com/competitions/pokemon-tcg-ai-battle/writeups/15th-place-solution)
- [20th place](https://www.kaggle.com/competitions/pokemon-tcg-ai-battle/writeups/20th-place-learning-to-play-pokmon-tcg)

Peer-reviewed venues for the arXiv papers come from their arXiv records (DART: CoRL 2017; Carroll: NeurIPS 2019). Belkhale et al. appear in the NeurIPS 2023 proceedings. Venues for the others were not checked, and they should be confirmed before citing.
