# UVU Autograder v1 - Canonical Backlog and Sprint Plan

> Supporting architecture and product decisions live in `JL_AGv1_decisions.md` and `JL_AGv1_technical_specs.md`. This file is the canonical backlog and sprint execution document.

> Target: Testable M1 for zero-retention grading and sandbox workflows for `@uvu.edu` users
> Team: 5 developers, half time (~35-65 hrs/week total)
> Window: 8-9 weeks
> Backlog tracked in: GitHub Projects (Issues + Milestones)
> Last updated: May 4, 2026

---

## Planning Context

Implementation decisions, permission semantics, storage contracts, and technical architecture are maintained in:

- `JL_AGv1_decisions.md`
- `JL_AGv1_technical_specs.md`

This backlog focuses on sprint planning, deliverables, and acceptance criteria.

Supporting note: `implementation_folder/ClassFlow_diagram.md` remains a non-canonical working artifact. The canonical diagram set for implementation lives in `implementation_folder/jaxon_implementation/diagrams/`.

---

## Epic 0 - Architecture + Design

Epic 0 captures the parallel architecture and UI design work that de-risks Sprint 1 implementation.

### Goal

Backend architecture, frontend structure, and shared contracts are explicit enough that Sprint 1 can begin without re-litigating core design decisions.

### Deliverables

- [ ] ER diagram reviewed as a canonical persistent-data reference
- [ ] Class and pipeline diagrams reviewed as canonical workflow references
- [ ] FastAPI router skeleton and request or response boundary plan reviewed
- [ ] Prompt integration boundaries documented
- [ ] Frontend wireframes completed for staff and sandbox flows
- [ ] Route structure and component hierarchy reviewed
- [ ] Shared API and UI contracts reviewed at the end of the parallel track

### Exit Criteria

The team has reviewed the canonical diagrams, shared backend/frontend contracts, and wireframes before Sprint 1 begins. No Sprint 1 feature work should start while those artifacts are still materially in flux.

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
  - `users`, `roles`, `courses`, `sections`, `staff_access`, `assignments`, `assignment_configs`, `concept_sets`, `assignment_concept_overrides`, `assignment_artifacts`, `test_cases`, `run_summaries`
- [ ] Redis running locally
- [ ] Celery connected to Redis
- [ ] Judge0 execution service running locally or in a compatible integration environment
- [ ] Judge0 service auth/config wiring documented for FastAPI and Celery
- [ ] Kata runtime validation documented for canonical Judge0 execution
- [ ] Railway deployment shape documented for `nextjs`, `fastapi`, `postgres`, `redis`, and `celery`, plus separate Judge0 execution infrastructure
- [ ] Docker Compose supports local development and integration-style testing for `postgres`, `redis`, `celery`, `fastapi`, `nextjs`, and the chosen Judge0 test/integration topology
- [ ] Judge0 submission/result deletion strategy documented and validated against the zero-retention requirement
- [ ] Monaco Editor hosted locally and wired into the frontend scaffold for canonical M1 editor/review workflows
- [ ] `.env.example` documents required environment variables including Azure OpenAI settings
- [ ] Backend/frontend shared interface contracts reviewed before Sprint 1 kickoff
- [ ] Frontend wireframes and component hierarchy reviewed before Sprint 1 kickoff
- [ ] README gets the full stack running locally
- [ ] Seed script creates 1 course, 1 assignment, 1 generated `config.json`, 1 concepts default set, and 1 model solution

### Exit Criteria

`docker compose -f docker-compose.testing.yml up` brings the testing stack online. FastAPI health check returns 200. A test Celery task runs successfully. Judge0 executes a Hello World Python script through the backend integration path. The Judge0 deletion strategy is validated for test submissions. Kata runtime requirements are documented for canonical execution environments even if the local Compose harness does not perfectly reproduce them. Monaco is available through the frontend scaffold for code-view and editor workflows. The seeded assignment loads with its stored config and concepts defaults. The team has signed off on the shared backend/frontend contract before Sprint 1 begins.

---

