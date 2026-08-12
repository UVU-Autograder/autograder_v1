import fnmatch
import re
from typing import Literal

from pydantic import BaseModel, Field, model_validator

TEST_KEY_RE = re.compile(r"^[a-z][a-z0-9_]*$")
DEPENDENCY_RE = re.compile(r"^[A-Za-z0-9_.-]+$")
ARTIFACT_TYPES = {"pytest_file", "model_solution", "support_file"}


def pytest_marker_for_key(key: str) -> str:
    return f"ag_{key}"


class FileRequirementConfig(BaseModel):
    label: str = Field(min_length=1)
    paths: list[str] | None = Field(default=None)
    pattern: str | None = Field(default=None)

    @model_validator(mode="after")
    def validate_mode(self) -> "FileRequirementConfig":
        if (self.paths is None) == (self.pattern is None):
            raise ValueError("file_requirements entry must specify exactly one of 'paths' or 'pattern'")
        if self.paths is not None:
            if len(self.paths) < 1:
                raise ValueError("file_requirements 'paths' must contain at least one path")
            if any(not p.strip() for p in self.paths):
                raise ValueError("file_requirements 'paths' entries cannot be blank")
        if self.pattern is not None and not self.pattern.strip():
            raise ValueError("file_requirements 'pattern' cannot be blank")
        return self


class BundleConfig(BaseModel):
    entrypoint: str = Field(min_length=1)
    file_requirements: list[FileRequirementConfig] = Field(default_factory=list)

    def derived_required_files(self) -> list[str]:
        paths: list[str] = []
        for req in self.file_requirements:
            if req.paths:
                paths.extend(req.paths)
            elif req.pattern:
                paths.append(req.pattern)
        paths.append(self.entrypoint)
        return list(dict.fromkeys(paths))

    @model_validator(mode="after")
    def entrypoint_must_be_covered(self) -> "BundleConfig":
        if not self.file_requirements:
            return self

        covered = False
        for requirement in self.file_requirements:
            if requirement.paths and self.entrypoint in requirement.paths:
                covered = True
                break
            if requirement.pattern and fnmatch.fnmatch(self.entrypoint, requirement.pattern):
                covered = True
                break

        if not covered:
            raise ValueError(
                f"bundle.entrypoint ('{self.entrypoint}') must be covered by at least one file_requirements entry"
            )
        return self






class ArtifactConfig(BaseModel):
    type: Literal["pytest_file", "model_solution", "support_file"]
    display_filename: str | None = None


class ScoringItemConfig(BaseModel):
    key: str = Field(pattern=TEST_KEY_RE.pattern)
    label: str = Field(min_length=1)
    points: int = Field(ge=0)
    extra_credit: bool
    item_type: Literal["pytest", "manual"] = "pytest"
    rubric_group_key: str | None = Field(default=None, pattern=TEST_KEY_RE.pattern)
    inputs: list[str] | None = Field(default=None)
    outputs: list[str] | None = Field(default=None)

    @model_validator(mode="after")
    def validate_inputs_outputs(self) -> "ScoringItemConfig":
        if self.item_type == "manual":
            if self.inputs is not None or self.outputs is not None:
                raise ValueError("Manual rubric items cannot have inputs or outputs.")
        else:
            if (self.inputs is None) != (self.outputs is None):
                raise ValueError("Both inputs and outputs must be specified, or both omitted.")
            if self.inputs is not None and self.outputs is not None:
                if len(self.inputs) != len(self.outputs):
                    raise ValueError("The number of inputs and outputs must match.")
        return self


class RubricGroupConfig(BaseModel):
    key: str = Field(pattern=TEST_KEY_RE.pattern)
    label: str = Field(min_length=1)


class CompletionRequirementConfig(BaseModel):
    key: str = Field(pattern=TEST_KEY_RE.pattern)
    label: str = Field(min_length=1)
    test_keys: list[str] = Field(min_length=1)
    minimum_passed: int = Field(ge=1)


class ConceptsConfig(BaseModel):
    allowlist: list[str] = Field(default_factory=list)
    denylist: list[str] = Field(default_factory=list)


