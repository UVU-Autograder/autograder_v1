# UVU Autograder v1 - Canonical Backlog and Sprint Plan

> Target: Testable M1 for zero-retention grading and sandbox workflows for `@uvu.edu` users
> Team: 5 developers, half time (~35-65 hrs/week total)
> Window: 8-9 weeks
> Backlog tracked in: GitHub Projects (Issues + Milestones)
> Last updated: May 4, 2026

---

## Decision Log

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Backlog tool | GitHub Projects (Issues + Milestones) | Lives in the repo, free, no external dependency |
| Data retention | Zero-retention for student submissions and grading artifacts | Minimizes FERPA risk and simplifies M1 operations |
| Database scope | Store staff, courses, assignments, configs, and sanitized run metadata only | Keeps the persistent footprint small and non-sensitive |
| Execution engine | Piston (Dockerized on Railway) | Clean service boundary for sandboxed code execution |
| AI inference | Azure OpenAI API | Uses university-approved cloud inference instead of local LLM operations |
| Plagiarism detection | Stanford MOSS via `mosspy` | Optional staff review aid using ephemeral batch files only |
| Auth (M1) | NextAuth + Microsoft OAuth | Fastest realistic path to trusted UVU identity |
| UVU restriction | Reject any login not ending in `@uvu.edu` in the NextAuth callback | Keeps M1 access bounded to UVU accounts |
| Student access | Students may sign in for sandbox use only; no student records are stored beyond the active session | Restores the projected-feedback workflow without persistent retention |
| Assignment content | Canvas-canonical | Assignment description, rosters, and final grade distribution remain in Canvas |
| Rubric/config setup | Basic wizard plus raw `config.json` import/export in M1 | Supports both guided setup and direct JSON editing without overbuilding |
| Concept policy | `Concepts Covered` progressive whitelist | Aligns AST checks and LLM feedback to the course timeline |
| Output format | Staff: CSV + master ZIP of per-student HTML feedback. Students: on-screen projected feedback only | Keeps official exports lightweight while preserving zero-retention for sandbox usage |
| Canvas redistribution | Bulk grade upload/import is assumed possible; bulk feedback upload remains future research | Keeps M1 wording specific without committing to unsolved Canvas feedback automation |
| Hosting target | Railway-first for M1 production hosting | Removes deployment ambiguity and keeps the environment simple |

---

## Locked M1 Assumptions

These assumptions should be treated as fixed for implementation unless the product direction changes.

- `Actors`
  - M1 actors are `admin`, `instructor`, `IA`, and `student`
  - staff accounts and role assignments are stored persistently
  - student access is session-based and zero-retention

- `Assignments`
  - store grading metadata needed to run future batches and sandbox sessions
  - Canvas remains canonical for assignment instructions, student identity, due dates, and final grade distribution
  - app-owned artifacts include rubric config, course-linked concepts defaults, pytest files, model solution, and student-visible test descriptions
  - staff may create/edit assignment config via either a basic wizard or direct `config.json`
  - the resulting `config.json` must be viewable, editable, and downloadable

- `Official batch processing`
  - instructor or IA uploads a Canvas ZIP for a single assignment run
  - malformed or non-Canvas ZIPs are rejected before queueing
  - extraction occurs only in memory or an ephemeral temp directory
  - optional plagiarism detection may submit the current ephemeral batch to Stanford MOSS via `mosspy`
  - when MOSS returns a URL, the UI must surface it prominently and warn the instructor to save it before leaving the page
  - student files, generated intermediate files, and detailed grading output are destroyed after the export package is returned
  - the system may keep sanitized run metadata such as timestamps, counts, and failure summaries, but not student code or detailed feedback files

- `Student sandbox processing`
  - student selects an assignment, uploads code, and receives projected score and feedback on screen
  - sandbox uploads are strictly limited to `5 uploads per hour` per authenticated student identity
  - sandbox uploads are processed only in ephemeral working storage
  - sandbox artifacts are destroyed when processing completes or when the session exits
  - student sandbox output is not downloadable and is not stored persistently

- `Concepts Covered`
  - M1 uses a progressive whitelist, not a blacklist
  - the allowed concepts list is enforced in AST checks before execution
  - the same allowed concepts list is injected into the LLM prompt context

