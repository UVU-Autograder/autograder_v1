"""Effective execution parameters, independently of runtime-image management."""
from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from app.integrations.judge0.client import DEFAULT_MEMORY_LIMIT, DEFAULT_WALL_TIME_LIMIT


@dataclass(frozen=True)
class PreloadedArtifacts:
    """Assignment artifacts loaded once for an official grading package."""

    files: dict[str, bytes]
    pytest_filenames: list[str]


def load_fallback_helper() -> bytes:
    """Use the same built-in helper source for live and captured execution."""
    domain = Path(__file__).resolve().parent / "resources" / "python_autograder_helpers.py"
    shared = Path(__file__).resolve().parents[2] / "db" / "seeds" / "shared" / "python_autograder_helpers.py"
    return (domain if domain.exists() else shared).read_bytes()


class ExecutionParameters(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    language_id: int = Field(ge=1)
    cpu_time_limit: float = Field(gt=0, allow_inf_nan=False)
    wall_time_limit: float = Field(default=DEFAULT_WALL_TIME_LIMIT, gt=0, allow_inf_nan=False)
    memory_limit: int = Field(default=DEFAULT_MEMORY_LIMIT, ge=1)
    preinstalled_dependencies: list[str]
