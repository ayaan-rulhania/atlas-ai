"""
Multi-Topic Knowledge Retriever - Retrieves knowledge from multiple topics/domains
for complex queries requiring cross-domain reasoning.
"""
import os
from typing import List, Dict, Optional, Set, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict

from .topic_extractor import get_topic_extractor
from .query_intent_analyzer import get_query_intent_analyzer
from .semantic_relevance import get_semantic_scorer
from brain.connector import BrainConnector


class MultiTopicRetriever:
    """
    Retrieves knowledge from multiple topics/domains for complex queries.
    Identifies relevant topics, retrieves knowledge in parallel, and ranks by relevance.
    """
    
    def __init__(self, brain_dir: str = "brain", use_sqlite: bool = True):
        self.brain_connector = BrainConnector(brain_dir, use_sqlite)
        self.topic_extractor = get_topic_extractor()
        self.query_analyzer = get_query_intent_analyzer()
        self.semantic_scorer = get_semantic_scorer()
        
        # Domain classification keywords
        self.domain_keywords = {
            'science': ['science', 'physics', 'chemistry', 'biology', 'research', 'experiment', 
                       'theory', 'hypothesis', 'discovery', 'study', 'scientific'],
            'economics': ['economics', 'economic', 'economy', 'market', 'trade', 'finance', 
                         'financial', 'policy', 'inflation', 'gdp', 'recession', 'growth'],
            'technology': ['technology', 'tech', 'computer', 'software', 'hardware', 'digital', 
                          'internet', 'network', 'system', 'platform', 'application'],
            'environment': ['climate', 'environment', 'environmental', 'pollution', 'carbon', 
                           'emission', 'green', 'sustainable', 'renewable', 'ecosystem'],
            'politics': ['politics', 'political', 'government', 'policy', 'law', 'legislation', 
                        'democracy', 'election', 'vote', 'senate', 'congress'],
            'health': ['health', 'medical', 'medicine', 'disease', 'treatment', 'patient', 
                      'doctor', 'hospital', 'symptom', 'diagnosis', 'therapy'],
            'education': ['education', 'learning', 'teaching', 'school', 'university', 'student', 
                         'teacher', 'curriculum', 'academic', 'study', 'research'],
            'history': ['history', 'historical', 'war', 'battle', 'empire', 'ancient', 
                       'medieval', 'revolution', 'civilization', 'culture'],
            'philosophy': ['philosophy', 'philosophical', 'ethics', 'moral', 'existence', 
                         'reality', 'consciousness', 'truth', 'meaning', 'wisdom'],
            'general': []
        }
    
    def identify_topics(self, query: str, max_topics: int = 5) -> List[Dict[str, any]]:
        """
        Identify all relevant topics from a query, including domain classification.
        
        Args:
            query: User query
            max_topics: Maximum number of topics to identify
            
        Returns:
            List of topic dictionaries with 'topic', 'domain', 'relevance_score'
        """
        # Extract topics using topic extractor
        extracted_topics = self.topic_extractor.extract_topics(query, max_topics=max_topics * 2)
        
        # Analyze query for additional context
        query_analysis = self.query_analyzer.analyze(query)
        
        # Classify domains for each topic
        topics_with_domains = []
        seen_topics = set()
        
        for topic in extracted_topics:
            topic_lower = topic.lower()
            
            # Skip if already seen (deduplication)
            if topic_lower in seen_topics:
                continue
            seen_topics.add(topic_lower)
            
            # Classify domain
            domain = self._classify_domain(topic, query)
            
            # Calculate relevance score
            relevance_score = self._calculate_topic_relevance(topic, query, query_analysis)
            
            topics_with_domains.append({
                'topic': topic,
                'domain': domain,
                'relevance_score': relevance_score,
                'extracted_from': 'topic_extractor'
            })
        
        # Also extract domain-specific topics from query analysis
        if query_analysis.get('entities'):
            for entity in query_analysis['entities']:
                entity_lower = entity.lower()
                if entity_lower not in seen_topics and len(entity) > 3:
                    domain = self._classify_domain(entity, query)
                    relevance_score = self._calculate_topic_relevance(entity, query, query_analysis)
                    
                    topics_with_domains.append({
                        'topic': entity,
                        'domain': domain,
                        'relevance_score': relevance_score,
                        'extracted_from': 'entity_extraction'
                    })
                    seen_topics.add(entity_lower)
        
        # Sort by relevance score
        topics_with_domains.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        return topics_with_domains[:max_topics]
    
    def retrieve_multi_topic_knowledge(
        self,
        query: str,
        topics: Optional[List[Dict]] = None,
        max_knowledge_per_topic: int = 5,
        parallel: bool = True
    ) -> Dict[str, List[Dict]]:
        """
        Retrieve knowledge from multiple topics in parallel.
        
        Args:
            query: Original query
            topics: List of topic dictionaries (if None, will identify automatically)
            max_knowledge_per_topic: Maximum knowledge items per topic
            parallel: Whether to retrieve in parallel
            
        Returns:
            Dictionary mapping topic -> list of knowledge items
        """
        if topics is None:
            topics = self.identify_topics(query)
        
        if not topics:
            return {}
        
        # Retrieve knowledge for each topic
        topic_knowledge = {}
        
        if parallel:
            # Parallel retrieval
            with ThreadPoolExecutor(max_workers=min(len(topics), 5)) as executor:
                future_to_topic = {
                    executor.submit(
                        self._retrieve_topic_knowledge,
                        topic_info['topic'],
                        query,
                        max_knowledge_per_topic
                    ): topic_info
                    for topic_info in topics
                }
                
                for future in as_completed(future_to_topic):
                    topic_info = future_to_topic[future]
                    try:
                        knowledge = future.result()
                        topic_knowledge[topic_info['topic']] = knowledge
                    except Exception as e:
                        print(f"[MultiTopicRetriever] Error retrieving knowledge for '{topic_info['topic']}': {e}")
                        topic_knowledge[topic_info['topic']] = []
        else:
            # Sequential retrieval
            for topic_info in topics:
                knowledge = self._retrieve_topic_knowledge(
                    topic_info['topic'],
                    query,
                    max_knowledge_per_topic
                )
                topic_knowledge[topic_info['topic']] = knowledge
        
        return topic_knowledge
    
    def _retrieve_topic_knowledge(
        self,
        topic: str,
        query: str,
        max_knowledge: int
    ) -> List[Dict]:
        """Retrieve knowledge for a specific topic."""
        # Use BrainConnector to get knowledge
        knowledge = self.brain_connector.get_relevant_knowledge(topic)
        
        # Score and rank by relevance to original query
        query_analysis = self.query_analyzer.analyze(query)
        scored_knowledge = []
        
        for item in knowledge:
            score = self.semantic_scorer.calculate_semantic_score(
                query,
                item,
                query_analysis
            )
            scored_knowledge.append((item, score))
        
        # Sort by score and return top items
        scored_knowledge.sort(key=lambda x: x[1], reverse=True)
        
        return [item for item, score in scored_knowledge[:max_knowledge]]
    
    def _classify_domain(self, topic: str, query: str) -> str:
        """Classify a topic into a domain."""
        topic_lower = topic.lower()
        query_lower = query.lower()
        combined = f"{topic_lower} {query_lower}"
        
        domain_scores = defaultdict(float)
        
        for domain, keywords in self.domain_keywords.items():
            if domain == 'general':
                continue
            
            # Count keyword matches
            matches = sum(1 for keyword in keywords if keyword in combined)
            if matches > 0:
                domain_scores[domain] = matches / len(keywords)
        
        if domain_scores:
            # Return domain with highest score
            return max(domain_scores.items(), key=lambda x: x[1])[0]
        
        return 'general'
    
    def _calculate_topic_relevance(
        self,
        topic: str,
        query: str,
        query_analysis: Dict
    ) -> float:
        """Calculate relevance score for a topic."""
        score = 0.0
        
        # Base score from topic extractor (if available)
        topic_lower = topic.lower()
        query_lower = query.lower()
        
        # Exact match
        if topic_lower in query_lower or query_lower in topic_lower:
            score += 0.5
        
        # Word overlap
        topic_words = set(topic_lower.split())
        query_words = set(query_lower.split())
        overlap = len(topic_words.intersection(query_words))
        if query_words:
            score += (overlap / len(query_words)) * 0.3
        
        # Length preference (2-4 word topics are ideal)
        word_count = len(topic_words)
        if 2 <= word_count <= 4:
            score += 0.2
        
        # Domain relevance (if topic domain matches query domain)
        topic_domain = self._classify_domain(topic, query)
        query_domain = self._classify_domain(query, query)
        if topic_domain == query_domain and topic_domain != 'general':
            score += 0.1
        
        return min(score, 1.0)
    
    def get_enhanced_multi_topic_knowledge(
        self,
        query: str,
        max_topics: int = 5,
        max_knowledge_per_topic: int = 5
    ) -> Dict[str, any]:
        """
        Get enhanced multi-topic knowledge with metadata.
        
        Returns:
            Dictionary with:
            - topics: List of identified topics
            - knowledge_by_topic: Dict mapping topic -> knowledge items
            - total_knowledge_items: Total count
            - domains: Set of domains covered
        """
        # Identify topics
        topics = self.identify_topics(query, max_topics=max_topics)
        
        # Retrieve knowledge
        knowledge_by_topic = self.retrieve_multi_topic_knowledge(
            query,
            topics=topics,
            max_knowledge_per_topic=max_knowledge_per_topic
        )
        
        # Calculate statistics
        total_items = sum(len(items) for items in knowledge_by_topic.values())
        domains = set(topic_info['domain'] for topic_info in topics)
        
        return {
            'topics': topics,
            'knowledge_by_topic': knowledge_by_topic,
            'total_knowledge_items': total_items,
            'domains': list(domains),
            'query': query
        }


# Global instance
_multi_topic_retriever = None


def get_multi_topic_retriever(brain_dir: str = "brain", use_sqlite: bool = True) -> MultiTopicRetriever:
    """Get or create the global multi-topic retriever instance."""
    global _multi_topic_retriever
    if _multi_topic_retriever is None:
        _multi_topic_retriever = MultiTopicRetriever(brain_dir, use_sqlite)
    return _multi_topic_retriever

