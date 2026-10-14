#!/usr/bin/env python3
"""
Convert Canvas Course Export for CS 1400 into the autograder course structure
matching cs1410 format:
- cs1400/m{X}/overview.md
- cs1400/m{X}/lab1/desc.md
- cs1400/m{X}/lab1/submissions/
- etc.
All Markdown is converted deterministically and verbatim from the instructor's
Canvas HTML without any AI rewriting or paraphrasing.
"""

import os
import re
import shutil
import xml.etree.ElementTree as ET
import lxml.html

CANVAS_EXPORT_DIR = r"C:\Users\Jaxon\Downloads\cs-1400-002-2026-fall-full-term-export"
TARGET_CS1400_DIR = r"C:\Users\Jaxon\coding\autograder_v1\cs1400"


def html_to_verbatim_markdown(raw_html: str) -> str:
    """
    Deterministically converts Canvas HTML to clean GitHub-Flavored Markdown.
    Preserves 100% of instructor text, variables, parameters, and sample output.
    Strips DesignPLUS framework tags, decorative icons, and inline styles.
    """
    if not raw_html or not raw_html.strip():
        return ""

    tree = lxml.html.fromstring(raw_html)

    # 1. Strip DesignPLUS / Canvas decorative / style / image elements
    for el in tree.xpath(
        '//i[contains(@class, "fa")] | //style | //script | //span[contains(@class, "dp-icon")] | //div[@id="dpCustomCss"] | //img'
    ):
        el.drop_tree()

    def convert_element(el, list_depth=0, is_ol=False, ol_idx=1) -> str:
        tag = el.tag.lower() if isinstance(el.tag, str) else ""
        text = el.text or ""
        tail = el.tail or ""

        # Handle tables
        if tag == "table":
            rows = []
            for tr in el.xpath(".//tr"):
                cells = [
                    re.sub(
                        r"\s+",
                        " ",
                        "".join(convert_element(c) for c in tr.xpath("./th | ./td")),
                    ).strip()
                    for c in tr.xpath("./th | ./td")
                ]
                if any(cells):
                    rows.append(cells)
            if not rows:
                return tail
            max_cols = max(len(r) for r in rows)
            padded = [r + [""] * (max_cols - len(r)) for r in rows]
            res = ["\n"]
            res.append("| " + " | ".join(padded[0]) + " |")
            res.append("| " + " | ".join(["---"] * max_cols) + " |")
            for r in padded[1:]:
                res.append("| " + " | ".join(r) + " |")
            res.append("\n")
            return "\n".join(res) + tail

        # Recursively process children
        children_strs = []
        if tag == "ol":
            idx = 1
            for child in el:
                if isinstance(child.tag, str) and child.tag.lower() == "li":
                    children_strs.append(
                        convert_element(child, list_depth + 1, is_ol=True, ol_idx=idx)
                    )
                    idx += 1
                else:
                    children_strs.append(convert_element(child, list_depth))
        elif tag == "ul":
            for child in el:
                if isinstance(child.tag, str) and child.tag.lower() == "li":
                    children_strs.append(
                        convert_element(child, list_depth + 1, is_ol=False)
                    )
                else:
                    children_strs.append(convert_element(child, list_depth))
        else:
            for child in el:
                children_strs.append(convert_element(child, list_depth, is_ol, ol_idx))

        children_md = "".join(children_strs)

        if tag in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            level = int(tag[1])
            inner = (text + children_md).strip()
            inner = re.sub(r"[\xa0\s]+", " ", inner)
            if not inner:
                return tail
            return f"\n\n{'#' * level} {inner}\n\n" + tail

        elif tag == "p":
            inner = (text + children_md).strip()
            inner = re.sub(r"\xa0", " ", inner)
            if not inner:
                return tail
            return f"\n\n{inner}\n\n" + tail

        elif tag == "li":
            indent = "  " * max(0, list_depth - 1)
            bullet = f"{ol_idx}. " if is_ol else "- "
            inner = (text + children_md).strip()
            inner = re.sub(r"[\xa0\s]+", " ", inner)
            return f"\n{indent}{bullet}{inner}" + tail

        elif tag in ["ul", "ol"]:
            return f"\n{children_md}\n" + tail

        elif tag in ["strong", "b"]:
            inner = (text + children_md).strip()
            if not inner:
                return tail
            return f"**{inner}**" + tail

        elif tag in ["em", "i"]:
            inner = (text + children_md).strip()
            if not inner:
                return tail
            return f"*{inner}*" + tail

        elif tag == "code":
            inner = text + children_md
            if "\n" in inner:
                return f"\n```text\n{inner.strip()}\n```\n" + tail
            return f"`{inner}`" + tail

        elif tag == "pre":
            inner = text + children_md
            return f"\n\n```text\n{inner.strip()}\n```\n\n" + tail

        elif tag == "br":
            return "\n" + tail

        elif tag == "hr":
            return "\n\n---\n\n" + tail

        elif tag == "a":
            href = el.attrib.get("href", "")
            inner = (text + children_md).strip()
            if href and inner:
                return f"[{inner}]({href})" + tail
            return f"{inner}" + tail

        elif tag == "img":
            return tail

        return f"{text}{children_md}{tail}"

    body = tree.find(".//body")
    if body is None:
        body = tree

    md = convert_element(body)

    # Decode smart punctuation and clean linebreaks
    md = md.replace("\r\n", "\n").replace("\r", "\n")
    md = md.replace("\u2013", "-").replace("\u2014", "--")
    md = md.replace("\u2018", "'").replace("\u2019", "'")
    md = md.replace("\u201c", '"').replace("\u201d", '"')
    md = md.replace("\ufffd", "-")

    # Clean whitespace lines
    lines = [line.rstrip() for line in md.split("\n")]
    cleaned_lines = []
    for line in lines:
        if line.strip() in ["&nbsp;", "\xa0"]:
            cleaned_lines.append("")
        else:
            cleaned_lines.append(line)
    md = "\n".join(cleaned_lines)

    # Collapse excessive blank lines
    md = re.sub(r"\n{3,}", "\n\n", md).strip()
    return md + "\n"


