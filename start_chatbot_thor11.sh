#!/bin/bash
# Start Atlas chatbot on port 5002 (avoids conflict with port 5000, e.g. AirPlay on macOS).
# Use this when you want to test/talk to Thor 1.1 via the UI or ask_model.py.

set -e
cd "$(dirname "$0")"

if [ -n "$VIRTUAL_ENV" ]; then
  :  # already in venv
elif [ -d ".venv" ]; then
  source .venv/bin/activate
elif [ -d ".venv-cli" ]; then
  source .venv-cli/bin/activate
else
  echo "No .venv or .venv-cli found. Activate a venv with Python + Flask deps, or create one."
  exit 1
fi

PORT=5002
export PORT

echo "Starting Atlas chatbot (Thor 1.1) on port $PORT..."
echo "  UI:    http://localhost:$PORT"
echo "  CLI:   python ask_model.py --port $PORT \"Your message\""
echo ""

cd apps/chatbot
exec python3 app.py
