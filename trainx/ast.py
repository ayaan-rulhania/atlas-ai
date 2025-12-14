"""
AST nodes used by the TrainX parser.
"""
from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class ListDeclaration:
    """Represents a `List name = ["key":"value", ...]` declaration."""

    name: str
    entries: List[Tuple[str, str]]
    line: int
    column: int


@dataclass
class QABlock:
    """Represents a Q/A statement pair."""

    question: str
    answer: str
    line: int
    column: int
    is_image: bool = False

