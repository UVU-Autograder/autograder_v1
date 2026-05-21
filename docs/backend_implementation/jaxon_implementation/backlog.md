# UVU Autograder v1 - Backlog and Sprint Plan

> Supporting architecture and product decisions live in `decisions.md` and `technical_specs.md`. This file is the current backlog and sprint execution document.

> Target: Testable M1 for zero-retention grading with staff `@uvu.edu` authentication and globally visible student sandbox access
> Team: 5 developers, half time (~35-65 hrs/week total)
> Window: 8-9 weeks
> Backlog tracked in: GitHub Projects (Issues + Milestones)
> Last updated: May 4, 2026

---

## Planning Context

Implementation decisions, permission semantics, storage contracts, and technical architecture are maintained in:

- `decisions.md`
- `technical_specs.md`

This backlog focuses on sprint planning, deliverables, and acceptance criteria.

Supporting note: `docs/backend_implementation/easton_implementation/ClassFlow_diagram.md` remains an older working artifact. The current diagram set for implementation lives in `docs/backend_implementation/jaxon_implementation/diagrams/`.

---

## Epic 0 - Architecture + Design

Epic 0 captures the parallel architecture and UI design work that de-risks Sprint 1 implementation.

### Goal

Backend architecture, frontend structure, and shared contracts are explicit enough that Sprint 1 can begin without re-litigating core design decisions.

### Deliverables

- [ ] ER diagram reviewed as a current persistent-data reference
- [ ] Class and pipeline diagrams reviewed as a current workflow reference
- [ ] FastAPI router skeleton and request or response boundary plan reviewed
- [ ] Prompt integration boundaries documented
- [ ] Frontend wireframes completed for staff and sandbox flows
- [ ] Route structure and component hierarchy reviewed
- [ ] Shared API and UI contracts reviewed at the end of the parallel track

### Exit Criteria

The team has reviewed the current diagrams, shared backend/frontend contracts, and wireframes before Sprint 1 begins. No Sprint 1 feature work should start while those artifacts are still materially in flux.

---

## Sprint 0 - Environment + Metadata Foundation

Sprint 0 should run as two parallel tracks with a shared signoff checkpoint before Sprint 1:

- backend track: architecture, schema, API skeleton, task boundaries, and prompt/execution integration boundaries
- frontend track: wireframes, route structure, component hierarchy, and role-aware UI scaffolding

Sprint 1 should not begin until the team has reviewed and agreed on the shared interface contracts between those tracks.

### Goal

Every developer can run the stack locally, and the persistent model matches the reduced M1 footprint.

### Deliverables

- [ ] Repo structure agreed: monorepo with `/frontend` (Next.js) and `/backend` (FastAPI)
- [ ] Next.js app bootstrapped
- [ ] FastAPI app bootstrapped with routers, schemas, services, and prompt integration boundaries
- [ ] PostgreSQL initial schema and Alembic migration for non-sensitive core tables:
  - `users`, `roles`, `courses`, `sections`, `staff_access`, `assignments`, `assignment_configs`, `assignment_concepts`, `assignment_artifacts`, `test_cases`, `run_summaries`
- [ ] Redis running locally
- [ ] Celery connected to Redis
- [ ] Judge0 execution service running locally or in a compatible integration environment
- [ ] Judge0 service auth/config wiring documented for FastAPI and Celery
- [ ] Kata runtime validation documented for the current Judge0 execution plan
- [ ] Dell-workstation deployment shape documented for `nextjs`, `fastapi`, `postgres`, `redis`, `celery`, `judge0`, and Kata runtime integration
- [ ] Docker Compose supports local development and integration-style testing for `postgres`, `redis`, `celery`, `fastapi`, `nextjs`, and the chosen Judge0 test/integration topology
- [ ] Judge0 submission/result deletion strategy documented and validated against the zero-retention requirement, including `DELETE /submissions/{token}` immediately after retrieval
- [ ] Safe Judge0 + Kata concurrency ceiling documented from Dell-workstation memory benchmarking, with queue/backpressure defaults
- [ ] Monaco Editor hosted locally and wired into the frontend scaffold for planned M1 editor/review workflows
- [ ] `.env.example` documents required environment variables including Azure OpenAI settings
- [ ] Backend/frontend shared interface contracts reviewed before Sprint 1 kickoff
- [ ] Frontend wireframes and component hierarchy reviewed before Sprint 1 kickoff
- [ ] README gets the full stack running locally
- [ ] Seed script creates 1 course with default `Concepts Covered`, 1 assignment with additive concept entries, 1 generated app-owned `config.json`, and 1 model solution

### Exit Criteria

`docker compose -f docker-compose.testing.yml up` brings the testing stack online. FastAPI health check returns 200. A test Celery task runs successfully. Judge0 executes a Hello World Python script through the backend integration path. The Judge0 deletion strategy is validated for test submissions. The Dell workstation deployment shape and safe memory-bound concurrency ceiling are documented. Kata runtime requirements are documented for the current execution plan even if the local Compose harness does not perfectly reproduce them. Monaco is available through the frontend scaffold for code-view and editor workflows. The seeded assignment loads with its stored config, course defaults, and assignment concept additions. The team has signed off on the shared backend/frontend contract before Sprint 1 begins.

---

## Sprint 1 - Staff SSO + Assignment/Config Setup + Ephemeral Ingestion

### Goal

