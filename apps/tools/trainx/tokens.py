"""
Token definitions used by the TrainX compiler pipeline.
"""
from dataclasses import dataclass
from typing import Any


@dataclass
class Token:
    """Represents a lexical token."""

    type: str
    value: Any
    line: int
    column: int

