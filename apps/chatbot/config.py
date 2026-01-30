"""
Centralized configuration management for Atlas AI chatbot.
All configuration values should be loaded from environment variables or this file.
"""
import os
from pathlib import Path
from typing import Optional

# Base directories
BASE_DIR = Path(__file__).parent.resolve()
ATLAS_ROOT = BASE_DIR.parent.parent  # apps/chatbot/ -> apps/ -> root
THOR_1_0_DIR = ATLAS_ROOT / "models" / "thor-1.0"
THOR_1_1_DIR = ATLAS_ROOT / "models" / "thor-1.1"
THOR_1_2_DIR = ATLAS_ROOT / "models" / "thor" / "thor-1.2"  # Improved version, loads instantly
THOR_CALC_1_0_DIR = ATLAS_ROOT / "models" / "thor-calc-1.0"
ANTELOPE_1_0_DIR = ATLAS_ROOT / "models" / "antelope-1.0"
ANTELOPE_1_1_DIR = ATLAS_ROOT / "models" / "antelope-1.1"
CHATBOT_DIR = BASE_DIR

# Default to Thor 1.1, but support both
THOR_DIR = THOR_1_1_DIR  # Default to latest

# Data root configuration
# Vercel/serverless environments have read-only project dirs; use /tmp for writes.
DATA_ROOT = BASE_DIR
if os.environ.get("VERCEL") == "1" or os.environ.get("ATLAS_DEPLOYMENT_MODE") in {"serverless", "lite"}:
    DATA_ROOT = Path("/tmp/atlas-ai")
    try:
        DATA_ROOT.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass

# Flask configuration
# SECRET_KEY: Use environment variable or generate persistent key
# For production, set ATLAS_SECRET_KEY environment variable
SECRET_KEY = os.environ.get("ATLAS_SECRET_KEY")
if not SECRET_KEY:
    # Generate a persistent key file if it doesn't exist
    SECRET_KEY_FILE = DATA_ROOT / ".secret_key"
    if SECRET_KEY_FILE.exists():
        try:
            SECRET_KEY = SECRET_KEY_FILE.read_text().strip()
        except Exception:
            SECRET_KEY = None
    
    if not SECRET_KEY:
        # Generate new key and save it
        import secrets
        SECRET_KEY = secrets.token_urlsafe(32)
        try:
            SECRET_KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
            SECRET_KEY_FILE.write_text(SECRET_KEY)
        except Exception:
            # If we can't write, use in-memory key (will reset on restart)
            pass

# CORS configuration
# Allow specific origins instead of all origins
CORS_ORIGINS = os.environ.get("ATLAS_CORS_ORIGINS", "http://localhost:5000,http://localhost:3000,http://127.0.0.1:5000,http://127.0.0.1:3000")
# Parse comma-separated origins
ALLOWED_ORIGINS = [origin.strip() for origin in CORS_ORIGINS.split(",") if origin.strip()]

# Model paths - will be set based on selected model
MODEL_DIR = str(THOR_1_1_DIR / "models")  # Default to Thor 1.1
TOKENIZER_DIR = str(THOR_1_1_DIR / "models")
CONFIG_PATH = str(THOR_1_1_DIR / "config" / "config.yaml")

# Calculator model paths
CALC_MODEL_DIR = str(THOR_CALC_1_0_DIR / "models")
CALC_TOKENIZER_DIR = str(THOR_CALC_1_0_DIR / "models")
CALC_CONFIG_PATH = str(THOR_CALC_1_0_DIR / "config" / "config.yaml")

# Data directories
CHATS_DIR = str(DATA_ROOT / "chats")
CONVERSATIONS_DIR = str(DATA_ROOT / "conversations")
PROJECTS_DIR = str(DATA_ROOT / "projects")
HISTORY_DIR = str(DATA_ROOT / "history")

# Result setter files
THOR_1_0_RESULT_SETTER_FILE = str(BASE_DIR / "thor_result_setter.json")
THOR_1_1_RESULT_SETTER_FILE = str(BASE_DIR / "thor_1_1_result_setter.json")
THOR_RESULT_SETTER_FILE = THOR_1_1_RESULT_SETTER_FILE  # Default to latest

# Gems (custom sub-models)
GEMS_DIR = DATA_ROOT / "gems"
GEMS_FILE = GEMS_DIR / "gems.json"

# UI directories
UI_TEMPLATE_DIR = BASE_DIR / "ui" / "templates"
UI_STATIC_DIR = BASE_DIR / "ui" / "static"

# Ensure directories exist
def ensure_directories():
    """Create all necessary directories if they don't exist."""
    directories = [
        CHATS_DIR,
        CONVERSATIONS_DIR,
        MODEL_DIR,
        PROJECTS_DIR,
        HISTORY_DIR,
        str(GEMS_DIR),
        str(THOR_1_2_DIR / "models"),  # Thor 1.2: models/thor/thor-1.2/models
        str(THOR_1_2_DIR / "config"),  # Thor 1.2: models/thor/thor-1.2/config
    ]
    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
        except Exception:
            pass
    
    # Initialize gems file if it doesn't exist
    if not GEMS_FILE.exists():
        try:
            GEMS_FILE.parent.mkdir(parents=True, exist_ok=True)
            import json
            with open(GEMS_FILE, "w", encoding="utf-8") as f:
                json.dump({"gems": []}, f, indent=2)
        except Exception:
            pass

# Initialize directories on import
ensure_directories()