Staff can authenticate, students can access globally visible sandbox listings without student authentication, staff can configure assignments through a comprehensive wizard with `config.json` import/export support, and official batch uploads can be prepared without persistent student submission records.

### Deliverables

- [ ] NextAuth Microsoft OAuth provider configured
- [ ] NextAuth callback rejects any login not ending in `@uvu.edu`
- [ ] Role-based route protection in Next.js
- [ ] Role-based API protection in FastAPI
- [ ] Minimal staff role management for admin, instructor, and IA
- [ ] Public sandbox entry path exists without student authentication
- [ ] Student sandbox dashboard shows globally visible sandbox-enabled courses and assignments only
- [ ] Assignment creation form stores name, course linkage, due date, and Canvas reference metadata
- [ ] Comprehensive config wizard captures all instructor-relevant assignment/rubric/config fields
- [ ] Wizard generates valid `config.json`
- [ ] `config.json` import UI with validation and error display
- [ ] Stored config editor/view renders all instructor-relevant editable fields from the current `config.json`
- [ ] Staff can download the current `config.json`
- [ ] IA role remains strict-by-default and does not receive assignment-config authoring in M1
- [ ] Course-level `Concepts Covered` defaults editor exists
- [ ] Assignment `Concepts Covered` additions editor exists with merged effective-list preview
- [ ] Instructor can edit assignment-specific concept additions directly
- [ ] Canvas ZIP upload endpoint with size and type validation
- [ ] Non-Canvas or otherwise unrecognized ZIPs rejected before queueing
- [ ] ZIP path traversal protection before extraction
- [ ] ZIP extraction implemented in RAM or an ephemeral temp directory only
- [ ] Canvas filename parser maps files to Canvas-provided identifiers
- [ ] Unmatched filename and malformed archive reporting in the staff UI
- [ ] Transient official-run creation with assignment link, uploader, aggregate status metadata, and file counts only

### Exit Criteria

An instructor signs in with a `@uvu.edu` account. A non-UVU login is rejected. The instructor configures course-level `Concepts Covered` defaults, creates an assignment through the comprehensive wizard or by importing valid `config.json`, confirms the assignment concept additions and merged effective concept list, downloads the resulting `config.json`, uploads a Canvas ZIP for an explicitly assigned section, and the system parses the archive into a transient official run without storing student code persistently. A student can open the sandbox and see globally visible sandbox-enabled courses and assignments.

---

## Sprint 2 - Grading Pipeline + Azure OpenAI + Zero-Retention Controls

### Goal

The system grades official runs and sandbox uploads end to end using ephemeral files, Judge0 execution inside Kata-backed VMs, AST concept enforcement, and Azure OpenAI feedback generation.

Before live student data is sent through this pipeline, Azure OpenAI privacy readiness must be confirmed.

### Deliverables

- [ ] AST checker supports a merged `Concepts Covered` whitelist built from course defaults plus assignment additions
- [ ] AST checker detects future-concept usage before execution and records warnings per result
- [ ] Security-sensitive AST findings can hard-block execution when configured
- [ ] Allowed concepts context is injected into the Azure OpenAI prompt
- [ ] Judge0 integration via `httpx`
- [ ] Judge0 auth/config wiring documented and validated
- [ ] Kata runtime validated as the planned Judge0 isolation layer
- [ ] Judge0 resource limits configured: 10s timeout target, 256MB memory limit target, network-disabled student execution
- [ ] language-to-Judge0 mapping implemented for current M1 supported language(s)
- [ ] pytest execution via Judge0
- [ ] pytest output parser returns structured test results
- [ ] Judge0 structured status handling integrated into grading outcomes
- [ ] Judge0 compile/runtime metadata captured for non-persistent grading feedback and status shaping
- [ ] `python_submitty_utils` output normalization integrated
- [ ] Minimal test and artifact management for M1:
  - upload/edit pytest file bodies through storage-backed artifact references
  - derive `TestCase` projections from the app-owned `config.json` for querying/UI as needed
  - keep human-authored grading fields in the app-owned config rather than duplicating them in `TestCase`
  - upload and run a model solution against the test suite
- [ ] model solution validation runs through Judge0, not on the host
- [ ] Azure OpenAI integration for rubric-context explanation and feedback generation
- [ ] Student sandbox UI shows an auto-populated LLM feedback textbox beside test-case results after each run
- [ ] Azure token usage logged to `run_summaries` or equivalent non-sensitive metadata storage
- [ ] Persistent run summaries and logs store aggregate non-identifying categories only; no filenames, identifiers, tracebacks, or detailed failure text
- [ ] Sensitive debug traces, if temporarily enabled, are rotated aggressively and purged within `24h`
- [ ] Azure OpenAI zero-retention/privacy posture confirmed before live student grading
- [ ] UVU/Microsoft FERPA coverage assumption confirmed before live student grading
- [ ] Hallucination guard enforced: tests remain ground truth and the LLM explains rather than re-evaluates correctness
- [ ] Celery grading chain supports both official runs and sandbox runs
- [ ] Celery worker concurrency aligned to documented Judge0 + Kata execution capacity
- [ ] `GET /runs/{id}/status` endpoint returns `queue`/`run`/`complete`/`failure` state from Redis-backed transient run status
- [ ] Staff and student views poll `GET /runs/{id}/status` every `2s` while state is `queue` or `run`
- [ ] Monaco-backed code review and editor workflows are ready where Sprint 2 execution results surface code context
- [ ] Failed jobs retry up to 3 times with backoff
- [ ] Timeout handling frees the worker immediately and records `failed:timeout`
- [ ] Judge0 submission/result deletion is verified after each official and sandbox execution, including `DELETE /submissions/{token}` after retrieval
- [ ] Kata-backed execution artifact deletion is verified after each official and sandbox execution
- [ ] Official review surfaces use derived artifacts and structured app data only; no raw student-submission download workflow is introduced
- [ ] Cleanup destroys extracted student files, generated code artifacts, and temporary feedback files at the end of each official or sandbox run

