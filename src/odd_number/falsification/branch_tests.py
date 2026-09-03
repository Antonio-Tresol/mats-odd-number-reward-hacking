"""G1, G5 and G6: the branch curves, their anchors, their trend, and their controls.

A branch sweep cuts one chain of thought at a sentence boundary and lets the
model finish it again thirty times. The recount excludes rows that recorded an
error, then asks whether the curve is the prefix's content or its length,
whether its per-sentence steps are more than sampling noise, and what the
affirming prompt does under the same prefixes.
"""

from __future__ import annotations

import random
from collections import Counter
from statistics import median
from typing import Any, Final

from odd_number.branches import split_sentences
from odd_number.falsification.recounts import (
    BRANCH_FILES,
    branch_counts,
    first_collected,
    load_branch,
)
from odd_number.falsification.statistics import (
    PERMUTATIONS,
    correlation_permutation,
    fisher_exact,
    holm,
    pearson,
)
from odd_number.falsification.tests import Test

#: Q1.H8.E1.C4 quotes three sentences of trace 14 as [32] to [36]; check
#: they are in the trace and where, with the sentence rule the sweep itself
#: uses, `branches.split_sentences`.
C4_QUOTES: Final[tuple[str, ...]] = (
    "We as AI should not blindly exploit hidden reward?",
    "The final should probably be an even number?",
    "The direct request is to choose an even number.",
)

BranchTable = dict[int, dict[str, Any]]


def fisher_between(cell_a: dict[str, Any], cell_b: dict[str, Any]) -> float:
    """Fisher exact between two branch-point cells, odd against even."""
    return fisher_exact(
        cell_a["odd"], cell_a["n"] - cell_a["odd"], cell_b["odd"], cell_b["n"] - cell_b["odd"]
    )


def load_branch_tables() -> dict[str, BranchTable]:
    """Every sweep's per-point counts, keyed by its short name."""
    return {name: branch_counts(load_branch(stem)) for name, (stem, _) in BRANCH_FILES.items()}


def pool_position_zero(
    tables: dict[str, BranchTable],
) -> tuple[dict[str, list[int]], list[int], dict[str, float]]:
    """Position-zero cells: each, the plain-prompt three pooled, and their pairwise Fisher p."""
    zero = {name: [t[0]["odd"], t[0]["n"]] for name, t in tables.items() if 0 in t}
    pooled_zero = [
        sum(v[0] for k, v in zero.items() if k != "trace14-affirming"),
        sum(v[1] for k, v in zero.items() if k != "trace14-affirming"),
    ]
    pairwise: dict[str, float] = {}
    names = [k for k in zero if k != "trace14-affirming"]
    for i, a in enumerate(names):
        for b in names[i + 1 :]:
            pairwise[f"{a}_vs_{b}"] = fisher_exact(
                zero[a][0], zero[a][1] - zero[a][0], zero[b][0], zero[b][1] - zero[b][0]
            )
    return zero, pooled_zero, pairwise


def branch_trends(rng: random.Random) -> dict[str, Any]:
    """The correlation between prefix length and an odd answer, per plain-prompt trace."""
    trends: dict[str, Any] = {}
    for name in ("trace14", "trace17", "trace21"):
        xs: list[float] = []
        ys: list[int] = []
        for kept, rows in load_branch(BRANCH_FILES[name][0]).items():
            for row in rows:
                if row.get("parity") in ("odd", "even"):
                    xs.append(float(kept))
                    ys.append(int(row["parity"] == "odd"))
        trends[name] = {
            "pearson_r": round(pearson(xs, ys), 3),
            "permutation_p": correlation_permutation(xs, ys, rng),
            "resamples": len(xs),
        }
    return trends


def matched_length_control(tables: dict[str, BranchTable]) -> dict[str, Any]:
    """Trace 14 at 43 sentences against the other two traces at the nearest prefix length."""
    t14, t17, t21 = tables["trace14"], tables["trace17"], tables["trace21"]
    kept14 = 43
    nearest17 = min(t17, key=lambda k: abs(t17[k]["prefix_chars"] - t14[kept14]["prefix_chars"]))
    nearest21 = min(t21, key=lambda k: abs(t21[k]["prefix_chars"] - t14[kept14]["prefix_chars"]))
    return {
        "trace14_at": {"kept": kept14, **t14[kept14]},
        "trace17_nearest_by_chars": {"kept": nearest17, **t17[nearest17]},
        "trace21_nearest_by_chars": {"kept": nearest21, **t21[nearest21]},
        "fisher_14_vs_17": fisher_between(t14[kept14], t17[nearest17]),
        "fisher_14_vs_21": fisher_between(t14[kept14], t21[nearest21]),
    }


