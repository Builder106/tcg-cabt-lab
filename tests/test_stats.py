"""Tests for the seed-level variant comparison."""

import pytest

from tcg_cabt_lab.stats import checkpoint_score, seed_level_analysis


def test_checkpoint_score_weights_families_equally() -> None:
    breakdown = {
        "a": {"wins": 9.0, "total_games": 10},
        "b": {"wins": 10.0, "total_games": 20},
    }
    assert checkpoint_score(breakdown) == pytest.approx(0.7)


def test_identical_variants_are_equivalent_within_margin() -> None:
    scores = [0.50, 0.52, 0.55, 0.58, 0.60]
    result = seed_level_analysis(scores, scores, equivalence_margin=0.05, seed=1)
    assert result["delta"] == 0.0
    assert result["difference_detected"] is False
    assert result["equivalent"] is True
    assert result["ci_95"][0] <= result["ci_90"][0] <= result["ci_90"][1] <= result["ci_95"][1]


def test_separated_variants_show_a_difference() -> None:
    low = [0.40, 0.41, 0.42, 0.43]
    high = [0.70, 0.71, 0.72, 0.73]
    result = seed_level_analysis(low, high, equivalence_margin=0.05, seed=1)
    assert result["delta"] == pytest.approx(0.30)
    assert result["difference_detected"] is True
    assert result["equivalent"] is False


def test_margin_is_optional() -> None:
    result = seed_level_analysis([0.5, 0.6], [0.5, 0.6], seed=1)
    assert result["equivalent"] is None


def test_bootstrap_is_seeded() -> None:
    a, b = [0.4, 0.5, 0.6], [0.5, 0.6, 0.7]
    assert seed_level_analysis(a, b, seed=7) == seed_level_analysis(a, b, seed=7)


def test_needs_two_seeds_per_variant() -> None:
    with pytest.raises(ValueError, match="at least two"):
        seed_level_analysis([0.5], [0.5, 0.6])
