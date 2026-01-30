"""
Lexical analysis for the TrainX DSL.
"""
from __future__ import annotations

from typing import List

from .exceptions import TrainXLexerError
from .tokens import Token


class TrainXLexer:
    """Converts TrainX source code into a token stream."""

    QUOTE = '"'
    WHITESPACE = {' ', '\t', '\r'}

    def __init__(self, source: str):
        self.source = source or ""
        self.length = len(self.source)
        self.position = 0
        self.line = 1
        self.column = 1

    def tokenize(self) -> List[Token]:
        tokens: List[Token] = []

        while not self._is_at_end():
            current = self._peek()

            if current in self.WHITESPACE:
                self._advance()
                continue

            if current == '\n':
                self._advance()
                continue

            if current == '#':
                self._skip_comment()
                continue

            if current.lower() == 'q' and self._looks_like_block():
                tokens.append(self._lex_block('Q'))
                continue

            if current.lower() == 'a' and self._looks_like_block():
                tokens.append(self._lex_block('A'))
                continue

            if current.isalpha() or current == '_':
                tokens.append(self._lex_identifier())
                continue

            if current == self.QUOTE:
                tokens.append(self._lex_string())
                continue

            if current == '=':
                tokens.append(self._make_token('EQUAL', '='))
                self._advance()
                continue

            if current == '[':
                tokens.append(self._make_token('LBRACKET', '['))
                self._advance()
                continue

            if current == ']':
                tokens.append(self._make_token('RBRACKET', ']'))
                self._advance()
                continue

            if current == ',':
                tokens.append(self._make_token('COMMA', ','))
                self._advance()
                continue

            if current == ':':
                tokens.append(self._make_token('COLON', ':'))
                self._advance()
                continue

            if current == '{':
                tokens.append(self._make_token('LBRACE', '{'))
                self._advance()
                continue

            if current == '}':
                tokens.append(self._make_token('RBRACE', '}'))
                self._advance()
                continue

            raise TrainXLexerError(
                f"Unexpected character '{current}'",
                line=self.line,
                column=self.column,
            )

        tokens.append(Token('EOF', '', self.line, self.column))
        return tokens

    # ------------------------------------------------------------------ helpers

    def _looks_like_block(self) -> bool:
        """Detect whether the current position starts a Q: or A: block (supports qualifiers)."""
        lookahead_pos = self.position + 1
        while lookahead_pos < self.length and self.source[lookahead_pos] in self.WHITESPACE:
            lookahead_pos += 1

        # Allow optional qualifier e.g., (Image)
        if lookahead_pos < self.length and self.source[lookahead_pos] == '(':
            while lookahead_pos < self.length and self.source[lookahead_pos] != ')':
                lookahead_pos += 1
            if lookahead_pos < self.length and self.source[lookahead_pos] == ')':
                lookahead_pos += 1
            while lookahead_pos < self.length and self.source[lookahead_pos] in self.WHITESPACE:
                lookahead_pos += 1

        if lookahead_pos >= self.length:
            return False

        return self.source[lookahead_pos] == ':'

    def _lex_block(self, kind: str) -> Token:
        start_line = self.line
        start_column = self.column

        # Consume the leading letter (Q or A)
        self._advance()

        # Skip whitespace between the letter and optional qualifier
        while not self._is_at_end() and self._peek() in self.WHITESPACE:
            self._advance()

        is_image = False
        if kind.upper() == 'Q' and not self._is_at_end() and self._peek() == '(':
            qualifier = self._consume_parenthetical()
            if qualifier.lower() == 'image':
                is_image = True

        # Skip whitespace between qualifier and colon
        while not self._is_at_end() and self._peek() in self.WHITESPACE:
            self._advance()

        if self._is_at_end() or self._peek() != ':':
            raise TrainXLexerError(
                f"Expected ':' after '{kind}'",
                line=start_line,
                column=start_column,
            )

        # Consume colon
        self._advance()

        # Skip whitespace before text
        while not self._is_at_end() and self._peek() in self.WHITESPACE:
            self._advance()

        # Check for alias syntax: Q: {"Canonical" / "Alias 1" / "Alias 2"}?
        if kind.upper() == 'Q' and not self._is_at_end() and self._peek() == '{':
            # Parse alias syntax
            value = self._lex_alias_block(is_image=is_image)
        else:
            # Regular block parsing
            text_chars: List[str] = []
            while not self._is_at_end() and self._peek() != '\n':
                text_chars.append(self._peek())
                self._advance()

            # Trim trailing whitespace but preserve intentional spacing inside text
            value = ''.join(text_chars).strip()

        if kind.upper() == 'Q' and is_image:
            value = f"__IMAGE__:{value}"

        if not value:
            raise TrainXLexerError(
                f"{kind}: block cannot be empty",
                line=start_line,
                column=start_column,
            )

        # Consume newline if present
        if not self._is_at_end() and self._peek() == '\n':
            self._advance()

        token_type = 'Q_BLOCK' if kind.upper() == 'Q' else 'A_BLOCK'
        return Token(token_type, value, start_line, start_column)

    def _lex_identifier(self) -> Token:
        start_line = self.line
        start_column = self.column
        start_pos = self.position

        while not self._is_at_end() and (self._peek().isalnum() or self._peek() == '_'):
            self._advance()

        value = self.source[start_pos:self.position]
        token_type = 'LIST' if value.lower() == 'list' else 'IDENTIFIER'

        return Token(token_type, value, start_line, start_column)

    def _lex_string(self) -> Token:
        start_line = self.line
        start_column = self.column
        self._advance()  # Opening quote
        chars: List[str] = []

        while not self._is_at_end():
            char = self._peek()

            if char == self.QUOTE:
                self._advance()
                value = ''.join(chars)
                return Token('STRING', value, start_line, start_column)

            if char == '\\':
                self._advance()
                if self._is_at_end():
                    break
                escape = self._peek()
                chars.append(self._translate_escape(escape))
                self._advance()
                continue

            chars.append(char)
            self._advance()

        raise TrainXLexerError(
            "Unterminated string literal",
            line=start_line,
            column=start_column,
        )

    def _translate_escape(self, char: str) -> str:
        mappings = {
            '"': '"',
            '\\': '\\',
            'n': '\n',
            't': '\t',
        }
        return mappings.get(char, char)

    def _lex_alias_block(self, is_image: bool = False) -> str:
        """Parse alias syntax: {"Canonical" / "Alias 1" / "Alias 2"}?"""
        aliases: List[str] = []
        
        # Consume opening brace
        if self._peek() != '{':
            raise TrainXLexerError(
                "Expected '{' to start alias block",
                line=self.line,
                column=self.column,
            )
        self._advance()
        
        # Skip whitespace
        while not self._is_at_end() and self._peek() in self.WHITESPACE:
            self._advance()
        
        # Parse aliases separated by '/'
        while True:
            # Parse quoted string
            if self._peek() != self.QUOTE:
                raise TrainXLexerError(
                    "Expected quoted string in alias block",
                    line=self.line,
                    column=self.column,
                )
            
            self._advance()  # Consume opening quote
            alias_chars: List[str] = []
            
            while not self._is_at_end():
                char = self._peek()
                if char == self.QUOTE:
                    self._advance()
                    break
                if char == '\\':
                    self._advance()
                    if self._is_at_end():
                        break
                    escape = self._peek()
                    alias_chars.append(self._translate_escape(escape))
                    self._advance()
                    continue
                alias_chars.append(char)
                self._advance()
            
            aliases.append(''.join(alias_chars))
            
            # Skip whitespace
            while not self._is_at_end() and self._peek() in self.WHITESPACE:
                self._advance()
            
            # Check for separator or closing brace
            if self._is_at_end():
                raise TrainXLexerError(
                    "Unterminated alias block",
                    line=self.line,
                    column=self.column,
                )
            
            if self._peek() == '/':
                self._advance()
                # Skip whitespace after separator
                while not self._is_at_end() and self._peek() in self.WHITESPACE:
                    self._advance()
                continue
            elif self._peek() == '}':
                self._advance()
                break
            else:
                raise TrainXLexerError(
                    f"Unexpected character '{self._peek()}' in alias block, expected '/' or '}}'",
                    line=self.line,
                    column=self.column,
                )
        
        # Check for optional '?' at the end
        while not self._is_at_end() and self._peek() in self.WHITESPACE:
            self._advance()
        
        if not self._is_at_end() and self._peek() == '?':
            self._advance()
        
        # Return special format: __ALIASES__:alias1|alias2|alias3 (or IMAGE alias variant)
        prefix = "__IMAGE_ALIAS__:" if is_image else "__ALIASES__:"
        return f"{prefix}{'|'.join(aliases)}"

    def _consume_parenthetical(self) -> str:
        """Consume a parenthetical qualifier like (Image) and return its content."""
        if self._peek() != '(':
            return ""
        self._advance()  # '('
        chars: List[str] = []
        while not self._is_at_end() and self._peek() != ')':
            chars.append(self._peek())
            self._advance()
        if not self._is_at_end() and self._peek() == ')':
            self._advance()  # ')'
        return ''.join(chars).strip()

    def _skip_comment(self) -> None:
        while not self._is_at_end() and self._peek() != '\n':
            self._advance()
        if not self._is_at_end() and self._peek() == '\n':
            self._advance()

    def _make_token(self, token_type: str, value: str) -> Token:
        return Token(token_type, value, self.line, self.column)

    def _is_at_end(self) -> bool:
        return self.position >= self.length

    def _peek(self) -> str:
        return self.source[self.position]

    def _advance(self) -> None:
        if self._is_at_end():
            return
        char = self.source[self.position]
        self.position += 1
        if char == '\n':
            self.line += 1
            self.column = 1
        else:
            self.column += 1


