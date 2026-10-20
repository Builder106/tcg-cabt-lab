"""Tests for compact numerical feature representation."""

import numpy as np

from tcg_cabt_lab.features import (
    OPTION_DIM,
    STATE_DIM,
    TOTAL_FEATURE_DIM,
    extract_candidate_matrix,
    extract_option_features,
    extract_state_features,
    measure_representation_profile,
)


def test_feature_dimensions_and_constants() -> None:
    assert STATE_DIM == 72
    assert OPTION_DIM == 16
    assert TOTAL_FEATURE_DIM == 88


def test_extract_state_features_empty_and_default() -> None:
    empty_vec = extract_state_features({})
    assert isinstance(empty_vec, np.ndarray)
    assert empty_vec.shape == (72,)
    assert empty_vec.dtype == np.float32
    assert np.all(empty_vec == 0.0)


def test_extract_state_features_structure() -> None:
    sample_obs = {
        "current": {
            "turn": 10,
            "yourIndex": 0,
            "firstPlayer": 1,
            "supporterPlayed": True,
            "stadiumPlayed": False,
            "energyAttached": True,
            "retreated": False,
            "round": 2,
            "stadium": 100,
            "players": [
                {
                    "deckCount": 50,
                    "hand": [1, 2, 3],
                    "prize": [1, 2, 3, 4],
                    "discard": [5],
                    "poisoned": True,
                    "burned": False,
                    "asleep": False,
                    "paralyzed": False,
                    "confused": False,
                    "active": [{"hp": 80, "maxHp": 100, "energies": [1, 2], "tools": [1]}],
                    "bench": [{"hp": 60, "maxHp": 60, "energies": [1]}],
                },
                {
                    "deckCount": 52,
                    "hand": None,
                    "handCount": 4,
                    "prize": [1, 2, 3, 4, 5],
                    "discard": [],
                    "poisoned": False,
                    "burned": False,
                    "asleep": False,
                    "paralyzed": False,
                    "confused": False,
                    "active": [{"hp": 120, "maxHp": 120, "energies": [], "tools": []}],
                    "bench": [],
                },
            ],
        },
        "select": {
            "minCount": 1,
            "maxCount": 1,
            "option": [{"type": 13, "attackId": 1}, {"type": 14}],
        },
    }

    vec = extract_state_features(sample_obs)
    assert vec.shape == (72,)
    # Turn: 10 / 50 = 0.2
    assert np.isclose(vec[0], 0.2)
    # yourIndex: 0
    assert vec[1] == 0.0
    # firstPlayer: 1
    assert vec[2] == 1.0
    # supporterPlayed: 1.0
    assert vec[3] == 1.0
    # energyAttached: 1.0
    assert vec[5] == 1.0
    # prize active: 4/6
    assert np.isclose(vec[14], 4.0 / 6.0)
    # poisoned active: 1.0
    assert vec[16] == 1.0
    # active mon present: 1.0
    assert vec[21] == 1.0
    # active mon hp ratio: 80/100 = 0.8
    assert np.isclose(vec[22], 0.8)


def test_extract_option_features_types() -> None:
    # Attack option
    attack_opt = {"type": 13, "attackId": 999999}
    vec_att = extract_option_features(attack_opt, index=0, total_options=3)
    assert vec_att.shape == (16,)
    assert vec_att[0] == 1.0  # is attack
    assert vec_att[13] == 1.0  # is first option

    # Bench option
    bench_opt = {"type": 8, "inPlayArea": 4, "inPlayIndex": 1}
    vec_bench = extract_option_features(bench_opt, index=1, total_options=3)
    assert vec_bench[2] == 1.0  # is bench/evolve
    assert vec_bench[11] == 1.0  # inPlayArea == 4 and inPlayIndex > 0 (bench)

    # Pass option
    pass_opt = {"type": 14}
    vec_pass = extract_option_features(pass_opt, index=2, total_options=3)
    assert vec_pass[8] == 1.0  # is pass
    assert vec_pass[14] == 1.0  # is last option


def test_extract_candidate_matrix() -> None:
    obs = {
        "current": {"turn": 1, "yourIndex": 0, "players": [{}, {}]},
        "select": {
            "option": [
                {"type": 13, "attackId": 1},
                {"type": 8},
                {"type": 9},
            ]
        },
    }
    matrix = extract_candidate_matrix(obs)
    assert isinstance(matrix, np.ndarray)
    assert matrix.shape == (3, 88)
    assert matrix.dtype == np.float32

    # State features are identical across candidate rows
    assert np.all(matrix[0, :72] == matrix[1, :72])
    # Option features vary
    assert not np.all(matrix[0, 72:] == matrix[1, 72:])


def test_representation_budget_adherence() -> None:
    profile = measure_representation_profile(num_trials=50)
    assert profile["within_budget"] is True
    assert profile["mean_latency_ms"] < 5.0  # Substantially under 50ms
    assert profile["matrix_bytes"] < 100000  # Substantially under 512 MiB
