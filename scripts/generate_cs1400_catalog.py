#!/usr/bin/env python3
"""
Generate backend/app/db/seeds/cs1400_catalog.json from the Canvas course export
and verify that all module folders, assignment folders, and desc.md files exist.
"""

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CANVAS_EXPORT_DIR = Path(r"C:\Users\Jaxon\Downloads\cs-1400-002-2026-fall-full-term-export")
MODULE_META_PATH = CANVAS_EXPORT_DIR / "course_settings" / "module_meta.xml"
TARGET_CATALOG_PATH = REPO_ROOT / "backend" / "app" / "db" / "seeds" / "cs1400_catalog.json"
CS1400_DIR = REPO_ROOT / "cs1400"

CONCEPT_MAP = {
    1: ["variables"],
    2: ["exceptions"],
    3: ["functions"],
    4: ["conditionals", "loops"],
    5: ["exceptions"],
    6: [],
    7: ["file-io"],
    8: [],
    9: [],
    10: [],
    11: [],
    12: [],
    13: ["classes"],
    14: ["testing"],
}


def generate_catalog():
    tree = ET.parse(MODULE_META_PATH)
    root = tree.getroot()
    ns = {"c": "http://canvas.instructure.com/xsd/cccv1p0"}

    catalog = {"modules": {}, "assignments": []}

    for mod in root.findall(".//c:module", ns):
        title = mod.find("c:title", ns).text
        m_match = re.search(r"Module\s*(\d+)", title)
        if not m_match or int(m_match.group(1)) >= 15:
            continue
        m_num = int(m_match.group(1))
        mod_code = f"m{m_num}"

        clean_mod_title = re.sub(r"^(Module\s*\d+\s*:\s*)+", "", title).strip()
        clean_mod_name = f"Module {m_num}: {clean_mod_title}"

        catalog["modules"][mod_code] = {
            "name": clean_mod_name,
            "concepts": CONCEPT_MAP.get(m_num, []),
        }

        lab_idx = 1
        ps_idx = 1
        for it in mod.findall(".//c:item", ns):
            ct = it.find("c:content_type", ns).text
            it_title = it.find("c:title", ns).text
            if ct == "Assignment":
                mod_in_title = re.search(r"Module\s*(\d+):", it_title)
                if mod_in_title and int(mod_in_title.group(1)) != m_num:
                    continue
                if "Extra Credit" in it_title:
                    continue

                proj_match = re.search(r"Project\s*(\d+)", it_title)
                if "PS Lab" in it_title:
                    folder_name = f"ps_lab{ps_idx}"
                    slug = f"{mod_code}-ps-lab{ps_idx}"
                    curr_ps = ps_idx
                    ps_idx += 1
                    curr_type = "ps"
                elif proj_match:
                    folder_name = f"project{proj_match.group(1)}"
                    slug = f"{mod_code}-project{proj_match.group(1)}"
                    curr_type = "proj"
                elif "Lab" in it_title:
                    folder_name = f"lab{lab_idx}"
                    slug = f"{mod_code}-lab{lab_idx}"
                    curr_lab = lab_idx
                    lab_idx += 1
                    curr_type = "lab"
                else:
                    folder_name = f"assign{lab_idx}"
                    slug = f"{mod_code}-assign{lab_idx}"
                    curr_lab = lab_idx
                    lab_idx += 1
                    curr_type = "assign"

                # Clean and standardize title
                t = it_title
                t = re.sub(r"^Module\s*\d+\s*:\s*", "", t).strip()
                t = re.sub(r"^Submit\s*\|\s*", "", t).strip()
                t = (
                    t.replace("\u201c", '"')
                    .replace("\u201d", '"')
                    .replace("\u2018", "'")
                    .replace("\u2019", "'")
                    .replace("\u2013", "–")
                )

                if curr_type == "lab" and t.startswith("Lab |"):
                    t = f"Lab {curr_lab}: " + t[5:].strip()
                elif curr_type == "ps" and t.startswith("PS Lab |"):
                    t = f"PS Lab {curr_ps}: " + t[8:].strip()
                elif (
                    curr_type == "proj"
                    and proj_match
                    and t.startswith(f"Project {proj_match.group(1)} |")
                ):
                    t = f"Project {proj_match.group(1)}: " + t[
                        len(f"Project {proj_match.group(1)} |") :
                    ].strip()

                # Verify folder and desc.md existence
                desc_path = CS1400_DIR / mod_code / folder_name / "desc.md"
                if not desc_path.exists():
                    raise FileNotFoundError(f"Missing desc.md at {desc_path}")

                catalog["assignments"].append(
                    {
                        "module": mod_code,
                        "folder": f"{mod_code}/{folder_name}",
                        "slug": slug,
                        "title": t,
                    }
                )

    TARGET_CATALOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    TARGET_CATALOG_PATH.write_text(
        json.dumps(catalog, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"Wrote catalog to {TARGET_CATALOG_PATH}")
    print(f"Modules: {len(catalog['modules'])}")
    print(f"Assignments: {len(catalog['assignments'])}")


if __name__ == "__main__":
    generate_catalog()
