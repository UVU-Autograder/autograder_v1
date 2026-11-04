"""AI-assisted pytest test case authoring for instructors (Issue #33)."""

from __future__ import annotations

import ast
import json
import logging
import re
from pathlib import Path
from typing import Any

import httpx
from pydantic import BaseModel, Field

from app.domains.grading.python_helpers import load_python_helpers_payload
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
You are an expert Python and pytest curriculum assistant for Utah Valley University Computer Science courses.
Your task is to author or revise automated pytest test suites for student code based on assignment specifications and scoring rubrics.

CRITICAL RULES:
1. Marker Mapping: Every `def test_*` function MUST be decorated with `@pytest.mark.ag_<key>` matching one of the rubric scoring keys provided in the prompt.
2. Assertions with Informative Feedback: Every `assert` statement MUST include an educational failure message explaining what went wrong (e.g., `assert actual == expected, f"fizz_buzz({n}) returned {actual!r}, expected {expected!r}"`). Never leak hidden solutions or dump raw internal exceptions.
3. Prefer Standard Pytest: Default to ordinary Python imports (`import account`), pytest's `capsys` fixture (or `bounded_output`) for stdout, and `monkeypatch` for `input()`. Do NOT generate `from autograder_capture import BoundedOutput` for new suites. Import from `python_autograder_helpers` ONLY when the AVAILABLE_RUNTIME_HELPERS notes require it (stdlib/pip filename collisions, import-time input(), or long multi-prompt CLI mocks).
4. Resilient Function Resolution: Student submissions often have slight naming variations or casing differences. Use defensive symbol resolution:
   - Example 1 (Direct import & alias fallback):
     ```python
     import math_ops  # entrypoint module

     # Check exact name or common variants
     func = getattr(math_ops, "add_numbers", getattr(math_ops, "addNumbers", None))
     assert func is not None, "Function 'add_numbers' not found in submission."
     ```
   - Example 2 (Heuristic discovery for single-function assignments):
     ```python
     import inspect
     # If primary name is missing, locate student's primary function
     if func is None:
         candidates = [
             fn for name, fn in inspect.getmembers(math_ops, inspect.isfunction)
             if not name.startswith("_") and name != "main"
         ]
         assert candidates, "No callable functions found in submission."
         func = candidates[0]
     ```
5. Test Quality: Cover standard cases, boundary/edge conditions (e.g. empty inputs, zero, negative numbers, large values), and type/attribute requirements. Keep tests concise and independent.
6. Revision Mode: When CURRENT TESTS.PY is provided, treat the request as an incremental revision—retain existing good tests, apply the requested updates, and return the complete suite. You may keep existing helper imports when revising code that already depends on them.
7. Valid Standalone Python: Generated code MUST be syntactically valid Python 3.11 with `import pytest`. Do not wrap the JSON output in markdown blocks outside the JSON.
8. Output Schema: Respond ONLY with a single valid JSON object:
{"generated_code": string, "explanation": string}
"""

def _extract_reference_symbols(code: str | None) -> dict[str, list[str]]:
    """Extract top-level functions and classes from reference solution code via AST."""
    if not code or not code.strip():
        return {"functions": [], "classes": []}
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return {"functions": [], "classes": []}

    functions: list[str] = []
    classes: list[str] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not node.name.startswith("_"):
                functions.append(node.name)
        elif isinstance(node, ast.ClassDef):
            if not node.name.startswith("_"):
                classes.append(node.name)
    return {"functions": functions, "classes": classes}


def _format_user_prompt(
    *,
    course_id: str | None,
    assignment_title: str,
    description: str | None,
    entrypoint: str,
    scoring_items: list[dict[str, Any]],
    allowed_concepts: list[str] | None,
    model_solution_code: str | None,
    request: AITestAuthoringRequest,
) -> str:
    """Format structured user prompt for test generation."""
    clean_desc = sanitize_code_and_text((description or "").strip()[:4000])
    clean_instr = sanitize_code_and_text((request.instruction or "").strip()[:3000])
    clean_tests = sanitize_code_and_text((request.current_test_code or "").strip()[:8000])
    clean_model = sanitize_code_and_text((model_solution_code or "").strip()[:8000])

    module_stem = Path(entrypoint).stem if entrypoint else "solution"

    sections: list[str] = []

    # 1. Assignment Context
    course_display = course_id.upper() if course_id else "UVU Computer Science"
    overview_lines = [
        "### Assignment Context",
        f"- Course: {course_display}",
        f"- Title: {sanitize_code_and_text(assignment_title)}",
        f"- Entrypoint File: `{sanitize_code_and_text(entrypoint)}`",
        f"- Entrypoint Python Module: `{module_stem}` (e.g. `import {module_stem}`)",
    ]
    if allowed_concepts:
        overview_lines.append(f"- Allowed Concepts: {', '.join(allowed_concepts)}")
    sections.append("\n".join(overview_lines))

    # 2. Detected Reference Symbols (if reference code provided)
    symbols = _extract_reference_symbols(clean_model)
    if symbols["functions"] or symbols["classes"]:
        sym_lines = ["### Target Symbols Detected in Reference Solution"]
        if symbols["functions"]:
            sym_lines.append(f"- Functions: {', '.join(f'`{fn}`' for fn in symbols['functions'])}")
        if symbols["classes"]:
            sym_lines.append(f"- Classes: {', '.join(f'`{cls}`' for cls in symbols['classes'])}")
        sections.append("\n".join(sym_lines))

    # 3. Rubric Scoring Keys
    rubric_lines = ["### Rubric Scoring Keys (use @pytest.mark.ag_<key>)"]
    pytest_items = [
        item for item in scoring_items
        if item.get("item_type", "pytest") == "pytest"
    ]
    if pytest_items:
        for item in pytest_items:
            key = item.get("key", "").strip()
            label = item.get("label", "")
            pts = item.get("points", 0)
            rubric_lines.append(f"- `ag_{key}`: {label} ({pts} pts)")
    else:
        rubric_lines.append("- (No scoring keys configured; define descriptive `ag_<key>` markers)")
    sections.append("\n".join(rubric_lines))

    # 4. Assignment Description
    if clean_desc:
        sections.append(f"### Assignment Description\n{clean_desc}")

    # 5. Instructor Instructions (only if provided)
    if clean_instr:
        sections.append(f"### Instructor Instructions\n{clean_instr}")

    # 6. Current Tests (if revising)
    if clean_tests:
        sections.append(f"### Current tests.py\n```python\n{clean_tests}\n```")

    # 7. Reference Solution Code (if available)
    if clean_model:
        sections.append(f"### Reference Solution Code\n```python\n{clean_model}\n```")

    # 8. Platform helpers available in the sandbox (same file instructors can view)
    helpers = load_python_helpers_payload()
    sections.append(
        "### AVAILABLE_RUNTIME_HELPERS\n"
        f"{helpers.usage_notes}\n\n"
        f"Injected sandbox file `{helpers.filename}`:\n"
        f"```python\n{helpers.source}\n```"
    )

    return "\n\n".join(sections)


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
    course_id: str | None = None,
    llm_client: LocalLLMClient | None = None,
) -> AITestAuthoringResponse:
    """Generate instructor pytest cases via local vLLM."""
    client = llm_client or LocalLLMClient(timeout_seconds=15.0)

    user_prompt = _format_user_prompt(
        course_id=course_id,
        assignment_title=assignment_title,
        description=description,
        entrypoint=entrypoint,
        scoring_items=scoring_items,
        allowed_concepts=allowed_concepts,
        model_solution_code=model_solution_code,
        request=request,
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
            "max_tokens": 1500,
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
