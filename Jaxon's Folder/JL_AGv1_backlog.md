# UVU Autograder - Canonical Backlog and Sprint Plan

> Target: Testable V1 with official grading workflow and student result visibility
> Team: 3 developers, half time (~20-40 hrs/week total)
> Window: 8-9 weeks
> Backlog tracked in: GitHub Projects (Issues + Milestones)
> Last updated: May 1, 2026

---

## Decision Log

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Backlog tool | GitHub Projects (Issues + Milestones) | Lives in the repo, free, no external dependency |
| Database hosting | Local PostgreSQL on Mac Mini | FERPA - no student data leaves on-prem infrastructure |
| Execution engine | Piston (self-hosted Docker) | Clean service boundary for code execution |
| Auth (M1) | NextAuth + Microsoft OAuth | Simple interim login path that aligns with eventual UVU identity |
| UVU restriction | Reject any login not ending in `@uvu.edu` in the NextAuth callback | Keeps M1 student/staff access bounded to UVU accounts |
| Student delivery (M1) | Student dashboard for released official results | Replaces token-link delivery and keeps result access tied to user identity |
| Student practice uploads | Deferred to M2 | M1 focuses on official Canvas grading flow only |
| Assignment content | Canvas-canonical | Assignment description lives in Canvas; the app stores grading artifacts and metadata |
| Rubric ingestion | Raw JSON input in M1; LLM-assisted PDF/text conversion in M2 | Keeps M1 deterministic and reduces extraction ambiguity |
| Constraint behavior | `review_flag` or `hard_block` | Normal constraints warn and flag for review; security-sensitive constraints block execution |
| Artifact storage | DB-backed storage behind a storage abstraction | Simplest M1 implementation without locking the system into one storage strategy forever |

---

## Locked M1 Data Model Assumptions

These are the planning assumptions the implementation should treat as fixed for M1.

- `Assignment`
  - stores grading metadata only
  - Canvas remains canonical for the assignment description/instructions
  - app-owned artifacts include rubric config, constraints, pytest files, model solution, student template, and student-visible test descriptions

- `Submission`
  - every submission is a version
  - one timeline per student per assignment
  - `source` enum is `official | practice`
  - M1 only creates `official` submissions through instructor uploads
  - M2 adds `practice` submissions from student self-uploads

- `Constraint`
  - M1 severity modes are `review_flag | hard_block`
  - `review_flag` does not stop execution
  - `hard_block` stops execution and surfaces a warning

- `Test`
  - stores pytest content or file handle
  - may link to one primary rubric criterion
  - stores a student-visible description
  - rubric criteria may have many tests
  - criteria without mapped tests must be explicitly treated as manual/LLM-reviewed

- `Release state`
  - M1 state machine is `pending -> ai_complete -> ta_reviewed -> approved -> released`
  - `released` means visible to the student

---

## Sprint Calendar

```text
Sprint 0  Environment + schema foundation
Sprint 1  Auth + assignment setup + official submission ingestion
Sprint 2  Grading pipeline + core test artifact management
Sprint 3  TA review + release + student dashboard + export
Sprint 4  Integration testing + hardening
```

Sprint 4 is a named buffer, not a feature sprint. If Sprints 1-3 land cleanly, Sprint 4 is for hardening and end-to-end validation.

---

## Sprint 0 - Environment + Schema Foundation

### Goal

Every developer can run the stack locally, and the schema reflects the M1 official-grading model.

### Deliverables

- [ ] Repo structure agreed - monorepo with `/frontend` (Next.js) and `/backend` (FastAPI)
- [ ] Next.js app bootstrapped
- [ ] FastAPI app bootstrapped with routers, models, schemas, and services
- [ ] PostgreSQL initial schema and Alembic migration for core tables:
  - `users`, `roles`, `students`, `assignments`, `constraints`, `rubric_criteria`,
    `assignment_artifacts`, `submissions`, `grading_jobs`, `grading_results`, `audit_log`
