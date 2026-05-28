# UVU Autograder v1 - Sprint Plan

This file tracks sprint execution for the current Jaxon implementation track. Product decisions live in [decisions.md](../backend_implementation/jaxon_implementation/decisions.md), runtime contracts live in [technical_specs.md](../backend_implementation/jaxon_implementation/technical_specs.md), frontend contracts live in [frontend_implementation.md](../frontend_implementation/frontend_implementation.md), and story tables live in [product_backlog.md](product_backlog.md).

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
- [ ] Clear warning that detailed official results are ephemeral and will be destroyed after download/request completion

#### Export packaging

- [ ] CSV export for Canvas-compatible grades
- [ ] Feedback renderer produces per-student staff-facing feedback artifacts
- [ ] Feedback packaging produces a per-run ZIP of per-student HTML feedback artifacts
- [ ] Staff can download the Canvas-grade CSV and feedback ZIP through separate actions with stable naming and actionable errors
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

## Action Items

- [ ] Benchmark safe Judge0 + Kata concurrency on the Dell workstation and document worker caps before Sprint 2 implementation begins.
- [ ] Validate that `docker-compose.testing.yml` remains documented as an integration harness even where local machines cannot fully reproduce the planned Kata isolation setup.
- [ ] Keep `docs/backend_implementation/easton_implementation/ClassFlow_diagram.md` separate from the current Jaxon working diagrams to avoid mixing older and newer planning artifacts.

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
