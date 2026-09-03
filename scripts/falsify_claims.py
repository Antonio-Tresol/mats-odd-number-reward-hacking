"""Falsification tests for the claims the write-up rests on.

The tests live in `src/odd_number/falsification/` and run as
`uv run odd-number falsify`; this path forwards to that subcommand so the
command the research log records still runs.

Run: uv run scripts/falsify_claims.py [--no-pin] [--out PATH]
"""

from __future__ import annotations

import sys

from odd_number.cli import main

if __name__ == "__main__":
    raise SystemExit(main(["falsify", *sys.argv[1:]]))
