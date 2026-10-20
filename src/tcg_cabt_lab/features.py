"""Compact numerical feature representation of CABT observations and actions."""

import time
from collections.abc import Mapping
from typing import Any

import numpy as np

from tcg_cabt_lab.catalog import get_attack_by_id

STATE_DIM: int = 72
OPTION_DIM: int = 16
TOTAL_FEATURE_DIM: int = STATE_DIM + OPTION_DIM  # 88


def _get_attacks() -> Mapping[int, Any]:
    try:
        return get_attack_by_id()
    except Exception:
        return {}


def extract_state_features(observation: Mapping[str, Any]) -> np.ndarray:
    """Extract a 72-dimensional normalized float32 vector from a sanitized observation.

    Layout:
      0..11: Global match context (turn, player indices, round, turn flags, option counts)
      12..41: Active player state (prize, hand, deck, discard, active Pokemon, 5 bench slots)
      42..71: Opponent player state (prize, handCount, deck, discard, active Pokemon, 5 bench slots)
    """
    feats = np.zeros(STATE_DIM, dtype=np.float32)

    current = observation.get("current")
    if not isinstance(current, Mapping):
        return feats

    # 0..11: Global context
    turn = float(current.get("turn", 0) or 0)
    feats[0] = min(turn, 50.0) / 50.0
    your_idx = int(current.get("yourIndex", 0) or 0)
    feats[1] = 1.0 if your_idx == 1 else 0.0
    first_player = int(current.get("firstPlayer", 0) or 0)
    feats[2] = 1.0 if first_player == 1 else 0.0
    feats[3] = 1.0 if current.get("supporterPlayed") else 0.0
    feats[4] = 1.0 if current.get("stadiumPlayed") else 0.0
    feats[5] = 1.0 if current.get("energyAttached") else 0.0
    feats[6] = 1.0 if current.get("retreated") else 0.0

    sel = observation.get("select")
    if isinstance(sel, Mapping):
        min_c = float(sel.get("minCount", 0) or 0)
        max_c = float(sel.get("maxCount", 1) or 1)
        opts = sel.get("option", [])
        feats[7] = min_c / 10.0
        feats[8] = max_c / 10.0
        feats[9] = float(len(opts)) / 30.0

    feats[10] = float(current.get("round", 0) or 0) / 10.0
    feats[11] = 1.0 if current.get("stadium") else 0.0

    # Extract player state: active player then opponent player
    players = current.get("players")
    if not isinstance(players, list) or len(players) < 2:
        return feats

    self_p = players[your_idx] if 0 <= your_idx < len(players) else {}
    opp_idx = 1 - your_idx
    opp_p = players[opp_idx] if 0 <= opp_idx < len(players) else {}

    def populate_player_block(p_dict: Mapping[str, Any], offset: int) -> None:
        if not isinstance(p_dict, Mapping):
            return

        # 0..3: Deck, hand, prize, discard counts
        feats[offset + 0] = float(p_dict.get("deckCount", 0) or 0) / 60.0
        hand = p_dict.get("hand")
        hand_len = len(hand) if isinstance(hand, list) else int(p_dict.get("handCount", 0) or 0)
        feats[offset + 1] = float(hand_len) / 20.0
        prize = p_dict.get("prize")
        prize_count = len(prize) if isinstance(prize, list) else int(prize or 0)
        feats[offset + 2] = float(prize_count) / 6.0
        discard = p_dict.get("discard")
        feats[offset + 3] = float(len(discard) if isinstance(discard, list) else 0) / 60.0

        # 4..8: Status conditions
        feats[offset + 4] = 1.0 if p_dict.get("poisoned") else 0.0
        feats[offset + 5] = 1.0 if p_dict.get("burned") else 0.0
        feats[offset + 6] = 1.0 if p_dict.get("asleep") else 0.0
        feats[offset + 7] = 1.0 if p_dict.get("paralyzed") else 0.0
        feats[offset + 8] = 1.0 if p_dict.get("confused") else 0.0

        # 9..14: Active Pokemon
        active_list = p_dict.get("active")
        if (
            isinstance(active_list, list)
            and len(active_list) > 0
            and isinstance(active_list[0], Mapping)
        ):
            act = active_list[0]
            feats[offset + 9] = 1.0
            hp = float(act.get("hp", 0) or 0)
            max_hp = float(act.get("maxHp", 1) or 1)
            feats[offset + 10] = min(hp / max(1.0, max_hp), 1.0)
            feats[offset + 11] = min(max_hp, 340.0) / 340.0
            energies = act.get("energies")
            feats[offset + 12] = float(len(energies) if isinstance(energies, list) else 0) / 10.0
            tools = act.get("tools")
            feats[offset + 13] = float(len(tools) if isinstance(tools, list) else 0) / 2.0
            feats[offset + 14] = 1.0 if act.get("appearThisTurn") else 0.0

        # 15..29: Bench Pokemon (up to 5 slots, 3 dims each: occupied, hp_ratio, energies)
        bench_list = p_dict.get("bench")
        if isinstance(bench_list, list):
            for slot_idx in range(min(5, len(bench_list))):
                bench_mon = bench_list[slot_idx]
                if isinstance(bench_mon, Mapping):
                    base = offset + 15 + slot_idx * 3
                    feats[base + 0] = 1.0
                    b_hp = float(bench_mon.get("hp", 0) or 0)
                    b_max_hp = float(bench_mon.get("maxHp", 1) or 1)
                    feats[base + 1] = min(b_hp / max(1.0, b_max_hp), 1.0)
                    b_energies = bench_mon.get("energies")
                    e_len = len(b_energies) if isinstance(b_energies, list) else 0
                    feats[base + 2] = float(e_len) / 10.0

    populate_player_block(self_p, offset=12)
    populate_player_block(opp_p, offset=42)

    return feats


