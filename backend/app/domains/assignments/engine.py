"""Assignment specification engine module encapsulating preflight checks, schema validation, and bundle packaging."""
from __future__ import annotations

import ast
import logging
from typing import Any

from sqlalchemy.orm import Session
from pydantic import ValidationError

from app.core.settings import get_settings
from app.domains.assignments.schemas import AssignmentConfigV1
from app.domains.assignments.service import (
    effective_allowed_concepts,
    get_artifact_content,
    get_assignment_for_course,
)
from app.integrations.artifacts.resolver import resolve_storage_ref

logger = logging.getLogger(__name__)


class AssignmentSpecificationEngine:
    """Deep domain module managing assignment specification validation, marker verification, and bundle packaging."""

    @staticmethod
    def extract_ag_markers(source_code: str) -> set[str]:
        """Parse Python source code using AST to find all pytest markers starting with 'ag_'."""
        markers: set[str] = set()
        try:
            tree = ast.parse(source_code)
        except SyntaxError:
            return markers

        def check_decorator(node: ast.AST) -> None:
            func_node = node
            if isinstance(node, ast.Call):
                func_node = node.func

            if isinstance(func_node, ast.Attribute):
                val = func_node.value
                if isinstance(val, ast.Attribute) and val.attr == "mark":
                    val_val = val.value
                    if isinstance(val_val, ast.Name) and val_val.id == "pytest":
                        if func_node.attr.startswith("ag_"):
                            markers.add(func_node.attr)
                elif isinstance(val, ast.Name) and val.id == "mark":
                    if func_node.attr.startswith("ag_"):
                        markers.add(func_node.attr)
            elif isinstance(func_node, ast.Name):
                if func_node.id.startswith("ag_"):
                    markers.add(func_node.id)

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for decorator in node.decorator_list:
                    check_decorator(decorator)

        return markers

    def validate_specification(
        self, db: Session, course_code: str, assignment_slug: str
    ) -> list[str]:
        """Run complete preflight validation on an assignment configuration and its artifacts."""
        errors: list[str] = []

        assignment = get_assignment_for_course(db, course_code, assignment_slug)
        if assignment is None:
            errors.append(f"Assignment '{assignment_slug}' not found.")
            return errors

        if assignment.config is None or not assignment.config.config:
            errors.append("Assignment is missing configuration.")
            return errors

        config_raw = assignment.config.config

        try:
            config = AssignmentConfigV1.model_validate(config_raw)
        except ValidationError as e:
            for err in e.errors():
                loc = " -> ".join(str(part) for part in err.get("loc", ()))
                errors.append(f"Schema validation error at '{loc}': {err.get('msg')}")
            return errors
        except Exception as e:
            errors.append(f"Invalid configuration format: {e}")
            return errors

        contents: dict[str, bytes] = {}
        available_models: set[str] = set()
        stored = {artifact.artifact_key: artifact for artifact in assignment.artifacts}
        for key, artifact in config.artifacts.items():
            record = stored.get(key)
            if not record or not record.storage_ref:
                continue
            try:
                path = resolve_storage_ref(record.storage_ref)
                if artifact.type == "model_solution":
                    if path.is_file():
                        available_models.add(key)
                else:
                    contents[key] = path.read_bytes()
            except (OSError, ValueError):
                errors.append(f"Artifact '{key}' is unavailable.")
        return errors + self.validate_captured_specification(
            config, contents, available_models, get_settings().preinstalled_dependency_names,
        )

    def validate_captured_specification(
        self,
        config: AssignmentConfigV1,
        contents: dict[str, bytes],
        available_models: set[str],
        preinstalled_dependencies: set[str],
    ) -> list[str]:
        """Validate the exact captured inputs without resolving live storage again."""
        errors: list[str] = []
        unsupported_deps = sorted(
            {
                dep
                for dep in config.dependencies
                if dep.lower() not in preinstalled_dependencies
            }
        )
        if unsupported_deps:
            errors.append(
                "Execution dependencies are not preinstalled in Judge0: "
                + ", ".join(unsupported_deps)
            )

        pytest_artifacts = [key for key, art in config.artifacts.items()
                            if art.type == "pytest_file" and key in contents]
        if not pytest_artifacts:
            errors.append("At least one 'pytest_file' artifact is required.")
            return errors

        model_configs = {
            key: artifact
            for key, artifact in config.artifacts.items()
            if artifact.type == "model_solution" and artifact.display_filename
        }
        model_filenames = {
            artifact.display_filename for artifact in model_configs.values()
        }

        if config.bundle.entrypoint not in model_filenames:
            errors.append(
                f"Missing model solution artifact for entrypoint '{config.bundle.entrypoint}'."
            )

        for req in config.bundle.file_requirements:
            if req.paths:
                if not any(p in model_filenames for p in req.paths):
                    errors.append(
                        f"Missing model solution artifact for file requirement '{req.label}' (none of {req.paths} found)."
                    )

        for key in model_configs:
            if key not in available_models:
                errors.append(
                    f"Model solution artifact '{key}' is missing physical file reference."
                )

        for key, artifact in config.artifacts.items():
            if artifact.type != "model_solution" and key not in contents:
                errors.append(f"Required grading artifact '{key}' is unavailable.")

        pytest_markers = set()
        for key in pytest_artifacts:
            try:
                content = contents[key].decode("utf-8")
                pytest_markers.update(self.extract_ag_markers(content))
            except UnicodeDecodeError:
                errors.append(f"Pytest artifact '{key}' is not UTF-8 text.")

        if errors:
            return errors

        for item in config.scoring_items:
            if item.item_type != "pytest":
                continue
            expected_marker = f"ag_{item.key}"
            if expected_marker not in pytest_markers:
                errors.append(
                    f"Scoring item key '{item.key}' has no matching '{expected_marker}' marker in pytest files."
                )

        return errors

    def prepare_model_solution_bundle(
        self, db: Session, course_code: str, assignment_slug: str
    ) -> dict[str, Any]:
        """Retrieve model solution files and package them into an execution payload."""
        assignment = get_assignment_for_course(db, course_code, assignment_slug)
        if assignment is None or not assignment.config:
            raise ValueError(f"Assignment '{assignment_slug}' configuration not found.")

        config = AssignmentConfigV1.model_validate(assignment.config.config)
        max_score = sum(item.points for item in config.scoring_items if item.item_type == "pytest" and not item.extra_credit)

        model_artifacts = {
            key: artifact
            for key, artifact in config.artifacts.items()
            if artifact.type == "model_solution"
        }
        if not model_artifacts:
            raise ValueError("No 'model_solution' artifacts defined in configuration.")

        model_files: dict[str, bytes] = {}
        model_keys: set[str] = set()
        for key, artifact in model_artifacts.items():
            if not artifact.display_filename:
                raise ValueError(f"Model solution artifact '{key}' is missing display_filename.")
            if artifact.display_filename in model_files:
                raise ValueError(f"Duplicate model solution filename: {artifact.display_filename}")
            content = get_artifact_content(db, course_code, assignment_slug, key)
            if not content:
                raise ValueError(f"Model solution file content missing for key '{key}'.")
            model_files[artifact.display_filename] = content[0]
            model_keys.add(key)

        from app.domains.runs.orchestrator import build_model_solution_zip

        zip_data = build_model_solution_zip(
            config.bundle.derived_required_files(), model_files
        )

        artifact_refs = {}
        for art in assignment.artifacts:
            if art.artifact_key not in model_keys and art.storage_ref:
                artifact_refs[art.artifact_key] = art.storage_ref

        allowed_concepts = effective_allowed_concepts(assignment)

        return {
            "config": config,
            "max_score": max_score,
            "zip_data": zip_data,
            "artifact_refs": artifact_refs,
            "allowed_concepts": allowed_concepts,
        }
