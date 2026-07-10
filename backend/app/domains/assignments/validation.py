import ast
from sqlalchemy.orm import Session

from app.domains.assignments.schemas import AssignmentConfigV1
from app.domains.assignments.service import get_assignment_for_course
from app.integrations.artifacts.resolver import resolve_storage_ref


def extract_ag_markers(source_code: str) -> set[str]:
    """Parse python source code to find all pytest decorators starting with 'ag_'."""
    markers = set()
    try:
        tree = ast.parse(source_code)
    except SyntaxError:
        return markers

    def check_decorator(node):
        func_node = node
        if isinstance(node, ast.Call):
            func_node = node.func

        if isinstance(func_node, ast.Attribute):
            # Resolve attribute path. For `@pytest.mark.ag_xxx`, we check
            # if func_node.attr is our ag_ marker and the parent path resolves
            # to pytest.mark
            val = func_node.value
            if isinstance(val, ast.Attribute) and val.attr == "mark":
                val_val = val.value
                if isinstance(val_val, ast.Name) and val_val.id == "pytest":
                    if func_node.attr.startswith("ag_"):
                        markers.add(func_node.attr)

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for decorator in node.decorator_list:
                check_decorator(decorator)

    return markers


def run_preflight_validation(db: Session, course_code: str, assignment_slug: str) -> list[str]:
    """Execute preflight checks on config_json and uploaded artifacts.

    Returns a list of validation error strings. If empty, validation passed.
    """
    errors = []

    assignment = get_assignment_for_course(db, course_code, assignment_slug)
    if assignment is None:
        errors.append(f"Assignment '{assignment_slug}' not found.")
        return errors

    if assignment.config is None or not assignment.config.config_json:
        errors.append("Assignment is missing configuration json.")
        return errors

    config_json = assignment.config.config_json

    # 1. Validate structure/schema and Pydantic constraints
    # (duplicate test keys, duplicate manual items, minimum_passed ge 1 etc.)
    try:
        config = AssignmentConfigV1.model_validate(config_json)
    except Exception as e:
        # Extract detailed validation messages if possible
        if hasattr(e, "errors"):
            for err in e.errors():
                loc = " -> ".join(str(l) for l in err.get("loc", []))
                errors.append(f"Schema validation error at '{loc}': {err.get('msg')}")
        else:
            errors.append(f"Invalid configuration format: {e}")
        return errors

    # 2. Check for missing assignment pytest artifacts
    pytest_artifacts = [
        art for art in assignment.artifacts if art.artifact_type == "pytest_file"
    ]
    if not pytest_artifacts:
        errors.append("At least one 'pytest_file' artifact is required.")
        return errors

    # 3. Read pytest files and extract all ag_<key> markers using AST
    pytest_markers = set()
    for artifact in pytest_artifacts:
        if not artifact.storage_ref:
            errors.append(f"Pytest artifact '{artifact.artifact_key}' is missing physical file reference.")
            continue
        try:
            path = resolve_storage_ref(artifact.storage_ref)
            content = path.read_text(encoding="utf-8")
            pytest_markers.update(extract_ag_markers(content))
        except FileNotFoundError:
            errors.append(f"Pytest artifact file not found for key '{artifact.artifact_key}'.")
        except Exception as e:
            errors.append(f"Failed to read/parse pytest file '{artifact.artifact_key}': {e}")

    if errors:
        return errors

    # 4. Require each test key in config to match a pytest marker named ag_<key> in the pytest files
    for test in config.tests:
        expected_marker = f"ag_{test.key}"
        if expected_marker not in pytest_markers:
            errors.append(
                f"Scoring item key '{test.key}' has no matching '{expected_marker}' marker in pytest files."
            )

    return errors