- [ ] Submission schema includes version number, `source`, release state, and review state
- [ ] Redis running locally
- [ ] Celery connected to Redis
- [ ] Piston running locally
- [ ] llama-server running locally
- [ ] Docker Compose covers `postgres`, `redis`, `celery`, `fastapi`, `nextjs`, `piston`
- [ ] `.env.example` documents required environment variables
- [ ] README gets the full stack running locally
- [ ] Seed script creates 1 assignment, 1 rubric config, 1 model solution, and 5 official sample submissions

### Exit criteria

`docker compose up` brings the stack online. FastAPI health check returns 200. A test Celery task runs successfully. Piston executes a Hello World Python script. The seeded assignment can be loaded from the database with rubric config and sample official submissions.

---

## Sprint 1 - Auth + Assignment Setup + Official Submission Ingestion

### Goal

Staff can sign in, define grading artifacts for an assignment, upload official Canvas submissions, and create versioned submission records.

### Deliverables

- [ ] NextAuth Microsoft OAuth provider configured
- [ ] NextAuth callback rejects any login not ending in `@uvu.edu`
- [ ] Role-based route protection in Next.js
- [ ] Role-based API protection in FastAPI
- [ ] Minimal user/role management for admin, instructor, TA, and student records
- [ ] Student identity mapping for official results:
  - staff can import or maintain a roster mapping `student_id -> uvu_email`
- [ ] Assignment creation form stores name, due date, and Canvas reference metadata
- [ ] Basic rubric builder UI for rubric criteria and point values
- [ ] Constraint builder UI for `review_flag | hard_block`
- [ ] Validated raw JSON rubric/config import (paste/upload)
- [ ] `config.json` generation and storage from UI inputs
- [ ] Canvas ZIP upload endpoint with path traversal protection
- [ ] Individual official file upload/reprocess path for regrades or corrections
- [ ] Canvas filename parser maps files to student records
- [ ] Submission record creation per parsed file with:
  - version number
  - `source = official`
  - initial state = `pending`
- [ ] Submission list view shows all official submissions for an assignment

### Exit criteria

An instructor signs in with a `@uvu.edu` account. A non-UVU login is rejected. The instructor creates an assignment, imports a complete raw JSON grading config, uploads a Canvas ZIP, and the system creates versioned official submission records tied to the correct students.

---

## Sprint 2 - Grading Pipeline + Core Test Artifact Management

### Goal

The system grades an official submission end to end and stores reviewable results using the M1 constraint policy and minimum viable assignment test management.

### Deliverables

- [ ] AST constraint checker supports:
  - `forbidden_call`
  - `forbidden_attribute`
  - `forbidden_node`
  - `forbidden_import`
  - `required_definition`
- [ ] Constraint handling policy is enforced:
  - `review_flag` constraints do not stop execution
  - `hard_block` constraints stop execution and surface a warning
- [ ] Constraint warnings are stored and shown separately from rubric scores
- [ ] Piston integration via `httpx`
- [ ] Piston resource limits configured: 10s timeout, 256MB memory limit
- [ ] pytest test suite execution via Piston
- [ ] pytest output parser returns structured test results
- [ ] `python_submitty_utils` output normalization integrated
- [ ] Minimum test artifact management for M1:
  - upload/edit pytest files
  - link each test to one primary rubric criterion
  - store a student-visible description per test
  - upload and run a model solution against the test suite
- [ ] LLM prompt set implemented:
  - rubric-context prompt
  - code annotation prompt
  - rubric scoring prompt
- [ ] Hallucination guard enforced: tests are ground truth; LLM explains rather than re-evaluates correctness
- [ ] Celery grading chain: AST -> Piston -> LLM annotator -> LLM scorer
- [ ] Grading results stored immutably in PostgreSQL
- [ ] Job status endpoint returns queue/run/complete/failure state
- [ ] Submission list shows live status through polling
- [ ] Failed jobs retry up to 3 times with backoff
- [ ] Timeout handling frees the worker immediately and records `failed:timeout`