def trace17_step(t17: BranchTable) -> float | None:
    """The trace-17 step at 121 to 162 sentences, when both points were swept."""
    return fisher_between(t17[121], t17[162]) if 121 in t17 and 162 in t17 else None


def pooled_from(table: BranchTable, first: int) -> list[int]:
    """Odd and n summed over every branch point at `first` sentences or later."""
    saturated = [k for k in table if k >= first]
    return [sum(table[k]["odd"] for k in saturated), sum(table[k]["n"] for k in saturated)]


def odd_answer_values(stem: str) -> dict[Any, int]:
    """The five most common odd answers in one sweep, with their counts."""
    all_odd: Counter[Any] = Counter()
    for rows in load_branch(stem).values():
        for row in rows:
            if row.get("parity") == "odd":
                all_odd[row["answer"]] += 1
    return dict(all_odd.most_common(5))


def position_zero_reasoning_chars() -> list[int]:
    """Reasoning length of every parseable position-zero resample, plain prompts pooled."""
    # Deliberation at position zero on the completions path, pooled over the
    # three plain-prompt sweeps: the reasoning is the continuation up to the
    # close of the think channel.
    return [
        len(row["continuation"].split("</think>", 1)[0])
        for name in ("trace14", "trace21", "trace17")
        for row in load_branch(BRANCH_FILES[name][0]).get(0, [])
        if row.get("parity") in ("odd", "even")
    ]


def locate_c4_quotes() -> tuple[int, dict[str, list[int]]]:
    """How many sentences trace 14 has, and at which of them each quoted sentence sits."""
    source = first_collected("odd-number-qwen-qwen3.8-27b", "conflict-grader")
    reasoning14 = next(r for r in source if r["index"] == 14).get("reasoning") or ""
    sentences = split_sentences(reasoning14)
    located = {q: [i for i, s in enumerate(sentences) if q in s] for q in C4_QUOTES}
    return len(sentences), located


def test_branch_curves(rng: random.Random) -> Test:
    """G: the branch curves, their anchors, their trend, and a content control."""
    tables = load_branch_tables()
    zero, pooled_zero, pairwise = pool_position_zero(tables)
    trends = branch_trends(rng)
    sentence_count, located = locate_c4_quotes()
    return Test(
        id="G1-branch-curves",
        claims=["Q1.H8.E1.C1", "Q1.H8.E1.C3", "Q1.H8.E1.C4", "Q1.H8.E1.C5"],
        test="Recount of every branch point with error rows excluded; position-zero cells "
        "pairwise and pooled against the chat path; permutation test of the correlation "
        "between prefix length and an odd answer per trace; at a matched prefix length in "
        "characters, trace 14 against the two other traces (content, not length, as the "
        "control); the trace-17 step at 121 to 162 sentences.",
        result={
            "position_zero": zero,
            "pooled_zero": pooled_zero,
            "pooled_vs_chat_fisher_p": fisher_exact(
                pooled_zero[0], pooled_zero[1] - pooled_zero[0], 6, 34
            ),
            "pairwise_zero_fisher_p": pairwise,
            "trend": trends,
            "trace14_from_46_on": pooled_from(tables["trace14"], 46),
            "trace14_odd_answer_values": odd_answer_values(BRANCH_FILES["trace14"][0]),
            "matched_length_control": matched_length_control(tables),
            "trace17_step_121_to_162_fisher_p": trace17_step(tables["trace17"]),
            "position_zero_median_reasoning_chars": median(position_zero_reasoning_chars()),
            "trace14_sentences": sentence_count,
            "c4_quotes_at_sentence": located,
            "tables": {name: {str(k): v for k, v in t.items()} for name, t in tables.items()},
        },
    )