### Explicit M2 Deferrals

- [ ] Automated Canvas feedback attachment/distribution
- [ ] LLM-assisted rubric extraction from PDF or plain text
- [ ] AI-assisted test generation
- [ ] Inline in-editor LLM annotation markers for Monaco code review surfaces
- [ ] Persistent student history, saved projected runs, or downloadable student feedback files
- [ ] Student plagiarism detection UX
- [ ] Manual or non-code grading workflows
- [ ] In-app grade overrides or feedback editing for official-run review

### Exit Criteria

An instructor uploads an official batch covering: 1 future-concept warning, 1 hard-block case, 1 timeout, 1 correct solution, and 1 broken solution. Hard-block files do not execute. Warning cases still execute and surface warnings. The system produces structured results, makes the staff CSV and feedback ZIP available through separate downloads, and destroys temporary student artifacts after the request concludes. Separately, a student opens a globally visible sandbox assignment, uploads code, receives a projected score and feedback on screen, and loses access to those artifacts once the session ends.

---

## Sprint 3 - Student Sandbox + Instructor Batch UX + Export Packaging

### Goal

Students can use the ephemeral sandbox, and staff can monitor official runs, inspect in-session results, and download the official CSV and feedback ZIP artifacts.

### Deliverables

#### Student sandbox

- [ ] Student course list and per-course assignment selection UI
- [ ] Student upload flow for supported assignment file formats
- [ ] Sandbox rate limiter enforces `5 uploads per hour` per sandbox session
- [ ] Student projected score view
- [ ] Student projected feedback view with warnings and test summaries
- [ ] Sandbox workspace shows remaining uploads in the current hour before and after each run
- [ ] Sandbox limit-reached state explains the `5 uploads per hour` cap and handles backend `429` responses clearly
- [ ] Student messaging makes zero-retention behavior explicit
- [ ] Student session cleanup clears projected results on exit/completion

#### Instructor batch run UX

- [ ] Official run list view shows assignment, uploader, aggregate status, and section-aware context
- [ ] In-session official run detail view shows:
  - current processing counts
  - per-student pass/fail state
  - warning and hard-block summaries
  - unmatched filename failures
- [ ] Result preview supports per-student feedback inspection before download
- [ ] Official review stays preview-only in M1 with no in-app grade override or feedback editing
- [ ] Staff can filter official run results by success, warning, hard-block, timeout, or parse failure
- [ ] Staff can view plagiarism-check status and active-session similarity-report availability for the current official run
- [ ] MOSS output is visible only during the active official-run review session and is not persisted afterward
- [ ] Clear warning that detailed official results are ephemeral and will be destroyed after download/request completion

#### Export packaging

- [ ] CSV export for Canvas-compatible grades
- [ ] Feedback renderer produces per-student staff-facing feedback artifacts
- [ ] Feedback packaging produces a per-run ZIP of per-student HTML feedback artifacts
- [ ] Staff can download the Canvas-grade CSV and feedback ZIP through separate actions with stable naming and actionable errors
- [ ] Optional MOSS result is viewable only inside the active official-run workflow when plagiarism detection is run
- [ ] Export naming convention uses assignment identifier + generated export identifier
- [ ] Export fails safely with actionable errors if packaging is incomplete
- [ ] Export flow fails fast with actionable errors for malformed or unrecognized ZIP submissions
- [ ] Docs state that grade import back into Canvas is assumed, while automated feedback upload remains out of scope for M1

### Exit Criteria

A student opens the sandbox, selects a course, selects an assignment, uploads code, sees a projected score and feedback on screen together with remaining sandbox quota, and then loses access to those artifacts after session exit. An instructor runs an official batch, watches progress in the UI, previews at least one student result, downloads the staff CSV and feedback ZIP through separate actions, and sees the run complete without leaving retained student files on the server.

---

## Sprint 4 - Integration Testing + FERPA/Compliance Hardening

### Goal

Validate the full M1 workflow under realistic conditions and verify the zero-retention guarantees for both official and sandbox usage.

### Activities

- [ ] End-to-end official-run test with a realistic class-size dataset (30-50 submissions)
- [ ] End-to-end student sandbox test for assignment selection, upload, feedback, and cleanup
- [ ] Validate staff OAuth flow:
  - `@uvu.edu` login succeeds
  - non-UVU login is rejected
- [ ] Validate public sandbox visibility flow:
  - sandbox shows only assignments explicitly marked sandbox-enabled
  - sandbox does not require student login or UVU ID entry
- [ ] Validate access control:
  - admin, instructor, and IA routes respect role checks
  - instructors can view assigned courses but edit only explicitly assigned sections
  - IAs can view only explicitly assigned sections for grading validation and cannot edit assignment configuration
  - sandbox users can access public sandbox features but not staff workflow pages
- [ ] Validate security:
  - network access from Judge0 student execution is blocked
  - Kata-backed VM isolation is active in the planned execution environments
  - malicious ZIP path traversal is rejected
  - configured hard-block findings stop execution
