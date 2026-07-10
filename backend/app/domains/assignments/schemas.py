import re
from typing import Literal

from pydantic import BaseModel, Field, model_validator

TEST_KEY_RE = re.compile(r"^[a-z][a-z0-9_]*$")
DEPENDENCY_RE = re.compile(r"^[A-Za-z0-9_.-]+$")
ARTIFACT_TYPES = {"pytest_file", "model_solution", "support_file"}


def pytest_marker_for_key(key: str) -> str:
    return f"ag_{key}"


class FileRequirementConfig(BaseModel):
    key: str = Field(pattern=TEST_KEY_RE.pattern)
    label: str | None = None
    requirement_type: Literal["exact", "one_of", "optional", "pattern"] = "exact"
    paths: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_paths(self) -> "FileRequirementConfig":
        if self.requirement_type in {"exact", "optional", "pattern"} and len(self.paths) != 1:
            raise ValueError(f"{self.requirement_type} file requirements must have exactly one path")
        if self.requirement_type == "one_of" and len(set(self.paths)) < 2:
            raise ValueError("one_of file requirements must have at least two distinct paths")
        return self


class BundleConfig(BaseModel):
    required_files: list[str] = Field(min_length=1)
    entrypoint: str = Field(min_length=1)
    file_requirements: list[FileRequirementConfig] = Field(default_factory=list)

    @model_validator(mode="after")
    def entrypoint_must_be_required_file(self) -> "BundleConfig":
        known_paths = set(self.required_files)
        for requirement in self.file_requirements:
            if requirement.requirement_type in {"exact", "optional", "one_of"}:
                known_paths.update(requirement.paths)
        if self.entrypoint not in known_paths:
            raise ValueError("bundle.entrypoint must appear in bundle.required_files")
        requirement_keys = [requirement.key for requirement in self.file_requirements]
        duplicate_keys = sorted({key for key in requirement_keys if requirement_keys.count(key) > 1})
        if duplicate_keys:
            raise ValueError(f"duplicate file requirement keys: {', '.join(duplicate_keys)}")
        return self


class ConceptsConfig(BaseModel):
    additions: list[str] = Field(default_factory=list)


class ArtifactConfig(BaseModel):
    type: Literal["pytest_file", "model_solution", "support_file"]
    display_filename: str | None = None


class TestItemConfig(BaseModel):
    key: str = Field(pattern=TEST_KEY_RE.pattern)
    label: str = Field(min_length=1)
    points: int = Field(ge=0)
    extra_credit: bool
    rubric_group_key: str | None = Field(default=None, pattern=TEST_KEY_RE.pattern)
    inputs: list[str] | None = Field(default=None)
    outputs: list[str] | None = Field(default=None)

    @model_validator(mode="after")
    def validate_inputs_outputs(self) -> "TestItemConfig":
        if (self.inputs is None) != (self.outputs is None):
            raise ValueError("Both inputs and outputs must be specified, or both omitted.")
        if self.inputs is not None and self.outputs is not None:
            if len(self.inputs) != len(self.outputs):
                raise ValueError("The number of inputs and outputs must match.")
        return self



class ManualRubricItemConfig(BaseModel):
    key: str = Field(pattern=TEST_KEY_RE.pattern)
    label: str = Field(min_length=1)
    points: int = Field(ge=0)
    extra_credit: bool
    rubric_group_key: str | None = Field(default=None, pattern=TEST_KEY_RE.pattern)


class RubricGroupConfig(BaseModel):
    key: str = Field(pattern=TEST_KEY_RE.pattern)
    label: str = Field(min_length=1)
    item_keys: list[str] = Field(min_length=1)


class ExecutionConfig(BaseModel):
    dependencies: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_dependencies(self) -> "ExecutionConfig":
        invalid = sorted({dependency for dependency in self.dependencies if not DEPENDENCY_RE.match(dependency)})
        if invalid:
            raise ValueError(f"invalid execution dependencies: {', '.join(invalid)}")
        if len(self.dependencies) != len(set(self.dependencies)):
            raise ValueError("duplicate execution dependencies are not allowed")
        return self


class SupportArtifactRefConfig(BaseModel):
    artifact_key: str = Field(pattern=TEST_KEY_RE.pattern)
    workspace_path: str = Field(min_length=1)


class OutputArtifactConfig(BaseModel):
    key: str = Field(pattern=TEST_KEY_RE.pattern)
    path: str = Field(min_length=1)
    required: bool = True
    artifact_type: Literal["generated_file"] = "generated_file"


class StdinScenarioConfig(BaseModel):
    key: str = Field(pattern=TEST_KEY_RE.pattern)
    label: str = Field(min_length=1)
    stdin: list[str] = Field(default_factory=list)


class CompletionRequirementConfig(BaseModel):
    key: str = Field(pattern=TEST_KEY_RE.pattern)
    label: str = Field(min_length=1)
    test_keys: list[str] = Field(min_length=1)
    minimum_passed: int = Field(ge=1)


