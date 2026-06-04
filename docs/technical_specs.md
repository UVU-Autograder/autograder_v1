# UVU Autograder v1 - Technical Specifications

## 1. System Architecture

- Frontend: Next.js in the current local/on-prem M1 stack on the Dell workstation for staff and student interfaces.
- UI language: TypeScript for frontend type safety.
- Code editor and review surface: Monaco Editor, locally hosted with the frontend app for current M1 read-only preview and review workflows.
- Backend: FastAPI in the current local/on-prem M1 stack for routing, orchestration, and API contracts.
- Backend language: Python `3.11+`.
- Execution engine: Judge0 CE for sandboxed code execution with strict resource limits and network-disabled student runs.
- Runtime isolation: Kata Containers is the planned VM-based isolation layer for Judge0 executions.
- Database: PostgreSQL in the current local/on-prem M1 stack for non-sensitive metadata only.
- ORM and migrations: SQLAlchemy plus Alembic.
- Queue and broker: Celery with Redis for official and sandbox grading jobs.
- AI inference: Azure OpenAI API for pedagogical explanations grounded in pytest and AST results.
- HTTP client: `httpx` for FastAPI-to-Judge0 async REST calls.

## 2. Core Features

- Staff authentication through Microsoft OAuth restricted to `@uvu.edu`.
- Student sandbox access through globally visible sandbox-enabled assignments without student-specific authentication.
- Progressive `Concepts Covered` enforcement using AST validation plus LLM prompt context.
- Zero-retention grading for both official staff runs and student sandbox runs.
- Multi-file support uses ZIP/project bundle uploads for both official staff runs and student sandbox runs.
- Hallucination guardrails that treat pytest and tracebacks as ground truth and limit the LLM to explanation rather than re-grading.
- Plagiarism detection is out of M1.
- M1 validation uses only fake/synthetic data or completely anonymized data with no retained re-identification map.

## 3. Open-Source Patterns Reused

- Autolab/Tango inspires the async grading/job orchestration shape, including queue-driven official-run processing and status tracking.
- Submitty's `config.json` format informs the grading-config direction for tests, point values, and execution settings.
- `python_submitty_utils` is used for output normalization to reduce false negatives from whitespace and formatting differences.

## 4. App Workflows

### Official staff batch grading

1. Staff uploads a Canvas ZIP for one assignment.
2. The backend validates the archive and rejects malformed or non-Canvas ZIPs before queueing.
3. Valid archives are extracted into a shared ephemeral workspace.
4. Student submission bundles are validated against assignment-config requirements, then graded through AST checks, Judge0 execution in Kata-backed VMs for test runs, and Azure OpenAI explanation generation when approved for the data being processed.
5. Results are packaged into staff-facing export artifacts.
6. Export is returned.

### Student sandbox projected grading

1. Student opens the sandbox entry flow.
2. Backend returns globally visible courses and assignments where sandbox access is enabled.
3. Student selects a visible course and assignment.
4. Student uploads a ZIP/project bundle for projected grading.
5. The backend applies sandbox rate limiting before any grading work starts.
6. The backend validates ZIP safety and assignment-config bundle requirements before grading.
7. The frontend shows upload quota, preview, and rate-limit state.
8. Code is processed through the same AST, Judge0-backed Kata-isolated test execution, and Azure explanation pipeline when approved for the data being processed.
9. Projected score, warnings, and feedback appear on screen only.

### Assignment and grading setup

1. Instructor creates an assignment linked to a course.
2. Authorized staff configure grading data primarily through a comprehensive instructor-facing wizard that generates the app-owned `config.json`, with `config.json` import/export support available as needed.
3. Assignment metadata (for example name, due date, and points context) is entered manually in M1; Canvas assignment-metadata import is not required.
4. `Concepts Covered` defaults are maintained at the course level, and each assignment stores additive concept entries only.
5. pytest-linked tests, model solution content, ZIP/project bundle requirements, and test metadata derived from the app-owned config are maintained as assignment-owned grading assets.
6. Model solution validation runs through the same Judge0 + Kata execution path used for student code.

