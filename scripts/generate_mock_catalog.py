#!/usr/bin/env python3
"""
Generate frontend/lib/mock-catalog.json containing all real CS 1400 and CS 1410
courses, modules, and assignments with real instructor markdown descriptions.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SEEDS_DIR = REPO_ROOT / "backend" / "app" / "db" / "seeds"
CS1400_CATALOG = SEEDS_DIR / "cs1400_catalog.json"
CS1410_CATALOG = SEEDS_DIR / "cs1410_catalog.json"
TARGET_PATH = REPO_ROOT / "frontend" / "lib" / "mock-catalog.json"


def clean_summary(text: str) -> str:
    lines = [
        line.strip()
        for line in text.strip().split("\n")
        if line.strip() and not line.strip().startswith("#")
    ]
    filtered = [
        l for l in lines
        if l.lower() not in ("objectives", "structure", "problem")
        and not l.startswith("```")
    ]
    if not filtered:
        return "Assignment description and requirements."
    joined = ""
    for l in filtered:
        clean_l = l.lstrip("-* \t").strip()
        if not clean_l:
            continue
        if not joined:
            joined = clean_l
        else:
            joined += " " + clean_l
        if len(joined) > 180:
            break
    if len(joined) > 220:
        return joined[:217] + "..."
    return joined


def build_catalog() -> dict:
    # 1. Build CS 1400
    c1400_raw = json.loads(CS1400_CATALOG.read_text(encoding="utf-8"))
    c1400_modules = []
    c1400_accumulated_concepts: set[str] = set()
    mod_id = 1
    mod_key_to_id = {}
    mod_key_to_name = {}
    mod_key_to_concepts = {}

    for key, mod_data in c1400_raw["modules"].items():
        c1400_accumulated_concepts.update(mod_data.get("concepts", []))
        c1400_modules.append({
            "id": mod_id,
            "key": key,
            "name": mod_data["name"],
            "concepts": sorted(list(c1400_accumulated_concepts)),
        })
        mod_key_to_id[key] = mod_id
        mod_key_to_name[key] = mod_data["name"]
        mod_key_to_concepts[key] = sorted(list(c1400_accumulated_concepts))
        mod_id += 1

    c1400_assignments = []
    for a in c1400_raw["assignments"]:
        folder = a.get("folder", "")
        desc_path = REPO_ROOT / "cs1400" / folder / "desc.md"
        desc = desc_path.read_text(encoding="utf-8") if desc_path.exists() else ""
        mod_key = a["module"]
        c1400_assignments.append({
            "id": a["slug"],
            "slug": a["slug"],
            "course_id": "cs1400",
            "title": a["title"],
            "module_name": mod_key_to_name.get(mod_key, f"Module {mod_key}"),
            "module_id": mod_key_to_id.get(mod_key, 1),
            "summary": clean_summary(desc),
            "description": desc,
            "concepts": mod_key_to_concepts.get(mod_key, []),
        })

    # 2. Build CS 1410
    c1410_raw = json.loads(CS1410_CATALOG.read_text(encoding="utf-8"))
    c1410_modules = []
    c1410_accumulated_concepts: set[str] = set()
    mod_id = 1
    mod_key_to_id_1410 = {}
    mod_key_to_name_1410 = {}
    mod_key_to_concepts_1410 = {}

    for key, mod_data in c1410_raw["modules"].items():
        c1410_accumulated_concepts.update(mod_data.get("concepts", []))
        c1410_modules.append({
            "id": mod_id,
            "key": key,
            "name": mod_data["name"],
            "concepts": sorted(list(c1410_accumulated_concepts)),
        })
        mod_key_to_id_1410[key] = mod_id
        mod_key_to_name_1410[key] = mod_data["name"]
        mod_key_to_concepts_1410[key] = sorted(list(c1410_accumulated_concepts))
        mod_id += 1

    # Map CS 1410 descriptions
    cs1410_root = REPO_ROOT / "cs1410"
    cs1410_descs: dict[str, str] = {}
    for p in cs1410_root.glob("**/desc.md"):
        slug = p.parent.name
        cs1410_descs[slug] = p.read_text(encoding="utf-8")

    c1410_assignments = []
    for a in c1410_raw["assignments"]:
        slug = a["slug"]
        desc = cs1410_descs.get(slug, "")
        mod_key = a["module"]
        c1410_assignments.append({
            "id": slug,
            "slug": slug,
            "course_id": "cs1410",
            "title": a["title"],
            "module_name": mod_key_to_name_1410.get(mod_key, f"Module {mod_key}"),
            "module_id": mod_key_to_id_1410.get(mod_key, 1),
            "summary": clean_summary(desc),
            "description": desc,
            "concepts": mod_key_to_concepts_1410.get(mod_key, []),
        })

    return {
        "cs1400": {
            "course_id": "cs1400",
            "code": "CS 1400",
            "title": "Fundamentals of Programming",
            "term": "Fall 2026",
            "default_concepts": ["variables", "conditionals", "functions"],
            "modules": c1400_modules,
            "assignments": c1400_assignments,
        },
        "cs1410": {
            "course_id": "cs1410",
            "code": "CS 1410",
            "title": "Object-Oriented Programming",
            "term": "Fall 2026",
            "default_concepts": [
                "variables",
                "conditionals",
                "functions",
                "classes",
                "inheritance",
            ],
            "modules": c1410_modules,
            "assignments": c1410_assignments,
        },
    }


def main():
    catalog = build_catalog()
    TARGET_PATH.write_text(json.dumps(catalog, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Generated {TARGET_PATH}")
    print(f"CS 1400: {len(catalog['cs1400']['assignments'])} assignments, {len(catalog['cs1400']['modules'])} modules")
    print(f"CS 1410: {len(catalog['cs1410']['assignments'])} assignments, {len(catalog['cs1410']['modules'])} modules")


if __name__ == "__main__":
    main()
