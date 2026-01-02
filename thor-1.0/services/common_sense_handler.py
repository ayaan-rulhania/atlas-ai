"""
Common Sense Handler for Atlas AI
Enhanced with emotional intelligence, empathy responses, and better conversational patterns
Detects compliments, praise, casual conversation, and emotional states to respond naturally
without triggering unnecessary web searches
"""
import re
from typing import Optional, List, Dict, Tuple


class CommonSenseHandler:
    """Handles common sense responses with enhanced emotional intelligence and conversational patterns"""
    
    def __init__(self):
        self.compliment_patterns = [
            r'\b(you|u)\s+(are|r)\s+(so|really|very|pretty|quite|extremely|super|incredibly)\s+(good|great|amazing|awesome|fantastic|wonderful|brilliant|excellent|perfect|smart|intelligent|helpful|nice|cool|badass|the best)\b',
            r'\b(you|u)\s+(are|r)\s+(good|great|amazing|awesome|fantastic|wonderful|brilliant|excellent|perfect|smart|intelligent|helpful|nice|cool|the best)\b',
            r'\b(that|this)\s+(is|was|s)\s+(so|really|very|pretty|quite|extremely|super|incredibly)\s+(good|great|amazing|awesome|fantastic|wonderful|brilliant|excellent|perfect|smart|intelligent|helpful|nice|cool)\b',
            r'\b(well\s+)?(good|great|amazing|awesome|fantastic|wonderful|brilliant|excellent|perfect)\s+job\b',
            r'\b(thank\s+you|thanks)\s+(so\s+)?(much|a lot|for everything)\b',
            r'\b(you|u)\s+(saved|helped)\s+(me|my|the)\s+(day|butt|life|time)\b',
            r'\b(you|u)\s+(rock|are the best|are awesome|are amazing)\b',
            r'\b(that|this)\s+(is|was|s)\s+(exactly|precisely|perfect|just)\s+(what|what I needed)\b',
        ]
        
        self.compliment_responses = [
            "Thank you so much! I really appreciate that. I'm here to help!",
            "Aww, thanks! That means a lot. I'm always here to assist you.",
            "Thank you! I'm glad I could help. Feel free to ask me anything!",
            "You're very welcome! I'm happy to be of assistance.",
            "Thanks! It's my pleasure to help. What else can I do for you?",
            "Thank you for the kind words! I'm here whenever you need me.",
            "I appreciate that! Let me know if there's anything else you'd like help with.",
        ]
        
        self.casual_patterns = [
            r'\b(hi|hello|hey|hiya)\s+(there|again|back)\b',
            r'\b(how\s+)?(are\s+)?(you|u)\s+(doing|today|feeling)\b',
            r'\b(how\s+)?(is\s+)?(your|ur)\s+(day|week|morning|afternoon|evening)\s+(going|been)\b',
            r'\b(how\'s|hows)\s+(your|ur)\s+(day|week|morning|afternoon|evening)\s*(going|been)?\b',
            r'\b(what\s+)?(are\s+)?(you|u)\s+(up to|doing)\b',
            r'\b(how\s+)?(are\s+)?(things|stuff)\s+(going|with you)\b',
            r'\b(what\'s|whats)\s+(up|new|good|happening)\b',
        ]

        # Enhanced emotional intelligence patterns
        self.emotional_patterns = {
            'frustrated': [
                r'\b(frustrated|frustrating|annoying|stuck|not working|problem|issue)\b',
                r'\b(can\'t figure it out|driving me crazy|making me mad)\b',
                r'\b(this is ridiculous|this sucks|what the hell)\b',
                r'\b(why won\'t it|why doesn\'t it|why isn\'t it)\b',
            ],
            'excited': [
                r'\b(excited|amazing|fantastic|awesome|can\'t wait|thrilled)\b',
                r'\b(so happy|super excited|really excited|excited about)\b',
                r'\b(yes!|woo hoo|hell yeah|awesome!)\b',
            ],
            'confused': [
                r'\b(confused|lost|don\'t understand|not sure|unclear|bewildered)\b',
                r'\b(what do you mean|I\'m confused|makes no sense)\b',
                r'\b(huh\?|wait what\?|come again\?)\b',
            ],
            'tired': [
                r'\b(tired|exhausted|drained|long day|worn out|need a break)\b',
                r'\b(can\'t think straight|brain fried|too tired)\b',
                r'\b(just want to sleep|need to rest|running on empty)\b',
            ],
            'proud': [
                r'\b(proud|accomplished|did it|success|finally worked|got it working)\b',
                r'\b(I did it|I figured it out|I solved it|I made it work)\b',
                r'\b(that was hard but|after all that work|worth the effort)\b',
            ],
            'grateful': [
                r'\b(thank you so much|really appreciate|so grateful|means a lot)\b',
                r'\b(you\'re amazing|you\'re the best|couldn\'t have done it without)\b',
            ]
        }

        # Enhanced response sets for different emotions
        self.empathy_responses = {
            'frustrated': [
                "I understand that can be really frustrating. Let me help you work through this step by step.",
                "I hear you - that sounds challenging. Let's break this down together and find a solution.",
                "That's definitely frustrating when things don't work as expected. I'm here to help you troubleshoot.",
                "I can see why that would be frustrating. Let's take a methodical approach and figure this out.",
                "Technology can be so frustrating sometimes! Don't worry, we'll get this sorted together.",
                "I get it - these things can be maddening. Let's tackle this systematically.",
                "That does sound frustrating. I'm here to help you find a way through this.",
            ],
            'excited': [
                "I can hear your excitement! That's fantastic. Tell me more about what has you so thrilled.",
                "That's awesome! I love hearing that enthusiasm. What's got you so excited?",
                "Your excitement is contagious! This sounds like something really special. What's the story?",
                "I'm thrilled to hear you're excited! That's exactly the kind of energy we want. What's next?",
                "Wonderful! I can tell this really means a lot to you. I'd love to hear more about it.",
                "That's fantastic! Your excitement makes me excited too. What happened?",
                "I love hearing this kind of enthusiasm! Tell me everything about it.",
            ],
            'confused': [
                "I can see this is confusing - that's completely understandable. Let me explain this differently.",
                "It's okay to feel confused about complex topics. Let's break this down into simpler terms.",
                "Don't worry if it's confusing at first. Many people feel the same way. Let me clarify.",
                "I understand this can be confusing. Let me rephrase and walk you through it step by step.",
                "It's normal to feel a bit lost with new concepts. I'm here to help clear things up.",
                "That's a common point of confusion. Let me explain it another way.",
                "I get that this can be confusing. Let's go through it together, nice and slow.",
            ],
            'tired': [
                "I can tell you've had a long day. Sometimes a fresh perspective helps. What can I assist you with?",
                "It's completely understandable to feel tired after a busy day. Take your time - I'm here when you're ready.",
                "Rest is important! When you're feeling refreshed, I'd be happy to help with whatever you need.",
                "I hear you - everyone needs a break sometimes. Feel free to come back whenever you need me.",
                "It's okay to take a moment. I'm here whenever you need me, no rush at all.",
                "That sounds like you've had a busy day. Take your time - I'm not going anywhere.",
                "I understand needing a break. I'm here whenever you're ready to continue.",
            ],
            'proud': [
                "That's fantastic! I can hear how proud you are of this accomplishment. Well done!",
                "Congratulations! That's a real achievement. You should definitely feel proud of this.",
                "I'm so impressed! Your hard work paid off. This is definitely something to celebrate.",
                "That's wonderful! I can tell this success means a lot to you. Great job!",
                "Excellent work! You're absolutely right to feel proud. This is a significant accomplishment.",
                "That's amazing! You've clearly put in the effort and it shows. Congratulations!",
                "Wonderful! This is a great reason to feel proud. You earned this success!",
            ],
            'grateful': [
                "You're so welcome! I'm truly glad I could help make a difference for you.",
                "I'm touched by your gratitude. It's my pleasure to assist you.",
                "You're very welcome! I'm happy I could be there when you needed help.",
                "That's very kind of you to say. I'm glad I could make a positive impact.",
                "I'm grateful for your kind words! I'm always happy to help.",
                "You're welcome! It means a lot to know I could assist you effectively.",
            ]
        }

        # Celebration responses for achievements
        self.celebration_responses = [
            "🎉 That's fantastic! You should definitely celebrate this achievement!",
            "🎊 Congratulations! This is a big win - time to celebrate!",
            "🎈 Amazing work! You've earned a celebration. What are you planning?",
            "🏆 Incredible! This success deserves some recognition. Well done!",
            "🎯 Perfect! You've hit the mark. This is definitely worth celebrating!",
            "⭐ Brilliant! Your hard work has paid off beautifully. Congratulations!",
            "🌟 Outstanding! This is a moment to savor and celebrate!",
        ]

        # Enhanced compliment responses with more variety
        self.enhanced_compliment_responses = self.compliment_responses + [
            "Thank you! I try my best to be helpful and accurate.",
            "That's very kind! I'm always learning and improving to better assist you.",
            "I appreciate the feedback! It motivates me to keep helping effectively.",
            "Thank you so much! I'm glad I'm meeting your expectations.",
            "That's wonderful to hear! I'm here whenever you need assistance.",
            "Thank you! Your encouragement means a lot as I continue to help.",
            "I appreciate that! I'm committed to providing the best help I can.",
            "Thank you for the kind words! I'm always striving to be more helpful.",
            "That's very generous! I'm grateful for users like you who appreciate the effort.",
            "Thank you! It makes all the work worthwhile when I can truly help someone.",
        ]
        
    def is_compliment(self, message: str) -> bool:
        """Check if message is a compliment or praise"""
        message_lower = message.lower().strip()
        
        # Check against compliment patterns
        for pattern in self.compliment_patterns:
            if re.search(pattern, message_lower, re.IGNORECASE):
                return True
        
        return False
    
    def is_casual_conversation(self, message: str) -> bool:
        """Check if message is casual conversation that doesn't need web search"""
        message_lower = message.lower().strip()

        for pattern in self.casual_patterns:
            if re.search(pattern, message_lower, re.IGNORECASE):
                return True

        return False

    def detect_emotion(self, message: str) -> Tuple[str, float]:
        """Detect emotional state from message. Returns (emotion, confidence)"""
        message_lower = message.lower().strip()

        for emotion, patterns in self.emotional_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message_lower, re.IGNORECASE):
                    # Simple confidence scoring - could be enhanced with ML
                    confidence = 0.8 if len(re.findall(pattern, message_lower)) > 1 else 0.6
                    return emotion, confidence

        return "neutral", 0.0

    def is_emotional_response_needed(self, message: str) -> bool:
        """Check if message indicates an emotional state that needs empathetic response"""
        emotion, confidence = self.detect_emotion(message)
        return emotion != "neutral" and confidence >= 0.6

    def get_empathy_response(self, message: str, emotion: str = None) -> Optional[str]:
        """Get appropriate empathy response based on detected emotion"""
        import random

        if not emotion:
            emotion, confidence = self.detect_emotion(message)
            if confidence < 0.6:
                return None

        if emotion in self.empathy_responses:
            return random.choice(self.empathy_responses[emotion])

        return None

    def get_celebration_response(self, message: str) -> Optional[str]:
        """Get celebration response for achievements"""
        import random

        message_lower = message.lower()
        achievement_indicators = [
            'finally worked', 'got it working', 'solved it', 'figured it out',
            'completed', 'finished', 'done', 'success', 'accomplished'
        ]

        if any(indicator in message_lower for indicator in achievement_indicators):
            return random.choice(self.celebration_responses)

        return None
    
    def should_skip_search(self, message: str) -> bool:
        """Determine if we should skip web search for this message"""
        if self.is_compliment(message) or self.is_casual_conversation(message):
            return True
        
        # Add more common sense patterns that don't need web search
        message_lower = message.lower().strip()
        
        # Common sense questions that can be answered without search
        common_sense_patterns = [
            r'\b(?:what|how|why)\s+is\s+(?:2\s*\+\s*2|the\s+time|today|the\s+date)',
            r'\b(?:what|which)\s+is\s+(?:better|best)\s+(?:python|javascript|java)\s+(?:or|vs)',
            r'\b(?:can|should|do)\s+you\s+(?:help|remember|save)',
            r'\b(?:tell|show)\s+me\s+(?:about\s+)?yourself',
            r'\b(?:what|who)\s+are\s+you',
            r'\b(?:how|what)\s+(?:do|does)\s+(?:you|this|it)\s+work',
            r'\b(?:is|are)\s+(?:this|that|it)\s+(?:good|bad|right|wrong|correct)',
            r'\b(?:should|can)\s+i\s+(?:use|try|do)',
            r'\b(?:what|which)\s+(?:should|can)\s+i\s+(?:use|choose|pick)',
        ]
        
        for pattern in common_sense_patterns:
            if re.search(pattern, message_lower, re.IGNORECASE):
                return True
        
        # Mathematical questions (simple arithmetic)
        math_pattern = r'^\s*(?:what\s+is|calculate|compute)\s+[\d\+\-\*\/\s\(\)]+\s*\?*\s*$'
        if re.match(math_pattern, message_lower):
            return True
        
        # Very short questions that are likely conversational
        if len(message.split()) <= 3 and not any(word in message_lower for word in ['who', 'what', 'when', 'where', 'why', 'how']):
            return True
        
        return False
    
    def get_common_sense_response(self, message: str, context: Optional[List[dict]] = None) -> Optional[str]:
        """Get common sense response for questions that don't need web search"""
        message_lower = message.lower().strip()
        
        # Mathematical questions
        math_pattern = r'^\s*(?:what\s+is|calculate|compute)\s+([\d\+\-\*\/\s\(\)]+)\s*\?*\s*$'
        math_match = re.match(math_pattern, message_lower)
        if math_match:
            try:
                expression = math_match.group(1).strip()
                # Simple evaluation (be careful with eval in production)
                result = eval(expression.replace(' ', ''))
                return f"The answer is **{result}**."
            except:
                pass
        
        # Questions about the assistant
        if re.search(r'\b(?:what|who)\s+are\s+you\b', message_lower):
            return "I'm Atlas, an AI assistant powered by Thor models. I'm here to help you with questions, tasks, and information. How can I assist you today?"
        
        if re.search(r'\b(?:tell|show)\s+me\s+(?:about\s+)?yourself\b', message_lower):
            return "I'm Atlas, an AI assistant. I can help you with a wide range of tasks including answering questions, generating content, writing code, creating images, and much more. What would you like to know or work on?"
        
        # Questions about capabilities
        if re.search(r'\b(?:what|what can)\s+(?:can|do)\s+you\s+(?:do|help)|\b(?:how)\s+can\s+you\s+help', message_lower):
            return "I can help you with:\n- Answering questions and providing information\n- Writing and debugging code\n- Creating images\n- Generating creative content\n- And much more! What would you like to do?"
        
        # Time/date questions
        if re.search(r'\b(?:what|what\'s)\s+(?:is\s+)?(?:the\s+)?(?:time|date|today)\b', message_lower):
            from datetime import datetime
            now = datetime.now()
            return f"Today is **{now.strftime('%B %d, %Y')}** and the current time is **{now.strftime('%I:%M %p')}**."
        
        return None
    
    def get_response(self, message: str, context: Optional[List[dict]] = None) -> str:
        """Get appropriate response with enhanced emotional intelligence"""
        import random

        # First check common sense responses
        common_sense = self.get_common_sense_response(message, context)
        if common_sense:
            return common_sense

        # Check for celebration-worthy achievements
        celebration = self.get_celebration_response(message)
        if celebration:
            return celebration

        # Check for emotional states that need empathy
        if self.is_emotional_response_needed(message):
            emotion, confidence = self.detect_emotion(message)
            empathy_response = self.get_empathy_response(message, emotion)
            if empathy_response:
                return empathy_response

        # Enhanced compliment detection and responses
        if self.is_compliment(message):
            response = random.choice(self.enhanced_compliment_responses)
            # Personalize based on context if available
            if context and len(context) > 0:
                # Check if user mentioned something specific we helped with
                last_assistant_msg = None
                for msg in reversed(context):
                    if msg.get('role') == 'assistant':
                        last_assistant_msg = msg.get('content', '')
                        break

                if last_assistant_msg:
                    response += " I'm glad I could assist you!"

            return response

        # Enhanced casual conversation responses
        elif self.is_casual_conversation(message):
            enhanced_casual_responses = [
                "I'm doing great, thanks for asking! How can I help you today?",
                "I'm here and ready to help! What can I do for you?",
                "Doing well! What would you like to know or work on?",
                "I'm good! How can I assist you?",
                "All good here! What's on your mind?",
                "I'm doing fantastic! Ready to tackle whatever you need.",
                "Doing well, thanks! What would you like to work on today?",
                "I'm great! Excited to help you with whatever you need.",
            ]
            return random.choice(enhanced_casual_responses)

        return None


# Global instance
_common_sense_handler = None

def get_common_sense_handler():
    """Get or create the global common sense handler instance"""
    global _common_sense_handler
    if _common_sense_handler is None:
        _common_sense_handler = CommonSenseHandler()
    return _common_sense_handler

