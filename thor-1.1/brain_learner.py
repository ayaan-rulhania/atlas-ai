#!/usr/bin/env python3
"""
Continuous Knowledge Acquisition System for Thor 1.1 (Enhanced with SQLite)
Uses multiple sources to continuously learn and store knowledge in a persistent database.
Supports mixed topic discovery: dictionary + user queries + trending topics.
"""
import os
import time
import random
import json
import threading
import signal
import sys
from datetime import datetime, timedelta
from urllib.parse import quote_plus
from typing import List, Dict, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from bs4 import BeautifulSoup

# Import our SQLite knowledge database directly (avoid __init__ import issues)
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.knowledge_db import get_knowledge_db, KnowledgeDatabase
from services.learning_tracker import get_tracker

# Try to import trending topics (optional)
try:
    from services.trending_topics import get_trending_topics_service
    TRENDING_AVAILABLE = True
except ImportError:
    TRENDING_AVAILABLE = False

# Try to import research engine for better knowledge acquisition
try:
    from services.research_engine import get_research_engine
    RESEARCH_ENGINE_AVAILABLE = True
except ImportError:
    RESEARCH_ENGINE_AVAILABLE = False


class BrainLearner:
    """
    Continuously learns from web searches and knowledge sources.
    Uses SQLite for persistent storage with mixed topic discovery strategy.
    """
    
    def __init__(
        self,
        search_interval_seconds: int = 5,  # Reduced default from 30 to 5
        db_path: str = None,
        dictionary_path: str = None,
        parallel_workers: int = 4  # Number of parallel workers
    ):
        self.search_interval = search_interval_seconds
        self.parallel_workers = parallel_workers
        self.running = False
        self.paused = False
        self.thread = None
        self.session_id = None
        
        # Thread pool for parallel processing
        self.executor = ThreadPoolExecutor(max_workers=parallel_workers)
        
        # Initialize SQLite database
        self.db = get_knowledge_db(db_path)
        
        # Dictionary path
        self.dictionary_path = dictionary_path or os.path.join(
            os.path.dirname(__file__), "dictionary.json"
        )
        
        # Legacy brain directory for backwards compatibility
        self.brain_dir = "brain"
        self.learned_data_dir = "learned_data"
        os.makedirs(self.brain_dir, exist_ok=True)
        os.makedirs(self.learned_data_dir, exist_ok=True)
        
        # Rate limiting (reduced for faster crawling)
        self.last_request_time = {}
        self.min_request_interval = 0.5  # Reduced from 2.0 to 0.5 seconds
        self.consecutive_errors = 0
        self.max_consecutive_errors = 5
        
        # Thread-safe locks
        self.db_lock = threading.Lock()
        self.stats_lock = threading.Lock()
        
        # User agent for web requests
        self.user_agent = (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
        
        # Topic source weights for mixed discovery
        self.topic_source_weights = {
            'dictionary': 0.5,      # 50% from dictionary
            'user_query': 0.3,      # 30% from user queries
            'trending': 0.15,       # 15% from trending
            'discovered': 0.05     # 5% from discovered related topics
        }
        
        # Initialize brain structure for legacy compatibility
        self._initialize_brain()
        
        # Load dictionary topics into database
        self._load_dictionary_topics()
        
        print(f"[BrainLearner] Initialized with SQLite database")
        print(f"[BrainLearner] Search interval: {self.search_interval}s")
        print(f"[BrainLearner] Parallel workers: {self.parallel_workers}")
    
    def _initialize_brain(self):
        """Initialize the brain folder structure with letters (legacy compatibility)."""
        letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        
        for letter in letters:
            letter_dir = os.path.join(self.brain_dir, letter)
            os.makedirs(letter_dir, exist_ok=True)
            
            keywords_file = os.path.join(letter_dir, "keywords.json")
            if not os.path.exists(keywords_file):
                with open(keywords_file, 'w') as f:
                    json.dump({
                        "letter": letter,
                        "keywords": [],
                        "knowledge": [],
                        "last_updated": datetime.now().isoformat()
                    }, f, indent=2)
    
    def _load_dictionary_topics(self):
        """Load topics from dictionary.json into the database."""
        if not os.path.exists(self.dictionary_path):
            print(f"[BrainLearner] Warning: Dictionary not found at {self.dictionary_path}")
            return
        
        try:
            with open(self.dictionary_path, 'r') as f:
                dictionary = json.load(f)
            
            topics = dictionary.get('topics', [])
            if not topics:
                print("[BrainLearner] Warning: No topics found in dictionary")
                return
            
            # Prepare topics with categories if available
            topic_data = []
            categories = dictionary.get('categories', {})
            
            for topic in topics:
                # Determine category based on topic content (simple heuristic)
                category = self._guess_category(topic, categories)
                topic_data.append({
                    'topic': topic,
                    'category': category,
                    'source': 'dictionary',
                    'priority': 5
                })
            
            added, existing = self.db.add_topics_batch(topic_data)
            print(f"[BrainLearner] Loaded dictionary: {added} new topics, {existing} existing")
            
        except Exception as e:
            print(f"[BrainLearner] Error loading dictionary: {e}")
            import traceback
            traceback.print_exc()
    
    def _guess_category(self, topic: str, categories: Dict) -> str:
        """Guess category for a topic based on keywords."""
        topic_lower = topic.lower()
        
        # Simple keyword-based categorization
        if any(kw in topic_lower for kw in ['programming', 'code', 'software', 'api', 'database', 'algorithm']):
            return 'programming_and_software'
        elif any(kw in topic_lower for kw in ['ai', 'machine learning', 'neural', 'deep learning']):
            return 'science_and_technology'
        elif any(kw in topic_lower for kw in ['history', 'war', 'empire', 'ancient', 'medieval']):
            return 'history_and_geography'
        elif any(kw in topic_lower for kw in ['math', 'calculus', 'algebra', 'physics', 'quantum']):
            return 'mathematics_and_physics'
        elif any(kw in topic_lower for kw in ['biology', 'cell', 'dna', 'gene', 'medicine']):
            return 'biology_and_medicine'
        elif any(kw in topic_lower for kw in ['art', 'music', 'literature', 'film', 'dance']):
            return 'arts_and_culture'
        elif any(kw in topic_lower for kw in ['economics', 'finance', 'business', 'market']):
            return 'economics_and_business'
        elif any(kw in topic_lower for kw in ['philosophy', 'psychology', 'ethics', 'mind']):
            return 'philosophy_and_psychology'
        else:
            return 'general'
    
    def start(self):
        """Start the continuous learning process."""
        if self.running:
            print("[BrainLearner] Already running")
            return
        
        self.running = True
        self.paused = False
        
        # Start a learning session
        self.session_id = self.db.start_learning_session()
        print(f"[BrainLearner] Started learning session {self.session_id}")
        
        self.thread = threading.Thread(target=self._learning_loop, daemon=True)
        self.thread.start()
        print(f"[BrainLearner] Started - searching every {self.search_interval} seconds")
    
    def stop(self):
        """Stop the learning process gracefully."""
        print("[BrainLearner] Stopping...")
        self.running = False
        
        # Shutdown thread pool
        self.executor.shutdown(wait=True, timeout=30)
        
        if self.session_id:
            self.db.end_learning_session(self.session_id)
            stats = self.db.get_session_stats(self.session_id)
            if stats:
                print(f"[BrainLearner] Session {self.session_id} ended:")
                print(f"  - Topics crawled: {stats['topics_crawled']}")
                print(f"  - Knowledge items added: {stats['knowledge_items_added']}")
                print(f"  - Errors: {stats['errors_encountered']}")
        
        if self.thread:
            self.thread.join(timeout=10)
        
        print("[BrainLearner] Stopped")
    
    def pause(self):
        """Pause the learning process."""
        self.paused = True
        print("[BrainLearner] Paused")
    
    def resume(self):
        """Resume the learning process."""
        self.paused = False
        print("[BrainLearner] Resumed")
    
    def _learning_loop(self):
        """Main learning loop - uses parallel processing for faster learning."""
        print("[BrainLearner] Learning loop started (parallel mode)")
        
        # Track active futures
        active_futures = {}
        
        while self.running:
            try:
                # Check if paused
                if self.paused:
                    time.sleep(1)
                    continue
                
                # Submit new tasks if we have capacity
                while len(active_futures) < self.parallel_workers:
                    # Get next topic using mixed strategy
                    topic_data = self._get_next_topic()
                    
                    if not topic_data:
                        break  # No more topics available
                    
                    topic = topic_data['topic']
                    topic_id = topic_data['id']
                    source = topic_data.get('source', 'unknown')
                    
                    # Submit learning task to thread pool
                    future = self.executor.submit(self._learn_and_store_topic, topic, topic_id, source)
                    active_futures[future] = (topic, topic_id)
                
                # Process completed tasks
                if active_futures:
                    done, not_done = [], []
                    for future in active_futures:
                        if future.done():
                            done.append(future)
                        else:
                            not_done.append(future)
                    
                    # Process completed futures
                    for future in done:
                        topic, topic_id = active_futures.pop(future)
                        try:
                            result = future.result()
                            if result:
                                successful, duplicates = result
                                print(f"[BrainLearner] ✓ Completed '{topic}': {successful} items ({duplicates} duplicates)")
                        except Exception as e:
                            print(f"[BrainLearner] Error processing '{topic}': {e}")
                            with self.db_lock:
                                self.db.update_topic_status(
                                    topic_id=topic_id,
                                    status='error',
                                    error=str(e)[:100]
                                )
                
                # If no active tasks and no topics, wait a bit
                if not active_futures:
                    time.sleep(self.search_interval)
                else:
                    # Small sleep to avoid busy waiting
                    time.sleep(0.1)
                
            except Exception as e:
                self.consecutive_errors += 1
                print(f"[BrainLearner] Error in learning loop: {e}")
                import traceback
                traceback.print_exc()
                
                # Exponential backoff on consecutive errors
                if self.consecutive_errors >= self.max_consecutive_errors:
                    wait_time = min(300, 60 * (2 ** (self.consecutive_errors - self.max_consecutive_errors)))
                    print(f"[BrainLearner] Too many errors, waiting {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    time.sleep(5)
        
        # Wait for all active tasks to complete
        print("[BrainLearner] Waiting for active tasks to complete...")
        for future in active_futures:
            try:
                future.result(timeout=30)
            except Exception:
                pass
    
    def _learn_and_store_topic(self, topic: str, topic_id: int, source: str) -> Optional[Tuple[int, int]]:
        """Learn about a topic and store results (thread-safe)."""
        try:
            print(f"[BrainLearner] 🔍 Learning: '{topic}' (source: {source})")
            
            # Learn from multiple sources
            knowledge = self._learn_topic(topic)
            
            if knowledge:
                # Store in SQLite database (thread-safe)
                with self.db_lock:
                    successful, duplicates = self.db.add_knowledge_batch(knowledge)
                    
                    # Update topic status
                    self.db.update_topic_status(
                        topic_id=topic_id,
                        status='crawled',
                        knowledge_count=successful
                    )
                    
                    # Update session stats
                    if self.session_id:
                        self.db.update_learning_session(
                            self.session_id,
                            topics_crawled=1,
                            knowledge_added=successful
                        )
                    
                    # Extract and add related topics
                    self._extract_related_topics(topic_id, knowledge)
                
                # Store in legacy brain (not critical, can be async)
                try:
                    self._store_in_brain(topic, knowledge)
                except:
                    pass
                
                # Record in tracker
                try:
                    tracker = get_tracker()
                    tracker.record_brain_search(topic, successful)
                    tracker.record_knowledge(successful)
                except:
                    pass
                
                return (successful, duplicates)
            else:
                # Mark topic as having no results
                with self.db_lock:
                    self.db.update_topic_status(
                        topic_id=topic_id,
                        status='no_results'
                    )
                return None
                
        except Exception as e:
            print(f"[BrainLearner] Error learning '{topic}': {e}")
            with self.db_lock:
                self.db.update_topic_status(
                    topic_id=topic_id,
                    status='error',
                    error=str(e)[:100]
                )
            return None
    
    def _get_next_topic(self) -> Optional[Dict]:
        """
        Get the next topic to learn using mixed discovery strategy.
        Weights: 50% dictionary, 30% user queries, 15% trending, 5% discovered
        """
        # Roll to determine source
        roll = random.random()
        cumulative = 0
        selected_source = 'dictionary'
        
        for source, weight in self.topic_source_weights.items():
            cumulative += weight
            if roll <= cumulative:
                selected_source = source
                break
        
        # Try to get topic from selected source
        topic = None
        
        if selected_source == 'user_query':
            # Get unanswered user queries
            unanswered = self.db.get_unanswered_topics(limit=10)
            if unanswered:
                topic_name = random.choice(unanswered)
                # Add as topic if not exists and get it
                self.db.add_topic(topic_name, source='user_query', priority=8)
        
        elif selected_source == 'trending' and TRENDING_AVAILABLE:
            try:
                trending_service = get_trending_topics_service()
                trending = trending_service.get_trending_topics(limit=10)
                if trending:
                    topic_name = random.choice(trending)
                    self.db.add_topic(topic_name, source='trending', priority=7)
            except Exception as e:
                print(f"[BrainLearner] Trending error: {e}")
        
        # Default to getting next topic from database
        topic = self.db.get_next_topic()
        
        return topic
    
    def _wait_for_rate_limit(self, worker_id: str = "default"):
        """Wait if needed to respect rate limits (per-worker)."""
        if worker_id not in self.last_request_time:
            self.last_request_time[worker_id] = 0
        
        elapsed = time.time() - self.last_request_time[worker_id]
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time[worker_id] = time.time()
    
    def _learn_topic(self, topic: str) -> List[Dict]:
        """Learn about a topic from multiple sources (optimized for speed)."""
        knowledge = []
        worker_id = threading.current_thread().name
        
        # Parallel requests to different sources
        def get_wikipedia():
            return self._learn_from_wikipedia(topic)
        
        def get_duckduckgo():
            return self._learn_from_duckduckgo(topic)
        
        def get_research():
            if RESEARCH_ENGINE_AVAILABLE:
                try:
                    research_engine = get_research_engine()
                    research_knowledge = research_engine.search_and_learn(topic)
                    if research_knowledge:
                        # Convert to our format
                        result = []
                        for item in research_knowledge:
                            result.append({
                                'topic': topic,
                                'title': item.get('title', ''),
                                'content': item.get('content', ''),
                                'source': item.get('source', 'research_engine'),
                                'url': item.get('url', ''),
                                'confidence': 0.8,
                                'learned_at': datetime.now().isoformat()
                            })
                        return result
                except:
                    pass
            return []
        
        # Execute requests in parallel
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(get_wikipedia): 'wikipedia',
                executor.submit(get_duckduckgo): 'duckduckgo',
                executor.submit(get_research): 'research'
            }
            
            for future in as_completed(futures):
                source_name = futures[future]
                try:
                    result = future.result(timeout=10)  # 10 second timeout per source
                    if result:
                        knowledge.extend(result)
                except Exception as e:
                    pass  # Silently continue if one source fails
        
        # If we still need more, try Wikipedia search
        if len(knowledge) < 3:
            try:
                wiki_search = self._learn_from_wikipedia_search(topic)
                if wiki_search:
                    knowledge.extend(wiki_search)
            except:
                pass
        
        return knowledge
    
    def _learn_from_wikipedia(self, query: str) -> List[Dict]:
        """Learn from Wikipedia REST API."""
        try:
            # Use Wikipedia summary API
            api_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote_plus(query)}"
            headers = {
                'User-Agent': 'Thor-AI-Learner/1.1 (Educational Purpose)',
                'Accept': 'application/json'
            }
            
            response = requests.get(api_url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                knowledge = []
                
                if 'extract' in data and len(data['extract']) > 100:
                    # Get full extract, not truncated
                    extract = data.get('extract', '')
                    
                    knowledge.append({
                        'topic': query,
                        'title': data.get('title', query),
                        'content': extract,
                        'source': 'wikipedia',
                        'url': data.get('content_urls', {}).get('desktop', {}).get('page', ''),
                        'confidence': 0.9,  # High confidence for Wikipedia
                        'learned_at': datetime.now().isoformat()
                    })
                
                return knowledge
            
            elif response.status_code == 404:
                # Topic not found directly, will try search
                return []
                
        except requests.exceptions.Timeout:
            print(f"  ⚠ Wikipedia timeout for: {query}")
        except Exception as e:
            print(f"  ⚠ Wikipedia error: {e}")
        
        return []
    
    def _learn_from_wikipedia_search(self, query: str) -> List[Dict]:
        """Search Wikipedia and learn from top results."""
        try:
            # Use Wikipedia search API
            api_url = "https://en.wikipedia.org/w/api.php"
            params = {
                'action': 'query',
                'list': 'search',
                'srsearch': query,
                'srlimit': 3,
                'format': 'json'
            }
            headers = {
                'User-Agent': 'Thor-AI-Learner/1.1 (Educational Purpose)'
            }
            
            response = requests.get(api_url, params=params, headers=headers, timeout=15)
            
            if response.status_code != 200:
                return []
            
            data = response.json()
            results = data.get('query', {}).get('search', [])
            
            knowledge = []
            for result in results[:2]:  # Top 2 results
                title = result.get('title', '')
                if title:
                    # Get summary for each result
                    summary = self._learn_from_wikipedia(title)
                    if summary:
                        # Update topic to original query
                        for item in summary:
                            item['topic'] = query
                        knowledge.extend(summary)
            
            return knowledge
            
        except Exception as e:
            print(f"  ⚠ Wikipedia search error: {e}")
        
        return []
    
    def _learn_from_duckduckgo(self, query: str) -> List[Dict]:
        """Learn from DuckDuckGo HTML results."""
        try:
            url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
            headers = {
                'User-Agent': self.user_agent,
                'Accept-Language': 'en-US,en;q=0.9'
            }
            
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            knowledge = []
            
            # Find result divs
            results = soup.find_all('div', class_='result')[:5]
            
            for result in results:
                title_elem = result.find('a', class_='result__a')
                snippet_elem = result.find('a', class_='result__snippet')
                
                if not title_elem:
                    continue
                
                title = title_elem.get_text().strip()
                href = title_elem.get('href', '')
                
                # Get snippet
                snippet = ""
                if snippet_elem:
                    snippet = snippet_elem.get_text().strip()
                else:
                    # Try to get text from result
                    snippet_div = result.find('div', class_='result__snippet')
                    if snippet_div:
                        snippet = snippet_div.get_text().strip()
                
                # Filter out low quality content
                if not snippet or len(snippet) < 50:
                    continue
                
                # Filter promotional content
                promo_patterns = [
                    'shop now', 'buy now', 'click here', 'sign up',
                    'subscribe', 'free trial', 'download now'
                ]
                if any(p in snippet.lower() for p in promo_patterns):
                    continue
                
                knowledge.append({
                    'topic': query,
                    'title': title,
                    'content': snippet,
                    'source': 'duckduckgo',
                    'url': href,
                    'confidence': 0.7,
                    'learned_at': datetime.now().isoformat()
                })
            
            return knowledge
            
        except requests.exceptions.Timeout:
            print(f"  ⚠ DuckDuckGo timeout for: {query}")
        except Exception as e:
            print(f"  ⚠ DuckDuckGo error: {e}")
        
        return []
    
    def _extract_related_topics(self, topic_id: int, knowledge: List[Dict]):
        """Extract and add related topics from learned knowledge."""
        related = set()
        
        for item in knowledge:
            content = item.get('content', '').lower()
            title = item.get('title', '').lower()
            
            # Extract potential topics from content (simple heuristic)
            # Look for "also known as", "related to", "see also" patterns
            patterns = [
                r'also known as ([^.]+)',
                r'related to ([^.]+)',
                r'similar to ([^.]+)',
                r'type of ([^.]+)',
                r'form of ([^.]+)'
            ]
            
            import re
            for pattern in patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    # Clean and add
                    topic = match.strip().strip(',')
                    if 3 < len(topic) < 50 and topic not in related:
                        related.add(topic)
        
        # Add related topics to database
        for related_topic in list(related)[:5]:  # Limit to 5 related topics
            self.db.add_related_topic(topic_id, related_topic)
    
    def _store_in_brain(self, topic: str, knowledge: List[Dict]):
        """Store knowledge in legacy brain folder structure for compatibility."""
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
                        
                        # Add keyword
                        if word not in data.get('keywords', []):
                            data.setdefault('keywords', []).append(word)
                        
                        # Add knowledge
                        existing_titles = [k.get('title', '') for k in data.get('knowledge', [])]
                        for k in knowledge:
                            if k.get('title', '') not in existing_titles:
                                data.setdefault('knowledge', []).append(k)
                        
                        data['last_updated'] = datetime.now().isoformat()
                        
                        with open(keywords_file, 'w') as f:
                            json.dump(data, f, indent=2)
                    except Exception as e:
                        print(f"  ⚠ Brain storage error: {e}")
    
    def get_stats(self) -> Dict:
        """Get current learning statistics."""
        db_stats = self.db.get_database_stats()
        
        return {
            'database': db_stats,
            'session': {
                'id': self.session_id,
                'running': self.running,
                'paused': self.paused,
                'consecutive_errors': self.consecutive_errors
            }
        }
    
    def record_user_query(
        self,
        query: str,
        extracted_topics: List[str],
        knowledge_found: bool,
        needs_research: bool
    ):
        """Record a user query for adaptive learning."""
        self.db.record_user_query(
            query=query,
            extracted_topics=extracted_topics,
            knowledge_found=knowledge_found,
            needs_research=needs_research
        )


# Global instance
_brain_learner = None


def get_brain_learner(
    search_interval_seconds: int = 5,
    db_path: str = None,
    parallel_workers: int = 4
) -> BrainLearner:
    """Get or create the global brain learner instance."""
    global _brain_learner
    if _brain_learner is None:
        _brain_learner = BrainLearner(
            search_interval_seconds=search_interval_seconds,
            db_path=db_path,
            parallel_workers=parallel_workers
        )
    return _brain_learner


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    print("\n[BrainLearner] Received shutdown signal...")
    if _brain_learner:
        _brain_learner.stop()
    sys.exit(0)


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Thor 1.1 Brain Learner - Continuous Knowledge Acquisition')
    parser.add_argument('--interval', type=int, default=5,
                       help='Search interval in seconds (default: 5)')
    parser.add_argument('--workers', type=int, default=4,
                       help='Number of parallel workers (default: 4)')
    parser.add_argument('--db', type=str, default=None,
                       help='Path to SQLite database')
    parser.add_argument('--dictionary', type=str, default=None,
                       help='Path to dictionary.json')
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("  Thor 1.1 - Brain Learner (SQLite Enhanced)")
    print("  Continuous Knowledge Acquisition System")
    print("=" * 70)
    print()
    print(f"  Search Interval: {args.interval} seconds")
    print(f"  Database: {args.db or 'default (knowledge.db)'}")
    print()
    print("  Starting continuous learning from web sources...")
    print("  Press Ctrl+C to stop.")
    print()
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create and start learner
    learner = BrainLearner(
        search_interval_seconds=args.interval,
        db_path=args.db,
        dictionary_path=args.dictionary,
        parallel_workers=args.workers
    )
    learner.start()
    
    try:
        # Keep main thread alive and print stats periodically
        while True:
            time.sleep(60)  # Print stats every minute
            stats = learner.get_stats()
            db_stats = stats['database']
            print(f"\n[Stats] Knowledge: {db_stats['total_knowledge_items']} | "
                  f"Topics: {db_stats['total_topics']} | "
                  f"24h: +{db_stats['knowledge_added_24h']} items")
    except KeyboardInterrupt:
        print("\nStopping...")
        learner.stop()
        print("Stopped.")
