"""Language execution and outcome parsing protocols for modular autograding.

Defines the Strategy and Protocol abstractions for decoupling the grading pipeline
from Python-specific packaging, AST parsing, and Pytest runners. Enables modular
support for C, C++, and Web Development coursework.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from app.domains.assignments.schemas import AssignmentConfigV1


@dataclass
class ExecutionCommand:
    """Command specification for compilation or test execution."""

    command: str
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    timeout_seconds: float = 30.0


@dataclass
class ExecutionPayload:
    """Prepared payload ready for sandbox execution in Judge0 or container."""

    source_code: str
    language_id: int
    additional_files_b64: str
    compile_cmd: ExecutionCommand | None = None
    test_cmd: ExecutionCommand | None = None
    cpu_time_limit: float = 30.0
    wall_time_limit: float = 60.0
    memory_limit: int = 512000
    stdin: str | None = None


@dataclass
class ExecutionRawResult:
    """Raw result returned by the sandbox execution engine."""

    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    status_id: int = 3  # 3 = Accepted in Judge0
    wall_time: float | None = None
    memory_kb: int | None = None
    compile_output: str | None = None


@dataclass
class StaticAnalysisOutcome:
    """Result of static analysis and validation prior to sandbox execution."""

    passed: bool = True
    warnings: list[dict[str, Any]] = field(default_factory=list)
    failure_category: str | None = None
    failure_message: str | None = None
    ast_result: Any | None = None
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class ParsedOutcome:
    """Standardized grading outcome produced by an OutcomeParser."""

    success: bool = False
    score: int = 0
    max_score: int = 0
    test_results: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[dict[str, Any]] = field(default_factory=list)
    failure_category: str | None = None
    failure_message: str | None = None
    compiler_errors: list[str] = field(default_factory=list)
    raw_data: Any | None = None


@runtime_checkable
class LanguageRunner(Protocol):
    """Protocol for language-specific packaging, static analysis, and command generation."""

    @property
    def language_name(self) -> str:
        """Normalized language identifier (e.g. 'python', 'cpp', 'c', 'web')."""
        ...

    def static_analysis(
        self,
        exec_dir: Path,
        config: AssignmentConfigV1,
        allowed_concepts: list[str],
    ) -> StaticAnalysisOutcome:
        """Perform static analysis, syntax verification, and concept constraints."""
        ...

    def prepare_bundle(
        self,
        exec_dir: Path,
        config: AssignmentConfigV1,
        support_artifacts: dict[str, bytes],
        stdin: str | None = None,
        *,
        language_id: int | None = None,
        cpu_time_limit: float | None = None,
        memory_limit: int | None = None,
        wall_time_limit: float | None = None,
        runner_source: str | None = None,
    ) -> ExecutionPayload:
        """Package submission and test artifacts into an ExecutionPayload."""
        ...

    def compile_command(self) -> ExecutionCommand | None:
        """Command to compile source code before execution, or None for interpreted languages."""
        ...

    def test_command(self) -> ExecutionCommand:
        """Command to run tests in the sandbox."""
        ...


@runtime_checkable
class OutcomeParser(Protocol):
    """Protocol for parsing raw sandbox output into standardized scores and diffs."""

    def parse_execution(
        self,
        raw_result: ExecutionRawResult,
        config: AssignmentConfigV1,
    ) -> ParsedOutcome:
        """Parse stdout, stderr, and exit codes into a standardized ParsedOutcome."""
        ...


@runtime_checkable
class LanguageStrategy(LanguageRunner, OutcomeParser, Protocol):
    """Unified language execution and evaluation strategy."""

    pass
