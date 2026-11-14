# Related work (draft)

Draft text for the IEEE CoG 2027 submission. Citation keys in brackets match the reference list at the end. Each claim was checked against the cited paper on 14 November 2026; the last section records how.

## Card games as a testbed

Collectible card games combine hidden information with a branching factor that changes with the game state and is often large. Hoover et al. [Hoover19] note that these games are relatively understudied in AI research despite their popularity, and lay out a range of AI challenges that Hearthstone poses. For a competition-level agent, Xi et al. [Xi23] describe an end-to-end policy and an optimistic smooth fictitious play method for the two-stage game Legends of Code and Magic, and report winning both the official LoCM 1.5 track and the bonus LoCM 1.2 track of the COG 2022 competition. The Pokémon Trading Card Game has received less attention. PTCG-Bench [Hua26] evaluates large language model agents on it, both for play within one environment and for improvement from accumulated experience. We study a different agent class: a 2,881-parameter option-scoring network that runs in well under a millisecond, evaluated under a fixed inference budget.

## Opponent diversity and generalization

Several lines of work argue that the opponents an agent trains against determine how far it generalizes. Lanctot et al. [Lanctot17] show that policies learned by independent reinforcement learning can overfit to the policies of the other agents seen in training, and propose best responses to mixtures of policies as a remedy. Strouse et al. [Strouse21] reach a similar view in cooperative play, arguing that a diverse set of training partners is the crux of generalizing to new partners. Both works train agents by reinforcement learning from play. Our study asks the same question about opponent diversity for an agent trained by imitation, where the opponent affects only which game states the demonstrations visit.

Work on generalization in reinforcement learning more broadly separates training and test conditions. Cobbe et al. [Cobbe19] build distinct training and test sets of procedurally generated environments and find that agents overfit to surprisingly large training sets. Kirk et al. [Kirk23] survey zero-shot generalization and its benchmarks. We follow this practice by keeping the test deck families entirely out of training, with a disjointness check between the splits.

## Imitation under distribution shift

In imitation learning, the learner's own mistakes lead it to states the demonstrator did not visit, which breaks the assumption that training and test data are identically distributed. Ross et al. [Ross11] describe this compounding of errors and propose DAgger, which collects trajectories with the current learned policy and trains the next policy to mimic the expert on all the data gathered so far. Our two arms differ only in the demonstration states: the teacher plays one fixed opponent in one arm and a mixture of three in the other. The student matches the teacher on at least 99.8% of held-out decisions in both arms, so we can ask whether a change of this kind moves the student's play at all.

## Statistical practice

Henderson et al. [Henderson18] document how non-determinism in environments, together with variance in the methods themselves, makes reported reinforcement learning results hard to interpret without significance measures. Agarwal et al. [Agarwal21] show that point estimates from a few training runs can mislead, and recommend interval estimates of aggregate performance. Both concerns apply to our setting: the CABT engine shuffles with a system entropy source, so no game can be replayed from a seed, and a 3-seed run of our own study moved the estimated difference between arms from -0.55 to +6.95 points. We therefore treat the training seed as the unit of analysis, report a cluster-bootstrap interval, and preregister an equivalence margin so that a null result can be stated with a bound.

## References

