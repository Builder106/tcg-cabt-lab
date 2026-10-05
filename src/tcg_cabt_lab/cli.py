"""Sample a CABT choice request without starting a simulator."""

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from random import Random

from tcg_cabt_lab.baseline import choose_random_action


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subcommands = parser.add_subparsers(dest="command", required=True)
    sample = subcommands.add_parser("sample", help="sample indices from an observation JSON file")
    sample.add_argument("observation", type=Path)
    sample.add_argument("--seed", type=int, default=11)
    args = parser.parse_args(argv)

    try:
        observation: object = json.loads(args.observation.read_text(encoding="utf-8"))
        action = choose_random_action(observation, Random(args.seed))
    except (OSError, UnicodeError, ValueError) as error:
        print(f"Invalid choice request: {error}", file=sys.stderr)
        return 2

    print(json.dumps(action))
    return 0