class AssignmentConfigV1(BaseModel):
    bundle: BundleConfig
    artifacts: dict[str, ArtifactConfig] = Field(min_length=1)
    scoring_items: list[ScoringItemConfig] = Field(min_length=1)
    concepts: ConceptsConfig = Field(default_factory=ConceptsConfig)
    completion_requirements: list[CompletionRequirementConfig] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    rubric_groups: list[RubricGroupConfig] = Field(default_factory=list)


    @model_validator(mode="after")
    def validate_dependencies(self) -> "AssignmentConfigV1":
        invalid = sorted({d for d in self.dependencies if not DEPENDENCY_RE.match(d)})
        if invalid:
            raise ValueError(f"invalid execution dependencies: {', '.join(invalid)}")
        if len(self.dependencies) != len(set(self.dependencies)):
            raise ValueError("duplicate execution dependencies are not allowed")
        return self

    @model_validator(mode="after")
    def validate_references(self) -> "AssignmentConfigV1":
        item_keys = [item.key for item in self.scoring_items]
        duplicate_keys = sorted({key for key in item_keys if item_keys.count(key) > 1})
        if duplicate_keys:
            raise ValueError(f"duplicate scoring item keys: {', '.join(duplicate_keys)}")

        artifact_types = [artifact.type for artifact in self.artifacts.values()]
        if artifact_types.count("pytest_file") < 1:
            raise ValueError("at least one pytest_file artifact is required")

        artifact_keys = list(self.artifacts)
        duplicate_artifacts = sorted({key for key in artifact_keys if artifact_keys.count(key) > 1})
        if duplicate_artifacts:
            raise ValueError(f"duplicate artifact keys: {', '.join(duplicate_artifacts)}")

        group_keys = [group.key for group in self.rubric_groups]
        duplicate_group_keys = sorted({key for key in group_keys if group_keys.count(key) > 1})
        if duplicate_group_keys:
            raise ValueError(f"duplicate rubric group keys: {', '.join(duplicate_group_keys)}")
        known_groups = set(group_keys)

        for item in self.scoring_items:
            if item.rubric_group_key is not None and item.rubric_group_key not in known_groups:
                raise ValueError(
                    f"scoring item {item.key} references unknown rubric group: {item.rubric_group_key}"
                )

        requirement_keys = [req.key for req in self.completion_requirements]
        duplicate_requirements = sorted({key for key in requirement_keys if requirement_keys.count(key) > 1})
        if duplicate_requirements:
            raise ValueError(f"duplicate completion requirement keys: {', '.join(duplicate_requirements)}")

        known_pytest_tests = {item.key for item in self.scoring_items if item.item_type == "pytest"}
        for req in self.completion_requirements:
            unknown = sorted(set(req.test_keys) - known_pytest_tests)
            if unknown:
                raise ValueError(
                    f"completion requirement {req.key} references unknown tests: {', '.join(unknown)}"
                )
            if req.minimum_passed > len(set(req.test_keys)):
                raise ValueError(
                    f"completion requirement {req.key} minimum_passed exceeds referenced tests"
                )

        return self

    @property
    def base_points(self) -> int:
        return sum(item.points for item in self.scoring_items if not item.extra_credit)

    @property
    def extra_credit_points(self) -> int:
        return sum(item.points for item in self.scoring_items if item.extra_credit)


class ScoringItem(BaseModel):
    key: str
    label: str
    points: int
    extra_credit: bool
    item_type: Literal["pytest", "manual"] = "pytest"
    pytest_marker: str | None = None
    rubric_group_key: str | None = None


class RubricGroup(BaseModel):
    key: str
    label: str
    item_keys: list[str]


class CompletionRequirement(BaseModel):
    key: str
    label: str
    test_keys: list[str]
    minimum_passed: int


class ArtifactMetadata(BaseModel):
    artifact_key: str
    artifact_type: str
    display_filename: str | None
    size_bytes: int | None = None
    sha256: str | None = None


class StaffAssignmentSetup(BaseModel):
    course_id: str
    assignment_id: str
    title: str
    language: str
    sandbox_enabled: bool
    base_points: int
    extra_credit_points: int
    entrypoint_path: str
    scoring_items: list[ScoringItem]
    rubric_groups: list[RubricGroup]
    completion_requirements: list[CompletionRequirement]
    canvas_ref: str | None = None
    artifacts: list[ArtifactMetadata]
    config_json: AssignmentConfigV1
    module_id: int | None = None
    effective_allowed_concepts: list[str] = Field(default_factory=list)






class StaffAssignmentSetupUpdate(BaseModel):
    title: str | None = None
    sandbox_enabled: bool | None = None
    canvas_ref: str | None = None
    language: str | None = None
    config_json: AssignmentConfigV1
    module_id: int | None = None


class AssignmentCreate(BaseModel):
    slug: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]*$")
    title: str = Field(min_length=1)
    language: str = Field(default="python")
    canvas_ref: str | None = Field(default=None)
    sandbox_enabled: bool = Field(default=True)
    module_id: int | None = Field(default=None)


class ArtifactListResponse(BaseModel):
    course_id: str
    assignment_id: str
    artifacts: list[ArtifactMetadata]