- `Output`
  - official grading produces a grade CSV and a master ZIP containing per-student HTML feedback files
  - sandbox grading produces on-screen projected feedback only
  - no PDF output is generated
  - no in-app long-term student result history is retained

---

## Sprint Calendar

```text
Sprint 0  Environment + metadata foundation
Sprint 1  Shadow SSO + assignment/config setup + ephemeral ingestion
Sprint 2  Grading pipeline + Azure OpenAI + zero-retention controls
Sprint 3  Student sandbox + instructor batch UX + export packaging
Sprint 4  Integration testing + FERPA/compliance hardening
```

Sprint 4 is a hardening buffer. If Sprints 1-3 land cleanly, Sprint 4 is reserved for end-to-end validation, security checks, and documentation polish.

---

## Sprint 0 - Environment + Metadata Foundation

### Goal

Every developer can run the stack locally, and the persistent model reflects the reduced M1 footprint.

### Deliverables

- [ ] Repo structure agreed: monorepo with `/frontend` (Next.js) and `/backend` (FastAPI)
- [ ] Next.js app bootstrapped
- [ ] FastAPI app bootstrapped with routers, schemas, services, and prompt integration boundaries
- [ ] PostgreSQL initial schema and Alembic migration for non-sensitive core tables:
  - `users`, `roles`, `courses`, `sections`, `assignments`, `assignment_configs`, `concept_sets`, `assignment_artifacts`, `run_summaries`
- [ ] Redis running locally
- [ ] Celery connected to Redis
- [ ] Piston running locally
- [ ] Railway deployment shape documented for `nextjs`, `fastapi`, `postgres`, `redis`, `celery`, and `piston`
- [ ] Docker Compose covers `postgres`, `redis`, `celery`, `fastapi`, `nextjs`, `piston`
- [ ] `.env.example` documents required environment variables including Azure OpenAI settings
- [ ] README gets the full stack running locally
- [ ] Seed script creates 1 course, 1 assignment, 1 generated `config.json`, 1 concepts default set, and 1 model solution

### Exit Criteria

`docker compose up` brings the stack online. FastAPI health check returns 200. A test Celery task runs successfully. Piston executes a Hello World Python script. The seeded assignment loads with its stored config and concepts defaults.

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

An instructor signs in with a `@uvu.edu` account. A non-UVU login is rejected. The instructor creates an assignment through the wizard or by importing valid raw `config.json`, confirms the `Concepts Covered` selections, downloads the resulting `config.json`, uploads a Canvas ZIP, and the system parses the archive into a transient official run without storing student code as persistent records.

---

## Sprint 2 - Grading Pipeline + Azure OpenAI + Zero-Retention Controls

### Goal

The system grades official runs and sandbox uploads end to end using ephemeral files, Piston execution, AST concept enforcement, and Azure OpenAI feedback generation.

### Deliverables

- [ ] AST checker supports a course-aligned `Concepts Covered` whitelist
- [ ] AST checker detects future-concept usage before execution and records warnings per result
- [ ] Security-sensitive AST findings can hard-block execution when configured
- [ ] Allowed concepts context is injected into the Azure OpenAI prompt
- [ ] Piston integration via `httpx`
- [ ] Piston resource limits configured: 10s timeout, 256MB memory limit
- [ ] pytest execution via Piston
- [ ] pytest output parser returns structured test results
- [ ] `python_submitty_utils` output normalization integrated
- [ ] Minimal test artifact management for M1:
  - upload/edit pytest files
  - link each test to one primary rubric criterion
  - store a student-visible description per test
  - upload and run a model solution against the test suite
- [ ] model solution validation runs inside Piston, not on the host
- [ ] Azure OpenAI integration for rubric-context explanation and feedback generation
- [ ] Azure token usage logged to `run_summaries` or equivalent non-sensitive metadata storage
- [ ] Hallucination guard enforced: tests remain ground truth and the LLM explains rather than re-evaluates correctness
- [ ] Celery grading chain supports both official runs and sandbox runs
- [ ] Celery worker concurrency aligned to Piston container parallelism
- [ ] Run status endpoint returns queue/run/complete/failure state
- [ ] Staff and student views show live status through polling where appropriate
- [ ] Failed jobs retry up to 3 times with backoff
- [ ] Timeout handling frees the worker immediately and records `failed:timeout`
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
  - student users can access sandbox features but not staff workflow pages
