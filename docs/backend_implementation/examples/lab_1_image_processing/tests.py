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
def test_part1_output_image_is_valid_and_nontrivial():
    assert_valid_nontrivial_image("bears2.jpg")


@pytest.mark.ag_part2_files
def test_part2_required_files_present():
    assert_file_exists("bears3.py")
    assert_file_exists("bears3.jpg")


@pytest.mark.ag_part2_output
def test_part2_output_image_is_valid_and_nontrivial():
    assert_valid_nontrivial_image("bears3.jpg")