### Explicit M2 deferrals

- [ ] LLM-assisted test generation
- [ ] PDF/text rubric ingestion
- [ ] advanced pytest editor polish
- [ ] richer test debugging preview/log UX
- [ ] student template authoring polish

### Exit criteria

An instructor uploads official submissions covering: 1 hard-block violation, 1 review-flag violation, 1 timeout, 1 correct solution, and 1 broken solution. Hard-block submissions do not execute. Review-flag submissions still execute and surface warnings. The grading pipeline stores test results, annotations, and rubric-aligned feedback without crashing.

---

## Sprint 3 - TA Review + Release + Student Dashboard + Export

### Goal

TAs and instructors can review official submissions, release final results, export grades, and students can sign in to view released official results in a dashboard.

### Deliverables

#### Review workflow

- [ ] Submission list sortable by score, status, and version
- [ ] Detail view with:
  - code and inline LLM comments
  - rubric scores and justification
  - constraint warnings / hard-block reason
- [ ] TA override with justification
- [ ] TA manual comment append
- [ ] TA approve / flag for instructor review
- [ ] Instructor approve button
- [ ] Status machine enforced:
  - `pending -> ai_complete -> ta_reviewed -> approved -> released`
- [ ] Audit log records AI output, override, approval, release, user, and timestamp
- [ ] Submission navigation within an assignment

#### Student dashboard

- [ ] Student sign-in via Microsoft OAuth
- [ ] Student account access limited to matched `@uvu.edu` identity
- [ ] Dashboard lists released official submissions only
- [ ] Student detail page shows:
  - total score
  - per-criterion feedback
  - code annotations
  - constraint warnings
  - test descriptions
- [ ] Unreleased official results are not visible to students
- [ ] Students cannot access another student's released results

#### Export

- [ ] CSV export for approved/released official grades
- [ ] XLSX export formatted for Canvas manual import
- [ ] Export blocked until submissions are approved

### Exit criteria

An instructor uploads official submissions, the pipeline grades them, a TA reviews one, the instructor approves and releases it, the grade exports successfully, and the correct student can sign in and view the released official result in the dashboard while another student cannot.

---

## Sprint 4 - Integration Testing + Hardening

### Goal

Validate the full M1 official-grading workflow under realistic conditions.

### Activities

- [ ] End-to-end test with a realistic class-size dataset (30-50 submissions)
- [ ] Validate OAuth flow:
  - `@uvu.edu` login succeeds
  - non-UVU login is rejected
- [ ] Validate access control:
  - student can view own released official results
  - student cannot view unreleased results
  - student cannot view another student's results
- [ ] Validate official submission versioning through repeat upload/reprocess
- [ ] Validate security:
  - network access from Piston execution is blocked
  - malicious ZIP path traversal is rejected
  - hard-block constraints stop execution
- [ ] Validate timeout handling with `while True: pass`
- [ ] Validate export totals against database values
- [ ] Smoke test on production-target hardware
- [ ] `launchd` service files for all processes
- [ ] Production Nginx config reviewed
- [ ] README updated with deployment steps
- [ ] Demo walkthrough recorded

### Exit criteria

A teammate unfamiliar with the codebase can complete the M1 workflow without assistance:

1. instructor signs in
2. official submissions are uploaded
3. results are graded
4. TA reviews and instructor releases
5. student signs in and views released official results
6. grades export successfully

---

## Tech Stack Reference

### Full Stack

