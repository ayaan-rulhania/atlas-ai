"""
Flask backend for Atlas AI - Thor 1.1 Model Interface
"""
from flask import Flask, render_template, request, jsonify, session, send_file
from flask_cors import CORS
import os
import json
import uuid
from datetime import datetime
from pathlib import Path
import re
import sys
from urllib.parse import quote_plus
import requests
from bs4 import BeautifulSoup

# Import centralized configuration
from config import (
    BASE_DIR, ATLAS_ROOT, THOR_1_0_DIR, THOR_1_1_DIR, THOR_1_2_DIR, ANTELOPE_1_0_DIR, ANTELOPE_1_1_DIR, CHATBOT_DIR, THOR_DIR,
    DATA_ROOT,
    SECRET_KEY, ALLOWED_ORIGINS,
    MODEL_DIR, TOKENIZER_DIR, CONFIG_PATH,
    CHATS_DIR, CONVERSATIONS_DIR, PROJECTS_DIR, HISTORY_DIR,
    THOR_1_0_RESULT_SETTER_FILE, THOR_1_1_RESULT_SETTER_FILE, THOR_RESULT_SETTER_FILE,
    GEMS_DIR, GEMS_FILE,
    UI_TEMPLATE_DIR, UI_STATIC_DIR,
)

# Import utilities
from app_utils.math_evaluator import safe_evaluate_math
from app_utils.path_manager import get_path_manager
from app_utils.percent_load_calc import calculate_loading_percentage, get_default_loading_steps
from app_utils.model_loading_error_handling import (
    handle_model_loading_error,
    get_error_progress_message,
    log_model_loading_error
)

# Path manager for cleaner imports (replaces sys.path manipulation)
path_manager = get_path_manager()

# Legacy sys.path manipulation (to be phased out gradually)
# TODO: Remove this once all imports use path_manager
thor_path = str(THOR_1_1_DIR)
# Also add thor-1.0 to path for stable mode
thor_1_0_path = str(THOR_1_0_DIR)
# Add chatbot directory to path for chatbot services
chatbot_path = str(CHATBOT_DIR)
atlas_root_path = str(ATLAS_ROOT)

# Keep import resolution deterministic:
# - `services` should resolve to Thor (not `chatbot/services`)
# - `chatbot.*` should resolve via ATLAS_ROOT
for _p in (thor_path, thor_1_0_path, atlas_root_path, chatbot_path):
    try:
        while _p in sys.path:
            sys.path.remove(_p)
    except Exception:
        pass

sys.path.insert(0, thor_path)
sys.path.insert(1, thor_1_0_path)
sys.path.insert(2, atlas_root_path)
# Allow local (non-package) imports like `from refinement import ...` when not running from `chatbot/`.
sys.path.append(chatbot_path)

try:
    import torch  # type: ignore
except Exception:  # pragma: no cover
    torch = None

# Import transformers for direct Qwen3 usage
try:
    from transformers import AutoTokenizer, AutoModelForCausalLM
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    AutoTokenizer = None
    AutoModelForCausalLM = None
# Import services with fallback for when paths aren't set up correctly
# Initialize as None first to avoid NameError
get_auto_trainer = None
get_tracker = None
get_greetings_handler = None
get_common_sense_handler = None
get_research_engine = None
get_query_intent_analyzer = None
get_semantic_scorer = None
get_creative_generator = None
get_image_processor = None
get_code_handler = None
get_response_cleaner = None

try:
    from services import (
        get_auto_trainer as _get_auto_trainer,
        get_tracker as _get_tracker,
        get_greetings_handler as _get_greetings_handler,
        get_common_sense_handler as _get_common_sense_handler,
        get_research_engine as _get_research_engine,
        get_query_intent_analyzer as _get_query_intent_analyzer,
        get_semantic_scorer as _get_semantic_scorer,
        get_creative_generator as _get_creative_generator,
        get_image_processor as _get_image_processor,
        get_code_handler as _get_code_handler,
        get_response_cleaner as _get_response_cleaner,
    )
    # Assign imported functions
    get_auto_trainer = _get_auto_trainer
    get_tracker = _get_tracker
    get_greetings_handler = _get_greetings_handler
    get_common_sense_handler = _get_common_sense_handler
    get_research_engine = _get_research_engine
    get_query_intent_analyzer = _get_query_intent_analyzer
    get_semantic_scorer = _get_semantic_scorer
    get_creative_generator = _get_creative_generator
    get_image_processor = _get_image_processor
    get_code_handler = _get_code_handler
    get_response_cleaner = _get_response_cleaner
    SERVICES_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Services import failed: {e}")
    SERVICES_AVAILABLE = False
    # Define dummy functions to prevent crashes
    def get_auto_trainer(): return None
    def get_tracker(): return None
    def get_greetings_handler(): return None
    def get_common_sense_handler(): return None
    def get_research_engine(): return None
    def get_query_intent_analyzer(): return None
    def get_semantic_scorer(): return None
    def get_creative_generator(): return None
    def get_image_processor(): return None
    def get_code_handler(): return None
    def get_response_cleaner(): return None
# Import user_memory from chatbot services (relative to this file)
import importlib.util
user_memory_path = BASE_DIR / "services" / "user_memory.py"
spec = importlib.util.spec_from_file_location("user_memory", user_memory_path)
user_memory_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(user_memory_module)
get_user_memory = user_memory_module.get_user_memory
from brain import BrainConnector
from biographical_handler import synthesize_knowledge, clean_promotional_text
from refinement import (
    get_question_normalizer,
    get_intent_router,
    get_knowledge_reranker,
    get_answer_refiner,
    get_clarifier,
    verify_response_accuracy,
    get_conversational_analyzer,
)
from handlers import ImageHandler, ResponseFormatter, MarkdownHandler
from handlers.image_handler import get_image_handler
from handlers.response_formatter import get_response_formatter
from handlers.markdown_handler import get_markdown_handler
from formatting import get_final_response_formatter
from refinement.response_variety import get_response_variety_manager
from refinement.emotional_intelligence import get_emotional_intelligence
from refinement.conversation_flow import get_conversation_flow_manager
from refinement.personalization import get_personalization_engine
import time
import random

# Initialize Flask app with centralized configuration
app = Flask(__name__, template_folder=str(UI_TEMPLATE_DIR), static_folder=str(UI_STATIC_DIR))
app.secret_key = SECRET_KEY  # Use persistent secret key from config

# Configure CORS with specific allowed origins (security improvement)
CORS(app, origins=ALLOWED_ORIGINS, supports_credentials=True)

# Security headers (v1.4.3o)
@app.after_request
def set_security_headers(response):
    """Add security headers to all responses."""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    # Only add CSP in production
    if os.environ.get('FLASK_ENV') == 'production':
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: https:; connect-src 'self'"
    return response

# Response caching for improved performance (v1.4.4)
from functools import lru_cache
from hashlib import md5

# Simple in-memory cache for responses (TTL-based)
_response_cache = {}
_cache_ttl = 300  # 5 minutes

def get_cache_key(query: str, model: str, tone: str) -> str:
    """Generate cache key for query."""
    key_string = f"{query}:{model}:{tone}"
    return md5(key_string.encode()).hexdigest()

def get_cached_response(query: str, model: str, tone: str):
    """Get cached response if available and not expired."""
    cache_key = get_cache_key(query, model, tone)
    if cache_key in _response_cache:
        cached_data, timestamp = _response_cache[cache_key]
        if time.time() - timestamp < _cache_ttl:
            return cached_data
        else:
            # Expired, remove from cache
            del _response_cache[cache_key]
    return None

def cache_response(query: str, model: str, tone: str, response: str):
    """Cache response for future use."""
    cache_key = get_cache_key(query, model, tone)
    _response_cache[cache_key] = (response, time.time())
    # Limit cache size (keep last 100 entries)
    if len(_response_cache) > 100:
        oldest_key = min(_response_cache.keys(), key=lambda k: _response_cache[k][1])
        del _response_cache[oldest_key]

# Input validation and sanitization (v1.4.3o)
def validate_and_sanitize_input(text: str, max_length: int = 10000) -> tuple:
    """
    Validate and sanitize user input.
    Returns (sanitized_text, is_valid)
    """
    if not isinstance(text, str):
        return "", False
    
    # Check length
    if len(text) > max_length:
        text = text[:max_length]
    
    # Remove potentially dangerous patterns
    dangerous_patterns = [
        r'<script[^>]*>.*?</script>',  # Script tags
        r'javascript:',  # JavaScript protocol
        r'on\w+\s*=',  # Event handlers
        r'data:text/html',  # Data URLs with HTML
    ]
    
    sanitized = text
    for pattern in dangerous_patterns:
        sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE | re.DOTALL)
    
    # Check for SQL injection patterns (basic)
    sql_patterns = [r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)", r"(--|;|/\*|\*/)"]
    has_sql = any(re.search(pattern, sanitized, re.IGNORECASE) for pattern in sql_patterns)
    
    # For chat, we allow most text but log suspicious patterns
    if has_sql:
        print(f"[Security] Potential SQL pattern detected in input (logged, not blocked): {text[:100]}")
    
    return sanitized, True

# Rate limiting (simple in-memory, v1.4.3o)
_rate_limit_store = {}
_rate_limit_max = 60  # requests per window
_rate_limit_window = 60  # seconds

def check_rate_limit(identifier: str) -> tuple:
    """
    Check if request is within rate limit.
    Returns (is_allowed, remaining_requests)
    """
    now = time.time()
    if identifier not in _rate_limit_store:
        _rate_limit_store[identifier] = {'count': 1, 'window_start': now}
        return True, _rate_limit_max - 1
    
    store = _rate_limit_store[identifier]
    
    # Reset window if expired
    if now - store['window_start'] > _rate_limit_window:
        store['count'] = 1
        store['window_start'] = now
        return True, _rate_limit_max - 1
    
    # Check limit
    if store['count'] >= _rate_limit_max:
        remaining = 0
    else:
        store['count'] += 1
        remaining = _rate_limit_max - store['count']
    
    return store['count'] <= _rate_limit_max, remaining


def _slugify(text: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    base = re.sub(r"-{2,}", "-", base)
    return base[:32] or "gem"


def _load_gems_db() -> dict:
    try:
        with open(GEMS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f) or {}
            if isinstance(data, dict) and isinstance(data.get("gems"), list):
                return data
    except Exception:
        pass
    return {"gems": []}


def _save_gems_db(db: dict) -> None:
    try:
        with open(GEMS_FILE, "w", encoding="utf-8") as f:
            json.dump(db, f, indent=2)
    except Exception:
        pass


def _public_gem(g: dict) -> dict:
    """Return a gem safe for UI (omit large file contents)."""
    sources = g.get("sources") or {}
    links = sources.get("links") if isinstance(sources.get("links"), list) else []
    files = sources.get("files") if isinstance(sources.get("files"), list) else []
    return {
        "id": g.get("id"),
        "name": g.get("name"),
        "description": g.get("description", ""),
        "instructions": g.get("instructions", ""),
        "tone": g.get("tone", "normal"),
        "sources": {
            "links": links,
            "files": [{"filename": f.get("filename")} for f in files if isinstance(f, dict) and f.get("filename")],
        },
        "created_at": g.get("created_at", ""),
        "updated_at": g.get("updated_at", ""),
    }


def _get_gem_by_id(gem_id: str) -> dict | None:
    db = _load_gems_db()
    for g in db.get("gems", []):
        if g.get("id") == gem_id:
            return g
    return None


def _gem_sources_to_knowledge(gem: dict) -> list[dict]:
    """Convert gem sources into in-memory knowledge items."""
    knowledge = []
    now = datetime.now().isoformat()
    sources = gem.get("sources") or {}
    
    # Handle both dict and direct list formats
    if isinstance(sources, list):
        # Old format: sources is a list of links
        links = [s for s in sources if isinstance(s, str)]
        files = []
    elif isinstance(sources, dict):
        links = sources.get("links") if isinstance(sources.get("links"), list) else []
        files = sources.get("files") if isinstance(sources.get("files"), list) else []
    else:
        links = []
        files = []
    
    print(f"[Gem Sources] Processing {len(links)} links and {len(files)} files")

    # Files: already stored as text content
    for f in files[:10]:  # Increased limit for more sources
        if not isinstance(f, dict):
            continue
        filename = (f.get("filename") or "").strip()
        content = (f.get("content") or "").strip()
        if filename and content and len(content) > 20:
            # SPECIAL HANDLING: Filter JavaScript code from .js files
            if filename.endswith('.js') or 'javascript' in filename.lower():
                # Extract only data/content, not code
                # Look for export const/let/var patterns and extract object/array content
                # Remove function definitions, imports, etc.
                
                # Remove code patterns
                content = re.sub(r'^import\s+.*?$', '', content, flags=re.MULTILINE)
                content = re.sub(r'^export\s+(const|let|var|function|class)\s+', '', content, flags=re.MULTILINE)
                content = re.sub(r'function\s+\w+\s*\([^)]*\)\s*\{[^}]*\}', '', content, flags=re.DOTALL)
                content = re.sub(r'const\s+\w+\s*=\s*\([^)]*\)\s*=>\s*\{[^}]*\}', '', content, flags=re.DOTALL)
                content = re.sub(r'=\s*\{[^}]*\};?', '', content)  # Remove object assignments
                
                # Try to extract JSON-like structures or data objects
                json_match = re.search(r'(\{.*\}|\[.*\])', content, re.DOTALL)
                if json_match:
                    try:
                        import json
                        data = json.loads(json_match.group(1))
                        # Convert structured data to text
                        if isinstance(data, dict):
                            content = ' '.join([f"{k}: {v}" if not isinstance(v, (dict, list)) else f"{k}" 
                                               for k, v in list(data.items())[:20]])
                        elif isinstance(data, list):
                            content = ' '.join([str(item) if not isinstance(item, (dict, list)) else str(item)[:100] 
                                               for item in data[:20]])
                    except:
                        pass  # If JSON parsing fails, use cleaned content
                
                # Remove remaining code syntax
                content = re.sub(r'[{}();=]', ' ', content)
                content = re.sub(r'\b(const|let|var|function|export|import|return|if|else|for|while)\b', '', content, flags=re.IGNORECASE)
            
            # Clean content with response cleaner
            cleaner = get_response_cleaner()
            content = cleaner.clean_wikipedia_artifacts(content)
            content = cleaner.clean_promotional_content(content)
            
            # Remove metadata/error messages
            content = re.sub(r'This article contains.*?\.', '', content, flags=re.IGNORECASE | re.DOTALL)
            content = re.sub(r'References script detected.*?\.', '', content, flags=re.IGNORECASE | re.DOTALL)
            content = re.sub(r'From Wikipedia.*?encyclopedia\s*', '', content, flags=re.IGNORECASE)
            
            # Extract meaningful sentences only
            sentences = [s.strip() for s in content.split('.') 
                        if len(s.strip()) > 20 
                        and not s.strip().lower().startswith(('sources:', 'model:', 'context-aware:', 'note:', 'export', 'const', 'let', 'var'))
                        and 'duplicate' not in s.lower()[:50]
                        and 'references script' not in s.lower()]
            content = '. '.join(sentences[:15])  # First 15 meaningful sentences
            
            if len(content) < 50:
                continue
                
            knowledge.append({
                "title": f"Gem Source — {filename}",
                "content": content[:2500],  # Increased from 1200 to 2500 for better context
                "query": gem.get("name", ""),
                "source": "gem_source",
                "learned_at": now,
                "priority": 1,  # High priority flag for gem sources
            })

    # Links: best-effort fetch (lightweight)
    for link in links[:5]:  # Increased from 3 to 5
        try:
            url = str(link).strip()
            if not url.startswith(("http://", "https://")):
                continue
            
            # SPECIAL HANDLING: Use Wikipedia API for Wikipedia URLs
            if "wikipedia.org" in url.lower():
                try:
                    # Extract page title from URL
                    page_title = url.split("/wiki/")[-1].split("#")[0].split("?")[0]
                    page_title = page_title.replace("_", " ")
                    # Use Wikipedia REST API for clean summary
                    api_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote_plus(page_title)}"
                    api_r = requests.get(api_url, timeout=10, headers={"User-Agent": "AtlasAI/Dev"})
                    if api_r.status_code == 200:
                        data = api_r.json()
                        extract = data.get("extract", "")
                        title = data.get("title", page_title)
                        
                        if extract and len(extract) > 100:
                            # Clean Wikipedia artifacts
                            cleaner = get_response_cleaner()
                            extract = cleaner.clean_wikipedia_artifacts(extract)
                            extract = cleaner.clean_promotional_content(extract)
                            
                            # Remove Wikipedia metadata/error messages
                            extract = re.sub(r'This article contains.*?\.', '', extract, flags=re.IGNORECASE | re.DOTALL)
                            extract = re.sub(r'References script detected.*?\.', '', extract, flags=re.IGNORECASE | re.DOTALL)
                            extract = re.sub(r'It is recommended to.*?\.', '', extract, flags=re.IGNORECASE | re.DOTALL)
                            extract = re.sub(r'From Wikipedia.*?encyclopedia\s*', '', extract, flags=re.IGNORECASE)
                            extract = re.sub(r'Systematic endeavour.*?\.', '', extract, flags=re.IGNORECASE | re.DOTALL)
                            
                            # Extract first few meaningful sentences
                            sentences = [s.strip() for s in extract.split('.') if len(s.strip()) > 30]
                            extract = '. '.join(sentences[:8])  # First 8 meaningful sentences
                            
                            if len(extract) > 100:
                                knowledge.append({
                                    "title": f"Gem Source — {title[:80]}",
                                    "content": extract[:2000],
                                    "query": gem.get("name", ""),
                                    "source": "gem_source",
                                    "learned_at": now,
                                    "url": url,
                                    "priority": 1,
                                })
                                continue  # Successfully processed Wikipedia, skip HTML scraping
                except Exception as wiki_err:
                    print(f"[Gem Source] Wikipedia API failed for {url}, falling back to HTML: {wiki_err}")
                    # Fall through to HTML scraping
            
            # For non-Wikipedia or if Wikipedia API fails, use HTML scraping
            r = requests.get(url, timeout=10, headers={"User-Agent": "AtlasAI/Dev", "Accept-Language": "en-US,en;q=0.9"})
            if r.status_code != 200:
                continue
            soup = BeautifulSoup(r.text, "html.parser")
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            title = (soup.title.get_text().strip() if soup.title else url)
            # Try to get main content first (article, main, or content divs)
            main_content = soup.find("article") or soup.find("main") or soup.find("div", class_=re.compile("content|main|article|post|entry", re.I))
            if main_content:
                text = main_content.get_text(" ", strip=True)
            else:
                # Fallback: try to find body or a large text container
                body = soup.find("body")
                if body:
                    # Remove common non-content elements
                    for elem in body.find_all(["nav", "footer", "header", "aside", "script", "style"]):
                        elem.decompose()
                    text = body.get_text(" ", strip=True)
                else:
                    text = soup.get_text(" ", strip=True)
            
            # Clean up whitespace and normalize
            text = re.sub(r"\s{2,}", " ", text)
            text = re.sub(r"\n\s*\n", "\n", text)  # Remove excessive newlines
            
            # Remove Wikipedia metadata/error messages
            text = re.sub(r'This article contains.*?\.', '', text, flags=re.IGNORECASE | re.DOTALL)
            text = re.sub(r'References script detected.*?\.', '', text, flags=re.IGNORECASE | re.DOTALL)
            text = re.sub(r'From Wikipedia.*?encyclopedia\s*', '', text, flags=re.IGNORECASE)
            
            # Extract meaningful paragraphs (skip very short lines and metadata)
            lines = [line.strip() for line in text.split("\n") 
                    if len(line.strip()) > 20 
                    and not line.strip().lower().startswith(('sources:', 'model:', 'context-aware:', 'note:'))
                    and 'duplicate' not in line.lower()[:50]
                    and 'references script' not in line.lower()]
            text = " ".join(lines[:50])  # Take first 50 meaningful lines
            
            # Clean with response cleaner
            cleaner = get_response_cleaner()
            text = cleaner.clean_wikipedia_artifacts(text)
            text = cleaner.clean_promotional_content(text)
            
            if len(text) < 100:
                continue
            knowledge.append({
                "title": f"Gem Source — {title[:80]}",
                "content": text[:2500],  # Increased from 1200 to 2500 for better context
                "query": gem.get("name", ""),
                "source": "gem_source",
                "learned_at": now,
                "url": url,
                "priority": 1,  # High priority flag for gem sources
            })
        except Exception as e:
            print(f"[Gem Source] Error fetching {link}: {e}")
            continue

    return knowledge


def _refine_large_text(text: str, max_chunk_size: int = 500) -> str:
    """
    Refine large text chunks by breaking them into manageable pieces
    and extracting key information for better model understanding.
    """
    if len(text) <= max_chunk_size:
        return text
    
    # Split by sentences first
    import re
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    # Group sentences into chunks
    chunks = []
    current_chunk = []
    current_length = 0
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        
        sentence_length = len(sentence)
        
        # If adding this sentence would exceed max_chunk_size, save current chunk
        if current_length + sentence_length > max_chunk_size and current_chunk:
            chunks.append(' '.join(current_chunk))
            current_chunk = [sentence]
            current_length = sentence_length
        else:
            current_chunk.append(sentence)
            current_length += sentence_length + 1  # +1 for space
    
    # Add remaining chunk
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    
    # If still too large, extract key phrases
    if len(chunks) > 10:
        # Extract key sentences (longer sentences often contain more information)
        key_sentences = sorted(sentences, key=lambda s: len(s), reverse=True)[:20]
        # Reorder to maintain some context
        refined_text = ' '.join(key_sentences[:15])
        if len(refined_text) > 2000:
            refined_text = refined_text[:2000] + "..."
        return refined_text
    
    # Join chunks with context markers
    if len(chunks) > 1:
        refined_text = ' '.join(chunks[:5])  # Use first 5 chunks
        if len(refined_text) > 2000:
            refined_text = refined_text[:2000] + "..."
        return refined_text
    
    # Fallback: truncate intelligently
    if len(text) > 2000:
        # Try to cut at sentence boundary
        truncated = text[:2000]
        last_period = truncated.rfind('.')
        last_question = truncated.rfind('?')
        last_exclamation = truncated.rfind('!')
        last_boundary = max(last_period, last_question, last_exclamation)
        if last_boundary > 1500:  # Only use if we keep most of the text
            return text[:last_boundary + 1] + "..."
        return text[:2000] + "..."
    
    return text


def _add_emoji_support(text: str, query: str) -> str:
    """
    Add emojis to response when relevant or requested.
    Only adds emojis if:
    1. User explicitly asks for an emoji (e.g., "give me a smile emoji")
    2. Emoji is contextually relevant (celebration, success, etc.)
    """
    if not text:
        return text
    
    query_lower = query.lower()
    text_lower = text.lower()
    
    # Check if user explicitly requested an emoji
    emoji_requests = {
        'smile': '😊', 'happy': '😊', 'joy': '😊',
        'sad': '😢', 'sadness': '😢',
        'heart': '❤️', 'love': '❤️',
        'thumbs up': '👍', 'thumbs down': '👎',
        'fire': '🔥', 'hot': '🔥',
        'star': '⭐', 'stars': '⭐',
        'check': '✅', 'checkmark': '✅', 'correct': '✅',
        'cross': '❌', 'wrong': '❌', 'incorrect': '❌',
        'warning': '⚠️', 'alert': '⚠️',
        'rocket': '🚀', 'launch': '🚀',
        'party': '🎉', 'celebration': '🎉', 'congratulations': '🎉',
        'lightbulb': '💡', 'idea': '💡',
        'thumbs': '👍',
        'cool': '😎',
        'wink': '😉',
        'laugh': '😂',
        'thinking': '🤔',
        'clap': '👏',
        'wave': '👋',
        'ok': '👌',
    }
    
    # Check for explicit emoji requests
    for keyword, emoji in emoji_requests.items():
        if f'emoji {keyword}' in query_lower or f'{keyword} emoji' in query_lower or f'give me a {keyword}' in query_lower:
            # Add emoji at the end if not already present
            if emoji not in text:
                return f"{text} {emoji}"
            return text
    
    # Contextual emojis (only add if very relevant)
    if any(word in text_lower for word in ['success', 'completed', 'done', 'finished', 'great job']):
        if '✅' not in text:
            return f"{text} ✅"
    elif any(word in text_lower for word in ['error', 'failed', 'problem', 'issue', 'warning']):
        if '⚠️' not in text:
            return f"{text} ⚠️"
    elif any(word in text_lower for word in ['congratulations', 'celebration', 'awesome', 'amazing']):
        if '🎉' not in text:
            return f"{text} 🎉"
    
    return text


def _tone_profile(tone: str) -> str:
    t = (tone or "normal").strip().lower()
    if t == "friendly":
        return "CRITICAL INSTRUCTION: You MUST adopt a friendly, warm, and supportive tone throughout your entire response. Use conversational language, show enthusiasm when appropriate, and make the user feel welcomed. Use short paragraphs (2-3 sentences max). Avoid forced bullets unless explicitly requested. Include encouraging phrases like 'Great question!' or 'I'd be happy to help!' when natural. This tone should be CONSISTENT and PERVASIVE in every sentence."
    if t == "critical":
        return "CRITICAL INSTRUCTION: You MUST adopt a critical and direct tone throughout your entire response. Be analytical, point out flaws or issues clearly, and propose concrete fixes. Avoid fluff, pleasantries, or unnecessary padding. Be straightforward and honest. Use direct language. If something is wrong, say it's wrong. If something could be better, explain how. This tone should be CONSISTENT and PERVASIVE in every sentence."
    if t == "calm":
        return "CRITICAL INSTRUCTION: You MUST adopt a calm, steady, and reassuring tone throughout your entire response. Keep sentences short and clear. Avoid intensity, urgency, or emotional language. Speak as if everything is under control. Use phrases like 'Take your time' or 'No need to worry' when appropriate. Maintain a peaceful, measured pace in your writing. This tone should be CONSISTENT and PERVASIVE in every sentence."
    if t == "formal":
        return "CRITICAL INSTRUCTION: You MUST adopt a formal and professional tone throughout your entire response. Use precise, academic wording. Structure your response with clear paragraphs. Avoid contractions (use 'do not' instead of 'don't'). Use formal address when appropriate. Maintain a scholarly, authoritative voice. This tone should be CONSISTENT and PERVASIVE in every sentence."
    return "Tone: Normal. Clear and concise. Maintain a balanced, neutral tone throughout."

# Global model instances
model_instances = {
    'thor-1.0': None,
    'thor-1.2': None,  # Improved version from models/thor/thor-1.2, loads instantly
    'qwen3-thor': None,  # This is what thor-1.1 maps to (combined Qwen3-4B + Thor 1.1)
    'antelope-1.0': None,
    'antelope-1.1': None
}

# Global model loading progress tracking (0-100)
model_loading_progress = {
    'thor-1.0': {'progress': 0, 'status': 'not_started', 'message': 'Not started'},
    'thor-1.1': {'progress': 0, 'status': 'not_started', 'message': 'Not started'},
    'thor-1.2': {'progress': 0, 'status': 'not_started', 'message': 'Not started'},
    'qwen3-thor': {'progress': 0, 'status': 'not_started', 'message': 'Not started'},
    'antelope-1.0': {'progress': 0, 'status': 'not_started', 'message': 'Not started'},
    'antelope-1.1': {'progress': 0, 'status': 'not_started', 'message': 'Not started'}
}

# Brain connector
brain_connector = BrainConnector()


def _get_enhanced_context(all_messages: list, current_message: str, normalized_message: str, max_context_length: int = 15) -> list:
    """
    Enhanced context selection that goes beyond just the last N messages.
    Selects context based on relevance, recency, and conversation threads.
    """
    if not all_messages:
        return []

    # Start with recent messages (minimum context)
    recent_messages = all_messages[-8:]

    # For longer conversations, analyze for relevant context
    if len(all_messages) > 8:
        # Extract conversation threads/topics
        conversation_threads = _extract_conversation_threads(all_messages)

        # Find relevant threads for current message
        current_topics = _extract_message_topics(current_message, normalized_message)
        relevant_threads = _find_relevant_threads(conversation_threads, current_topics)

        # Build enhanced context from relevant threads + recent messages
        enhanced_context = []
        thread_messages = []

        # Collect messages from relevant threads (not just recent ones)
        for thread in relevant_threads[:3]:  # Limit to top 3 relevant threads
            thread_messages.extend(thread.get('messages', []))

        # Combine: prioritize recent messages, then add relevant older messages
        recent_set = set((msg.get('content', ''), msg.get('role', '')) for msg in recent_messages)

        # Add thread messages that aren't already in recent context
        for msg in thread_messages[-10:]:  # Last 10 from each relevant thread
            msg_tuple = (msg.get('content', ''), msg.get('role', ''))
            if msg_tuple not in recent_set:
                enhanced_context.append(msg)
                if len(enhanced_context) >= 5:  # Limit additional context
                    break

        # Combine and sort by recency
        all_context = recent_messages + enhanced_context
        all_context.sort(key=lambda x: x.get('timestamp', ''), reverse=True)

        # Remove duplicates while preserving order
        seen = set()
        deduplicated = []
        for msg in all_context:
            msg_key = (msg.get('content', ''), msg.get('role', ''))
            if msg_key not in seen:
                seen.add(msg_key)
                deduplicated.append(msg)

        # Limit total context length
        return deduplicated[-max_context_length:]

    return recent_messages


def _extract_conversation_threads(messages: list) -> list:
    """
    Extract conversation threads/topics from message history.
    Groups related messages into topic clusters.
    """
    if not messages:
        return []

    threads = []
    current_thread = {'topic': None, 'messages': []}

    for msg in messages:
        content = msg.get('content', '').lower()
        role = msg.get('role', '')

        # Extract potential topics from user messages
        if role == 'user':
            topics = _extract_message_topics_from_content(content)
            if topics:
                # Start new thread if topic significantly changes
                if current_thread['messages']:
                    current_thread['topic'] = _determine_thread_topic(current_thread['messages'])
                    threads.append(current_thread)

                current_thread = {'topic': topics[0], 'messages': [msg]}
            else:
                current_thread['messages'].append(msg)
        else:
            current_thread['messages'].append(msg)

    # Add final thread
    if current_thread['messages']:
        current_thread['topic'] = _determine_thread_topic(current_thread['messages'])
        threads.append(current_thread)

    return threads


