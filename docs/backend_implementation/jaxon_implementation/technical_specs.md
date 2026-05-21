# UVU Autograder v1 - Technical Specifications

## 1. System Architecture

- Frontend: Next.js in the current local/on-prem M1 stack on the Dell workstation for staff and student interfaces.
- Code editor and review surface: Monaco Editor, locally hosted with the frontend app for current M1 code-editing and review workflows.
- Backend: FastAPI in the current local/on-prem M1 stack for routing, orchestration, and API contracts.
- Execution engine: Judge0 CE for sandboxed code execution with strict resource limits and network-disabled student runs.
- Runtime isolation: Kata Containers is the planned VM-based isolation layer for Judge0 executions.
- Database: PostgreSQL in the current local/on-prem M1 stack for non-sensitive metadata only.
- Queue and broker: Celery with Redis for official and sandbox grading jobs.
- AI inference: Azure OpenAI API for pedagogical explanations grounded in pytest and AST results.

## 2. Core Features

- Staff authentication through Microsoft OAuth restricted to `@uvu.edu`.
- Student sandbox access through globally visible sandbox-enabled assignments without student-specific authentication.
- Progressive `Concepts Covered` enforcement using AST validation plus LLM prompt context.
- Zero-retention grading for both official staff runs and student sandbox runs.
- Optional staff-facing plagiarism analysis through Stanford MOSS using ephemeral official batch files only.
- Staff review uses derived artifacts plus structured in-app review data; M1 does not provide a raw student-submission download workflow.
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
5. Results are packaged into staff-facing export artifacts.
6. Optional MOSS analysis may run using the same ephemeral official workspace.
7. Judge0 result metadata is retrieved and verified, then the app calls `DELETE /submissions/{token}` and Judge0 submission/result artifacts and Kata execution state are destroyed immediately.
8. Export is returned, then temporary student files and detailed feedback artifacts are destroyed; no raw student-submission download is produced.

### Student sandbox projected grading

1. Student opens the sandbox entry flow.
2. Backend returns globally visible courses and assignments where sandbox access is enabled.
3. Student selects a visible course and assignment.
4. Student uploads code for projected grading.
5. The backend applies sandbox rate limiting before any grading work starts.
6. The frontend shows remaining uploads in the current window and a clear limit-reached state if the backend returns a rate-limit response.
7. Code is processed through the same AST, Judge0-backed Kata-isolated test execution, and Azure explanation pipeline.
8. Projected score, warnings, and feedback appear on screen only.
9. Execution artifacts are destroyed immediately after result retrieval and verification according to the zero-retention contract, including `DELETE /submissions/{token}` against Judge0 for the retrieved execution record.
10. Temporary student files and detailed sandbox artifacts are destroyed on completion or session exit.

### Assignment and grading setup

1. Instructor creates an assignment linked to a course.
2. Authorized staff configure grading data primarily through a comprehensive instructor-facing wizard that generates the app-owned `config.json`, with `config.json` import/export support available as needed.
3. Assignment metadata (for example name, due date, and points context) is entered manually in M1; Canvas assignment-metadata import is not required.
4. `Concepts Covered` defaults are maintained at the course level, and each assignment stores additive concept entries only.
5. pytest-linked tests, model solution content, and test metadata derived from the app-owned config are maintained as assignment-owned grading assets.
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
- `TestCase` is a derived record, not the editable grading definition and not the raw file body.
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
- `RunSummary` must not store:
  - student code
  - filenames or submission-path fragments
  - student identifiers
  - traceback bodies
  - detailed failure text
  - code snippets copied from logs or outputs
  - detailed AI feedback bodies
  - downloadable sandbox artifacts
  - persisted MOSS URLs or other persistent MOSS report references

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

These remain outside persistent storage and are represented conceptually in `docs/backend_implementation/jaxon_implementation/diagrams/ephemeral_pipeline_diagram.md`.

## Execution Engine Notes

- Judge0 is the planned execution engine for M1 and later phases.
- Kata Containers is the planned VM-based isolation layer for Judge0 and should be treated as part of the core execution design rather than optional hardening.
- The app uses Judge0's structured execution metadata, including status, execution time, memory usage, exit code, exit signal, and compile output when applicable.
- Judge0 improves long-term support for richer execution diagnostics and future compiled or multi-file coursework without expanding current M1 scope.
- The current M1 deployment plan uses local/on-prem Docker on the Dell workstation rather than Railway or another hosted provider.
- Railway-style hosted deployment is not viable for the current implementation because the Judge0 + Kata execution path depends on the local Docker and hardware/containerization model on the Dell workstation.
- Judge0's default persistence behavior must not become part of the product model; cleanup must satisfy the zero-retention contract for execution artifacts immediately after result verification and retrieval.
- The required Judge0 cleanup call is `DELETE /submissions/{token}` immediately after retrieval of the execution result.
- Capacity planning for Judge0 and Celery is memory-bound on the Dell workstation and must prefer queueing/backpressure over aggressive parallelism.

## Frontend Tooling Notes

- Monaco Editor is a planned M1 dependency and should be locally hosted with the app rather than fetched from a third-party CDN.
- Monaco supports sandbox code editing and upload assistance plus staff-side code inspection in M1.
- In M1, LLM feedback is surfaced as a student-sandbox textbox adjacent to test results and auto-shown after each run; it is explanation-only and does not alter grading outcomes.
- Monaco does not change the persistent data model; it is a frontend/editor dependency and a review surface backed by structured app data rather than raw submission downloads.

