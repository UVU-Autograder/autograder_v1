"""Pure domain parser for Canvas submission export archives.

Operates strictly on ZIP bytes or directory paths with ZERO database dependencies,
encapsulating Canvas filename regex matching, student identifier extraction,
submission grouping, version suffix stripping, and collision tracking.
"""

from __future__ import annotations

import io
import re
import zipfile
from dataclasses import dataclass, field
from pathlib import Path


CANVAS_FILENAME_PATTERN = re.compile(
    r"^([a-zA-Z0-9\-]+)_(LATE_)?([0-9]+)_([0-9]+)_(.*)$"
)

CANVAS_FILE_SUFFIX_PATTERN = re.compile(
    r"-(?:([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})|([0-9]+))$"
)


class CanvasParsingError(Exception):
    """Raised when an archive violates structure, safety bounds, or cannot be parsed."""


@dataclass
class ParsedSubmissionFile:
    """A single file belonging to a student submission."""

    raw_filename: str
    clean_filename: str
    size_bytes: int
    is_zip: bool = False
    content: bytes | None = None


@dataclass
class ParsedStudentSubmission:
    """A student's parsed submission group within a Canvas batch."""

    canvas_user_id: str
    student_name: str
    submission_id: str
    is_late: bool
    files: list[ParsedSubmissionFile] = field(default_factory=list)

    @property
    def file_names(self) -> list[str]:
        return [f.clean_filename for f in self.files]


@dataclass
class ParsedCanvasBatch:
    """Aggregated parsed result of a full Canvas ZIP export archive."""

    submissions: list[ParsedStudentSubmission] = field(default_factory=list)
    unmatched_files: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    total_archive_bytes: int = 0

    @property
    def submission_count(self) -> int:
        return len(self.submissions)

    @property
    def canvas_user_ids(self) -> list[str]:
        return [s.canvas_user_id for s in self.submissions]

    def get_submission(self, canvas_user_id: str) -> ParsedStudentSubmission | None:
        for s in self.submissions:
            if s.canvas_user_id == canvas_user_id:
                return s
        return None


def normalize_canvas_clean_filename(filename: str) -> str:
    """Strip trailing Canvas duplicate/UUID/number suffixes from a filename stem."""
    path = Path(filename)
    new_stem = CANVAS_FILE_SUFFIX_PATTERN.sub("", path.stem)
    if new_stem == path.stem:
        return filename
    return f"{new_stem}{path.suffix}"


class CanvasArchiveParser:
    """Pure, database-agnostic parser for Canvas export archives."""

    def __init__(self, default_max_bytes: int = 100 * 1024 * 1024) -> None:
        self.default_max_bytes = default_max_bytes

    def parse_canvas_filename(
        self, filename: str
    ) -> tuple[str, bool, str, str, str] | None:
        """Parse Canvas export filename pattern.

        Returns (student_name, is_late, canvas_user_id, submission_id, original_filename)
        if matching, else None.
        """
        match = CANVAS_FILENAME_PATTERN.match(filename)
        if not match:
            return None
        student_name, late_marker, canvas_user_id, submission_id, original_filename = (
            match.groups()
        )
        is_late = bool(late_marker)
        return student_name, is_late, canvas_user_id, submission_id, original_filename

    def parse_archive_bytes(
        self,
        zip_data: bytes,
        max_total_size: int | None = None,
        extract_contents: bool = False,
    ) -> ParsedCanvasBatch:
        """Parse an in-memory Canvas export ZIP into a strongly-typed ParsedCanvasBatch.

        Guarantees:
        - Checks for directory traversal and rejects symbolic links.
        - Enforces max total uncompressed size bounds.
        - Groups files by student Canvas user ID.
        - Deduplicates and resolves filename collisions.
        - 0 database calls or ORM imports.
        """
        effective_max = (
            max_total_size if max_total_size is not None else self.default_max_bytes
        )

        total_uncompressed = 0
        student_map: dict[str, ParsedStudentSubmission] = {}
        unmatched_files: list[str] = []
        warnings: list[str] = []

        try:
            with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
                for info in zf.infolist():
                    path = Path(info.filename)
                    if path.is_absolute() or ".." in path.parts:
                        raise CanvasParsingError(
                            "Directory traversal detected in ZIP file"
                        )

                    mode = info.external_attr >> 16
                    if mode & 0o120000 == 0o120000:
                        raise CanvasParsingError(
                            "Symbolic links are not allowed in ZIP files"
                        )

                    total_uncompressed += info.file_size
                    if total_uncompressed > effective_max:
                        raise CanvasParsingError(
                            f"ZIP extraction size limit exceeded ({effective_max} bytes)"
                        )

                    if info.is_dir() or len(path.parts) != 1:
                        # Canvas root exports contain submissions at the top level
                        if not info.is_dir():
                            unmatched_files.append(info.filename)
                        continue

                    parsed = self.parse_canvas_filename(path.name)
                    if not parsed:
                        unmatched_files.append(path.name)
                        continue

                    (
                        student_name,
                        is_late,
                        canvas_user_id,
                        submission_id,
                        original_filename,
                    ) = parsed

                    clean_name = normalize_canvas_clean_filename(original_filename)
                    is_zip = clean_name.lower().endswith(".zip")
                    file_bytes = zf.read(info) if extract_contents else None

                    parsed_file = ParsedSubmissionFile(
                        raw_filename=path.name,
                        clean_filename=clean_name,
                        size_bytes=info.file_size,
                        is_zip=is_zip,
                        content=file_bytes,
                    )

                    if canvas_user_id not in student_map:
                        student_map[canvas_user_id] = ParsedStudentSubmission(
                            canvas_user_id=canvas_user_id,
                            student_name=student_name,
                            submission_id=submission_id,
                            is_late=is_late,
                            files=[parsed_file],
                        )
                    else:
                        sub = student_map[canvas_user_id]
                        # Check collision on clean_filename
                        existing_idx = next(
                            (
                                i
                                for i, f in enumerate(sub.files)
                                if f.clean_filename == clean_name
                            ),
                            None,
                        )
                        if existing_idx is not None:
                            existing_file = sub.files[existing_idx]
                            warnings.append(
                                f"Collision for student {canvas_user_id} on {clean_name}: "
                                f"keeping larger file ({max(existing_file.size_bytes, parsed_file.size_bytes)} bytes)"
                            )
                            if parsed_file.size_bytes >= existing_file.size_bytes:
                                sub.files[existing_idx] = parsed_file
                        else:
                            sub.files.append(parsed_file)

        except zipfile.BadZipFile as exc:
            raise CanvasParsingError("Malformed or corrupted ZIP file") from exc

        return ParsedCanvasBatch(
            submissions=list(student_map.values()),
            unmatched_files=unmatched_files,
            warnings=warnings,
            total_archive_bytes=total_uncompressed,
        )
