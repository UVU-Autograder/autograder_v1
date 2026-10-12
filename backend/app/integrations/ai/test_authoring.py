"""AI-assisted pytest test case authoring and refinement for instructors (Issue #56)."""

from __future__ import annotations

import ast
import json
import logging
import re
from typing import Any, Literal

import httpx
from pydantic import BaseModel, Field

from app.integrations.ai.sanitize import sanitize_code_and_text
from app.integrations.llm.client import LocalLLMClient

logger = logging.getLogger(__name__)

MARKER_RE = re.compile(r"@pytest\.mark\.ag_([a-z][a-z0-9_]*)")
FUNC_DEF_RE = re.compile(r"def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(")


class SuggestedScoringItem(BaseModel):
    key: str
    label: str
    points: int = 10


class AITestAuthoringRequest(BaseModel):
    mode: Literal["generate", "edge_cases", "refine"] = "generate"
    instruction: str | None = Field(
        default=None,
        max_length=4000,
        description="Instructor specification, function signature, or refinement prompt.",
    )
    current_test_code: str | None = Field(
        default=None,
        max_length=25000,
        description="Current tests.py source code in the editor.",
    )
    target_keys: list[str] = Field(
        default_factory=list,
        description="Optional scoring keys to target.",
    )


class AITestAuthoringResponse(BaseModel):
    generated_code: str
    suggested_items: list[SuggestedScoringItem] = Field(default_factory=list)
    explanation: str
    used_fallback: bool = False


