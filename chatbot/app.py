"""
Flask backend for Atlas AI - Thor 1.0 Model Interface
"""
from flask import Flask, render_template, request, jsonify, session
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

# Add parent directories to path for imports
BASE_DIR = Path(__file__).parent.resolve()
ATLAS_ROOT = BASE_DIR.parent
THOR_DIR = ATLAS_ROOT / "thor-1.0"

# Ensure THOR_DIR is first for imports
thor_path = str(THOR_DIR)
if thor_path in sys.path:
    sys.path.remove(thor_path)
sys.path.insert(0, thor_path)

try:
    import torch  # type: ignore
except Exception:  # pragma: no cover
    torch = None
from services import (
    get_auto_trainer,
    get_tracker,
    get_greetings_handler,
    get_common_sense_handler,
    get_research_engine,
    get_query_intent_analyzer,
    get_semantic_scorer,
    get_creative_generator,
    get_image_processor,
    get_code_handler,
    get_response_cleaner,
)
from brain import BrainConnector
from biographical_handler import synthesize_knowledge, clean_promotional_text
from refinement import (
    get_question_normalizer,
    get_intent_router,
    get_knowledge_reranker,
    get_answer_refiner,
    get_clarifier,
    verify_response_accuracy,
)
from handlers import ImageHandler, ResponseFormatter, MarkdownHandler
from handlers.image_handler import get_image_handler
from handlers.response_formatter import get_response_formatter
from handlers.markdown_handler import get_markdown_handler
from formatting import get_final_response_formatter
import time
import random

UI_TEMPLATE_DIR = BASE_DIR / "ui" / "templates"
UI_STATIC_DIR = BASE_DIR / "ui" / "static"

app = Flask(__name__, template_folder=str(UI_TEMPLATE_DIR), static_folder=str(UI_STATIC_DIR))
app.secret_key = os.urandom(24)
CORS(app)

# Configuration - updated paths for new structure
# Vercel/serverless environments have read-only project dirs; use /tmp for writes.
DATA_ROOT = BASE_DIR
if os.environ.get("VERCEL") == "1" or os.environ.get("ATLAS_DEPLOYMENT_MODE") in {"serverless", "lite"}:
    DATA_ROOT = Path("/tmp/atlas-ai")
    try:
        DATA_ROOT.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass

MODEL_DIR = str(THOR_DIR / "models")
TOKENIZER_DIR = str(THOR_DIR / "models")
CONFIG_PATH = str(THOR_DIR / "config" / "config.yaml")
CHATS_DIR = str(DATA_ROOT / "chats")
CONVERSATIONS_DIR = str(DATA_ROOT / "conversations")
PROJECTS_DIR = str(DATA_ROOT / "projects")
HISTORY_DIR = str(DATA_ROOT / "history")
THOR_RESULT_SETTER_FILE = str(BASE_DIR / "thor_result_setter.json")

# Gems (custom sub-models)
GEMS_DIR = DATA_ROOT / "gems"
GEMS_FILE = GEMS_DIR / "gems.json"

# Ensure directories exist
os.makedirs(CHATS_DIR, exist_ok=True)
os.makedirs(CONVERSATIONS_DIR, exist_ok=True)
os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(PROJECTS_DIR, exist_ok=True)
os.makedirs(HISTORY_DIR, exist_ok=True)
os.makedirs(str(GEMS_DIR), exist_ok=True)

if not GEMS_FILE.exists():
    try:
        with open(GEMS_FILE, "w", encoding="utf-8") as f:
            json.dump({"gems": []}, f, indent=2)
    except Exception:
        pass


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
            
            # Extract meaningful paragraphs (skip very short lines)
            lines = [line.strip() for line in text.split("\n") if len(line.strip()) > 20]
            text = " ".join(lines[:50])  # Take first 50 meaningful lines
            
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
    'thor-1.0': None
}

# Brain connector
brain_connector = BrainConnector()


def check_result_setter(query, model_name='thor-1.0'):
    """
    Check if the query has a pre-set answer in the Result Setter.
    Returns the authoritative answer if found, None otherwise.
    
    Uses fuzzy matching to handle variations in how questions are asked.
    """
    try:
        # Single source of truth now (Thor only); keep signature for compatibility
        rs_file = THOR_RESULT_SETTER_FILE
        
        if not os.path.exists(rs_file):
            return None
        
        with open(rs_file, 'r', encoding='utf-8') as f:
            qa_data = json.load(f)
        
        qa_pairs = qa_data.get('qa_pairs', [])
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