class AssignmentConfigV1(BaseModel):
    schema_version: Literal[1]
    bundle: BundleConfig
    concepts: ConceptsConfig = Field(default_factory=ConceptsConfig)
    artifacts: dict[str, ArtifactConfig] = Field(min_length=1)
    tests: list[TestItemConfig] = Field(min_length=1)
    completion_requirements: list[CompletionRequirementConfig] = Field(default_factory=list)
    execution: ExecutionConfig = Field(default_factory=ExecutionConfig)
    support_artifacts: list[SupportArtifactRefConfig] = Field(default_factory=list)
    output_artifacts: list[OutputArtifactConfig] = Field(default_factory=list)
    rubric_groups: list[RubricGroupConfig] = Field(default_factory=list)
    manual_rubric_items: list[ManualRubricItemConfig] = Field(default_factory=list)
    stdin_scenarios: list[StdinScenarioConfig] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_references(self) -> "AssignmentConfigV1":
        test_keys = [item.key for item in self.tests]
        duplicate_keys = sorted({key for key in test_keys if test_keys.count(key) > 1})
        if duplicate_keys:
            raise ValueError(f"duplicate test keys: {', '.join(duplicate_keys)}")

        artifact_types = [artifact.type for artifact in self.artifacts.values()]
        if artifact_types.count("pytest_file") < 1:
            raise ValueError("at least one pytest_file artifact is required")

        artifact_keys = list(self.artifacts)
        duplicate_artifacts = sorted({key for key in artifact_keys if artifact_keys.count(key) > 1})
        if duplicate_artifacts:
            raise ValueError(f"duplicate artifact keys: {', '.join(duplicate_artifacts)}")

        known_tests = set(test_keys)
        manual_keys = [item.key for item in self.manual_rubric_items]
        duplicate_manual_keys = sorted({key for key in manual_keys if manual_keys.count(key) > 1})
        if duplicate_manual_keys:
            raise ValueError(f"duplicate manual rubric item keys: {', '.join(duplicate_manual_keys)}")
        overlapping_item_keys = sorted(set(test_keys) & set(manual_keys))
        if overlapping_item_keys:
            raise ValueError(f"duplicate scoring item keys: {', '.join(overlapping_item_keys)}")
        known_scoring_items = set(test_keys) | set(manual_keys)

        group_keys = [group.key for group in self.rubric_groups]
        duplicate_group_keys = sorted({key for key in group_keys if group_keys.count(key) > 1})
        if duplicate_group_keys:
            raise ValueError(f"duplicate rubric group keys: {', '.join(duplicate_group_keys)}")
        known_groups = set(group_keys)
        for group in self.rubric_groups:
            unknown_items = sorted(set(group.item_keys) - known_scoring_items)
            if unknown_items:
                raise ValueError(
                    f"rubric group {group.key} references unknown scoring items: {', '.join(unknown_items)}"
                )
        for item in [*self.tests, *self.manual_rubric_items]:
            if item.rubric_group_key is not None and item.rubric_group_key not in known_groups:
                raise ValueError(
                    f"scoring item {item.key} references unknown rubric group: {item.rubric_group_key}"
                )

        requirement_keys = [requirement.key for requirement in self.completion_requirements]
        duplicate_requirements = sorted(
            {key for key in requirement_keys if requirement_keys.count(key) > 1}
        )
        if duplicate_requirements:
            raise ValueError(f"duplicate completion requirement keys: {', '.join(duplicate_requirements)}")

        for requirement in self.completion_requirements:
            unknown = sorted(set(requirement.test_keys) - known_tests)
            if unknown:
                raise ValueError(
                    f"completion requirement {requirement.key} references unknown tests: {', '.join(unknown)}"
                )
            if requirement.minimum_passed > len(set(requirement.test_keys)):
                raise ValueError(
                    f"completion requirement {requirement.key} minimum_passed exceeds referenced tests"
                )

        support_keys = [support.artifact_key for support in self.support_artifacts]
        duplicate_support_keys = sorted({key for key in support_keys if support_keys.count(key) > 1})
        if duplicate_support_keys:
            raise ValueError(f"duplicate support artifact references: {', '.join(duplicate_support_keys)}")
        for support in self.support_artifacts:
            artifact = self.artifacts.get(support.artifact_key)
            if artifact is None:
                raise ValueError(f"support artifact references unknown artifact: {support.artifact_key}")
            if artifact.type != "support_file":
                raise ValueError(f"support artifact {support.artifact_key} must reference a support_file artifact")

        file_requirement_paths = set(self.bundle.required_files)
        for requirement in self.bundle.file_requirements:
            if requirement.requirement_type in {"exact", "optional", "one_of"}:
                file_requirement_paths.update(requirement.paths)
        output_keys = [artifact.key for artifact in self.output_artifacts]
        duplicate_output_keys = sorted({key for key in output_keys if output_keys.count(key) > 1})
        if duplicate_output_keys:
            raise ValueError(f"duplicate output artifact keys: {', '.join(duplicate_output_keys)}")
        for output_artifact in self.output_artifacts:
            if output_artifact.path not in file_requirement_paths:
                raise ValueError(
                    f"output artifact {output_artifact.key} references a path not present in submitted/generated files"
                )

        scenario_keys = [scenario.key for scenario in self.stdin_scenarios]
        duplicate_scenario_keys = sorted({key for key in scenario_keys if scenario_keys.count(key) > 1})
        if duplicate_scenario_keys:
            raise ValueError(f"duplicate stdin scenario keys: {', '.join(duplicate_scenario_keys)}")
        return self

    @property
    def base_points(self) -> int:
        items = [*self.tests, *self.manual_rubric_items]
        return sum(item.points for item in items if not item.extra_credit)

    @property
    def extra_credit_points(self) -> int:
        items = [*self.tests, *self.manual_rubric_items]
        return sum(item.points for item in items if item.extra_credit)


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
    required_files: list[str]
    entrypoint_path: str
    concept_additions: list[str]
    scoring_items: list[ScoringItem]
    rubric_groups: list[RubricGroup]
    completion_requirements: list[CompletionRequirement]
    canvas_ref: str | None = None
    artifacts: list[ArtifactMetadata]
    config_json: AssignmentConfigV1
    module_id: int | None = None


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