- [ ] Validate timeout handling with `while True: pass`
- [ ] Validate export totals against rubric config and pytest results
- [ ] Validate optional MOSS submission uses only ephemeral files and does not retain local copies after completion
- [ ] Validate active-session MOSS results are surfaced during official review without creating a persistent post-run link
- [ ] Validate cleanup:
  - extracted official files are deleted after request completion
  - sandbox upload artifacts are deleted after session exit/completion
  - temporary feedback artifacts are deleted after packaging
  - no student code remains in persistent storage
- [ ] Smoke test on the Dell-workstation deployment
- [ ] Deployment configuration reviewed
- [ ] README updated with deployment and operating notes
- [ ] Demo walkthrough recorded

### Exit Criteria

A teammate unfamiliar with the codebase can complete the M1 workflow without assistance:

1. sign in with a `@uvu.edu` staff account
2. create or open an assignment
3. use the wizard or import a valid `config.json`
4. confirm the course defaults, assignment concept additions, and merged effective `Concepts Covered` list
5. download the current `config.json`
6. upload a Canvas ZIP or use the student sandbox flow
7. monitor grading progress
8. download the staff CSV and feedback ZIP when using the official path
9. verify no student files remain on the server after completion or session exit

---

## Tech Stack Reference

### Full Stack

| Layer                | Technology                | Version                     | Role                                               |
| -------------------- | ------------------------- | --------------------------- | -------------------------------------------------- |
| Frontend framework   | Next.js                   | 14.x (App Router)           | Staff and student UI                               |
| UI language          | TypeScript                | 5.x                         | Type safety across frontend                        |
| Code editor          | Monaco Editor             | current                     | Locally hosted code editing, preview, and review   |
| Auth                 | NextAuth.js               | 5.x (Auth.js)               | Staff Microsoft OAuth in M1                        |
| Backend framework    | FastAPI                   | 0.110.x                     | API, business logic, prompt engine                 |
| Backend language     | Python                    | 3.11+                       | Grading pipeline, AST checks, export packaging     |
| Task queue           | Celery                    | 5.3.x                       | Async official and sandbox grading jobs            |
| Message broker       | Redis                     | 7.x                         | Celery broker + transient job state                |
| Database             | PostgreSQL                | 16.x                        | Non-sensitive metadata only                        |
| ORM                  | SQLAlchemy                | 2.x                         | DB access from FastAPI                             |
| Migrations           | Alembic                   | 1.13.x                      | Schema versioning                                  |
| Containerization     | Docker + Compose          | 25.x                        | Dev environment + app/integration services         |
| AI inference         | Azure OpenAI API          | current approved deployment | Feedback generation                                |
| Plagiarism detection | mosspy                    | current                     | Optional Stanford MOSS submission for staff review |
| Grade export         | Standard export packaging | current                     | Staff-facing export packaging                      |
| Code highlighting    | Monaco Editor + Prism.js  | current / 1.29.x            | Interactive editor/review plus lightweight preview |

### Grading Pipeline

| Component                 | Technology                           | Role                                                                  |
| ------------------------- | ------------------------------------ | --------------------------------------------------------------------- |
| Static analysis           | Python `ast`                         | Enforce `Concepts Covered` before execution                           |
| VM isolation              | Kata Containers                      | Canonical VM-based isolation layer for Judge0 execution               |
| Execution engine          | Judge0 CE                            | Sandboxed student code execution with structured status metadata      |
| HTTP client               | httpx                                | FastAPI -> Judge0 async REST calls                                    |
| Test framework            | pytest                               | Official and sandbox test execution                                   |
| Output normalization      | python_submitty_utils                | Whitespace/encoding normalization                                     |
| HTML output               | Server-side templating               | Official student feedback file generation                             |
| Config authoring          | Wizard + `config.json` import/export | App-owned assignment config setup with wizard-first authoring |
| PDF/text rubric ingestion | Deferred                             | M2, not M1                                                            |

### Infrastructure Notes

| Component        | Location                          | Note                                                                                        |
| ---------------- | --------------------------------- | ------------------------------------------------------------------------------------------- |
| PostgreSQL       | Dell workstation local service    | Metadata only, no student submissions                                                       |
| Redis            | Dell workstation local service    | Celery broker + transient status                                                            |
| Judge0 + Kata    | Dell workstation local Docker     | Judge0 execution service with planned Kata VM isolation and explicit `DELETE /submissions/{token}` post-result deletion |
| Azure OpenAI     | University-approved Azure tenant  | LLM inference path for M1                                                                   |
| Next.js          | Dell workstation local service    | Canonical M1 frontend host                                                                  |
| FastAPI + Celery | Dell workstation local services   | Canonical M1 API and workers                                                                |

Teammate machines may be used for local and integration-style validation, but the Dell workstation remains the current M1 deployment target.

---

## Functional Requirements

### FR-01 - Admin / Identity

| ID      | Requirement                                                                                                                                                                              | Sprint |
| ------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------ |
| FR-01.1 | Admin can create, edit, and deactivate staff accounts                                                                                                                                    | S1     |
| FR-01.2 | Admin can assign roles: admin, instructor, ia                                                                                                                                            | S1     |
| FR-01.3 | Admin can maintain staff access by course or section                                                                                                                                     | S1     |
| FR-01.4 | Staff can authenticate through Microsoft OAuth with a `@uvu.edu` account for admin, instructor, and IA workflows                                                                | S1     |
| FR-01.5 | System does not require student-specific authentication or roster-based authorization for sandbox visibility | S1     |

