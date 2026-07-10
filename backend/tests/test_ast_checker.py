"""Comprehensive tests for the AST concept whitelist validator."""

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

import pytest

from app.integrations.ast_checker.validator import (
    ASTCheckResult,
    ASTFinding,
    check_student_code,
)


# ---------------------------------------------------------------------------
# 1. Valid code with only allowed concepts → no warnings or blocks
# ---------------------------------------------------------------------------


class TestAllowedConceptsProduceCleanResult:
    """When code only uses concepts on the whitelist the result should be
    completely clean – no warnings, no blocks."""

    def test_variables_only(self):
        code = "x = 10\ny = x + 5\n"
        result = check_student_code(code, ["variables"])

        assert "variables" in result.detected_concepts
        assert result.warnings == []
        assert result.blocked == []
        assert result.is_blocked is False

    def test_variables_and_loops(self):
        code = "total = 0\nfor i in range(10):\n    total += i\n"
        result = check_student_code(code, ["variables", "loops"])

        assert result.warnings == []
        assert result.blocked == []
        assert result.is_blocked is False

    def test_empty_source(self):
        result = check_student_code("", ["variables"])
        assert result.detected_concepts == set()
        assert result.warnings == []
        assert result.blocked == []


# ---------------------------------------------------------------------------
# 2. Using ``for`` loop when only ``variables`` is allowed → concept_warning
# ---------------------------------------------------------------------------


class TestForLoopWarning:
    def test_for_loop_not_allowed(self):
        code = "for i in range(5):\n    x = i\n"
        result = check_student_code(code, ["variables"])

        assert "loops" in result.detected_concepts
        warning_codes = [w.code for w in result.warnings]
        assert "concept_warning" in warning_codes
        assert any("loops" in w.message for w in result.warnings)
        assert result.is_blocked is False


# ---------------------------------------------------------------------------
# 3. ``while`` loop counts as ``loops``
# ---------------------------------------------------------------------------


class TestWhileLoopDetection:
    def test_while_loop_detected_as_loops(self):
        code = "i = 0\nwhile i < 10:\n    i += 1\n"
        result = check_student_code(code, ["variables", "loops", "conditionals"])

        assert "loops" in result.detected_concepts
        assert result.warnings == []
        assert result.blocked == []


# ---------------------------------------------------------------------------
# 4. ``import subprocess`` → concept_blocked
# ---------------------------------------------------------------------------


class TestBlockedImports:
    def test_import_subprocess(self):
        code = "import subprocess\n"
        result = check_student_code(code, ["variables"])

        assert result.is_blocked is True
        assert any(f.code == "concept_blocked" for f in result.blocked)
        assert any("subprocess" in f.message for f in result.blocked)

    def test_import_os(self):
        code = "import os\n"
        result = check_student_code(code, [])

        assert result.is_blocked is True
        assert any("os" in f.message for f in result.blocked)

    def test_from_import_blocked(self):
        code = "from shutil import copy\n"
        result = check_student_code(code, [])

        assert result.is_blocked is True
        assert any("shutil" in f.message for f in result.blocked)


# ---------------------------------------------------------------------------
# 5. ``eval(...)`` → concept_blocked
# ---------------------------------------------------------------------------


class TestBlockedEval:
    def test_eval_call(self):
        code = "x = eval('1 + 2')\n"
        result = check_student_code(code, ["variables"])

        assert result.is_blocked is True
        blocked_messages = [f.message for f in result.blocked]
        assert any("eval" in m for m in blocked_messages)

    def test_eval_has_line_number(self):
        code = "a = 1\nx = eval('a')\n"
        result = check_student_code(code, ["variables"])

        eval_finding = [f for f in result.blocked if "eval" in f.message][0]
        assert eval_finding.line == 2


# ---------------------------------------------------------------------------
# 6. ``exec(...)`` → concept_blocked
# ---------------------------------------------------------------------------


class TestBlockedExec:
    def test_exec_call(self):
        code = "exec('x = 1')\n"
        result = check_student_code(code, [])

        assert result.is_blocked is True
        assert any("exec" in f.message for f in result.blocked)


# ---------------------------------------------------------------------------
# 7. ``from PIL import Image`` → image-processing
# ---------------------------------------------------------------------------


class TestImageProcessingDetection:
    def test_pil_import_detected(self):
        code = "from PIL import Image\n"
        result = check_student_code(code, ["image-processing"])

        assert "image-processing" in result.detected_concepts
        assert result.warnings == []
        assert result.is_blocked is False

    def test_pil_import_not_allowed(self):
        code = "from PIL import Image\n"
        result = check_student_code(code, ["variables"])

        assert "image-processing" in result.detected_concepts
        assert any("image-processing" in w.message for w in result.warnings)

    def test_pil_method_call_detected(self):
        code = "from PIL import Image\nimg = Image.open('photo.png')\n"
        result = check_student_code(code, ["image-processing", "variables"])

        assert "image-processing" in result.detected_concepts
        assert result.warnings == []


# ---------------------------------------------------------------------------
# 8. ``open('file.txt')`` → file-io
# ---------------------------------------------------------------------------


