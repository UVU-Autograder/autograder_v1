# UVU Autograder v1 - M1 Delivery Checklist

> Product Goal: deliver a testable M1 for zero-retention grading with staff `@uvu.edu` authentication and globally visible student sandbox access.
> Team: 3 frontend developers and 2 backend developers, part time.

This file is the primary M1 delivery checklist. It tracks implementation work only; detailed product decisions, runtime contracts, frontend contracts, and acceptance gates stay in the source-of-truth docs below.

## Source Of Truth

- [decisions.md](../backend_implementation/decisions.md) - product, policy, and M1 assumption decisions
- [storage_and_test_plan.md](../backend_implementation/storage_and_test_plan.md) - canonical assignment config, artifact storage, and pytest scoring architecture
- [technical_specs.md](../technical_specs.md) - backend/system behavior, data contracts, runtime limits, and deployment shape
- [frontend_implementation.md](../frontend_implementation/frontend_implementation.md) - routes, UI surfaces, and frontend constraints
- [delivery_controls.md](delivery_controls.md) - review cadence, Definition of Done, and M1 scope boundaries

When a checklist item repeats a policy or runtime rule, treat the linked canonical document as authoritative and update that document first.

## Overall Deliverables

| Done | Deliverable                                                             | Completion Evidence                                                                                                                                          |
| ---- | ----------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| [ ]  | Shared architecture and frontend/backend contracts are confirmed        | Team can explain the backend/frontend boundary, shared routes, API responsibilities, and current diagram set.                                                |
| [ ]  | Local stack and metadata-only persistence foundation is working         | Developers can run the local stack; Postgres stores only approved metadata tables; Redis/Celery/Judge0 integration path and Compose harness are documented.  |
| [ ]  | Judge0/Kata cleanup proof is established                                | The team has evidence that Judge0 submission/result artifacts and Kata execution state are destroyed after result retrieval.                                 |
| [ ]  | Staff `@uvu.edu` authentication and role boundaries are implemented     | Staff sign-in rejects non-UVU accounts; admin, instructor, and IA access rules are enforced.                                                                 |
| [ ]  | Admin course, section, staff, and monitoring workflows are usable       | Admins can manage courses, sections, access grants, and admin-only operational monitoring for token usage, upload limits, and worker/capacity status.        |
| [ ]  | Assignment setup and canonical `config_json` are usable                 | Staff can create or open an assignment, edit setup through the wizard, define ZIP/project bundle requirements, define visible scoring items, and persist validated internal config. |
| [ ]  | Assignment artifact management is usable                               | Staff can manage the single assignment pytest file, model solutions, and support files through local filesystem-backed `assignment_artifacts` storage references. |
| [ ]  | Ephemeral Canvas ZIP ingest is implemented                              | Staff can upload a Canvas ZIP containing single-file or multi-file student bundles; malformed archives, path traversal, and unmatched filenames surface actionable errors without persistent student submissions. |
| [ ]  | Grading chain works with AST checks, Judge0/Kata execution, and cleanup | Official and sandbox grading can run through AST checks, Judge0/Kata execution, structured results, and post-result cleanup.                                 |
| [ ]  | Safe Judge0/Kata worker caps are documented                             | Dell-workstation benchmarking defines approved grading worker caps before grading-pipeline implementation begins.                                            |
| [ ]  | Queue admission and wait UX are usable                                  | The system accepts work asynchronously, warns at high load, rejects full queues cleanly, and shows queue position/ETA without exceeding execution caps.       |
| [ ]  | Azure feedback is available only after privacy confirmation             | Written UVU approval and Azure resource/privacy confirmation are complete before live student-code AI feedback is enabled.                                  |
| [ ]  | Public sandbox workflow is usable                                       | A sandbox user can select an enabled course and assignment, upload a ZIP/project bundle, see a sanitized file tree, quota state, read-only preview, and on-screen projected feedback. |
| [ ]  | Official review and export workflow is usable                           | Staff can monitor an official run, inspect derived/ephemeral read-only previews while available, and download separate Canvas-grade CSV and per-student feedback ZIP outputs. |
| [ ]  | Compliance hardening and realistic end-to-end validation are complete   | Access control, cleanup, Azure readiness, performance targets, fake/synthetic or completely anonymized validation data handling, and Canvas-shaped format assumptions are validated. |

## Operating Guidelines

- Work through the checklist in priority order when dependencies allow.
- Keep assigned work small enough for a student developer to complete in a focused day when possible.
- Review progress weekly against this checklist and the Definition of Done in [delivery_controls.md](delivery_controls.md).
- Adjust assignments based on actual student availability, exams, jobs, vacations, and skill bottlenecks.
- Prefer completing fewer end-to-end deliverables over starting many disconnected tasks.
- Reduce scope before weakening zero-retention, FERPA, authentication, or cleanup safeguards.

