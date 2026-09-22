"""Local LLM integration client for on-premise pedagogical feedback."""

import json
import logging
import re
from typing import Any, Generator
import httpx

from app.core.settings import get_settings

logger = logging.getLogger(__name__)


def sanitize_code_and_text(text: str) -> str:
    """Strip student identifiers, emails, and student ID patterns to ensure FERPA compliance."""
    if not text:
        return ""
    # Strip email addresses
    sanitized = re.sub(r"[\w\.-]+@[\w\.-]+\.\w+", "[REDACTED_EMAIL]", text)
    # Strip UVU-style IDs (e.g., 10123456 or U10123456 or A12345678)
    sanitized = re.sub(r"\b[AUau]?\d{7,8}\b", "[REDACTED_ID]", sanitized)
    # Strip common name/author header patterns in comments or metadata lines without corrupting code variables
    sanitized = re.sub(
        r"(?im)^([ \t]*(?:#|//|/\*|\*)\s*)(author|student(?:\s*name)?|name|submitted\s*by)\s*[:=]\s*[^\n\r]+",
        r"\1\2: [REDACTED_NAME]",
        sanitized,
    )
    sanitized = re.sub(
        r"(?im)^([ \t]*)(author|student(?:\s*name)?|submitted\s*by)\s*[:=]\s*[^\n\r]+",
        r"\1\2: [REDACTED_NAME]",
        sanitized,
    )
    return sanitized