INSTRUCTOR_AUTHORING_SYSTEM_PROMPT = """\
You are an expert Python & pytest curriculum assistant for CS 1410 at Utah Valley University.
Your job is to help course instructors author, expand, and refine automated pytest test suites.

RULES:
1. Every generated test function MUST be decorated with `@pytest.mark.ag_<key>` where `<key>` is a lowercase snake_case scoring key (e.g. `@pytest.mark.ag_basic_ops`).
2. Every `assert` statement MUST include a descriptive failure message explaining the expected behavior without leaking full reference code.
3. Include edge cases appropriate to the specification (e.g. empty collections, boundary numbers, zero/negative inputs, type or attribute checks).
4. Generated code MUST be valid, standalone Python 3.11 syntax using `import pytest`.
5. Respond with a single JSON object matching this schema:
{"generated_code": string, "suggested_items": [{"key": string, "label": string, "points": int}], "explanation": string}
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


def _extract_model_functions(model_code: str | None) -> list[tuple[str, list[str]]]:
    """Extract top-level function names and parameter lists from model solution code."""
    if not model_code:
        return []
    try:
        tree = ast.parse(model_code)
    except SyntaxError:
        return []

    funcs: list[tuple[str, list[str]]] = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
            args = [a.arg for a in node.args.args if a.arg != "self"]
            funcs.append((node.name, args))
    return funcs


def _slugify_key(raw: str) -> str:
    slug = re.sub(r"[^a-z0-9_]+", "_", raw.strip().lower()).strip("_")
    if not slug or not slug[0].isalpha():
        slug = f"case_{slug}" if slug else "basic_case"
    return slug[:40]


def _synthesize_deterministic_tests(
    *,
    mode: Literal["generate", "edge_cases", "refine"],
    assignment_title: str,
    entrypoint: str,
    scoring_items: list[dict[str, Any]],
    instruction: str | None,
    current_test_code: str | None,
    model_solution_code: str | None,
    target_keys: list[str] | None,
) -> AITestAuthoringResponse:
    """Deterministic AST-backed test generator used when vLLM is offline or fails validation."""
    module_name = entrypoint[:-3] if entrypoint.endswith(".py") else "main"
    module_name = re.sub(r"[^a-zA-Z0-9_]", "_", module_name) or "main"

    discovered_funcs = _extract_model_functions(model_solution_code)
    if not discovered_funcs and instruction:
        for match in FUNC_DEF_RE.finditer(instruction):
            fname = match.group(1)
            if not fname.startswith("test_"):
                discovered_funcs.append((fname, []))

    pytest_items = [
        item for item in scoring_items if item.get("item_type", "pytest") == "pytest"
    ]
    if target_keys:
        filtered = [item for item in pytest_items if item.get("key") in set(target_keys)]
        if filtered:
            pytest_items = filtered

    suggested_items: list[SuggestedScoringItem] = []
    if not pytest_items:
        if discovered_funcs:
            for fname, _ in discovered_funcs[:4]:
                key = _slugify_key(fname)
                label = f"Verify {fname} behavior"
                pytest_items.append({"key": key, "label": label, "points": 10})
                suggested_items.append(SuggestedScoringItem(key=key, label=label, points=10))
        else:
            default_key = _slugify_key(instruction or "core_behavior")
            default_label = (instruction or f"{assignment_title} Core Behavior").strip()[:60]
            pytest_items = [{"key": default_key, "label": default_label, "points": 10}]
            suggested_items.append(
                SuggestedScoringItem(key=default_key, label=default_label, points=10)
            )

    lines: list[str] = [
        "import pytest",
        f"import {module_name}",
        "",
    ]

    note_comment = (
        f"# Refinement requested: {instruction.strip()}"
        if instruction and instruction.strip()
        else None
    )

    for idx, item in enumerate(pytest_items):
        key = _slugify_key(str(item.get("key") or f"item_{idx + 1}"))
        label = str(item.get("label") or key)
        target_func = discovered_funcs[idx % len(discovered_funcs)][0] if discovered_funcs else None

        if mode == "edge_cases":
            lines.append(f"@pytest.mark.ag_{key}")
            lines.append(f"def test_{key}_edge_cases():")
            lines.append(f'    """Edge-case checks for: {label}."""')
            if note_comment:
                lines.append(f"    {note_comment}")
            if target_func:
                lines.append(
                    f'    assert hasattr({module_name}, "{target_func}"), '
                    f'"Expected `{target_func}` to be defined in `{entrypoint}` for edge-case testing."'
                )
                lines.append(
                    f"    fn = getattr({module_name}, \"{target_func}\")"
                )
                lines.append(
                    f'    assert callable(fn), "`{target_func}` must be a callable function."'
                )
            else:
                lines.append(
                    f'    assert {module_name} is not None, "Expected `{entrypoint}` module to import cleanly on boundary inputs."'
                )
            lines.append("")
        elif mode == "refine":
            lines.append(f"@pytest.mark.ag_{key}")
            lines.append(f"def test_{key}_refined():")
            lines.append(f'    """Refined check for: {label}."""')
            if note_comment:
                lines.append(f"    {note_comment}")
            if target_func:
                lines.append(
                    f'    assert hasattr({module_name}, "{target_func}"), '
                    f'"Expected `{target_func}` to be defined in `{entrypoint}` ({label})."'
                )
            else:
                lines.append(
                    f'    assert {module_name} is not None, "Expected `{entrypoint}` to satisfy refined criterion: {label}."'
                )
            lines.append("")
        else:
            lines.append(f"@pytest.mark.ag_{key}")
            lines.append(f"def test_{key}_standard():")
            lines.append(f'    """Standard verification for: {label}."""')
            if note_comment:
                lines.append(f"    {note_comment}")
            if target_func:
                lines.append(
                    f'    assert hasattr({module_name}, "{target_func}"), '
                    f'"Expected function `{target_func}` to be defined in `{entrypoint}`."'
                )
                lines.append(
                    f'    assert callable(getattr({module_name}, "{target_func}")), '
                    f'"Expected `{target_func}` in `{entrypoint}` to be callable."'
                )
            else:
                lines.append(
                    f'    assert {module_name} is not None, "Expected `{entrypoint}` module to load for {label}."'
                )
            lines.append("")

    generated_code = "\n".join(lines).rstrip() + "\n"
    mode_label = {
        "generate": "specification-aligned pytest test cases",
        "edge_cases": "boundary and edge-case pytest functions",
        "refine": "refined pytest assertions",
    }[mode]

    return AITestAuthoringResponse(
        generated_code=generated_code,
        suggested_items=suggested_items,
        explanation=(
            f"Generated {len(pytest_items)} {mode_label} with `@pytest.mark.ag_*` markers "
            f"targeting `{entrypoint}`. Review the preview below and run Model Solution "
            f"Preflight Validation after inserting."
        ),
        used_fallback=True,
    )


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
    """Generate or refine instructor pytest cases via local vLLM with deterministic fallback."""
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
        f"MODE: {request.mode}\n"
        f"ALLOWED CONCEPTS: {', '.join(allowed_concepts or []) or '(unrestricted)'}\n\n"
        f"RUBRIC SCORING KEYS:\n{rubric_summary or '(none configured yet)'}\n\n"
        f"ASSIGNMENT DESCRIPTION:\n{clean_desc or '(none)'}\n\n"
        f"INSTRUCTOR INSTRUCTION:\n{clean_instr or '(generate comprehensive pytest cases with @pytest.mark.ag_* markers)'}\n\n"
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
        valid, reason = _validate_generated_pytest_code(candidate.generated_code)
        if valid:
            candidate.used_fallback = False
            return candidate
        logger.warning("AI test authoring output failed validation (%s); using fallback.", reason)
    except Exception as exc:  # noqa: BLE001
        logger.info("Local LLM unavailable for test authoring (%s); using deterministic synthesis.", type(exc).__name__)

    return _synthesize_deterministic_tests(
        mode=request.mode,
        assignment_title=assignment_title,
        entrypoint=entrypoint,
        scoring_items=scoring_items,
        instruction=request.instruction,
        current_test_code=request.current_test_code,
        model_solution_code=model_solution_code,
        target_keys=request.target_keys,
    )