## Detailed M1 Checklist

### Architecture And Shared Contracts

- [ ] Review ER diagram as the current persistent-data reference.
- [ ] Review class and pipeline diagrams as current workflow references.
- [ ] Confirm FastAPI router skeleton and request/response boundaries.
- [ ] Confirm prompt integration boundaries.
- [ ] Review staff and sandbox wireframes.
- [ ] Review frontend route structure and component hierarchy.
- [ ] Review shared API and UI contracts before dependent feature work proceeds.
- [ ] Capture implementation action items that block shared-contract signoff.

### Environment And Metadata Foundation

- [ ] Agree on repo structure with `/frontend` for Next.js and `/backend` for FastAPI.
- [ ] Bootstrap the Next.js app using the App Router.
- [ ] Bootstrap the FastAPI app with routers, schemas, services, and prompt integration boundaries.
- [ ] Add PostgreSQL schema and Alembic initial migration for metadata-only tables.
- [ ] Include metadata tables for users, roles, courses, sections, staff access, assignments, assignment configs, assignment concepts, assignment artifacts, test cases, scoring_items, and run summaries.
- [ ] Run Redis locally.
- [x] Wire Celery to Redis.
- [ ] Make the Judge0 execution service reachable from the backend integration path.
- [ ] Document Judge0 service auth and config wiring for FastAPI and Celery.
- [ ] Validate Kata runtime requirements for the planned Judge0 isolation layer.
- [ ] Document Dell-workstation deployment shape for Next.js, FastAPI, Postgres, Redis, Celery, Judge0, and Kata integration.
- [ ] Support local development and integration-style testing through Docker Compose for Postgres, Redis, Celery, FastAPI, Next.js, and the chosen Judge0 test topology.
- [ ] Validate that `docker-compose.testing.yml` remains documented as an integration harness even where local machines cannot fully reproduce the planned Kata isolation setup.
- [ ] Document and validate Judge0/Kata cleanup according to the canonical zero-retention contract, including deletion failure as launch-blocking for live workflows.
- [ ] Implement automated cleanup proof tests for execution-service and workspace artifacts across success, failure, timeout, and exception paths.
- [ ] Collect documented Dell-workstation cleanup spot-check evidence for Judge0, Kata, and local workspace cleanup.
- [ ] Benchmark safe Judge0 + Kata concurrency on the Dell workstation with mixed synthetic workloads and document worker caps before grading-pipeline implementation begins.
- [ ] Configure the M1 execution-slot cap and benchmark any increase according to the canonical capacity policy.
- [x] Document queue and backpressure thresholds for work beyond the approved cap, including `40` queued-job high-load messaging and `50` queued-job rejection.
- [ ] Host Monaco Editor locally in the frontend scaffold for planned editor and review workflows.
- [x] Document required environment variables in `.env.example`, including Azure OpenAI settings.
- [ ] Update README so a developer can bring up the local stack.
- [ ] Add a seed path for one course, course-level `Concepts Covered`, one assignment, assignment concept additions, one app-owned `config_json`, one assignment pytest file, and one model solution.

### Staff Auth And Access Control

- [ ] Configure staff Microsoft OAuth through NextAuth.
- [ ] Reject staff login callbacks that do not end in `@uvu.edu`.
- [ ] Add role-based route protection in Next.js.
- [ ] Add role-based API protection in FastAPI.
- [ ] Support minimal staff role management for admin, instructor, and IA.
- [ ] Add admin course management for creating, editing, and deactivating courses.
- [ ] Add admin section management for creating, editing, and deactivating sections.
- [ ] Add admin staff/user management for assigning instructors and IAs to course or section scopes.
- [ ] Add admin-only monitoring for Azure token usage, sandbox upload-limit state, and worker/capacity status.
- [ ] Keep IA access strict by default and exclude assignment-config authoring in M1.
- [ ] Ensure instructors can view assigned courses and edit only explicitly assigned sections.
- [ ] Ensure IAs can view only explicitly assigned sections for grading validation.
- [ ] Ensure public sandbox users cannot access staff workflow pages or export flows.

### Assignment Setup And `config_json`