## Sprint 1 - Shadow SSO + Assignment/Config Setup + Ephemeral Ingestion

### Goal

UVU users can authenticate, staff can configure assignments through either the wizard or raw JSON, and official batch uploads can be prepared without persistent student submission records.

### Deliverables

- [ ] NextAuth Microsoft OAuth provider configured
- [ ] NextAuth callback rejects any login not ending in `@uvu.edu`
- [ ] Role-based route protection in Next.js
- [ ] Role-based API protection in FastAPI
- [ ] Minimal staff role management for admin, instructor, and IA
- [ ] Student sign-in path exists for sandbox access without creating persistent student records
- [ ] Assignment creation form stores name, course linkage, due date, and Canvas reference metadata
- [ ] Basic config wizard captures core assignment/rubric/config fields
- [ ] Wizard generates valid `config.json`
- [ ] Raw `config.json` paste/import UI with validation and error display
- [ ] Stored config editor/view renders editable fields from the current `config.json`
- [ ] Staff can download the current `config.json`
- [ ] `Concepts Covered` checklist UI seeded from course timeline defaults
- [ ] Instructor override support for assignment-specific concepts selections
- [ ] Canvas ZIP upload endpoint with size and type validation
- [ ] Non-Canvas or otherwise unrecognized ZIPs rejected before queueing
- [ ] ZIP path traversal protection before extraction
- [ ] ZIP extraction implemented in RAM or an ephemeral temp directory only
- [ ] Canvas filename parser maps files to Canvas-provided identifiers
- [ ] Unmatched filename and malformed archive reporting in the staff UI
- [ ] Transient official-run creation with assignment link, uploader, timestamps, and file counts only

### Exit Criteria

An instructor signs in with a `@uvu.edu` account. A non-UVU login is rejected. The instructor creates an assignment through the wizard or by importing valid raw `config.json`, confirms the `Concepts Covered` selections, downloads the resulting `config.json`, uploads a Canvas ZIP for an explicitly assigned section, and the system parses the archive into a transient official run without storing student code persistently.

---

## Sprint 2 - Grading Pipeline + Azure OpenAI + Zero-Retention Controls

### Goal

The system grades official runs and sandbox uploads end to end using ephemeral files, Judge0 execution inside Kata-backed VMs, AST concept enforcement, and Azure OpenAI feedback generation.

Before live student data is sent through this pipeline, Azure OpenAI privacy readiness must be confirmed.

### Deliverables

- [ ] AST checker supports a course-aligned `Concepts Covered` whitelist
- [ ] AST checker detects future-concept usage before execution and records warnings per result
- [ ] Security-sensitive AST findings can hard-block execution when configured
- [ ] Allowed concepts context is injected into the Azure OpenAI prompt
- [ ] Judge0 integration via `httpx`
- [ ] Judge0 auth/config wiring documented and validated
- [ ] Kata runtime validated as the canonical Judge0 isolation layer
- [ ] Judge0 resource limits configured: 10s timeout target, 256MB memory limit target, network-disabled student execution
- [ ] language-to-Judge0 mapping implemented for current M1 supported language(s)
- [ ] pytest execution via Judge0
- [ ] pytest output parser returns structured test results
- [ ] Judge0 structured status handling integrated into grading outcomes
- [ ] Judge0 compile/runtime metadata captured for non-persistent grading feedback and status shaping
- [ ] `python_submitty_utils` output normalization integrated
- [ ] Minimal test and artifact management for M1:
  - upload/edit pytest file bodies through storage-backed artifact references
  - link each `TestCase` to one primary rubric criterion
  - store a student-visible description per `TestCase`
  - upload and run a model solution against the test suite
- [ ] model solution validation runs through Judge0, not on the host
- [ ] Azure OpenAI integration for rubric-context explanation and feedback generation
- [ ] Azure token usage logged to `run_summaries` or equivalent non-sensitive metadata storage
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
- [ ] Judge0 submission/result deletion is verified after each official and sandbox execution
- [ ] Kata-backed execution artifact deletion is verified after each official and sandbox execution
- [ ] Cleanup destroys extracted student files, generated code artifacts, and temporary feedback files at the end of each official or sandbox run

