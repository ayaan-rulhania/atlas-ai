"""
Research Engine - Searches Google and learns when Thor doesn't know something
"""
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from datetime import datetime
import json
import os
import re
from urllib.parse import urlencode
from brain import BrainConnector
from .learning_tracker import get_tracker
from .response_cleaner import get_response_cleaner
import hashlib
from typing import Dict, List, Optional, Tuple

class ResearchEngine:
    """Searches and learns about topics Thor doesn't know"""
    
    def __init__(self):
        self.brain_connector = BrainConnector()
        self.brain_dir = "brain"
        self._ua = (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    
    def search_and_learn(self, query):
        """Search Google + two other engines + Wikipedia and learn about the topic."""
        print(f"[Research Engine] Researching: {query}...")
        
        # For programming queries, add "programming" or "tutorial" to avoid shopping results
        query_lower = query.lower()
        programming_keywords = ['kotlin', 'python', 'javascript', 'java', 'c++', 'typescript', 'go', 'rust', 'ruby', 'php', 'swift', 'scala']
        is_programming_query = any(keyword in query_lower for keyword in programming_keywords)
        
        # Enhance query for programming topics to get better results
        if is_programming_query and 'programming' not in query_lower and 'tutorial' not in query_lower:
            enhanced_query = f"{query} programming tutorial"
            print(f"[Research Engine] Enhanced programming query: {query} -> {enhanced_query}")
            query = enhanced_query
        
        knowledge = []
        
        # Detect relationship questions and handle them specially
        is_relationship_query = any(phrase in query.lower() for phrase in [
            'relationship between', 'relationship of', 'connection between', 'connection of',
            'difference between', 'compare', 'comparison between', 'versus', 'vs',
            'similarities between', 'how does', 'how do', 'how are', 'how is'
        ])
        
        # Get more results for relationship queries (they need more context)
        max_results = 8 if is_relationship_query else 5
        
        # For relationship queries, also search each topic individually
        if is_relationship_query:
            # Extract topics from "relationship between X and Y"
            words = query.lower().split()
            if 'between' in words or 'of' in words:
                idx = next((i for i, w in enumerate(words) if w in ['between', 'of']), -1)
                if idx >= 0 and idx + 1 < len(words):
                    # Try to extract topics
                    topic1_words = []
                    topic2_words = []
                    found_and = False
                    for i in range(idx + 1, len(words)):
                        if words[i] == 'and':
                            found_and = True
                            continue
                        if not found_and:
                            topic1_words.append(words[i])
                        else:
                            topic2_words.append(words[i])
                    
                    if topic1_words and topic2_words:
                        topic1 = ' '.join(topic1_words).strip(',.')
                        topic2 = ' '.join(topic2_words).strip(',.')
                        
                        # Search individual topics too
                        print(f"[Research Engine] Relationship query detected. Also researching: {topic1} and {topic2}")
                        for topic in [topic1, topic2]:
                            if len(topic) > 3:  # Only if topic is meaningful
                                # Use the same multi-engine path for topic-specific context,
                                # but with a smaller quota to keep latency reasonable.
                                knowledge.extend(self._multi_engine_search(topic, max_results=3))
        
        # Core multi-engine pull (always-on):
        # - Google (SerpAPI if available; else best-effort HTML)
        # - Bing HTML
        # - DuckDuckGo HTML
        # - Wikipedia API
        knowledge.extend(self._multi_engine_search(query, max_results=max_results))

        # Brave Search (optional; requires BRAVE_SEARCH_API_KEY) – adds extra coverage.
        try:
            brave_key = os.environ.get("BRAVE_SEARCH_API_KEY", "").strip()
            if brave_key:
                knowledge.extend(self._search_brave(query, brave_key, max_results=3 if is_relationship_query else 2))
        except Exception as e:
            print(f"[Research Engine] Brave search error: {e}")
        
        knowledge = self._dedupe_knowledge(knowledge)
        
        # Store in brain
        if knowledge:
            self._store_in_brain(query, knowledge)
            # Record in tracker
            try:
                tracker = get_tracker()
                tracker.record_brain_search(query, len(knowledge))
                tracker.record_knowledge(len(knowledge))
            except:
                pass
        
        return knowledge

    def _multi_engine_search(self, query: str, max_results: int = 5) -> List[Dict]:
        """
        Pull data from Google + Bing + DuckDuckGo + Wikipedia.
        Google is attempted via SerpAPI first (if configured), else via HTML.
        """
        out: List[Dict] = []
        is_relationship_query = any(phrase in query.lower() for phrase in [
            'relationship between', 'relationship of', 'connection between', 'connection of',
            'difference between', 'compare', 'comparison between', 'versus', 'vs',
            'similarities between', 'how does', 'how do', 'how are', 'how is',
            'what is the relationship', 'what is the connection'
        ])

        # Per-engine quotas; relationship queries need more breadth.
        google_n = min(max_results, 6 if is_relationship_query else 4)
        bing_n = min(max_results, 6 if is_relationship_query else 4)
        ddg_n = min(max_results, 6 if is_relationship_query else 4)
        wiki_n = 2 if is_relationship_query else 1

        # Google (SerpAPI if available; fallback to HTML)
        serp_key = os.environ.get("SERPAPI_API_KEY", "").strip()
        try:
            if serp_key:
                out.extend(self._search_google_serpapi(query, serp_key, max_results=google_n))
            else:
                out.extend(self._search_google_html(query, max_results=google_n))
        except Exception as e:
            print(f"[Research Engine] Google search error: {e}")

        # Bing
        try:
            out.extend(self._search_bing_html(query, max_results=bing_n))
        except Exception as e:
            print(f"[Research Engine] Bing search error: {e}")

        # DuckDuckGo
        try:
            out.extend(self._search_duckduckgo_html(query, max_results=ddg_n))
        except Exception as e:
            print(f"[Research Engine] DuckDuckGo search error: {e}")

        # Wikipedia (lightweight)
        try:
            out.extend(self._search_wikipedia(query, max_results=wiki_n))
        except Exception as e:
            print(f"[Research Engine] Wikipedia search error: {e}")

        return out

    def _dedupe_knowledge(self, knowledge: List[Dict]) -> List[Dict]:
        """
        Remove near-duplicates across engines.
        Prefers keeping items with URLs, and keeps first-seen order.
        """
        seen = set()
        unique: List[Dict] = []

        def norm(s: str) -> str:
            return re.sub(r"\s+", " ", (s or "").strip().lower())

        for item in knowledge or []:
            title = norm(item.get("title", ""))
            url = norm(item.get("url", ""))
            content = norm(item.get("content", ""))[:280]
            source = norm(item.get("source", ""))
            key = url or (title + "|" + content)
            if not key:
                continue
            # Mix in source lightly so same-title from different engines doesn’t explode,
            # but still allow identical content to collapse.
            fingerprint = hashlib.md5((key + "|" + source[:8]).encode("utf-8")).hexdigest()
            if fingerprint in seen:
                continue
            seen.add(fingerprint)
            unique.append(item)
        return unique

    def _search_wikipedia(self, query: str, max_results: int = 1):
        """Search Wikipedia via API and return short summaries."""
        response_cleaner = get_response_cleaner()
        out = []

        api = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "srlimit": max_results,
            "format": "json",
        }
        r = requests.get(api, params=params, timeout=10)
        if r.status_code != 200:
            return out
        data = r.json()
        hits = (data.get("query") or {}).get("search") or []
        for hit in hits:
            title = hit.get("title")
            if not title:
                continue
            summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote_plus(title)}"
            rs = requests.get(summary_url, timeout=10)
            if rs.status_code != 200:
                continue
            sd = rs.json()
            extract = (sd.get("extract") or "").strip()
            if not extract:
                continue
            cleaned = response_cleaner.clean_wikipedia_artifacts(extract)
            cleaned = response_cleaner.format_factual_response(cleaned)
            if cleaned and len(cleaned) > 40:
                out.append({
                    "title": f"Wikipedia — {title}",
                    "content": cleaned[:800],
                    "query": query,
                    "source": "wikipedia",
                    "learned_at": datetime.now().isoformat(),
                    "url": (sd.get("content_urls") or {}).get("desktop", {}).get("page")
                })
        return out

    def _search_brave(self, query: str, api_key: str, max_results: int = 2):
        """Search Brave Search API (requires key)."""
        response_cleaner = get_response_cleaner()
        out = []
        url = "https://api.search.brave.com/res/v1/web/search"
        headers = {
            "Accept": "application/json",
            "X-Subscription-Token": api_key,
            "User-Agent": "AtlasAI/Dev",
        }
        r = requests.get(url, headers=headers, params={"q": query, "count": max_results}, timeout=12)
        if r.status_code != 200:
            return out
        data = r.json()
        results = (((data.get("web") or {}).get("results")) or [])[:max_results]
        for item in results:
            title = (item.get("title") or "").strip()
            desc = (item.get("description") or "").strip()
            if not title or not desc:
                continue
            cleaned = response_cleaner.clean_wikipedia_artifacts(desc)
            cleaned = response_cleaner.format_factual_response(cleaned)
            if cleaned and len(cleaned) > 30:
                out.append({
                    "title": f"Brave — {title}",
                    "content": cleaned[:700],
                    "query": query,
                    "source": "brave",
                    "learned_at": datetime.now().isoformat(),
                })
        return out

    def _search_google_serpapi(self, query: str, api_key: str, max_results: int = 2):
        """Search Google via SerpAPI (requires SERPAPI_API_KEY)."""
        response_cleaner = get_response_cleaner()
        out = []
        url = "https://serpapi.com/search.json"
        params = {
            "engine": "google",
            "q": query,
            "num": max_results,
            "api_key": api_key,
        }
        r = requests.get(url, params=params, timeout=15)
        if r.status_code != 200:
            return out
        data = r.json()
        results = (data.get("organic_results") or [])[:max_results]
        for item in results:
            title = (item.get("title") or "").strip()
            snippet = (item.get("snippet") or "").strip()
            link = (item.get("link") or "").strip()
            if not title or not snippet:
                continue
            cleaned = self._clean_promotional_text(snippet)
            cleaned = response_cleaner.clean_wikipedia_artifacts(cleaned)
            cleaned = response_cleaner.format_factual_response(cleaned)
            if cleaned and len(cleaned) > 30:
                out.append({
                    "title": f"Google — {title}",
                    "content": cleaned[:700],
                    "query": query,
                    "source": "google",
                    "learned_at": datetime.now().isoformat(),
                    "url": link,
                })
        return out

    def _search_duckduckgo_html(self, query: str, max_results: int = 5) -> List[Dict]:
        """DuckDuckGo HTML results (snippets only)."""
        knowledge: List[Dict] = []
        response_cleaner = get_response_cleaner()
        url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
        headers = {
            "User-Agent": self._ua,
            "Accept-Language": "en-US,en;q=0.9",
        }
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code != 200:
            return knowledge

        soup = BeautifulSoup(r.text, "html.parser")
        results = soup.find_all("div", class_="result")[: max_results + 6]  # extra for filtering

        for result in results:
            if len(knowledge) >= max_results:
                break
            title_elem = result.find("a", class_="result__a")
            snippet_elem = result.find("a", class_="result__snippet")
            if not title_elem or not snippet_elem:
                continue
            title = title_elem.get_text().strip()
            snippet = snippet_elem.get_text().strip()
            href = (title_elem.get("href") or "").strip()
            if not title or not snippet or len(snippet) < 20:
                continue

            cleaned = self._clean_promotional_text(snippet)
            cleaned = response_cleaner.clean_wikipedia_artifacts(cleaned)
            cleaned = response_cleaner.format_factual_response(cleaned)
            if not cleaned or len(cleaned) < 20:
                continue
            if re.match(r"^(Official|Welcome|Visit|Click)", cleaned, flags=re.IGNORECASE):
                continue

            knowledge.append({
                "title": f"DuckDuckGo — {title}",
                "content": cleaned[:650],
                "query": query,
                "source": "duckduckgo",
                "learned_at": datetime.now().isoformat(),
                "url": href,
            })
        return knowledge

    def _search_bing_html(self, query: str, max_results: int = 5) -> List[Dict]:
        """Bing HTML results (snippets only)."""
        out: List[Dict] = []
        response_cleaner = get_response_cleaner()
        url = f"https://www.bing.com/search?q={quote_plus(query)}&count={max_results}&setlang=en-US&cc=US"
        headers = {
            "User-Agent": self._ua,
            "Accept-Language": "en-US,en;q=0.9",
        }
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code != 200:
            return out

        soup = BeautifulSoup(r.text, "html.parser")
        results = soup.select("li.b_algo")[: max_results + 6]
        for item in results:
            if len(out) >= max_results:
                break
            a = item.select_one("h2 a")
            p = item.select_one("p")
            if not a or not p:
                continue
            title = (a.get_text() or "").strip()
            href = (a.get("href") or "").strip()
            snippet = (p.get_text() or "").strip()
            if not title or not snippet or len(snippet) < 20:
                continue

            cleaned = self._clean_promotional_text(snippet)
            cleaned = response_cleaner.clean_wikipedia_artifacts(cleaned)
            cleaned = response_cleaner.format_factual_response(cleaned)
            if not cleaned or len(cleaned) < 20:
                continue
            if re.match(r"^(Official|Welcome|Visit|Click)", cleaned, flags=re.IGNORECASE):
                continue

            out.append({
                "title": f"Bing — {title}",
                "content": cleaned[:650],
                "query": query,
                "source": "bing",
                "learned_at": datetime.now().isoformat(),
                "url": href,
            })
        return out

    def _search_google_html(self, query: str, max_results: int = 5) -> List[Dict]:
        """
        Best-effort Google HTML scraping.
        Note: may be blocked in some environments; SerpAPI is preferred when available.
        """
        out: List[Dict] = []
        response_cleaner = get_response_cleaner()
        url = f"https://www.google.com/search?q={quote_plus(query)}&num={max_results}&hl=en&gl=us"
        headers = {
            "User-Agent": self._ua,
            "Accept-Language": "en-US,en;q=0.9",
        }
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code != 200:
            return out

        soup = BeautifulSoup(r.text, "html.parser")
        # Common result container
        items = soup.select("div.tF2Cxc")[: max_results + 6]
        for item in items:
            if len(out) >= max_results:
                break
            h3 = item.select_one("h3")
            a = item.select_one("a")
            snippet_el = item.select_one("div.VwiC3b") or item.select_one("div.IsZvec")
            if not h3 or not a or not snippet_el:
                continue
            title = (h3.get_text() or "").strip()
            href = (a.get("href") or "").strip()
            snippet = (snippet_el.get_text() or "").strip()
            if not title or not snippet or len(snippet) < 20:
                continue

            cleaned = self._clean_promotional_text(snippet)
            cleaned = response_cleaner.clean_wikipedia_artifacts(cleaned)
            cleaned = response_cleaner.format_factual_response(cleaned)
            if not cleaned or len(cleaned) < 20:
                continue
            if re.match(r"^(Official|Welcome|Visit|Click)", cleaned, flags=re.IGNORECASE):
                continue

            out.append({
                "title": f"Google — {title}",
                "content": cleaned[:650],
                "query": query,
                "source": "google",
                "learned_at": datetime.now().isoformat(),
                "url": href,
            })
        return out
    
    def _store_in_brain(self, topic, knowledge):
        """Store researched knowledge in brain"""
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
                        
                        if word not in data.get('keywords', []):
                            data.setdefault('keywords', []).append(word)
                            try:
                                tracker = get_tracker()
                                tracker.record_keyword(word, letter)
                            except:
                                pass
                        
                        existing_titles = [k.get('title', '') for k in data.get('knowledge', [])]
                        for k in knowledge:
                            if k.get('title', '') not in existing_titles:
                                data.setdefault('knowledge', []).append(k)
                        
                        data['last_updated'] = datetime.now().isoformat()
                        
                        with open(keywords_file, 'w') as f:
                            json.dump(data, f, indent=2)
                    except:
                        pass
    
    def _clean_promotional_text(self, text):
        """Remove promotional/ad copy language from text"""
        import re
        if not text:
            return text
        
        # Patterns that indicate promotional/ad copy text
        promotional_patterns = [
            r'Learn\s+(everything\s+)?(you\s+need\s+to\s+know\s+)?(about\s+)?',
            r'Discover\s+(everything\s+)?(about\s+)?',
            r'Find\s+out\s+(everything\s+)?(about\s+)?',
            r'Get\s+(started\s+)?(with\s+)?(everything\s+)?(about\s+)?',
            r'Explore\s+(everything\s+)?(about\s+)?',
            r'Master\s+(everything\s+)?(about\s+)?',
            r'Unlock\s+(the\s+)?(secrets?\s+of\s+)?',
            r'Click\s+(here\s+)?(to\s+)?',
            r'Visit\s+(our\s+)?(website\s+)?(to\s+)?',
            r'Check\s+out\s+(our\s+)?',
            r'Sign\s+up\s+(for\s+)?',
            r'Subscribe\s+(to\s+)?',
            r'Join\s+(us\s+)?(to\s+)?',
            r'Start\s+(your\s+)?(journey\s+)?(with\s+)?',
        ]
        
        cleaned = text
        for pattern in promotional_patterns:
            cleaned = re.sub(r'^' + pattern, '', cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r'\s+' + pattern, ' ', cleaned, flags=re.IGNORECASE)
        
        # Remove call-to-action endings
        cta_endings = [
            r'\s+to\s+get\s+started\.?$',
            r'\s+to\s+learn\s+more\.?$',
            r'\s+to\s+find\s+out\s+more\.?$',
            r'\s+to\s+discover\s+more\.?$',
            r'\s+and\s+more\.?$',
        ]
        
        for pattern in cta_endings:
            cleaned = re.sub(pattern, '.', cleaned, flags=re.IGNORECASE)
        
        # Clean up multiple spaces
        cleaned = re.sub(r'\s+', ' ', cleaned)
        cleaned = cleaned.strip()
        
        # Capitalize if needed
        if cleaned and cleaned[0].islower():
            cleaned = cleaned[0].upper() + cleaned[1:]
        
        return cleaned
    
    def needs_research(self, message):
        """Check if message needs research (keywords not in brain)"""
        # Always research relationship queries - they need comprehensive information
        is_relationship_query = any(phrase in message.lower() for phrase in [
            'relationship between', 'relationship of', 'connection between', 'connection of',
            'difference between', 'compare', 'comparison between', 'versus', 'vs',
            'similarities between', 'how does', 'how do', 'how are', 'how is',
            'what is the relationship', 'what is the connection'
        ])
        
        if is_relationship_query:
            return True  # Always research relationship queries
        
        knowledge = self.brain_connector.get_relevant_knowledge(message)
        
        # If no knowledge found, needs research
        if not knowledge:
            # Extract main keywords
            words = message.lower().split()
            important_words = [w for w in words if len(w) > 3 and w.isalpha()][:3]
            
            if important_words:
                # Check if any important words are in brain
                found_any = False
                for word in important_words:
                    letter = word[0].upper()
                    keywords_file = os.path.join(self.brain_dir, letter, "keywords.json")
                    if os.path.exists(keywords_file):
                        try:
                            with open(keywords_file, 'r') as f:
                                data = json.load(f)
                                if word in data.get('keywords', []):
                                    found_any = True
                                    break
                        except:
                            pass
                
                return not found_any
        
        return False


# Global instance
_research_engine = None

def get_research_engine():
    """Get or create global research engine"""
    global _research_engine
    if _research_engine is None:
        _research_engine = ResearchEngine()
    return _research_engine

