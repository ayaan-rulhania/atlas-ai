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

# Add chatbot directory to Python path (must be first for relative imports to work)
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

# Verify that lite_app.py exists before importing
lite_app_path = CHATBOT_DIR / "lite_app.py"
if not lite_app_path.exists():
    raise ImportError(f"lite_app.py not found at {lite_app_path}")

# Verify that required directories exist
required_dirs = ["handlers", "refinement", "services"]
for dir_name in required_dirs:
    dir_path = CHATBOT_DIR / dir_name
    if not dir_path.exists():
        print(f"[api/index.py] WARNING: Required directory {dir_name} not found at {dir_path}")

# Import lite_app with better error handling
try:
    # First, try importing as a module from the chatbot directory
    from lite_app import app  # noqa: F401
    print("[api/index.py] Successfully imported lite_app")
except ImportError as e:
    print(f"[api/index.py] Import error from lite_app: {e}")
    import traceback
    traceback.print_exc()
    
    # Try alternative import path (if deployed from root)
    try:
        from chatbot.lite_app import app  # noqa: F401
        print("[api/index.py] Successfully imported chatbot.lite_app")
    except ImportError as e2:
        print(f"[api/index.py] Import error from chatbot.lite_app: {e2}")
        traceback.print_exc()
        
        # Last resort: try importing directly by file path
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("lite_app", lite_app_path)
            if spec and spec.loader:
                lite_app_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(lite_app_module)
                app = lite_app_module.app
                print("[api/index.py] Successfully imported lite_app via file path")
            else:
                raise ImportError("Could not create module spec from file")
        except Exception as e3:
            print(f"[api/index.py] All import attempts failed. Last error: {e3}")
            traceback.print_exc()
            raise ImportError(f"Failed to import lite_app: {e}. Alternative attempts also failed: {e2}, {e3}") from e
