"""
Interpreter for the TrainX DSL.
"""
from __future__ import annotations

import itertools
import re
from typing import Dict, List, Sequence, Tuple

from .ast import ListDeclaration, QABlock
from .exceptions import TrainXRuntimeError


PLACEHOLDER_PATTERN = re.compile(r"\{([a-zA-Z_][\w]*)(?:\.(object))?\}")
ALIAS_PATTERN = re.compile(r"\{([^{}]*\"[^{}]*\"[^{}]*)\}")


class TrainXInterpreter:
    """Executes a TrainX AST and emits structured Q&A pairs."""

    def __init__(self, statements: Sequence[object]):
        self.statements = statements
        self.lists: Dict[str, List[Tuple[str, str]]] = {}

    def execute(self) -> List[Dict[str, str]]:
        results: List[Dict[str, str]] = []

        for statement in self.statements:
            if isinstance(statement, ListDeclaration):
                self.lists[statement.name] = statement.entries
                continue

            if isinstance(statement, QABlock):
                results.extend(self._expand_qablock(statement))
                continue

            raise TrainXRuntimeError(
                "Unsupported statement encountered",
                line=getattr(statement, "line", None),
                column=getattr(statement, "column", None),
            )

        return results

    # ------------------------------------------------------------------ helpers

    def _expand_qablock(self, block: QABlock) -> List[Dict[str, str]]:
        question_variants = self._expand_aliases(block.question)
        answer_variants = self._expand_aliases(block.answer)

        expanded_pairs: List[Dict[str, str]] = []

        for question in question_variants:
            for answer in answer_variants:
                expanded_pairs.extend(self._expand_placeholders(block, question, answer))

        return expanded_pairs

    def _expand_placeholders(self, block: QABlock, question: str, answer: str) -> List[Dict[str, str]]:
        placeholders = self._collect_placeholders(question, answer)

        if not placeholders:
            return [self._build_pair(question, answer, block.is_image)]

        list_names = sorted(placeholders)

        entries_per_list: List[List[Tuple[str, str]]] = []
        for name in list_names:
            if name not in self.lists:
                raise TrainXRuntimeError(
                    f"List '{name}' is not defined",
                    line=block.line,
                    column=block.column,
                )
            if not self.lists[name]:
                raise TrainXRuntimeError(
                    f"List '{name}' does not contain any entries",
                    line=block.line,
                    column=block.column,
                )
            entries_per_list.append(self.lists[name])

        results: List[Dict[str, str]] = []
        for combination in itertools.product(*entries_per_list):
            mapping = {name: entry for name, entry in zip(list_names, combination)}
            final_question = self._apply_mapping(question, mapping)
            final_answer = self._apply_mapping(answer, mapping)
            results.append(self._build_pair(final_question, final_answer, block.is_image))

        return results

    def _build_pair(self, question: str, answer: str, is_image: bool) -> Dict[str, str]:
        q = question.strip()
        a = answer.strip()
        if is_image:
            q = self._normalize_image_question(q)
        pair = {
            "question": q,
            "answer": a,
        }
        if is_image:
            pair["is_image"] = True
        if is_image or self._looks_like_image(a):
            pair["type"] = "image"
        return pair

    @staticmethod
    def _looks_like_image(answer: str) -> bool:
        if not answer:
            return False
        lower = answer.lower()
        if '{{trainx_iframe:' in lower:
            return True
        img_exts = ('.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp', '.svg')
        if any(lower.endswith(ext) for ext in img_exts):
            return True
        # Handle URLs with query strings
        return any(ext in lower for ext in img_exts) and ('http://' in lower or 'https://' in lower)

    @staticmethod
    def _normalize_image_question(question: str) -> str:
        q = question.strip()
        if not q:
            return "Create an image"
        lower = q.lower()
        keywords = ("image", "picture", "photo", "render", "draw", "illustration", "graphic")
        if any(keyword in lower for keyword in keywords):
            return q
        return f"Create an image of {q}"

    def _collect_placeholders(self, *texts: str) -> List[str]:
        names = []
        for text in texts:
            for match in PLACEHOLDER_PATTERN.findall(text):
                name = match[0]
                if name not in names:
                    names.append(name)
        return names

    def _apply_mapping(self, text: str, mapping: Dict[str, Tuple[str, str]]) -> str:
        rendered = text
        for name, (key, value) in mapping.items():
            rendered = rendered.replace(f"{{{name}}}", key)
            rendered = rendered.replace(f"{{{name}.object}}", value)
            rendered = rendered.replace(f"{{{name}.Object}}", value)
        return rendered

    def _expand_aliases(self, text: str) -> List[str]:
        def _expand(current: str) -> List[str]:
            match = self._find_alias(current)
            if not match:
                return [current]

            start, end, options = match
            expanded: List[str] = []
            for option in options:
                substituted = current[:start] + option + current[end:]
                expanded.extend(_expand(substituted))
            return expanded

        return [variant.strip() for variant in _expand(text)]

    def _find_alias(self, text: str):
        for match in ALIAS_PATTERN.finditer(text):
            inner = match.group(1)
            if '"' not in inner:
                continue
            options = self._parse_alias_options(inner)
            if options:
                return match.start(), match.end(), options
        return None

    def _parse_alias_options(self, inner: str) -> List[str]:
        raw_options = inner.split('/')
        options = []
        for raw in raw_options:
            value = raw.strip()
            if value.startswith('"') and value.endswith('"'):
                options.append(value[1:-1])
        return options

