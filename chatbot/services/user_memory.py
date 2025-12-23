"""
User Memory System for Atlas AI
Stores user preferences and information from previous chats
"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import re


class UserMemory:
    """Manages user preferences and information across all chats"""
    
    def __init__(self, memory_file: str = None):
        self.memory_file = memory_file or os.path.join(
            Path(__file__).parent.parent.resolve(),
            "user_memory.json"
        )
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.memory_file), exist_ok=True)
        self.memory = self._load_memory()
    
    def _load_memory(self) -> Dict:
        """Load user memory from disk"""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"[User Memory] Error loading memory: {e}")
                return self._default_memory()
        return self._default_memory()
    
    def _default_memory(self) -> Dict:
        """Return default memory structure"""
        return {
            "preferences": {},
            "facts": [],
            "conversation_topics": [],
            "last_updated": datetime.now().isoformat()
        }
    
    def _save_memory(self):
        """Save user memory to disk"""
        try:
            self.memory["last_updated"] = datetime.now().isoformat()
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(self.memory, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[User Memory] Error saving memory: {e}")
    
    def extract_preferences_from_message(self, message: str, response: str = None):
        """Extract user preferences from messages"""
        message_lower = message.lower()
        
        # Extract preferences (e.g., "I prefer", "I like", "I don't like")
        preference_patterns = [
            r'\b(?:i|i\'m|i am)\s+(?:prefer|like|love|enjoy|hate|dislike|don\'t like|dislike)\s+(.+?)(?:\.|$)',
            r'\b(?:i|i\'m|i am)\s+(?:into|interested in|not interested in)\s+(.+?)(?:\.|$)',
            r'\b(?:my|my favorite|my preferred)\s+(.+?)\s+is\s+(.+?)(?:\.|$)',
            r'\b(?:i)\s+(?:use|usually|typically|always|never)\s+(.+?)(?:\.|$)',
            r'\b(?:i)\s+(?:want|need|would like)\s+(.+?)(?:\.|$)',
        ]
        
        for pattern in preference_patterns:
            matches = re.finditer(pattern, message_lower, re.IGNORECASE)
            for match in matches:
                preference = match.group(1).strip()
                if len(preference) > 3 and len(preference) < 100:
                    category = self._categorize_preference(preference)
                    if category:
                        if category not in self.memory["preferences"]:
                            self.memory["preferences"][category] = []
                        if preference not in self.memory["preferences"][category]:
                            self.memory["preferences"][category].append(preference)
                            print(f"[User Memory] Extracted preference: {category} -> {preference}")
    
    def extract_facts_from_conversation(self, user_message: str, assistant_message: str):
        """Extract factual information about the user from conversations"""
        # Extract personal facts (e.g., "I'm a developer", "I work at X", "I'm from Y")
        fact_patterns = [
            r'\b(?:i|i\'m|i am)\s+(?:a|an)\s+(.+?)(?:\.|,|$)',
            r'\b(?:i|i\'m|i am)\s+(?:from|in|at|working at|work at)\s+(.+?)(?:\.|,|$)',
            r'\b(?:my|i have|i own)\s+(.+?)\s+is\s+(.+?)(?:\.|,|$)',
            r'\b(?:i)\s+(?:work|study|live|am located)\s+(?:at|in|for)\s+(.+?)(?:\.|,|$)',
        ]
        
        combined = f"{user_message} {assistant_message}".lower()
        
        for pattern in fact_patterns:
            matches = re.finditer(pattern, combined, re.IGNORECASE)
            for match in matches:
                fact_text = match.group(0).strip()
                if len(fact_text) > 5 and len(fact_text) < 200:
                    # Check if we already have this fact
                    if not any(fact_text.lower() in f.get("content", "").lower() for f in self.memory["facts"]):
                        fact = {
                            "content": fact_text,
                            "category": self._categorize_fact(fact_text),
                            "extracted_at": datetime.now().isoformat()
                        }
                        self.memory["facts"].append(fact)
                        # Keep only last 50 facts
                        if len(self.memory["facts"]) > 50:
                            self.memory["facts"] = self.memory["facts"][-50:]
                        print(f"[User Memory] Extracted fact: {fact_text}")
    
    def _categorize_preference(self, preference: str) -> Optional[str]:
        """Categorize a preference"""
        pref_lower = preference.lower()
        categories = {
            "technology": ["python", "javascript", "java", "react", "node", "code", "programming", "software", "app"],
            "languages": ["english", "spanish", "french", "german", "language"],
            "format": ["markdown", "json", "csv", "table", "list", "bullet", "paragraph"],
            "style": ["detailed", "brief", "simple", "complex", "formal", "casual"],
            "interests": ["music", "movies", "books", "games", "sports", "travel", "food", "cooking"],
        }
        
        for category, keywords in categories.items():
            if any(keyword in pref_lower for keyword in keywords):
                return category
        return "general"
    
    def _categorize_fact(self, fact: str) -> str:
        """Categorize a fact"""
        fact_lower = fact.lower()
        if any(word in fact_lower for word in ["work", "job", "developer", "engineer", "designer"]):
            return "profession"
        elif any(word in fact_lower for word in ["from", "live", "located", "country", "city"]):
            return "location"
        elif any(word in fact_lower for word in ["study", "student", "university", "college"]):
            return "education"
        elif any(word in fact_lower for word in ["have", "own", "use"]):
            return "possessions"
        return "general"
    
    def get_relevant_context(self, query: str) -> str:
        """Get relevant user context for a query"""
        query_lower = query.lower()
        context_parts = []
        
        # Check preferences
        for category, prefs in self.memory["preferences"].items():
            if any(keyword in query_lower for keyword in [category] + prefs):
                context_parts.append(f"User preferences in {category}: {', '.join(prefs[:3])}")
        
        # Check facts
        relevant_facts = []
        for fact in self.memory["facts"][-10:]:  # Check recent facts
            fact_content = fact.get("content", "").lower()
            if any(word in fact_content for word in query_lower.split()[:5]):
                relevant_facts.append(fact.get("content"))
        
        if relevant_facts:
            context_parts.append(f"Relevant user information: {', '.join(relevant_facts[:2])}")
        
        return " | ".join(context_parts) if context_parts else ""
    
    def add_conversation_topic(self, topic: str):
        """Add a conversation topic"""
        if topic and len(topic) > 3:
            topic_lower = topic.lower().strip()
            if topic_lower not in [t.lower() for t in self.memory["conversation_topics"]]:
                self.memory["conversation_topics"].append(topic)
                # Keep only last 20 topics
                if len(self.memory["conversation_topics"]) > 20:
                    self.memory["conversation_topics"] = self.memory["conversation_topics"][-20:]
                self._save_memory()
    
    def get_all_context_string(self) -> str:
        """Get all user context as a string for prompt injection"""
        parts = []
        
        if self.memory["preferences"]:
            prefs_str = ", ".join([
                f"{cat}: {', '.join(vals[:2])}"
                for cat, vals in self.memory["preferences"].items()
            ])
            parts.append(f"User Preferences: {prefs_str}")
        
        if self.memory["facts"]:
            facts_str = ", ".join([f["content"] for f in self.memory["facts"][-5:]])
            parts.append(f"Known User Information: {facts_str}")
        
        if self.memory["conversation_topics"]:
            topics_str = ", ".join(self.memory["conversation_topics"][-5:])
            parts.append(f"Recent Conversation Topics: {topics_str}")
        
        return " | ".join(parts) if parts else ""
    
    def save(self):
        """Save memory to disk"""
        self._save_memory()


# Global instance
_user_memory = None

def get_user_memory():
    """Get or create the global user memory instance"""
    global _user_memory
    if _user_memory is None:
        _user_memory = UserMemory()
    return _user_memory

