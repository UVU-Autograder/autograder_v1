import json
import logging
import sys
from pathlib import Path
import pytest

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


def test_audit_event_raises_on_unallowlisted_fields_in_development():
    with pytest.raises(ValueError, match="Unallowlisted fields in audit_event 'official.run_completed'"):
        audit_event(
            "official.run_completed",
            run_id=7,
            success_count=10,
            student_identifier="should-not-appear",
            matched_file="dessert.py",
        )


def test_audit_event_production_drops_and_warns_on_meta(caplog, monkeypatch):
    import app.core.settings as settings_mod
    current_settings = settings_mod.get_settings()
    monkeypatch.setattr(current_settings, "environment", "production")

    caplog.set_level(logging.INFO)
    audit_event(
        "official.run_completed",
        run_id=7,
        success_count=10,
        student_identifier="should-not-appear",
        matched_file="dessert.py",
    )

    audit_records = [r for r in caplog.records if r.name == "autograder.audit"]
    meta_records = [r for r in caplog.records if r.name == "autograder.audit.meta"]

    assert len(audit_records) == 1
    payload = json.loads(audit_records[0].message)
    assert payload["audit_event"] == "official.run_completed"
    assert payload["run_id"] == 7
    assert payload["success_count"] == 10
    assert "student_identifier" not in payload
    assert "matched_file" not in payload

    assert len(meta_records) == 1
    assert "Dropped unallowlisted audit fields" in meta_records[0].message
    assert "student_identifier" in meta_records[0].message


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


def test_redact_institutional_student_id():
    raw = "Request failed for student U10876543 and u12345678 and U-10123456"
    redacted = redact_sensitive_text(raw)
    assert "U10876543" not in redacted
    assert "u12345678" not in redacted
    assert "U-10123456" not in redacted
    assert "[REDACTED_UVU_ID]" in redacted


def test_redact_sensitive_text_preserves_numeric_identifiers():
    raw = "Listening on port 8000 with 42 submissions at unix timestamp 1728940800"
    redacted = redact_sensitive_text(raw)
    assert "8000" in redacted
    assert "42" in redacted
    assert "1728940800" in redacted


def test_audit_context_copy_on_write():
    from app.core.audit_log import _AUDIT_CONTEXT, audit_context

    assert _AUDIT_CONTEXT.get() is None

    with audit_context(run_id=10, workflow_type="official"):
        assert _AUDIT_CONTEXT.get() == {"run_id": 10, "workflow_type": "official"}

        with audit_context(run_id=20, course_id="cs1410"):
            # Nested context overrides run_id and inherits workflow_type
            assert _AUDIT_CONTEXT.get() == {
                "run_id": 20,
                "workflow_type": "official",
                "course_id": "cs1410",
            }

        # Parent context restored
        assert _AUDIT_CONTEXT.get() == {"run_id": 10, "workflow_type": "official"}

    # Exited context restored to None
    assert _AUDIT_CONTEXT.get() is None


def test_audit_context_tagging_idempotent(caplog):
    from app.core.audit_log import SensitiveDataFilter, audit_context

    caplog.set_level(logging.INFO)
    logger = logging.getLogger("test.audit.tagging")
    filter_instance = SensitiveDataFilter()
    logger.addFilter(filter_instance)
    logger.propagate = False

    handler = logging.StreamHandler()
    handler.addFilter(filter_instance)
    logger.addHandler(handler)

    with audit_context(run_id=42, workflow_type="official"):
        record = logger.makeRecord("test.audit.tagging", logging.INFO, "fn", 1, "Task completed %s", ("cleanly",), None)
        filter_instance.filter(record)
        assert record.msg == "[run_id=42 workflow_type=official] Task completed cleanly"

        # A second filter pass (e.g. at handler level) must not double-prefix
        filter_instance.filter(record)
        assert record.msg == "[run_id=42 workflow_type=official] Task completed cleanly"


def test_audit_context_does_not_tag_audit_json(caplog):
    from app.core.audit_log import audit_context

    caplog.set_level(logging.INFO)
    with audit_context(run_id=55, workflow_type="official"):
        audit_event("official.workspace_deleted")

    audit_records = [r for r in caplog.records if r.name == "autograder.audit"]
    assert len(audit_records) == 1
    assert not audit_records[0].message.startswith("[")
    payload = json.loads(audit_records[0].message)
    assert payload["run_id"] == 55
    assert payload["workflow_type"] == "official"
    assert payload["audit_event"] == "official.workspace_deleted"


def test_log_and_audit_error_helper(caplog):
    from app.core.audit_log import log_and_audit_error

    caplog.set_level(logging.INFO)
    domain_logger = logging.getLogger("test.domain.executor")

    log_and_audit_error(
        domain_logger,
        "Failed Judge0 cleanup for token",
        event="judge0.cleanup_failed",
        failure_category="cleanup_failure",
        workflow_type="official",
    )

    domain_records = [r for r in caplog.records if r.name == "test.domain.executor"]
    audit_records = [r for r in caplog.records if r.name == "autograder.audit"]

    assert len(domain_records) == 1
    assert domain_records[0].levelno == logging.ERROR
    assert "Failed Judge0 cleanup" in domain_records[0].message

    assert len(audit_records) == 1
    payload = json.loads(audit_records[0].message)
    assert payload["audit_event"] == "judge0.cleanup_failed"
    assert payload["failure_category"] == "cleanup_failure"


def test_inspect_logs_cli_subprocess(tmp_path):
    import subprocess

    clean_file = tmp_path / "clean_audit.log"
    clean_file.write_text(
        '{"timestamp": "2026-10-14T20:00:00Z", "audit_event": "official.workspace_deleted", "run_id": 1}\n',
        encoding="utf-8",
    )

    dirty_file = tmp_path / "dirty_audit.log"
    dirty_file.write_text(
        'Error occurred for user test@uvu.edu in student_12345\n',
        encoding="utf-8",
    )

    python_bin = sys.executable
    inspect_script = Path(BACKEND_ROOT).parent / "scripts" / "inspect_logs.py"

    # Clean file check
    res_clean = subprocess.run(
        [python_bin, str(inspect_script), "--file", str(clean_file), "--verify-pii"],
        capture_output=True,
        text=True,
    )
    assert res_clean.returncode == 0
    assert "[OK] 0 residual Canvas filename" in res_clean.stdout

    # Dirty file check
    res_dirty = subprocess.run(
        [python_bin, str(inspect_script), "--file", str(dirty_file), "--verify-pii"],
        capture_output=True,
        text=True,
    )
    assert res_dirty.returncode == 1
    assert "[VIOLATION]" in res_dirty.stderr



