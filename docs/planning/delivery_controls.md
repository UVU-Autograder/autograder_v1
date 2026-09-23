# UVU Autograder — Delivery Controls & Acceptance Gates

> **Purpose:** Single source of truth for the Definition of Done (DoD), verification standards, risk-based testing requirements, and launch signoff gates.
> - Product decisions: [decisions.md](../core/decisions.md)
> - Technical contracts: [technical_specs.md](../core/technical_specs.md)
> - Frontend contracts: [frontend_implementation.md](../implementation/frontend_implementation.md)
> - Active roadmap: [backlog.md](backlog.md)

---

## Evidence and Status Labels

Track these independently; none implies the next:

| Label | Required evidence |
| :--- | :--- |
| **Implemented** | Code/configuration exists at an identified commit; not a claim that checks passed. |
| **Automatically tested** | Dated test command, result, scope, and commit; distinguish mocks from integrated services. |
| **Host verified** | Dated host/configuration, commit, workload, commands, measured outcomes, and sanitized evidence link. |
| **Approved for live use** | Recorded institutional approval scope plus release acceptance signoff and responsible owner. |

Projections must remain labeled as projections. A smaller workload does not close a larger workload's acceptance gate. Preserve historical reports with unknown dates/revisions explicitly marked; do not invent missing evidence. Keep student identifiers, code, credentials, and raw sensitive payloads out of retained evidence.

The next milestone is a controlled course pilot. The [backlog](backlog.md) tracks open work; the retention contract remains immediate sandbox cleanup after results, immediate execution-artifact cleanup after retrieval, and official review/export deletion within 24 hours or on earlier staff cleanup.

## 1. Definition of Done (DoD)

A checklist item or pull request is complete when:

- [ ] **End-to-End Verification:** Feature functions end-to-end in the integrated stack, not merely in isolation.
- [ ] **Code Quality & Linting:** Passes type checking (`tsc` and Python typing) and linters (`ESLint` and `Ruff`) with zero comment suppressions (`// eslint-disable-next-line ...`). Re-exported symbols use explicit `as` or `__all__`.
- [ ] **Automated Test Coverage:** Includes unit and integration test coverage for happy paths and high-risk paths (input validation, rate limiting, zero-retention cleanup, permissions).
- [ ] **Edge Case Handling:** Correctly handles malformed ZIPs, unsafe archive paths (path traversal), missing bundle entrypoints, unmatched student filenames, non-`@uvu.edu` log-ins, execution timeouts, and workspace cleanup failures.
- [ ] **Zero-Retention & Slot Safety Compliance:** Deletion of temporary student code, extracted workspaces, and Judge0 execution artifacts is verified by automated test assertions. All concurrency slot reservations are guarded by top-level `try...finally` blocks.
- [ ] **On-Prem Host Evidence:** Code changes affecting execution or system capacity include host evidence (or documented spot-check logs) prior to marking complete.
- [ ] **Documentation Parity:** Updated relevant specifications in `docs/` and `.agents/memory/context.md` if interfaces, setup, or behaviors changed.

### 1.1 Standard Verification Suites & Tooling

Every pull request or release milestone must execute and pass the standardized local verification commands:

- **Unified Quality Gate (`npm run check`):**
  Cross-platform entry point via `scripts/run_checks.ps1` (PowerShell) and `scripts/run_checks.sh` (POSIX). Executes 7 sequential checks:
  1. `Backend Linting`: `ruff check app tests` (zero lint warnings/errors).
  2. `Backend Type Checking`: `mypy backend/app` (strict static typing across all 83 backend domain files).
  3. `Backend Unit Tests`: `pytest tests/unit -q` (all unit test assertions passing).
  4. `Database Schema Drift`: `alembic check` (verifies 0 unmigrated schema drift against models).
  5. `Frontend Type Checking`: `tsc --noEmit` (strict TypeScript validation).
  6. `Frontend Linting`: `eslint` (zero lint violations).
  7. `Frontend Unit Tests`: `vitest run` (all React component/dialog lifecycle tests passing).

- **Browser Acceptance Suite (`npm run test:e2e`):**
  Playwright E2E browser acceptance suite configured in `frontend/playwright.config.ts`. Automatically manages dual `webServer` lifecycles (FastAPI on port 8000, Next.js on port 3000):
  - `frontend/e2e/staff-auth.spec.ts`: Unauthenticated route guards, session timeout displays, institutional email domain restrictions, local mock login, and Microsoft Entra ID handoff cookie processing.
  - `frontend/e2e/sandbox.spec.ts`: Public catalog discovery, assignment list metadata, interactive workspace loading, and live test/score projection.
  - `frontend/e2e/official-review.spec.ts`: Official submission cohort review, "Needs Grading" rubric filtering, interactive student inspection dialog with manual grading saves, and grades CSV / feedback ZIP export button access.