- [ ] Add assignment creation with course linkage, due date, and Canvas reference metadata.
- [ ] Build a comprehensive setup wizard for instructor-relevant assignment, rubric, and config fields.
- [ ] Generate valid app-owned `config_json` v1 from the wizard.
- [ ] Validate `config_json` v1 with strict schema-version handling and stable human-readable keys for tests and artifact references.
- [ ] Add assignment-config fields for ZIP/project bundle requirements, including required files, entrypoint, and layout expectations.
- [ ] Validate required files, entrypoint, and layout expectations before model-solution validation or grading.
- [ ] Render all instructor-relevant editable fields from the stored app-owned config.
- [ ] Add `/staff/courses/[courseId]/assignments/[assignmentId]/artifacts` for assignment-owned grading assets.
- [ ] Manage one or more M1 pytest file artifacts per assignment through lightweight `assignment_artifacts` metadata plus generated local filesystem storage keys.
- [ ] Manage model solution artifacts through lightweight `assignment_artifacts` metadata plus generated local filesystem storage keys.
- [ ] Manage support-file artifacts through lightweight `assignment_artifacts` metadata plus generated local filesystem storage keys.
- [ ] Validate artifact metadata before file bodies are used for model-solution validation or grading.
- [ ] Require each visible scoring item key to match a pytest marker named `ag_<key>` in the assignment pytest files.
- [ ] Allow one scoring item to map to multiple pytest functions that share the same `ag_<key>` marker.
- [ ] Run strict preflight validation for duplicate keys, missing derived `ag_<key>` markers, missing assignment pytest artifacts, invalid point values, missing or invalid `extra_credit` booleans, and invalid completion requirements before model-solution validation or grading.
- [ ] Add course-level `Concepts Covered` defaults editor.
- [ ] Add assignment-level `Concepts Covered` additions editor.
- [ ] Show a merged effective `Concepts Covered` preview.
- [ ] Let instructors edit assignment-specific concept additions directly.
- [ ] Keep human-authored grading fields in the app-owned config instead of duplicating them in `TestCase`.
- [ ] Regenerate derived `TestCase` and `ScoringItem` projections from the app-owned config after setup changes where query or UI behavior needs them.
- [ ] Ensure derived `TestCase` projections never become editable grading truth and are reconciled when they disagree with config.
- [ ] Defer any separate simple test-case editor; keep test authoring in the wizard/config and pytest artifact surfaces for M1.

### Ephemeral Canvas ZIP Ingest

- [ ] Add Canvas ZIP upload endpoint with size validation.
- [ ] Add upload type validation.
- [ ] Reject malformed, non-Canvas, or unrecognized ZIPs before queueing.
- [ ] Block ZIP path traversal before extraction.
- [ ] Extract ZIP contents only in RAM or an ephemeral temp directory.
- [ ] Parse Canvas filenames using Canvas-provided identifiers.
- [ ] Support Canvas submissions that contain one ZIP/project bundle per student.
- [ ] Validate each student bundle against assignment-config required files, entrypoint, and layout expectations.
- [ ] Reject missing required files, ambiguous entrypoints, unsupported layouts, and unsafe nested paths with actionable errors.
- [ ] Report unmatched filenames in the staff UI.
- [ ] Report malformed archive failures in the staff UI.
- [ ] Create transient official-run metadata with assignment link, uploader, aggregate status, and file counts only.
- [ ] Avoid persistent storage of raw student submissions, filenames, tracebacks, or detailed failure text.

### AST, Judge0, And Kata Grading Pipeline

- [x] Implement AST checker for merged `Concepts Covered` whitelist enforcement.
- [x] Detect future-concept usage before execution and record warnings per result.
- [x] Support hard-block behavior for configured security-sensitive AST findings.
- [x] Integrate Judge0 through `httpx`.
- [ ] Validate Judge0 auth/config wiring.
- [x] Configure Judge0 resource limits for the M1 target: `10s` timeout, `256MB` memory limit, and network-disabled student execution.
- [x] Implement language-to-Judge0 mapping for the current M1 supported language.
- [x] Run pytest execution through Judge0.
- [x] Parse pytest output into structured test results.
- [x] Normalize output with custom normalizer (replaces `python_submitty_utils` per implementation decision).
- [x] Integrate Judge0 structured status handling into grading outcomes.
- [ ] Capture compile/runtime metadata only for non-persistent grading feedback and status shaping.
- [ ] Upload or edit pytest file bodies through storage-backed assignment artifact references.
- [ ] Run model solutions against assignment tests through Judge0, not on the host.
- [x] Package single-file and ZIP/project bundle submissions into the Judge0 execution workspace without persisting source bodies.
- [ ] Build Celery grading chain for official runs.
- [x] Build Celery grading chain for sandbox runs.
- [x] Align Celery worker concurrency to documented Judge0 + Kata execution capacity.
- [x] Add global queue admission control for a maximum of `50` waiting per-submission execution jobs.
- [x] Add high-load response behavior at `40` queued execution jobs.
- [x] Add full-queue rejection with retry guidance before file persistence at `50` queued execution jobs.
- [x] Add separate logical official and sandbox queues with round-robin scheduling into the bounded execution slots.
- [ ] Chunk official runs internally so large Canvas batches feed per-submission execution jobs as queue capacity opens.
- [x] Add Redis-backed transient run status with `queue`, `run`, `complete`, `failure`, sanitized counters, and coarse failure categories.
- [ ] Add `GET /runs/{id}/status`.
- [ ] Poll run status from staff and sandbox views every `2s` while the run is queued or running.
- [ ] Return queue position and rough ETA band from run status while a job is queued.
- [ ] Allow queued sandbox jobs to be cancelled before execution starts.
- [ ] Finalize worker-cap and backpressure policy from Dell-workstation benchmark results.
- [x] Retry failed jobs up to 3 times with backoff.
- [ ] Free workers immediately on timeout and record `failed:timeout`.
- [x] Verify Judge0 submission/result deletion after each official and sandbox execution.
- [ ] Verify Kata-backed execution artifact deletion after each official and sandbox execution.
- [x] Destroy extracted student files, generated code artifacts, and temporary feedback files at the end of each official or sandbox run.

