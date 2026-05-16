# UVU Autograder v1 - Technical Specifications

## 1. System Architecture

- Frontend: Next.js on Railway for staff and student interfaces.
- Code editor and review surface: Monaco Editor, locally hosted with the frontend app for canonical M1 code-editing and review workflows.
- Backend: FastAPI on Railway for routing, orchestration, and API contracts.
- Execution engine: Judge0 CE on separate execution infrastructure for sandboxed code execution with strict resource limits and network-disabled student runs.
- Runtime isolation: Kata Containers is the canonical VM-based isolation layer for Judge0 executions.
- Database: Railway PostgreSQL for non-sensitive metadata only.
- Queue and broker: Celery with Redis for official and sandbox grading jobs.
- AI inference: Azure OpenAI API for pedagogical explanations grounded in pytest and AST results.

## 2. Core Features

- Shadow SSO using Microsoft OAuth restricted to `@uvu.edu`.
- Student sandbox course visibility authorized through a minimal student-course mapping derived from normalized Microsoft email matched against instructor-uploaded Canvas roster entries.
- Progressive `Concepts Covered` enforcement using AST validation plus LLM prompt context.
- Zero-retention grading for both official staff runs and student sandbox runs.
- Optional staff-facing plagiarism analysis through Stanford MOSS using ephemeral official batch files only.
- Hallucination guardrails that treat pytest and tracebacks as ground truth and limit the LLM to explanation rather than re-grading.

## 3. Open-Source Patterns Reused

- Autolab/Tango inspires the async grading/job orchestration shape, including queue-driven official-run processing and status tracking.
- Submitty's `config.json` format informs the grading-config direction for tests, point values, and execution settings.
- `python_submitty_utils` is used for output normalization to reduce false negatives from whitespace and formatting differences.

## 4. App Workflows

### Official staff batch grading

1. Staff uploads a Canvas ZIP for one assignment.
2. The backend validates the archive and rejects malformed or non-Canvas ZIPs before queueing.
3. Valid archives are extracted into a shared ephemeral workspace.
4. Student submissions are graded through AST checks, Judge0 execution in Kata-backed VMs for test runs, and Azure OpenAI explanation generation.
5. Results are packaged as a minimal Canvas-oriented CSV plus a ZIP of per-student HTML feedback files.
6. Optional MOSS analysis may run using the same ephemeral official workspace.
7. Judge0 result metadata is retrieved, then Judge0 submission, result, and Kata-backed execution artifacts are deleted or invalidated.
8. Export is returned, then temporary student files and detailed feedback artifacts are destroyed.

### Student sandbox projected grading

1. Student signs in with a `@uvu.edu` account.
2. Backend resolves student-authorized courses from a minimal authorization mapping keyed by normalized Microsoft email.
3. Student selects a configured authorized course and assignment, or sees an empty dashboard when none are authorized.
4. Student uploads code for projected grading.
5. The backend applies sandbox rate limiting before any grading work starts.
6. Code is processed through the same AST, Judge0-backed Kata-isolated test execution, and Azure explanation pipeline.
7. Projected score, warnings, and feedback appear on screen only.
8. Judge0 submission, result, and Kata-backed execution artifacts are deleted or invalidated after retrieval.
9. Temporary student files and detailed sandbox artifacts are destroyed on completion or session exit.

### Assignment and grading setup

1. Instructor creates an assignment linked to a course.
2. Authorized staff configure grading data primarily through a comprehensive instructor-facing wizard that generates the canonical app-owned `config.json`, with `config.json` import/export support available as needed.
3. Assignment metadata (for example name, due date, and points context) is entered manually in M1; Canvas assignment-metadata import is not required.
4. Concepts defaults and assignment-specific overrides are maintained per course and assignment.
5. Instructor uploads an initial Canvas roster for student sandbox authorization mapping (Canvas-listed students only).
6. pytest-linked tests, model solution content, and student-visible test descriptions are maintained as assignment-owned grading assets.
7. Model solution validation runs through the same Judge0 + Kata execution path used for student code.

