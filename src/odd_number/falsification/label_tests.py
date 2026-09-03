"""F1: the write-up's confusion table, its rater, and its length confound.

The six labels come from the Sonnet rater with each quote re-grounded in the
trace text, so a label counts only where its evidence is there. Each label is
then asked whether it predicts an odd answer three ways: Fisher exact, a
permutation of the label within reasoning-length quintiles, and a logistic
model with length as a covariate. Cohen's kappa against the Haiku rater says
how much of the table is the rater.
"""

from __future__ import annotations

import math
import random
from collections import defaultdict
from dataclasses import dataclass
from statistics import median
from typing import Any

from odd_number.falsification.recounts import (
    CONFUSION_KEYS,
    LABELS,
    RESULTS,
    Row,
    is_collected,
    normalise_space,
    read_jsonl,
)
from odd_number.falsification.statistics import (
    PERMUTATIONS,
    chi_square_1df_survival,
    cohens_kappa,
    fisher_exact,
    fit_logistic,
    holm,
)
from odd_number.falsification.tests import Test


@dataclass(frozen=True, slots=True)
class LabelledTraces:
    """The Sonnet-labelled traces with a parseable answer, and what every label test shares."""

    traces: list[str]
    sonnet: dict[str, dict[str, Any]]
    haiku: dict[str, dict[str, Any]]
    reasoning_by_trace: dict[str, str]
    odd_flags: list[bool]
    lengths: list[int]
    stratum: list[int]


def load_labels(name: str) -> dict[str, dict[str, Any]]:
    """Label rows keyed by trace id."""
    return {row["trace_id"]: row for row in read_jsonl(LABELS / name)}


def load_reasoning_by_trace() -> dict[str, str]:
    """The reasoning text of every collected qwen3.8-27b row, keyed by trace id."""
    reasoning_by_trace: dict[str, str] = {}
    for path in RESULTS.glob("odd-number-qwen-qwen3.8-27b*.jsonl"):
        if path.name.endswith(".answers.jsonl"):
            continue
        model_part = path.stem.removeprefix("odd-number-")
        # First collected row wins, the same rule `load_file` applies; a dict
        # comprehension would keep the last and pair a label with the wrong
        # duplicate's reasoning.
        for record in read_jsonl(path):
            key = f"{model_part}--{record['treatment']}--{record['index']}"
            if is_collected(record) and key not in reasoning_by_trace:
                reasoning_by_trace[key] = record.get("reasoning") or ""
    return reasoning_by_trace


def index_parity_by_trace(cells: dict[tuple[str, str], list[Row]]) -> dict[str, str]:
    """Each qwen3.8-27b row's parity, keyed by trace id."""
    parity_by_trace: dict[str, str] = {}
    for (stem, treatment), rows in cells.items():
        if not stem.startswith("odd-number-qwen-qwen3.8-27b"):
            continue
        model_part = stem.removeprefix("odd-number-")
        for row in rows:
            parity_by_trace[f"{model_part}--{treatment}--{row.index}"] = row.parity
    return parity_by_trace


