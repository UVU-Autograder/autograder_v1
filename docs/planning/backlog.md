# UVU Autograder — Active Development Backlog

> Product goal: on-prem retention-aware Python grading with a public student sandbox, staff assignment setup, and official Canvas ZIP runs. Sandbox and execution artifacts have immediate cleanup boundaries; official review/export data has a ≤24h maximum retention contract.
> Core POC workflows are implemented. Next milestone: a controlled course pilot, subject to the launch gates below. Updated 2026-09-21 with local frontend verification below; Dell rollout and host verification remain pending.

## Source of Truth

- [decisions.md](../core/decisions.md) — product and policy decisions
- [storage_and_test_plan.md](../implementation/storage_and_test_plan.md) — assignment config, artifacts, pytest scoring
- [technical_specs.md](../core/technical_specs.md) — runtime contracts and system behavior
- [frontend_implementation.md](../implementation/frontend_implementation.md) — routes and UI contracts
- [delivery_controls.md](delivery_controls.md) — Definition of Done and acceptance gates

When a checklist item repeats a policy or runtime rule, treat the linked canonical document as authoritative and update that document first.

## Operating Guidelines

Refer to [delivery_controls.md](delivery_controls.md) for Definition of Done (DoD), verification standards, and zero-retention / FERPA acceptance gates. Refer to [.agents/memory/context.md](../../.agents/memory/context.md) for operational domain vocabulary. Do not reintroduce purged topics without a new product decision.

---

## Active — Controlled Course Pilot

Priority order: P0 correctness, retention, authentication, deployment, and institutional gates; then P1 operational and course acceptance. Owners and target dates remain to be assigned. Use the evidence labels in [delivery_controls.md](delivery_controls.md); implementation alone does not close validation work.

### P0 — Official Batch Scheduling and Capacity
- [ ] Replace whole-batch queue reservation with bounded dispatch that admits a 200-submission batch while preserving the global warn-at-40 / reject-at-50 waiting-execution policy and default two active execution slots. Define intake limits for retained batch work separately from dispatch capacity.
- [ ] Remove the conflict between whole-batch tasks and inherited Celery 120s soft / 180s hard limits; prove long batches complete and individual submissions remain bounded.
- [ ] Define Redis-outage behavior that preserves global admission safety instead of silently using independent process-local counters; recover reservations after crashes/restarts and prevent duplicate grading/export side effects on retry.
- [ ] Verify mixed official/sandbox scheduling prevents starvation. Include timeouts, task interruption, broker interruption, and concurrent uploads; assert slot release and eventual terminal status.
- [ ] Close the actual 200-submission grading and export benchmarks in the workstation section below after these changes.

### P0 — Retention Deadline and Cleanup Reliability
- [x] Implement the ≤24h official review/export lifecycle: review access ends at 23h, expiry is derived from intake, expired access is blocked, and physical deletion is verified.
- [x] Replace suppressed directory-deletion failures with a durable tombstone, retryable cleanup state, sanitized failure reporting, and staff/admin visibility.
- [x] Add an independent cleanup worker with startup reconciliation, 60-second sweeps, orphan detection for recognized official paths, cross-process locks, database fail-closed behavior, and restart-safe retries.
- [x] Add local integration coverage for success, failure, timeout/cancellation paths, partial deletion, exact expiry, service/database/Redis outages, orphan safety, symlink safety, and lock release.
- [ ] Complete the retention maintenance runbook and Dell rollout: stop intake, drain workers, apply the migration with deadlines backfilled from original `created_at`, and run startup reconciliation before reopening intake. Classify existing artifacts by their original age.
- [ ] Record synthetic Dell-host evidence for startup recovery, physical workspace/ZIP/export deletion, failure visibility, and cleanup independence from Celery/Redis. Verify Judge0 tokens become unretrievable and execution artifacts are removed immediately; local tests do not close this gate.
- **Rollout access:** Target is `dev@10.115.20.200`; the last SSH attempt failed authentication (`Permission denied (publickey,password)`). Host rollout remains blocked until working SSH access is available.