def _extract_message_topics(current_message: str, normalized_message: str) -> list:
    """Extract key topics/concepts from current message."""
    return _extract_message_topics_from_content(normalized_message or current_message)


def _extract_message_topics_from_content(content: str) -> list:
    """Extract key topics from message content."""
    # Simple topic extraction based on noun phrases and key terms
    content_lower = content.lower()

    # Common topic indicators
    topics = []

    # Extract potential entities/topics
    words = content.split()
    for i, word in enumerate(words):
        # Look for capitalized words or important terms
        if (word[0].isupper() or word in [
            'python', 'javascript', 'java', 'react', 'angular', 'vue',
            'machine learning', 'ai', 'artificial intelligence', 'neural network',
            'database', 'sql', 'mongodb', 'api', 'rest', 'graphql',
            'docker', 'kubernetes', 'aws', 'azure', 'gcp'
        ]):
            topics.append(word.lower())

        # Look for compound terms
        if i < len(words) - 1:
            bigram = f"{word} {words[i+1]}"
            if bigram in ['machine learning', 'artificial intelligence', 'web development', 'data science']:
                topics.append(bigram)

    # Remove duplicates and common stop words
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were'}
    topics = [t for t in topics if t not in stop_words and len(t) > 2]

    return list(set(topics))[:5]  # Limit to top 5 topics


def _determine_thread_topic(messages: list) -> str:
    """Determine the main topic of a conversation thread."""
    all_content = ' '.join([msg.get('content', '') for msg in messages if msg.get('role') == 'user'])
    topics = _extract_message_topics_from_content(all_content)
    return topics[0] if topics else 'general'


def _find_relevant_threads(threads: list, current_topics: list) -> list:
    """Find threads most relevant to current topics."""
    if not current_topics or not threads:
        return threads[-3:]  # Return most recent threads if no topics

    scored_threads = []

    for thread in threads:
        thread_topic = thread.get('topic', '')
        score = 0

        # Topic matching
        for current_topic in current_topics:
            if current_topic in thread_topic or thread_topic in current_topic:
                score += 3
            # Partial matches
            current_words = set(current_topic.split())
            thread_words = set(thread_topic.split())
            if current_words & thread_words:
                score += 1

        # Recency boost (more recent threads slightly preferred)
        thread_messages = thread.get('messages', [])
        if thread_messages:
            # Simple recency based on position in list (assuming chronological order)
            recency_score = len(threads) - threads.index(thread)
            score += recency_score * 0.1

        scored_threads.append((score, thread))

    # Sort by score and return top threads
    scored_threads.sort(key=lambda x: x[0], reverse=True)
    return [thread for _, thread in scored_threads[:5]]


def _detect_multi_turn_intent(message: str, context: list) -> dict:
    """
    Enhanced multi-turn query detection and intent analysis.
    """
    intent_info = {
        'is_follow_up': False,
        'is_clarification': False,
        'references_previous': False,
        'topic_continuation': False,
        'confidence': 0.0
    }

    message_lower = message.lower()

    # Follow-up indicators
    follow_up_indicators = [
        'tell me more', 'explain more', 'what about', 'how about', 'why is',
        'what do you mean', 'can you elaborate', 'give me details',
        'what are the', 'how does', 'what is the'
    ]

    for indicator in follow_up_indicators:
        if indicator in message_lower:
            intent_info['is_follow_up'] = True
            intent_info['confidence'] = 0.8
            break

    # Clarification requests
    clarification_indicators = [
        'what do you mean', 'i don\'t understand', 'can you clarify',
        'what is', 'explain', 'clarify', 'what does that mean'
    ]

    if any(indicator in message_lower for indicator in clarification_indicators):
        intent_info['is_clarification'] = True
        intent_info['confidence'] = max(intent_info['confidence'], 0.7)

    # Check if message references previous context
    if context:
        recent_user_messages = [msg.get('content', '') for msg in context[-6:] if msg.get('role') == 'user']
        recent_assistant_messages = [msg.get('content', '') for msg in context[-6:] if msg.get('role') == 'assistant']

        # Check for pronouns and context references
        context_references = ['it', 'that', 'this', 'those', 'these', 'them', 'they', 'he', 'she', 'the']
        if any(ref in message_lower.split()[:3] for ref in context_references):
            intent_info['references_previous'] = True
            intent_info['confidence'] = max(intent_info['confidence'], 0.6)

        # Topic continuity check
        current_topics = _extract_message_topics_from_content(message)
        context_topics = []
        for msg in recent_user_messages + recent_assistant_messages:
            context_topics.extend(_extract_message_topics_from_content(msg))

        if current_topics and context_topics:
            common_topics = set(current_topics) & set(context_topics)
            if common_topics:
                intent_info['topic_continuation'] = True
                intent_info['confidence'] = max(intent_info['confidence'], 0.5)

    return intent_info


def check_result_setter(query, model_name='thor-1.1'):
    """
    Check if the query has a pre-set answer in the Result Setter.
    Returns the authoritative answer if found, None otherwise.
    
    Uses fuzzy matching to handle variations in how questions are asked.
    Supports both Thor 1.0 and Thor 1.1 result setters.
    """
    try:
        # Use appropriate result setter file based on model
        # Thor 1.1 imports base knowledge from Thor 1.0
        qa_pairs = []
        
        # First, check model-specific file
        if model_name == 'thor-1.0':
            rs_file = THOR_1_0_RESULT_SETTER_FILE
        else:
            rs_file = THOR_1_1_RESULT_SETTER_FILE
        
        if os.path.exists(rs_file):
            with open(rs_file, 'r', encoding='utf-8') as f:
                qa_data = json.load(f)
                qa_pairs.extend(qa_data.get('qa_pairs', []))
        
        # For Thor 1.1, also import base knowledge from Thor 1.0
        if model_name == 'thor-1.1' and os.path.exists(THOR_1_0_RESULT_SETTER_FILE):
            with open(THOR_1_0_RESULT_SETTER_FILE, 'r', encoding='utf-8') as f:
                qa_data_1_0 = json.load(f)
                # Merge, avoiding duplicates by question
                existing_questions = {qa.get('question', '').lower().strip() for qa in qa_pairs}
                for qa in qa_data_1_0.get('qa_pairs', []):
                    question_lower = qa.get('question', '').lower().strip()
                    if question_lower and question_lower not in existing_questions:
                        qa_pairs.append(qa)
                        existing_questions.add(question_lower)
        
        if not qa_pairs:
            return None
        
        # Normalize the query for matching
        query_lower = query.lower().strip()
        query_words = set(query_lower.split())
        
        # Try exact match first
        for qa in qa_pairs:
            question_lower = qa.get('question', '').lower().strip()
            if query_lower == question_lower:
                print(f"[Result Setter] Exact match found for: {query}")
                answers = [q.get('answer', '') for q in qa_pairs if q.get('question', '').lower().strip() == question_lower]
                unique_answers = list(dict.fromkeys([a for a in answers if a]))
                if len(unique_answers) > 1:
                    combined = "; ".join(unique_answers)
                    return combined
                return qa.get('answer')
        
        # Try fuzzy matching - check if query contains the question or vice versa
        best_match = None
        best_score = 0
        
        def _strip_prefix(text: str, prefix_regex: str) -> str:
            text = text.lower().strip()
            text = re.sub(prefix_regex, "", text)
            return text.strip(" ?!.")

        for qa in qa_pairs:
            question = qa.get('question', '').strip()
            question_lower = question.lower()
            question_words = set(question_lower.split())
            
            # SPECIAL CASE: tighten "who is ..." and "do you know ..." matches to avoid cross-person leakage
            if query_lower.startswith(("who is", "who was", "who's")):
                qname = _strip_prefix(query_lower, r"^who\s+(is|was|'s)\s+")
                tname = _strip_prefix(question_lower, r"^who\s+(is|was|'s)\s+")
                if qname and tname and not (qname in tname or tname in qname):
                    continue  # names do not overlap -> skip

            if query_lower.startswith("do you know"):
                qname = _strip_prefix(query_lower, r"^do\s+you\s+know\s+")
                tname = _strip_prefix(question_lower, r"^do\s+you\s+know\s+")
                if qname and tname and not (qname in tname or tname in qname):
                    continue  # names do not overlap -> skip

            # Calculate word overlap score
            common_words = query_words.intersection(question_words)
            if len(common_words) > 0:
                # Score based on percentage of words in common
                score = len(common_words) / max(len(query_words), len(question_words))
                
                # Boost score if query contains question or vice versa
                if question_lower in query_lower or query_lower in question_lower:
                    score += 0.5
                
                # Check for key question words match
                key_words = {'what', 'how', 'why', 'when', 'where', 'who', 'which'}
                query_key_words = query_words.intersection(key_words)
                question_key_words = question_words.intersection(key_words)
                if query_key_words == question_key_words and len(query_key_words) > 0:
                    score += 0.2
                
                if score > best_score:
                    best_score = score
                    best_match = qa
        
        # Return match if score is high enough (at least 60% similarity)
        min_score = 0.6
        if query_lower.startswith(("who is", "who was", "who's", "do you know")):
            min_score = 0.8

        if best_match and best_score >= min_score:
            print(f"[Result Setter] Fuzzy match found (score: {best_score:.2f}) for: {query}")
            print(f"[Result Setter] Matched question: {best_match.get('question')}")
            matched_question_lower = best_match.get('question', '').lower().strip()
            sibling_answers = [
                q.get('answer', '')
                for q in qa_pairs
                if q.get('question', '').lower().strip() == matched_question_lower
            ]
            unique_answers = list(dict.fromkeys([a for a in sibling_answers if a]))
            if len(unique_answers) > 1:
                combined = "; ".join(unique_answers)
                return combined
            return best_match.get('answer')
        
        return None
        
    except Exception as e:
        print(f"[Result Setter] Error checking result setter: {e}")
        return None


def get_model(model_name='thor-1.1', force_reload=False):
    """Get or initialize the model instance.

    Args:
        model_name: 'thor-1.0', 'thor-1.1', 'thor-1.2', 'qwen3-thor', 'antelope-1.0', 'antelope-1.1', or 'knowledge-only' (default: thor-1.1)
        force_reload: Force reload of the model
    """
    global model_instances, MODEL_DIR, TOKENIZER_DIR, CONFIG_PATH, THOR_DIR

    # Handle knowledge-only mode (no model needed)
    if model_name == 'knowledge-only':
        return None

    # Map only thor-1.1 to qwen3-thor (combined model). Thor 1.2 has its own backend.
    if model_name == 'thor-1.1':
        model_name = 'qwen3-thor'

    # Validate model name
    if model_name not in model_instances:
        model_name = 'thor-1.2'  # Default to Thor 1.2 (improved, loads instantly)

    # Set paths based on model version
    if model_name == 'thor-1.0':
        THOR_DIR = THOR_1_0_DIR
        model_dir = str(THOR_1_0_DIR / "models")
        tokenizer_dir = str(THOR_1_0_DIR / "models")
        config_file = str(THOR_1_0_DIR / "config" / "config.yaml")
    elif model_name == 'thor-1.2':
        THOR_DIR = THOR_1_2_DIR
        model_dir = str(THOR_1_2_DIR / "models")
        tokenizer_dir = str(THOR_1_2_DIR / "models")
        config_file = str(THOR_1_2_DIR / "config" / "config.yaml")
    elif model_name == 'antelope-1.0':
        THOR_DIR = ANTELOPE_1_0_DIR
        model_dir = str(ANTELOPE_1_0_DIR / "models")
        tokenizer_dir = str(ANTELOPE_1_0_DIR / "models")
        config_file = str(ANTELOPE_1_0_DIR / "config" / "config.yaml")
    elif model_name == 'qwen3-thor':
        # Use combined Qwen3-4B + Thor 1.1 model
        THOR_DIR = THOR_1_1_DIR
        model_dir = str(THOR_1_1_DIR / "models")
        tokenizer_dir = str(THOR_1_1_DIR / "models")
        config_file = str(THOR_1_1_DIR / "config" / "config.yaml")
    else:  # thor-1.1 (legacy)
        THOR_DIR = THOR_1_1_DIR
        model_dir = str(THOR_1_1_DIR / "models")
        tokenizer_dir = str(THOR_1_1_DIR / "models")
        config_file = str(THOR_1_1_DIR / "config" / "config.yaml")
    
    if model_instances[model_name] is None or force_reload:
        # In serverless/lite deployments we may not ship torch/model weights.
        if torch is None:
            model_loading_progress[model_name] = {'progress': 0, 'status': 'failed', 'message': 'PyTorch not available'}
            return None
        
        # Update progress tracking
        progress_key = 'thor-1.1' if model_name == 'qwen3-thor' else model_name
        if progress_key in model_loading_progress:
            model_loading_progress[progress_key]['status'] = 'loading'
            model_loading_progress[progress_key]['progress'] = 10
            model_loading_progress[progress_key]['message'] = 'Initializing model loading...'
        
        if model_name == 'qwen3-thor':
            # Load combined Qwen3-4B + Thor 1.1 model using AllRounderInference
            # AllRounderInference internally uses Qwen3ThorWrapper which loads Qwen3-4B
            try:
                # #region agent log
                import json
                try:
                    with open('/Users/arulhania/Coding/atlas-ai/.cursor/debug.log', 'a') as f:
                        f.write(json.dumps({"id":f"log_{int(__import__('time').time())}_{__import__('secrets').token_hex(3)}","timestamp":int(__import__('time').time()*1000),"location":"app.py:1104","message":"Starting Qwen3-Thor model load","data":{"model_name":model_name,"config_file":config_file},"sessionId":"debug-session","runId":"verify-fixes","hypothesisId":"B"})+"\n")
                except: pass
                # #endregion agent log
                # Update progress
                if progress_key in model_loading_progress:
                    model_loading_progress[progress_key]['progress'] = 20
                    model_loading_progress[progress_key]['message'] = 'Setting up paths...'
                
                # Ensure correct path is in sys.path for imports
                # Remove ALL thor paths first to avoid conflicts
                thor_paths_to_remove = [
                    str(THOR_1_0_DIR),
                    str(THOR_1_1_DIR),
                    str(THOR_1_2_DIR),
                    str(ANTELOPE_1_0_DIR),
                    str(ANTELOPE_1_1_DIR)
                ]
                for path in thor_paths_to_remove:
                    if path in sys.path:
                        sys.path.remove(path)
                
                # Now add the correct path
                current_thor_path = str(THOR_DIR)
                sys.path.insert(0, current_thor_path)

                # Update progress
                if progress_key in model_loading_progress:
                    model_loading_progress[progress_key]['progress'] = 40
                    model_loading_progress[progress_key]['message'] = 'Importing model classes...'

                # Use AllRounderInference which loads Qwen3ThorWrapper (Qwen3-4B + Thor task heads)
                # Force fresh import to avoid cached thor-1.0 module
                import importlib
                # Remove cached inference module if it exists (to avoid importing thor-1.0 version)
                modules_to_remove = [k for k in list(sys.modules.keys()) if k == 'inference' or k.endswith('.inference')]
                for mod in modules_to_remove:
                    try:
                        mod_file = sys.modules[mod].__file__ if hasattr(sys.modules[mod], '__file__') else None
                        if mod_file and 'thor-1.0' in str(mod_file):
                            del sys.modules[mod]
                    except:
                        pass
                
                # Now import fresh from current directory (thor-1.1)
                from inference import AllRounderInference  # type: ignore
                
                # Update progress
                if progress_key in model_loading_progress:
                    model_loading_progress[progress_key]['progress'] = 60
                    model_loading_progress[progress_key]['message'] = 'Loading Qwen3-4B base model...'
                
                # AllRounderInference will load Qwen3-4B internally via Qwen3ThorWrapper
                # Qwen3Loader will automatically use local path (models/thor-1.1/qwen3-4b/) if available
                # Otherwise falls back to HuggingFace
                # But we need a valid config path
                if not config_file or not os.path.exists(config_file):
                    # Fallback to default config path
                    config_file = str(THOR_1_1_DIR / "config" / "config.yaml")
                    if not os.path.exists(config_file):
                        raise FileNotFoundError(f"Config file not found: {config_file}")
                
                print(f"[Qwen3-Thor] Using config file: {config_file}")
                print(f"[Qwen3-Thor] Config file exists: {os.path.exists(config_file)}")
                
                try:
                    print(f"[Qwen3-Thor] Creating AllRounderInference instance...")
                    print(f"[Qwen3-Thor] model_path='', tokenizer_path='', config_path='{config_file}'")
                    model_instances[model_name] = AllRounderInference(
                        model_path="",  # Not used - Qwen3 loaded from local path or HuggingFace
                        tokenizer_path="",  # Not used - Qwen3 tokenizer loaded from local path or HuggingFace
                        config_path=config_file
                    )
                    print(f"[Qwen3-Thor] AllRounderInference created successfully")
                except Exception as e:
                    # Log full traceback for any error
                    print(f"[Qwen3-Thor] Error creating AllRounderInference: {type(e).__name__}: {e}")
                    import traceback
                    print("[Qwen3-Thor] Full traceback:")
                    traceback.print_exc()
                    raise
                
                # #region agent log
                try:
                    with open('/Users/arulhania/Coding/atlas-ai/.cursor/debug.log', 'a') as f:
                        f.write(json.dumps({"id":f"log_{int(__import__('time').time())}_{__import__('secrets').token_hex(3)}","timestamp":int(__import__('time').time()*1000),"location":"app.py:1138","message":"Qwen3-Thor model loaded successfully","data":{"model_name":model_name,"has_model":model_instances[model_name] is not None},"sessionId":"debug-session","runId":"verify-fixes","hypothesisId":"B"})+"\n")
                except: pass
                # #endregion agent log
                
                # Update progress - complete
                if progress_key in model_loading_progress:
                    model_loading_progress[progress_key]['progress'] = 100
                    model_loading_progress[progress_key]['status'] = 'loaded'
                    model_loading_progress[progress_key]['message'] = 'Model loaded successfully'
                
                if force_reload:
                    print(f"✅ Combined Qwen3-4B + Thor 1.1 model reloaded successfully")
                else:
                    print(f"✅ Combined Qwen3-4B + Thor 1.1 model loaded successfully")
                    print(f"   Using Qwen3-4B base model (from local path or HuggingFace) with Thor task heads")
            except Exception as e:
                print(f"❌ Error loading combined Qwen3-Thor model: {e}")
                import traceback
                traceback.print_exc()
                model_instances[model_name] = None
                if progress_key in model_loading_progress:
                    # Use error handling utility to log and track error with progress
                    log_model_loading_error(model_name, e, model_loading_progress.get(progress_key))
                    model_loading_progress[progress_key]['status'] = 'failed'
                    model_loading_progress[progress_key]['message'] = f'Loading failed: {str(e)[:100]}'
                    # Ensure progress is preserved even on error
                    if 'progress' not in model_loading_progress[progress_key]:
                        model_loading_progress[progress_key]['progress'] = 0
        else:
            # Load traditional Thor models
            model_path = os.path.join(model_dir, "final_model.pt")
            tokenizer_path = os.path.join(tokenizer_dir, "tokenizer.json")

            if os.path.exists(model_path) and os.path.exists(tokenizer_path):
                try:
                    # Update progress
                    if progress_key in model_loading_progress:
                        model_loading_progress[progress_key]['progress'] = 20
                        model_loading_progress[progress_key]['message'] = 'Checking model files...'
                    
                    # Ensure correct path is in sys.path for imports
                    # Remove ALL thor paths first to avoid conflicts
                    thor_paths_to_remove = [
                        str(THOR_1_0_DIR),
                        str(THOR_1_1_DIR),
                        str(THOR_1_2_DIR),
                        str(ANTELOPE_1_0_DIR),
                        str(ANTELOPE_1_1_DIR)
                    ]
                    for path in thor_paths_to_remove:
                        if path in sys.path:
                            sys.path.remove(path)
                    
                    # Now add the correct path
                    current_thor_path = str(THOR_DIR)
                    sys.path.insert(0, current_thor_path)

                    # Update progress
                    if progress_key in model_loading_progress:
                        model_loading_progress[progress_key]['progress'] = 40
                        model_loading_progress[progress_key]['message'] = 'Importing model classes...'

                    # Lazy import to avoid hard dependency in lightweight deployments.
                    from inference import AllRounderInference  # type: ignore
                    
                    # Update progress
                    if progress_key in model_loading_progress:
                        model_loading_progress[progress_key]['progress'] = 60
                        model_loading_progress[progress_key]['message'] = 'Loading model weights...'
                    
                    model_instances[model_name] = AllRounderInference(
                        model_path=model_path,
                        tokenizer_path=tokenizer_path,
                        config_path=config_file
                    )
                    
                    # Update progress - complete
                    if progress_key in model_loading_progress:
                        model_loading_progress[progress_key]['progress'] = 100
                        model_loading_progress[progress_key]['status'] = 'loaded'
                        model_loading_progress[progress_key]['message'] = 'Model loaded successfully'
                    
                    if force_reload:
                        print(f"Model {model_name} reloaded successfully (auto-trained)")
                    else:
                        print(f"Model {model_name} loaded successfully")
                except Exception as e:
                    print(f"Error loading model {model_name}: {e}")
                    model_instances[model_name] = None
                    if progress_key in model_loading_progress:
                        # Use error handling utility to log and track error with progress
                        log_model_loading_error(model_name, e, model_loading_progress.get(progress_key))
                        model_loading_progress[progress_key]['status'] = 'failed'
                        model_loading_progress[progress_key]['message'] = f'Loading failed: {str(e)[:100]}'
                        # Ensure progress is preserved even on error
                        if 'progress' not in model_loading_progress[progress_key]:
                            model_loading_progress[progress_key]['progress'] = 0
            else:
                print(f"Model files not found for {model_name}. Expected: {model_path}, {tokenizer_path}")
                if progress_key in model_loading_progress:
                    # Use error handling utility
                    error = FileNotFoundError(f"Model files not found: {model_path}, {tokenizer_path}")
                    log_model_loading_error(model_name, error, model_loading_progress.get(progress_key))
                    model_loading_progress[progress_key]['status'] = 'failed'
                    model_loading_progress[progress_key]['message'] = 'Model files not found'
                    # Ensure progress is preserved even on error
                    if 'progress' not in model_loading_progress[progress_key]:
                        model_loading_progress[progress_key]['progress'] = 0
    
    # If model is already loaded, mark progress as complete
    # Only update progress to "loaded" if model is actually functional
    if model_instances[model_name] is not None:
        progress_key = 'thor-1.1' if model_name == 'qwen3-thor' else model_name
        # Don't automatically mark as loaded - let the calling code verify functionality first
        # This prevents false "100% loaded" when model loading actually failed
    
    return model_instances[model_name]


def generate_chat_name(first_message, first_response):
    """Generate an intelligent chat name based on first question/response."""
    # Extract key information from the first message
    message = first_message.lower().strip()
    
    # Remove common prefixes
    prefixes = ["what is", "what are", "how to", "how do", "explain", "tell me about", "can you", "help me"]
    for prefix in prefixes:
        if message.startswith(prefix):
            message = message[len(prefix):].strip()
    
    # Extract first meaningful words (up to 4-5 words, max 40 chars)
    words = message.split()[:5]
    name = " ".join(words)
    
    # Capitalize first letter of each word
    name = " ".join(word.capitalize() for word in name.split())
    
    # Limit length
    if len(name) > 40:
        name = name[:37] + "..."
    
    # Fallback if empty
    if not name or len(name.strip()) < 3:
        # Try to extract from response
        response_words = first_response.lower().split()[:4]
        name = " ".join(response_words).capitalize()
        if len(name) > 40:
            name = name[:37] + "..."
        if not name or len(name.strip()) < 3:
            name = "New Chat"
    
    return name




_FOLLOW_UP_PRONOUNS = {'it', 'they', 'them', 'this', 'that', 'those', 'these', 'he', 'she', 'him', 'her'}
_QUESTION_TRIGGERS = {'can', 'could', 'would', 'should', 'does', 'do', 'did', 'is', 'are', 'was', 'were', 'will'}
_QUESTION_WORDS = {'what', 'how', 'why', 'when', 'where', 'who', 'which', 'whom'}


def _has_explicit_subject(message):
    """Check if message already specifies a subject (proper noun, acronym, or keyword)."""
    tokens = message.split()
    for token in tokens:
        stripped = token.strip(".,!?\"'()")
        if len(stripped) < 2:
            continue
        lower = stripped.lower()
        if lower in _FOLLOW_UP_PRONOUNS or lower in _QUESTION_WORDS or lower in _QUESTION_TRIGGERS:
            continue
        if stripped[0].isupper():
            return True
        if any(char.isdigit() for char in stripped):
            return True
        if '-' in stripped:
            parts = stripped.split('-')
            if any(part and part[0].isupper() for part in parts):
                return True
    return False


def _is_pronoun_follow_up(message):
    """Detect short pronoun-based follow-up questions like 'What can it do?'"""
    words = [re.sub(r'[^a-z0-9]', '', w.lower()) for w in message.split()]
    words = [w for w in words if w]
    if not words or len(words) > 10:
        return False
    if not any(word in _FOLLOW_UP_PRONOUNS for word in words):
        return False
    if not any(word in _QUESTION_TRIGGERS for word in words):
        return False
    if _has_explicit_subject(message):
        return False
    return True


def _evaluate_math(expression):
    """
    Evaluate simple math expressions safely.
    
    This function now uses safe_evaluate_math from utils instead of eval(),
    preventing arbitrary code execution vulnerabilities.
    """
    return safe_evaluate_math(expression)


def _is_solvable_problem(message: str) -> bool:
    """
    Detect if the message is a problem that should be solved by the model
    instead of searching the web (math word problems, logic puzzles, reasoning tasks).
    """
    lower = message.lower()
    
    # Math word problem indicators
    math_indicators = [
        'how many', 'how much', 'calculate', 'compute', 'solve',
        'total', 'sum', 'difference', 'product', 'quotient',
        'add', 'subtract', 'multiply', 'divide', 'plus', 'minus',
        'cookies', 'apples', 'dollars', 'cents', 'meters', 'miles',
        'years old', 'age', 'speed', 'distance', 'time',
        'left', 'remaining', 'have left', 'has left'
    ]
    
    # Logic/reasoning indicators
    reasoning_indicators = [
        'if', 'then', 'therefore', 'because', 'since',
        'puzzle', 'riddle', 'brain teaser',
        'what would happen', 'what if'
    ]
    
    # Check for number patterns (indicates math problem)
    import re
    has_numbers = bool(re.search(r'\b\d+\b', message))
    
    # Check for math/reasoning indicators
    has_math_indicator = any(indicator in lower for indicator in math_indicators)
    has_reasoning_indicator = any(indicator in lower for indicator in reasoning_indicators)
    
    # It's a solvable problem if:
    # 1. Has numbers + math indicators (word problem)
    # 2. Has reasoning indicators (logic puzzle)
    # 3. Starts with "solve" or "calculate"
    is_solvable = (
        (has_numbers and has_math_indicator) or
        has_reasoning_indicator or
        lower.startswith(('solve', 'calculate', 'compute', 'find the'))
    )
    
    return is_solvable


def _solve_simple_math_problem(message: str) -> str:
    """
    Solve simple math word problems directly without web search.
    Returns a solution string or None if can't solve.
    """
    import re
    lower = message.lower()
    
    # Extract numbers from the problem
    numbers = [int(n) for n in re.findall(r'\b\d+\b', message)]
    
    if len(numbers) < 2:
        return None
    
    # Detect operation type
    if any(word in lower for word in ['take away', 'takes away', 'subtract', 'minus', 'left', 'remaining', 'have left', 'has left', 'gave away', 'lost']):
        # Subtraction problem
        result = numbers[0] - sum(numbers[1:])
        operation = "subtraction"
        explanation = f"{numbers[0]} - {' - '.join(map(str, numbers[1:]))} = {result}"
    elif any(word in lower for word in ['add', 'plus', 'total', 'sum', 'altogether', 'combined', 'got', 'received', 'gained']):
        # Addition problem
        result = sum(numbers)
        operation = "addition"
        explanation = f"{' + '.join(map(str, numbers))} = {result}"
    elif any(word in lower for word in ['multiply', 'times', 'product', 'each']):
        # Multiplication problem
        result = numbers[0]
        for n in numbers[1:]:
            result *= n
        operation = "multiplication"
        explanation = f"{' × '.join(map(str, numbers))} = {result}"
    elif any(word in lower for word in ['divide', 'split', 'share', 'per']):
        # Division problem
        result = numbers[0]
        for n in numbers[1:]:
            if n != 0:
                result = result / n
        operation = "division"
        explanation = f"{numbers[0]} ÷ {' ÷ '.join(map(str, numbers[1:]))} = {result}"
    else:
        # Default to subtraction for "left" problems
        if 'left' in lower or 'remaining' in lower:
            result = numbers[0] - sum(numbers[1:])
            operation = "subtraction"
            explanation = f"{numbers[0]} - {' - '.join(map(str, numbers[1:]))} = {result}"
        else:
            return None
    
    # Format result
    if isinstance(result, float) and result.is_integer():
        result = int(result)
    
    return f"Let me solve this step by step:\n\n{explanation}\n\n**Answer: {result}**"


def _extract_image_request(message: str) -> str:
    """Return the subject of a web image request if present."""
    if not message:
        return ""
    text = message.strip()
    patterns = [
        r'^\s*(?:create|generate|make|draw|show)\s+(?:a\s+)?(?:beautiful\s+|personalized\s+|custom\s+|nice\s+|cool\s+)?(?:image|picture|photo|portrait|drawing)\s+of\s+(.+)',
        r'\b(?:image|picture|photo|portrait|drawing)\s+of\s+(.+)',
    ]
    for pat in patterns:
        m = re.search(pat, text, flags=re.IGNORECASE)
        if m:
            return m.group(1).strip(" .!?")
    return ""


def _normalize_image_url(url: str, subject: str) -> str:
    """Ensure the image URL is a valid https URL; otherwise use image handler."""
    image_handler = get_image_handler()
    if not url:
        return image_handler.get_image_url(subject, "960x540")
    url = url.strip()
    if url.startswith("http://"):
        url = "https://" + url[len("http://"):]
    if not url.startswith("https://"):
        return image_handler.get_image_url(subject, "960x540")
    return url


