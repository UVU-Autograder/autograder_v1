"""Assignment specification engine module encapsulating preflight checks, schema validation, and bundle packaging."""
from __future__ import annotations

import ast
import logging
from typing import Any

from sqlalchemy.orm import Session

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
        markers = set()
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

        if assignment.config is None or not assignment.config.config_json:
            errors.append("Assignment is missing configuration json.")
            return errors

        config_json = assignment.config.config_json

        try:
            config = AssignmentConfigV1.model_validate(config_json)
        except Exception as e:
            if hasattr(e, "errors"):
                for err in e.errors():
                    loc = " -> ".join(str(part) for part in err.get("loc", []))
                    errors.append(f"Schema validation error at '{loc}': {err.get('msg')}")
            else:
                errors.append(f"Invalid configuration format: {e}")
            return errors

        unsupported_deps = sorted(
            {
                dep
                for dep in config.dependencies
                if dep.lower() not in get_settings().preinstalled_dependency_names
            }
        )
        if unsupported_deps:
            errors.append(
                "Execution dependencies are not preinstalled in Judge0: "
                + ", ".join(unsupported_deps)
            )

        pytest_artifacts = [
            art for art in assignment.artifacts if art.artifact_type == "pytest_file"
        ]
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

        artifacts_by_key = {
            artifact.artifact_key: artifact for artifact in assignment.artifacts
        }
        for key in model_configs:
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

        pytest_markers = set()
        for artifact in pytest_artifacts:
            if not artifact.storage_ref:
                errors.append(
                    f"Pytest artifact '{artifact.artifact_key}' is missing physical file reference."
                )
                continue
            try:
                path = resolve_storage_ref(artifact.storage_ref)
                content = path.read_text(encoding="utf-8")
                pytest_markers.update(self.extract_ag_markers(content))
            except FileNotFoundError:
                errors.append(
                    f"Pytest artifact file not found for key '{artifact.artifact_key}'."
                )
            except Exception as e:
                errors.append(
                    f"Failed to read/parse pytest file '{artifact.artifact_key}': {e}"
                )

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

        config = AssignmentConfigV1.model_validate(assignment.config.config_json)
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

        zip_data = build_model_solution_zip(config.bundle.required_files, model_files)

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
