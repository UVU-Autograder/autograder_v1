import json
import logging
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.core.audit_log import (
    RedactingFormatter,
    SensitiveDataFilter,
    audit_access_denied,
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


def test_redacting_formatter_scrubs_traceback():
    import io

    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(RedactingFormatter(logging.Formatter("%(levelname)s: %(message)s")))

    test_logger = logging.getLogger("test.audit.traceback")
    test_logger.handlers = [handler]
    test_logger.propagate = False

    try:
        raise ValueError(
            "Failed student_12345 in allenandrew_2051945_133817322_dessert.py with token 12345678-1234-5678-1234-567812345678 and email user@uvu.edu"
        )
    except ValueError:
        test_logger.exception("Traceback error encountered")

    output = stream.getvalue()
    assert "allenandrew" not in output
    assert "2051945" not in output
    assert "student_12345" not in output
    assert "12345678-1234-5678-1234-567812345678" not in output
    assert "user@uvu.edu" not in output
    assert "[REDACTED_CANVAS_FILENAME]" in output
    assert "student_[REDACTED]" in output
    assert "[REDACTED_TOKEN]" in output
    assert "[REDACTED_EMAIL]" in output


def test_configure_audit_logging_applies_to_child_loggers():
    import io

    child = logging.getLogger("test.audit.child_unpropagated")
    child.setLevel(logging.INFO)
    child.propagate = False
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(logging.Formatter("%(message)s"))
    child.handlers = [handler]

    configure_audit_logging()

    child.info("Student workspace /data/workspaces/official_1/student_99999/test.py")
    output = stream.getvalue()
    assert "student_99999" not in output
    assert "student_[REDACTED]" in output


def test_audit_event_security_fields(caplog):
    caplog.set_level(logging.INFO, logger="autograder.audit")
    audit_event(
        "auth.access_denied",
        status_code=403,
        denial_reason="Insufficient staff permissions",
        path="/staff/courses/10/concepts",
        http_method="PUT",
        client_ip="10.0.0.42",
        actor_user_id=101,
        unallowed_query="student_email=test@uvu.edu",
    )
    assert len(caplog.records) == 1
    payload = json.loads(caplog.records[0].message)
    assert payload["audit_event"] == "auth.access_denied"
    assert payload["status_code"] == 403
    assert payload["denial_reason"] == "Insufficient staff permissions"
    assert payload["path"] == "/staff/courses/10/concepts"
    assert payload["http_method"] == "PUT"
    assert payload["client_ip"] == "10.0.0.42"
    assert payload["actor_user_id"] == 101
    assert "unallowed_query" not in payload


def test_audit_access_denied_helper(caplog):
    caplog.set_level(logging.INFO, logger="autograder.audit")
    audit_access_denied(
        status_code=401,
        reason="Missing student_12345 in clarklandon_1972516_133846039_test_sundae-6.py",
        actor_user_id=None,
        path="/runs",
        http_method="POST",
        client_ip="127.0.0.1",
    )
    assert len(caplog.records) == 1
    payload = json.loads(caplog.records[0].message)
    assert payload["audit_event"] == "auth.access_denied"
    assert payload["status_code"] == 401
    assert "[REDACTED_CANVAS_FILENAME]" in payload["denial_reason"]
    assert "clarklandon" not in payload["denial_reason"]
    assert "student_12345" not in payload["denial_reason"]
    assert payload["path"] == "/runs"
    assert payload["http_method"] == "POST"
    assert payload["client_ip"] == "127.0.0.1"
    assert "actor_user_id" not in payload