- [Agarwal21] R. Agarwal, M. Schwarzer, P. S. Castro, A. Courville, M. G. Bellemare. Deep Reinforcement Learning at the Edge of the Statistical Precipice. Advances in Neural Information Processing Systems (NeurIPS), 2021. arXiv:2108.13264.
- [Cobbe19] K. Cobbe, O. Klimov, C. Hesse, T. Kim, J. Schulman. Quantifying Generalization in Reinforcement Learning. Proceedings of the 36th International Conference on Machine Learning (ICML), PMLR 97:1282-1289, 2019.
- [Henderson18] P. Henderson, R. Islam, P. Bachman, J. Pineau, D. Precup, D. Meger. Deep Reinforcement Learning that Matters. AAAI Conference on Artificial Intelligence, 2018. arXiv:1709.06560.
- [Hoover19] A. K. Hoover, J. Togelius, S. Lee, F. de Mesentier Silva. The Many AI Challenges of Hearthstone. KI - Künstliche Intelligenz, 34(1):33-43. Published online 2019. doi:10.1007/s13218-019-00615-z.
- [Hua26] D. Hua, Y. Sun, R. Huang, C. Wang, F. Gao, Y. Yang. PTCG-Bench: Can LLM Agents Master Pokémon Trading Card Game? Findings of the Association for Computational Linguistics: EMNLP 2026, pages 36084-36099. https://aclanthology.org/2026.findings-emnlp.1689/
- [Kirk23] R. Kirk, A. Zhang, E. Grefenstette, T. Rocktäschel. A Survey of Zero-shot Generalisation in Deep Reinforcement Learning. Journal of Artificial Intelligence Research, 76:201-264, 2023. doi:10.1613/jair.1.14174.
- [Lanctot17] M. Lanctot, V. Zambaldi, A. Gruslys, A. Lazaridou, K. Tuyls, J. Perolat, D. Silver, T. Graepel. A Unified Game-Theoretic Approach to Multiagent Reinforcement Learning. Advances in Neural Information Processing Systems (NIPS), 2017. arXiv:1711.00832.
- [Ross11] S. Ross, G. J. Gordon, J. A. Bagnell. A Reduction of Imitation Learning and Structured Prediction to No-Regret Online Learning. Proceedings of the Fourteenth International Conference on Artificial Intelligence and Statistics (AISTATS), PMLR 15:627-635, 2011.
- [Strouse21] D. J. Strouse, K. R. McKee, M. Botvinick, E. Hughes, R. Everett. Collaborating with Humans without Human Data. Advances in Neural Information Processing Systems (NeurIPS), 2021. arXiv:2110.08176.
- [Xi23] W. Xi, Y. Zhang, C. Xiao, X. Huang, S. Deng, H. Liang, J. Chen, P. Sun. Mastering Strategy Card Game (Legends of Code and Magic) via End-to-End Policy and Optimistic Smooth Fictitious Play. arXiv:2303.04096, 2023.

## Citation check (14 November 2026)

| Key | Authors | Venue | Claims |
| --- | --- | --- | --- |
| Agarwal21 | arXiv record | arXiv comment (NeurIPS 2021, Outstanding Paper Award) and Semantic Scholar | Abstract |
| Cobbe19 | arXiv record | PMLR v97 page | Abstract |
| Henderson18 | arXiv record | arXiv comment (AAAI 2018) and Semantic Scholar | Abstract |
| Hoover19 | Crossref | Crossref (Springer DOI) | Full text: hidden information, variable and often high branching factor, "relatively understudied" |
| Hua26 | ACL Anthology (published order differs from arXiv) | ACL Anthology | Abstract |
| Kirk23 | arXiv record | arXiv journal reference and Semantic Scholar | Abstract |
| Lanctot17 | arXiv record | arXiv comment (NIPS 2017) and Semantic Scholar | Abstract |
| Ross11 | arXiv record and PMLR | PMLR v15 page | Full text: compounding of errors; DAgger collects trajectories with the current policy and trains on the aggregate dataset |
| Strouse21 | arXiv record | arXiv comment (NeurIPS 2021) and Semantic Scholar | Full text: "the crux of the problem is to produce a diverse set of training partners"; agents trained with the VMPO reinforcement learning algorithm |
| Xi23 | arXiv record | arXiv only; Semantic Scholar lists no peer-reviewed version | Full text: won the official LoCM 1.5 and bonus LoCM 1.2 tracks at COG 2022 |

Still open:

- Page numbers for the NeurIPS, NIPS and AAAI papers come only from Semantic Scholar, so they are left out. Add them from the proceedings if the template needs them.
- Hoover19 volume 34 was published online in 2019. Check whether the print issue is 2020 before choosing the year.
- The CABT engine documentation and the Kaggle 20th-place write-up listed in RESEARCH.md are not cited here, because they have not been opened. Cite them in the environment section once checked.
- No claim here is about what is novel. State novelty only after a literature search on imitation with varied demonstration opponents.
