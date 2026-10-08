"""Grading engine facade delegating to the unified GradingPipeline.

Encapsulates submission intake, workspace orchestration, and backward-compatible
entrypoints for official execution workers and Celery tasks.
"""
from __future__ import annotations

import logging
from pathlib import Path

from app.core.settings import get_settings
from app.domains.assignments.schemas import AssignmentConfigV1
from app.domains.grading.executor import execute_pytest_in_judge0
from app.domains.grading.pipeline import (
    EvaluationReport,
    GradingPipeline,
    SubmissionPayload,
    preload_grading_artifacts,
)
from app.domains.grading.runtime import ExecutionParameters, PreloadedArtifacts, load_fallback_helper
from app.integrations.artifacts.resolver import load_artifact_content

logger = logging.getLogger(__name__)

# Re-export EvaluationReport as GradingResult for backwards compatibility across callers & tests
GradingResult = EvaluationReport

__all__ = [
    "GradingResult",
    "GradingEngine",
    "preload_grading_artifacts",
]


class GradingEngine:
    """Deep domain engine for executing Python submission grading.

    Maintains backwards compatibility for existing worker dispatchers while
    delegating evaluation logic to :class:`~app.domains.grading.pipeline.GradingPipeline`.
    """

    def __init__(
        self,
        config: AssignmentConfigV1,
        artifact_refs: dict[str, str],
        allowed_concepts: list[str],
        preloaded_artifacts: PreloadedArtifacts | None = None,
        execution_parameters: ExecutionParameters | None = None,
        runner_source: str | None = None,
        fallback_helper: bytes | None = None,
    ) -> None:
        self.config = config
        self.artifact_refs = artifact_refs
        self.allowed_concepts = allowed_concepts
        self.preloaded_artifacts = preloaded_artifacts
        self.settings = get_settings()
        self.execution_parameters = execution_parameters
        self.runner_source = runner_source
        self.fallback_helper = fallback_helper
        if execution_parameters is not None and (runner_source is None or fallback_helper is None):
            raise ValueError("Frozen execution requires captured runner and helper inputs")

    def _create_pipeline(self) -> GradingPipeline:
        """Construct the GradingPipeline with module-level callable bindings."""
        return GradingPipeline(
            config=self.config,
            artifact_refs=self.artifact_refs,
            allowed_concepts=self.allowed_concepts,
            preloaded_artifacts=self.preloaded_artifacts,
            execution_parameters=self.execution_parameters,
            runner_source=self.runner_source,
            fallback_helper=self.fallback_helper,
            executor_fn=execute_pytest_in_judge0,
            load_artifact_fn=load_artifact_content,
            load_fallback_helper_fn=load_fallback_helper,
        )

    def grade_submission_sync(
        self,
        zip_data: bytes | None = None,
        *,
        bundle_dir: Path | None = None,
        stdin: str | None = None,
    ) -> GradingResult:
        """Synchronous convenience entrypoint for Celery workers and offline execution."""
        pipeline = self._create_pipeline()
        payload = SubmissionPayload(
            zip_data=zip_data,
            bundle_dir=bundle_dir,
            stdin=stdin,
        )
        return pipeline.evaluate_sync(payload)

    async def grade_submission(
        self,
        zip_data: bytes | None = None,
        *,
        bundle_dir: Path | None = None,
        stdin: str | None = None,
        official_run_id: int | None = None,
    ) -> GradingResult:
        """Execute the full grading pipeline for a single student submission bundle.

        Provide exactly one of ``zip_data`` or ``bundle_dir``.
        """
        pipeline = self._create_pipeline()
        payload = SubmissionPayload(
            zip_data=zip_data,
            bundle_dir=bundle_dir,
            stdin=stdin,
            official_run_id=official_run_id,
        )
        return await pipeline.evaluate(payload)

    def _inject_artifacts(self, exec_dir: Path) -> list[str]:
        """Write assignment artifacts into exec_dir; return pytest filenames."""
        pipeline = self._create_pipeline()
        return pipeline._inject_artifacts(exec_dir)
