"""
Common Sense Handler for Atlas AI
Detects compliments, praise, casual conversation, and responds with common sense
without triggering unnecessary web searches
"""
import re
from typing import Optional, List


class CommonSenseHandler:
    """Handles common sense responses for compliments, praise, and casual conversation"""
    
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
            r'\b(what\s+)?(are\s+)?(you|u)\s+(up to|doing)\b',
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
        """Get appropriate response for compliment or casual conversation"""
        import random
        
        # First check common sense responses
        common_sense = self.get_common_sense_response(message, context)
        if common_sense:
            return common_sense
        
        if self.is_compliment(message):
            response = random.choice(self.compliment_responses)
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
        
        elif self.is_casual_conversation(message):
            casual_responses = [
                "I'm doing great, thanks for asking! How can I help you today?",
                "I'm here and ready to help! What can I do for you?",
                "Doing well! What would you like to know or work on?",
                "I'm good! How can I assist you?",
            ]
            return random.choice(casual_responses)
        
        return None


# Global instance
_common_sense_handler = None

def get_common_sense_handler():
    """Get or create the global common sense handler instance"""
    global _common_sense_handler
    if _common_sense_handler is None:
        _common_sense_handler = CommonSenseHandler()
    return _common_sense_handler

