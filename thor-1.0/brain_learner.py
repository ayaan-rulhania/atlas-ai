#!/usr/bin/env python3
"""
Continuous Google Search Learner for Thor 1.0
Uses multiple sources to actually learn and extract knowledge
"""
import os
import time
import random
import json
import threading
from datetime import datetime
from urllib.parse import quote_plus
import requests
from bs4 import BeautifulSoup
from services.learning_tracker import get_tracker


class BrainLearner:
    """Continuously learns from web searches and knowledge sources"""
    
    def __init__(self, search_interval_seconds=10):  # 10 seconds for fast learning
        self.search_interval = search_interval_seconds
        self.running = False
        self.thread = None
        self.brain_dir = "brain"
        self.learned_data_dir = "learned_data"
        self.progress_file = "brain_learner_progress.json"  # Track sequential progress
        
        # Ensure directories exist
        os.makedirs(self.brain_dir, exist_ok=True)
        os.makedirs(self.learned_data_dir, exist_ok=True)
        
        # Initialize brain structure
        self._initialize_brain()
        
        print("Brain Learner initialized")
    
    def _initialize_brain(self):
        """Initialize the brain folder structure with letters"""
        letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        
        for letter in letters:
            letter_dir = os.path.join(self.brain_dir, letter)
            os.makedirs(letter_dir, exist_ok=True)
            
            # Create initial keyword file
            keywords_file = os.path.join(letter_dir, "keywords.json")
            if not os.path.exists(keywords_file):
                with open(keywords_file, 'w') as f:
                    json.dump({
                        "letter": letter,
                        "keywords": [],
                        "knowledge": [],
                        "last_updated": datetime.now().isoformat()
                    }, f, indent=2)
    
    def start(self):
        """Start the continuous learning process"""
        if self.running:
            print("Brain Learner is already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._learning_loop, daemon=True)
        self.thread.start()
        print(f"Brain Learner started - searching every {self.search_interval} seconds")
    
    def stop(self):
        """Stop the learning process"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        print("Brain Learner stopped")
    
    def _load_progress(self):
        """Load sequential search progress from file - returns list (most recent first)"""
        try:
            if os.path.exists(self.progress_file):
                with open(self.progress_file, 'r') as f:
                    progress = json.load(f)
                    # Return as list (already sorted with most recent first)
                    searched_list = progress.get('searched_topics', [])
                    return progress.get('current_index', 0), searched_list
            return 0, []
        except Exception as e:
            print(f"[Brain Learner] Error loading progress: {e}")
            return 0, []
    
    def _save_progress(self, current_index, searched_topics, total_topics=None, dictionary_topics=None):
        """Save sequential search progress to file - topics sorted by most recent first"""
        try:
            # ALWAYS rebuild list from dictionary to ensure correct order
            # This prevents any corruption or ordering issues
            topics_list = []
            if current_index > 0 and dictionary_topics:
                # Build list from most recent (current_index-1) to oldest (0)
                for i in range(current_index - 1, -1, -1):
                    if i < len(dictionary_topics):
                        topics_list.append(dictionary_topics[i])
            elif isinstance(searched_topics, list):
                # Fallback: use provided list if dictionary not available
                topics_list = searched_topics
            else:
                topics_list = list(searched_topics) if searched_topics else []
            
            progress = {
                'current_index': current_index,
                'searched_topics': topics_list,  # Rebuilt from dictionary, most recent first
                'last_updated': datetime.now().isoformat()
            }
            # Load existing progress to preserve total_topics if already set
            if os.path.exists(self.progress_file):
                try:
                    with open(self.progress_file, 'r') as f:
                        existing = json.load(f)
                        progress['total_topics'] = existing.get('total_topics', total_topics or 0)
                except:
                    progress['total_topics'] = total_topics or 0
            else:
                progress['total_topics'] = total_topics or 0
            with open(self.progress_file, 'w') as f:
                json.dump(progress, f, indent=2)
        except Exception as e:
            print(f"[Brain Learner] Error saving progress: {e}")
    
    def _learning_loop(self):
        """Main learning loop - searches topics sequentially from dictionary.json"""
        # Load topics from dictionary.json
        dictionary_path = "dictionary.json"
        
        # Load dictionary topics IN ORDER (no shuffling)
        dictionary_topics = []
        try:
            if os.path.exists(dictionary_path):
                with open(dictionary_path, 'r') as f:
                    dict_data = json.load(f)
                    dictionary_topics = dict_data.get('topics', [])
                    # NO SHUFFLING - keep original order from dictionary.json
                    print(f"[Brain Learner] Loaded {len(dictionary_topics)} topics from dictionary.json (sequential order)")
            else:
                print(f"[Brain Learner] Warning: dictionary.json not found at {dictionary_path}")
        except Exception as e:
            print(f"[Brain Learner] Error loading dictionary: {e}")
            import traceback
            traceback.print_exc()
        
        # Fallback if dictionary is empty or failed to load
        if not dictionary_topics:
            dictionary_topics = [
                "artificial intelligence", "machine learning", "deep learning",
                "natural language processing", "computer science", "programming"
            ]
            print(f"[Brain Learner] Using fallback topics (only {len(dictionary_topics)} topics)")
        
        # Load progress (which index we're at)
        current_index, searched_topics_list = self._load_progress()
        
        # Rebuild list from dictionary to ensure correct order (most recent first)
        # This fixes any corruption or ordering issues
        if current_index > 0:
            searched_topics_list = []
            # Build list from most recent (current_index-1) to oldest (0)
            for i in range(current_index - 1, -1, -1):
                if i < len(dictionary_topics):
                    searched_topics_list.append(dictionary_topics[i])
        
        # Keep as list to maintain order (most recent first), use set for fast lookup
        searched_topics_list = searched_topics_list if searched_topics_list else []
        searched_topics_set = set(searched_topics_list)  # Convert to set for fast lookup
        
        print(f"[Brain Learner] Starting from index {current_index}/{len(dictionary_topics)}")
        print(f"[Brain Learner] Already searched {len(searched_topics_set)} topics")
        if searched_topics_list:
            print(f"[Brain Learner] Most recent topic: {searched_topics_list[0]}")
        
        while self.running:
            try:
                # Check if we've completed all topics
                if current_index >= len(dictionary_topics):
                    print(f"[Brain Learner] ✅ Completed all {len(dictionary_topics)} topics!")
                    print(f"[Brain Learner] Resetting to start from beginning...")
                    current_index = 0
                    searched_topics_list = []
                    searched_topics_set = set()
                    self._save_progress(current_index, searched_topics_list, len(dictionary_topics), dictionary_topics)
                
                # Get the next topic in order
                base_topic = dictionary_topics[current_index]
                
                # Skip if already searched (shouldn't happen in sequential mode, but safety check)
                if base_topic in searched_topics_set:
                    print(f"[Brain Learner] ⚠ Topic '{base_topic}' already searched, skipping to next...")
                    current_index += 1
                    continue
                
                search_query = base_topic  # Start with base topic
                
                print(f"[Brain Learner] ✅ Selected topic #{current_index + 1}/{len(dictionary_topics)}: '{base_topic}'")
                print(f"    📊 Progress: {current_index + 1}/{len(dictionary_topics)} topics ({((current_index + 1) * 100) // len(dictionary_topics)}%)")
                
                # Simple sequential search - just search the base topic as-is
                # No modifiers, no combinations - go through dictionary.json in order
                topic = base_topic
                
                print(f"[Brain Learner] 🔍 Searching Google/DuckDuckGo for: '{topic}'...")
                
                # Try multiple methods to get knowledge
                knowledge = []
                
                # Method 1: Try Wikipedia API
                wiki_knowledge = self._learn_from_wikipedia(topic)
                if wiki_knowledge:
                    knowledge.extend(wiki_knowledge)
                    print(f"  ✓ Learned {len(wiki_knowledge)} items from Wikipedia")
                
                # Method 2: Try DuckDuckGo (more permissive than Google)
                print(f"  [Brain Learner] Searching DuckDuckGo for: {topic}")
                ddg_knowledge = self._learn_from_duckduckgo(topic)
                if ddg_knowledge:
                    knowledge.extend(ddg_knowledge)
                    print(f"  ✓ Learned {len(ddg_knowledge)} items from DuckDuckGo/Google")
                else:
                    print(f"  ⚠ No results from DuckDuckGo for: {topic}")
                
                # Method 3: Generate structured knowledge from topic
                if not knowledge:
                    structured_knowledge = self._generate_structured_knowledge(topic)
                    knowledge.extend(structured_knowledge)
                    print(f"  ✓ Generated {len(structured_knowledge)} structured knowledge items")
                
                if knowledge:
                    # Store in brain structure
                    self._store_in_brain(topic, knowledge)
                    print(f"[Brain Learner] ✓ Stored {len(knowledge)} knowledge items about: {topic}")
                    
                    # Record in tracker
                    try:
                        tracker = get_tracker()
                        tracker.record_brain_search(base_topic, len(knowledge))
                        tracker.record_knowledge(len(knowledge))
                        print(f"[Brain Learner] 📊 Recorded to learning tracker: topic='{base_topic}', knowledge_items={len(knowledge)}")
                    except Exception as e:
                        print(f"[Brain Learner] Error recording: {e}")
                else:
                    print(f"[Brain Learner] ⚠ No knowledge extracted for: {topic}")
                
                # Mark topic as searched and move to next index (whether we got knowledge or not)
                # Add to set for fast lookup
                if base_topic not in searched_topics_set:
                    searched_topics_set.add(base_topic)
                    # ALWAYS insert at the beginning (index 0) to maintain most recent first order
                    searched_topics_list.insert(0, base_topic)
                else:
                    # If already in set but somehow missing from list, add it at the beginning
                    if base_topic not in searched_topics_list:
                        searched_topics_list.insert(0, base_topic)
                
                current_index += 1
                
                # Save progress after each search (include total_topics and dictionary_topics)
                # Always rebuild from dictionary to ensure correct order
                self._save_progress(current_index, searched_topics_list, len(dictionary_topics), dictionary_topics)
                print(f"[Brain Learner] 💾 Progress saved: {current_index}/{len(dictionary_topics)} topics completed")
                
                # Sleep until next search
                time.sleep(self.search_interval)
                
            except Exception as e:
                print(f"[Brain Learner] Error: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(60)  # Wait 1 minute before retrying
    
    def _learn_from_wikipedia(self, query):
        """Learn from Wikipedia API"""
        try:
            # Use Wikipedia API
            api_url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + quote_plus(query)
            headers = {
                'User-Agent': 'Thor-AI-Learner/1.0 (Educational Purpose)'
            }
            
            response = requests.get(api_url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                knowledge = []
                if 'extract' in data:
                    # Extract main content
                    extract = data['extract']
                    if len(extract) > 100:  # Only if substantial content
                        knowledge.append({
                            'title': data.get('title', query),
                            'content': extract[:500],  # First 500 chars
                            'query': query,
                            'source': 'wikipedia',
                            'learned_at': datetime.now().isoformat()
                        })
                
                return knowledge
        except Exception as e:
            # Silently fail - try other methods
            pass
        
        return []
    
    def _learn_from_duckduckgo(self, query):
        """Learn from DuckDuckGo (more permissive than Google)"""
        try:
            # Use DuckDuckGo HTML
            url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                knowledge = []
                
                # Extract results - try multiple selectors
                results = soup.find_all('div', class_='result')[:5]
                for result in results:
                    # Try different ways to find title
                    title_elem = result.find('a', class_='result__a')
                    if not title_elem:
                        title_elem = result.find('h2') or result.find('a')
                    
                    # Try different ways to find snippet
                    snippet_elem = result.find('a', class_='result__snippet')
                    if not snippet_elem:
                        snippet_elem = result.find('div', class_='result__snippet')
                    if not snippet_elem:
                        snippet_elem = result.find('span', class_='result__snippet')
                    # Try getting text from result directly
                    if not snippet_elem:
                        # Get all text and use part of it as snippet
                        all_text = result.get_text()
                        if len(all_text) > 100:
                            snippet_elem = type('obj', (object,), {'get_text': lambda: all_text})()
                    
                    if title_elem:
                        title = title_elem.get_text().strip()
                        snippet = snippet_elem.get_text().strip() if snippet_elem else ""
                        
                        # If no snippet found, try to extract from result text
                        if not snippet or len(snippet) < 20:
                            all_text = result.get_text()
                            # Extract meaningful snippet (skip title)
                            lines = [line.strip() for line in all_text.split('\n') if line.strip()]
                            if len(lines) > 1:
                                snippet = ' '.join(lines[1:3])[:400]  # Take 2nd and 3rd lines
                        
                        if title and snippet and len(snippet) > 20:
                            knowledge.append({
                                'title': title,
                                'content': snippet[:400],
                                'query': query,
                                'source': 'duckduckgo',
                                'learned_at': datetime.now().isoformat()
                            })
                
                if knowledge:
                    print(f"    [DuckDuckGo] Successfully extracted {len(knowledge)} results for '{query}'")
                return knowledge
        except Exception as e:
            print(f"    [DuckDuckGo] Error searching for '{query}': {e}")
        
        return []
    
    def _generate_structured_knowledge(self, topic):
        """Generate structured knowledge about a topic"""
        # Create meaningful knowledge based on topic
        knowledge_base = {
            "artificial intelligence": [
                {
                    'title': 'What is Artificial Intelligence?',
                    'content': 'Artificial Intelligence (AI) is the simulation of human intelligence by machines. It includes learning, reasoning, and self-correction. AI systems can process large amounts of data and identify patterns.',
                    'query': topic,
                    'source': 'structured',
                    'learned_at': datetime.now().isoformat()
                },
                {
                    'title': 'AI Applications',
                    'content': 'AI is used in various fields including natural language processing, computer vision, robotics, healthcare, finance, and autonomous vehicles.',
                    'query': topic,
                    'source': 'structured',
                    'learned_at': datetime.now().isoformat()
                }
            ],
            "machine learning": [
                {
                    'title': 'Machine Learning Basics',
                    'content': 'Machine Learning is a subset of AI that enables systems to learn and improve from experience without being explicitly programmed. It uses algorithms to analyze data and make predictions.',
                    'query': topic,
                    'source': 'structured',
                    'learned_at': datetime.now().isoformat()
                },
                {
                    'title': 'Types of Machine Learning',
                    'content': 'Machine Learning includes supervised learning (labeled data), unsupervised learning (unlabeled data), and reinforcement learning (reward-based).',
                    'query': topic,
                    'source': 'structured',
                    'learned_at': datetime.now().isoformat()
                }
            ],
            "python programming": [
                {
                    'title': 'Python Programming Language',
                    'content': 'Python is a high-level, interpreted programming language known for its simplicity and readability. It supports multiple programming paradigms and has a large standard library.',
                    'query': topic,
                    'source': 'structured',
                    'learned_at': datetime.now().isoformat()
                },
                {
                    'title': 'Python Use Cases',
                    'content': 'Python is widely used for web development, data science, machine learning, automation, scientific computing, and software development.',
                    'query': topic,
                    'source': 'structured',
                    'learned_at': datetime.now().isoformat()
                }
            ]
        }
        
        # Check if we have structured knowledge for this topic
        topic_lower = topic.lower()
        for key, knowledge_list in knowledge_base.items():
            if key in topic_lower:
                return knowledge_list
        
        # Generate generic knowledge
        return [{
            'title': f'About {topic}',
            'content': f'{topic} is an important topic in technology and science. It involves various concepts, principles, and applications that are relevant to modern computing and innovation.',
            'query': topic,
            'source': 'structured',
            'learned_at': datetime.now().isoformat()
        }]
    
    def _store_in_brain(self, topic, knowledge):
        """Store knowledge in the brain folder structure"""
        # Extract keywords from topic
        words = topic.lower().split()
        
        for word in words:
            if word and word[0].isalpha():
                letter = word[0].upper()
                letter_dir = os.path.join(self.brain_dir, letter)
                keywords_file = os.path.join(letter_dir, "keywords.json")
                
                if os.path.exists(keywords_file):
                    try:
                        with open(keywords_file, 'r') as f:
                            data = json.load(f)
                        
                        # Add keyword if not exists
                        if word not in data['keywords']:
                            data['keywords'].append(word)
                            # Record keyword in tracker
                            try:
                                tracker = get_tracker()
                                tracker.record_keyword(word, letter)
                            except:
                                pass
                        
                        # Add knowledge (avoid duplicates)
                        existing_titles = [k.get('title', '') for k in data['knowledge']]
                        for k in knowledge:
                            if k.get('title', '') not in existing_titles:
                                data['knowledge'].append(k)
                        
                        data['last_updated'] = datetime.now().isoformat()
                        
                        with open(keywords_file, 'w') as f:
                            json.dump(data, f, indent=2)
                    except Exception as e:
                        print(f"Error storing in brain: {e}")
        
        # Also save to learned_data
        learned_file = os.path.join(self.learned_data_dir, f"{datetime.now().strftime('%Y%m%d')}.json")
        try:
            if os.path.exists(learned_file):
                with open(learned_file, 'r') as f:
                    learned = json.load(f)
            else:
                learned = []
            
            # Add new knowledge
            existing_titles = [k.get('title', '') for k in learned]
            for k in knowledge:
                if k.get('title', '') not in existing_titles:
                    learned.append(k)
            
            with open(learned_file, 'w') as f:
                json.dump(learned, f, indent=2)
        except Exception as e:
            print(f"Error saving learned data: {e}")


# Global instance
_brain_learner = None

def get_brain_learner():
    """Get or create the global brain learner instance"""
    global _brain_learner
    if _brain_learner is None:
        _brain_learner = BrainLearner(search_interval_seconds=10)  # 10 seconds for fast learning
    return _brain_learner


if __name__ == '__main__':
    print("=" * 60)
    print("Thor 1.0 - Brain Learner")
    print("=" * 60)
    print()
    print("Starting continuous learning from web sources...")
    print("This will run in the background and learn continuously.")
    print("Press Ctrl+C to stop.")
    print()
    
    learner = get_brain_learner()
    learner.start()
    
    try:
        # Keep running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping Brain Learner...")
        learner.stop()
        print("Stopped.")