### Azure Feedback And Privacy Confirmation

- [ ] Confirm Azure OpenAI privacy posture, UVU approval, and launch-blocking evidence before live student-code AI feedback is enabled.
- [ ] Write the Azure/UVU compliance confirmation checklist and approval evidence expectations before go-live.
- [ ] Use UVU-approved Azure OpenAI configuration before sending live student code.
- [ ] Disable Azure feedback for live, pseudonymous, or real student-derived code unless the UVU/Azure approval checklist is complete.
- [ ] Inject allowed-concepts context into the Azure OpenAI prompt.
- [ ] Generate rubric-context explanations and feedback without re-grading correctness.
- [ ] Enforce hallucination guard: tests remain ground truth and the LLM explains rather than re-evaluates.
- [ ] Degrade AI feedback under high queue or resource load by returning grounded test results first and delaying, skipping, or marking AI feedback unavailable.
- [ ] Show auto-populated LLM feedback beside test-case results after each sandbox run.
- [ ] Log Azure token usage in `run_summaries` or equivalent non-sensitive metadata storage.
- [ ] Rotate and purge sensitive debug traces within `24h` if temporary debug traces are enabled.

### Public Student Sandbox

- [ ] Provide public sandbox entry without student authentication.
- [ ] Show globally visible sandbox-enabled courses only.
- [ ] Show globally visible sandbox-enabled assignments only.
- [ ] Add student course list and per-course assignment selection UI.
- [ ] Add student ZIP/project bundle upload flow for supported assignment file formats.
- [ ] Reject loose multi-file drag-and-drop outside the M1 ZIP/project bundle contract.
- [ ] Show sanitized file tree and read-only Monaco preview for the uploaded sandbox bundle.
- [ ] Enforce `5 uploads per hour` per sandbox session.
- [ ] Show remaining uploads in the current hour before and after each run.
- [ ] Handle backend `429` responses with clear limit-reached messaging.
- [ ] Show projected score on screen.
- [ ] Show projected feedback with warnings and test summaries on screen.
- [ ] Show assignment rubric information in the sandbox workspace.
- [ ] Show assignment constraints in the sandbox workspace.
- [ ] Show terminal/output information where grading results include it.
- [ ] Show test-result details with passed/failed counts.
- [ ] Show queued/running status, queue position, and rough ETA band after accepted sandbox uploads.
- [ ] Support same-session sandbox result return with a non-identifying run token for up to `1h`.
- [ ] Support cancellation of sandbox jobs before execution starts.
- [ ] Make zero-retention behavior explicit in student-facing messaging.
- [ ] Clear projected results on sandbox session exit or completion.

### Official Run Review And Export Packaging

