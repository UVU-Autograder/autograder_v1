"""Lossless, non-executing extraction of rubric metadata from an unsaved Python suite."""
import ast
import math
from typing import Any

from pydantic import BaseModel, Field


class TestSuiteSyncRequest(BaseModel):
    source: str = Field(max_length=262144)


class SyncedScoringItem(BaseModel):
    key: str
    inputs: list[str] | None = None
    outputs: list[str] | None = None
    comparison_mode: str | None = None
    tolerance: float | None = None


class TestSuiteSyncResponse(BaseModel):
    items: list[SyncedScoringItem]


ALIASES = {**{name: "inputs" for name in ("EXPECTED_INPUT", "EXPECTED_INPUTS", "INPUT", "INPUTS")},
           **{name: "outputs" for name in ("EXPECTED_OUTPUT", "EXPECTED_OUTPUTS", "EXPECTED", "OUTPUT", "OUTPUTS")},
           **{name: "comparison_mode" for name in ("COMPARISON_MODE", "COMPARE_MODE", "MODE")},
           **{name: "tolerance" for name in ("TOLERANCE", "TOL", "EPSILON", "ATOL", "RTOL")}}


def _constants(statements: list[ast.stmt]) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for statement in statements:
        targets: list[ast.expr] = []
        node: ast.expr | None = None
        if isinstance(statement, ast.Assign):
            targets, node = statement.targets, statement.value
        elif isinstance(statement, ast.AnnAssign):
            targets, node = [statement.target], statement.value
        if node is None:
            continue
        for target in targets:
            if not isinstance(target, ast.Name) or target.id not in ALIASES:
                continue
            try:
                literal = ast.literal_eval(node)
            except (ValueError, TypeError, SyntaxError):
                continue  # An expression is not guessed or executed; retain the configured value.
            key = ALIASES[target.id]
            if key in {"inputs", "outputs"}:
                literal = [literal] if isinstance(literal, str) else literal
                if not isinstance(literal, (list, tuple)) or not all(isinstance(x, str) for x in literal):
                    raise ValueError(f"{target.id} must contain strings")
                values[key] = list(literal)
            elif key == "comparison_mode":
                if literal not in {"normalized", "exact", "numeric_tolerance", "regex"}:
                    raise ValueError("Unsupported comparison mode")
                values[key] = literal
            else:
                if isinstance(literal, bool) or not isinstance(literal, (int, float)) or not math.isfinite(literal) or literal < 0:
                    raise ValueError("Tolerance must be a finite nonnegative number")
                values[key] = float(literal)
    return values


def synchronize_python_suite(source: str) -> TestSuiteSyncResponse:
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        raise ValueError(f"Invalid Python syntax on line {exc.lineno}") from None
    defaults = _constants(tree.body)
    items: dict[str, dict[str, Any]] = {}

    def visit(statements: list[ast.stmt], scope: dict[str, Any]) -> None:
        for node in statements:
            if isinstance(node, ast.ClassDef):
                visit(node.body, {**scope, **_constants(node.body)})
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for decorator in node.decorator_list:
                target = decorator.func if isinstance(decorator, ast.Call) else decorator
                name = target.attr if isinstance(target, ast.Attribute) else target.id if isinstance(target, ast.Name) else ""
                if not name.startswith("ag_"):
                    continue
                key = name.removeprefix("ag_")
                if not key or not key[0].islower() or any(c not in "abcdefghijklmnopqrstuvwxyz0123456789_" for c in key):
                    raise ValueError("Rubric markers require lowercase keys")
                values = {**scope, **_constants(node.body)}
                if ("inputs" in values) != ("outputs" in values):
                    raise ValueError(f"Marker {name} requires both expected input and output")
                if "inputs" in values and len(values["inputs"]) != len(values["outputs"]):
                    raise ValueError(f"Marker {name} has unequal input/output counts")
                previous = items.setdefault(key, {"key": key})
                for field, value in values.items():
                    if field in previous and previous[field] != value:
                        raise ValueError(f"Marker {name} has conflicting {field} declarations")
                    previous[field] = value
    visit(tree.body, defaults)
    return TestSuiteSyncResponse(items=[SyncedScoringItem.model_validate(item) for item in items.values()])
