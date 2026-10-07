"""Versioned, transient official grading inputs. Digests detect corruption, not trust."""
from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator
from sqlalchemy.orm import Session

from app.core.settings import get_settings
from app.db.session import engine
from app.domains.assignments.engine import AssignmentSpecificationEngine
from app.domains.assignments.schemas import AssignmentConfigV1
from app.domains.assignments.service import effective_allowed_concepts, get_assignment_for_course
from app.domains.grading.runner_gen import generate_runner_script
from app.domains.grading.runtime import ExecutionParameters, PreloadedArtifacts, load_fallback_helper
from app.domains.runs.service import official_run_dir
from app.integrations.artifacts.resolver import resolve_storage_ref

SNAPSHOT_FILENAME = "grading_snapshot.json"


class PackageCaptureError(ValueError):
    """Safe staff-facing readiness error, without source bytes or storage paths."""


class GradingPackageError(ValueError):
    def __init__(self, category: Literal["grading_package_missing", "grading_package_invalid"]):
        super().__init__(category)
        self.category = category


def execution_filename(key: str, display_filename: str | None) -> str:
    # Preserve the grader's historical basename placement on both platforms.
    name = (display_filename or key).replace("\\", "/").rsplit("/", 1)[-1]
    if name in {"", ".", ".."} or name.casefold() == "runner.py" or ":" in name:
        raise ValueError("Invalid or reserved grading filename")
    return name


