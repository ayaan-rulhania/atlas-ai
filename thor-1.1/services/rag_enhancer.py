"""
RAG (Retrieval-Augmented Generation) Enhancer Service.
Provides semantic retrieval, hybrid search, and contextual reranking for improved knowledge integration.
"""
import os
import json
import torch
import numpy as np
from typing import List, Dict, Optional, Tuple, Any
from pathlib import Path
import logging
from collections import defaultdict
import re
from typing import TYPE_CHECKING

# region agent log
def _agent_log(message: str, data: dict, *, hypothesis_id: str, run_id: str = "pre-fix") -> None:
    # NDJSON debug log: keep tiny; do not log secrets/PII.
    try:
        import json as _json
        import os as _os
        import sys as _sys
        from time import time as _time
        payload = {
            "sessionId": "debug-session",
            "runId": run_id,
            "hypothesisId": hypothesis_id,
            "location": "thor-1.1/services/rag_enhancer.py:agent_log",
            "message": message,
            "data": {
                **data,
                "cwd": _os.getcwd(),
                "sys_path_head": _sys.path[:8],
            },
            "timestamp": int(_time() * 1000),
        }
        _atlas_root = __file__
        for _ in range(3):
            _atlas_root = _os.path.dirname(_atlas_root)
        with open(_os.path.join(_atlas_root, ".cursor", "debug.log"), "a", encoding="utf-8") as _f:
            _f.write(_json.dumps(payload, ensure_ascii=False) + "\n")
    except Exception:
        pass
# endregion agent log

if TYPE_CHECKING:  # pragma: no cover
    from brain.connector import BrainConnector  # noqa: F401

_agent_log(
    "module imported",
    {"note": "rag_enhancer loaded (TYPE_CHECKING only for BrainConnector)"},
    hypothesis_id="F",
)

logger = logging.getLogger(__name__)

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logger.warning("sentence-transformers not available. Install with: pip install sentence-transformers")

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    logger.warning("faiss not available. Install with: pip install faiss-cpu")


