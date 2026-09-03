"""The B-series: does reasoning length carry the effect, between arms and within them?

`predict_from_length` is the shared instrument: a logistic fit of P(odd) on
log10 reasoning characters over one set of cells, asked what it expects in
another given the lengths observed there, so that a zero in a cell whose
deliberation collapsed can be told from a zero the label produced on its own.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from statistics import median
from typing import Any

from odd_number.falsification.recounts import SLATE, Row, median_or_zero
from odd_number.falsification.statistics import (
    PERMUTATIONS,
    fisher_exact,
    fit_logistic,
    rank_sum_permutation,
)
from odd_number.falsification.tests import Test


@dataclass(frozen=True, slots=True)
class LengthFit:
    """P(odd | log10 chars), fit on the parseable, non-empty rows of one set of cells."""

    rows: list[Row]
    odd: int
    intercept: float
    slope: float
    shortest_odd_chars: int

    def probability(self, chars: int) -> float:
        """The fitted P(odd) for a trace of `chars` reasoning characters."""
        return 1 / (1 + math.exp(-(self.intercept + self.slope * math.log10(chars))))


def test_length_by_arm(cells: dict[tuple[str, str], list[Row]]) -> Test:
    """B1: reasoning longer under conflict, by median tokens and chars."""
    per_model: dict[str, Any] = {}
    for name, stem in SLATE.items():
        conflict = cells.get((stem, "conflict-grader"), [])
        agree = cells.get((stem, "agree-grader"), [])
        if not conflict or not agree:
            continue
        per_model[name] = {
            "median_tokens": [
                median_or_zero([r.reasoning_tokens for r in conflict]),
                median_or_zero([r.reasoning_tokens for r in agree]),
            ],
            "median_chars": [
                median_or_zero([r.reasoning_chars for r in conflict]),
                median_or_zero([r.reasoning_chars for r in agree]),
            ],
            "n": [len(conflict), len(agree)],
        }
    return Test(
        id="B1-length-by-arm",
        claims=["Q1.H1.E1.C2"],
        test="Median reasoning tokens and characters per arm, all collected rows of the "
        "verbatim files including truncated ones, as the claim states.",
        result={"per_model": per_model},
    )


def test_length_within_conflict(
    cells: dict[tuple[str, str], list[Row]], rng: random.Random
) -> Test:
    """B2: within the baseline conflict arm, do odd answers come from longer traces?"""
    rows = [
        r
        for r in cells[("odd-number-qwen-qwen3.8-27b", "conflict-grader")]
        if r.parity != "unparseable"
    ]
    odd = [float(r.reasoning_chars) for r in rows if r.parity == "odd"]
    even = [float(r.reasoning_chars) for r in rows if r.parity == "even"]
    return Test(
        id="B2-length-within-conflict",
        claims=["Q1.H1.E1.C2"],
        test="Rank-sum permutation test, reasoning characters of odd against even answers in "
        "the qwen3.8-27b baseline conflict arm.",
        result={
            "n_odd": len(odd),
            "n_even": len(even),
            "min_odd_chars": min(odd),
            "median_odd": median(odd),
            "median_even": median(even),
            "even_above_min_odd": sum(v >= min(odd) for v in even),
            "permutation_p": rank_sum_permutation(odd, even, rng),
        },
    )


def fit_length_model(fit_rows: list[Row]) -> LengthFit:
    """Fit P(odd | log10 chars) on the parseable, non-empty rows."""
    usable = [r for r in fit_rows if r.parity != "unparseable" and r.reasoning_chars > 0]
    features = [[1.0, math.log10(r.reasoning_chars)] for r in usable]
    ys = [int(r.parity == "odd") for r in usable]
    (b0, b1), _ = fit_logistic(features, ys)
    shortest_odd = min(r.reasoning_chars for r in usable if r.parity == "odd")
    return LengthFit(usable, sum(ys), b0, b1, shortest_odd)


def predict_cell(fit: LengthFit, rows: list[Row], rng: random.Random) -> dict[str, Any]:
    """What the fit expects in one target cell given the lengths actually observed there."""
    rows = [r for r in rows if r.parity != "unparseable" and r.reasoning_chars > 0]
    probs = [fit.probability(r.reasoning_chars) for r in rows]
    observed = sum(r.parity == "odd" for r in rows)
    expected = sum(probs)
    at_most = at_least = 0
    for _ in range(PERMUTATIONS):
        draw = sum(rng.random() < p for p in probs)
        at_most += draw <= observed
        at_least += draw >= observed
    # Model-free companion: inside the band of lengths the target cell
    # actually spans, compare the fit set's odd rate with the target's by
    # Fisher exact. No functional form, at the cost of the tails.
    low, high = min(r.reasoning_chars for r in rows), max(r.reasoning_chars for r in rows)
    fit_in_band = [r for r in fit.rows if low <= r.reasoning_chars <= high]
    fit_band_odd = sum(r.parity == "odd" for r in fit_in_band)
    return {
        "n": len(rows),
        "observed_odd": observed,
        "expected_odd_from_length": round(expected, 2),
        "p_at_most_observed": round(at_most / PERMUTATIONS, 4),
        "p_at_least_observed": round(at_least / PERMUTATIONS, 4),
        "median_chars": median(r.reasoning_chars for r in rows),
        "traces_at_or_above_shortest_odd": sum(
            r.reasoning_chars >= fit.shortest_odd_chars for r in rows
        ),
        "matched_band": {
            "chars": [low, high],
            "fit_rows_in_band": [fit_band_odd, len(fit_in_band)],
            "target": [observed, len(rows)],
            "fisher_p": fisher_exact(
                fit_band_odd, len(fit_in_band) - fit_band_odd, observed, len(rows) - observed
            )
            if fit_in_band
            else None,
        },
    }


def predict_from_length(
    fit_rows: list[Row], targets: dict[str, list[Row]], rng: random.Random
) -> dict[str, Any]:
    """Would a length-only model predict what each target cell showed?

    Fit P(odd | log10 chars) on `fit_rows`, then ask what that model expects in
    each target cell given the lengths actually observed there, and how often a
    draw from it gives the observed count or fewer (or, for cells above the
    prediction, the observed count or more).
    """
    fit = fit_length_model(fit_rows)
    return {
        "fit_n": len(fit.rows),
        "fit_odd": fit.odd,
        "intercept": round(fit.intercept, 3),
        "slope_per_log10_char": round(fit.slope, 3),
        "shortest_odd_chars_in_fit": fit.shortest_odd_chars,
        "cells": {label: predict_cell(fit, rows, rng) for label, rows in targets.items()},
    }


def test_length_explains_zeros(cells: dict[tuple[str, str], list[Row]], rng: random.Random) -> Test:
    """B3: qwen3.8-27b's label cells against a length-only model.

    The fit set is the two plain-prompt cells that kept deliberating, baseline
    and system_added, so the model learns how often a trace of a given length
    games when nothing in the prompt tells it what the block is for.
    """
    stem = "odd-number-qwen-qwen3.8-27b"
    fit_rows = (
        cells[(stem, "conflict-grader")]
        + cells[(f"{stem}-system_added", "conflict-grader-system_added")]
    )
    targets = {
        label: cells[(f"{stem}-{label}", f"conflict-grader-{label}")]
        for label in ("test", "misaligned", "want", "user_authored", "human_sender")
    }
    targets["vendor-sampling"] = cells[(f"{stem}-vendor-sampling", "conflict-grader")]
    return Test(
        id="B3-length-explains-zeros-qwen",
        claims=["Q1.H7.E6.C2", "Q1.H1.E6.C2"],
        test="Logistic fit of odd on log10 reasoning chars over the qwen3.8-27b baseline and "
        "system_added conflict cells; expected odd count in each label cell under that "
        "fit given its own lengths; Monte Carlo P(observed or fewer) and P(observed or more).",
        result=predict_from_length(fit_rows, targets, rng),
    )


def test_length_explains_zeros_kimi(
    cells: dict[tuple[str, str], list[Row]], rng: random.Random
) -> Test:
    """B4: Kimi K3's label and paraphrase cells against a length-only model fit on its baseline."""
    stem = "odd-number-moonshotai-kimi-k3"
    fit_rows = cells[(stem, "conflict-grader")]
    targets = {
        label: cells[(f"{stem}-{label}", f"conflict-grader-{label}")]
        for label in ("test", "misaligned", "want", "p1", "p2", "p3")
    }
    return Test(
        id="B4-length-explains-zeros-kimi",
        claims=["Q1.H1.E6.C1", "Q1.H1.E5.C1"],
        test="Logistic fit of odd on log10 reasoning chars over the Kimi K3 verbatim conflict "
        "cell; expected odd count in each label and paraphrase cell under that fit given "
        "its own lengths; Monte Carlo P(observed or fewer) and P(observed or more).",
        result=predict_from_length(fit_rows, targets, rng),
    )
