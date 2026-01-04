"""
External LLM judge (OpenAI-compatible) for rubric scoring.

This module is designed to be used in offline evaluation runs (no training-time dependency).
It expects an OpenAI-compatible Chat Completions endpoint.

Environment variables:
  - OPENAI_API_KEY: required
  - OPENAI_BASE_URL: optional (default: https://api.openai.com/v1)
  - OPENAI_MODEL: optional (default: gpt-4o-mini)
"""

from __future__ import annotations

import json
import os
import urllib.request
from typing import Any, Dict, Optional


class OpenAICompatibleJudge:
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout_s: int = 60,
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = (base_url or os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1").rstrip("/")
        self.model = model or os.getenv("OPENAI_MODEL") or "gpt-4o-mini"
        self.timeout_s = timeout_s

        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is required for OpenAICompatibleJudge.")

    def judge(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """
        Returns the judge JSON object (parsed).
        Raises on HTTP errors or invalid JSON output.
        """
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }

        req = urllib.request.Request(
            url=url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
            raw = resp.read().decode("utf-8")
            data = json.loads(raw)

        content = (
            data.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
            .strip()
        )

        # Some models wrap JSON in code fences; strip if present.
        if content.startswith("```"):
            content = content.strip("`")
            # Try to remove a leading language tag line if present.
            lines = content.splitlines()
            if lines and lines[0].lower().strip() in {"json", "javascript"}:
                content = "\n".join(lines[1:])

        return json.loads(content)


