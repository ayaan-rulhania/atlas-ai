"""
Helper utilities for building biographical/definition responses.
"""
from __future__ import annotations

import random
import re
from typing import Any, Dict, List, Optional

from services import get_response_cleaner
from collections import defaultdict
import re


def _verify_facts_across_sources(knowledge_items: List[Dict[str, Any]]) -> Dict[str, Dict]:
    """
    Verify facts across multiple sources to identify agreements and conflicts.
    Returns a dictionary with fact verification results.
    """
    if len(knowledge_items) < 2:
        return {}

    # Extract key facts from each source
    source_facts = {}
    for item in knowledge_items:
        source = item.get('source', 'unknown')
        content = item.get('content', '')

        # Extract potential facts (sentences with key information)
        sentences = re.split(r'[.!?]+', content)
        facts = []

        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 20:
                continue

            # Look for sentences that contain factual information
            if any(indicator in sentence.lower() for indicator in [
                ' is ', ' are ', ' was ', ' were ', ' has ', ' have ', ' contains ',
                ' consists ', ' includes ', ' means ', ' refers to ', ' represents ',
                ' developed ', ' created ', ' invented ', ' founded ', ' established '
            ]):
                facts.append(sentence)

        source_facts[source] = facts[:3]  # Limit to top 3 facts per source

    # Find agreements and conflicts
    verification_results = {}
    all_facts = []
    for facts in source_facts.values():
        all_facts.extend(facts)

    # Simple similarity-based verification
    for fact in all_facts:
        fact_lower = fact.lower()
        similar_facts = []
        conflicting_facts = []

        for other_fact in all_facts:
            if other_fact == fact:
                continue

            other_lower = other_fact.lower()

            # Check for similarity (basic word overlap)
            fact_words = set(fact_lower.split())
            other_words = set(other_lower.split())
            overlap = len(fact_words & other_words)

            if overlap >= 3:  # Significant overlap
                # Check for potential conflicts (different numbers, dates, etc.)
                fact_nums = re.findall(r'\d+', fact)
                other_nums = re.findall(r'\d+', other_fact)

                if fact_nums != other_nums and fact_nums and other_nums:
                    conflicting_facts.append(other_fact)
                else:
                    similar_facts.append(other_fact)

        if similar_facts or conflicting_facts:
            verification_results[fact] = {
                'agreements': len(similar_facts),
                'conflicts': conflicting_facts,
                'confidence': len(similar_facts) / max(1, len(similar_facts) + len(conflicting_facts))
            }

    return verification_results


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

    # Enhanced source prioritization and diversification
    source_priority = {
        'wikipedia': 10,  # Highest priority - authoritative, structured knowledge
        'gem_source': 9,  # User-curated sources
        'brain': 8,       # Learned knowledge
        'duckduckgo': 6,  # Good general search
        'google': 5,      # Standard web search
        'bing': 4,        # Additional web search
        'unknown': 1      # Lowest priority
    }

    # Group by source and apply prioritization
    prioritized_items: List[Dict[str, Any]] = []
    by_source: Dict[str, List[Dict[str, Any]]] = {}

    for k in knowledge_items:
        src = (k.get("source") or "unknown").strip().lower()
        # Normalize source names
        if 'wikipedia' in src:
            src = 'wikipedia'
        elif 'gem' in src:
            src = 'gem_source'
        elif 'brain' in src:
            src = 'brain'
        elif 'duck' in src:
            src = 'duckduckgo'
        elif 'google' in src:
            src = 'google'
        elif 'bing' in src:
            src = 'bing'

        by_source.setdefault(src, []).append(k)

    # Sort sources by priority and diversify within each priority level
    sorted_sources = sorted(by_source.keys(), key=lambda s: source_priority.get(s, 1), reverse=True)

    # Take top 2-3 items from highest priority sources, then 1-2 from lower priority
    for i, src in enumerate(sorted_sources):
        bucket = by_source[src]
        # Sort bucket by content length (prefer more detailed info)
        bucket.sort(key=lambda x: len(x.get('content', '')), reverse=True)

        if i < 2:  # Top 2 priority sources get 2-3 items each
            prioritized_items.extend(bucket[:3])
        else:  # Lower priority sources get 1-2 items
            prioritized_items.extend(bucket[:2])

    knowledge_items = prioritized_items[:10]  # Limit to top 10 for processing

    response_cleaner = get_response_cleaner()
    intent = query_intent.get('intent', 'general') if query_intent else 'general'
    entity = query_intent.get('entity', '') if query_intent else ''
    is_person_query = query_intent.get('is_person_query', False) if query_intent else False

    # Detect query types that benefit from structured synthesis
    query_lower = query.lower()
    is_comparison = any(word in query_lower for word in ['vs', 'versus', 'compare', 'comparison', 'difference', 'different'])
    is_relationship = any(word in query_lower for word in ['relationship', 'connection', 'between', 'how does', 'how do'])
    is_technical = any(word in query_lower for word in ['how to', 'tutorial', 'guide', 'steps', 'process'])

    # Cross-source fact verification
    fact_verification = _verify_facts_across_sources(knowledge_items) if len(knowledge_items) > 1 else {}

    if intent == 'biographical' or is_person_query:
        return response_cleaner.synthesize_biographical_response(entity, knowledge_items)

    if intent == 'definition' and entity:
        return response_cleaner.synthesize_definition_response(entity, knowledge_items, query_intent)

    key_points: List[str] = []
    definitions: List[str] = []
    examples: List[str] = []
    relationships: List[str] = []  # For relationship/comparison queries
    steps: List[str] = []  # For how-to/technical queries

    # Enhanced processing based on query type
    items_to_process = knowledge_items[:8]  # Use our prioritized list
    
    for item in items_to_process:
        content = item.get('content', '').strip()
        if not content or len(content) < 20:
            continue

        # CRITICAL: Filter out JavaScript code, Wikipedia metadata, and irrelevant content
        content_lower = content.lower()
        
        # Skip if content is mostly code
        if any(pattern in content_lower[:200] for pattern in [
            'export const', 'export let', 'export var', 'function(', '=> {',
            'const ', 'let ', 'var ', 'import ', 'module.exports'
        ]) and content.count('{') > 3:
            continue  # Likely JavaScript code, skip
        
        # Skip Wikipedia error messages
        if any(pattern in content_lower for pattern in [
            'this article contains one or more duplicated citations',
            'references script detected',
            'systematic endeavour to gain knowledge',
            'from wikipedia, the free encyclopedia'
        ]):
            # Try to extract actual content after error message
            error_end = max(
                content_lower.find('this article contains'),
                content_lower.find('references script'),
                content_lower.find('from wikipedia, the free encyclopedia')
            )
            if error_end > 0:
                content = content[error_end + 100:]  # Skip past error message
            else:
                continue  # Skip if we can't find actual content

        cleaned = response_cleaner.clean_response(content)
        if not cleaned or len(cleaned) < 20:
            continue

        cleaned = clean_promotional_text(cleaned)
        if not cleaned:
            continue

        # ENHANCED: Extract key sentences more intelligently
        # For long content (like gem sources), extract first few meaningful sentences
        sentences = [s.strip() for s in cleaned.split('.') if len(s.strip()) > 15]
        
        # For very long content, prioritize first sentences which are usually most relevant
        max_sentences_per_item = 5 if len(cleaned) > 500 else 3
        
        # Remove source attribution lines that make responses look like raw output
        # Patterns like "Sources: DuckDuckGo — ..." or "Model: Thor 1.0..."
        source_patterns = [
            r'^Sources?:.*$',
            r'^Model:.*$',
            r'^Context-aware:.*$',
            r'^Note:.*$',
            r'DuckDuckGo\s*—',
            r'Google\s*—',
            r'Bing\s*—',
        ]
        
        # Check query relevance - only use sentences that relate to the query
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        for sentence in sentences[:max_sentences_per_item]:
            sentence_lower = sentence.lower()
            
            # Skip source attribution lines
            if any(re.search(pattern, sentence, re.IGNORECASE) for pattern in source_patterns):
                continue
            
            # Skip if sentence is just promotional/ad copy
            if any(phrase in sentence_lower for phrase in ['click here', 'visit our', 'sign up', 'subscribe now']):
                continue
            
            # Skip sentences that are just metadata
            if sentence_lower.startswith(('sources:', 'model:', 'context-aware:', 'note:', 'export', 'const', 'let', 'var')):
                continue
            
            # Skip JavaScript code patterns
            if any(pattern in sentence_lower for pattern in ['export const', 'function(', '=> {', 'module.exports']):
                continue
            
            # Skip Wikipedia error messages
            if any(pattern in sentence_lower for pattern in ['duplicated citations', 'references script', 'systematic endeavour']):
                continue
            
            # RELEVANCE CHECK: Only include sentences that relate to the query
            # Check if sentence contains query words or related terms
            sentence_words = set(sentence_lower.split())
            common_words = sentence_words & query_words
            
            # If entity is specified, check if sentence mentions it
            if entity:
                entity_lower = entity.lower()
                if entity_lower not in sentence_lower and len(common_words) == 0:
                    continue  # Skip if sentence doesn't mention entity or share words with query
            
            # For gem sources, be more strict - only use highly relevant sentences
            if item.get("source") == "gem_source" or item.get("priority") == 1:
                if not common_words and (not entity or entity_lower not in sentence_lower):
                    continue  # Skip irrelevant sentences from gem sources

            # Enhanced classification based on query type and content
            confidence_boost = 0
            if sentence in fact_verification:
                confidence_boost = fact_verification[sentence].get('confidence', 0)

            # Special handling for different query types
            if is_comparison or is_relationship:
                # Look for relationship indicators
                if any(word in sentence_lower for word in [
                    'relationship', 'connection', 'between', 'compared to', 'versus', 'vs',
                    'difference', 'similar', 'unlike', 'whereas', 'while'
                ]):
                    if sentence not in relationships:
                        relationships.append((sentence, confidence_boost))
                    continue

            if is_technical:
                # Look for step-by-step or process indicators
                if any(word in sentence_lower for word in [
                    'first', 'then', 'next', 'after', 'finally', 'step', 'process',
                    'begin by', 'start with', 'follow these'
                ]):
                    if sentence not in steps:
                        steps.append((sentence, confidence_boost))
                    continue

            # Standard classification with confidence weighting
            if any(word in sentence_lower for word in ['is', 'are', 'was', 'were', 'means', 'refers to', 'defined as']):
                if sentence not in [s[0] if isinstance(s, tuple) else s for s in definitions]:
                    definitions.append((sentence, confidence_boost))
            elif any(word in sentence_lower for word in ['example', 'for instance', 'such as', 'like', 'including']):
                if sentence not in [s[0] if isinstance(s, tuple) else s for s in examples]:
                    examples.append((sentence, confidence_boost))
            else:
                if sentence not in [s[0] if isinstance(s, tuple) else s for s in key_points]:
                    key_points.append((sentence, confidence_boost))

    # Enhanced response synthesis with confidence weighting and query-type awareness
    response_parts: List[str] = []

    # Sort by confidence for better quality
    definitions = sorted(definitions, key=lambda x: x[1] if isinstance(x, tuple) else 0, reverse=True)
    key_points = sorted(key_points, key=lambda x: x[1] if isinstance(x, tuple) else 0, reverse=True)
    examples = sorted(examples, key=lambda x: x[1] if isinstance(x, tuple) else 0, reverse=True)
    relationships = sorted(relationships, key=lambda x: x[1] if isinstance(x, tuple) else 0, reverse=True)
    steps = sorted(steps, key=lambda x: x[1] if isinstance(x, tuple) else 0, reverse=True)

    # Handle different query types with structured responses
    if is_comparison or is_relationship:
        # Structured comparison/relationship response
        if entity:
            response_parts.append(f"**{entity.title()}**:")
        else:
            response_parts.append(f"**{query}**:")

        for rel, conf in relationships[:3]:
            response_parts.append(f"• {rel}")
        for point, conf in key_points[:2]:
            response_parts.append(f"• {point}")

    elif is_technical:
        # Structured how-to/technical response
        if entity:
            response_parts.append(f"**{entity.title()}**:")

        # Add steps in order
        for step, conf in steps[:5]:
            response_parts.append(f"• {step}")
        for point, conf in key_points[:2]:
            response_parts.append(f"• {point}")

    else:
        # Standard definition + key points response
        if definitions:
            main_definition = definitions[0][0] if isinstance(definitions[0], tuple) else definitions[0]
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
                response_parts.append(" " + (key_points[0][0] if isinstance(key_points[0], tuple) else key_points[0]))
            else:
                response_parts.append(key_points[0][0] if isinstance(key_points[0], tuple) else key_points[0])

            if len(key_points) > 1:
                response_parts.append(" " + (key_points[1][0] if isinstance(key_points[1], tuple) else key_points[1]))

        if examples and response_parts:
            example_text = examples[0][0] if isinstance(examples[0], tuple) else examples[0]
            response_parts.append(f"\\n\\nFor example, {example_text}")

    synthesized = "".join(response_parts)
    
    # Remove any remaining source attribution patterns
    source_patterns = [
        r'Sources?:.*?(?=\n|$)',
        r'Model:.*?(?=\n|$)',
        r'Context-aware:.*?(?=\n|$)',
        r'Note:.*?(?=\n|$)',
        r'DuckDuckGo\s*—.*?(?=\n|$)',
        r'Google\s*—.*?(?=\n|$)',
        r'Bing\s*—.*?(?=\n|$)',
    ]
    for pattern in source_patterns:
        synthesized = re.sub(pattern, '', synthesized, flags=re.IGNORECASE | re.MULTILINE)
    
    synthesized = response_cleaner.fix_grammar_issues(synthesized)
    synthesized = response_cleaner.fix_incomplete_sentences(synthesized)
    
    # Clean up multiple spaces and newlines
    synthesized = re.sub(r'\s+', ' ', synthesized)
    synthesized = re.sub(r'\n\s*\n', '\n\n', synthesized)
    synthesized = synthesized.strip()

    if len(synthesized) > 500:
        last_period = synthesized[:500].rfind('.')
        if last_period > 300:
            synthesized = synthesized[:last_period + 1]
        else:
            synthesized = synthesized[:497] + "..."

    # Only add starters if it's a follow-up, and only if the response doesn't already start with one
    if synthesized and query_intent:
        if query_intent.get('is_follow_up') and not synthesized.lower().startswith(('sure', 'absolutely', 'great', "i'd", 'here')):
            starters = ["Sure! ", "Absolutely. ", "Great question! ", "I'd be happy to explain. ", ""]
            synthesized = random.choice(starters) + synthesized

    return synthesized or None

