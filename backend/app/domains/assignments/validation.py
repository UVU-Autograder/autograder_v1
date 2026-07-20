import ast
from sqlalchemy.orm import Session

from app.core.settings import get_settings
from app.domains.assignments.schemas import AssignmentConfigV1
from app.domains.assignments.service import get_assignment_for_course
from app.domains.assignments.io_parser import extract_expected_io
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
            val = func_node.value
            # Case 1: @pytest.mark.ag_xxx
            if isinstance(val, ast.Attribute) and val.attr == "mark":
                val_val = val.value
                if isinstance(val_val, ast.Name) and val_val.id == "pytest":
                    if func_node.attr.startswith("ag_"):
                        markers.add(func_node.attr)
            # Case 2: @mark.ag_xxx
            elif isinstance(val, ast.Name) and val.id == "mark":
                if func_node.attr.startswith("ag_"):
                    markers.add(func_node.attr)
        # Case 3: @ag_xxx
        elif isinstance(func_node, ast.Name):
            if func_node.id.startswith("ag_"):
                markers.add(func_node.id)

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

    unsupported_dependencies = sorted(
        {
            dependency
            for dependency in config.execution.dependencies
            if dependency.lower()
            not in get_settings().preinstalled_dependency_names
        }
    )
    if unsupported_dependencies:
        errors.append(
            "Execution dependencies are not preinstalled in Judge0: "
            + ", ".join(unsupported_dependencies)
        )

    # 2. Check for missing assignment pytest artifacts
    pytest_artifacts = [
        art for art in assignment.artifacts if art.artifact_type == "pytest_file"
    ]
    if not pytest_artifacts:
        errors.append("At least one 'pytest_file' artifact is required.")
        return errors

    # 3. Every required student-bundle path needs a real instructor model file.
    model_configs = {
        key: artifact
        for key, artifact in config.artifacts.items()
        if artifact.type == "model_solution" and artifact.display_filename
    }
    model_filenames = {
        artifact.display_filename for artifact in model_configs.values()
    }
    missing_model_files = [
        path for path in config.bundle.required_files if path not in model_filenames
    ]
    if missing_model_files:
        errors.append(
            "Missing model solution artifacts for required files: "
            + ", ".join(sorted(missing_model_files))
        )

    artifacts_by_key = {
        artifact.artifact_key: artifact for artifact in assignment.artifacts
    }
    for key, model_config in model_configs.items():
        stored = artifacts_by_key.get(key)
        if stored is None or not stored.storage_ref:
            errors.append(
                f"Model solution artifact '{key}' is missing physical file reference."
            )
            continue
        try:
            resolve_storage_ref(stored.storage_ref)
        except FileNotFoundError:
            errors.append(
                f"Model solution artifact file not found for key '{key}'."
            )

    # 4. Read pytest files and extract all ag_<key> markers using AST
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

    # 5. Require each test key to match a pytest marker named ag_<key>.
    for test in config.tests:
        expected_marker = f"ag_{test.key}"
        if expected_marker not in pytest_markers:
            errors.append(
                f"Scoring item key '{test.key}' has no matching '{expected_marker}' marker in pytest files."
            )

    return errors
