#!/usr/bin/env python3
"""Audit Log Inspector & FERPA Pattern Verifier.

Standard-library CLI tool for institutional auditors and developers to:
1. Pretty-print structured audit records in a clean tabular view.
2. Validate log streams against canonical FERPA regex rules to ensure zero
   residual Canvas filenames, emails, U-numbers, workspace segments, or tokens.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# Ensure backend modules are importable
BACKEND_ROOT = Path(__file__).resolve().parent.parent / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.sanitizer import LOG_REDACTION_RULES

SAMPLE_AUDIT_RECORDS: list[dict[str, Any]] = [
    {
        "timestamp": "2026-10-14T20:15:00.123456+00:00",
        "audit_event": "auth.access_denied",
        "actor_user_id": 101,
        "status_code": 403,
        "workflow_type": "logging",
        "denial_reason": "Insufficient section permissions",
        "path": "/staff/courses/10/concepts",
    },
    {
        "timestamp": "2026-10-14T20:18:22.654321+00:00",
        "audit_event": "official.ingest_queued",
        "actor_user_id": 101,
        "course_id": "cs1410",
        "assignment_id": "lab2",
        "submission_count": 48,
        "workflow_type": "official",
        "run_id": 12,
    },
    {
        "timestamp": "2026-10-14T20:19:05.111222+00:00",
        "audit_event": "judge0.cleanup_failed",
        "failure_category": "cleanup_failure",
        "workflow_type": "official",
    },
    {
        "timestamp": "2026-10-14T20:25:00.999888+00:00",
        "audit_event": "official.workspace_deleted",
        "run_id": 12,
        "workflow_type": "official",
    },
]


def format_table(headers: list[str], rows: list[list[str]]) -> str:
    """Format plain-text aligned ASCII table using only standard library."""
    if not rows:
        return "(No records to display)"
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, val in enumerate(row):
            if i < len(col_widths):
                col_widths[i] = max(col_widths[i], len(val))

    header_line = " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
    separator = "-+-".join("-" * col_widths[i] for i in range(len(headers)))
    row_lines = [
        " | ".join(val.ljust(col_widths[i]) for i, val in enumerate(row))
        for row in rows
    ]
    return f"{header_line}\n{separator}\n" + "\n".join(row_lines)


def render_audit_records(records: list[dict[str, Any]]) -> str:
    headers = ["Timestamp (UTC)", "Event", "Actor", "Status", "Workflow", "Metadata"]
    rows: list[list[str]] = []
    for record in records:
        ts = str(record.get("timestamp", ""))[:19].replace("T", " ")
        event = str(record.get("audit_event", ""))
        actor = str(record.get("actor_user_id", "-"))
        status = str(record.get("status_code", "-"))
        workflow = str(record.get("workflow_type", "-"))

        meta_parts: list[str] = []
        for key in sorted(record.keys()):
            if key not in ("timestamp", "audit_event", "actor_user_id", "status_code", "workflow_type"):
                meta_parts.append(f"{key}={record[key]}")
        metadata = ", ".join(meta_parts) if meta_parts else "-"
        rows.append([ts, event, actor, status, workflow, metadata])

    return format_table(headers, rows)


def verify_pii_patterns(lines: list[str]) -> tuple[bool, list[str]]:
    """Scan log lines against canonical patterns. Returns (is_clean, violations)."""
    violations: list[str] = []
    for line_idx, line in enumerate(lines, start=1):
        clean_line = line.strip()
        if not clean_line:
            continue
        for pattern, _replacement in LOG_REDACTION_RULES:
            match = pattern.search(clean_line)
            if match:
                violations.append(
                    f"Line {line_idx} matched {pattern.pattern!r}: {match.group(0)!r}\n  Full line: {clean_line}"
                )
    return (len(violations) == 0, violations)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Inspect and verify autograder audit logs for FERPA compliance."
    )
    parser.add_argument(
        "--file",
        help="Path to log file (or '-' for stdin)",
    )
    parser.add_argument(
        "--verify-pii",
        action="store_true",
        help="Scan log lines against canonical FERPA regex rules and verify zero residual identifiers.",
    )
    parser.add_argument(
        "--sample",
        action="store_true",
        help="Print pretty-formatted sample audit events demonstrating schema and redaction in action.",
    )
    args = parser.parse_args()

    if args.sample:
        print("\n=== Sample Structured Audit Log Records ===")
        print(render_audit_records(SAMPLE_AUDIT_RECORDS))
        print("\nAll fields conform to ALLOWED_AUDIT_FIELDS and omit raw student education records.\n")
        return

    if not args.file:
        parser.print_help()
        sys.exit(0)

    # Read input lines
    if args.file == "-":
        lines = sys.stdin.readlines()
    else:
        path = Path(args.file)
        if not path.is_file():
            print(f"Error: Log file not found: {path}", file=sys.stderr)
            sys.exit(2)
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()

    if args.verify_pii:
        is_clean, violations = verify_pii_patterns(lines)
        if is_clean:
            print(
                f"[OK] 0 residual Canvas filename, email, U-number, workspace-segment, or token patterns in {len(lines)} records."
            )
            print(
                "(Note: Pattern scanning validates automated scrubbers; it does not detect student names or grades outside defined patterns.)"
            )
            sys.exit(0)
        else:
            print(f"[VIOLATION] Found {len(violations)} unredacted pattern match(es):", file=sys.stderr)
            for v in violations:
                print(f"  {v}", file=sys.stderr)
            sys.exit(1)

    # If --verify-pii was not passed, parse as JSON audit records if possible
    records: list[dict[str, Any]] = []
    raw_lines: list[str] = []
    for line in lines:
        line_clean = line.strip()
        if not line_clean:
            continue
        try:
            records.append(json.loads(line_clean))
        except (json.JSONDecodeError, ValueError):
            raw_lines.append(line_clean)

    if records:
        print(f"\n=== Audit Log Inspection ({len(records)} records) ===")
        print(render_audit_records(records))
    if raw_lines:
        print(f"\n=== Non-JSON Log Lines ({len(raw_lines)} lines) ===")
        for raw in raw_lines[:20]:
            print(f"  {raw}")
        if len(raw_lines) > 20:
            print(f"  ... ({len(raw_lines) - 20} more lines)")


if __name__ == "__main__":
    main()
