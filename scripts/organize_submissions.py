#!/usr/bin/env python3
import argparse
import os
import re
import shutil
import tempfile
import zipfile
from pathlib import Path

# Regex to parse canvas filename pattern:
# [studentname]_[id]_[otherid]_[original_filename]
# e.g., johnsmith_12345_67890_lab1.zip or john_smith_12345_67890_student_functions.py
CANVAS_FILENAME_PATTERN = re.compile(r"^([a-zA-Z0-9\-_\s]+?)_([0-9]+)_([0-9]+)_(.*)$")


def parse_canvas_filename(filename: str):
    match = CANVAS_FILENAME_PATTERN.match(filename)
    if not match:
        return None
    return match.groups()


def cleanup_system_files(directory: Path) -> None:
    """Recursively deletes hidden/system files and directories like .DS_Store, __MACOSX, Thumbs.db."""
    directory = Path(directory).resolve()
    paths = sorted(list(directory.rglob("*")), key=lambda p: len(p.parts), reverse=True)
    for path in paths:
        if not path.exists():
            continue
        name_lower = path.name.lower()
        if name_lower in {
            ".ds_store",
            "__macosx",
            "thumbs.db",
            ".git",
            ".idea",
            ".vscode",
            "__pycache__",
        }:
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
        for sub_item in list(single_dir.iterdir()):
            target = extract_dir / sub_item.name
            if target.exists():
                if target.is_dir():
                    shutil.rmtree(target)
                else:
                    target.unlink()
            shutil.move(str(sub_item), str(target))
        single_dir.rmdir()


def sanitize_zip_path(filename: str) -> str:
    """Sanitizes each path component of a ZIP filename to be safe for Windows.
    This strips trailing spaces and dots from directory/file names.
    """
    normalized = filename.replace("\\", "/")
    parts = normalized.split("/")
    sanitized = []
    for part in parts:
        cleaned = part.rstrip(" .")
        if cleaned:
            sanitized.append(cleaned)
    return "/".join(sanitized)


def is_relative_to(target: Path, base: Path) -> bool:
    """Robust, cross-platform relative path check that avoids Windows casing/short-name bugs."""
    try:
        target_abs = os.path.abspath(target)
        base_abs = os.path.abspath(base)
        if os.name == "nt":
            target_abs = target_abs.lower()
            base_abs = base_abs.lower()
        common = os.path.commonpath([target_abs, base_abs])
        return common == base_abs
    except Exception:
        return False


def safe_extract_zip(zip_path: Path, extract_dir: Path) -> None:
    """Safely extracts a ZIP file to extract_dir, preventing directory traversal and sanitizing paths."""
    extract_dir = Path(extract_dir).resolve()
    extract_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path) as zf:
        for info in zf.infolist():
            clean_filename = sanitize_zip_path(info.filename)
            if not clean_filename:
                continue

            if Path(clean_filename).is_absolute() or clean_filename.startswith(".."):
                print(
                    f"Warning: Absolute or traversal path ignored in {zip_path.name}: {info.filename}"
                )
                continue

            target_path = (extract_dir / clean_filename).resolve()
            if not is_relative_to(target_path, extract_dir):
                print(
                    f"Warning: Directory traversal attempt ignored in {zip_path.name}: {info.filename}"
                )
                continue

            if info.is_dir():
                target_path.mkdir(parents=True, exist_ok=True)
            else:
                target_path.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(info) as source, open(target_path, "wb") as target:
                    shutil.copyfileobj(source, target)


