import json
import logging
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.core.audit_log import (
    SensitiveDataFilter,
    audit_event,
    configure_audit_logging,
    redact_sensitive_text,
)


def test_redact_canvas_export_filename():
    raw = "Failed to copy allenandrew_2051945_133817322_dessert-bccde8b7-b9d3-4fb7-b04c-3e48ba38dfa2.py"
    redacted = redact_sensitive_text(raw)
    assert "allenandrew" not in redacted
    assert "2051945" not in redacted
    assert "[REDACTED_CANVAS_FILENAME]" in redacted


def test_redact_student_workspace_segment():
    raw = "Workspace /data/workspaces/official_12/student_2051945/main.py missing"
    redacted = redact_sensitive_text(raw)
    assert "student_2051945" not in redacted
    assert "student_[REDACTED]" in redacted


def test_audit_event_allowlists_fields(caplog):
    caplog.set_level(logging.INFO, logger="autograder.audit")
    audit_event(
        "official.run_completed",
        run_id=7,
        success_count=10,
        student_identifier="should-not-appear",
        matched_file="dessert.py",
    )
    assert len(caplog.records) == 1
    payload = json.loads(caplog.records[0].message)
    assert payload["audit_event"] == "official.run_completed"
    assert payload["run_id"] == 7
    assert payload["success_count"] == 10
    assert "student_identifier" not in payload
    assert "matched_file" not in payload


def test_sensitive_data_filter_redacts_log_message(caplog):
    caplog.set_level(logging.INFO)
    logger = logging.getLogger("test.audit.filter")
    logger.addFilter(SensitiveDataFilter())
    logger.error(
        "Could not read clarklandon_LATE_1972516_133846039_test_sundae-6.py in student_1972516"
    )
    assert len(caplog.records) == 2
    audit_records = [record for record in caplog.records if record.name == "autograder.audit"]
    error_records = [record for record in caplog.records if record.name == "test.audit.filter"]
    assert len(audit_records) == 1
    assert json.loads(audit_records[0].message)["audit_event"] == "audit.pii_redacted"
    assert "clarklandon" not in error_records[0].message


def test_configure_audit_logging_is_idempotent():
    configure_audit_logging()
    root_filters = list(logging.getLogger().filters)
    configure_audit_logging()
    assert sum(isinstance(item, SensitiveDataFilter) for item in root_filters) == 1
