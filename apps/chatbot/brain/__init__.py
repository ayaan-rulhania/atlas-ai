"""
Brain knowledge connector: loads keyword-indexed knowledge from brain/*/keywords.json
and provides get_relevant_knowledge, enhance_response, and search.
"""
import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional


class BrainConnector:
    """Connects to the brain knowledge base (keywords.json files under brain/)."""

    def __init__(self, brain_dir: Optional[Path] = None):
        self.brain_dir = brain_dir or Path(__file__).parent.resolve()
        self._knowledge: List[Dict[str, Any]] = []
        self._load_all()

    def _load_all(self) -> None:
        """Load all keywords.json from brain/<letter>/ subdirs."""
        self._knowledge = []
        if not self.brain_dir.is_dir():
            return
        for sub in self.brain_dir.iterdir():
            if sub.is_dir():
                kw_file = sub / "keywords.json"
                if kw_file.exists():
                    try:
                        with open(kw_file, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        for item in data.get("knowledge", []):
                            self._knowledge.append({
                                "title": item.get("title", ""),
                                "content": item.get("content", ""),
                                "query": item.get("query", ""),
                                "source": item.get("source", "brain"),
                                "learned_at": item.get("learned_at", ""),
                                "url": item.get("url", ""),
                            })
                    except (json.JSONDecodeError, OSError):
                        pass

    def _score(self, query: str, item: Dict[str, Any]) -> float:
        """Simple relevance score: keyword overlap."""
        q = (query or "").lower()
        text = (
            (item.get("title", "") or "")
            + " "
            + (item.get("content", "") or "")
            + " "
            + (item.get("query", "") or "")
        ).lower()
        if not q:
            return 0.0
        words = set(q.split())
        hits = sum(1 for w in words if w in text)
        return hits / len(words) if words else 0.0

    def get_relevant_knowledge(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Return knowledge items relevant to the query (for context)."""
        if not query or not self._knowledge:
            return []
        scored = [(self._score(query, item), item) for item in self._knowledge]
        scored = [(s, item) for s, item in scored if s > 0]
        scored.sort(key=lambda x: -x[0])
        out = []
        for score, item in scored[:limit]:
            out.append({
                "title": item.get("title", ""),
                "content": item.get("content", ""),
                "source": item.get("source", "brain"),
                "score": score,
                "learned_at": item.get("learned_at", ""),
            })
        return out

    def enhance_response(self, message: str, response: str) -> str:
        """Optionally enhance the response using brain knowledge. Returns response if no enhancement."""
        if not response:
            return response
        knowledge = self.get_relevant_knowledge(message, limit=2)
        if not knowledge:
            return response
        # Minimal enhancement: append a short "Based on..." only if we have a strong match
        best = knowledge[0]
        if best.get("score", 0) >= 0.5 and best.get("content"):
            suffix = f" (Reference: {best.get('title', '')[:50]}.)"
            if suffix not in response and len(response) + len(suffix) < 2000:
                return response + suffix
        return response

    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search brain knowledge; returns items with title, content, source, learned_at, relevance_score."""
        items = self.get_relevant_knowledge(query, limit=limit)
        return [
            {
                "title": k.get("title", ""),
                "content": k.get("content", ""),
                "source": k.get("source", "brain"),
                "learned_at": k.get("learned_at", ""),
                "relevance_score": k.get("score", 0),
            }
            for k in items
        ]
