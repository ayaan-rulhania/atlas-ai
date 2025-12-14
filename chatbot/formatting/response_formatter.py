"""
Final Response Formatter (post-model, pre-return).

Goal: light-touch normalization and grammar cleanup without forcing bullets.
This runs after the model/refiner and before the final response cleaner.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, Optional


_BULLET_REQUEST_RE = re.compile(r"\b(bullets?|bullet\s+points?|list|steps?|checklist)\b", re.IGNORECASE)


def _normalize_whitespace(text: str) -> str:
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _fix_punctuation_spacing(text: str) -> str:
    # Space after punctuation when missing: "word.Word" -> "word. Word"
    text = re.sub(r"([a-z0-9])([.!?])([A-Z])", r"\1\2 \3", text)
    # Remove spaces before punctuation: "word !" -> "word!"
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    return text


def _ensure_terminal_punctuation(text: str) -> str:
    if not text:
        return text
    # If ends with a quote or bracket, look one char back
    tail = text[-1]
    if tail in ")]}\"'":
        core = text.rstrip(")]}\"'")
        if core and core[-1] not in ".!?":
            return core + "." + text[len(core):]
        return text
    if tail not in ".!?":
        return text + "."
    return text


def _debullet_if_not_requested(text: str, user_message: str) -> str:
    """
    If the answer is purely bullet list and user didn't ask for bullets/steps,
    convert to short paragraphs.
    """
    if not text:
        return text
    if _BULLET_REQUEST_RE.search(user_message or ""):
        return text

    lines = [ln.rstrip() for ln in text.splitlines()]
    bullet_lines = [ln for ln in lines if re.match(r"^\s*-\s+\S", ln)]
    nonempty = [ln for ln in lines if ln.strip()]
    if nonempty and len(bullet_lines) >= 3 and len(bullet_lines) / len(nonempty) > 0.6:
        # Convert "- x" into "x" sentences
        paras = []
        for ln in nonempty:
            m = re.match(r"^\s*-\s+(.*)$", ln)
            if m:
                item = m.group(1).strip()
                paras.append(_ensure_terminal_punctuation(item))
            else:
                paras.append(ln.strip())
        return "\n\n".join(paras)
    return text


def _strip_overformatting(text: str) -> str:
    # Avoid repeated bolding of generic keywords
    text = re.sub(r"\*\*(Important|Note|Warning|Tip|Summary)\*\*", r"\1", text)
    return text


@dataclass
class FinalResponseFormatter:
    """
    Lightweight final formatter. Intentionally conservative.
    """

    def format(self, text: str, *, user_message: str = "", hints: Optional[Dict] = None) -> str:
        if not text:
            return text

        out = str(text)
        out = _normalize_whitespace(out)
        out = _fix_punctuation_spacing(out)
        out = _strip_overformatting(out)
        out = _debullet_if_not_requested(out, user_message=user_message)
        return out


_instance: Optional[FinalResponseFormatter] = None


def get_final_response_formatter() -> FinalResponseFormatter:
    global _instance
    if _instance is None:
        _instance = FinalResponseFormatter()
    return _instance

