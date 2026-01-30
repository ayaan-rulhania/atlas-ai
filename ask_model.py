#!/usr/bin/env python3
"""
Quick CLI to test/talk to Atlas AI models (Thor 1.0, Thor 1.1, etc.).

Usage:
  # Interactive mode (prompt for messages until you type /quit or Ctrl+C)
  python ask_model.py

  # One-shot message
  python ask_model.py "What is 2+2?"

  # Custom port (default 5002 when chatbot runs via start_chatbot_thor11.sh)
  python ask_model.py --port 5000 "Hello"

  # Use Thor 1.0 instead of 1.1
  python ask_model.py --model thor-1.0 "Hello"

Requires the Atlas chatbot to be running. Start it with:
  ./start_chatbot_thor11.sh
or
  cd apps/chatbot && PORT=5002 python3 app.py
"""

from __future__ import annotations

import argparse
import json
import sys
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

DEFAULT_PORT = 5002
TIMEOUT = 180


def chat(base_url: str, message: str, model: str = "thor-1.1", chat_id: str | None = None) -> dict:
    """Send a message to /api/chat and return the JSON response."""
    url = f"{base_url.rstrip('/')}/api/chat"
    payload = {"message": message, "model": model}
    if chat_id:
        payload["chat_id"] = chat_id
    body = json.dumps(payload).encode("utf-8")
    req = Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    with urlopen(req, timeout=TIMEOUT) as r:
        return json.loads(r.read().decode("utf-8"))


def check_server(base_url: str) -> bool:
    """Quick health check: GET /api/model/status."""
    try:
        req = Request(f"{base_url.rstrip('/')}/api/model/status")
        with urlopen(req, timeout=5) as r:
            r.read()
        return True
    except Exception:
        return False


def main() -> int:
    ap = argparse.ArgumentParser(description="Talk to Thor 1.1 via Atlas chatbot API")
    ap.add_argument("message", nargs="*", help="Message to send (omit for interactive mode)")
    ap.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"Chatbot port (default: {DEFAULT_PORT})")
    ap.add_argument("--host", default="127.0.0.1", help="Chatbot host (default: 127.0.0.1)")
    ap.add_argument("--model", default="thor-1.1", help="Model: thor-1.1 (default) or thor-1.0")
    args = ap.parse_args()
    base_url = f"http://{args.host}:{args.port}"
    model = args.model

    if not check_server(base_url):
        print("Chatbot not reachable.")
        print(f"  Tried: {base_url}")
        print("Start it first with:")
        print("  ./start_chatbot_thor11.sh")
        print("  or: cd apps/chatbot && PORT=5002 python3 app.py")
        return 1

    chat_id: str | None = None
    one_shot = " ".join(args.message).strip() if args.message else ""

    if one_shot:
        try:
            out = chat(base_url, one_shot, model=model, chat_id=chat_id)
        except HTTPError as e:
            body = e.read().decode("utf-8") if e.fp else ""
            try:
                err = json.loads(body)
                print("Error:", err.get("error", body))
            except Exception:
                print("Error:", body or str(e))
            return 1
        except URLError as e:
            print("Request failed:", e.reason)
            return 1
        except Exception as e:
            print("Error:", e)
            return 1

        if "error" in out:
            print("Error:", out["error"])
            return 1
        text = out.get("response", "")
        model_used = out.get("model_used", f"Atlas AI ({model})")
        print(f"[{model_used}]\n{text}")
        return 0

    # Interactive
    print(f"Atlas AI chat ({model} model). Type /quit or Ctrl+C to exit.")
    print(f"Connected to {base_url}\n")
    while True:
        try:
            line = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            return 0
        if not line:
            continue
        if line.lower() in ("/quit", "/exit", "/q"):
            print("Bye.")
            return 0
        try:
            out = chat(base_url, line, model=model, chat_id=chat_id)
        except HTTPError as e:
            body = e.read().decode("utf-8") if e.fp else ""
            try:
                err = json.loads(body)
                print("Error:", err.get("error", body))
            except Exception:
                print("Error:", body or str(e))
            continue
        except URLError as e:
            print("Request failed:", e.reason)
            continue
        except Exception as e:
            print("Error:", e)
            continue

        if "error" in out:
            print("Error:", out["error"])
            continue
        chat_id = out.get("chat_id") or chat_id
        text = out.get("response", "")
        model_used = out.get("model_used", f"Atlas AI ({model})")
        print(f"\n[{model_used}]\n{text}\n")


if __name__ == "__main__":
    sys.exit(main())
