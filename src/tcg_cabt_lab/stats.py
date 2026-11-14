"""Seed-level comparison of two training variants.

Games played by one checkpoint share its weights, so they are not independent. The unit of
analysis is the training seed: each checkpoint gets one score, and the interval comes from
resampling seeds within each variant (a cluster bootstrap).
"""

from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np


def checkpoint_score(family_breakdown: Mapping[str, Mapping[str, Any]]) -> float:
    """Equally weighted mean of a checkpoint's per-family win rates (a draw counts half)."""
    rates = [float(f["wins"]) / int(f["total_games"]) for f in family_breakdown.values()]
    if not rates:
        raise ValueError("checkpoint has no deck-family results")
    return float(np.mean(rates))


def seed_level_analysis(
    baseline_scores: Sequence[float],
    treatment_scores: Sequence[float],
    equivalence_margin: float | None = None,
    resamples: int = 10_000,
    seed: int = 0,
) -> dict[str, Any]:
    """Compare mean checkpoint scores, treatment minus baseline, with a cluster bootstrap.

    A difference is detected when the 95% interval excludes zero. Equivalence holds when the
    90% interval lies inside (-margin, +margin), the bootstrap form of two one-sided tests at
    the 5% level.
    """
    base = np.asarray(baseline_scores, dtype=np.float64)
    treat = np.asarray(treatment_scores, dtype=np.float64)
    if base.size < 2 or treat.size < 2:
        raise ValueError("each variant needs at least two training seeds")

    rng = np.random.default_rng(seed)
    base_means = base[rng.integers(0, base.size, size=(resamples, base.size))].mean(axis=1)
    treat_means = treat[rng.integers(0, treat.size, size=(resamples, treat.size))].mean(axis=1)
    deltas = treat_means - base_means

    lo95, hi95 = (float(v) for v in np.percentile(deltas, [2.5, 97.5]))
    lo90, hi90 = (float(v) for v in np.percentile(deltas, [5.0, 95.0]))
    equivalent = (
        None
        if equivalence_margin is None
        else bool(lo90 > -equivalence_margin and hi90 < equivalence_margin)
    )
    return {
        "unit": "training seed",
        "n_seeds": [int(base.size), int(treat.size)],
        "means": [round(float(base.mean()), 4), round(float(treat.mean()), 4)],
        "std": [round(float(base.std(ddof=1)), 4), round(float(treat.std(ddof=1)), 4)],
        "delta": round(float(treat.mean() - base.mean()), 4),
        "ci_95": [round(lo95, 4), round(hi95, 4)],
        "ci_90": [round(lo90, 4), round(hi90, 4)],
        "difference_detected": bool(lo95 > 0.0 or hi95 < 0.0),
        "equivalence_margin": equivalence_margin,
        "equivalent": equivalent,
        "bootstrap": {"resamples": resamples, "seed": seed},
    }
