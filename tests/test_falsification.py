"""Tests for the falsification statistics, against values worked by hand.

The scorecard rests on these: a Fisher p, a Wilson interval, a Holm step-down,
a kappa, and a logistic fit, each written in the package rather than imported.

Run:  uv run pytest tests/test_falsification.py
"""

from __future__ import annotations

from odd_number.falsification.statistics import (
    cohens_kappa,
    fisher_exact,
    fit_logistic,
    holm,
    wilson_interval,
)


def test_fisher_exact_on_a_zero_cell_table() -> None:
    assert round(fisher_exact(7, 23, 0, 30), 4) == 0.0105


def test_fisher_exact_on_a_two_sided_table() -> None:
    assert round(fisher_exact(12, 27, 6, 34), 4) == 0.1136


def test_wilson_interval_on_six_of_forty() -> None:
    low, high = wilson_interval(6, 40)
    assert (round(low, 4), round(high, 4)) == (0.0706, 0.2907)


def test_holm_stops_rejecting_at_the_first_p_above_its_threshold() -> None:
    kept = holm({"a": 0.001, "b": 0.03, "c": 0.04})
    assert kept == {"a": True, "b": False, "c": False}


def test_cohens_kappa_of_identical_ratings_is_one() -> None:
    ratings = [True, False, True, False, True]
    assert cohens_kappa(ratings, ratings) == 1.0


def test_fit_logistic_reports_separation_as_a_large_slope() -> None:
    features = [[1.0, x] for x in (-3.0, -2.0, -1.0, 1.0, 2.0, 3.0)]
    ys = [0, 0, 0, 1, 1, 1]
    (_, slope), log_likelihood = fit_logistic(features, ys)
    assert slope > 5
    assert log_likelihood > -1e-3