class SemanticRetriever:
    """
    Handles semantic similarity search using embeddings.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2", cache_dir: str = "cache/embeddings"):
        self.model_name = model_name
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        if SENTENCE_TRANSFORMERS_AVAILABLE:
            self.encoder = SentenceTransformer(model_name)
            self.embedding_dim = self.encoder.get_sentence_embedding_dimension()
        else:
            self.encoder = None
            self.embedding_dim = 384  # Default dimension

        self.index = None
        self.knowledge_base = []
        self.id_to_knowledge = {}

    def encode_text(self, text: str) -> np.ndarray:
        """Encode text to embedding vector."""
        if self.encoder:
            return self.encoder.encode(text, convert_to_numpy=True)
        else:
            # Fallback: simple hash-based encoding (not semantic)
            import hashlib
            hash_obj = hashlib.md5(text.encode())
            hash_bytes = hash_obj.digest()
            # Convert to float array and normalize
            embedding = np.frombuffer(hash_bytes, dtype=np.uint8).astype(np.float32)
            embedding = embedding / np.linalg.norm(embedding)
            return embedding[:self.embedding_dim]

    def build_index(self, knowledge_items: List[Dict]) -> None:
        """
        Build FAISS index from knowledge items.

        Args:
            knowledge_items: List of knowledge dictionaries with 'content' field
        """
        if not FAISS_AVAILABLE:
            logger.warning("FAISS not available, skipping index building")
            return

        self.knowledge_base = knowledge_items

        # Encode all knowledge items
        embeddings = []
        valid_items = []

        for i, item in enumerate(knowledge_items):
            content = item.get('content', '').strip()
            if content and len(content) > 10:  # Filter out very short content
                embedding = self.encode_text(content)
                embeddings.append(embedding)
                self.id_to_knowledge[i] = item
                valid_items.append(item)

        if embeddings:
            embeddings = np.array(embeddings, dtype=np.float32)

            # Create FAISS index
            if self.embedding_dim > 0:
                self.index = faiss.IndexFlatIP(self.embedding_dim)  # Inner product (cosine similarity)
                # Normalize embeddings for cosine similarity
                faiss.normalize_L2(embeddings)
                self.index.add(embeddings)

            logger.info(f"Built FAISS index with {len(valid_items)} knowledge items")

    def semantic_search(self, query: str, top_k: int = 5) -> List[Tuple[Dict, float]]:
        """
        Perform semantic search for the query.

        Args:
            query: Search query
            top_k: Number of results to return

        Returns:
            List of (knowledge_item, similarity_score) tuples
        """
        if not self.index or not FAISS_AVAILABLE:
            return []

        # Encode query
        query_embedding = self.encode_text(query).reshape(1, -1).astype(np.float32)
        faiss.normalize_L2(query_embedding)

        # Search
        scores, indices = self.index.search(query_embedding, min(top_k, self.index.ntotal))

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(self.knowledge_base) and score > 0:
                knowledge_item = self.id_to_knowledge.get(idx)
                if knowledge_item:
                    results.append((knowledge_item, float(score)))

        return results


class HybridRetriever:
    """
    Combines keyword-based and semantic search for better retrieval.
    """

    def __init__(self, brain_connector: Optional["BrainConnector"], semantic_retriever: SemanticRetriever):
        self.brain_connector = brain_connector
        self.semantic_retriever = semantic_retriever

    def hybrid_search(
        self,
        query: str,
        top_k: int = 5,
        keyword_weight: float = 0.4,
        semantic_weight: float = 0.6
    ) -> List[Tuple[Dict, float]]:
        """
        Perform hybrid search combining keyword and semantic retrieval.

        Args:
            query: Search query
            top_k: Number of results to return
            keyword_weight: Weight for keyword-based results
            semantic_weight: Weight for semantic results

        Returns:
            List of (knowledge_item, combined_score) tuples
        """
        # Get keyword-based results
        keyword_results = self.brain_connector.get_relevant_knowledge(query) if self.brain_connector else []

        # Get semantic results
        semantic_results = self.semantic_retriever.semantic_search(query, top_k * 2)

        # Combine results with scoring
        combined_scores = defaultdict(float)
        all_items = {}

        # Process keyword results
        for item in keyword_results:
            item_id = id(item)
            combined_scores[item_id] += keyword_weight
            all_items[item_id] = item

        # Process semantic results
        for item, semantic_score in semantic_results:
            item_id = id(item)
            combined_scores[item_id] += semantic_weight * semantic_score
            all_items[item_id] = item

        # Sort by combined score
        sorted_results = sorted(
            [(all_items[item_id], score) for item_id, score in combined_scores.items()],
            key=lambda x: x[1],
            reverse=True
        )

        return sorted_results[:top_k]


class ContextualReranker:
    """
    Reranks retrieved knowledge based on query context and relevance.
    """

    def __init__(self):
        self.query_patterns = {
            'technical': ['code', 'programming', 'algorithm', 'function', 'api', 'software'],
            'scientific': ['research', 'study', 'experiment', 'theory', 'evidence', 'data'],
            'general': ['what', 'how', 'why', 'when', 'where', 'who']
        }

    def rerank_by_context(
        self,
        query: str,
        candidates: List[Tuple[Dict, float]],
        top_k: int = 5
    ) -> List[Tuple[Dict, float]]:
        """
        Rerank candidates based on query context.

        Args:
            query: Original query
            candidates: List of (item, score) tuples
            top_k: Number of top results to return

        Returns:
            Reranked list of (item, score) tuples
        """
        query_lower = query.lower()

        # Determine query type
        query_type = self._classify_query(query_lower)

        reranked = []
        for item, base_score in candidates:
            content = item.get('content', '').lower()
            title = item.get('title', '').lower()
            source = item.get('source', '')

            # Context-aware scoring
            context_score = self._calculate_context_score(query_type, content, title, source, query_lower)
            final_score = base_score * (1 + context_score)

            reranked.append((item, final_score))

        # Sort by final score
        reranked.sort(key=lambda x: x[1], reverse=True)

        return reranked[:top_k]

    def _classify_query(self, query: str) -> str:
        """Classify query type for context-aware reranking."""
        for query_type, patterns in self.query_patterns.items():
            if any(pattern in query for pattern in patterns):
                return query_type
        return 'general'

    def _calculate_context_score(self, query_type: str, content: str, title: str, source: str, query: str) -> float:
        """Calculate context-aware relevance score."""
        score = 0.0

        # Query type specific scoring
        if query_type == 'technical':
            if source in ['structured', 'wikipedia'] and any(term in content for term in ['code', 'function', 'api']):
                score += 0.3
            if 'programming' in content or 'algorithm' in content:
                score += 0.2

        elif query_type == 'scientific':
            if source in ['wikipedia', 'structured'] and any(term in content for term in ['research', 'study', 'evidence']):
                score += 0.3
            if 'theory' in content or 'experiment' in content:
                score += 0.2

        # Source reliability scoring
        source_scores = {
            'wikipedia': 0.2,
            'structured': 0.15,
            'duckduckgo': 0.1,
            'research_engine': 0.05
        }
        score += source_scores.get(source, 0.0)

        # Content length appropriateness
        content_length = len(content.split())
        if 20 <= content_length <= 200:  # Prefer medium-length content
            score += 0.1

        # Exact keyword matches
        query_words = set(query.split())
        content_words = set(content.split())
        overlap = len(query_words.intersection(content_words))
        if overlap > 0:
            score += min(overlap * 0.1, 0.3)  # Cap at 0.3

        return score


class MultiHopRetriever:
    """
    Performs iterative retrieval to gather comprehensive information.
    """

    def __init__(self, hybrid_retriever: HybridRetriever, max_hops: int = 3):
        self.hybrid_retriever = hybrid_retriever
        self.max_hops = max_hops

    def multi_hop_search(
        self,
        initial_query: str,
        top_k_per_hop: int = 3,
        max_total_results: int = 8
    ) -> List[Tuple[Dict, float]]:
        """
        Perform multi-hop retrieval starting from initial query.

        Args:
            initial_query: Initial search query
            top_k_per_hop: Results per hop
            max_total_results: Maximum total results to return

        Returns:
            List of (knowledge_item, score) tuples from multi-hop search
        """
        all_results = []
        seen_items = set()
        current_queries = [initial_query]

        for hop in range(self.max_hops):
            if not current_queries:
                break

            hop_results = []

            for query in current_queries:
                # Search with current query
                results = self.hybrid_retriever.hybrid_search(query, top_k=top_k_per_hop)

                for item, score in results:
                    item_id = id(item)
                    if item_id not in seen_items:
                        hop_results.append((item, score))
                        seen_items.add(item_id)

            if not hop_results:
                break

            all_results.extend(hop_results)

            # Generate follow-up queries from top results
            if hop < self.max_hops - 1:
                current_queries = self._generate_followup_queries(
                    [item for item, _ in hop_results[:2]],  # Use top 2 for follow-ups
                    initial_query
                )

        # Sort all results by score and limit
        all_results.sort(key=lambda x: x[1], reverse=True)
        return all_results[:max_total_results]

    def _generate_followup_queries(self, top_items: List[Dict], original_query: str) -> List[str]:
        """Generate follow-up queries based on retrieved content."""
        followup_queries = []

        for item in top_items:
            content = item.get('content', '')

            # Extract key concepts or related terms
            # Simple approach: extract noun phrases or key terms
            words = re.findall(r'\b\w+\b', content.lower())
            key_terms = [word for word in words if len(word) > 4 and word not in ['which', 'their', 'there', 'these', 'those', 'that', 'this', 'with', 'from', 'they', 'what', 'when', 'where', 'how', 'why']]

            if key_terms:
                # Create a related query using key terms
                related_terms = list(set(key_terms[:3]))  # Unique terms, max 3
                if len(related_terms) >= 2:
                    followup_query = f"{' '.join(related_terms)} {original_query.split()[0]}"  # Combine with first word of original
                    followup_queries.append(followup_query)

        return followup_queries[:2]  # Max 2 follow-up queries


class RAGEnhancer:
    """
    Main RAG enhancement service that combines all retrieval components.
    """

    def __init__(self, brain_dir: str = "brain"):
        # IMPORTANT: Do not instantiate BrainConnector here (it depends on RAGEnhancer),
        # or we create an import/runtime cycle. Keyword retrieval will be skipped if no connector is provided.
        self.brain_dir = brain_dir
        self.brain_connector = None
        self.semantic_retriever = SemanticRetriever()
        self.hybrid_retriever = HybridRetriever(self.brain_connector, self.semantic_retriever)
        self.contextual_reranker = ContextualReranker()
        self.multi_hop_retriever = MultiHopRetriever(self.hybrid_retriever)

        # Initialize knowledge base
        self._load_knowledge_base()

    def _load_knowledge_base(self):
        """Load and index knowledge base."""
        knowledge_items = []

        # Load from brain structure
        brain_path = Path(self.brain_dir)
        if brain_path.exists():
            for letter_dir in brain_path.iterdir():
                if letter_dir.is_dir():
                    keywords_file = letter_dir / "keywords.json"
                    if keywords_file.exists():
                        try:
                            with open(keywords_file, 'r') as f:
                                data = json.load(f)
                                knowledge_items.extend(data.get('knowledge', []))
                        except Exception as e:
                            logger.warning(f"Error loading {keywords_file}: {e}")

        # Build semantic index
        if knowledge_items:
            self.semantic_retriever.build_index(knowledge_items)
            logger.info(f"Loaded {len(knowledge_items)} knowledge items into RAG system")

    def retrieve_enhanced(
        self,
        query: str,
        retrieval_method: str = "hybrid",
        top_k: int = 5,
        use_reranking: bool = True,
        use_multi_hop: bool = False
    ) -> List[Tuple[Dict, float]]:
        """
        Enhanced retrieval with multiple strategies.

        Args:
            query: Search query
            retrieval_method: "keyword", "semantic", "hybrid"
            top_k: Number of results to return
            use_reranking: Whether to use contextual reranking
            use_multi_hop: Whether to use multi-hop retrieval

        Returns:
            List of (knowledge_item, score) tuples
        """
        if use_multi_hop:
            results = self.multi_hop_retriever.multi_hop_search(query, max_total_results=top_k)
        else:
            if retrieval_method == "keyword":
                if not self.brain_connector:
                    return []
                results = [(item, 1.0) for item in self.brain_connector.get_relevant_knowledge(query)[:top_k]]
            elif retrieval_method == "semantic":
                results = self.semantic_retriever.semantic_search(query, top_k)
            else:  # hybrid
                results = self.hybrid_retriever.hybrid_search(query, top_k)

        # Apply reranking if requested
        if use_reranking and results:
            results = self.contextual_reranker.rerank_by_context(query, results, top_k)

        return results

    def generate_rag_context(
        self,
        query: str,
        max_context_length: int = 1000,
        **retrieval_kwargs
    ) -> str:
        """
        Generate RAG context for a query.

        Args:
            query: The query to generate context for
            max_context_length: Maximum context length in characters
            **retrieval_kwargs: Arguments for retrieval

        Returns:
            Formatted context string
        """
        results = self.retrieve_enhanced(query, **retrieval_kwargs)

        if not results:
            return ""

        # Format context
        context_parts = []
        total_length = 0

        for item, score in results:
            content = item.get('content', '').strip()
            title = item.get('title', '')
            source = item.get('source', '')

            if content and len(content) > 20:  # Filter very short content
                # Create context snippet
                snippet = f"[{source.upper()}] {title}: {content[:300]}..."

                if total_length + len(snippet) <= max_context_length:
                    context_parts.append(snippet)
                    total_length += len(snippet)
                else:
                    break

        return "\n\n".join(context_parts)

    def enhance_response_with_rag(
        self,
        query: str,
        base_response: str,
        **retrieval_kwargs
    ) -> str:
        """
        Enhance a response with RAG context.

        Args:
            query: Original query
            base_response: Base model response
            **retrieval_kwargs: Retrieval arguments

        Returns:
            Enhanced response with RAG context
        """
        context = self.generate_rag_context(query, **retrieval_kwargs)

        if context:
            enhanced_response = f"{base_response}\n\nBased on relevant knowledge:\n{context}"
            return enhanced_response

        return base_response


# Global instance
_rag_enhancer = None


def get_rag_enhancer(brain_dir: str = "brain") -> RAGEnhancer:
    """Get or create the global RAG enhancer instance."""
    global _rag_enhancer
    if _rag_enhancer is None:
        _rag_enhancer = RAGEnhancer(brain_dir)
    return _rag_enhancer
