"""
Custom exception types for the TrainX compiler pipeline.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class TrainXError(Exception):
    """Base class for TrainX errors with location metadata."""

    message: str
    line: Optional[int] = None
    column: Optional[int] = None

    def __str__(self) -> str:
        if self.line is not None and self.column is not None:
            return f"{self.message} (line {self.line}, column {self.column})"
        if self.line is not None:
            return f"{self.message} (line {self.line})"
        return self.message


class TrainXLexerError(TrainXError):
    """Raised when raw TrainX source cannot be tokenized."""


class TrainXParserError(TrainXError):
    """Raised when the TrainX token stream cannot be parsed."""


class TrainXRuntimeError(TrainXError):
    """Raised when the interpreter cannot execute the TrainX AST."""

