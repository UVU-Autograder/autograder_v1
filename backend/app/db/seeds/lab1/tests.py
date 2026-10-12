"""Lab 1 image-processing checks aligned with cs1410/m1/lab1/desc.md.

Part 1 requires filtering bears_copy.jpg into bears2.jpg via bears2.py, so we
re-run the script with the injected support file.

Part 2 lets students use any red-balloon image they find online and only
requires submitting bears3.py + bears3.jpg — so we validate the submitted
composite, not a re-run that would need their private balloon asset.
"""

import os
import runpy
from pathlib import Path

import pytest
from PIL import Image

ROOT = Path.cwd()


def assert_file_exists(path: str) -> Path:
    file_path = ROOT / path
    assert file_path.exists(), f"Missing required file: {path}"
    assert file_path.is_file(), f"Required path is not a file: {path}"
    return file_path


def assert_valid_nontrivial_image(path: str) -> None:
    file_path = assert_file_exists(path)
    with Image.open(file_path) as image:
        image.verify()

    with Image.open(file_path) as image:
        width, height = image.size
        assert width > 0 and height > 0
        pixels = list(image.convert("RGB").resize((32, 32)).getdata())
        assert len(set(pixels)) > 1, f"{path} appears to be blank or single-color"


@pytest.mark.ag_part1_files
def test_part1_required_files_present():
    assert_file_exists("bears2.py")
    assert_file_exists("bears2.jpg")


@pytest.mark.ag_part1_output
def test_part1_script_produces_valid_filter_image():
    """desc.md: filter bears_copy.jpg and save bears2.jpg via bears2.py."""
    assert_file_exists("bears_copy.jpg")
    assert_file_exists("bears2.py")
    if os.path.exists("bears2.jpg"):
        try:
            os.remove("bears2.jpg")
        except OSError:
            pass
    runpy.run_path("bears2.py", run_name="__main__")
    assert_valid_nontrivial_image("bears2.jpg")


@pytest.mark.ag_part2_files
def test_part2_required_files_present():
    assert_file_exists("bears3.py")
    assert_file_exists("bears3.jpg")


@pytest.mark.ag_part2_output
def test_part2_submitted_composite_is_valid():
    """desc.md: students submit bears3.jpg; balloon source is not required."""
    assert_valid_nontrivial_image("bears3.jpg")
