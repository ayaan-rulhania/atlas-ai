"""Vercel entrypoint.

Vercel's Python runtime will treat this module as a serverless function.
Exporting the Flask WSGI app as `app` allows Vercel to route all requests
through the Flask router (/, /api/chat, /dev-atlas, /static/*, etc.).

This deployment uses `chatbot/lite_app.py` to avoid depending on `thor-1.0/`
when the deployment root is `chatbot/`.
"""

import sys
import os
from pathlib import Path

# Get the directory containing this file (api/)
API_DIR = Path(__file__).parent.resolve()
# Get the chatbot directory (parent of api/)
CHATBOT_DIR = API_DIR.parent.resolve()

# Add chatbot directory to Python path
if str(CHATBOT_DIR) not in sys.path:
    sys.path.insert(0, str(CHATBOT_DIR))

# Also add parent directory in case we're deployed from root
PARENT_DIR = CHATBOT_DIR.parent.resolve()
if str(PARENT_DIR) not in sys.path:
    sys.path.insert(0, str(PARENT_DIR))

# Debug: Print path info (will be visible in Vercel logs)
print(f"[api/index.py] API_DIR: {API_DIR}")
print(f"[api/index.py] CHATBOT_DIR: {CHATBOT_DIR}")
print(f"[api/index.py] PARENT_DIR: {PARENT_DIR}")
print(f"[api/index.py] sys.path: {sys.path[:5]}")  # First 5 entries
print(f"[api/index.py] Current working directory: {os.getcwd()}")

try:
    from lite_app import app  # noqa: F401
    print("[api/index.py] Successfully imported lite_app")
except ImportError as e:
    print(f"[api/index.py] Import error from lite_app: {e}")
    import traceback
    traceback.print_exc()
    
    # Try alternative import path
    try:
        from chatbot.lite_app import app  # noqa: F401
        print("[api/index.py] Successfully imported chatbot.lite_app")
    except ImportError as e2:
        print(f"[api/index.py] Import error from chatbot.lite_app: {e2}")
        traceback.print_exc()
        raise