### Explicit M2 Deferrals

- [ ] Automated Canvas feedback attachment/distribution
- [ ] LLM-assisted rubric extraction from PDF or plain text
- [ ] AI-assisted test generation
- [ ] Persistent student history, saved projected runs, or downloadable student feedback files
- [ ] Student plagiarism detection UX

### Exit Criteria

An instructor uploads an official batch covering: 1 future-concept warning, 1 hard-block case, 1 timeout, 1 correct solution, and 1 broken solution. Hard-block files do not execute. Warning cases still execute and surface warnings. The system produces structured results, generates HTML feedback files, returns the export package, and destroys temporary student artifacts after the request concludes. Separately, a student signs in, uploads code for an assignment, receives a projected score and feedback on screen, and loses access to those artifacts once the session ends.

---

## Sprint 3 - Student Sandbox + Instructor Batch UX + Export Packaging

### Goal

Students can use the ephemeral sandbox, and staff can monitor official runs, inspect in-session results, and download the final CSV plus HTML feedback ZIP.

### Deliverables

#### Student sandbox

- [ ] Student course and assignment selection UI
- [ ] Student upload flow for supported assignment file formats
- [ ] Sandbox rate limiter enforces `5 uploads per hour` per authenticated student identity
- [ ] Student projected score view
- [ ] Student projected feedback view with warnings and test summaries
- [ ] Student messaging makes zero-retention behavior explicit
- [ ] Student session cleanup clears projected results on exit/completion

#### Instructor batch run UX

- [ ] Official run list view shows assignment, uploader, started time, completed time, and aggregate status
- [ ] In-session official run detail view shows:
  - current processing counts
  - per-student pass/fail state
  - warning and hard-block summaries
  - unmatched filename failures
- [ ] Result preview supports per-student HTML feedback inspection before download
- [ ] Staff can filter official run results by success, warning, hard-block, timeout, or parse failure
- [ ] Staff can view plagiarism-check status and similarity-report availability for the current official run
- [ ] MOSS report URL is surfaced prominently with an instructor save warning
- [ ] Clear warning that detailed official results are ephemeral and will be destroyed after download/request completion

#### Export packaging

- [ ] CSV export for Canvas-compatible grades
- [ ] HTML feedback renderer for individual student files
- [ ] Master ZIP builder bundles all student HTML files into one archive
- [ ] Download response includes CSV plus feedback ZIP in one instructor workflow
- [ ] Optional MOSS result link or summary is attached to the official-run workflow when plagiarism detection is run
- [ ] Export naming convention uses assignment identifier + run timestamp
- [ ] Export fails safely with actionable errors if packaging is incomplete
- [ ] Export flow fails fast with actionable errors for malformed or unrecognized ZIP submissions
- [ ] Docs state that grade import back into Canvas is assumed, while bulk feedback upload remains future research

### Exit Criteria

A student signs in, selects an assignment, uploads code, sees a projected score and feedback on screen, and then loses access to those artifacts after session exit. An instructor runs an official batch, watches progress in the UI, previews at least one student result, downloads the grade CSV and master HTML feedback ZIP, and sees the run complete without leaving retained student files on the server.

---

## Sprint 4 - Integration Testing + FERPA/Compliance Hardening

### Goal

Validate the full M1 workflow under realistic conditions and verify the zero-retention guarantees for both official and sandbox usage.

### Activities

- [ ] End-to-end official-run test with a realistic class-size dataset (30-50 submissions)
- [ ] End-to-end student sandbox test for assignment selection, upload, feedback, and cleanup
- [ ] Validate OAuth flow:
  - `@uvu.edu` login succeeds
  - non-UVU login is rejected
- [ ] Validate access control:
  - admin, instructor, and IA routes respect role checks
  - instructors can view assigned courses but edit only explicitly assigned sections
  - IAs can view only explicitly assigned sections for grading validation
  - student users can access sandbox features but not staff workflow pages