## 5. Data Model

### Persistent PostgreSQL entities

- `users`
- `roles`
- `courses`
- `sections`
- `staff_access`
- `assignments`
- `assignment_configs`
- `assignment_concepts`
- `assignment_artifacts`
- `test_cases`
- `run_summaries`

### Persistent model notes

- `staff_access` stores user, role, course, optional section, and permission semantics.
- `courses` store the teacher-authored default `Concepts Covered` baseline used across assignments in that course.
- `assignments` are course-linked, while section-level edit authority is enforced through staff access rules.
- `assignment_configs` store the app-owned `config.json`, which is the primary editable grading configuration in M1; the frontend wizard is the primary authoring surface for that config.
- `assignment_configs` also store ZIP/project bundle requirements such as required files, entrypoint, and layout expectations.
- `assignment_concepts` store assignment-specific additive concept entries only; the runtime-effective allow-list is derived by merging course defaults with assignment additions when AST checks or UI surfaces need it.
- `assignment_artifacts` store lightweight metadata and storage references for assignment-owned files such as pytest files, model solutions, and support files.
- `test_cases` are optional derived records used for querying, validation, and UI rendering; they must never become a second editable grading source of truth.
- `run_summaries` store workflow type, actor, aggregate counts, failure categories, and sanitized Azure token usage only.
- Judge0 submission tokens and raw Judge0 result payloads are transient execution-service data and must not be persisted as app-owned Postgres records.
- Persistent operational metadata must remain aggregate-only and non-identifying; filenames, student identifiers, raw tracebacks, detailed failure text, and code snippets must not be stored in long-lived metadata tables or logs.

### Concepts Covered contract

- The course-level baseline is teacher-authored and stored with the course or course settings payload.
- Assignment concepts are additive only in M1 and represent assignment-specific concepts beyond the course baseline.
- The effective concept allow-list is computed at runtime as `course defaults + assignment additions`.
- Runtime merge rules:
  - course defaults appear first
  - assignment additions appear after course defaults
  - duplicate concepts are removed automatically
- AST enforcement and any UI display of allowed concepts must use the same merged effective list.
- Existing assignments always reflect the current course defaults at runtime; M1 does not snapshot course defaults into assignment config.
- Assignment `config.json` stores assignment-owned concept additions only and does not duplicate course-owned defaults.
- Importing the same assignment config into a different course may produce a different effective concept list because course defaults are course-owned in M1.

### `config.json` v1 contract

- M1 uses a strict app-owned `config.json` v1 contract for assignment import, export, wizard generation, bundle validation, test projection, and execution planning.
- `config.json` v1 is Python-focused and pytest-focused. It does not model multi-language execution, compiled-language build pipelines, manual grading, plagiarism workflows, or Canvas grade passback.
- The exported/imported config must include `schema_version: 1`. Missing versions, unknown major versions, or configs that cannot be validated against the v1 schema must be rejected with actionable import errors.
- The v1 schema should be expressed as JSON Schema 2020-12 for portable import/export validation. Backend and frontend validators may use implementation-native tools, but they must enforce the same schema and error paths.
- Config entries that need durable identity across import/export use stable human-readable keys, not database IDs. Stable keys are required for tests and artifact references.
- Display labels may change without changing stable keys. Renaming a stable key is treated as replacing that config object and should trigger regeneration or reconciliation of derived records.
- Minimum top-level v1 sections:
  - `schema_version`
  - `assignment`
  - `bundle`
  - `concepts`
  - `artifacts`
  - `tests`
  - `grading`
