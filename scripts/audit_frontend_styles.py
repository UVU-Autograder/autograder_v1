#!/usr/bin/env python3
"""Frontend Styling & Color Scheme Audit Script.
Scans all frontend files for:
1. Color usage (Tailwind color classes, arbitrary values, hex/rgb values)
2. UI component patterns (custom buttons, cards, badges vs standard components)
3. Spacing, radius, typography inconsistencies
4. Hardcoded styles and style token divergence
"""

import os
import re
from collections import Counter, defaultdict
from pathlib import Path

FRONTEND_DIR = Path("/home/jaxon/coding/autograder_v1/frontend")

# Regex patterns
HEX_COLOR_PATTERN = re.compile(r"#(?:[0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})\b")
RGB_HSL_PATTERN = re.compile(r"(?:rgb|hsl)a?\([^\)]+\)")
ARBITRARY_TAILWIND_COLOR = re.compile(r"(?:bg|text|border|ring|stroke|fill)-\[([^\]]+)\]")

# Tailwind color class regex
# Matches things like bg-slate-100, text-primary/80, border-emerald-500, bg-zinc-900, bg-indigo-600, etc.
TW_COLOR_CLASS = re.compile(
    r"\b((?:bg|text|border|ring|from|to|via|outline|divide|accent|fill|stroke)-"
    r"(?:slate|gray|zinc|neutral|stone|red|orange|amber|yellow|lime|green|emerald|teal|cyan|sky|blue|indigo|violet|purple|fuchsia|pink|rose|primary|secondary|muted|accent|destructive|card|popover|background|foreground|sidebar)"
    r"(?:-[0-9]{2,3})?(?:/[0-9]{1,3})?)\b"
)

BUTTON_ELEMENT_PATTERN = re.compile(r'<button\b[^>]*className=["\']([^"\']+)["\']', re.IGNORECASE)
SHADCN_BUTTON_PATTERN = re.compile(r'<Button\b[^>]*variant=["\']([^"\']+)["\']', re.IGNORECASE)
INPUT_ELEMENT_PATTERN = re.compile(r'<input\b[^>]*className=["\']([^"\']+)["\']', re.IGNORECASE)


def scan_frontend():
    files_scanned = 0
    all_hex_colors = defaultdict(list)
    all_rgb_hsl = defaultdict(list)
    all_tw_colors = Counter()
    all_tw_color_by_file = defaultdict(Counter)
    all_arbitrary_colors = defaultdict(list)
    raw_buttons = []
    shadcn_buttons = Counter()
    custom_cards = []

    # Track which color families are being used
    color_families = Counter()

    for root, dirs, files in os.walk(FRONTEND_DIR):
        # Skip node_modules, .next, .git
        if any(ignored in root for ignored in ["node_modules", ".next", ".git", "coverage"]):
            continue

        for file in files:
            if not file.endswith((".tsx", ".ts", ".jsx", ".js", ".css")):
                continue

            file_path = Path(root) / file
            rel_path = file_path.relative_to(FRONTEND_DIR)
            files_scanned += 1

            try:
                content = file_path.read_text(encoding="utf-8")
            except Exception:
                continue

            # 1. Hex colors
            for match in HEX_COLOR_PATTERN.finditer(content):
                hex_val = match.group(0).lower()
                all_hex_colors[hex_val].append(str(rel_path))

            # 2. RGB/HSL
            for match in RGB_HSL_PATTERN.finditer(content):
                val = match.group(0)
                all_rgb_hsl[val].append(str(rel_path))

            # 3. Arbitrary tailwind values e.g. bg-[#123456] or bg-primary/[0.04]
            for match in ARBITRARY_TAILWIND_COLOR.finditer(content):
                val = match.group(0)
                all_arbitrary_colors[val].append(str(rel_path))

            # 4. Tailwind color classes
            for match in TW_COLOR_CLASS.finditer(content):
                cls = match.group(1)
                all_tw_colors[cls] += 1
                all_tw_color_by_file[str(rel_path)][cls] += 1

                # Extract family (e.g. slate, zinc, emerald, primary)
                parts = cls.split("-")
                if len(parts) >= 2:
                    family = parts[1]
                    color_families[family] += 1

            # 5. Raw button tags with custom classes vs Shadcn Button
            for match in BUTTON_ELEMENT_PATTERN.finditer(content):
                raw_buttons.append((str(rel_path), match.group(1)))

            for match in SHADCN_BUTTON_PATTERN.finditer(content):
                shadcn_buttons[match.group(1)] += 1

            # 6. Ad-hoc card-like elements (e.g. rounded-lg border p-4 ...)
            if "rounded-" in content and "border" in content and "bg-" in content:
                # find custom card structures
                for card_match in re.finditer(
                    r'className=["\']([^"\']*(?:rounded-lg|rounded-xl|rounded-md)[^"\']*(?:border)[^"\']*(?:bg-)[^"\']*)["\']',
                    content,
                ):
                    custom_cards.append((str(rel_path), card_match.group(1)))

    return {
        "files_scanned": files_scanned,
        "color_families": color_families,
        "tw_colors": all_tw_colors,
        "hex_colors": all_hex_colors,
        "rgb_hsl": all_rgb_hsl,
        "arbitrary_colors": all_arbitrary_colors,
        "tw_color_by_file": all_tw_color_by_file,
        "raw_buttons": raw_buttons,
        "shadcn_buttons": shadcn_buttons,
        "custom_cards_count": len(custom_cards),
        "sample_custom_cards": custom_cards[:20],
    }


if __name__ == "__main__":
    results = scan_frontend()
    print(f"=== SCANNED {results['files_scanned']} FILES ===")
    print("\n--- COLOR FAMILIES USED ---")
    for fam, count in results["color_families"].most_common():
        print(f"  {fam:15}: {count:4} occurrences")

    print("\n--- TOP 25 TAILWIND COLOR CLASSES ---")
    for cls, count in results["tw_colors"].most_common(25):
        print(f"  {cls:30}: {count:4} times")

    print("\n--- HARDCODED HEX / RGB COLORS ---")
    for h, files in results["hex_colors"].items():
        print(f"  {h:10}: in {len(files)} files -> {files[:3]}")

    print("\n--- ARBITRARY TAILWIND COLORS ---")
    for arb, files in list(results["arbitrary_colors"].items())[:15]:
        print(f"  {arb:35}: in {files[:2]}")

    print("\n--- BUTTON USAGE ---")
    print(f"  Raw <button> tags with custom CSS: {len(results['raw_buttons'])}")
    print(f"  Shadcn <Button variant='...'>: {sum(results['shadcn_buttons'].values())}")
    for var, count in results["shadcn_buttons"].items():
        print(f"    variant '{var}': {count}")

    print("\n--- AD-HOC CARD CONTAINERS ---")
    print(f"  Total custom ad-hoc card divs: {results['custom_cards_count']}")
