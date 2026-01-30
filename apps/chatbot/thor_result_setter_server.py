"""
Thor Result Setter server for curating authoritative responses.
Runs on port 5005 and supports both manual entry and TrainX automation.
"""
from __future__ import annotations

import json
import os
import sys
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from flask import Flask, jsonify, render_template, request
from flask_cors import CORS

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from trainx import TrainXCompiler
from trainx.exceptions import TrainXError

TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')
app = Flask(__name__, template_folder=TEMPLATE_DIR)
CORS(app)

os.makedirs(TEMPLATE_DIR, exist_ok=True)

RESULT_SETTER_FILE = os.path.join(BASE_DIR, 'thor_result_setter.json')
IMAGE_SETTER_FILE = os.path.join(BASE_DIR, 'thor_image_setter.json')
APP_LABEL = "Thor Result Setter"


def _log(message: str) -> None:
    print(f"[{APP_LABEL}] {message}")


def _timestamp() -> str:
    return datetime.now().isoformat()


def _load_pairs() -> Dict[str, List[dict]]:
    if not os.path.exists(RESULT_SETTER_FILE):
        return {'qa_pairs': []}
    try:
        with open(RESULT_SETTER_FILE, 'r', encoding='utf-8') as handle:
            data = json.load(handle)
            data.setdefault('qa_pairs', [])
            return data
    except Exception as exc:  # pragma: no cover - defensive
        _log(f"Error loading data: {exc}")
        return {'qa_pairs': []}


def _load_images() -> Dict[str, List[dict]]:
    if not os.path.exists(IMAGE_SETTER_FILE):
        return {'images': []}
    try:
        with open(IMAGE_SETTER_FILE, 'r', encoding='utf-8') as handle:
            data = json.load(handle)
            data.setdefault('images', [])
            return data
    except Exception as exc:  # pragma: no cover - defensive
        _log(f"Error loading images: {exc}")
        return {'images': []}


def _save_pairs(data: Dict[str, List[dict]]) -> bool:
    try:
        with open(RESULT_SETTER_FILE, 'w', encoding='utf-8') as handle:
            json.dump(data, handle, indent=2, ensure_ascii=False)
        return True
    except Exception as exc:  # pragma: no cover - defensive
        _log(f"Error saving data: {exc}")
        return False


def _save_images(data: Dict[str, List[dict]]) -> bool:
    try:
        with open(IMAGE_SETTER_FILE, 'w', encoding='utf-8') as handle:
            json.dump(data, handle, indent=2, ensure_ascii=False)
        return True
    except Exception as exc:  # pragma: no cover - defensive
        _log(f"Error saving images: {exc}")
        return False


def _guess_type(question: str, answer: str) -> Optional[str]:
    img_exts = ('.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp', '.svg')
    lowered = answer.lower().strip()
    # Allow query strings; check substring plus URL hint
    if (any(ext in lowered for ext in img_exts) and ('http://' in lowered or 'https://' in lowered)) or lowered.endswith(img_exts):
        return 'image'
    if 'image' in question.lower():
        return 'image'
    return None


def _build_pair(question: str, answer: str, pair_type: Optional[str] = None) -> Dict[str, str]:
    timestamp = _timestamp()
    pair = {
        'id': str(uuid.uuid4()),
        'question': question,
        'answer': answer,
        'created_at': timestamp,
        'updated_at': timestamp,
    }
    detected_type = pair_type or _guess_type(question, answer)
    if detected_type:
        pair['type'] = detected_type
    return pair


def _build_image_entry(thing: str, image_url: str, question: Optional[str] = None) -> Dict[str, str]:
    timestamp = _timestamp()
    q_text = question if question else f"Create an image of {thing}"
    return {
        'id': str(uuid.uuid4()),
        'thing': thing,
        'question': q_text,
        'image_url': image_url,
        'created_at': timestamp,
        'updated_at': timestamp,
    }