def fetch_image_from_web(subject: str) -> str:
    """Fetch an image URL from the web for the subject using ImageHandler."""
    if not subject:
        return ""
    try:
        image_handler = get_image_handler()
        url, _ = image_handler.get_image(subject, "960x540")
        return url
    except Exception as e:
        print(f"[Image Search] Error fetching image for '{subject}': {e}")
        # Fallback to Lorem Picsum with deterministic seed
        import hashlib
        seed = hashlib.md5(subject.lower().encode()).hexdigest()[:8]
        return f"https://picsum.photos/seed/{seed}/960/540"


def save_chat(chat_id, messages, chat_name=None):
    """Save chat to disk."""
    chat_file = os.path.join(CHATS_DIR, f"{chat_id}.json")
    
    # Load existing chat to preserve name if it exists
    existing_chat = load_chat(chat_id)
    if existing_chat and existing_chat.get("name") and not chat_name:
        chat_name = existing_chat.get("name")
    elif not chat_name and len(messages) >= 2:
        # Generate name from first question/response
        first_user_msg = next((msg.get("content", "") for msg in messages if msg.get("role") == "user"), "")
        first_assistant_msg = next((msg.get("content", "") for msg in messages if msg.get("role") == "assistant"), "")
        if first_user_msg and first_assistant_msg:
            chat_name = generate_chat_name(first_user_msg, first_assistant_msg)
    
    chat_data = {
        "chat_id": chat_id,
        "created_at": existing_chat.get("created_at", datetime.now().isoformat()) if existing_chat else datetime.now().isoformat(),
        "name": chat_name or "New Chat",
        "messages": messages
    }
    with open(chat_file, 'w') as f:
        json.dump(chat_data, f, indent=2)


def load_chat(chat_id):
    """Load chat from disk."""
    chat_file = os.path.join(CHATS_DIR, f"{chat_id}.json")
    if os.path.exists(chat_file):
        with open(chat_file, 'r') as f:
            return json.load(f)
    return None


def list_chats():
    """List all saved chats."""
    chats = []
    if os.path.exists(CHATS_DIR):
        for file in os.listdir(CHATS_DIR):
            if file.endswith('.json'):
                chat_id = file[:-5]  # Remove .json
                chat_data = load_chat(chat_id)
                if chat_data:
                    # Generate name if missing
                    name = chat_data.get("name")
                    if not name and len(chat_data.get("messages", [])) >= 2:
                        first_user_msg = next((msg.get("content", "") for msg in chat_data.get("messages", []) if msg.get("role") == "user"), "")
                        first_assistant_msg = next((msg.get("content", "") for msg in chat_data.get("messages", []) if msg.get("role") == "assistant"), "")
                        if first_user_msg and first_assistant_msg:
                            name = generate_chat_name(first_user_msg, first_assistant_msg)
                            # Update the chat with the generated name
                            save_chat(chat_id, chat_data.get("messages", []), name)
                    
                    chats.append({
                        "chat_id": chat_id,
                        "name": name or "New Chat",
                        "created_at": chat_data.get("created_at", ""),
                        "message_count": len(chat_data.get("messages", []))
                    })
    # Sort by created_at, newest first
    chats.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return chats


# API Key Management
API_KEYS_FILE = BASE_DIR / "api-keys.json"

def _load_api_keys():
    """Load API keys from file."""
    try:
        if API_KEYS_FILE.exists():
            with open(API_KEYS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('keys', [])
    except Exception as e:
        print(f"[API Keys] Error loading API keys: {e}")
    return []

def _save_api_keys(keys):
    """Save API keys to file."""
    try:
        API_KEYS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(API_KEYS_FILE, 'w', encoding='utf-8') as f:
            json.dump({'keys': keys}, f, indent=2)
    except Exception as e:
        print(f"[API Keys] Error saving API keys: {e}")

def _validate_api_key(api_key):
    """Validate an API key and return model info if valid."""
    keys = _load_api_keys()
    for key_data in keys:
        if key_data.get('key') == api_key:
            # Update last_used timestamp
            key_data['last_used'] = datetime.now().isoformat()
            _save_api_keys(keys)
            return {
                'valid': True,
                'model': key_data.get('model'),
                'created_at': key_data.get('created_at'),
                'last_used': key_data.get('last_used')
            }
    return {'valid': False}

def _register_api_key(api_key, model):
    """Register a new API key."""
    if not api_key or not model:
        return False

    # Validate model
    if model not in ['thor-1.0', 'thor-1.1', 'thor-1.2', 'antelope-1.1']:
        return False

    keys = _load_api_keys()

    # Check if key already exists
    for key_data in keys:
        if key_data.get('key') == api_key:
            return False  # Key already registered

    # Add new key
    key_data = {
        'key': api_key,
        'model': model,
        'created_at': datetime.now().isoformat(),
        'last_used': None
    }
    keys.append(key_data)
    _save_api_keys(keys)
    return True


@app.route('/api/keys/register', methods=['POST'])
def register_api_key():
    """Register a new API key."""
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'JSON data required'}), 400

        api_key = data.get('key', '').strip()
        model = data.get('model', '').strip()

        if not api_key or not model:
            return jsonify({'error': 'key and model are required'}), 400

        # Validate key format
        if not api_key.startswith(f'{model}-'):
            return jsonify({'error': f'Key must start with {model}-'}), 400

        if _register_api_key(api_key, model):
            return jsonify({
                'success': True,
                'key': api_key,
                'model': model,
                'message': 'API key registered successfully'
            })
        else:
            return jsonify({'error': 'Failed to register API key'}), 500

    except Exception as e:
        print(f"[API Keys] Error registering key: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/keys/validate')
def validate_api_key():
    """Validate an API key."""
    api_key = request.args.get('key', '').strip()
    if not api_key:
        return jsonify({'error': 'key parameter required'}), 400

    result = _validate_api_key(api_key)
    return jsonify(result)


@app.route('/')
def index():
    """Render the main chat interface."""
    return render_template('index.html')


@app.route('/install')
def install():
    """Render the macOS installation page."""
    return render_template('install.html')


@app.route('/update')
def update():
    """Render the update checker page (for macOS app only)."""
    return render_template('update.html')


@app.route('/api/translate', methods=['POST'])
def translate_text():
    """Translate text to target language using Google Translate public API."""
    try:
        data = request.json
        text = data.get('text', '').strip()
        target_lang = data.get('target_language', 'en')
        
        if not text:
            return jsonify({"error": "Text is required"}), 400
        
        # Map language codes to Google Translate codes
        lang_map = {
            'hi-IN': 'hi',  # Hindi
            'ta-IN': 'ta',  # Tamil
            'te-IN': 'te',  # Telugu
            'es-ES': 'es',  # Spanish
            'es-MX': 'es',  # Spanish (Mexico)
            'fr-FR': 'fr',  # French
            'de-DE': 'de',  # German
            'zh-CN': 'zh-cn',  # Chinese Simplified
            'ja-JP': 'ja',  # Japanese
            'ko-KR': 'ko',  # Korean
            'it-IT': 'it',  # Italian
            'pt-BR': 'pt',  # Portuguese
        }
        
        target_code = lang_map.get(target_lang, target_lang.split('-')[0] if '-' in target_lang else target_lang)
        
        # Use Google Translate public API (no key required for basic use)
        import requests
        import urllib.parse
        
        # Google Translate public endpoint
        url = f"https://translate.googleapis.com/translate_a/single"
        params = {
            'client': 'gtx',
            'sl': 'en',  # Source language (always English since model responds in English)
            'tl': target_code,  # Target language
            'dt': 't',
            'q': text
        }
        
        try:
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                result = response.json()
                if result and len(result) > 0 and len(result[0]) > 0:
                    translated_text = ''.join([item[0] for item in result[0] if item[0]])
                    return jsonify({"translated_text": translated_text, "original_text": text, "target_language": target_lang})
                else:
                    return jsonify({"error": "Translation failed: invalid response format"}), 500
            else:
                return jsonify({"error": f"Translation API error: {response.status_code}"}), 500
        except requests.exceptions.RequestException as e:
            print(f"[Translate] Error calling translation API: {e}")
            return jsonify({"error": f"Translation service unavailable: {str(e)}"}), 500
            
    except Exception as e:
        print(f"[Translate] Error in translate endpoint: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Translation error: {str(e)}"}), 500

@app.route('/api/version')
def get_version():
    """Get current and latest version information for update checking."""
    import json
    updates_file = ATLAS_ROOT / 'apps' / 'app' / 'updates.json'
    
    try:
        if updates_file.exists():
            with open(updates_file, 'r') as f:
                version_data = json.load(f)
                # Ensure currentVersion matches package.json if not specified
                package_json = ATLAS_ROOT / 'apps' / 'app' / 'package.json'
                if package_json.exists():
                    with open(package_json, 'r') as pkg:
                        pkg_data = json.load(pkg)
                        if 'currentVersion' not in version_data:
                            version_data['currentVersion'] = pkg_data.get('version', '1.0.0')
                return jsonify(version_data)
        else:
            # Default version info
            package_json = ATLAS_ROOT / 'apps' / 'app' / 'package.json'
            current_ver = '1.0.0'
            if package_json.exists():
                with open(package_json, 'r') as pkg:
                    pkg_data = json.load(pkg)
                    current_ver = pkg_data.get('version', '1.0.0')
            return jsonify({
                'currentVersion': current_ver,
                'latestVersion': current_ver,
                'updates': []
            })
    except Exception as e:
        print(f"Error reading version info: {e}")
        return jsonify({
            'currentVersion': '1.0.0',
            'latestVersion': '1.0.0',
            'updates': [],
            'error': str(e)
        }), 500


@app.route('/download/atlas-windows.exe')
def download_windows_app():
    """Serve the Windows app installer."""
    import os
    dist_dir = ATLAS_ROOT / 'apps' / 'app' / 'dist'
    exe_path = dist_dir / 'Atlas Setup 1.0.0.exe'
    
    if exe_path.exists():
        return send_file(
            str(exe_path),
            as_attachment=True,
            download_name='Atlas-Windows.exe',
            mimetype='application/x-msdownload'
        )
    else:
        return jsonify({
            'error': 'Windows installer not found',
            'message': 'The Windows app has not been built yet. Please run: cd app && npm run build:win'
        }), 404


@app.route('/download/atlas-linux.AppImage')
def download_linux_app():
    """Serve the Linux AppImage."""
    import os
    dist_dir = ATLAS_ROOT / 'apps' / 'app' / 'dist'
    appimage_path = dist_dir / 'Atlas-1.0.0.AppImage'
    
    if appimage_path.exists():
        return send_file(
            str(appimage_path),
            as_attachment=True,
            download_name='Atlas-Linux.AppImage',
            mimetype='application/x-executable'
        )
    else:
        # Try .deb as fallback
        deb_path = dist_dir / 'atlas_1.0.0_amd64.deb'
        if deb_path.exists():
            return send_file(
                str(deb_path),
                as_attachment=True,
                download_name='Atlas-Linux.deb',
                mimetype='application/vnd.debian.binary-package'
            )
        return jsonify({
            'error': 'Linux app not found',
            'message': 'The Linux app has not been built yet. Please run: cd app && npm run build:linux'
        }), 404


@app.route('/download/atlas-macos.dmg')
def download_macos_app():
    """Serve the macOS app DMG file for download."""
    import os
    dist_dir = ATLAS_ROOT / 'apps' / 'app' / 'dist'
    
    # Detect architecture from User-Agent (prefer arm64 for Apple Silicon)
    user_agent = request.headers.get('User-Agent', '').lower()
    is_apple_silicon = 'arm' in user_agent or 'aarch64' in user_agent
    
    # Try to find the appropriate DMG file
    if dist_dir.exists():
        # Prefer arm64 for Apple Silicon, x64 for Intel
        if is_apple_silicon:
            arm64_dmg = dist_dir / 'Atlas-1.0.0-arm64.dmg'
            if arm64_dmg.exists():
                dmg_path = arm64_dmg
            else:
                # Fallback to regular DMG
                dmg_path = dist_dir / 'Atlas-1.0.0.dmg'
        else:
            # For Intel or unknown, prefer regular DMG, fallback to arm64
            regular_dmg = dist_dir / 'Atlas-1.0.0.dmg'
            if regular_dmg.exists():
                dmg_path = regular_dmg
            else:
                dmg_path = dist_dir / 'Atlas-1.0.0-arm64.dmg'
        
        # If specific file doesn't exist, try any DMG
        if not dmg_path.exists():
            dmg_files = list(dist_dir.glob('*.dmg'))
            if dmg_files:
                dmg_path = dmg_files[0]
    else:
        dmg_path = None
    
    if dmg_path and dmg_path.exists():
        return send_file(
            str(dmg_path),
            as_attachment=True,
            download_name='Atlas-macOS.dmg',
            mimetype='application/x-apple-diskimage'
        )
    else:
        # Return a helpful message if DMG doesn't exist
        return jsonify({
            'error': 'DMG file not found',
            'message': 'The macOS app has not been built yet. Please run the build script in the /app directory first.',
            'build_instructions': 'cd app && npm install && npm run build:mac'
        }), 404


@app.route('/api/dev-chat', methods=['POST'])
def dev_chat():
    """Handle chat messages with detailed debugging information."""
    # Get the original request data and add debug_mode flag
    original_data = request.get_json(force=True, silent=True) or {}
    original_data['debug_mode'] = True
    
    # Use Flask's test_request_context to create a new request with modified data
    with app.test_request_context(json=original_data, method='POST'):
        # Now call chat() which will read from this new request context
        return chat()


def _handle_multi_model_comparison(compare_models, contextual_input, task, think_deeper, is_voice_mode,
                                  effective_tone, language_instruction, response_language, data):
    """Handle multi-model comparison for beta feature."""
    try:
        comparison_results = []

        for model_name in compare_models[:3]:  # Limit to 3 models max
            try:
                # Load the specific model
                model = _load_model_for_comparison(model_name, data)

                if not model:
                    comparison_results.append({
                        "model": model_name,
                        "error": f"Model {model_name} not available"
                    })
                    continue

                # Set generation parameters
                if is_voice_mode:
                    max_gen_tokens = 256 if think_deeper else 128
                else:
                    max_gen_tokens = 512 if think_deeper else 256

                # Generate response
                if task == 'text_generation':
                    result = model.predict(contextual_input, task=task, max_new_tokens=max_gen_tokens)
                else:
                    result = model.predict(contextual_input, task=task)

                if result and 'generated_text' in result:
                    response = result['generated_text']

                    # Basic validation
                    if response and len(response.strip()) > 10:
                        comparison_results.append({
                            "model": model_name,
                            "response": response,
                            "length": len(response),
                            "timestamp": datetime.now().isoformat()
                        })
                    else:
                        comparison_results.append({
                            "model": model_name,
                            "error": "Generated response too short or invalid"
                        })
                else:
                    comparison_results.append({
                        "model": model_name,
                        "error": "Failed to generate response"
                    })

            except Exception as e:
                print(f"[Beta] Error generating response for {model_name}: {e}")
                comparison_results.append({
                    "model": model_name,
                    "error": str(e)
                })

        return jsonify({
            "comparison_mode": True,
            "models_compared": compare_models,
            "results": comparison_results,
            "message": f"Compared {len(comparison_results)} models"
        })

    except Exception as e:
        print(f"[Beta] Error in multi-model comparison: {e}")
        return jsonify({"error": "Failed to perform model comparison"}), 500


def _load_model_for_comparison(model_name, data):
    """Load a specific model for comparison."""
    try:
        # Import required services
        from services import get_creative_generator, get_code_handler

        if model_name == 'thor-1.0':
            # Load Thor 1.0
            from thor_1_0.inference import ThorInference
            model = ThorInference()
            model.load_model()
            return model

        elif model_name == 'thor-1.1':
            return get_model(model_name='thor-1.1')
        elif model_name == 'thor-1.2':
            return get_model(model_name='thor-1.2')

        elif model_name.startswith('gem:'):
            # For gem comparison, we'd need to modify the inference to use gem config
            # For now, return None to indicate not supported
            return None

        else:
            return None

    except Exception as e:
        print(f"[Beta] Error loading model {model_name}: {e}")
        return None


def _prepare_structured_output(output_format):
    """Prepare structured output configuration for beta feature."""
    formats = {
        'json': {
            'instruction': 'Respond with valid JSON format only. Structure your answer as a JSON object.',
            'wrapper': lambda x: f'```json\n{x}\n```'
        },
        'table': {
            'instruction': 'Format your response as a markdown table with clear headers and data.',
            'wrapper': lambda x: x  # No wrapper needed for tables
        },
        'csv': {
            'instruction': 'Format your response as CSV data with headers in the first row.',
            'wrapper': lambda x: f'```\n{x}\n```'
        }
    }
    return formats.get(output_format)


@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat messages."""
    # #region agent log
    # Initialize decision tracker for this request
    try:
        import sys
        sys.path.insert(0, str(ATLAS_ROOT / ".cursor"))
        from debug_agent import start_tracking
        data = request.get_json()
        message = data.get('message', '')
        start_tracking(message, run_id="live")
    except Exception:
        pass
    # #endregion agent log
    
    # Security: Rate limiting (v1.4.3o)
    client_ip = request.remote_addr or 'unknown'
    is_allowed, remaining = check_rate_limit(client_ip)
    if not is_allowed:
        return jsonify({
            "error": "Rate limit exceeded. Please wait a moment before sending another message.",
            "retry_after": _rate_limit_window
        }), 429

    # Optional API key validation (for API packages)
    api_key = request.json and request.json.get('api_key')
    if api_key:
        key_validation = _validate_api_key(api_key)
        if not key_validation.get('valid', False):
            return jsonify({
                "error": "Invalid API key",
                "message": "The provided API key is not valid or registered."
            }), 401

    # Check if debug mode is enabled
    debug_mode = request.json and request.json.get('debug_mode', False)
    debug_log = []
    
    def log_debug(step_name, data=None, status="info"):
        """Log debug information if debug mode is enabled"""
        if debug_mode:
            entry = {
                "timestamp": datetime.now().isoformat(),
                "step": step_name,
                "status": status,
                "data": data
            }
            debug_log.append(entry)
            print(f"[DEV] {step_name}: {data if data else 'OK'}")
    
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Invalid request: JSON data required"}), 400
        
        message = data.get('message', '').strip()
        
        # Security: Input validation and sanitization (v1.4.3o)
        sanitized_message, is_valid = validate_and_sanitize_input(message)
        if not is_valid:
            return jsonify({"error": "Invalid input detected"}), 400
        message = sanitized_message
        chat_id = data.get('chat_id')
        task = data.get('task', 'text_generation')  # Default to text generation for chat
        think_deeper = data.get('think_deeper', False)  # Think deeper mode
        code_mode = data.get('code_mode', False)  # Code mode
        code_language = data.get('code_language', 'python')  # Code language (python, javascript, html)
        image_data = data.get('image_data')  # Image data if attached
        
        # Default to Thor 1.2 if no model is loaded
        default_model = 'thor-1.2'
        
        requested_model = (data.get('model') or default_model).strip()
        requested_tone = (data.get('tone') or 'normal').strip()
        response_language = data.get('response_language', 'en-US')  # Language to respond in (from Poseidon)
        is_voice_mode = data.get('voice_mode', False)  # Optimize for voice mode (v4.3.0)
        compare_models = data.get('compare_models', [])  # Beta: Multi-model comparison
        output_format = data.get('output_format')  # Beta: Structured output format
        
        # Beta Feature: Structured output formatting
        structured_output = None
        if output_format and request.headers.get('X-Beta-Mode') == 'true':
            structured_output = _prepare_structured_output(output_format)

        # Enhanced Thor 1.1: Use improved max_new_tokens for longer, more comprehensive responses
        # Optimize for voice mode: shorter, more concise responses (v4.3.0)
        if is_voice_mode:
            max_gen_tokens = 256 if think_deeper else 128  # Shorter for voice mode
        else:
            max_gen_tokens = 512 if think_deeper else 256  # Longer for think deeper mode

        log_debug("Request Received", {
            "message": message[:100],
            "chat_id": chat_id,
            "model": requested_model,
            "tone": requested_tone
        })
        
        # Determine model_name and labels
        model_name = 'thor-1.2'  # Default
        model_label_for_ui = "Thor 1.2"
        
        # Check for AI models first, then fall back to system mode
        if 'ai-direct' in model_instances and model_instances['ai-direct']['type'] == 'direct':
            model_name = 'ai-direct'
            model_label_for_ui = "Atlas AI (AI Model)"
        else:
            system_mode = data.get('system_mode', 'latest')
            if system_mode == 'stable':
                model_name = 'thor-1.0'
                model_label_for_ui = "Thor 1.0 (Stable)"
            elif system_mode == 'knowledge':
                model_name = 'knowledge-only'
                model_label_for_ui = "Atlas AI (Knowledge-Based)"
            else:
                # Latest mode
                if requested_model == 'thor-1.1':
                    model_name = 'qwen3-thor'
                    model_label_for_ui = "Thor 1.1"
                else:
                    model_name = 'thor-1.2'
                    model_label_for_ui = "Thor 1.2"
        
        # Explicit override
        if requested_model in ['thor-1.0', 'thor-1.1', 'thor-1.2', 'antelope-1.1']:
            if requested_model == 'thor-1.0':
                model_name = 'thor-1.0'
                model_label_for_ui = "Thor 1.0"
            elif requested_model == 'thor-1.1':
                model_name = 'qwen3-thor'
                model_label_for_ui = "Thor 1.1"
            elif requested_model == 'thor-1.2':
                model_name = 'thor-1.2'
                model_label_for_ui = "Thor 1.2"
            elif requested_model == 'antelope-1.1':
                model_name = 'antelope-1.1'
                model_label_for_ui = "Antelope 1.1"
        
        gem_config = None
        gem_knowledge = []

        # Resolve gem selection (saved gem or preview gem)
        try:
            if requested_model == "gem:preview" and isinstance(data.get("gem_draft"), dict):
                draft = data.get("gem_draft") or {}
                gem_config = {
                    "id": "preview",
                    "name": (draft.get("name") or "Gem").strip()[:60],
                    "description": (draft.get("description") or "").strip(),
                    "instructions": (draft.get("instructions") or "").strip(),
                    "tone": (draft.get("tone") or requested_tone or "normal").strip(),
                    "sources": draft.get("sources") or {"links": [], "files": []},
                }
                model_label_for_ui = f"Gem: {gem_config.get('name')} (Try)"
            elif requested_model.startswith("gem:") and requested_model != "gem:preview":
                gem_id = requested_model.replace("gem:", "", 1).strip()
                found = _get_gem_by_id(gem_id)
                if found:
                    gem_config = found
                    model_label_for_ui = f"Gem: {found.get('name', 'Gem')}"
        except Exception:
            gem_config = None

        if gem_config:
            try:
                # Debug: print gem config to see what we're working with
                print(f"[Gem] Loading sources for gem: {gem_config.get('name', 'unknown')}")
                print(f"[Gem] Sources structure: {gem_config.get('sources', {})}")
                gem_knowledge = _gem_sources_to_knowledge(gem_config)
                print(f"[Gem] Extracted {len(gem_knowledge)} knowledge items from sources")
                if gem_knowledge:
                    for k in gem_knowledge[:3]:
                        print(f"[Gem]   - {k.get('title', 'no title')[:60]} ({len(k.get('content', ''))} chars)")
            except Exception as e:
                print(f"[Gem] Error converting sources to knowledge: {e}")
                import traceback
                traceback.print_exc()
                gem_knowledge = []

        effective_tone = (gem_config.get("tone") if gem_config else requested_tone) or "normal"
        effective_tone = str(effective_tone).strip().lower() or "normal"
        
        if not message:
            return jsonify({"error": "Message is required"}), 400
        
        # Security: Input validation and sanitization (v1.4.3o)
        sanitized_message, is_valid = validate_and_sanitize_input(message)
        if not is_valid:
            return jsonify({"error": "Invalid input detected"}), 400
        message = sanitized_message
        
        # Beta Feature: Structured output formatting
        structured_output = None
        if output_format and request.headers.get('X-Beta-Mode') == 'true':
            structured_output = _prepare_structured_output(output_format)

        # Enhanced Thor 1.1: Use improved max_new_tokens for longer, more comprehensive responses
        # Optimize for voice mode: shorter, more concise responses (v4.3.0)
        if is_voice_mode:
            max_gen_tokens = 256 if think_deeper else 128  # Shorter for voice mode
        else:
            max_gen_tokens = 512 if think_deeper else 256  # Longer for think deeper mode

        # Model Improvement: Check cache first (v1.4.4)
        cached_response = get_cached_response(message, model_name, effective_tone)
        if cached_response:
            print(f"[Cache] Returning cached response for query: {message[:50]}...")
            # Still save to chat history
            chat_data["messages"].append({"role": "user", "content": message})
            chat_data["messages"].append({"role": "assistant", "content": cached_response})
            save_chat(chat_id, chat_data["messages"], chat_data.get("name"))
            return jsonify({
                "response": cached_response,
                "chat_id": chat_id,
                "model": model_label_for_ui,
                "from_cache": True
            })
        
        # Refine large text chunks for better understanding
        if len(message) > 500:
            message = _refine_large_text(message)
            print(f"[Refinement] Processed large text chunk ({len(message)} chars)")
        
        # Get or create chat ID
        if not chat_id:
            chat_id = str(uuid.uuid4())
        
        # Load existing chat or create new
        chat_data = load_chat(chat_id)
        if not chat_data:
            chat_data = {
                "chat_id": chat_id,
                "created_at": datetime.now().isoformat(),
                "messages": []
            }
        
        # Check if it's a greeting first (works without model)
        greetings_handler = get_greetings_handler()
        research_engine = get_research_engine()
        creative_generator = get_creative_generator()
        image_processor = get_image_processor()

        # Initialize enhanced conversation services
        response_variety_manager = get_response_variety_manager()
        emotional_intelligence = get_emotional_intelligence()
        conversation_flow_manager = get_conversation_flow_manager()
        personalization_engine = get_personalization_engine()
        
        # Handle image if provided
        if image_data:
            image_info = image_processor.process_image(image_data, f"image_{chat_id}.png")
            message = f"{message} [Image processed: {image_processor.describe_image(image_info)}]"
            print(f"[Image processed] {image_info.get('description', 'Image processed')}")
        
        # Initialize response variable to None - will be set by one of the branches
        response = None
        query_intent = {}  # ensure availability even if early exits skip intent analysis
        from_result_setter = False
        skip_refinement = False  # set to True for responses we must not clean/alter
        refinement_knowledge_used = []
        
        # Initialize refinement helpers
        normalizer = get_question_normalizer()
        intent_router = get_intent_router()
        knowledge_reranker = get_knowledge_reranker()
        answer_refiner = get_answer_refiner()
        clarifier = get_clarifier()
        conversational_analyzer = get_conversational_analyzer()
        
        # Normalize message BEFORE using it in _get_enhanced_context
        normalized = normalizer.normalize(message, {})
        normalized_message = normalized.get("normalized_query", message)
        
        # Enhanced conversation context with intelligent selection
        # Optimize context for voice mode: use fewer messages for faster processing (v4.3.0)
        if is_voice_mode:
            # For voice mode, use only last 4 messages instead of 8 for faster response
            voice_messages = chat_data.get("messages", [])[-4:] if len(chat_data.get("messages", [])) > 4 else chat_data.get("messages", [])
            conversation_context = _get_enhanced_context(voice_messages, message, normalized_message)
        else:
            conversation_context = _get_enhanced_context(chat_data.get("messages", []), message, normalized_message)
        
        # Load user memory and add context to query
        user_memory = get_user_memory()
        user_context = user_memory.get_relevant_context(message)
        if user_context:
            print(f"[User Memory] Adding context: {user_context}")
        
        # Re-normalize with full conversation_context for better accuracy
        normalized = normalizer.normalize(message, conversation_context)
        normalized_message = normalized.get("normalized_query", message)
        log_debug("Query Normalized", {
            "original": message[:100],
            "normalized": normalized_message[:100],
            "changes": normalized.get("changes", [])
        })
        
        # Initialize common sense handler
        common_sense_handler = get_common_sense_handler()
        
        # Initialize context_query early to avoid UnboundLocalError in common-sense fallback branches
        context_query = normalized_message or message
        
        # Enhanced conversational context analysis
        conversational_analysis = conversational_analyzer.analyze_context(
            message,
            conversation_context,
            normalized_message
        )

        # Initialize conversation flow tracking
        conversation_key = conversation_flow_manager.get_conversation_key(chat_id)
        conversation_flow_manager.update_conversation_context(conversation_key, message)

        # Analyze emotional intelligence
        emotional_context = emotional_intelligence.get_emotional_context(message)

        # Get personalization for this user
        user_key = personalization_engine.get_user_key(chat_id)
        personalization_style = personalization_engine.get_adapted_response_style(user_key)

        # Update personalization with this interaction
        personalization_engine.update_user_profile(user_key, message)

        # Enhanced multi-turn intent detection
        multi_turn_intent = _detect_multi_turn_intent(message, conversation_context)

        # Check for conversation flow interruptions or resumptions
        interruption = conversation_flow_manager.detect_interruption(conversation_key, message)
        resumption = conversation_flow_manager.handle_resumption(conversation_key, message)

        # Combine analyses for better context understanding
        enhanced_context_analysis = {
            **conversational_analysis,
            **multi_turn_intent,
            'enhanced_context': True,
            'interruption': interruption,
            'resumption': resumption
        }

        log_debug("Enhanced Context Analysis", {
            "conversational": conversational_analysis,
            "multi_turn": multi_turn_intent
        })
        
        # Enhanced conversational response handling with multi-turn awareness
        if response is None and (enhanced_context_analysis.get('is_conversational') or enhanced_context_analysis.get('is_follow_up')):
            confidence = max(
                enhanced_context_analysis.get('confidence', 0),
                conversational_analysis.get('confidence', 0)
            )

            if confidence >= 0.6:  # Lower threshold for enhanced analysis
                conversational_response = conversational_analyzer.generate_conversational_response(
                    message,
                    enhanced_context_analysis,
                    conversation_context
                )
                if conversational_response:
                    response = conversational_response
                    skip_refinement = True
                    print(f"[Enhanced Context] Detected conversational response "
                          f"(type: {enhanced_context_analysis.get('conversational_response_type', 'unknown')}, "
                          f"confidence: {confidence:.2f})")
                    if enhanced_context_analysis.get('references_previous'):
                        print(f"[Enhanced Context] References previous conversation context")
                    if enhanced_context_analysis.get('topic_continuation'):
                        print(f"[Enhanced Context] Continuing previous topic")
        
        # Initialize follow-up detection variables early (accessible everywhere)
        message_lower = normalized_message.lower().strip()
        is_tell_me_more = 'tell me more' in message_lower or ('more' in message_lower and len(message.split()) <= 3)
        
        # QUICK PATH: short acknowledgments - avoid pulling random context/knowledge
        short_ack_terms = {"cool", "ok", "okay", "k", "thanks", "thank you", "nice", "great", "awesome", "got it"}
        if response is None and len(message_lower.split()) <= 2 and message_lower in short_ack_terms:
            response = "👍 Got it. What would you like to do next?"
            skip_refinement = True

        # QUICK PATH: simple goodbyes / closings – do not hit web search.
        # Enhanced goodbye detection with pattern matching
        def is_goodbye(msg_lower):
            goodbye_terms = {
                "bye", "goodbye", "bye bye", "see you", "see you later", "cya", 
                "good night", "goodnight", "farewell", "later", "catch you later",
                "talk later", "gotta go", "have to go", "take care", "ttyl", "ttys"
            }
            if msg_lower.strip() in goodbye_terms:
                return True
            for term in goodbye_terms:
                if msg_lower.startswith(term + " ") or msg_lower == term:
                    if not any(q in msg_lower for q in ['who', 'what', 'where', 'when', 'why', 'how']):
                        return True
            goodbye_patterns = [
                r'^(bye|goodbye|see you|later|farewell)',
                r'(bye|goodbye|see you|later|farewell)$',
                r'\b(gotta go|have to go|take care|talk later)\b'
            ]
            for pattern in goodbye_patterns:
                if re.search(pattern, msg_lower):
                    if not msg_lower.strip().endswith('?') and len(msg_lower.split()) <= 6:
                        return True
            return False
        
        if response is None and is_goodbye(message_lower):
            response = "Goodbye! It was nice chatting — come back any time."
            skip_refinement = True

        # QUICK PATH: Enhanced non-question detection
        def is_non_question_statement(msg_lower):
            if len(msg_lower.split()) <= 4 and not msg_lower.strip().endswith('?'):
                if "learn" in msg_lower and not any(q in msg_lower for q in ['what', 'how', 'why', 'when', 'where']):
                    return True
                casual_patterns = [
                    r'^(cool|nice|great|awesome|ok|okay|thanks|thank you|got it|alright|sure)',
                    r'^(that\'s|this is|here\'s|there\'s|it\'s)',
                    r'^(i see|i understand|gotcha|roger)',
                ]
                for pattern in casual_patterns:
                    if re.match(pattern, msg_lower):
                        return True
            if msg_lower.endswith('!') and not msg_lower.strip().endswith('?'):
                exclamation_patterns = [
                    r'learn\s+\w+\s*!$',
                    r'^(wow|nice|great|awesome|cool)\s*!?$',
                ]
                for pattern in exclamation_patterns:
                    if re.search(pattern, msg_lower):
                        return True
            return False
        
        if response is None and is_non_question_statement(message_lower):
            if "learn" in message_lower:
                response = (
                    "I'm always learning from what you ask and the sources I read. "
                    "Ask me something you care about, and I'll do my best to give a useful answer."
                )
            else:
                response = "👍 Got it. What would you like to do next?"
            skip_refinement = True
        elif (
            response is None
            and "learn" in message_lower
            and "?" not in message_lower
            and len(message_lower.split()) <= 4
        ):
            response = (
                "I’m always learning from what you ask and the sources I read. "
                "Ask me something you care about, and I’ll do my best to give a useful answer."
            )
            skip_refinement = True
        
        # QUICK PATH: Web image search when asked to "Create an image of..."
        image_handler = get_image_handler()
        image_subject = image_handler.extract_image_request(message) or _extract_image_request(message)
        if image_subject:
            # If the user explicitly asks for "another/different", force a variant.
            img_variant = None
            if any(w in message_lower for w in ["another", "different", "new one", "new image", "different one"]):
                img_variant = f"{int(time.time() * 1000)}"
            image_url, image_source = image_handler.get_image(image_subject, "960x540", variant=img_variant)
            response = image_handler.format_image_response(
                image_subject,
                image_url,
                is_trainx=(image_source == "trainx")
            )
            skip_refinement = True  # keep markdown intact (no cleaning/rewrites)
            print(f"[Image Search] Served web image for '{image_subject}' -> {image_url} (source={image_source})")
        
        # QUICK PATH: Image refinements (style/angle/background/size/subject tweaks) referencing last image
        if response is None:
            tweak_phrases = [
                "another style", "different style", "another angle", "different angle",
                "different background", "another background", "different size", "change size",
                "bigger", "smaller", "another one", "another image", "change subject", "make it",
                # broadened: allow more natural image tweak phrasing
                "angle", "view", "perspective", "style", "watercolor", "colour", "color", "background"
            ]
            wants_tweak = any(p in message_lower for p in tweak_phrases)
            if wants_tweak:
                # Find last image subject in recent assistant messages
                last_subject = None
                if conversation_context:
                    for msg_ctx in reversed(conversation_context):
                        if msg_ctx.get("role") != "assistant":
                            continue
                        content = msg_ctx.get("content", "") or ""
                        # Prefer the new ImageHandler format: "## Image: Subject"
                        m1 = re.search(r"(?mi)^\s*##\s*Image:\s*(.+?)\s*$", content)
                        if m1:
                            last_subject = m1.group(1).strip()
                            break
                        # Backward-compat: "Here is an image of **Subject**"
                        m2 = re.search(r"Here is an image of\s+\*\*(.+?)\*\*", content, flags=re.IGNORECASE)
                        if m2:
                            last_subject = m2.group(1).strip()
                            break
                # Allow subject override: "make it X" or "change subject to X"
                new_subject = None
                m_subj = re.search(r"(?:make it|change (?:it )?(?:to|into|subject to))\s+(.+)", message, flags=re.IGNORECASE)
                if m_subj:
                    new_subject = m_subj.group(1).strip(" .!?")
                subject_for_image = new_subject or last_subject
                
                # Extract richer tweak modifiers (angle/style/color/background) so requests like
                # "give me a top-down angle", "watercolor style", "make it red" actually work.
                mods: List[str] = []

                # Angle / view / perspective
                angle_phrase = None
                m_angle = re.search(
                    r"\b(?:give me|show me|make it|render it|give it|in|from)\s+(?:a|an|the)?\s*([a-z0-9\s\-\']{0,48}?)\s*(?:angle|view|perspective)\b",
                    message,
                    flags=re.IGNORECASE,
                )
                if m_angle:
                    cand = (m_angle.group(1) or "").strip(" .,!?:;\"'")
                    if cand:
                        angle_phrase = cand
                angle_keywords = [
                    "top down", "top-down", "overhead", "bird's eye", "birds eye",
                    "side view", "front view", "rear view", "back view",
                    "3/4 view", "three quarter", "close up", "close-up", "wide shot",
                    "isometric", "first person", "third person",
                ]
                if not angle_phrase:
                    for kw in angle_keywords:
                        if kw in message_lower:
                            angle_phrase = kw
                            break
                if angle_phrase:
                    mods.append(f"{angle_phrase} angle")
                elif any(k in message_lower for k in ["angle", "view", "perspective"]):
                    mods.append("different angle")

                # Style
                style_phrase = None
                style_keywords = [
                    "watercolor", "water colour", "oil painting", "sketch", "pencil sketch",
                    "anime", "pixel art", "3d", "3d render", "cinematic", "photorealistic",
                    "cartoon", "comic", "minimalist", "line art", "noir",
                ]
                for kw in style_keywords:
                    if kw in message_lower:
                        style_phrase = kw
                        break
                m_style = re.search(r"\b(?:in|as|with)\s+([a-z0-9\s\-]{3,40})\s+style\b", message, flags=re.IGNORECASE)
                if m_style:
                    cand = (m_style.group(1) or "").strip(" .,!?:;\"'")
                    # Avoid overly generic captures like "a" / "the"
                    if cand and len(cand.split()) <= 5:
                        style_phrase = cand
                if style_phrase:
                    mods.append(f"{style_phrase} style")
                elif "style" in message_lower:
                    mods.append("different style")

                # Background
                bg_phrase = None
                m_bg = re.search(r"\bbackground\s*(?:of|with|:)?\s*([a-z0-9\s\-]{3,60})", message, flags=re.IGNORECASE)
                if m_bg:
                    cand = (m_bg.group(1) or "").strip(" .,!?:;\"'")
                    if cand and len(cand.split()) <= 10:
                        bg_phrase = cand
                if bg_phrase:
                    mods.append(f"background {bg_phrase}")
                elif "background" in message_lower:
                    mods.append("different background")

                # Color
                color_phrase = None
                hex_match = re.search(r"#([0-9a-fA-F]{6})\b", message)
                if hex_match:
                    color_phrase = f"#{hex_match.group(1)}"
                else:
                    color_words = [
                        "red", "blue", "green", "yellow", "orange", "purple", "pink",
                        "black", "white", "gray", "grey", "brown", "teal", "cyan",
                    ]
                    m_color = re.search(
                        r"\b(?:in|with|using|make it|give it|color it|colour it)\s+(?:a\s+)?(" + "|".join(color_words) + r")\b",
                        message_lower,
                    )
                    if m_color:
                        color_phrase = m_color.group(1)
                if color_phrase:
                    mods.append(f"color {color_phrase}")

                # Apply modifiers to the subject so the image request actually changes
                if subject_for_image and mods:
                    mods_text = ", ".join(dict.fromkeys(mods))  # stable dedupe
                    if mods_text.lower() not in subject_for_image.lower():
                        subject_for_image = f"{subject_for_image} ({mods_text})"
                
                if subject_for_image:
                    # Size override if provided (e.g., 1024x768)
                    size_match = re.search(r"(\d{2,4})\s*[xX]\s*(\d{2,4})", message)
                    size_str = f"{size_match.group(1)}x{size_match.group(2)}" if size_match else "960x540"
                    # Force a new variant so "another angle/style/background" actually changes output.
                    variant_hint = "-".join([m.replace(" ", "_") for m in mods]) if mods else "variant"
                    variant_key = f"{int(time.time() * 1000)}:{variant_hint}"
                    img_url, img_source = image_handler.get_image(subject_for_image, size_str, variant=variant_key)
                    response = image_handler.format_image_response(
                        subject_for_image,
                        img_url,
                        is_trainx=(img_source == "trainx")
                    )
                    skip_refinement = True
                    print(f"[Image Tweak] Served new image for '{subject_for_image}' size={size_str} (source={img_source})")
                else:
                    response = "I can tweak the image—tell me the subject (and size if you want)!"
                    skip_refinement = True
        
        # QUICK PATH: Commands (check before other processing)
        if response is None:
            message_lower_cmd = message.lower().strip()
            
            # Command: /help
            if message_lower_cmd == '/help' or message_lower_cmd.startswith('/help '):
                response = """# Available Commands