- [ ] Validate security:
  - network access from Piston execution is blocked
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

| Layer | Technology | Version | Role |
|-------|------------|---------|------|
| Frontend framework | Next.js | 14.x (App Router) | Staff and student UI |
| UI language | TypeScript | 5.x | Type safety across frontend |
| Auth | NextAuth.js | 5.x (Auth.js) | Microsoft OAuth in M1 |
| Backend framework | FastAPI | 0.110.x | API, business logic, prompt engine |
| Backend language | Python | 3.11+ | Grading pipeline, AST checks, export packaging |
| Task queue | Celery | 5.3.x | Async official and sandbox grading jobs |
| Message broker | Redis | 7.x | Celery broker + transient job state |
| Database | PostgreSQL | 16.x | Non-sensitive metadata only |
| ORM | SQLAlchemy | 2.x | DB access from FastAPI |
| Migrations | Alembic | 1.13.x | Schema versioning |
| Containerization | Docker + Compose | 25.x | Dev environment + Piston service |
| AI inference | Azure OpenAI API | current approved deployment | Feedback generation |
| Plagiarism detection | mosspy | current | Optional Stanford MOSS submission for staff review |
| Grade export | Standard CSV + ZIP tooling | current | CSV + HTML feedback packaging |
| Code highlighting | Prism.js | 1.29.x | Result preview |

### Grading Pipeline

| Component | Technology | Role |
|-----------|------------|------|
| Static analysis | Python `ast` | Enforce `Concepts Covered` before execution |
| Execution engine | Piston | Sandboxed student code execution |
| HTTP client | httpx | FastAPI -> Piston async REST calls |
| Test framework | pytest | Official and sandbox test execution |
| Output normalization | python_submitty_utils | Whitespace/encoding normalization |
| HTML output | Server-side templating | Official student feedback file generation |
| Config authoring | Wizard + JSON editor | Round-trip assignment config setup |
| PDF/text rubric ingestion | Deferred | M2, not M1 |

### Infrastructure Notes

| Component | Location | Note |
|-----------|----------|------|
| PostgreSQL | Railway PostgreSQL | Metadata only, no student submissions |
| Redis | Railway Redis | Celery broker + transient status |
| Piston | Railway Docker service | Requires documented isolation settings |
| Azure OpenAI | University-approved Azure tenant | LLM inference path for M1 |
| Next.js | Railway service | Production frontend host |
| FastAPI + Celery | Railway services | Production API and workers |

---

## Functional Requirements

### FR-01 - Admin / Identity

| ID | Requirement | Sprint |
|----|-------------|--------|
| FR-01.1 | Admin can create, edit, and deactivate staff accounts | S1 |
| FR-01.2 | Admin can assign roles: admin, instructor, ia | S1 |
| FR-01.3 | Admin can maintain staff access by course or section | S1 |
| FR-01.4 | Student can authenticate through Microsoft OAuth with a `@uvu.edu` account without creating a persistent student profile | S1 |

### FR-02 - Instructor / IA

| ID | Requirement | Sprint |
|----|-------------|--------|
| FR-02.1 | Instructor or IA can create assignments with name, course linkage, due date, and Canvas reference metadata | S1 |
| FR-02.2 | Instructor or IA can use a basic wizard to generate valid `config.json` | S1 |
| FR-02.3 | Instructor or IA can paste or import a validated raw `config.json` | S1 |
| FR-02.4 | Instructor or IA can edit stored config through a rendered form and download the current `config.json` | S1 |
| FR-02.5 | Instructor or IA can set or override a `Concepts Covered` checklist per assignment | S1 |
| FR-02.6 | Instructor or IA can upload a bulk Canvas ZIP for official grading | S1 |
| FR-02.7 | Instructor or IA can manage assignment pytest artifacts and run a model solution inside Piston | S2 |
| FR-02.8 | Instructor or IA can monitor official-run status and inspect in-session results | S3 |
| FR-02.9 | Instructor or IA can optionally run plagiarism detection for an official run and review the returned MOSS output | S3 |
| FR-02.10 | Instructor or IA can download a CSV and a master ZIP of per-student HTML feedback | S3 |

### FR-03 - Student Sandbox

