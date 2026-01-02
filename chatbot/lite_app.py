"""Lite Flask app for serverless deployments (e.g., Vercel).

This version intentionally avoids importing `thor-1.0/` so it can run when the
deployment root is `chatbot/` only.

Features (subset of full app):
- Main UI (/)
- /api/chat with multi-engine research + images + Gems
- /api/gems CRUD (stored under /tmp on Vercel)

Note: This is a best-effort deployment mode. The full local experience remains
in `chatbot/app.py`.
"""

from __future__ import annotations

import json
import os
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from flask import Flask, jsonify, render_template, request
from flask_cors import CORS

# Ensure proper path resolution for imports
import sys
BASE_DIR = Path(__file__).parent.resolve()
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Import with individual error handling for each module (more resilient)
def _safe_import(module_path, function_name, fallback_factory=None):
    """Safely import a function, with fallback if needed."""
    try:
        module = __import__(module_path, fromlist=[function_name])
        return getattr(module, function_name)
    except (ImportError, AttributeError) as e:
        print(f"[lite_app] Failed to import {module_path}.{function_name}: {e}")
        if fallback_factory:
            print(f"[lite_app] Using fallback for {function_name}")
            return fallback_factory()
        raise

# Import each module individually with fallbacks
try:
    from handlers.image_handler import get_image_handler
except Exception as e:
    print(f"[lite_app] Image handler import failed: {e}")
    def get_image_handler(*args, **kwargs):
        class FallbackImageHandler:
            def extract_image_request(self, msg): return None
            def get_image(self, subject, size, variant=None): return ("", "placeholder")
            def format_image_response(self, subject, url, is_trainx=False): return f"Image: {subject}"
        return FallbackImageHandler()

try:
    from refinement.answer_refiner import get_answer_refiner
except Exception as e:
    print(f"[lite_app] Answer refiner import failed: {e}")
    def get_answer_refiner(*args, **kwargs):
        class FallbackRefiner:
            def refine(self, text, **kwargs): return text
        return FallbackRefiner()

try:
    from refinement.accuracy_checker import verify_response_accuracy
except Exception as e:
    print(f"[lite_app] Accuracy checker import failed: {e}")
    def verify_response_accuracy(text, *args, **kwargs): return text

try:
    from services.research_engine_lite import get_research_engine_lite
except Exception as e:
    print(f"[lite_app] Research engine import failed: {e}")
    def get_research_engine_lite(*args, **kwargs):
        class FallbackEngine:
            def search(self, query, max_results=5): return []
        return FallbackEngine()
UI_TEMPLATE_DIR = BASE_DIR / "ui" / "templates"
UI_STATIC_DIR = BASE_DIR / "ui" / "static"

DATA_ROOT = BASE_DIR
if os.environ.get("VERCEL") == "1" or os.environ.get("ATLAS_DEPLOYMENT_MODE") in {"serverless", "lite"}:
    DATA_ROOT = Path("/tmp/atlas-ai")
    DATA_ROOT.mkdir(parents=True, exist_ok=True)

GEMS_DIR = DATA_ROOT / "gems"
GEMS_FILE = GEMS_DIR / "gems.json"
GEMS_DIR.mkdir(parents=True, exist_ok=True)
if not GEMS_FILE.exists():
    GEMS_FILE.write_text(json.dumps({"gems": []}, indent=2), encoding="utf-8")

app = Flask(__name__, template_folder=str(UI_TEMPLATE_DIR), static_folder=str(UI_STATIC_DIR))
CORS(app)