def main():
    parser = argparse.ArgumentParser(
        description="Organize Canvas bulk student submissions into a tidy directory structure."
    )
    parser.add_argument("zip_path", type=str, help="Path to the submissions.zip file.")
    parser.add_argument(
        "-o",
        "--output-dir",
        type=str,
        default="submissions",
        help="Directory where processed submissions will be saved.",
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Overwrite the output directory if it exists.",
    )
    args = parser.parse_args()

    zip_file_path = Path(args.zip_path).resolve()
    if not zip_file_path.exists() or not zip_file_path.is_file():
        print(f"Error: ZIP file not found at {args.zip_path}")
        return

    output_dir = Path(args.output_dir).resolve()
    if output_dir.exists():
        if args.force:
            print(f"Removing existing output directory: {output_dir}")
            shutil.rmtree(output_dir)
        else:
            print(
                f"Error: Output directory already exists at {output_dir}. Use -f or --force to overwrite it."
            )
            return

    output_dir.mkdir(parents=True, exist_ok=True)

    # Use a temporary directory to unzip submissions.zip first
    with tempfile.TemporaryDirectory() as temp_dir_str:
        temp_dir = Path(temp_dir_str)
        print("Extracting main submissions ZIP to temporary directory...")
        try:
            safe_extract_zip(zip_file_path, temp_dir)
        except Exception as e:
            print(f"Error extracting main ZIP: {e}")
            return

        # Scan and group files by canvas_user_id (to ensure all files for the same student are in one folder)
        # key: canvas_user_id -> list of file info dicts
        student_files = {}
        unmatched_files = []

        for item in temp_dir.iterdir():
            if not item.is_file():
                continue

            parsed = parse_canvas_filename(item.name)
            if not parsed:
                unmatched_files.append(item)
                continue

            student_name, canvas_user_id, submission_id, original_filename = parsed
            is_zip = original_filename.lower().endswith(".zip")

            student_files.setdefault(canvas_user_id, []).append({
                "is_zip": is_zip,
                "path": item,
                "submission_id": submission_id,
                "original_filename": original_filename
            })

        print(f"Processing {len(student_files)} student submissions...")

        # Process each student's submission
        for canvas_user_id, files in student_files.items():
            # Determine the folder name of format [id]_[otherid]
            # Try to find a zip file first to use its submission_id (otherid)
            zip_files = [f for f in files if f["is_zip"]]
            if zip_files:
                selected_submission_id = zip_files[0]["submission_id"]
            else:
                selected_submission_id = files[0]["submission_id"]

            folder_name = f"{canvas_user_id}_{selected_submission_id}"
            student_dir = output_dir / folder_name
            student_dir.mkdir(parents=True, exist_ok=True)

            for file_info in files:
                path = file_info["path"]
                orig_name = file_info["original_filename"]

                if file_info["is_zip"]:
                    # Create a temp directory for this zip's extraction
                    with tempfile.TemporaryDirectory() as zip_temp_dir_str:
                        zip_temp_dir = Path(zip_temp_dir_str)
                        try:
                            safe_extract_zip(path, zip_temp_dir)
                            cleanup_system_files(zip_temp_dir)
                            normalize_root_directory(zip_temp_dir)

                            # Copy contents of normalized zip extraction into student folder
                            for sub_item in zip_temp_dir.iterdir():
                                dest = student_dir / sub_item.name
                                if dest.exists():
                                    if dest.is_dir():
                                        shutil.rmtree(dest)
                                    else:
                                        dest.unlink()
                                shutil.move(str(sub_item), str(dest))
                        except Exception as e:
                            print(
                                f"Warning: Failed to extract student ZIP for {folder_name}: {e}"
                            )
                else:
                    # Copy loose file renamed to its original name
                    dest = student_dir / orig_name
                    shutil.copy2(path, dest)

            # Post-cleanup of student folder just in case
            cleanup_system_files(student_dir)

        # Handle unmatched files
        if unmatched_files:
            unmatched_dir = output_dir / "unmatched"
            unmatched_dir.mkdir(parents=True, exist_ok=True)
            print(
                f"Warning: Found {len(unmatched_files)} files not matching the Canvas format. Moving them to '{unmatched_dir.name}/'"
            )
            for file_path in unmatched_files:
                shutil.copy2(file_path, unmatched_dir / file_path.name)

        print("\nSuccessfully organized all submissions!")
        print(f"Processed submissions are saved in: {output_dir}")


if __name__ == "__main__":
    main()
