import io
import shutil
import zipfile
from pathlib import Path
from app.domains.assignments.schemas import AssignmentConfigV1

class ExtractionError(Exception):
    """Raised when ZIP validation or extraction fails."""
    pass

def safe_extract_zip(zip_data: bytes, extract_dir: Path, max_total_size: int | None = None) -> None:
    """Safely extracts a ZIP file to extract_dir.
    Rejects directory traversal (paths escaping extract_dir) and total size exceeding max_total_size.
    """
    from app.core.settings import get_settings
    if max_total_size is None:
        max_total_size = get_settings().default_max_zip_size

    extract_dir = Path(extract_dir).resolve()
    extract_dir.mkdir(parents=True, exist_ok=True)
    
    total_size = 0
    try:
        with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
            # First pass: check for traversal and calculate total uncompressed size
            for info in zf.infolist():
                if Path(info.filename).is_absolute():
                    raise ExtractionError("Directory traversal detected in ZIP file")

                target_path = (extract_dir / info.filename).resolve()
                try:
                    target_path.relative_to(extract_dir)
                except ValueError:
                    raise ExtractionError("Directory traversal detected in ZIP file")

                mode = info.external_attr >> 16
                if mode & 0o120000 == 0o120000:
                    raise ExtractionError("Symbolic links are not allowed in ZIP files")
                
                total_size += info.file_size
                if total_size > max_total_size:
                    raise ExtractionError("ZIP extraction size limit exceeded")
            
            # Second pass: extract safely
            for info in zf.infolist():
                target_path = (extract_dir / info.filename).resolve()
                try:
                    target_path.relative_to(extract_dir)
                except ValueError:
                    raise ExtractionError("Directory traversal detected in ZIP file")
                if info.is_dir():
                    target_path.mkdir(parents=True, exist_ok=True)
                else:
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    with zf.open(info) as source, open(target_path, "wb") as target:
                        shutil.copyfileobj(source, target)
    except zipfile.BadZipFile as e:
        raise ExtractionError("Malformed or corrupted ZIP file") from e

def cleanup_system_files(directory: Path) -> None:
    """Recursively deletes hidden/system files and directories like .DS_Store, __MACOSX, Thumbs.db."""
    directory = Path(directory).resolve()
    paths = sorted(list(directory.rglob("*")), key=lambda p: len(p.parts), reverse=True)
    for path in paths:
        if not path.exists():
            continue
        name_lower = path.name.lower()
        if name_lower in {".ds_store", "__macosx", "thumbs.db", ".git", ".idea", ".vscode"}:
            if path.is_dir():
                shutil.rmtree(path, ignore_errors=True)
            else:
                path.unlink(missing_ok=True)


def normalize_root_directory(extract_dir: Path) -> None:
    """If extract_dir contains exactly one directory and no files, moves all files
    from that directory up into extract_dir and deletes the empty subdirectory.
    """
    extract_dir = Path(extract_dir).resolve()
    cleanup_system_files(extract_dir)
    items = list(extract_dir.iterdir())
    
    if len(items) == 1 and items[0].is_dir():
        single_dir = items[0]
        for sub_item in single_dir.iterdir():
            target = extract_dir / sub_item.name
            shutil.move(str(sub_item), str(target))
        single_dir.rmdir()