### P0 — Production Staff Authentication (Microsoft Entra ID / NextAuth)
- [ ] Implement institutional Microsoft sign-in and server-side verification of token signature, issuer, audience, tenant, and expiry. A client email suffix check or forwarded claim fields alone are insufficient.
- [ ] Map verified identities to active `users` / `staff_access` grants. Do not automatically grant instructor authority based only on a university email; an optional pending account carries no staff privileges.
- [ ] Disable mock login for live deployment and fail startup on development secrets or incompatible auth configuration. Preserve explicit isolated-development support.
- [ ] Verify denied tenants, inactive users, missing/revoked grants, section boundaries, logout, and session expiry across API and browser flows.
- **Proposed integration:** NextAuth with Entra ID, followed by a backend-verified token exchange if required. `/auth/microsoft-login` and `AUTH_PROVIDER=microsoft` are proposed interfaces, not existing functionality; finalize them with the implementation and regenerate API documentation.

### P0 — Reverse Proxy & Single-Origin Deployment (Nginx / Caddy)
- [ ] Deploy reverse proxy on port 80/443:
  - Reserve `/api/*` for FastAPI, stripping `/api` before forwarding to existing backend routes (`127.0.0.1:8000`).
  - Route all remaining page paths to Next.js (`127.0.0.1:3000`), including `/staff/*` and `/sandbox/*`; these prefixes overlap backend routes and must not be forwarded wholesale to FastAPI.
  - Update API clients, streaming feedback, downloads, health checks, and API documentation URLs for the public `/api` prefix. Remove port-specific CORS workarounds after same-origin verification.
  - Prepare configuration for UVU institutional TLS/SSL termination.
- [ ] Restrict direct backend, Postgres, Redis, and Judge0 exposure to required internal/host access, preserving Kata connectivity. Replace POC credential defaults and document secret provisioning/rotation.
- [ ] Verify page refresh/deep links, sign-in, uploads, polling, AI streaming, and both exports through the TLS endpoint.

### P0 — Institutional Live-Use Gate
- [ ] Record completion of UVU Software Approval and approved workflow/data scope before live-course deployment. The canonical [institutional status](../core/ferpa_analysis.md) remains in progress; technical readiness does not close this gate.
- [ ] Record release signoff against [delivery_controls.md](delivery_controls.md), including any separately approved local-AI scope. Use synthetic or approved anonymized fixtures for release validation.

### P1 — Repeatable Verification and Operations
- [x] Fix React effect errors in course-section management and student inspection. Dialog sessions now reset on reopen or record changes, ignore late file/section-list responses from previous sessions, and preserve unsaved grading feedback during same-student polling updates.
  - *Local evidence (2026-09-21):* Uncommitted working tree based on `93fcaf0`; from `frontend/`, `npm run lint` passed without warnings, `npm run type-check` passed, `npm run test` passed all 50 tests across 12 files (including six new dialog lifecycle regressions), and `npm run build` passed with the existing multiple-lockfile warning tracked below. This is local component coverage, not browser/host acceptance.
- [ ] Add a repeatable CI/check entry point for backend tests, frontend tests/build/type/lint checks, and generated schema drift. Keep real Judge0/Kata checks as a separately documented integration/host stage.
- [ ] Resolve the previously identified repository-wide Python typing errors in seeds/tests before treating full backend typing as a passing check; changed application-source checks do not close this task.
- [ ] Set and verify the intended Next.js file-tracing root for the repository/frontend package layout; the production build currently warns about multiple lockfiles.
- [ ] Add integrated browser acceptance for assignment setup, sandbox results, official ingest/review, manual-score export gating, CSV/HTML exports, and expired-workspace behavior.
- [ ] Write an operator runbook covering startup/dependency health, queue stalls, failed-run retry, cleanup alerts, scheduler downtime, credentials, upgrades/rollback, and responsible operator/escalation contacts.
- [ ] Define backup scope for persistent course/config/artifact metadata and instructor-owned assets; exclude ephemeral student data. Demonstrate restore and migration recovery without restoring expired submissions, broker payloads, or exports.
- [ ] Attach dated, commit-specific evidence to prior host reports; leave unknown dates/revisions explicit. Record workload, configuration, commands, measured outcomes, and a sanitized evidence link for new runs.
- [x] Add a quiesced Redis task-result purge helper with dry-run default and explicit confirmation for deletion.
- [ ] During host maintenance, inspect the target Redis database, run the helper dry-run, then apply it only after intake is stopped and workers are drained. Complete and execute the procedure to regenerate enabled Redis persistence files, verify legacy application task results are gone, and preserve broker queues and unrelated keys. Any backup must follow the approved scope that excludes student data.

---

## Active — Ops and workstation validation