- **Metadata Backup Automation:**
  - `scripts/backup_metadata.ps1` / `scripts/backup_metadata.sh`: Dumps persistent configuration, course structure, and assignment artifacts while strictly excluding ephemeral student runs, submissions, and container workspaces.

---

## 2. Risk-Based Testing Matrix

| Subsystem / Area | Verification Standard & Required Coverage |
| :--- | :--- |
| **Archive Ingestion & Bundle Safety** | Unit tests verifying safe path extraction, zip-slip rejection, malformed ZIP handling, assignment `config_json` schema validation, Canvas filename matching, `_LATE_` variants, and Canvas version suffix normalization. |
| **Execution Engine & Runner** | Integration tests covering AST concept checking, `execute_pytest_in_judge0` runner generator, test timeouts (30s limit), immediate `DELETE /submissions/{token}` execution, and immediate deletion of `ag_grade_*` execution workspaces. |
| **Student Sandbox Flow** | End-to-end tests for unauthenticated course/assignment discovery, rate-limiting (`warn@40` / `reject@50`), projected scoring results, `visual-diff-viewer`, and immediate post-run cleanup. |
| **Official Batch Runs** | End-to-end tests for staff Canvas ZIP ingest, section permission checks, transient Redis run status (`GET /runs/{id}/status`), CSV grade exports, per-student review workspace retention during the review window, and ≤24h workspace cleanup. |
| **FERPA & Privacy Guardrails** | Automated assertions confirming that persistent DB tables (`RunSummary`), long-lived logs, and AI payloads do not store student code, names, identifiers, or tracebacks; ephemeral official workspaces may contain identifying review data only within the ≤24h window; structured audit logs use allowlisted fields plus log redaction filters. |
| **Capacity & Backpressure** | Stress tests verifying queue admission limits (`warn@40` / `reject@50`), execution slot caps (default 2 slots, max 4), and Celery worker stability under load. |

---

## 3. Launch-Blocking Acceptance Gates

1. **Cleanup Proof Gate:** Automated integration tests must prove that `DELETE /submissions/{token}` runs immediately post-retrieval, Judge0 tokens are un-retrievable, and ephemeral workspaces are wiped.
2. **On-Prem Host Verification:** Dell workstation spot-checks must confirm Kata VM isolation, host Hugepages/CPU pinning stability, and cleanup execution without logging PII or raw student code.
3. **Execution Concurrency Cap:** Bounded Judge0 execution slots defaults to `2`. Raising the cap to `3` or `4` requires benchmark proof showing zero container crashes and clean queue backpressure under mixed synthetic workloads.
4. **Queue Admission Enforcement:** Global queued job cap rejects intake at `50` waiting jobs and warns at `40` across sandbox and official channels.
5. **Sanitized AI Payloads:** Sandbox Local LLM explanation requests must process code only when free of student PII/identifiers. Official-run AI feedback remains explicitly deferred.
6. **Official Retention Enforcement:** Prove deletion by the ≤24h deadline and on explicit staff cleanup. Test deletion failure, orphaned files, and worker/scheduler restart; verify removal, expose sanitized failures, and document downtime limitations. Hourly dispatch or successful task return alone is insufficient proof.
7. **Batch Capacity and Fairness:** An actual 200-submission batch must enter the system, finish within 40 min, and package exports within 2 min after grading. Use representative synthetic workloads alongside sandbox traffic; verify timeouts, bounded dispatch, no starvation, Redis-outage handling, reservation recovery, and retry behavior without duplicate grading side effects.
8. **Identity and Deployment:** Verify institutional staff identity and explicit active grants; disable mock login and development secrets. Verify TLS and the `/api/*` proxy contract without intercepting frontend pages, and restrict direct service exposure.
9. **Institutional Authorization:** Record UVU approval for the live official workflow and its approved data/infrastructure scope. Local-AI authorization is separate where applicable; no technical test substitutes for approval.
10. **Pilot Acceptance and Recovery:** Record instructor grading calibration for assignments included in the pilot, integrated staff/student browser acceptance, operator ownership, and a restore rehearsal limited to permitted persistent data and instructor assets.

---

## 4. In Scope vs. Explicit Non-Goals

### In Scope for Active Development
- Pilot-readiness fixes for bounded batch scheduling, retention enforcement, institutional staff authentication, single-origin deployment, and operational recovery.
- Course grading calibration and repeatable automated/integrated acceptance evidence.
- Ephemeral manual rubric grading for visual/pixel assignment criteria.
- Sandbox Local LLM pedagogical feedback (PII-safe, on-screen only).
- Section-scoped staff authorization and monitoring.
- Dell workstation Kata container deployment & validation.

### Explicit Non-Goals (Purged / Deferred)
- Canvas LTI or automated Canvas API feedback upload/write-backs.
- Persistent student submission history or saved sandbox run timelines.
- Central multi-user shared grading grids or edit-locking concurrency primitives.
- Downloadable student sandbox artifacts.
- Multi-language or compiled language execution outside Python 3.11+.