- [ ] Validate security:
  - network access from Judge0 student execution is blocked
  - Kata-backed VM isolation is active in canonical execution environments
  - malicious ZIP path traversal is rejected
  - configured hard-block findings stop execution
- [ ] Validate timeout handling with `while True: pass`
- [ ] Validate export totals against rubric config and pytest results
- [ ] Validate optional MOSS submission uses only ephemeral files and does not retain local copies after completion
- [ ] Validate returned MOSS URL is surfaced with an explicit save warning before navigation
- [ ] Validate cleanup:
  - extracted official files are deleted after request completion
  - sandbox upload artifacts are deleted after session exit/completion
  - temporary HTML feedback files are deleted after packaging
  - no student code remains in persistent storage
- [ ] Smoke test on Railway-target deployment
- [ ] Deployment configuration reviewed
- [ ] README updated with deployment and operating notes
- [ ] Demo walkthrough recorded

### Exit Criteria

A teammate unfamiliar with the codebase can complete the M1 workflow without assistance:

1. sign in with a `@uvu.edu` account
2. create or open an assignment
3. use the wizard or import a valid `config.json`
4. confirm the `Concepts Covered` selections
5. download the current `config.json`
6. upload a Canvas ZIP or use the student sandbox flow
7. monitor grading progress
8. download the staff CSV and feedback ZIP when using the official path
9. verify no student files remain on the server after completion or session exit

---

## Tech Stack Reference

### Full Stack

| Layer                | Technology                 | Version                     | Role                                               |
| -------------------- | -------------------------- | --------------------------- | -------------------------------------------------- |
| Frontend framework   | Next.js                    | 14.x (App Router)           | Staff and student UI                               |
| UI language          | TypeScript                 | 5.x                         | Type safety across frontend                        |
| Code editor          | Monaco Editor              | current                     | Locally hosted code editing, preview, and review   |
| Auth                 | NextAuth.js                | 5.x (Auth.js)               | Microsoft OAuth in M1                              |
| Backend framework    | FastAPI                    | 0.110.x                     | API, business logic, prompt engine                 |
| Backend language     | Python                     | 3.11+                       | Grading pipeline, AST checks, export packaging     |
| Task queue           | Celery                     | 5.3.x                       | Async official and sandbox grading jobs            |
| Message broker       | Redis                      | 7.x                         | Celery broker + transient job state                |
| Database             | PostgreSQL                 | 16.x                        | Non-sensitive metadata only                        |
| ORM                  | SQLAlchemy                 | 2.x                         | DB access from FastAPI                             |
| Migrations           | Alembic                    | 1.13.x                      | Schema versioning                                  |
| Containerization     | Docker + Compose           | 25.x                        | Dev environment + app/integration services         |
| AI inference         | Azure OpenAI API           | current approved deployment | Feedback generation                                |
| Plagiarism detection | mosspy                     | current                     | Optional Stanford MOSS submission for staff review |
| Grade export         | Standard CSV + ZIP tooling | current                     | CSV + HTML feedback packaging                      |
| Code highlighting    | Monaco Editor + Prism.js   | current / 1.29.x            | Interactive editor/review plus lightweight preview |

### Grading Pipeline

| Component                 | Technology             | Role                                                             |
| ------------------------- | ---------------------- | ---------------------------------------------------------------- |
| Static analysis           | Python `ast`           | Enforce `Concepts Covered` before execution                      |
| VM isolation              | Kata Containers        | Canonical VM-based isolation layer for Judge0 execution          |
| Execution engine          | Judge0 CE              | Sandboxed student code execution with structured status metadata |
| HTTP client               | httpx                  | FastAPI -> Judge0 async REST calls                               |
| Test framework            | pytest                 | Official and sandbox test execution                              |
| Output normalization      | python_submitty_utils  | Whitespace/encoding normalization                                |
| HTML output               | Server-side templating | Official student feedback file generation                        |
| Config authoring          | Wizard + JSON editor   | Round-trip assignment config setup                               |
| PDF/text rubric ingestion | Deferred               | M2, not M1                                                       |

### Infrastructure Notes