| Layer | Technology | Version | Role |
|-------|------------|---------|------|
| Frontend framework | Next.js | 14.x (App Router) | Staff UI + student dashboard |
| UI language | TypeScript | 5.x | Type safety across frontend |
| Auth | NextAuth.js | 5.x (Auth.js) | Microsoft OAuth in M1 |
| Backend framework | FastAPI | 0.110.x | API, business logic, prompt engine |
| Backend language | Python | 3.11+ | Grading pipeline, LLM integration |
| Task queue | Celery | 5.3.x | Async grading jobs |
| Message broker | Redis | 7.x | Celery broker + result backend |
| Database | PostgreSQL | 16.x | Local on Mac Mini |
| ORM | SQLAlchemy | 2.x | DB access from FastAPI |
| Migrations | Alembic | 1.13.x | Schema versioning |
| Reverse proxy | Nginx | 1.24.x | TLS termination, rate limiting |
| Containerization | Docker + Compose | 25.x | Dev environment + Piston service |
| Inference server | llama-server (llama.cpp) | latest | Local LLM |
| LLM model | Llama 3.3 70B Q4_K_M | - | Grading feedback generation |
| Grade export | openpyxl | 3.1.x | CSV / XLSX export |
| Code highlighting | Prism.js | 1.29.x | Syntax highlighting |

### Grading Pipeline

| Component | Technology | Role |
|-----------|------------|------|
| Static analysis | Python `ast` | Constraint checking before execution |
| Execution engine | Piston | Sandboxed student code execution |
| HTTP client | httpx | FastAPI -> Piston async REST calls |
| Test framework | pytest | Official submission test execution |
| Output normalization | python_submitty_utils | Whitespace/encoding normalization |
| Plagiarism | mosspy | M2 - not M1 |
| PDF/text rubric ingestion | LLM-assisted conversion | M2 - not M1 |

### Infrastructure Notes

| Component | Location | Note |
|-----------|----------|------|
| PostgreSQL | Mac Mini local | Data stays on-prem |
| Redis | Mac Mini local | Celery broker + result backend |
| Piston | Mac Mini Docker | Requires security review and documented container settings |
| llama-server | Mac Mini local | Persistent service |
| Nginx | Mac Mini local | TLS termination |

---

## Functional Requirements

### FR-01 - Admin / Identity

| ID | Requirement | Sprint |
|----|-------------|--------|
| FR-01.1 | Admin can create, edit, deactivate user accounts | S1 |
| FR-01.2 | Admin can assign roles: admin, instructor, ta, student | S1 |
| FR-01.3 | Admin can maintain student identity mappings (`student_id -> uvu_email`) | S1 |
| FR-01.4 | Admin can view the audit log | S3 |

### FR-02 - Instructor

| ID | Requirement | Sprint |
|----|-------------|--------|
| FR-02.1 | Instructor can create assignments with name, due date, and Canvas reference metadata | S1 |
| FR-02.2 | Instructor can define rubric criteria with point values | S1 |
| FR-02.3 | Instructor can import validated raw JSON grading configs | S1 |
| FR-02.4 | Instructor can define constraints with severity `review_flag | hard_block` | S1 |
| FR-02.5 | Instructor can upload bulk Canvas ZIP submissions | S1 |
| FR-02.6 | Instructor can upload individual official files for regrade/reprocess | S1 |
| FR-02.7 | Instructor can manage assignment test artifacts and run a model solution | S2 |
| FR-02.8 | Instructor can review AI comments and scores | S3 |
| FR-02.9 | Instructor can approve and release official submissions | S3 |
| FR-02.10 | Instructor can export approved grades as CSV and XLSX | S3 |

### FR-03 - TA

| ID | Requirement | Sprint |
|----|-------------|--------|
| FR-03.1 | TA can upload bulk Canvas ZIP submissions for assigned sections | S1 |
| FR-03.2 | TA can view live grading status | S2 |
| FR-03.3 | TA can review AI inline comments and per-criterion scores | S3 |
| FR-03.4 | TA can override AI score per criterion with justification | S3 |
| FR-03.5 | TA can add manual comments | S3 |
| FR-03.6 | TA can approve submission or flag for instructor review | S3 |
| FR-03.7 | TA can view constraint warnings and hard-block reasons | S3 |

### FR-04 - Grading Pipeline

