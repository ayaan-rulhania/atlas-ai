"""
Personalization Engine - Remembers user preferences and adapts communication style.

This module provides:
- User communication style tracking (formal/casual, verbose/brief)
- Conversation preference memory
- Response length adaptation
- Topic interest tracking
- Dynamic user profile building
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple, Set, Any
import re
import time
import json
from collections import defaultdict, Counter
from pathlib import Path


class PersonalizationEngine:
    """
    Personalizes interactions based on user preferences and communication patterns.

    Learns from user interactions to adapt communication style, response length,
    and content preferences over time.
    """

    def __init__(self, persistence_file: str = "user_profiles.json", max_profile_age_days: int = 90):
        """
        Initialize the personalization engine.

        Args:
            persistence_file: File to store user profiles
            max_profile_age_days: Maximum age of profile data before cleanup
        """
        self.persistence_file = Path("chatbot") / persistence_file
        self.max_profile_age_days = max_profile_age_days
        self.max_age_seconds = max_profile_age_days * 24 * 3600

        # User profiles in memory
        self.user_profiles: Dict[str, Dict] = {}

        # Load existing profiles
        self._load_profiles()

        # Communication style indicators
        self.formal_indicators = [
            'please', 'thank you', 'excuse me', 'pardon', 'would you', 'could you',
            'i would like', 'i would appreciate', 'may i', 'kindly', 'regards'
        ]

        self.casual_indicators = [
            'hey', 'sup', 'yo', 'dude', 'man', 'cool', 'awesome', 'yeah',
            'nah', 'kinda', 'sorta', 'wanna', 'gonna', 'gotta'
        ]

        self.verbose_indicators = [
            'additionally', 'furthermore', 'moreover', 'in addition', 'besides',
            'not only', 'but also', 'as well as', 'let me explain', 'to elaborate'
        ]

        self.brief_indicators = [
            'short', 'quick', 'brief', 'concise', 'to the point', 'just', 'simply'
        ]

        # Topic interest categories
        self.topic_categories = {
            'technical': ['programming', 'code', 'software', 'hardware', 'tech', 'development'],
            'scientific': ['science', 'research', 'experiment', 'data', 'analysis'],
            'creative': ['art', 'design', 'music', 'writing', 'creative'],
            'business': ['business', 'work', 'career', 'company', 'startup'],
            'personal': ['family', 'friends', 'life', 'experience', 'personal'],
            'entertainment': ['movies', 'games', 'books', 'music', 'shows'],
            'health': ['health', 'fitness', 'exercise', 'diet', 'wellness'],
            'education': ['learning', 'study', 'course', 'knowledge', 'skill']
        }

    def get_user_key(self, chat_id: str, user_id: Optional[str] = None) -> str:
        """Generate a unique key for user identification."""
        if user_id:
            return f"{chat_id}:{user_id}"
        return f"chat:{chat_id}"

    def update_user_profile(self, user_key: str, message: str, response: str = None):
        """
        Update user profile based on message and response interaction.

        Args:
            user_key: Unique user identifier
            message: User's message
            response: Assistant's response (optional)
        """
        if user_key not in self.user_profiles:
            self.user_profiles[user_key] = {
                'created_at': time.time(),
                'last_updated': time.time(),
                'interaction_count': 0,
                'communication_style': {
                    'formality': 0.5,  # 0.0 = very casual, 1.0 = very formal
                    'verbosity': 0.5,  # 0.0 = very brief, 1.0 = very verbose
                    'confidence': 0.0  # How confident we are in these assessments
                },
                'topic_interests': defaultdict(float),
                'preferred_response_length': 'medium',  # short, medium, long
                'interaction_patterns': {
                    'greeting_preference': None,  # morning/afternoon/evening patterns
                    'response_engagement': [],  # Tracks if user continues conversation after responses
                    'topic_persistence': [],  # How long user stays on topics
                    'question_frequency': 0,  # How often user asks questions vs statements
                    'emotional_range': [],  # Track emotional states over time
                },
                'response_preferences': {
                    'technical_detail': 0.5,
                    'examples': 0.5,
                    'humor': 0.3,
                    'empathy': 0.5,
                    'structure': 0.5,  # How structured responses should be
                    'variety': 0.5,  # How much response variety to use
                    'humor': 0.3,
                    'structure': 0.5
                },
                'interaction_history': []
            }

        profile = self.user_profiles[user_key]
        profile['last_updated'] = time.time()
        profile['interaction_count'] += 1

        # Analyze communication style from message
        self._analyze_communication_style(profile, message)

        # Track topic interests
        self._analyze_topic_interests(profile, message)

        # Learn from response preferences (if response provided)
        if response:
            self._learn_from_response(profile, message, response)

        # Update interaction history (keep last 50)
        profile['interaction_history'].append({
            'timestamp': time.time(),
            'message_length': len(message.split()),
            'has_questions': '?' in message,
            'topics_detected': list(self._detect_topics(message))
        })

        if len(profile['interaction_history']) > 50:
            profile['interaction_history'] = profile['interaction_history'][-50:]

        # Save profiles periodically (every 10 interactions)
        if profile['interaction_count'] % 10 == 0:
            self._save_profiles()

    def _analyze_communication_style(self, profile: Dict, message: str):
        """Analyze and update communication style preferences."""
        message_lower = message.lower()

        # Formality analysis
        formal_count = sum(1 for indicator in self.formal_indicators if indicator in message_lower)
        casual_count = sum(1 for indicator in self.casual_indicators if indicator in message_lower)

        if formal_count + casual_count > 0:
            formality_ratio = formal_count / (formal_count + casual_count)
            # Update with weighted average
            current_formality = profile['communication_style']['formality']
            new_formality = (current_formality * 0.8) + (formality_ratio * 0.2)
            profile['communication_style']['formality'] = new_formality

        # Verbosity analysis
        word_count = len(message.split())
        avg_sentence_length = self._get_average_sentence_length(message)

        # Adjust verbosity based on message patterns
        if word_count < 5:
            verbosity_adjustment = -0.1  # Shorter messages suggest preference for brevity
        elif word_count > 20:
            verbosity_adjustment = 0.1   # Longer messages suggest tolerance for detail
        else:
            verbosity_adjustment = 0.0

        current_verbosity = profile['communication_style']['verbosity']
        new_verbosity = max(0.0, min(1.0, current_verbosity + verbosity_adjustment * 0.1))
        profile['communication_style']['verbosity'] = new_verbosity

        # Increase confidence as we get more data
        profile['communication_style']['confidence'] = min(1.0,
            profile['communication_style']['confidence'] + 0.05)

    def _get_average_sentence_length(self, text: str) -> float:
        """Calculate average sentence length in words."""
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]

        if not sentences:
            return 0.0

        total_words = sum(len(s.split()) for s in sentences)
        return total_words / len(sentences)

    def _analyze_topic_interests(self, profile: Dict, message: str):
        """Analyze and update topic interests."""
        detected_topics = self._detect_topics(message)

        for topic in detected_topics:
            # Increase interest score for detected topics
            profile['topic_interests'][topic] += 0.1

        # Decay old interests slightly
        for topic in list(profile['topic_interests'].keys()):
            profile['topic_interests'][topic] *= 0.99

    def _detect_topics(self, message: str) -> Set[str]:
        """Detect topics present in a message."""
        message_lower = message.lower()
        detected_topics = set()

        for category, keywords in self.topic_categories.items():
            for keyword in keywords:
                if keyword in message_lower:
                    detected_topics.add(category)
                    break

        return detected_topics

    def _learn_from_response(self, profile: Dict, message: str, response: str):
        """Learn user preferences from response patterns."""
        # Analyze response length preference
        response_word_count = len(response.split())

        if response_word_count < 50:
            # User might prefer concise responses
            if profile['preferred_response_length'] == 'long':
                profile['preferred_response_length'] = 'medium'
            elif profile['preferred_response_length'] == 'medium':
                profile['preferred_response_length'] = 'short'
        elif response_word_count > 150:
            # User might prefer detailed responses
            if profile['preferred_response_length'] == 'short':
                profile['preferred_response_length'] = 'medium'
            elif profile['preferred_response_length'] == 'medium':
                profile['preferred_response_length'] = 'long'

        # Learn technical detail preference
        technical_terms = ['function', 'class', 'method', 'algorithm', 'implementation']
        if any(term in response.lower() for term in technical_terms):
            profile['response_preferences']['technical_detail'] += 0.05

        # Learn example preference
        if 'example' in response.lower() or 'for instance' in response.lower():
            profile['response_preferences']['examples'] += 0.05

    def get_adapted_response_style(self, user_key: str) -> Dict:
        """
        Get recommended response style adaptations for a user.

        Returns style recommendations based on learned preferences.
        """
        if user_key not in self.user_profiles:
            return self._get_default_style()

        profile = self.user_profiles[user_key]

        # Only use preferences if we have enough confidence
        if profile['communication_style']['confidence'] < 0.3:
            return self._get_default_style()

        style = {
            'formality_level': profile['communication_style']['formality'],
            'verbosity_level': profile['communication_style']['verbosity'],
            'preferred_length': profile['preferred_response_length'],
            'technical_detail': profile['response_preferences']['technical_detail'],
            'include_examples': profile['response_preferences']['examples'] > 0.5,
            'top_interests': self._get_top_interests(profile, 3)
        }

        return style

    def _get_default_style(self) -> Dict:
        """Get default response style when no user data is available."""
        return {
            'formality_level': 0.5,
            'verbosity_level': 0.5,
            'preferred_length': 'medium',
            'technical_detail': 0.5,
            'include_examples': True,
            'top_interests': []
        }

    def _get_top_interests(self, profile: Dict, limit: int) -> List[str]:
        """Get user's top topic interests."""
        interests = profile['topic_interests']
        if not interests:
            return []

        # Sort by interest score
        sorted_interests = sorted(interests.items(), key=lambda x: x[1], reverse=True)
        return [topic for topic, score in sorted_interests[:limit] if score > 0.2]

    def adapt_response(self, base_response: str, user_key: str) -> str:
        """
        Adapt a response based on user preferences.

        Args:
            base_response: The original response
            user_key: User identifier

        Returns:
            Adapted response
        """
        if user_key not in self.user_profiles:
            return base_response

        profile = self.user_profiles[user_key]
        style = self.get_adapted_response_style(user_key)

        adapted_response = base_response

        # Adjust length based on preference
        if style['preferred_length'] == 'short' and len(adapted_response.split()) > 100:
            adapted_response = self._shorten_response(adapted_response)
        elif style['preferred_length'] == 'long' and len(adapted_response.split()) < 50:
            adapted_response = self._expand_response(adapted_response, profile)

        # Adjust formality
        formality = style['formality_level']
        if formality < 0.3:  # Very casual user
            adapted_response = self._make_more_casual(adapted_response)
        elif formality > 0.7:  # Very formal user
            adapted_response = self._make_more_formal(adapted_response)

        # Adjust technical detail
        if style['technical_detail'] > 0.7 and 'technical' not in adapted_response.lower():
            adapted_response = self._add_technical_detail(adapted_response)

        return adapted_response

    def _shorten_response(self, response: str) -> str:
        """Create a shorter version of the response."""
        sentences = re.split(r'[.!?]+', response)
        sentences = [s.strip() for s in sentences if s.strip()]

        if len(sentences) <= 2:
            return response

        # Keep the first 2-3 sentences
        return '. '.join(sentences[:2]) + '.'

    def _expand_response(self, response: str, profile: Dict) -> str:
        """Add more detail to a response for verbose users."""
        # Add a follow-up question or additional context
        expansions = [
            " Would you like me to elaborate on any part of this?",
            " Is there a specific aspect you'd like me to explain further?",
            " Let me know if you'd like more details about this topic."
        ]

        import random
        return response + random.choice(expansions)

    def _make_more_casual(self, response: str) -> str:
        """Make response more casual."""
        # Replace formal phrases with casual alternatives
        casual_replacements = {
            'I would like to': 'I wanna',
            'I would appreciate': 'I\'d love',
            'Please': 'Can you',
            'Thank you': 'Thanks',
            'Excuse me': 'Hey',
            'Pardon me': 'Oops'
        }

        casual_response = response
        for formal, casual in casual_replacements.items():
            casual_response = casual_response.replace(formal, casual)

        return casual_response

    def _make_more_formal(self, response: str) -> str:
        """Make response more formal."""
        # Replace casual phrases with formal alternatives
        formal_replacements = {
            'wanna': 'would like to',
            'gonna': 'going to',
            'kinda': 'somewhat',
            'sorta': 'somewhat',
            'yeah': 'yes',
            'nah': 'no'
        }

        formal_response = response
        for casual, formal in formal_replacements.items():
            formal_response = re.sub(r'\b' + re.escape(casual) + r'\b', formal, formal_response, flags=re.IGNORECASE)

        return formal_response

    def _add_technical_detail(self, response: str) -> str:
        """Add technical details for users who prefer them."""
        # This is a simplified version - in practice, this would be more sophisticated
        if 'code' not in response.lower() and 'function' not in response.lower():
            return response + " (For more technical details, let me know if you'd like to see the implementation.)"

        return response

    def track_user_engagement(self, user_key: str, message: str, response: str, led_to_follow_up: bool = False):
        """
        Track user engagement patterns to improve response personalization.

        Args:
            user_key: Unique user identifier
            message: User's message
            response: Assistant's response
            led_to_follow_up: Whether this response led to continued conversation
        """
        if user_key not in self.user_profiles:
            return

        profile = self.user_profiles[user_key]
        patterns = profile['interaction_patterns']

        # Track response engagement
        patterns['response_engagement'].append({
            'timestamp': time.time(),
            'response_length': len(response.split()),
            'led_to_follow_up': led_to_follow_up,
            'message_type': self._classify_message_type(message)
        })

        # Keep only recent engagement data (last 50 interactions)
        if len(patterns['response_engagement']) > 50:
            patterns['response_engagement'] = patterns['response_engagement'][-50:]

        # Track emotional state
        emotional_state = self._detect_emotional_state(message)
        if emotional_state != 'neutral':
            patterns['emotional_range'].append({
                'timestamp': time.time(),
                'emotion': emotional_state,
                'message': message[:100]
            })

            # Keep only recent emotional data
            if len(patterns['emotional_range']) > 20:
                patterns['emotional_range'] = patterns['emotional_range'][-20:]

        # Update question frequency
        if '?' in message:
            patterns['question_frequency'] = (patterns['question_frequency'] * 0.9) + 0.1  # Weighted average
        else:
            patterns['question_frequency'] = patterns['question_frequency'] * 0.9

        # Track topic persistence (simplified)
        current_topics = self._extract_topics(message)
        if current_topics:
            patterns['topic_persistence'].append({
                'timestamp': time.time(),
                'topics': current_topics
            })

            # Keep only recent topic data
            if len(patterns['topic_persistence']) > 30:
                patterns['topic_persistence'] = patterns['topic_persistence'][-30:]

    def generate_response_variations(self, user_key: str, base_responses: List[str], context: str = 'general') -> List[str]:
        """
        Generate varied responses based on user preferences and interaction history.

        Args:
            user_key: Unique user identifier
            base_responses: List of base response options
            context: Context of the response (greeting, help, etc.)

        Returns:
            List of personalized response variations
        """
        if user_key not in self.user_profiles or not base_responses:
            return base_responses

        profile = self.user_profiles[user_key]
        patterns = profile['interaction_patterns']
        preferences = profile['response_preferences']

        # Start with base responses
        varied_responses = base_responses.copy()

        # Adjust for communication style
        formality = profile['communication_style']['formality']
        verbosity = profile['communication_style']['verbosity']

        # Add variety based on user engagement patterns
        engagement_history = patterns['response_engagement']
        if len(engagement_history) >= 5:
            # Analyze what types of responses get engagement
            engaging_lengths = [e['response_length'] for e in engagement_history if e['led_to_follow_up']]
            if engaging_lengths:
                avg_engaging_length = sum(engaging_lengths) / len(engaging_lengths)

                # Adjust verbosity preference based on engagement
                if avg_engaging_length < 20 and verbosity > 0.3:
                    # User prefers shorter responses
                    preferences['variety'] = max(0.1, preferences['variety'] - 0.1)
                elif avg_engaging_length > 50 and verbosity < 0.7:
                    # User prefers longer responses
                    preferences['variety'] = min(0.9, preferences['variety'] + 0.1)

        # Add contextual variations based on emotional patterns
        emotional_history = patterns['emotional_range']
        if emotional_history:
            recent_emotions = [e['emotion'] for e in emotional_history[-5:]]  # Last 5 emotions
            most_common_emotion = max(set(recent_emotions), key=recent_emotions.count) if recent_emotions else None

            if most_common_emotion == 'frustrated':
                # Add more empathetic variations
                varied_responses.extend([
                    resp + " I understand this can be challenging - I'm here to help work through it."
                    for resp in base_responses[:2]
                ])
            elif most_common_emotion == 'excited':
                # Add enthusiastic variations
                varied_responses.extend([
                    resp + " Your enthusiasm makes this fun!"
                    for resp in base_responses[:2]
                ])

        # Add humor based on user preference (if appropriate for context)
        if preferences.get('humor', 0.3) > 0.5 and context in ['casual', 'general']:
            if random.random() < 0.3:  # 30% chance to add light humor
                humor_additions = [
                    " (Though I might need some coffee first! ☕)",
                    " (I'm just an AI, but I'll do my best! 🤖)",
                    " (Hopefully I don't crash while helping! 💻)"
                ]
                for i, resp in enumerate(varied_responses[:3]):
                    if len(resp.split()) < 30:  # Only for shorter responses
                        varied_responses.append(resp + random.choice(humor_additions))

        # Ensure we don't have too many variations (max 8)
        if len(varied_responses) > 8:
            # Keep most diverse responses
            varied_responses = varied_responses[:8]

        return varied_responses

    def _classify_message_type(self, message: str) -> str:
        """Classify the type of user message."""
        message_lower = message.lower()

        if '?' in message:
            return 'question'
        elif any(word in message_lower for word in ['thanks', 'thank you', 'appreciate']):
            return 'gratitude'
        elif any(word in message_lower for word in ['yes', 'no', 'okay', 'sure', 'alright']):
            return 'acknowledgment'
        elif len(message.split()) <= 3:
            return 'short_statement'
        else:
            return 'statement'

    def _detect_emotional_state(self, message: str) -> str:
        """Simple emotional state detection for personalization."""
        message_lower = message.lower()

        # Positive emotions
        if any(word in message_lower for word in ['great', 'awesome', 'amazing', 'excited', 'happy', 'love']):
            return 'positive'

        # Negative emotions
        if any(word in message_lower for word in ['frustrated', 'annoying', 'stuck', 'problem', 'issue', 'hate', 'angry']):
            return 'frustrated'

        # Confusion
        if any(word in message_lower for word in ['confused', 'lost', 'not sure', 'unclear', 'bewildered', 'huh']):
            return 'confused'

        # Excitement
        if any(word in message_lower for word in ['excited', 'thrilled', 'wow', 'amazing']):
            return 'excited'

        return 'neutral'

    def _extract_topics(self, message: str) -> List[str]:
        """Extract topics from message for personalization."""
        message_lower = message.lower()
        topics = []

        for category, keywords in self.topic_categories.items():
            if any(keyword in message_lower for keyword in keywords):
                topics.append(category)

        return topics

    def get_personalized_greeting(self, user_key: str) -> Optional[str]:
        """Generate a personalized greeting based on user profile."""
        if user_key not in self.user_profiles:
            return None

        profile = self.user_profiles[user_key]

        # Use top interests for personalization
        top_interests = self._get_top_interests(profile, 2)
        if top_interests:
            interest = top_interests[0]
            greetings = {
                'technical': "Ready to dive into some technical challenges?",
                'scientific': "Excited to explore some scientific questions?",
                'creative': "Ready for some creative exploration?",
                'business': "Let's tackle some business challenges together.",
                'personal': "How are you doing today?",
                'entertainment': "Ready for some fun discussion?",
                'health': "How are you feeling today?",
                'education': "Ready to learn something new?"
            }

            if interest in greetings:
                return greetings[interest]

        # Fallback based on communication style
        formality = profile['communication_style']['formality']
        if formality < 0.3:
            return "Hey! What's up?"
        elif formality > 0.7:
            return "Hello. How may I assist you today?"
        else:
            return "Hi there! How can I help?"

    def get_user_insights(self, user_key: str) -> Dict:
        """Get insights about a user's preferences and patterns."""
        if user_key not in self.user_profiles:
            return {'insights': 'No profile data available yet.'}

        profile = self.user_profiles[user_key]

        insights = {
            'interaction_count': profile['interaction_count'],
            'communication_style': 'casual' if profile['communication_style']['formality'] < 0.4 else 'formal' if profile['communication_style']['formality'] > 0.6 else 'balanced',
            'verbosity_preference': 'brief' if profile['communication_style']['verbosity'] < 0.4 else 'verbose' if profile['communication_style']['verbosity'] > 0.6 else 'moderate',
            'top_interests': self._get_top_interests(profile, 5),
            'preferred_response_length': profile['preferred_response_length'],
            'profile_confidence': profile['communication_style']['confidence']
        }

        return insights

    def _load_profiles(self):
        """Load user profiles from persistent storage."""
        try:
            if self.persistence_file.exists():
                with open(self.persistence_file, 'r') as f:
                    data = json.load(f)
                    self.user_profiles = data.get('profiles', {})

                # Clean up old profiles
                self._cleanup_old_profiles()
        except Exception as e:
            print(f"Warning: Could not load user profiles: {e}")
            self.user_profiles = {}

    def _save_profiles(self):
        """Save user profiles to persistent storage."""
        try:
            data = {
                'last_updated': time.time(),
                'profiles': self.user_profiles
            }

            self.persistence_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.persistence_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save user profiles: {e}")

    def _cleanup_old_profiles(self):
        """Remove profiles that are too old."""
        current_time = time.time()
        to_remove = []

        for user_key, profile in self.user_profiles.items():
            if current_time - profile.get('last_updated', 0) > self.max_age_seconds:
                to_remove.append(user_key)

        for user_key in to_remove:
            del self.user_profiles[user_key]


# Global instance
_personalization_engine: Optional[PersonalizationEngine] = None


def get_personalization_engine() -> PersonalizationEngine:
    """Get or create global personalization engine instance."""
    global _personalization_engine
    if _personalization_engine is None:
        _personalization_engine = PersonalizationEngine()
    return _personalization_engine