class TestFileIODetection:
    def test_open_call_detected(self):
        code = "f = open('file.txt')\n"
        result = check_student_code(code, ["file-io", "variables"])

        assert "file-io" in result.detected_concepts
        assert result.warnings == []

    def test_open_in_with_statement(self):
        code = "with open('data.csv') as f:\n    data = f.read()\n"
        result = check_student_code(code, ["file-io", "variables"])

        assert "file-io" in result.detected_concepts
        assert result.warnings == []

    def test_read_method_detected(self):
        code = "f.read()\n"
        result = check_student_code(code, ["file-io"])

        assert "file-io" in result.detected_concepts

    def test_write_method_detected(self):
        code = "f.write('hello')\n"
        result = check_student_code(code, ["file-io"])

        assert "file-io" in result.detected_concepts

    def test_file_io_not_allowed(self):
        code = "f = open('file.txt')\n"
        result = check_student_code(code, ["variables"])

        assert "file-io" in result.detected_concepts
        assert any("file-io" in w.message for w in result.warnings)


# ---------------------------------------------------------------------------
# 9. Syntax errors → graceful handling with syntax_error blocked finding
# ---------------------------------------------------------------------------


class TestSyntaxErrorHandling:
    def test_syntax_error_produces_blocked(self):
        code = "def broken(\n"
        result = check_student_code(code, ["functions"])

        assert result.is_blocked is True
        assert len(result.blocked) == 1
        assert result.blocked[0].code == "syntax_error"
        assert result.detected_concepts == set()

    def test_syntax_error_has_message(self):
        code = "x = = 1\n"
        result = check_student_code(code, [])

        assert result.is_blocked is True
        assert result.blocked[0].code == "syntax_error"
        assert result.blocked[0].message  # non-empty


# ---------------------------------------------------------------------------
# 10. Multiple concepts detected simultaneously
# ---------------------------------------------------------------------------


class TestMultipleConceptDetection:
    def test_loops_and_conditionals_and_variables(self):
        code = (
            "total = 0\n"
            "for i in range(10):\n"
            "    if i % 2 == 0:\n"
            "        total += i\n"
        )
        result = check_student_code(code, ["variables", "loops", "conditionals"])

        assert "variables" in result.detected_concepts
        assert "loops" in result.detected_concepts
        assert "conditionals" in result.detected_concepts
        assert result.warnings == []
        assert result.blocked == []

    def test_functions_and_variables(self):
        code = "def greet(name):\n    message = f'Hello, {name}'\n    return message\n"
        result = check_student_code(code, ["functions", "variables"])

        assert "functions" in result.detected_concepts
        assert "variables" in result.detected_concepts
        assert result.warnings == []

    def test_partial_whitelist_produces_warnings(self):
        code = (
            "total = 0\n"
            "for i in range(10):\n"
            "    if i > 5:\n"
            "        total += i\n"
        )
        # Only allow variables – loops and conditionals should warn
        result = check_student_code(code, ["variables"])

        assert "loops" in result.detected_concepts
        assert "conditionals" in result.detected_concepts
        warning_concepts = {w.message for w in result.warnings}
        assert any("loops" in m for m in warning_concepts)
        assert any("conditionals" in m for m in warning_concepts)

    def test_blocked_and_warnings_coexist(self):
        code = (
            "import subprocess\n"
            "for i in range(5):\n"
            "    x = i\n"
        )
        result = check_student_code(code, ["variables"])

        assert result.is_blocked is True
        assert any(f.code == "concept_blocked" for f in result.blocked)
        assert any(w.code == "concept_warning" for w in result.warnings)

    def test_all_concepts_in_one_file(self):
        code = (
            "from PIL import Image\n"
            "x = 10\n"
            "for i in range(x):\n"
            "    if i > 5:\n"
            "        pass\n"
            "def process():\n"
            "    with open('data.txt') as f:\n"
            "        data = f.read()\n"
            "    img = Image.open('pic.png')\n"
        )
        allowed = [
            "variables",
            "loops",
            "conditionals",
            "functions",
            "file-io",
            "image-processing",
        ]
        result = check_student_code(code, allowed)

        assert "variables" in result.detected_concepts
        assert "loops" in result.detected_concepts
        assert "conditionals" in result.detected_concepts
        assert "functions" in result.detected_concepts
        assert "file-io" in result.detected_concepts
        assert "image-processing" in result.detected_concepts
        assert result.warnings == []
        assert result.blocked == []


def test_concepts_metadata():
    from app.integrations.ast_checker.validator import get_concepts_metadata, CONCEPT_NODE_MAP
    import ast

    meta = get_concepts_metadata()
    assert "loops" in meta
    assert meta["loops"]["title"] == "Loops"
    assert "For" in meta["loops"]["nodes"]
    assert "While" in meta["loops"]["nodes"]
    assert "AsyncFor" in meta["loops"]["nodes"]

    assert "conditionals" in meta
    assert meta["conditionals"]["title"] == "Conditionals"
    
    assert "file-io" in meta
    assert len(meta["file-io"]["nodes"]) == 0
    assert len(meta["file-io"]["syntax_patterns"]) > 0

    # Ensure CONCEPT_NODE_MAP has the right keys/values
    assert set(CONCEPT_NODE_MAP.keys()) == {"loops", "conditionals", "functions", "variables"}
    assert CONCEPT_NODE_MAP["loops"] == (ast.For, ast.While, ast.AsyncFor)

