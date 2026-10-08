"""Grading language execution strategies."""
from __future__ import annotations

from app.domains.grading.strategies.cpp import CppStrategy
from app.domains.grading.strategies.python import PythonPytestStrategy
from app.domains.grading.strategies.registry import (
    StrategyRegistry,
    get_strategy,
    register_strategy,
    registry,
)

# Register standard language strategies
python_strategy = PythonPytestStrategy()
cpp_strategy = CppStrategy()

registry.register("python", python_strategy)
registry.register("cpp", cpp_strategy)
registry.register("c", cpp_strategy)

__all__ = [
    "StrategyRegistry",
    "registry",
    "get_strategy",
    "register_strategy",
    "PythonPytestStrategy",
    "CppStrategy",
]