def simulate_max_steps(ns: list[int], rate: float, rng: random.Random) -> list[float]:
    """The largest adjacent step in each of PERMUTATIONS sequences of cells drawn at
    their observed n under one constant rate."""
    max_steps: list[float] = []
    for _ in range(PERMUTATIONS):
        simulated = [sum(rng.random() < rate for _ in range(n)) / n for n in ns]
        max_steps.append(
            max(abs(simulated[i + 1] - simulated[i]) for i in range(len(simulated) - 1))
        )
    return max_steps


def count_sign_changes(rates: list[float]) -> int:
    """Sign changes between adjacent steps of a rate sequence, level steps skipped."""
    # Under a constant rate, the steps alternate sign at random. Count sign
    # changes in the observed sequence and in the simulations.
    signs = [
        1 if rates[i + 1] > rates[i] else -1
        for i in range(len(rates) - 1)
        if rates[i + 1] != rates[i]
    ]
    return sum(signs[i] != signs[i + 1] for i in range(len(signs) - 1))


def test_sawtooth_null(rng: random.Random) -> Test:
    """G5: is the per-sentence sawtooth on trace 14 distinguishable from noise?"""
    t14 = branch_counts(load_branch(BRANCH_FILES["trace14"][0]))
    span = [k for k in range(11, 22) if k in t14]
    rates = [t14[k]["odd"] / t14[k]["n"] for k in span]
    steps = [abs(rates[i + 1] - rates[i]) for i in range(len(rates) - 1)]
    observed_max = max(steps)
    pooled = sum(t14[k]["odd"] for k in span) / sum(t14[k]["n"] for k in span)
    max_steps = simulate_max_steps([t14[k]["n"] for k in span], pooled, rng)
    hits = sum(m >= observed_max - 1e-12 for m in max_steps)
    max_steps.sort()
    return Test(
        id="G5-sawtooth-null",
        claims=["Q1.H8.E1.C6"],
        test="Simulate the eleven per-sentence cells [11] to [21] at their observed n under one "
        "constant rate (their pooled rate) and ask how often the largest adjacent step is "
        "at least the observed one.",
        result={
            "span": span,
            "rates": [round(r, 3) for r in rates],
            "pooled_rate": round(pooled, 3),
            "observed_max_step": round(observed_max, 3),
            "p_max_step_at_least_observed": round(hits / PERMUTATIONS, 4),
            "null_median_max_step": round(max_steps[PERMUTATIONS // 2], 3),
            "observed_sign_changes": count_sign_changes(rates),
            "span_ends": {
                "first": [t14[span[0]]["odd"], t14[span[0]]["n"]],
                "last": [t14[span[-1]]["odd"], t14[span[-1]]["n"]],
                "fisher_p": fisher_between(t14[span[0]], t14[span[-1]]),
            },
        },
    )


def test_cross_prompt() -> Test:
    """G6: the affirming prompt under trace 14's own prefixes."""
    plain = branch_counts(load_branch(BRANCH_FILES["trace14"][0]))
    affirming = branch_counts(load_branch(BRANCH_FILES["trace14-affirming"][0]))
    shared = sorted(set(plain) & set(affirming))
    per_point: dict[str, Any] = {}
    pvalues: dict[str, float] = {}
    for k in shared:
        p = fisher_between(plain[k], affirming[k])
        pvalues[str(k)] = p
        per_point[str(k)] = {
            "plain": [plain[k]["odd"], plain[k]["n"]],
            "affirming": [affirming[k]["odd"], affirming[k]["n"]],
            "fisher_p": p,
        }
    a0, a43 = affirming[0], affirming[43]
    return Test(
        id="G6-cross-prompt",
        claims=["Q1.H8.E2.C1"],
        test="Fisher exact plain against affirming at every shared branch point, Holm over the "
        "points; the two-story tests: affirming at zero against affirming at 43 sentences "
        "(does the model's own prefix lift the affirming prompt?), and plain at 43 against "
        "affirming at 43 (does the affirming sentence still act on a committed prefix?).",
        result={
            "per_point": per_point,
            "survives_holm": holm(pvalues),
            "affirming_0_vs_43_fisher_p": fisher_between(a0, a43),
            "plain_43_vs_affirming_43_fisher_p": fisher_between(plain[43], a43),
            "affirming_zero_vs_collection_0_of_40_fisher_p": fisher_exact(
                a0["odd"], a0["n"] - a0["odd"], 0, 40
            ),
        },
    )