class PackageFile(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    content_base64: str
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @classmethod
    def from_bytes(cls, content: bytes) -> PackageFile:
        return cls(content_base64=base64.b64encode(content).decode("ascii"),
                   sha256=hashlib.sha256(content).hexdigest())

    def decode(self) -> bytes:
        content = base64.b64decode(self.content_base64, validate=True)
        if hashlib.sha256(content).hexdigest() != self.sha256:
            raise ValueError("Grading file digest mismatch")
        return content


def package_digest(payload: dict) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class OfficialGradingPackage(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    version: Literal[1]
    assignment_id: int = Field(ge=1)
    config_version: int = Field(ge=1)
    config: AssignmentConfigV1
    concepts: list[str]
    description: str | None
    files: dict[str, PackageFile]
    pytest_filenames: list[str] = Field(min_length=1)
    runner_source: str = Field(min_length=1)
    fallback_helper: PackageFile
    execution_parameters: ExecutionParameters
    digest: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_package(self) -> OfficialGradingPackage:
        expected_files: set[str] = set()
        expected_pytest: list[str] = []
        portable_names: set[str] = set()
        contents: dict[str, bytes] = {}
        for key, artifact in self.config.artifacts.items():
            if artifact.type == "model_solution":
                continue
            name = execution_filename(key, artifact.display_filename)
            if name.casefold() in portable_names:
                raise ValueError("Conflicting grading filenames")
            portable_names.add(name.casefold())
            expected_files.add(name)
            if name not in self.files:
                raise ValueError("Required grading file missing")
            contents[key] = self.files[name].decode()
            if artifact.type == "pytest_file":
                expected_pytest.append(name)
        if set(self.files) != expected_files or self.pytest_filenames != expected_pytest:
            raise ValueError("Grading file membership mismatch")
        self.fallback_helper.decode()
        # Model readiness was checked during capture; model bytes are never packaged.
        model_keys = {key for key, art in self.config.artifacts.items() if art.type == "model_solution"}
        errors = AssignmentSpecificationEngine().validate_captured_specification(
            self.config, contents, model_keys, set(self.execution_parameters.preinstalled_dependencies),
        )
        if errors:
            raise ValueError("Invalid captured grading specification")
        if self.digest != package_digest(self.model_dump(mode="json", exclude={"digest"})):
            raise ValueError("Grading package digest mismatch")
        return self

    def preloaded_artifacts(self) -> PreloadedArtifacts:
        return PreloadedArtifacts(files={name: file.decode() for name, file in self.files.items()},
                                  pytest_filenames=list(self.pytest_filenames))


def capture_package(course_code: str, assignment_slug: str) -> OfficialGradingPackage:
    """Own one consistent metadata read transaction; perform no scheduling or network I/O.

    Uploaded files use unique paths and their stored digest. Seed/runtime deployment
    must drain official work first; this package does not pin the running image.
    """
    settings = get_settings()
    bind = engine.execution_options(isolation_level="REPEATABLE READ") if engine.dialect.name == "postgresql" else engine
    with Session(bind=bind) as db:
        # sqlite3's legacy transaction mode does not start a transaction for SELECT.
        # Explicit BEGIN is needed to keep selectin/lazy relationship reads coherent.
        if engine.dialect.name == "sqlite":
            db.connection().exec_driver_sql("BEGIN")
        try:
            assignment = get_assignment_for_course(db, course_code, assignment_slug)
            if assignment is None or assignment.config is None:
                raise PackageCaptureError("Assignment configuration is unavailable.")
            config = AssignmentConfigV1.model_validate(assignment.config.config)
            records = {record.artifact_key: record for record in assignment.artifacts}
            contents: dict[str, bytes] = {}
            available_models: set[str] = set()
            files: dict[str, PackageFile] = {}
            names: set[str] = set()
            pytest_filenames: list[str] = []
            for key, artifact in config.artifacts.items():
                record = records.get(key)
                if not record or not record.storage_ref or record.artifact_type != artifact.type:
                    raise PackageCaptureError(f"Required artifact '{key}' is unavailable or has the wrong type.")
                try:
                    path = resolve_storage_ref(record.storage_ref)
                    if artifact.type == "model_solution":
                        if path.is_file():
                            available_models.add(key)
                        continue
                    content = path.read_bytes()
                except (OSError, ValueError):
                    raise PackageCaptureError(f"Required artifact '{key}' could not be captured. Retry after checking assignment assets.") from None
                if record.sha256 and hashlib.sha256(content).hexdigest() != record.sha256:
                    raise PackageCaptureError(f"Required artifact '{key}' failed its integrity check.")
                name = execution_filename(key, artifact.display_filename)
                if name.casefold() in names:
                    raise PackageCaptureError("Grading artifacts have conflicting execution filenames.")
                names.add(name.casefold())
                contents[key] = content
                files[name] = PackageFile.from_bytes(content)
                if artifact.type == "pytest_file":
                    pytest_filenames.append(name)
            parameters = ExecutionParameters(
                language_id=settings.judge0_language_id,
                cpu_time_limit=float(settings.test_execution_timeout_seconds),
                preinstalled_dependencies=sorted(settings.preinstalled_dependency_names),
            )
            errors = AssignmentSpecificationEngine().validate_captured_specification(
                config, contents, available_models, set(parameters.preinstalled_dependencies),
            )
            if errors:
                raise PackageCaptureError("; ".join(errors))
            test_cases = {item.key: {"inputs": item.inputs, "outputs": item.outputs}
                          for item in config.scoring_items
                          if item.inputs is not None and item.outputs is not None}
            runner = generate_runner_script(pytest_filenames, test_cases,
                                           Path(config.bundle.entrypoint).stem, config.dependencies)
            payload = {
                "version": 1, "assignment_id": assignment.id,
                "config_version": assignment.config.version, "config": config.model_dump(mode="json"),
                "concepts": effective_allowed_concepts(assignment), "description": assignment.description,
                "files": {name: file.model_dump() for name, file in files.items()},
                "pytest_filenames": pytest_filenames, "runner_source": runner,
                "fallback_helper": PackageFile.from_bytes(load_fallback_helper()).model_dump(),
                "execution_parameters": parameters.model_dump(),
            }
            return OfficialGradingPackage.model_validate({**payload, "digest": package_digest(payload)})
        except PackageCaptureError:
            raise
        except (OSError, ValueError):
            raise PackageCaptureError("Assignment grading inputs could not be captured. Check configuration and assets.") from None


def atomic_write(path: Path, content: bytes, *, temporary_directory: Path | None = None) -> None:
    """Caller holds the run guard. Temporary files remain in governed storage."""
    temporary = (temporary_directory or path.parent) / (path.name + ".tmp")
    with temporary.open("wb") as stream:
        stream.write(content)
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


def write_package(run_id: int, package: OfficialGradingPackage) -> None:
    directory = official_run_dir(run_id)
    directory.mkdir(parents=True, exist_ok=True)
    atomic_write(directory / SNAPSHOT_FILENAME, package.model_dump_json().encode("utf-8"))


def load_package(run_id: int, *, assignment_id: int) -> OfficialGradingPackage:
    try:
        package = OfficialGradingPackage.model_validate_json(
            (official_run_dir(run_id) / SNAPSHOT_FILENAME).read_bytes(),
        )
        if package.assignment_id != assignment_id:
            raise ValueError("Grading package belongs to another assignment")
        return package
    except FileNotFoundError:
        raise GradingPackageError("grading_package_missing") from None
    except (OSError, ValueError, ValidationError):
        raise GradingPackageError("grading_package_invalid") from None