def extract_option_features(
    option: Mapping[str, Any],
    index: int,
    total_options: int,
    attacks: Mapping[int, Any] | None = None,
) -> np.ndarray:
    """Extract a 16-dimensional normalized float32 vector for a candidate selection option.

    Layout:
      0..9: Option type flags (attack, damage_norm, bench_evolve, energy, trainer,
            context_choice, target, special_action, pass_end, other)
      10..12: In-play area and target flags (in_play_active, in_play_bench, has_target)
      13..15: Ordering and positional signals (is_first, is_last, index_norm)
    """
    feats = np.zeros(OPTION_DIM, dtype=np.float32)
    if not isinstance(option, Mapping):
        return feats

    opt_type = option.get("type", -1)

    # 0: Attack (type 13)
    if opt_type == 13:
        feats[0] = 1.0
        if attacks is None:
            attacks = _get_attacks()
        attack_id = option.get("attackId")
        if isinstance(attack_id, int):
            dmg = float(attacks.get(attack_id, {}).get("damage", 0) or 0)
            feats[1] = min(dmg, 300.0) / 300.0
    elif opt_type == 8:
        # 2: Bench or evolve
        feats[2] = 1.0
    elif opt_type == 9:
        # 3: Attach energy
        feats[3] = 1.0
    elif opt_type == 7:
        # 4: Trainer
        feats[4] = 1.0
    elif opt_type == 3:
        # 5: Context card / choice
        feats[5] = 1.0
    elif opt_type in (1, 2):
        # 6: Target / Pokemon selection
        feats[6] = 1.0
    elif opt_type in (10, 12):
        # 7: Special action / retreat / ability
        feats[7] = 1.0
    elif opt_type == 14:
        # 8: Pass / End Turn
        feats[8] = 1.0
    else:
        # 9: Other / unrecognized
        feats[9] = 1.0

    # 10..12: Location & Target
    in_play_area = option.get("inPlayArea")
    in_play_index = option.get("inPlayIndex", 0)
    if in_play_area == 4:
        if in_play_index == 0:
            feats[10] = 1.0  # active
        else:
            feats[11] = 1.0  # bench

    if option.get("targetArea") is not None:
        feats[12] = 1.0

    # 13..15: Order and position
    feats[13] = 1.0 if index == 0 else 0.0
    feats[14] = 1.0 if (total_options > 0 and index == total_options - 1) else 0.0
    feats[15] = float(index) / 20.0

    return feats