**Core Commands:**
- `/help` - Show this help message
- `/clear` - Clear the current chat
- `/history` - View chat history
- `/settings` - Open settings

**Content Commands:**
- `/office` or `/office suite` - Open the Office Suite
- `/arcade` or `/games` - Open the Game Suite
- `/image <description>` - Generate an image
- `/code <language>` - Switch to code mode (e.g., `/code python`)

**Mode Commands:**
- `/think` - Toggle Think Deeper mode
- `/tone <style>` - Set response tone (friendly, calm, formal, critical, normal)

**Utility Commands:**
- `/remember <information>` - Save information for future reference
- `/forget` - Clear saved preferences
- `/info` - Show information about me

You can also use natural language - just ask me anything!"""
                skip_refinement = True
                print("[Command] /help")
            
            # Command: /clear
            elif message_lower_cmd == '/clear':
                response = "Chat cleared. Starting fresh!"
                skip_refinement = True
                # Clear messages in current chat
                chat_data["messages"] = []
                save_chat(chat_id, chat_data["messages"], chat_data.get("name"))
                print("[Command] /clear")
            
            # Command: /remember
            elif message_lower_cmd.startswith('/remember '):
                memory_text = message[10:].strip()
                if memory_text:
                    user_memory = get_user_memory()
                    user_memory.extract_preferences_from_message(memory_text)
                    user_memory.extract_facts_from_conversation(memory_text, "")
                    user_memory.save()
                    response = f"Got it! I'll remember: **{memory_text}**"
                    skip_refinement = True
                    print(f"[Command] /remember: {memory_text}")
                else:
                    response = "Usage: `/remember <information>` - Tell me what you'd like me to remember."
                    skip_refinement = True
            
            # Command: /forget
            elif message_lower_cmd == '/forget':
                user_memory = get_user_memory()
                user_memory.memory = user_memory._default_memory()
                user_memory.save()
                response = "I've cleared my memory of your preferences and information."
                skip_refinement = True
                print("[Command] /forget")
            
            # Command: /info
            elif message_lower_cmd == '/info':
                user_memory = get_user_memory()
                context_str = user_memory.get_all_context_string()
                if context_str:
                    response = f"## About Me\n\nI'm Atlas, powered by Thor 1.1.\n\n**What I Know About You:**\n{context_str}\n\nHow can I help you today?"
                else:
                    response = "## About Me\n\nI'm Atlas, powered by Thor 1.1. I'm here to help you with questions, tasks, and information. Use `/remember <info>` to help me learn about your preferences!"
                skip_refinement = True
                print("[Command] /info")
            
            # Command: /think
            elif message_lower_cmd == '/think':
                think_deeper = not think_deeper
                response = f"Think Deeper mode is now **{'ON' if think_deeper else 'OFF'}**."
                skip_refinement = True
                print(f"[Command] /think: {think_deeper}")
            
            # Command: /tone
            elif message_lower_cmd.startswith('/tone '):
                tone_arg = message[6:].strip().lower()
                valid_tones = ['normal', 'friendly', 'calm', 'formal', 'critical']
                if tone_arg in valid_tones:
                    effective_tone = tone_arg
                    requested_tone = tone_arg
                    response = f"Response tone set to **{tone_arg}**."
                    skip_refinement = True
                    print(f"[Command] /tone: {tone_arg}")
                else:
                    response = f"Usage: `/tone <style>`\n\nAvailable tones: {', '.join(valid_tones)}"
                    skip_refinement = True
        
        # QUICK PATH: Interactive iframe for office suite
        if response is None:
            # NOTE: previously used r"[^a-z0-9\\s]+" which *removed spaces* (\\s was literal).
            # This prevented command matching and caused fall-through into web search.
            normalized_cmd = re.sub(r"[^a-z0-9\s]+", " ", (normalized_message or "").lower())
            normalized_cmd = re.sub(r"\s+", " ", normalized_cmd).strip()
            tokens = set(normalized_cmd.split())

            wants_office_suite = ("office" in tokens and "suite" in tokens) or normalized_cmd == "load office suite"
            wants_game_suite = (
                ("game" in tokens and "suite" in tokens) or ("games" in tokens and "suite" in tokens)
                or ("arcade" in tokens)
                or ("play" in tokens and ("game" in tokens or "games" in tokens))
                or normalized_cmd in {"load game suite", "lets play games"}
            )

            if wants_office_suite:
                office_url = "https://quantumwebsolutions.netlify.app"
                response = (
                    "## Office Suite\n\n"
                    f"{{{{TRAINX_IFRAME:{office_url}}}}}\n\n"
                    f"[Open in new tab]({office_url})"
                )
                skip_refinement = True  # keep iframe token intact
                print("[Office Suite] Served interactive iframe for office suite request")
            elif wants_game_suite:
                games_url = "https://arcade-indol-six.vercel.app"
                response = (
                    "## Game Suite\n\n"
                    f"{{{{TRAINX_IFRAME:{games_url}}}}}\n\n"
                    f"[Open in new tab]({games_url})"
                )
                skip_refinement = True
                print("[Game Suite] Served interactive iframe for game suite request")
        
        # PRIORITY 1: Check Result Setter first for pre-set authoritative answers
        if response is None:
            qa_answer = check_result_setter(message, model_name)
            from_result_setter = False
            if qa_answer:
                response = qa_answer
                from_result_setter = True
                print(f"[Result Setter] Using pre-set answer from result setter")

        # PRIORITY 2: Check common sense BEFORE other processing (enhanced common sense prioritization)
        if response is None and common_sense_handler is not None:
            # Analyze conversation context for better response selection
            conversation_key = conversation_flow_manager.get_conversation_key(chat_id)
            context_analysis = conversation_flow_manager.analyze_context_for_response(conversation_key, message)

            # Add user key for personalization
            personalization_engine = get_personalization_engine()
            context_analysis['user_key'] = personalization_engine.get_user_key(chat_id)

            # Enhanced common sense check with conversation context awareness
            common_sense_response = common_sense_handler.get_response(message, conversation_context, context_analysis)
            if common_sense_response:
                response = common_sense_response
                print(f"[Common Sense] Responding with context-aware common sense: {response[:50]}...")
                skip_refinement = True
            elif common_sense_handler.should_skip_search(message):
                # Should skip search but no response yet - use fallback
                response = "Thank you! How can I help you?"
                skip_refinement = True
                print(f"[Common Sense] Skipping search for: {message[:50]}...")
            elif common_sense_handler.should_fallback_to_research(message, conversation_context):
                # Common sense is insufficient - check for partial response first
                partial_response = common_sense_handler.get_partial_response(message)
                if partial_response:
                    response = partial_response
                    print(f"[Common Sense] Providing partial response before research: {response[:50]}...")
                    # Allow research to continue and combine with partial response
                    context_query = f"{context_query}\n[Additional context: User received partial guidance, provide specific details to complement this response]"
                else:
                    # No partial response - provide fallback suggestion
                    fallback_suggestion = common_sense_handler.get_fallback_suggestion(message)
                    if fallback_suggestion:
                        print(f"[Common Sense] Insufficient for research query - providing suggestion: {fallback_suggestion}")
                        # Don't set skip_refinement, allowing research to proceed
                        # The fallback suggestion will be incorporated into the research prompt
                        context_query = f"{context_query}\n[Context: {fallback_suggestion}]"
                    else:
                        print(f"[Common Sense] Insufficient for query - proceeding with research: {message[:50]}...")
            else:
                # No common sense response but also shouldn't skip search - allow normal processing
                print(f"[Common Sense] No response available - proceeding with normal processing: {message[:50]}...")

        # Check if it's a math question (simple calculations) - only if no common sense answer found
        if response is None:
            math_result = _evaluate_math(message)
            if math_result is not None:
                response = f"The answer is: **{math_result}**"
                print(f"[Math] Calculated: {message} = {math_result}")
            else:
                # Try solving as a word problem
                word_problem_solution = _solve_simple_math_problem(message)
                if word_problem_solution:
                    response = word_problem_solution
                    print(f"[Math Word Problem] Solved: {message[:50]}...")

        if response is None:
            # Check for identity questions (after common sense but before brain lookup)
            identity_questions = [
                "who are you", "what are you", "who is thor", "what is thor",
                "tell me about yourself", "introduce yourself", "what can you do",
                "what do you do", "who am i talking to", "what's your name"
            ]

            if any(q in message_lower for q in identity_questions):
                response = """I'm **Thor 1.1**, your AI assistant powered by Atlas!

I'm designed to help you with:
- **Coding**: Python, JavaScript, and more
- **Learning**: I continuously learn from our conversations and web research
- **Problem Solving**: Ask me questions and I'll do my best to help
- **Creative Thinking**: Use "Think Deeper" mode for more comprehensive responses

