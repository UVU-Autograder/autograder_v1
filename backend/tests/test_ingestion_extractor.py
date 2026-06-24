import io
import sys
import pytest
import zipfile
from pathlib import Path
from unittest.mock import patch

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.domains.ingestion.extractor import (
    safe_extract_zip,
    normalize_root_directory,
    validate_submission_bundle,
    ExtractionError,
)
from app.domains.assignments.schemas import AssignmentConfigV1


def create_zip_bytes(files_dict: dict[str, bytes]) -> bytes:
    """Helper to create ZIP file in memory."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for filepath, data in files_dict.items():
            zf.writestr(filepath, data)
    return buf.getvalue()


def test_safe_extract_zip_success(tmp_path: Path):
    files = {
        "main.py": b"print('hello')",
        "utils/helper.py": b"def help(): pass",
    }
    zip_data = create_zip_bytes(files)
    extract_dir = tmp_path / "extracted"

    safe_extract_zip(zip_data, extract_dir)

    assert (extract_dir / "main.py").read_text() == "print('hello')"
    assert (extract_dir / "utils/helper.py").read_text() == "def help(): pass"


def test_safe_extract_zip_traversal(tmp_path: Path):
    # Try to write a file that attempts traversal
    files = {
        "../escaped.txt": b"traversal",
    }
    zip_data = create_zip_bytes(files)
    extract_dir = tmp_path / "extracted"

    with pytest.raises(ExtractionError, match="Directory traversal detected in ZIP file"):
        safe_extract_zip(zip_data, extract_dir)


def test_safe_extract_zip_bomb(tmp_path: Path):
    files = {
        "large.txt": b"x" * 100,
    }
    zip_data = create_zip_bytes(files)
    extract_dir = tmp_path / "extracted"

    # Set max_total_size to 50 bytes, but we have 100 bytes
    with pytest.raises(ExtractionError, match="ZIP extraction size limit exceeded"):
        safe_extract_zip(zip_data, extract_dir, max_total_size=50)


def test_safe_extract_zip_malformed(tmp_path: Path):
    extract_dir = tmp_path / "extracted"
    with pytest.raises(ExtractionError, match="Malformed or corrupted ZIP file"):
        safe_extract_zip(b"not a zip file", extract_dir)


def test_cleanup_system_files(tmp_path: Path):
    from app.domains.ingestion.extractor import cleanup_system_files
    directory = tmp_path / "target"
    directory.mkdir()
    
    (directory / ".DS_Store").write_text("dsstore")
    (directory / "Thumbs.db").write_text("thumbs")
    (directory / "normal_file.py").write_text("python")
    
    macosx_dir = directory / "__MACOSX"
    macosx_dir.mkdir()
    (macosx_dir / "nested_file.jpg").write_text("image")
    
    cleanup_system_files(directory)
    
    assert not (directory / ".DS_Store").exists()
    assert not (directory / "Thumbs.db").exists()
    assert not macosx_dir.exists()
    assert (directory / "normal_file.py").exists()


def test_normalize_root_directory_single_subdir(tmp_path: Path):
    # Create a structure: extract_dir/subdir/file.py
    extract_dir = tmp_path / "extracted"
    subdir = extract_dir / "my_project_root"
    subdir.mkdir(parents=True)
    (subdir / "main.py").write_text("main")
    (subdir / "utils.py").write_text("utils")
    
    (extract_dir / ".DS_Store").write_text("junk")
    (extract_dir / "__MACOSX").mkdir()
    (extract_dir / "__MACOSX" / "nested.xml").write_text("xml")

    normalize_root_directory(extract_dir)

    assert (extract_dir / "main.py").exists()
    assert (extract_dir / "utils.py").exists()
    assert not subdir.exists()
    assert not (extract_dir / ".DS_Store").exists()
    assert not (extract_dir / "__MACOSX").exists()


def test_normalize_root_directory_no_change_multiple_items(tmp_path: Path):
    extract_dir = tmp_path / "extracted"
    extract_dir.mkdir(parents=True)
    (extract_dir / "main.py").write_text("main")
    (extract_dir / "subdir").mkdir()
    (extract_dir / "subdir" / "utils.py").write_text("utils")

    normalize_root_directory(extract_dir)

    assert (extract_dir / "main.py").exists()
    assert (extract_dir / "subdir").exists()
    assert (extract_dir / "subdir" / "utils.py").exists()


def test_normalize_root_directory_no_change_file_only(tmp_path: Path):
    extract_dir = tmp_path / "extracted"
    extract_dir.mkdir(parents=True)
    (extract_dir / "main.py").write_text("main")

    normalize_root_directory(extract_dir)

    assert (extract_dir / "main.py").exists()


@pytest.fixture
def base_config_dict():
    return {
        "schema_version": 1,
        "bundle": {
            "required_files": ["main.py", "utils.py"],
            "entrypoint": "main.py",
            "file_requirements": []
        },
        "artifacts": {
            "pytest_file": {
                "type": "pytest_file",
            }
        },
        "tests": [
            {
                "key": "test_1",
                "label": "Test 1",
                "points": 10,
                "extra_credit": False
            }
        ]
    }


def test_validate_submission_bundle_success(tmp_path: Path, base_config_dict):
    extract_dir = tmp_path / "extracted"
    extract_dir.mkdir(parents=True)
    (extract_dir / "main.py").write_text("main")
    (extract_dir / "utils.py").write_text("utils")

    config = AssignmentConfigV1.model_validate(base_config_dict)
    validate_submission_bundle(extract_dir, config)  # should not raise any error


def test_validate_submission_bundle_missing_required(tmp_path: Path, base_config_dict):
    extract_dir = tmp_path / "extracted"
    extract_dir.mkdir(parents=True)
    (extract_dir / "main.py").write_text("main")
    # missing utils.py

    config = AssignmentConfigV1.model_validate(base_config_dict)
    with pytest.raises(ValueError, match="Required file 'utils.py' is missing."):
        validate_submission_bundle(extract_dir, config)


def test_validate_submission_bundle_max_files_exceeded(tmp_path: Path, base_config_dict):
    extract_dir = tmp_path / "extracted"
    extract_dir.mkdir(parents=True)
    (extract_dir / "main.py").write_text("main")
    (extract_dir / "utils.py").write_text("utils")
    for i in range(4):
        (extract_dir / f"extra_{i}.py").write_text("extra")

    config = AssignmentConfigV1.model_validate(base_config_dict)
    from app.core.settings import get_settings
    with patch.object(get_settings(), "default_max_files", 5):
        with pytest.raises(ValueError, match="Submission exceeds maximum allowed files limit"):
            validate_submission_bundle(extract_dir, config)


def test_validate_submission_bundle_root_flattening(tmp_path: Path, base_config_dict):
    extract_dir = tmp_path / "extracted"
    subdir = extract_dir / "nested"
    subdir.mkdir(parents=True)
    (subdir / "main.py").write_text("main")
    (subdir / "utils.py").write_text("utils")

    config = AssignmentConfigV1.model_validate(base_config_dict)
    validate_submission_bundle(extract_dir, config)

    assert (extract_dir / "main.py").exists()
    assert (extract_dir / "utils.py").exists()


def test_validate_submission_bundle_file_requirements_exact(tmp_path: Path, base_config_dict):
    base_config_dict["bundle"]["file_requirements"] = [
        {
            "key": "exact_req",
            "requirement_type": "exact",
            "paths": ["extra.py"]
        }
    ]
    # In pydantic validator, any files in file_requirements are added to known_paths,
    # but let's make sure entrypoint.path is in required_files.
    base_config_dict["bundle"]["required_files"].append("extra.py")

    extract_dir = tmp_path / "extracted"
    extract_dir.mkdir(parents=True)
    (extract_dir / "main.py").write_text("main")
    (extract_dir / "utils.py").write_text("utils")

    config = AssignmentConfigV1.model_validate(base_config_dict)
    
    # Missing exact.py
    with pytest.raises(ValueError, match="Required file 'extra.py' is missing"):
        validate_submission_bundle(extract_dir, config)

    (extract_dir / "extra.py").write_text("extra")
    validate_submission_bundle(extract_dir, config)


def test_validate_submission_bundle_file_requirements_one_of(tmp_path: Path, base_config_dict):
    base_config_dict["bundle"]["file_requirements"] = [
        {
            "key": "one_of_req",
            "requirement_type": "one_of",
            "paths": ["opt1.py", "opt2.py"]
        }
    ]
    # add to required_files just in case, though the validator allows it
    base_config_dict["bundle"]["required_files"].append("opt1.py")

    extract_dir = tmp_path / "extracted"
    extract_dir.mkdir(parents=True)
    (extract_dir / "main.py").write_text("main")
    (extract_dir / "utils.py").write_text("utils")

    config = AssignmentConfigV1.model_validate(base_config_dict)

    # Missing both opt1.py and opt2.py
    with pytest.raises(ValueError, match="None of the options for 'one_of_req' were found"):
        validate_submission_bundle(extract_dir, config)

    # Adding one option should satisfy it
    (extract_dir / "opt2.py").write_text("opt2")
    validate_submission_bundle(extract_dir, config)


def test_validate_submission_bundle_file_requirements_optional(tmp_path: Path, base_config_dict):
    base_config_dict["bundle"]["file_requirements"] = [
        {
            "key": "opt_req",
            "requirement_type": "optional",
            "paths": ["maybe.py"]
        }
    ]
    base_config_dict["bundle"]["required_files"].append("maybe.py")

    extract_dir = tmp_path / "extracted"
    extract_dir.mkdir(parents=True)
    (extract_dir / "main.py").write_text("main")
    (extract_dir / "utils.py").write_text("utils")

    config = AssignmentConfigV1.model_validate(base_config_dict)

    # Option is not present - valid
    validate_submission_bundle(extract_dir, config)

    # Option is a directory - invalid
    (extract_dir / "maybe.py").mkdir()
    with pytest.raises(ValueError, match="Optional path 'maybe.py' exists but is not a file"):
        validate_submission_bundle(extract_dir, config)

    # Option is a file - valid
    (extract_dir / "maybe.py").rmdir()
    (extract_dir / "maybe.py").write_text("maybe")
    validate_submission_bundle(extract_dir, config)


def test_validate_submission_bundle_file_requirements_pattern(tmp_path: Path, base_config_dict):
    base_config_dict["bundle"]["file_requirements"] = [
        {
            "key": "pat_req",
            "requirement_type": "pattern",
            "paths": ["*.txt"]
        }
    ]
    # No paths in pattern needs to be in required_files unless entrypoint uses it,
    # but entrypoint needs to be in required_files. Let's make sure it's valid.

    extract_dir = tmp_path / "extracted"
    extract_dir.mkdir(parents=True)
    (extract_dir / "main.py").write_text("main")
    (extract_dir / "utils.py").write_text("utils")

    config = AssignmentConfigV1.model_validate(base_config_dict)

    # No files matching *.txt - invalid
    with pytest.raises(ValueError, match="No files matching pattern '\\*\\.txt' were found"):
        validate_submission_bundle(extract_dir, config)

    (extract_dir / "something.txt").write_text("text")
    validate_submission_bundle(extract_dir, config)


from app.domains.ingestion.extractor import (
    parse_canvas_filename,
    group_canvas_files,
    prepare_student_bundle,
)


def test_parse_canvas_filename():
    assert parse_canvas_filename("jaxonlarsen_12345_67890_student_functions.py") == (
        "jaxonlarsen",
        "12345",
        "67890",
        "student_functions.py",
    )
    assert parse_canvas_filename("easton-smith_24680_13579_project.zip") == (
        "easton-smith",
        "24680",
        "13579",
        "project.zip",
    )
    assert parse_canvas_filename("invalid_filename.py") is None


def test_group_canvas_files(tmp_path: Path):
    extract_dir = tmp_path / "canvas_extracted"
    extract_dir.mkdir()
    (extract_dir / "jaxonlarsen_12345_67890_student_functions.py").write_text("code1")
    (extract_dir / "jaxonlarsen_12345_67890_helper.py").write_text("code2")
    (extract_dir / "eastonsmith_24680_13579_submission.zip").write_bytes(b"zip")
    (extract_dir / "unmatched_file.txt").write_text("garbage")

    grouped, unmatched = group_canvas_files(extract_dir)

    assert "12345" in grouped
    assert len(grouped["12345"]) == 2
    assert {p.name for p in grouped["12345"]} == {
        "jaxonlarsen_12345_67890_student_functions.py",
        "jaxonlarsen_12345_67890_helper.py",
    }

    assert "24680" in grouped
    assert len(grouped["24680"]) == 1

    assert len(unmatched) == 1
    assert unmatched[0].name == "unmatched_file.txt"


def test_prepare_student_bundle_loose_files(tmp_path: Path):
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    f1 = src_dir / "jaxonlarsen_12345_67890_student_functions.py"
    f1.write_text("print('f1')")
    f2 = src_dir / "jaxonlarsen_12345_67890_helper.py"
    f2.write_text("print('f2')")

    student_dir = tmp_path / "student_12345"

    prepare_student_bundle([f1, f2], student_dir)

    assert (student_dir / "student_functions.py").read_text() == "print('f1')"
    assert (student_dir / "helper.py").read_text() == "print('f2')"


def test_prepare_student_bundle_zip_file(tmp_path: Path):
    src_dir = tmp_path / "src"
    src_dir.mkdir()

    nested_zip_data = create_zip_bytes({"main.py": b"print('nested')"})

    zip_filename = src_dir / "eastonsmith_24680_13579_submission.zip"
    zip_filename.write_bytes(nested_zip_data)

    student_dir = tmp_path / "student_24680"

    prepare_student_bundle([zip_filename], student_dir)

    assert (student_dir / "main.py").read_text() == "print('nested')"
