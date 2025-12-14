"""
Dev Atlas server (minimal UI + API proxy).

- Serves the Dev Atlas UI (Aboreto-styled, basic features).
- Proxies /api/chat to the main Atlas backend (port 5000 by default),
  so Thor 1.0 is only loaded once.
"""

from __future__ import annotations

import os
from pathlib import Path

import requests
from flask import Flask, jsonify, render_template, request

BASE_DIR = Path(__file__).parent.resolve()
UI_TEMPLATE_DIR = BASE_DIR / "ui" / "templates"
UI_STATIC_DIR = BASE_DIR / "ui" / "static"

app = Flask(__name__, template_folder=str(UI_TEMPLATE_DIR), static_folder=str(UI_STATIC_DIR))

# Main Atlas backend base URL (where Thor 1.0 runs)
ATLAS_API_BASE = os.environ.get("ATLAS_API_BASE", "http://127.0.0.1:5000").rstrip("/")


@app.route("/")
def index():
    return render_template("dev_atlas.html")


@app.route("/api/chat", methods=["POST"])
def proxy_chat():
    try:
        payload = request.get_json(force=True, silent=True) or {}
        upstream = requests.post(
            f"{ATLAS_API_BASE}/api/chat",
            json=payload,
            timeout=180,
        )
        content_type = upstream.headers.get("Content-Type", "application/json")
        return upstream.content, upstream.status_code, {"Content-Type": content_type}
    except Exception as e:
        return jsonify({"error": f"Dev Atlas proxy error: {e}"}), 502


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    # No debug reloader by default to keep it lightweight.
    app.run(host="0.0.0.0", port=port, debug=False)