- `assignment` stores assignment-owned display metadata needed by the config surface, such as title or points context. Canvas remains the course/grade source of truth.
- `bundle` stores ZIP/project bundle requirements, including required files, entrypoint rules, and supported layout expectations.
- `concepts` stores assignment-owned concept additions only. Course defaults are not duplicated in exported assignment config.
- `artifacts` maps stable artifact keys to required artifact type and optional display filename metadata. File bodies are stored through the assignment artifact storage layer, not embedded in config JSON.
- `tests` stores stable test keys, display names, point values, visibility settings, pytest artifact references, and any safe test metadata needed for UI and execution planning.
- `grading` stores total-point expectations and aggregation rules needed to validate that test points and exported grades are internally consistent.
- `TestCase` rows, UI previews, and execution plans are derived from the app-owned config. If derived rows disagree with the config, the config wins and derived rows must be regenerated or reconciled.
- Config validation must catch at least: duplicate stable keys, missing artifact references, invalid point totals, missing bundle entrypoint rules, unsupported artifact types, and fields outside the supported v1 contract where strict validation applies.

### TestCase and artifact contract

- `AssignmentArtifact` is the storage-backed file reference layer for assignment-owned grading assets.
- Minimum M1 artifact classes:
  - `config_json`
  - `pytest_file`
  - `model_solution`
  - `support_file`
- M1 expectations by artifact class:
  - `config_json`: validated, persisted as the primary config, and available for import/export and download
  - `pytest_file`: editable, validated through test execution, stored as metadata plus storage-backed file body
  - `model_solution`: editable, executable through Judge0, stored as metadata plus storage-backed file body
  - `support_file`: assignment-owned file content available to grading and test execution as needed
- `AssignmentArtifact` metadata should stay lightweight in M1: assignment linkage, artifact type, storage reference, and optional filename are sufficient unless later implementation work proves otherwise.
- M1 artifact file bodies use the local on-prem filesystem behind a storage interface.
- Artifact storage keys are generated opaque identifiers and must not be based on instructor-provided filenames or paths.
- Optional instructor-provided filenames are display metadata only. They may be shown in staff UI after sanitization, but they must not become storage paths or long-lived student-run metadata.
- Artifact file bodies must be stored outside any web-served directory and retrieved only through authorized backend code.
- Artifact writes must enforce allowlisted artifact types, size limits, checksum capture, generated paths, and least-privilege filesystem permissions.
- Assignment-owned artifacts may persist as grading assets. Student submissions, execution workspaces, generated feedback bodies, and Judge0/Kata execution artifacts remain ephemeral and are not assignment artifacts.
- Artifact delete behavior must remove the local file body and metadata reference, or mark the metadata unusable if deletion fails and surface an actionable admin/staff error.
- `TestCase` is a derived record, not the editable grading definition and not the raw file body.
- M1 does not provide a separate simple test-case editor; test authoring flows through the wizard/config and pytest artifacts.
- `AssignmentConfig` / app-owned `config.json` wins if it ever disagrees with a derived `TestCase`; derived records must be regenerated or reconciled rather than edited independently.
- `TestCase` should minimally capture:
  - assignment linkage
  - stable config test identifier such as `config_test_key`
  - reference to the pytest artifact used for execution
  - optional display order for UI/query needs

### Run summary contract

- `RunSummary` should minimally store:
  - workflow type: `official` or `sandbox`
  - actor user reference for staff-triggered workflows, or non-identifying sandbox session identifier as needed
  - assignment reference
  - status
  - total submission count
  - success, warning, failure, and timeout counts
  - sanitized token usage
  - coarse failure category summary only
- Admin-only monitoring may summarize sanitized token usage, sandbox upload-limit state, global queued count, running count, approved execution-slot cap, high-load/full-queue state, official versus sandbox queue counts, worker/capacity status, and AI degradation state from run summaries and operational metrics.
- `RunSummary` must not store:
  - student code
  - filenames or submission-path fragments
  - student identifiers
  - traceback bodies
  - detailed failure text
  - code snippets copied from logs or outputs
  - detailed AI feedback bodies
  - downloadable sandbox artifacts
  - persisted plagiarism-report URLs or other persistent external report references