def get_model(model_name='thor-1.0', force_reload=False):
    """Get or initialize the model instance.
    
    Args:
        model_name: only 'thor-1.0' is supported
        force_reload: Force reload of the model
    """
    global model_instances
    
    # Validate model name
    if model_name not in model_instances:
        model_name = 'thor-1.0'
    
    if model_instances[model_name] is None or force_reload:
        # In serverless/lite deployments we may not ship torch/model weights.
        if torch is None:
            return None
        model_dir = MODEL_DIR
        config_file = CONFIG_PATH
        
        model_path = os.path.join(model_dir, "final_model.pt")
        tokenizer_path = os.path.join(model_dir, "tokenizer.json")
        
        if os.path.exists(model_path) and os.path.exists(tokenizer_path):
            try:
                # Lazy import to avoid hard dependency in lightweight deployments.
                from inference import AllRounderInference  # type: ignore
                model_instances[model_name] = AllRounderInference(
                    model_path=model_path,
                    tokenizer_path=tokenizer_path,
                    config_path=config_file
                )
                if force_reload:
                    print(f"Model {model_name} reloaded successfully (auto-trained)")
                else:
                    print(f"Model {model_name} loaded successfully")
            except Exception as e:
                print(f"Error loading model {model_name}: {e}")
                model_instances[model_name] = None
        else:
            print(f"Model files not found for {model_name}. Expected: {model_path}, {tokenizer_path}")
    
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
    """Evaluate simple math expressions safely"""
    import re
    import math
    
    # Remove common question words and normalize
    expr = expression.lower().strip()
    
    # Patterns: "what is 2 + 2", "calculate 10 * 5", "2+2", etc.
    # Extract math expression
    math_patterns = [
        r'what\s+is\s+(.+?)(?:\?|$)',
        r'calculate\s+(.+?)(?:\?|$)',
        r'compute\s+(.+?)(?:\?|$)',
        r'solve\s+(.+?)(?:\?|$)',
        r'^\s*([0-9+\-*/().\s]+)\s*$',  # Pure math expression
        r'=\s*([0-9+\-*/().\s]+)',  # "equals ..."
    ]
    
    math_expr = None
    for pattern in math_patterns:
        match = re.search(pattern, expr)
        if match:
            math_expr = match.group(1).strip()
            break
    
    if not math_expr:
        # Check if it looks like a math expression directly
        if re.match(r'^[\d+\-*/().\s]+$', expr):
            math_expr = expr
        else:
            return None
    
    # Clean and validate the expression
    math_expr = math_expr.replace(' ', '')
    
    # Only allow safe characters: digits, operators, parentheses, decimal point
    if not re.match(r'^[\d+\-*/().]+$', math_expr):
        return None
    
    # Check for dangerous operations (only allow basic math)
    if any(op in math_expr for op in ['__', 'import', 'exec', 'eval', 'open']):
        return None
    
    try:
        # Safely evaluate the expression
        # Replace common math functions
        math_expr = math_expr.replace('^', '**')  # Power operator
        
        # Evaluate using a safe method
        result = eval(math_expr, {"__builtins__": {}}, {"math": math})
        
        # Return formatted result
        if isinstance(result, float):
            if result.is_integer():
                return int(result)
            return round(result, 10)
        return result
    except:
        return None


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


@app.route('/')
def index():
    """Render the main chat interface."""
    return render_template('index.html')


@app.route('/dev-atlas')
def dev_atlas():
    """Render the minimal Dev Atlas interface."""
    return render_template('dev_atlas.html')


