"""Knowledge reranking utilities to order brain/research hits.

This module is intentionally thorough to provide a robust, layered scoring
strategy. Goals:
- Respect semantic relevance (existing scorer)
- Prefer freshness when available
- Encourage diversity to avoid repeating similar snippets
- Penalize noisy or promotional content
- Support light clustering for relationship/comparison questions
- Surface trace data for observability

All behavior is enabled by default; no toggles are added.
"""

from __future__ import annotations

from typing import Dict, List, Tuple, Optional, Set
from datetime import datetime
import math
import re

from services.semantic_relevance import get_semantic_scorer


def _safe_float(value, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _parse_timestamp(value) -> Optional[datetime]:
    if not value:
        return None
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(value)
        except Exception:
            return None
    if isinstance(value, str):
        for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(value[:26], fmt)
            except Exception:
                continue
    return None


def _recency_boost(timestamp: Optional[datetime], weight: float = 0.1) -> float:
    if not timestamp:
        return 0.0
    delta_days = max((datetime.utcnow() - timestamp).days, 0)
    # Decay: newer items get closer to weight, older trend toward 0
    return weight * math.exp(-delta_days / 90.0)


def _penalize_promotional(text: str) -> float:
    promos = [
        "click here", "subscribe", "buy now", "signup", "sign up", "join now", "limited offer",
        "official website", "discount", "deal", "coupon", "sale",
    ]
    lower = (text or "").lower()
    if any(p in lower for p in promos):
        return -0.2
    return 0.0


def _penalize_low_content(text: str) -> float:
    if not text:
        return -0.2
    words = text.split()
    if len(words) < 6:
        return -0.1
    if len(text) < 24:
        return -0.05
    return 0.0


def _dedup_by_title(items: List[Dict]) -> List[Dict]:
    seen: Set[str] = set()
    deduped = []
    for item in items:
        title = (item.get("title") or "").strip().lower()
        if not title:
            deduped.append(item)
            continue
        if title in seen:
            continue
        seen.add(title)
        deduped.append(item)
    return deduped


def _cluster_by_source(items: List[Dict]) -> Dict[str, List[Dict]]:
    clusters: Dict[str, List[Dict]] = {}
    for item in items:
        src = item.get("source", "unknown")
        clusters.setdefault(src, []).append(item)
    return clusters


def _diversity_sample(items: List[Tuple[float, Dict]], per_source: int = 2, limit: int = 6) -> List[Dict]:
    clusters = _cluster_by_source([itm for _, itm in items])
    selected: List[Dict] = []

    # Enhanced diversity sampling with better source balancing
    # Sort sources by average score to prioritize high-quality sources
    source_scores = {}
    for src, members in clusters.items():
        if members:
            avg_score = sum(score for score, _ in [(s, i) for s, i in items if i in members]) / len(members)
            source_scores[src] = avg_score

    sorted_sources = sorted(source_scores.keys(), key=lambda s: source_scores[s], reverse=True)

    # First pass: take top items from highest-scoring sources
    for src in sorted_sources:
        members = clusters[src]
        # Sort members by score within each source
        members_with_scores = [(score, item) for score, item in items if item in members]
        members_with_scores.sort(key=lambda x: x[0], reverse=True)
        take = [item for _, item in members_with_scores[:per_source]]
        selected.extend(take)
        if len(selected) >= limit:
            return selected[:limit]

    # Second pass: fill remainder from global ranking, ensuring diversity
    remaining_needed = limit - len(selected)
    if remaining_needed > 0:
        used_sources = {item.get('source', 'unknown') for item in selected}
        for score, item in items:
            if item not in selected:
                item_source = item.get('source', 'unknown')
                # Prefer sources not yet represented, but don't exclude good content
                if item_source not in used_sources or len(used_sources) >= 3:
                    selected.append(item)
                    used_sources.add(item_source)
                    remaining_needed -= 1
                    if remaining_needed <= 0:
                        break

    return selected[:limit]


def _relationship_boost(query_intent: Dict) -> bool:
    """Enhanced detection of relationship/comparison queries that benefit from diverse sources."""
    hints = query_intent.get("hints", {}) if query_intent else {}
    if hints.get("prefer_multi_source", False):
        return True

    # Check query content for relationship indicators
    query = query_intent.get("query", "") if query_intent else ""
    query_lower = query.lower()

    relationship_indicators = [
        ' vs ', ' versus ', ' compare ', ' comparison ', ' difference between ',
        ' relationship ', ' connection ', ' how does ', ' how do ', ' similar to ',
        ' unlike ', ' whereas ', ' compared to ', ' in contrast ', ' pros and cons ',
        ' advantages ', ' disadvantages ', ' better than ', ' worse than '
    ]

    return any(indicator in query_lower for indicator in relationship_indicators)


def _extract_title_snippet(item: Dict) -> str:
    title = item.get("title") or ""
    content = item.get("content") or ""
    snippet = content[:120]
    return f"{title} :: {snippet}"


class KnowledgeReranker:
    """Rerank knowledge using semantic relevance plus lightweight recency."""

    def __init__(self):
        self.semantic_scorer = get_semantic_scorer()
        self.base_limit = 6
        self.relationship_limit = 8
        self.min_score = 0.0

    def _score_item(self, query: str, item: Dict, query_intent: Dict) -> float:
        semantic_score = self.semantic_scorer.calculate_semantic_score(query, item, query_intent)
        ts = item.get("timestamp") or item.get("updated_at") or item.get("last_updated")
        recency = _recency_boost(_parse_timestamp(ts), weight=0.08)
        promo_penalty = _penalize_promotional(item.get("content", ""))
        low_content_penalty = _penalize_low_content(item.get("content", ""))

        # Enhanced query-specific boosting
        query_specific_boost = self._calculate_query_specific_boost(query, item, query_intent)

        # Improved temporal relevance for time-sensitive topics
        temporal_boost = self._calculate_temporal_relevance(query, item)

        # Diversity penalty to avoid redundant information
        diversity_penalty = self._calculate_diversity_penalty(item)

        total_score = (semantic_score +
                      recency +
                      query_specific_boost +
                      temporal_boost +
                      promo_penalty +
                      low_content_penalty +
                      diversity_penalty)

        return max(0.0, total_score)

    def _calculate_query_specific_boost(self, query: str, item: Dict, query_intent: Dict) -> float:
        """Calculate boost based on query type and source alignment."""
        boost = 0.0
        query_lower = query.lower()
        content_lower = item.get("content", "").lower()
        source = item.get("source", "").lower()

        # Technical queries: boost sources that typically contain tutorials/code
        if any(word in query_lower for word in ['how to', 'tutorial', 'guide', 'steps', 'install', 'setup']):
            if any(tech_source in source for tech_source in ['wikipedia', 'brain', 'gem_source']):
                boost += 0.15  # Technical sources get boost for how-to questions
            if any(tech_indicator in content_lower for tech_indicator in ['step', 'first', 'then', 'install', 'run']):
                boost += 0.1

        # Comparison queries: boost sources that handle relationships well
        if any(word in query_lower for word in ['vs', 'versus', 'compare', 'comparison', 'difference']):
            if source in ['wikipedia', 'brain']:  # Authoritative sources for comparisons
                boost += 0.12
            if any(comp_word in content_lower for comp_word in ['compared to', 'versus', 'unlike', 'whereas']):
                boost += 0.08

        # Recent events/news: boost recent content more aggressively
        if any(word in query_lower for word in ['latest', 'recent', 'new', 'update', '2024', '2025']):
            # Already handled by temporal boost, but add small additional boost for news sources
            if source in ['google', 'duckduckgo', 'bing']:
                boost += 0.05

        # Factual queries: boost authoritative sources
        intent = query_intent.get('intent', '') if query_intent else ''
        if intent in ['factual', 'definition', 'biographical']:
            if source == 'wikipedia':
                boost += 0.1
            elif source == 'brain':
                boost += 0.08

        return boost

    def _calculate_temporal_relevance(self, query: str, item: Dict) -> float:
        """Enhanced temporal relevance based on query content."""
        query_lower = query.lower()
        ts = item.get("timestamp") or item.get("updated_at") or item.get("last_updated")
        timestamp = _parse_timestamp(ts)

        if not timestamp:
            return 0.0

        base_recency = _recency_boost(timestamp, weight=0.08)

        # Time-sensitive topics get stronger recency boost
        time_sensitive_keywords = [
            'latest', 'recent', 'new', 'update', 'breaking', 'today', 'yesterday',
            '2024', '2025', 'current', 'now', 'modern', 'contemporary'
        ]

        if any(keyword in query_lower for keyword in time_sensitive_keywords):
            # Double the recency weight for time-sensitive queries
            enhanced_recency = _recency_boost(timestamp, weight=0.16)
            return enhanced_recency - base_recency  # Return the additional boost

        # Technology/news topics: moderate boost for recent content
        tech_news_keywords = [
            'technology', 'tech', 'ai', 'artificial intelligence', 'software',
            'update', 'release', 'version', 'news', 'announcement'
        ]

        if any(keyword in query_lower for keyword in tech_news_keywords):
            enhanced_recency = _recency_boost(timestamp, weight=0.12)
            return enhanced_recency - base_recency

        return 0.0  # No additional boost for non-time-sensitive queries

    def _calculate_diversity_penalty(self, item: Dict) -> float:
        """Calculate penalty to encourage source diversity."""
        # This will be used during the final diversity pass, but we can add
        # a small penalty for sources that tend to be very similar
        source = item.get("source", "").lower()

        # Slight penalty for sources that often have similar content
        if source in ['bing', 'google'] and 'duck' not in source:
            return -0.02  # Small penalty to prefer more diverse sources

        return 0.0

    def _score_all(self, query: str, knowledge_items: List[Dict], query_intent: Dict) -> List[Tuple[float, Dict]]:
        scored: List[Tuple[float, Dict]] = []
        for item in knowledge_items:
            score = self._score_item(query, item, query_intent)
            scored.append((score, item))
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return scored

    def _apply_diversity(self, scored: List[Tuple[float, Dict]], query_intent: Dict, limit: int) -> List[Dict]:
        if _relationship_boost(query_intent):
            return _diversity_sample(scored, per_source=2, limit=limit)
        return [itm for _, itm in scored[:limit]]

    def _trace(self, scored: List[Tuple[float, Dict]]) -> List[str]:
        traces = []
        for score, item in scored:
            traces.append(f"{score:.3f} | {item.get('source', 'unknown')} | {item.get('title', '')[:60]}")
        return traces

    def rerank(
        self,
        query: str,
        knowledge_items: List[Dict],
        query_intent: Dict,
        limit: Optional[int] = None,
    ) -> List[Dict]:
        if not knowledge_items:
            return []

        effective_limit = limit or (self.relationship_limit if _relationship_boost(query_intent) else self.base_limit)

        # Deduplicate by title to reduce noise
        knowledge_items = _dedup_by_title(knowledge_items)

        scored = self._score_all(query, knowledge_items, query_intent)
        filtered = [(s, i) for s, i in scored if s > self.min_score]

        # Keep a trace for debugging (printed at debug level only)
        trace = self._trace(filtered[:effective_limit * 2])
        if trace:
            print("[Refinement:Reranker] candidates:", "; ".join(trace))

        reranked = self._apply_diversity(filtered, query_intent, effective_limit)
        return reranked


_knowledge_reranker: KnowledgeReranker = None


def get_knowledge_reranker() -> KnowledgeReranker:
    global _knowledge_reranker
    if _knowledge_reranker is None:
        _knowledge_reranker = KnowledgeReranker()
    return _knowledge_reranker


# -----------------------------
# Extended diagnostics and helpers
# -----------------------------

def explain_scores(query: str, knowledge_items: List[Dict], query_intent: Dict) -> List[Dict]:
    """Return detailed scoring breakdowns for observability and debugging."""
    reranker = get_knowledge_reranker()
    detailed = []
    for item in knowledge_items:
        semantic = reranker.semantic_scorer.calculate_semantic_score(query, item, query_intent)
        ts_val = item.get("timestamp") or item.get("updated_at") or item.get("last_updated")
        ts = _parse_timestamp(ts_val)
        recency = _recency_boost(ts, weight=0.08)
        promo = _penalize_promotional(item.get("content", ""))
        lowc = _penalize_low_content(item.get("content", ""))
        total = max(0.0, semantic + recency + promo + lowc)
        detailed.append({
            "title": item.get("title"),
            "source": item.get("source", "unknown"),
            "semantic": semantic,
            "recency": recency,
            "promo_penalty": promo,
            "low_content_penalty": lowc,
            "total": total,
            "timestamp_raw": ts_val,
        })
    detailed.sort(key=lambda x: x["total"], reverse=True)
    return detailed


def select_for_relationship(query: str, knowledge_items: List[Dict], query_intent: Dict) -> List[Dict]:
    """Surface a balanced, source-diverse set tailored to comparison questions."""
    reranker = get_knowledge_reranker()
    scored = reranker._score_all(query, knowledge_items, query_intent)
    diversified = _diversity_sample(scored, per_source=2, limit=reranker.relationship_limit)
    return diversified


def prune_noise(knowledge_items: List[Dict]) -> List[Dict]:
    """Remove clearly noisy entries before scoring."""
    cleaned = []
    for item in knowledge_items:
        content = item.get("content", "")
        if not content or len(content.strip()) < 8:
            continue
        if "lorem ipsum" in content.lower():
            continue
        cleaned.append(item)
    return cleaned


def soft_merge(primary: List[Dict], secondary: List[Dict], max_items: int = 10) -> List[Dict]:
    """Merge two knowledge lists with preference for primary."""
    merged: List[Dict] = []
    seen: Set[str] = set()

    def add_items(items: List[Dict]):
        for it in items:
            key = (it.get("title") or "") + "::" + (it.get("content") or "")[:40]
            if key in seen:
                continue
            seen.add(key)
            merged.append(it)
            if len(merged) >= max_items:
                return

    add_items(primary)
    if len(merged) < max_items:
        add_items(secondary)
    return merged[:max_items]


def summarize_trace(trace: List[str]) -> str:
    """Join trace lines for logging."""
    return "; ".join(trace)


def has_high_confidence(scores: List[Tuple[float, Dict]], threshold: float = 0.65) -> bool:
    return bool(scores and scores[0][0] >= threshold)


def boost_by_source(scores: List[Tuple[float, Dict]], source: str, bonus: float = 0.05) -> List[Tuple[float, Dict]]:
    boosted = []
    for score, item in scores:
        if item.get("source") == source:
            boosted.append((min(1.0, score + bonus), item))
        else:
            boosted.append((score, item))
    boosted.sort(key=lambda s: s[0], reverse=True)
    return boosted


def filter_by_length(items: List[Dict], min_chars: int = 40) -> List[Dict]:
    return [it for it in items if len(it.get("content", "")) >= min_chars]


def detect_overlap(item_a: Dict, item_b: Dict) -> float:
    """Rough token overlap to penalize near-duplicates."""
    content_a = (item_a.get("content") or "").lower().split()
    content_b = (item_b.get("content") or "").lower().split()
    if not content_a or not content_b:
        return 0.0
    set_a, set_b = set(content_a), set(content_b)
    inter = len(set_a & set_b)
    denom = max(len(set_a), len(set_b), 1)
    return inter / denom


def enforce_diversity(items: List[Dict], max_overlap: float = 0.6, limit: int = 6) -> List[Dict]:
    selected: List[Dict] = []
    for item in items:
        if len(selected) >= limit:
            break
        if all(detect_overlap(item, s) < max_overlap for s in selected):
            selected.append(item)
    return selected


def rerank_with_diversity(query: str, knowledge_items: List[Dict], query_intent: Dict, limit: int = 6) -> List[Dict]:
    """Convenience wrapper that reranks then enforces diversity."""
    reranker = get_knowledge_reranker()
    scored = reranker._score_all(query, knowledge_items, query_intent)
    ordered = [itm for _, itm in scored]
    diverse = enforce_diversity(ordered, limit=limit)
    return diverse


# Quality tags for future tracing or analytics
QUALITY_FLAGS = [
    "short_content",
    "promotional",
    "fresh",
    "stale",
    "high_semantic_match",
    "low_semantic_match",
    "diverse_source",
    "duplicate_title",
]


def flag_item(item: Dict) -> List[str]:
    flags: List[str] = []
    content = item.get("content", "")
    if len(content) < 40:
        flags.append("short_content")
    if _penalize_promotional(content) < 0:
        flags.append("promotional")
    ts = item.get("timestamp") or item.get("updated_at") or item.get("last_updated")
    if _parse_timestamp(ts):
        flags.append("fresh")
    return flags


def annotate_items_with_flags(items: List[Dict]) -> List[Dict]:
    annotated = []
    for item in items:
        copy = dict(item)
        copy["flags"] = flag_item(item)
        annotated.append(copy)
    return annotated


RERANKER_GUIDELINES = [
    "Semantic score is primary; bonuses should be small.",
    "Recency bonus should not dominate relevance.",
    "Penalize promotional or very short content even if semantically close.",
    "Diversity matters for comparison/relationship questions.",
    "Deduplicate by title to reduce redundant snippets.",
    "Keep traces concise to avoid log bloat.",
    "Fail open: if scoring fails, return original list.",
    "Limit list length to keep downstream synthesis efficient.",
    "Prefer deterministic ordering when scores tie.",
    "Avoid external dependencies beyond semantic scorer.",
]


def reranker_guidelines_text() -> str:
    return "\n".join(f"- {g}" for g in RERANKER_GUIDELINES)


RERANKER_TEST_CASES = [
    {"query": "difference between tcp and udp", "expect": "diversity + high semantic"},
    {"query": "who is ada lovelace", "expect": "fresh + identity match"},
    {"query": "recipe for pasta", "expect": "penalize promotional, prefer fresh"},
    {"query": "what is life", "expect": "strict match, avoid unrelated brain entries"},
    {"query": "fix typeerror in react", "expect": "troubleshooting items scored higher if relevant"},
    {"query": "compare s3 and gcs pricing", "expect": "multi-source and recency bonus"},
    {"query": "how to center a div", "expect": "semantic strong match, short content allowed if clear"},
    {"query": "explain oauth2", "expect": "semantic + not promotional"},
    {"query": "pytorch tensor broadcasting", "expect": "prefer content with keywords early"},
    {"query": "graphql vs rest", "expect": "diversity across sources"},
]


def reranker_test_cases_text() -> str:
    lines = []
    for case in RERANKER_TEST_CASES:
        lines.append(f"- {case['query']} -> {case['expect']}")
    return "\n".join(lines)


LONG_NOTES = """
Reranker notes:
- Semantic score should dominate ordering.
- Recency bonus is additive and decays with time.
- Promotional content penalty should suppress low-signal marketing text.
- Low-content penalty discourages extremely short snippets.
- Deduplication is by title; consider hashing content if needed later.
- Diversity sampling clusters by source and caps per source.
- Relationship questions increase limit to allow multiple perspectives.
- Traces should remain short to avoid log bloat.
- Filters must fail open; if scoring fails, return originals.
- Keep scoring functions pure and deterministic.
- Avoid external dependencies to keep startup fast.
- Keep scoring weights documented for future tuning.
- Ensure stable sorting for equal scores.
- Avoid leaking sensitive content in traces.
- Support items without titles by allowing them through.
- Maintain compatibility with both brain and research schemas.
- Keep limit values conservative to avoid long synthesis.
- Keep helper functions reusable for diagnostics.
- Avoid expensive operations (no embeddings or network calls here).
- Keep constants grouped for easy adjustment.
- Prefer simplicity; this layer should be fast.
"""


def long_notes_text() -> str:
    return LONG_NOTES.strip()