### Logging and operational-metadata contract

- Persistent logs and long-lived operational metadata must be aggregate-only and non-identifying.
- Long-lived logs and metadata must not contain:
  - student code
  - filenames
  - student identifiers
  - raw traceback text
  - detailed compile/runtime error text
  - per-student feedback bodies
- Coarse categories such as `compile_error`, `timeout`, `test_failure`, or aggregate counts are allowed.
- If sensitive debug traces are temporarily enabled for operations, they must:
  - be explicitly scoped to troubleshooting
  - be aggressively rotated
  - be purged within `24h`
  - never become part of normal persistent run reporting

### Ephemeral-only pipeline data

- Student code bodies
- Extracted temporary files
- pytest tracebacks
- detailed AI hint bodies
- generated sandbox feedback artifacts
- temporary official feedback artifacts before packaging

These remain outside persistent storage and are represented conceptually in `docs/backend_implementation/diagrams/ephemeral_pipeline_diagram.md`.

### ZIP/project bundle contract

- M1 supports ZIP/project bundle uploads for official staff runs and student sandbox runs.
- Loose multi-file drag-and-drop is out of scope for M1.
- The app-owned assignment config defines required files, entrypoint, and layout expectations for the bundle.
- Upload validation must reject:
  - malformed ZIP files
  - unsafe archive paths before extraction
  - unsupported archive structures
  - missing required files
  - ambiguous or duplicate entrypoint matches
  - files that cannot be mapped to the expected assignment layout
- Official Canvas ZIP ingestion may contain one multi-file submission bundle per student.
- Student sandbox ZIP upload represents one projected-grading bundle for the selected assignment.
- File tree and file preview surfaces must use sanitized names only and must not write filenames into persistent run metadata.

## Execution Engine Notes

- Judge0 is the planned execution engine for M1 and later phases.
- Kata Containers is the planned VM-based isolation layer for Judge0 and should be treated as part of the core execution design rather than optional hardening.
- The app uses Judge0's structured execution metadata, including status, execution time, memory usage, exit code, exit signal, and compile output when applicable.
- The current M1 deployment plan uses local/on-prem Docker on the Dell workstation rather than Railway or another hosted provider.
- Railway-style hosted deployment is not viable for the current implementation because the Judge0 + Kata execution path depends on the local Docker and hardware/containerization model on the Dell workstation.
- Judge0's default persistence behavior must not become part of the product model; cleanup must satisfy the zero-retention contract for execution artifacts immediately after result verification and retrieval.
- The required Judge0 cleanup call is `DELETE /submissions/{token}` immediately after retrieval of the execution result.
- Judge0 deletion must be enabled and authorized in the deployed Judge0 instance. If deletion is disabled, forbidden, or cannot be verified, cleanup proof fails and live official or live student-derived workflows remain launch-blocked.
- Cleanup verification must confirm:
  - `DELETE /submissions/{token}` was issued after result retrieval
  - the deleted Judge0 submission/result is no longer retrievable
  - ephemeral local workspace files are removed
  - Kata execution state is destroyed or no longer reachable
- Cleanup proof for M1 signoff requires automated integration evidence plus documented Dell-workstation operational spot checks summarized in `docs/planning/delivery_controls.md`.
- Automated cleanup tests must cover success, test failure, compile/import error, timeout, Judge0 cleanup failure, and workspace cleanup after exceptions.
- Dell spot-check evidence must be dated and must include sanitized command output or summaries for Judge0 deletion/non-retrievability, workspace removal, and Kata runtime evidence. It must not include student code, filenames, identifiers, raw tracebacks, or detailed feedback.
- Capacity planning for Judge0 and Celery is memory-bound on the Dell workstation and must prefer queueing/backpressure over aggressive parallelism.
- M1 default execution-slot cap is `2` concurrent Judge0/Kata grading jobs; `3` and `4` are benchmark targets, and no cap above `4` is approved by M1 RAM estimates alone.
- Benchmark evidence must use mixed synthetic workloads covering passing submissions, test failures, compile/import errors, timeouts, and malformed bundles.
- A benchmarked cap is approved only when cleanup proof passes, no worker/container crashes occur, queue/backpressure behaves correctly, and current service targets remain satisfied.
- Benchmark evidence must include app-level duration and failure counters, Celery queue behavior, Judge0 status behavior, and Docker/Kata resource observations. Docker stats output may be summarized, but memory and process/thread pressure must be checked.