| ID | Requirement | Sprint |
|----|-------------|--------|
| FR-04.1 | System parses Canvas uploads into official submission versions | S1 |
| FR-04.2 | Every official upload creates a versioned submission record | S1 |
| FR-04.3 | System runs AST constraint checks before execution | S2 |
| FR-04.4 | `review_flag` constraints warn and allow execution | S2 |
| FR-04.5 | `hard_block` constraints stop execution and surface a warning | S2 |
| FR-04.6 | System executes pytest via Piston with resource limits | S2 |
| FR-04.7 | System sends code and test results to the LLM feedback agent | S2 |
| FR-04.8 | LLM feedback remains consistent with test outcomes | S2 |
| FR-04.9 | System stores test results, AI output, warnings, and review actions immutably | S2 |
| FR-04.10 | Grading jobs run asynchronously via Celery | S2 |

### FR-05 - Student Dashboard

| ID | Requirement | Sprint |
|----|-------------|--------|
| FR-05.1 | Student can sign in through Microsoft OAuth using a `@uvu.edu` account | S3 |
| FR-05.2 | Student can view a dashboard of released official submissions | S3 |
| FR-05.3 | Student can open a released official result detail page | S3 |
| FR-05.4 | Student sees score, feedback, annotations, constraint warnings, and test descriptions | S3 |
| FR-05.5 | Student cannot access unreleased results or another student's results | S3 |
| FR-05.6 | Student self-uploaded practice submissions are deferred to M2 | M2 |

---

## Non-Functional Requirements

### Performance

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-P1 | ZIP upload response time | < 2s for files up to 50MB |
| NFR-P2 | Concurrent grading throughput | 8 submissions simultaneously |
| NFR-P3 | 200-submission batch completion | < 40 min on 256GB hardware |
| NFR-P4 | Status polling response time | < 200ms |
| NFR-P5 | Released results dashboard page load | < 2s |

### Security

| ID | Requirement |
|----|-------------|
| NFR-S1 | Piston executes student code with network access disabled |
| NFR-S2 | Piston memory and timeout limits are enforced |
| NFR-S3 | ZIP extraction validates all paths before any file is written |
| NFR-S4 | All app endpoints require a valid session token except the auth entrypoints and health checks |
| NFR-S5 | OAuth callback rejects non-`@uvu.edu` accounts |
| NFR-S6 | Student dashboard access is restricted to the exact mapped student identity |
| NFR-S7 | PostgreSQL, Redis, and llama-server remain bound to localhost only |

### Reliability

| ID | Requirement |
|----|-------------|
| NFR-R1 | All services restart automatically on reboot via launchd |
| NFR-R2 | Grading job failure does not affect other queued jobs |
| NFR-R3 | Failed jobs retry up to 3 times before permanent failure |
| NFR-R4 | PostgreSQL is backed up to external storage on a daily schedule |

### Compliance

| ID | Requirement |
|----|-------------|
| NFR-C1 | No student submission content is transmitted outside university-controlled infrastructure |
| NFR-C2 | All grade decisions are recorded in an immutable audit log with user and timestamp |
| NFR-C3 | No result becomes student-visible until status = `released` |
| NFR-C4 | Audit log entries are append-only |

---

## Product Backlog

1 story point ~= 2-4 hours focused work.
Priority: **Must** = M1 required · **Should** = M1 if capacity · **Won't** = post-M1

### Epic 1 - Environment and Infrastructure (Sprint 0)

| ID | Story | Pts | Priority |
|----|-------|-----|----------|
| E1-01 | Docker Compose: postgres, redis, celery, fastapi, nextjs, piston | 3 | Must |
| E1-02 | FastAPI project structure with routers, models, schemas, services | 2 | Must |
| E1-03 | Next.js project structure with App Router | 2 | Must |
| E1-04 | PostgreSQL schema + Alembic initial migration | 3 | Must |
| E1-05 | Submission/version/release-state data model foundation | 3 | Must |
| E1-06 | Celery + Redis wiring | 2 | Must |
| E1-07 | Piston service running locally | 2 | Must |
| E1-08 | llama-server running locally | 2 | Must |
| E1-09 | `.env.example`, README, CI checks | 3 | Must |

