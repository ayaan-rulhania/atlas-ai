"""
Minimal biographical handler: synthesize_knowledge and clean_promotional_text.
"""
import re
from typing import List, Dict, Any, Optional


def synthesize_knowledge(
    query: str,
    research_knowledge: List[Dict[str, Any]],
    query_intent: Optional[Dict[str, Any]] = None,
) -> Optional[str]:
    """Synthesize research knowledge into a single response string. Returns None if empty."""
    if not research_knowledge:
        return None
    parts = []
    for item in research_knowledge[:5]:
        content = (item.get("content") or "").strip()
        if content:
            parts.append(content)
    if not parts:
        return None
    return " ".join(parts)[:1500] if parts else None


def clean_promotional_text(content: str) -> str:
    """Remove promotional boilerplate from text. Returns cleaned string."""
    if not content or not isinstance(content, str):
        return ""
    text = content.strip()
    # Remove common promotional phrases
    patterns = [
        r"\s*Sign up[^.]*\.?\s*",
        r"\s*Subscribe[^.]*\.?\s*",
        r"\s*Click here[^.]*\.?\s*",
        r"\s*Learn more[^.]*\.?\s*",
        r"\s*Visit our[^.]*\.?\s*",
        r"\s*\[.*?\]\s*",  # bracketed call-to-actions
    ]
    for p in patterns:
        text = re.sub(p, " ", text, flags=re.IGNORECASE)
    return " ".join(text.split()).strip()
