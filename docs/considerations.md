# Privacy and future constraints

These are engineering requirements, not institutional signoff. Detailed approval/security work and future questions live in [GitHub Issues](https://github.com/UVU-Autograder/autograder_v1/issues).

## Institutional authorization

Live official grading needs recorded UVU Software Approval/ATSC scope and clear team responsibility; AI approval is separate where applicable. The staff pilot waits for institutional SSO. Development mock login is not its fallback.

Use synthetic or completely anonymized validation data; mapped pseudonyms are not anonymous. Existing policy permits authorized, section-scoped workstation debugging of real Canvas ZIPs in governed ephemeral storage. This does not authorize live-course use. Keep submissions/exports out of Git, issues and long-lived fixtures.

## Retention and data boundaries

| Data | Boundary |
| --- | --- |
| Staff/grants, course/assignment setup, instructor assets | Persistent approved database/artifact storage |
| Operational records | Aggregate counts, scheduling metadata and sanitized usage/errors only |
| Student execution files and Judge0 payloads/results/tokens | Delete immediately after result handling; verify non-retrievability |
| Sandbox bundle/files | Clean after results/failure/cancellation; session results remain transient |
| Official ZIP, review detail, names/identifiers and exports | Review ends 23h after intake; physical deletion by 24h or earlier staff cleanup |

The independent [cleanup worker](../backend/app/domains/runs/cleanup_worker.py) reconciles at startup/every 60 seconds, tombstones access, retries deletion and reports overdue files. Database outages fail closed. Downtime preventing physical deletion remains a violation to resolve. Institutional handling applies to staff-downloaded exports.

Logs/AI payloads exclude identifiers, code, raw filenames, traceback bodies and detailed feedback. [Python JSON audit logging](../backend/app/core/audit_log.py) allowlists fields, intercepts 401/403 access denials, and enforces process-wide redaction and traceback scrubbing via `RedactingFormatter` and framework logger wrappers. Host destinations (`0640` permissions) and container log rotation caps (`50m`/5 files) are verified on the workstation. Any approved sensitive debugging trace must be purged within 24h.

### FERPA audit log compliance and data dictionary

To comply with 34 CFR Part 99 (FERPA § 99.30) and institutional inspection requirements, the system strictly separates operational system telemetry from student education records.

#### Prohibited data (Never logged or stored)
Under no circumstances are any of the following written to application or audit logs:
- **Student Identifiers**: Student names, Canvas user IDs, UVU U-numbers (`[REDACTED_UVU_ID]`), or email addresses (`[REDACTED_EMAIL]`).
- **Submission Artifacts**: Source code files, submission contents, or unredacted Canvas export archive filenames (`[REDACTED_CANVAS_FILENAME]`).
- **Academic Evaluations**: Grades, numerical scores, test failure messages, assertion outputs, or student-facing rubric feedback.

#### Audit log data dictionary (`autograder.audit`)
All structured audit entries are emitted as single-line JSON records containing only `timestamp` (ISO 8601 UTC), `audit_event`, and keys explicitly present in the field allowlist ([`backend/app/core/audit_log.py`](../backend/app/core/audit_log.py)):

| Field | Type | Description / Scope | Compliance Classification |
| --- | --- | --- | --- |
| `actor_user_id` | integer | Staff user ID performing the administrative action | Staff administrative identity only |
| `assignment_id` | string / integer | Target assignment identifier | Curriculum catalog metadata |
| `cleaned_runs_count` | integer | Number of expired run workspaces removed during reconciliation | Aggregate operational metric |
| `client_ip` | string | Remote IP address initiating the HTTP request | Transient network security telemetry |
| `course_id` | string / integer | Course identifier (e.g., `cs1410`) | Course catalog metadata |
| `denial_reason` | string | Normalized HTTP 401/403 authorization rejection reason | Sanitized operational message |
| `error_count` | integer | Number of system errors encountered during worker pass | Aggregate operational metric |
| `failure_category` | string | Machine-readable failure classification (e.g. `invalid_runner_report`) | Aggregate operational diagnostic |
| `failure_count` | integer | Count of failed jobs in batch pass | Aggregate operational metric |
| `http_method` | string | HTTP request verb (e.g., `GET`, `POST`) | Operational protocol telemetry |
| `path` | string | URL route requested (e.g., `/staff/courses`) | Operational routing telemetry |
| `run_id` | integer | Internal autograder execution run database ID | Internal system reference |
| `sandbox_run_id` | integer | Ephemeral sandbox execution session ID | Transient execution reference |
| `section_id` | string / integer | Section identifier | Course catalog metadata |
| `status_code` | integer | HTTP response status code | Operational protocol telemetry |
| `submission_count` | integer | Aggregate batch size received during Canvas intake | Aggregate volume metric |
| `success_count` | integer | Number of successful student executions completed | Aggregate volume metric |
| `timeout_count` | integer | Number of sandboxes reaching hard time limits | Aggregate operational metric |
| `unmatched_count` | integer | Number of archive files not matching expected student patterns | Aggregate operational metric |
| `warning_count` | integer | Non-fatal anomaly count | Aggregate operational metric |
| `workflow_type` | string | Operational pipeline segment (`official`, `sandbox`, `logging`) | System architectural categorization |

#### Enforcement and verification
1. **Single-Path Validation**: Any parameter key passed to `audit_context` or `audit_event` outside the allowlist raises a `ValueError` in non-production environments (`environment != "production"`) to prevent silent metric omissions. In production, unallowlisted keys are dropped and an operational warning is emitted to the separate `autograder.audit.meta` logger, ensuring `autograder.audit` records remain parseable single-line JSON.
2. **Process-Wide Interception**: `SensitiveDataFilter` and `RedactingFormatter` wrap all application and third-party framework loggers (`uvicorn`, `celery`, `sqlalchemy`), scrubbing unhandled exception tracebacks, stack frames, and idempotently prefixing application lines with ambient context.
3. **Inspector Tooling**: Institutional auditors and developers can review audit streams or verify logs using [`scripts/inspect_logs.py`](../scripts/inspect_logs.py):
   * `python scripts/inspect_logs.py --sample`: Formats sample audit records in a clean tabular report.
   * `python scripts/inspect_logs.py --file <path> --verify-pii`: Scans records against canonical FERPA regex rules, reporting zero residual Canvas filename, email, U-number, workspace-segment, or token patterns. Pattern scanning validates automated scrubbers; it does not detect unpatterned student names or grades.
4. **Automated Verification**: Non-retention, sanitization, and context tagging guarantees are continuously verified by [`backend/tests/test_audit_log.py`](../backend/tests/test_audit_log.py) and [`backend/tests/test_audit_access_denial.py`](../backend/tests/test_audit_access_denial.py).

Back up only approved persistent metadata and instructor assets, excluding student detail, workspaces, and broker/results (FERPA contract). [Recovery](guides/workstation.md#back-up-and-restore) describes verified metadata dump and container artifact extraction procedures; institutional offsite schedule and retention cadence remain open.

## AI data and future changes

AI is sandbox-only, explanation-only and university-local, with sanitization and unavailable-feedback fallback. Training uses reviewed synthetic seed mutations; preserve provenance, held-out separation and prompt/eval/serving parity. Student corpora require separate data/retention approval; model weights are not deletable review workspaces. Keep data/training on university-controlled hardware.

The pilot stays on the workstation with Judge0/Kata VM isolation, restricted listeners and TLS/Entra for live operation. Cloud/external AI, persistent histories, Canvas integration or altered isolation require an explicit approved scope. Open-source ownership/licensing and funding remain tracked in GitHub Issues ([#48](https://github.com/UVU-Autograder/autograder_v1/issues/48), [#49](https://github.com/UVU-Autograder/autograder_v1/issues/49)).

Institutional references: [UVU FERPA](https://www.uvu.edu/registration/ferpa/index.html), [system procurement](https://www.uvu.edu/biservices/system-procurement-implementation.html), [ATSC](https://www.uvu.edu/biservices/governance.html), [policy manual](https://www.uvu.edu/policies/manual/). Confirm current requirements with UVU.