**Epic 1 total: 22 points**

---

### Epic 2 - Auth and Identity (Sprint 1)

| ID | Story | Pts | Priority |
|----|-------|-----|----------|
| E2-01 | NextAuth Microsoft OAuth provider | 3 | Must |
| E2-02 | Callback rejects non-`@uvu.edu` logins | 1 | Must |
| E2-03 | Role-based route protection | 2 | Must |
| E2-04 | Role-based API protection | 2 | Must |
| E2-05 | Admin: manage user roles | 3 | Must |
| E2-06 | Student identity mapping (`student_id -> uvu_email`) | 4 | Must |

**Epic 2 total: 15 points**

---

### Epic 3 - Assignment and Rubric Setup (Sprint 1)

| ID | Story | Pts | Priority |
|----|-------|-----|----------|
| E3-01 | Assignment creation form with name, due date, Canvas reference metadata | 2 | Must |
| E3-02 | Rubric builder for criteria and point values | 4 | Must |
| E3-03 | Constraint builder with `review_flag | hard_block` severity | 4 | Must |
| E3-04 | config generation and storage from UI | 3 | Must |
| E3-05 | Validated raw JSON grading config import | 3 | Must |
| E3-06 | Assignment list view | 2 | Must |

**Epic 3 total: 18 points**

---

### Epic 4 - Official Submission Ingestion and Versioning (Sprint 1)

| ID | Story | Pts | Priority |
|----|-------|-----|----------|
| E4-01 | Canvas ZIP upload endpoint with size + type validation | 3 | Must |
| E4-02 | ZIP path traversal protection | 2 | Must |
| E4-03 | Filename parser for official Canvas uploads | 3 | Must |
| E4-04 | Student record lookup from parsed submission data | 2 | Must |
| E4-05 | Official submission version creation per upload | 3 | Must |
| E4-06 | Individual official file upload/reprocess path | 2 | Must |
| E4-07 | Unmatched filename flagging + UI display | 2 | Must |
| E4-08 | Submission list view with version and source metadata | 2 | Must |

**Epic 4 total: 19 points**

---

### Epic 5 - Grading Pipeline and Core Test Management (Sprint 2)

| ID | Story | Pts | Priority |
|----|-------|-----|----------|
| E5-01 | AST checker for supported constraint types | 6 | Must |
| E5-02 | Constraint review-flag vs hard-block behavior | 3 | Must |
| E5-03 | Piston integration with resource limits | 5 | Must |
| E5-04 | pytest execution + output parsing + normalization | 5 | Must |
| E5-05 | Store/manage minimal pytest artifacts per assignment | 4 | Must |
| E5-06 | Link tests to primary rubric criterion and student-visible description | 3 | Must |
| E5-07 | Run model solution against assignment tests | 3 | Must |
| E5-08 | LLM prompt set + hallucination guard | 8 | Must |
| E5-09 | Celery grading chain + immutable result storage | 5 | Must |
| E5-10 | Status endpoint + live polling | 2 | Must |
| E5-11 | Retry and timeout handling | 3 | Must |
| E5-12 | Advanced pytest editor polish | 3 | Should |
| E5-13 | Rich test debugging preview/log UI | 2 | Should |
| E5-14 | Student template authoring polish | 2 | Should |

**Epic 5 total: 54 points**

---

### Epic 6 - Student Dashboard for Official Results (Sprint 3)

| ID | Story | Pts | Priority |
|----|-------|-----|----------|
| E6-01 | Student dashboard shell | 3 | Must |
| E6-02 | Released official submission list view | 3 | Must |
| E6-03 | Released official result detail page | 4 | Must |
| E6-04 | Student access control against mapped identity | 4 | Must |
| E6-05 | Dashboard polish and richer history UI | 3 | Should |