| Component        | Location                          | Note                                                                     |
| ---------------- | --------------------------------- | ------------------------------------------------------------------------ |
| PostgreSQL       | Railway PostgreSQL                | Metadata only, no student submissions                                    |
| Redis            | Railway Redis                     | Celery broker + transient status                                         |
| Judge0 + Kata    | Separate execution infrastructure | Judge0 execution service with canonical Kata VM isolation and explicit post-result deletion |
| Azure OpenAI     | University-approved Azure tenant  | LLM inference path for M1                                                |
| Next.js          | Railway service                   | Production frontend host                                                 |
| FastAPI + Celery | Railway services                  | Production API and workers                                               |

Optional dev/staging hardware may be used for local and integration-style validation, but this does not change Railway as the canonical M1 production target.

---

## Functional Requirements

### FR-01 - Admin / Identity

| ID      | Requirement                                                                                                              | Sprint |
| ------- | ------------------------------------------------------------------------------------------------------------------------ | ------ |
| FR-01.1 | Admin can create, edit, and deactivate staff accounts                                                                    | S1     |
| FR-01.2 | Admin can assign roles: admin, instructor, ia                                                                            | S1     |
| FR-01.3 | Admin can maintain staff access by course or section                                                                     | S1     |
| FR-01.4 | Student can authenticate through Microsoft OAuth with a `@uvu.edu` account without creating a persistent student profile | S1     |

### FR-02 - Instructor / IA

| ID       | Requirement                                                                                                                         | Sprint |
| -------- | ----------------------------------------------------------------------------------------------------------------------------------- | ------ |
| FR-02.1  | Instructor or IA can create assignments with name, course linkage, due date, and Canvas reference metadata                          | S1     |
| FR-02.2  | Instructor or IA can use a basic wizard to generate valid `config.json`                                                             | S1     |
| FR-02.3  | Instructor or IA can paste or import a validated raw `config.json`                                                                  | S1     |
| FR-02.4  | Instructor or IA can edit stored config through a rendered form and download the current `config.json`                              | S1     |
| FR-02.5  | Instructor or IA can set or override a `Concepts Covered` checklist per assignment                                                  | S1     |
| FR-02.6  | Instructor or IA can upload a bulk Canvas ZIP for official grading                                                                  | S1     |
| FR-02.7  | Instructor or IA can manage `TestCase` grading records, storage-backed pytest artifacts, and run a model solution through Judge0    | S2     |
| FR-02.8  | Instructor or IA can monitor official-run status and inspect in-session results                                                     | S3     |
| FR-02.9  | Instructor or IA can optionally run plagiarism detection for an authorized official run and review the returned MOSS URL and output | S3     |
| FR-02.10 | Instructor or IA can download a CSV and a master ZIP of per-student HTML feedback                                                   | S3     |

### FR-03 - Student Sandbox

| ID      | Requirement                                                                                 | Sprint |
| ------- | ------------------------------------------------------------------------------------------- | ------ |
| FR-03.1 | Student can sign in through Microsoft OAuth using a `@uvu.edu` account                      | S1     |
| FR-03.2 | Student can select a course and assignment for sandbox use                                  | S3     |
| FR-03.3 | Student can upload code for projected grading                                               | S3     |
| FR-03.4 | Student can view projected score, warnings, and feedback on screen                          | S3     |
| FR-03.5 | Student projected results are destroyed when processing completes or the session exits      | S3     |
| FR-03.6 | Student cannot access staff workflow pages or official export artifacts                     | S3     |
| FR-03.7 | Student sandbox uploads are rate-limited to `5 uploads per hour` per authenticated identity | S3     |

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
| FR-04.8  | System generates HTML feedback files per student using Canvas identifiers                                                                        | S2     |
| FR-04.9  | System can submit the current ephemeral official run to Stanford MOSS via `mosspy` for staff review                                              | S3     |
| FR-04.10 | System destroys student files and detailed official-run artifacts after the request concludes                                                    | S2     |
| FR-04.11 | Official grading jobs run asynchronously via Celery                                                                                              | S2     |
| FR-04.12 | System rejects malformed or non-Canvas ZIPs before queueing official grading work                                                                | S1     |
| FR-04.13 | System logs Azure token usage and optional safe MOSS URL metadata for official runs                                                              | S2     |
| FR-04.14 | System deletes or invalidates Judge0 submission/result artifacts after result retrieval so student code is not retained in the execution service | S2     |

