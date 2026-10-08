"""Instructor grading calibration engine and synthetic manifest verification.

Provides calibration test case manifests, discrepancy detection, and automated
scoring verification across reference implementations, valid alternatives,
common student misconceptions, and boundary edge cases.
"""
from __future__ import annotations

import asyncio
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from app.db.seed import SEEDS_DIR
from app.domains.assignments.schemas import AssignmentConfigV1
from app.domains.grading.executor import ExecutionOutcome
from app.domains.grading.pipeline import (
    GradingPipeline,
    PreloadedArtifacts,
    SubmissionPayload,
)
from app.domains.grading.result_parser import parse_pytest_json
from app.domains.grading.runner_gen import generate_runner_script


@dataclass(frozen=True)
class CalibrationCase:
    """A synthetic student submission scenario with expected grading rubric outcomes."""

    assignment_slug: str
    case_id: str
    name: str
    category: str  # "reference", "valid_alternative", "misconception", "boundary", "blocked_concept"
    description: str
    files: dict[str, bytes]
    expected_score: int
    expected_max_score: int
    expected_outcomes: dict[str, bool] = field(default_factory=dict)
    expected_success: bool = True
    expected_failure_category: str | None = None
    allowed_concepts: list[str] = field(default_factory=lambda: ["all"])


@dataclass
class CalibrationDiscrepancy:
    """A deviation between actual grading outcome and the expected calibration standard."""

    case_id: str
    assignment_slug: str
    category: str
    detail: str


@dataclass
class CalibrationOutcome:
    """The evaluated outcome of a single calibration test case."""

    case: CalibrationCase
    passed: bool
    actual_score: int
    actual_max_score: int
    actual_outcomes: dict[str, bool]
    actual_success: bool
    actual_failure_category: str | None
    discrepancies: list[CalibrationDiscrepancy] = field(default_factory=list)


async def execute_local_calibration_runner(
    exec_dir: Path,
    *,
    test_filenames: list[str],
    test_cases: dict[str, dict[str, list[str]]],
    entrypoint_module: str,
    language_id: int,
    cpu_time_limit: float,
    dependencies: list[str] | None = None,
    memory_limit: int = 128 * 1024,
    stdin: str | None = None,
    wall_time_limit: float = 10.0,
    runner_source: str | None = None,
) -> ExecutionOutcome:
    """Local subprocess runner stand-in for Judge0 during offline calibration tests."""
    outcome = ExecutionOutcome()
    script = runner_source or generate_runner_script(
        test_filenames,
        test_cases,
        entrypoint_module,
        dependencies,
    )
    runner_file = exec_dir / "runner.py"
    runner_file.write_text(script, encoding="utf-8")

    env = os.environ.copy()
    env["PYTHONPATH"] = str(exec_dir)
    env["SDL_VIDEODRIVER"] = "dummy"
    env["SDL_AUDIODRIVER"] = "dummy"

    proc = await asyncio.create_subprocess_exec(
        sys.executable,
        str(runner_file),
        cwd=str(exec_dir),
        stdin=asyncio.subprocess.PIPE if stdin else None,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=env,
    )

    stdin_bytes = stdin.encode("utf-8") if stdin else None
    stdout_bytes, stderr_bytes = await proc.communicate(input=stdin_bytes)
    stdout_text = stdout_bytes.decode("utf-8", errors="replace")

    pytest_result = parse_pytest_json(stdout_text)
    outcome.pytest_result = pytest_result
    if pytest_result.error_message:
        outcome.failure_category = "test_failure"
        outcome.failure_message = pytest_result.error_message
        outcome.success = False
    else:
        outcome.success = True

    return outcome