**Epic 6 total: 17 points**

---

### Epic 7 - TA Review and Release Workflow (Sprint 3)

| ID | Story | Pts | Priority |
|----|-------|-----|----------|
| E7-01 | Submission list sortable by score, state, and version | 3 | Must |
| E7-02 | Detail view with code, rubric, annotations, and warnings | 4 | Must |
| E7-03 | TA override + manual comment workflow | 4 | Must |
| E7-04 | Instructor approval and release workflow | 3 | Must |
| E7-05 | Audit log for AI output, override, approval, and release | 4 | Must |
| E7-06 | Submission navigation within assignment | 2 | Must |
| E7-07 | Extra dashboard/review polish | 2 | Should |

**Epic 7 total: 22 points**

---

### Epic 8 - Export (Sprint 3)

| ID | Story | Pts | Priority |
|----|-------|-----|----------|
| E8-01 | CSV export for approved/released official grades | 3 | Must |
| E8-02 | XLSX export formatted for Canvas import | 3 | Must |
| E8-03 | Export blocked until workflow state requirements are met | 2 | Must |

**Epic 8 total: 8 points**

---

### Epic 9 - M2 Follow-On Features

| ID | Story | Pts | Priority |
|----|-------|-----|----------|
| E9-01 | Student self-uploaded practice submissions | 3 | Won't |
| E9-02 | Projected grading for practice submissions | 3 | Won't |
| E9-03 | Practice submission history in dashboard | 2 | Won't |
| E9-04 | LLM-assisted PDF/text rubric conversion | 3 | Won't |
| E9-05 | AI-assisted test generation | 5 | Won't |

---

### Backlog Summary

| Epic | Name | M1 Points | Sprint |
|------|------|-----------|--------|
| E1 | Environment and Infrastructure | 22 | S0 |
| E2 | Auth and Identity | 15 | S1 |
| E3 | Assignment and Rubric Setup | 18 | S1 |
| E4 | Official Submission Ingestion and Versioning | 19 | S1 |
| E5 | Grading Pipeline and Core Test Management | 54 | S2 |
| E6 | Student Dashboard for Official Results | 17 | S3 |
| E7 | TA Review and Release Workflow | 22 | S3 |
| E8 | Export | 8 | S3 |
| **Total with Must + Should** | | **175 points** | |

### Capacity reality check

```text
Conservative (20 hrs/week, 8 weeks, 3 hrs/point): ~53 points
Optimistic   (40 hrs/week, 8 weeks, 3 hrs/point): ~107 points
With Sprint 4 buffer absorbed:                     ~120-130 points realistic
```

The full backlog is still larger than the realistic capacity envelope. To keep M1 project-ready:

- protect E1-E4 as non-negotiable
- protect the Must stories in E5-E8 that are required for official grading, release, export, and student visibility
- cut Should items in E5-E7 first
- if further trimming is required, reduce polish before reducing core workflow

---

## Definition of Done

A story is complete when:

- [ ] feature works end to end, not just in isolation
- [ ] reviewed by at least one teammate
- [ ] no TypeScript or Python type errors on CI
- [ ] Ruff and ESLint pass
- [ ] at least one unit or integration test covers the happy path
- [ ] edge cases handled: bad input, missing file, unmatched student, unreleased result, unauthorized student access
- [ ] no hardcoded secrets or environment-specific values
- [ ] docs updated if setup or behavior changed

---

## Hard Scope Boundaries - M1

These are explicitly out of scope for M1. Do not pull them in under deadline pressure:

- official university SSO integration beyond Microsoft OAuth + `@uvu.edu` domain restriction
- Canvas LTI or grade passback API integration
- student self-uploaded practice submissions
- projected grading before official submission
- LLM-assisted PDF/text rubric conversion
- AI-assisted test generation
- MOSS plagiarism detection
- WeasyPrint PDF generation
- multi-language support beyond Python
- analytics or class-wide reporting
- multi-course support
- mobile-responsive dashboard polish
