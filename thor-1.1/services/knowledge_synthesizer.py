"""
Knowledge Synthesizer - Synthesizes knowledge from multiple topics into coherent context
for reasoning engines.
"""
from typing import List, Dict, Optional, Set, Tuple
from collections import defaultdict
import re

from .semantic_relevance import get_semantic_scorer


class KnowledgeSynthesizer:
    """
    Synthesizes knowledge from multiple topics into coherent, unified context.
    Identifies relationships, resolves conflicts, and creates contextual knowledge.
    """
    
    def __init__(self):
        self.semantic_scorer = get_semantic_scorer()
        
        # Relationship indicators
        self.relationship_patterns = {
            'causal': [
                r'causes?', r'leads? to', r'results? in', r'due to', r'because of',
                r'effects?', r'impacts?', r'influences?', r'affects?', r'contributes? to'
            ],
            'hierarchical': [
                r'is a type of', r'is a kind of', r'is part of', r'belongs to',
                r'contains?', r'includes?', r'consists? of', r'comprises?'
            ],
            'associative': [
                r'related to', r'associated with', r'connected to', r'linked to',
                r'similar to', r'like', r'compared to', r'analogous to'
            ],
            'temporal': [
                r'before', r'after', r'during', r'follows?', r'precedes?',
                r'earlier', r'later', r'subsequently', r'previously'
            ],
            'comparative': [
                r'versus', r'vs', r'compared to', r'different from', r'unlike',
                r'better than', r'worse than', r'more than', r'less than'
            ]
        }
    
    def synthesize_knowledge(
        self,
        knowledge_by_topic: Dict[str, List[Dict]],
        query: str,
        previous_context: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Synthesize knowledge from multiple topics into unified context.
        
        Args:
            knowledge_by_topic: Dictionary mapping topic -> knowledge items
            query: Original query
            previous_context: Context from previous reasoning steps
            
        Returns:
            Dictionary with:
            - synthesized_context: Unified context string
            - relationships: Detected relationships between topics
            - conflicts: Any conflicting information found
            - quality_score: Synthesis quality score
        """
        if not knowledge_by_topic:
            return {
                'synthesized_context': '',
                'relationships': [],
                'conflicts': [],
                'quality_score': 0.0
            }
        
        # Extract all knowledge items
        all_knowledge = []
        topic_to_items = {}
        
        for topic, items in knowledge_by_topic.items():
            all_knowledge.extend(items)
            topic_to_items[topic] = items
        
        # Detect relationships between topics
        relationships = self._detect_relationships(knowledge_by_topic, query)
        
        # Identify conflicts
        conflicts = self._identify_conflicts(all_knowledge)
        
        # Merge knowledge into coherent context
        synthesized_context = self._merge_knowledge(
            knowledge_by_topic,
            relationships,
            previous_context
        )
        
        # Calculate quality score
        quality_score = self._calculate_synthesis_quality(
            synthesized_context,
            relationships,
            conflicts,
            len(all_knowledge)
        )
        
        return {
            'synthesized_context': synthesized_context,
            'relationships': relationships,
            'conflicts': conflicts,
            'quality_score': quality_score,
            'topics_covered': list(knowledge_by_topic.keys()),
            'total_items': len(all_knowledge)
        }
    
    def _detect_relationships(
        self,
        knowledge_by_topic: Dict[str, List[Dict]],
        query: str
    ) -> List[Dict]:
        """Detect relationships between topics from knowledge content."""
        relationships = []
        topics = list(knowledge_by_topic.keys())
        
        # Compare each pair of topics
        for i, topic1 in enumerate(topics):
            for topic2 in topics[i+1:]:
                # Get knowledge items for both topics
                items1 = knowledge_by_topic[topic1]
                items2 = knowledge_by_topic[topic2]
                
                # Check for relationships in content
                relationship = self._find_relationship_between_topics(
                    topic1, items1, topic2, items2
                )
                
                if relationship:
                    relationships.append(relationship)
        
        return relationships
    
    def _find_relationship_between_topics(
        self,
        topic1: str,
        items1: List[Dict],
        topic2: str,
        items2: List[Dict]
    ) -> Optional[Dict]:
        """Find relationship between two topics."""
        # Combine content from both topics
        content1 = ' '.join(item.get('content', '') for item in items1[:3])
        content2 = ' '.join(item.get('content', '') for item in items2[:3])
        combined_content = f"{content1} {content2}".lower()
        
        # Check for relationship patterns
        for rel_type, patterns in self.relationship_patterns.items():
            for pattern in patterns:
                # Check if topic names appear together with relationship indicator
                if topic1.lower() in combined_content and topic2.lower() in combined_content:
                    # Look for pattern near topic mentions
                    pattern_matches = re.findall(pattern, combined_content, re.IGNORECASE)
                    if pattern_matches:
                        return {
                            'topic1': topic1,
                            'topic2': topic2,
                            'relationship_type': rel_type,
                            'strength': 0.7,  # Default strength
                            'evidence': f"Found '{pattern}' pattern in knowledge"
                        }
        
        # Check for direct mentions
        topic1_lower = topic1.lower()
        topic2_lower = topic2.lower()
        
        if topic1_lower in content2:
            return {
                'topic1': topic1,
                'topic2': topic2,
                'relationship_type': 'associative',
                'strength': 0.5,
                'evidence': f"'{topic1}' mentioned in '{topic2}' knowledge"
            }
        
        if topic2_lower in content1:
            return {
                'topic1': topic1,
                'topic2': topic2,
                'relationship_type': 'associative',
                'strength': 0.5,
                'evidence': f"'{topic2}' mentioned in '{topic1}' knowledge"
            }
        
        return None
    
    def _identify_conflicts(self, all_knowledge: List[Dict]) -> List[Dict]:
        """Identify conflicting information in knowledge items."""
        conflicts = []
        
        # Group by similar topics/titles
        topic_groups = defaultdict(list)
        for item in all_knowledge:
            topic = item.get('topic', '')
            title = item.get('title', '')
            key = f"{topic}:{title}".lower()
            topic_groups[key].append(item)
        
        # Check for contradictions within groups
        for key, items in topic_groups.items():
            if len(items) < 2:
                continue
            
            # Simple contradiction detection (can be enhanced)
            contents = [item.get('content', '').lower() for item in items]
            
            # Check for negation patterns
            negation_words = ['not', 'no', 'never', 'none', 'cannot', "doesn't", "don't"]
            positive_words = ['is', 'are', 'has', 'have', 'can', 'will', 'does']
            
            for i, content1 in enumerate(contents):
                for content2 in contents[i+1:]:
                    # Check for contradictory statements
                    has_negation1 = any(word in content1 for word in negation_words)
                    has_negation2 = any(word in content2 for word in negation_words)
                    has_positive1 = any(word in content1 for word in positive_words)
                    has_positive2 = any(word in content2 for word in positive_words)
                    
                    # Simple heuristic: if one has negation and other has positive for same concept
                    if (has_negation1 and has_positive2) or (has_negation2 and has_positive1):
                        # Check if they're talking about similar things
                        words1 = set(content1.split()[:20])  # First 20 words
                        words2 = set(content2.split()[:20])
                        overlap = len(words1.intersection(words2))
                        
                        if overlap > 3:  # Significant overlap
                            conflicts.append({
                                'item1': items[i],
                                'item2': items[i+1],
                                'type': 'contradiction',
                                'severity': 'medium'
                            })
        
        return conflicts
    
    def _merge_knowledge(
        self,
        knowledge_by_topic: Dict[str, List[Dict]],
        relationships: List[Dict],
        previous_context: Optional[str] = None
    ) -> str:
        """Merge knowledge from multiple topics into coherent context."""
        context_parts = []
        
        # Add previous context if available
        if previous_context:
            context_parts.append(f"Previous context: {previous_context}")
            context_parts.append("")
        
        # Group knowledge by topic
        for topic, items in knowledge_by_topic.items():
            if not items:
                continue
            
            # Create topic section
            context_parts.append(f"Knowledge about '{topic}':")
            
            # Add knowledge items (limit to avoid too long context)
            for i, item in enumerate(items[:3]):  # Max 3 items per topic
                title = item.get('title', '')
                content = item.get('content', '')
                source = item.get('source', 'unknown')
                
                if content:
                    # Truncate long content
                    if len(content) > 300:
                        content = content[:300] + "..."
                    
                    snippet = f"  [{source}] {title}: {content}"
                    context_parts.append(snippet)
            
            context_parts.append("")
        
        # Add relationship information
        if relationships:
            context_parts.append("Relationships between topics:")
            for rel in relationships[:5]:  # Max 5 relationships
                rel_type = rel['relationship_type']
                topic1 = rel['topic1']
                topic2 = rel['topic2']
                context_parts.append(f"  - {topic1} {rel_type} {topic2}")
            context_parts.append("")
        
        return "\n".join(context_parts)
    
    def _calculate_synthesis_quality(
        self,
        synthesized_context: str,
        relationships: List[Dict],
        conflicts: List[Dict],
        total_items: int
    ) -> float:
        """Calculate quality score for synthesized knowledge."""
        score = 0.0
        
        # Base score from context length (not too short, not too long)
        context_length = len(synthesized_context)
        if 200 <= context_length <= 2000:
            score += 0.3
        elif context_length > 200:
            score += 0.2
        
        # Relationship detection bonus
        if relationships:
            score += min(len(relationships) * 0.1, 0.3)
        
        # Conflict penalty
        if conflicts:
            score -= min(len(conflicts) * 0.1, 0.3)
        
        # Knowledge coverage bonus
        if total_items >= 3:
            score += 0.2
        elif total_items >= 1:
            score += 0.1
        
        return max(0.0, min(score, 1.0))
    
    def create_step_context(
        self,
        step_query: str,
        knowledge_by_topic: Dict[str, List[Dict]],
        previous_steps_context: Optional[List[str]] = None
    ) -> str:
        """
        Create context for a specific reasoning step.
        
        Args:
            step_query: Query for this specific step
            knowledge_by_topic: Knowledge items by topic
            previous_steps_context: Context from previous reasoning steps
            
        Returns:
            Formatted context string for the step
        """
        # Filter knowledge relevant to this step
        relevant_knowledge = {}
        
        step_lower = step_query.lower()
        for topic, items in knowledge_by_topic.items():
            # Check if topic is relevant to step
            if topic.lower() in step_lower:
                relevant_knowledge[topic] = items
            else:
                # Check if any items mention step keywords
                relevant_items = []
                step_words = set(step_lower.split())
                for item in items:
                    content = item.get('content', '').lower()
                    content_words = set(content.split())
                    overlap = len(step_words.intersection(content_words))
                    if overlap >= 2:  # At least 2 word overlap
                        relevant_items.append(item)
                
                if relevant_items:
                    relevant_knowledge[topic] = relevant_items
        
        # Synthesize with previous context
        previous_context = None
        if previous_steps_context:
            previous_context = "\n".join(previous_steps_context)
        
        synthesis_result = self.synthesize_knowledge(
            relevant_knowledge,
            step_query,
            previous_context
        )
        
        return synthesis_result['synthesized_context']


# Global instance
_knowledge_synthesizer = None


def get_knowledge_synthesizer() -> KnowledgeSynthesizer:
    """Get or create the global knowledge synthesizer instance."""
    global _knowledge_synthesizer
    if _knowledge_synthesizer is None:
        _knowledge_synthesizer = KnowledgeSynthesizer()
    return _knowledge_synthesizer

