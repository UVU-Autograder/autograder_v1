"""C/C++ grading through the trusted multi-file supervisor."""
from pathlib import Path

from app.domains.assignments.schemas import AssignmentConfigV1
from app.domains.grading import multilang
from app.domains.grading.protocols import ExecutionCommand, ExecutionPayload, ExecutionRawResult, ParsedOutcome, StaticAnalysisOutcome


class CppStrategy:
    @property
    def language_name(self) -> str:
        return "cpp"

    def static_analysis(self, exec_dir: Path, config: AssignmentConfigV1,
                        allowed_concepts: list[str] | None) -> StaticAnalysisOutcome:
        return multilang.static_analysis(exec_dir, config)

    def prepare_bundle(self, exec_dir: Path, config: AssignmentConfigV1,
                       support_artifacts: dict[str, bytes], stdin: str | None = None, *,
                       language_id: int | None = None, cpu_time_limit: float | None = None,
                       memory_limit: int | None = None, wall_time_limit: float | None = None,
                       runner_source: str | None = None) -> ExecutionPayload:
        if language_id not in (None, 89):
            raise ValueError("Native/Web execution requires Judge0 multi-file language 89")
        return multilang.prepare_bundle(exec_dir, config, stdin=stdin, cpu_time_limit=cpu_time_limit,
                                        memory_limit=memory_limit, wall_time_limit=wall_time_limit,
                                        runner_source=runner_source)

    def compile_command(self) -> ExecutionCommand | None:
        return None

    def test_command(self) -> ExecutionCommand:
        return ExecutionCommand(command="run")

    def parse_execution(self, raw_result: ExecutionRawResult, config: AssignmentConfigV1) -> ParsedOutcome:
        return multilang.parse_execution(raw_result, config)