## 5. Data Model

### Persistent PostgreSQL entities

- `users`
- `roles`
- `courses`
- `sections`
- `staff_access`
- `assignments`
- `course_enrollments`
- `assignment_configs`
- `concept_sets`
- `assignment_concept_overrides`
- `assignment_artifacts`
- `test_cases`
- `run_summaries`

### Persistent model notes

- `staff_access` stores user, role, course, optional section, and permission semantics.
- `course_enrollments` stores minimal student-course authorization mapping for sandbox visibility and access checks, keyed by normalized Microsoft email without storing a full student profile.
- `assignments` are course-linked, while section-level edit authority is enforced through staff access rules.
- `assignment_configs` store structured grading configuration including the canonical app-owned `config.json`, with the frontend wizard treated as the primary M1 authoring surface.
- `concept_sets` represent course-level defaults; `assignment_concept_overrides` represent assignment-specific overrides.
- `assignment_artifacts` store metadata and storage references for pytest files, model solutions, and support files.
- `test_cases` represent grading metadata, criterion linkage, point values, student-visible descriptions, and the reference needed to locate pytest content through artifact-backed storage.
- `run_summaries` store workflow type, actor, timestamps, aggregate counts, failure categories, sanitized Azure token usage, and optional safe operational metadata such as a MOSS report URL.

### TestCase and artifact contract

- `AssignmentArtifact` is the storage-backed file reference layer for assignment-owned grading assets.
- Minimum M1 artifact classes:
  - `config_json`
  - `pytest_file`
  - `model_solution`
  - `support_file`
- M1 expectations by artifact class:
  - `config_json`: validated, persisted as structured config, and available for import/export and download
  - `pytest_file`: editable, validated through test execution, stored as metadata plus storage-backed file body
  - `model_solution`: editable, executable through Judge0, stored as metadata plus storage-backed file body
  - `support_file`: assignment-owned file content available to grading and test execution as needed
- `TestCase` is the explicit grading record, not the raw file body.
- `TestCase` should minimally capture:
  - assignment linkage
  - criterion label or criterion reference
  - point value
  - student-visible description
  - reference to the pytest artifact used for execution

### Student authorization mapping contract

- `CourseEnrollment` is a minimal authorization record for sandbox course visibility, not a student profile.
- Minimum M1 fields:
  - `course_id`
  - `canvas_student_id` (from instructor-uploaded Canvas roster)
  - normalized `email` (from Microsoft OAuth identity and Canvas roster import)
  - `source` metadata (`canvas_roster_import`, `manual_adjustment`, or equivalent)
  - `is_active`
- M1 matching behavior:
  - match authenticated Microsoft email to active `course_enrollments.email` values for course visibility
  - deny course visibility when no active course-enrollment mapping exists for the authenticated student identity
  - only students present in the Canvas-seeded roster mapping may see that course in sandbox
  - no grades, submission history, profile attributes, or student feedback bodies are stored in this mapping

### Canvas roster upload and import

- Instructors upload a CSV file with the following required columns: `Student_Name`, `Canvas_ID`, `UVU_ID`, and `Section`
- The roster CSV is mandatory before any student can see a course in sandbox; instructors must upload an initial roster before enabling the course for student access
- Roster files are parsed, validated for required columns and data integrity, then imported into `course_enrollments` with `source` set to `canvas_roster_import`
- Canvas roster import normalizes student emails (e.g., from Canvas email field or constructed from UVU_ID + `@uvu.edu`) and stores them in `course_enrollments.email`
- Instructors can upload a new roster file at any time to add latecomers, remove withdrawals, or adjust section assignments mid-semester; the new upload replaces the previous mapping for that course
- Backend authorization checks query `course_enrollments` fresh on every request (not cached persistently) to immediately reflect roster updates
- When a student attempts to access a course and has no matching `course_enrollments` entry, the system displays: "You have not been added to a class. If you are enrolled in a class, contact your instructor."

### Run summary contract

