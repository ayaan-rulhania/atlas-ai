"""
Context Manager - Intelligent conversation context management
Handles summarization, compression, and relevant context extraction for efficient memory usage
"""
import re
from typing import List, Dict, Tuple, Optional
from collections import defaultdict
import heapq
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ConversationTurn:
    """Represents a single turn in the conversation"""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: Optional[datetime] = None
    importance_score: float = 0.0
    topic_keywords: List[str] = None
    summary: Optional[str] = None

    def __post_init__(self):
        if self.topic_keywords is None:
            self.topic_keywords = []
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class ContextSummary:
    """Summary of conversation context"""
    summary_text: str
    key_topics: List[str]
    important_turns: List[ConversationTurn]
    compression_ratio: float
    relevance_score: float


class ContextManager:
    """Manages conversation context for efficient memory usage and relevance"""

    def __init__(self, max_context_length: int = 2048, summary_threshold: int = 1000):
        self.max_context_length = max_context_length
        self.summary_threshold = summary_threshold

        # Context management settings
        self.recency_weight = 0.3
        self.relevance_weight = 0.4
        self.importance_weight = 0.3

        # Topic tracking
        self.topic_tracker = defaultdict(int)
        self.conversation_topics = set()

    def manage_context(
        self,
        conversation_history: List[Dict],
        current_query: str,
        max_tokens: int = 2048
    ) -> Dict:
        """
        Manage conversation context by summarizing, compressing, and extracting relevant parts.

        Args:
            conversation_history: List of conversation turns [{'role': 'user'/'assistant', 'content': '...'}]
            current_query: Current user query for relevance calculation
            max_tokens: Maximum context length in tokens

        Returns:
            Dict with managed context and metadata
        """
        # Convert to ConversationTurn objects
        turns = self._parse_conversation_history(conversation_history)

        # Calculate importance and relevance scores
        self._score_conversation_turns(turns, current_query)

        # Check if summarization is needed
        total_content_length = sum(len(turn.content) for turn in turns)

        if total_content_length <= self.summary_threshold:
            # No summarization needed, just select relevant turns
            selected_turns = self._select_relevant_turns(turns, max_tokens)
            context_text = self._format_context(selected_turns)

            return {
                'context': context_text,
                'summarized': False,
                'compression_ratio': 1.0,
                'selected_turns': len(selected_turns),
                'total_turns': len(turns)
            }

        # Summarization needed
        summary = self._generate_context_summary(turns, current_query)
        compressed_context = self._compress_context(turns, summary, max_tokens)

        return {
            'context': compressed_context,
            'summarized': True,
            'summary': summary,
            'compression_ratio': len(compressed_context) / total_content_length if total_content_length > 0 else 1.0,
            'selected_turns': len(summary.important_turns),
            'total_turns': len(turns),
            'key_topics': summary.key_topics
        }

    def _parse_conversation_history(self, history: List[Dict]) -> List[ConversationTurn]:
        """Parse raw conversation history into ConversationTurn objects"""
        turns = []

        for item in history:
            turn = ConversationTurn(
                role=item.get('role', 'unknown'),
                content=item.get('content', ''),
                timestamp=item.get('timestamp')
            )

            # Extract topic keywords from content
            turn.topic_keywords = self._extract_topic_keywords(turn.content)

            # Update topic tracking
            for keyword in turn.topic_keywords:
                self.topic_tracker[keyword] += 1

            turns.append(turn)

        return turns

    def _extract_topic_keywords(self, text: str) -> List[str]:
        """Extract important topic keywords from text"""
        # Simple keyword extraction (can be enhanced with NLP)
        words = re.findall(r'\b\w+\b', text.lower())

        # Filter meaningful words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him',
            'her', 'us', 'them', 'my', 'your', 'his', 'her', 'its', 'our', 'their'
        }

        keywords = [word for word in words if len(word) > 3 and word not in stop_words]

        # Get most frequent meaningful keywords (top 5)
        keyword_freq = defaultdict(int)
        for keyword in keywords:
            keyword_freq[keyword] += 1

        # Return top keywords by frequency
        top_keywords = heapq.nlargest(5, keyword_freq.items(), key=lambda x: x[1])
        return [keyword for keyword, _ in top_keywords]

    def _score_conversation_turns(self, turns: List[ConversationTurn], current_query: str):
        """Calculate importance and relevance scores for each turn"""
        current_keywords = set(self._extract_topic_keywords(current_query))

        for i, turn in enumerate(turns):
            # Recency score (more recent = higher score)
            recency_score = i / len(turns) if len(turns) > 1 else 1.0

            # Relevance score based on keyword overlap with current query
            turn_keywords = set(turn.topic_keywords)
            if current_keywords and turn_keywords:
                overlap = len(current_keywords.intersection(turn_keywords))
                total = len(current_keywords.union(turn_keywords))
                relevance_score = overlap / total if total > 0 else 0.0
            else:
                relevance_score = 0.0

            # Importance score based on content length and topic significance
            content_length = len(turn.content)
            importance_score = min(content_length / 500, 1.0)  # Cap at 1.0

            # Boost score for turns with high topic significance
            topic_significance = sum(self.topic_tracker[kw] for kw in turn.topic_keywords)
            importance_score += min(topic_significance / 10, 0.5)

            # Combine scores
            turn.importance_score = (
                self.recency_weight * recency_score +
                self.relevance_weight * relevance_score +
                self.importance_weight * importance_score
            )

    def _select_relevant_turns(self, turns: List[ConversationTurn], max_tokens: int) -> List[ConversationTurn]:
        """Select the most relevant conversation turns within token limit"""
        if not turns:
            return []

        # Sort by importance score (highest first)
        sorted_turns = sorted(turns, key=lambda x: x.importance_score, reverse=True)

        selected_turns = []
        current_length = 0

        for turn in sorted_turns:
            turn_length = len(turn.content.split())  # Rough token estimation

            if current_length + turn_length <= max_tokens:
                selected_turns.append(turn)
                current_length += turn_length
            else:
                break

        # Sort selected turns back to chronological order
        selected_turns.sort(key=lambda x: x.timestamp or datetime.now())

        return selected_turns

    def _generate_context_summary(self, turns: List[ConversationTurn], current_query: str) -> ContextSummary:
        """Generate a comprehensive summary of the conversation context"""
        # Identify key topics
        all_keywords = []
        for turn in turns:
            all_keywords.extend(turn.topic_keywords)

        # Get most frequent topics
        topic_freq = defaultdict(int)
        for keyword in all_keywords:
            topic_freq[keyword] += 1

        key_topics = heapq.nlargest(10, topic_freq.items(), key=lambda x: x[1])
        key_topics = [topic for topic, _ in key_topics]

        # Identify important turns (top 20% by importance score)
        sorted_turns = sorted(turns, key=lambda x: x.importance_score, reverse=True)
        num_important = max(1, int(len(turns) * 0.2))
        important_turns = sorted_turns[:num_important]

        # Generate summary text
        summary_parts = []

        # Add key topics
        if key_topics:
            summary_parts.append(f"Main topics discussed: {', '.join(key_topics[:5])}")

        # Add conversation overview
        user_turns = [t for t in turns if t.role == 'user']
        assistant_turns = [t for t in turns if t.role == 'assistant']

        summary_parts.append(f"Conversation has {len(user_turns)} user messages and {len(assistant_turns)} assistant responses.")

        # Add recent context
        if len(turns) > 0:
            last_turn = turns[-1]
            if last_turn.role == 'user':
                summary_parts.append(f"Last user query: {last_turn.content[:100]}{'...' if len(last_turn.content) > 100 else ''}")
            else:
                summary_parts.append(f"Last assistant response covered: {last_turn.content[:100]}{'...' if len(last_turn.content) > 100 else ''}")

        # Calculate relevance to current query
        query_keywords = set(self._extract_topic_keywords(current_query))
        context_keywords = set(key_topics)

        if query_keywords and context_keywords:
            overlap = len(query_keywords.intersection(context_keywords))
            total = len(query_keywords.union(context_keywords))
            relevance_score = overlap / total if total > 0 else 0.0
        else:
            relevance_score = 0.0

        summary_text = " ".join(summary_parts)

        return ContextSummary(
            summary_text=summary_text,
            key_topics=key_topics,
            important_turns=important_turns,
            compression_ratio=0.0,  # Will be set later
            relevance_score=relevance_score
        )

    def _compress_context(self, turns: List[ConversationTurn], summary: ContextSummary,
                         max_tokens: int) -> str:
        """Compress conversation context using summary and selective turn inclusion"""
        compressed_parts = []

        # Start with summary
        compressed_parts.append(f"[Conversation Summary: {summary.summary_text}]")

        # Add most important turns
        important_turns = summary.important_turns
        current_length = len(compressed_parts[0].split())  # Rough token count

        for turn in important_turns:
            turn_text = f"{turn.role.title()}: {turn.content}"

            # Check if we can fit this turn
            turn_length = len(turn_text.split())
            if current_length + turn_length <= max_tokens * 0.8:  # Leave room for summary
                compressed_parts.append(turn_text)
                current_length += turn_length
            else:
                break

        # Add current context window (last few turns)
        recent_turns = turns[-3:]  # Last 3 turns
        for turn in recent_turns:
            if turn not in important_turns:  # Avoid duplication
                turn_text = f"{turn.role.title()}: {turn.content}"
                turn_length = len(turn_text.split())

                if current_length + turn_length <= max_tokens:
                    compressed_parts.append(f"[Recent] {turn_text}")
                    current_length += turn_length

        compressed_text = "\n".join(compressed_parts)

        # Update compression ratio
        original_length = sum(len(turn.content.split()) for turn in turns)
        compressed_length = len(compressed_text.split())
        summary.compression_ratio = compressed_length / original_length if original_length > 0 else 1.0

        return compressed_text

    def _format_context(self, turns: List[ConversationTurn]) -> str:
        """Format selected turns into context string"""
        if not turns:
            return ""

        formatted_turns = []
        for turn in turns:
            formatted_turns.append(f"{turn.role.title()}: {turn.content}")

        return "\n".join(formatted_turns)

    def get_context_stats(self, conversation_history: List[Dict]) -> Dict:
        """Get statistics about conversation context"""
        turns = self._parse_conversation_history(conversation_history)

        total_length = sum(len(turn.content) for turn in turns)
        avg_turn_length = total_length / len(turns) if turns else 0

        # Topic diversity
        all_topics = set()
        for turn in turns:
            all_topics.update(turn.topic_keywords)

        return {
            'total_turns': len(turns),
            'total_characters': total_length,
            'average_turn_length': avg_turn_length,
            'unique_topics': len(all_topics),
            'top_topics': list(all_topics)[:10]
        }


# Global instance
_context_manager = None

def get_context_manager():
    """Get or create global context manager instance"""
    global _context_manager
    if _context_manager is None:
        _context_manager = ContextManager()
    return _context_manager

