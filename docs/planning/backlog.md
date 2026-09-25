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
- **Sandbox AI Feedback Architecture:** [sandbox_feedback_model_decision.md](../core/sandbox_feedback_model_decision.md) (Gemma 4 12B QAT + `cs1410-p2c` LoRA adapter, deployed as systemd service `vllm-cs1410` on loopback port 8001 with rollback to `gemma4-12b-qat`)

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
- [x] **Student Feedback Delivery Contract:** Resolved: Instructors manually attach per-student HTML feedback files or copy/paste comments into Canvas from the downloaded `feedback.zip` package. Files are not persistently hosted on the autograder server, maintaining strict zero-retention compliance.

---

### P1 — Sandbox AI Feedback Model Go-Live

Decision and evidence: [sandbox_feedback_model_decision.md](../core/sandbox_feedback_model_decision.md). Live use also requires the P0 Institutional Live-Use Gate above. (Note: `vllm-cs1410.service` installation on port 8001 is complete and running on the Dell host).

- [ ] **Staff Spot-Check of `cs1410-p2c`:** Instructors or IAs score ~20 cases in the p2c eval review sheet (`backend/eval/results/p2c-v6-review.md`, each case next to the untuned model; Accurate / Helpful / Tone) and record formal sign-off.

## Deferred Architecture Proposals — After Pilot Readiness

The following are forward-looking proposals, not implemented capabilities or approved live-data workflows. Official AI, Canvas automation, and additional languages remain outside the pilot milestone.

- [ ] On-Prem Local AI Coaching for Official Canvas ZIP Runs (Deferred for pilot; official runs remain strictly AI-free per [decisions.md](../core/decisions.md) and [ferpa_analysis.md](../core/ferpa_analysis.md). Ingest opt-in, strict in-memory PII stripping, and non-blocking failure fallbacks remain defined for future consideration).
- [ ] Configuration Schema Versioning & Migration Pipeline (Deferred while in testing stage without active live assignments).
- [ ] Canvas automated feedback upload / distribution (manual Canvas grade CSV import remains assumed).
- [ ] Multi-language or compiled-language execution pipelines beyond current Python Judge0 path.
