"""
Trending Topics Service - Discovers trending and popular topics for knowledge acquisition.
Uses multiple sources: Wikipedia, RSS feeds, and public APIs.
"""
import os
import json
import time
import random
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set
from urllib.parse import quote_plus
import requests
from bs4 import BeautifulSoup


class TrendingTopicsService:
    """
    Discovers trending topics from various sources for knowledge acquisition.
    Maintains a cache to avoid repeated lookups.
    """
    
    def __init__(self, cache_ttl_hours: int = 6):
        self.cache_ttl = timedelta(hours=cache_ttl_hours)
        self.cache_file = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "trending_cache.json"
        )
        
        self.user_agent = (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 1.0
        
        # Topic categories for filtering
        self.blocked_patterns = [
            'advertisement', 'sponsored', 'promoted',
            'stock price', 'betting odds', 'casino',
            'adult', 'explicit'
        ]
        
        self.cache = self._load_cache()
    
    def _load_cache(self) -> Dict:
        """Load trending topics cache from file."""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    cache = json.load(f)
                    # Check if cache is still valid
                    cached_time = datetime.fromisoformat(cache.get('timestamp', '2000-01-01'))
                    if datetime.now() - cached_time < self.cache_ttl:
                        return cache
            except Exception:
                pass
        return {'topics': [], 'timestamp': None}
    
    def _save_cache(self):
        """Save trending topics cache to file."""
        try:
            self.cache['timestamp'] = datetime.now().isoformat()
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            print(f"[TrendingTopics] Cache save error: {e}")
    
    def _wait_for_rate_limit(self):
        """Rate limiting between requests."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()
    
    def _is_valid_topic(self, topic: str) -> bool:
        """Check if a topic is valid for learning."""
        if not topic or len(topic) < 3 or len(topic) > 100:
            return False
        
        topic_lower = topic.lower()
        
        # Filter blocked patterns
        for pattern in self.blocked_patterns:
            if pattern in topic_lower:
                return False
        
        # Should contain mostly letters
        letter_count = sum(1 for c in topic if c.isalpha())
        if letter_count < len(topic) * 0.5:
            return False
        
        return True
    
    def get_trending_topics(self, limit: int = 50, refresh: bool = False) -> List[str]:
        """
        Get trending topics from all sources.
        Uses cache if available and not expired.
        """
        # Check cache first
        if not refresh and self.cache.get('topics'):
            cached_time = self.cache.get('timestamp')
            if cached_time:
                try:
                    cached_dt = datetime.fromisoformat(cached_time)
                    if datetime.now() - cached_dt < self.cache_ttl:
                        topics = self.cache['topics']
                        random.shuffle(topics)
                        return topics[:limit]
                except Exception:
                    pass
        
        # Fetch from all sources
        all_topics: Set[str] = set()
        
        # Source 1: Wikipedia Current Events
        wiki_topics = self._get_wikipedia_current_events()
        all_topics.update(wiki_topics)
        print(f"[TrendingTopics] Wikipedia: {len(wiki_topics)} topics")
        
        # Source 2: Wikipedia Featured Articles
        featured = self._get_wikipedia_featured()
        all_topics.update(featured)
        print(f"[TrendingTopics] Wikipedia Featured: {len(featured)} topics")
        
        # Source 3: Wikipedia On This Day
        on_this_day = self._get_wikipedia_on_this_day()
        all_topics.update(on_this_day)
        print(f"[TrendingTopics] On This Day: {len(on_this_day)} topics")
        
        # Source 4: Science/Tech News (RSS)
        tech_topics = self._get_tech_news_topics()
        all_topics.update(tech_topics)
        print(f"[TrendingTopics] Tech News: {len(tech_topics)} topics")
        
        # Source 5: Wikipedia Vital Articles (evergreen important topics)
        vital = self._get_vital_articles()
        all_topics.update(vital)
        print(f"[TrendingTopics] Vital Articles: {len(vital)} topics")
        
        # Filter and clean topics
        valid_topics = [t for t in all_topics if self._is_valid_topic(t)]
        
        # Update cache
        self.cache['topics'] = valid_topics
        self._save_cache()
        
        print(f"[TrendingTopics] Total: {len(valid_topics)} valid topics")
        
        # Return shuffled subset
        random.shuffle(valid_topics)
        return valid_topics[:limit]
    
    def _get_wikipedia_current_events(self) -> List[str]:
        """Get topics from Wikipedia Current Events portal."""
        topics = []
        try:
            self._wait_for_rate_limit()
            
            # Get today's date for the portal
            today = datetime.now()
            url = f"https://en.wikipedia.org/wiki/Portal:Current_events/{today.strftime('%B_%Y')}"
            
            headers = {'User-Agent': self.user_agent}
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code != 200:
                # Try main current events page
                url = "https://en.wikipedia.org/wiki/Portal:Current_events"
                response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find links in the current events content
                content = soup.find('div', {'class': 'mw-parser-output'})
                if content:
                    links = content.find_all('a', href=True)
                    for link in links[:100]:  # Limit to first 100 links
                        href = link.get('href', '')
                        title = link.get('title', '') or link.get_text()
                        
                        # Filter for article links
                        if href.startswith('/wiki/') and ':' not in href:
                            # Skip special pages
                            if not any(x in href.lower() for x in ['portal:', 'file:', 'help:', 'special:']):
                                topic = title.strip()
                                if topic:
                                    topics.append(topic)
        
        except Exception as e:
            print(f"[TrendingTopics] Current events error: {e}")
        
        return list(set(topics))[:30]
    
    def _get_wikipedia_featured(self) -> List[str]:
        """Get topics from Wikipedia's featured articles."""
        topics = []
        try:
            self._wait_for_rate_limit()
            
            # Use Wikipedia API to get featured content
            api_url = "https://en.wikipedia.org/api/rest_v1/feed/featured/{year}/{month}/{day}"
            today = datetime.now()
            url = api_url.format(
                year=today.year,
                month=str(today.month).zfill(2),
                day=str(today.day).zfill(2)
            )
            
            headers = {'User-Agent': self.user_agent}
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                # Featured article
                if 'tfa' in data:
                    title = data['tfa'].get('title', '')
                    if title:
                        topics.append(title)
                
                # Most read articles
                if 'mostread' in data:
                    for article in data['mostread'].get('articles', [])[:20]:
                        title = article.get('title', '').replace('_', ' ')
                        if title and not title.startswith('Main Page'):
                            topics.append(title)
                
                # On this day
                if 'onthisday' in data:
                    for item in data['onthisday'][:10]:
                        for page in item.get('pages', [])[:2]:
                            title = page.get('title', '').replace('_', ' ')
                            if title:
                                topics.append(title)
        
        except Exception as e:
            print(f"[TrendingTopics] Featured articles error: {e}")
        
        return list(set(topics))
    
    def _get_wikipedia_on_this_day(self) -> List[str]:
        """Get topics from Wikipedia's 'On This Day' feature."""
        topics = []
        try:
            self._wait_for_rate_limit()
            
            today = datetime.now()
            url = f"https://en.wikipedia.org/api/rest_v1/feed/onthisday/all/{today.month}/{today.day}"
            
            headers = {'User-Agent': self.user_agent}
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                for category in ['events', 'births', 'deaths', 'holidays']:
                    for item in data.get(category, [])[:10]:
                        for page in item.get('pages', [])[:2]:
                            title = page.get('title', '').replace('_', ' ')
                            if title:
                                topics.append(title)
        
        except Exception as e:
            print(f"[TrendingTopics] On This Day error: {e}")
        
        return list(set(topics))[:30]
    
    def _get_tech_news_topics(self) -> List[str]:
        """Get topics from tech news RSS feeds."""
        topics = []
        
        # RSS feeds for tech/science news
        feeds = [
            "https://feeds.arstechnica.com/arstechnica/science",
            "https://www.sciencedaily.com/rss/all.xml",
            "https://feeds.feedburner.com/TechCrunch/",
        ]
        
        for feed_url in feeds:
            try:
                self._wait_for_rate_limit()
                
                headers = {'User-Agent': self.user_agent}
                response = requests.get(feed_url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'xml')
                    
                    # Try to find items/entries
                    items = soup.find_all('item')[:10] or soup.find_all('entry')[:10]
                    
                    for item in items:
                        title = item.find('title')
                        if title:
                            topic = title.get_text().strip()
                            # Clean up the topic
                            topic = topic.split('|')[0].strip()
                            topic = topic.split(' - ')[0].strip()
                            if topic:
                                topics.append(topic)
            
            except Exception as e:
                # Skip failed feeds silently
                continue
        
        return list(set(topics))[:20]
    
    def _get_vital_articles(self) -> List[str]:
        """Get a sample of Wikipedia's vital articles (important evergreen topics)."""
        # Pre-defined list of important topics to ensure coverage
        vital_topics = [
            # Science
            "Evolution", "DNA", "Cell biology", "Climate change", "Photosynthesis",
            "Periodic table", "Atom", "Molecule", "Energy", "Force",
            "Gravity", "Electromagnetism", "Thermodynamics", "Entropy",
            
            # Technology
            "Internet", "Computer", "Artificial intelligence", "Algorithm",
            "Programming language", "Software engineering", "Database",
            "Operating system", "Computer network", "Cybersecurity",
            
            # History
            "World War I", "World War II", "Cold War", "Industrial Revolution",
            "Renaissance", "Ancient Rome", "Ancient Greece", "Ancient Egypt",
            "Colonialism", "French Revolution", "American Revolution",
            
            # Geography
            "Earth", "Ocean", "Mountain", "River", "Climate",
            "Continent", "Europe", "Asia", "Africa", "Americas",
            
            # Arts
            "Literature", "Music", "Painting", "Sculpture", "Architecture",
            "Film", "Theatre", "Dance", "Photography",
            
            # Philosophy
            "Philosophy", "Ethics", "Logic", "Metaphysics", "Epistemology",
            "Democracy", "Human rights", "Justice", "Freedom",
            
            # Economics
            "Economics", "Capitalism", "Market economy", "Trade",
            "Inflation", "Unemployment", "Globalization",
            
            # Biology
            "Human body", "Brain", "Heart", "Immune system",
            "Genetics", "Virus", "Bacteria", "Ecology"
        ]
        
        # Shuffle and return a subset
        random.shuffle(vital_topics)
        return vital_topics[:20]
    
    def get_topics_by_category(self, category: str, limit: int = 20) -> List[str]:
        """Get trending topics filtered by category."""
        all_topics = self.get_trending_topics(limit=100, refresh=False)
        
        # Simple category filtering based on keywords
        category_keywords = {
            'science': ['science', 'research', 'study', 'discovery', 'experiment'],
            'technology': ['technology', 'tech', 'digital', 'software', 'ai', 'computer'],
            'politics': ['election', 'government', 'political', 'president', 'congress'],
            'entertainment': ['movie', 'film', 'music', 'celebrity', 'award'],
            'sports': ['sport', 'game', 'championship', 'league', 'player'],
            'health': ['health', 'medical', 'disease', 'treatment', 'vaccine']
        }
        
        keywords = category_keywords.get(category.lower(), [])
        if not keywords:
            return all_topics[:limit]
        
        filtered = [t for t in all_topics 
                   if any(kw in t.lower() for kw in keywords)]
        
        return filtered[:limit]


# Global instance
_trending_service = None


def get_trending_topics_service() -> TrendingTopicsService:
    """Get or create the global trending topics service."""
    global _trending_service
    if _trending_service is None:
        _trending_service = TrendingTopicsService()
    return _trending_service


if __name__ == '__main__':
    # Test the service
    print("Testing Trending Topics Service...")
    service = get_trending_topics_service()
    
    print("\nFetching trending topics...")
    topics = service.get_trending_topics(limit=30, refresh=True)
    
    print(f"\nFound {len(topics)} trending topics:")
    for i, topic in enumerate(topics, 1):
        print(f"  {i}. {topic}")