## Frontend Tooling Notes

- Monaco Editor is a planned M1 dependency and should be locally hosted with the app rather than fetched from a third-party CDN.
- Monaco is a read-only preview and review surface in M1.
- In M1, LLM feedback is surfaced as a student-sandbox textbox adjacent to test results and auto-shown after each run; it is explanation-only and does not alter grading outcomes.
- Monaco does not change the persistent data model; it is a frontend/editor dependency and a review surface backed by structured app data rather than raw submission downloads.

## 6. Permissions Matrix

| Actor      | View course assignments              | Edit grading setup                                       | Launch official runs                                                 | View official run results                  | Access sandbox assignment listings                    |
| ---------- | ------------------------------------ | -------------------------------------------------------- | -------------------------------------------------------------------- | ------------------------------------------ | ----------------------------------------------------- |
| Admin      | Yes                                  | Yes                                                      | Yes                                                                  | Yes                                        | Optional administrative access only                   |
| Instructor | Yes, across assigned courses         | Yes, only in explicitly assigned sections                | Yes, only in explicitly assigned sections                            | Yes, for assigned courses and sections     | Not a normal student path                             |
| IA         | No course-wide visibility by default | No; IAs are read-only for assignment configuration in M1 | Yes, only in explicitly assigned sections when granted run authority | Yes, only for explicitly assigned sections | Not a normal student path                             |
| Student    | No staff assignment access           | No                                                       | No                                                                   | No                                         | Yes, for globally visible sandbox-enabled assignments |

Notes:

- `staff_access` stores course scope, optional section scope, and role semantics.
- Admin workflows must support creating, editing, deactivating, and assigning staff accounts, roles, and course or section access grants.
- Admin workflows must support creating, editing, and deactivating courses and sections.
- Admin-only monitoring is admin-only.
- Instructors can see what other teachers are doing in assigned courses but may not modify grading setup outside their own assigned sections.
- IAs are section-limited validators in M1, with read-only access to assignment configuration in assigned sections.
- Official batch execution is section-scoped even though assignments are course-owned.
- All app endpoints require a valid session token except auth entrypoints and health checks.

## 7. Canvas ZIP Format and Filename Mapping

- Official ingestion accepts Canvas-exported ZIP archives only.
- Validation must reject:
  - malformed ZIP files
  - unrecognized non-Canvas structures
  - path traversal attempts before any file is written
- M1 Canvas assumptions:
  - the archive contains student submission entries that can be mapped to Canvas-provided identifiers from filenames or enclosing paths
  - the parser can detect when a file does not map cleanly to a single student submission target
- Filename mapping rules for M1:
  - unmatched files are collected and surfaced as actionable ingest errors
  - multiple files for a single student are allowed when they belong to the same extracted submission bundle
  - duplicate or ambiguous identifier matches must fail clearly rather than guessing
  - submission bundles must also pass the assignment-config ZIP/project bundle requirements before grading
  - resubmission semantics are not persisted as submission history; the uploaded ZIP is treated as the official batch snapshot for that run only