### FR-05 - Ephemeral Student Sandbox Processing

| ID      | Requirement                                                                                                               | Sprint |
| ------- | ------------------------------------------------------------------------------------------------------------------------- | ------ |
| FR-05.1 | System accepts student sandbox uploads without creating persistent student records or submission history                  | S3     |
| FR-05.2 | System runs the same AST, execution, and feedback pipeline for sandbox grading with sandbox-appropriate output formatting | S3     |
| FR-05.3 | System presents sandbox feedback on screen only and does not produce downloadable artifacts                               | S3     |
| FR-05.4 | System destroys student sandbox files and detailed feedback artifacts after completion or session exit                    | S3     |
| FR-05.5 | System logs Azure token usage as non-sensitive metadata for sandbox runs                                                  | S2     |

---

## Non-Functional Requirements

### Performance

| ID     | Requirement                                            | Target                                                      |
| ------ | ------------------------------------------------------ | ----------------------------------------------------------- |
| NFR-P1 | ZIP upload acceptance time                             | < 2s for files up to 50MB                                   |
| NFR-P2 | Concurrent grading throughput                          | 8 submissions simultaneously                                |
| NFR-P3 | 200-submission official batch completion               | < 40 min on target hosting                                  |
| NFR-P4 | Status polling response time                           | < 200ms                                                     |
| NFR-P5 | Export packaging overhead after grading                | < 2 min for 200 submissions                                 |
| NFR-P6 | Student sandbox projected result latency               | fast enough to feel interactive for normal assignment files |
| NFR-P7 | Azure token usage is measurable per run and assignment | available in non-sensitive run metadata                     |

### Security

| ID     | Requirement                                                                                                           |
| ------ | --------------------------------------------------------------------------------------------------------------------- |
| NFR-S1 | Judge0 executes student code with network access disabled                                                             |
| NFR-S2 | Judge0 memory and timeout limits are enforced                                                                         |
| NFR-S3 | Kata Containers is the canonical VM-based isolation layer for Judge0 execution                                        |
| NFR-S4 | ZIP extraction validates all paths before any file is written                                                         |
| NFR-S5 | All app endpoints require a valid session token except auth entrypoints and health checks                             |
| NFR-S6 | OAuth callback rejects non-`@uvu.edu` accounts                                                                        |
| NFR-S7 | Detailed student artifacts are stored only in ephemeral working space during official and sandbox runs                |
| NFR-S8 | Cleanup routines remove extracted student files, Judge0 artifacts, and generated feedback artifacts immediately after completion |
| NFR-S9 | MOSS integration uses only ephemeral official-run files and does not create additional persistent student code copies |
| NFR-S10 | Sandbox rate limiting is enforced by authenticated Shadow SSO identity rather than IP-only heuristics                |

### Reliability

| ID     | Requirement                                                                                  |
| ------ | -------------------------------------------------------------------------------------------- |
| NFR-R1 | Grading job failure does not affect other queued jobs                                        |
| NFR-R2 | Failed jobs retry up to 3 times before permanent failure                                     |
| NFR-R3 | Timeout or packaging failure returns actionable errors to users                              |
| NFR-R4 | Persistent metadata remains recoverable without retaining student submissions                |
| NFR-R5 | Celery concurrency does not exceed documented Judge0 + Kata execution-capacity limits in production |

### Compliance

| ID     | Requirement                                                                                                                  |
| ------ | ---------------------------------------------------------------------------------------------------------------------------- |
| NFR-C1 | No student submission content is retained in persistent storage                                                              |
| NFR-C2 | Student code and detailed feedback artifacts are destroyed after the official request completes or the sandbox session exits |
| NFR-C3 | Only non-sensitive metadata is stored in the database                                                                        |
| NFR-C4 | Azure OpenAI usage must follow the university-approved zero-retention/privacy posture                                        |
| NFR-C5 | Plagiarism detection results are staff-facing review artifacts and must not require persistent storage of student code       |
| NFR-C6 | MOSS report handling must not imply local persistence of the external report contents                                        |

