"""AI-assisted pytest test case authoring for instructors (Issue #33)."""

from __future__ import annotations

import ast
import json
import logging
import re
from typing import Any

import httpx
from pydantic import BaseModel, Field

from app.integrations.ai.sanitize import sanitize_code_and_text
from app.integrations.llm.client import LocalLLMClient

logger = logging.getLogger(__name__)

MARKER_RE = re.compile(r"@pytest\.mark\.ag_([a-z][a-z0-9_]*)")


class AITestAuthoringRequest(BaseModel):
    instruction: str | None = Field(
        default=None,
        max_length=4000,
        description="Assignment specification or test generation instructions.",
    )
    current_test_code: str | None = Field(
        default=None,
        max_length=25000,
        description="Current tests.py source code in the editor.",
    )


class AITestAuthoringResponse(BaseModel):
    generated_code: str
    explanation: str


INSTRUCTOR_AUTHORING_SYSTEM_PROMPT = """\
You are an expert Python & pytest curriculum assistant for CS 1410 at Utah Valley University.
Your job is to help course instructors author and revise automated pytest test suites from an assignment specification.

RULES:
1. Every generated test function MUST be decorated with `@pytest.mark.ag_<key>` where `<key>` is a lowercase snake_case scoring key (e.g. `@pytest.mark.ag_basic_ops`).
2. Every `assert` statement MUST include a descriptive failure message explaining the expected behavior without leaking full reference code.
3. Include edge cases appropriate to the specification (e.g. empty collections, boundary numbers, zero/negative inputs, type or attribute checks).
4. Generated code MUST be valid, standalone Python 3.11 syntax using `import pytest`.
5. When CURRENT TESTS.PY is non-empty, treat the instructor specification as a revision request: keep unmarked structure that still fits, apply the requested changes, and return the full updated suite (not a fragment).
6. Respond with a single JSON object matching this schema:
{"generated_code": string, "explanation": string}
"""


def _validate_generated_pytest_code(code: str) -> tuple[bool, str]:
    """Verify generated code is valid Python and contains pytest functions and ag_ markers."""
    cleaned = code.strip()
    if not cleaned:
        return False, "Generated code is empty."
    try:
        tree = ast.parse(cleaned)
    except SyntaxError as exc:
        return False, f"Generated code has a Python syntax error: {exc.msg} (line {exc.lineno})"

    has_test_func = any(
        isinstance(node, ast.FunctionDef) and node.name.startswith("test_")
        for node in ast.walk(tree)
    )
    if not has_test_func:
        return False, "Generated code must define at least one `def test_*` function."

    if not MARKER_RE.search(cleaned):
        return False, "Generated code must include at least one `@pytest.mark.ag_<key>` decorator."

    return True, ""


def generate_instructor_tests(
    *,
    assignment_title: str,
    description: str | None,
    entrypoint: str,
    scoring_items: list[dict[str, Any]],
    allowed_concepts: list[str] | None,
    model_solution_code: str | None,
    request: AITestAuthoringRequest,
    llm_client: LocalLLMClient | None = None,
) -> AITestAuthoringResponse:
    """Generate instructor pytest cases via local vLLM."""
    client = llm_client or LocalLLMClient(timeout_seconds=15.0)

    clean_desc = sanitize_code_and_text((description or "").strip()[:1500])
    clean_instr = sanitize_code_and_text((request.instruction or "").strip()[:2000])
    clean_tests = sanitize_code_and_text((request.current_test_code or "").strip()[:6000])
    clean_model = sanitize_code_and_text((model_solution_code or "").strip()[:6000])

    rubric_summary = "\n".join(
        f"- ag_{item.get('key')}: {item.get('label')} ({item.get('points', 0)} pts)"
        for item in scoring_items
        if item.get("item_type", "pytest") == "pytest"
    )

    user_prompt = (
        f"ASSIGNMENT: {sanitize_code_and_text(assignment_title)}\n"
        f"ENTRYPOINT: {sanitize_code_and_text(entrypoint)}\n"
        f"ALLOWED CONCEPTS: {', '.join(allowed_concepts or []) or '(unrestricted)'}\n\n"
        f"RUBRIC SCORING KEYS:\n{rubric_summary or '(none configured yet)'}\n\n"
        f"ASSIGNMENT DESCRIPTION:\n{clean_desc or '(none)'}\n\n"
        f"INSTRUCTOR SPECIFICATION:\n{clean_instr or clean_desc or '(generate pytest cases with @pytest.mark.ag_* markers)'}\n\n"
        f"CURRENT TESTS.PY:\n{clean_tests or '(empty)'}\n\n"
        f"REFERENCE SOLUTION:\n{clean_model or '(not provided)'}\n"
    )

    messages = [
        {"role": "system", "content": INSTRUCTOR_AUTHORING_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    try:
        url = f"{client.endpoint}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {client.api_key}",
        }
        payload: dict[str, Any] = {
            "model": client.model,
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": 1200,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "instructor_test_authoring",
                    "schema": AITestAuthoringResponse.model_json_schema(),
                    "strict": True,
                },
            },
        }
        with httpx.Client(timeout=client.timeout) as http:
            resp = http.post(url, json=payload, headers=headers)
            if resp.status_code in (400, 422):
                payload.pop("response_format", None)
                resp = http.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            raw_content = (resp.json()["choices"][0]["message"].get("content") or "").strip()

        parsed_json = json.loads(raw_content)
        candidate = AITestAuthoringResponse.model_validate(parsed_json)
    except Exception as exc:
        logger.warning("Local LLM test authoring request failed: %s", type(exc).__name__)
        raise RuntimeError(
            "Local AI service is unavailable or returned an invalid response."
        ) from exc

    valid, reason = _validate_generated_pytest_code(candidate.generated_code)
    if not valid:
        raise RuntimeError(f"AI generated invalid pytest code: {reason}")

    return candidate