I'm always learning and improving through our conversations. How can I help you today?"""
                print(f"[Identity question] Responding with introduction")
        
        if response is None:
            if greetings_handler is not None and greetings_handler.is_greeting(message):
                response = greetings_handler.get_response(message)
                print(f"[Greeting detected] Responding with: {response}")
                # Skip research and brain lookup for greetings - use direct response
            elif code_mode:
                # Code mode - focus on Python/JavaScript/HTML
                try:
                    code_handler = get_code_handler()
                    response = code_handler.handle_code_query(message, think_deeper, code_language)
                    print(f"[Code Mode] Responding with code information for {code_language}")
                except Exception as e:
                    print(f"Error in code handler: {e}")
                    import traceback
                    traceback.print_exc()
                    # Fallback response
                    response = f"I can help you with **{code_language}** code! Here's a basic example:\n\n```{code_language}\n# Your code here\nprint('Hello, World!')\n```\n\nWhat specific code would you like help with?"
            else:
                # PRIORITY: Check if we need to research this topic (only if not a greeting, math, or common sense)
                # Always prioritize searching Google for unknown topics and relationship queries
                # Add conversation context to the query if available
                contextual_message = normalized_message
                
                # Detect follow-up questions (short questions that likely reference previous context)
                follow_up_patterns = ['what about', 'tell me about', 'explain', 'how about',
                                     'and', 'also', 'tell me more', 'more about', 'more info',
                                     'more information', 'continue', 'go on', 'elaborate', 'expand',
                                     'details', 'more details', 'what else', 'anything else',
                                     'can it', 'can they', 'does it', 'does that', 'does this',
                                     'could it', 'would it', 'should it', 'will it', 'could they',
                                     'would they', 'should they', 'will they', 'why is that', 'why is it']
                
                # "Tell me more" is always a follow-up (already defined above)
                max_follow_up_words = 8
                referential_terms = {'it', 'that', 'this', 'they', 'them', 'those', 'these', 'he', 'she', 'there'}
                has_referential = any(term in message_lower.split() for term in referential_terms)
                pattern_follow_up = (
                    any(pattern in message_lower for pattern in follow_up_patterns)
                    and len(message.split()) <= max_follow_up_words
                )
                # Require referential cues for generic patterns to avoid hijacking new questions
                if pattern_follow_up and not has_referential and not message_lower.startswith(('and', 'also')):
                    pattern_follow_up = False
                is_follow_up = pattern_follow_up or is_tell_me_more
                
                previous_topic = None
                recent_user_messages = []
                
                if conversation_context and len(conversation_context) > 0:
                    # Get recent conversation for context
                    recent_messages = conversation_context[-6:]  # Last 6 messages
                    recent_user_messages = [msg.get('content', '') for msg in recent_messages if msg.get('role') == 'user']
                    recent_assistant_messages = [msg.get('content', '') for msg in recent_messages if msg.get('role') == 'assistant']
                    
                    # Extract topic keywords from previous conversation
                    if recent_user_messages:
                        # Get the last substantial user message (more than 3 words)
                        for msg in reversed(recent_user_messages):
                            if len(msg.split()) > 3:
                                previous_topic = msg
                                break
                    
                    # Detect pronoun-based follow-ups referencing previous topic
                    if previous_topic and not is_follow_up and _is_pronoun_follow_up(message):
                        is_follow_up = True
                        print(f"[Context] Pronoun follow-up detected, linking to previous topic: {previous_topic[:60]}...")
                    
                    # For follow-up questions, combine with previous topic
                    if is_follow_up and previous_topic:
                        # For "tell me more", use the previous topic directly
                        if is_tell_me_more:
                            contextual_message = previous_topic
                            print(f"[Context] 'Tell me more' detected, using previous topic: {contextual_message}")
                        else:
                            # Extract keywords from previous topic to maintain context
                            prev_words = previous_topic.lower().split()
                            # Find programming languages, technologies mentioned
                            lang_keywords = ['javascript', 'js', 'python', 'java', 'c++', 'typescript', 'html', 'css', 'react', 'node', 'kotlin', 'swift', 'go', 'rust', 'ruby', 'php', 'c#', 'scala']
                            mentioned_lang = None
                            for word in prev_words:
                                if word in lang_keywords or any(lang in word for lang in lang_keywords):
                                    mentioned_lang = word
                                    break
                            
                            # Build contextual message: combine previous topic keywords with current question
                            if mentioned_lang:
                                contextual_message = f"{mentioned_lang} {message}"
                                print(f"[Context] Follow-up detected: {message} -> {contextual_message}")
                            else:
                                # Use full previous topic for context
                                contextual_message = f"{previous_topic} {message}"
                                print(f"[Context] Follow-up detected: {message} -> {contextual_message}")
                
                # Detect if this is a question vs command/statement
                is_question = (
                    message.strip().endswith('?') or
                    any(word in message_lower for word in ['what', 'how', 'why', 'when', 'where', 'who', 'which', 'can', 'could', 'should', 'would', 'does', 'do', 'did', 'is', 'are', 'was', 'were', 'will'])
                )
                
                # Do not blend unrelated context for fresh questions; keep the user's prompt primary
                if not is_follow_up:
                    contextual_message = normalized_message
                
                context_query = (contextual_message or message).strip()
                if not context_query:
                    context_query = message
                
                # Add user memory context to query if available
                user_memory = get_user_memory()
                memory_context = user_memory.get_relevant_context(context_query)
                if memory_context:
                    # Inject user context into the knowledge synthesis process
                    context_query = f"{context_query} [User context: {memory_context}]"
                    print(f"[User Memory] Added context to query: {memory_context}")
                
                # ENHANCED: Check if this is actually a searchable question before proceeding
                # Skip search for simple statements, commands, or acknowledgments
                # Also respect conversational context analysis
                # CRITICAL: Skip search for solvable problems (math, logic, reasoning)
                is_solvable_problem = _is_solvable_problem(message)
                requires_search = True and not is_solvable_problem
                
                # If conversational analyzer determined this doesn't need search, respect that
                if conversational_analysis.get('requires_search') == False:
                    requires_search = False
                    print(f"[Conversational Context] Skipping search - conversational statement detected")
                
                if requires_search and not is_question and len(message_lower.split()) <= 4:
                    # Short non-questions are likely commands/statements, not search queries
                    simple_patterns = [
                        r'^(that\'s|this is|here\'s|there\'s|it\'s|nice|good|great|ok|okay|yes|no|sure)',
                        r'^(thanks|thank you|got it|cool|awesome|alright)',
                        r'^(learn|think|remember|forget)',
                    ]
                    for pattern in simple_patterns:
                        if re.match(pattern, message_lower):
                            requires_search = False
                            break
                
                # Use query intent analyzer for intelligent query understanding
                intent_analyzer = get_query_intent_analyzer()
                query_intent = (intent_analyzer.analyze(context_query) or {}) if intent_analyzer else {}
                if is_follow_up and query_intent is not None:
                    query_intent['is_follow_up'] = True
                query_intent = intent_router.route(query_intent, normalized_message, conversation_context)
                
                # Detect recipe/cooking queries early - these should always search web
                recipe_patterns = ['how to make', 'recipe for', 'how do you make', 'how do i make', 
                                  'recipe', 'how to cook', 'how to prepare', 'ingredients for']
                is_recipe_query = any(pattern in context_query.lower() for pattern in recipe_patterns)
                
                # Track if we've done research for this query (initialize early so it's accessible everywhere)
                research_done = False
                research_knowledge = []
                
                # ENHANCED: Only proceed with search/knowledge retrieval if this is actually a searchable query
                if not requires_search:
                    # This is a command/statement, not a search query - skip search entirely
                    print(f"[Intent] Non-searchable command/statement detected: {message}")
                    knowledge = []
                    needs_research = False
                    
                    # If conversational but no response generated yet, generate one
                    if response is None and conversational_analysis.get('is_conversational'):
                        conversational_response = conversational_analyzer.generate_conversational_response(
                            message,
                            conversational_analysis,
                            conversation_context
                        )
                        if conversational_response:
                            response = conversational_response
                            skip_refinement = True
                            print(f"[Conversational Context] Generated response for conversational statement")
                # Check if query should force web search
                elif query_intent.get('should_search_web'):
                    print(f"[Query Intent] {query_intent.get('intent', 'unknown').upper()} query detected, forcing web search: {message}")
                    knowledge = list(gem_knowledge) if gem_knowledge else []  # Keep gem sources, force web search otherwise
                else:
                    if is_recipe_query:
                        # Recipe queries should always search web, don't check brain first
                        print(f"[Recipe Query] Detected recipe query: {message}")
                        knowledge = list(gem_knowledge) if gem_knowledge else []  # Keep gem sources, force web search otherwise
                    else:
                        log_debug("Retrieving Knowledge from Brain", {
                            "query": contextual_message[:100],
                            "description": f"Searching internal knowledge base for: \"{contextual_message}\". Checking stored information from previous conversations."
                        })
                        knowledge = brain_connector.get_relevant_knowledge(contextual_message)
                        if gem_knowledge:
                            knowledge = list(gem_knowledge) + (knowledge or [])
                        if knowledge:
                            log_debug("Knowledge Retrieved from Brain", {
                                "items_count": len(knowledge),
                                "description": f"Found {len(knowledge)} relevant knowledge item{'s' if len(knowledge) != 1 else ''} in internal knowledge base",
                                "items": [{"title": k.get("title", "")[:60], "score": k.get("score", 0)} for k in knowledge[:5]]
                            })
                        else:
                            log_debug("No Knowledge Found in Brain", {
                                "description": "No relevant information found in internal knowledge base. Will search the web for accurate information."
                            })
                
                # Detect relationship/comparison questions - always research these
                is_relationship_query = any(phrase in context_query.lower() for phrase in [
                    'relationship between', 'relationship of', 'connection between',
                    'difference between', 'compare', 'comparison between', 'versus', 'vs',
                    'similarities between', 'how does', 'how do', 'how are', 'how is',
                    'what is the relationship', 'what is the connection'
                ])
                
                # CORE PRINCIPLE: Model first, web search as fallback
                # The model has deep internal knowledge and reasoning capabilities.
                # Web search should ONLY be used for:
                # 1. Explicit "think deeper" mode (user wants comprehensive research)
                # 2. Specific domains that require current data (recipes, current events)
                # 3. When model explicitly fails or gives low-quality response
                
                # For "tell me more" follow-ups, don't research if we already have knowledge from previous query
                if not requires_search:
                    # Commands/statements don't need research
                    needs_research = False
                    print(f"[Intent] Skipping research for non-searchable query (solvable problem): {message[:50]}")
                elif is_tell_me_more and knowledge and len(knowledge) > 0:
                    needs_research = False  # Use existing knowledge for follow-up
                    print(f"[Context] 'Tell me more' detected with existing knowledge, skipping research")
                else:
                    # CORE PRINCIPLE: Model first, web search as fallback
                    # Try model for ALL queries first. Only pre-emptively research for:
                    # 1. Explicit "think deeper" mode
                    # 2. Recipes (require current data)
                    # 3. Relationship/comparison queries (benefit from multiple sources)
                    # 4. Time-sensitive queries (current events, news)
                    
                    # Check for time-sensitive queries first
                    time_sensitive_indicators = [
                        'latest', 'recent', 'current', 'today', 'yesterday', 'this week',
                        'this month', 'this year', '2024', '2025', '2026',
                        'news', 'breaking', 'update', 'now', 'currently'
                    ]
                    is_time_sensitive = any(indicator in context_query.lower() for indicator in time_sensitive_indicators)
                    
                    # Only research for specific cases that genuinely need web search
                    needs_research = think_deeper or is_recipe_query or is_relationship_query or is_time_sensitive
                    
                    # Log the decision
                    if needs_research:
                        reasons = []
                        if think_deeper:
                            reasons.append("think_deeper")
                        if is_recipe_query:
                            reasons.append("recipe")
                        if is_relationship_query:
                            reasons.append("relationship")
                        if is_time_sensitive:
                            reasons.append("time_sensitive")
                        print(f"[Decision] Will research (reasons: {', '.join(reasons)}): {context_query[:50]}")
                    else:
                        print(f"[Decision] Model will handle (no pre-emptive research): {context_query[:50]}")
                    
                # #region agent log
                try:
                    import sys
                    sys.path.insert(0, str(ATLAS_ROOT / ".cursor"))
                    from debug_agent import get_tracker
                    tracker = get_tracker()
                    if tracker:
                        reasons = []
                        if needs_research:
                            if think_deeper:
                                reasons.append("think_deeper_mode")
                            if is_recipe_query:
                                reasons.append("recipe_query")
                            if is_relationship_query:
                                reasons.append("relationship_query")
                            if is_time_sensitive:
                                reasons.append("time_sensitive")
                        else:
                            reasons.append("model_first_approach")
                        tracker.log_research_decision(needs_research, reasons)
                except Exception:
                    pass
                # #endregion agent log
                
                if needs_research:
                    # Use contextual message for research (includes follow-up context)
                    search_query = context_query
                    search_type = "relationship query" if is_relationship_query else ("recipe query" if is_recipe_query else "topic not in brain")
                    print(f"[Research] {search_type.upper()}, PRIORITIZING Google search: {search_query}")
                    research_done = True
                    try:
                        log_debug("Starting Web Search", {
                            "query": search_query[:100],
                            "description": f"Searching multiple engines (Google, Bing, DuckDuckGo, Wikipedia) for: \"{search_query}\""
                        })
                        research_knowledge = research_engine.search_and_learn(search_query)
                        if research_knowledge:
                            print(f"[Research] Learned {len(research_knowledge)} items from Google")
                            
                            # Group results by source for better display
                            results_by_source = {}
                            for r in research_knowledge:
                                source = r.get("source", "unknown")
                                if source not in results_by_source:
                                    results_by_source[source] = []
                                results_by_source[source].append({
                                    "title": r.get("title", "")[:80],
                                    "url": r.get("url", "")[:100] if r.get("url") else None
                                })
                            
                            # Prepare detailed results with source information
                            detailed_results = []
                            for r in research_knowledge[:10]:
                                detailed_results.append({
                                    "title": r.get("title", ""),
                                    "url": r.get("url", ""),
                                    "source": r.get("source", "unknown"),
                                    "content": r.get("content", "")[:200] if r.get("content") else None
                                })
                            
                            log_debug("Web Search Complete", {
                                "results_count": len(research_knowledge),
                                "description": f"Found {len(research_knowledge)} search results from multiple sources",
                                "sources": {k: len(v) for k, v in results_by_source.items()},
                                "results": detailed_results  # Include full results with source info
                            })
                            # PRIORITIZE gem sources: prepend gem_knowledge so it's used first
                            if gem_knowledge:
                                knowledge = list(gem_knowledge) + research_knowledge
                            else:
                                knowledge = research_knowledge
                        else:
                            print(f"[Research] No knowledge retrieved, will use existing brain knowledge if available")
                            # Still preserve gem_knowledge even if research failed
                            if gem_knowledge and not knowledge:
                                knowledge = list(gem_knowledge)
                    except Exception as e:
                        print(f"[Research] Error during research: {e}")
                        import traceback
                        traceback.print_exc()
                
                # Get model for non-greeting messages (only if response not already set)
                if response is None:
                    # Check for direct AI model first
                    if model_name == 'ai-direct' and 'ai-direct' in model_instances and model_instances['ai-direct']['type'] == 'direct':
                        model = model_instances['ai-direct']  # Use direct AI model
                        print(f"[DEBUG] Using direct AI model for inference")
                    else:
                        # #region agent log
                        import json
                        try:
                            with open('/Users/arulhania/Coding/atlas-ai/.cursor/debug.log', 'a') as f:
                                f.write(json.dumps({"id":f"log_{int(__import__('time').time())}_{__import__('secrets').token_hex(3)}","timestamp":int(__import__('time').time()*1000),"location":"app.py:3158","message":"Model check in chat endpoint","data":{"model_name":model_name,"in_instances":model_name in model_instances,"is_loaded":model_instances.get(model_name) is not None},"sessionId":"debug-session","runId":"verify-fixes","hypothesisId":"A"})+"\n")
                        except: pass
                        # #endregion agent log
                        # Check if model is already loaded first (don't try to load during request)
                        if model_name in model_instances and model_instances[model_name] is not None:
                            model = model_instances[model_name]
                            print(f"[Model] Using already-loaded model: {model_name}")
                            # #region agent log
                            try:
                                with open('/Users/arulhania/Coding/atlas-ai/.cursor/debug.log', 'a') as f:
                                    f.write(json.dumps({"id":f"log_{int(__import__('time').time())}_{__import__('secrets').token_hex(3)}","timestamp":int(__import__('time').time()*1000),"location":"app.py:3161","message":"Model found in instances","data":{"model_name":model_name},"sessionId":"debug-session","runId":"verify-fixes","hypothesisId":"A"})+"\n")
                            except: pass
                            # #endregion agent log
                        else:
                            # Model not loaded - check loading status
                            progress_key = 'thor-1.1' if model_name == 'qwen3-thor' else model_name
                            loading_status = model_loading_progress.get(progress_key, {'status': 'not_started', 'progress': 0, 'message': 'Not started'})
                            # #region agent log
                            try:
                                with open('/Users/arulhania/Coding/atlas-ai/.cursor/debug.log', 'a') as f:
                                    f.write(json.dumps({"id":f"log_{int(__import__('time').time())}_{__import__('secrets').token_hex(3)}","timestamp":int(__import__('time').time()*1000),"location":"app.py:3165","message":"Model not loaded, checking status","data":{"model_name":model_name,"progress_key":progress_key,"status":loading_status.get('status'),"progress":loading_status.get('progress')},"sessionId":"debug-session","runId":"verify-fixes","hypothesisId":"A"})+"\n")
                            except: pass
                            # #endregion agent log
                            if loading_status['status'] == 'loading':
                                # Model is currently loading - return loading status
                                return jsonify({
                                    "error": f"Model {model_name} is currently loading. Please wait.",
                                    "model_status": "loading",
                                    "loading_progress": loading_status['progress'],
                                    "loading_message": loading_status['message'],
                                    "suggestion": f"Model is {loading_status['progress']}% loaded. Please try again in a moment."
                                }), 503
                            elif loading_status['status'] == 'failed':
                                # Model failed to load - return error with details, always include progress
                                progress = loading_status.get('progress', 0)
                                error_response = handle_model_loading_error(
                                    model_name=model_name,
                                    error=Exception(loading_status.get('message', 'Model loading failed')),
                                    loading_progress=loading_status,
                                    context={'status': 'failed', 'source': 'server_startup'}
                                )
                                # Ensure progress is always included
                                error_response['loading_progress'] = progress
                                error_response['progress_percentage'] = f"{progress:.1f}%"
                                error_response['error_message'] = loading_status.get('message', 'Model loading failed')
                                return jsonify(error_response), 503
                            else:
                                # Model not started loading - return error, always include progress
                                progress = loading_status.get('progress', 0)
                                error_response = handle_model_loading_error(
                                    model_name=model_name,
                                    error=Exception("Model has not been loaded"),
                                    loading_progress=loading_status,
                                    context={'status': 'not_started', 'source': 'model_check'}
                                )
                                # Ensure progress is always included
                                error_response['loading_progress'] = progress
                                error_response['progress_percentage'] = f"{progress:.1f}%"
                                return jsonify(error_response), 503
                    # #region agent log
                    try:
                        import sys
                        sys.path.insert(0, str(ATLAS_ROOT / ".cursor"))
                        from debug_agent import get_tracker
                        tracker = get_tracker()
                        if tracker:
                            tracker.log_model_check(model is not None, model_name)
                    except Exception:
                        pass
                    # #endregion agent log
                else:
                    model = None  # Skip model if we already have a response
                
                # #region agent log
                try:
                    import sys
                    sys.path.insert(0, str(ATLAS_ROOT / ".cursor"))
                    from debug_agent import agent_log
                    agent_log(
                        "model_and_response_check",
                        {
                            "model_is_none": model is None,
                            "response_is_none": response is None,
                            "will_use_brain_knowledge": model is None and response is None,
                            "will_use_model": model is not None
                        },
                        hypothesis_id="FLOW_CHECK",
                        run_id="live",
                        location="chatbot/app.py:2833"
                    )
                except Exception:
                    pass
                # #endregion agent log
                
                # PRIORITY: Try model first, only use research if model fails
                # This ensures we exhaust internal knowledge before web search
                model_response_quality = None  # Track if model generated good response
                
                if model is None and response is None:
                    # No model available - provide a simple but helpful response
                    ai_available = 'ai-direct' in model_instances and model_instances['ai-direct']['type'] == 'direct'
                    response = f"I understand you said: '{message}'. AI models available: {ai_available}. Model instances: {list(model_instances.keys())}"

                elif model is None and response is not None:
                    # We already have a response, continue
                    pass
                # Model-based response generation
                else:
                    # Generate response using model with conversation context
                    # #region agent log
                    try:
                        import sys
                        sys.path.insert(0, str(ATLAS_ROOT / ".cursor"))
                        from debug_agent import agent_log
                        agent_log(
                            "model_generation_started",
                            {
                                "model_loaded": model is not None,
                                "message": message[:100]
                            },
                            hypothesis_id="MODEL_GEN",
                            run_id="live",
                            location="chatbot/app.py:3213"
                        )
                    except Exception:
                        pass
                    # #endregion agent log

                    try:
                        # Enhanced Thor 1.1/1.2: Build better contextual input with improved prompt engineering
                        contextual_input = message
                        if conversation_context and len(conversation_context) > 0:
                            # Include last 4-6 exchanges for better context (enhanced from 2-3)
                            recent_context = []
                            for msg in conversation_context[-8:]:  # Increased from 6 to 8
                                role = msg.get('role', '')
                                content = msg.get('content', '')
                                if role == 'user':
                                    recent_context.append(f"User: {content}")
                                elif role == 'assistant':
                                    recent_context.append(f"Assistant: {content}")
                            
                            if recent_context:
                                # Enhanced: Better context formatting for improved understanding
                                contextual_input = "\n".join(recent_context[-6:]) + f"\nUser: {message}\nAssistant:"
                                print(f"[Model] Using enhanced conversation context ({len(recent_context)} previous messages)")
                        
                        # Enhanced Thor 1.1/1.2: Add knowledge context to prompt for better synthesis
                        if 'knowledge' in locals() and knowledge and len(knowledge) > 0:
                            # Add relevant knowledge as context (first 2-3 items)
                            knowledge_context = "\n\nRelevant Information:\n"
                            for idx, k in enumerate(knowledge[:3]):
                                title = k.get('title', 'Source')
                                content_snippet = (k.get('content', '') or '')[:300].strip()
                                if content_snippet:
                                    knowledge_context += f"{idx+1}. {title}: {content_snippet}...\n"
                            contextual_input = contextual_input + knowledge_context
                            print(f"[Model] Enhanced: Added {len(knowledge[:3])} knowledge items to context")
                        
                        # Apply Gem instructions as a lightweight "system prompt" prefix.
                        tone_line = _tone_profile(effective_tone)

                        # Beta: Add structured output instruction to tone line
                        if structured_output:
                            tone_line += f" {structured_output['instruction']}"

                        # Add language instruction if response_language is specified and not English
                        language_instruction = ""
                        if response_language and response_language != 'en-US':
                            language_map = {
                                'hi-IN': 'Hindi', 'ta-IN': 'Tamil', 'te-IN': 'Telugu',
                                'es-ES': 'Spanish', 'fr-FR': 'French', 'de-DE': 'German',
                                'zh-CN': 'Mandarin Chinese', 'ja-JP': 'Japanese',
                                'ko-KR': 'Korean', 'it-IT': 'Italian', 'pt-BR': 'Portuguese'
                            }
                            lang_name = language_map.get(response_language, response_language)
                            language_instruction = f" CRITICAL: You MUST respond entirely in {lang_name}. The user is speaking in {lang_name}, so respond in {lang_name} only."
                            print(f"[Language] Adding language instruction: Respond in {lang_name}")
                        
                        if gem_config and (gem_config.get("instructions") or "").strip():
                            gem_name = (gem_config.get("name") or "Gem").strip()
                            gem_instr = (gem_config.get("instructions") or "").strip()
                            gem_desc = (gem_config.get("description") or "").strip()
                            
                            # Build gem sources context
                            gem_sources_context = ""
                            if gem_knowledge and len(gem_knowledge) > 0:
                                gem_titles = [k.get("title", "Source") for k in gem_knowledge[:3]]
                                gem_sources_context = f"\n\nGem Sources Available ({len(gem_knowledge)} items): {', '.join(gem_titles)}"
                                for idx, k in enumerate(gem_knowledge[:2]):
                                    content_preview = (k.get("content", "") or "")[:200].strip()
                                    if content_preview:
                                        gem_sources_context += f"\n\nSource {idx+1} ({k.get('title', 'Unknown')}): {content_preview}..."
                            
                            desc_line = f" Description: {gem_desc}" if gem_desc else ""
                            prefix = f"System: {tone_line}{language_instruction} You are {gem_name}.{desc_line} {gem_instr}{gem_sources_context}".strip()
                            contextual_input = prefix + "\n\n" + contextual_input
                        else:
                            contextual_input = f"System: {tone_line}{language_instruction}\n\n" + contextual_input

                        # Check if model is a direct AI model dict
                        if isinstance(model, dict) and model.get('type') == 'direct':
                            ai_model = model['model']
                            ai_tokenizer = model['tokenizer']
                            print(f"[AI] Generating response for: {message[:50]}...")
                            inputs = ai_tokenizer(message, return_tensors="pt").to(ai_model.device)
                            with torch.no_grad():
                                outputs = ai_model.generate(
                                    **inputs, max_new_tokens=100, temperature=0.7, do_sample=True,
                                    pad_token_id=ai_tokenizer.eos_token_id, no_repeat_ngram_size=3, top_p=0.9
                                )
                            full_response = ai_tokenizer.decode(outputs[0], skip_special_tokens=True)
                            response = full_response.replace(message, "").strip()
                            if response.startswith(("AI:", "Assistant:", "Response:")):
                                response = response.split(":", 1)[1].strip()
                            response = response_cleaner.clean_response(response, message)

                        elif hasattr(model, 'predict'):
                            # Use Thor model inference
                            result = model.predict(contextual_input, task=task, max_new_tokens=max_gen_tokens)
                            if result and 'generated_text' in result:
                                response = result['generated_text']
                                # Apply structured output formatting
                                if structured_output and response:
                                    response = structured_output['wrapper'](response)
                                
                                # Validate response
                                response_cleaner = get_response_cleaner()
                                if response and response_cleaner.is_corrupted(response):
                                    print(f"[Model] Detected corrupted response, rejecting")
                                    response = None
                                elif response:
                                    response = response_cleaner.clean_response(response, message)
                                    print(f"[Thor] Generated response using {model_name}")
                        
                        if not response:
                            print(f"[Model] Failed to generate a valid response using {model_name}")

                    except Exception as e:
                        print(f"[Model] Error generating response: {e}")
                        import traceback
                        traceback.print_exc()
                        response = None

                # Fallback to research/brain if no model response
                if response is None:
                    try:
                        # If we haven't done research yet, do it now as fallback
                        if not research_done:
                            print(f"[Fallback] Model failed, starting fallback research...")
                            research_knowledge = research_engine.search_and_learn(context_query)
                            research_done = True
                            if gem_knowledge:
                                knowledge = list(gem_knowledge) + research_knowledge
                            else:
                                knowledge = research_knowledge
                    except Exception as e:
                        print(f"[Fallback Research] Error: {e}")
                
                # Dummy block to consume old code
                if False:
                    pass
                    
                    try:
                        # Enhanced Thor 1.1: Build better contextual input with improved prompt engineering
                        contextual_input = message
                        if conversation_context and len(conversation_context) > 0:
                            # Include last 4-6 exchanges for better context (enhanced from 2-3)
                            recent_context = []
                            for msg in conversation_context[-8:]:  # Increased from 6 to 8
                                role = msg.get('role', '')
                                content = msg.get('content', '')
                                if role == 'user':
                                    recent_context.append(f"User: {content}")
                                elif role == 'assistant':
                                    recent_context.append(f"Assistant: {content}")
                            
                            if recent_context:
                                # Enhanced: Better context formatting for improved understanding
                                contextual_input = "\n".join(recent_context[-6:]) + f"\nUser: {message}\nAssistant:"
                                print(f"[Model] Using enhanced conversation context ({len(recent_context)} previous messages)")
                        
                        # Enhanced Thor 1.1: Add knowledge context to prompt for better synthesis
                        if 'knowledge' in locals() and knowledge and len(knowledge) > 0:
                            # Add relevant knowledge as context (first 2-3 items)
                            knowledge_context = "\n\nRelevant Information:\n"
                            for idx, k in enumerate(knowledge[:3]):
                                title = k.get('title', 'Source')
                                content_snippet = (k.get('content', '') or '')[:300].strip()
                                if content_snippet:
                                    knowledge_context += f"{idx+1}. {title}: {content_snippet}...\n"
                            contextual_input = contextual_input + knowledge_context
                            print(f"[Model] Enhanced: Added {len(knowledge[:3])} knowledge items to context")
                        
                        # Apply Gem instructions as a lightweight "system prompt" prefix.
                        tone_line = _tone_profile(effective_tone)

                        # Beta: Add structured output instruction to tone line
                        if structured_output:
                            tone_line += f" {structured_output['instruction']}"

                        # Add language instruction if response_language is specified and not English
                        language_instruction = ""
                        if response_language and response_language != 'en-US':
                            language_map = {
                                'hi-IN': 'Hindi',
                                'ta-IN': 'Tamil',
                                'te-IN': 'Telugu',
                                'es-ES': 'Spanish',
                                'fr-FR': 'French',
                                'de-DE': 'German',
                                'zh-CN': 'Mandarin Chinese',
                                'ja-JP': 'Japanese',
                                'ko-KR': 'Korean',
                                'it-IT': 'Italian',
                                'pt-BR': 'Portuguese'
                            }
                            lang_name = language_map.get(response_language, response_language)
                            language_instruction = f" CRITICAL: You MUST respond entirely in {lang_name}. The user is speaking in {lang_name}, so respond in {lang_name} only. Do not use English unless the user explicitly asks a question in English."
                            print(f"[Language] Adding language instruction: Respond in {lang_name}")
                        
                        if gem_config and (gem_config.get("instructions") or "").strip():
                            gem_name = (gem_config.get("name") or "Gem").strip()
                            gem_instr = (gem_config.get("instructions") or "").strip()
                            gem_desc = (gem_config.get("description") or "").strip()
                            
                            # Build gem sources context - include actual content snippets, not just titles
                            gem_sources_context = ""
                            if gem_knowledge and len(gem_knowledge) > 0:
                                gem_titles = [k.get("title", "Source") for k in gem_knowledge[:3]]
                                gem_sources_context = f"\n\nGem Sources Available ({len(gem_knowledge)} items): {', '.join(gem_titles)}"
                                # Add key content snippets from first 2 sources for context
                                for idx, k in enumerate(gem_knowledge[:2]):
                                    content_preview = (k.get("content", "") or "")[:200].strip()
                                    if content_preview:
                                        gem_sources_context += f"\n\nSource {idx+1} ({k.get('title', 'Unknown')}): {content_preview}..."
                            
                            # Include description in the system prompt if available
                            desc_line = f" Description: {gem_desc}" if gem_desc else ""
                            prefix = f"System: {tone_line}{language_instruction} You are {gem_name}.{desc_line} {gem_instr}{gem_sources_context}".strip()
                            contextual_input = prefix + "\n\n" + contextual_input
                            print(f"[Gem] Using gem '{gem_name}' with {len(gem_knowledge or [])} source(s) in context")
                        else:
                            # Global tone (no gem): still guide style strongly
                            contextual_input = f"System: {tone_line}{language_instruction}\n\n" + contextual_input

                        log_debug("Generating Response", {
                            "description": "Synthesizing information from web search and knowledge base to generate a comprehensive answer. Using enhanced Thor 1.1 model with multi-step generation for natural, helpful responses.",
                            "context_length": len(contextual_input),
                            "has_knowledge": len(knowledge) > 0 if 'knowledge' in locals() else False,
                            "knowledge_items": len(knowledge) if 'knowledge' in locals() and knowledge else 0,
                            "enhanced_generation": True
                        })
                        
                        # Beta Feature: Multi-model comparison
                        if compare_models and len(compare_models) > 1 and request.headers.get('X-Beta-Mode') == 'true':
                            return _handle_multi_model_comparison(
                                compare_models, contextual_input, task, think_deeper, is_voice_mode,
                                effective_tone, language_instruction, response_language, data
                            )

                        # Beta Feature: Structured output formatting
                        structured_output = None
                        if output_format and request.headers.get('X-Beta-Mode') == 'true':
                            structured_output = _prepare_structured_output(output_format)

                        # Enhanced Thor 1.1: Use improved max_new_tokens for longer, more comprehensive responses
                        # Optimize for voice mode: shorter, more concise responses (v4.3.0)
                        if is_voice_mode:
                            max_gen_tokens = 256 if think_deeper else 128  # Shorter for voice mode
                        else:
                            max_gen_tokens = 512 if think_deeper else 256  # Longer for think deeper mode

                        # Check if model loaded successfully
                        if model is None:
                            print(f"[Model Error] Model {model_name} failed to load")
                            return jsonify({
                                "error": f"Model {model_name} is not available. Please check model files and try again.",
                                "model_status": "unavailable"
                            }), 503

                        # Pass max_new_tokens for text generation, max_length for input sequence
                        if task == 'text_generation':
                            result = model.predict(contextual_input, task=task, max_new_tokens=max_gen_tokens)
                        else:
                            result = model.predict(contextual_input, task=task)
                        
                        # Get response cleaner for validation
                        response_cleaner = get_response_cleaner()
                        
                        # Extract response based on task
                        if task == 'text_generation' and 'generated_text' in result:
                            response = result['generated_text']

                            # Beta: Apply structured output formatting
                            if structured_output and response:
                                response = structured_output['wrapper'](response)

                            # CRITICAL: Mark this as a model-generated response to prevent overwriting
                            model_response_generated = True
                            # #region agent log
                            try:
                                import sys
                                sys.path.insert(0, str(ATLAS_ROOT / ".cursor"))
                                from debug_agent import agent_log
                                agent_log(
                                    "model_generated_text",
                                    {
                                        "response_length": len(response) if response else 0,
                                        "response_preview": response[:100] if response else None,
                                        "task": task
                                    },
                                    hypothesis_id="H1",
                                    run_id="math-debug",
                                    location="chatbot/app.py:3358"
                                )
                            except Exception:
                                pass
                            # #endregion agent log
                            
                            # Validate response - use response_cleaner's corruption detection
                            if response:
                                # Use comprehensive corruption detection
                                if response_cleaner.is_corrupted(response):
                                    print(f"[Model] Detected corrupted response, rejecting: '{response[:50]}...'")
                                    response = None
                                # TRUST the model's response - don't reject based on length or punctuation
                                # The model knows what it's doing. Only reject if truly corrupted.
                                # Skip the overly-strict validation that rejects perfectly good responses
                                else:
                                    # Additional validation for very short or repetitive responses
                                    words = response.lower().split()
                                    if len(words) > 3:
                                        # Check for excessive repetition (same word 3+ times in a row)
                                        max_repeat = 1
                                        for i in range(len(words) - 2):
                                            if words[i] == words[i+1] == words[i+2]:
                                                max_repeat = max(max_repeat, words[i:].count(words[i]))
                                        if max_repeat > 3:
                                            print(f"[Model] Detected corrupted response (repeated words), rejecting")
                                            response = None
                                        # Skip nonsensical pattern check - it's too aggressive and rejects valid responses
                                        # elif len(words) >= 4 and any(words[i] == words[i+2] and words[i+1] == words[i+3] 
                                        #        for i in range(len(words) - 3)):
                                        #     print(f"[Model] Detected nonsensical pattern, rejecting")
                                        #     response = None
                                
                                # If model generated something valid, clean it before using
                                if response and len(response.strip()) > 10:
                                    # #region agent log
                                    try:
                                        import sys
                                        sys.path.insert(0, str(ATLAS_ROOT / ".cursor"))
                                        from debug_agent import agent_log
                                        agent_log(
                                            "before_cleaning",
                                            {
                                                "response_length": len(response) if response else 0,
                                                "response_preview": response[:200] if response else None
                                            },
                                            hypothesis_id="H3",
                                            run_id="math-debug",
                                            location="chatbot/app.py:3435"
                                        )
                                    except Exception:
                                        pass
                                    # #endregion agent log
                                    
                                    # Apply cleaning to fix minor grammar issues
                                    response = response_cleaner.clean_response(response, message)
                                    # #region agent log
                                    try:
                                        import sys
                                        sys.path.insert(0, str(ATLAS_ROOT / ".cursor"))
                                        from debug_agent import agent_log
                                        agent_log(
                                            "response_after_cleaning",
                                            {
                                                "response_length": len(response) if response else 0,
                                                "response_preview": response[:100] if response else None
                                            },
                                            hypothesis_id="H2",
                                            run_id="math-debug",
                                            location="chatbot/app.py:3405"
                                        )
                                    except Exception:
                                        pass
                                    # #endregion agent log
                                    
                                    # Optimize response length for voice mode (v4.3.0)
                                    if is_voice_mode and len(response) > 500:
                                        # For voice mode, prefer shorter responses - truncate intelligently
                                        # Try to end at sentence boundary
                                        truncated = response[:500]
                                        last_period = truncated.rfind('.')
                                        last_exclamation = truncated.rfind('!')
                                        last_question = truncated.rfind('?')
                                        last_sentence_end = max(last_period, last_exclamation, last_question)
                                        if last_sentence_end > 300:  # Only truncate if we have enough content
                                            response = response[:last_sentence_end + 1]
                                        else:
                                            response = truncated + '...'
                                        print(f"[Voice Mode] Truncated response from {len(response_cleaner.clean_response(response, message))} to {len(response)} chars")
                                    
                                    if response and len(response.strip()) > 10:
                                        # Check if response is too vague or unhelpful (fallback trigger)
                                        response_lower = response.lower()
                                        vague_phrases = [
                                            "i understand your message",
                                            "i'm continuously learning",
                                            "let me think about that",
                                            "that's an interesting question",
                                            "i'm having trouble",
                                            "could you tell me more",
                                            "what would you like to know",
                                            "how can i help"
                                        ]
                                        is_vague = any(phrase in response_lower for phrase in vague_phrases)
                                        is_too_short = len(response.strip()) < 30  # Very short responses
                                        
                                        # DISABLED: Skip the Thor 1.0 fallback for vague responses
                                        # The vague phrase detection is too aggressive and rejects good responses
                                        # from the model. Let the model's response stand on its own merit.
                                        if False and model_name == 'thor-1.1' and (is_vague or is_too_short) and not skip_refinement:
                                            print(f"[Model] Thor 1.1 response too vague/short, trying Thor 1.0 fallback...")
                                            try:
                                                # Get Thor 1.0 model
                                                thor_1_0_model = get_model('thor-1.0', force_reload=False)
                                                if thor_1_0_model:
                                                    # Try with Thor 1.0
                                                    fallback_result = thor_1_0_model.predict(contextual_input, task=task)
                                                    if fallback_result and 'generated_text' in fallback_result:
                                                        fallback_response = fallback_result['generated_text']
                                                        if fallback_response and len(fallback_response.strip()) > 10:
                                                            # Validate fallback response
                                                            if not response_cleaner.is_corrupted(fallback_response):
                                                                fallback_response = response_cleaner.clean_response(fallback_response, message)
                                                                if fallback_response and len(fallback_response.strip()) > 10:
                                                                    # Check if fallback is better (not vague)
                                                                    fallback_lower = fallback_response.lower()
                                                                    fallback_is_vague = any(phrase in fallback_lower for phrase in vague_phrases)
                                                                    if not fallback_is_vague or len(fallback_response.strip()) > len(response.strip()):
                                                                        print(f"[Model] Using Thor 1.0 fallback (better response: {len(fallback_response)} chars)")
                                                                        response = fallback_response
                                                                        model_label_for_ui = "Thor 1.0 (Fallback)"
                                                                    else:
                                                                        print(f"[Model] Thor 1.0 fallback also vague, keeping Thor 1.1 response")
                                                                else:
                                                                    print(f"[Model] Thor 1.0 fallback too short after cleaning")
                                                            else:
                                                                print(f"[Model] Thor 1.0 fallback corrupted, keeping Thor 1.1 response")
                                                        else:
                                                            print(f"[Model] Thor 1.0 fallback too short")
                                                    else:
                                                        print(f"[Model] Thor 1.0 model not available for fallback")
                                                else:
                                                    print(f"[Model] Could not load Thor 1.0 for fallback")
                                            except Exception as fallback_error:
                                                print(f"[Model] Error trying Thor 1.0 fallback: {fallback_error}")
                                                # Keep original Thor 1.1 response
                                        
                                        print(f"[Model] Generated response using {model_name} ({len(response)} chars)")
                                        log_debug("Response Generated", {
                                            "length": len(response),
                                            "description": f"Generated response ({len(response)} characters). Combining information from multiple sources to provide an accurate answer."
                                        })
                                    else:
                                        response = None
                                else:
                                    response = None
                                    
                            # If Thor 1.1 completely failed (no response), try Thor 1.0 fallback
                            if not response and model_name == 'thor-1.1' and not skip_refinement:
                                print(f"[Model] Thor 1.1 failed to generate response, trying Thor 1.0 fallback...")
                                try:
                                    thor_1_0_model = get_model('thor-1.0', force_reload=False)
                                    if thor_1_0_model:
                                        fallback_result = thor_1_0_model.predict(contextual_input, task=task)
                                        if fallback_result and 'generated_text' in fallback_result:
                                            fallback_response = fallback_result['generated_text']
                                            # Apply same strict validation as Thor 1.1
                                            if fallback_response and len(fallback_response.strip()) >= 15:
                                                if not response_cleaner.is_corrupted(fallback_response):
                                                    # Check for incomplete sentences
                                                    if any(fallback_response.strip().endswith(p) for p in ['.', '!', '?', ':', '"', "'"]):
                                                        fallback_response = response_cleaner.clean_response(fallback_response, message)
                                                        if fallback_response and len(fallback_response.strip()) >= 15:
                                                            print(f"[Model] Using Thor 1.0 fallback (better response: {len(fallback_response)} chars)")
                                                            response = fallback_response
                                                            model_label_for_ui = "Thor 1.0 (Fallback)"
                                                    else:
                                                        print(f"[Model] Thor 1.0 response incomplete, rejecting: '{fallback_response[:50]}...'")
                                                else:
                                                    print(f"[Model] Thor 1.0 response corrupted, rejecting")
                                            else:
                                                print(f"[Model] Thor 1.0 response too short ({len(fallback_response.strip()) if fallback_response else 0} chars), rejecting")
                                except Exception as fallback_error:
                                    print(f"[Model] Error trying Thor 1.0 fallback: {fallback_error}")
                        elif task == 'sentiment_analysis':
                            sentiment_labels = ['Negative', 'Neutral', 'Positive']
                            pred = result.get('prediction', 1)
                            sentiment = sentiment_labels[pred] if pred < len(sentiment_labels) else 'Unknown'
                            response = f"I detect this as: **{sentiment}** sentiment."
                            # Add helpful follow-up
                            if sentiment == 'Positive':
                                response += " I'm glad you're feeling positive!"
                            elif sentiment == 'Negative':
                                response += " Is there something I can help you with?"
                        elif task == 'text_classification':
                            response = f"Classification result: {result.get('prediction', 'N/A')}"
                        elif 'answer' in result:
                            response = result['answer']
                        else:
                            # If model doesn't have good response, try Thor 1.0 fallback if using Thor 1.1
                            if model_name == 'thor-1.1' and not skip_refinement:
                                print(f"[Model] Thor 1.1 returned no valid response, trying Thor 1.0 fallback...")
                                try:
                                    thor_1_0_model = get_model('thor-1.0', force_reload=False)
                                    if thor_1_0_model:
                                        fallback_result = thor_1_0_model.predict(contextual_input, task=task)
                                        if fallback_result and 'generated_text' in fallback_result:
                                            fallback_response = fallback_result['generated_text']
                                            # Apply same strict validation
                                            if fallback_response and len(fallback_response.strip()) >= 15:
                                                if not response_cleaner.is_corrupted(fallback_response):
                                                    if any(fallback_response.strip().endswith(p) for p in ['.', '!', '?', ':', '"', "'"]):
                                                        fallback_response = response_cleaner.clean_response(fallback_response, message)
                                                        if fallback_response and len(fallback_response.strip()) >= 15:
                                                            print(f"[Model] Using Thor 1.0 fallback (Thor 1.1 returned no response)")
                                                            response = fallback_response
                                                            model_label_for_ui = "Thor 1.0 (Fallback)"
                                except Exception as fallback_error:
                                    print(f"[Model] Error trying Thor 1.0 fallback: {fallback_error}")
                            
                            if not response:
                                response = "I understand your message. Let me think about that..."
                        
                        # Enhance response with brain knowledge only if model's response is weak
                        try:
                            if not response or len(response.strip()) < 20:
                                # Model response is too short or corrupted, use knowledge directly
                                print("[Response] Model response invalid, using knowledge")
                                
                                # If we haven't researched yet, do it now as fallback
                                if not research_done and requires_search:
                                    print(f"[Fallback] Model failed, triggering web search as fallback for: {context_query[:50]}")
                                    try:
                                        research_knowledge = research_engine.search_and_learn(context_query)
                                        if research_knowledge and len(research_knowledge) > 0:
                                            research_done = True
                                            print(f"[Fallback Research] Found {len(research_knowledge)} results")
                                            # Add to knowledge for synthesis
                                            if gem_knowledge:
                                                knowledge = list(gem_knowledge) + research_knowledge
                                            else:
                                                knowledge = research_knowledge
                                    except Exception as e:
                                        print(f"[Fallback Research] Error: {e}")
                                
                                # First, check if we already researched and have results
                                if research_done and research_knowledge and len(research_knowledge) > 0:
                                    print(f"[Response] Using research results: {len(research_knowledge)} items")
                                    # Synthesize research results instead of using verbatim
                                    intent_analyzer = get_query_intent_analyzer()
                                    query_intent = (intent_analyzer.analyze(context_query) or {}) if intent_analyzer else {}
                                    synthesized = synthesize_knowledge(context_query, research_knowledge, query_intent)
                                    if synthesized:
                                        response = synthesized
                                    else:
                                        # Fallback to first result if synthesis fails
                                        content = research_knowledge[0].get('content', '')
                                        cleaned_content = clean_promotional_text(content)
                                        if cleaned_content:
                                            if query_intent.get('intent') == 'definition':
                                                entity = query_intent.get('entity', message)
                                                response = f"**{entity.title()}** is {cleaned_content[:400].lstrip('is ').lstrip('Is ')}"
                                            else:
                                                response = cleaned_content[:400]
                                        else:
                                            response = content[:400] if content else None
                                
                                # If no response yet, try brain knowledge
                                if not response:
                                    knowledge = brain_connector.get_relevant_knowledge(context_query)
                                    if gem_knowledge:
                                        knowledge = list(gem_knowledge) + (knowledge or [])
                                    if knowledge:
                                        # Use semantic scorer to get most relevant
                                        semantic_scorer = get_semantic_scorer()
                                        intent_analyzer = get_query_intent_analyzer()
                                        query_intent = (intent_analyzer.analyze(context_query) or {}) if intent_analyzer else {}
                                        scored = semantic_scorer.filter_knowledge_by_relevance(
                                            context_query, knowledge, query_intent, min_score=0.3
                                        )
                                        if scored:
                                            top_knowledge = scored[0][1]
                                            content = top_knowledge.get('content', '')
                                            cleaned_content = clean_promotional_text(content)
                                            response = cleaned_content[:500]
                                            if not response.startswith(('A', 'An', 'The', 'I', 'This', 'That')):
                                                # Add natural intro
                                                entity = query_intent.get('entity', message.split()[-1] if message.split() else 'this')
                                                if query_intent.get('intent') == 'definition':
                                                    response = f"**{entity.title()}** {response}"
                                                else:
                                                    response = f"Here's what I know: {response}"
                                
                                # Final fallback - use research results even if they didn't pass semantic scoring
                                if not response and research_done and research_knowledge and len(research_knowledge) > 0:
                                    print(f"[Response] Using research results as fallback: {len(research_knowledge)} items")
                                    intent_analyzer = get_query_intent_analyzer()
                                    query_intent = (intent_analyzer.analyze(context_query) or {}) if intent_analyzer else {}
                                    synthesized = synthesize_knowledge(context_query, research_knowledge, query_intent)
                                    if synthesized:
                                        response = synthesized
                                    else:
                                        # Fallback to first result if synthesis fails
                                        content = research_knowledge[0].get('content', '')
                                        cleaned_content = clean_promotional_text(content)
                                        if cleaned_content:
                                            if query_intent.get('intent') == 'definition':
                                                entity = query_intent.get('entity', message)
                                                response = f"**{entity.title()}** is {cleaned_content[:400].lstrip('is ').lstrip('Is ')}"
                                            else:
                                                response = cleaned_content[:400]
                                        else:
                                            response = content[:400] if content else None
                                
                                # Last resort fallback message - ONLY if response is genuinely None/empty
                                # Do NOT replace valid model responses with fallback messages
                                if not response or (isinstance(response, str) and len(response.strip()) == 0):
                                    if research_done:
                                        response = f"I've searched for information about '{message}', but I'm having trouble finding a clear answer. Could you tell me more specifically what you'd like to know about this topic?"
                                    else:
                                        response = f"I understand you're asking about '{message}'. Let me search for more information about that."
                            elif think_deeper:
                                # Think deeper mode with model response - enhance comprehensively
                                print("[Think Deeper] Enhancing model response with deep analysis...")
                                # PRESERVE the original response - don't let it be overwritten
                                original_response = response
                                
                                # First, validate the response is not corrupted
                                if response:
                                    words = response.lower().split()
                                    # Check for excessive repetition or garbled text
                                    is_corrupted = False
                                    if len(words) > 3:
                                        # Check for repeated words
                                        for i in range(len(words) - 2):
                                            if words[i] == words[i+1] == words[i+2]:
                                                is_corrupted = True
                                                break
                                        # Check for nonsensical patterns like "what is what is"
                                        if not is_corrupted:
                                            for i in range(len(words) - 3):
                                                if words[i] == words[i+2] and words[i+1] == words[i+3]:
                                                    is_corrupted = True
                                                    break
                                    
                                    if is_corrupted:
                                        print("[Think Deeper] Detected corrupted response, using comprehensive knowledge instead")
                                        response = None
                                
                                # Perform comprehensive enhancement
                                if response and len(response.strip()) > 20:
                                    # Step 1: Research for additional context
                                    print("[Think Deeper] Researching for additional context...")
                                    research_knowledge = research_engine.search_and_learn(context_query)
                                    
                                    # Step 2: Get related knowledge from brain
                                    log_debug("Retrieving Knowledge from Brain", {"query": context_query[:100]})
                                    knowledge = brain_connector.get_relevant_knowledge(context_query)
                                    log_debug("Knowledge Retrieved", {
                                        "items_count": len(knowledge) if knowledge else 0,
                                        "top_items": [{"title": k.get("title", "")[:50]} for k in (knowledge or [])[:3]]
                                    })
                                    if gem_knowledge:
                                        knowledge = list(gem_knowledge) + (knowledge or [])
                                    
                                    # Step 3: Combine all knowledge sources
                                    all_knowledge = []
                                    if research_knowledge:
                                        all_knowledge.extend(research_knowledge)
                                    if knowledge:
                                        all_knowledge.extend(knowledge)
                                    
                                    # Step 4: Filter and score
                                    semantic_scorer = get_semantic_scorer()
                                    intent_analyzer = get_query_intent_analyzer()
                                    query_intent = (intent_analyzer.analyze(context_query) or {}) if intent_analyzer else {}
                                    
                                    if all_knowledge:
                                        # Filter out low-quality content
                                        filtered = [k for k in all_knowledge 
                                                   if 'Response pattern' not in k.get('content', '')
                                                   and k.get('source', '') != 'greetings_handler'
                                                   and len(k.get('content', '').strip()) > 20]
                                        
                                        if filtered:
                                            scored = semantic_scorer.filter_knowledge_by_relevance(
                                                context_query, filtered, query_intent, min_score=0.35
                                            )
                                            
                                            if scored:
                                                # Build enhanced response
                                                enhanced_parts = [f"**Initial Response:**\n\n{response}"]
                                                
                                                # Add related insights
                                                top_related = [item for _, item in scored[:3]]
                                                if top_related:
                                                    enhanced_parts.append("\n\n**Additional Insights:**")
                                                    for i, k in enumerate(top_related, 1):
                                                        content = k.get('content', '').strip()
                                                        if content and len(content) > 30:
                                                            if len(content) > 250:
                                                                content = content[:247] + "..."
                                                            enhanced_parts.append(f"\n\n{i}. {content}")
                                                
                                                # Add synthesis if multiple sources
                                                unique_sources = set(k.get('source', 'unknown') for k in top_related)
                                                if len(unique_sources) > 1:
                                                    enhanced_parts.append("\n\n**Synthesis:** These insights come from multiple sources, providing a more comprehensive perspective.")
                                                
                                                response = "".join(enhanced_parts)
                                            else:
                                                # No highly relevant connections, but enhance with prefix
                                                response = f"**Deep Analysis:**\n\n{response}"
                                        else:
                                            response = f"**Deep Analysis:**\n\n{response}"
                                    else:
                                        # No additional knowledge, but enhance with prefix
                                        response = f"**Deep Analysis:**\n\n{response}"
                                else:
                                    # Response is corrupted or missing, use comprehensive knowledge-based response
                                    print("[Think Deeper] Response invalid, using comprehensive knowledge-based fallback")
                                    
                                    # Research first
                                    research_knowledge = research_engine.search_and_learn(context_query)
                                    
                                    # Get brain knowledge
                                    knowledge = brain_connector.get_relevant_knowledge(context_query)
                                    if gem_knowledge:
                                        knowledge = list(gem_knowledge) + (knowledge or [])
                                    
                                    # Combine
                                    all_knowledge = []
                                    if research_knowledge:
                                        all_knowledge.extend(research_knowledge)
                                    if knowledge:
                                        all_knowledge.extend(knowledge)
                                    
                                    semantic_scorer = get_semantic_scorer()
                                    intent_analyzer = get_query_intent_analyzer()
                                    query_intent = (intent_analyzer.analyze(context_query) or {}) if intent_analyzer else {}
                                    
                                    if all_knowledge:
                                        filtered = [k for k in all_knowledge 
                                                   if 'Response pattern' not in k.get('content', '')
                                                   and k.get('source', '') != 'greetings_handler'
                                                   and len(k.get('content', '').strip()) > 20]
                                        
                                        if filtered:
                                            scored = semantic_scorer.filter_knowledge_by_relevance(
                                                context_query, filtered, query_intent, min_score=0.3
                                            )
                                            
                                            if scored:
                                                top_knowledge = scored[0][1]
                                                content = top_knowledge.get('content', '').strip()
                                                if content:
                                                    response = f"**Deep Analysis:**\n\n{content[:600]}"
                                                    
                                                    # Add additional perspectives
                                                    if len(scored) > 1:
                                                        response += "\n\n**Additional Perspectives:**"
                                                        for i, (_, k) in enumerate(scored[1:3], 1):
                                                            additional = k.get('content', '').strip()[:250]
                                                            if additional:
                                                                response += f"\n\n{i}. {additional}"
                                                else:
                                                    response = f"**Deep Analysis:**\n\nI'm thinking deeply about '{message}'. I'm continuously learning and improving."
                                            else:
                                                response = f"**Deep Analysis:**\n\nI'm thinking deeply about '{message}'. I'm continuously learning and improving."
                                        else:
                                            response = f"**Deep Analysis:**\n\nI'm thinking deeply about '{message}'. I'm continuously learning and improving."
                                    else:
                                        response = f"**Deep Analysis:**\n\nI'm thinking deeply about '{message}'. I'm continuously learning and improving."
                            else:
                                # Light enhancement - keep model's primary response but add awareness
                                # Add natural conversation flow
                                if conversation_context and len(conversation_context) > 2:
                                    # Check if we're continuing a topic
                                    recent_topics = [msg.get('content', '')[:50] for msg in conversation_context[-4:] if msg.get('role') == 'user']
                                    if len(recent_topics) > 1:
                                        # Add subtle acknowledgment of context
                                        if not response.startswith(('Sure', 'Yes', 'Absolutely', 'I', 'Let me', 'That')):
                                            response = "Here's what I think: " + response
                                
                                enhanced = brain_connector.enhance_response(message, response)
                                # Only use enhancement if it adds value
                                if enhanced and len(enhanced) > len(response) * 1.5:
                                    response = enhanced
                        except Exception as e:
                            print(f"Error enhancing response: {e}")
                    except Exception as e:
                        print(f"Error generating model response: {e}")
                        import traceback
                        traceback.print_exc()
                        # Fallback to brain knowledge - this is expected if model has issues
                        try:
                            knowledge = brain_connector.get_relevant_knowledge(context_query)
                            if gem_knowledge:
                                knowledge = list(gem_knowledge) + (knowledge or [])
                            # Filter out greeting patterns
                            filtered_knowledge = [k for k in knowledge 
                                                 if 'Response pattern for greeting' not in k.get('content', '')
                                                 and 'Use appropriate greeting' not in k.get('content', '')
                                                 and k.get('source', '') != 'greetings_handler'
                                                 and not k.get('content', '').startswith('Response pattern')]
                            
                            if filtered_knowledge:
                                refinement_knowledge_used = filtered_knowledge
                                content = filtered_knowledge[0].get('content', '')
                                cleaned_content = clean_promotional_text(content)
                                response = cleaned_content[:500]
                            else:
                                # Use research engine as fallback
                                try:
                                    research_knowledge = research_engine.search_and_learn(context_query)
                                    if research_knowledge:
                                        refinement_knowledge_used = research_knowledge
                                        content = research_knowledge[0].get('content', '')
                                        cleaned_content = clean_promotional_text(content)
                                        response = cleaned_content[:500]
                                    else:
                                        response = f"I understand your message about '{message}'. I'm continuously learning. How can I help you?"
                                except:
                                    response = f"I understand your message about '{message}'. I'm learning continuously. How can I help?"
                        except Exception as fallback_error:
                            print(f"Error in fallback response: {fallback_error}")
                            response = "I understand your message. I'm continuously learning and improving. How can I assist you?"
        
        # Final refinement pass on the answer (skip for result-setter to avoid annotations)
        if not from_result_setter and not skip_refinement:
            # #region agent log
            try:
                import sys
                sys.path.insert(0, str(ATLAS_ROOT / ".cursor"))
                from debug_agent import agent_log
                agent_log(
                    "before_refinement",
                    {
                        "response_length": len(response) if response else 0,
                        "response_preview": response[:100] if response else None,
                        "model_label": model_label_for_ui
                    },
                    hypothesis_id="H4",
                    run_id="math-debug",
                    location="chatbot/app.py:3905"
                )
            except Exception:
                pass
            # #endregion agent log
            
            response = answer_refiner.refine(response, refinement_knowledge_used, query_intent or {}, model_label_for_ui)
            
            # #region agent log
            try:
                import sys
                sys.path.insert(0, str(ATLAS_ROOT / ".cursor"))
                from debug_agent import agent_log
                agent_log(
                    "after_refinement",
                    {
                        "response_length": len(response) if response else 0,
                        "response_preview": response[:100] if response else None
                    },
                    hypothesis_id="H4",
                    run_id="math-debug",
                    location="chatbot/app.py:3905"
                )
            except Exception:
                pass
            # #endregion agent log

        # Final accuracy check (conservative): avoid ungrounded numeric claims when we have sources.
        if not skip_refinement:
            try:
                knowledge_for_check = (refinement_knowledge_used or []) + (gem_knowledge or [])
                response = verify_response_accuracy(response, knowledge_for_check, query=message)
            except Exception as e:
                print(f"[Accuracy Check] Skipped due to error: {e}")
        
        # Add user message and assistant response to chat
        chat_data["messages"].append({
            "role": "user",
            "content": message,
            "timestamp": datetime.now().isoformat()
        })
        chat_data["messages"].append({
            "role": "assistant",
            "content": response,
            "timestamp": datetime.now().isoformat()
        })
        
        # Extract user preferences and facts from conversation
        try:
            user_memory = get_user_memory()
            user_memory.extract_preferences_from_message(message, response)
            user_memory.extract_facts_from_conversation(message, response)
            user_memory.add_conversation_topic(message[:100])  # Add topic from message
            user_memory.save()
        except Exception as e:
            print(f"[User Memory] Error extracting memory: {e}")
        
        # Generate chat name if this is the first exchange
        chat_name = None
        if len(chat_data["messages"]) == 2:  # Just added user + assistant
            chat_name = generate_chat_name(message, response)
        
        # Model Improvement: Cache response for future use (v1.4.4)
        if response and len(response.strip()) > 20 and not skip_refinement:
            cache_response(message, model_name, effective_tone, response)
        
        # Save chat
        save_chat(chat_id, chat_data["messages"], chat_name)
        
        # Also save to conversations directory for backup/archive
        try:
            conversation_file = os.path.join(CONVERSATIONS_DIR, f"{chat_id}.json")
            with open(conversation_file, 'w') as f:
                json.dump(chat_data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save to conversations directory: {e}")
        
        # Record history entry for new chats
        if len(chat_data["messages"]) == 2:  # Just created first exchange
            try:
                history_entry = {
                    "type": "chat",
                    "title": chat_name or message[:50],
                    "description": message[:100],
                    "chat_id": chat_id,
                    "metadata": {"message_count": 2}
                }
                save_history_entry(history_entry)
            except Exception as e:
                print(f"Error recording history: {e}")
        
        # Add conversation to auto-trainer
        try:
            auto_trainer = get_auto_trainer()
            if auto_trainer is not None:
                # Ensure chat_data has the right structure for auto-trainer
                conversation_data = {
                    "chat_id": chat_data.get("chat_id"),
                    "created_at": chat_data.get("created_at"),
                    "messages": chat_data.get("messages", [])
                }
                auto_trainer.add_conversation(conversation_data)
            
            # Record conversation in tracker
            tracker = get_tracker()
            if tracker and hasattr(tracker, 'record_conversation'):
                tracker.record_conversation()
                print(f"[Learning] Conversation recorded: {len(chat_data.get('messages', []))} messages")
        except Exception as e:
            print(f"Error adding conversation to auto-trainer: {e}")
            import traceback
            traceback.print_exc()
        
        # Ensure response is always a string and not empty
        if not isinstance(response, str):
            response = str(response) if response else "I understand your message. How can I help you?"
        
        if not response or len(response.strip()) == 0:
            response = "I understand your message. How can I help you?"
        
        # FINAL FORMATTER: light-touch grammar/format cleanup (no forced bullets)
        if not skip_refinement:
            try:
                log_debug("Formatting Response", {
                    "description": "Formatting the response with proper markdown, code blocks, and structure for better readability."
                })
                final_formatter = get_final_response_formatter()
                response = final_formatter.format(
                    response,
                    user_message=message,
                    hints={
                        "task": task,
                        "tone": effective_tone if 'effective_tone' in locals() else (data.get('tone') or 'normal'),
                    },
                )
                log_debug("Response Formatted", {
                    "description": "Response formatting complete. The answer is ready to be sent."
                })
            except Exception as e:
                print(f"[Final Formatter] Error: {e}")
                log_debug("Formatting Error", {"error": str(e)}, "warning")

        # FINAL CLEANUP: Apply response cleaner to catch any remaining issues
        if not skip_refinement:
            try:
                final_cleaner = get_response_cleaner()
                # Check if response is corrupted
                if final_cleaner.is_corrupted(response):
                    print(f"[Final Check] Response corrupted, using fallback")
                    response = f"I understand you're asking about '{message}'. Let me research that for you."
                else:
                    # Apply final grammar and formatting fixes
                    response = final_cleaner.fix_grammar_issues(response)
                    response = final_cleaner.fix_incomplete_sentences(response)
            except Exception as e:
                print(f"[Final Check] Error in final cleanup: {e}")

        # Accuracy guardrail: strip ungrounded numeric claims when we used retrieved knowledge.
        if not skip_refinement:
            try:
                if refinement_knowledge_used:
                    response = verify_response_accuracy(response, refinement_knowledge_used, query=message)
            except Exception as e:
                print(f"[Accuracy Check] Error: {e}")
        
        # INTEGRATE ENHANCED CONVERSATION SERVICES
        try:
            # Apply emotional intelligence and tone matching
            if emotional_context.get('needs_empathy') or emotional_context.get('emotion_confidence', 0) > 0.6:
                empathy_response = emotional_intelligence.generate_empathy_response(message, emotional_context.get('primary_emotion'))
                if empathy_response:
                    response = empathy_response
                    print(f"[Emotional Intelligence] Applied empathy response for {emotional_context.get('primary_emotion')}")

            # Check for celebration responses
            celebration = emotional_intelligence.generate_celebration_response(message)
            if celebration:
                response = celebration
                print("[Emotional Intelligence] Applied celebration response")

            # Apply personalization adaptation
            if personalization_style and response:
                adapted_response = personalization_engine.adapt_response(response, user_key)
                if adapted_response != response:
                    response = adapted_response
                    print("[Personalization] Adapted response based on user preferences")

            # Apply response variety management
            conversation_variety_key = response_variety_manager.get_conversation_key(chat_id)
            variety_score = response_variety_manager.get_variety_score(conversation_variety_key, response)

            if variety_score < 0.7:  # Response might be too repetitive
                alternative = response_variety_manager.suggest_alternative(conversation_variety_key, 'general', response)
                if alternative:
                    print(f"[Response Variety] Suggested alternative: {alternative}")
                # Still use the original response but record it for future variety

            # Record this response for variety tracking
            response_variety_manager.record_response(conversation_variety_key, response)

            # Update conversation flow with the final response
            conversation_flow_manager.update_conversation_context(conversation_key, message, response)

        except Exception as e:
            print(f"[Conversation Services] Error in enhanced integration: {e}")
            # Continue with original response if integration fails

        # Add emoji support (only when relevant or requested)
        try:
            response = _add_emoji_support(response, message)
        except Exception as e:
            print(f"[Emoji] Error adding emoji support: {e}")

        # Model Improvement: Cache response for future use (v1.4.4)
        if response and len(response.strip()) > 20 and not skip_refinement:
            cache_response(message, model_name, effective_tone, response)
        
        # Track user engagement for personalization
        if response:
            personalization_engine = get_personalization_engine()
            user_key = personalization_engine.get_user_key(chat_id)
            # We'll track engagement on the next interaction, so store this for later comparison
            personalization_engine.update_user_profile(user_key, message, response)

        response_data = {
            "response": response,
            "chat_id": chat_id,
            "task": task,
            "model_used": model_label_for_ui  # Include which model was actually used
        }
        
        # Add debug log if debug mode is enabled
        if debug_mode and debug_log:
            response_data["debug_log"] = debug_log
        
        # Add search results if available (for debugging)
        if debug_mode:
            # Extract search results from knowledge items if they exist
            search_results = []
            if 'knowledge' in locals() and knowledge:
                for k in knowledge:
                    if k.get("source") in ["google", "bing", "duckduckgo", "wikipedia", "brave"]:
                        search_results.append({
                            "title": k.get("title", ""),
                            "url": k.get("url", ""),
                            "source": k.get("source", "unknown")
                        })
            if search_results:
                response_data["search_results"] = search_results
        
        return jsonify(response_data), 200
            
    except (ValueError, TypeError, KeyError) as e:
        # Handle specific validation and data errors
        error_type = type(e).__name__
        error_msg = str(e) if str(e) else f"{error_type} occurred"
        print(f"❌ Validation error in chat endpoint ({error_type}): {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "error": f"Invalid request: {error_msg}",
            "error_type": error_type
        }), 400
    except (FileNotFoundError, PermissionError, OSError) as e:
        # Handle file system errors
        error_type = type(e).__name__
        error_msg = str(e) if str(e) else f"{error_type} occurred"
        print(f"❌ File system error in chat endpoint ({error_type}): {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "error": "File system error occurred",
            "error_type": error_type
        }), 500
    except (ImportError, ModuleNotFoundError) as e:
        # Handle import errors
        error_type = type(e).__name__
        error_msg = str(e) if str(e) else f"{error_type} occurred"
        print(f"❌ Import error in chat endpoint ({error_type}): {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "error": "Module import error occurred",
            "error_type": error_type
        }), 500
    except (requests.exceptions.RequestException, requests.exceptions.Timeout) as e:
        # Handle network/API errors
        error_type = type(e).__name__
        error_msg = str(e) if str(e) else f"{error_type} occurred"
        print(f"❌ Network error in chat endpoint ({error_type}): {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "error": "Network error occurred while processing request",
            "error_type": error_type
        }), 503
    except MemoryError as e:
        # Handle memory errors
        error_type = type(e).__name__
        print(f"❌ Memory error in chat endpoint: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "error": "Insufficient memory to process request",
            "error_type": error_type
        }), 507
    except Exception as e:
        # Catch-all for unexpected errors (should be minimized)
        error_type = type(e).__name__
        error_msg = str(e) if str(e) else "Internal server error"
        print(f"❌ Unexpected error in chat endpoint ({error_type}): {e}")
        import traceback
        traceback.print_exc()
        
        # If error message is too short or unclear, provide more context
        if len(error_msg) < 5 or error_msg.isdigit():
            error_msg = f"{error_type}: {error_msg}" if error_msg else f"{error_type} occurred"
        
        print(f"   Error type: {error_type}")
        print(f"   Error message: {error_msg}")
        print(f"   Returning error response: {error_msg}")
        
        # Return user-friendly error message
        user_message = f"I encountered an error: {error_msg}. Please try again."
        if "KeyError" in error_type:
            user_message = "I encountered an error processing your request. Please try rephrasing your question."
        elif "IndexError" in error_type:
            user_message = "I encountered an error with the model. Please try again."
        
        return jsonify({"error": error_msg, "response": user_message}), 500


