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
        out: List[Dict] = []
        out.extend(self._search_google_html(query, max_results=max_results))
        out.extend(self._search_bing_html(query, max_results=max_results))
        out.extend(self._search_duckduckgo_html(query, max_results=max_results))
        out.extend(self._search_wikipedia(query, max_results=1))
        return self._dedupe(out)

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
