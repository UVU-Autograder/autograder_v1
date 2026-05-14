# UVU Autograder v1 - Technical Specifications

> This file is part of the canonical Jaxon-authored M1 implementation baseline. Preserved Easton reference docs in this folder are useful context but non-authoritative when they conflict with the choices here.

## 1. System Architecture

- Frontend: Next.js on Railway for staff and student interfaces.
- Backend: FastAPI on Railway for routing, orchestration, and API contracts.
- Execution engine: Piston on Railway for sandboxed Python execution with no network access and strict resource limits.
- Database: Railway PostgreSQL for non-sensitive metadata only.
- Queue and broker: Celery with Redis for official and sandbox grading jobs.
- AI inference: Azure OpenAI API for pedagogical explanations grounded in pytest and AST results.

## 2. Core Features

- Shadow SSO using Microsoft OAuth restricted to `@uvu.edu`.
- Progressive `Concepts Covered` enforcement using AST validation plus LLM prompt context.
- Zero-retention grading for both official staff runs and student sandbox runs.
- Optional staff-facing plagiarism analysis through Stanford MOSS using ephemeral official batch files only.
- Hallucination guardrails that treat pytest and tracebacks as ground truth and limit the LLM to explanation rather than re-grading.

## 3. App Workflows

### Official staff batch grading

1. Staff uploads a Canvas ZIP for one assignment.
2. The backend validates the archive and rejects malformed or non-Canvas ZIPs before queueing.
3. Valid archives are extracted into a shared ephemeral workspace.
4. Student submissions are graded through AST checks, pytest execution in Piston, and Azure OpenAI explanation generation.
5. Results are packaged as a minimal Canvas-oriented CSV plus a ZIP of per-student HTML feedback files.
6. Optional MOSS analysis may run using the same ephemeral official workspace.
7. Export is returned, then temporary student files and detailed feedback artifacts are destroyed.

### Student sandbox projected grading

1. Student signs in with a `@uvu.edu` account.
2. Student selects a configured course and assignment.
3. Student uploads code for projected grading.
4. The backend applies sandbox rate limiting before any grading work starts.
5. Code is processed through the same AST, pytest, and Azure explanation pipeline.
6. Projected score, warnings, and feedback appear on screen only.
7. Temporary student files and detailed sandbox artifacts are destroyed on completion or session exit.

### Assignment and grading setup

1. Instructor creates an assignment linked to a course.
2. Staff configure grading data through a wizard or direct `config.json`.
3. Concepts defaults and assignment-specific overrides are maintained per course and assignment.
4. pytest-linked tests, model solution content, and student-visible test descriptions are maintained as assignment-owned grading assets.
5. Model solution validation runs in the same Piston environment used for student code.

## 4. Data Model

### Persistent PostgreSQL entities

- `users`
- `roles`
- `courses`
- `sections`
- `staff_access`
- `assignments`
- `assignment_configs`
- `concept_sets`
- `assignment_concept_overrides`
- `assignment_artifacts`
- `test_cases`
- `run_summaries`

### Persistent model notes

- `staff_access` stores user, role, course, optional section, and permission semantics.
- `assignments` are course-linked, while section-level edit authority is enforced through staff access rules.
- `assignment_configs` store structured grading configuration including the canonical app-owned `config.json`.
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
  - `config_json`: editable, validated, persisted as structured config plus exportable JSON representation
  - `pytest_file`: editable, validated through test execution, stored as metadata plus storage-backed file body
  - `model_solution`: editable, executable in Piston, stored as metadata plus storage-backed file body
  - `support_file`: assignment-owned file content available to grading and test execution as needed
- `TestCase` is the explicit grading record, not the raw file body.
- `TestCase` should minimally capture:
  - assignment linkage
  - criterion label or criterion reference
  - point value
  - student-visible description
  - reference to the pytest artifact used for execution

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

These remain outside persistent storage and are represented conceptually in `class_diagrams/ephemeral_pipeline_diagram.md`.

## 5. Permissions Matrix

| Actor | View course assignments | Edit grading setup | Launch official runs | View official run results | Trigger MOSS | Access sandbox assignment listings |
|------|--------------------------|--------------------|----------------------|---------------------------|--------------|------------------------------------|
| Admin | Yes | Yes | Yes | Yes | Yes | Optional administrative access only |
| Instructor | Yes, across assigned courses | Yes, only in explicitly assigned sections | Yes, only in explicitly assigned sections | Yes, for assigned courses and sections | Yes, for official runs they are allowed to manage | Not a normal student path |
| IA | No course-wide visibility by default | No grading-setup edits unless explicitly elevated later | Yes, only in explicitly assigned sections when granted run authority | Yes, only for explicitly assigned sections | No by default in M1 unless explicitly delegated later | Not a normal student path |
| Student | No staff assignment access | No | No | No | No | Yes, for configured sandbox-enabled assignments visible to the student |

Notes:
- `staff_access` stores course scope, optional section scope, and role semantics.
- Instructors can see what other teachers are doing in assigned courses but may not modify grading setup outside their own assigned sections.
- IAs are section-limited validators in M1.
- Official batch execution is section-scoped even though assignments are course-owned.

## 6. Canvas ZIP Format and Filename Mapping

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

## 7. Celery Grading Pipeline

### Official run

`upload validation -> ephemeral extraction -> per-student AST/concept check -> per-student pytest/Piston execution -> Azure explanation -> HTML feedback generation -> export packaging -> cleanup`

- Per-student parallelization begins only after the official archive has passed validation and been extracted.
- Celery concurrency must respect Piston container parallelism.
- Failed jobs retry up to `3` times with backoff.
- Timeout handling must release workers quickly and surface an actionable failed state.
- Official cleanup semantics:
  - temporary HTML feedback files exist only long enough to package and return the export
  - cleanup runs after export completion rather than preserving packaged student artifacts on disk
  - MOSS-prepared files are deleted in the same official-run cleanup cycle

### Sandbox run

`rate limit -> upload intake -> ephemeral workspace creation -> AST/concept check -> pytest/Piston execution -> Azure explanation -> on-screen response shaping -> cleanup`

- The sandbox limiter is student-only and must run before grading work begins.
- Sandbox output never becomes a downloadable artifact.
- Sandbox cleanup runs on completion, timeout, failure, or session exit.

## 8. Output Formats

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

## 9. Deployment and Environment

- Production target is Railway for frontend, backend, PostgreSQL, Redis, Celery, and Piston.
- Docker Compose supports local development and integration-style testing through `docker compose -f docker-compose.testing.yml`.
- Required environment configuration includes:
  - Azure OpenAI credentials and endpoint
  - Piston URL
  - Redis and Celery broker URL
  - MOSS user id
  - sandbox rate-limit settings
  - cleanup-related settings if made configurable

### Runtime limits and guardrails

- Piston timeout: `10s`
- Piston memory limit: `256MB`
- Piston network access: disabled
- Hallucination guard: pytest and tracebacks remain the correctness source of truth
- Azure logging: token usage only, stored as sanitized metadata
