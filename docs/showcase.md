# Public showcase

The first public deliverable is a tournament you can inspect: compact learned agents, a heuristic, and reproduced references playing the same dated deck pool. A newcomer can watch a match and understand the prize race. An experienced player can inspect the choices, deck matchups, failures, and evidence behind the result.

## Tournament view

Show the tested agents, deck families, matchup results, uncertainty, and compute budget. Each result links to its evaluation run. Explain how failures and ties affect the score. Let readers switch between aggregate performance and individual matchups without implying that one average captures every deck.

## Match view

Render evaluated CABT matches with Active and Bench positions, visible cards, damage, energy, discard, and remaining Prize cards. Include a turn timeline and plain descriptions of the action taken. Mark spectator-only information clearly so it cannot be mistaken for information available to the agent.

Initially show the recorded action and its outcome. Add alternative-policy choices when they are actually computed from the same observation. Label policy scores as scores; do not present them as calibrated win probabilities. Calling an action a mistake requires repeated counterfactual rollout evidence, not a single loss or a language-model explanation.

## First release

Use stored matches and compact result files from reproducible runs. Include a readable explanation of the research question, representative wins and losses, and a way to inspect the full matchup table. Card images and exported traces need a permitted release path before they appear in the demo.

The visual design should make the board and decisions easy to read, with deliberate typography and restrained color. Review rendered desktop and mobile states before publishing. The current repository contains this brief; the browser interface has not been implemented.
