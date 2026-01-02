"""
Brain Connector - Connects Thor's responses to the brain keyword system
Enhanced with confidence scoring, knowledge filtering, RAG integration, and SQLite database
"""
import os
import json
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta
from services.query_intent_analyzer import get_query_intent_analyzer
from services.semantic_relevance import get_semantic_scorer
from services.rag_enhancer import get_rag_enhancer

# Try to import SQLite knowledge database
try:
    from services.knowledge_db import get_knowledge_db, KnowledgeDatabase
    SQLITE_AVAILABLE = True
except ImportError:
    SQLITE_AVAILABLE = False


class BrainConnector:
    """Connects AI responses to brain keyword knowledge with enhanced filtering and scoring"""

    def __init__(self, brain_dir="brain", use_sqlite: bool = True):
        self.brain_dir = brain_dir
        self.rag_enhancer = get_rag_enhancer(brain_dir)
        
        # Initialize SQLite database if available
        self.knowledge_db = None
        self.use_sqlite = use_sqlite and SQLITE_AVAILABLE
        if self.use_sqlite:
            try:
                self.knowledge_db = get_knowledge_db()
                print("[BrainConnector] SQLite knowledge database connected")
            except Exception as e:
                print(f"[BrainConnector] SQLite not available: {e}")
                self.use_sqlite = False

        # Confidence scoring parameters
        self.confidence_weights = {
            'source_reliability': 0.3,
            'content_quality': 0.25,
            'temporal_relevance': 0.2,
            'semantic_similarity': 0.15,
            'keyword_overlap': 0.1
        }

        # Quality filters
        self.min_content_length = 20
        self.max_content_age_days = 365 * 2  # 2 years
        self.low_quality_sources = ['greetings_handler', 'test']
        self.low_quality_patterns = [
            'response pattern for',
            'use appropriate',
            'this is a test',
            'placeholder content'
        ]
    
    def get_relevant_knowledge(self, message):
        """Get relevant knowledge from brain based on message keywords.
        Queries both SQLite database and legacy JSON brain structure.
        """
        # Use query intent analyzer for better understanding
        intent_analyzer = get_query_intent_analyzer()
        query_intent = intent_analyzer.analyze(message)
        
        # For philosophical queries like "what's life", force web search
        if query_intent.get('should_search_web') or query_intent.get('intent') == 'philosophical':
            # Return empty to force web search
            return []
        
        # Try SQLite database first (primary source)
        sqlite_knowledge = []
        if self.use_sqlite and self.knowledge_db:
            try:
                sqlite_knowledge = self._get_knowledge_from_sqlite(message, query_intent)
                if sqlite_knowledge:
                    # Record user query for adaptive learning
                    self._record_query_for_learning(message, sqlite_knowledge, query_intent)
            except Exception as e:
                print(f"[BrainConnector] SQLite query error: {e}")
        
        # Also get from legacy JSON brain (for backwards compatibility)
        json_knowledge = self._get_knowledge_from_json(message, query_intent)
        
        # Merge and deduplicate
        all_knowledge = self._merge_knowledge_sources(sqlite_knowledge, json_knowledge)
        
        return all_knowledge
    
    def _get_knowledge_from_sqlite(self, message: str, query_intent: Dict) -> List[Dict]:
        """Query SQLite database for knowledge."""
        if not self.knowledge_db:
            return []
        
        # Search knowledge database
        results = self.knowledge_db.search_knowledge(
            query=message,
            limit=10,
            min_confidence=0.3
        )
        
        # Convert to expected format and score
        knowledge = []
        for item in results:
            knowledge.append({
                'title': item.get('title', ''),
                'content': item.get('content', ''),
                'source': item.get('source', 'sqlite'),
                'url': item.get('url', ''),
                'confidence': item.get('confidence', 0.5),
                'learned_at': item.get('created_at', ''),
                'from_sqlite': True
            })
        
        return knowledge
    
    def _record_query_for_learning(self, message: str, knowledge: List[Dict], query_intent: Dict):
        """Record user query for adaptive learning."""
        if not self.knowledge_db:
            return
        
        try:
            # Use topic extractor for better topic extraction
            try:
                from services.topic_extractor import get_topic_extractor
                extractor = get_topic_extractor()
                topics = extractor.extract_topics(message, max_topics=5)
            except ImportError:
                # Fallback to simple extraction
                words = message.lower().split()
                common_words = {'a', 'an', 'the', 'is', 'are', 'was', 'were', 'what', 'how', 'why', 'when', 'where', 'who'}
                topics = [w for w in words if len(w) > 3 and w not in common_words][:5]
            
            # Record the query
            self.knowledge_db.record_user_query(
                query=message,
                extracted_topics=topics,
                knowledge_found=len(knowledge) > 0,
                needs_research=len(knowledge) == 0
            )
            
            # Boost priority of topics that were asked about
            for topic in topics:
                self.knowledge_db.boost_topic_priority(topic, boost=1)
                
        except Exception as e:
            # Silently fail - logging is optional
            pass
    
    def _merge_knowledge_sources(
        self,
        sqlite_knowledge: List[Dict],
        json_knowledge: List[Dict]
    ) -> List[Dict]:
        """Merge and deduplicate knowledge from multiple sources."""
        seen_content = set()
        merged = []
        
        # Prioritize SQLite results (usually more recent and higher quality)
        for item in sqlite_knowledge:
            content_hash = hash(item.get('content', '')[:100])
            if content_hash not in seen_content:
                seen_content.add(content_hash)
                merged.append(item)
        
        # Add JSON results that aren't duplicates
        for item in json_knowledge:
            content_hash = hash(item.get('content', '')[:100])
            if content_hash not in seen_content:
                seen_content.add(content_hash)
                merged.append(item)
        
        # Sort by confidence
        merged.sort(key=lambda x: x.get('confidence', 0.5), reverse=True)
        
        return merged[:10]  # Return top 10
    
    def _get_knowledge_from_json(self, message: str, query_intent: Dict) -> List[Dict]:
        """Get knowledge from legacy JSON brain structure."""
        message_lower = message.lower()
        words = message_lower.split()
        
        # Detect recipe/cooking queries
        recipe_patterns = ['how to make', 'recipe for', 'how do you make', 'how do i make', 
                          'recipe', 'cook', 'cooking', 'dish', 'ingredients']
        is_recipe_query = any(pattern in message_lower for pattern in recipe_patterns)
        
        # Expand abbreviations (js -> javascript, py -> python)
        lang_expansions = {
            'js': 'javascript',
            'py': 'python',
            'ts': 'typescript',
            'rb': 'ruby',
            'cpp': 'c++',
            'cs': 'c#'
        }
        
        # Replace abbreviations with full names
        expanded_words = []
        for word in words:
            # Remove punctuation for matching
            clean_word = word.strip('.,!?;:()[]{}')
            if clean_word.lower() in lang_expansions:
                expanded_words.append(lang_expansions[clean_word.lower()])
                expanded_words.append(clean_word)  # Keep original too
            else:
                expanded_words.append(word)
        words = expanded_words
        message_lower = ' '.join(words).lower()
        
        # Filter out very common words that cause false matches
        common_words = {
            'a', 'an', 'the', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those',
            'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her',
            'us', 'them', 'my', 'your', 'his', 'her', 'its', 'our', 'their',
            'who', 'what', 'where', 'when', 'why', 'how', 'which', 'whose',
            'and', 'or', 'but', 'if', 'then', 'else', 'for', 'with', 'from',
            'to', 'of', 'in', 'on', 'at', 'by', 'about', 'into', 'through',
            'up', 'down', 'out', 'off', 'over', 'under', 'again', 'further',
            'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how',
            'all', 'both', 'each', 'few', 'more', 'most', 'other', 'some',
            'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than',
            'too', 'very', 's', 't', 'can', 'will', 'just', 'don', 'should',
            'now', 'make', 'makes', 'making', 'tell', 'me', 'explain', 'about'  # Added common question words
        }
        
        # Filter words - only use meaningful words (length > 2 and not common)
        meaningful_words = [w.strip('.,!?;:()[]{}') for w in words if len(w.strip('.,!?;:()[]{}')) > 2 and w.strip('.,!?;:()[]{}').lower() not in common_words]
        
        # For queries like "js functions", prioritize finding "javascript functions" not just "javascript"
        # Group related words together
        programming_langs = ['javascript', 'python', 'java', 'typescript', 'c++', 'c#', 'ruby', 'go', 'rust']
        tech_keywords = ['functions', 'classes', 'objects', 'arrays', 'variables', 'loops', 'conditions', 
                        'methods', 'constructors', 'prototypes', 'modules', 'packages']
        
        # Build topic phrases - combine language + keyword if both present
        topic_phrases = []
        for lang in programming_langs:
            lang_in_msg = lang in message_lower
            lang_abbrev_in_msg = any(lang.startswith(word) or word == lang[:2] for word in meaningful_words if len(word) <= 3)
            if lang_in_msg or lang_abbrev_in_msg:
                for keyword in tech_keywords:
                    if keyword in message_lower:
                        # Use full language name, not abbreviation
                        topic_phrases.append(f"{lang} {keyword}")
                        break
        
        # Extract the main topic (likely the dish name) - usually the last meaningful word or phrase
        # For "how to make pasta", "pasta" is the main topic
        main_topic = None
        if is_recipe_query and meaningful_words:
            # For recipe queries, prioritize the last meaningful word(s) as the dish name
            # Skip common action words like "make"
            action_words = {'make', 'cook', 'prepare', 'bake', 'fry', 'grill'}
            topic_words = [w for w in meaningful_words if w not in action_words]
            if topic_words:
                main_topic = topic_words[-1]  # Usually the dish name comes last
                # Also try combining last 2 words for multi-word dish names
                if len(topic_words) > 1:
                    main_topic_phrase = ' '.join(topic_words[-2:])
        
        # If message is too short or only has common words, return empty
        if len(meaningful_words) == 0:
            return []
        
        relevant_knowledge = []
        seen_titles = set()
        
        # Priority: search for main topic first, then other meaningful words
        search_order = []
        if main_topic:
            search_order.append(main_topic)
        # Add other meaningful words that aren't the main topic
        for word in meaningful_words:
            if word != main_topic and word not in search_order:
                search_order.append(word)
        
        # If no main topic identified, use original order
        if not search_order:
            search_order = meaningful_words
        
        # Search through brain structure using prioritized words
        for word in search_order:
            if word and word[0].isalpha():
                letter = word[0].upper()
                keywords_file = os.path.join(self.brain_dir, letter, "keywords.json")
                
                if os.path.exists(keywords_file):
                    try:
                        with open(keywords_file, 'r') as f:
                            data = json.load(f)
                        
                        # Check if word is a keyword
                        if word in data.get('keywords', []):
                            # Get knowledge for this keyword
                            for knowledge in data.get('knowledge', []):
                                content = knowledge.get('content', '').lower()
                                title = knowledge.get('title', '').lower()
                                source = knowledge.get('source', '')
                                
                                # Filter out greeting patterns and metadata
                                if 'response pattern for greeting' in content:
                                    continue
                                if 'use appropriate greeting' in content:
                                    continue
                                if source == 'greetings_handler':
                                    continue
                                if content.startswith('response pattern'):
                                    continue
                                
                                # For recipe queries, filter out non-cooking content
                                if is_recipe_query:
                                    # Reject if content is clearly about machine learning, programming, etc.
                                    cooking_keywords = ['recipe', 'cook', 'ingredient', 'dish', 'food', 'bake', 
                                                       'fry', 'grill', 'oven', 'stove', 'kitchen', 'serve', 
                                                       'taste', 'flavor', 'meal']
                                    tech_keywords = ['machine learning', 'algorithm', 'programming', 'code', 
                                                    'software', 'computer', 'ai', 'artificial intelligence']
                                    
                                    # If content has tech keywords but no cooking keywords, skip it
                                    has_cooking = any(ck in content for ck in cooking_keywords)
                                    has_tech = any(tk in content for tk in tech_keywords)
                                    
                                    if has_tech and not has_cooking:
                                        continue
                                    
                                    # For recipe queries, require the main topic (dish name) to appear in content or title
                                    if main_topic and main_topic not in content and main_topic not in title:
                                        continue
                                
                                # Check relevance - content should contain at least one meaningful word
                                # For recipe queries, require stronger relevance (main topic must match)
                                if is_recipe_query and main_topic:
                                    # Must contain the main topic
                                    if main_topic not in content and main_topic not in title:
                                        continue
                                else:
                                    # General relevance check - require multiple keyword matches for better precision
                                    matching_words = [mw for mw in meaningful_words[:5] if mw in content or mw in title]
                                    
                                    # For topic phrases (like "javascript functions"), require phrase match
                                    phrase_match = False
                                    if topic_phrases:
                                        for phrase in topic_phrases:
                                            if phrase in content or phrase in title:
                                                phrase_match = True
                                                break
                                    
                                    # Require at least 2 word matches OR a phrase match for better relevance
                                    if not phrase_match and len(matching_words) < 2 and len(meaningful_words) > 1:
                                        continue
                                    
                                    # If only one word, it must be in title or strongly in content
                                    if len(meaningful_words) == 1:
                                        if meaningful_words[0] not in title and meaningful_words[0] not in content[:100]:
                                            continue
                                
                                if title and title not in seen_titles:
                                    seen_titles.add(title)
                                    # Score by relevance - prioritize main topic matches and phrase matches
                                    score = 1
                                    if main_topic and (main_topic in content or main_topic in title):
                                        score = 2
                                    # Boost score for topic phrase matches
                                    if topic_phrases:
                                        for phrase in topic_phrases:
                                            if phrase in content or phrase in title:
                                                score = 3
                                                break
                                    relevant_knowledge.append((score, knowledge))
                    except:
                        continue
        
        # Sort by relevance score (higher first), then return knowledge items
        # Filter out any non-tuple items and ensure we have valid tuples
        valid_knowledge = []
        for item in relevant_knowledge:
            if isinstance(item, tuple) and len(item) >= 2:
                valid_knowledge.append(item)
            elif isinstance(item, dict):
                # If it's a dict, wrap it in a tuple with default score
                valid_knowledge.append((1, item))
        
        valid_knowledge.sort(key=lambda x: x[0], reverse=True)
        # k is already the knowledge dict (second element of tuple), not a tuple itself
        scored_items = [(score, k) for score, k in valid_knowledge]
        
        # Use semantic relevance scorer to filter and re-score for better accuracy
        semantic_scorer = get_semantic_scorer()
        final_scored = semantic_scorer.filter_knowledge_by_relevance(
            message,
            [item[1] for item in scored_items[:10]],  # Top 10 candidates
            query_intent,
            min_score=0.2  # Minimum relevance threshold
        )
        
        # If we have semantic scores, use those; otherwise use original scores
        if final_scored:
            # Combine scores (weighted average: 60% semantic, 40% keyword-based)
            score_map = {id(item[1]): item[0] for item in final_scored}
            result = []
            for orig_score, item in scored_items[:10]:
                item_id = id(item)
                if item_id in score_map:
                    # Weighted: 60% semantic, 40% keyword-based
                    combined_score = (score_map[item_id] * 0.6) + (min(orig_score / 3.0, 1.0) * 0.4)
                    result.append((combined_score, item))
            result.sort(key=lambda x: x[0], reverse=True)
            return [item for _, item in result[:5]]  # Return top 5 most relevant
        
        # Fallback to original scoring
        return [k[1] for k in scored_items[:5]]
    
    def get_database_stats(self) -> Optional[Dict]:
        """Get statistics from the SQLite knowledge database."""
        if self.use_sqlite and self.knowledge_db:
            try:
                return self.knowledge_db.get_database_stats()
            except Exception as e:
                print(f"[BrainConnector] Stats error: {e}")
        return None
    
    def search_database(
        self,
        query: str,
        limit: int = 10,
        min_confidence: float = 0.0,
        sources: List[str] = None
    ) -> List[Dict]:
        """Direct search of the SQLite knowledge database."""
        if self.use_sqlite and self.knowledge_db:
            try:
                return self.knowledge_db.search_knowledge(
                    query=query,
                    limit=limit,
                    min_confidence=min_confidence,
                    sources=sources
                )
            except Exception as e:
                print(f"[BrainConnector] Search error: {e}")
        return []

    def calculate_confidence_score(self, knowledge_item: Dict, query: str, query_intent: Optional[Dict] = None) -> float:
        """
        Calculate comprehensive confidence score for knowledge item.

        Args:
            knowledge_item: Knowledge dictionary
            query: Original query
            query_intent: Query intent analysis

        Returns:
            Confidence score between 0.0 and 1.0
        """
        score = 0.0
        weights = self.confidence_weights

        content = knowledge_item.get('content', '').lower()
        title = knowledge_item.get('title', '').lower()
        source = knowledge_item.get('source', '')

        # Source reliability score
        source_score = self._calculate_source_reliability(source)
        score += weights['source_reliability'] * source_score

        # Content quality score
        quality_score = self._calculate_content_quality(knowledge_item)
        score += weights['content_quality'] * quality_score

        # Temporal relevance score
        temporal_score = self._calculate_temporal_relevance(knowledge_item)
        score += weights['temporal_relevance'] * temporal_score

        # Semantic similarity score
        semantic_score = self._calculate_semantic_similarity(content, query)
        score += weights['semantic_similarity'] * semantic_score

        # Keyword overlap score
        keyword_score = self._calculate_keyword_overlap(content, title, query)
        score += weights['keyword_overlap'] * keyword_score

        return min(max(score, 0.0), 1.0)  # Clamp to [0, 1]

    def _calculate_source_reliability(self, source: str) -> float:
        """Calculate reliability score based on source."""
        source_scores = {
            'wikipedia': 0.9,
            'structured': 0.8,
            'duckduckgo': 0.7,
            'research_engine': 0.6,
            'brain_learner': 0.5,
            'conversation': 0.4,
        }

        # Low quality sources get low scores
        if source in self.low_quality_sources:
            return 0.1

        return source_scores.get(source, 0.3)

    def _calculate_content_quality(self, knowledge_item: Dict) -> float:
        """Calculate content quality score."""
        content = knowledge_item.get('content', '')
        title = knowledge_item.get('title', '')

        score = 0.0

        # Length check
        content_length = len(content.split())
        if content_length < self.min_content_length:
            return 0.1  # Too short
        elif content_length > 500:
            score += 0.3  # Substantial content
        elif content_length > 100:
            score += 0.2  # Good length
        else:
            score += 0.1  # Minimal acceptable

        # Completeness check (ends with sentence terminator)
        if content.strip().endswith(('.', '!', '?', '...')):
            score += 0.2

        # Has title
        if title and len(title) > 5:
            score += 0.2

        # Check for low-quality patterns
        content_lower = content.lower()
        if any(pattern.lower() in content_lower for pattern in self.low_quality_patterns):
            score *= 0.3  # Significant penalty

        # Information density (ratio of meaningful words)
        words = content.split()
        meaningful_words = [w for w in words if len(w) > 3 and w not in ['that', 'this', 'with', 'from', 'they', 'what', 'when', 'where', 'how', 'why']]
        if words:
            density = len(meaningful_words) / len(words)
            score += min(density * 0.3, 0.3)

        return min(score, 1.0)

    def _calculate_temporal_relevance(self, knowledge_item: Dict) -> float:
        """Calculate temporal relevance score."""
        learned_at = knowledge_item.get('learned_at')

        if not learned_at:
            return 0.5  # Neutral if no timestamp

        try:
            # Parse timestamp
            if isinstance(learned_at, str):
                learned_date = datetime.fromisoformat(learned_at.replace('Z', '+00:00'))
            else:
                learned_date = datetime.now() - timedelta(days=365)  # Assume 1 year old

            days_old = (datetime.now() - learned_date).days

            # Exponential decay: newer is better
            if days_old <= 30:
                return 1.0  # Very recent
            elif days_old <= 90:
                return 0.8  # Recent
            elif days_old <= 365:
                return 0.6  # Within a year
            elif days_old <= self.max_content_age_days:
                return 0.4  # Within acceptable range
            else:
                return 0.2  # Too old

        except Exception:
            return 0.5  # Neutral on parsing error

    def _calculate_semantic_similarity(self, content: str, query: str) -> float:
        """Calculate semantic similarity between content and query."""
        if not content or not query:
            return 0.0

        # Simple word overlap as proxy (in production, use embeddings)
        query_words = set(query.lower().split())
        content_words = set(content.lower().split())

        if not query_words:
            return 0.0

        overlap = len(query_words.intersection(content_words))
        similarity = overlap / len(query_words)

        return min(similarity, 1.0)

    def _calculate_keyword_overlap(self, content: str, title: str, query: str) -> float:
        """Calculate keyword overlap score."""
        query_lower = query.lower()
        combined_text = (content + " " + title).lower()

        # Exact phrase matches
        if query_lower in combined_text:
            return 1.0

        # Word-level matches
        query_words = set(query_lower.split())
        text_words = set(combined_text.split())

        overlap = len(query_words.intersection(text_words))
        if not query_words:
            return 0.0

        return min(overlap / len(query_words), 1.0)

    def filter_knowledge_by_quality(self, knowledge_items: List[Dict], min_confidence: float = 0.3) -> List[Dict]:
        """
        Filter knowledge items by quality and confidence scores.

        Args:
            knowledge_items: List of knowledge items
            min_confidence: Minimum confidence score to keep

        Returns:
            Filtered list of knowledge items
        """
        filtered = []

        for item in knowledge_items:
            # Basic quality checks
            content = item.get('content', '').strip()
            source = item.get('source', '')

            # Skip low-quality sources
            if source in self.low_quality_sources:
                continue

            # Skip very short content
            if len(content) < self.min_content_length:
                continue

            # Skip low-quality patterns
            content_lower = content.lower()
            if any(pattern.lower() in content_lower for pattern in self.low_quality_patterns):
                continue

            # Confidence check
            confidence = self.calculate_confidence_score(item, "")
            if confidence >= min_confidence:
                # Add confidence score to item
                item['confidence_score'] = confidence
                filtered.append(item)

        return filtered

    def synthesize_knowledge(self, knowledge_items: List[Dict], query: str) -> Dict:
        """
        Synthesize multiple knowledge items into coherent information.

        Args:
            knowledge_items: List of related knowledge items
            query: Original query

        Returns:
            Synthesized knowledge dictionary
        """
        if not knowledge_items:
            return {}

        # Group by topic/theme
        topics = {}
        for item in knowledge_items:
            # Simple topic extraction from title/content
            title = item.get('title', '').lower()
            content_start = item.get('content', '').lower()[:100]

            # Use first meaningful words as topic key
            words = (title + " " + content_start).split()[:3]
            topic_key = " ".join(w for w in words if len(w) > 2)[:50]

            if topic_key not in topics:
                topics[topic_key] = []
            topics[topic_key].append(item)

        # Synthesize each topic
        synthesized_parts = []
        for topic, items in topics.items():
            if len(items) == 1:
                # Single item - use as is
                synthesized_parts.append(items[0]['content'][:300])
            else:
                # Multiple items - create summary
                contents = [item['content'][:200] for item in items]
                combined = " ".join(contents)

                # Simple extractive summarization (take first and last sentences)
                sentences = combined.split('.')
                if len(sentences) >= 2:
                    summary = sentences[0].strip() + ". " + sentences[-2].strip() + "."
                else:
                    summary = combined[:400] + "..."

                synthesized_parts.append(f"{topic}: {summary}")

        return {
            'title': f"Synthesized knowledge about: {query[:50]}",
            'content': "\n\n".join(synthesized_parts),
            'source': 'synthesized',
            'learned_at': datetime.now().isoformat(),
            'confidence_score': sum(item.get('confidence_score', 0.5) for item in knowledge_items) / len(knowledge_items)
        }

    def enhance_response(self, message, base_response):
        """
        Enhance response with knowledge from brain using advanced filtering and synthesis.

        Args:
            message: Original user message
            base_response: Base AI response

        Returns:
            Enhanced response with relevant knowledge
        """
        # Get initial knowledge with enhanced retrieval
        knowledge = self.get_relevant_knowledge(message)

        if knowledge:
            # Apply quality filtering with confidence scoring
            filtered_knowledge = self.filter_knowledge_by_quality(knowledge, min_confidence=0.4)

            if filtered_knowledge:
                # Sort by confidence score
                filtered_knowledge.sort(key=lambda x: x.get('confidence_score', 0.5), reverse=True)

                # Try RAG-enhanced response first
                try:
                    rag_response = self.rag_enhancer.enhance_response_with_rag(
                        message, base_response,
                        retrieval_method="hybrid",
                        top_k=3,
                        use_reranking=True
                    )
                    if rag_response != base_response:  # RAG added content
                        return rag_response
                except Exception as e:
                    # Fallback to traditional enhancement if RAG fails
                    pass

                # Fallback: traditional knowledge enhancement
                context_parts = []
                used_items = 0
                max_items = 2

                for k in filtered_knowledge:
                    if used_items >= max_items:
                        break

                    content = k.get('content', '').strip()
                    confidence = k.get('confidence_score', 0.5)

                    # Enhanced content cleaning
                    if content and len(content) > self.min_content_length:
                        # Ensure complete sentences
                        if not content.endswith(('.', '!', '?', '...')):
                            last_period = content.rfind('.')
                            if last_period > len(content) * 0.5:
                                content = content[:last_period + 1]

                        # Limit length based on confidence (higher confidence = more content)
                        max_length = int(200 + (confidence * 100))  # 200-300 chars
                        content = content[:max_length]

                        if content:
                            # Add confidence indicator for high-confidence content
                            if confidence > 0.7:
                                context_parts.append(f"[High confidence] {content}")
                            else:
                                context_parts.append(content)
                            used_items += 1

                if context_parts:
                    # Create enhanced response
                    enhanced = base_response

                    if len(context_parts) == 1:
                        enhanced += f"\n\nRelated knowledge: {context_parts[0]}"
                    else:
                        enhanced += "\n\nRelated knowledge:"
                        for i, part in enumerate(context_parts, 1):
                            enhanced += f"\n{i}. {part}"

                    return enhanced

        return base_response
    
    def get_keywords_for_message(self, message):
        """Extract keywords that match brain structure"""
        message_lower = message.lower()
        words = message_lower.split()
        
        matched_keywords = []
        
        for word in words:
            if word and word[0].isalpha():
                letter = word[0].upper()
                keywords_file = os.path.join(self.brain_dir, letter, "keywords.json")
                
                if os.path.exists(keywords_file):
                    try:
                        with open(keywords_file, 'r') as f:
                            data = json.load(f)
                        
                        if word in data.get('keywords', []):
                            matched_keywords.append(word)
                    except:
                        continue
        
        return matched_keywords

    def get_enhanced_knowledge(
        self,
        query: str,
        context: str = "",
        max_results: int = 5,
        include_citations: bool = True
    ) -> Dict:
        """
        Enhanced knowledge retrieval with semantic search, ranking, and context injection.

        Args:
            query: User's query
            context: Conversation context for better relevance
            max_results: Maximum number of knowledge items to return
            include_citations: Whether to include source citations

        Returns:
            Dict with knowledge items, rankings, and injection context
        """
        # Get query intent for better understanding
        query_analyzer = get_query_intent_analyzer()
        query_intent = query_analyzer.analyze(query)

        # Combine query and context for better semantic understanding
        combined_query = f"{query} {context}".strip()

        # Get initial keyword-based knowledge
        keyword_knowledge = self.get_relevant_knowledge(query)

        # Apply semantic ranking and filtering
        semantic_scorer = get_semantic_scorer()
        ranked_knowledge = semantic_scorer.filter_knowledge_by_relevance(
            combined_query,
            keyword_knowledge,
            query_intent,
            min_score=0.15  # Lower threshold for enhanced retrieval
        )

        # Apply additional ranking factors
        final_ranked = self._apply_advanced_ranking(
            ranked_knowledge,
            query,
            context,
            query_intent
        )

        # Select top results
        top_knowledge = final_ranked[:max_results]

        # Prepare knowledge for injection into generation context
        injection_context = self._prepare_knowledge_injection(top_knowledge, query)

        # Add citations if requested
        citations = []
        if include_citations:
            citations = self._generate_citations(top_knowledge)

        return {
            'knowledge_items': [item for _, item in top_knowledge],
            'rankings': [{'score': score, 'item': item} for score, item in top_knowledge],
            'injection_context': injection_context,
            'citations': citations,
            'query_intent': query_intent,
            'total_candidates': len(ranked_knowledge),
            'selected_count': len(top_knowledge)
        }

    def _apply_advanced_ranking(
        self,
        scored_knowledge: List[Tuple[float, Dict]],
        query: str,
        context: str,
        query_intent: Dict
    ) -> List[Tuple[float, Dict]]:
        """
        Apply advanced ranking factors beyond semantic similarity.

        Factors:
        - Recency (newer knowledge is preferred)
        - Source quality (wikipedia > duckduckgo > bing)
        - Length appropriateness (longer content for complex queries)
        - Context relevance (how well it fits conversation context)
        """
        enhanced_scores = []

        for score, item in scored_knowledge:
            enhanced_score = score

            # Recency factor (newer knowledge gets slight boost)
            learned_at = item.get('learned_at', '')
            if learned_at:
                try:
                    learned_date = datetime.fromisoformat(learned_at.replace('Z', '+00:00'))
                    days_old = (datetime.now() - learned_date).days
                    # Slight boost for knowledge less than 7 days old
                    if days_old < 7:
                        enhanced_score += 0.05
                    elif days_old < 30:
                        enhanced_score += 0.02
                except:
                    pass

            # Source quality factor
            source = item.get('source', '').lower()
            source_quality = {
                'wikipedia': 0.1,
                'google': 0.08,
                'duckduckgo': 0.06,
                'bing': 0.05,
                'brave': 0.07,
                'structured': 0.03
            }
            enhanced_score += source_quality.get(source, 0.0)

            # Length appropriateness factor
            content_length = len(item.get('content', ''))
            query_complexity = len(query.split()) + len(context.split()) * 0.5

            # Prefer longer content for complex queries
            if query_complexity > 15 and content_length > 300:
                enhanced_score += 0.05
            elif query_complexity < 8 and content_length < 200:
                enhanced_score += 0.03

            # Context relevance factor
            if context:
                context_overlap = self._calculate_context_overlap(item, context)
                enhanced_score += context_overlap * 0.1

            enhanced_scores.append((enhanced_score, item))

        # Re-sort by enhanced scores
        enhanced_scores.sort(key=lambda x: x[0], reverse=True)
        return enhanced_scores

    def _calculate_context_overlap(self, knowledge_item: Dict, context: str) -> float:
        """Calculate how well knowledge overlaps with conversation context"""
        content = knowledge_item.get('content', '').lower()
        context_lower = context.lower()

        # Extract meaningful words from context
        context_words = set(w for w in context_lower.split() if len(w) > 3)
        content_words = set(w for w in content[:500].split() if len(w) > 3)

        # Calculate overlap ratio
        overlap = len(context_words.intersection(content_words))
        total_words = len(context_words.union(content_words))

        if total_words == 0:
            return 0.0

        return overlap / total_words

    def _prepare_knowledge_injection(self, knowledge_items: List[Tuple[float, Dict]], query: str) -> str:
        """
        Prepare knowledge for injection into generation context.
        Creates a structured knowledge block that can be injected into prompts.
        """
        if not knowledge_items:
            return ""

        knowledge_blocks = []

        for i, (score, item) in enumerate(knowledge_items[:3]):  # Top 3 for context injection
            title = item.get('title', 'Knowledge Item')
            content = item.get('content', '').strip()
            source = item.get('source', 'unknown')

            # Truncate content if too long (keep most relevant part)
            if len(content) > 400:
                # Try to find a natural break point
                truncated = content[:400]
                last_period = truncated.rfind('.')
                if last_period > 300:  # If period is in last 100 chars
                    truncated = truncated[:last_period + 1]
                content = truncated + "..."

            # Format as structured knowledge block
            block = f"""[Knowledge {i+1}: {title}]
Source: {source}
Content: {content}
Relevance: {score:.2f}"""

            knowledge_blocks.append(block)

        # Combine into injection context
        if knowledge_blocks:
            injection = "\n\n".join(knowledge_blocks)
            return f"""Relevant knowledge from my learning database:

{injection}

Based on this knowledge, provide your response to: {query}"""
        else:
            return ""

    def _generate_citations(self, knowledge_items: List[Tuple[float, Dict]]) -> List[str]:
        """Generate citations for knowledge sources"""
        citations = []

        for i, (score, item) in enumerate(knowledge_items):
            title = item.get('title', 'Unknown Title')
            source = item.get('source', 'unknown')
            url = item.get('url', '')

            if url:
                citation = f"[{i+1}] {title} - {source.capitalize()} ({url})"
            else:
                citation = f"[{i+1}] {title} - {source.capitalize()}"

            citations.append(citation)

        return citations

    def inject_knowledge_into_prompt(self, base_prompt: str, knowledge_context: str) -> str:
        """
        Inject knowledge context into a generation prompt.
        Places knowledge before the main query for better context awareness.
        """
        if not knowledge_context.strip():
            return base_prompt

        # Find where to inject knowledge (before the main instruction)
        injection_point = base_prompt.find("Respond naturally") or base_prompt.find("Answer this") or len(base_prompt)

        if injection_point > 0:
            # Insert knowledge before the main instruction
            enhanced_prompt = (
                base_prompt[:injection_point] +
                "\n\n" + knowledge_context + "\n\n" +
                base_prompt[injection_point:]
            )
        else:
            # Append to end if no clear injection point
            enhanced_prompt = base_prompt + "\n\n" + knowledge_context

        return enhanced_prompt

