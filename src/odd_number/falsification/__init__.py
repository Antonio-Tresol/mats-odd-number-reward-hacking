"""Falsification tests for the claims the write-up rests on.

Run: uv run odd-number falsify [--no-pin] [--out PATH]

Writes `results/falsify-scorecard-2026-09-01.json`: every test, its inputs, its
result, and a verdict per claim. `recounts.py` loads and recounts the results
files, `statistics.py` holds the exact and permutation tests, `tests.py` the
record one test produces, the `*_tests.py` modules the tests by family, and
`scorecards.py` the verdicts and the writer.
"""
