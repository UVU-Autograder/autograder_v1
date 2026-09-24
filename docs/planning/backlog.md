# UVU Autograder — Active Development Backlog

> **Product Goal:** On-prem, retention-aware Python grading with a public student sandbox, staff assignment setup, and official Canvas ZIP runs. Sandbox and execution artifacts have immediate cleanup boundaries; official review/export data has a ≤24h maximum retention contract.
> **Deployment Status:** Dell workstation (`10.115.20.200`) deployment active with Kata-isolated execution, bounded batch scheduling, independent cleanup worker, Nginx reverse proxy (port 80), and Microsoft Entra ID authentication.
> **Next Milestone:** Institutional UVU software approval, TLS certificate deployment, instructor grading calibration, and controlled course pilot.

## Source of Truth & Completed Foundations

The following subsystems are implemented, verified, and canonically documented:

- **Bounded Dispatch & Scheduling:** [bounded_dispatch_rollout.md](../deployment/bounded_dispatch_rollout.md)
- **Retention Lifecycle & 24h Cleanup:** [retention_rollout.md](../deployment/retention_rollout.md)
- **Host Deployment & Kata Isolation:** [workstation_deployment.md](../deployment/workstation_deployment.md) & [operator_runbook.md](../operations/operator_runbook.md)
- **Staff Authentication (Microsoft Entra ID):** [technical_specs.md §6](../core/technical_specs.md#6-authentication-and-session-architecture) & [frontend_implementation.md](../implementation/frontend_implementation.md)
- **Quality Gates & Verification Suites:** [delivery_controls.md §1.1](delivery_controls.md#11-standard-verification-suites--tooling)
- **Backup & Disaster Recovery:** [backup_and_recovery.md](../operations/backup_and_recovery.md)
- **CS 1410 Assignment Modeling:** [cs1410_assignments_spec.md](../modeling/cs1410_assignments_spec.md)

---

## Active Backlog — Controlled Course Pilot

> [!IMPORTANT]
> **Backlog Lifecycle Rule:** When a backlog item is complete, do not persist it in this file. Instead, record the outcome, configuration, or architectural details in the relevant documentation (`docs/`) if helpful, otherwise discard it. This file tracks only active, actionable items.

Priority order: Institutional software gates, TLS deployment verification, and instructor course acceptance. Refer to [delivery_controls.md](delivery_controls.md) for Definition of Done and required evidence labels.

### P0 — Institutional Live-Use Gate

- [ ] **UVU Software Approval & Data Scope:** Record formal completion of institutional UVU Software Approval and approved workflow/data scope before live-course deployment. Canonical analysis in [ferpa_analysis.md](../core/ferpa_analysis.md); technical readiness alone does not close this gate.
- [ ] **Pilot Release Signoff:** Record release signoff against [delivery_controls.md](delivery_controls.md), including responsible operators and separately approved local-AI scope. Use synthetic or approved anonymized fixtures for release validation.

### P0 — Production Deployment & TLS Verification

- [ ] **End-to-End TLS Endpoint Verification:** Verify page refresh/deep links, Microsoft Entra ID sign-in, bundle uploads, polling, AI streaming, and CSV/ZIP exports through the institutional TLS endpoint (`https://...` on port 443) once campus certificates are installed on the workstation.
- [ ] **Workstation `.env` Hardening (Azure AD Credentials):** Add institutional `AZURE_AD_CLIENT_ID`, `AZURE_AD_TENANT_ID`, and `AZURE_AD_CLIENT_SECRET` to workstation `.env` once Entra ID app registration is issued by UVU IT. (All non-credential variables, network bind IPs, and 60m expiry are already synchronized).

### P1 — Testing & Verification

- [ ] **Entra ID Integration Test:** Perform end-to-end Microsoft Entra ID sign-in on the workstation with real Azure AD credentials. Verify PKCE flow, session token issuance, staff gating (provisioned vs unprovisioned), and session expiration. Requires Azure AD app registration.

### P1 — Course Modeling & Grading Acceptance

- [ ] **CS 1400 Syllabus & Assignment Modeling:** Implement assignment seeds and test suites for CS 1400 (Fundamentals of Programming) upon receipt of official UVU syllabus and assignment specifications (replaces placeholder assignment `simple-python-functions`).

---

## Deferred Architecture Proposals — After Pilot Readiness

The following are forward-looking proposals, not implemented capabilities or approved live-data workflows. Official AI, Canvas automation, and additional languages remain outside the pilot milestone.

### 1. Official-Run Opt-In Local LLM Feedback
- **Goal:** On-prem, private AI coaching integrated into official Canvas ZIP grading runs, powered by the workstation's local `qwen2.5-coder:7b` model.
- **Privacy & Retention Constraints:**
  - Student identifiers (name, canvas_user_id, submission_id, file header comments, author tags) must be strictly stripped before prompt synthesis.
  - Only ephemeral in-memory prompt generation; no prompt caching or logging containing student code.
  - Test suites must verify with negative assertions that no raw PII or student filenames are passed to the Local LLM client.
  - Skip AI feedback when payloads may remain personally traceable; identifier stripping alone does not establish anonymization or institutional authorization.
- **Workflow & UI Contract:**
  - **Ingest Opt-In:** Checkbox on the staff run creation page: `"Generate Local AI Coaching Feedback"`, defaulting to unchecked.
  - **Task Pipeline:** In `grade_official_run` (Celery), if enabled, invoke `generate_student_ai_feedback` sequentially or bounded-concurrently after pytest evaluation completes.
  - **Failure Handling:** LLM timeout or error must never fail the official run; missing AI comments log an audit event and cleanly fallback to standard score report.
- **Output Shape:**
  - Distinct `<section class="ai-coaching-section">` in the student's `feedback.html`.
  - Explicit disclaimer: *"AI Coaching generated on-prem by local Qwen2.5-Coder. Grades are determined strictly by automated test criteria."*
  - Generated feedback is included in the staff review dialog where instructors can edit or clear comments before export.

### 2. Additional Deferred Capabilities
- [ ] Configuration Schema Versioning & Migration Pipeline (Deferred while in testing stage without active live assignments).
- [ ] Canvas automated feedback upload / distribution (manual Canvas grade CSV import remains assumed).
- [ ] Multi-language or compiled-language execution pipelines beyond current Python Judge0 path.
