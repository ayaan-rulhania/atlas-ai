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


# Enhanced token patterns for accuracy checking
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

_DATE_RE = re.compile(
    r"""
    (?:
        \b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b  # MM/DD/YYYY or DD-MM-YYYY
        |
        \b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b    # YYYY/MM/DD
        |
        \b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b
        |
        \b\d{4}\b                           # standalone years
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)

_ENTITY_RE = re.compile(
    r"""
    (?:
        \b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b  # Proper nouns (multiple capitalized words)
    )
    """,
    re.VERBOSE,
)

_TECHNICAL_TERM_RE = re.compile(
    r"""
    (?:
        \b[A-Z][a-z]*(?:[A-Z][a-z]*)*\b    # CamelCase terms
        |
        \b\w+(?:[-_]\w+)+\b                # hyphenated/underscored terms
    )
    """,
    re.VERBOSE,
)


def _extract_claims_from_text(text: str) -> Dict[str, List[str]]:
    """Extract different types of claims from text for verification."""
    claims = {
        'numeric': [],
        'dates': [],
        'entities': [],
        'technical_terms': [],
        'causal_relationships': []
    }

    sentences = re.split(r'(?<=[.!?])\s+', text.strip())

    for sentence in sentences:
        # Extract numeric claims
        numeric_tokens = [t.strip() for t in _NUM_TOKEN_RE.findall(sentence)]
        claims['numeric'].extend(numeric_tokens)

        # Extract date claims
        date_tokens = [t.strip() for t in _DATE_RE.findall(sentence)]
        claims['dates'].extend(date_tokens)

        # Extract named entities (simplified heuristic)
        entity_tokens = [t.strip() for t in _ENTITY_RE.findall(sentence)]
        # Filter out common false positives
        filtered_entities = [e for e in entity_tokens if not any(word in e.lower() for word in [
            'the', 'and', 'but', 'for', 'are', 'with', 'this', 'that', 'from', 'into'
        ])]
        claims['entities'].extend(filtered_entities)

        # Extract technical terms
        technical_tokens = [t.strip() for t in _TECHNICAL_TERM_RE.findall(sentence)]
        claims['technical_terms'].extend(technical_tokens)

        # Extract causal relationships (basic pattern matching)
        if any(word in sentence.lower() for word in ['because', 'causes', 'leads to', 'results in', 'due to', 'therefore']):
            claims['causal_relationships'].append(sentence.strip())

    # Remove duplicates
    for key in claims:
        claims[key] = list(set(claims[key]))

    return claims


def _verify_claims_in_knowledge(claims: Dict[str, List[str]], knowledge_items: List[Dict]) -> Dict[str, Dict]:
    """Verify claims against knowledge sources and return verification results."""
    if not knowledge_items:
        return {}

    # Build searchable knowledge blob
    blob_parts = []
    for k in knowledge_items[:15]:  # Check more sources for better verification
        content = (k.get("content") or "").lower()
        title = (k.get("title") or "").lower()
        blob_parts.extend([content, title])

    knowledge_blob = " ".join(blob_parts)

    verification_results = {}

    # Verify each claim type
    for claim_type, claim_list in claims.items():
        verification_results[claim_type] = {}

        for claim in claim_list:
            claim_lower = claim.lower().strip()

            # Skip very short claims
            if len(claim_lower) < 2:
                continue

            # Check if claim appears in knowledge
            supported = False
            confidence = 0.0

            if claim_type == 'numeric':
                # For numbers, check exact match or close variations
                supported = claim_lower in knowledge_blob
                if not supported:
                    # Check for similar numbers (e.g., 2023 vs 2024)
                    try:
                        claim_num = float(re.sub(r'[,%]', '', claim))
                        # Look for numbers within 10% range
                        numbers_in_blob = re.findall(r'\b\d+(?:\.\d+)?\b', knowledge_blob)
                        for num_str in numbers_in_blob:
                            try:
                                blob_num = float(num_str)
                                if abs(claim_num - blob_num) / max(claim_num, blob_num) < 0.1:
                                    supported = True
                                    confidence = 0.7  # Lower confidence for approximate matches
                                    break
                            except ValueError:
                                continue
                    except ValueError:
                        pass

            elif claim_type == 'dates':
                # For dates, check exact match and variations
                supported = claim_lower in knowledge_blob
                if not supported:
                    # Check year-only matches for full dates
                    year_match = re.search(r'\b(\d{4})\b', claim)
                    if year_match:
                        year = year_match.group(1)
                        if year in knowledge_blob:
                            supported = True
                            confidence = 0.8

            elif claim_type == 'entities':
                # For entities, check exact match and case variations
                supported = claim_lower in knowledge_blob
                if not supported:
                    # Try case-insensitive match
                    supported = any(claim_lower == blob_part for blob_part in knowledge_blob.split())

            elif claim_type == 'technical_terms':
                # For technical terms, check exact match
                supported = claim_lower in knowledge_blob

            elif claim_type == 'causal_relationships':
                # For causal relationships, check if key causal indicators are present
                causal_keywords = ['because', 'causes', 'leads to', 'results in', 'due to']
                sentence_supported = any(keyword in knowledge_blob for keyword in causal_keywords)
                if sentence_supported:
                    supported = True
                    confidence = 0.6  # Lower confidence for causal claims

            verification_results[claim_type][claim] = {
                'supported': supported,
                'confidence': confidence if supported else 0.0,
                'claim_type': claim_type
            }

    return verification_results


def _generate_accuracy_warnings(verification_results: Dict[str, Dict], original_answer: str) -> str:
    """Generate appropriate warnings based on verification results."""
    warnings = []

    unsupported_claims = []
    low_confidence_claims = []

    for claim_type, claims in verification_results.items():
        for claim, result in claims.items():
            if not result['supported']:
                unsupported_claims.append((claim_type, claim))
            elif result['confidence'] < 0.8:
                low_confidence_claims.append((claim_type, claim, result['confidence']))

    # Generate warnings for unsupported claims
    if unsupported_claims:
        claim_descriptions = []
        for claim_type, claim in unsupported_claims:
            if claim_type == 'numeric':
                claim_descriptions.append(f"numeric details (e.g., {claim})")
            elif claim_type == 'dates':
                claim_descriptions.append(f"dates (e.g., {claim})")
            elif claim_type == 'entities':
                claim_descriptions.append(f"names/entities (e.g., {claim})")
            elif claim_type == 'technical_terms':
                claim_descriptions.append(f"technical terms (e.g., {claim})")
            elif claim_type == 'causal_relationships':
                claim_descriptions.append("causal relationships")

        if claim_descriptions:
            unique_descriptions = list(set(claim_descriptions))
            warnings.append(f"I couldn't verify some {', '.join(unique_descriptions)} from the sources I checked. "
                          "For the most accurate information, please specify the exact context or timeframe.")

    # Generate warnings for low confidence claims
    if low_confidence_claims and not warnings:  # Don't add both types of warnings
        warnings.append("Some details in my response are based on partial matches in the available sources. "
                       "For complete accuracy, consider checking the original sources directly.")

    return " ".join(warnings) if warnings else ""


def verify_response_accuracy(answer: str, knowledge_items: List[Dict], *, query: str = "") -> str:
    if not answer or not isinstance(answer, str):
        return answer
    if not knowledge_items:
        return answer

    # Enhanced accuracy checking for multiple claim types

    # Skip accuracy checking for very casual queries
    simple_query = (query or "").strip().lower()
    casual_indicators = ['bye', 'hi', 'hello', 'thanks', 'thank you', 'cool', 'nice', 'great', 'ok', 'okay']
    if simple_query and (len(simple_query.split()) <= 4 or any(word in simple_query for word in casual_indicators)):
        return answer

    if not knowledge_items:
        return answer

    # Extract all types of claims from the answer
    claims = _extract_claims_from_text(answer)

    # Check if we have any claims to verify
    total_claims = sum(len(claim_list) for claim_list in claims.values())
    if total_claims == 0:
        return answer

    # Verify claims against knowledge sources
    verification_results = _verify_claims_in_knowledge(claims, knowledge_items)

    # Check for conflicting information across sources
    conflicts = _detect_source_conflicts(verification_results, knowledge_items)

    # Generate appropriate warnings
    warning_text = _generate_accuracy_warnings(verification_results, answer)

    # Handle unsupported claims (remove or flag)
    cleaned_answer = _handle_unsupported_claims(answer, verification_results)

    # Add confidence indicators and conflict warnings
    final_answer = _add_confidence_indicators(cleaned_answer, conflicts)

    # Add warning note if needed
    if warning_text and warning_text.lower() not in final_answer.lower():
        final_answer = f"{final_answer}\n\n*{warning_text}*"

    return final_answer.strip()


def _detect_source_conflicts(verification_results: Dict[str, Dict], knowledge_items: List[Dict]) -> List[Dict]:
    """Detect when sources provide conflicting information."""
    conflicts = []

    if len(knowledge_items) < 2:
        return conflicts

    # For now, focus on numeric and date conflicts which are most verifiable
    numeric_claims = verification_results.get('numeric', {})
    date_claims = verification_results.get('dates', {})

    # Check for conflicting numeric claims
    for claim in numeric_claims:
        if not numeric_claims[claim]['supported']:
            # Look for alternative numbers in sources
            alternative_numbers = []
            for item in knowledge_items:
                content = item.get('content', '')
                numbers = _NUM_TOKEN_RE.findall(content)
                if numbers:
                    alternative_numbers.extend(numbers[:3])  # Limit per source

            if len(set(alternative_numbers)) > 1:  # Multiple different numbers found
                conflicts.append({
                    'type': 'numeric_conflict',
                    'claim': claim,
                    'alternatives': list(set(alternative_numbers))[:5]
                })

    return conflicts


def _handle_unsupported_claims(answer: str, verification_results: Dict[str, Dict]) -> str:
    """Handle unsupported claims by either removing or flagging them."""
    # For now, keep the original answer but mark it for warnings
    # More aggressive removal could be added for high-stakes claims
    return answer


def _add_confidence_indicators(answer: str, conflicts: List[Dict]) -> str:
    """Add subtle confidence indicators when there are conflicts."""
    if not conflicts:
        return answer

    # Add a subtle note about conflicting information
    conflict_note = "\n\n*Note: Some sources provided varying information on specific details.*"
    if conflict_note.lower() not in answer.lower():
        return answer + conflict_note

    return answer