def _extract_thing_from_question(question: str) -> str:
    q = (question or '').strip()
    if not q:
        return ''
    lower = q.lower()
    if 'image of' in lower:
        idx = lower.find('image of')
        subject = q[idx + len('image of'):].strip(" :.?")
        if subject:
            return subject
    if lower.startswith('create '):
        parts = q.split(' ', 2)
        if len(parts) == 3:
            return parts[2].strip()
    return q


def _list_response(pairs: List[dict]):
    return jsonify({
        'success': True,
        'result_pairs': pairs,
        'qa_pairs': pairs,
        'total': len(pairs),
    })


@app.route('/')
def index():
    """Render the Result Setter interface."""
    return render_template('result_setter.html')


@app.route('/image-setter')
def image_setter():
    """Render the Thor Image Setter interface."""
    return render_template('image_setter.html')


@app.route('/api/qa/list', methods=['GET'])
def list_result_pairs():
    """Return every curated result pair."""
    data = _load_pairs()
    return _list_response(data.get('qa_pairs', []))


@app.route('/api/image-setter/list', methods=['GET'])
def list_image_entries():
    """Return all image mappings."""
    data = _load_images()
    images = data.get('images', [])
    return jsonify({
        'success': True,
        'images': images,
        'total': len(images),
    })


@app.route('/api/qa/add', methods=['POST'])
def add_result_pair():
    """Insert a single result pair supplied by a human editor."""
    payload = request.json or {}
    question = (payload.get('question') or '').strip()
    answer = (payload.get('answer') or '').strip()
    pair_type = (payload.get('type') or '').strip()

    if not question:
        return jsonify({'success': False, 'error': 'Question is required'}), 400
    if not answer:
        return jsonify({'success': False, 'error': 'Answer is required'}), 400

    data = _load_pairs()
    new_pair = _build_pair(question, answer, pair_type or None)
    data['qa_pairs'].insert(0, new_pair)

    if not _save_pairs(data):
        return jsonify({'success': False, 'error': 'Failed to save result pair'}), 500

    _log(f"Added manual result pair: {question[:60]}...")
    return jsonify({
        'success': True,
        'result_pair': new_pair,
        'qa_pair': new_pair,
        'message': 'Result pair added successfully',
    })


@app.route('/api/image-setter/add', methods=['POST'])
def add_image_entry():
    """Insert a single image mapping (thing -> image_url)."""
    payload = request.json or {}
    thing = (payload.get('thing') or '').strip()
    image_url = (payload.get('image_url') or '').strip()
    question_override = (payload.get('question') or '').strip()

    if not thing:
        return jsonify({'success': False, 'error': 'Thing / subject is required'}), 400
    if not image_url:
        return jsonify({'success': False, 'error': 'Image URL is required'}), 400

    data = _load_images()
    entry = _build_image_entry(thing, image_url, question_override or None)
    data['images'].insert(0, entry)

    if not _save_images(data):
        return jsonify({'success': False, 'error': 'Failed to save image entry'}), 500

    _log(f"Added image entry: {thing[:60]}...")
    return jsonify({'success': True, 'entry': entry})


@app.route('/api/image-setter/update', methods=['POST'])
def update_image_entry():
    """Update an existing image mapping."""
    payload = request.json or {}
    entry_id = (payload.get('id') or '').strip()
    thing = (payload.get('thing') or '').strip()
    image_url = (payload.get('image_url') or '').strip()
    question_override = (payload.get('question') or '').strip()

    if not entry_id:
        return jsonify({'success': False, 'error': 'Entry ID is required'}), 400
    if not thing:
        return jsonify({'success': False, 'error': 'Thing / subject is required'}), 400
    if not image_url:
        return jsonify({'success': False, 'error': 'Image URL is required'}), 400

    data = _load_images()
    updated = False
    for entry in data.get('images', []):
        if entry.get('id') == entry_id:
            entry['thing'] = thing
            entry['image_url'] = image_url
            entry['question'] = question_override or entry.get('question') or f"Create an image of {thing}"
            entry['updated_at'] = _timestamp()
            updated = True
            break

    if not updated:
        return jsonify({'success': False, 'error': 'Entry not found'}), 404

    if not _save_images(data):
        return jsonify({'success': False, 'error': 'Failed to save changes'}), 500

    _log(f"Updated image entry: {entry_id}")
    return jsonify({'success': True, 'message': 'Image entry updated'})


