"""
Helper utilities for building biographical/definition responses.
"""
from __future__ import annotations

import random
import re
from typing import Any, Dict, List, Optional

from services import get_response_cleaner


def clean_promotional_text(text: Optional[str]) -> Optional[str]:
    """Remove promotional/ad copy language from text and make it more direct."""
    if not text:
        return text

    promotional_patterns = [
        r'Learn\s+(everything\s+)?(you\s+need\s+to\s+know\s+)?(about\s+)?',
        r'Discover\s+(everything\s+)?(about\s+)?',
        r'Find\s+out\s+(everything\s+)?(about\s+)?',
        r'Get\s+(started\s+)?(with\s+)?(everything\s+)?(about\s+)?',
        r'Explore\s+(everything\s+)?(about\s+)?',
        r'Master\s+(everything\s+)?(about\s+)?',
        r'Unlock\s+(the\s+)?(secrets?\s+of\s+)?',
        r'Click\s+(here\s+)?(to\s+)?',
        r'Visit\s+(our\s+)?(website\s+)?(to\s+)?',
        r'Check\s+out\s+(our\s+)?',
        r'Sign\s+up\s+(for\s+)?',
        r'Subscribe\s+(to\s+)?',
        r'Join\s+(us\s+)?(to\s+)?',
        r'Start\s+(your\s+)?(journey\s+)?(with\s+)?',
    ]

    cleaned = text
    for pattern in promotional_patterns:
        cleaned = re.sub(r'^' + pattern, '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\s+' + pattern, ' ', cleaned, flags=re.IGNORECASE)

    cta_endings = [
        r'\s+to\s+get\s+started\.?$',
        r'\s+to\s+learn\s+more\.?$',
        r'\s+to\s+find\s+out\s+more\.?$',
        r'\s+to\s+discover\s+more\.?$',
        r'\s+and\s+more\.?$',
        r'\s+\.\s*\.\s*\.\s*$',  # Remove trailing ellipses
    ]

    for pattern in cta_endings:
        cleaned = re.sub(pattern, '.', cleaned, flags=re.IGNORECASE)

    cleaned = re.sub(r'\s+', ' ', cleaned)
    cleaned = cleaned.strip()

    if cleaned and cleaned[0].islower():
        cleaned = cleaned[0].upper() + cleaned[1:]

    return cleaned


def synthesize_knowledge(
    query: str,
    knowledge_items: List[Dict[str, Any]],
    query_intent: Optional[Dict[str, Any]],
) -> Optional[str]:
    """Synthesize multiple knowledge items into a coherent, thoughtful response."""
    if not knowledge_items:
        return None

    # Diversify by source so multi-engine research doesn't echo one snippet repeatedly.
    diversified: List[Dict[str, Any]] = []
    by_source: Dict[str, List[Dict[str, Any]]] = {}
    for k in knowledge_items:
        src = (k.get("source") or "unknown").strip().lower()
        by_source.setdefault(src, []).append(k)
    # Interleave sources (stable order by first appearance)
    source_order = list(dict.fromkeys([(k.get("source") or "unknown").strip().lower() for k in knowledge_items]))
    for i in range(0, 3):  # up to 3 rounds
        for src in source_order:
            bucket = by_source.get(src) or []
            if i < len(bucket):
                diversified.append(bucket[i])
    if diversified:
        knowledge_items = diversified

    response_cleaner = get_response_cleaner()
    intent = query_intent.get('intent', 'general') if query_intent else 'general'
    entity = query_intent.get('entity', '') if query_intent else ''
    is_person_query = query_intent.get('is_person_query', False) if query_intent else False

    if intent == 'biographical' or is_person_query:
        return response_cleaner.synthesize_biographical_response(entity, knowledge_items)

    if intent == 'definition' and entity:
        return response_cleaner.synthesize_definition_response(entity, knowledge_items, query_intent)

    key_points: List[str] = []
    definitions: List[str] = []
    examples: List[str] = []

    for item in knowledge_items[:8]:
        content = item.get('content', '').strip()
        if not content or len(content) < 20:
            continue

        cleaned = response_cleaner.clean_response(content)
        if not cleaned or len(cleaned) < 20:
            continue

        cleaned = clean_promotional_text(cleaned)
        if not cleaned:
            continue

        sentences = [s.strip() for s in cleaned.split('.') if len(s.strip()) > 15]

        for sentence in sentences[:3]:
            sentence_lower = sentence.lower()

            if any(word in sentence_lower for word in ['is', 'are', 'was', 'were', 'means', 'refers to', 'defined as']):
                if sentence not in definitions:
                    definitions.append(sentence)
            elif any(word in sentence_lower for word in ['example', 'for instance', 'such as', 'like', 'including']):
                if sentence not in examples:
                    examples.append(sentence)
            else:
                if sentence not in key_points:
                    key_points.append(sentence)

    response_parts: List[str] = []

    if definitions:
        main_definition = definitions[0]
        if entity:
            entity_lower = entity.lower()
            main_def_lower = main_definition.lower()

            if main_def_lower.startswith(entity_lower):
                response_parts.append(f"**{entity.title()}** {main_definition[len(entity):]}")
            elif entity_lower in main_def_lower[:50]:
                response_parts.append(main_definition)
            else:
                response_parts.append(f"**{entity.title()}** is {main_definition}")
        else:
            response_parts.append(main_definition)

    if key_points:
        if definitions:
            response_parts.append(" " + key_points[0])
        else:
            response_parts.append(key_points[0])

        if len(key_points) > 1:
            response_parts.append(" " + key_points[1])

    if examples and response_parts:
        response_parts.append(f"\\n\\nFor example, {examples[0]}")

    synthesized = "".join(response_parts)
    synthesized = response_cleaner.fix_grammar_issues(synthesized)
    synthesized = response_cleaner.fix_incomplete_sentences(synthesized)

    if len(synthesized) > 500:
        last_period = synthesized[:500].rfind('.')
        if last_period > 300:
            synthesized = synthesized[:last_period + 1]
        else:
            synthesized = synthesized[:497] + "..."

    if synthesized and query_intent:
        starters = ["Sure! ", "Absolutely. ", "Great question! ", "I'd be happy to explain. ", ""]
        if query_intent.get('is_follow_up'):
            synthesized = random.choice(starters) + synthesized

    return synthesized or None