@app.route('/api/chats', methods=['GET'])
def get_chats():
    """Get list of all chats."""
    try:
        chats = list_chats()
        return jsonify({"chats": chats})
    except Exception as e:
        print(f"Error listing chats: {e}")
        return jsonify({"error": "Error loading chats"}), 500


@app.route('/api/chats/<chat_id>', methods=['GET'])
def get_chat(chat_id):
    """Get a specific chat."""
    try:
        chat_data = load_chat(chat_id)
        if chat_data:
            return jsonify(chat_data)
        else:
            return jsonify({"error": "Chat not found"}), 404
    except Exception as e:
        print(f"Error loading chat: {e}")
        return jsonify({"error": "Error loading chat"}), 500


@app.route('/api/chats/<chat_id>', methods=['DELETE'])
def delete_chat(chat_id):
    """Delete a chat."""
    try:
        chat_file = os.path.join(CHATS_DIR, f"{chat_id}.json")
        if os.path.exists(chat_file):
            os.remove(chat_file)
            return jsonify({"success": True})
        else:
            return jsonify({"error": "Chat not found"}), 404
    except Exception as e:
        print(f"Error deleting chat: {e}")
        return jsonify({"error": "Error deleting chat"}), 500


@app.route('/api/chats', methods=['DELETE'])
def delete_all_chats():
    """Delete all chats."""
    try:
        # Get all .json files in CHATS_DIR
        for filename in os.listdir(CHATS_DIR):
            if filename.endswith(".json"):
                file_path = os.path.join(CHATS_DIR, filename)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                except Exception as e:
                    print(f"Error deleting file {file_path}: {e}")
        
        # Also clear chats from session/cache if needed
        # (Based on app logic, chats are mostly file-based)
        
        return jsonify({"success": True})
    except Exception as e:
        print(f"Error deleting all chats: {e}")
        return jsonify({"error": "Error deleting all chats"}), 500


