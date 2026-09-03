"""C1, D1 and E1: what the prompt's wording, its labels, and its provenance do to the rate.

Each test compares an intervention cell with the model's verbatim cell by
Fisher exact and corrects over the comparisons it makes with Holm.
"""

from __future__ import annotations

import random
from typing import Any

from odd_number.falsification.recounts import SLATE, Row, odd_n
from odd_number.falsification.statistics import PERMUTATIONS, fisher_exact, holm
from odd_number.falsification.tests import Test


def test_paraphrases(cells: dict[tuple[str, str], list[Row]], rng: random.Random) -> Test:
    """C: does any paraphrase cell differ from its model's verbatim cell?"""
    comparisons: dict[str, float] = {}
    table: dict[str, Any] = {}
    at_least_one: dict[str, Any] = {}
    for name, stem in SLATE.items():
        odd_b, n_b = odd_n(cells.get((stem, "conflict-grader"), []))
        cells_here: dict[str, list[int]] = {"verbatim": [odd_b, n_b]}
        pooled_odd, pooled_n = odd_b, n_b
        paraphrase_cells: list[tuple[int, int]] = []
        for p in ("p1", "p2", "p3", "p4"):
            rows = cells.get((f"{stem}-{p}", f"conflict-grader-{p}"), [])
            odd_p, n_p = odd_n(rows)
            cells_here[p] = [odd_p, n_p]
            if n_p:
                comparisons[f"{name}:{p}"] = fisher_exact(odd_p, n_p - odd_p, odd_b, n_b - odd_b)
                pooled_odd += odd_p
                pooled_n += n_p
                paraphrase_cells.append((odd_p, n_p))
        table[name] = cells_here
        if odd_b == 0 and paraphrase_cells:
            # Under one constant rate per model, how often would at least one
            # paraphrase cell show an odd answer? The rate is the model's pooled
            # rate over every conflict cell it has, which is the most generous
            # null the data allows.
            rate = pooled_odd / pooled_n
            none_odd = 1.0
            for _, n_p in paraphrase_cells:
                none_odd *= (1 - rate) ** n_p
            at_least_one[name] = {
                "pooled_rate": round(rate, 4),
                "p_at_least_one_odd_under_constant_rate": round(1 - none_odd, 4),
                "observed_any_odd": any(o > 0 for o, _ in paraphrase_cells),
            }
    kept = holm(comparisons)
    return Test(
        id="C1-paraphrases",
        claims=["Q1.H1.E5.C1"],
        test="Fisher exact, each paraphrase cell against its model's verbatim cell, Holm "
        "over all comparisons; for models at 0 verbatim, the chance of seeing at least one "
        "odd paraphrase answer under a constant per-model rate.",
        result={
            "cells": table,
            "fisher_p": comparisons,
            "survives_holm": kept,
            "models_at_zero_verbatim": at_least_one,
        },
    )


def test_post_labels(cells: dict[tuple[str, str], list[Row]]) -> Test:
    """D: the post's description labels against each model's baseline."""
    out: dict[str, Any] = {}
    for name, stem in (
        ("kimi-k3", "odd-number-moonshotai-kimi-k3"),
        ("qwen3.8-27b", "odd-number-qwen-qwen3.8-27b"),
    ):
        odd_b, n_b = odd_n(cells[(stem, "conflict-grader")])
        pvalues: dict[str, float] = {}
        counts: dict[str, list[int]] = {"baseline": [odd_b, n_b]}
        pooled_odd = pooled_n = 0
        for label in ("test", "misaligned", "want"):
            odd_l, n_l = odd_n(cells[(f"{stem}-{label}", f"conflict-grader-{label}")])
            counts[label] = [odd_l, n_l]
            pvalues[label] = fisher_exact(odd_l, n_l - odd_l, odd_b, n_b - odd_b)
            if label != "test":
                pooled_odd += odd_l
                pooled_n += n_l
        out[name] = {
            "counts": counts,
            "fisher_p": pvalues,
            "survives_holm": holm(pvalues),
            "misaligned_plus_want": [pooled_odd, pooled_n],
            "pooled_fisher_p": fisher_exact(pooled_odd, pooled_n - pooled_odd, odd_b, n_b - odd_b),
        }
    return Test(
        id="D1-post-labels",
        claims=["Q1.H1.E6.C1", "Q1.H1.E6.C2"],
        test="Fisher exact, each label cell against the model's baseline, Holm over the three "
        "labels within a model; the two zero cells pooled.",
        result=out,
    )


def test_provenance_ladder(cells: dict[tuple[str, str], list[Row]], rng: random.Random) -> Test:
    """E: the provenance ladder, with the difference's bootstrap interval."""
    stem = "odd-number-qwen-qwen3.8-27b"
    base = cells[(stem, "conflict-grader")]
    ladder = {
        label: cells[(f"{stem}-{label}", f"conflict-grader-{label}")]
        for label in ("system_added", "user_authored", "human_sender")
    }
    odd_b, n_b = odd_n(base)
    counts = {"baseline": [odd_b, n_b]}
    pvalues: dict[str, float] = {}
    for label, rows in ladder.items():
        odd_l, n_l = odd_n(rows)
        counts[label] = [odd_l, n_l]
        pvalues[f"{label}_vs_baseline"] = fisher_exact(odd_l, n_l - odd_l, odd_b, n_b - odd_b)
    odd_s, n_s = counts["system_added"]
    odd_u, n_u = counts["user_authored"]
    pvalues["user_authored_vs_system_added"] = fisher_exact(odd_u, n_u - odd_u, odd_s, n_s - odd_s)
    # Bootstrap the difference system_added minus baseline.
    base_flags = [r.parity == "odd" for r in base if r.parity != "unparseable"]
    sys_flags = [r.parity == "odd" for r in ladder["system_added"] if r.parity != "unparseable"]
    diffs = []
    for _ in range(PERMUTATIONS):
        b = sum(rng.choice(base_flags) for _ in base_flags) / len(base_flags)
        s = sum(rng.choice(sys_flags) for _ in sys_flags) / len(sys_flags)
        diffs.append(s - b)
    diffs.sort()
    return Test(
        id="E1-provenance-ladder",
        claims=["Q1.H7.E6.C1", "Q1.H7.E6.C2"],
        test="Fisher exact along the ladder; bootstrap 95% interval of the system_added minus "
        "baseline rate difference; Holm over the three rungs against baseline.",
        result={
            "counts": counts,
            "fisher_p": pvalues,
            "survives_holm": holm({k: v for k, v in pvalues.items() if k.endswith("baseline")}),
            "bootstrap_diff_system_added_minus_baseline": [
                round(diffs[int(0.025 * PERMUTATIONS)], 4),
                round(diffs[int(0.975 * PERMUTATIONS)], 4),
            ],
            "share_of_bootstraps_with_decrease": round(sum(d < 0 for d in diffs) / len(diffs), 4),
        },
    )
