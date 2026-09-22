"""Storage reference resolver for assignment artifacts.

Resolves opaque storage reference strings (``seed://…``, ``file://…``) to
concrete filesystem paths so that callers can load artifact content without
knowing the underlying storage layout.
"""

from __future__ import annotations

from pathlib import Path

SEEDS_DIR = Path(__file__).resolve().parents[2] / "db" / "seeds"


def resolve_storage_ref(storage_ref: str) -> Path:
    """Resolve a *storage_ref* string to a local filesystem :class:`~pathlib.Path`.

    Supported URI schemes:

    ``seed://<example_dir>/<filename>``
        Maps to ``backend/app/db/seeds/<example_dir>/<filename>``
        inside the repository root.  Used for built-in seed/example artifacts.

    ``file://<absolute_path>``
        Maps directly to the given absolute path on the local filesystem.

    Args:
        storage_ref: A URI string identifying the artifact.

    Returns:
        The resolved :class:`~pathlib.Path`.

    Raises:
        ValueError: If the URI scheme is not recognised.
        FileNotFoundError: If the resolved path does not exist on disk.
    """
    if storage_ref.startswith("seed://"):
        relative = storage_ref[len("seed://"):]
        path = SEEDS_DIR / relative
    elif storage_ref.startswith("file://"):
        raw_path = storage_ref[len("file://"):]
        path = Path(raw_path)
    else:
        scheme = storage_ref.split("://", 1)[0] if "://" in storage_ref else "<none>"
        raise ValueError(
            f"Unsupported storage reference scheme '{scheme}' "
            f"in storage_ref: {storage_ref!r}"
        )

    if not path.exists():
        raise FileNotFoundError(
            f"Resolved path does not exist: {path}  (storage_ref={storage_ref!r})"
        )

    return path


def load_artifact_content(storage_ref: str) -> bytes:
    """Load the raw file content for a storage reference.

    This is a convenience wrapper around :func:`resolve_storage_ref` that
    reads and returns the file bytes.

    Args:
        storage_ref: A URI string identifying the artifact.

    Returns:
        The raw bytes of the resolved file.

    Raises:
        ValueError: If the URI scheme is not recognised.
        FileNotFoundError: If the resolved path does not exist on disk.
    """
    path = resolve_storage_ref(storage_ref)
    return path.read_bytes()