async def evaluate_calibration_case(
    pipeline: GradingPipeline,
    case: CalibrationCase,
) -> CalibrationOutcome:
    """Grade a calibration case through the grading pipeline and check for discrepancies."""
    payload = SubmissionPayload.from_files(case.files)
    report = await pipeline.evaluate(payload)

    actual_outcomes: dict[str, bool] = {
        item["key"]: item.get("passed", False)
        for item in report.test_results
    }
    discrepancies: list[CalibrationDiscrepancy] = []

    if report.success != case.expected_success:
        discrepancies.append(
            CalibrationDiscrepancy(
                case_id=case.case_id,
                assignment_slug=case.assignment_slug,
                category="success_status",
                detail=(
                    f"Expected success={case.expected_success}, "
                    f"got {report.success} (failure_category={report.failure_category})"
                ),
            )
        )

    if report.failure_category != case.expected_failure_category:
        discrepancies.append(
            CalibrationDiscrepancy(
                case_id=case.case_id,
                assignment_slug=case.assignment_slug,
                category="failure_category",
                detail=(
                    f"Expected failure_category={case.expected_failure_category}, "
                    f"got {report.failure_category}"
                ),
            )
        )

    if report.score != case.expected_score:
        discrepancies.append(
            CalibrationDiscrepancy(
                case_id=case.case_id,
                assignment_slug=case.assignment_slug,
                category="score_mismatch",
                detail=(
                    f"Expected score={case.expected_score}, got {report.score} "
                    f"(out of max={report.max_score})"
                ),
            )
        )

    for marker_key, expected_pass in case.expected_outcomes.items():
        actual_pass = actual_outcomes.get(marker_key)
        if actual_pass is None:
            discrepancies.append(
                CalibrationDiscrepancy(
                    case_id=case.case_id,
                    assignment_slug=case.assignment_slug,
                    category="missing_scoring_item",
                    detail=f"Expected scoring item '{marker_key}' was not evaluated in report",
                )
            )
        elif actual_pass != expected_pass:
            discrepancies.append(
                CalibrationDiscrepancy(
                    case_id=case.case_id,
                    assignment_slug=case.assignment_slug,
                    category="outcome_mismatch",
                    detail=(
                        f"Scoring item '{marker_key}': expected passed={expected_pass}, "
                        f"got {actual_pass}"
                    ),
                )
            )

    return CalibrationOutcome(
        case=case,
        passed=len(discrepancies) == 0,
        actual_score=report.score,
        actual_max_score=report.max_score,
        actual_outcomes=actual_outcomes,
        actual_success=report.success,
        actual_failure_category=report.failure_category,
        discrepancies=discrepancies,
    )


async def verify_assignment_calibration(
    config: AssignmentConfigV1,
    preloaded_artifacts: PreloadedArtifacts,
    cases: list[CalibrationCase],
    executor_fn: Callable[..., Any] | None = None,
) -> list[CalibrationDiscrepancy]:
    """Execute all calibration cases for an assignment; return all detected discrepancies."""
    executor = executor_fn or execute_local_calibration_runner
    discrepancies: list[CalibrationDiscrepancy] = []

    for case in cases:
        pipeline = GradingPipeline(
            config=config,
            artifact_refs={},
            allowed_concepts=case.allowed_concepts,
            preloaded_artifacts=preloaded_artifacts,
            executor_fn=executor,
        )
        outcome = await evaluate_calibration_case(pipeline, case)
        discrepancies.extend(outcome.discrepancies)

    return discrepancies


# ---------------------------------------------------------------------------
# Pilot CS 1410 Calibration Manifests (ds1, lab1, lab6)
# ---------------------------------------------------------------------------