- `RunSummary` should minimally store:
  - workflow type: `official` or `sandbox`
  - actor user reference
  - assignment reference
  - status
  - started and completed timestamps
  - total submission count
  - success, warning, failure, and timeout counts
  - sanitized token usage
  - concise failure summary or category summary
  - optional safe MOSS report URL metadata for official runs
- `RunSummary` must not store:
  - student code
  - traceback bodies
  - detailed AI feedback bodies
  - downloadable sandbox artifacts

### Ephemeral-only pipeline data

- Student code bodies
- Extracted temporary files
- pytest tracebacks
- detailed AI hint bodies
- generated sandbox feedback artifacts
- temporary official HTML feedback files before packaging

These remain outside persistent storage and are represented conceptually in `implementation_folder/jaxon_implementation/diagrams/ephemeral_pipeline_diagram.md`.

## Execution Engine Notes

- Judge0 is the canonical execution engine for M1 and later phases.
- Judge0 is hosted separately from the Railway app stack because student-code execution requires isolated privileged infrastructure.
- Kata Containers is the canonical VM-based isolation layer for Judge0 and should be treated as part of the core execution design rather than optional hardening.
- The app uses Judge0's structured execution metadata, including status, execution time, memory usage, exit code, exit signal, and compile output when applicable.
- Judge0 improves long-term support for richer execution diagnostics and future compiled or multi-file coursework without expanding current M1 scope.
- The docs do not freeze a specific host OS or cloud provider for execution infrastructure, but they do freeze Kata as the required isolation layer for canonical implementation.
- Judge0's default persistence behavior must not become part of the product model; submission, result, and Kata-backed execution artifacts must be deleted or invalidated immediately after retrieval.

## Frontend Tooling Notes

- Monaco Editor is a canonical M1 dependency and should be locally hosted with the app rather than fetched from a third-party CDN.
- Monaco supports sandbox code editing and upload assistance plus staff-side code inspection in M1.
- In M1, LLM feedback is surfaced as a student-sandbox textbox adjacent to test results and auto-shown after each run; it is explanation-only and does not alter grading outcomes.
- Inline in-editor annotation markers are deferred to post-M1 without changing the zero-retention model.
- Monaco does not change the persistent data model; it is a frontend/editor dependency and a review surface.

## 6. Permissions Matrix

| Actor      | View course assignments              | Edit grading setup                                                 | Launch official runs                                                 | View official run results                  | Trigger MOSS                                          | Access sandbox assignment listings                                     |
| ---------- | ------------------------------------ | ------------------------------------------------------------------ | -------------------------------------------------------------------- | ------------------------------------------ | ----------------------------------------------------- | ---------------------------------------------------------------------- |
| Admin      | Yes                                  | Yes                                                                | Yes                                                                  | Yes                                        | Yes                                                   | Optional administrative access only                                    |
| Instructor | Yes, across assigned courses         | Yes, only in explicitly assigned sections                          | Yes, only in explicitly assigned sections                            | Yes, for assigned courses and sections     | Yes, for official runs they are allowed to manage     | Not a normal student path                                              |
| IA         | No course-wide visibility by default | Deferred for M1 rubric/config authoring; do not treat as finalized | Yes, only in explicitly assigned sections when granted run authority | Yes, only for explicitly assigned sections | No by default in M1 unless explicitly delegated later | Not a normal student path                                              |
| Student    | No staff assignment access           | No                                                                 | No                                                                   | No                                         | No                                                    | Yes, for configured sandbox-enabled assignments visible to the student |

Notes:

- `staff_access` stores course scope, optional section scope, and role semantics.
- Instructors can see what other teachers are doing in assigned courses but may not modify grading setup outside their own assigned sections.
- IAs are section-limited validators in M1 for the parts of the workflow already locked.
- Whether IAs also receive rubric/config authoring permission remains deferred and should be decided separately from the canonical config-authoring model.
- Official batch execution is section-scoped even though assignments are course-owned.

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
  - resubmission semantics are not persisted as submission history; the uploaded ZIP is treated as the official batch snapshot for that run only
