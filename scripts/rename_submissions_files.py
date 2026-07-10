#!/usr/bin/env python3
import argparse
import os
import re
import shutil
from pathlib import Path

# Regex to match the suffix: -[UUID] or -[digits] at the end of the filename stem
SUFFIX_PATTERN = re.compile(
    r"-(?:([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})|([0-9]+))$"
)

def fix_filename_suffixes(directory: Path):
    print(f"Scanning files in: {directory}")
    # Gather all files first
    all_files = [f for f in directory.rglob("*") if f.is_file()]
    
    renamed_count = 0
    conflict_count = 0

    for path in all_files:
        if not path.exists():
            continue
            
        stem = path.stem
        match = SUFFIX_PATTERN.search(stem)
        if match:
            new_stem = SUFFIX_PATTERN.sub("", stem)
            new_name = new_stem + path.suffix
            new_path = path.parent / new_name
            
            if new_path.exists():
                conflict_count += 1
                # Conflict resolution: keep the larger file (which is more likely to contain the actual code/work)
                existing_size = new_path.stat().st_size
                current_size = path.stat().st_size
                
                if current_size >= existing_size:
                    print(f"Conflict: Keeping larger/newer '{path.name}' ({current_size} bytes) over '{new_name}' ({existing_size} bytes)")
                    new_path.unlink()
                    shutil.move(str(path), str(new_path))
                    renamed_count += 1
                else:
                    print(f"Conflict: Keeping existing '{new_name}' ({existing_size} bytes) over smaller/older '{path.name}' ({current_size} bytes)")
                    path.unlink()
            else:
                print(f"Renaming: '{path.name}' -> '{new_name}'")
                shutil.move(str(path), str(new_path))
                renamed_count += 1

    print(f"Finished folder. Renamed/Cleaned: {renamed_count} files. Handled conflicts: {conflict_count}")

def main():
    parser = argparse.ArgumentParser(
        description="Clean student filenames by removing trailing Canvas suffix numbers/UUIDs (e.g. -7 or -041f3f21...)."
    )
    parser.add_argument("target_dir", type=str, help="The root directory containing submissions folders to clean.")
    args = parser.parse_args()

    root_dir = Path(args.target_dir).resolve()
    if not root_dir.exists() or not root_dir.is_dir():
        print(f"Error: Target directory does not exist or is not a directory: {args.target_dir}")
        return

    # Find all 'submissions' subdirectories
    submissions_dirs = []
    if root_dir.name == "submissions":
        submissions_dirs.append(root_dir)
    else:
        for path in root_dir.rglob("submissions"):
            if path.is_dir():
                submissions_dirs.append(path)
                
    if not submissions_dirs:
        print("No 'submissions' folders found. Scanning the entire target directory instead...")
        submissions_dirs.append(root_dir)

    for sub_dir in submissions_dirs:
        print(f"\nProcessing submissions folder: {sub_dir}")
        fix_filename_suffixes(sub_dir)

    print("\nFilename suffix cleanup complete!")

if __name__ == "__main__":
    main()