@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat messages."""
    try:
        data = request.json
        message = data.get('message', '').strip()
        chat_id = data.get('chat_id')
        task = data.get('task', 'text_generation')  # Default to text generation for chat
        think_deeper = data.get('think_deeper', False)  # Think deeper mode
        code_mode = data.get('code_mode', False)  # Code mode
        code_language = data.get('code_language', 'python')  # Code language (python, javascript, html)
        image_data = data.get('image_data')  # Image data if attached
        requested_model = (data.get('model') or 'thor-1.0').strip()
        requested_tone = (data.get('tone') or 'normal').strip()
        model_name = 'thor-1.0'  # Underlying model (Thor) for inference
        gem_config = None
        gem_knowledge = []
        model_label_for_ui = "Thor 1.0"

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
        
        # Handle image if provided
        if image_data:
            image_info = image_processor.process_image(image_data, f"image_{chat_id}.png")
            message = f"{message} [Image processed: {image_processor.describe_image(image_info)}]"
            print(f"[Image processed] {image_info.get('description', 'Image processed')}")
        
        # Get conversation context (previous messages)
        conversation_context = chat_data.get("messages", [])[-10:]  # Last 10 messages for context
        
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
        
        normalized = normalizer.normalize(message, conversation_context)
        normalized_message = normalized.get("normalized_query", message)
        
        # Initialize common sense handler
        common_sense_handler = get_common_sense_handler()
        
        # Initialize follow-up detection variables early (accessible everywhere)
        message_lower = normalized_message.lower().strip()
        is_tell_me_more = 'tell me more' in message_lower or ('more' in message_lower and len(message.split()) <= 3)
        
        # QUICK PATH: short acknowledgments - avoid pulling random context/knowledge
        short_ack_terms = {"cool", "ok", "okay", "k", "thanks", "thank you", "nice", "great", "awesome", "got it"}
        if response is None and len(message_lower.split()) <= 2 and message_lower in short_ack_terms:
            response = "👍 Got it. What would you like to do next?"
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
        
        # Check if it's a math question (simple calculations) - only if no Q&A answer found
        if response is None:
            math_result = _evaluate_math(message)
            if math_result is not None:
                response = f"The answer is: **{math_result}**"
                print(f"[Math] Calculated: {message} = {math_result}")
        
        if response is None:
            # Check for identity questions first (before common sense/research)
            identity_questions = [
                "who are you", "what are you", "who is thor", "what is thor",
                "tell me about yourself", "introduce yourself", "what can you do",
                "what do you do", "who am i talking to", "what's your name"
            ]
            
            if any(q in message_lower for q in identity_questions):
                response = """I'm **Thor 1.0**, your AI assistant powered by Atlas! 

I'm designed to help you with:
- **Coding**: Python, JavaScript, and more
- **Learning**: I continuously learn from our conversations and web research
- **Problem Solving**: Ask me questions and I'll do my best to help
- **Creative Thinking**: Use "Think Deeper" mode for more comprehensive responses