| ID | Requirement | Sprint |
|----|-------------|--------|
| FR-03.1 | Student can sign in through Microsoft OAuth using a `@uvu.edu` account | S1 |
| FR-03.2 | Student can select a course and assignment for sandbox use | S3 |
| FR-03.3 | Student can upload code for projected grading | S3 |
| FR-03.4 | Student can view projected score, warnings, and feedback on screen | S3 |
| FR-03.5 | Student projected results are destroyed when processing completes or the session exits | S3 |
| FR-03.6 | Student cannot access staff workflow pages or official export artifacts | S3 |
| FR-03.7 | Student sandbox uploads are rate-limited to `5 uploads per hour` per authenticated identity | S3 |

### FR-04 - Ephemeral Official Processing

| ID | Requirement | Sprint |
|----|-------------|--------|
| FR-04.1 | System parses Canvas uploads into a transient official run | S1 |
| FR-04.2 | System extracts ZIP contents only into RAM or an ephemeral temp directory | S1 |
| FR-04.3 | System rejects ZIP path traversal attempts before extraction | S1 |
| FR-04.4 | System does not create persistent student submission records for official runs | S1 |
| FR-04.5 | System runs AST concept checks before execution | S2 |
| FR-04.6 | System executes pytest via Piston with resource limits | S2 |
| FR-04.7 | System sends code, test results, and allowed-concepts context to Azure OpenAI | S2 |
| FR-04.8 | System generates HTML feedback files per student using Canvas identifiers | S2 |
| FR-04.9 | System can submit the current ephemeral official run to Stanford MOSS via `mosspy` for staff review | S3 |
| FR-04.10 | System destroys student files and detailed official-run artifacts after the request concludes | S2 |
| FR-04.11 | Official grading jobs run asynchronously via Celery | S2 |
| FR-04.12 | System rejects malformed or non-Canvas ZIPs before queueing official grading work | S1 |
| FR-04.13 | System logs Azure token usage as non-sensitive metadata for official runs | S2 |

### FR-05 - Ephemeral Student Sandbox Processing

| ID | Requirement | Sprint |
|----|-------------|--------|
| FR-05.1 | System accepts student sandbox uploads without creating persistent student records or submission history | S3 |
| FR-05.2 | System runs the same AST, execution, and feedback pipeline for sandbox grading with sandbox-appropriate output formatting | S3 |
| FR-05.3 | System presents sandbox feedback on screen only and does not produce downloadable artifacts | S3 |
| FR-05.4 | System destroys student sandbox files and detailed feedback artifacts after completion or session exit | S3 |
| FR-05.5 | System logs Azure token usage as non-sensitive metadata for sandbox runs | S2 |

---

## Non-Functional Requirements

### Performance

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-P1 | ZIP upload acceptance time | < 2s for files up to 50MB |
| NFR-P2 | Concurrent grading throughput | 8 submissions simultaneously |
| NFR-P3 | 200-submission official batch completion | < 40 min on target hosting |
| NFR-P4 | Status polling response time | < 200ms |
| NFR-P5 | Export packaging overhead after grading | < 2 min for 200 submissions |
| NFR-P6 | Student sandbox projected result latency | fast enough to feel interactive for normal assignment files |
| NFR-P7 | Azure token usage is measurable per run and assignment | available in non-sensitive run metadata |

### Security

| ID | Requirement |
|----|-------------|
| NFR-S1 | Piston executes student code with network access disabled |
| NFR-S2 | Piston memory and timeout limits are enforced |
| NFR-S3 | ZIP extraction validates all paths before any file is written |
| NFR-S4 | All app endpoints require a valid session token except auth entrypoints and health checks |
| NFR-S5 | OAuth callback rejects non-`@uvu.edu` accounts |
| NFR-S6 | Detailed student artifacts are stored only in ephemeral working space during official and sandbox runs |
| NFR-S7 | Cleanup routines remove extracted student files and generated feedback artifacts immediately after completion |
| NFR-S8 | MOSS integration uses only ephemeral official-run files and does not create additional persistent student code copies |
| NFR-S9 | Sandbox rate limiting is enforced by authenticated Shadow SSO identity rather than IP-only heuristics |

### Reliability

| ID | Requirement |
|----|-------------|
| NFR-R1 | Grading job failure does not affect other queued jobs |
| NFR-R2 | Failed jobs retry up to 3 times before permanent failure |
| NFR-R3 | Timeout or packaging failure returns actionable errors to users |
| NFR-R4 | Persistent metadata remains recoverable without retaining student submissions |
| NFR-R5 | Celery concurrency does not exceed documented Piston parallelism limits in production |

