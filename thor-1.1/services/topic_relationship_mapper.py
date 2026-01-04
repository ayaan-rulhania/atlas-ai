"""
Topic Relationship Mapper - Builds and maintains topic relationship graph
for understanding connections between topics.
"""
import re
from typing import List, Dict, Optional, Set, Tuple
from collections import defaultdict

from .knowledge_db import get_knowledge_db
from .semantic_relevance import get_semantic_scorer


class TopicRelationshipMapper:
    """
    Maps relationships between topics by analyzing knowledge content.
    Identifies causal, hierarchical, and associative relationships.
    """
    
    def __init__(self):
        self.knowledge_db = get_knowledge_db()
        self.semantic_scorer = get_semantic_scorer()
        
        # Relationship patterns for extraction
        self.relationship_patterns = {
            'causal': [
                (r'(.+?)\s+(?:causes?|leads? to|results? in|brings? about)\s+(.+?)', 'forward'),
                (r'(.+?)\s+(?:is caused by|is due to|results from|stems from)\s+(.+?)', 'backward'),
                (r'(.+?)\s+(?:affects?|impacts?|influences?|affects?)\s+(.+?)', 'forward'),
                (r'(.+?)\s+(?:because of|due to|as a result of)\s+(.+?)', 'backward'),
            ],
            'hierarchical': [
                (r'(.+?)\s+(?:is a type of|is a kind of|is a form of|is a category of)\s+(.+?)', 'forward'),
                (r'(.+?)\s+(?:is part of|belongs to|is included in)\s+(.+?)', 'forward'),
                (r'(.+?)\s+(?:contains?|includes?|consists? of|comprises?)\s+(.+?)', 'backward'),
                (r'(.+?)\s+(?:is an example of|is an instance of)\s+(.+?)', 'forward'),
            ],
            'associative': [
                (r'(.+?)\s+(?:is related to|is associated with|is connected to|is linked to)\s+(.+?)', 'bidirectional'),
                (r'(.+?)\s+(?:similar to|like|analogous to|comparable to)\s+(.+?)', 'bidirectional'),
                (r'(.+?)\s+(?:and|with|alongside)\s+(.+?)', 'bidirectional'),
            ],
            'comparative': [
                (r'(.+?)\s+(?:versus|vs|compared to|in contrast to|unlike)\s+(.+?)', 'bidirectional'),
                (r'(.+?)\s+(?:better than|worse than|more than|less than)\s+(.+?)', 'forward'),
            ],
            'temporal': [
                (r'(.+?)\s+(?:before|precedes?|comes before)\s+(.+?)', 'forward'),
                (r'(.+?)\s+(?:after|follows?|comes after)\s+(.+?)', 'forward'),
                (r'(.+?)\s+(?:during|while|at the same time as)\s+(.+?)', 'bidirectional'),
            ]
        }
    
    def extract_relationships_from_knowledge(
        self,
        knowledge_items: List[Dict],
        topics: List[str]
    ) -> List[Dict]:
        """
        Extract relationships between topics from knowledge content.
        
        Args:
            knowledge_items: List of knowledge dictionaries
            topics: List of topics to find relationships for
            
        Returns:
            List of relationship dictionaries
        """
        relationships = []
        topic_set = set(t.lower() for t in topics)
        
        for item in knowledge_items:
            content = item.get('content', '').lower()
            title = item.get('title', '').lower()
            combined_text = f"{title} {content}"
            
            # Extract relationships using patterns
            for rel_type, patterns in self.relationship_patterns.items():
                for pattern, direction in patterns:
                    matches = re.finditer(pattern, combined_text, re.IGNORECASE)
                    for match in matches:
                        topic1 = match.group(1).strip()
                        topic2 = match.group(2).strip()
                        
                        # Check if both topics are in our topic set
                        topic1_lower = topic1.lower()
                        topic2_lower = topic2.lower()
                        
                        # Check for topic matches (exact or partial)
                        matched_topic1 = self._find_matching_topic(topic1_lower, topic_set)
                        matched_topic2 = self._find_matching_topic(topic2_lower, topic_set)
                        
                        if matched_topic1 and matched_topic2 and matched_topic1 != matched_topic2:
                            # Found a relationship
                            strength = self._calculate_relationship_strength(
                                topic1_lower,
                                topic2_lower,
                                rel_type,
                                combined_text
                            )
                            
                            relationships.append({
                                'topic1': matched_topic1,
                                'topic2': matched_topic2,
                                'relationship_type': rel_type,
                                'strength': strength,
                                'confidence': 0.7,  # Base confidence
                                'evidence': match.group(0),
                                'source': item.get('source', 'unknown')
                            })
        
        # Deduplicate relationships (keep strongest)
        relationships = self._deduplicate_relationships(relationships)
        
        return relationships
    
    def _find_matching_topic(self, text: str, topic_set: Set[str]) -> Optional[str]:
        """Find if text contains or matches any topic in topic_set."""
        text_lower = text.lower().strip()
        
        # Exact match
        if text_lower in topic_set:
            return text_lower
        
        # Check if any topic is contained in text
        for topic in topic_set:
            if topic in text_lower or text_lower in topic:
                return topic
        
        # Check word-level matching
        text_words = set(text_lower.split())
        for topic in topic_set:
            topic_words = set(topic.split())
            if len(text_words.intersection(topic_words)) >= min(len(topic_words), 2):
                return topic
        
        return None
    
    def _calculate_relationship_strength(
        self,
        topic1: str,
        topic2: str,
        rel_type: str,
        context: str
    ) -> float:
        """Calculate strength of a relationship."""
        strength = 0.5  # Base strength
        
        # Increase strength if both topics appear multiple times
        topic1_count = context.lower().count(topic1.lower())
        topic2_count = context.lower().count(topic2.lower())
        
        if topic1_count > 1 and topic2_count > 1:
            strength += 0.2
        
        # Increase strength for explicit relationship words
        explicit_indicators = {
            'causal': ['cause', 'effect', 'impact', 'influence', 'result'],
            'hierarchical': ['type', 'kind', 'part', 'contains', 'includes'],
            'associative': ['related', 'associated', 'connected', 'linked'],
            'comparative': ['versus', 'compared', 'different', 'similar'],
            'temporal': ['before', 'after', 'during', 'follows']
        }
        
        indicators = explicit_indicators.get(rel_type, [])
        indicator_count = sum(1 for indicator in indicators if indicator in context.lower())
        if indicator_count > 0:
            strength += min(indicator_count * 0.1, 0.3)
        
        return min(strength, 1.0)
    
    def _deduplicate_relationships(self, relationships: List[Dict]) -> List[Dict]:
        """Deduplicate relationships, keeping the strongest."""
        relationship_map = {}
        
        for rel in relationships:
            # Create key (order-independent)
            key = tuple(sorted([rel['topic1'], rel['topic2']])) + (rel['relationship_type'],)
            
            if key not in relationship_map:
                relationship_map[key] = rel
            else:
                # Keep stronger relationship
                existing = relationship_map[key]
                if rel['strength'] > existing['strength']:
                    relationship_map[key] = rel
        
        return list(relationship_map.values())
    
    def build_relationship_graph(
        self,
        topics: List[str],
        knowledge_by_topic: Dict[str, List[Dict]]
    ) -> Dict[str, List[Dict]]:
        """
        Build a relationship graph for given topics.
        
        Returns:
            Dictionary mapping topic -> list of relationships
        """
        # Collect all knowledge items
        all_knowledge = []
        for items in knowledge_by_topic.values():
            all_knowledge.extend(items)
        
        # Extract relationships
        relationships = self.extract_relationships_from_knowledge(all_knowledge, topics)
        
        # Store relationships in database
        for rel in relationships:
            self.knowledge_db.add_topic_relationship(
                topic1=rel['topic1'],
                topic2=rel['topic2'],
                relationship_type=rel['relationship_type'],
                strength=rel['strength'],
                confidence=rel['confidence'],
                evidence=rel.get('evidence', '')
            )
        
        # Build graph structure
        graph = defaultdict(list)
        for rel in relationships:
            graph[rel['topic1']].append(rel)
            # Add reverse relationship for bidirectional types
            if rel['relationship_type'] in ['associative', 'comparative', 'temporal']:
                reverse_rel = rel.copy()
                reverse_rel['topic1'], reverse_rel['topic2'] = reverse_rel['topic2'], reverse_rel['topic1']
                graph[rel['topic2']].append(reverse_rel)
        
        return dict(graph)
    
    def find_related_topics(
        self,
        topic: str,
        relationship_type: str = None,
        max_results: int = 10
    ) -> List[str]:
        """Find topics related to a given topic."""
        relationships = self.knowledge_db.get_topic_relationships(
            topic,
            relationship_type=relationship_type
        )
        
        related = []
        topic_lower = topic.lower()
        
        for rel in relationships[:max_results]:
            if rel['topic1'] == topic_lower:
                related.append(rel['topic2'])
            else:
                related.append(rel['topic1'])
        
        return related
    
    def find_causal_path(
        self,
        topic1: str,
        topic2: str
    ) -> Optional[List[Dict]]:
        """Find a causal path between two topics."""
        return self.knowledge_db.find_causal_path(topic1, topic2)


# Global instance
_topic_relationship_mapper = None


def get_topic_relationship_mapper() -> TopicRelationshipMapper:
    """Get or create the global topic relationship mapper instance."""
    global _topic_relationship_mapper
    if _topic_relationship_mapper is None:
        _topic_relationship_mapper = TopicRelationshipMapper()
    return _topic_relationship_mapper

