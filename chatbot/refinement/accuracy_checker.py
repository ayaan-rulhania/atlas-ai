"""
Accuracy checker (conservative).

This is intentionally heuristic-based: it does *not* attempt full fact-checking.
Instead it focuses on catching the most common high-risk hallucinations:
- Specific numbers/dates/percentages that are not present in the retrieved context.

If a sentence contains numeric claims that are not found in any retrieved
knowledge snippet, we remove that sentence and add a short note asking for the
exact dataset/timeframe if precision matters.
"""

from __future__ import annotations

import re
from typing import Dict, List


_NUM_TOKEN_RE = re.compile(
    r"""
    (?:
        \b\d{4}\b                 # years
        |
        \b\d{1,3}(?:,\d{3})+\b    # 1,000 style
        |
        \b\d+(?:\.\d+)?%?\b       # 12 / 12.5 / 12%
    )
    """,
    re.VERBOSE,
)


def verify_response_accuracy(answer: str, knowledge_items: List[Dict], *, query: str = "") -> str:
    if not answer or not isinstance(answer, str):
        return answer
    if not knowledge_items:
        return answer

    # For very short, non-numeric queries (e.g. "bye", "thanks", "learn
    # sometimes"), the numeric guardrail is more distracting than helpful.
    # Skip the accuracy note entirely in those cases.
    simple_query = (query or "").strip().lower()
    if simple_query and len(simple_query.split()) <= 4 and not any(ch.isdigit() for ch in simple_query):
        return answer

    # Build a low-cost searchable blob of retrieved content.
    blob_parts: List[str] = []
    for k in knowledge_items[:10]:
        content = (k.get("content") or "")
        title = (k.get("title") or "")
        if content:
            blob_parts.append(content)
        if title:
            blob_parts.append(title)
    blob = " ".join(blob_parts).lower()
    if len(blob) < 40:
        return answer

    # Work sentence-by-sentence; keep formatting conservative.
    sentences = re.split(r"(?<=[.!?])\s+", answer.strip())
    if len(sentences) <= 1:
        sentences = [answer.strip()]

    unsupported_sentences: List[str] = []
    for s in sentences:
        tokens = [t.strip() for t in _NUM_TOKEN_RE.findall(s)]
        if not tokens:
            continue
        # If any numeric token is present in the retrieved blob, we consider it supported.
        supported = any(t.lower() in blob for t in tokens if t)
        if not supported:
            unsupported_sentences.append(s)

    if not unsupported_sentences:
        # All numeric claims appear somewhere in the retrieved blob, so we keep
        # the answer as-is and do not add any cautionary note.
        return answer

    # Remove unsupported numeric sentences (avoid over-aggressive trimming).
    cleaned = answer
    removed_any = False
    for s in unsupported_sentences:
        if s and s in cleaned:
            cleaned = cleaned.replace(s, "").strip()
            removed_any = True
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()

    # If we stripped too much, keep the original but still add a caution note.
    if len(cleaned) < max(40, int(len(answer) * 0.35)):
        # If we had to revert to the original text, treat it as if we did not
        # remove anything so we don't append a confusing numeric disclaimer.
        cleaned = answer.strip()
        removed_any = False

    # Only surface the numeric disclaimer when we actually removed one or more
    # sentences. This keeps answers for casual queries from being cluttered
    # with warnings that do not really apply.
    if removed_any:
        note = (
            "Note: I couldn’t verify some numeric details from the sources I pulled. "
            "If you need exact figures, tell me the exact region/timeframe/dataset and I’ll re-check."
        )
        if note.lower() not in cleaned.lower():
            cleaned = f"{cleaned}\n\n{note}"
    return cleaned

