"""
Parser for the TrainX DSL.
"""
from __future__ import annotations

from typing import List, Tuple

from .ast import ListDeclaration, QABlock
from .exceptions import TrainXParserError
from .tokens import Token


class TrainXParser:
    """Transforms tokens into an abstract syntax tree."""

    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.position = 0

    def parse(self) -> List[object]:
        statements: List[object] = []

        while not self._is_at_end():
            current = self._peek()

            if current.type == 'EOF':
                break

            if current.type == 'LIST':
                statements.append(self._parse_list())
            elif current.type == 'Q_BLOCK':
                # Check if this is an alias block
                if current.value.startswith('__ALIASES__:') or current.value.startswith('__IMAGE_ALIAS__:'):
                    # Expand aliases into multiple Q&A pairs
                    statements.extend(self._parse_alias_qablock())
                else:
                    statements.append(self._parse_qablock())
            else:
                raise TrainXParserError(
                    f"Unexpected token '{current.type}'",
                    line=current.line,
                    column=current.column,
                )

        return statements

    # ------------------------------------------------------------------ parsing

    def _parse_list(self) -> ListDeclaration:
        list_token = self._consume('LIST', "Expected 'List' keyword")
        name_token = self._consume('IDENTIFIER', "List name is required")
        self._consume('EQUAL', "Expected '=' after list name")
        self._consume('LBRACKET', "Expected '[' to start list entries")

        entries = []
        while not self._check('RBRACKET'):
            key_token = self._consume('STRING', "List keys must be quoted")
            self._consume('COLON', "Expected ':' between list key and value")
            value_token = self._consume('STRING', "List values must be quoted")
            entries.append((key_token.value, value_token.value))

            if self._match('COMMA'):
                continue
            elif self._check('RBRACKET'):
                break
            else:
                raise TrainXParserError(
                    "Expected ',' or ']' in list declaration",
                    line=self._peek().line,
                    column=self._peek().column,
                )

        self._consume('RBRACKET', "Expected ']' to close list declaration")

        return ListDeclaration(
            name=name_token.value,
            entries=entries,
            line=list_token.line,
            column=list_token.column,
        )

    def _parse_qablock(self) -> QABlock:
        q_token = self._consume('Q_BLOCK', "Expected Q: block")
        if not self._check('A_BLOCK'):
            raise TrainXParserError(
                "Each Q: block must be followed by an A:",
                line=q_token.line,
                column=q_token.column,
            )
        a_token = self._consume('A_BLOCK', "Expected A: block after Q:")

        question, is_image = self._normalize_question_value(q_token.value)

        return QABlock(
            question=question,
            answer=a_token.value,
            line=q_token.line,
            column=q_token.column,
            is_image=is_image,
        )

    def _parse_alias_qablock(self) -> List[QABlock]:
        """Parse alias Q block and generate multiple Q&A pairs."""
        q_token = self._consume('Q_BLOCK', "Expected Q: block")
        if not self._check('A_BLOCK'):
            raise TrainXParserError(
                "Each Q: block must be followed by an A:",
                line=q_token.line,
                column=q_token.column,
            )
        a_token = self._consume('A_BLOCK', "Expected A: block after Q:")

        # Extract aliases from token value
        # Format: __ALIASES__:alias1|alias2|alias3
        alias_str = q_token.value.replace('__ALIASES__:', '').replace('__IMAGE_ALIAS__:', '')
        aliases = alias_str.split('|')
        is_image = q_token.value.startswith('__IMAGE_ALIAS__:')
        
        if not aliases:
            raise TrainXParserError(
                "Alias block must contain at least one alias",
                line=q_token.line,
                column=q_token.column,
            )

        # Generate QABlock for each alias
        # First alias is canonical
        qa_blocks: List[QABlock] = []
        for alias in aliases:
            qa_blocks.append(QABlock(
                question=alias.strip(),
                answer=a_token.value,
                line=q_token.line,
                column=q_token.column,
                is_image=is_image,
            ))

        return qa_blocks

    def _normalize_question_value(self, value: str) -> Tuple[str, bool]:
        """Strip image marker if present."""
        if value.startswith('__IMAGE__:'):
            return value.replace('__IMAGE__:', '', 1), True
        return value, False

    # ------------------------------------------------------------------ helpers

    def _consume(self, token_type: str, message: str) -> Token:
        if self._check(token_type):
            return self._advance()
        token = self._peek()
        raise TrainXParserError(message, line=token.line, column=token.column)

    def _match(self, token_type: str) -> bool:
        if self._check(token_type):
            self._advance()
            return True
        return False

    def _check(self, token_type: str) -> bool:
        if self._is_at_end():
            return False
        return self._peek().type == token_type

    def _advance(self) -> Token:
        if not self._is_at_end():
            self.position += 1
        return self._previous()

    def _is_at_end(self) -> bool:
        return self._peek().type == 'EOF'

    def _peek(self) -> Token:
        return self.tokens[self.position]

    def _previous(self) -> Token:
        return self.tokens[self.position - 1]

