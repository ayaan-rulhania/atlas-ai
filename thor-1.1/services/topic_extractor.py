"""
Topic Extractor - Extracts meaningful topics from user queries for adaptive learning.
"""
import re
from typing import List, Set, Dict
from collections import Counter


class TopicExtractor:
    """
    Extracts topics from user queries using NLP techniques.
    Identifies entities, concepts, and domain-specific terms.
    """
    
    def __init__(self):
        # Common stop words to filter out
        self.stop_words = {
            'a', 'an', 'the', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those',
            'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her',
            'us', 'them', 'my', 'your', 'his', 'her', 'its', 'our', 'their',
            'who', 'what', 'where', 'when', 'why', 'how', 'which', 'whose',
            'and', 'or', 'but', 'if', 'then', 'else', 'for', 'with', 'from',
            'to', 'of', 'in', 'on', 'at', 'by', 'about', 'into', 'through',
            'up', 'down', 'out', 'off', 'over', 'under', 'again', 'further',
            'tell', 'me', 'explain', 'about', 'what', 'is', 'how', 'does',
            'can', 'you', 'help', 'with', 'show', 'me', 'give', 'me'
        }
        
        # Question patterns that indicate topics
        self.question_patterns = [
            r'what is (.+?)(?:\?|$)',
            r'what are (.+?)(?:\?|$)',
            r'what does (.+?) mean(?:\?|$)',
            r'how does (.+?) work(?:\?|$)',
            r'how do (.+?) work(?:\?|$)',
            r'explain (.+?)(?:\?|$)',
            r'tell me about (.+?)(?:\?|$)',
            r'what is the (.+?)(?:\?|$)',
            r'who is (.+?)(?:\?|$)',
            r'who are (.+?)(?:\?|$)',
            r'where is (.+?)(?:\?|$)',
            r'when did (.+?)(?:\?|$)',
            r'why does (.+?)(?:\?|$)',
            r'how to (.+?)(?:\?|$)',
            r'how can (.+?)(?:\?|$)',
        ]
        
        # Domain-specific patterns
        self.domain_patterns = {
            'programming': [
                r'(\w+)\s+(function|class|method|variable|array|object|loop|condition)',
                r'(\w+)\s+programming',
                r'(\w+)\s+code',
                r'(\w+)\s+language',
                r'(\w+)\s+framework',
                r'(\w+)\s+library',
                r'(\w+)\s+api',
            ],
            'science': [
                r'(\w+)\s+(theory|law|principle|concept|phenomenon)',
                r'(\w+)\s+(discovery|experiment|research|study)',
            ],
            'history': [
                r'(\w+)\s+(war|battle|empire|dynasty|revolution)',
                r'(\w+)\s+history',
            ],
            'technology': [
                r'(\w+)\s+(technology|device|system|platform)',
                r'(\w+)\s+(ai|machine learning|neural network)',
            ]
        }
    
    def extract_topics(self, query: str, max_topics: int = 5) -> List[str]:
        """
        Extract topics from a user query.
        
        Args:
            query: User's query string
            max_topics: Maximum number of topics to extract
            
        Returns:
            List of extracted topics
        """
        query_lower = query.lower().strip()
        topics: Set[str] = set()
        
        # Method 1: Extract from question patterns
        for pattern in self.question_patterns:
            matches = re.findall(pattern, query_lower, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]
                topic = self._clean_topic(match)
                if topic and len(topic) > 2:
                    topics.add(topic)
        
        # Method 2: Extract domain-specific terms
        for domain, patterns in self.domain_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, query_lower, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple):
                        match = ' '.join(match)
                    topic = self._clean_topic(match)
                    if topic and len(topic) > 2:
                        topics.add(topic)
        
        # Method 3: Extract noun phrases (simple heuristic)
        words = query_lower.split()
        meaningful_words = [
            w.strip('.,!?;:()[]{}') 
            for w in words 
            if len(w.strip('.,!?;:()[]{}')) > 3 
            and w.strip('.,!?;:()[]{}') not in self.stop_words
        ]
        
        # Create 2-word phrases from consecutive meaningful words
        for i in range(len(meaningful_words) - 1):
            phrase = f"{meaningful_words[i]} {meaningful_words[i+1]}"
            if len(phrase) < 50:  # Reasonable length
                topics.add(phrase)
        
        # Add single meaningful words
        for word in meaningful_words[:max_topics]:
            if len(word) > 3:
                topics.add(word)
        
        # Score and rank topics
        scored_topics = self._score_topics(list(topics), query)
        
        # Return top topics
        return [topic for topic, score in scored_topics[:max_topics]]
    
    def _clean_topic(self, topic: str) -> str:
        """Clean and normalize a topic string."""
        # Remove leading/trailing whitespace and punctuation
        topic = topic.strip().strip('.,!?;:()[]{}')
        
        # Remove common prefixes
        prefixes = ['the', 'a', 'an', 'about', 'regarding', 'concerning']
        words = topic.split()
        if words and words[0].lower() in prefixes:
            topic = ' '.join(words[1:])
        
        # Capitalize properly
        if topic:
            topic = topic[0].upper() + topic[1:] if len(topic) > 1 else topic.upper()
        
        return topic.strip()
    
    def _score_topics(self, topics: List[str], original_query: str) -> List[tuple]:
        """Score topics by relevance to the original query."""
        query_words = set(original_query.lower().split())
        scored = []
        
        for topic in topics:
            score = 0.0
            topic_lower = topic.lower()
            topic_words = set(topic_lower.split())
            
            # Length score (prefer 2-4 word topics)
            word_count = len(topic_words)
            if 2 <= word_count <= 4:
                score += 0.3
            elif word_count == 1:
                score += 0.1
            
            # Overlap with query
            overlap = len(query_words.intersection(topic_words))
            if query_words:
                score += (overlap / len(query_words)) * 0.5
            
            # Specificity (longer topics are more specific)
            if len(topic) > 10:
                score += 0.2
            
            scored.append((topic, score))
        
        # Sort by score descending
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored
    
    def extract_main_topic(self, query: str) -> str:
        """Extract the main topic from a query."""
        topics = self.extract_topics(query, max_topics=1)
        return topics[0] if topics else query.split()[0] if query.split() else ""


# Global instance
_topic_extractor = None


def get_topic_extractor() -> TopicExtractor:
    """Get or create the global topic extractor instance."""
    global _topic_extractor
    if _topic_extractor is None:
        _topic_extractor = TopicExtractor()
    return _topic_extractor

