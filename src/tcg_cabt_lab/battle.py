"""Execute and record reproducible CABT battles between agents."""

from collections.abc import Callable, Mapping, Sequence
from typing import Any

from kaggle_environments import make

from tcg_cabt_lab.agent import RandomAgent, sanitize_observation
from tcg_cabt_lab.catalog import EXPECTED_CATALOG_SHA256, get_catalog_sha256
from tcg_cabt_lab.deck import REFERENCE_DECK, validate_deck

KAGGLE_ENVIRONMENTS_VERSION = "1.33.0"
CABT_SPEC_VERSION = "1.0.0"


def _normalize_agent(
    agent: Callable[..., list[int]],
    seat: int = 0,
    decisions: list[dict[str, Any]] | None = None,
) -> Callable[..., list[int]]:
    def wrapped(observation: Mapping[str, Any], configuration: Any = None) -> list[int]:
        try:
            action = agent(observation, configuration)
        except TypeError:
            action = agent(observation)

        # Deck submission has no selection; only in-game choices are decisions
        current = observation.get("current")
        if decisions is not None and observation.get("select") is not None and current:
            scores = getattr(agent, "last_scores", None)
            decisions.append(
                {
                    "seat": seat,
                    "turn": current.get("turn"),
                    "option_count": len(observation["select"].get("option") or []),
                    "action": list(action),
                    "scores": list(scores) if scores is not None else None,
                }
            )
        return action

    return wrapped


def run_battle(
    agent_p0: Callable[..., list[int]] | None = None,
    agent_p1: Callable[..., list[int]] | None = None,
    deck_p0: Sequence[int] | None = None,
    deck_p1: Sequence[int] | None = None,
    seed_p0: int = 11,
    seed_p1: int = 22,
    best_of: int = 1,
    record_replay: bool = False,
) -> dict[str, Any]:
    """Run a complete CABT battle between two agents.

    Args:
        agent_p0: Callable agent for player 0. Defaults to RandomAgent(seed=seed_p0).
        agent_p1: Callable agent for player 1. Defaults to RandomAgent(seed=seed_p1).
        deck_p0: 60-card deck for player 0. Defaults to REFERENCE_DECK.
        deck_p1: 60-card deck for player 1. Defaults to REFERENCE_DECK.
        seed_p0: Seed for player 0's default RandomAgent.
        seed_p1: Seed for player 1's default RandomAgent.
        best_of: Best-of match configuration (1 for single battle, 3 for BO3).
        record_replay: Also return the engine's spectator frames and each agent
            decision (action and any option scores) under the "replay" key.

    Returns:
        Structured dictionary containing run metadata, player configurations,
        step-by-step game logs, and final battle outcome.
    """
    valid_deck_p0 = validate_deck(deck_p0 if deck_p0 is not None else REFERENCE_DECK)
    valid_deck_p1 = validate_deck(deck_p1 if deck_p1 is not None else REFERENCE_DECK)

    raw_p0 = agent_p0 if agent_p0 is not None else RandomAgent(seed=seed_p0, deck=valid_deck_p0)
    raw_p1 = agent_p1 if agent_p1 is not None else RandomAgent(seed=seed_p1, deck=valid_deck_p1)

    decisions: list[dict[str, Any]] | None = [] if record_replay else None
    p0 = _normalize_agent(raw_p0, 0, decisions)
    p1 = _normalize_agent(raw_p1, 1, decisions)

    env = make("cabt", configuration={"bo": best_of})
    raw_steps = env.run([p0, p1])

    recorded_steps: list[dict[str, Any]] = []
    for step_index, step_pair in enumerate(raw_steps):
        s0, s1 = step_pair[0], step_pair[1]
        active_index = 0 if s0.status == "ACTIVE" else (1 if s1.status == "ACTIVE" else None)

        action_taken = None
        if active_index is not None:
            action_taken = s0.action if active_index == 0 else s1.action

        obs_record: dict[str, Any] | None = None
        if active_index is not None:
            active_state = s0 if active_index == 0 else s1
            obs_record = sanitize_observation(active_state.observation)

        recorded_steps.append(
            {
                "step": step_index,
                "active_player": active_index,
                "action": action_taken,
                "status": [s0.status, s1.status],
                "reward": [s0.reward, s1.reward],
                "observation": obs_record,
            }
        )

    final_state_p0 = raw_steps[-1][0]
    final_state_p1 = raw_steps[-1][1]

    winner: int | str
    if (final_state_p0.reward or 0) > (final_state_p1.reward or 0):
        winner = 0
    elif (final_state_p1.reward or 0) > (final_state_p0.reward or 0):
        winner = 1
    else:
        winner = "draw"

    catalog_hash = get_catalog_sha256()

    log: dict[str, Any] = {
        "metadata": {
            "engine": "cabt",
            "spec_version": CABT_SPEC_VERSION,
            "package_version": KAGGLE_ENVIRONMENTS_VERSION,
            "card_catalog_sha256": catalog_hash,
            "expected_catalog_sha256": EXPECTED_CATALOG_SHA256,
            "best_of": best_of,
            "total_steps": len(raw_steps),
        },
        "players": [
            {
                "index": 0,
                "seed": seed_p0 if agent_p0 is None else None,
                "deck": valid_deck_p0,
                "final_status": final_state_p0.status,
                "final_reward": final_state_p0.reward,
            },
            {
                "index": 1,
                "seed": seed_p1 if agent_p1 is None else None,
                "deck": valid_deck_p1,
                "final_status": final_state_p1.status,
                "final_reward": final_state_p1.reward,
            },
        ],
        "outcome": {
            "winner": winner,
            "rewards": [final_state_p0.reward, final_state_p1.reward],
            "statuses": [final_state_p0.status, final_state_p1.status],
        },
        "steps": recorded_steps,
    }
    if record_replay:
        # Spectator frames include both hands, deck order, and Prize identities
        log["replay"] = {
            "frames": env.steps[0][0].get("visualize") or [],
            "decisions": decisions,
        }
    return log
