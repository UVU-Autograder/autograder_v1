"""Private scoring-item projection must not leak assertion detail to students/AI."""
from __future__ import annotations

from types import SimpleNamespace

from app.domains.grading.result_parser import (
    PRIVATE_TEST_KEY,
    PRIVATE_TEST_LABEL,
    redact_private_test_details,
    student_safe_diagnostics,
)
from app.domains.sandbox.catalog import project_student_scoring
from app.integrations.ai.prompts import failures_from_test_results, requirements_from_config


def test_redact_private_test_details_preserves_points_hides_diff() -> None:
    items = [
        {
            "key": "public_add",
            "label": "Add numbers",
            "points": 5,
            "points_awarded": 0,
            "passed": False,
            "is_private": False,
            "your_value": "1",
            "expected_value": "2",
            "test_results": [{"nodeid": "t::test_add", "outcome": "failed", "message": "assert 1 == 2"}],
        },
        {
            "key": "secret_edge",
            "label": "Secret edge case",
            "points": 10,
            "points_awarded": 0,
            "passed": False,
            "is_private": True,
            "marker": "ag_secret_edge",
            "your_value": "bad",
            "expected_value": "good",
            "test_results": [
                {
                    "nodeid": "t::test_secret",
                    "outcome": "failed",
                    "message": "assert secret",
                    "actual": "bad",
                    "expected": "good",
                }
            ],
        },
    ]
    out = redact_private_test_details(items)
    assert out[0]["label"] == "Add numbers"
    assert out[0]["your_value"] == "1"
    assert out[1]["key"] == f"{PRIVATE_TEST_KEY}_1"
    assert out[1]["label"] == PRIVATE_TEST_LABEL
    assert out[1]["points"] == 10
    assert out[1]["points_awarded"] == 0
    assert out[1]["your_value"] is None
    assert out[1]["expected_value"] is None
    assert out[1]["marker"] is None
    assert "secret" not in (out[1].get("message") or "").lower()
    assert "secret" not in out[1]["key"].lower()
    assert out[1]["test_results"][0]["message"] is None
    assert "secret" not in str(out[1]["test_results"]).lower()


def test_student_safe_diagnostics_drops_streams() -> None:
    safe = student_safe_diagnostics(
        {
            "stdout": "SECRET_OUTPUT",
            "stderr": "traceback with secret",
            "stdout_truncated": True,
            "stderr_truncated": False,
            "extra": "drop me",
        }
    )
    assert safe == {"stdout_truncated": True, "stderr_truncated": False}
    assert student_safe_diagnostics(None) == {}
    assert student_safe_diagnostics({}) == {}


def test_failures_from_test_results_redacts_private() -> None:
    failures, passing = failures_from_test_results(
        [
            {
                "key": "secret_edge",
                "label": "Secret edge case",
                "passed": False,
                "is_private": True,
                "item_type": "pytest",
                "test_results": [{"outcome": "failed", "message": "assert secret == 1", "actual": "0"}],
            },
            {
                "key": "ok",
                "label": "Visible pass",
                "passed": True,
                "is_private": False,
                "item_type": "pytest",
                "test_results": [],
            },
        ]
    )
    assert passing == ["Visible pass"]
    assert len(failures) == 1
    assert failures[0]["label"] == PRIVATE_TEST_LABEL
    assert failures[0]["key"] == f"{PRIVATE_TEST_KEY}_1"
    assert "secret" not in failures[0]["key"].lower()
    assert failures[0].get("message") is None
    assert failures[0].get("your_value") is None


def test_requirements_from_config_omits_private_labels() -> None:
    text = requirements_from_config(
        {
            "scoring_items": [
                {"key": "a", "label": "Public check", "item_type": "pytest"},
                {"key": "b", "label": "Secret regression", "item_type": "pytest", "is_private": True},
            ]
        }
    )
    assert "Public check" in text
    assert "Secret regression" not in text
    assert "hidden automated check" in text.lower()


def test_project_student_scoring_redacts_private_catalog_items() -> None:
    config = SimpleNamespace(
        scoring_items=[
            SimpleNamespace(
                key="public_add",
                label="Add numbers",
                points=5,
                extra_credit=False,
                item_type="pytest",
                is_private=False,
                rubric_group_key="core",
                inputs=["1 2"],
                outputs=["3"],
            ),
            SimpleNamespace(
                key="secret_edge",
                label="Secret edge case",
                points=10,
                extra_credit=False,
                item_type="pytest",
                is_private=True,
                rubric_group_key="core",
                inputs=["hidden input"],
                outputs=["hidden output"],
            ),
        ],
        rubric_groups=[SimpleNamespace(key="core", label="Core")],
        completion_requirements=[
            SimpleNamespace(
                model_dump=lambda: {
                    "key": "pass_both",
                    "label": "Pass both",
                    "test_keys": ["public_add", "secret_edge"],
                    "minimum_passed": 2,
                }
            )
        ],
    )
    rubric, groups, completion = project_student_scoring(config)
    assert rubric[0].key == "public_add"
    assert rubric[0].label == "Add numbers"
    assert rubric[0].pytest_marker == "ag_public_add"
    assert rubric[0].inputs == ["1 2"]

    assert rubric[1].key == f"{PRIVATE_TEST_KEY}_1"
    assert rubric[1].label == PRIVATE_TEST_LABEL
    assert rubric[1].pytest_marker is None
    assert rubric[1].inputs is None
    assert rubric[1].outputs is None
    assert "secret" not in (rubric[1].key or "").lower()

    assert groups[0].item_keys == ["public_add", f"{PRIVATE_TEST_KEY}_1"]
    assert completion[0]["test_keys"] == ["public_add", f"{PRIVATE_TEST_KEY}_1"]