---

## Product Backlog

1 story point ~= 2-4 hours focused work.  
Priority: **Must** = M1 required · **Should** = M1 if capacity · **Won't** = post-M1

### Epic 1 - Environment and Infrastructure (Sprint 0)

| ID    | Story                                                                                                                                                  | Pts | Priority |
| ----- | ------------------------------------------------------------------------------------------------------------------------------------------------------ | --- | -------- |
| E0-01 | ER and class diagrams reviewed as canonical architecture references | 2   | Must     |
| E0-02 | FastAPI router skeleton and prompt-boundary plan reviewed | 2   | Must     |
| E0-03 | Staff and sandbox wireframes reviewed with shared interface contracts | 3   | Must     |
| E0-04 | Route structure and component hierarchy reviewed before Sprint 1 | 2   | Must     |
| E0-05 | Implementation action items captured for Sprint 0 signoff | 1   | Must     |

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
| E1-07 | Railway deployment topology documented for production services                                                                                         | 1   | Must     |
| E1-08 | Monaco locally hosted in the frontend scaffold for canonical M1 editor and review workflows                                                           | 2   | Must     |
| E1-09 | `.env.example`, README, CI checks                                                                                                                      | 2   | Must     |

**Epic 1 total: 17 points**

---

### Epic 2 - Auth and Identity (Sprint 1)

| ID    | Story                                                                     | Pts | Priority |
| ----- | ------------------------------------------------------------------------- | --- | -------- |
| E2-01 | NextAuth Microsoft OAuth provider                                         | 2   | Must     |
| E2-02 | Callback rejects non-`@uvu.edu` logins                                    | 1   | Must     |
| E2-03 | Role-based route protection for admin, instructor, IA, and student access | 3   | Must     |
| E2-04 | Role-based API protection                                                 | 2   | Must     |
| E2-05 | Admin manages staff roles and course access                               | 2   | Must     |
| E2-06 | Student sandbox sign-in path without persistent student profile storage   | 2   | Must     |

**Epic 2 total: 12 points**

---

### Epic 3 - Assignment and Config Setup (Sprint 1)

| ID    | Story                                                            | Pts | Priority |
| ----- | ---------------------------------------------------------------- | --- | -------- |
| E3-01 | Assignment creation form with course linkage and Canvas metadata | 2   | Must     |
| E3-02 | Basic wizard for core assignment/rubric/config fields            | 3   | Must     |
| E3-03 | Wizard generates valid `config.json`                             | 2   | Must     |
| E3-04 | Validated raw `config.json` paste/import UI                      | 3   | Must     |
| E3-05 | Stored config editor/view renders editable fields from JSON      | 3   | Must     |
| E3-06 | Current `config.json` is downloadable                            | 1   | Must     |
| E3-07 | `Concepts Covered` checklist seeded from course defaults         | 3   | Must     |

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

| ID    | Story                                                                                                    | Pts | Priority |
| ----- | -------------------------------------------------------------------------------------------------------- | --- | -------- |
| E5-01 | AST checker for `Concepts Covered` whitelist enforcement                                                 | 4   | Must     |
| E5-02 | Warning vs hard-block concept/security handling                                                          | 2   | Must     |
| E5-03 | Judge0 integration with Kata-backed isolation, resource limits, language mapping, structured statuses, and post-result deletion | 5   | Must     |
| E5-04 | pytest execution + output parsing + normalization                                                        | 4   | Must     |
| E5-05 | Minimal pytest artifact management per assignment                                                        | 3   | Must     |
| E5-06 | Link tests to rubric criteria and student-visible descriptions                                           | 2   | Must     |
| E5-07 | Run model solution against assignment tests through Judge0                                               | 1   | Must     |
| E5-08 | Azure OpenAI integration with concept-context prompting and hallucination guard                          | 4   | Must     |
| E5-09 | Celery grading chain for official and sandbox runs                                                       | 3   | Must     |
| E5-10 | Timeout, retry, and cleanup guarantees                                                                   | 2   | Must     |
| E5-11 | Azure token usage logging in `run_summaries` or equivalent metadata storage                              | 2   | Must     |
| E5-12 | Celery worker concurrency aligned to Judge0 + Kata execution-capacity limits                             | 1   | Must     |
| E5-13 | Optional Stanford MOSS integration via `mosspy` using ephemeral official-run files only                  | 3   | Should   |