### FR-02 - Staff Assignment and Config Workflows

| ID       | Requirement                                                                                                                                                                                                                 | Sprint |
| -------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------ |
| FR-02.1  | Authorized assignment-config staff can create assignments with name, course linkage, due date, and Canvas reference metadata                                                                                                | S1     |
| FR-02.2  | Authorized assignment-config staff can use a comprehensive wizard to generate valid `config.json`                                                                                                                           | S1     |
| FR-02.3  | Authorized assignment-config staff can import a validated `config.json`                                                                                                                                                     | S1     |
| FR-02.4  | Authorized assignment-config staff can edit all instructor-relevant stored config fields through a rendered form and download the current `config.json`                                                                     | S1     |
| FR-02.5  | Authorized assignment-config staff can define course-level `Concepts Covered` defaults and assignment-level additive concept entries, with a merged effective-list preview                                                                                                                                   | S1     |
| FR-02.6  | Instructor or IA can upload a bulk Canvas ZIP for official grading                                                                                                                                                          | S1     |
| FR-02.7  | Instructors can manage the app-owned grading config, storage-backed pytest artifacts, derived `TestCase` projections as needed, and run a model solution through Judge0; IAs remain read-only for assignment configuration | S2     |
| FR-02.8  | Instructor or IA can monitor official-run status and inspect in-session results                                                                                                                                             | S3     |
| FR-02.9  | Instructor or IA can optionally run plagiarism detection for an authorized official run and review the result during the active official-run session only                                                                    | S3     |
| FR-02.10 | Instructor or IA can download a Canvas-grade CSV and a per-run feedback ZIP as separate official-run outputs                                                                                                                | S3     |

### FR-03 - Student Sandbox

| ID      | Requirement                                                                                                                                                                                                                                                                                                        | Sprint |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------ |
| FR-03.1 | Student can access sandbox course and assignment listings without student authentication                                                                                                                                                                                                                           | S1     |
| FR-03.2 | Student can see only courses and assignments explicitly marked sandbox-enabled; sandbox visibility is not derived from roster or enrollment data | S3     |
| FR-03.3 | Student can upload code for projected grading                                                                                                                                                                                                                                                                      | S3     |
| FR-03.4 | Student can view projected score, warnings, test results, and on-screen feedback in the sandbox UI                                                                                                                                                                                                                 | S3     |
| FR-03.5 | Student projected results are destroyed when processing completes or the session exits                                                                                                                                                                                                                             | S3     |
| FR-03.6 | Student cannot access staff workflow pages or official export artifacts                                                                                                                                                                                                                                            | S3     |
| FR-03.7 | Student sandbox uploads are rate-limited to `5 uploads per hour` per sandbox session                                                                                                                                                                                | S3     |
| FR-03.8 | Student sandbox auto-displays an LLM feedback textbox next to test results after each run; feedback is explanation-only and does not modify scoring                                                                                                                                                                | S3     |
| FR-03.9 | Student sandbox workspace shows remaining uploads in the current hour and a clear limit-reached message when the rate limit is hit                                                                                                                                                                    | S3     |

### FR-04 - Ephemeral Official Processing

| ID       | Requirement                                                                                                                                      | Sprint |
| -------- | ------------------------------------------------------------------------------------------------------------------------------------------------ | ------ |
| FR-04.1  | System parses Canvas uploads into a transient official run                                                                                       | S1     |
| FR-04.2  | System extracts ZIP contents only into RAM or an ephemeral temp directory                                                                        | S1     |
| FR-04.3  | System rejects ZIP path traversal attempts before extraction                                                                                     | S1     |
| FR-04.4  | System does not create persistent student submission records for official runs                                                                   | S1     |
| FR-04.5  | System runs AST concept checks before execution                                                                                                  | S2     |
| FR-04.6  | System executes pytest via Judge0 with resource limits and structured execution statuses                                                         | S2     |
| FR-04.7  | System sends code, test results, and allowed-concepts context to Azure OpenAI                                                                    | S2     |
| FR-04.8  | System generates per-student staff-facing feedback artifacts using Canvas identifiers                                                            | S2     |
| FR-04.9  | System can submit the current ephemeral official run to Stanford MOSS via `mosspy` for staff review                                              | S3     |
| FR-04.10 | System destroys student files and detailed official-run artifacts after the request concludes                                                    | S2     |
| FR-04.11 | Official grading jobs run asynchronously via Celery                                                                                              | S2     |
| FR-04.12 | System rejects malformed or non-Canvas ZIPs before queueing official grading work                                                                | S1     |
| FR-04.13 | System logs Azure token usage as sanitized run metadata for official runs without persisting MOSS report references                              | S2     |
| FR-04.14 | System deletes or invalidates Judge0 submission/result artifacts and tears down Kata-backed execution state immediately after result verification and retrieval so student code is not retained in the execution service | S2     |

### FR-05 - Ephemeral Student Sandbox Processing

