# UVU Autograder — Delivery Controls & Acceptance Gates

> **Purpose:** Single source of truth for the Definition of Done (DoD), verification standards, risk-based testing requirements, and launch signoff gates.
> - Product decisions: [decisions.md](../core/decisions.md)
> - Technical contracts: [technical_specs.md](../core/technical_specs.md)
> - Frontend contracts: [frontend_implementation.md](../implementation/frontend_implementation.md)
> - Active roadmap: [backlog.md](backlog.md)

---

## 1. Definition of Done (DoD)

A checklist item or pull request is complete when:

- [ ] **End-to-End Verification:** Feature functions end-to-end in the integrated stack, not merely in isolation.
- [ ] **Code Quality & Linting:** Passes type checking (`tsc` and Python typing) and linters (`ESLint` and `Ruff`) with zero comment suppressions (`// eslint-disable-next-line ...`). Re-exported symbols use explicit `as` or `__all__`.
- [ ] **Automated Test Coverage:** Includes unit and integration test coverage for happy paths and high-risk paths (input validation, rate limiting, zero-retention cleanup, permissions).
- [ ] **Edge Case Handling:** Correctly handles malformed ZIPs, unsafe archive paths (path traversal), missing bundle entrypoints, unmatched student filenames, non-`@uvu.edu` log-ins, execution timeouts, and workspace cleanup failures.
- [ ] **Zero-Retention & Slot Safety Compliance:** Deletion of temporary student code, extracted workspaces, and Judge0 execution artifacts is verified by automated test assertions. All concurrency slot reservations are guarded by top-level `try...finally` blocks.
- [ ] **On-Prem Host Evidence:** Code changes affecting execution or system capacity include host evidence (or documented spot-check logs) prior to marking complete.
- [ ] **Documentation Parity:** Updated relevant specifications in `docs/` and `.agents/memory/context.md` if interfaces, setup, or behaviors changed.

---

## 2. Risk-Based Testing Matrix

| Subsystem / Area | Verification Standard & Required Coverage |
| :--- | :--- |
| **Archive Ingestion & Bundle Safety** | Unit tests verifying safe path extraction, zip-slip rejection, malformed ZIP handling, assignment `config_json` schema validation, and Canvas filename matching. |
| **Execution Engine & Runner** | Integration tests covering AST concept checking, `execute_pytest_in_judge0` runner generator, test timeouts (30s limit), and immediate `DELETE /submissions/{token}` execution. |
| **Student Sandbox Flow** | End-to-end tests for unauthenticated course/assignment discovery, rate-limiting (`warn@40` / `reject@50`), projected scoring results, `visual-diff-viewer`, and immediate post-run cleanup. |
| **Official Batch Runs** | End-to-end tests for staff Canvas ZIP ingest, section permission checks, transient Redis run status (`GET /runs/{id}/status`), CSV grade exports, and ≤24h workspace cleanup. |
| **FERPA & Privacy Guardrails** | Automated assertions confirming that persistent DB tables (`RunSummary`), long-lived logs, and AI payloads do not store student code, names, identifiers, or tracebacks. |
| **Capacity & Backpressure** | Stress tests verifying queue admission limits (`warn@40` / `reject@50`), execution slot caps (default 2 slots, max 4), and Celery worker stability under load. |

---

## 3. Launch-Blocking Acceptance Gates

1. **Cleanup Proof Gate:** Automated integration tests must prove that `DELETE /submissions/{token}` runs immediately post-retrieval, Judge0 tokens are un-retrievable, and ephemeral workspaces are wiped.
2. **On-Prem Host Verification:** Dell workstation spot-checks must confirm Kata VM isolation, host Hugepages/CPU pinning stability, and cleanup execution without logging PII or raw student code.
3. **Execution Concurrency Cap:** Bounded Judge0 execution slots defaults to `2`. Raising the cap to `3` or `4` requires benchmark proof showing zero container crashes and clean queue backpressure under mixed synthetic workloads.
4. **Queue Admission Enforcement:** Global queued job cap rejects intake at `50` waiting jobs and warns at `40` across sandbox and official channels.
5. **Sanitized AI Payloads:** Sandbox Local LLM explanation requests must process code only when free of student PII/identifiers. Official-run AI feedback remains explicitly deferred.

---

## 4. In Scope vs. Explicit Non-Goals

### In Scope for Active Development
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
