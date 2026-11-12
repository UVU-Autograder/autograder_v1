import ast
from collections.abc import Generator
from typing import TypedDict


class ExpectedIO(TypedDict):
    expected_input: str | None
    expected_output: str | None
    comparison_mode: str | None
    tolerance: float | None


def _get_string_constant(node: ast.AST | None) -> str | None:
    """Helper to extract a string literal constant from an AST node."""
    if node is not None and isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _get_numeric_constant(node: ast.AST | None) -> float | None:
    """Helper to extract a numeric literal constant from an AST node."""
    if node is not None and isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        val = _get_numeric_constant(node.operand)
        return -val if val is not None else None
    return None


def _get_assignment_targets_and_node(stmt: ast.AST) -> Generator[tuple[str, ast.AST | None], None, None]:
    """Yields (target_var_name, value_node) pairs for Assign and AnnAssign nodes."""
    if isinstance(stmt, ast.Assign):
        for target in stmt.targets:
            if isinstance(target, ast.Name):
                yield target.id, stmt.value
    elif isinstance(stmt, ast.AnnAssign):
        if isinstance(stmt.target, ast.Name):
            yield stmt.target.id, stmt.value


def _process_assignment(
    var_name: str,
    val_node: ast.AST | None,
) -> tuple[str | None, str | None, str | None, float | None]:
    """Returns (input_val, output_val, comparison_mode, tolerance)."""
    input_val = None
    output_val = None
    comparison_mode = None
    tolerance = None

    str_val = _get_string_constant(val_node)
    num_val = _get_numeric_constant(val_node)

    if str_val is not None:
        if var_name in ("EXPECTED_INPUT", "EXPECTED_INPUTS", "INPUT", "INPUTS"):
            input_val = str_val
        elif var_name in ("EXPECTED_OUTPUT", "EXPECTED_OUTPUTS", "EXPECTED", "OUTPUT", "OUTPUTS"):
            output_val = str_val
        elif var_name in ("COMPARISON_MODE", "COMPARE_MODE", "MODE"):
            norm_mode = str_val.lower().strip()
            if norm_mode in ("normalized", "exact", "numeric_tolerance", "regex"):
                comparison_mode = norm_mode

    if num_val is not None:
        if var_name in ("TOLERANCE", "TOL", "EPSILON", "ATOL", "RTOL"):
            tolerance = num_val

    return input_val, output_val, comparison_mode, tolerance


def extract_expected_io(source_code: str) -> dict[str, ExpectedIO]:
    """Parse python pytest source code to extract EXPECTED_INPUT, EXPECTED_OUTPUT,

    COMPARISON_MODE, and TOLERANCE constants associated with @pytest.mark.ag_<key> decorated functions.

    Returns a dict mapping ag_marker name -> {"expected_input": ..., "expected_output": ..., "comparison_mode": ..., "tolerance": ...}
    """
    results: dict[str, ExpectedIO] = {}
    try:
        tree = ast.parse(source_code)
    except SyntaxError:
        return results

    # Track module-level assignments as fallbacks
    module_input: str | None = None
    module_output: str | None = None
    module_mode: str | None = None
    module_tolerance: float | None = None

    for stmt in tree.body:
        for var_name, val_node in _get_assignment_targets_and_node(stmt):
            inp, out, mode, tol = _process_assignment(var_name, val_node)
            if inp is not None:
                module_input = inp
            if out is not None:
                module_output = out
            if mode is not None:
                module_mode = mode
            if tol is not None:
                module_tolerance = tol

    def get_ag_markers(func_node: ast.AST) -> list[str]:
        markers = []
        for decorator in getattr(func_node, "decorator_list", []):
            d_node = decorator
            if isinstance(decorator, ast.Call):
                d_node = decorator.func

            if isinstance(d_node, ast.Attribute):
                val = d_node.value
                # @pytest.mark.ag_xxx
                if isinstance(val, ast.Attribute) and val.attr == "mark":
                    val_val = val.value
                    if isinstance(val_val, ast.Name) and val_val.id == "pytest":
                        if d_node.attr.startswith("ag_"):
                            markers.append(d_node.attr)
                # @mark.ag_xxx
                elif isinstance(val, ast.Name) and val.id == "mark":
                    if d_node.attr.startswith("ag_"):
                        markers.append(d_node.attr)
            elif isinstance(d_node, ast.Name):
                if d_node.id.startswith("ag_"):
                    markers.append(d_node.id)
        return markers

    # Iterate over top-level and nested statements in lexical order
    for stmt in tree.body:
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
            markers = get_ag_markers(stmt)
            if not markers:
                continue

            func_input: str | None = None
            func_output: str | None = None
            func_mode: str | None = None
            func_tolerance: float | None = None

            for body_stmt in stmt.body:
                for var_name, val_node in _get_assignment_targets_and_node(body_stmt):
                    inp, out, mode, tol = _process_assignment(var_name, val_node)
                    if inp is not None:
                        func_input = inp
                    if out is not None:
                        func_output = out
                    if mode is not None:
                        func_mode = mode
                    if tol is not None:
                        func_tolerance = tol

            effective_input = func_input if func_input is not None else module_input
            effective_output = func_output if func_output is not None else module_output
            effective_mode = func_mode if func_mode is not None else module_mode
            effective_tolerance = func_tolerance if func_tolerance is not None else module_tolerance

            for marker in markers:
                if marker not in results:
                    results[marker] = {
                        "expected_input": effective_input,
                        "expected_output": effective_output,
                        "comparison_mode": effective_mode,
                        "tolerance": effective_tolerance,
                    }
                else:
                    if results[marker]["expected_input"] is None and effective_input is not None:
                        results[marker]["expected_input"] = effective_input
                    if results[marker]["expected_output"] is None and effective_output is not None:
                        results[marker]["expected_output"] = effective_output
                    if results[marker]["comparison_mode"] is None and effective_mode is not None:
                        results[marker]["comparison_mode"] = effective_mode
                    if results[marker]["tolerance"] is None and effective_tolerance is not None:
                        results[marker]["tolerance"] = effective_tolerance

    return results
