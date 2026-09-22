"""Artifact storage integration package.

Re-exports the public API from :mod:`.resolver` for convenient access.
"""

from app.integrations.artifacts.resolver import (
    load_artifact_content,
    resolve_storage_ref,
)

__all__ = [
    "load_artifact_content",
    "resolve_storage_ref",
]
