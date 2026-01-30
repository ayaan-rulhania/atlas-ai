"""
Emotional Intelligence Module - Detects and responds to user emotions with empathy.

This module provides:
- Emotion detection from text (happy, sad, frustrated, excited, confused, etc.)
- Empathetic response generation based on detected emotions
- Tone matching to user's emotional state
- Celebration and encouragement responses
- Supportive responses for negative emotions
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple, Set
import re
import random


class EmotionalIntelligence:
    """
    Handles emotional intelligence for more empathetic and natural conversations.

    Analyzes user messages for emotional content and generates appropriate
    empathetic responses to create better rapport and understanding.
    """

    def __init__(self):
        # Emotion detection patterns with keywords and intensity markers
        self.emotion_patterns = {
            'joy': {
                'keywords': [
                    'happy', 'excited', 'thrilled', 'delighted', 'overjoyed',
                    'ecstatic', 'wonderful', 'fantastic', 'amazing', 'awesome',
                    'great', 'excellent', 'brilliant', 'perfect', 'love it'
                ],
                'intensifiers': ['so', 'really', 'very', 'extremely', 'totally', 'absolutely'],
                'context_words': ['yay', 'woo', 'hooray', 'celebrate', 'success', 'achievement']
            },
            'frustration': {
                'keywords': [
                    'frustrated', 'annoying', 'stuck', 'problem', 'issue',
                    'not working', 'broken', 'failed', 'error', 'wrong',
                    'terrible', 'awful', 'horrible', 'ridiculous', 'stupid'
                ],
                'intensifiers': ['so', 'really', 'very', 'extremely', 'totally'],
                'context_words': ['ugh', 'argh', 'damn', 'crap', 'shit', 'sucks']
            },
            'confusion': {
                'keywords': [
                    'confused', 'lost', 'don\'t understand', 'not sure',
                    'unclear', 'bewildered', 'puzzled', 'mystified', 'baffled'
                ],
                'intensifiers': ['really', 'very', 'completely', 'totally'],
                'context_words': ['huh', 'what', 'wait', 'how', 'why']
            },
            'sadness': {
                'keywords': [
                    'sad', 'disappointed', 'upset', 'unhappy', 'depressed',
                    'down', 'blue', 'heartbroken', 'devastated', 'sorry'
                ],
                'intensifiers': ['so', 'really', 'very', 'deeply', 'terribly'],
                'context_words': ['unfortunately', 'regret', 'wish', 'if only']
            },
            'anger': {
                'keywords': [
                    'angry', 'mad', 'furious', 'irritated', 'annoyed',
                    'pissed', 'rage', 'hate', 'disgusted', 'outraged'
                ],
                'intensifiers': ['so', 'really', 'very', 'extremely', 'absolutely'],
                'context_words': ['damn', 'hell', 'stupid', 'idiot', 'moron']
            },
            'fear': {
                'keywords': [
                    'scared', 'afraid', 'worried', 'anxious', 'nervous',
                    'terrified', 'frightened', 'panic', 'dread', 'concerned'
                ],
                'intensifiers': ['so', 'really', 'very', 'extremely', 'terribly'],
                'context_words': ['what if', 'afraid of', 'worried about', 'scary']
            },
            'surprise': {
                'keywords': [
                    'surprised', 'shocked', 'amazed', 'astonished', 'stunned',
                    'unexpected', 'wow', 'oh my', 'incredible', 'unbelievable'
                ],
                'intensifiers': ['so', 'really', 'very', 'completely', 'totally'],
                'context_words': ['wow', 'oh', 'gosh', 'goodness', 'heavens']
            },
            'gratitude': {
                'keywords': [
                    'thankful', 'grateful', 'appreciative', 'thank you',
                    'thanks', 'appreciate', 'gratitude', 'blessed'
                ],
                'intensifiers': ['so', 'really', 'very', 'deeply', 'truly'],
                'context_words': ['means a lot', 'thankful for', 'grateful for']
            },
            'pride': {
                'keywords': [
                    'proud', 'accomplished', 'achievement', 'success',
                    'accomplished', 'proud of', 'well done', 'victory'
                ],
                'intensifiers': ['so', 'really', 'very', 'extremely', 'incredibly'],
                'context_words': ['finally', 'after all', 'accomplished', 'succeeded']
            },
            'tiredness': {
                'keywords': [
                    'tired', 'exhausted', 'drained', 'worn out', 'fatigued',
                    'sleepy', 'weary', 'beat', 'pooped', 'run down'
                ],
                'intensifiers': ['so', 'really', 'very', 'extremely', 'completely'],
                'context_words': ['long day', 'need rest', 'worn out', 'drained']
            },
            'hope': {
                'keywords': [
                    'hope', 'optimistic', 'looking forward', 'excited for',
                    'can\'t wait', 'anticipating', 'eager', 'positive'
                ],
                'intensifiers': ['so', 'really', 'very', 'truly', 'genuinely'],
                'context_words': ['hopefully', 'fingers crossed', 'wish', 'dream']
            }
        }

        # Empathetic response templates organized by emotion
        self.empathy_responses = {
            'joy': [
                "I can hear your excitement! That sounds absolutely wonderful.",
                "Your enthusiasm is contagious! I'm so happy for you.",
                "That sounds fantastic! Tell me more about what's making you so happy.",
                "I love hearing that kind of energy! What's got you so thrilled?",
                "Wonderful! Your joy is palpable. What's the great news?",
                "That's absolutely fantastic! I can feel your happiness from here."
            ],
            'frustration': [
                "I can tell this is really frustrating. Let's work through this together.",
                "I understand how frustrating that can be. I'm here to help you figure it out.",
                "That sounds incredibly frustrating. Don't worry, we'll get this sorted.",
                "I hear you - technology can be so maddening sometimes. Let's troubleshoot this.",
                "That's definitely frustrating when things don't work as expected. I'm here to help.",
                "I can see why that would be frustrating. Let's break this down and solve it."
            ],
            'confusion': [
                "It's completely okay to feel confused about this. Let's clarify together.",
                "I understand this can be confusing. Let me explain it differently.",
                "Don't worry if it's confusing - many people feel the same way. Let's go through it.",
                "That's a normal reaction when things are unclear. I'm here to help clear it up.",
                "It's fine to be confused. Let's break this down into simpler terms.",
                "I get that this can be puzzling. Let me walk you through it step by step."
            ],
            'sadness': [
                "I'm really sorry you're feeling this way. I'm here for you.",
                "That sounds really difficult. I wish I could help make it better.",
                "I can hear how much this is affecting you. What's on your mind?",
                "I'm here to listen if you want to talk about what's troubling you.",
                "That sounds really tough. How can I support you right now?",
                "I understand this is a difficult time. I'm here whenever you need to talk."
            ],
            'anger': [
                "I can sense your frustration. Let's take a breath and work through this.",
                "I understand you're upset about this. I'm here to help you navigate it.",
                "That sounds really aggravating. What specifically is bothering you?",
                "I hear your anger - it's valid. How can I help you with this situation?",
                "I can tell this has you really upset. Let's figure out the best way forward.",
                "That's understandably frustrating. I'm here to help you through this."
            ],
            'fear': [
                "I can tell this is worrying you. You're not alone in this.",
                "It's normal to feel anxious about uncertain situations. What concerns you most?",
                "I understand this feels scary. Let's talk through what's worrying you.",
                "Your feelings are completely valid. What aspects are you most concerned about?",
                "I hear your worry. Sometimes talking through fears can help. What's on your mind?",
                "It's okay to feel apprehensive. I'm here to help you work through this."
            ],
            'surprise': [
                "Wow! That sounds completely unexpected. Tell me more!",
                "That's quite surprising! What happened?",
                "I can hear your surprise! This sounds like quite a story.",
                "That's unexpected! I'm intrigued - what led to this?",
                "Wow, that's surprising! How did that come about?",
                "I can tell this caught you off guard. What's the full story?"
            ],
            'gratitude': [
                "You're so welcome! I'm truly glad I could help.",
                "I'm touched by your gratitude. It means a lot that I could assist you.",
                "You're very welcome! I'm happy I could make a positive difference.",
                "I'm grateful for your kind words. I'm always here to help.",
                "That's very sweet of you to say. I'm glad I could be useful.",
                "You're welcome! It warms my heart to know I could help."
            ],
            'pride': [
                "That's absolutely fantastic! You should be incredibly proud of this achievement.",
                "What an accomplishment! Your hard work has clearly paid off beautifully.",
                "I'm so impressed! This is definitely something to celebrate and be proud of.",
                "That's wonderful! You've clearly put in the effort and it shows. Congratulations!",
                "What a great achievement! I'm thrilled for you and your success.",
                "That's amazing! Your dedication and effort have led to something truly special."
            ],
            'tiredness': [
                "I can tell you're feeling exhausted. Take all the time you need.",
                "It's completely understandable to feel drained. Rest is important.",
                "You sound like you need some rest. I'm here whenever you're ready.",
                "I hear you - everyone needs a break sometimes. Take care of yourself.",
                "It's okay to feel worn out. I'm here when you have more energy.",
                "Rest is so important. I'm not going anywhere - we can continue when you're refreshed."
            ],
            'hope': [
                "I love hearing that optimism! It's wonderful to look forward to things.",
                "Your hope and positivity are inspiring. What's got you feeling so positive?",
                "That's a great attitude! Looking forward to good things is so important.",
                "I can hear your hopeful spirit. That's such a positive way to approach things.",
                "What wonderful anticipation! It's great to have things to look forward to.",
                "Your optimism is contagious! What's making you feel so hopeful?"
            ]
        }

        # Celebration responses for achievements and successes
        self.celebration_responses = [
            "🎉 That's absolutely fantastic! You deserve to celebrate this achievement!",
            "🎊 Congratulations! This is a huge win - time to celebrate!",
            "🏆 What an incredible accomplishment! I'm so proud of you!",
            "🌟 That's amazing! Your hard work has paid off beautifully!",
            "🎈 Congratulations! This success deserves some serious celebration!",
            "⭐ Brilliant work! You've earned this moment of celebration!",
            "🎯 Perfect! You've hit the mark. This is definitely worth celebrating!",
            "🏅 Outstanding! This achievement is something to be truly proud of!",
            "🎊 Wow! This is a major accomplishment. Congratulations!",
            "🎉 Fantastic! You've accomplished something truly special here!"
        ]

        # Encouragement responses for motivation and support
        self.encouragement_responses = [
            "You've got this! I believe in your ability to work through this.",
            "I know this is challenging, but you're capable of overcoming it.",
            "Keep going! Every step forward is progress, no matter how small.",
            "You're stronger than you realize. I have confidence in you.",
            "This might be tough now, but you're going to get through it.",
            "Remember how far you've already come. You're capable of so much more.",
            "I believe in you completely. You've got the skills to handle this.",
            "Take it one step at a time. You're making progress even if it doesn't feel like it.",
            "You're not alone in this. I'm here cheering you on every step of the way.",
            "This challenge doesn't define you - your response to it does. You've got this!"
        ]

    def detect_emotion(self, message: str) -> Tuple[str, float, Dict]:
        """
        Detect the primary emotion in a message.

        Returns:
            Tuple of (emotion_name, confidence_score, emotion_details)
        """
        message_lower = message.lower().strip()

        # Count emotion indicators
        emotion_scores = {}

        for emotion, patterns in self.emotion_patterns.items():
            score = 0
            matches = []

            # Check keywords
            for keyword in patterns['keywords']:
                if keyword in message_lower:
                    score += 2  # Keywords are strong indicators
                    matches.append(keyword)

            # Check intensifiers that modify emotions
            for intensifier in patterns['intensifiers']:
                if intensifier in message_lower:
                    # Check if intensifier appears near emotion words
                    for keyword in patterns['keywords']:
                        if abs(message_lower.find(keyword) - message_lower.find(intensifier)) < 20:
                            score += 1
                            break

            # Check context words
            for context_word in patterns['context_words']:
                if context_word in message_lower:
                    score += 1
                    matches.append(context_word)

            # Check for exclamation marks (intensity indicator)
            if '!' in message:
                score += 0.5

            # Check for multiple question marks (confusion indicator)
            if message.count('?') > 1:
                if emotion == 'confusion':
                    score += 1

            if score > 0:
                emotion_scores[emotion] = {
                    'score': score,
                    'matches': matches,
                    'confidence': min(score / 5.0, 1.0)  # Normalize to 0-1
                }

        # Return the highest scoring emotion
        if emotion_scores:
            best_emotion = max(emotion_scores.items(), key=lambda x: x[1]['score'])
            return best_emotion[0], best_emotion[1]['confidence'], best_emotion[1]

        return 'neutral', 0.0, {'score': 0, 'matches': []}

    def should_respond_empathically(self, message: str, emotion: str, confidence: float) -> bool:
        """
        Determine if an empathetic response is appropriate.

        Returns True if the message indicates a need for emotional support.
        """
        # Always respond empathetically to high-confidence emotional detection
        if confidence >= 0.7:
            return True

        # Respond to certain emotions even at lower confidence
        high_priority_emotions = ['frustration', 'sadness', 'anger', 'fear', 'tiredness']
        if emotion in high_priority_emotions and confidence >= 0.5:
            return True

        # Check for distress signals
        distress_words = ['help', 'please', 'urgent', 'emergency', 'crisis', 'problem']
        if any(word in message.lower() for word in distress_words):
            return True

        return False

    def generate_empathy_response(self, message: str, emotion: str, confidence: float) -> Optional[str]:
        """
        Generate an appropriate empathetic response based on detected emotion.

        Returns None if no empathetic response is needed.
        """
        if not self.should_respond_empathically(message, emotion, confidence):
            return None

        if emotion in self.empathy_responses:
            return random.choice(self.empathy_responses[emotion])

        return None

    def generate_celebration_response(self, message: str) -> Optional[str]:
        """
        Generate a celebration response for achievements.

        Returns None if no celebration is warranted.
        """
        achievement_indicators = [
            'finally worked', 'got it working', 'solved it', 'figured it out',
            'completed', 'finished', 'done', 'success', 'victory', 'won',
            'accomplished', 'achieved', 'made it', 'succeeded'
        ]

        message_lower = message.lower()
        if any(indicator in message_lower for indicator in achievement_indicators):
            return random.choice(self.celebration_responses)

        return None

    def generate_encouragement_response(self, message: str) -> Optional[str]:
        """
        Generate an encouraging response for motivation.

        Returns None if no encouragement is needed.
        """
        motivation_indicators = [
            'can\'t do this', 'too hard', 'giving up', 'want to quit',
            'not sure', 'doubt', 'struggling', 'difficult', 'challenging',
            'overwhelmed', 'stuck', 'lost', 'confused about'
        ]

        message_lower = message.lower()
        if any(indicator in message_lower for indicator in motivation_indicators):
            return random.choice(self.encouragement_responses)

        return None

    def match_tone(self, user_message: str, base_response: str) -> str:
        """
        Adjust response tone to match user's emotional state.

        Returns the response with tone adjustments.
        """
        emotion, confidence, _ = self.detect_emotion(user_message)

        if confidence < 0.5:
            return base_response  # No significant emotion detected

        # Tone adjustments based on emotion
        tone_adjustments = {
            'joy': {
                'add_enthusiasm': True,
                'make_supportive': False,
                'add_emojis': True
            },
            'frustration': {
                'be_supportive': True,
                'be_patient': True,
                'avoid_sarcasm': True
            },
            'sadness': {
                'be_gentle': True,
                'be_supportive': True,
                'avoid_brightness': True
            },
            'anger': {
                'be_calm': True,
                'be_supportive': True,
                'deescalate': True
            },
            'fear': {
                'be_reassuring': True,
                'be_supportive': True,
                'be_patient': True
            },
            'tiredness': {
                'be_understanding': True,
                'be_patient': True,
                'keep_concise': True
            }
        }

        if emotion in tone_adjustments:
            adjustments = tone_adjustments[emotion]

            # Apply tone adjustments (simplified version)
            if adjustments.get('be_supportive'):
                # Add supportive language if not already present
                if not any(word in base_response.lower() for word in ['help', 'support', 'assist', 'together']):
                    base_response = "I'm here to help. " + base_response

            if adjustments.get('be_patient') and len(user_message.split()) > 10:
                # For longer frustrated messages, add patience
                if not 'patience' in base_response.lower():
                    base_response = "Take your time. " + base_response

        return base_response

    def get_emotional_context(self, message: str) -> Dict:
        """
        Get comprehensive emotional context for a message.

        Returns detailed emotional analysis.
        """
        emotion, confidence, details = self.detect_emotion(message)

        return {
            'primary_emotion': emotion,
            'confidence': confidence,
            'emotion_details': details,
            'needs_empathy': self.should_respond_empathically(message, emotion, confidence),
            'needs_celebration': self.generate_celebration_response(message) is not None,
            'needs_encouragement': self.generate_encouragement_response(message) is not None,
            'tone_suggestions': self._get_tone_suggestions(emotion, confidence)
        }

    def _get_tone_suggestions(self, emotion: str, confidence: float) -> List[str]:
        """Get tone suggestions based on detected emotion."""
        suggestions = []

        if emotion == 'joy' and confidence >= 0.6:
            suggestions.extend(['enthusiastic', 'celebratory', 'positive'])
        elif emotion == 'frustration' and confidence >= 0.6:
            suggestions.extend(['supportive', 'patient', 'understanding'])
        elif emotion == 'sadness' and confidence >= 0.6:
            suggestions.extend(['gentle', 'compassionate', 'supportive'])
        elif emotion == 'anger' and confidence >= 0.6:
            suggestions.extend(['calm', 'understanding', 'de-escalating'])
        elif emotion == 'fear' and confidence >= 0.6:
            suggestions.extend(['reassuring', 'supportive', 'calm'])
        elif emotion == 'tiredness' and confidence >= 0.6:
            suggestions.extend(['understanding', 'patient', 'concise'])

        return suggestions


# Global instance
_emotional_intelligence: Optional[EmotionalIntelligence] = None


def get_emotional_intelligence() -> EmotionalIntelligence:
    """Get or create global emotional intelligence instance."""
    global _emotional_intelligence
    if _emotional_intelligence is None:
        _emotional_intelligence = EmotionalIntelligence()
    return _emotional_intelligence
