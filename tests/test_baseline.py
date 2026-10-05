from random import Random

import pytest

from tcg_cabt_lab.baseline import choose_random_action


def test_selected_indices_respect_bounds_and_are_distinct() -> None:
    for option_count in range(8):
        for selection_count in range(option_count + 1):
            observation = {
                "select": {
                    "option": [{} for _ in range(option_count)],
                    "minCount": 0,
                    "maxCount": selection_count,
                }
            }
            for seed in range(5):
                action = choose_random_action(observation, Random(seed))
                assert len(action) == selection_count
                assert len(set(action)) == selection_count
                assert all(0 <= index < option_count for index in action)


def test_seed_reproduces_action_without_mutating_observation() -> None:
    options = [{"number": index} for index in range(8)]
    observation = {"select": {"option": options, "minCount": 1, "maxCount": 3}}
    before = [dict(option) for option in options]
    assert choose_random_action(observation, Random(11)) == choose_random_action(
        observation, Random(11)
    )
    assert options == before


@pytest.mark.parametrize(
    "observation",
    [
        None,
        [],
        {},
        {"select": None},
        {"select": {"option": "invalid", "maxCount": 1}},
        {"select": {"option": [], "maxCount": True}},
        {"select": {"option": [], "maxCount": 1.0}},
        {"select": {"option": [], "maxCount": -1}},
        {"select": {"option": [], "maxCount": 1}},
        {"select": {"option": [], "maxCount": 0, "minCount": True}},
        {"select": {"option": [{}], "maxCount": 1, "minCount": 2}},
    ],
)
def test_malformed_requests_fail_without_producing_actions(observation: object) -> None:
    with pytest.raises(ValueError):
        choose_random_action(observation, Random(11))