| ID      | Requirement                                                                                                                                                    | Sprint |
| ------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------ |
| FR-05.1 | System accepts student sandbox uploads without creating persistent student profiles, roster mappings, or submission history | S3     |
| FR-05.2 | System runs the same AST, execution, and feedback pipeline for sandbox grading with sandbox-appropriate output formatting                                      | S3     |
| FR-05.3 | System presents sandbox feedback on screen only and does not produce downloadable artifacts                                                                    | S3     |
| FR-05.4 | System destroys student sandbox files and detailed feedback artifacts after completion or session exit                                                         | S3     |
| FR-05.5 | System logs Azure token usage as non-sensitive metadata for sandbox runs                                                                                       | S2     |

---

## Non-Functional Requirements

### Performance

| ID     | Requirement                                            | Target                                                      |
| ------ | ------------------------------------------------------ | ----------------------------------------------------------- |
| NFR-P1 | ZIP upload acceptance time                             | < 2s for files up to 50MB                                   |
| NFR-P2 | Concurrent grading throughput                          | documented safe concurrency floor from Dell-memory benchmark |
| NFR-P3 | 200-submission official batch completion               | < 40 min on the Dell workstation                            |
| NFR-P4 | Status polling response time                           | < 200ms                                                     |
| NFR-P5 | Export packaging overhead after grading                | < 2 min for 200 submissions                                 |
| NFR-P6 | Student sandbox projected result latency               | fast enough to feel interactive for normal assignment files |
| NFR-P7 | Azure token usage is measurable per run and assignment | available in non-sensitive run metadata                     |

### Security

| ID      | Requirement                                                                                                                      |
| ------- | -------------------------------------------------------------------------------------------------------------------------------- |
| NFR-S1  | Judge0 executes student code with network access disabled                                                                        |
| NFR-S2  | Judge0 memory and timeout limits are enforced                                                                                    |
| NFR-S3  | Kata Containers is the planned VM-based isolation layer for Judge0 execution                                                      |
| NFR-S4  | ZIP extraction validates all paths before any file is written                                                                    |
| NFR-S5  | All app endpoints require a valid session token except auth entrypoints and health checks                                        |
| NFR-S6  | Staff OAuth callback rejects non-`@uvu.edu` accounts                                                                             |
| NFR-S7  | Detailed student artifacts are stored only in ephemeral working space during official and sandbox runs                           |
| NFR-S8  | Cleanup routines remove extracted student files, Judge0 artifacts, Kata execution state, and generated feedback artifacts immediately after verification/retrieval and workflow completion |
| NFR-S9  | MOSS integration uses only ephemeral official-run files and does not create additional persistent student code copies            |
| NFR-S10 | Sandbox rate limiting is enforced without student authentication, using sandbox-session controls rather than student identity                                                      |

### Reliability

| ID     | Requirement                                                                                         |
| ------ | --------------------------------------------------------------------------------------------------- |
| NFR-R1 | Grading job failure does not affect other queued jobs                                               |
| NFR-R2 | Failed jobs retry up to 3 times before permanent failure                                            |
| NFR-R3 | Timeout or packaging failure returns actionable errors to users                                     |
| NFR-R4 | Persistent metadata remains recoverable without retaining student submissions                       |
| NFR-R5 | Celery concurrency does not exceed the Dell workstation's documented Judge0 + Kata memory-tested execution-capacity limits |

### Compliance

| ID     | Requirement                                                                                                                  |
| ------ | ---------------------------------------------------------------------------------------------------------------------------- |
| NFR-C1 | No student submission content is retained in persistent storage                                                              |
| NFR-C2 | Student code and detailed feedback artifacts are destroyed after the official request completes or the sandbox session exits |
| NFR-C3 | Only non-sensitive metadata is stored in the database                                                                        |
| NFR-C3.1 | Persistent logs and run summaries exclude filenames, student identifiers, traceback bodies, and detailed failure text     |
| NFR-C4 | Azure OpenAI usage must follow the university-approved zero-retention/privacy posture                                        |
| NFR-C5 | Plagiarism detection results are staff-facing review artifacts and must not require persistent storage of student code       |
| NFR-C6 | MOSS report handling must not imply local persistence of the external report contents                                        |

---

## Product Backlog

1 story point ~= 2-4 hours focused work.  
Priority: **Must** = M1 required · **Should** = M1 if capacity · **Won't** = post-M1

### Epic 1 - Environment and Infrastructure (Sprint 0)

| ID    | Story                                                                 | Pts | Priority |
| ----- | --------------------------------------------------------------------- | --- | -------- |
| E0-01 | ER and class diagrams reviewed as current architecture references     | 2   | Must     |
| E0-02 | FastAPI router skeleton and prompt-boundary plan reviewed             | 2   | Must     |
| E0-03 | Staff and sandbox wireframes reviewed with shared interface contracts | 3   | Must     |
| E0-04 | Route structure and component hierarchy reviewed before Sprint 1      | 2   | Must     |
| E0-05 | Implementation action items captured for Sprint 0 signoff             | 1   | Must     |

**Epic 0 total: 10 points**

---

### Epic 1 - Environment and Infrastructure (Sprint 0)

