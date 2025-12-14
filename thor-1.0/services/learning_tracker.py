"""
Learning Tracker - Tracks Thor's learning progress
"""
import json
import os
from datetime import datetime, timedelta

class LearningTracker:
    """Tracks learning metrics and statistics"""
    
    def __init__(self, stats_file="learning_stats.json"):
        self.stats_file = stats_file
        self.stats = self._load_stats()
    
    def _load_stats(self):
        """Load existing statistics"""
        if os.path.exists(self.stats_file):
            try:
                with open(self.stats_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        return {
            "total_training_cycles": 0,
            "total_brain_searches": 0,
            "total_conversations": 0,
            "total_keywords_learned": 0,
            "total_knowledge_items": 0,
            "training_history": [],
            "brain_search_history": [],
            "keywords_by_letter": {},
            "topics_learned": [],
            "dictionary_topics_searched": [],  # Track which dictionary.json topics were searched
            "dictionary_progress": {
                "total_topics": 0,
                "searched_count": 0,
                "percentage": 0.0
            },
            "learning_rate": {
                "keywords_per_hour": 0,
                "knowledge_per_hour": 0,
                "training_cycles_per_day": 0
            },
            "last_updated": datetime.now().isoformat()
        }
    
    def _save_stats(self):
        """Save statistics to file"""
        self.stats["last_updated"] = datetime.now().isoformat()
        with open(self.stats_file, 'w') as f:
            json.dump(self.stats, f, indent=2)
    
    def record_training(self, examples_count, tasks_trained):
        """Record a training cycle"""
        self.stats["total_training_cycles"] += 1
        self.stats["training_history"].append({
            "timestamp": datetime.now().isoformat(),
            "examples_count": examples_count,
            "tasks_trained": tasks_trained
        })
        # Keep only last 100 training cycles
        if len(self.stats["training_history"]) > 100:
            self.stats["training_history"] = self.stats["training_history"][-100:]
        self._update_learning_rate()
        self._save_stats()
    
    def record_brain_search(self, topic, knowledge_count):
        """Record a brain search"""
        self.stats["total_brain_searches"] += 1
        self.stats["brain_search_history"].append({
            "timestamp": datetime.now().isoformat(),
            "topic": topic,
            "knowledge_count": knowledge_count
        })
        # Keep only last 200 searches
        if len(self.stats["brain_search_history"]) > 200:
            self.stats["brain_search_history"] = self.stats["brain_search_history"][-200:]
        
        if topic not in self.stats["topics_learned"]:
            self.stats["topics_learned"].append(topic)
        
        # Check if topic is from dictionary.json
        self._check_dictionary_topic(topic)
        
        self._update_learning_rate()
        self._save_stats()
    
    def _check_dictionary_topic(self, topic):
        """Check if topic is from dictionary.json and update progress"""
        try:
            import os
            dict_path = "dictionary.json"
            if os.path.exists(dict_path):
                import json
                with open(dict_path, 'r') as f:
                    dict_data = json.load(f)
                    dict_topics = dict_data.get('topics', [])
                    
                    # Initialize dictionary progress if needed
                    if "dictionary_progress" not in self.stats:
                        self.stats["dictionary_progress"] = {
                            "total_topics": len(dict_topics),
                            "searched_count": 0,
                            "percentage": 0.0
                        }
                    
                    # Update total if dictionary changed
                    self.stats["dictionary_progress"]["total_topics"] = len(dict_topics)
                    
                    # Initialize dictionary topics searched list
                    if "dictionary_topics_searched" not in self.stats:
                        self.stats["dictionary_topics_searched"] = []
                    
                    # Check if this exact topic is in dictionary (exact match)
                    if topic in dict_topics:
                        if topic not in self.stats["dictionary_topics_searched"]:
                            self.stats["dictionary_topics_searched"].append(topic)
                            self.stats["dictionary_progress"]["searched_count"] = len(self.stats["dictionary_topics_searched"])
                            print(f"[Learning Tracker] ✓ Tracked dictionary topic: '{topic}' ({len(self.stats['dictionary_topics_searched'])}/{len(dict_topics)})")
                    
                    # For queries with modifiers or combined queries, extract base topics
                    # Check if any dictionary topic appears as a complete phrase in the search query
                    import re
                    topic_lower = topic.lower()
                    
                    # Sort by length (longest first) to match "artificial intelligence" before "intelligence"
                    sorted_dict_topics = sorted(dict_topics, key=len, reverse=True)
                    
                    for dict_topic in sorted_dict_topics:
                        if dict_topic in self.stats["dictionary_topics_searched"]:
                            continue  # Skip already tracked topics
                            
                        dict_topic_lower = dict_topic.lower()
                        # Use word boundaries to match complete phrases, not substrings
                        # Escape special regex characters in the topic
                        escaped_topic = re.escape(dict_topic_lower)
                        # Match as a word/phrase (allow word boundaries or start/end)
                        pattern = r'\b' + escaped_topic + r'\b'
                        
                        if re.search(pattern, topic_lower):
                            # Found a match - track it
                            self.stats["dictionary_topics_searched"].append(dict_topic)
                            self.stats["dictionary_progress"]["searched_count"] = len(self.stats["dictionary_topics_searched"])
                            print(f"[Learning Tracker] ✓ Tracked base dictionary topic from query '{topic}': '{dict_topic}' ({len(self.stats['dictionary_topics_searched'])}/{len(dict_topics)})")
                    
                    # Update percentage
                    total = self.stats["dictionary_progress"]["total_topics"]
                    if total > 0:
                        searched = self.stats["dictionary_progress"]["searched_count"]
                        self.stats["dictionary_progress"]["percentage"] = round((searched / total) * 100, 2)
        except Exception as e:
            # Silently fail - dictionary tracking is optional
            pass
    
    def record_keyword(self, keyword, letter):
        """Record a keyword learned"""
        keywords_list = self.stats.get("keywords_learned", [])
        if not any(k.get("keyword") == keyword for k in keywords_list):
            self.stats["total_keywords_learned"] += 1
            if "keywords_learned" not in self.stats:
                self.stats["keywords_learned"] = []
            self.stats["keywords_learned"].append({
                "keyword": keyword,
                "letter": letter,
                "learned_at": datetime.now().isoformat()
            })
            if letter not in self.stats["keywords_by_letter"]:
                self.stats["keywords_by_letter"][letter] = 0
            self.stats["keywords_by_letter"][letter] += 1
            self._update_learning_rate()
            self._save_stats()
    
    def record_knowledge(self, count=1):
        """Record knowledge items learned"""
        self.stats["total_knowledge_items"] += count
        self._update_learning_rate()
        self._save_stats()
    
    def record_conversation(self):
        """Record a conversation"""
        self.stats["total_conversations"] += 1
        self._update_learning_rate()
        self._save_stats()
    
    def _update_learning_rate(self):
        """Calculate learning rates"""
        now = datetime.now()
        one_hour_ago = now - timedelta(hours=1)
        one_day_ago = now - timedelta(days=1)
        
        # Keywords per hour
        keywords_list = self.stats.get("keywords_learned", [])
        recent_keywords = [
            k for k in keywords_list
            if datetime.fromisoformat(k.get("learned_at", now.isoformat())) > one_hour_ago
        ]
        self.stats["learning_rate"]["keywords_per_hour"] = len(recent_keywords)
        
        # Knowledge per hour (from brain searches)
        recent_searches = [
            s for s in self.stats["brain_search_history"]
            if datetime.fromisoformat(s["timestamp"]) > one_hour_ago
        ]
        total_knowledge = sum(s.get("knowledge_count", 0) for s in recent_searches)
        self.stats["learning_rate"]["knowledge_per_hour"] = total_knowledge
        
        # Training cycles per day
        recent_training = [
            t for t in self.stats["training_history"]
            if datetime.fromisoformat(t["timestamp"]) > one_day_ago
        ]
        self.stats["learning_rate"]["training_cycles_per_day"] = len(recent_training)
    
    def get_stats(self):
        """Get current statistics"""
        self._update_learning_rate()
        return self.stats
    
    def get_recent_activity(self, hours=24):
        """Get recent learning activity"""
        cutoff = datetime.now() - timedelta(hours=hours)
        
        recent_training = [
            t for t in self.stats["training_history"]
            if datetime.fromisoformat(t["timestamp"]) > cutoff
        ]
        
        recent_searches = [
            s for s in self.stats["brain_search_history"]
            if datetime.fromisoformat(s["timestamp"]) > cutoff
        ]
        
        # Sort by timestamp, newest first
        recent_training.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        recent_searches.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        return {
            "training_cycles": len(recent_training),
            "brain_searches": len(recent_searches),
            "recent_training": recent_training[:10],  # Top 10 newest
            "recent_searches": recent_searches[:20]   # Top 20 newest
        }


# Global instance
_tracker = None

def get_tracker():
    """Get or create global tracker instance"""
    global _tracker
    if _tracker is None:
        _tracker = LearningTracker()
    return _tracker

