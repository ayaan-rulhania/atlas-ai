"""
Greetings Handler - Teaches Thor how to respond to greetings
Enhanced with time-of-day awareness, personalized greetings, and 20+ response variations
"""
import json
import os
import re
import random
from datetime import datetime

class GreetingsHandler:
    """Handles greeting recognition and responses with enhanced conversational capabilities"""

    def __init__(self, greetings_file="greetings_knowledge.json"):
        self.greetings_file = greetings_file
        self.greetings_data = self._load_greetings()
        self._store_in_brain()
    
    def _load_greetings(self):
        """Load greetings knowledge with enhanced patterns and responses"""
        if os.path.exists(self.greetings_file):
            try:
                with open(self.greetings_file, 'r') as f:
                    return json.load(f)
            except:
                pass

        # Enhanced greetings with time-of-day awareness and 25+ response variations
        return {
            "greetings": {
                "patterns": [
                    "hi", "hello", "hey", "what's up", "whats up", "howdy", "greetings",
                    "good morning", "good afternoon", "good evening", "good day",
                    "sup", "hey there", "hi there", "hello there", "what's good",
                    "whats good", "yo", "hiya", "how's it going", "how are you"
                ],
                "responses": [
                    "Hello! How can I help you today?",
                    "Hi there! What can I do for you?",
                    "Hey! I'm your AI assistant. How can I assist you?",
                    "Hello! I'm here to help. What would you like to know?",
                    "Hi! Ready to help. What's on your mind?",
                    "Hey there! Great to see you. What can I help with?",
                    "Hello! I'm excited to chat. What's up?",
                    "Hi! I'm all set and ready to assist. How can I help?",
                    "Hey! Let's make this productive. What would you like to work on?",
                    "Hello there! I'm here and listening. What's on your agenda?",
                    "Hi! I love helping people. What can I do for you today?",
                    "Hey! Ready for some great conversation. What's up?",
                    "Hello! I'm energized and ready to help. What's next?",
                    "Hi there! I'm your friendly AI assistant. How can I assist you?",
                    "Hey! Let's get started. What would you like to accomplish?",
                    "Hello! I'm here to make things easier for you. What's your goal?",
                    "Hi! I'm always happy to help. What do you need?",
                    "Hey there! I'm fully charged and ready to assist. What's up?",
                    "Hello! I'm looking forward to our conversation. How can I help?",
                    "Hi! I'm your go-to assistant for anything. What's on your mind?",
                    "Hey! I'm here to make your day better. What can I do for you?",
                    "Hello there! I'm excited about what we can accomplish together. What's next?",
                    "Hi! I'm ready to tackle whatever you throw at me. What's up?",
                    "Hey! Let's make this conversation productive. How can I help?"
                ],
                "time_based_responses": {
                    "morning": [
                        "Good morning! Hope you're having a great start to your day. How can I help?",
                        "Morning! Ready to tackle the day. What would you like to work on?",
                        "Good morning! I'm energized and ready to help. What's on your agenda?",
                        "Morning! Let's make today productive. What can I assist you with?",
                        "Good morning! Wishing you an excellent day ahead. How can I help?"
                    ],
                    "afternoon": [
                        "Good afternoon! Hope your day is going well. How can I assist you?",
                        "Afternoon! Halfway through the day. What would you like to work on?",
                        "Good afternoon! I'm here and ready. What's on your mind?",
                        "Afternoon! Let's make the rest of your day productive. How can I help?",
                        "Good afternoon! Hope you're having a great day so far. What can I do for you?"
                    ],
                    "evening": [
                        "Good evening! Hope you've had a wonderful day. How can I help?",
                        "Evening! Time to wind down or get some work done. What would you like?",
                        "Good evening! I'm here if you need anything. What's on your mind?",
                        "Evening! Ready to assist you. How can I help this evening?",
                        "Good evening! Hope you're having a relaxing evening. What can I do for you?"
                    ]
                },
                "contextual_responses": {
                    "what's up": "Not much! Just here and ready to help. What can I do for you?",
                    "whats up": "Not much! Just here and ready to help. What can I do for you?",
                    "sup": "Hey! Not much, just hanging out and ready to help. What's good?",
                    "what's good": "Not much! I'm here and ready to help. What's good with you?",
                    "whats good": "Not much! I'm here and ready to help. What's good with you?",
                    "how are you": "I'm doing great, thanks for asking! How can I help you today?",
                    "how's it going": "It's going well! I'm here to help. What do you need?",
                    "howdy": "Howdy! Great to see you. How can I help you today?",
                    "yo": "Yo! What's up? Ready to help with whatever you need!",
                    "hiya": "Hiya! I'm doing great. What can I help you with today?"
                },
                "name_greetings": {
                    "responses": [
                        "Hello {name}! Nice to meet you. How can I help?",
                        "Hi {name}! Great to see you. What can I do for you?",
                        "Hey {name}! I'm your AI assistant. How can I assist you today?",
                        "Hello {name}! Wonderful to connect with you. What's on your mind?",
                        "Hi {name}! I'm excited to chat. How can I help you?",
                        "Hey {name}! Good to have you here. What would you like to work on?",
                        "Hello {name}! Always great to see you. How can I assist?"
                    ]
                },
                "returning_user_responses": [
                    "Welcome back! Great to see you again. How can I help you today?",
                    "Hey! Good to have you back. What would you like to work on?",
                    "Welcome back! I remember our last conversation. What's new?",
                    "Great to see you again! Ready to continue where we left off?",
                    "Welcome back! It's always nice when familiar faces return. How can I assist you?",
                    "Hey there! Good to see you again. What can I help you with today?"
                ]
            }
        }
    
    def _store_in_brain(self):
        """Store greeting knowledge in brain structure"""
        brain_dir = "brain"
        os.makedirs(brain_dir, exist_ok=True)
        
        # Store greeting keywords
        for pattern in self.greetings_data.get("greetings", {}).get("patterns", []):
            if pattern and pattern[0].isalpha():
                letter = pattern[0].upper()
                letter_dir = os.path.join(brain_dir, letter)
                keywords_file = os.path.join(letter_dir, "keywords.json")
                
                os.makedirs(letter_dir, exist_ok=True)
                
                if os.path.exists(keywords_file):
                    try:
                        with open(keywords_file, 'r') as f:
                            data = json.load(f)
                    except:
                        data = {"letter": letter, "keywords": [], "knowledge": []}
                else:
                    data = {"letter": letter, "keywords": [], "knowledge": []}
                
                # Add greeting keyword
                if pattern not in data.get("keywords", []):
                    data.setdefault("keywords", []).append(pattern)
                
                # Don't store generic greeting patterns in brain - greetings are handled directly
                # Only store keywords for search purposes
                
                data["last_updated"] = datetime.now().isoformat()
                
                with open(keywords_file, 'w') as f:
                    json.dump(data, f, indent=2)
    
    def is_greeting(self, message):
        """Check if message is a greeting"""
        message_lower = message.lower().strip()
        
        # Don't treat questions starting with "who" or "what" as greetings
        if message_lower.startswith(('who ', 'what ', 'who is', 'what is', 'who are', 'what are', 
                                      'who was', 'what was', 'who were', 'what were',
                                      'who can', 'what can', 'who do', 'what do',
                                      'who does', 'what does', 'who did', 'what did',
                                      'who will', 'what will', 'who would', 'what would',
                                      'who should', 'what should', 'who might', 'what might')):
            return False
        
        # Check exact matches (only for standalone greetings)
        patterns = self.greetings_data.get("greetings", {}).get("patterns", [])
        for pattern in patterns:
            # Only match if it's exactly the pattern or starts with pattern + space
            # and is not followed by question words
            if message_lower == pattern:
                return True
            if message_lower.startswith(pattern + " "):
                # Don't treat as greeting if it's followed by a question
                rest = message_lower[len(pattern):].strip()
                if not rest.startswith(('who', 'what', 'where', 'when', 'why', 'how', 'which')):
                    return True
        
        # Check contextual greetings (but not if it's a question)
        contextual = self.greetings_data.get("greetings", {}).get("contextual_responses", {})
        for key in contextual.keys():
            if key in message_lower:
                # Make sure it's not part of a question
                if not any(q in message_lower for q in ['who', 'what', 'where', 'when', 'why', 'how']):
                    return True
        
        # Check conversational greetings like "How's your day going?"
        conversational_patterns = [
            r'\b(how\'s|hows)\s+(your|ur)\s+(day|week|morning|afternoon|evening)\s*(going|been)?\??\s*$',
            r'\b(how\s+)?(is\s+)?(your|ur)\s+(day|week|morning|afternoon|evening)\s+(going|been)\??\s*$',
            r'\b(how\s+)?(are\s+)?(things|stuff)\s+(going|with you)\??\s*$',
            r'\b(what\'s|whats)\s+(up|new|good|happening)\??\s*$',
        ]
        for pattern in conversational_patterns:
            if re.search(pattern, message_lower, re.IGNORECASE):
                return True
        
        # Check name greetings (hey name, hi name, etc.)
        name_pattern = r'\b(hey|hi|hello|good morning|good afternoon|good evening)\s+([A-Z][a-z]+)\b'
        if re.search(name_pattern, message, re.IGNORECASE):
            return True
        
        return False
    
    def extract_name(self, message):
        """Extract name from greeting if present"""
        # Pattern: "hey John", "hi Sarah", etc.
        name_pattern = r'\b(hey|hi|hello|good morning|good afternoon|good evening)\s+([A-Z][a-z]+)\b'
        match = re.search(name_pattern, message, re.IGNORECASE)
        if match:
            return match.group(2)
        return None

    def get_time_of_day(self):
        """Get current time of day for context-aware greetings"""
        current_hour = datetime.now().hour

        if 5 <= current_hour < 12:
            return "morning"
        elif 12 <= current_hour < 17:
            return "afternoon"
        else:
            return "evening"

    def is_returning_user(self, message, conversation_context=None):
        """Check if this appears to be a returning user based on message content"""
        returning_indicators = [
            "back again", "came back", "returned", "here again",
            "good to see you again", "nice to see you again"
        ]

        message_lower = message.lower()
        return any(indicator in message_lower for indicator in returning_indicators)

    def get_personalized_greeting(self, message, conversation_context=None, user_name=None):
        """Get a personalized greeting based on context"""
        # Check for returning user
        if self.is_returning_user(message, conversation_context):
            responses = self.greetings_data.get("greetings", {}).get("returning_user_responses", [])
            if responses:
                return random.choice(responses)

        # Check for named greeting
        name = self.extract_name(message)
        if name or user_name:
            name_to_use = name or user_name
            name_responses = self.greetings_data.get("greetings", {}).get("name_greetings", {}).get("responses", [])
            if name_responses:
                response = random.choice(name_responses)
                return response.replace("{name}", name_to_use)

        return None
    
    def get_response(self, message, conversation_context=None, user_name=None):
        """Get appropriate greeting response with enhanced personalization"""
        import random
        message_lower = message.lower().strip()

        # First, try personalized greetings
        personalized = self.get_personalized_greeting(message, conversation_context, user_name)
        if personalized:
            return personalized

        # Check for time-based greetings (good morning, afternoon, evening)
        time_of_day = self.get_time_of_day()
        time_based_responses = self.greetings_data.get("greetings", {}).get("time_based_responses", {})

        if "morning" in message_lower and time_of_day == "morning":
            return random.choice(time_based_responses.get("morning", ["Good morning! How can I help?"]))
        elif "afternoon" in message_lower and time_of_day == "afternoon":
            return random.choice(time_based_responses.get("afternoon", ["Good afternoon! How can I help?"]))
        elif "evening" in message_lower and time_of_day == "evening":
            return random.choice(time_based_responses.get("evening", ["Good evening! How can I help?"]))

        # Check for conversational greetings like "How's your day going?"
        conversational_responses = {
            r'\b(how\'s|hows)\s+(your|ur)\s+(day|week)\s*(going|been)?\??\s*$': [
                "I'm doing great, thanks for asking! How can I help you today?",
                "I'm here and ready to help! What can I do for you?",
                "Doing well! What would you like to know or work on?",
            ],
            r'\b(how\s+)?(are\s+)?(things|stuff)\s+(going|with you)\??\s*$': [
                "Things are going well! How can I assist you?",
                "All good here! What can I help you with?",
            ],
            r'\b(what\'s|whats)\s+(up|new|good|happening)\??\s*$': [
                "Not much! Just here to help. What can I do for you?",
                "All good! How can I assist you today?",
            ],
        }

        for pattern, responses_list in conversational_responses.items():
            if re.search(pattern, message_lower, re.IGNORECASE):
                return random.choice(responses_list)

        # Check contextual responses first (includes informal greetings like "sup", "yo")
        contextual = self.greetings_data.get("greetings", {}).get("contextual_responses", {})
        for key, response in contextual.items():
            if key in message_lower:
                return response

        # Handle name greetings (if not caught by personalized greeting)
        name = self.extract_name(message)
        if name:
            name_responses = self.greetings_data.get("greetings", {}).get("name_greetings", {}).get("responses", [])
            if name_responses:
                response = random.choice(name_responses)
                return response.replace("{name}", name)

        # Regular greeting responses - use expanded set of 25+ responses
        responses = self.greetings_data.get("greetings", {}).get("responses", [])
        if responses:
            return random.choice(responses)

        # Default fallback
        return "Hello! How can I help you today?"


# Global instance
_greetings_handler = None

def get_greetings_handler():
    """Get or create global greetings handler"""
    global _greetings_handler
    if _greetings_handler is None:
        _greetings_handler = GreetingsHandler()
    return _greetings_handler

