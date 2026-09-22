"""Minimal OpenAI-compatible chat client.

Works unchanged against LM Studio (:1234), Ollama (:11434/v1), and vLLM (:8000/v1),
so the same harness scores the Mac baseline and the Dell deployment.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

import httpx

from app.integrations.ai.prompts import GENERATION_TEMPERATURE, MAX_OUTPUT_TOKENS

PRESETS = {
    "lmstudio": "http://127.0.0.1:1234/v1",
    "ollama": "http://127.0.0.1:11434/v1",
    "vllm": "http://127.0.0.1:8001/v1",  # backend owns 8000 on the Dell
}


@dataclass
class Completion:
    text: str
    latency_s: float
    prompt_tokens: int = 0
    completion_tokens: int = 0


class ChatClient:
    def __init__(
        self,
        base_url: str,
        model: str,
        *,
        api_key: str = "not-needed",
        temperature: float = GENERATION_TEMPERATURE,
        max_tokens: int = MAX_OUTPUT_TOKENS,
        timeout: float = 180.0,
        json_schema: dict | None = None,
    ) -> None:
        self.base_url = PRESETS.get(base_url, base_url).rstrip("/")
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.json_schema = json_schema
        self._client = httpx.Client(
            timeout=timeout, headers={"Authorization": f"Bearer {api_key}"}
        )

    def complete(self, messages: list[dict[str, str]]) -> Completion:
        payload: dict = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        if self.json_schema is not None:
            # Honored by LM Studio and vLLM; harmlessly ignored elsewhere.
            payload["response_format"] = {
                "type": "json_schema",
                "json_schema": {"name": "feedback", "schema": self.json_schema, "strict": True},
            }

        started = time.perf_counter()
        response = self._client.post(f"{self.base_url}/chat/completions", json=payload)
        elapsed = time.perf_counter() - started
        response.raise_for_status()
        data = response.json()
        usage = data.get("usage") or {}
        return Completion(
            text=data["choices"][0]["message"]["content"] or "",
            latency_s=elapsed,
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
        )

    def close(self) -> None:
        self._client.close()
