"""Prepare trusted multi-file adapters and normalize their protocol-2 results."""
from __future__ import annotations

import base64
import io
import json
from pathlib import Path
import zipfile

from app.domains.assignments.schemas import AssignmentConfigV1
from app.domains.grading.protocols import ExecutionPayload, ExecutionRawResult, ParsedOutcome, StaticAnalysisOutcome
from app.domains.grading.result_parser import calculate_scores, parse_pytest_json

RESOURCES = Path(__file__).parent / "resources"
RESERVED = frozenset({"compile", "run", "ag_adapter.py", "ag_config.json", "ag_web_runner.cjs", "ag_program"})


def adapter_source() -> str:
    return ((Path(__file__).parent / "normalizer.py").read_text(encoding="utf-8")
            + "\nWEB_RUNNER_SOURCE = " + repr((RESOURCES / "web_runner.cjs").read_text(encoding="utf-8"))
            + "\n" + (RESOURCES / "multilang_runtime.py").read_text(encoding="utf-8"))


def test_files(config: AssignmentConfigV1) -> list[str]:
    return [Path(artifact.display_filename or key).name for key, artifact in config.artifacts.items()
            if artifact.type == "test_file"]


def static_analysis(exec_dir: Path, config: AssignmentConfigV1) -> StaticAnalysisOutcome:
    # Imported lazily: the ingestion package imports runs.grading_package, which imports this module.
    from app.domains.ingestion.extractor import validate_submission_bundle

    try:
        validate_submission_bundle(exec_dir, config)
        if any(p.name.casefold() in RESERVED or p.name.startswith("ag_object_") for p in exec_dir.rglob("*") if p.is_file()):
            raise ValueError("Reserved grading harness filename in submission.")
    except ValueError as exc:
        return StaticAnalysisOutcome(passed=False, failure_category="missing_required_file", failure_message=str(exc))
    return StaticAnalysisOutcome(passed=True)


def prepare_bundle(exec_dir: Path, config: AssignmentConfigV1, *, stdin: str | None = None,
                   cpu_time_limit: float | None = None, memory_limit: int | None = None,
                   wall_time_limit: float | None = None, runner_source: str | None = None) -> ExecutionPayload:
    trusted = {"ag_adapter.py": runner_source or adapter_source(),
               "ag_config.json": json.dumps({"framework": config.test_framework, "language": config.bundle.language,
                   "entrypoint": config.bundle.entrypoint, "test_files": test_files(config),
                   "items": [item.model_dump() for item in config.scoring_items]}),
               "run": "#!/bin/bash\nexec /usr/local/python-3.11.9/bin/python3.11 -I ag_adapter.py\n"}
    if config.bundle.language != "web":
        trusted["compile"] = "#!/bin/bash\nexec /usr/local/python-3.11.9/bin/python3.11 -I ag_adapter.py --compile\n"
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for file in sorted(exec_dir.rglob("*")):
            if not file.is_file():
                continue
            # Trusted harness names always come from the adapter, never the submission.
            if file.name.casefold() in RESERVED or file.name.startswith("ag_object_"):
                continue
            archive.write(file, file.relative_to(exec_dir).as_posix())
        for name, source in trusted.items():
            entry = zipfile.ZipInfo(name)
            entry.external_attr = (0o100755 if name in {"compile", "run"} else 0o100644) << 16
            archive.writestr(entry, source.encode())
    return ExecutionPayload(source_code=None, language_id=89,
                            additional_files_b64=base64.b64encode(buffer.getvalue()).decode(),
                            cpu_time_limit=cpu_time_limit or 30, wall_time_limit=wall_time_limit or 45,
                            memory_limit=memory_limit or 262144, stdin=stdin)


def parse_execution(raw: ExecutionRawResult, config: AssignmentConfigV1, expected_manifest: dict | None = None) -> ParsedOutcome:
    if raw.status_id == 6:
        messages = (raw.compile_output or raw.stderr or "Compilation failed.").splitlines()[:20]
        return ParsedOutcome(success=False, max_score=config.base_points, failure_category="compilation_error",
                             failure_message="The submission did not compile.", compiler_errors=messages)
    result = parse_pytest_json(raw.stdout, stderr=raw.stderr, exit_code=raw.exit_code, expected_manifest=expected_manifest)
    score, details = calculate_scores(result, config.scoring_items)
    return ParsedOutcome(success=result.error_message is None, score=score, max_score=config.base_points,
                         test_results=details, failure_category=result.failure_category if result.error_message else None,
                         failure_message=result.error_message, raw_data=result)