def main():
    print(f"Reading Canvas export from: {CANVAS_EXPORT_DIR}")
    print(f"Target CS 1400 directory: {TARGET_CS1400_DIR}")

    os.makedirs(TARGET_CS1400_DIR, exist_ok=True)

    manifest_path = os.path.join(CANVAS_EXPORT_DIR, "imsmanifest.xml")
    module_meta_path = os.path.join(
        CANVAS_EXPORT_DIR, "course_settings", "module_meta.xml"
    )

    mtree = ET.parse(manifest_path)
    mroot = mtree.getroot()
    res_map = {}
    for r in mroot.findall(
        ".//{http://www.imsglobal.org/xsd/imsccv1p1/imscp_v1p1}resource"
    ):
        res_map[r.attrib.get("identifier", "")] = r

    tree = ET.parse(module_meta_path)
    root = tree.getroot()
    ns = {"c": "http://canvas.instructure.com/xsd/cccv1p0"}

    modules = root.findall(".//c:module", ns)
    print(f"Found {len(modules)} modules in Canvas export.")

    summary = []

    for mod in modules:
        title = mod.find("c:title", ns).text
        m_match = re.search(r"Module\s*(\d+)", title)
        if not m_match:
            continue
        m_num = int(m_match.group(1))
        mod_dirname = f"m{m_num}"
        mod_dir = os.path.join(TARGET_CS1400_DIR, mod_dirname)
        os.makedirs(mod_dir, exist_ok=True)

        items = mod.findall(".//c:item", ns)

        # 1. Module Overview
        overview_found = False
        for it in items:
            ct = it.find("c:content_type", ns).text
            it_title = it.find("c:title", ns).text
            ident = (
                it.find("c:identifierref", ns).text
                if it.find("c:identifierref", ns) is not None
                else ""
            )

            if ct == "WikiPage" and "Overview" in it_title:
                res = res_map.get(ident)
                if res is not None:
                    href = res.attrib.get("href", "")
                    full_p = os.path.join(CANVAS_EXPORT_DIR, href)
                    if os.path.exists(full_p):
                        with open(full_p, "r", encoding="utf-8", errors="ignore") as f:
                            raw_html = f.read()
                        md = html_to_verbatim_markdown(raw_html)
                        # Add module header
                        md = f"# Module {m_num}: {title.split(':')[-1].strip()}\n\n" + md
                        with open(
                            os.path.join(mod_dir, "overview.md"), "w", encoding="utf-8"
                        ) as of:
                            of.write(md)
                        overview_found = True
                        break

        if not overview_found:
            # Fallback placeholder if no overview page
            with open(
                os.path.join(mod_dir, "overview.md"), "w", encoding="utf-8"
            ) as of:
                of.write(f"# Module {m_num}: {title}\n\nOverview content.\n")

        # 2. Assignments
        lab_idx = 1
        ps_idx = 1
        mod_assignments = []

        for it in items:
            ct = it.find("c:content_type", ns).text
            it_title = it.find("c:title", ns).text
            ident = (
                it.find("c:identifierref", ns).text
                if it.find("c:identifierref", ns) is not None
                else ""
            )

            if ct != "Assignment":
                continue

            # Check if this assignment actually belongs to this module
            mod_in_title = re.search(r"Module\s*(\d+):", it_title)
            if mod_in_title and int(mod_in_title.group(1)) != m_num:
                continue
            if "Extra Credit" in it_title:
                continue

            # Determine sequential folder name matching user preference
            proj_match = re.search(r"Project\s*(\d+)", it_title)
            final_match = "Final Exam (Project)" in it_title

            if "PS Lab" in it_title:
                folder_name = f"ps_lab{ps_idx}"
                ps_idx += 1
            elif proj_match:
                folder_name = f"project{proj_match.group(1)}"
            elif final_match:
                folder_name = "final_project"
            elif "Lab" in it_title:
                folder_name = f"lab{lab_idx}"
                lab_idx += 1
            else:
                folder_name = f"assign{lab_idx}"
                lab_idx += 1

            assign_dir = os.path.join(mod_dir, folder_name)
            os.makedirs(assign_dir, exist_ok=True)

            # Submissions empty folder
            submissions_dir = os.path.join(assign_dir, "submissions")
            os.makedirs(submissions_dir, exist_ok=True)

            # Convert assignment HTML to desc.md
            src_assign_dir = os.path.join(CANVAS_EXPORT_DIR, ident)
            html_files = (
                [f for f in os.listdir(src_assign_dir) if f.endswith(".html")]
                if os.path.exists(src_assign_dir)
                else []
            )

            if html_files:
                html_path = os.path.join(src_assign_dir, html_files[0])
                with open(html_path, "r", encoding="utf-8", errors="ignore") as hf:
                    raw_html = hf.read()
                md = html_to_verbatim_markdown(raw_html)
                with open(
                    os.path.join(assign_dir, "desc.md"), "w", encoding="utf-8"
                ) as df:
                    df.write(md)
            else:
                with open(
                    os.path.join(assign_dir, "desc.md"), "w", encoding="utf-8"
                ) as df:
                    df.write(f"# {it_title}\n\nDescription.\n")

            # Copy specific known starter/asset files if applicable
            # Module 14 Lab 2: Fix the Student Registration System
            if "Fix the Student Registration System" in it_title:
                buggy_src = os.path.join(
                    CANVAS_EXPORT_DIR,
                    "web_resources",
                    "Uploaded Media",
                    "student_registration_buggy.py",
                )
                if os.path.exists(buggy_src):
                    shutil.copy2(
                        buggy_src,
                        os.path.join(assign_dir, "student_registration_buggy.py"),
                    )

            # Module 15 Final Exam: BLS_private_p7.csv
            if final_match:
                csv_src = os.path.join(
                    CANVAS_EXPORT_DIR, "web_resources", "BLS_private_p7.csv"
                )
                if os.path.exists(csv_src):
                    shutil.copy2(csv_src, os.path.join(assign_dir, "BLS_private_p7.csv"))

            mod_assignments.append((folder_name, it_title))

        summary.append((m_num, title, mod_assignments))

    print("\n=== CONVERSION COMPLETE ===")
    for m_num, title, assigns in summary:
        print(f"\nm{m_num}: {title} (overview.md generated)")
        for f_name, a_title in assigns:
            print(f"  - {f_name}: {a_title}")


if __name__ == "__main__":
    main()
