"""Lite research engine (serverless friendly).

Multi-engine snippet retrieval:
- Google (best-effort HTML)
- Bing (HTML)
- DuckDuckGo (HTML)
- Wikipedia (API)

No persistence; results are returned in-memory.
"""

from __future__ import annotations

import hashlib
import os
import re
from datetime import datetime
from typing import Dict, List
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup

from .response_cleaner import get_response_cleaner


class ResearchEngineLite:
    def __init__(self):
        self._ua = (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )

    def search(self, query: str, *, max_results: int = 5) -> List[Dict]:
        # Enhanced search with query expansion and reformulation
        expanded_queries = self._expand_query(query)

        all_results = []
        for expanded_query in expanded_queries[:3]:  # Try up to 3 variations
            results = self._search_single_query(expanded_query, max_results=max_results)
            all_results.extend(results)

            # If we got good results from the first query, don't try expansions
            if len(results) >= max_results and expanded_query == query:
                break

        return self._dedupe(all_results)

    def _expand_query(self, query: str) -> List[str]:
        """Generate query variations for better search results."""
        expansions = [query]  # Always include original

        query_lower = query.lower().strip()

        # Technical query expansions
        if any(word in query_lower for word in ['how to', 'tutorial', 'guide', 'steps']):
            # Add technical context
            expansions.append(f"{query} tutorial guide")
            expansions.append(f"{query} steps example")

        # Programming language expansions
        prog_languages = ['python', 'javascript', 'java', 'c++', 'c#', 'ruby', 'php', 'go', 'rust']
        for lang in prog_languages:
            if lang in query_lower:
                expansions.append(f"{query} {lang} programming")
                break

        # Definition expansions
        if query_lower.startswith(('what is', 'what are', 'define', 'meaning of')):
            expansions.append(f"{query} definition explanation")

        # Comparison expansions
        if any(word in query_lower for word in ['vs', 'versus', 'compare', 'difference']):
            expansions.append(f"{query} comparison pros cons")

        # Recent information expansions
        if any(word in query_lower for word in ['latest', 'recent', 'new', 'current', '2024', '2025']):
            expansions.append(f"{query} latest updates")

        return list(set(expansions))  # Remove duplicates

    def _search_single_query(self, query: str, *, max_results: int = 5) -> List[Dict]:
        """Search with a single query across all engines."""
        out: List[Dict] = []
        out.extend(self._search_google_html(query, max_results=max_results))
        out.extend(self._search_bing_html(query, max_results=max_results))
        out.extend(self._search_duckduckgo_html(query, max_results=max_results))
        out.extend(self._search_wikipedia(query, max_results=1))
        return out

    def _reformulate_query(self, original_query: str, initial_results: List[Dict]) -> str:
        """Reformulate query based on initial search results."""
        if not initial_results:
            return original_query

        # Analyze initial results to identify better search terms
        all_content = ' '.join([r.get('content', '') for r in initial_results])
        all_titles = ' '.join([r.get('title', '') for r in initial_results])

        combined_text = (all_content + ' ' + all_titles).lower()

        # Extract key terms that appear frequently in results
        words = re.findall(r'\b[a-z]{4,}\b', combined_text)  # Words of 4+ characters
        word_freq = {}
        for word in words:
            if word not in ['that', 'this', 'with', 'from', 'they', 'have', 'been', 'were']:
                word_freq[word] = word_freq.get(word, 0) + 1

        # Get top frequent terms
        top_terms = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:3]
        frequent_terms = [term for term, _ in top_terms if term not in original_query.lower()]

        if frequent_terms:
            # Add most frequent term to original query for refinement
            refined_query = f"{original_query} {frequent_terms[0]}"
            return refined_query

        return original_query

    def _dedupe(self, items: List[Dict]) -> List[Dict]:
        seen = set()
        uniq: List[Dict] = []

        def norm(s: str) -> str:
            return re.sub(r"\s+", " ", (s or "").strip().lower())

        for it in items or []:
            title = norm(it.get('title', ''))
            url = norm(it.get('url', ''))
            content = norm(it.get('content', ''))[:240]
            src = norm(it.get('source', ''))
            key = url or (title + '|' + content)
            if not key:
                continue
            fp = hashlib.md5((key + '|' + src[:8]).encode('utf-8')).hexdigest()
            if fp in seen:
                continue
            seen.add(fp)
            uniq.append(it)
        return uniq

    def _search_wikipedia(self, query: str, max_results: int = 1) -> List[Dict]:
        cleaner = get_response_cleaner()
        out: List[Dict] = []
        api = "https://en.wikipedia.org/w/api.php"
        params = {"action": "query", "list": "search", "srsearch": query, "srlimit": max_results, "format": "json"}
        r = requests.get(api, params=params, timeout=10)
        if r.status_code != 200:
            return out
        hits = ((r.json().get('query') or {}).get('search') or [])[:max_results]
        for hit in hits:
            title = hit.get('title')
            if not title:
                continue
            summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote_plus(title)}"
            rs = requests.get(summary_url, timeout=10)
            if rs.status_code != 200:
                continue
            sd = rs.json()
            extract = (sd.get('extract') or '').strip()
            if not extract:
                continue
            cleaned = cleaner.clean_wikipedia_artifacts(extract)
            cleaned = cleaner.format_factual_response(cleaned)
            if cleaned and len(cleaned) > 40:
                out.append({
                    'title': f"Wikipedia — {title}",
                    'content': cleaned[:800],
                    'query': query,
                    'source': 'wikipedia',
                    'learned_at': datetime.now().isoformat(),
                    'url': (sd.get('content_urls') or {}).get('desktop', {}).get('page')
                })
        return out

    def _search_duckduckgo_html(self, query: str, max_results: int = 5) -> List[Dict]:
        cleaner = get_response_cleaner()
        out: List[Dict] = []
        url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
        r = requests.get(url, headers={"User-Agent": self._ua, "Accept-Language": "en-US,en;q=0.9"}, timeout=15)
        if r.status_code != 200:
            return out
        soup = BeautifulSoup(r.text, 'html.parser')
        results = soup.find_all('div', class_='result')[: max_results + 6]
        for res in results:
            if len(out) >= max_results:
                break
            a = res.find('a', class_='result__a')
            sn = res.find('a', class_='result__snippet')
            if not a or not sn:
                continue
            title = (a.get_text() or '').strip()
            href = (a.get('href') or '').strip()
            snippet = (sn.get_text() or '').strip()
            if not title or not snippet or len(snippet) < 20:
                continue
            snippet = cleaner.format_factual_response(cleaner.clean_wikipedia_artifacts(snippet))
            if not snippet:
                continue
            out.append({
                'title': f"DuckDuckGo — {title}",
                'content': snippet[:650],
                'query': query,
                'source': 'duckduckgo',
                'learned_at': datetime.now().isoformat(),
                'url': href,
            })
        return out

    def _search_bing_html(self, query: str, max_results: int = 5) -> List[Dict]:
        cleaner = get_response_cleaner()
        out: List[Dict] = []
        url = f"https://www.bing.com/search?q={quote_plus(query)}&count={max_results}&setlang=en-US&cc=US"
        r = requests.get(url, headers={"User-Agent": self._ua, "Accept-Language": "en-US,en;q=0.9"}, timeout=15)
        if r.status_code != 200:
            return out
        soup = BeautifulSoup(r.text, 'html.parser')
        results = soup.select('li.b_algo')[: max_results + 6]
        for item in results:
            if len(out) >= max_results:
                break
            a = item.select_one('h2 a')
            p = item.select_one('p')
            if not a or not p:
                continue
            title = (a.get_text() or '').strip()
            href = (a.get('href') or '').strip()
            snippet = (p.get_text() or '').strip()
            if not title or not snippet or len(snippet) < 20:
                continue
            snippet = cleaner.format_factual_response(cleaner.clean_wikipedia_artifacts(snippet))
            if not snippet:
                continue
            out.append({
                'title': f"Bing — {title}",
                'content': snippet[:650],
                'query': query,
                'source': 'bing',
                'learned_at': datetime.now().isoformat(),
                'url': href,
            })
        return out

    def _search_google_html(self, query: str, max_results: int = 5) -> List[Dict]:
        cleaner = get_response_cleaner()
        out: List[Dict] = []
        url = f"https://www.google.com/search?q={quote_plus(query)}&num={max_results}&hl=en&gl=us"
        r = requests.get(url, headers={"User-Agent": self._ua, "Accept-Language": "en-US,en;q=0.9"}, timeout=15)
        if r.status_code != 200:
            return out
        soup = BeautifulSoup(r.text, 'html.parser')
        items = soup.select('div.tF2Cxc')[: max_results + 6]
        for item in items:
            if len(out) >= max_results:
                break
            h3 = item.select_one('h3')
            a = item.select_one('a')
            sn = item.select_one('div.VwiC3b') or item.select_one('div.IsZvec')
            if not h3 or not a or not sn:
                continue
            title = (h3.get_text() or '').strip()
            href = (a.get('href') or '').strip()
            snippet = (sn.get_text() or '').strip()
            if not title or not snippet or len(snippet) < 20:
                continue
            snippet = cleaner.format_factual_response(cleaner.clean_wikipedia_artifacts(snippet))
            if not snippet:
                continue
            out.append({
                'title': f"Google — {title}",
                'content': snippet[:650],
                'query': query,
                'source': 'google',
                'learned_at': datetime.now().isoformat(),
                'url': href,
            })
        return out


_instance: ResearchEngineLite | None = None


def get_research_engine_lite() -> ResearchEngineLite:
    global _instance
    if _instance is None:
        _instance = ResearchEngineLite()
    return _instance