@app.route('/api/model/status', methods=['GET'])
def model_status():
    """Get model status without trying to load models."""
    # Check model instances without loading (don't call get_model which tries to load)
    thor_1_0_model = model_instances.get('thor-1.0')
    thor_1_1_model = model_instances.get('qwen3-thor')  # thor-1.1 maps to qwen3-thor
    antelope_1_1_model = model_instances.get('antelope-1.1')
    
    # Get available tasks from the models
    thor_1_0_tasks = []
    if thor_1_0_model and hasattr(thor_1_0_model, 'model') and hasattr(thor_1_0_model.model, 'task_heads'):
        thor_1_0_tasks = list(thor_1_0_model.model.task_heads.keys())
    
    thor_1_1_tasks = []
    if thor_1_1_model and hasattr(thor_1_1_model, 'model') and hasattr(thor_1_1_model.model, 'task_heads'):
        thor_1_1_tasks = list(thor_1_1_model.model.task_heads.keys())
    
    antelope_1_1_tasks = []
    if antelope_1_1_model and hasattr(antelope_1_1_model, 'model') and hasattr(antelope_1_1_model.model, 'task_heads'):
        antelope_1_1_tasks = list(antelope_1_1_model.model.task_heads.keys())
    
    thor_1_2_model = model_instances.get('thor-1.2')  # Thor 1.2 from models/thor/thor-1.2
    thor_1_2_tasks = []
    if thor_1_2_model and hasattr(thor_1_2_model, 'model') and hasattr(thor_1_2_model.model, 'task_heads'):
        thor_1_2_tasks = list(thor_1_2_model.model.task_heads.keys())
    # Check why models might not be loaded
    def get_model_info(model, model_dir_path, model_name_str):
        if model_name_str == 'thor-1.0':
            tasks = thor_1_0_tasks
        elif model_name_str == 'thor-1.1':
            tasks = thor_1_1_tasks
        elif model_name_str == 'thor-1.2':
            tasks = thor_1_2_tasks
        elif model_name_str == 'antelope-1.1':
            tasks = antelope_1_1_tasks
        else:
            tasks = []
        
        info = {
            "loaded": model is not None,
            "available_tasks": tasks
        }
        
        if not model:
            info["reason"] = "not_loaded"
            info["diagnostics"] = {}
            
            # Check if torch is available
            if torch is None:
                info["diagnostics"]["torch_available"] = False
                info["diagnostics"]["message"] = "PyTorch not available (normal in serverless/lite deployments)"
            else:
                info["diagnostics"]["torch_available"] = True
                
                # Check if model files exist
                model_path = os.path.join(model_dir_path, "final_model.pt")
                tokenizer_path = os.path.join(model_dir_path, "tokenizer.json")
                
                info["diagnostics"]["model_file_exists"] = os.path.exists(model_path)
                info["diagnostics"]["tokenizer_file_exists"] = os.path.exists(tokenizer_path)
                
                if not os.path.exists(model_path) or not os.path.exists(tokenizer_path):
                    info["diagnostics"]["message"] = f"Model files not found (expected in {model_name_str}/models/)"
                else:
                    info["diagnostics"]["message"] = "Model files exist but loading failed (check server logs)"
        
        return info
    
    thor_1_0_info = get_model_info(thor_1_0_model, str(THOR_1_0_DIR / "models"), "thor-1.0")
    thor_1_1_info = get_model_info(thor_1_1_model, str(THOR_1_1_DIR / "models"), "thor-1.1")
    thor_1_2_info = get_model_info(thor_1_2_model, str(THOR_1_2_DIR / "models"), "thor-1.2")
    antelope_1_1_info = get_model_info(antelope_1_1_model, str(ANTELOPE_1_1_DIR / "models"), "antelope-1.1")
    
    thor_1_1_loading = model_loading_progress.get('thor-1.1', model_loading_progress.get('qwen3-thor', {'progress': 0, 'status': 'not_started', 'message': ''}))
    thor_1_2_loading = model_loading_progress.get('thor-1.2', {'progress': 0, 'status': 'not_started', 'message': ''})
    # Determine default model: prefer Thor 1.2 (loads instantly from models/thor/thor-1.2)
    thor_1_0_loaded = thor_1_0_model is not None
    thor_1_1_loaded = thor_1_1_model is not None
    thor_1_2_loaded = thor_1_2_model is not None
    default_model = "thor-1.2" if thor_1_2_loaded else ("thor-1.0" if thor_1_0_loaded else ("thor-1.1" if thor_1_1_loaded else "thor-1.2"))
    
    return jsonify({
        "models": {
            "thor-1.0": {
                **thor_1_0_info,
                "loading_progress": model_loading_progress.get('thor-1.0', {'progress': 0, 'status': 'not_started', 'message': ''})
            },
            "thor-1.1": {
                **thor_1_1_info,  # This is actually the combined Qwen3-4B + Thor 1.1 model
                "loading_progress": thor_1_1_loading
            },
            "thor-1.2": {
                **thor_1_2_info,  # Improved version from models/thor/thor-1.2, loads instantly
                "loading_progress": thor_1_2_loading
            },
            "antelope-1.1": {
                **antelope_1_1_info,
                "loading_progress": model_loading_progress.get('antelope-1.1', {'progress': 0, 'status': 'not_started', 'message': ''})
            }
        },
        "available_models": ["thor-1.0", "thor-1.1", "thor-1.2", "antelope-1.1"],
        "default_model": default_model,
        "stable_model": "thor-1.0",
        "fallback_available": True,  # App can work without model using research engine
        "message": "Chat will work using research engine and knowledge base even if model is not loaded",
        "model_info": {
            "thor-1.1": "Combined Qwen3-4B + Thor 1.1 (5B parameters total)",
            "thor-1.2": "Thor 1.2 improved version (models/thor/thor-1.2, loads instantly)"
        }
    })


@app.route('/api/model/loading-progress', methods=['GET'])
def model_loading_progress_endpoint():
    """Get model loading progress for frontend display."""
    model_name = request.args.get('model', 'thor-1.2')
    
    # Map model names to progress keys
    progress_key_map = {
        'thor-1.1': 'thor-1.1',
        'thor-1.2': 'thor-1.2',
        'qwen3-thor': 'thor-1.1',
        'thor-1.0': 'thor-1.0',
        'antelope-1.1': 'antelope-1.1'
    }
    
    progress_key = progress_key_map.get(model_name, model_name)
    progress = model_loading_progress.get(progress_key, {
        'progress': 0,
        'status': 'not_started',
        'message': 'Not started'
    })
    
    # Also check if model is actually loaded
    model_key = 'qwen3-thor' if model_name in ['thor-1.1', 'qwen3-thor'] else model_name
    is_loaded = model_instances.get(model_key) is not None
    
    # If progress says loaded but model isn't actually loaded, update status
    if progress['status'] == 'loaded' and not is_loaded:
        progress['status'] = 'not_started'
        progress['progress'] = 0
        progress['message'] = 'Model loading failed or not started'
    
    # Generate display message using utility function - always include progress
    if progress['status'] == 'loading':
        display_message = f"Model Currently Loading - {progress.get('progress', 0):.1f}% Loaded."
    elif progress['status'] == 'loaded' and is_loaded:
        display_message = "Model loaded successfully"
    elif progress['status'] == 'failed':
        # Use error progress message utility to ensure progress is always shown
        display_message = get_error_progress_message(model_name, progress.get('progress', 0))
        if not display_message:
            display_message = f"Model loading failed: {progress['message']} ({progress.get('progress', 0):.1f}%)"
    else:
        progress_pct = progress.get('progress', 0)
        display_message = progress['message'] or f'Not started (0%)'
        if progress_pct > 0:
            display_message += f" ({progress_pct:.1f}%)"
    
    # Always include progress percentage in response
    progress_value = progress.get('progress', 0)
    return jsonify({
        'model': model_name,
        'progress': progress_value,
        'progress_percentage': f"{progress_value:.1f}%",
        'status': progress['status'],
        'message': progress['message'],
        'loaded': is_loaded,
        'display_message': display_message
    })


# ==================== GEMS API ====================

@app.route('/api/gems', methods=['GET'])
def list_gems():
    try:
        db = _load_gems_db()
        gems_out = [_public_gem(g) for g in db.get("gems", [])]
        gems_out.sort(key=lambda g: g.get("updated_at", ""), reverse=True)
        return jsonify({"gems": gems_out})
    except Exception as e:
        print(f"Error listing gems: {e}")
        return jsonify({"error": "Error loading gems"}), 500


@app.route('/api/gems', methods=['POST'])
def create_gem():
    try:
        data = request.json or {}
        name = (data.get("name") or "").strip()
        if not name:
            return jsonify({"error": "Gem name is required"}), 400

        gem_id = f"{_slugify(name)}-{uuid.uuid4().hex[:6]}"
        now = datetime.now().isoformat()
        gem = {
            "id": gem_id,
            "name": name,
            "description": (data.get("description") or "").strip(),
            "instructions": (data.get("instructions") or "").strip(),
            "tone": (data.get("tone") or "normal").strip(),
            "sources": data.get("sources") or {"links": [], "files": []},
            "created_at": now,
            "updated_at": now,
        }

        db = _load_gems_db()
        db.setdefault("gems", []).append(gem)
        _save_gems_db(db)
        return jsonify({"gem": _public_gem(gem)}), 201
    except Exception as e:
        print(f"Error creating gem: {e}")
        return jsonify({"error": "Error creating gem"}), 500


@app.route('/api/gems/<gem_id>', methods=['PUT'])
def update_gem(gem_id):
    try:
        data = request.json or {}
        db = _load_gems_db()
        updated = None
        for g in db.get("gems", []):
            if g.get("id") != gem_id:
                continue
            if "name" in data:
                g["name"] = (data.get("name") or "").strip() or g.get("name")
            if "description" in data:
                g["description"] = (data.get("description") or "").strip()
            if "instructions" in data:
                g["instructions"] = (data.get("instructions") or "").strip()
            if "tone" in data:
                g["tone"] = (data.get("tone") or "normal").strip()
            if "sources" in data:
                g["sources"] = data.get("sources") or {"links": [], "files": []}
            g["updated_at"] = datetime.now().isoformat()
            updated = g
            break

        if not updated:
            return jsonify({"error": "Gem not found"}), 404
        _save_gems_db(db)
        return jsonify({"gem": _public_gem(updated)})
    except Exception as e:
        print(f"Error updating gem: {e}")
        return jsonify({"error": "Error updating gem"}), 500


@app.route('/api/gems/<gem_id>', methods=['DELETE'])
def delete_gem(gem_id):
    try:
        db = _load_gems_db()
        gems_list = db.get("gems", [])
        before = len(gems_list)
        db["gems"] = [g for g in gems_list if g.get("id") != gem_id]
        if len(db["gems"]) == before:
            return jsonify({"error": "Gem not found"}), 404
        _save_gems_db(db)
        return jsonify({"success": True})
    except Exception as e:
        print(f"Error deleting gem: {e}")
        return jsonify({"error": "Error deleting gem"}), 500


@app.route('/api/learning/status', methods=['GET'])
def learning_status():
    """Get learning status."""
    try:
        tracker = get_tracker()
        stats = tracker.get_stats()
        recent = tracker.get_recent_activity(hours=24)
        
        auto_trainer = get_auto_trainer()
        if auto_trainer is None:
            return jsonify({
                "error": "Auto-trainer is not available",
                "conversations": []
            }), 503
        
        conversations = auto_trainer._get_conversations()
        
        return jsonify({
            "total_conversations": stats.get("total_conversations", 0),
            "total_training_cycles": stats.get("total_training_cycles", 0),
            "recent_training_cycles": recent.get("training_cycles", 0),
            "recent_brain_searches": recent.get("brain_searches", 0),
            "conversations_available": len(conversations),
            "auto_trainer_running": auto_trainer.running,
            "learning_rate": stats.get("learning_rate", {}),
            "last_updated": stats.get("last_updated")
        })
    except Exception as e:
        print(f"Error getting learning status: {e}")
        return jsonify({"error": "Error getting learning status"}), 500


# ==================== PROJECTS API ====================

def save_project(project_id, project_data):
    """Save project to disk."""
    project_file = os.path.join(PROJECTS_DIR, f"{project_id}.json")
    with open(project_file, 'w') as f:
        json.dump(project_data, f, indent=2)


def load_project(project_id):
    """Load project from disk."""
    project_file = os.path.join(PROJECTS_DIR, f"{project_id}.json")
    if os.path.exists(project_file):
        with open(project_file, 'r') as f:
            return json.load(f)
    return None


def list_projects():
    """List all saved projects."""
    projects = []
    if os.path.exists(PROJECTS_DIR):
        for file in os.listdir(PROJECTS_DIR):
            if file.endswith('.json'):
                project_id = file[:-5]  # Remove .json
                project_data = load_project(project_id)
                if project_data:
                    # Count chats in project
                    chat_ids = project_data.get("chat_ids", [])
                    projects.append({
                        "project_id": project_id,
                        "name": project_data.get("name", "Untitled Project"),
                        "description": project_data.get("description", ""),
                        "created_at": project_data.get("created_at", ""),
                        "updated_at": project_data.get("updated_at", ""),
                        "chat_count": len(chat_ids),
                        "context": project_data.get("context", "")
                    })
    # Sort by updated_at, newest first
    projects.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
    return projects


@app.route('/api/projects', methods=['GET'])
def get_projects():
    """Get list of all projects."""
    try:
        projects = list_projects()
        return jsonify({"projects": projects})
    except Exception as e:
        print(f"Error listing projects: {e}")
        return jsonify({"error": "Error loading projects"}), 500


