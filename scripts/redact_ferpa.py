#!/usr/bin/env python3
import argparse
import os
import re
import shutil
from pathlib import Path

# List of student names to check
STUDENT_LIST = [
    {"first": "Andrew", "last": "Allen"},
    {"first": "Dawn", "last": "Armstrong"},
    {"first": "Angel", "last": "Ayala Zalazar"},
    {"first": "Benjamin", "last": "Bates"},
    {"first": "Hans", "last": "Belka"},
    {"first": "Elizabeth", "last": "Brady"},
    {"first": "Kynnaston", "last": "Brown"},
    {"first": "Chandralekha", "last": "Chaganti"},
    {"first": "Landon", "last": "Clark"},
    {"first": "Keith", "last": "Clinger"},
    {"first": "Caleb", "last": "Conklin"},
    {"first": "Braden", "last": "Hermansen"},
    {"first": "Savanna", "last": "Kim"},
    {"first": "Chandler", "last": "Lake"},
    {"first": "Douglas", "last": "London"},
    {"first": "Christopher", "last": "Miller"},
    {"first": "Michael", "last": "Mitchell"},
    {"first": "Garth", "last": "Neptune"},
    {"first": "Heyam", "last": "Obied"},
    {"first": "Jase", "last": "Riley"},
    {"first": "Bradon", "last": "Sandage"},
    {"first": "Frankie", "last": "Sellers"},
    {"first": "Jacob", "last": "Smith"},
    {"first": "Keoni", "last": "Spencer"},
    {"first": "Julio", "last": "Ureta-Lopez"},
    {"first": "Luke", "last": "Wilde"},
    {"first": "Martin", "last": "Zanazzi"}
]

EXCLUDED_USERNAMES = {"skim"}

def get_redact_patterns(first, last):
    first_esc = re.escape(first)
    last_esc = re.escape(last)
    
    patterns = [
        # First Last (e.g., Andrew Allen)
        re.compile(rf"\b{first_esc}\s+{last_esc}\b", re.IGNORECASE),
        # Last, First (e.g., Allen, Andrew)
        re.compile(rf"\b{last_esc},\s+{first_esc}\b", re.IGNORECASE),
        # Last First (e.g., Allen Andrew)
        re.compile(rf"\b{last_esc}\s+{first_esc}\b", re.IGNORECASE),
        # First.Last or Last.First (e.g., andrew.allen, allen.andrew)
        re.compile(rf"\b{first_esc}\.{last_esc}\b", re.IGNORECASE),
        re.compile(rf"\b{last_esc}\.{first_esc}\b", re.IGNORECASE),
        # concatenated names (e.g., andrewallen, allenandrew, batesbenjamin)
        re.compile(rf"\b{first_esc}{last_esc}\b", re.IGNORECASE),
        re.compile(rf"\b{last_esc}{first_esc}\b", re.IGNORECASE),
    ]
    
    first_initial = first[0].lower()
    last_initial = last[0].lower()
    
    if len(first_initial) == 1 and len(last) > 3:
        username = f"{first_initial}{last}".lower()
        if username not in EXCLUDED_USERNAMES:
            patterns.append(re.compile(rf"\b{re.escape(first_initial)}{last_esc}\b", re.IGNORECASE))
            
    if len(last_initial) == 1 and len(first) > 3:
        username = f"{last_initial}{first}".lower()
        if username not in EXCLUDED_USERNAMES:
            patterns.append(re.compile(rf"\b{re.escape(last_initial)}{first_esc}\b", re.IGNORECASE))
            
    return patterns

def is_text_file(file_path: Path) -> bool:
    binary_extensions = {
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico', '.pdf', '.zip', '.tar', '.gz',
        '.db', '.sqlite', '.exe', '.dll', '.so', '.pyc', '.pyd', '.class', '.jar'
    }
    if file_path.suffix.lower() in binary_extensions:
        return False
    try:
        with open(file_path, 'r', encoding='utf-8', errors='strict') as f:
            f.read(1024)
        return True
    except UnicodeDecodeError:
        return False