@app.route('/api/image-setter/delete', methods=['POST'])
def delete_image_entry():
    """Delete an image mapping."""
    payload = request.json or {}
    entry_id = (payload.get('id') or '').strip()

    if not entry_id:
        return jsonify({'success': False, 'error': 'Entry ID is required'}), 400

    data = _load_images()
    before = len(data.get('images', []))
    data['images'] = [entry for entry in data.get('images', []) if entry.get('id') != entry_id]

    if len(data.get('images', [])) == before:
        return jsonify({'success': False, 'error': 'Entry not found'}), 404

    if not _save_images(data):
        return jsonify({'success': False, 'error': 'Failed to save changes'}), 500

    _log(f"Deleted image entry: {entry_id}")
    return jsonify({'success': True, 'message': 'Image entry deleted'})


@app.route('/api/image-setter/trainx/compile', methods=['POST'])
def compile_image_trainx():
    """Compile TrainX code into image mappings (thing -> image_url)."""
    payload = request.json or {}
    source = (payload.get('source') or '').strip()

    if not source:
        return jsonify({'success': False, 'error': 'TrainX code is required'}), 400

    try:
        compiler = TrainXCompiler(source)
        generated = compiler.compile()
    except TrainXError as exc:
        return jsonify({'success': False, 'error': str(exc)}), 400
    except Exception as exc:  # pragma: no cover - defensive
        _log(f"Unexpected TrainX error (image-setter): {exc}")
        return jsonify({'success': False, 'error': 'Unexpected TrainX error'}), 500

    if not generated:
        return jsonify({
            'success': False,
            'error': 'TrainX code did not generate any pairs',
        }), 400

    data = _load_images()
    created: List[dict] = []

    for pair in generated:
        question = (pair.get('question') or '').strip()
        answer = (pair.get('answer') or '').strip()
        pair_type = (pair.get('type') or '').strip()
        is_image = pair.get('is_image', False) or (pair_type.lower() == 'image' if pair_type else False)

        if not answer or not question:
            continue

        # accept if image-typed or answer looks like image
        if not is_image:
            lower = answer.lower()
            img_exts = ('.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp', '.svg')
            if '{{trainx_iframe:' in lower or any(ext in lower for ext in img_exts):
                is_image = True
        if not is_image:
            continue

        thing = _extract_thing_from_question(question)
        if not thing:
            continue

        entry = _build_image_entry(thing, answer, question)
        data['images'].insert(0, entry)
        created.append(entry)

    if not created:
        return jsonify({
            'success': False,
            'error': 'No image pairs produced by the TrainX script',
        }), 400

    if not _save_images(data):
        return jsonify({'success': False, 'error': 'Failed to save TrainX images'}), 500

    _log(f"Image Setter TrainX generated {len(created)} entries")
    return jsonify({
        'success': True,
        'entries': created,
        'count': len(created),
        'message': f"Generated {len(created)} image mappings via TrainX",
    })


@app.route('/api/qa/update', methods=['POST'])
def update_result_pair():
    """Update an existing result pair."""
    payload = request.json or {}
    pair_id = (payload.get('id') or '').strip()
    question = (payload.get('question') or '').strip()
    answer = (payload.get('answer') or '').strip()
    pair_type = (payload.get('type') or '').strip()

    if not pair_id:
        return jsonify({'success': False, 'error': 'Result pair ID is required'}), 400
    if not question:
        return jsonify({'success': False, 'error': 'Question is required'}), 400
    if not answer:
        return jsonify({'success': False, 'error': 'Answer is required'}), 400

    data = _load_pairs()
    updated = False

    for pair in data.get('qa_pairs', []):
        if pair['id'] == pair_id:
            pair['question'] = question
            pair['answer'] = answer
            pair['updated_at'] = _timestamp()
            if pair_type:
                pair['type'] = pair_type
            updated = True
            break

    if not updated:
        return jsonify({'success': False, 'error': 'Result pair not found'}), 404

    if not _save_pairs(data):
        return jsonify({'success': False, 'error': 'Failed to save result pair'}), 500

    _log(f"Updated result pair: {pair_id}")
    return jsonify({'success': True, 'message': 'Result pair updated successfully'})


