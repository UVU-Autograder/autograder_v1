"""Model-solution files for a seed assignment, for the guardrails only.

The runtime gate blocks feedback that defines any name from the assignment's
model solution (a missing method is only there, not in the student's code). The
eval and the training-data gate read the same files from the seeds so they
measure what production enforces. Never put these files in a prompt.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

SEEDS = Path(__file__).resolve().parents[1] / "app" / "db" / "seeds"


def _resolve(seed: Path, filename: str) -> Path | None:
    """Same order as assignments.service.resolve_seed_artifact_path, without its database imports."""
    for path in (seed / filename, seed / "model_solution.py", SEEDS / "shared" / filename):
        if path.is_file():
            return path
    return None


def _seed_dir(slug: str) -> Path:
    for name in (slug, slug.replace("-", "_"), slug.replace("_", "-")):
        if (SEEDS / name).is_dir():
            return SEEDS / name
    return SEEDS / slug


@lru_cache(maxsize=None)
def _solution_files(slug: str) -> tuple[tuple[str, str], ...]:
    seed = _seed_dir(slug)
    config_path = seed / "config.json"
    if not config_path.is_file():
        return ()
    artifacts = json.loads(config_path.read_text(encoding="utf-8")).get("artifacts") or {}
    files: list[tuple[str, str]] = []
    for key, artifact in artifacts.items():
        if artifact.get("type") != "model_solution":
            continue
        name = artifact.get("display_filename") or key
        path = _resolve(seed, name)
        if path is None or path.suffix != ".py":
            continue  # images and data files define no names
        files.append((name, path.read_text(encoding="utf-8")))
    return tuple(files)


def solution_files(slug: str) -> dict[str, str]:
    """``{filename: source}`` of the seed's Python model-solution files (empty if none)."""
    return dict(_solution_files(slug))
