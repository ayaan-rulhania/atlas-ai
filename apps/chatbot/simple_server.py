#!/usr/bin/env python3
"""
Simple Atlas AI Server - Basic Flask app for testing
"""
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import os
from pathlib import Path

# Basic configuration
BASE_DIR = Path(__file__).parent.resolve()
SECRET_KEY = "atlas-ai-simple-key"

# Template and static directories
UI_TEMPLATE_DIR = BASE_DIR / "ui" / "templates"
UI_STATIC_DIR = BASE_DIR / "ui" / "static"

app = Flask(__name__,
            template_folder=str(UI_TEMPLATE_DIR),
            static_folder=str(UI_STATIC_DIR))
app.secret_key = SECRET_KEY

# Configure CORS
CORS(app, origins=["http://localhost:5000", "http://127.0.0.1:5000"])

@app.route('/')
def index():
    """Main chat interface"""
    try:
        return render_template('index.html')
    except Exception as e:
        return f"<h1>Atlas AI</h1><p>Server running. Template error: {e}</p>"

@app.route('/api/chat', methods=['POST'])
def chat():
    """Simple chat endpoint"""
    try:
        data = request.get_json()
        user_message = data.get('message', '')

        # Simple response based on message content
        if 'hello' in user_message.lower() or 'hi' in user_message.lower():
            response_text = f"Hello! I received your message: '{user_message}'. Atlas AI is running in simple mode."
        elif 'how are you' in user_message.lower():
            response_text = "I'm doing well, thank you for asking! I'm running in a simplified mode right now."
        else:
            response_text = f"I understand you said: '{user_message}'. I'm currently running in basic mode with limited AI capabilities."

        return jsonify({
            'response': response_text,
            'chat_id': None,
            'model': 'Atlas AI (Simple Mode)',
            'status': 'working'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'mode': 'simple'})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Starting Atlas AI Simple Server on port {port}")
    print("📱 Access at: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=port)