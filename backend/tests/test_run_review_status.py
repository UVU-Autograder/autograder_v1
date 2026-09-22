import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.domains.runs.service import automated_review_status, student_detail_from_result


def test_automated_review_status_partial_score():
    status, preview = automated_review_status({
        "success": True,
        "score": 40,
        "automated_max_score": 100,
        "test_results": [
            {"key": "relational_ops", "label": "Relational operators", "passed": True},
            {"key": "order_sort", "label": "Order.sort()", "passed": False},
        ],
    })
    assert status == "warning"
    assert "Partial automated score (40/100 pts)" in preview
    assert "Order.sort()" in preview


def test_automated_review_status_full_score():
    status, preview = automated_review_status({
        "success": True,
        "score": 100,
        "automated_max_score": 100,
        "test_results": [{"key": "all", "label": "All checks", "passed": True}],
    })
    assert status == "success"
    assert preview == "All automated tests passed successfully."


def test_student_detail_includes_bundle_files():
    detail = student_detail_from_result(
        "1915257",
        {
            "student_identifier": "wildeluke",
            "success": True,
            "score": 40,
            "max_score": 100,
            "automated_max_score": 100,
            "bundle_files": ["dessert.py", "dessertshop.py", "payment.py"],
            "bundle_file_count": 3,
            "test_results": [{"key": "a", "label": "Check A", "passed": False}],
        },
    )
    assert detail["bundle_files"] == ["dessert.py", "dessertshop.py", "payment.py"]
    assert detail["bundle_file_count"] == 3
    assert "matched_file" not in detail
