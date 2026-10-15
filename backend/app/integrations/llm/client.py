"""Local LLM integration client for on-premise pedagogical feedback."""

import json
import logging
from dataclasses import dataclass
from typing import Any, Generator, Literal
import httpx

from app.core.settings import get_settings
from app.integrations.ai import prompts
from app.integrations.ai.guardrails import gate_names, validate_feedback
from app.integrations.ai.sanitize import sanitize_code_and_text

__all__ = ["LocalLLMClient", "sanitize_code_and_text", "FEEDBACK_UNAVAILABLE"]

# Shown instead of any model output that fails the guardrails. Never show
# unvalidated text: a score or a full solution on screen can't be retracted.
FEEDBACK_UNAVAILABLE = (
    "The AI assistant couldn't produce hints that passed our accuracy checks for this run. "
    "Your test results above are complete and correct -- start with the first failing test "
    "and compare what your code produced with what was expected."
)

UNREACHABLE_MESSAGE = (
    "⚠️ Local AI assistant is currently unreachable. "
    "Please make sure the model server is running and the model is available."
)
TIMEOUT_MESSAGE = "⚠️ Local AI assistant request timed out. Please try again."
ERROR_MESSAGE = "⚠️ An error occurred while generating AI feedback. Please try again later."

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class FeedbackOutcome:
    """What happened when asking the model for feedback, plus the text to show.

    ``ok`` and ``guardrail`` are answers (the guardrail text is the safe fallback);
    ``timeout``, ``unreachable`` and ``error`` mean no answer was produced.
    """

    kind: Literal["ok", "guardrail", "timeout", "unreachable", "error"]
    text: str


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
            endpoint or settings.local_llm_endpoint or "http://127.0.0.1:8001/v1"
        ).rstrip("/")
        self.api_key = api_key or settings.local_llm_api_key or "none"
        self.model = model or settings.local_llm_model or "cs1410-p3b"
        # Each model gets the prompt it was trained on (p3b: v8, p4: v9).
        self.prompt_version = settings.prompt_version_for(self.model)
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
                "Please make sure the local feedback service is running and the model is available."
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
            yield "⚠️ Local AI assistant is currently unreachable. Please make sure the local feedback service is running."
        except httpx.TimeoutException:
            yield "⚠️ Local AI assistant request timed out."
        except Exception as exc:
            yield f"⚠️ Error generating AI feedback: {exc!s}"

    def _complete_structured(self, messages: list[dict[str, str]]) -> str:
        """One non-streamed completion, asking the server to enforce the JSON schema.

        Raises on transport/HTTP errors so the caller can pick the right message.
        Servers that reject ``response_format`` get one retry without it; the
        guardrails still validate whatever comes back.
        """
        url = f"{self.endpoint}/chat/completions"
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"}
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": prompts.GENERATION_TEMPERATURE,
            "max_tokens": prompts.MAX_OUTPUT_TOKENS,
            "response_format": {
                "type": "json_schema",
                "json_schema": {"name": "feedback", "schema": prompts.RESPONSE_JSON_SCHEMA, "strict": True},
            },
        }
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(url, json=payload, headers=headers)
            if response.status_code in (400, 422):
                payload.pop("response_format")
                response = client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return (response.json()["choices"][0]["message"].get("content") or "").strip()

    def build_sandbox_messages(
        self,
        assignment_title: str,
        code_files: dict[str, str],
        test_results: list[dict[str, Any]],
        allowed_concepts: list[str] | None = None,
        warnings: list[dict[str, str]] | None = None,
        failure_message: str | None = None,
        requirements: str | None = None,
    ) -> list[dict[str, str]]:
        """Messages for the sandbox, built by the shared prompt module (see prompts.py)."""
        failures, passing = prompts.failures_from_test_results(test_results, failure_message)
        violations = [f"{w.get('code', 'warning')}: {w.get('message', '')}" for w in (warnings or [])]
        return prompts.build_messages(
            prompt_version=self.prompt_version,
            assignment_title=assignment_title,
            requirements=requirements or "",
            allowed_concepts=allowed_concepts or [],
            failures=failures,
            concept_violations=violations,
            # Not a .py name: unreadable files must not be reported as an empty submission.
            code_files=code_files or {"(no Python files could be read)": ""},
            passing_labels=passing,
        )

    def generate_sandbox_feedback(
        self,
        assignment_title: str,
        code_files: dict[str, str],
        test_results: list[dict[str, Any]],
        allowed_concepts: list[str] | None = None,
        warnings: list[dict[str, str]] | None = None,
        failure_message: str | None = None,
        requirements: str | None = None,
        reference_files: dict[str, str] | None = None,
    ) -> str:
        """Generate, validate, and render feedback. Only validated text is returned."""
        return self.generate_sandbox_feedback_outcome(
            assignment_title=assignment_title,
            code_files=code_files,
            test_results=test_results,
            allowed_concepts=allowed_concepts,
            warnings=warnings,
            failure_message=failure_message,
            requirements=requirements,
            reference_files=reference_files,
        ).text

    def generate_sandbox_feedback_outcome(
        self,
        assignment_title: str,
        code_files: dict[str, str],
        test_results: list[dict[str, Any]],
        allowed_concepts: list[str] | None = None,
        warnings: list[dict[str, str]] | None = None,
        failure_message: str | None = None,
        requirements: str | None = None,
        reference_files: dict[str, str] | None = None,
    ) -> FeedbackOutcome:
        """Like generate_sandbox_feedback, but says whether the model actually answered.

        ``reference_files`` (the assignment's model solution) only feed the
        guardrails; they are never part of the prompt.
        """
        failures, passing = prompts.failures_from_test_results(test_results, failure_message)
        messages = self.build_sandbox_messages(
            assignment_title=assignment_title,
            code_files=code_files,
            test_results=test_results,
            allowed_concepts=allowed_concepts,
            warnings=warnings,
            failure_message=failure_message,
            requirements=requirements,
        )
        try:
            raw = self._complete_structured(messages)
        except httpx.ConnectError:
            logger.warning("Failed to connect to Local LLM at %s", self.endpoint)
            return FeedbackOutcome("unreachable", UNREACHABLE_MESSAGE)
        except httpx.TimeoutException:
            logger.warning("Local LLM request timed out at %s", self.endpoint)
            return FeedbackOutcome("timeout", TIMEOUT_MESSAGE)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Local LLM request failed: %s", type(exc).__name__)
            return FeedbackOutcome("error", ERROR_MESSAGE)

        try:
            parsed = prompts.parse_response(raw)
        except ValueError:
            logger.warning("Local LLM feedback rejected: response was not valid FeedbackResponse JSON")
            return FeedbackOutcome("guardrail", FEEDBACK_UNAVAILABLE)

        # Defining a symbol from the student's code or the model solution is writing their code.
        labels = [f"{f['key']} {f.get('label', '')}" for f in failures] + passing
        forbidden, known = gate_names(code_files or {}, reference_files, labels)
        reasons = validate_feedback(
            parsed, {f["key"] for f in failures}, forbidden,
            known_names=known, placeholder=prompts.submission_is_placeholder(code_files or {}),
        )
        if reasons:
            # Reasons name checks and test keys only -- never student code or text.
            logger.warning("Local LLM feedback rejected by guardrails: %s", "; ".join(reasons))
            return FeedbackOutcome("guardrail", FEEDBACK_UNAVAILABLE)
        return FeedbackOutcome("ok", prompts.render_markdown(parsed, {f["key"]: f["label"] for f in failures}))

    def generate_sandbox_feedback_stream(
        self,
        assignment_title: str,
        code_files: dict[str, str],
        test_results: list[dict[str, Any]],
        allowed_concepts: list[str] | None = None,
        warnings: list[dict[str, str]] | None = None,
        failure_message: str | None = None,
        requirements: str | None = None,
        reference_files: dict[str, str] | None = None,
    ) -> Generator[str, None, None]:
        """Stream *validated* feedback, line by line.

        Generation finishes and passes the guardrails before the first chunk is
        sent. Token-by-token streaming would put unchecked text on screen.
        """
        text = self.generate_sandbox_feedback(
            assignment_title=assignment_title,
            code_files=code_files,
            test_results=test_results,
            allowed_concepts=allowed_concepts,
            warnings=warnings,
            failure_message=failure_message,
            requirements=requirements,
            reference_files=reference_files,
        )
        yield from text.splitlines(keepends=True)