- Extraction occurs only inside the shared ephemeral workspace lifecycle used by official runs.
- No student submission should ever be extracted into a shared persistent workspace across runs.
- M1 Canvas validation uses synthetic Canvas ZIP/CSV fixtures and any available completely anonymized Canvas-shaped samples.
- M1 does not use live, pseudonymous, or re-identifiable Canvas data for validation.
- Synthetic Canvas fixtures must cover malformed ZIPs, path traversal, ambiguous filenames, unmatched files, multi-file submission bundles, and Canvas-grade CSV shape.

## 8. Celery Grading Pipeline

- Both official and sandbox grading evaluate the merged effective concept list derived from current course defaults plus assignment additions before execution.

### Official run

`upload validation -> ephemeral extraction -> bundle validation -> per-student AST/concept check -> per-student Judge0-backed Kata-isolated test execution -> Judge0 result retrieval -> execution-artifact cleanup -> Azure explanation when approved -> feedback rendering -> export packaging -> cleanup`

- Per-student parallelization begins only after the official archive has passed validation and been extracted.
- Per-student bundle validation uses the app-owned assignment config before AST or execution starts.
- Official batches may contain more submissions than available queue capacity. After validation, official runs are chunked internally into per-submission execution jobs and only feed more work into the global execution queue as capacity opens.
- Work beyond the approved execution-slot cap remains queued or backpressured rather than starting additional execution jobs.
- Failed jobs retry up to `3` times with backoff.
- Timeout handling must surface an actionable failed state and ensure execution artifacts are not retained after result handling.
- Temporary official feedback artifacts exist only long enough to package and return the export.

### Sandbox run

`rate limit -> ZIP/project bundle intake -> ephemeral workspace creation -> bundle validation -> AST/concept check -> Judge0-backed Kata-isolated test execution -> Judge0 result retrieval -> execution-artifact cleanup -> Azure explanation when approved -> on-screen response shaping -> cleanup`

- The sandbox limiter is student-only and must run before grading work begins.
- Sandbox upload intake accepts ZIP/project bundles only.
- Bundle validation uses the app-owned assignment config before AST or execution starts.
- Accepted sandbox uploads return immediately with a non-identifying run token and status URL.
- Sandbox users may leave and return in the same browser session for up to `1h` while the run is queued, running, or recently completed.
- Sandbox users may cancel queued jobs before execution starts; cancellation frees queue capacity and triggers cleanup of any temporary intake artifacts.
- Sandbox cleanup runs on completion, timeout, failure, cancellation, or session exit.

### Queue admission and scheduling contract

- High-concurrency submission intake is separate from low-concurrency Judge0/Kata execution.
- The global queued execution-job limit is `50` waiting jobs across official and sandbox workflows.
- One queued execution job equals one per-submission Judge0/Kata execution.
- Running jobs do not count toward the `50` queued-job limit; they are governed by the approved execution-slot cap.
- At `40` queued execution jobs, staff and sandbox status surfaces should show high-load messaging.
- At `50` queued execution jobs, new intake is rejected before file persistence with a sanitized full-queue error, retry guidance, and `Retry-After` where the protocol allows it.
- The app uses separate logical official and sandbox queues that feed the same bounded execution slots.
- When both official and sandbox queues have waiting jobs, execution starts use simple round-robin fairness between workflow types.
- Queue capacity policy must never raise the active Judge0/Kata execution slot cap.
- Under high queue or resource load, AI feedback may be delayed, skipped, or marked unavailable; grounded test results should return first. AI degradation must not block cleanup or execution-slot release.

### Run status delivery contract

