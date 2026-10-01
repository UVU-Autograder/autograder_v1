# Privacy and future constraints

These are engineering requirements, not institutional signoff. Detailed approval/security work and future questions live in the [backlog](planning/backlog.md).

## Institutional authorization

Live official grading needs recorded UVU Software Approval/ATSC scope and clear team responsibility; AI approval is separate where applicable. The staff pilot waits for institutional SSO. Development mock login is not its fallback.

Use synthetic or completely anonymized validation data; mapped pseudonyms are not anonymous. Existing policy permits authorized, section-scoped workstation debugging of real Canvas ZIPs in governed ephemeral storage. This does not authorize live-course use. Keep submissions/exports out of Git, issues and long-lived fixtures.

## Retention and data boundaries

| Data | Boundary |
| --- | --- |
| Staff/grants, course/assignment setup/history, instructor assets | Persistent approved database/artifact storage |
| Operational records | Aggregate counts, scheduling metadata and sanitized usage/errors only |
| Student execution files and Judge0 payloads/results/tokens | Delete immediately after result handling; verify non-retrievability |
| Sandbox bundle/files | Clean after results/failure/cancellation; session results remain transient |
| Official ZIP, review detail, names/identifiers and exports | Review ends 23h after intake; physical deletion by 24h or earlier staff cleanup |

The independent [cleanup worker](../backend/app/domains/runs/cleanup_worker.py) reconciles at startup/every 60 seconds, tombstones access, retries deletion and reports overdue files. Database outages fail closed. Downtime preventing physical deletion remains a violation to resolve. Institutional handling applies to staff-downloaded exports.

Logs/AI payloads exclude identifiers, code, raw filenames, traceback bodies and detailed feedback. [Python JSON audit logging](../backend/app/core/audit_log.py) allowlists fields, but its root-only filter does not establish process-wide redaction; destinations/coverage/access/rotation need verification. Any approved sensitive debugging trace must be purged within 24h.

Back up only approved persistent metadata/instructor assets, excluding student detail and broker/results. [Recovery](guides/workstation.md#back-up-and-restore) describes current script limitations.

## AI data and future changes

AI is sandbox-only, explanation-only and university-local, with sanitization and unavailable-feedback fallback. Training uses reviewed synthetic seed mutations; preserve provenance, held-out separation and prompt/eval/serving parity. Student corpora require separate data/retention approval; model weights are not deletable review workspaces. Keep data/training on university-controlled hardware.

The pilot stays on the workstation with Judge0/Kata VM isolation, restricted listeners and TLS/Entra for live operation. Cloud/external AI, persistent histories, Canvas integration or altered isolation require an explicit approved scope. Open-source ownership/licensing and funding remain unanswered backlog questions.

Institutional references: [UVU FERPA](https://www.uvu.edu/registration/ferpa/index.html), [system procurement](https://www.uvu.edu/biservices/system-procurement-implementation.html), [ATSC](https://www.uvu.edu/biservices/governance.html), [policy manual](https://www.uvu.edu/policies/manual/). Confirm current requirements with UVU.