| ID    | Story                                                                                                                                                  | Pts | Priority |
| ----- | ------------------------------------------------------------------------------------------------------------------------------------------------------ | --- | -------- |
| E1-01 | Docker Compose for local development and integration-style testing: postgres, redis, celery, fastapi, nextjs, and Judge0-compatible execution topology | 2   | Must     |
| E1-02 | FastAPI project structure with routers, schemas, services, and prompt boundaries                                                                       | 2   | Must     |
| E1-03 | Next.js project structure with App Router                                                                                                              | 2   | Must     |
| E1-04 | PostgreSQL schema + Alembic initial migration for metadata-only tables                                                                                 | 2   | Must     |
| E1-05 | Celery + Redis wiring                                                                                                                                  | 1   | Must     |
| E1-06 | Judge0 execution service reachable with documented auth, Kata isolation, and deletion strategy                                                         | 3   | Must     |
| E1-07 | Dell-workstation deployment topology documented for production services                                                                                | 1   | Must     |
| E1-08 | Monaco locally hosted in the frontend scaffold for planned M1 editor and review workflows                                                              | 2   | Must     |
| E1-09 | `.env.example`, README, CI checks                                                                                                                      | 2   | Must     |

**Epic 1 total: 17 points**

---

### Epic 2 - Auth and Identity (Sprint 1)

| ID    | Story                                                                     | Pts | Priority |
| ----- | ------------------------------------------------------------------------- | --- | -------- |
| E2-01 | Staff NextAuth Microsoft OAuth provider                                   | 2   | Must     |
| E2-02 | Staff callback rejects non-`@uvu.edu` logins                              | 1   | Must     |
| E2-03 | Role-based route protection for admin, instructor, IA, and student access | 3   | Must     |
| E2-04 | Role-based API protection                                                 | 2   | Must     |
| E2-05 | Admin manages staff roles and course access                               | 2   | Must     |
| E2-06 | Public student sandbox entry path without student authentication or persistent student profile storage | 2   | Must     |

**Epic 2 total: 12 points**

---

### Epic 3 - Assignment and Config Setup (Sprint 1)

| ID    | Story                                                                                             | Pts | Priority |
| ----- | ------------------------------------------------------------------------------------------------- | --- | -------- |
| E3-01 | Assignment creation form with course linkage and Canvas metadata                                  | 2   | Must     |
| E3-02 | Comprehensive wizard for instructor-relevant assignment/rubric/config fields                      | 3   | Must     |
| E3-03 | Wizard generates valid `config.json`                                                              | 2   | Must     |
| E3-04 | Validated `config.json` import UI                                                                 | 3   | Must     |
| E3-05 | Stored config form/view renders all instructor-relevant editable fields from the app-owned config | 3   | Must     |
| E3-06 | Current `config.json` is downloadable                                                             | 1   | Must     |
| E3-07 | Course defaults editor plus assignment concept-additions editor with merged preview            | 3   | Must     |

**Epic 3 total: 17 points**

---

### Epic 4 - Ephemeral Submission Ingestion (Sprint 1)

| ID    | Story                                                                         | Pts | Priority |
| ----- | ----------------------------------------------------------------------------- | --- | -------- |
| E4-01 | Canvas ZIP upload endpoint with size + type validation                        | 2   | Must     |
| E4-02 | Reject malformed or non-Canvas ZIPs before queueing                           | 2   | Must     |
| E4-03 | ZIP path traversal protection                                                 | 2   | Must     |
| E4-04 | Ephemeral extraction workflow in RAM or temp directory only                   | 2   | Must     |
| E4-05 | Filename parser for Canvas uploads using Canvas identifiers                   | 2   | Must     |
| E4-06 | Unmatched filename/malformed archive reporting                                | 2   | Must     |
| E4-07 | Transient official-run metadata record without persistent student submissions | 1   | Must     |

**Epic 4 total: 13 points**

---

### Epic 5 - Grading Pipeline and AI Enrichment (Sprint 2)

| ID    | Story                                                                                                                           | Pts | Priority |
| ----- | ------------------------------------------------------------------------------------------------------------------------------- | --- | -------- |
| E5-01 | AST checker for merged `Concepts Covered` whitelist enforcement                                                             | 4   | Must     |
| E5-02 | Warning vs hard-block concept/security handling                                                                                 | 2   | Must     |
| E5-03 | Judge0 integration with Kata-backed isolation, resource limits, language mapping, structured statuses, and post-result deletion | 5   | Must     |
| E5-04 | pytest execution + output parsing + normalization                                                                               | 4   | Must     |
| E5-05 | Minimal pytest artifact management per assignment                                                                               | 3   | Must     |
| E5-06 | Keep test-to-rubric and student-visible metadata in the app-owned `config.json`, with derived `TestCase` projections when needed | 2   | Must     |
| E5-07 | Run model solution against assignment tests through Judge0                                                                      | 1   | Must     |
| E5-08 | Azure OpenAI integration with concept-context prompting and hallucination guard                                                 | 4   | Must     |
| E5-09 | Celery grading chain for official and sandbox runs                                                                              | 3   | Must     |
| E5-10 | Timeout, retry, and cleanup guarantees                                                                                          | 2   | Must     |
| E5-11 | Azure token usage logging in `run_summaries` or equivalent metadata storage                                                     | 2   | Must     |
| E5-12 | Celery worker concurrency aligned to Judge0 + Kata execution-capacity limits                                                    | 1   | Must     |
| E5-13 | Optional Stanford MOSS integration via `mosspy` using ephemeral official-run files only                                         | 3   | Should   |

**Epic 5 total: 36 points**

---

### Epic 6 - Student Sandbox (Sprint 3)