def assign_length_strata(lengths: list[int]) -> list[int]:
    """The reasoning-length quintile of each trace, 0 to 4."""
    order = sorted(range(len(lengths)), key=lambda i: lengths[i])
    stratum = [0] * len(lengths)
    for rank, i in enumerate(order):
        stratum[i] = min(4, rank * 5 // len(lengths))
    return stratum


def load_labelled_traces(cells: dict[tuple[str, str], list[Row]]) -> LabelledTraces:
    """Both raters' labels over the Sonnet-labelled traces that answered with a number."""
    sonnet = load_labels("qwen38-conflict-labels-sonnet.jsonl")
    haiku = load_labels("qwen38-conflict-labels.jsonl")
    reasoning_by_trace = load_reasoning_by_trace()
    parity_by_trace = index_parity_by_trace(cells)
    traces = [t for t in sonnet if parity_by_trace.get(t) in ("odd", "even")]
    lengths = [len(reasoning_by_trace.get(t, "")) for t in traces]
    return LabelledTraces(
        traces=traces,
        sonnet=sonnet,
        haiku=haiku,
        reasoning_by_trace=reasoning_by_trace,
        odd_flags=[parity_by_trace[t] == "odd" for t in traces],
        lengths=lengths,
        stratum=assign_length_strata(lengths),
    )


def ground_label(labelled: LabelledTraces, key: str) -> tuple[list[bool], int, int]:
    """Per trace, the label present with its quote found in the trace; and how many
    positive labels there were and how many of those grounded."""
    flags: list[bool] = []
    positive = grounded = 0
    for t in labelled.traces:
        entry = labelled.sonnet[t].get(key) or {}
        present = bool(entry.get("present"))
        quote = normalise_space(str(entry.get("quote") or ""))
        found = bool(quote) and quote in normalise_space(labelled.reasoning_by_trace.get(t, ""))
        if present:
            positive += 1
            grounded += found
        flags.append(present and found)
    return flags, positive, grounded


def stratified_permutation_p(
    labelled: LabelledTraces, flags: list[bool], observed: float, rng: random.Random
) -> float:
    """How often the label's rate difference is at least `observed` with the label
    shuffled within length quintiles."""
    odd_flags = labelled.odd_flags
    n = len(odd_flags)
    # Stratified permutation: shuffle the label within length quintiles.
    hits = 0
    by_stratum: dict[int, list[int]] = defaultdict(list)
    for i, s in enumerate(labelled.stratum):
        by_stratum[s].append(i)
    shuffled = list(flags)
    for _ in range(PERMUTATIONS):
        for members in by_stratum.values():
            values = [flags[i] for i in members]
            rng.shuffle(values)
            for i, v in zip(members, values, strict=True):
                shuffled[i] = v
        w = sum(shuffled)
        ow = sum(o for o, f in zip(odd_flags, shuffled, strict=True) if f)
        diff = ow / w - (sum(odd_flags) - ow) / (n - w) if 0 < w < n else 0
        if abs(diff) >= abs(observed) - 1e-12:
            hits += 1
    return round((hits + 1) / (PERMUTATIONS + 1), 4)


def length_adjusted_association(labelled: LabelledTraces, flags: list[bool]) -> dict[str, Any]:
    """The label's log-odds ratio for an odd answer with reasoning length held."""
    # Length-adjusted logistic model: odd on log10 chars plus the label,
    # against log10 chars alone, by likelihood ratio.
    ys = [int(o) for o in labelled.odd_flags]
    full = [
        [1.0, math.log10(max(v, 1)), float(f)] for v, f in zip(labelled.lengths, flags, strict=True)
    ]
    reduced = [row[:2] for row in full]
    beta_full, ll_full = fit_logistic(full, ys)
    _, ll_reduced = fit_logistic(reduced, ys)
    return {
        "label_log_odds_ratio_given_length": round(beta_full[2], 3),
        "likelihood_ratio_p": chi_square_1df_survival(2 * (ll_full - ll_reduced)),
        "separated": abs(beta_full[2]) > 15,
    }


def haiku_agreement(
    labelled: LabelledTraces, key: str, flags: list[bool]
) -> tuple[float, list[float | None]]:
    """Cohen's kappa against the Haiku rater, and the odd rate with and without its
    label, over the traces it also rated."""
    haiku = labelled.haiku
    haiku_flags = [bool((haiku.get(t, {}).get(key) or {}).get("present")) for t in labelled.traces]
    shared = [i for i, t in enumerate(labelled.traces) if t in haiku]
    h_with = sum(haiku_flags[i] for i in shared)
    h_odd_with = sum(labelled.odd_flags[i] for i in shared if haiku_flags[i])
    h_odd_without = sum(labelled.odd_flags[i] for i in shared) - h_odd_with
    kappa = round(cohens_kappa([flags[i] for i in shared], [haiku_flags[i] for i in shared]), 3)
    rates = [
        round(h_odd_with / h_with, 4) if h_with else None,
        round(h_odd_without / (len(shared) - h_with), 4) if len(shared) > h_with else None,
    ]
    return kappa, rates


def label_association(
    labelled: LabelledTraces, key: str, flags: list[bool], rng: random.Random
) -> dict[str, Any]:
    """One row of the confusion table: the label against an odd answer, raw,
    length-stratified, length-adjusted, and under the other rater."""
    odd_flags = labelled.odd_flags
    n = len(odd_flags)
    with_label = sum(flags)
    odd_with = sum(o for o, f in zip(odd_flags, flags, strict=True) if f)
    odd_without = sum(odd_flags) - odd_with
    observed = odd_with / with_label - odd_without / (n - with_label)
    kappa, haiku_rates = haiku_agreement(labelled, key, flags)
    return {
        "traces_with_label": with_label,
        "odd_with_label": odd_with,
        "odd_without_label": odd_without,
        "rate_with": round(odd_with / with_label, 4),
        "rate_without": round(odd_without / (n - with_label), 4),
        "fisher_p": fisher_exact(
            odd_with, with_label - odd_with, odd_without, n - with_label - odd_without
        ),
        "length_stratified_permutation_p": stratified_permutation_p(labelled, flags, observed, rng),
        "length_adjusted": length_adjusted_association(labelled, flags),
        "median_chars_with_label": median(
            v for v, f in zip(labelled.lengths, flags, strict=True) if f
        ),
        "median_chars_without": median(
            v for v, f in zip(labelled.lengths, flags, strict=True) if not f
        ),
        "kappa_sonnet_vs_haiku": kappa,
        "haiku_rate_with_vs_without": haiku_rates,
    }


def test_confusion_labels(cells: dict[tuple[str, str], list[Row]], rng: random.Random) -> Test:
    """F: the write-up's confusion table, its rater, and its length confound."""
    labelled = load_labelled_traces(cells)
    per_label: dict[str, Any] = {}
    grounded_total = positive_total = 0
    for key in CONFUSION_KEYS:
        flags, positive, grounded = ground_label(labelled, key)
        positive_total += positive
        grounded_total += grounded
        per_label[key] = label_association(labelled, key, flags, rng)
    pvalues = {key: entry["fisher_p"] for key, entry in per_label.items()}
    return Test(
        id="F1-confusion-labels",
        claims=["Q1.H7.E7.C1", "Q1.H7.E7.C2"],
        test="Recount of the six-question table from the Sonnet labels with quotes re-grounded "
        "in the trace; Fisher exact of each label against an odd answer with Holm over six; "
        "the same association with the label permuted within reasoning-length quintiles; "
        "Cohen's kappa against the Haiku rater and the association under Haiku's labels.",
        result={
            "traces": len(labelled.traces),
            "odd": sum(labelled.odd_flags),
            "positive_labels": positive_total,
            "grounded_positive_labels": grounded_total,
            "per_label": per_label,
            "survives_holm": holm(pvalues),
        },
    )