- Extraction occurs only inside the shared ephemeral workspace lifecycle used by official runs.
- No student submission should ever be extracted into a shared persistent workspace across runs.

## 8. Celery Grading Pipeline

### Official run

`upload validation -> ephemeral extraction -> per-student AST/concept check -> per-student Judge0-backed Kata-isolated test execution -> Judge0 result retrieval -> Judge0 and Kata artifact deletion -> Azure explanation -> HTML feedback generation -> export packaging -> cleanup`

- Per-student parallelization begins only after the official archive has passed validation and been extracted.
- Celery concurrency must respect documented Judge0 + Kata execution capacity.
- Failed jobs retry up to `3` times with backoff.
- Timeout handling must surface an actionable failed state and ensure Judge0-side and Kata-backed execution artifacts are not retained after result handling.
- Official cleanup semantics:
  - Judge0 submission, result, and Kata-backed execution artifacts are deleted or invalidated immediately after result retrieval
  - temporary HTML feedback files exist only long enough to package and return the export
  - cleanup runs after export completion rather than preserving packaged student artifacts on disk
  - MOSS-prepared files are deleted in the same official-run cleanup cycle
  - cleanup verification is part of expected operational behavior, not optional best effort

### Sandbox run

`rate limit -> upload intake -> ephemeral workspace creation -> AST/concept check -> Judge0-backed Kata-isolated test execution -> Judge0 result retrieval -> Judge0 and Kata artifact deletion -> Azure explanation -> on-screen response shaping -> cleanup`

- The sandbox limiter is student-only and must run before grading work begins.
- Sandbox output never becomes a downloadable artifact.
- Sandbox cleanup runs on completion, timeout, failure, or session exit.

### Run status delivery contract

- Delivery contract endpoint: `GET /runs/{id}/status`.
- Backend status reads are backed by Redis transient run-state storage.
- `GET /runs/{id}/status` must surface `queue`, `run`, `complete`, or `failure` state.
- Staff and student clients poll this endpoint every `2s` while state is `queue` or `run`, then stop polling after `complete` or `failure`.

## 9. Output Formats

### Official CSV

- Minimal and Canvas-import-oriented.
- Contains assignment-linked grade output only.
- Does not include detailed AI feedback bodies or tracebacks.

### Official HTML feedback

- Per-student HTML files bundled into a master ZIP.
- Includes:
  - projected score or earned grade
  - test breakdown
  - warnings and hard-block reasons when applicable
  - AI explanation grounded in test results

### Sandbox response

- On-screen only.
- Includes projected score, warnings, and AI-backed explanation.
- Is not downloadable and is not stored persistently.

## 10. Deployment and Environment

- Production target is Railway for frontend, backend, PostgreSQL, Redis, and Celery, with Judge0 + Kata hosted on separate execution infrastructure.
- Docker Compose supports local development and integration-style testing through `docker compose -f docker-compose.testing.yml`.
- The testing Compose stack is a local or integration harness for the app stack plus Judge0 connectivity; it is not required to perfectly reproduce the canonical Kata isolation layer in every local environment.
- A separate dev or staging machine may be used for local or integration validation, but it does not replace Railway as the canonical M1 production target.
- Required environment configuration includes:
  - Azure OpenAI credentials and endpoint
  - Judge0 URL and any required service auth token
  - Kata-capable execution host or runtime configuration for canonical deployments
  - Redis and Celery broker URL
  - MOSS user id
  - sandbox rate-limit settings
  - cleanup-related settings if made configurable

### Runtime limits and guardrails

- Judge0 timeout target: `10s`
- Judge0 memory limit target: `256MB`
- Judge0 student execution network access: disabled
- Kata-backed VM isolation is required for canonical production execution.
- Hallucination guard: pytest and tracebacks remain the correctness source of truth
- Azure privacy readiness: ZDR/privacy posture must be confirmed before live student data use
- Azure logging: token usage only, stored as sanitized metadata