def _slugify(text: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    base = re.sub(r"-{2,}", "-", base)
    return base[:32] or "gem"


def _load_gems_db() -> Dict[str, Any]:
    try:
        data = json.loads(GEMS_FILE.read_text(encoding="utf-8"))
        if isinstance(data, dict) and isinstance(data.get("gems"), list):
            return data
    except Exception:
        pass
    return {"gems": []}


def _save_gems_db(db: Dict[str, Any]) -> None:
    GEMS_FILE.write_text(json.dumps(db, indent=2), encoding="utf-8")


def _public_gem(g: Dict[str, Any]) -> Dict[str, Any]:
    sources = g.get("sources") or {}
    links = sources.get("links") if isinstance(sources.get("links"), list) else []
    files = sources.get("files") if isinstance(sources.get("files"), list) else []
    return {
        "id": g.get("id"),
        "name": g.get("name"),
        "description": g.get("description", ""),
        "instructions": g.get("instructions", ""),
        "sources": {
            "links": links,
            "files": [{"filename": f.get("filename")} for f in files if isinstance(f, dict) and f.get("filename")],
        },
        "created_at": g.get("created_at", ""),
        "updated_at": g.get("updated_at", ""),
    }


def _get_gem_by_id(gem_id: str) -> Dict[str, Any] | None:
    db = _load_gems_db()
    for g in db.get("gems", []):
        if g.get("id") == gem_id:
            return g
    return None


def _gem_sources_to_knowledge(gem: Dict[str, Any]) -> List[Dict[str, Any]]:
    now = datetime.now().isoformat()
    sources = gem.get("sources") or {}
    files = sources.get("files") if isinstance(sources.get("files"), list) else []
    links = sources.get("links") if isinstance(sources.get("links"), list) else []
    knowledge: List[Dict[str, Any]] = []

    for f in files[:6]:
        if not isinstance(f, dict):
            continue
        filename = (f.get("filename") or "").strip()
        content = (f.get("content") or "").strip()
        if filename and content and len(content) > 20:
            knowledge.append({
                "title": f"Gem Source — {filename}",
                "content": content[:1200],
                "query": gem.get("name", ""),
                "source": "gem_source",
                "learned_at": now,
            })

    # Links are not fetched in lite mode (avoid unpredictable latency). We keep them as titles only.
    for url in links[:3]:
        u = str(url).strip()
        if not u:
            continue
        knowledge.append({
            "title": f"Gem Source — {u[:60]}",
            "content": f"User-provided source link: {u}",
            "query": gem.get("name", ""),
            "source": "gem_source",
            "learned_at": now,
            "url": u,
        })

    return knowledge


def _synthesize_lite(query: str, knowledge_items: List[Dict[str, Any]]) -> str:
    """Lightweight synthesis from snippets."""
    q_lower = (query or "").strip().lower()

    # Very short chit-chat / closing phrases should not trigger web search.
    smalltalk_map = {
        "hi": "Hi! How can I help you?",
        "hello": "Hello! What would you like to explore?",
        "hey": "Hey! What can I help you with?",
        "thanks": "You’re welcome — happy to help.",
        "thank you": "You’re welcome — happy to help.",
        "bye": "Bye! Talk to you soon.",
        "goodbye": "Goodbye! Feel free to come back any time.",
        "see you": "See you later!",
    }
    if q_lower in smalltalk_map:
        return smalltalk_map[q_lower]

    # If this looks like a weather query, avoid parroting search snippets and be
    # explicit about the limitation instead of pretending to be a live weather API.
    if "weather" in q_lower and (" in " in q_lower or "at " in q_lower):
        return (
            "I can look up weather pages for that location, but I don’t have a trusted, "
            "real‑time weather API. For the most accurate current conditions and forecast, "
            "check a dedicated weather site (like your local meteorological service or a "
            "weather app). If you paste a forecast here, I can help interpret it."
        )

    if not knowledge_items:
        return "I couldn’t find enough reliable info. What exact aspect should I focus on?"

    # Prefer Wikipedia / multi-source diversity
    picked: List[str] = []
    seen_sources = set()
    for k in knowledge_items:
        src = (k.get("source") or "").lower()
        txt = (k.get("content") or "").strip()
        if not txt or len(txt) < 30:
            continue
        if src in seen_sources and len(picked) >= 2:
            continue
        seen_sources.add(src)
        picked.append(txt)
        if len(picked) >= 3:
            break

    if not picked:
        picked = [str(knowledge_items[0].get("content") or "")[:500]]

    # Definition-ish framing when user asks "what is"
    if re.search(r"\bwhat is\b|\bdefine\b|\bmeaning of\b", query.lower()):
        return picked[0]

    # General: short summary + 1–2 supporting points
    out = picked[0]
    if len(picked) > 1:
        out += "\n\n" + "\n".join(f"- {p}" for p in picked[1:])
    return out


@app.route('/favicon.ico')
def favicon():
    """Serve favicon."""
    from flask import send_from_directory
    return send_from_directory(str(UI_STATIC_DIR), 'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/')
def index():
    return render_template('index.html')




@app.route('/api/gems', methods=['GET'])
def list_gems():
    db = _load_gems_db()
    gems_out = [_public_gem(g) for g in db.get('gems', [])]
    gems_out.sort(key=lambda g: g.get('updated_at', ''), reverse=True)
    return jsonify({'gems': gems_out})


@app.route('/api/gems', methods=['POST'])
def create_gem():
    data = request.json or {}
    name = (data.get('name') or '').strip()
    if not name:
        return jsonify({'error': 'Gem name is required'}), 400

    gem_id = f"{_slugify(name)}-{uuid.uuid4().hex[:6]}"
    now = datetime.now().isoformat()
    gem = {
        'id': gem_id,
        'name': name,
        'description': (data.get('description') or '').strip(),
        'instructions': (data.get('instructions') or '').strip(),
        'sources': data.get('sources') or {'links': [], 'files': []},
        'created_at': now,
        'updated_at': now,
    }
    db = _load_gems_db()
    db.setdefault('gems', []).append(gem)
    _save_gems_db(db)
    return jsonify({'gem': _public_gem(gem)}), 201


@app.route('/api/gems/<gem_id>', methods=['PUT'])
def update_gem(gem_id):
    data = request.json or {}
    db = _load_gems_db()
    updated = None
    for g in db.get('gems', []):
        if g.get('id') != gem_id:
            continue
        if 'name' in data:
            g['name'] = (data.get('name') or '').strip() or g.get('name')
        if 'description' in data:
            g['description'] = (data.get('description') or '').strip()
        if 'instructions' in data:
            g['instructions'] = (data.get('instructions') or '').strip()
        if 'sources' in data:
            g['sources'] = data.get('sources') or {'links': [], 'files': []}
        g['updated_at'] = datetime.now().isoformat()
        updated = g
        break

    if not updated:
        return jsonify({'error': 'Gem not found'}), 404
    _save_gems_db(db)
    return jsonify({'gem': _public_gem(updated)})


@app.route('/api/gems/<gem_id>', methods=['DELETE'])
def delete_gem(gem_id):
    db = _load_gems_db()
    before = len(db.get('gems', []))
    db['gems'] = [g for g in db.get('gems', []) if g.get('id') != gem_id]
    if len(db['gems']) == before:
        return jsonify({'error': 'Gem not found'}), 404
    _save_gems_db(db)
    return jsonify({'success': True})


@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json or {}
    message = (data.get('message') or '').strip()
    if not message:
        return jsonify({'error': 'Message is required'}), 400

    requested_model = (data.get('model') or 'thor-1.0').strip()
    gem_config = None
    model_label = 'Thor 1.0'

    if requested_model == 'gem:preview' and isinstance(data.get('gem_draft'), dict):
        draft = data.get('gem_draft') or {}
        gem_config = {
            'id': 'preview',
            'name': (draft.get('name') or 'Gem').strip()[:60],
            'description': (draft.get('description') or '').strip(),
            'instructions': (draft.get('instructions') or '').strip(),
            'sources': draft.get('sources') or {'links': [], 'files': []},
        }
        model_label = f"Gem: {gem_config.get('name')} (Try)"
    elif requested_model.startswith('gem:') and requested_model != 'gem:preview':
        gem_id = requested_model.replace('gem:', '', 1)
        g = _get_gem_by_id(gem_id)
        if g:
            gem_config = g
            model_label = f"Gem: {g.get('name', 'Gem')}"

    # Image flow (same UX as local)
    message_lower = message.lower()
    image_handler = get_image_handler()
    image_subject = image_handler.extract_image_request(message)
    if image_subject:
        variant = None
        if any(w in message_lower for w in ['another', 'different', 'new one', 'new image']):
            variant = f"{int(datetime.now().timestamp() * 1000)}"
        url, src = image_handler.get_image(image_subject, '960x540', variant=variant)
        resp = image_handler.format_image_response(image_subject, url, is_trainx=(src == 'trainx'))
        return jsonify({'response': resp, 'chat_id': None, 'task': 'text_generation'})

    # Image tweaks: another angle/style/background
    tweak_phrases = [
        'another style', 'different style', 'another angle', 'different angle',
        'different background', 'another background', 'different size', 'change size',
        'bigger', 'smaller', 'another one', 'another image', 'change subject', 'make it'
    ]
    if any(p in message_lower for p in tweak_phrases):
        m_subj = re.search(r"(?:make it|change (?:it )?(?:to|into|subject to))\s+(.+)", message, flags=re.IGNORECASE)
        subject = (m_subj.group(1).strip(" .!?") if m_subj else 'image')
        modifier = 'different angle' if 'angle' in message_lower else ('different background' if 'background' in message_lower else ('different style' if 'style' in message_lower else 'variant'))
        subject_for_image = f"{subject} {modifier}".strip()
        size_match = re.search(r"(\d{2,4})\s*[xX]\s*(\d{2,4})", message)
        size_str = f"{size_match.group(1)}x{size_match.group(2)}" if size_match else '960x540'
        variant_key = f"{int(datetime.now().timestamp() * 1000)}:{modifier}"
        url, src = image_handler.get_image(subject_for_image, size_str, variant=variant_key)
        resp = image_handler.format_image_response(subject_for_image, url, is_trainx=(src == 'trainx'))
        return jsonify({'response': resp, 'chat_id': None, 'task': 'text_generation'})

    # Multi-engine research + lite synthesis
    engine = get_research_engine_lite()
    knowledge = engine.search(message, max_results=5)

    if gem_config:
        knowledge = _gem_sources_to_knowledge(gem_config) + knowledge

    response_text = _synthesize_lite(message, knowledge)

    # Apply gem instruction prefix lightly (no model, so we bias style)
    if gem_config and (gem_config.get('instructions') or '').strip():
        # Keep it short and non-invasive
        response_text = f"{response_text}\n\n_Context:_ {gem_config.get('instructions','')[:220]}"

    # Final refinement + accuracy check
    refiner = get_answer_refiner()
    refined = refiner.refine(
        response_text,
        knowledge_used=knowledge,
        query_intent={
            'is_follow_up': False,
            'hints': {
                # Lite mode does not run the full intent analyzer, but we can
                # still pass through a basic tone hint so the final formatter
                # can avoid over-casual prefixes.
                'tone': 'neutral',
            },
        },
        model_name=model_label,
    )
    refined = verify_response_accuracy(refined, knowledge, query=message)

    return jsonify({'response': refined, 'chat_id': None, 'task': 'text_generation'})


@app.route('/api/chats', methods=['GET'])
def list_chats():
    """List all chats (lite version - returns empty list)."""
    return jsonify({'chats': []})


@app.route('/api/chats/<chat_id>', methods=['GET'])
def get_chat(chat_id):
    """Get specific chat (lite version - returns empty)."""
    return jsonify({'chat_id': chat_id, 'messages': []}), 404


@app.route('/api/chats/<chat_id>', methods=['DELETE'])
def delete_chat(chat_id):
    """Delete chat (lite version - always succeeds)."""
    return jsonify({'success': True})


@app.route('/api/model/status', methods=['GET'])
def model_status():
    """Get model status (lite version - indicates fallback available)."""
    return jsonify({
        'models': {},
        'fallback_available': True,
        'message': 'Lite mode: Using research engine fallback (no local models available)'
    })


@app.route('/api/projects', methods=['GET'])
def list_projects():
    """List projects (lite version - returns empty list)."""
    return jsonify({'projects': []})


@app.route('/api/projects', methods=['POST'])
def create_project():
    """Create project (lite version - returns success)."""
    return jsonify({'project': {'id': 'lite', 'name': 'Default', 'chat_ids': []}}), 201


@app.route('/api/history', methods=['GET'])
def get_history():
    """Get history (lite version - returns empty list)."""
    return jsonify({'history': []})


@app.route('/install')
def install():
    """Install page."""
    try:
        # Pass a flag to indicate this is a serverless deployment
        return render_template('install.html', is_serverless=True)
    except Exception as e:
        print(f"[lite_app] Error rendering install.html: {e}")
        # Fallback to index.html if install.html doesn't exist
        return render_template('index.html')


@app.route('/download/atlas-macos.dmg')
@app.route('/download/atlas-windows.exe')
@app.route('/download/atlas-linux.AppImage')
def download_app():
    """Download desktop app (not available in serverless deployment)."""
    # Redirect to install page which will show the appropriate message
    from flask import redirect
    return redirect('/install', code=302)
