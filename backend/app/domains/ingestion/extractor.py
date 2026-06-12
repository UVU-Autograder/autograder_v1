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
                # Rejects path traversal attempts
                target_path = (extract_dir / info.filename).resolve()
                if not str(target_path).startswith(str(extract_dir)):
                    raise ExtractionError("Directory traversal detected in ZIP file")
                
                total_size += info.file_size
                if total_size > max_total_size:
                    raise ExtractionError("ZIP extraction size limit exceeded")
            
            # Second pass: extract safely
            for info in zf.infolist():
                target_path = (extract_dir / info.filename).resolve()
                if info.is_dir():
                    target_path.mkdir(parents=True, exist_ok=True)
                else:
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    with zf.open(info) as source, open(target_path, "wb") as target:
                        shutil.copyfileobj(source, target)
    except zipfile.BadZipFile as e:
        raise ExtractionError("Malformed or corrupted ZIP file") from e

def normalize_root_directory(extract_dir: Path) -> None:
    """If extract_dir contains exactly one directory and no files, moves all files
    from that directory up into extract_dir and deletes the empty subdirectory.
    """
    extract_dir = Path(extract_dir).resolve()
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