def get_ds1_calibration_manifest() -> list[CalibrationCase]:
    """Calibration cases for CS 1410 ds1 (OOP Dessert Shop)."""
    ds1_dir = SEEDS_DIR / "ds1"
    ref_dessert_code = (ds1_dir / "dessert.py").read_bytes()

    # 1. Valid alternative: Property getters and setters
    valid_property_alt = b'''\
class DessertItem:
    def __init__(self, name: str = "") -> None:
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, val: str) -> None:
        self._name = val


class Candy(DessertItem):
    def __init__(self, name: str = "", candy_weight: float = 0.0, price_per_pound: float = 0.0) -> None:
        super().__init__(name)
        self._w = candy_weight
        self._p = price_per_pound

    @property
    def candy_weight(self) -> float:
        return self._w

    @candy_weight.setter
    def candy_weight(self, val: float) -> None:
        self._w = val

    @property
    def price_per_pound(self) -> float:
        return self._p

    @price_per_pound.setter
    def price_per_pound(self, val: float) -> None:
        self._p = val


class Cookie(DessertItem):
    def __init__(self, name: str = "", cookie_quantity: int = 0, price_per_dozen: float = 0.0) -> None:
        super().__init__(name)
        self._q = cookie_quantity
        self._p = price_per_dozen

    @property
    def cookie_quantity(self) -> int:
        return self._q

    @cookie_quantity.setter
    def cookie_quantity(self, val: int) -> None:
        self._q = val

    @property
    def price_per_dozen(self) -> float:
        return self._p

    @price_per_dozen.setter
    def price_per_dozen(self, val: float) -> None:
        self._p = val


class IceCream(DessertItem):
    def __init__(self, name: str = "", scoop_count: int = 0, price_per_scoop: float = 0.0) -> None:
        super().__init__(name)
        self._s = scoop_count
        self._p = price_per_scoop

    @property
    def scoop_count(self) -> int:
        return self._s

    @scoop_count.setter
    def scoop_count(self, val: int) -> None:
        self._s = val

    @property
    def price_per_scoop(self) -> float:
        return self._p

    @price_per_scoop.setter
    def price_per_scoop(self, val: float) -> None:
        self._p = val


class Sundae(IceCream):
    def __init__(self, name: str = "", scoop_count: int = 0, price_per_scoop: float = 0.0, topping_name: str = "", topping_price: float = 0.0) -> None:
        super().__init__(name, scoop_count, price_per_scoop)
        self._tn = topping_name
        self._tp = topping_price

    @property
    def topping_name(self) -> str:
        return self._tn

    @topping_name.setter
    def topping_name(self, val: str) -> None:
        self._tn = val

    @property
    def topping_price(self) -> float:
        return self._tp

    @topping_price.setter
    def topping_price(self, val: float) -> None:
        self._tp = val
'''

    # 2. Misconception: Sundae inherits directly from DessertItem instead of IceCream
    broken_inheritance = b'''\
class DessertItem:
    def __init__(self, name: str = ""):
        self.name = name

class Candy(DessertItem):
    def __init__(self, name: str = "", candy_weight: float = 0.0, price_per_pound: float = 0.0):
        super().__init__(name)
        self.candy_weight = candy_weight
        self.price_per_pound = price_per_pound

class Cookie(DessertItem):
    def __init__(self, name: str = "", cookie_quantity: int = 0, price_per_dozen: float = 0.0):
        super().__init__(name)
        self.cookie_quantity = cookie_quantity
        self.price_per_dozen = price_per_dozen

class IceCream(DessertItem):
    def __init__(self, name: str = "", scoop_count: int = 0, price_per_scoop: float = 0.0):
        super().__init__(name)
        self.scoop_count = scoop_count
        self.price_per_scoop = price_per_scoop

class Sundae(DessertItem):  # WRONG: Inherits DessertItem directly
    def __init__(self, name: str = "", scoop_count: int = 0, price_per_scoop: float = 0.0, topping_name: str = "", topping_price: float = 0.0):
        super().__init__(name)
        self.scoop_count = scoop_count
        self.price_per_scoop = price_per_scoop
        self.topping_name = topping_name
        self.topping_price = topping_price
'''

    # 3. Misconception: Missing attribute default or wrong attribute name in Candy
    wrong_candy_attr = b'''\
class DessertItem:
    def __init__(self, name: str = ""):
        self.name = name

class Candy(DessertItem):
    def __init__(self, name: str = "", candy_weight: float = 0.0, price_per_pound: float = 0.0):
        super().__init__(name)
        self.weight = candy_weight  # WRONG attribute name
        self.price = price_per_pound

class Cookie(DessertItem):
    def __init__(self, name: str = "", cookie_quantity: int = 0, price_per_dozen: float = 0.0):
        super().__init__(name)
        self.cookie_quantity = cookie_quantity
        self.price_per_dozen = price_per_dozen

class IceCream(DessertItem):
    def __init__(self, name: str = "", scoop_count: int = 0, price_per_scoop: float = 0.0):
        super().__init__(name)
        self.scoop_count = scoop_count
        self.price_per_scoop = price_per_scoop

class Sundae(IceCream):
    def __init__(self, name: str = "", scoop_count: int = 0, price_per_scoop: float = 0.0, topping_name: str = "", topping_price: float = 0.0):
        super().__init__(name, scoop_count, price_per_scoop)
        self.topping_name = topping_name
        self.topping_price = topping_price
'''

    # 4. Misconception: Cookie has default quantity 1 instead of 0
    wrong_cookie_default = b'''\
class DessertItem:
    def __init__(self, name: str = ""):
        self.name = name

class Candy(DessertItem):
    def __init__(self, name: str = "", candy_weight: float = 0.0, price_per_pound: float = 0.0):
        super().__init__(name)
        self.candy_weight = candy_weight
        self.price_per_pound = price_per_pound

class Cookie(DessertItem):
    def __init__(self, name: str = "", cookie_quantity: int = 1, price_per_dozen: float = 0.0):  # WRONG default 1
        super().__init__(name)
        self.cookie_quantity = cookie_quantity
        self.price_per_dozen = price_per_dozen

class IceCream(DessertItem):
    def __init__(self, name: str = "", scoop_count: int = 0, price_per_scoop: float = 0.0):
        super().__init__(name)
        self.scoop_count = scoop_count
        self.price_per_scoop = price_per_scoop

class Sundae(IceCream):
    def __init__(self, name: str = "", scoop_count: int = 0, price_per_scoop: float = 0.0, topping_name: str = "", topping_price: float = 0.0):
        super().__init__(name, scoop_count, price_per_scoop)
        self.topping_name = topping_name
        self.topping_price = topping_price
'''

    # 5. Blocked concept: subprocess usage
    blocked_subprocess = b'''\
import subprocess

class DessertItem:
    def __init__(self, name: str = ""):
        self.name = name
'''

    return [
        CalibrationCase(
            assignment_slug="ds1",
            case_id="ds1_reference",
            name="Reference Model Solution",
            category="reference",
            description="Official instructor model solution passes all 5 tests for 100 points.",
            files={"dessert.py": ref_dessert_code},
            expected_score=100,
            expected_max_score=100,
            expected_outcomes={
                "dessert_item": True,
                "candy": True,
                "cookie": True,
                "icecream": True,
                "sundae": True,
            },
            expected_success=True,
        ),
        CalibrationCase(
            assignment_slug="ds1",
            case_id="ds1_valid_alternative_properties",
            name="Valid Alternative: Property Getters & Setters",
            category="valid_alternative",
            description="Student encapsulates all fields behind python properties; full credit awarded.",
            files={"dessert.py": valid_property_alt},
            expected_score=100,
            expected_max_score=100,
            expected_outcomes={
                "dessert_item": True,
                "candy": True,
                "cookie": True,
                "icecream": True,
                "sundae": True,
            },
            expected_success=True,
        ),
        CalibrationCase(
            assignment_slug="ds1",
            case_id="ds1_misconception_broken_inheritance",
            name="Misconception: Sundae directly inherits DessertItem",
            category="misconception",
            description="Sundae inherits DessertItem directly instead of IceCream; 20 points deducted.",
            files={"dessert.py": broken_inheritance},
            expected_score=80,
            expected_max_score=100,
            expected_outcomes={
                "dessert_item": True,
                "candy": True,
                "cookie": True,
                "icecream": True,
                "sundae": False,
            },
            expected_success=True,
        ),
        CalibrationCase(
            assignment_slug="ds1",
            case_id="ds1_misconception_missing_candy_attribute",
            name="Misconception: Candy uses 'weight' instead of 'candy_weight'",
            category="misconception",
            description="Candy constructor binds wrong attribute name; 20 points deducted.",
            files={"dessert.py": wrong_candy_attr},
            expected_score=80,
            expected_max_score=100,
            expected_outcomes={
                "dessert_item": True,
                "candy": False,
                "cookie": True,
                "icecream": True,
                "sundae": True,
            },
            expected_success=True,
        ),
        CalibrationCase(
            assignment_slug="ds1",
            case_id="ds1_misconception_cookie_wrong_default",
            name="Misconception: Cookie defaults to quantity 1",
            category="misconception",
            description="Cookie defaults quantity to 1 instead of 0; 20 points deducted.",
            files={"dessert.py": wrong_cookie_default},
            expected_score=80,
            expected_max_score=100,
            expected_outcomes={
                "dessert_item": True,
                "candy": True,
                "cookie": False,
                "icecream": True,
                "sundae": True,
            },
            expected_success=True,
        ),
        CalibrationCase(
            assignment_slug="ds1",
            case_id="ds1_blocked_concept_subprocess",
            name="Security/AST: Blocked concept import subprocess",
            category="blocked_concept",
            description="Imports subprocess when only classes/functions are allowed; execution blocked.",
            files={"dessert.py": blocked_subprocess},
            expected_score=0,
            expected_max_score=100,
            expected_outcomes={},
            expected_success=False,
            expected_failure_category="concept_blocked",
            allowed_concepts=["classes", "functions"],
        ),
    ]