| ID    | Story                                                                         | Pts | Priority |
| ----- | ----------------------------------------------------------------------------- | --- | -------- |
| E6-01 | Student course and assignment selection UI                                    | 2   | Must     |
| E6-02 | Student upload flow for projected grading                                     | 3   | Must     |
| E6-03 | Sandbox rate limiter enforcing `5 uploads per hour` per sandbox session      | 2   | Must     |
| E6-04 | On-screen projected score and feedback view                                   | 3   | Must     |
| E6-05 | Student-facing warnings, quota messaging, and zero-retention messaging        | 2   | Must     |
| E6-06 | Session-exit and completion cleanup for sandbox results                       | 2   | Must     |
| E6-07 | Student route isolation from staff pages and export flows                     | 2   | Must     |

**Epic 6 total: 16 points**

---

### Epic 7 - Instructor Batch Run UX (Sprint 3)

| ID    | Story                                                                                     | Pts | Priority |
| ----- | ----------------------------------------------------------------------------------------- | --- | -------- |
| E7-01 | Official run list with aggregate status and section-aware context                         | 2   | Must     |
| E7-02 | In-session official-run detail view with counts, warnings, and failures                   | 2   | Must     |
| E7-03 | `GET /runs/{id}/status` live polling at `2s` cadence for per-run status                   | 1   | Must     |
| E7-04 | Per-student HTML preview before export                                                    | 2   | Must     |
| E7-05 | Filtering for success, warning, hard-block, timeout, parse failure, and plagiarism status | 1   | Should   |
| E7-06 | Surface active-session MOSS availability without persisting a post-run link              | 1   | Must     |

**Epic 7 total: 9 points**

---

### Epic 8 - Export Packaging (Sprint 3)

| ID    | Story                                                                                         | Pts | Priority |
| ----- | --------------------------------------------------------------------------------------------- | --- | -------- |
| E8-01 | CSV export for Canvas-compatible grades                                                       | 2   | Must     |
| E8-02 | Per-student staff-facing feedback renderer                                                    | 2   | Must     |
| E8-03 | Feedback ZIP packaging builder for per-student HTML official-run artifacts                    | 2   | Must     |
| E8-04 | Separate CSV and feedback-ZIP download workflow with stable naming and actionable errors      | 1   | Must     |
| E8-05 | Graceful failure for malformed or unrecognized ZIP submissions                                | 2   | Must     |
| E8-06 | Documentation note: Canvas grade import assumed; automated feedback upload is out of scope for M1 | 1   | Must     |

**Epic 8 total: 10 points**

---

## Action Items

- [ ] Benchmark safe Judge0 + Kata concurrency on the Dell workstation and document worker caps before Sprint 2 implementation begins.
- [ ] Validate that `docker-compose.testing.yml` remains documented as an integration harness even where local machines cannot fully reproduce the planned Kata isolation setup.
- [ ] Keep `docs/backend_implementation/easton_implementation/ClassFlow_diagram.md` separate from the current Jaxon working diagrams to avoid mixing older and newer planning artifacts.

---

### Backlog Summary

| Epic      | Name                               | M1 Points      | Sprint |
| --------- | ---------------------------------- | -------------- | ------ |
| E0        | Architecture and Design            | 10             | S0     |
| E1        | Environment and Infrastructure     | 17             | S0     |
| E2        | Auth and Identity                  | 12             | S1     |
| E3        | Assignment and Config Setup        | 17             | S1     |
| E4        | Ephemeral Submission Ingestion     | 13             | S1     |
| E5        | Grading Pipeline and AI Enrichment | 36             | S2     |
| E6        | Student Sandbox                    | 16             | S3     |
| E7        | Instructor Batch Run UX            | 9              | S3     |
| E8        | Export Packaging                   | 10             | S3     |
| **Total** |                                    | **140 points** |        |

### Capacity Reality Check

```text
Conservative (35 hrs/week, 8 weeks, 3 hrs/point): ~93 points
Optimistic   (65 hrs/week, 8 weeks, 3 hrs/point): ~173 points
With Sprint 4 buffer absorbed:                     ~185-195 points realistic
```

With the student sandbox restored to M1 and the operational hardening stories added, the backlog remains above the conservative delivery line but inside the realistic range for a 5-developer team. If priorities tighten:

- protect Epics 1-5 as the core shared platform and grading path
- protect the Must stories in Epic 6 before adding staff UX polish
- cut MOSS and staff filtering polish before cutting zero-retention guarantees or config round-trip behavior

---

## Definition of Done

A story is complete when:

- [ ] feature works end to end, not just in isolation
- [ ] reviewed in a pull request by at least one teammate
- [ ] no TypeScript or Python type errors on CI
- [ ] Ruff and ESLint pass
- [ ] at least one unit or integration test covers the happy path
- [ ] edge cases handled: bad input, malformed ZIP, unmatched filename, non-UVU login, timeout, cleanup failure, sandbox exit cleanup
- [ ] no hardcoded secrets or environment-specific values
- [ ] docs updated if setup or behavior changed
- [ ] zero-retention cleanup is verified for any story that touches student code or student-facing grading artifacts

---

## Hard Scope Boundaries - M1

These are explicitly out of scope for M1. Do not pull them in under deadline pressure:

- official university SSO integration beyond staff Microsoft OAuth + `@uvu.edu` domain restriction
- Canvas LTI or grade passback API integration
- automated bulk feedback upload/distribution into Canvas
- manual or non-code grading workflows
- in-app grade override or feedback-editing workflows for official review
- persistent submission history or resubmission timelines
- downloadable student sandbox artifacts
- LLM-assisted PDF/text rubric conversion
- AI-assisted test generation
- PDF feedback generation
- multi-language support beyond Python
- analytics or class-wide reporting