class LocalLLMClient:
    """Client for querying a locally hosted LLM (e.g. Ollama or vLLM via OpenAI compatible API)."""

    def __init__(
        self,
        endpoint: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
        timeout_seconds: float = 30.0,
    ) -> None:
        settings = get_settings()
        self.endpoint = (
            endpoint or settings.local_llm_endpoint or "http://127.0.0.1:11434/v1"
        ).rstrip("/")
        self.api_key = api_key or settings.local_llm_api_key or "ollama"
        self.model = model or settings.local_llm_model or "qwen2.5:3b"
        self.timeout = timeout_seconds

    def generate_chat_completion(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 400,
    ) -> str:
        """Call the local LLM /chat/completions endpoint synchronously."""
        url = f"{self.endpoint}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
                content = data["choices"][0]["message"].get("content")
                return (content or "").strip()
        except httpx.ConnectError:
            logger.warning("Failed to connect to Local LLM at %s", self.endpoint)
            return (
                "⚠️ Local AI assistant is currently unreachable. "
                "Please make sure Ollama is running (`ollama serve`) and the model is available."
            )
        except httpx.TimeoutException:
            logger.warning("Local LLM request timed out at %s", self.endpoint)
            return (
                "⚠️ Local AI assistant request timed out. "
                "The local model is taking too long to generate feedback. Please try again."
            )
        except Exception as exc:
            logger.exception("Unexpected error communicating with local LLM: %s", exc)
            return "⚠️ An error occurred while generating AI feedback. Please try again later."

    def generate_chat_completion_stream(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 400,
    ) -> Generator[str, None, None]:
        """Stream chunks from the local LLM /chat/completions endpoint."""
        url = f"{self.endpoint}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                with client.stream("POST", url, json=payload, headers=headers) as response:
                    response.raise_for_status()
                    for line in response.iter_lines():
                        if not line:
                            continue
                        if line.startswith("data: "):
                            raw_json = line[6:].strip()
                            if raw_json == "[DONE]":
                                break
                            try:
                                chunk_data = json.loads(raw_json)
                                delta = chunk_data["choices"][0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    yield content
                            except Exception:
                                pass
        except httpx.ConnectError:
            yield "⚠️ Local AI assistant is currently unreachable. Please make sure Ollama is running."
        except httpx.TimeoutException:
            yield "⚠️ Local AI assistant request timed out."
        except Exception as exc:
            yield f"⚠️ Error generating AI feedback: {exc!s}"

    def build_sandbox_messages(
        self,
        assignment_title: str,
        code_files: dict[str, str],
        test_results: list[dict[str, Any]],
        allowed_concepts: list[str] | None = None,
        warnings: list[dict[str, str]] | None = None,
        failure_message: str | None = None,
    ) -> list[dict[str, str]]:
        """Construct compact, high-signal messages for local model inference."""
        system_prompt = (
            "You are a friendly, concise Computer Science Teaching Assistant at Utah Valley University.\n"
            "Pedagogical Rules:\n"
            "1. NEVER give the complete solution code or copy-paste code fixes.\n"
            "2. Give 2 to 3 concise, bulleted Socratic hints pointing to the specific function or logic to check.\n"
            "3. Keep your total response under 150 words.\n"
            "4. If all tests passed, congratulate them in one short sentence!"
        )

        user_content_parts = [f"### Assignment: {assignment_title}\n"]

        if allowed_concepts:
            user_content_parts.append(f"**Allowed Concepts:** {', '.join(allowed_concepts)}\n")

        if failure_message:
            user_content_parts.append(f"**Issue:** {sanitize_code_and_text(failure_message)}\n")

        if warnings:
            user_content_parts.append("**AST Warnings:**")
            for w in warnings:
                msg = sanitize_code_and_text(w.get("message", ""))
                user_content_parts.append(f"- {w.get('code', 'Warning')}: {msg}")
            user_content_parts.append("")

        if test_results:
            user_content_parts.append("**Test Results:**")
            for tr in test_results:
                name = tr.get("name") or tr.get("label") or "Test"
                outcome = tr.get("outcome") or (
                    "Passed" if tr.get("points_earned", 0) > 0 else "Failed"
                )
                user_content_parts.append(f"- {name}: {outcome}")
                for sub in tr.get("test_results", []):
                    if sub.get("outcome") != "passed":
                        msg = sanitize_code_and_text(sub.get("message") or "")
                        actual = sanitize_code_and_text(str(sub.get("actual", "")))
                        expected = sanitize_code_and_text(str(sub.get("expected", "")))
                        if msg:
                            user_content_parts.append(f"  * Error: {msg}")
                        if actual or expected:
                            user_content_parts.append(
                                f"  * Got: `{actual}` | Expected: `{expected}`"
                            )
            user_content_parts.append("")

        if code_files:
            user_content_parts.append("**Student Code:**")
            total_code_chars = 0
            max_file_chars = 4000
            max_total_chars = 8000
            for fname, code in code_files.items():
                if total_code_chars >= max_total_chars:
                    user_content_parts.append("... [additional files truncated due to context limits] ...\n")
                    break
                sanitized_fname = sanitize_code_and_text(fname)
                sanitized_code = sanitize_code_and_text(code).replace("```", "'''")
                remaining_budget = max_total_chars - total_code_chars
                max_chars = min(max_file_chars, remaining_budget)
                if len(sanitized_code) > max_chars:
                    sanitized_code = sanitized_code[:max_chars] + "\n... [truncated] ..."
                total_code_chars += len(sanitized_code)
                user_content_parts.append(f"```{sanitized_fname}\n{sanitized_code}\n```\n")

        user_content_parts.append("Provide concise Socratic hints to help me fix my code.")
        user_prompt = "\n".join(user_content_parts)

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

    def generate_sandbox_feedback(
        self,
        assignment_title: str,
        code_files: dict[str, str],
        test_results: list[dict[str, Any]],
        allowed_concepts: list[str] | None = None,
        warnings: list[dict[str, str]] | None = None,
        failure_message: str | None = None,
    ) -> str:
        messages = self.build_sandbox_messages(
            assignment_title=assignment_title,
            code_files=code_files,
            test_results=test_results,
            allowed_concepts=allowed_concepts,
            warnings=warnings,
            failure_message=failure_message,
        )
        return self.generate_chat_completion(messages)

    def generate_sandbox_feedback_stream(
        self,
        assignment_title: str,
        code_files: dict[str, str],
        test_results: list[dict[str, Any]],
        allowed_concepts: list[str] | None = None,
        warnings: list[dict[str, str]] | None = None,
        failure_message: str | None = None,
    ) -> Generator[str, None, None]:
        messages = self.build_sandbox_messages(
            assignment_title=assignment_title,
            code_files=code_files,
            test_results=test_results,
            allowed_concepts=allowed_concepts,
            warnings=warnings,
            failure_message=failure_message,
        )
        yield from self.generate_chat_completion_stream(messages)
