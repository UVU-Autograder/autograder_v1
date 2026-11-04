"""Platform-injected Python test helpers exposed to instructors and AI authoring."""

from __future__ import annotations

from functools import lru_cache

from pydantic import BaseModel, Field

from app.domains.grading.runtime import load_fallback_helper

PYTHON_HELPERS_FILENAME = "python_autograder_helpers.py"

PYTHON_HELPERS_USAGE_NOTES = """\
Prefer ordinary pytest in tests.py:
- `import student_module` for student files with normal names
- `capsys` or the `bounded_output` fixture for stdout/stderr (do not import BoundedOutput from autograder_capture)
- `monkeypatch.setattr("builtins.input", ...)` for simple CLI prompts

Import symbols from this file only when required:
- `import_student_modules` when a student filename collides with stdlib/pip (e.g. packaging.py)
- `with_input_blocked` when student code calls input() during import
- `sequential_input_mock` for long multi-prompt CLI sequences

Canvas filename suffixes are normalized at official intake; do not import helpers only for Canvas renames.
"""


class PythonHelpersPayload(BaseModel):
    """Read-only view of the helper module injected into the grading sandbox."""

    filename: str = Field(description="Sandbox filename for the injected helper module")
    source: str = Field(description="Exact helper source copied into the execution directory")
    usage_notes: str = Field(description="When to prefer standard pytest vs these helpers")


@lru_cache(maxsize=1)
def load_python_helpers_payload() -> PythonHelpersPayload:
    """Return the same helper bytes the grading pipeline injects into the sandbox."""
    source = load_fallback_helper().decode("utf-8")
    return PythonHelpersPayload(
        filename=PYTHON_HELPERS_FILENAME,
        source=source,
        usage_notes=PYTHON_HELPERS_USAGE_NOTES.strip(),
    )