def extract_candidate_matrix(
    observation: Mapping[str, Any],
    attacks: Mapping[int, Any] | None = None,
) -> np.ndarray:
    """Extract an (N, 88) candidate feature matrix for all options in select.

    If select is missing or option list is empty, returns an empty (0, 88) float32 matrix.
    """
    sel = observation.get("select")
    if not isinstance(sel, Mapping):
        return np.empty((0, TOTAL_FEATURE_DIM), dtype=np.float32)

    options = sel.get("option", [])
    if not isinstance(options, list) or not options:
        return np.empty((0, TOTAL_FEATURE_DIM), dtype=np.float32)

    state_vec = extract_state_features(observation)
    n_opts = len(options)
    matrix = np.empty((n_opts, TOTAL_FEATURE_DIM), dtype=np.float32)

    if attacks is None:
        attacks = _get_attacks()

    for idx, opt in enumerate(options):
        opt_vec = extract_option_features(
            opt if isinstance(opt, Mapping) else {},
            index=idx,
            total_options=n_opts,
            attacks=attacks,
        )
        matrix[idx, :STATE_DIM] = state_vec
        matrix[idx, STATE_DIM:] = opt_vec

    return matrix


def measure_representation_profile(num_trials: int = 200) -> dict[str, Any]:
    """Measure observation and candidate feature extraction sizes, memory, and latency.

    Returns:
        Structured dictionary summarizing dimensionalities, memory footprints,
        and latency benchmarks.
    """
    dummy_obs: dict[str, Any] = {
        "current": {
            "turn": 5,
            "yourIndex": 0,
            "firstPlayer": 0,
            "supporterPlayed": False,
            "stadiumPlayed": False,
            "energyAttached": True,
            "retreated": False,
            "round": 3,
            "stadium": None,
            "players": [
                {
                    "deckCount": 45,
                    "hand": [1, 2, 3, 4],
                    "prize": [1, 2, 3, 4, 5, 6],
                    "discard": [7, 8],
                    "poisoned": False,
                    "burned": False,
                    "asleep": False,
                    "paralyzed": False,
                    "confused": False,
                    "active": [{"hp": 120, "maxHp": 150, "energies": [1, 2], "tools": []}],
                    "bench": [{"hp": 70, "maxHp": 70, "energies": []}],
                },
                {
                    "deckCount": 48,
                    "hand": None,
                    "handCount": 5,
                    "prize": [1, 2, 3, 4, 5, 6],
                    "discard": [],
                    "poisoned": False,
                    "burned": False,
                    "asleep": False,
                    "paralyzed": False,
                    "confused": False,
                    "active": [{"hp": 90, "maxHp": 90, "energies": [1], "tools": []}],
                    "bench": [],
                },
            ],
        },
        "select": {
            "minCount": 1,
            "maxCount": 1,
            "option": [
                {"type": 13, "attackId": 1},
                {"type": 8, "inPlayArea": 4, "inPlayIndex": 0},
                {"type": 9, "inPlayArea": 4, "inPlayIndex": 0},
                {"type": 7},
                {"type": 14},
            ],
        },
    }

    attacks = _get_attacks()

    # Latency test
    latencies: list[float] = []
    for _ in range(num_trials):
        t0 = time.perf_counter()
        mat = extract_candidate_matrix(dummy_obs, attacks=attacks)
        latencies.append(time.perf_counter() - t0)

    mean_latency_ms = float(np.mean(latencies) * 1000.0)
    p95_latency_ms = float(np.percentile(latencies, 95) * 1000.0)
    matrix_bytes = int(mat.nbytes)

    return {
        "state_dimension": STATE_DIM,
        "option_dimension": OPTION_DIM,
        "total_feature_dimension": TOTAL_FEATURE_DIM,
        "sample_options_count": len(dummy_obs["select"]["option"]),
        "matrix_shape": list(mat.shape),
        "matrix_bytes": matrix_bytes,
        "mean_latency_ms": round(mean_latency_ms, 4),
        "p95_latency_ms": round(p95_latency_ms, 4),
        "budget_limit_ms": 50.0,
        "budget_limit_bytes": 536870912,
        "within_budget": mean_latency_ms < 50.0 and matrix_bytes < 536870912,
    }