### Compliance

| ID | Requirement |
|----|-------------|
| NFR-C1 | No student submission content is retained in persistent storage |
| NFR-C2 | Student code and detailed feedback artifacts are destroyed after the official request completes or the sandbox session exits |
| NFR-C3 | Only non-sensitive metadata is stored in the database |
| NFR-C4 | Azure OpenAI usage must follow the university-approved zero-retention/privacy posture |
| NFR-C5 | Plagiarism detection results are staff-facing review artifacts and must not require persistent storage of student code |
| NFR-C6 | MOSS report handling must not imply local persistence of the external report contents |

---

## Product Backlog

1 story point ~= 2-4 hours focused work.  
Priority: **Must** = M1 required · **Should** = M1 if capacity · **Won't** = post-M1

### Epic 1 - Environment and Infrastructure (Sprint 0)

| ID | Story | Pts | Priority |
|----|-------|-----|----------|
| E1-01 | Docker Compose: postgres, redis, celery, fastapi, nextjs, piston | 2 | Must |
| E1-02 | FastAPI project structure with routers, schemas, services, and prompt boundaries | 2 | Must |
| E1-03 | Next.js project structure with App Router | 2 | Must |
| E1-04 | PostgreSQL schema + Alembic initial migration for metadata-only tables | 2 | Must |
| E1-05 | Celery + Redis wiring | 1 | Must |
| E1-06 | Piston service running with documented isolation settings | 2 | Must |
| E1-07 | Railway deployment topology documented for production services | 1 | Must |
| E1-08 | `.env.example`, README, CI checks | 2 | Must |

**Epic 1 total: 14 points**

---

### Epic 2 - Auth and Identity (Sprint 1)

| ID | Story | Pts | Priority |
|----|-------|-----|----------|
| E2-01 | NextAuth Microsoft OAuth provider | 2 | Must |
| E2-02 | Callback rejects non-`@uvu.edu` logins | 1 | Must |
| E2-03 | Role-based route protection for admin, instructor, IA, and student access | 3 | Must |
| E2-04 | Role-based API protection | 2 | Must |
| E2-05 | Admin manages staff roles and course access | 2 | Must |
| E2-06 | Student sandbox sign-in path without persistent student profile storage | 2 | Must |

**Epic 2 total: 12 points**

---

### Epic 3 - Assignment and Config Setup (Sprint 1)

| ID | Story | Pts | Priority |
|----|-------|-----|----------|
| E3-01 | Assignment creation form with course linkage and Canvas metadata | 2 | Must |
| E3-02 | Basic wizard for core assignment/rubric/config fields | 3 | Must |
| E3-03 | Wizard generates valid `config.json` | 2 | Must |
| E3-04 | Validated raw `config.json` paste/import UI | 3 | Must |
| E3-05 | Stored config editor/view renders editable fields from JSON | 3 | Must |
| E3-06 | Current `config.json` is downloadable | 1 | Must |
| E3-07 | `Concepts Covered` checklist seeded from course defaults | 3 | Must |

**Epic 3 total: 17 points**

---

### Epic 4 - Ephemeral Submission Ingestion (Sprint 1)

| ID | Story | Pts | Priority |
|----|-------|-----|----------|
| E4-01 | Canvas ZIP upload endpoint with size + type validation | 2 | Must |
| E4-02 | Reject malformed or non-Canvas ZIPs before queueing | 2 | Must |
| E4-03 | ZIP path traversal protection | 2 | Must |
| E4-04 | Ephemeral extraction workflow in RAM or temp directory only | 2 | Must |
| E4-05 | Filename parser for Canvas uploads using Canvas identifiers | 2 | Must |
| E4-06 | Unmatched filename/malformed archive reporting | 2 | Must |
| E4-07 | Transient official-run metadata record without persistent student submissions | 1 | Must |

**Epic 4 total: 13 points**

---

### Epic 5 - Grading Pipeline and AI Enrichment (Sprint 2)