@app.route('/api/projects', methods=['POST'])
def create_project():
    """Create a new project."""
    try:
        data = request.json
        project_id = str(uuid.uuid4())
        
        project_data = {
            "project_id": project_id,
            "name": data.get("name", "Untitled Project"),
            "description": data.get("description", ""),
            "context": data.get("context", ""),
            "chat_ids": data.get("chat_ids", []),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        save_project(project_id, project_data)
        return jsonify(project_data), 201
    except Exception as e:
        print(f"Error creating project: {e}")
        return jsonify({"error": "Error creating project"}), 500


@app.route('/api/projects/<project_id>', methods=['GET'])
def get_project(project_id):
    """Get a specific project."""
    try:
        project_data = load_project(project_id)
        if project_data:
            return jsonify(project_data)
        else:
            return jsonify({"error": "Project not found"}), 404
    except Exception as e:
        print(f"Error loading project: {e}")
        return jsonify({"error": "Error loading project"}), 500


@app.route('/api/projects/<project_id>', methods=['PUT'])
def update_project(project_id):
    """Update a project."""
    try:
        project_data = load_project(project_id)
        if not project_data:
            return jsonify({"error": "Project not found"}), 404
        
        data = request.json
        if "name" in data:
            project_data["name"] = data["name"]
        if "description" in data:
            project_data["description"] = data["description"]
        if "context" in data:
            project_data["context"] = data["context"]
        if "chat_ids" in data:
            project_data["chat_ids"] = data["chat_ids"]
        
        project_data["updated_at"] = datetime.now().isoformat()
        save_project(project_id, project_data)
        return jsonify(project_data)
    except Exception as e:
        print(f"Error updating project: {e}")
        return jsonify({"error": "Error updating project"}), 500


@app.route('/api/projects/<project_id>', methods=['DELETE'])
def delete_project(project_id):
    """Delete a project."""
    try:
        project_file = os.path.join(PROJECTS_DIR, f"{project_id}.json")
        if os.path.exists(project_file):
            os.remove(project_file)
            return jsonify({"success": True})
        else:
            return jsonify({"error": "Project not found"}), 404
    except Exception as e:
        print(f"Error deleting project: {e}")
        return jsonify({"error": "Error deleting project"}), 500


@app.route('/api/projects/<project_id>/chats', methods=['POST'])
def add_chat_to_project(project_id):
    """Add a chat to a project."""
    try:
        project_data = load_project(project_id)
        if not project_data:
            return jsonify({"error": "Project not found"}), 404
        
        data = request.json
        chat_id = data.get("chat_id")
        if not chat_id:
            return jsonify({"error": "chat_id is required"}), 400
        
        chat_ids = project_data.get("chat_ids", [])
        if chat_id not in chat_ids:
            chat_ids.append(chat_id)
            project_data["chat_ids"] = chat_ids
            project_data["updated_at"] = datetime.now().isoformat()
            save_project(project_id, project_data)
        
        return jsonify(project_data)
    except Exception as e:
        print(f"Error adding chat to project: {e}")
        return jsonify({"error": "Error adding chat to project"}), 500


@app.route('/api/projects/<project_id>/chats/<chat_id>', methods=['DELETE'])
def remove_chat_from_project(project_id, chat_id):
    """Remove a chat from a project."""
    try:
        project_data = load_project(project_id)
        if not project_data:
            return jsonify({"error": "Project not found"}), 404
        
        chat_ids = project_data.get("chat_ids", [])
        if chat_id in chat_ids:
            chat_ids.remove(chat_id)
            project_data["chat_ids"] = chat_ids
            project_data["updated_at"] = datetime.now().isoformat()
            save_project(project_id, project_data)
        
        return jsonify(project_data)
    except Exception as e:
        print(f"Error removing chat from project: {e}")
        return jsonify({"error": "Error removing chat from project"}), 500


# ==================== HISTORY API ====================

def save_history_entry(entry_data):
    """Save a history entry."""
    history_file = os.path.join(HISTORY_DIR, "history.json")
    
    # Load existing history
    history = []
    if os.path.exists(history_file):
        try:
            with open(history_file, 'r') as f:
                history = json.load(f)
        except:
            history = []
    
    # Add new entry
    history.append(entry_data)
    
    # Keep only last 1000 entries
    history = history[-1000:]
    
    # Save back
    with open(history_file, 'w') as f:
        json.dump(history, f, indent=2)


def get_history(limit=100, offset=0):
    """Get history entries."""
    history_file = os.path.join(HISTORY_DIR, "history.json")
    
    if not os.path.exists(history_file):
        return []
    
    try:
        with open(history_file, 'r') as f:
            history = json.load(f)
        
        # Sort by timestamp, newest first
        history.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        # Apply pagination
        return history[offset:offset+limit]
    except:
        return []


@app.route('/api/history', methods=['GET'])
def get_history_endpoint():
    """Get history entries."""
    try:
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        history = get_history(limit=limit, offset=offset)
        return jsonify({"history": history, "count": len(history)})
    except Exception as e:
        print(f"Error getting history: {e}")
        return jsonify({"error": "Error loading history"}), 500


@app.route('/api/history', methods=['POST'])
def create_history_entry():
    """Create a history entry (automatically called on chat actions)."""
    try:
        data = request.json
        entry_data = {
            "id": str(uuid.uuid4()),
            "type": data.get("type", "chat"),  # chat, project, action, etc.
            "title": data.get("title", ""),
            "description": data.get("description", ""),
            "chat_id": data.get("chat_id"),
            "project_id": data.get("project_id"),
            "timestamp": datetime.now().isoformat(),
            "metadata": data.get("metadata", {})
        }
        
        save_history_entry(entry_data)
        return jsonify(entry_data), 201
    except Exception as e:
        print(f"Error creating history entry: {e}")
        return jsonify({"error": "Error creating history entry"}), 500


@app.route('/api/history/<entry_id>', methods=['DELETE'])
def delete_history_entry(entry_id):
    """Delete a history entry."""
    try:
        history_file = os.path.join(HISTORY_DIR, "history.json")
        
        if not os.path.exists(history_file):
            return jsonify({"error": "History entry not found"}), 404
        
        with open(history_file, 'r') as f:
            history = json.load(f)
        
        # Remove entry
        history = [h for h in history if h.get("id") != entry_id]
        
        with open(history_file, 'w') as f:
            json.dump(history, f, indent=2)
        
        return jsonify({"success": True})
    except Exception as e:
        print(f"Error deleting history entry: {e}")
        return jsonify({"error": "Error deleting history entry"}), 500


# ==================== ENHANCED FEATURES v2.5.0 API ====================

@app.route('/api/chats/<chat_id>/export', methods=['GET'])
def export_chat(chat_id):
    """Export a chat as JSON."""
    try:
        chat_file = os.path.join(CHATS_DIR, f"{chat_id}.json")
        if not os.path.exists(chat_file):
            return jsonify({"error": "Chat not found"}), 404
        
        with open(chat_file, 'r', encoding='utf-8') as f:
            chat_data = json.load(f)
        
        export_data = {
            "version": "2.5.0",
            "exported_at": datetime.now().isoformat(),
            "chat": chat_data
        }
        
        return jsonify(export_data)
    except Exception as e:
        print(f"Error exporting chat: {e}")
        return jsonify({"error": "Error exporting chat"}), 500


@app.route('/api/chats/import', methods=['POST'])
def import_chat():
    """Import a chat from JSON."""
    try:
        data = request.json
        if not data or "chat" not in data:
            return jsonify({"error": "Invalid import data"}), 400
        
        chat_data = data["chat"]
        chat_id = chat_data.get("chat_id") or str(uuid.uuid4())
        
        # Ensure chat_id is unique
        chat_file = os.path.join(CHATS_DIR, f"{chat_id}.json")
        counter = 1
        while os.path.exists(chat_file):
            chat_id = f"{chat_data.get('chat_id', str(uuid.uuid4()))}-imported-{counter}"
            chat_file = os.path.join(CHATS_DIR, f"{chat_id}.json")
            counter += 1
        
        chat_data["chat_id"] = chat_id
        chat_data["imported_at"] = datetime.now().isoformat()
        
        with open(chat_file, 'w', encoding='utf-8') as f:
            json.dump(chat_data, f, indent=2, ensure_ascii=False)
        
        return jsonify({"chat_id": chat_id, "success": True})
    except Exception as e:
        print(f"Error importing chat: {e}")
        return jsonify({"error": "Error importing chat"}), 500


@app.route('/api/analytics', methods=['GET'])
def get_analytics():
    """Get conversation analytics and statistics."""
    try:
        # Get all chats
        chats = []
        if os.path.exists(CHATS_DIR):
            for filename in os.listdir(CHATS_DIR):
                if filename.endswith('.json'):
                    try:
                        with open(os.path.join(CHATS_DIR, filename), 'r', encoding='utf-8') as f:
                            chat = json.load(f)
                            chats.append(chat)
                    except:
                        continue
        
        # Calculate statistics
        total_chats = len(chats)
        total_messages = sum(len(chat.get("messages", [])) for chat in chats)
        
        # Messages by role
        user_messages = 0
        assistant_messages = 0
        for chat in chats:
            for msg in chat.get("messages", []):
                if msg.get("role") == "user":
                    user_messages += 1
                elif msg.get("role") == "assistant":
                    assistant_messages += 1
        
        # Chats by date
        chats_by_date = {}
        for chat in chats:
            created_at = chat.get("created_at", "")
            if created_at:
                date = created_at[:10]  # YYYY-MM-DD
                chats_by_date[date] = chats_by_date.get(date, 0) + 1
        
        # Average messages per chat
        avg_messages = total_messages / total_chats if total_chats > 0 else 0
        
        analytics = {
            "total_chats": total_chats,
            "total_messages": total_messages,
            "user_messages": user_messages,
            "assistant_messages": assistant_messages,
            "average_messages_per_chat": round(avg_messages, 2),
            "chats_by_date": chats_by_date,
            "generated_at": datetime.now().isoformat()
        }
        
        return jsonify(analytics)
    except Exception as e:
        print(f"Error getting analytics: {e}")
        return jsonify({"error": "Error getting analytics"}), 500


@app.route('/api/chats/search', methods=['GET'])
def search_chats():
    """Search chats by query."""
    try:
        query = request.args.get('q', '').lower()
        if not query:
            return jsonify({"chats": []})
        
        chats = []
        if os.path.exists(CHATS_DIR):
            for filename in os.listdir(CHATS_DIR):
                if filename.endswith('.json'):
                    try:
                        with open(os.path.join(CHATS_DIR, filename), 'r', encoding='utf-8') as f:
                            chat = json.load(f)
                            
                            # Search in title/name
                            name = (chat.get("name") or "").lower()
                            
                            # Search in messages
                            matches = False
                            for msg in chat.get("messages", []):
                                content = (msg.get("content") or "").lower()
                                if query in content:
                                    matches = True
                                    break
                            
                            if query in name or matches:
                                chats.append({
                                    "chat_id": chat.get("chat_id"),
                                    "name": chat.get("name"),
                                    "created_at": chat.get("created_at"),
                                    "message_count": len(chat.get("messages", []))
                                })
                    except:
                        continue
        
        return jsonify({"chats": chats})
    except Exception as e:
        print(f"Error searching chats: {e}")
        return jsonify({"error": "Error searching chats"}), 500

# Beta Features - Search & Discovery
# ===================================

@app.route('/api/beta/search', methods=['GET'])
def global_search():
    """Global search across chats, projects, gems, and brain (Beta Feature)."""
    try:
        if not request.headers.get('X-Beta-Mode') == 'true':
            return jsonify({"error": "Beta features not enabled"}), 403

        query = request.args.get('q', '').strip()
        search_type = request.args.get('type', 'all')  # all, chats, projects, gems, brain
        limit = int(request.args.get('limit', 20))

        if not query:
            return jsonify({"error": "Query parameter 'q' is required"}), 400

        results = {
            "query": query,
            "total_results": 0,
            "chats": [],
            "projects": [],
            "gems": [],
            "brain": []
        }

        # Search chats
        if search_type in ['all', 'chats']:
            chat_results = _search_chats(query, limit // 4)
            results["chats"] = chat_results
            results["total_results"] += len(chat_results)

        # Search projects
        if search_type in ['all', 'projects']:
            project_results = _search_projects(query, limit // 4)
            results["projects"] = project_results
            results["total_results"] += len(project_results)

        # Search gems
        if search_type in ['all', 'gems']:
            gem_results = _search_gems(query, limit // 4)
            results["gems"] = gem_results
            results["total_results"] += len(gem_results)

        # Search brain (knowledge)
        if search_type in ['all', 'brain']:
            brain_results = _search_brain(query, limit // 4)
            results["brain"] = brain_results
            results["total_results"] += len(brain_results)

        return jsonify(results)

    except Exception as e:
        print(f"[Beta] Error in global search: {e}")
        return jsonify({"error": "Failed to perform search"}), 500

def _search_chats(query, limit):
    """Search within chats."""
    results = []
    try:
        if os.path.exists(CHATS_DIR):
            for file in os.listdir(CHATS_DIR):
                if file.endswith('.json') and len(results) < limit:
                    chat_id = file[:-5]
                    chat_data = load_chat(chat_id)
                    if chat_data:
                        # Search in chat name
                        name_score = 0
                        if query.lower() in (chat_data.get("name") or "").lower():
                            name_score = 10

                        # Search in messages with context
                        message_results = []
                        messages = chat_data.get("messages", [])
                        for i, msg in enumerate(messages):
                            content = msg.get("content", "")
                            if query.lower() in content.lower():
                                # Get context (previous and next messages)
                                context_start = max(0, i - 1)
                                context_end = min(len(messages), i + 2)
                                context = messages[context_start:context_end]

                                message_results.append({
                                    "content": content,
                                    "role": msg.get("role"),
                                    "timestamp": msg.get("timestamp"),
                                    "context": context
                                })

                        if name_score > 0 or message_results:
                            results.append({
                                "chat_id": chat_id,
                                "name": chat_data.get("name", "New Chat"),
                                "created_at": chat_data.get("created_at", ""),
                                "score": name_score + len(message_results),
                                "message_matches": message_results[:3]
                            })
    except Exception as e:
        print(f"[Beta] Error searching chats: {e}")

    return sorted(results, key=lambda x: x["score"], reverse=True)[:limit]

def _search_projects(query, limit):
    """Search within projects."""
    results = []
    try:
        if os.path.exists(PROJECTS_DIR):
            for file in os.listdir(PROJECTS_DIR):
                if file.endswith('.json') and len(results) < limit:
                    project_id = file[:-5]
                    project_data = load_project(project_id)
                    if project_data:
                        score = 0
                        if query.lower() in (project_data.get("name") or "").lower():
                            score += 10
                        if query.lower() in (project_data.get("description") or "").lower():
                            score += 5

                        if score > 0:
                            results.append({
                                "project_id": project_id,
                                "name": project_data.get("name", "Project"),
                                "description": project_data.get("description", ""),
                                "created_at": project_data.get("created_at", ""),
                                "chat_count": len(project_data.get("chat_ids", [])),
                                "score": score
                            })
    except Exception as e:
        print(f"[Beta] Error searching projects: {e}")

    return sorted(results, key=lambda x: x["score"], reverse=True)[:limit]

def _search_gems(query, limit):
    """Search within gems."""
    results = []
    try:
        gems = _load_gems()
        for gem_id, gem_data in gems.items():
            if len(results) >= limit:
                break

            score = 0
            if query.lower() in gem_id.lower():
                score += 10
            if query.lower() in (gem_data.get("name") or "").lower():
                score += 8
            if query.lower() in (gem_data.get("description") or "").lower():
                score += 5
            if query.lower() in (gem_data.get("instructions") or "").lower():
                score += 3

            if score > 0:
                results.append({
                    "gem_id": gem_id,
                    "name": gem_data.get("name", "Gem"),
                    "description": gem_data.get("description", ""),
                    "tone": gem_data.get("tone", "normal"),
                    "score": score
                })
    except Exception as e:
        print(f"[Beta] Error searching gems: {e}")

    return sorted(results, key=lambda x: x["score"], reverse=True)[:limit]

def _search_brain(query, limit):
    """Search within brain knowledge."""
    results = []
    try:
        # Import brain connector
        from brain import BrainConnector
        brain = BrainConnector()

        # Search across all brain data
        knowledge_results = brain.search(query, limit=limit)

        for item in knowledge_results:
            results.append({
                "title": item.get("title", ""),
                "content": item.get("content", "")[:200] + "...",
                "source": item.get("source", "brain"),
                "learned_at": item.get("learned_at", ""),
                "score": item.get("relevance_score", 0)
            })
    except Exception as e:
        print(f"[Beta] Error searching brain: {e}")

    return results[:limit]

@app.route('/api/beta/analytics', methods=['GET'])
def get_beta_analytics():
    """Get analytics and insights for beta features."""
    try:
        if not request.headers.get('X-Beta-Mode') == 'true':
            return jsonify({"error": "Beta features not enabled"}), 403

        # Get basic analytics
        analytics = {
            "total_chats": 0,
            "total_messages": 0,
            "total_projects": 0,
            "total_gems": 0,
            "top_topics": [],
            "usage_patterns": {},
            "beta_features_usage": {},
            "recent_activity": []
        }

        # Count chats and messages
        if os.path.exists(CHATS_DIR):
            for file in os.listdir(CHATS_DIR):
                if file.endswith('.json'):
                    analytics["total_chats"] += 1
                    try:
                        with open(os.path.join(CHATS_DIR, file), 'r', encoding='utf-8') as f:
                            chat_data = json.load(f)
                            analytics["total_messages"] += len(chat_data.get("messages", []))
                    except:
                        pass

        # Count projects
        if os.path.exists(PROJECTS_DIR):
            analytics["total_projects"] = len([f for f in os.listdir(PROJECTS_DIR) if f.endswith('.json')])

        # Count gems
        gems = _load_gems()
        analytics["total_gems"] = len(gems)

        # Get top topics (simple keyword analysis)
        topic_counts = {}
        if os.path.exists(CHATS_DIR):
            for file in os.listdir(CHATS_DIR):
                if file.endswith('.json'):
                    try:
                        with open(os.path.join(CHATS_DIR, file), 'r', encoding='utf-8') as f:
                            chat_data = json.load(f)
                            chat_name = chat_data.get("name", "").lower()
                            # Extract keywords from chat names
                            words = chat_name.split()
                            for word in words:
                                if len(word) > 3:  # Skip short words
                                    topic_counts[word] = topic_counts.get(word, 0) + 1
                    except:
                        pass

        # Sort topics by frequency
        analytics["top_topics"] = sorted(
            [{"topic": k, "count": v} for k, v in topic_counts.items()],
            key=lambda x: x["count"],
            reverse=True
        )[:10]

        # Get recent activity (last 10 chats)
        recent_chats = []
        if os.path.exists(CHATS_DIR):
            for file in os.listdir(CHATS_DIR):
                if file.endswith('.json'):
                    try:
                        with open(os.path.join(CHATS_DIR, file), 'r', encoding='utf-8') as f:
                            chat_data = json.load(f)
                            recent_chats.append({
                                "name": chat_data.get("name", "Chat"),
                                "created_at": chat_data.get("created_at", ""),
                                "message_count": len(chat_data.get("messages", []))
                            })
                    except:
                        pass

        # Sort by creation date and take last 10
        analytics["recent_activity"] = sorted(
            recent_chats,
            key=lambda x: x.get("created_at", ""),
            reverse=True
        )[:10]

        # Beta features usage stats
        analytics["beta_features_usage"] = {
            "shared_chats": len(_load_shared_chats()) if os.path.exists(SHARED_CHATS_FILE.parent) else 0,
            "templates": len(_load_templates().get("templates", [])),
            "tasks": len(_load_tasks().get("global_tasks", [])),
            "snippets": len(_load_snippets().get("snippets", [])),
            "workflows": len(_load_workflows().get("workflows", []))
        }

        return jsonify(analytics)

    except Exception as e:
        print(f"[Beta] Error getting analytics: {e}")
        return jsonify({"error": "Failed to get analytics"}), 500


# Beta Features - Collaboration & Sharing
# ======================================

SHARED_CHATS_FILE = DATA_ROOT / "shared_chats.json"
TEMPLATES_FILE = DATA_ROOT / "templates.json"
GEM_MARKETPLACE_FILE = DATA_ROOT / "gem_marketplace.json"

def _load_shared_chats():
    """Load shared chats from file."""
    try:
        if SHARED_CHATS_FILE.exists():
            with open(SHARED_CHATS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"[Beta] Error loading shared chats: {e}")
    return {}

def _save_shared_chats(shared_chats):
    """Save shared chats to file."""
    try:
        SHARED_CHATS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(SHARED_CHATS_FILE, 'w', encoding='utf-8') as f:
            json.dump(shared_chats, f, indent=2)
    except Exception as e:
        print(f"[Beta] Error saving shared chats: {e}")

def _load_templates():
    """Load chat templates from file."""
    try:
        if TEMPLATES_FILE.exists():
            with open(TEMPLATES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"[Beta] Error loading templates: {e}")
    return {"templates": []}

def _save_templates(templates):
    """Save chat templates to file."""
    try:
        TEMPLATES_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(TEMPLATES_FILE, 'w', encoding='utf-8') as f:
            json.dump(templates, f, indent=2)
    except Exception as e:
        print(f"[Beta] Error saving templates: {e}")

def _load_gem_marketplace():
    """Load gem marketplace from file."""
    try:
        if GEM_MARKETPLACE_FILE.exists():
            with open(GEM_MARKETPLACE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"[Beta] Error loading gem marketplace: {e}")
    return {"gems": []}

def _save_gem_marketplace(marketplace):
    """Save gem marketplace to file."""
    try:
        GEM_MARKETPLACE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(GEM_MARKETPLACE_FILE, 'w', encoding='utf-8') as f:
            json.dump(marketplace, f, indent=2)
    except Exception as e:
        print(f"[Beta] Error saving gem marketplace: {e}")

@app.route('/api/beta/shared-chats/<chat_id>/share', methods=['POST'])
def share_chat(chat_id):
    """Create a shareable link for a chat (Beta Feature)."""
    try:
        # Check if beta mode is enabled
        if not request.headers.get('X-Beta-Mode') == 'true':
            return jsonify({"error": "Beta features not enabled"}), 403

        # Load the chat
        chat_data = load_chat(chat_id)
        if not chat_data:
            return jsonify({"error": "Chat not found"}), 404

        # Generate share token
        import secrets
        share_token = secrets.token_urlsafe(16)

        # Store shared chat metadata
        shared_chats = _load_shared_chats()
        shared_chats[share_token] = {
            "chat_id": chat_id,
            "chat_name": chat_data.get("name", "Shared Chat"),
            "created_at": chat_data.get("created_at", ""),
            "shared_at": datetime.now().isoformat(),
            "share_token": share_token,
            "message_count": len(chat_data.get("messages", [])),
            "is_active": True
        }
        _save_shared_chats(shared_chats)

        # Generate shareable URL
        base_url = request.host_url.rstrip('/')
        share_url = f"{base_url}/shared/{share_token}"

        return jsonify({
            "share_token": share_token,
            "share_url": share_url,
            "chat_name": chat_data.get("name", "Shared Chat")
        })

    except Exception as e:
        print(f"[Beta] Error sharing chat: {e}")
        return jsonify({"error": "Failed to share chat"}), 500

@app.route('/shared/<share_token>')
def view_shared_chat(share_token):
    """View a shared chat (Beta Feature)."""
    try:
        shared_chats = _load_shared_chats()
        share_data = shared_chats.get(share_token)

        if not share_data or not share_data.get("is_active", False):
            return render_template('shared_chat_not_found.html'), 404

        # Load the actual chat data
        chat_data = load_chat(share_data["chat_id"])
        if not chat_data:
            return render_template('shared_chat_not_found.html'), 404

        return render_template('shared_chat.html',
                             chat_data=chat_data,
                             share_data=share_data,
                             share_token=share_token)

    except Exception as e:
        print(f"[Beta] Error viewing shared chat: {e}")
        return render_template('shared_chat_not_found.html'), 500

@app.route('/api/beta/templates', methods=['GET'])
def get_templates():
    """Get all chat templates (Beta Feature)."""
    try:
        if not request.headers.get('X-Beta-Mode') == 'true':
            return jsonify({"error": "Beta features not enabled"}), 403

        templates = _load_templates()
        return jsonify(templates)

    except Exception as e:
        print(f"[Beta] Error getting templates: {e}")
        return jsonify({"error": "Failed to get templates"}), 500

@app.route('/api/beta/templates', methods=['POST'])
def create_template():
    """Create a new chat template (Beta Feature)."""
    try:
        if not request.headers.get('X-Beta-Mode') == 'true':
            return jsonify({"error": "Beta features not enabled"}), 403

        data = request.get_json()
        if not data or not data.get('name') or not data.get('messages'):
            return jsonify({"error": "Template name and messages are required"}), 400

        templates = _load_templates()
        template_id = str(uuid.uuid4())

        template = {
            "id": template_id,
            "name": data['name'],
            "description": data.get('description', ''),
            "messages": data['messages'],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "usage_count": 0
        }

        templates["templates"].append(template)
        _save_templates(templates)

        return jsonify(template), 201

    except Exception as e:
        print(f"[Beta] Error creating template: {e}")
        return jsonify({"error": "Failed to create template"}), 500

@app.route('/api/beta/templates/<template_id>/use', methods=['POST'])
def use_template(template_id):
    """Use a template to create a new chat (Beta Feature)."""
    try:
        if not request.headers.get('X-Beta-Mode') == 'true':
            return jsonify({"error": "Beta features not enabled"}), 403

        templates = _load_templates()
        template = next((t for t in templates["templates"] if t["id"] == template_id), None)

        if not template:
            return jsonify({"error": "Template not found"}), 404

        # Increment usage count
        template["usage_count"] = template.get("usage_count", 0) + 1
        _save_templates(templates)

        # Create new chat with template messages
        chat_id = str(uuid.uuid4())
        chat_data = {
            "messages": template["messages"].copy(),
            "name": template["name"],
            "created_at": datetime.now().isoformat(),
            "template_id": template_id
        }

        save_chat(chat_id, chat_data["messages"], chat_data["name"])

        return jsonify({
            "chat_id": chat_id,
            "name": template["name"],
            "message_count": len(template["messages"])
        })

    except Exception as e:
        print(f"[Beta] Error using template: {e}")
        return jsonify({"error": "Failed to use template"}), 500

@app.route('/api/beta/templates/<template_id>', methods=['DELETE'])
def delete_template(template_id):
    """Delete a chat template (Beta Feature)."""
    try:
        if not request.headers.get('X-Beta-Mode') == 'true':
            return jsonify({"error": "Beta features not enabled"}), 403

        templates = _load_templates()
        templates["templates"] = [t for t in templates["templates"] if t["id"] != template_id]
        _save_templates(templates)

        return jsonify({"success": True})

    except Exception as e:
        print(f"[Beta] Error deleting template: {e}")
        return jsonify({"error": "Failed to delete template"}), 500

@app.route('/api/beta/gem-marketplace', methods=['GET'])
def get_gem_marketplace():
    """Get gem marketplace (Beta Feature)."""
    try:
        if not request.headers.get('X-Beta-Mode') == 'true':
            return jsonify({"error": "Beta features not enabled"}), 403

        marketplace = _load_gem_marketplace()
        return jsonify(marketplace)

    except Exception as e:
        print(f"[Beta] Error getting gem marketplace: {e}")
        return jsonify({"error": "Failed to get gem marketplace"}), 500

@app.route('/api/beta/gems/<gem_id>/publish', methods=['POST'])
def publish_gem_to_marketplace(gem_id):
    """Publish a gem to the marketplace (Beta Feature)."""
    try:
        if not request.headers.get('X-Beta-Mode') == 'true':
            return jsonify({"error": "Beta features not enabled"}), 403

        # Load the gem
        gems = _load_gems()
        gem = gems.get(gem_id)
        if not gem:
            return jsonify({"error": "Gem not found"}), 404

        # Add to marketplace
        marketplace = _load_gem_marketplace()
        marketplace_gem = {
            "id": gem_id,
            "name": gem["name"],
            "description": gem["description"],
            "instructions": gem["instructions"],
            "tone": gem["tone"],
            "published_at": datetime.now().isoformat(),
            "publisher": "current_user",  # TODO: Add user system
            "downloads": 0,
            "rating": 0,
            "reviews": []
        }

        marketplace["gems"].append(marketplace_gem)
        _save_gem_marketplace(marketplace)

        return jsonify(marketplace_gem), 201

    except Exception as e:
        print(f"[Beta] Error publishing gem: {e}")
        return jsonify({"error": "Failed to publish gem"}), 500

@app.route('/api/beta/chats/<chat_id>/export/<format>', methods=['GET'])
def export_chat_enhanced(chat_id, format):
    """Export a chat in enhanced formats (Beta Feature)."""
    try:
        if not request.headers.get('X-Beta-Mode') == 'true':
            return jsonify({"error": "Beta features not enabled"}), 403

        chat_data = load_chat(chat_id)
        if not chat_data:
            return jsonify({"error": "Chat not found"}), 404

        chat_name = chat_data.get("name", "Chat").replace("/", "_").replace("\\", "_")

        if format == 'pdf':
            # Generate PDF export
            html_content = _generate_chat_html(chat_data)
            pdf_buffer = _convert_html_to_pdf(html_content)
            return send_file(
                pdf_buffer,
                as_attachment=True,
                download_name=f"{chat_name}.pdf",
                mimetype='application/pdf'
            )

        elif format == 'markdown':
            # Generate Markdown export
            md_content = _generate_chat_markdown(chat_data)
            return Response(
                md_content,
                mimetype='text/markdown',
                headers={
                    'Content-Disposition': f'attachment; filename="{chat_name}.md"'
                }
            )

        elif format == 'html':
            # Generate HTML export
            html_content = _generate_chat_html(chat_data)
            return Response(
                html_content,
                mimetype='text/html',
                headers={
                    'Content-Disposition': f'attachment; filename="{chat_name}.html"'
                }
            )

        else:
            return jsonify({"error": f"Unsupported format: {format}"}), 400

    except Exception as e:
        print(f"[Beta] Error exporting chat: {e}")
        return jsonify({"error": "Failed to export chat"}), 500

def _generate_chat_markdown(chat_data):
    """Generate Markdown representation of chat."""
    lines = [f"# {chat_data.get('name', 'Chat')}\n"]
    lines.append(f"**Created:** {chat_data.get('created_at', 'Unknown')}\n")

    for msg in chat_data.get('messages', []):
        role = msg.get('role', 'unknown')
        content = msg.get('content', '')

        if role == 'user':
            lines.append(f"## User\n\n{content}\n")
        elif role == 'assistant':
            lines.append(f"## Assistant\n\n{content}\n")
        else:
            lines.append(f"## {role.title()}\n\n{content}\n")

    return "\n".join(lines)

def _generate_chat_html(chat_data):
    """Generate HTML representation of chat."""
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{chat_data.get('name', 'Chat')}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .message {{ margin: 20px 0; padding: 15px; border-radius: 8px; }}
            .user {{ background: #e3f2fd; border-left: 4px solid #2196f3; }}
            .assistant {{ background: #f5f5f5; border-left: 4px solid #4caf50; }}
            .role {{ font-weight: bold; margin-bottom: 10px; }}
            .timestamp {{ color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <h1>{chat_data.get('name', 'Chat')}</h1>
        <p><strong>Created:</strong> {chat_data.get('created_at', 'Unknown')}</p>
    """

    for msg in chat_data.get('messages', []):
        role = msg.get('role', 'unknown')
        content = msg.get('content', '').replace('\n', '<br>')
        css_class = 'user' if role == 'user' else 'assistant'

        html += f"""
        <div class="message {css_class}">
            <div class="role">{role.title()}</div>
            <div>{content}</div>
        </div>
        """

    html += "</body></html>"
    return html

def _convert_html_to_pdf(html_content):
    """Convert HTML to PDF (placeholder - would need pdfkit or similar library)."""
    # This is a placeholder - in a real implementation, you'd use a library like pdfkit
    # For now, return the HTML as a simple text response
    from io import BytesIO
    buffer = BytesIO()
    buffer.write(html_content.encode('utf-8'))
    buffer.seek(0)
    return buffer

# Beta Features - Productivity & Workflow
# =====================================

TASKS_FILE = DATA_ROOT / "tasks.json"
SNIPPETS_FILE = DATA_ROOT / "snippets.json"
WORKFLOWS_FILE = DATA_ROOT / "workflows.json"

def _load_tasks():
    """Load tasks from file."""
    try:
        if TASKS_FILE.exists():
            with open(TASKS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"[Beta] Error loading tasks: {e}")
    return {"chat_tasks": {}, "global_tasks": []}

def _save_tasks(tasks):
    """Save tasks to file."""
    try:
        TASKS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(TASKS_FILE, 'w', encoding='utf-8') as f:
            json.dump(tasks, f, indent=2)
    except Exception as e:
        print(f"[Beta] Error saving tasks: {e}")

def _load_snippets():
    """Load snippets from file."""
    try:
        if SNIPPETS_FILE.exists():
            with open(SNIPPETS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"[Beta] Error loading snippets: {e}")
    return {"snippets": []}

def _save_snippets(snippets):
    """Save snippets to file."""
    try:
        SNIPPETS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(SNIPPETS_FILE, 'w', encoding='utf-8') as f:
            json.dump(snippets, f, indent=2)
    except Exception as e:
        print(f"[Beta] Error saving snippets: {e}")

def _load_workflows():
    """Load workflows from file."""
    try:
        if WORKFLOWS_FILE.exists():
            with open(WORKFLOWS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"[Beta] Error loading workflows: {e}")
    return {"workflows": []}

def _save_workflows(workflows):
    """Save workflows to file."""
    try:
        WORKFLOWS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(WORKFLOWS_FILE, 'w', encoding='utf-8') as f:
            json.dump(workflows, f, indent=2)
    except Exception as e:
        print(f"[Beta] Error saving workflows: {e}")

@app.route('/api/beta/tasks', methods=['GET'])
def get_tasks():
    """Get tasks for a chat or global tasks (Beta Feature)."""
    try:
        if not request.headers.get('X-Beta-Mode') == 'true':
            return jsonify({"error": "Beta features not enabled"}), 403

        chat_id = request.args.get('chat_id')
        tasks_data = _load_tasks()

        if chat_id:
            tasks = tasks_data.get('chat_tasks', {}).get(chat_id, [])
        else:
            tasks = tasks_data.get('global_tasks', [])

        return jsonify({"tasks": tasks})

    except Exception as e:
        print(f"[Beta] Error getting tasks: {e}")
        return jsonify({"error": "Failed to get tasks"}), 500

@app.route('/api/beta/tasks/extract/<chat_id>', methods=['POST'])
def extract_tasks_from_chat(chat_id):
    """Extract tasks from a chat conversation (Beta Feature)."""
    try:
        if not request.headers.get('X-Beta-Mode') == 'true':
            return jsonify({"error": "Beta features not enabled"}), 403

        # Load the chat
        chat_data = load_chat(chat_id)
        if not chat_data:
            return jsonify({"error": "Chat not found"}), 404

        # Import task extractor
        from services.task_extractor import get_task_extractor
        extractor = get_task_extractor()

        # Extract tasks
        tasks = extractor.extract_tasks_from_conversation(chat_data.get('messages', []))

        # Save tasks for this chat
        extractor.save_tasks(tasks, chat_id)

        return jsonify({"tasks": tasks, "count": len(tasks)})

    except Exception as e:
        print(f"[Beta] Error extracting tasks: {e}")
        return jsonify({"error": "Failed to extract tasks"}), 500

@app.route('/api/beta/tasks/<task_id>/status', methods=['PUT'])
def update_task_status(task_id):
    """Update task status (Beta Feature)."""
    try:
        if not request.headers.get('X-Beta-Mode') == 'true':
            return jsonify({"error": "Beta features not enabled"}), 403

        data = request.get_json()
        if not data or 'status' not in data:
            return jsonify({"error": "Status is required"}), 400

        chat_id = request.args.get('chat_id')

        from services.task_extractor import get_task_extractor
        extractor = get_task_extractor()
        extractor.update_task_status(task_id, data['status'], chat_id)

        return jsonify({"success": True})

    except Exception as e:
        print(f"[Beta] Error updating task status: {e}")
        return jsonify({"error": "Failed to update task status"}), 500

@app.route('/api/beta/snippets', methods=['GET'])
def get_snippets():
    """Get all snippets (Beta Feature)."""
    try:
        if not request.headers.get('X-Beta-Mode') == 'true':
            return jsonify({"error": "Beta features not enabled"}), 403

        snippets = _load_snippets()
        return jsonify(snippets)

    except Exception as e:
        print(f"[Beta] Error getting snippets: {e}")
        return jsonify({"error": "Failed to get snippets"}), 500

@app.route('/api/beta/snippets', methods=['POST'])
def create_snippet():
    """Create a new snippet (Beta Feature)."""
    try:
        if not request.headers.get('X-Beta-Mode') == 'true':
            return jsonify({"error": "Beta features not enabled"}), 403

        data = request.get_json()
        if not data or not data.get('name') or not data.get('content'):
            return jsonify({"error": "Name and content are required"}), 400

        snippets = _load_snippets()
        snippet_id = str(uuid.uuid4())

        snippet = {
            "id": snippet_id,
            "name": data['name'],
            "description": data.get('description', ''),
            "content": data['content'],
            "category": data.get('category', 'general'),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "usage_count": 0
        }

        snippets["snippets"].append(snippet)
        _save_snippets(snippets)

        return jsonify(snippet), 201

    except Exception as e:
        print(f"[Beta] Error creating snippet: {e}")
        return jsonify({"error": "Failed to create snippet"}), 500

@app.route('/api/beta/snippets/<snippet_id>', methods=['DELETE'])
def delete_snippet(snippet_id):
    """Delete a snippet (Beta Feature)."""
    try:
        if not request.headers.get('X-Beta-Mode') == 'true':
            return jsonify({"error": "Beta features not enabled"}), 403

        snippets = _load_snippets()
        snippets["snippets"] = [s for s in snippets["snippets"] if s["id"] != snippet_id]
        _save_snippets(snippets)

        return jsonify({"success": True})

    except Exception as e:
        print(f"[Beta] Error deleting snippet: {e}")
        return jsonify({"error": "Failed to delete snippet"}), 500

@app.route('/api/beta/summarize/<chat_id>', methods=['POST'])
def summarize_chat(chat_id):
    """Generate a summary of a chat conversation (Beta Feature)."""
    try:
        if not request.headers.get('X-Beta-Mode') == 'true':
            return jsonify({"error": "Beta features not enabled"}), 403

        data = request.get_json() or {}
        format_type = data.get('format', 'paragraph')  # paragraph, bullet_points, key_insights

        # Load the chat
        chat_data = load_chat(chat_id)
        if not chat_data:
            return jsonify({"error": "Chat not found"}), 404

        # Simple summarization logic (placeholder - could integrate with AI model)
        messages = chat_data.get('messages', [])
        user_messages = [m for m in messages if m.get('role') == 'user']
        assistant_messages = [m for m in messages if m.get('role') == 'assistant']

        summary_data = {
            "chat_id": chat_id,
            "chat_name": chat_data.get("name", "Chat"),
            "total_messages": len(messages),
            "user_messages": len(user_messages),
            "assistant_messages": len(assistant_messages),
            "created_at": chat_data.get("created_at", ""),
            "format": format_type
        }

        if format_type == 'paragraph':
            # Generate paragraph summary
            summary_text = f"This conversation contains {len(messages)} messages "
            summary_text += f"between the user and Atlas AI assistant. "

            if user_messages:
                first_user_msg = user_messages[0].get('content', '')[:100]
                summary_text += f"It began with the user asking about: '{first_user_msg}...' "

            if assistant_messages:
                summary_text += f"The assistant provided {len(assistant_messages)} responses "
                summary_text += "covering various topics and questions."

            summary_data["summary"] = summary_text

        elif format_type == 'bullet_points':
            # Generate bullet point summary
            bullets = [
                f"• **Total Messages**: {len(messages)}",
                f"• **User Messages**: {len(user_messages)}",
                f"• **Assistant Responses**: {len(assistant_messages)}",
                f"• **Created**: {chat_data.get('created_at', '')[:10]}"
            ]

            if messages:
                bullets.append(f"• **Started with**: {messages[0].get('content', '')[:80]}...")

            summary_data["summary"] = "\n".join(bullets)

        elif format_type == 'key_insights':
            # Extract key insights (placeholder)
            insights = [
                "• Conversation covers multiple topics",
                "• Assistant provided detailed responses",
                f"• {len(user_messages)} user questions addressed"
            ]
            summary_data["summary"] = "\n".join(insights)

        return jsonify(summary_data)

    except Exception as e:
        print(f"[Beta] Error summarizing chat: {e}")
        return jsonify({"error": "Failed to summarize chat"}), 500


if __name__ == '__main__':
    # Try to load models on startup (with timeout and fallback)
    print("Initializing Atlas AI...")

    # Load Thor 1.2 first (default, improved version from models/thor/thor-1.2 - should load instantly)
    print("Loading Thor 1.2 (default, models/thor/thor-1.2)...")
    try:
        model_loading_progress['thor-1.2']['status'] = 'loading'
        model_loading_progress['thor-1.2']['progress'] = 10
        model_loading_progress['thor-1.2']['message'] = 'Starting Thor 1.2 load...'
        get_model(model_name='thor-1.2')
        model_loading_progress['thor-1.2']['progress'] = 100
        model_loading_progress['thor-1.2']['status'] = 'loaded'
        model_loading_progress['thor-1.2']['message'] = 'Thor 1.2 loaded successfully'
        print("✅ Thor 1.2 loaded successfully (default, loads instantly)")
    except Exception as e:
        print(f"❌ Failed to load Thor 1.2: {e}")
        model_loading_progress['thor-1.2']['status'] = 'failed'
        model_loading_progress['thor-1.2']['message'] = f'Failed to load: {str(e)[:100]}'

    # Try loading Thor 1.0 (stable)
    print("Loading Thor 1.0 (stable)...")
    try:
        model_loading_progress['thor-1.0']['status'] = 'loading'
        model_loading_progress['thor-1.0']['progress'] = 10
        model_loading_progress['thor-1.0']['message'] = 'Starting Thor 1.0 load...'
        get_model(model_name='thor-1.0')
        model_loading_progress['thor-1.0']['progress'] = 100
        model_loading_progress['thor-1.0']['status'] = 'loaded'
        model_loading_progress['thor-1.0']['message'] = 'Thor 1.0 loaded successfully'
        print("✅ Thor 1.0 loaded successfully")
    except Exception as e:
        print(f"❌ Failed to load Thor 1.0: {e}")
        model_loading_progress['thor-1.0']['status'] = 'failed'
        model_loading_progress['thor-1.0']['message'] = f'Failed to load: {str(e)[:100]}'

    # Try loading Thor 1.1 (Qwen3-Thor combined model) in background
    print("Loading Thor 1.1 (latest)...")
    import threading
    def load_thor_1_1():
        progress_key = 'thor-1.1'
        try:
            # Initialize progress tracking
            model_loading_progress[progress_key]['status'] = 'loading'
            model_loading_progress[progress_key]['progress'] = 10
            model_loading_progress[progress_key]['message'] = 'Starting Thor 1.1 load...'
            
            model = get_model(model_name='thor-1.1')  # This maps to qwen3-thor
            
            # Verify model actually loaded and has a valid predict method
            if model is None or not hasattr(model, 'predict'):
                raise Exception("Model returned None or is not functional after loading attempt")
            
            # Test the model with a simple call to ensure it works
            try:
                test_result = model.predict("test", task="text_generation", max_new_tokens=5)
                if not test_result or 'generated_text' not in test_result:
                    raise Exception("Model loaded but failed basic functionality test")
            except Exception as e:
                raise Exception(f"Model loaded but not functional: {e}")
            
            print("✅ Thor 1.1 loaded successfully")
            
            # Mark as loaded ONLY after successful functionality test
            model_loading_progress[progress_key]['progress'] = 100
            model_loading_progress[progress_key]['status'] = 'loaded'
            model_loading_progress[progress_key]['message'] = 'Thor 1.1 loaded successfully'
        except Exception as e:
            print(f"❌ Failed to load Thor 1.1: {e}")
            import traceback
            traceback.print_exc()
            model_loading_progress[progress_key]['status'] = 'failed'
            model_loading_progress[progress_key]['progress'] = 0
            model_loading_progress[progress_key]['message'] = f'Failed to load: {str(e)[:100]}'
    
    # Start loading in background thread so it doesn't block server startup
    thor_1_1_thread = threading.Thread(target=load_thor_1_1, daemon=True)
    thor_1_1_thread.start()

    # Load working AI model directly (skip problematic Thor/Qwen3-4B)
    print("Loading AI model (DialoGPT-medium)...")
    try:
        from transformers import AutoTokenizer, AutoModelForCausalLM
        import torch

        print("Loading AI tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained("microsoft/DialoGPT-medium")
        print("Loading AI model...")
        model = AutoModelForCausalLM.from_pretrained(
            "microsoft/DialoGPT-medium",
            torch_dtype=torch.float16,
            device_map={"": "cpu"}
        )

        # Store as direct model
        model_instances['ai-direct'] = {
            'model': model,
            'tokenizer': tokenizer,
            'type': 'direct'
        }

        print("✅ AI model loaded successfully!")
        print(f"Model has {model.num_parameters():,} parameters")

    except Exception as e:
        print(f"❌ Failed to load AI model: {e}")
        print("Falling back to knowledge-based responses")

    # Check if we have any working models (including direct AI models)
    has_direct_models = any(k for k, v in model_instances.items() if isinstance(v, dict) and v.get('type') == 'direct')
    has_models = any(v for k, v in model_instances.items() if not isinstance(v, dict) or not isinstance(v, dict)) or has_direct_models

    if has_models:
        print("✅ AI models are available!")
        print("Starting Auto-Trainer...")
        try:
            if get_auto_trainer is not None and callable(get_auto_trainer):
                auto_trainer = get_auto_trainer()
                if auto_trainer is not None:
                    auto_trainer.start()
                    print("Auto-Trainer is running in the background!")
                    print("Thor will continuously learn from conversations and improve itself.")
                else:
                    print("⚠️  Auto-trainer not available (running in fallback mode)")
            else:
                print("⚠️  Auto-trainer function not available (running in fallback mode)")
        except Exception as e:
            print(f"❌ Failed to start auto-trainer: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("⚠️  No models loaded - running in fallback mode")
    print()

    # Run Flask app
    port = int(os.environ.get("PORT", 5002))
    print(f"🚀 Starting Flask server on port {port}")
    app.run(debug=True, host='0.0.0.0', port=port)