Prior POC reports below describe the Dell Pro Max Tower T2 (Intel Core Ultra 7 265, 32GB RAM, RTX PRO 4500 GPU, Ubuntu 24.04 LTS, IP `10.115.20.200`). Checked items preserve those historical reports; their execution dates, commit IDs, and raw evidence links were not recorded here and have not been reverified in this documentation update. They are not release signoff.

- [x] Official run with a realistic class-size dataset (30–50 submissions).
  - *Evidence:* Executed Run 1 with 35 synthetic submissions on `cs1400/simple-python-functions`; all 35 scored and individual HTML feedback packages generated.
- [ ] Validate an actual 200-submission official batch completes within 40 min on the Dell workstation, with mixed representative assignments and concurrent sandbox traffic.
  - *Prior measurement:* 35 simple synthetic submissions completed in 76.2s (~2.17s / submission). The ~7.2-minute estimate for 200 is a projection, not validation. Blocked by current admission and batch task-lifetime limits.
- [ ] Validate export packaging overhead under 2 min for an actual 200-submission run after grading completes; verify CSV rows, scores, and all feedback files.
  - *Prior measurement:* CSV export took 0.044s and feedback ZIP packaging took 0.089s for 35 HTML files. This does not close the 200-submission gate.
- [x] Validate Kata-backed VM isolation is active in the planned execution environment.
  - *Evidence:* Kata 3.x `containerd-shim-kata-v2` registered in Docker daemon, executed Judge0 workers with non-privileged capability scoping (`privileged: false` + `SYS_ADMIN`, `SYS_RESOURCE`, etc.), verified active shims during grading.
- [x] Validate on-prem local LLM serving (Ollama/vLLM) on the Dell workstation.
  - *Evidence:* Ollama active via systemd serving `qwen2.5-coder:7b` on RTX PRO 4500 Blackwell GPU with 0.37s–0.93s latency per request.
- [x] Smoke test on the Dell-workstation deployment.
  - *Evidence:* Next.js frontend serving on `http://10.115.20.200:3000` via `autograder-frontend.service`; FastAPI backend serving on `http://10.115.20.200:8000/health`; CORS headers verified across LAN; mock login authenticating `dev.staff@uvu.edu`.
- [x] Review deployment configuration.
  - *Evidence:* Reconciled `docker-compose.poc.yml` (`celery-beat`, `LOCAL_LLM_MODEL`, `CORS_ALLOWED_ORIGINS`), `docker-compose.kata.yml`, `package.json` (`docker:up:kata`), and deployment documentation.
- [x] Update README with deployment and operating notes.
  - *Evidence:* Added Kata run commands, service unit references, and workstation endpoints to `README.md`.

---

## Course Modeling Status

- [x] **CS 1410 (Object-Oriented Programming): Assignment seeds and test suites implemented**
  - All 12 modules (`m1`–`m12`) cataloged in `backend/app/db/seeds/cs1410_catalog.json`.
  - Complete assignment seeds and test suites implemented: Labs 1–7 (`lab_1_image_processing`, `lab2`–`lab7`) and Dessert Shop projects 1–10 (`ds1`–`ds10`).
  - Active section `67890` seeded with automated pytest scoring configurations, support files, and starter bundles.
- [ ] **P1 — CS 1410 grading calibration:** For every assignment, compare instructor-expected per-item and total scores against representative correct, partially correct, and incorrect synthetic solutions. Include alternate valid implementations, concept restrictions, visual/manual criteria, and exported feedback. Record instructor signoff; seed completeness alone is not grading acceptance.
- [ ] **CS 1400 (Fundamentals of Programming): Placeholder**
  - Currently contains only synthetic placeholder assignment (`simple-python-functions`, section `12345`).
  - Awaiting official UVU CS 1400 syllabus, assignment specifications, and test suites before full modeling.

---

## Deferred Architecture Proposals — After Pilot Readiness

The following are design proposals, not implemented capabilities or approved live-data workflows. Official AI, Canvas automation, and additional languages remain outside the pilot milestone.

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

### 2. Additional Deferred Items
- [ ] Configuration Schema Versioning & Migration Pipeline (Deferred while in testing stage without active live assignments).
- [ ] Canvas automated feedback upload / distribution (manual Canvas grade CSV import remains assumed).
- [ ] Multi-language or compiled-language execution pipelines beyond current Python Judge0 path.
