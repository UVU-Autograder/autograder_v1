"""Tests for reusable instructor rubric comment templates (#41)."""
from __future__ import annotations

from app.domains.assignments.schemas import ScoringItemConfig
from app.domains.assignments.service import build_scoring_items
from app.domains.runs.service import init_manual_results, student_detail_from_result


def test_scoring_item_config_comment_templates():
    item = ScoringItemConfig(
        key="style_review",
        label="Code Style",
        points=10,
        extra_credit=False,
        item_type="manual",
        comment_templates=[
            "  Missing docstrings on helper functions  ",
            "Variable names should follow PEP 8 snake_case",
            "",
            "   ",
        ],
    )
    # Strips whitespace and filters empty items
    assert item.comment_templates == [
        "Missing docstrings on helper functions",
        "Variable names should follow PEP 8 snake_case",
    ]


def test_build_scoring_items_preserves_templates():
    configs = [
        ScoringItemConfig(
            key="manual_check",
            label="Manual Check",
            points=5,
            extra_credit=False,
            item_type="manual",
            comment_templates=["Good structure", "Add inline comments"],
        ),
        ScoringItemConfig(
            key="pytest_check",
            label="Automated Check",
            points=10,
            extra_credit=False,
            item_type="pytest",
        ),
    ]
    items = build_scoring_items(configs)
    assert len(items) == 2
    assert items[0].comment_templates == ["Good structure", "Add inline comments"]
    assert items[1].comment_templates == []


def test_init_manual_results_includes_comment_templates():
    scoring_items = [
        ScoringItemConfig(
            key="readability",
            label="Readability",
            points=5,
            extra_credit=False,
            item_type="manual",
            comment_templates=["Follow PEP 8", "Break down long functions"],
        ),
        ScoringItemConfig(
            key="test_auto",
            label="Test Auto",
            points=10,
            extra_credit=False,
            item_type="pytest",
        ),
    ]
    manual = init_manual_results(scoring_items)
    assert "readability" in manual
    assert "test_auto" not in manual
    assert manual["readability"]["comment_templates"] == [
        "Follow PEP 8",
        "Break down long functions",
    ]
    assert manual["readability"]["score"] is None
    assert manual["readability"]["comments"] == ""


def test_student_detail_from_result_preserves_comment_templates():
    raw_result = {
        "student_identifier": "Student A",
        "score": 80,
        "max_score": 100,
        "manual_results": {
            "style": {
                "label": "Code Style",
                "points": 10,
                "score": 8,
                "comments": "Minor formatting fixes needed.",
                "comment_templates": ["Follow PEP 8", "Missing docstrings"],
            }
        },
    }
    detail = student_detail_from_result("student_123", raw_result)
    assert detail["canvas_id"] == "student_123"
    assert "style" in detail["manual_results"]
    assert detail["manual_results"]["style"]["comment_templates"] == [
        "Follow PEP 8",
        "Missing docstrings",
    ]
