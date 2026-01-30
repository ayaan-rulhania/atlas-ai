"""
Conversation Flow Manager - Maintains natural dialogue continuity and topic tracking.

This module provides:
- Topic tracking and transition detection
- Context maintenance across conversation turns
- Natural topic bridging suggestions
- Interruption and resumption handling
- Conversation coherence analysis
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple, Set, Any
import re
import time
from collections import defaultdict, deque


class ConversationFlowManager:
    """
    Manages conversation flow and continuity for natural dialogue.

    Tracks topics, detects transitions, maintains context, and provides
    suggestions for smooth conversation progression.
    """

    def __init__(self, max_context_memory: int = 20, topic_decay_minutes: int = 30):
        """
        Initialize the conversation flow manager.

        Args:
            max_context_memory: Maximum conversation turns to remember
            topic_decay_minutes: Minutes before topic relevance decays
        """
        self.max_context_memory = max_context_memory
        self.topic_decay_minutes = topic_decay_minutes

        # Conversation memory per chat
        self.conversation_memory: Dict[str, Dict] = {}

        # Topic keywords and categories for detection
        self.topic_categories = {
            'technology': [
                'computer', 'software', 'hardware', 'programming', 'code', 'coding',
                'programming', 'developer', 'development', 'app', 'application',
                'website', 'web', 'internet', 'online', 'digital', 'tech'
            ],
            'science': [
                'science', 'scientific', 'research', 'experiment', 'theory',
                'physics', 'chemistry', 'biology', 'mathematics', 'math',
                'data', 'analysis', 'study', 'hypothesis'
            ],
            'health': [
                'health', 'medical', 'doctor', 'medicine', 'treatment',
                'disease', 'illness', 'wellness', 'fitness', 'exercise',
                'diet', 'nutrition', 'mental health', 'therapy'
            ],
            'business': [
                'business', 'company', 'work', 'job', 'career', 'money',
                'finance', 'investment', 'market', 'economy', 'startup',
                'entrepreneur', 'management', 'strategy'
            ],
            'education': [
                'school', 'university', 'college', 'learning', 'study',
                'student', 'teacher', 'course', 'class', 'lesson', 'education',
                'knowledge', 'skill', 'training', 'academic'
            ],
            'entertainment': [
                'movie', 'film', 'music', 'song', 'game', 'gaming', 'book',
                'reading', 'art', 'artist', 'show', 'series', 'tv', 'entertainment',
                'fun', 'hobby', 'leisure'
            ],
            'personal': [
                'family', 'friend', 'relationship', 'life', 'experience',
                'feeling', 'emotion', 'personal', 'private', 'home'
            ],
            'travel': [
                'travel', 'trip', 'vacation', 'journey', 'destination',
                'place', 'location', 'country', 'city', 'tourism'
            ],
            'food': [
                'food', 'cooking', 'recipe', 'meal', 'restaurant', 'eat',
                'drink', 'cuisine', 'ingredient', 'dish', 'dining'
            ],
            'sports': [
                'sport', 'game', 'team', 'player', 'athlete', 'competition',
                'match', 'tournament', 'championship', 'fitness', 'exercise'
            ]
        }

        # Transition phrases for smooth topic changes
        self.transition_phrases = {
            'related_shift': [
                "Speaking of which...", "That reminds me...", "On a related note...",
                "This connects to...", "Building on that idea...", "Similarly..."
            ],
            'contrast_shift': [
                "On the other hand...", "In contrast...", "However...", "But speaking of...",
                "That said...", "Alternatively..."
            ],
            'question_shift': [
                "By the way, have you thought about...", "Speaking of questions...",
                "That makes me wonder about...", "This brings up..."
            ],
            'time_shift': [
                "Moving on to...", "Let's talk about...", "Now, regarding...",
                "Next, let's consider...", "Another aspect is..."
            ]
        }

    def get_conversation_key(self, chat_id: str, user_id: Optional[str] = None) -> str:
        """Generate a unique key for conversation tracking."""
        key_parts = [chat_id]
        if user_id:
            key_parts.append(user_id)
        return '|'.join(key_parts)

    def update_conversation_context(self, conversation_key: str, user_message: str, assistant_message: str = None):
        """
        Update conversation context with new messages.

        Args:
            conversation_key: Unique conversation identifier
            user_message: The user's message
            assistant_message: The assistant's response (optional)
        """
        if conversation_key not in self.conversation_memory:
            self.conversation_memory[conversation_key] = {
                'turns': deque(maxlen=self.max_context_memory),
                'current_topics': set(),
                'topic_history': [],
                'last_activity': time.time(),
                'conversation_flow': [],
                'interruption_state': None
            }

        memory = self.conversation_memory[conversation_key]

        # Add new turn
        turn = {
            'timestamp': time.time(),
            'user_message': user_message,
            'assistant_message': assistant_message,
            'detected_topics': self._detect_topics(user_message),
            'turn_number': len(memory['turns']) + 1
        }

        memory['turns'].append(turn)
        memory['last_activity'] = time.time()

        # Update current topics
        current_topics = set()
        for turn_data in list(memory['turns'])[-3:]:  # Last 3 turns
            current_topics.update(turn_data['detected_topics'])

        # Decay old topics
        current_time = time.time()
        active_topics = set()
        for topic in current_topics:
            # Find most recent mention of this topic
            recent_mention = 0
            for turn_data in memory['turns']:
                if topic in turn_data['detected_topics']:
                    recent_mention = max(recent_mention, turn_data['timestamp'])

            # Keep topic if mentioned within decay period
            if current_time - recent_mention < (self.topic_decay_minutes * 60):
                active_topics.add(topic)

        memory['current_topics'] = active_topics

        # Track topic transitions
        if len(memory['turns']) >= 2:
            prev_turn = memory['turns'][-2]
            current_turn = memory['turns'][-1]

            prev_topics = prev_turn['detected_topics']
            curr_topics = current_turn['detected_topics']

            if prev_topics and curr_topics and not prev_topics.intersection(curr_topics):
                # Topic change detected
                transition = {
                    'from_topics': list(prev_topics),
                    'to_topics': list(curr_topics),
                    'transition_type': self._classify_transition(prev_topics, curr_topics),
                    'turn_number': len(memory['turns'])
                }
                memory['conversation_flow'].append(transition)

    def _detect_topics(self, message: str) -> Set[str]:
        """Detect topics present in a message."""
        message_lower = message.lower()
        detected_topics = set()

        # Check each topic category
        for category, keywords in self.topic_categories.items():
            for keyword in keywords:
                if keyword in message_lower:
                    detected_topics.add(category)
                    break  # Only add category once

        # Check for specific named entities (simplified)
        # In a full implementation, this would use NER
        if re.search(r'\b(python|javascript|java|c\+\+|programming)\b', message_lower):
            detected_topics.add('programming')

        return detected_topics

    def _classify_transition(self, from_topics: Set[str], to_topics: Set[str]) -> str:
        """Classify the type of topic transition."""
        # Check for related transitions
        related_categories = {
            'technology': ['science', 'business'],
            'science': ['technology', 'education'],
            'business': ['technology', 'education'],
            'education': ['science', 'technology'],
            'health': ['science', 'personal'],
            'personal': ['health', 'entertainment'],
            'entertainment': ['personal', 'travel']
        }

        for from_topic in from_topics:
            if from_topic in related_categories:
                if to_topics.intersection(set(related_categories[from_topic])):
                    return 'related'

        # Check for contrast (opposite topics)
        contrast_pairs = [('work', 'leisure'), ('serious', 'fun'), ('professional', 'personal')]

        # If no clear relationship, it's a shift
        return 'shift'

    def get_topic_continuity_score(self, conversation_key: str) -> float:
        """
        Calculate how well the conversation maintains topic continuity.

        Returns a score from 0.0 (no continuity) to 1.0 (perfect continuity).
        """
        if conversation_key not in self.conversation_memory:
            return 0.0

        memory = self.conversation_memory[conversation_key]
        turns = list(memory['turns'])

        if len(turns) < 2:
            return 1.0  # Single turn has perfect continuity

        continuity_score = 0.0
        transitions = 0

        for i in range(1, len(turns)):
            prev_topics = turns[i-1]['detected_topics']
            curr_topics = turns[i]['detected_topics']

            if prev_topics and curr_topics:
                overlap = len(prev_topics.intersection(curr_topics))
                union = len(prev_topics.union(curr_topics))
                if union > 0:
                    turn_continuity = overlap / union
                    continuity_score += turn_continuity
                    transitions += 1

        return continuity_score / max(transitions, 1)

    def suggest_topic_bridge(self, conversation_key: str, new_topic: str) -> Optional[str]:
        """
        Suggest a natural transition phrase to bridge to a new topic.

        Returns a transition phrase or None if no bridge needed.
        """
        if conversation_key not in self.conversation_memory:
            return None

        memory = self.conversation_memory[conversation_key]

        if not memory['current_topics']:
            return None  # No current topics to bridge from

        current_topics = memory['current_topics']

        # Determine transition type
        transition_type = 'time_shift'  # Default

        # Check if new topic is related to current topics
        if new_topic in current_topics:
            return None  # No bridge needed for same topic

        # Check for related topics
        for topic in current_topics:
            if self._topics_are_related(topic, new_topic):
                transition_type = 'related_shift'
                break

        # Get appropriate transition phrase
        if transition_type in self.transition_phrases:
            return self.transition_phrases[transition_type][0]  # Return first option

        return None

    def _topics_are_related(self, topic1: str, topic2: str) -> bool:
        """Check if two topics are related."""
        related_pairs = [
            ('technology', 'science'),
            ('technology', 'business'),
            ('science', 'education'),
            ('health', 'personal'),
            ('business', 'education'),
            ('entertainment', 'personal'),
            ('travel', 'entertainment')
        ]

        return (topic1, topic2) in related_pairs or (topic2, topic1) in related_pairs

    def detect_interruption(self, conversation_key: str, user_message: str) -> Optional[Dict]:
        """
        Detect if the user message indicates an interruption or change of direction.

        Returns interruption details or None.
        """
        if conversation_key not in self.conversation_memory:
            return None

        message_lower = user_message.lower()

        # Interruption indicators
        interruption_patterns = [
            r'\b(wait|hold on|stop|never mind)\b',
            r'\bactually\b.*\b(i|we)\b',
            r'\bon second thought\b',
            r'\bi meant\b',
            r'\bi forgot\b',
            r'\bby the way\b',
            r'\boh wait\b'
        ]

        for pattern in interruption_patterns:
            if re.search(pattern, message_lower):
                return {
                    'type': 'interruption',
                    'reason': 'user_correction' if 'actually' in message_lower or 'i meant' in message_lower else 'topic_change',
                    'confidence': 0.8
                }

        # Sudden topic changes
        memory = self.conversation_memory[conversation_key]
        current_topics = memory['current_topics']
        message_topics = self._detect_topics(user_message)

        if current_topics and message_topics and not current_topics.intersection(message_topics):
            # Check if this is a natural transition or abrupt change
            if len(memory['turns']) >= 2:
                return {
                    'type': 'topic_shift',
                    'from_topics': list(current_topics),
                    'to_topics': list(message_topics),
                    'confidence': 0.6
                }

        return None

    def handle_resumption(self, conversation_key: str, user_message: str) -> Optional[str]:
        """
        Handle conversation resumption after interruption.

        Returns a resumption phrase if appropriate.
        """
        memory = self.conversation_memory.get(conversation_key)
        if not memory or not memory['turns']:
            return None

        # Check if user is resuming a previous topic
        message_lower = user_message.lower()
        resumption_indicators = [
            'going back to', 'as i was saying', 'anyway', 'so anyway',
            'where was i', 'continuing', 'back to'
        ]

        for indicator in resumption_indicators:
            if indicator in message_lower:
                return "Yes, let's continue with that."

        # Check if user is referring to previous context
        recent_turns = list(memory['turns'])[-3:]  # Last 3 turns
        for turn in recent_turns:
            if turn['assistant_message']:
                # Simple check for references to previous response
                if any(word in message_lower for word in ['that', 'it', 'this', 'those']):
                    return "Glad you want to continue with that."

        return None

    def get_conversation_summary(self, conversation_key: str) -> Dict:
        """
        Get a summary of the conversation flow and topics.

        Returns conversation statistics and insights.
        """
        if conversation_key not in self.conversation_memory:
            return {'turns': 0, 'topics': [], 'continuity_score': 0.0}

        memory = self.conversation_memory[conversation_key]
        turns = list(memory['turns'])

        # Count topic frequency
        topic_counts = defaultdict(int)
        for turn in turns:
            for topic in turn['detected_topics']:
                topic_counts[topic] += 1

        # Get main topics (mentioned in at least 20% of turns)
        min_mentions = max(1, len(turns) // 5)
        main_topics = [topic for topic, count in topic_counts.items() if count >= min_mentions]

        return {
            'total_turns': len(turns),
            'main_topics': main_topics,
            'topic_distribution': dict(topic_counts),
            'continuity_score': self.get_topic_continuity_score(conversation_key),
            'transitions': len(memory['conversation_flow']),
            'last_activity_minutes': (time.time() - memory['last_activity']) / 60
        }

    def suggest_follow_up(self, conversation_key: str) -> Optional[str]:
        """
        Suggest a natural follow-up based on conversation context.

        Returns a follow-up question or topic suggestion.
        """
        if conversation_key not in self.conversation_memory:
            return None

        memory = self.conversation_memory[conversation_key]
        current_topics = memory['current_topics']

        if not current_topics:
            return None

        # Topic-based follow-ups
        topic_follow_ups = {
            'technology': [
                "Have you tried any new tools or frameworks recently?",
                "What's your favorite programming language and why?",
                "Are you working on any interesting projects?"
            ],
            'science': [
                "What's the most fascinating scientific discovery you've heard about recently?",
                "Do you have a favorite field of science?",
                "How do you think technology will change scientific research?"
            ],
            'business': [
                "What's your experience with entrepreneurship?",
                "How do you think AI will impact business?",
                "What's the most interesting company you've learned about recently?"
            ],
            'personal': [
                "What's something you're looking forward to?",
                "How has your week been going?",
                "What's a hobby or interest you're passionate about?"
            ]
        }

        for topic in current_topics:
            if topic in topic_follow_ups:
                return random.choice(topic_follow_ups[topic])

        return None

    def analyze_context_for_response(self, conversation_key: str, current_message: str) -> Dict:
        """
        Analyze conversation context to provide insights for response selection.

        Returns context analysis including:
        - User's current emotional state
        - Recent topics of interest
        - Response patterns and preferences
        - Conversation flow indicators
        """
        if conversation_key not in self.conversation_memory:
            return {
                'emotional_state': 'neutral',
                'recent_topics': [],
                'response_preference': 'balanced',
                'conversation_flow': 'new',
                'context_available': False
            }

        memory = self.conversation_memory[conversation_key]
        turns = list(memory['turns'])

        if not turns:
            return {
                'emotional_state': 'neutral',
                'recent_topics': [],
                'response_preference': 'balanced',
                'conversation_flow': 'new',
                'context_available': False
            }

        # Analyze recent emotional state
        emotional_state = self._analyze_emotional_state(turns[-3:])  # Last 3 turns

        # Get recent topics
        recent_topics = memory.get('current_topics', [])

        # Analyze response preferences based on conversation history
        response_preference = self._analyze_response_preferences(turns)

        # Determine conversation flow state
        conversation_flow = self._analyze_conversation_flow(turns, current_message)

        # Check for follow-up patterns
        is_follow_up = self._detect_follow_up_pattern(current_message, turns)

        return {
            'emotional_state': emotional_state,
            'recent_topics': list(recent_topics),
            'response_preference': response_preference,
            'conversation_flow': conversation_flow,
            'is_follow_up': is_follow_up,
            'context_available': True,
            'conversation_length': len(turns)
        }

    def _analyze_emotional_state(self, recent_turns: list) -> str:
        """Analyze the user's emotional state from recent messages"""
        if not recent_turns:
            return 'neutral'

        emotional_indicators = {
            'frustrated': ['frustrated', 'annoying', 'stuck', 'problem', 'issue', 'not working'],
            'excited': ['excited', 'amazing', 'fantastic', 'awesome', 'thrilled', 'great'],
            'confused': ['confused', 'lost', 'not sure', 'unclear', 'bewildered', 'huh'],
            'tired': ['tired', 'exhausted', 'drained', 'long day', 'worn out'],
            'satisfied': ['good', 'nice', 'cool', 'awesome', 'helpful', 'useful', 'great'],
            'curious': ['interesting', 'wonder', 'curious', 'fascinating', 'want to know']
        }

        emotional_scores = {emotion: 0 for emotion in emotional_indicators.keys()}

        for turn in recent_turns:
            message = turn.get('user_message', '').lower()
            for emotion, indicators in emotional_indicators.items():
                for indicator in indicators:
                    if indicator in message:
                        emotional_scores[emotion] += 1

        # Return the emotion with the highest score, or neutral if none detected
        if max(emotional_scores.values()) > 0:
            return max(emotional_scores, key=emotional_scores.get)
        return 'neutral'

    def _analyze_response_preferences(self, turns: list) -> str:
        """Analyze what type of responses the user seems to prefer"""
        if len(turns) < 3:
            return 'balanced'

        # Analyze assistant responses to see what works well
        assistant_responses = [turn.get('assistant_message', '') for turn in turns if turn.get('assistant_message')]

        if not assistant_responses:
            return 'balanced'

        # Simple heuristics based on response patterns
        short_responses = sum(1 for resp in assistant_responses if len(resp.split()) < 20)
        long_responses = sum(1 for resp in assistant_responses if len(resp.split()) > 50)

        if short_responses > long_responses * 1.5:
            return 'concise'
        elif long_responses > short_responses * 1.5:
            return 'detailed'
        else:
            return 'balanced'

    def _analyze_conversation_flow(self, turns: list, current_message: str) -> str:
        """Analyze the current state of conversation flow"""
        if len(turns) <= 1:
            return 'starting'

        # Check if conversation is building on previous topics
        recent_topics = set()
        for turn in turns[-3:]:
            recent_topics.update(turn.get('detected_topics', []))

        current_topics = self._detect_topics(current_message)

        if recent_topics.intersection(current_topics):
            return 'continuing_topic'
        elif current_topics:
            return 'topic_shift'
        else:
            return 'general_chat'

    def _detect_follow_up_pattern(self, current_message: str, turns: list) -> bool:
        """Detect if current message is following up on previous conversation"""
        if not turns:
            return False

        message_lower = current_message.lower()
        follow_up_indicators = [
            'that', 'it', 'this', 'those', 'them', 'there',
            'what about', 'tell me more', 'and', 'also', 'so'
        ]

        has_referential_words = any(indicator in message_lower for indicator in follow_up_indicators)
        short_message = len(current_message.split()) <= 5

        return has_referential_words and short_message

    def cleanup_old_conversations(self, max_age_hours: int = 24):
        """Clean up conversations that haven't been active for too long."""
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600

        to_remove = []
        for key, memory in self.conversation_memory.items():
            if current_time - memory['last_activity'] > max_age_seconds:
                to_remove.append(key)

        for key in to_remove:
            del self.conversation_memory[key]


# Global instance
_conversation_flow_manager: Optional[ConversationFlowManager] = None


def get_conversation_flow_manager() -> ConversationFlowManager:
    """Get or create global conversation flow manager instance."""
    global _conversation_flow_manager
    if _conversation_flow_manager is None:
        _conversation_flow_manager = ConversationFlowManager()
    return _conversation_flow_manager
