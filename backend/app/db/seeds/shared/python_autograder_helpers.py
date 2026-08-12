import builtins
import importlib
import os
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

_MISSING_MODULE = object()


def import_student_modules(*module_names: str):
    """Import local student modules while temporarily shadowing name collisions."""
    saved_modules = {
        name: sys.modules.get(name, _MISSING_MODULE) for name in module_names
    }
    original_path = list(sys.path)
    try:
        target_dir = os.getenv("STUDENT_SUBMISSION_DIR") or str(Path.cwd())
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
            if name == "packaging" and "packaging" in sys.modules and hasattr(sys.modules["packaging"], "Packaging"):
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