I'm always learning and improving through our conversations. How can I help you today?"""
                print(f"[Identity question] Responding with introduction")
        
        if response is None and common_sense_handler.should_skip_search(message):
            # Check for compliments, praise, or casual conversation
            response = common_sense_handler.get_response(message, conversation_context)
            if response:
                print(f"[Common Sense] Responding to compliment/casual conversation: {response[:50]}...")
            else:
                # Fallback if handler doesn't recognize it
                response = "Thank you! How can I help you?"
        
        if response is None:
            if greetings_handler.is_greeting(message):
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
                
                # Do not blend unrelated context for fresh questions; keep the user's prompt primary
                if not is_follow_up:
                    contextual_message = normalized_message
                
                context_query = (contextual_message or message).strip()
                if not context_query:
                    context_query = message
                
                # Use query intent analyzer for intelligent query understanding
                intent_analyzer = get_query_intent_analyzer()
                query_intent = intent_analyzer.analyze(context_query) or {}
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
                
                # Check if query should force web search
                if query_intent.get('should_search_web'):
                    print(f"[Query Intent] {query_intent.get('intent', 'unknown').upper()} query detected, forcing web search: {message}")
                    knowledge = list(gem_knowledge) if gem_knowledge else []  # Keep gem sources, force web search otherwise
                else:
                    if is_recipe_query:
                        # Recipe queries should always search web, don't check brain first
                        print(f"[Recipe Query] Detected recipe query: {message}")
                        knowledge = list(gem_knowledge) if gem_knowledge else []  # Keep gem sources, force web search otherwise
                    else:
                        knowledge = brain_connector.get_relevant_knowledge(contextual_message)
                        if gem_knowledge:
                            knowledge = list(gem_knowledge) + (knowledge or [])
                
                # Detect relationship/comparison questions - always research these
                is_relationship_query = any(phrase in context_query.lower() for phrase in [
                    'relationship between', 'relationship of', 'connection between',
                    'difference between', 'compare', 'comparison between', 'versus', 'vs',
                    'similarities between', 'how does', 'how do', 'how are', 'how is',
                    'what is the relationship', 'what is the connection'
                ])
                
                # In think deeper mode, always research for comprehensive information
                # For "tell me more" follow-ups, don't research if we already have knowledge from previous query
                if is_tell_me_more and knowledge and len(knowledge) > 0:
                    needs_research = False  # Use existing knowledge for follow-up
                    print(f"[Context] 'Tell me more' detected with existing knowledge, skipping research")
                else:
                    needs_research = think_deeper or is_recipe_query or research_engine.needs_research(context_query) or is_relationship_query or not knowledge or len(knowledge) == 0
                
                if needs_research:
                    # Use contextual message for research (includes follow-up context)
                    search_query = context_query
                    search_type = "relationship query" if is_relationship_query else ("recipe query" if is_recipe_query else "topic not in brain")
                    print(f"[Research] {search_type.upper()}, PRIORITIZING Google search: {search_query}")
                    research_done = True
                    try:
                        research_knowledge = research_engine.search_and_learn(search_query)
                        if research_knowledge:
                            print(f"[Research] Learned {len(research_knowledge)} items from Google")
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
                    model = get_model(model_name=model_name)
                else:
                    model = None  # Skip model if we already have a response
                
                if model is None and response is None:
                    # Try to use brain knowledge for response (or newly researched knowledge)
                    try:
                        # For "tell me more" follow-ups, try to get knowledge from previous conversation first
                        if is_tell_me_more and conversation_context and len(conversation_context) > 0:
                            # Look for the previous topic in recent messages
                            for msg in reversed(conversation_context[-6:]):
                                if msg.get('role') == 'user' and len(msg.get('content', '').split()) > 3:
                                    prev_query = msg.get('content', '')
                                    # Try to get knowledge about the previous topic
                                    prev_knowledge = brain_connector.get_relevant_knowledge(prev_query)
                                    if gem_knowledge:
                                        prev_knowledge = list(gem_knowledge) + (prev_knowledge or [])
                                    if prev_knowledge:
                                        knowledge = prev_knowledge
                                        print(f"[Context] Using knowledge from previous query: {prev_query[:50]}...")
                                        break
                        
                        # If we don't have knowledge yet, try brain again (but only if we haven't already researched)
                        if not knowledge and not research_done:
                            knowledge = brain_connector.get_relevant_knowledge(contextual_message)
                            if gem_knowledge:
                                knowledge = list(gem_knowledge) + (knowledge or [])
                        # If we researched but got no results, use the research_knowledge directly even if empty
                        elif not knowledge and research_done and research_knowledge:
                            knowledge = research_knowledge
                        
                        # Rerank any knowledge we have to prioritize the most relevant/ recent
                        # BUT preserve gem sources at the front (they have priority=1)
                        if knowledge:
                            gem_sources = [k for k in knowledge if k.get("source") == "gem_source" or k.get("priority") == 1]
                            other_knowledge = [k for k in knowledge if k.get("source") != "gem_source" and k.get("priority") != 1]
                            if other_knowledge:
                                other_knowledge = knowledge_reranker.rerank(context_query, other_knowledge, query_intent)
                            knowledge = gem_sources + other_knowledge  # Gem sources always first
                            print(f"[Refinement] Reranked knowledge: {len(gem_sources)} gem sources + {len(other_knowledge)} other items")

                        # Early clarification if we still have nothing confident
                        if response is None and (not knowledge or len(knowledge) == 0):
                            clarification = clarifier.build_clarification(normalized_message, query_intent, knowledge_available=False)
                            if clarification:
                                response = clarification
                        
                        if think_deeper:
                            # Think deeper mode - perform comprehensive multi-step reasoning
                            print("[Think Deeper] Starting deep reasoning process...")
                            
                            # Step 1: Always research the topic to get comprehensive information
                            print("[Think Deeper] Step 1: Researching topic comprehensively...")
                            research_knowledge = research_engine.search_and_learn(context_query)
                            
                            # Step 2: Get additional knowledge from brain
                            print("[Think Deeper] Step 2: Gathering knowledge from brain...")
                            brain_knowledge = brain_connector.get_relevant_knowledge(context_query)
                            if gem_knowledge:
                                brain_knowledge = list(gem_knowledge) + (brain_knowledge or [])
                            
                            # Step 3: Combine and analyze all knowledge sources
                            print("[Think Deeper] Step 3: Synthesizing information...")
                            all_knowledge = []
                            if research_knowledge:
                                all_knowledge.extend(research_knowledge)
                            if brain_knowledge:
                                all_knowledge.extend(brain_knowledge)
                            
                            # Step 4: Use semantic scorer to filter and rank
                            semantic_scorer = get_semantic_scorer()
                            intent_analyzer = get_query_intent_analyzer()
                            query_intent = intent_analyzer.analyze(context_query) or {}
                            
                            # Filter out greeting patterns and low-quality content
                            filtered_knowledge = [k for k in all_knowledge 
                                             if 'Response pattern for greeting' not in k.get('content', '')
                                             and 'Use appropriate greeting' not in k.get('content', '')
                                             and k.get('source', '') != 'greetings_handler'
                                             and not k.get('content', '').startswith('Response pattern')
                                             and len(k.get('content', '').strip()) > 20]
                            
                            if filtered_knowledge:
                                # Use moderate threshold to get more comprehensive coverage
                                scored_knowledge = semantic_scorer.filter_knowledge_by_relevance(
                                    context_query,
                                    filtered_knowledge,
                                    query_intent,
                                    min_score=0.3  # Moderate threshold to get comprehensive info
                                )
                                
                                if scored_knowledge:
                                    # Sort by score and get top knowledge items
                                    scored_knowledge.sort(key=lambda x: x[0], reverse=True)
                                    top_knowledge = [item for _, item in scored_knowledge[:5]]  # Get top 5
                                    refinement_knowledge_used = top_knowledge
                                    
                                    # Step 5: Build comprehensive structured response
                                    print("[Think Deeper] Step 4: Building comprehensive response...")
                                    response_parts = []
                                    
                                    # Main response
                                    if top_knowledge:
                                        main_content = top_knowledge[0].get('content', '').strip()
                                        if main_content and len(main_content) > 30:
                                            # Clean promotional text
                                            main_content = clean_promotional_text(main_content)
                                            response_parts.append(f"**Deep Analysis:**\n\n{main_content[:600]}")
                                            
                                            # Add related perspectives and connections
                                            if len(top_knowledge) > 1:
                                                response_parts.append("\n\n**Additional Perspectives:**")
                                                for i, k in enumerate(top_knowledge[1:4], 1):  # Up to 3 more
                                                    additional = k.get('content', '').strip()
                                                    if additional and len(additional) > 30:
                                                        # Clean promotional text
                                                        additional = clean_promotional_text(additional)
                                                        # Truncate if too long
                                                        if len(additional) > 300:
                                                            additional = additional[:297] + "..."
                                                        response_parts.append(f"\n\n{i}. {additional}")
                                            
                                            # Add connections if we have multiple sources
                                            if len(top_knowledge) > 1:
                                                response_parts.append("\n\n**Key Connections:**")
                                                unique_sources = set(k.get('source', 'unknown') for k in top_knowledge[:3])
                                                if len(unique_sources) > 1:
                                                    response_parts.append("These perspectives come from multiple sources, providing a more comprehensive understanding.")
                                            
                                            response = "".join(response_parts)
                                        else:
                                            response = f"**Deep Analysis:**\n\nI'm thinking deeply about '{message}'. Let me provide a comprehensive answer based on my research and knowledge."
                                    else:
                                        response = f"**Deep Analysis:**\n\nI'm thinking deeply about '{message}'. Let me provide a comprehensive answer based on my research and knowledge."
                                else:
                                    # No highly relevant knowledge, but we researched - provide what we found
                                    if research_knowledge:
                                        refinement_knowledge_used = research_knowledge
                                        response = f"**Deep Analysis:**\n\nI've researched '{message}' and found some information. "
                                        if len(research_knowledge) > 0:
                                            content = research_knowledge[0].get('content', '')
                                            cleaned_content = clean_promotional_text(content)
                                            response += cleaned_content[:500]
                                        else:
                                            response += "While I'm continuously learning, I want to make sure I give you accurate information. Could you tell me more specifically what you'd like to know?"
                                    else:
                                        response = f"**Deep Analysis:**\n\nI'm thinking deeply about '{message}'. While I'm continuously learning, I want to make sure I give you accurate information. Could you tell me more specifically what you'd like to know about this topic?"
                            else:
                                # No knowledge available, but we researched - use research results
                                if research_knowledge and len(research_knowledge) > 0:
                                    refinement_knowledge_used = research_knowledge
                                    content = research_knowledge[0].get('content', '')
                                    cleaned_content = clean_promotional_text(content)
                                    response = f"**Deep Analysis:**\n\n{cleaned_content[:600]}"
                                else:
                                    response = f"**Deep Analysis:**\n\nI'm thinking deeply about '{message}'. I'm continuously learning and improving. What specific aspect would you like me to explore?"
                        else:
                            # Initialize filtered_knowledge
                            filtered_knowledge = []
                            
                            if knowledge:
                                # Filter out greeting patterns from knowledge
                                for k in knowledge:
                                    content = k.get('content', '')
                                    source = k.get('source', '')
                                    if 'Response pattern for greeting' in content:
                                        continue
                                    if 'Use appropriate greeting' in content:
                                        continue
                                    if source == 'greetings_handler':
                                        continue
                                    if content.startswith('Response pattern'):
                                        continue
                                    filtered_knowledge.append(k)
                            
                            if filtered_knowledge:
                                # Use semantic scorer to ensure relevance before responding
                                semantic_scorer = get_semantic_scorer()
                                scored_knowledge = semantic_scorer.filter_knowledge_by_relevance(
                                    context_query,
                                    filtered_knowledge,
                                    query_intent,
                                    min_score=0.25  # Higher threshold for final response
                                )
                                
                                # Use scored knowledge if available, otherwise use original
                                if scored_knowledge:
                                    filtered_knowledge = [item for _, item in scored_knowledge]
                                else:
                                    # If nothing passed semantic scoring and strict match required, 
                                    # but we already researched, use the knowledge anyway (lower threshold)
                                    if query_intent.get('strict_match_required') and research_done:
                                        print(f"[Semantic Filter] Strict match required but no high-scoring knowledge found, using research results with lower threshold")
                                        # Re-score with lower threshold
                                        scored_knowledge = semantic_scorer.filter_knowledge_by_relevance(
                                            context_query,
                                            filtered_knowledge,
                                            query_intent,
                                            min_score=0.15  # Lower threshold for researched content
                                        )
                                        if scored_knowledge:
                                            filtered_knowledge = [item for _, item in scored_knowledge]
                                        else:
                                            # Still use the knowledge even if low score, since we researched it
                                            print(f"[Semantic Filter] Using researched knowledge despite low score")
                                            filtered_knowledge = filtered_knowledge[:1]  # Use at least the first item
                                    elif query_intent.get('strict_match_required'):
                                        print(f"[Semantic Filter] Strict match required but no high-scoring knowledge found, forcing web search")
                                        filtered_knowledge = []
                                
                                if filtered_knowledge:
                                    refinement_knowledge_used = filtered_knowledge
                                    # Add human-like awareness: check conversation context for natural flow
                                    is_follow_up = len(conversation_context) > 2
                                    is_continuation = any(
                                        prev_msg.get('role') == 'user' and 
                                        len(prev_msg.get('content', '').split()) < 8
                                        for prev_msg in conversation_context[-3:]
                                    )
                                    
                                    # Check if this is a relationship question
                                    is_relationship = any(phrase in context_query.lower() for phrase in [
                                        'relationship between', 'relationship of', 'connection between',
                                        'difference between', 'compare', 'versus', 'vs'
                                    ])
                                    
                                    if is_relationship and len(filtered_knowledge) > 1:
                                        # For relationship questions, synthesize information from multiple sources
                                        response = f"Let me break down the relationship between these concepts for you.\n\n"
                                        
                                        # Combine relevant knowledge items
                                        combined_content = []
                                        for k in filtered_knowledge[:5]:  # Use up to 5 sources
                                            content = k.get('content', '').strip()
                                            if content and len(content) > 30:
                                                # Clean promotional text
                                                cleaned = clean_promotional_text(content)
                                                if cleaned:
                                                    combined_content.append(cleaned)
                                        
                                        if combined_content:
                                            response += " ".join(combined_content[:3])  # First 3 items
                                            if len(combined_content) > 3:
                                                response += f"\n\nThese concepts are interconnected and often influence each other in meaningful ways."
                                        else:
                                            content = filtered_knowledge[0].get('content', '')
                                            cleaned_content = clean_promotional_text(content)
                                            response += cleaned_content[:400]
                                    else:
                                        # Regular questions - synthesize knowledge instead of using verbatim
                                        # Try to synthesize multiple knowledge items into a coherent response
                                        synthesized = synthesize_knowledge(context_query, filtered_knowledge, query_intent)
                                        
                                        if synthesized:
                                            # Add natural conversation starters based on context
                                            if is_follow_up:
                                                starters = [
                                                    "Sure! ",
                                                    "Absolutely. ",
                                                    "Great question! ",
                                                    "I'd be happy to explain. ",
                                                    ""
                                                ]
                                                starter = random.choice(starters)
                                            else:
                                                starter = ""
                                            
                                            response = starter + synthesized
                                        else:
                                            # Fallback to single knowledge item if synthesis fails
                                            top_knowledge = filtered_knowledge[0]
                                            content = top_knowledge.get('content', '').strip()
                                            
                                            # Add natural conversation starters based on context
                                            if is_follow_up:
                                                starters = [
                                                    "Sure! ",
                                                    "Absolutely. ",
                                                    "Great question! ",
                                                    "I'd be happy to explain. ",
                                                    ""
                                                ]
                                                starter = random.choice(starters)
                                            else:
                                                starter = ""
                                            
                                            # Clean promotional text from content
                                            cleaned_content = clean_promotional_text(content)
                                            
                                            # For definition queries, use clearer format
                                            if query_intent.get('intent') == 'definition':
                                                entity = query_intent.get('entity', message)
                                                # Format as direct definition
                                                if cleaned_content:
                                                    response = f"{starter}**{entity.title()}** is {cleaned_content[:400].lstrip('is ').lstrip('Is ')}"
                                                else:
                                                    response = f"{starter}**{entity.title()}** {content[:400]}"
                                            else:
                                                # For other queries, provide direct answer
                                                if cleaned_content:
                                                    response = f"{starter}{cleaned_content[:400]}"
                                                else:
                                                    response = f"{starter}{content[:400]}"
                            else:
                                # If we already researched but got no usable results, use the research results anyway
                                if research_done and research_knowledge and len(research_knowledge) > 0:
                                    print(f"[Fallback] Using research results despite filtering: {len(research_knowledge)} items")
                                    # Synthesize research results instead of using verbatim
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
                                
                                # If still no response, use friendly fallback
                                if not response:
                                    # Friendly fallback response with more awareness
                                    # Check if this seems like a question
                                    is_question = message.strip().endswith('?') or any(
                                        word in message.lower() for word in ['what', 'how', 'why', 'when', 'where', 'who', 'which', 'can', 'could', 'should', 'would']
                                    )
                                    
                                    if is_question:
                                        if research_done:
                                            response = f"I've searched for information about '{message}', but I'm having trouble finding a clear answer. Could you tell me more specifically what you'd like to know about this topic?"
                                        else:
                                            response = f"That's an interesting question about '{message}'. Let me think about that for a moment. While I'm processing this, I'm continuously learning from our conversations and web research to give you better answers. Could you tell me a bit more about what specifically you'd like to know?"
                                    else:
                                        if research_done:
                                            response = f"I've searched for information about '{message}', but I'm having trouble finding relevant details. What would you like to explore about this topic?"
                                        else:
                                            response = f"I understand you're mentioning '{message}'. That's something I'm learning more about through our conversations and research. What would you like to explore about this topic?"
                    except Exception as e:
                        print(f"Error using brain knowledge: {e}")
                        response = f"I understand your message. I'm continuously learning. While my full model is training, I can help with basic questions. What would you like to know?"
                else:
                    # Generate response using model with conversation context
                    try:
                        # Build contextual input with previous messages
                        contextual_input = message
                        if conversation_context and len(conversation_context) > 0:
                            # Include last 2-3 exchanges for context
                            recent_context = []
                            for msg in conversation_context[-6:]:
                                role = msg.get('role', '')
                                content = msg.get('content', '')
                                if role == 'user':
                                    recent_context.append(f"User: {content}")
                                elif role == 'assistant':
                                    recent_context.append(f"Assistant: {content}")
                            
                            if recent_context:
                                contextual_input = "\n".join(recent_context[-4:]) + f"\nUser: {message}\nAssistant:"
                                print(f"[Model] Using conversation context ({len(recent_context)} previous messages)")
                        
                        # Apply Gem instructions as a lightweight "system prompt" prefix.
                        tone_line = _tone_profile(effective_tone)
                        if gem_config and (gem_config.get("instructions") or "").strip():
                            gem_name = (gem_config.get("name") or "Gem").strip()
                            gem_instr = (gem_config.get("instructions") or "").strip()
                            
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
                            
                            prefix = f"System: {tone_line} You are {gem_name}. {gem_instr}{gem_sources_context}".strip()
                            contextual_input = prefix + "\n\n" + contextual_input
                            print(f"[Gem] Using gem '{gem_name}' with {len(gem_knowledge or [])} source(s) in context")
                        else:
                            # Global tone (no gem): still guide style strongly
                            contextual_input = f"System: {tone_line}\n\n" + contextual_input

                        result = model.predict(contextual_input, task=task)
                        
                        # Get response cleaner for validation
                        response_cleaner = get_response_cleaner()
                        
                        # Extract response based on task
                        if task == 'text_generation' and 'generated_text' in result:
                            response = result['generated_text']
                            # Validate response - use response_cleaner's corruption detection
                            if response:
                                # Use comprehensive corruption detection
                                if response_cleaner.is_corrupted(response):
                                    print(f"[Model] Detected corrupted response, rejecting: '{response[:50]}...'")
                                    response = None
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
                                        # Check for nonsensical patterns like "what is what is is"
                                        elif len(words) >= 4 and any(words[i] == words[i+2] and words[i+1] == words[i+3] 
                                               for i in range(len(words) - 3)):
                                            print(f"[Model] Detected nonsensical pattern, rejecting")
                                            response = None
                                
                                # If model generated something valid, clean it before using
                                if response and len(response.strip()) > 10:
                                    # Apply cleaning to fix minor grammar issues
                                    response = response_cleaner.clean_response(response, message)
                                    if response and len(response.strip()) > 10:
                                        print(f"[Model] Generated response using own knowledge ({len(response)} chars)")
                                    else:
                                        response = None
                                else:
                                    response = None
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
                            # If model doesn't have good response, try to use its own processing
                            response = "I understand your message. Let me think about that..."
                        
                        # Enhance response with brain knowledge only if model's response is weak
                        try:
                            if not response or len(response.strip()) < 20:
                                # Model response is too short or corrupted, use knowledge directly
                                print("[Response] Model response invalid, using knowledge")
                                
                                # First, check if we already researched and have results
                                if research_done and research_knowledge and len(research_knowledge) > 0:
                                    print(f"[Response] Using research results: {len(research_knowledge)} items")
                                    # Synthesize research results instead of using verbatim
                                    intent_analyzer = get_query_intent_analyzer()
                                    query_intent = intent_analyzer.analyze(context_query) or {}
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
                                        query_intent = intent_analyzer.analyze(context_query) or {}
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
                                    query_intent = intent_analyzer.analyze(context_query) or {}
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
                                
                                # Last resort fallback message
                                if not response:
                                    if research_done:
                                        response = f"I've searched for information about '{message}', but I'm having trouble finding a clear answer. Could you tell me more specifically what you'd like to know about this topic?"
                                    else:
                                        response = f"I understand you're asking about '{message}'. Let me search for more information about that."
                            elif think_deeper:
                                # Think deeper mode with model response - enhance comprehensively
                                print("[Think Deeper] Enhancing model response with deep analysis...")
                                
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
                                    knowledge = brain_connector.get_relevant_knowledge(context_query)
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
                                    query_intent = intent_analyzer.analyze(context_query) or {}
                                    
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
                                    query_intent = intent_analyzer.analyze(context_query) or {}
                                    
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
            response = answer_refiner.refine(response, refinement_knowledge_used, query_intent or {}, model_label_for_ui)

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
        
        # Generate chat name if this is the first exchange
        chat_name = None
        if len(chat_data["messages"]) == 2:  # Just added user + assistant
            chat_name = generate_chat_name(message, response)
        
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
            # Ensure chat_data has the right structure for auto-trainer
            conversation_data = {
                "chat_id": chat_data.get("chat_id"),
                "created_at": chat_data.get("created_at"),
                "messages": chat_data.get("messages", [])
            }
            auto_trainer.add_conversation(conversation_data)
            
            # Record conversation in tracker
            tracker = get_tracker()
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
                final_formatter = get_final_response_formatter()
                response = final_formatter.format(
                    response,
                    user_message=message,
                    hints={
                        "task": task,
                        "tone": effective_tone if 'effective_tone' in locals() else (data.get('tone') or 'normal'),
                    },
                )
            except Exception as e:
                print(f"[Final Formatter] Error: {e}")

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
        
        return jsonify({
            "response": response,
            "chat_id": chat_id,
            "task": task
        }), 200
            
    except Exception as e:
        print(f"❌ ERROR in chat endpoint: {e}")
        import traceback
        traceback.print_exc()
        # Get detailed error information
        error_type = type(e).__name__
        error_msg = str(e) if str(e) else "Internal server error"
        
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


@app.route('/api/model/status', methods=['GET'])
def model_status():
    """Get model status."""
    thor_model = get_model(model_name='thor-1.0')
    
    # Get available tasks from the model
    thor_tasks = []
    if thor_model and hasattr(thor_model, 'model') and hasattr(thor_model.model, 'task_heads'):
        thor_tasks = list(thor_model.model.task_heads.keys())
    
    return jsonify({
        "models": {
            "thor-1.0": {
                "loaded": thor_model is not None,
                "available_tasks": thor_tasks
            }
        },
        "available_models": ["thor-1.0"]
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


if __name__ == '__main__':
    # Try to load models on startup
    print("Initializing Atlas AI...")
    print("Loading Thor 1.0...")
    get_model(model_name='thor-1.0')
    
    # Start auto-trainer
    print("Starting Auto-Trainer...")
    auto_trainer = get_auto_trainer()
    auto_trainer.start()
    print("Auto-Trainer is running in the background!")
    print("Thor will continuously learn from conversations and improve itself.")
    print()
    
    # Run Flask app
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)

