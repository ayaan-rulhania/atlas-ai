"""
Minimal semantic relevance scorer: keyword overlap and simple scoring.
Provides get_semantic_scorer() for use by knowledge_reranker and app.
"""
from typing import Dict, List, Any, Optional


class _SemanticScorer:
    """Simple scorer: keyword overlap between query and item content."""

    def calculate_semantic_score(
        self,
        query: str,
        item: Dict[str, Any],
        query_intent: Optional[Dict[str, Any]] = None,
    ) -> float:
        if not query:
            return 0.0
        text = (
            (item.get("content") or "")
            + " "
            + (item.get("title") or "")
            + " "
            + (item.get("query") or "")
        ).lower()
        q = query.lower()
        words = set(q.split())
        if not words:
            return 0.0
        hits = sum(1 for w in words if w in text)
        return hits / len(words)

    def filter_knowledge_by_relevance(
        self,
        query: str,
        knowledge: List[Dict[str, Any]],
        query_intent: Optional[Dict[str, Any]] = None,
        min_score: float = 0.0,
    ) -> List[tuple]:
        """Return list of (score, item) sorted by score descending."""
        if not knowledge:
            return []
        scored = [(self.calculate_semantic_score(query, item, query_intent), item) for item in knowledge]
        scored = [(s, item) for s, item in scored if s >= min_score]
        scored.sort(key=lambda x: -x[0])
        return scored


_scorer: Optional[_SemanticScorer] = None


def get_semantic_scorer() -> _SemanticScorer:
    global _scorer
    if _scorer is None:
        _scorer = _SemanticScorer()
    return _scorer