def validate_submission_bundle(extract_dir: Path, config: AssignmentConfigV1) -> None:
    """Validates the structure of the extracted student submission against configuration constraints."""
    from app.core.settings import get_settings
    settings = get_settings()
    extract_dir = Path(extract_dir).resolve()
    
    # 1. Normalize root automatically
    normalize_root_directory(extract_dir)
    
    # 2. Enforce max_files count (global safety limit)
    all_files = [f for f in extract_dir.rglob("*") if f.is_file()]
    if len(all_files) > settings.default_max_files:
        raise ValueError(f"Submission exceeds maximum allowed files limit: {settings.default_max_files}")
            
    # 3. Identify and enforce strictly required files
    non_mandatory_paths = set()
    for req in config.bundle.file_requirements:
        if req.requirement_type in {"one_of", "optional", "pattern"}:
            non_mandatory_paths.update(req.paths)
            
    strictly_required = [p for p in config.bundle.required_files if p not in non_mandatory_paths]
    for filename in strictly_required:
        target_file = extract_dir / filename
        if not target_file.exists() or not target_file.is_file():
            raise ValueError(f"Required file '{filename}' is missing.")

    # 4. Process file_requirements
    for req in config.bundle.file_requirements:
        satisfied = False
        if req.requirement_type == "exact":
            target = extract_dir / req.paths[0]
            if target.exists() and target.is_file():
                satisfied = True
            else:
                raise ValueError(f"Required file '{req.paths[0]}' is missing.")
                
        elif req.requirement_type == "one_of":
            for path in req.paths:
                target = extract_dir / path
                if target.exists() and target.is_file():
                    satisfied = True
                    break
            if not satisfied:
                raise ValueError(f"None of the options for '{req.label or req.key}' were found ({', '.join(req.paths)}).")
                
        elif req.requirement_type == "optional":
            target = extract_dir / req.paths[0]
            if not target.exists() or target.is_file():
                satisfied = True
            else:
                raise ValueError(f"Optional path '{req.paths[0]}' exists but is not a file.")
                
        elif req.requirement_type == "pattern":
            pattern = req.paths[0]
            matches = [m for m in extract_dir.glob(pattern) if m.is_file()]
            if matches:
                satisfied = True
            else:
                raise ValueError(f"No files matching pattern '{pattern}' were found.")

    # 5. Check entrypoint
    entrypoint_path = extract_dir / config.bundle.entrypoint
    if not entrypoint_path.exists() or not entrypoint_path.is_file():
        raise ValueError(f"Entrypoint file '{config.bundle.entrypoint}' not found in submission.")


import re

CANVAS_FILENAME_PATTERN = re.compile(r"^([a-zA-Z0-9\-]+)_([0-9]+)_([0-9]+)_(.*)$")


def parse_canvas_filename(filename: str) -> tuple[str, str, str, str] | None:
    """Parse Canvas filename pattern.

    Returns (student_name, canvas_user_id, submission_id, original_filename) if matching,
    else None.
    """
    match = CANVAS_FILENAME_PATTERN.match(filename)
    if not match:
        return None
    return match.groups()


def group_canvas_files(extract_dir: Path) -> tuple[dict[str, list[Path]], list[Path]]:
    """Scan extract_dir and group files by canvas_user_id.

    Returns (grouped_files, unmatched_files).
    """
    extract_dir = Path(extract_dir).resolve()
    grouped_files = {}
    unmatched_files = []

    for path in extract_dir.iterdir():
        if path.is_file():
            parsed = parse_canvas_filename(path.name)
            if parsed:
                _, canvas_user_id, _, _ = parsed
                grouped_files.setdefault(canvas_user_id, []).append(path)
            else:
                unmatched_files.append(path)

    return grouped_files, unmatched_files


def prepare_student_bundle(student_files: list[Path], student_dir: Path) -> None:
    """Prepare a student's submission workspace directory.

    Extracts any zip files, and copies loose files renamed to their original filenames.
    """
    student_dir = Path(student_dir).resolve()
    student_dir.mkdir(parents=True, exist_ok=True)

    for path in student_files:
        parsed = parse_canvas_filename(path.name)
        if not parsed:
            continue
        _, _, _, original_filename = parsed

        if original_filename.lower().endswith(".zip"):
            try:
                safe_extract_zip(path.read_bytes(), student_dir)
            except Exception as e:
                raise ValueError(f"Failed to extract student ZIP '{original_filename}': {e}")
        else:
            dest = (student_dir / original_filename).resolve()
            try:
                dest.relative_to(student_dir)
            except ValueError as exc:
                raise ValueError(f"Unsafe Canvas filename '{original_filename}'") from exc
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, dest)
