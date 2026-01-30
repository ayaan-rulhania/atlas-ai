"""
Orchestrates the TrainX compilation pipeline.
"""
from __future__ import annotations

from typing import Dict, List

from .exceptions import TrainXError
from .interpreter import TrainXInterpreter
from .lexer import TrainXLexer
from .parser import TrainXParser


class TrainXCompiler:
    """Runs the TrainX pipeline end-to-end."""

    def __init__(self, source: str):
        self.source = source or ""

    def compile(self) -> List[Dict[str, str]]:
        lexer = TrainXLexer(self.source)
        tokens = lexer.tokenize()

        parser = TrainXParser(tokens)
        statements = parser.parse()

        interpreter = TrainXInterpreter(statements)
        return interpreter.execute()


def compile_trainx(source: str) -> List[Dict[str, str]]:
    """Convenience helper for compiling TrainX source."""
    compiler = TrainXCompiler(source)
    return compiler.compile()