def get_lab1_calibration_manifest() -> list[CalibrationCase]:
    """Calibration cases for CS 1410 lab1 (Pillow Image Processing & File I/O)."""
    lab1_dir = SEEDS_DIR / "lab1"
    ref_bears2 = (lab1_dir / "bears2.py").read_bytes()
    ref_bears3 = (lab1_dir / "bears3.py").read_bytes()
    ref_bears2_jpg = (lab1_dir / "bears2.jpg").read_bytes()
    ref_bears3_jpg = (lab1_dir / "bears3.jpg").read_bytes()

    # 1. Valid alternative: average grayscale (r + g + b) // 3
    alt_bears2 = b'''\
from PIL import Image

filename = 'bears_copy.jpg'
orig_image = Image.open(filename)
width, height = orig_image.size
new_image = Image.new("RGB", (width, height))
orig_map = orig_image.load()
new_map = new_image.load()

for x in range(width):
    for y in range(height):
        r, g, b = orig_map[x, y][:3]
        avg = (r + g + b) // 3
        new_map[x, y] = (avg, avg, avg)

new_image.save("bears2.jpg")
'''

    # 2. Blank single-color output
    blank_bears2 = b'''\
from PIL import Image
img = Image.new("RGB", (100, 100), (0, 0, 0))
img.save("bears2.jpg")
'''

    # 3. Crashing script in part 1
    crashing_bears2 = b'''\
raise RuntimeError("Student script error")
'''

    return [
        CalibrationCase(
            assignment_slug="lab1",
            case_id="lab1_reference",
            name="Reference Model Solution",
            category="reference",
            description="Full automated credit (60 points) for correct script and output files.",
            files={
                "bears2.py": ref_bears2,
                "bears3.py": ref_bears3,
                "bears2.jpg": ref_bears2_jpg,
                "bears3.jpg": ref_bears3_jpg,
            },
            expected_score=60,
            expected_max_score=100,
            expected_outcomes={
                "part1_files": True,
                "part1_output": True,
                "part2_files": True,
                "part2_output": True,
            },
            expected_success=True,
        ),
        CalibrationCase(
            assignment_slug="lab1",
            case_id="lab1_valid_alternative_average_grayscale",
            name="Valid Alternative: RGB Average Grayscale",
            category="valid_alternative",
            description="Student uses RGB average instead of luminance weighting; full credit awarded.",
            files={
                "bears2.py": alt_bears2,
                "bears3.py": ref_bears3,
                "bears2.jpg": ref_bears2_jpg,
                "bears3.jpg": ref_bears3_jpg,
            },
            expected_score=60,
            expected_max_score=100,
            expected_outcomes={
                "part1_files": True,
                "part1_output": True,
                "part2_files": True,
                "part2_output": True,
            },
            expected_success=True,
        ),
        CalibrationCase(
            assignment_slug="lab1",
            case_id="lab1_misconception_missing_required_file",
            name="Bundle Error: Missing bears3.jpg",
            category="misconception",
            description="Student forgets to submit bears3.jpg; intake bundle rejects execution.",
            files={
                "bears2.py": ref_bears2,
                "bears3.py": ref_bears3,
                "bears2.jpg": ref_bears2_jpg,
            },
            expected_score=0,
            expected_max_score=100,
            expected_outcomes={},
            expected_success=False,
            expected_failure_category="missing_required_file",
        ),
        CalibrationCase(
            assignment_slug="lab1",
            case_id="lab1_misconception_blank_image",
            name="Misconception: Single-color blank bears2.jpg output",
            category="misconception",
            description="bears2.py produces trivial all-black image; part1_output fails (15 pts deducted).",
            files={
                "bears2.py": blank_bears2,
                "bears3.py": ref_bears3,
                "bears2.jpg": ref_bears2_jpg,
                "bears3.jpg": ref_bears3_jpg,
            },
            expected_score=45,
            expected_max_score=100,
            expected_outcomes={
                "part1_files": True,
                "part1_output": False,
                "part2_files": True,
                "part2_output": True,
            },
            expected_success=True,
        ),
        CalibrationCase(
            assignment_slug="lab1",
            case_id="lab1_misconception_crashing_script",
            name="Runtime Error: Script raises exception",
            category="misconception",
            description="bears2.py crashes on execution; part1_output fails (15 pts deducted).",
            files={
                "bears2.py": crashing_bears2,
                "bears3.py": ref_bears3,
                "bears2.jpg": ref_bears2_jpg,
                "bears3.jpg": ref_bears3_jpg,
            },
            expected_score=45,
            expected_max_score=100,
            expected_outcomes={
                "part1_files": True,
                "part1_output": False,
                "part2_files": True,
                "part2_output": True,
            },
            expected_success=True,
        ),
    ]