def redact_path_name(path: Path, student_patterns: list) -> Path:
    name = path.name
    new_name = name
    for student, patterns in student_patterns:
        for pattern in patterns:
            if pattern.search(new_name):
                new_name = pattern.sub("", new_name)
                # Clean up multiple underscores/spaces/dashes
                new_name = re.sub(r'[_-\s]+', '_', new_name)
                new_name = new_name.strip('_-. ')
                
    if new_name != name:
        if not new_name:
            new_name = "redacted_student_file" + path.suffix
        new_path = path.parent / new_name
        counter = 1
        while new_path.exists():
            stem = Path(new_name).stem
            suffix = Path(new_name).suffix
            new_path = path.parent / f"{stem}_{counter}{suffix}"
            counter += 1
        
        print(f"Renaming: {path} -> {new_path}")
        shutil.move(str(path), str(new_path))
        return new_path
    return path

def redact_file_contents(file_path: Path, student_patterns: list) -> bool:
    try:
        content = file_path.read_text(encoding='utf-8', errors='ignore')
    except Exception as e:
        print(f"Failed to read file {file_path}: {e}")
        return False
        
    modified = False
    new_content = content
    
    for student, patterns in student_patterns:
        for pattern in patterns:
            if pattern.search(new_content):
                new_content = pattern.sub("[REDACTED_STUDENT_NAME]", new_content)
                modified = True
                
    if modified:
        try:
            file_path.write_text(new_content, encoding='utf-8')
            print(f"Redacted file content: {file_path}")
            return True
        except Exception as e:
            print(f"Failed to write file {file_path}: {e}")
    return False

def main():
    parser = argparse.ArgumentParser(description="Scan and redact FERPA-risky student names from submissions files, folder names, and file contents.")
    parser.add_argument("target_dir", type=str, help="The root directory containing submissions folders to clean.")
    args = parser.parse_args()

    root_dir = Path(args.target_dir).resolve()
    if not root_dir.exists() or not root_dir.is_dir():
        print(f"Error: Target directory does not exist or is not a directory: {args.target_dir}")
        return

    # Compile patterns for all students
    student_patterns = []
    for s in STUDENT_LIST:
        patterns = get_redact_patterns(s["first"], s["last"])
        student_name_str = f"{s['first']} {s['last']}"
        student_patterns.append((student_name_str, patterns))

    print(f"Scanning target directory: {root_dir}")
    
    # First, find all 'submissions' subdirectories to focus on
    submissions_dirs = []
    if root_dir.name == "submissions":
        submissions_dirs.append(root_dir)
    else:
        # Search for any subdirectory named 'submissions'
        for path in root_dir.rglob("submissions"):
            if path.is_dir():
                submissions_dirs.append(path)
                
    if not submissions_dirs:
        print("No 'submissions' folders found. Scanning the entire target directory instead...")
        submissions_dirs.append(root_dir)

    renamed_count = 0
    redacted_content_count = 0

    for sub_dir in submissions_dirs:
        print(f"\nProcessing submissions folder: {sub_dir}")
        
        # We must gather all items and sort them by depth (reverse order)
        # to rename files and folders starting from the deepest level.
        all_items = sorted(list(sub_dir.rglob("*")), key=lambda p: len(p.parts), reverse=True)
        
        # Rename paths (files and directories) first
        processed_paths = []
        for path in all_items:
            if not path.exists():
                # Might have been renamed or parent renamed already
                continue
            new_path = redact_path_name(path, student_patterns)
            if new_path != path:
                renamed_count += 1
            processed_paths.append(new_path)
            
        # Re-gather all text files in the sanitized structure to perform content redaction
        for path in sub_dir.rglob("*"):
            if path.is_file() and is_text_file(path):
                if redact_file_contents(path, student_patterns):
                    redacted_content_count += 1

    print("\nFERPA Scan and Redaction Complete!")
    print(f"Total path names renamed: {renamed_count}")
    print(f"Total files redacted in-place: {redacted_content_count}")

if __name__ == "__main__":
    main()
