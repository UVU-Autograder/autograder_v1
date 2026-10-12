"""Read-only metadata + real synthetic Judge0 check, during a drained window.

Uses only instructor model fixtures; creates no run, changes no assignment, and
prints boolean checks. Execution files and Judge0 submissions use normal cleanup.
Run from backend with its deployed environment and a synthetic assignment selected.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from unittest.mock import patch

from sqlalchemy import func, select

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.settings import get_settings
from app.db.base import import_domain_models
from app.db.session import SessionLocal
from app.domains.assignments.engine import AssignmentSpecificationEngine
from app.domains.grading.engine import GradingEngine
from app.domains.runs.grading_package import capture_package
from app.domains.runs import retention
from app.domains.runs.models import ExecutionTicket, RunSummary
from app.integrations.judge0.client import DEFAULT_MEMORY_LIMIT, DEFAULT_WALL_TIME_LIMIT, Judge0Client


def report(check: str, passed: bool) -> None:
    print(json.dumps({"check": check, "passed": passed}), flush=True)
    if not passed:
        raise RuntimeError("Synthetic package check failed")


async def verify(course: str, assignment: str) -> None:
    import_domain_models()
    with SessionLocal() as db:
        unfinished = db.scalar(select(func.count()).select_from(RunSummary).where(
            RunSummary.workflow_type == "official", RunSummary.status.in_(("queue", "run")),
        ))
        tickets = db.scalar(select(func.count()).select_from(ExecutionTicket).where(
            ExecutionTicket.state.in_(("waiting", "active")), ExecutionTicket.expires_at > retention.utc_now(),
        ))
    report("workload_drained", unfinished == 0 and tickets == 0)
    package = capture_package(course, assignment)
    with SessionLocal() as db:
        model = AssignmentSpecificationEngine().prepare_model_solution_bundle(db, course, assignment)
    report("synthetic_fixture_matches_captured_config", model["config"] == package.config)
    parameters = package.execution_parameters
    settings = get_settings()
    calls: list[tuple[int, float, float, int]] = []
    deleted: list[bool] = []

    class RecordingClient(Judge0Client):
        async def create_submission(
            self, source_code: str, language_id: int, additional_files_b64: str | None = None,
            stdin: str | None = None, cpu_time_limit: float = 10.0,
            wall_time_limit: float = DEFAULT_WALL_TIME_LIMIT, memory_limit: int = DEFAULT_MEMORY_LIMIT,
        ) -> str:
            calls.append((language_id, cpu_time_limit, wall_time_limit, memory_limit))
            report("captured_runner_submitted", source_code == package.runner_source)
            report("captured_parameters_submitted", calls[-1] == (
                parameters.language_id, parameters.cpu_time_limit, parameters.wall_time_limit, parameters.memory_limit,
            ))
            return await super().create_submission(
                source_code=source_code, language_id=language_id, additional_files_b64=additional_files_b64,
                stdin=stdin, cpu_time_limit=cpu_time_limit, wall_time_limit=wall_time_limit, memory_limit=memory_limit,
            )

        async def delete_submission(self, token: str) -> bool:
            result = await super().delete_submission(token)
            deleted.append(result)
            absent = False
            for _ in range(5):
                response = await self._client.get(f"/submissions/{token}", params={"fields": "status"})
                if response.status_code == 404:
                    absent = True
                    break
                await asyncio.sleep(0.5)
            report("deleted_submission_non_retrievable", absent)
            return result

    # Only this CLI process's settings change, never service configuration or DB.
    language, timeout = settings.judge0_language_id, settings.test_execution_timeout_seconds
    settings.judge0_language_id = 1 if language != 1 else 2
    settings.test_execution_timeout_seconds = 1 if timeout != 1 else 2
    grader = GradingEngine(
        config=package.config, artifact_refs={}, allowed_concepts=package.concepts,
        preloaded_artifacts=package.preloaded_artifacts(), execution_parameters=parameters,
        runner_source=package.runner_source, fallback_helper=package.fallback_helper.decode(),
    )
    try:
        with patch("app.domains.grading.executor.create_judge0_client",
                   side_effect=lambda: RecordingClient(settings.judge0_url, settings.judge0_auth_token)):
            result = await grader.grade_submission(zip_data=model["zip_data"])
        expected_score = sum(item.points for item in package.config.scoring_items if item.item_type == "pytest")
        report("model_passed_captured_grading", result.success and result.score == expected_score)
        report("one_execution_deleted", len(calls) == 1 and deleted == [True])
    finally:
        settings.judge0_language_id, settings.test_execution_timeout_seconds = language, timeout


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--course", default="cs1400")
    parser.add_argument("--assignment", default="simple-python-functions")
    args = parser.parse_args()
    try:
        asyncio.run(verify(args.course, args.assignment))
    except Exception:
        print(json.dumps({"check": "host_package_smoke", "passed": False}), flush=True)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