def get_lab6_calibration_manifest() -> list[CalibrationCase]:
    """Calibration cases for CS 1410 lab6 (Pygame Headless & AST Checks)."""
    lab6_dir = SEEDS_DIR / "lab6"
    ref_part1 = (lab6_dir / "lab6_part1.py").read_bytes()
    ref_part2 = (lab6_dir / "lab6_part2.py").read_bytes()

    # 1. Valid alternative: Blit with (rect.x, rect.y) tuple in Part 2
    alt_part2 = b'''\
import sys
import pygame

pygame.init()
width = 600
height = 600
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Animal Animation - Part 2")

try:
    animal = pygame.image.load("animal.png")
except (FileNotFoundError, OSError, pygame.error):
    animal = pygame.Surface((100, 100))
    animal.fill((255, 0, 0))

animal = pygame.transform.scale(animal, (100, 100))
clock = pygame.time.Clock()

def main() -> None:
    rect = pygame.Rect(0, height - animal.get_height(), 100, 100)
    speed = 5
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        rect.x += speed
        if rect.right >= width or rect.left <= 0:
            speed = -speed

        screen.fill((255, 255, 255))
        screen.blit(animal, (rect.x, rect.y))  # Blit tuple coords instead of rect directly
        pygame.display.update()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
'''

    # 2. Misconception: Part 1 uses pygame.Rect prematurely
    part1_with_rect = b'''\
import sys
import pygame

pygame.init()
width = 600
height = 600
screen = pygame.display.set_mode((width, height))
animal = pygame.Surface((100, 100))

def main() -> None:
    rect = pygame.Rect(0, height - 100, 100, 100)  # WRONG in Part 1!
    screen.blit(animal, (rect.x, rect.y))

if __name__ == "__main__":
    main()
'''

    # 3. Misconception: Part 2 omits pygame.Rect
    part2_no_rect = b'''\
import sys
import pygame

pygame.init()
width = 600
height = 600
screen = pygame.display.set_mode((width, height))
animal = pygame.Surface((100, 100))

def main() -> None:
    x = 0
    y = height - 100
    screen.blit(animal, (x, y))  # WRONG in Part 2: no Rect used!

if __name__ == "__main__":
    main()
'''

    # 4. Pitfall: Negative initial coordinates in Part 1
    part1_negative_coords = b'''\
import sys
import pygame

pygame.init()
width = 600
height = 600
screen = pygame.display.set_mode((width, height))
animal = pygame.Surface((100, 100))

def main() -> None:
    x = -20  # WRONG: negative initial position
    y = height - 100
    screen.blit(animal, (x, y))

if __name__ == "__main__":
    main()
'''

    return [
        CalibrationCase(
            assignment_slug="lab6",
            case_id="lab6_reference",
            name="Reference Model Solution",
            category="reference",
            description="Full automated credit (60 points) for correct scalar & Rect AST patterns.",
            files={
                "lab6_part1.py": ref_part1,
                "lab6_part2.py": ref_part2,
            },
            expected_score=60,
            expected_max_score=100,
            expected_outcomes={
                "part1_ast_execution": True,
                "part2_ast_execution": True,
            },
            expected_success=True,
        ),
        CalibrationCase(
            assignment_slug="lab6",
            case_id="lab6_valid_alternative_tuple_blit",
            name="Valid Alternative: Part 2 Blits (rect.x, rect.y) Tuple",
            category="valid_alternative",
            description="Part 2 extracts rect.x/y into tuple for blit; both AST & execution pass.",
            files={
                "lab6_part1.py": ref_part1,
                "lab6_part2.py": alt_part2,
            },
            expected_score=60,
            expected_max_score=100,
            expected_outcomes={
                "part1_ast_execution": True,
                "part2_ast_execution": True,
            },
            expected_success=True,
        ),
        CalibrationCase(
            assignment_slug="lab6",
            case_id="lab6_misconception_part1_uses_rect",
            name="Misconception: Part 1 uses pygame.Rect prematurely",
            category="misconception",
            description="AST validator detects pygame.Rect in Part 1; 30 points deducted.",
            files={
                "lab6_part1.py": part1_with_rect,
                "lab6_part2.py": ref_part2,
            },
            expected_score=30,
            expected_max_score=100,
            expected_outcomes={
                "part1_ast_execution": False,
                "part2_ast_execution": True,
            },
            expected_success=True,
        ),
        CalibrationCase(
            assignment_slug="lab6",
            case_id="lab6_misconception_part2_no_rect",
            name="Misconception: Part 2 omits pygame.Rect",
            category="misconception",
            description="AST validator detects missing pygame.Rect in Part 2; 30 points deducted.",
            files={
                "lab6_part1.py": ref_part1,
                "lab6_part2.py": part2_no_rect,
            },
            expected_score=30,
            expected_max_score=100,
            expected_outcomes={
                "part1_ast_execution": True,
                "part2_ast_execution": False,
            },
            expected_success=True,
        ),
        CalibrationCase(
            assignment_slug="lab6",
            case_id="lab6_pitfall_negative_coordinates",
            name="Pitfall: Negative initial coordinate in Part 1",
            category="boundary",
            description="Sprite starts at negative x; assertion fails for 30 points deducted.",
            files={
                "lab6_part1.py": part1_negative_coords,
                "lab6_part2.py": ref_part2,
            },
            expected_score=30,
            expected_max_score=100,
            expected_outcomes={
                "part1_ast_execution": False,
                "part2_ast_execution": True,
            },
            expected_success=True,
        ),
    ]


def get_pilot_calibration_manifests() -> dict[str, list[CalibrationCase]]:
    """Return all pilot CS 1410 calibration manifests indexed by assignment slug."""
    return {
        "ds1": get_ds1_calibration_manifest(),
        "lab1": get_lab1_calibration_manifest(),
        "lab6": get_lab6_calibration_manifest(),
    }
