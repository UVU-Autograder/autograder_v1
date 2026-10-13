"""Tests for instructor grading calibration and focused regression cases (Issue #24).

Validates test suites against reference implementations, valid alternatives,
common student misconceptions, and boundary edge cases for pilot CS 1410 assignments
(ds1 OOP, lab1 I/O & Pillow, and lab6 Pygame).
"""
from __future__ import annotations

import json

import pytest

from app.db.seed import SEEDS_DIR
from app.domains.assignments.engine import AssignmentSpecificationEngine
from app.domains.assignments.schemas import AssignmentConfigV1
from app.domains.grading.calibration import (
    CalibrationCase,
    evaluate_calibration_case,
    execute_local_calibration_runner,
    get_pilot_calibration_manifests,
)
from app.domains.grading.pipeline import GradingPipeline, PreloadedArtifacts

MANIFESTS = get_pilot_calibration_manifests()


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


def _get_preloaded_artifacts_for_slug(slug: str) -> tuple[AssignmentConfigV1, PreloadedArtifacts]:
    """Helper to construct config and PreloadedArtifacts from seed directory."""
    seed_dir = SEEDS_DIR / slug
    config_data = json.loads((seed_dir / "config.json").read_text(encoding="utf-8"))
    config = AssignmentConfigV1.model_validate(config_data)

    files: dict[str, bytes] = {}
    pytest_filenames: list[str] = []

    for art_key, art_meta in config.artifacts.items():
        if art_meta.type == "model_solution":
            continue
        filename = art_meta.display_filename or art_key
        # Check seed dir then shared dir
        art_path = seed_dir / filename
        if not art_path.exists():
            art_path = SEEDS_DIR / "shared" / filename
        if art_path.exists():
            files[filename] = art_path.read_bytes()
            if art_meta.type == "pytest_file":
                pytest_filenames.append(filename)

    return config, PreloadedArtifacts(files=files, pytest_filenames=pytest_filenames)


def test_pilot_manifests_completeness() -> None:
    """Ensure all 3 pilot assignments (ds1, lab1, lab6) have calibration manifests."""
    assert "ds1" in MANIFESTS, "ds1 calibration manifest missing"
    assert "lab1" in MANIFESTS, "lab1 calibration manifest missing"
    assert "lab6" in MANIFESTS, "lab6 calibration manifest missing"

    for slug, cases in MANIFESTS.items():
        categories = {c.category for c in cases}
        assert "reference" in categories, f"{slug} missing reference implementation case"
        assert "valid_alternative" in categories, f"{slug} missing valid alternative case"
        assert "misconception" in categories, f"{slug} missing misconception case"


# Flatten cases for clean, readable pytest parametrization
ALL_CALIBRATION_CASES: list[tuple[str, CalibrationCase]] = [
    (slug, case)
    for slug, cases in MANIFESTS.items()
    for case in cases
]


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("slug", "case"),
    ALL_CALIBRATION_CASES,
    ids=[f"{slug}:{c.case_id}" for slug, c in ALL_CALIBRATION_CASES],
)
async def test_calibration_case_execution(slug: str, case: CalibrationCase) -> None:
    """Execute each calibration case and assert scoring outcomes match rubric specifications."""
    config, preloaded_artifacts = _get_preloaded_artifacts_for_slug(slug)
    pipeline = GradingPipeline(
        config=config,
        artifact_refs={},
        allowed_concepts=case.allowed_concepts,
        preloaded_artifacts=preloaded_artifacts,
        executor_fn=execute_local_calibration_runner,
    )

    outcome = await evaluate_calibration_case(pipeline, case)

    assert outcome.passed, (
        f"Calibration failure in '{case.case_id}' ({case.name}):\n"
        + "\n".join(f"- [{d.category}] {d.detail}" for d in outcome.discrepancies)
    )
    assert outcome.actual_score == case.expected_score
    assert outcome.actual_success == case.expected_success
    assert outcome.actual_failure_category == case.expected_failure_category


