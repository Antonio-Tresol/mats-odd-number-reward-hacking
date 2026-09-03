"""Exact and permutation statistics for the falsification tests.

Written here rather than imported: the project's environment carries no scipy,
and a Fisher test on a 2x2 table is thirty lines. Every random draw takes the
`random.Random` its caller threads through, seeded once in `scorecards.py`.
"""

from __future__ import annotations

import math
import random
from fractions import Fraction
from typing import Final

PERMUTATIONS: Final[int] = 20_000


def hypergeometric_probability(a: int, r1: int, r2: int, c1: int) -> Fraction:
    """P(top-left cell = a) with row sums r1, r2 and first column sum c1."""
    n = r1 + r2
    return Fraction(math.comb(r1, a) * math.comb(r2, c1 - a), math.comb(n, c1))


def fisher_exact(a: int, b: int, c: int, d: int) -> float:
    """Two-sided Fisher exact p for the table [[a, b], [c, d]].

    Two-sided the way scipy does it: sum the probabilities of every table at
    least as extreme as the observed one, with a relative tolerance so a
    floating tie is not dropped.
    """
    r1, r2, c1 = a + b, c + d, a + c
    observed = hypergeometric_probability(a, r1, r2, c1)
    low, high = max(0, c1 - r2), min(r1, c1)
    total = Fraction(0)
    for k in range(low, high + 1):
        p = hypergeometric_probability(k, r1, r2, c1)
        if p <= observed * Fraction(1 + 1e-9):
            total += p
    return float(min(total, Fraction(1)))


def wilson_interval(successes: int, trials: int) -> tuple[float, float]:
    """95% Wilson score interval, as `grades.py` reports it."""
    if trials == 0:
        return (0.0, 1.0)
    z = 1.959963984540054
    p = successes / trials
    denominator = 1 + z * z / trials
    centre = (p + z * z / (2 * trials)) / denominator
    half = z * math.sqrt(p * (1 - p) / trials + z * z / (4 * trials * trials)) / denominator
    return (max(0.0, centre - half), min(1.0, centre + half))


def holm(pvalues: dict[str, float], alpha: float = 0.05) -> dict[str, bool]:
    """Holm step-down: which comparisons stay significant at `alpha`."""
    ordered = sorted(pvalues.items(), key=lambda item: item[1])
    m = len(ordered)
    kept: dict[str, bool] = {}
    still_rejecting = True
    for rank, (name, p) in enumerate(ordered):
        threshold = alpha / (m - rank)
        still_rejecting = still_rejecting and p <= threshold
        kept[name] = still_rejecting
    return kept


def rank_values(values: list[float]) -> list[float]:
    """Average ranks, ties shared."""
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    position = 0
    while position < len(order):
        end = position
        while end + 1 < len(order) and values[order[end + 1]] == values[order[position]]:
            end += 1
        average = (position + end) / 2 + 1
        for i in range(position, end + 1):
            ranks[order[i]] = average
        position = end + 1
    return ranks


def rank_sum_permutation(group_a: list[float], group_b: list[float], rng: random.Random) -> float:
    """Two-sided permutation p for the Mann-Whitney rank sum of `group_a`."""
    pooled = group_a + group_b
    ranks = rank_values(pooled)
    n_a = len(group_a)
    observed = sum(ranks[:n_a])
    expected = n_a * (len(pooled) + 1) / 2
    deviation = abs(observed - expected)
    hits = 0
    indices = list(range(len(pooled)))
    for _ in range(PERMUTATIONS):
        rng.shuffle(indices)
        statistic = sum(ranks[i] for i in indices[:n_a])
        if abs(statistic - expected) >= deviation - 1e-9:
            hits += 1
    return (hits + 1) / (PERMUTATIONS + 1)


def pearson(xs: list[float], ys: list[float]) -> float:
    """Pearson correlation, 0 when either side is constant."""
    n = len(xs)
    mean_x, mean_y = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mean_x) ** 2 for x in xs)
    syy = sum((y - mean_y) ** 2 for y in ys)
    if sxx == 0 or syy == 0:
        return 0.0
    sxy = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys, strict=True))
    return sxy / math.sqrt(sxx * syy)