## 6. Permissions Matrix

| Actor      | View course assignments              | Edit grading setup                                                 | Launch official runs                                                 | View official run results                  | Trigger MOSS                                          | Access sandbox assignment listings                                     |
| ---------- | ------------------------------------ | ------------------------------------------------------------------ | -------------------------------------------------------------------- | ------------------------------------------ | ----------------------------------------------------- | ---------------------------------------------------------------------- |
| Admin      | Yes                                  | Yes                                                                | Yes                                                                  | Yes                                        | Yes                                                   | Optional administrative access only                                    |
| Instructor | Yes, across assigned courses         | Yes, only in explicitly assigned sections                          | Yes, only in explicitly assigned sections                            | Yes, for assigned courses and sections     | Yes, for official runs they are allowed to manage     | Not a normal student path                                              |
| IA         | No course-wide visibility by default | No; IAs are read-only for assignment configuration in M1           | Yes, only in explicitly assigned sections when granted run authority | Yes, only for explicitly assigned sections | No by default in M1 unless explicitly delegated later | Not a normal student path                                              |
| Student    | No staff assignment access           | No                                                                 | No                                                                   | No                                         | No                                                    | Yes, for globally visible sandbox-enabled assignments |

Notes:

- `staff_access` stores course scope, optional section scope, and role semantics.
- Instructors can see what other teachers are doing in assigned courses but may not modify grading setup outside their own assigned sections.
- IAs are section-limited validators in M1, with read-only access to assignment configuration in assigned sections.
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

`upload validation -> ephemeral extraction -> per-student AST/concept check -> per-student Judge0-backed Kata-isolated test execution -> Judge0 result retrieval -> execution-artifact cleanup -> Azure explanation -> feedback rendering -> export packaging -> cleanup`

- Per-student parallelization begins only after the official archive has passed validation and been extracted.
- AST/concept checks must evaluate the merged effective concept list derived from current course defaults plus assignment additions.
- Celery concurrency must respect the Dell workstation's documented memory-tested Judge0 + Kata execution capacity.
- Failed jobs retry up to `3` times with backoff.
- Timeout handling must surface an actionable failed state and ensure execution artifacts are not retained after result handling.
- Official cleanup semantics:
  - execution artifacts are cleaned up immediately after result verification and retrieval according to the zero-retention contract
  - Judge0 cleanup includes `DELETE /submissions/{token}` immediately after the result is read
  - temporary feedback artifacts exist only long enough to package and return the export
  - cleanup runs after export completion rather than preserving packaged student artifacts on disk
  - MOSS-prepared files are deleted in the same official-run cleanup cycle
  - cleanup verification is part of expected operational behavior, not optional best effort
  - persistent run reporting is limited to aggregate, non-identifying metadata

### Sandbox run

`rate limit -> upload intake -> ephemeral workspace creation -> AST/concept check -> Judge0-backed Kata-isolated test execution -> Judge0 result retrieval -> execution-artifact cleanup -> Azure explanation -> on-screen response shaping -> cleanup`

- The sandbox limiter is student-only and must run before grading work begins.
- AST/concept checks must evaluate the merged effective concept list derived from current course defaults plus assignment additions.
- Judge0 cleanup includes `DELETE /submissions/{token}` immediately after the result is read.
- Sandbox output never becomes a downloadable artifact.
- Sandbox cleanup runs on completion, timeout, failure, or session exit.
- Persistent sandbox reporting is limited to aggregate, non-identifying metadata.

### Run status delivery contract

- Delivery contract endpoint: `GET /runs/{id}/status`.
- Backend status reads are backed by Redis transient run-state storage.
- `GET /runs/{id}/status` must surface `queue`, `run`, `complete`, or `failure` state.
- Staff and student clients poll this endpoint every `2s` while state is `queue` or `run`, then stop polling after `complete` or `failure`.

## 9. Output Formats

### Staff-facing export artifacts

- M1 requires a downloadable staff export workflow for official runs.
- M1 official runs expose two separate staff download actions: one Canvas-grade CSV and one ZIP of per-student HTML feedback artifacts.
- Official review is preview-only in M1; the app does not support in-session grade overrides or feedback editing before export.
- M1 does not expose a raw student-submission tarball, raw-code ZIP, or equivalent download path.
- Structured review data may be shown in Monaco-backed or JSON-backed app surfaces without changing the zero-retention contract.
- Automated Canvas feedback upload or distribution is out of scope for M1.
- Export artifacts must not imply persistent storage of student code on the server.

### Sandbox response

- On-screen only.
- Includes projected score, warnings, and AI-backed explanation.
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
  - MOSS user id
  - sandbox rate-limit settings
  - cleanup-related settings if made configurable

### Runtime limits and guardrails

- Judge0 timeout target: `10s`
- Judge0 memory limit target: `256MB`
- Judge0 student execution network access: disabled
- Kata-backed VM isolation is required for the current planned production execution model.
- Worker concurrency and queue limits must stay within the Dell workstation's documented memory-safe execution envelope.
- Hallucination guard: pytest and tracebacks remain the correctness source of truth
- Azure privacy readiness: ZDR/privacy posture must be confirmed before live student data use
- Azure logging: token usage only, stored as sanitized aggregate metadata