@pytest.mark.anyio
async def test_unresolved_scoring_discrepancy_blocks_publication() -> None:
    """Verify that scoring discrepancies block assignment publication via AssignmentSpecificationEngine."""
    engine = AssignmentSpecificationEngine()
    config, preloaded_artifacts = _get_preloaded_artifacts_for_slug("ds1")

    # Construct an intentionally uncalibrated case: expects 100 points, but code is broken and gets 80
    broken_case = CalibrationCase(
        assignment_slug="ds1",
        case_id="ds1_intentional_discrepancy",
        name="Broken case expecting 100 points",
        category="misconception",
        description="Expects 100 points but broken inheritance actually yields 80",
        files={
            "dessert.py": b"""class DessertItem:
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
class Sundae(DessertItem): # WRONG
    def __init__(self, name: str = "", scoop_count: int = 0, price_per_scoop: float = 0.0, topping_name: str = "", topping_price: float = 0.0):
        super().__init__(name)
        self.scoop_count = scoop_count
        self.price_per_scoop = price_per_scoop
        self.topping_name = topping_name
        self.topping_price = topping_price
"""
        },
        expected_score=100,  # Intentional discrepancy: expects 100, will score 80
        expected_max_score=100,
        expected_outcomes={"sundae": True},  # expects sundae to pass, will fail
    )

    errors = engine.verify_calibration(
        config=config,
        preloaded_artifacts=preloaded_artifacts,
        cases=[broken_case],
        executor_fn=execute_local_calibration_runner,
    )

    assert len(errors) > 0, "Unresolved discrepancy did not generate blocking validation errors"
    assert any("score_mismatch" in err for err in errors)
    assert any("outcome_mismatch" in err for err in errors)


@pytest.mark.anyio
async def test_regression_ds1_property_decorator_mutability() -> None:
    """Regression: Properties must allow attribute mutation (e.g. item.name = 'Cake')."""
    config, preloaded_artifacts = _get_preloaded_artifacts_for_slug("ds1")
    cases = MANIFESTS["ds1"]
    prop_case = next(c for c in cases if c.case_id == "ds1_valid_alternative_properties")

    pipeline = GradingPipeline(
        config=config,
        artifact_refs={},
        allowed_concepts=["all"],
        preloaded_artifacts=preloaded_artifacts,
        executor_fn=execute_local_calibration_runner,
    )
    outcome = await evaluate_calibration_case(pipeline, prop_case)
    assert outcome.passed
    assert outcome.actual_score == 100


@pytest.mark.anyio
async def test_regression_lab1_single_color_blank_image_detection() -> None:
    """Regression: Blank or single-color image in lab1 is flagged without crashing."""
    config, preloaded_artifacts = _get_preloaded_artifacts_for_slug("lab1")
    cases = MANIFESTS["lab1"]
    blank_case = next(c for c in cases if c.case_id == "lab1_misconception_blank_image")

    pipeline = GradingPipeline(
        config=config,
        artifact_refs={},
        allowed_concepts=["all"],
        preloaded_artifacts=preloaded_artifacts,
        executor_fn=execute_local_calibration_runner,
    )
    outcome = await evaluate_calibration_case(pipeline, blank_case)
    assert outcome.passed
    assert outcome.actual_outcomes["part1_output"] is False
    assert outcome.actual_outcomes["part1_files"] is True
    assert outcome.actual_score == 45


@pytest.mark.anyio
async def test_regression_lab6_ast_checks_enforce_part_separation() -> None:
    """Regression: Part 1 rejects Rect; Part 2 requires Rect."""
    config, preloaded_artifacts = _get_preloaded_artifacts_for_slug("lab6")
    cases = MANIFESTS["lab6"]
    p1_with_rect = next(c for c in cases if c.case_id == "lab6_misconception_part1_uses_rect")
    p2_no_rect = next(c for c in cases if c.case_id == "lab6_misconception_part2_no_rect")

    pipeline = GradingPipeline(
        config=config,
        artifact_refs={},
        allowed_concepts=["all"],
        preloaded_artifacts=preloaded_artifacts,
        executor_fn=execute_local_calibration_runner,
    )

    outcome1 = await evaluate_calibration_case(pipeline, p1_with_rect)
    assert outcome1.passed
    assert outcome1.actual_outcomes["part1_ast_execution"] is False
    assert outcome1.actual_outcomes["part2_ast_execution"] is True
    assert outcome1.actual_score == 30

    outcome2 = await evaluate_calibration_case(pipeline, p2_no_rect)
    assert outcome2.passed
    assert outcome2.actual_outcomes["part1_ast_execution"] is True
    assert outcome2.actual_outcomes["part2_ast_execution"] is False
    assert outcome2.actual_score == 30