| ID | Story | Pts | Priority |
|----|-------|-----|----------|
| E5-01 | AST checker for `Concepts Covered` whitelist enforcement | 4 | Must |
| E5-02 | Warning vs hard-block concept/security handling | 2 | Must |
| E5-03 | Piston integration with resource limits | 4 | Must |
| E5-04 | pytest execution + output parsing + normalization | 4 | Must |
| E5-05 | Minimal pytest artifact management per assignment | 3 | Must |
| E5-06 | Link tests to rubric criteria and student-visible descriptions | 2 | Must |
| E5-07 | Run model solution against assignment tests inside Piston | 1 | Must |
| E5-08 | Azure OpenAI integration with concept-context prompting and hallucination guard | 4 | Must |
| E5-09 | Celery grading chain for official and sandbox runs | 3 | Must |
| E5-10 | Timeout, retry, and cleanup guarantees | 2 | Must |
| E5-11 | Azure token usage logging in `run_summaries` or equivalent metadata storage | 2 | Must |
| E5-12 | Celery worker concurrency aligned to Piston container limits | 1 | Must |
| E5-13 | Optional Stanford MOSS integration via `mosspy` using ephemeral official-run files only | 3 | Should |

**Epic 5 total: 35 points**

---

### Epic 6 - Student Sandbox (Sprint 3)

| ID | Story | Pts | Priority |
|----|-------|-----|----------|
| E6-01 | Student course and assignment selection UI | 2 | Must |
| E6-02 | Student upload flow for projected grading | 3 | Must |
| E6-03 | Sandbox rate limiter enforcing `5 uploads per hour` per authenticated student | 2 | Must |
| E6-04 | On-screen projected score and feedback view | 3 | Must |
| E6-05 | Student-facing warnings and zero-retention messaging | 2 | Must |
| E6-06 | Session-exit and completion cleanup for sandbox results | 2 | Must |
| E6-07 | Student route isolation from staff pages and export flows | 2 | Must |

**Epic 6 total: 16 points**

---

### Epic 7 - Instructor Batch Run UX (Sprint 3)

| ID | Story | Pts | Priority |
|----|-------|-----|----------|
| E7-01 | Official run list with aggregate status and timestamps | 2 | Must |
| E7-02 | In-session official-run detail view with counts, warnings, and failures | 2 | Must |
| E7-03 | Live polling for per-run status | 1 | Must |
| E7-04 | Per-student HTML preview before export | 2 | Must |
| E7-05 | Filtering for success, warning, hard-block, timeout, parse failure, and plagiarism status | 1 | Should |
| E7-06 | Surface MOSS report URL prominently with instructor save warning | 1 | Must |

**Epic 7 total: 9 points**

---

### Epic 8 - Export Packaging (Sprint 3)

| ID | Story | Pts | Priority |
|----|-------|-----|----------|
| E8-01 | CSV export for Canvas-compatible grades | 2 | Must |
| E8-02 | Individual student HTML feedback renderer | 2 | Must |
| E8-03 | Master ZIP builder for HTML feedback package | 2 | Must |
| E8-04 | Instructor download workflow with stable naming and actionable errors | 1 | Must |
| E8-05 | Graceful failure for malformed or unrecognized ZIP submissions | 2 | Must |
| E8-06 | Documentation note: Canvas bulk grade import assumed, feedback upload remains future research | 1 | Must |

**Epic 8 total: 10 points**

---

### Backlog Summary

| Epic | Name | M1 Points | Sprint |
|------|------|-----------|--------|
| E1 | Environment and Infrastructure | 14 | S0 |
| E2 | Auth and Identity | 12 | S1 |
| E3 | Assignment and Config Setup | 17 | S1 |
| E4 | Ephemeral Submission Ingestion | 13 | S1 |
| E5 | Grading Pipeline and AI Enrichment | 35 | S2 |
| E6 | Student Sandbox | 16 | S3 |
| E7 | Instructor Batch Run UX | 9 | S3 |
| E8 | Export Packaging | 10 | S3 |
| **Total** | | **126 points** | |

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
- [ ] reviewed by at least one teammate
- [ ] no TypeScript or Python type errors on CI
- [ ] Ruff and ESLint pass
- [ ] at least one unit or integration test covers the happy path
- [ ] edge cases handled: bad input, malformed ZIP, unmatched filename, non-UVU login, timeout, cleanup failure, sandbox exit cleanup
- [ ] no hardcoded secrets or environment-specific values
- [ ] docs updated if setup or behavior changed

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
