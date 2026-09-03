"""What one falsification test records: the claims it bears on, what it did, and what it found."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class Test:
    """One falsification test and what it found. The verdicts read the results."""

    id: str
    claims: list[str]
    test: str
    result: dict[str, Any]
