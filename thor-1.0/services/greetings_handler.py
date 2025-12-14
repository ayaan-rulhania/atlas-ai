"""
Greetings Handler - Teaches Thor how to respond to greetings
"""
import json
import os
import re
import random
from datetime import datetime

class GreetingsHandler:
    """Handles greeting recognition and responses"""
    
    def __init__(self, greetings_file="greetings_knowledge.json"):
        self.greetings_file = greetings_file
        self.greetings_data = self._load_greetings()
        self._store_in_brain()
    
    def _load_greetings(self):
        """Load greetings knowledge"""
        if os.path.exists(self.greetings_file):
            try:
                with open(self.greetings_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        # Default greetings with more patterns
        return {
            "greetings": {
                "patterns": ["hi", "hello", "hey", "what's up", "whats up", "howdy", "greetings", "good morning", "good afternoon", "good evening"],
                "responses": [
                    "Hello! How can I help you today?",
                    "Hi there! What can I do for you?",
                    "Hey! I'm your AI assistant. How can I assist you?",
                    "Hello! I'm here to help. What would you like to know?",
                    "Hi! Ready to help. What's on your mind?"
                ],
                "contextual_responses": {
                    "what's up": "Not much! I'm here and ready to help. What can I do for you?",
                    "whats up": "Not much! I'm here and ready to help. What can I do for you?",
                    "how are you": "I'm doing great, thanks for asking! How can I help you today?",
                    "how's it going": "It's going well! I'm here to help. What do you need?",
                    "good morning": "Good morning! How can I assist you today?",
                    "good afternoon": "Good afternoon! What can I help you with?",
                    "good evening": "Good evening! How can I be of service?"
                },
                "name_greetings": {
                    "responses": [
                        "Hello {name}! Nice to meet you. How can I help?",
                        "Hi {name}! Great to see you. What can I do for you?",
                        "Hey {name}! I'm your AI assistant. How can I assist you today?"
                    ]
                }
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
    
    def get_response(self, message):
        """Get appropriate greeting response"""
        message_lower = message.lower().strip()
        name = self.extract_name(message)
        
        # Check contextual responses first
        contextual = self.greetings_data.get("greetings", {}).get("contextual_responses", {})
        for key, response in contextual.items():
            if key in message_lower:
                return response
        
        # Handle name greetings
        if name:
            name_responses = self.greetings_data.get("greetings", {}).get("name_greetings", {}).get("responses", [])
            if name_responses:
                response = random.choice(name_responses)
                return response.replace("{name}", name)
        
        # Regular greeting responses
        responses = self.greetings_data.get("greetings", {}).get("responses", [])
        if responses:
            return random.choice(responses)
        
        # Default
        return "Hello! How can I help you today?"


# Global instance
_greetings_handler = None

def get_greetings_handler():
    """Get or create global greetings handler"""
    global _greetings_handler
    if _greetings_handler is None:
        _greetings_handler = GreetingsHandler()
    return _greetings_handler

