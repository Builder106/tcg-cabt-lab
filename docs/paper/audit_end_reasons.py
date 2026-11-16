"""Count how held-out games end, for the paper's limitations section.

The 30-seed study reports store no replays, so this plays a small separate set of games with
replays on: four study B checkpoints (seeds 2001 and 2002, both arms) and BoardAgent, each in
the 120-game held-out protocol. Run on the VM from the repository root:

    uv run python docs/paper/audit_end_reasons.py

It writes experiments/board/end-reasons-audit.json. The first run of this audit wrote the same
summary to the working directory instead; the games and the code that plays them are unchanged.
"""

import collections
import json
import statistics
import tempfile
from pathlib import Path

from tcg_cabt_lab.board import BoardAgent
from tcg_cabt_lab.experiment import evaluate_agent_on_heldout, evaluate_checkpoint_on_heldout

CHECKPOINTS = "experiments/board/checkpoints"
OUTPUT = Path("experiments/board/end-reasons-audit.json")
PROTOCOL = {
    "opponents": ["heuristic", "first", "random"],
    "eval_seeds": [11, 29, 47, 101, 202],
    "pairs_per_seed": 2,
}


def main() -> None:
    groups: dict[str, list[dict]] = {}
    with tempfile.TemporaryDirectory() as tmp:
        for variant in ("fixed-opponent-pool", "diverse-opponent-pool"):
            for seed in (2001, 2002):
                result = evaluate_checkpoint_on_heldout(
                    f"{CHECKPOINTS}/{variant}-seed-{seed}.json",
                    replay_dir=f"{tmp}/{variant}-{seed}",
                    **PROTOCOL,
                )
                groups[f"student {variant} {seed}"] = result["games"]
        result = evaluate_agent_on_heldout(
            lambda deck: BoardAgent(deck=deck),
            {"id": "board", "agent": "board"},
            replay_dir=f"{tmp}/board",
            **PROTOCOL,
        )
        groups["board teacher"] = result["games"]

    out: dict = {
        "note": (
            "Separate audit, not the study games: the 30-seed reports store no replays. "
            "Students are study B checkpoints for seeds 2001 and 2002 (both arms); the "
            "teacher is BoardAgent. 120 games each."
        ),
        "by_deck": {},
    }
    for family in ("psychic-mewtwo", "colorless-snorlax"):
        games = [g for group in groups.values() for g in group if g["family"] == family]
        out["by_deck"][family] = {
            "games": len(games),
            "end_reasons": dict(collections.Counter(g["end_reason"] for g in games)),
            "median_turns": statistics.median(g["turns"] for g in games),
            "turns_min": min(g["turns"] for g in games),
            "turns_max": max(g["turns"] for g in games),
        }
    OUTPUT.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