def correlation_permutation(xs: list[float], ys: list[int], rng: random.Random) -> float:
    """Two-sided permutation p for the Pearson correlation of `xs` with `ys`."""
    observed = abs(pearson(xs, ys))
    hits = 0
    shuffled = list(ys)
    for _ in range(PERMUTATIONS):
        rng.shuffle(shuffled)
        if abs(pearson(xs, shuffled)) >= observed - 1e-12:
            hits += 1
    return (hits + 1) / (PERMUTATIONS + 1)


def solve_linear(matrix: list[list[float]], vector: list[float]) -> list[float] | None:
    """Gaussian elimination with partial pivoting; None when singular."""
    k = len(vector)
    rows = [list(matrix[i]) + [vector[i]] for i in range(k)]
    for col in range(k):
        pivot = max(range(col, k), key=lambda r: abs(rows[r][col]))
        if abs(rows[pivot][col]) < 1e-12:
            return None
        rows[col], rows[pivot] = rows[pivot], rows[col]
        for r in range(k):
            if r != col:
                factor = rows[r][col] / rows[col][col]
                rows[r] = [a - factor * b for a, b in zip(rows[r], rows[col], strict=True)]
    return [rows[i][k] / rows[i][i] for i in range(k)]


def log_likelihood(beta: list[float], features: list[list[float]], ys: list[int]) -> float:
    total = 0.0
    for x, y in zip(features, ys, strict=True):
        z = sum(b * v for b, v in zip(beta, x, strict=True))
        total += y * z - (math.log1p(math.exp(z)) if z < 30 else z)
    return total


def fit_logistic(features: list[list[float]], ys: list[int]) -> tuple[list[float], float]:
    """Coefficients and log-likelihood of a logistic regression, by damped Newton steps.

    Small problems only: one to three predictors, a few hundred rows. Complete
    separation is not hidden; it shows up as a coefficient of large magnitude,
    which the caller reports rather than trusting.
    """
    k = len(features[0])
    beta = [0.0] * k
    for _ in range(100):
        gradient = [0.0] * k
        hessian = [[0.0] * k for _ in range(k)]
        for x, y in zip(features, ys, strict=True):
            z = sum(b * v for b, v in zip(beta, x, strict=True))
            p = 1 / (1 + math.exp(-z))
            w = p * (1 - p)
            for i in range(k):
                gradient[i] += (y - p) * x[i]
                for j in range(k):
                    hessian[i][j] += w * x[i] * x[j]
        step = solve_linear(hessian, gradient)
        if step is None:
            break
        before = log_likelihood(beta, features, ys)
        scale = 1.0
        candidate = beta
        while scale > 1e-4:
            candidate = [b + scale * s for b, s in zip(beta, step, strict=True)]
            if log_likelihood(candidate, features, ys) >= before - 1e-9:
                break
            scale /= 2
        beta = candidate
        if max(abs(scale * s) for s in step) < 1e-8:
            break
    return beta, log_likelihood(beta, features, ys)


def chi_square_1df_survival(statistic: float) -> float:
    """P(chi-square with one degree of freedom >= statistic)."""
    return math.erfc(math.sqrt(max(statistic, 0.0) / 2))


def cohens_kappa(a: list[bool], b: list[bool]) -> float:
    """Agreement between two binary raters beyond chance."""
    n = len(a)
    agree = sum(x == y for x, y in zip(a, b, strict=True)) / n
    pa, pb = sum(a) / n, sum(b) / n
    chance = pa * pb + (1 - pa) * (1 - pb)
    return 0.0 if chance == 1 else (agree - chance) / (1 - chance)


def binomial_tail(k: int, n: int, p: float) -> float:
    """P(X >= k) for X ~ Binomial(n, p)."""
    return sum(math.comb(n, i) * p**i * (1 - p) ** (n - i) for i in range(k, n + 1))
