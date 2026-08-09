import ast
from collections.abc import Generator
from typing import TypedDict


class ExpectedIO(TypedDict):
    expected_input: str | None
    expected_output: str | None


def _get_string_constant(node: ast.AST | None) -> str | None:
    """Helper to extract a string literal constant from an AST node."""
    if node is not None and isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _get_assignment_targets_and_value(stmt: ast.AST) -> Generator[tuple[str, str | None], None, None]:
    """Yields (target_var_name, string_value) pairs for Assign and AnnAssign nodes."""
    if isinstance(stmt, ast.Assign):
        val = _get_string_constant(stmt.value)
        for target in stmt.targets:
            if isinstance(target, ast.Name):
                yield target.id, val
    elif isinstance(stmt, ast.AnnAssign):
        if isinstance(stmt.target, ast.Name) and stmt.value is not None:
            val = _get_string_constant(stmt.value)
            yield stmt.target.id, val


def extract_expected_io(source_code: str) -> dict[str, ExpectedIO]:
    """Parse python pytest source code to extract EXPECTED_INPUT and EXPECTED_OUTPUT

    constants associated with @pytest.mark.ag_<key> decorated functions.

    Returns a dict mapping ag_marker name -> {"expected_input": ..., "expected_output": ...}
    """
    results: dict[str, ExpectedIO] = {}
    try:
        tree = ast.parse(source_code)
    except SyntaxError:
        return results

    # Track module-level assignments as fallbacks
    module_input: str | None = None
    module_output: str | None = None

    for stmt in tree.body:
        for var_name, val in _get_assignment_targets_and_value(stmt):
            if val is not None:
                if var_name in ("EXPECTED_INPUT", "EXPECTED_INPUTS", "INPUT", "INPUTS"):
                    module_input = val
                elif var_name in ("EXPECTED_OUTPUT", "EXPECTED_OUTPUTS", "EXPECTED", "OUTPUT", "OUTPUTS"):
                    module_output = val

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

            for body_stmt in stmt.body:
                for var_name, val in _get_assignment_targets_and_value(body_stmt):
                    if val is not None:
                        if var_name in ("EXPECTED_INPUT", "EXPECTED_INPUTS", "INPUT", "INPUTS"):
                            func_input = val
                        elif var_name in ("EXPECTED_OUTPUT", "EXPECTED_OUTPUTS", "EXPECTED", "OUTPUT", "OUTPUTS"):
                            func_output = val

            effective_input = func_input if func_input is not None else module_input
            effective_output = func_output if func_output is not None else module_output

            for marker in markers:
                if marker not in results:
                    results[marker] = {
                        "expected_input": effective_input,
                        "expected_output": effective_output,
                    }
                else:
                    if results[marker]["expected_input"] is None and effective_input is not None:
                        results[marker]["expected_input"] = effective_input
                    if results[marker]["expected_output"] is None and effective_output is not None:
                        results[marker]["expected_output"] = effective_output

    return results