**Epic 5 total: 36 points**

---

### Epic 6 - Student Sandbox (Sprint 3)

| ID    | Story                                                                         | Pts | Priority |
| ----- | ----------------------------------------------------------------------------- | --- | -------- |
| E6-01 | Student course and assignment selection UI                                    | 2   | Must     |
| E6-02 | Student upload flow for projected grading                                     | 3   | Must     |
| E6-03 | Sandbox rate limiter enforcing `5 uploads per hour` per authenticated student | 2   | Must     |
| E6-04 | On-screen projected score and feedback view                                   | 3   | Must     |
| E6-05 | Student-facing warnings and zero-retention messaging                          | 2   | Must     |
| E6-06 | Session-exit and completion cleanup for sandbox results                       | 2   | Must     |
| E6-07 | Student route isolation from staff pages and export flows                     | 2   | Must     |

**Epic 6 total: 16 points**

---

### Epic 7 - Instructor Batch Run UX (Sprint 3)

| ID    | Story                                                                                     | Pts | Priority |
| ----- | ----------------------------------------------------------------------------------------- | --- | -------- |
| E7-01 | Official run list with aggregate status and timestamps                                    | 2   | Must     |
| E7-02 | In-session official-run detail view with counts, warnings, and failures                   | 2   | Must     |
| E7-03 | `GET /runs/{id}/status` live polling at `2s` cadence for per-run status                   | 1   | Must     |
| E7-04 | Per-student HTML preview before export                                                    | 2   | Must     |
| E7-05 | Filtering for success, warning, hard-block, timeout, parse failure, and plagiarism status | 1   | Should   |
| E7-06 | Surface MOSS report URL prominently with instructor save warning                          | 1   | Must     |

**Epic 7 total: 9 points**

---

### Epic 8 - Export Packaging (Sprint 3)

| ID    | Story                                                                                         | Pts | Priority |
| ----- | --------------------------------------------------------------------------------------------- | --- | -------- |
| E8-01 | CSV export for Canvas-compatible grades                                                       | 2   | Must     |
| E8-02 | Individual student HTML feedback renderer                                                     | 2   | Must     |
| E8-03 | Master ZIP builder for HTML feedback package                                                  | 2   | Must     |
| E8-04 | Instructor download workflow with stable naming and actionable errors                         | 1   | Must     |
| E8-05 | Graceful failure for malformed or unrecognized ZIP submissions                                | 2   | Must     |
| E8-06 | Documentation note: Canvas bulk grade import assumed, feedback upload remains future research | 1   | Must     |

**Epic 8 total: 10 points**

---

## Action Items

- [ ] Confirm canonical Judge0 runtime assumptions and Kata execution-host requirements before Sprint 2 implementation begins.
- [ ] Validate that `docker-compose.testing.yml` remains documented as an integration harness even where local machines cannot fully reproduce canonical Kata isolation.
- [ ] Keep `implementation_folder/ClassFlow_diagram.md` out of the canonical source-of-truth set; use `implementation_folder/jaxon_implementation/diagrams/` for implementation references.

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

- official university SSO integration beyond Microsoft OAuth + `@uvu.edu` domain restriction
- Canvas LTI or grade passback API integration
- automated bulk feedback upload/distribution into Canvas
- persistent submission history or resubmission timelines
- downloadable student sandbox artifacts
- LLM-assisted PDF/text rubric conversion
- AI-assisted test generation
- PDF feedback generation
- multi-language support beyond Python
- analytics or class-wide reporting
