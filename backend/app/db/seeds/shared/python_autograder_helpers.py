import builtins
import importlib
import math
import os
import re
import shutil
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

_MISSING_MODULE = object()
CANVAS_FILE_SUFFIX_RE = re.compile(
    r"-(?:([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})|([0-9]+))$"
)


def _resolve_canvas_module(target_path: Path, module_name: str) -> None:
    """If target_path lacks module_name.py but has a Canvas-renamed copy (e.g. module_name-1.py), alias it."""
    expected_file = target_path / f"{module_name}.py"
    if expected_file.is_file():
        return
    for p in target_path.glob("*.py"):
        clean_stem = CANVAS_FILE_SUFFIX_RE.sub("", p.stem)
        if clean_stem == module_name:
            try:
                shutil.copy2(p, expected_file)
            except OSError:
                pass
            return


def import_student_modules(*module_names: str):
    """Import local student modules while temporarily shadowing name collisions."""
    saved_modules = {name: sys.modules.get(name, _MISSING_MODULE) for name in module_names}
    original_path = list(sys.path)
    try:
        target_dir = os.getenv("STUDENT_SUBMISSION_DIR") or str(Path.cwd())
        target_path = Path(target_dir).resolve()
        for name in module_names:
            _resolve_canvas_module(target_path, name)
        sys.path.insert(0, target_dir)
        importlib.invalidate_caches()
        for name in module_names:
            sys.modules.pop(name, None)
        imported = []
        for name in module_names:
            try:
                mod = importlib.import_module(name)
                imported.append(mod)
            except ModuleNotFoundError:
                imported.append(None)
        return tuple(imported)
    finally:
        sys.path[:] = original_path
        for name, module in saved_modules.items():
            if (
                name == "packaging"
                and "packaging" in sys.modules
                and hasattr(sys.modules["packaging"], "Packaging")
            ):
                continue
            if module is _MISSING_MODULE:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module


class ImportTimeExit(BaseException):
    """Abort student module import when code calls input() at import time."""


def with_input_blocked(import_fn: Callable[[], Any]) -> Any:
    """Run import_fn with builtins.input raising ImportTimeExit; restore afterward."""
    orig_input = builtins.input

    def mock_input(*args: Any, **kwargs: Any) -> None:
        raise ImportTimeExit()

    builtins.input = mock_input
    try:
        return import_fn()
    finally:
        builtins.input = orig_input


def sequential_input_mock(responses: list[str]):
    it = iter(responses)

    def _mock(prompt: str = "") -> str:
        try:
            return next(it)
        except StopIteration:
            pytest.fail(
                f"Student prompt method called input() more times than expected. "
                f"Responses defined: {responses}"
            )

    return _mock


NUMBER_PATTERN = re.compile(r"[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?")
DEFAULT_NUMERIC_TOLERANCE = 1e-4


def normalize_output(text: str) -> str:
    """Normalize program output for comparison."""
    if not text:
        return ""
    lines = [stripped for line in text.splitlines() if (stripped := line.rstrip())]
    return "\n".join(lines).strip()


def compare_exact(actual: str, expected: str) -> bool:
    """Compare exact strings, normalizing CRLF to LF."""
    return (actual or "").replace("\r\n", "\n") == (expected or "").replace("\r\n", "\n")


def compare_regex(actual: str, pattern: str) -> bool:
    """Match output against configured regular expression with MULTILINE flag."""
    norm_actual = (actual or "").replace("\r\n", "\n")
    norm_pattern = (pattern or "").replace("\r\n", "\n")
    if not norm_pattern:
        return norm_actual == ""
    try:
        compiled = re.compile(norm_pattern, re.MULTILINE)
        return compiled.search(norm_actual) is not None
    except re.error:
        return False


def compare_numeric_tolerance(
    actual: str,
    expected: str,
    tolerance: float | None = None,
) -> bool:
    """Compare numeric outputs within tolerance."""
    if tolerance is None:
        tol = DEFAULT_NUMERIC_TOLERANCE
    else:
        try:
            tol_f = float(tolerance)
            tol = DEFAULT_NUMERIC_TOLERANCE if tol_f < 0 else tol_f
        except (ValueError, TypeError):
            tol = DEFAULT_NUMERIC_TOLERANCE
    act_str = actual or ""
    exp_str = expected or ""
    if act_str.replace("\r\n", "\n") == exp_str.replace("\r\n", "\n"):
        return True
    try:
        act_val = float(act_str.strip())
        exp_val = float(exp_str.strip())
        if math.isnan(act_val) and math.isnan(exp_val):
            return True
        return math.isclose(act_val, exp_val, rel_tol=tol, abs_tol=tol)
    except (ValueError, TypeError):
        pass
    norm_act = normalize_output(act_str)
    norm_exp = normalize_output(exp_str)
    if norm_act == norm_exp:
        return True
    act_nums = NUMBER_PATTERN.findall(norm_act)
    exp_nums = NUMBER_PATTERN.findall(norm_exp)
    if len(act_nums) != len(exp_nums):
        return False
    act_parts = NUMBER_PATTERN.split(norm_act)
    exp_parts = NUMBER_PATTERN.split(norm_exp)
    if len(act_parts) != len(exp_parts):
        return False
    for a_part, e_part in zip(act_parts, exp_parts):
        if re.sub(r"[ \t]+", " ", a_part) != re.sub(r"[ \t]+", " ", e_part):
            return False
    for a_num, e_num in zip(act_nums, exp_nums):
        try:
            a_f = float(a_num)
            e_f = float(e_num)
        except (ValueError, TypeError):
            return False
        if math.isnan(a_f) and math.isnan(e_f):
            continue
        if not math.isclose(a_f, e_f, rel_tol=tol, abs_tol=tol):
            return False
    return True


def compare_outputs(
    actual: str,
    expected: str,
    mode: str = "normalized",
    tolerance: float | None = None,
) -> bool:
    """Compare outputs according to configured mode."""
    if mode == "exact":
        return compare_exact(actual, expected)
    elif mode == "numeric_tolerance":
        return compare_numeric_tolerance(actual, expected, tolerance=tolerance)
    elif mode == "regex":
        return compare_regex(actual, expected)
    else:
        return normalize_output(actual or "") == normalize_output(expected or "")


def assert_output_matches(
    actual: str,
    expected: str,
    mode: str = "normalized",
    tolerance: float | None = None,
) -> None:
    """Assert actual output matches expected according to comparison mode."""
    matched = compare_outputs(actual, expected, mode=mode, tolerance=tolerance)
    if not matched:
        if mode == "exact":
            assert (actual or "").replace("\r\n", "\n") == (expected or "").replace("\r\n", "\n")
        elif mode == "numeric_tolerance":
            tol_val = DEFAULT_NUMERIC_TOLERANCE if (tolerance is None or tolerance < 0) else tolerance
            pytest.fail(f"Output did not match expected within tolerance {tol_val}.\nExpected: {expected!r}\nActual: {actual!r}")
        elif mode == "regex":
            pytest.fail(f"Output did not match regex pattern.\nPattern: {expected!r}\nActual: {actual!r}")
        else:
            assert normalize_output(actual or "") == normalize_output(expected or "")

