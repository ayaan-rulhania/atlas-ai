"""Vercel entrypoint.

Vercel's Python runtime will treat this module as a serverless function.
Exporting the Flask WSGI app as `app` allows Vercel to route all requests
through the Flask router (/, /api/chat, /dev-atlas, /static/*, etc.).

This deployment uses `chatbot/lite_app.py` to avoid depending on `thor-1.0/`
when the deployment root is `chatbot/`.
"""

from lite_app import app  # noqa: F401