- [ ] Add official run list view with assignment, uploader, aggregate status, and section-aware context.
- [ ] Add official run detail view with current processing counts.
- [ ] Show per-student pass/fail state during in-session official review.
- [ ] Show warning and hard-block summaries during in-session official review.
- [ ] Show unmatched filename failures during in-session official review.
- [ ] Support per-student feedback preview before export.
- [ ] Show ephemeral read-only Monaco previews for official submissions while temporary files remain available.
- [ ] Keep official review preview-only in M1 with no feedback editing.
- [ ] Use derived artifacts and structured app data only; do not add raw student-submission download workflows.
- [ ] Add optional filtering by success, warning, hard-block, timeout, and parse failure if capacity allows.
- [ ] Warn staff that detailed official results are ephemeral and will be destroyed after download or request completion.
- [ ] Produce Canvas-compatible grade CSV export.
- [ ] Render per-student staff-facing HTML feedback artifacts.
- [ ] Package per-student HTML feedback artifacts into a per-run ZIP.
- [ ] Provide separate Canvas-grade CSV and feedback-ZIP download actions.
- [ ] Use stable export naming based on assignment identifier plus generated export identifier.
- [ ] Fail safely with actionable errors if packaging is incomplete.
- [ ] Fail fast with actionable errors for malformed or unrecognized ZIP submissions.
- [ ] Document that Canvas grade import is assumed and automated feedback upload is out of scope for M1.

### End-To-End Validation And Compliance Hardening

- [ ] Test an official run with a realistic class-size dataset of 30-50 submissions.
- [ ] Test an official run with multi-file ZIP/project bundles.
- [ ] Test the student sandbox flow end to end from assignment selection through ZIP/project bundle upload, preview, results, and cleanup.
- [ ] Write the risk-based M1 test matrix covering unit, integration, cleanup, FERPA/privacy, and stress scenarios.
- [ ] Apply the documented Judge0/Kata cleanup proof standard for implementation signoff.
- [ ] Validate stored `config_json` v1 rejects missing or unsupported schema versions through wizard/setup saves.
- [ ] Validate strict preflight rejects missing derived `ag_<key>` pytest markers, duplicate config keys, missing assignment pytest artifact, invalid point values, missing or invalid `extra_credit` booleans, and invalid completion-requirement references or thresholds.
- [ ] Validate derived `TestCase` projections are regenerated from canonical config and reconciled when stale rows disagree.
- [ ] Validate artifact storage uses generated opaque keys, preserves filenames only as sanitized display metadata, and stores file bodies outside web-served paths.
- [ ] Validate run status responses expose only sanitized counters and coarse failure categories.
- [ ] Validate synthetic Canvas ZIP/CSV fixtures and any completely anonymized Canvas-shaped samples before treating ingest/export as dependable.
- [ ] Build or collect only fake/synthetic or completely anonymized Canvas-shaped samples for M1 validation.
- [ ] Build synthetic Canvas fixtures for malformed ZIPs, path traversal, ambiguous filenames, unmatched files, multi-file submission bundles, and grade CSV shape.
- [ ] Define an M1 validation-data checklist that excludes live, pseudonymous, or re-identifiable student data before app upload.
- [ ] Validate ZIP upload acceptance under `2s` for files up to `50MB`.
- [ ] Validate `200` official submissions complete within `40 min` on the Dell workstation.
- [ ] Validate status polling responses under `200ms`.
- [ ] Validate queue admission at `39`, `40`, `49`, and `50` queued execution jobs.
- [ ] Validate full-queue rejection includes retry guidance and does not persist uploaded files.
- [ ] Validate official batches larger than available queue capacity are chunked safely.
- [ ] Validate round-robin fairness when official and sandbox queues both have waiting jobs.
- [ ] Validate queued sandbox cancellation frees queue capacity and cleans temporary artifacts.
- [ ] Validate queue status includes position and rough ETA band without sensitive fields.
- [ ] Validate export packaging overhead under `2 min` for `200` submissions after grading completes.
- [ ] Validate `@uvu.edu` staff login succeeds.
- [ ] Validate non-UVU staff login is rejected.
- [ ] Validate public sandbox visibility shows only sandbox-enabled assignments.
- [ ] Validate public sandbox does not require student login or UVU ID entry.
- [ ] Validate admin, instructor, and IA routes respect role checks.
- [ ] Validate sandbox users cannot reach staff workflow pages.
- [ ] Validate network access from Judge0 student execution is blocked.
- [ ] Validate Kata-backed VM isolation is active in the planned execution environment.
- [ ] Validate malicious ZIP path traversal is rejected.
- [ ] Validate configured hard-block findings stop execution.
- [ ] Validate timeout handling with `while True: pass`.
- [ ] Validate export totals against rubric config and pytest results.
- [ ] Validate extracted official files are deleted after request completion.
- [ ] Validate sandbox upload artifacts are deleted after session exit or completion.
- [ ] Validate temporary feedback artifacts are deleted after packaging.
- [ ] Validate no student code remains in persistent storage.
- [ ] Smoke test on the Dell-workstation deployment.
- [ ] Review deployment configuration.
- [ ] Update README with deployment and operating notes.
- [ ] Record a demo walkthrough.