@app.route('/api/qa/delete', methods=['POST'])
def delete_result_pair():
    """Delete an existing result pair."""
    payload = request.json or {}
    pair_id = (payload.get('id') or '').strip()

    if not pair_id:
        return jsonify({'success': False, 'error': 'Result pair ID is required'}), 400

    data = _load_pairs()
    before = len(data.get('qa_pairs', []))
    data['qa_pairs'] = [pair for pair in data['qa_pairs'] if pair['id'] != pair_id]

    if len(data['qa_pairs']) == before:
        return jsonify({'success': False, 'error': 'Result pair not found'}), 404

    if not _save_pairs(data):
        return jsonify({'success': False, 'error': 'Failed to save changes'}), 500

    _log(f"Deleted result pair: {pair_id}")
    return jsonify({'success': True, 'message': 'Result pair deleted successfully'})


@app.route('/api/qa/search', methods=['POST'])
def search_result_pairs():
    """Search stored result pairs."""
    payload = request.json or {}
    query = (payload.get('query') or '').strip().lower()

    if not query:
        return jsonify({'success': False, 'error': 'Search query is required'}), 400

    data = _load_pairs()
    results = []
    for pair in data.get('qa_pairs', []):
        if query in pair['question'].lower() or query in pair['answer'].lower():
            results.append(pair)

    return jsonify({
        'success': True,
        'result_pairs': results,
        'qa_pairs': results,
        'total': len(results),
    })


@app.route('/api/trainx/compile', methods=['POST'])
def compile_trainx_pairs():
    """Compile TrainX code into result pairs and persist them."""
    payload = request.json or {}
    source = (payload.get('source') or '').strip()

    if not source:
        return jsonify({'success': False, 'error': 'TrainX code is required'}), 400

    try:
        compiler = TrainXCompiler(source)
        generated = compiler.compile()
    except TrainXError as exc:
        return jsonify({'success': False, 'error': str(exc)}), 400
    except Exception as exc:  # pragma: no cover - defensive
        _log(f"Unexpected TrainX error: {exc}")
        return jsonify({'success': False, 'error': 'Unexpected TrainX error'}), 500

    if not generated:
        return jsonify({
            'success': False,
            'error': 'TrainX code did not generate any question-answer pairs',
        }), 400

    data = _load_pairs()
    created_pairs: List[dict] = []

    for pair in generated:
        question = (pair.get('question') or '').strip()
        answer = (pair.get('answer') or '').strip()
        pair_type = (pair.get('type') or '').strip()
        if not pair_type and pair.get('is_image'):
            pair_type = 'image'
        if not question or not answer:
            continue
        new_pair = _build_pair(question, answer, pair_type or None)
        data['qa_pairs'].insert(0, new_pair)
        created_pairs.append(new_pair)

    if not created_pairs:
        return jsonify({
            'success': False,
            'error': 'No valid pairs were produced by the TrainX script',
        }), 400

    if not _save_pairs(data):
        return jsonify({'success': False, 'error': 'Failed to save TrainX results'}), 500

    _log(f"TrainX generated {len(created_pairs)} result pairs")
    return jsonify({
        'success': True,
        'generated': created_pairs,
        'count': len(created_pairs),
        'result_pairs': created_pairs,
        'message': f"Generated {len(created_pairs)} result pairs via TrainX",
    })


if __name__ == '__main__':
    print("=" * 60)
    print(f"{APP_LABEL} Server")
    print("=" * 60)
    print("Starting on http://localhost:5004")
    print()
    print("This server allows you to:")
    print("  • Add manual question-answer result pairs")
    print("  • Generate large batches via TrainX")
    print("  • Edit, delete, and search curated responses")
    print()
    print(f"Data stored in: {RESULT_SETTER_FILE}")
    print("=" * 60)
    print()
    app.run(debug=True, host='0.0.0.0', port=5004)
