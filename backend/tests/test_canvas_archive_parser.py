"""Unit tests for CanvasArchiveParser pure domain module."""

import io
import zipfile
import pytest

from app.domains.ingestion.parser import (
    CanvasArchiveParser,
    CanvasParsingError,
    normalize_canvas_clean_filename,
)


def create_zip_archive(files: dict[str, bytes | str]) -> bytes:
    """Helper creating an in-memory ZIP archive from a dict of filename -> bytes/str."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, data in files.items():
            content = data.encode("utf-8") if isinstance(data, str) else data
            zf.writestr(name, content)
    return buf.getvalue()


def test_normalize_canvas_clean_filename():
    assert normalize_canvas_clean_filename("main-1.py") == "main.py"
    assert normalize_canvas_clean_filename("assignment_submission-42.py") == "assignment_submission.py"
    assert normalize_canvas_clean_filename("project-a1b2c3d4-e5f6-7890-abcd-ef1234567890.py") == "project.py"
    assert normalize_canvas_clean_filename("standard_file.py") == "standard_file.py"


def test_parse_canvas_filename_variants():
    parser = CanvasArchiveParser()

    # Standard submission
    parsed = parser.parse_canvas_filename("smithjohn_12345_67890_solution.py")
    assert parsed is not None
    student_name, is_late, user_id, sub_id, orig_file = parsed
    assert student_name == "smithjohn"
    assert not is_late
    assert user_id == "12345"
    assert sub_id == "67890"
    assert orig_file == "solution.py"

    # Late submission
    parsed_late = parser.parse_canvas_filename("doejane_LATE_54321_98765_main.py")
    assert parsed_late is not None
    student_name, is_late, user_id, sub_id, orig_file = parsed_late
    assert student_name == "doejane"
    assert is_late
    assert user_id == "54321"
    assert sub_id == "98765"
    assert orig_file == "main.py"

    # Non-canvas filename
    assert parser.parse_canvas_filename("random_script.py") is None


def test_parse_archive_bytes_groups_by_student():
    parser = CanvasArchiveParser()
    zip_bytes = create_zip_archive({
        "smithjohn_101_1001_main.py": "print('hello')",
        "smithjohn_101_1001_helper-1.py": "def help(): pass",
        "doejane_LATE_102_1002_solution.py": "def solve(): return 42",
        "unmatched_notes.txt": "some teacher notes",
    })

    batch = parser.parse_archive_bytes(zip_bytes)

    assert batch.submission_count == 2
    assert "101" in batch.canvas_user_ids
    assert "102" in batch.canvas_user_ids

    sub101 = batch.get_submission("101")
    assert sub101 is not None
    assert sub101.student_name == "smithjohn"
    assert not sub101.is_late
    assert len(sub101.files) == 2
    assert "main.py" in sub101.file_names
    assert "helper.py" in sub101.file_names  # normalized -1 stripped

    sub102 = batch.get_submission("102")
    assert sub102 is not None
    assert sub102.is_late
    assert len(sub102.files) == 1
    assert "solution.py" in sub102.file_names

    assert "unmatched_notes.txt" in batch.unmatched_files


def test_collision_resolution_keeps_larger_file():
    parser = CanvasArchiveParser()
    zip_bytes = create_zip_archive({
        "smithjohn_101_1001_main-1.py": "small",
        "smithjohn_101_1001_main-2.py": "this is a much larger submission content",
    })

    batch = parser.parse_archive_bytes(zip_bytes, extract_contents=True)
    sub = batch.get_submission("101")
    assert sub is not None
    assert len(sub.files) == 1
    assert sub.files[0].clean_filename == "main.py"
    assert sub.files[0].size_bytes == len("this is a much larger submission content")
    assert any("Collision" in w for w in batch.warnings)


def test_rejects_directory_traversal():
    parser = CanvasArchiveParser()
    zip_bytes = create_zip_archive({
        "../escape.py": "evil",
    })

    with pytest.raises(CanvasParsingError, match="Directory traversal"):
        parser.parse_archive_bytes(zip_bytes)


def test_rejects_oversized_archive():
    parser = CanvasArchiveParser()
    zip_bytes = create_zip_archive({
        "smithjohn_101_1001_main.py": "x" * 1000,
    })

    with pytest.raises(CanvasParsingError, match="size limit exceeded"):
        parser.parse_archive_bytes(zip_bytes, max_total_size=500)


def test_rejects_corrupted_archive():
    parser = CanvasArchiveParser()
    with pytest.raises(CanvasParsingError, match="Malformed or corrupted"):
        parser.parse_archive_bytes(b"not a valid zip file")