- `GET /runs/{id}/status` reads from Redis transient run-state storage.
- `GET /runs/{id}/status` must surface `queue`, `run`, `complete`, or `failure` state.
- The status response must include sanitized counters: `total`, `queued`, `running`, `completed`, `failed`, and `warnings`.
- When state is `queue`, the status response should include queue position and a rough ETA band: `under_1_min`, `1_to_3_min`, `3_to_5_min`, or `over_5_min`.
- The status response may include a sanitized human-readable message and coarse failure summary, but must not include student code, filenames, student identifiers, raw traceback text, detailed compiler/runtime output, detailed feedback bodies, or raw Judge0 payloads.
- Coarse failure categories for M1:
  - `validation_error`
  - `unsafe_zip`
  - `missing_required_file`
  - `ambiguous_entrypoint`
  - `concept_warning`
  - `concept_blocked`
  - `compile_error`
  - `test_failure`
  - `timeout`
  - `judge0_error`
  - `cleanup_failure`
  - `packaging_failure`
  - `queue_full`
  - `cancelled`
  - `ai_disabled`
  - `ai_error`
  - `internal_error`
- `cleanup_failure` is launch-blocking for live workflows and must be visible to staff/admin status surfaces without exposing sensitive detail.
- Staff and student clients poll this endpoint every `2s` while state is `queue` or `run`, then stop polling after `complete` or `failure`.

## 9. Output Formats

### Staff-facing export artifacts

- M1 requires a downloadable staff export workflow for official runs.
- M1 official runs expose two separate staff download actions: one Canvas-grade CSV and one ZIP of per-student HTML feedback artifacts.
- Official review is preview-only in M1.
- M1 does not expose a raw student-submission tarball, raw-code ZIP, or equivalent download path.
- Structured review data and read-only Monaco previews may be shown only while ephemeral data exists, without changing the zero-retention contract.
- Automated Canvas feedback upload or distribution is out of scope for M1.
- Export artifacts must not imply persistent storage of student code on the server.

### Sandbox response

- On-screen only.
- Includes projected score, warnings, and AI-backed explanation when AI feedback is available.
- May include sanitized file tree and read-only Monaco preview while the sandbox bundle remains in ephemeral storage.
- Is not downloadable and is not stored persistently.

## 10. Deployment and Environment

- The current M1 deployment target is the Dell workstation running the full local/on-prem stack.
- Docker Compose supports local development and integration-style testing through `docker compose -f docker-compose.testing.yml`.
- The testing Compose stack is also the current deployment-shape reference for the on-prem M1 stack, even if some teammate machines cannot fully reproduce the final Kata runtime locally.
- Teammate machines may use reduced local or integration harnesses for development, but those do not replace the Dell workstation in the current M1 hosting plan.
- Required environment configuration includes:
  - Azure OpenAI credentials and endpoint
  - Judge0 URL and any required service auth token
  - Kata-capable runtime configuration for the Dell workstation deployment
  - PostgreSQL connection settings
  - Redis and Celery broker URL
  - sandbox rate-limit settings
  - cleanup-related settings if made configurable

### Runtime limits and guardrails

- Judge0 timeout target: `10s`
- Judge0 memory limit target: `256MB`
- Judge0 student execution network access: disabled
- Kata-backed VM isolation is required for the current planned production execution model.
- Hallucination guard: pytest and tracebacks remain the correctness source of truth
- Azure privacy readiness: ZDR/privacy posture must be confirmed before live student data use
- Azure approval readiness: written UVU approval plus Azure resource/privacy confirmation must be complete before live student-code AI feedback
- Azure is disabled for live, pseudonymous, or real student-derived code unless the UVU/Azure approval checklist is complete
- Azure logging: token usage only, stored as sanitized aggregate metadata

### Service targets and reliability guardrails

- ZIP upload acceptance target: under `2s` for files up to `50MB`.
- Official batch target: `200` submissions complete within `40 min` on the Dell workstation.
- Status polling response target: under `200ms`.
- Export packaging overhead target: under `2 min` for `200` submissions after grading completes.
- Student sandbox projected grading should feel interactive for normal assignment files.
- Azure token usage must be measurable per run and assignment in non-sensitive metadata.
- Grading job failure must not affect other queued jobs.
- Timeout or packaging failure must return actionable errors to users.
- Persistent metadata must remain recoverable without retaining student submissions.
