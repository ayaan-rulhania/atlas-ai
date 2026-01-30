"""
Response Variety Manager - Ensures natural conversation flow by tracking and rotating response patterns.

This module prevents repetitive responses by:
- Tracking recent response patterns per conversation
- Rotating through response variations
- Maintaining context-aware response selection
- Avoiding repetitive phrases within conversation sessions
"""

from __future__ import annotations

from typing import Dict, List, Optional, Set, Tuple
import time
import hashlib


class ResponseVarietyManager:
    """
    Manages response variety to prevent repetitive conversations.

    Tracks response patterns and ensures natural variety in conversations
    by rotating through different response styles and avoiding repetition.
    """

    def __init__(self, max_memory: int = 10, variety_window: int = 5):
        """
        Initialize the response variety manager.

        Args:
            max_memory: Maximum number of conversations to track
            variety_window: Number of recent responses to consider for variety
        """
        self.max_memory = max_memory
        self.variety_window = variety_window

        # Track response patterns per conversation
        self.conversation_memory: Dict[str, List[Dict]] = {}

        # Response pattern categories and their variations
        self.response_patterns = {
            'greeting': {
                'variations': [
                    'hello', 'hi', 'hey', 'good morning', 'good afternoon',
                    'good evening', 'welcome', 'nice to see you'
                ],
                'cooldown_period': 3  # Don't repeat greeting patterns too frequently
            },
            'acknowledgment': {
                'variations': [
                    'got it', 'understood', 'i see', 'makes sense', 'noted',
                    'roger', 'copy that', 'alright', 'okay', 'sure'
                ],
                'cooldown_period': 2
            },
            'agreement': {
                'variations': [
                    'exactly', 'absolutely', 'totally', 'definitely', 'you bet',
                    'spot on', 'correct', 'right', 'yes', 'indeed'
                ],
                'cooldown_period': 2
            },
            'question': {
                'variations': [
                    'what do you think', 'how about', 'would you like',
                    'shall we', 'what if', 'have you considered'
                ],
                'cooldown_period': 4
            },
            'transition': {
                'variations': [
                    'speaking of', 'that reminds me', 'on another note',
                    'interestingly', 'by the way', 'additionally'
                ],
                'cooldown_period': 3
            },
            'empathy': {
                'variations': [
                    'i understand', 'that makes sense', 'i can see why',
                    'that\'s completely normal', 'i hear you', 'i get it'
                ],
                'cooldown_period': 2
            },
            'enthusiasm': {
                'variations': [
                    'that\'s great', 'fantastic', 'wonderful', 'excellent',
                    'awesome', 'amazing', 'brilliant', 'perfect'
                ],
                'cooldown_period': 2
            }
        }

        # Global pattern tracking to avoid repetition across conversations
        self.global_pattern_usage: Dict[str, float] = {}

    def get_conversation_key(self, chat_id: str, user_id: Optional[str] = None) -> str:
        """Generate a unique key for conversation tracking."""
        key_parts = [chat_id]
        if user_id:
            key_parts.append(user_id)
        return hashlib.md5('|'.join(key_parts).encode()).hexdigest()[:8]

    def record_response(self, conversation_key: str, response_text: str, response_type: str = 'general'):
        """
        Record a response to track usage patterns.

        Args:
            conversation_key: Unique conversation identifier
            response_text: The actual response text
            response_type: Category of response (greeting, acknowledgment, etc.)
        """
        if conversation_key not in self.conversation_memory:
            self.conversation_memory[conversation_key] = []

        # Clean up old memory if needed
        if len(self.conversation_memory) > self.max_memory:
            # Remove oldest conversation (simple LRU)
            oldest_key = min(
                self.conversation_memory.keys(),
                key=lambda k: self.conversation_memory[k][-1]['timestamp'] if self.conversation_memory[k] else 0
            )
            del self.conversation_memory[oldest_key]

        # Limit memory per conversation
        conversation_history = self.conversation_memory[conversation_key]
        if len(conversation_history) >= self.variety_window * 2:
            conversation_history[:] = conversation_history[-self.variety_window:]

        # Record this response
        response_record = {
            'text': response_text,
            'type': response_type,
            'timestamp': time.time(),
            'patterns_used': self._extract_patterns(response_text)
        }

        conversation_history.append(response_record)

        # Update global pattern usage
        for pattern in response_record['patterns_used']:
            self.global_pattern_usage[pattern] = time.time()

    def _extract_patterns(self, response_text: str) -> List[str]:
        """Extract response patterns from text."""
        text_lower = response_text.lower()
        patterns_found = []

        for category, data in self.response_patterns.items():
            for variation in data['variations']:
                if variation in text_lower:
                    patterns_found.append(f"{category}:{variation}")
                    break  # Only record one variation per category

        return patterns_found

    def get_variety_score(self, conversation_key: str, proposed_response: str, response_type: str = 'general') -> float:
        """
        Calculate how varied this response would be compared to recent responses.

        Returns a score from 0.0 (very repetitive) to 1.0 (very varied).
        """
        if conversation_key not in self.conversation_memory:
            return 1.0  # No history, so it's varied by default

        conversation_history = self.conversation_memory[conversation_key]
        if not conversation_history:
            return 1.0

        # Check recent patterns
        recent_patterns = set()
        cutoff_time = time.time() - (60 * 5)  # Last 5 minutes

        for record in conversation_history[-self.variety_window:]:
            if record['timestamp'] > cutoff_time:
                recent_patterns.update(record['patterns_used'])

        proposed_patterns = set(self._extract_patterns(proposed_response))

        # Calculate overlap
        overlap = len(recent_patterns.intersection(proposed_patterns))
        total_patterns = len(proposed_patterns) or 1

        # Lower score means more repetitive
        repetition_penalty = overlap / total_patterns

        # Also check for exact text matches
        exact_matches = sum(1 for record in conversation_history[-3:]
                          if record['text'].lower().strip() == proposed_response.lower().strip())

        exact_penalty = min(exact_matches * 0.3, 0.5)  # Max 50% penalty for exact matches

        return max(0.0, 1.0 - repetition_penalty - exact_penalty)

    def suggest_alternative(self, conversation_key: str, response_type: str, current_response: str) -> Optional[str]:
        """
        Suggest an alternative response if the current one would be too repetitive.

        Returns None if current response is fine, or an alternative response suggestion.
        """
        variety_score = self.get_variety_score(conversation_key, current_response, response_type)

        if variety_score > 0.6:  # Good enough variety
            return None

        # Find alternative patterns that haven't been used recently
        if response_type in self.response_patterns:
            category_data = self.response_patterns[response_type]
            cooldown_period = category_data['cooldown_period']

            # Check which variations haven't been used recently
            available_variations = []
            for variation in category_data['variations']:
                pattern_key = f"{response_type}:{variation}"
                last_used = self.global_pattern_usage.get(pattern_key, 0)
                if time.time() - last_used > (cooldown_period * 60):  # Convert to seconds
                    available_variations.append(variation)

            if available_variations:
                # Return a template suggestion (not full response)
                return f"Try using: {available_variations[0]}"

        return None

    def get_response_style_suggestion(self, conversation_key: str) -> str:
        """
        Suggest a response style based on conversation history.

        Returns style suggestions like 'more_enthusiastic', 'more_concise', 'more_empathic', etc.
        """
        if conversation_key not in self.conversation_memory:
            return 'balanced'

        history = self.conversation_memory[conversation_key]
        if len(history) < 3:
            return 'balanced'

        # Analyze recent response patterns
        recent_types = [record['type'] for record in history[-5:]]

        # Check for repetitive patterns
        if recent_types.count('acknowledgment') > 3:
            return 'more_engaged'
        elif recent_types.count('question') > 3:
            return 'more_statement_based'
        elif recent_types.count('general') > 4:
            return 'more_varied'

        # Check emotional balance
        emotional_responses = sum(1 for t in recent_types if t in ['empathy', 'enthusiasm'])
        if emotional_responses < 1:
            return 'more_empathic'

        return 'balanced'

    def reset_conversation(self, conversation_key: str):
        """Reset memory for a specific conversation."""
        if conversation_key in self.conversation_memory:
            self.conversation_memory[conversation_key] = []

    def get_conversation_stats(self, conversation_key: str) -> Dict:
        """Get statistics about response variety for a conversation."""
        if conversation_key not in self.conversation_memory:
            return {'total_responses': 0, 'unique_patterns': 0, 'variety_score': 1.0}

        history = self.conversation_memory[conversation_key]

        all_patterns = set()
        for record in history:
            all_patterns.update(record['patterns_used'])

        recent_responses = history[-self.variety_window:]
        if len(recent_responses) >= 2:
            # Calculate average variety score for recent responses
            scores = []
            for i, record in enumerate(recent_responses[1:], 1):
                score = self.get_variety_score(conversation_key, record['text'], record['type'])
                scores.append(score)

            avg_variety = sum(scores) / len(scores) if scores else 1.0
        else:
            avg_variety = 1.0

        return {
            'total_responses': len(history),
            'unique_patterns': len(all_patterns),
            'variety_score': avg_variety,
            'most_used_type': max(set(record['type'] for record in history), key=lambda x: sum(1 for r in history if r['type'] == x)) if history else 'none'
        }


# Global instance
_variety_manager: Optional[ResponseVarietyManager] = None


def get_response_variety_manager() -> ResponseVarietyManager:
    """Get or create global response variety manager instance."""
    global _variety_manager
    if _variety_manager is None:
        _variety_manager = ResponseVarietyManager()
    return _variety_manager
