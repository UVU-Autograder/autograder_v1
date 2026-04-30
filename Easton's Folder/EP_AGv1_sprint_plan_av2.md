# UVU Autograder — M1 Sprint Plan v2

> Target: Testable V1 by June 30, 2025
> Team: 3 developers, half time (~20–40 hrs/week total)
> Window: April 30 – June 30 (61 days, ~8.5 weeks)
> Backlog tracked in: GitHub Projects (Issues + Milestones)
> Last updated: April 30, 2025

---

## Decision Log

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Backlog tool | GitHub Projects (Issues + Milestones) | Lives in the repo, free, no external dependency |
| Database hosting | Local PostgreSQL on Mac Mini | FERPA — no student data leaves on-prem infrastructure |
| Execution engine | Piston (self-hosted Docker) | Stateless, language-agnostic, clean REST API separation |
| Student delivery | Pre-signed URL portal | Replaces PDF — no login, no friction, FERPA-safe |
| PDF export (WeasyPrint) | Pushed to M2 | Redundant with portal; frees Sprint 3 capacity |
| Resubmission | M1 — open until due date | Instructor-controlled per assignment due date |
| Rubric ingestion | One-time extraction from PDF → config.json | Deterministic scoring, validates LLM coverage |
| LLM provider | llama-server local (Llama 3.3 70B Q4_K_M) | FERPA, zero marginal cost, no external dependency |

---

## Sprint Calendar

```
Apr 30 ─────────────────────────────────────────────────── Jun 30
   │                                                           │
   ├── Sprint 0 ──┤  Apr 30 – May 6   (1 week)   Environment + scaffolding
   ├── Sprint 1 ──┤  May 7  – May 20  (2 weeks)  Auth + assignment setup + rubric ingestion
   ├── Sprint 2 ──┤  May 21 – Jun 3   (2 weeks)  Grading pipeline core
   ├── Sprint 3 ──┤  Jun 4  – Jun 17  (2 weeks)  Student portal + review dashboard + export
   └── Sprint 4 ──┘  Jun 18 – Jun 30  (1.5 weeks) Integration testing + buffer
```

Sprint 4 is a named buffer — not a feature sprint. If Sprints 1–3 complete cleanly,
Sprint 4 is used for hardening and end-to-end testing. Slip absorbs here, not past June 30.

---

## Sprint 0 — Environment + Scaffolding
### April 30 – May 6 (1 week)

**Goal:** Every developer can run the full stack locally. No features. Pipes working end to end.

**Deliverables:**

- [ ] Repo structure agreed — monorepo with `/frontend` (Next.js) and `/backend` (FastAPI)
- [ ] Next.js app bootstrapped (`npx create-next-app --typescript`)
- [ ] FastAPI app bootstrapped with routers, models, schemas folder structure
- [ ] PostgreSQL initial schema — Alembic migration with core tables:
  - `users`, `roles`, `assignments`, `rubric_criteria`, `constraints`,
    `submissions`, `grading_jobs`, `grading_results`, `audit_log`,
    `presigned_tokens`
- [ ] Redis running locally (Docker Compose service)
- [ ] Celery connected to Redis — hello world task fires and completes
- [ ] Piston running as self-hosted Docker container on local dev machine
- [ ] llama-server running locally, responding to a test prompt via curl
- [ ] Docker Compose covers: `postgres`, `redis`, `celery`, `fastapi`, `nextjs`, `piston`
- [ ] `.env.example` with all required environment variables documented
- [ ] README — clone to running in under 30 minutes
- [ ] GitHub Actions — lint (Ruff, ESLint) and type check (Mypy, tsc) on push
- [ ] Seed script — 1 test assignment, 1 rubric (from PDF extraction), 5 sample submissions
- [ ] Rubric extraction script — `pdfplumber` extracts text from PDF rubrics for manual
      review and import into config.json format

**Owner assignments (suggested):**
- Dev A: FastAPI scaffold + PostgreSQL schema + Alembic migrations + Celery/Redis
- Dev B: Next.js scaffold + Docker Compose + GitHub Actions
- Dev C: Piston setup + llama-server setup + rubric extraction script + seed data

**Sprint 0 exit criteria:**
`docker compose up` brings the full stack online. FastAPI health check returns 200.
A manually triggered Celery task completes and writes to Redis. Piston executes a
Hello World Python script and returns stdout. llama-server responds to a test prompt.
Next.js loads at localhost:3000. At least one rubric PDF extracted to config.json.

---

## Sprint 1 — Auth + Assignment Setup + Rubric Ingestion
### May 7 – May 20 (2 weeks)

**Goal:** Instructor and TA can log in, create an assignment with rubric and constraints,
and upload a Canvas ZIP. Rubric PDFs importable via the extraction workflow. No grading yet.

**Deliverables:**

- [ ] NextAuth.js local credential auth (email + password)
- [ ] Role-based route protection middleware (Next.js)
- [ ] Role-based API protection via FastAPI dependency injection
- [ ] Admin panel — create/edit/deactivate users, assign roles
- [ ] Assignment creation form — name, description, due date
- [ ] Rubric builder UI — add/edit/remove criteria with point values
- [ ] Constraint builder UI — type, target, penalty, report_only flag
- [ ] config.json generation and storage from UI inputs
- [ ] Rubric import from extracted JSON — paste or upload from extraction script output
- [ ] Canvas ZIP upload endpoint (FastAPI) with path traversal protection
- [ ] ZIP parser — `lastname_studentid_assignmentname.py` → student records
- [ ] Unmatched filename flagging — unknown files listed for manual review
- [ ] Submission record creation in PostgreSQL per parsed file
- [ ] Submission list view — all submissions, status = `pending`
- [ ] `presigned_tokens` table and token generation utility (used in Sprint 3)

**Owner assignments (suggested):**
- Dev A: NextAuth.js + role middleware + admin panel
- Dev B: Assignment / rubric / constraint UI + config.json + rubric import
- Dev C: ZIP upload + path traversal protection + parser + submission record creation

**Sprint 1 exit criteria:**
Instructor logs in. Creates an assignment with 3 rubric criteria and 2 constraints.
Imports rubric from one of the 4 extracted PDFs. Uploads a ZIP of 5 sample submissions.
All 5 appear in submission list with status `pending`. No unmatched file errors on seed data.
Token generation utility produces valid UUIDs and stores them in `presigned_tokens`.

---

## Sprint 2 — Grading Pipeline Core
### May 21 – June 3 (2 weeks)

**Goal:** The system grades a submission end to end. AST check → Piston execution →
LLM feedback → results stored. Live status visible. No review UI yet.

> **Important:** Spend the first 2–3 days of Sprint 2 on LLM prompt iteration
> with real sample submissions before wiring prompts into the Celery chain.
> Do not assume the first prompt draft produces acceptable output.

**Deliverables:**

- [ ] AST constraint checker — all 5 constraint types:
  - `forbidden_call` — e.g. `sorted()`
  - `forbidden_attribute` — e.g. `.sort()`
  - `forbidden_node` — e.g. `Lambda`
  - `forbidden_import` — e.g. `import collections`
  - `required_definition` — e.g. must define `bubble_sort`
- [ ] Constraint violation report generated per submission
- [ ] Piston integration — FastAPI calls Piston `/api/v2/execute` via httpx
- [ ] Piston resource limits configured: 10s timeout, 256MB memory limit
- [ ] pytest test suite execution via Piston (student code + test file passed together)
- [ ] pytest output parser — structured pass/fail per test case with stdout/stderr
- [ ] python_submitty_utils output normalization on pytest results
- [ ] LLM rubric parser prompt — extracts criteria from config.json into grading context
      (runs once per assignment, result cached, not per submission)
- [ ] LLM code annotator prompt — inline comments on student code
- [ ] LLM rubric scorer prompt — per-criterion score + justification
- [ ] Hallucination guard enforced in all prompts:
      test result is ground truth, LLM explains — never re-evaluates correctness
- [ ] Prompt validation — run all 3 prompts against the 4 rubric PDFs + sample submissions,
      review output quality before marking done
- [ ] Celery grading task chains: AST → Piston → LLM annotator → LLM scorer
- [ ] Grading results stored immutably in PostgreSQL
- [ ] Job status endpoint: `GET /jobs/{id}/status` reads from Redis
- [ ] Submission list live status via 2-second polling (Next.js)
- [ ] Failed job retry — 3 attempts, 10-second backoff
- [ ] Timeout handling — `failed:timeout` state, Celery worker freed immediately

**Owner assignments (suggested):**
- Dev A: AST constraint checker (all 5 types) + violation report
- Dev B: Piston integration + pytest execution + output parser + output normalization
- Dev C: Celery task chain + all 3 LLM prompts + hallucination guard + result storage

**Sprint 2 exit criteria:**
Upload ZIP of 5 sample submissions covering: 1 constraint violation, 1 timeout,
1 correct, 1 partially correct, 1 completely broken. All 5 grade without crashing.
Constraint violations flagged correctly. Timeout marked `failed:timeout`, worker freed.
LLM generates per-criterion feedback for graded submissions. Status polling updates live.
All 3 prompts validated against real rubric PDF content — output reviewed and approved
by at least one team member before sprint closes.

---

## Sprint 3 — Student Portal + Review Dashboard
### June 4 – June 17 (2 weeks)

**Goal:** TA reviews and approves grades. Students access results via pre-signed URL.
Students can resubmit until the assignment due date. Grade CSV/XLSX export works.

> **WeasyPrint PDF export is deferred to M2.** The student portal renders all feedback
> that the PDF would have contained. Instructors can print-to-PDF from the browser natively.

**Deliverables:**

### Student Portal (pre-signed URL)

- [ ] Pre-signed URL generation on instructor "Release Grades" action
      — one UUID token per student per assignment, stored in `presigned_tokens`
- [ ] Token-to-submission mapping in PostgreSQL
- [ ] Bulk token export — CSV with student ID + pre-signed URL
      (instructor pastes into Canvas SpeedGrader or bulk message)
- [ ] Public report page: `GET /report/:token`
      — no login, no session, token is the credential
- [ ] Report page renders:
  - Score summary (per-criterion scores + total)
  - Overall LLM summary
  - Constraint violations (if any)
  - Inline code annotations on syntax-highlighted code
  - Resubmission upload section (if before due date)
- [ ] Due date check — resubmission section hidden/disabled after assignment due date
- [ ] Resubmission upload — student uploads `.py` file via token-authenticated POST
- [ ] Resubmission triggers single-file Celery grading job (same pipeline as bulk)
- [ ] On resubmission completion — report page updates with new results
- [ ] Instructor dashboard shows resubmission indicator on updated submissions
- [ ] Resubmission requires re-review and re-approval by TA/instructor before
      new pre-signed URL reflects updated results
- [ ] Expired/invalid token returns friendly error page (not a 404 or stack trace)

### TA Review Dashboard

- [ ] Submission list — sortable by score, status, resubmission flag
- [ ] Detail view — split pane:
  - Left: syntax-highlighted code with inline LLM comments as margin annotations
  - Right: rubric with AI score, justification, override field per criterion
- [ ] Constraint violation panel in detail view
- [ ] TA score override — input + justification field, saves with TA user ID + timestamp
- [ ] TA manual comment — append to AI comment per criterion
- [ ] TA approve / flag for instructor review
- [ ] Instructor approve button (role-gated, instructor only)
- [ ] Status machine enforced:
      `ai_complete` → `ta_reviewed` → `approved` → `released`
- [ ] Export and pre-signed URL generation blocked until status = `approved`
- [ ] Immutable audit log entries for: AI output, TA override, approver, timestamps
- [ ] Submission navigation — prev/next within assignment
- [ ] Resubmission history — TA can see all submission versions, select which to grade

### Export

- [ ] CSV export — student ID, name, per-criterion scores, total, status (openpyxl)
- [ ] XLSX export — same data, formatted for Canvas manual import
- [ ] Export blocked until all submissions in `approved` state

**Owner assignments (suggested):**
- Dev A: Student portal — pre-signed URL page, report rendering, resubmission upload
- Dev B: TA review dashboard — submission list, detail view, override, approve
- Dev C: Status machine enforcement + audit log + CSV/XLSX export + token bulk export

**Sprint 3 exit criteria:**
Full happy path end to end:
1. Instructor uploads ZIP → submissions grade → TA reviews, overrides 1 score,
   adds 1 manual comment → instructor approves all
2. Instructor releases grades → bulk token CSV generated
3. Student navigates to pre-signed URL → sees score, feedback, annotated code
4. Student uploads resubmission before due date → job queues and grades →
   report page updates with new results
5. TA re-reviews resubmission → instructor re-approves
6. Instructor exports CSV → file opens correctly in Excel
7. Audit log shows correct entries for every action in the workflow

---

## Sprint 4 — Integration Testing + Buffer
### June 18 – June 30 (1.5 weeks)

**Goal:** System works as a whole under realistic conditions. Not a feature sprint.

**Activities:**

- [ ] End-to-end test with realistic class-size dataset (30–50 submissions)
- [ ] Memory budget validation — monitor `vm_stat` during full grading run on Mac Mini
- [ ] Security validation:
  - Attempt network access from inside a Piston execution — confirm blocked
  - Craft malicious ZIP with path traversal — confirm rejected before extraction
  - Access another student's pre-signed URL with a guessed token — confirm rejected
- [ ] Timeout validation — submit `while True: pass`, confirm worker freed in <15s
- [ ] Resubmission validation — submit after due date, confirm upload blocked
- [ ] Audit log completeness — every grade decision traceable to user + timestamp
- [ ] Export validation — CSV totals match DB values, XLSX opens in Excel without errors
- [ ] Smoke test on production Mac Mini (not just dev machines)
- [ ] `launchd` service files for all processes — confirm auto-restart after reboot
- [ ] Production Nginx config reviewed — rate limiting, HSTS, CSP headers
- [ ] Update README with production deployment steps
- [ ] Record demo walkthrough video — full workflow in under 5 minutes (backup for live demo)
- [ ] Fix bugs surfaced by testing (no new features)
- [ ] Tag `v0.1.0-alpha` release on repo

**Sprint 4 exit criteria (= M1 done):**
A team member unfamiliar with the codebase can complete the full workflow —
upload, grade, review, approve, release, student views report, student resubmits,
re-review, re-approve, export — without assistance and without a crash.
Demo video covers the complete happy path.

---

## Tech Stack Reference

### Full Stack

| Layer | Technology | Version | Role |
|-------|------------|---------|------|
| Frontend framework | Next.js | 14.x (App Router) | Instructor/TA dashboard + student portal |
| UI language | TypeScript | 5.x | Type safety across frontend |
| Auth | NextAuth.js | 5.x (Auth.js) | Local credentials M1, SSO added M3 |
| Backend framework | FastAPI | 0.110.x | API, business logic, prompt engine |
| Backend language | Python | 3.11+ | Grading pipeline, LLM integration |
| Task queue | Celery | 5.3.x | Async grading jobs |
| Message broker | Redis | 7.x | Celery broker + result backend |
| Database | PostgreSQL | 16.x | Local on Mac Mini — all student data on-prem |
| ORM | SQLAlchemy | 2.x | DB access from FastAPI |
| Migrations | Alembic | 1.13.x | Schema versioning |
| Reverse proxy | Nginx | 1.24.x | TLS termination, rate limiting |
| Containerization | Docker + Compose | 25.x | Dev environment + Piston service |
| Inference server | llama-server (llama.cpp) | latest | Local LLM, Metal acceleration |
| LLM model | Llama 3.3 70B Q4_K_M | — | Grading feedback generation |
| Grade export | openpyxl | 3.1.x | CSV / XLSX export for Canvas import |
| Code highlighting | Prism.js | 1.29.x | Syntax highlighting in portal + dashboard |
| PDF extraction | pdfplumber | 0.10.x | One-time rubric PDF → text extraction |

### Grading Pipeline

| Component | Technology | Role |
|-----------|------------|------|
| Static analysis | Python `ast` (stdlib) | Constraint checking before execution |
| Execution engine | Piston (self-hosted Docker) | Sandboxed student code execution |
| HTTP client | httpx | FastAPI → Piston async REST calls |
| Test framework | pytest | Student code test execution inside Piston |
| Output normalization | python_submitty_utils | Whitespace/encoding false-negative prevention |
| Plagiarism | mosspy | M2 — not M1 |
| PDF report | WeasyPrint | M2 — not M1 |

### Infrastructure Notes

| Component | Location | Note |
|-----------|----------|------|
| PostgreSQL | Mac Mini local | Data never leaves on-prem — FERPA by design |
| Redis | Mac Mini local | Celery broker + result backend |
| Piston | Mac Mini Docker | Requires `--privileged` flag — document for IT |
| llama-server | Mac Mini local | Persistent launchd service, ~40GB in unified memory |
| Nginx | Mac Mini local | TLS termination — InCommon cert added in M3 |

### Development Tooling

| Tool | Purpose |
|------|---------|
| GitHub Projects | Backlog, sprint boards, issue tracking |
| GitHub Actions | CI — lint and type check on push |
| ESLint + Prettier | Frontend code style |
| Ruff | Python linter (replaces flake8 + isort) |
| Mypy | Python type checking |
| pytest | Backend unit and integration tests |
| Docker Compose | Full local stack in one command |
| Alembic | Database migration management |

---

## Open-Source Components

### Used in M1

| Component | Source | How used |
|-----------|--------|----------|
| Piston | engineer-man/piston | Self-hosted execution engine — REST API, stateless, 100+ languages |
| python_submitty_utils | Submitty/Submitty | Output normalization, token diff |
| llama.cpp / llama-server | ggerganov/llama.cpp | Local LLM inference, Metal acceleration |
| NextAuth.js | nextauthjs/next-auth | Auth framework — local credentials M1 |
| pdfplumber | jsvine/pdfplumber | Rubric PDF text extraction (setup step, not runtime) |

### Used in M2

| Component | Source | How used |
|-----------|--------|----------|
| WeasyPrint | Kozea/WeasyPrint | Instructor-facing PDF archive export |
| mosspy | soachishti/moss.py | MOSS plagiarism detection |

### Architectural patterns borrowed

| Source | Pattern |
|--------|---------|
| Autolab / Tango (CMU) | Job queue architecture → Celery + Redis |
| Autolab / Tango (CMU) | Submission versioning model |
| Submitty (RPI) | config.json grading spec format |
| Submitty (RPI) | Worker isolation model → Piston container hardening |

---

## Functional Requirements

### FR-01 — Admin

| ID | Requirement | Sprint |
|----|-------------|--------|
| FR-01.1 | Admin can create, edit, deactivate user accounts | S1 |
| FR-01.2 | Admin can assign roles: admin, course_admin, instructor, ta | S1 |
| FR-01.3 | Admin can view system-wide audit log | S3 |
| FR-01.4 | Admin can configure LLM endpoint and model parameters | S0 |

### FR-02 — Instructor

| ID | Requirement | Sprint |
|----|-------------|--------|
| FR-02.1 | Instructor can create assignments with name, description, due date | S1 |
| FR-02.2 | Instructor can define rubric criteria with point values | S1 |
| FR-02.3 | Instructor can import rubric from extracted PDF JSON | S1 |
| FR-02.4 | Instructor can define constraints separately from rubric | S1 |
| FR-02.5 | Instructor can upload bulk Canvas ZIP | S1 |
| FR-02.6 | Instructor can view live grading status per submission | S2 |
| FR-02.7 | Instructor can review AI comments and scores | S3 |
| FR-02.8 | Instructor can override AI score per criterion | S3 |
| FR-02.9 | Instructor can approve submissions (gate before release) | S3 |
| FR-02.10 | Instructor can release grades — generates pre-signed URLs | S3 |
| FR-02.11 | Instructor can export approved grades as CSV and XLSX | S3 |

### FR-03 — TA

| ID | Requirement | Sprint |
|----|-------------|--------|
| FR-03.1 | TA can upload bulk Canvas ZIP for assigned section | S1 |
| FR-03.2 | TA can view submission list with live status | S2 |
| FR-03.3 | TA can review AI inline comments and per-criterion scores | S3 |
| FR-03.4 | TA can override AI score per criterion with justification | S3 |
| FR-03.5 | TA can add manual comments on top of AI comments | S3 |
| FR-03.6 | TA can approve submission or flag for instructor review | S3 |
| FR-03.7 | TA cannot release grades — instructor approval required | S3 |
| FR-03.8 | TA can view constraint violation report per submission | S3 |
| FR-03.9 | TA can view resubmission history and select version to grade | S3 |

### FR-04 — Grading Pipeline

| ID | Requirement | Sprint |
|----|-------------|--------|
| FR-04.1 | System parses Canvas ZIP filename format to student records | S1 |
| FR-04.2 | System flags unmatched filenames for manual review | S1 |
| FR-04.3 | System runs AST constraint checker before execution | S2 |
| FR-04.4 | System executes pytest via Piston with resource limits | S2 |
| FR-04.5 | System enforces 10-second execution timeout | S2 |
| FR-04.6 | System normalizes output before comparison | S2 |
| FR-04.7 | System sends code + test results to LLM feedback agent | S2 |
| FR-04.8 | LLM generates per-criterion comment consistent with test results | S2 |
| FR-04.9 | System stores AI output, test results, violations immutably | S2 |
| FR-04.10 | Grading jobs process asynchronously via Celery | S2 |
| FR-04.11 | Live job status displayed via 2-second polling | S2 |
| FR-04.12 | Failed jobs retry up to 3 times with backoff | S2 |
| FR-04.13 | Constraint violations reported separately from rubric scores | S2 |

### FR-05 — Student Portal

| ID | Requirement | Sprint |
|----|-------------|--------|
| FR-05.1 | System generates unique pre-signed UUID token per student per assignment | S3 |
| FR-05.2 | Instructor exports bulk CSV of student ID + pre-signed URL | S3 |
| FR-05.3 | Student accesses report via pre-signed URL — no login required | S3 |
| FR-05.4 | Report page shows: score summary, feedback, annotations, violations | S3 |
| FR-05.5 | Student can upload resubmission before assignment due date | S3 |
| FR-05.6 | Resubmission blocked after assignment due date | S3 |
| FR-05.7 | Resubmission triggers same grading pipeline as original submission | S3 |
| FR-05.8 | Report page updates with new results after resubmission grades | S3 |
| FR-05.9 | Resubmission flags submission for re-review in TA dashboard | S3 |
| FR-05.10 | Invalid or expired token returns friendly error page | S3 |

---

## Non-Functional Requirements

### Performance

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-P1 | ZIP upload response time | < 2s for files up to 50MB |
| NFR-P2 | Concurrent grading throughput | 8 submissions simultaneously |
| NFR-P3 | 200-submission batch completion | < 40 min on 256GB hardware |
| NFR-P4 | Status polling response time | < 200ms |
| NFR-P5 | Student portal page load | < 2s |
| NFR-P6 | Pre-signed URL generation (bulk, 200 students) | < 5s |

### Security

| ID | Requirement |
|----|-------------|
| NFR-S1 | Piston executes student code with network access disabled |
| NFR-S2 | Piston memory limit 256MB, timeout 10 seconds enforced |
| NFR-S3 | ZIP extraction validates all paths before any file is written |
| NFR-S4 | All FastAPI endpoints require valid session token (except /report/:token) |
| NFR-S5 | Role-based access enforced at API layer, not just UI |
| NFR-S6 | No student data transmitted to any external service |
| NFR-S7 | PostgreSQL, Redis, llama-server bound to localhost only |
| NFR-S8 | Pre-signed tokens are UUID v4 — not sequential, not guessable |
| NFR-S9 | Piston container runs with `--privileged` — documented for IT security review |

### Reliability

| ID | Requirement |
|----|-------------|
| NFR-R1 | All services restart automatically on reboot via launchd |
| NFR-R2 | Grading job failure does not affect other queued jobs |
| NFR-R3 | Failed jobs retry up to 3 times before marking permanently failed |
| NFR-R4 | PostgreSQL backed up to external volume on daily schedule |

### Compliance

| ID | Requirement |
|----|-------------|
| NFR-C1 | No student submission content transmitted outside university infrastructure |
| NFR-C2 | All grade decisions recorded in immutable audit log with user + timestamp |
| NFR-C3 | No grade released until status = approved by instructor |
| NFR-C4 | Audit log entries append-only — no update or delete permitted |
| NFR-C5 | Pre-signed URL access does not expose student identity in URL or page |

---

## Product Backlog

1 story point ≈ 2–4 hours focused work.
Priority: **Must** = M1 required · **Should** = M1 if capacity · **Won't** = post-M1

### Epic 1 — Environment and Infrastructure (Sprint 0)

| ID | Story | Pts | Priority |
|----|-------|-----|----------|
| E1-01 | Docker Compose: postgres, redis, celery, fastapi, nextjs, piston | 3 | Must |
| E1-02 | FastAPI project structure with routers, models, schemas | 2 | Must |
| E1-03 | Next.js project structure with App Router and layout | 2 | Must |
| E1-04 | PostgreSQL schema + Alembic initial migration | 3 | Must |
| E1-05 | Celery + Redis wiring — hello world task fires end to end | 2 | Must |
| E1-06 | Piston self-hosted container running, executes Python test | 2 | Must |
| E1-07 | llama-server running locally, responds to test prompt via curl | 2 | Must |
| E1-08 | `.env.example` and environment variable documentation | 1 | Must |
| E1-09 | README — clone to running in under 30 minutes | 2 | Must |
| E1-10 | GitHub Actions — lint and type check on push | 2 | Must |
| E1-11 | Seed script — assignment, rubric, 5 sample submissions | 2 | Must |
| E1-12 | PDF rubric extraction script (pdfplumber) | 2 | Must |

**Epic 1 total: 25 points**

---

### Epic 2 — Auth and User Management (Sprint 1)

| ID | Story | Pts | Priority |
|----|-------|-----|----------|
| E2-01 | NextAuth.js local credential provider | 3 | Must |
| E2-02 | Role-based route protection middleware (Next.js) | 2 | Must |
| E2-03 | Role-based API protection (FastAPI dependency) | 2 | Must |
| E2-04 | Admin: create and edit user accounts | 3 | Must |
| E2-05 | Admin: assign roles | 2 | Must |
| E2-06 | Admin: deactivate accounts | 1 | Must |
| E2-07 | Login page UI | 2 | Must |

**Epic 2 total: 15 points**

---

### Epic 3 — Assignment and Rubric Setup (Sprint 1)

| ID | Story | Pts | Priority |
|----|-------|-----|----------|
| E3-01 | Assignment creation form | 2 | Must |
| E3-02 | Rubric builder — add/edit/remove criteria + point values | 4 | Must |
| E3-03 | Constraint builder — type, target, penalty, report_only | 4 | Must |
| E3-04 | config.json generation from UI inputs | 3 | Must |
| E3-05 | Rubric import from extracted PDF JSON | 3 | Must |
| E3-06 | Assignment list view for instructor | 2 | Must |
| E3-07 | Edit assignment before submissions uploaded | 2 | Should |

**Epic 3 M1 total: 20 points**

---

### Epic 4 — Submission Ingestion (Sprint 1)

| ID | Story | Pts | Priority |
|----|-------|-----|----------|
| E4-01 | Canvas ZIP upload endpoint with size + type validation | 3 | Must |
| E4-02 | ZIP path traversal protection | 2 | Must |
| E4-03 | Filename parser — Canvas format → student record | 3 | Must |
| E4-04 | Student record creation/lookup from parsed filename | 2 | Must |
| E4-05 | Submission record creation per parsed file | 2 | Must |
| E4-06 | Unmatched filename flagging + UI display | 2 | Must |
| E4-07 | Submission list view — status = pending | 2 | Must |
| E4-08 | Submission versioning — new upload preserves prior version | 2 | Should |

**Epic 4 M1 total: 18 points**

---

### Epic 5 — Grading Pipeline (Sprint 2)

| ID | Story | Pts | Priority |
|----|-------|-----|----------|
| E5-01 | AST: forbidden_call | 2 | Must |
| E5-02 | AST: forbidden_attribute | 2 | Must |
| E5-03 | AST: forbidden_node | 2 | Must |
| E5-04 | AST: forbidden_import | 2 | Must |
| E5-05 | AST: required_definition | 2 | Must |
| E5-06 | Constraint violation report per submission | 2 | Must |
| E5-07 | Piston integration — httpx async POST to /api/v2/execute | 4 | Must |
| E5-08 | pytest execution via Piston — student code + test file | 3 | Must |
| E5-09 | pytest output parser — structured pass/fail per test | 3 | Must |
| E5-10 | python_submitty_utils output normalization | 2 | Must |
| E5-11 | LLM rubric parser prompt (once per assignment, cached) | 2 | Must |
| E5-12 | LLM code annotator prompt | 3 | Must |
| E5-13 | LLM rubric scorer prompt | 3 | Must |
| E5-14 | Hallucination guard in all 3 prompts | 2 | Must |
| E5-15 | Prompt validation against 4 rubric PDFs + sample submissions | 3 | Must |
| E5-16 | Celery task chain: AST → Piston → LLM annotator → LLM scorer | 4 | Must |
| E5-17 | Grading results stored immutably in PostgreSQL | 2 | Must |
| E5-18 | Job status endpoint (GET /jobs/{id}/status) | 2 | Must |
| E5-19 | Submission list live status via 2-second polling | 2 | Must |
| E5-20 | Job retry — 3 attempts, 10-second backoff | 2 | Must |
| E5-21 | Timeout handling — failed:timeout, worker freed | 2 | Must |

**Epic 5 total: 51 points**

---

### Epic 6 — Student Portal (Sprint 3)

| ID | Story | Pts | Priority |
|----|-------|-----|----------|
| E6-01 | Pre-signed UUID token generation on grade release | 2 | Must |
| E6-02 | Token storage in presigned_tokens table | 1 | Must |
| E6-03 | Bulk token CSV export (student ID + URL) | 2 | Must |
| E6-04 | Public report page — /report/:token, no login | 3 | Must |
| E6-05 | Report page: score summary + per-criterion feedback | 3 | Must |
| E6-06 | Report page: syntax-highlighted code + inline annotations | 4 | Must |
| E6-07 | Report page: constraint violations section | 2 | Must |
| E6-08 | Resubmission upload on report page (before due date) | 3 | Must |
| E6-09 | Due date enforcement — upload blocked after deadline | 2 | Must |
| E6-10 | Resubmission triggers single-file Celery grading job | 3 | Must |
| E6-11 | Report page updates after resubmission grades complete | 2 | Must |
| E6-12 | Resubmission flags submission for re-review in dashboard | 2 | Must |
| E6-13 | Invalid/expired token — friendly error page | 1 | Must |

**Epic 6 total: 30 points**

---

### Epic 7 — TA Review Dashboard (Sprint 3)

| ID | Story | Pts | Priority |
|----|-------|-----|----------|
| E7-01 | Submission list — sortable by score, status, resubmission flag | 3 | Must |
| E7-02 | Detail view — split pane code + rubric | 3 | Must |
| E7-03 | Inline LLM comments as margin annotations on code | 4 | Must |
| E7-04 | Per-criterion AI score + justification display | 3 | Must |
| E7-05 | TA score override input + justification field | 3 | Must |
| E7-06 | TA manual comment — append to AI comment | 2 | Must |
| E7-07 | Constraint violation panel in detail view | 2 | Must |
| E7-08 | TA approve / flag for instructor review | 2 | Must |
| E7-09 | Instructor approve button (role-gated) | 2 | Must |
| E7-10 | Status machine: ai_complete → ta_reviewed → approved → released | 3 | Must |
| E7-11 | Release and export blocked until status = approved | 2 | Must |
| E7-12 | Immutable audit log — AI output, override, approver, timestamp | 3 | Must |
| E7-13 | Resubmission history view — all versions, select to grade | 3 | Must |
| E7-14 | Submission navigation — prev/next within assignment | 1 | Should |

**Epic 7 M1 total: 36 points**

---

### Epic 8 — Export (Sprint 3)

| ID | Story | Pts | Priority |
|----|-------|-----|----------|
| E8-01 | CSV export — student ID, name, per-criterion scores, total | 3 | Must |
| E8-02 | XLSX export — formatted for Canvas manual import | 3 | Must |
| E8-03 | Export blocked until all submissions approved | 2 | Must |
| E8-04 | PDF report per student (WeasyPrint) | 5 | **M2** |

**Epic 8 M1 total: 8 points**

---

### Backlog Summary

| Epic | Name | M1 Points | Sprint |
|------|------|-----------|--------|
| E1 | Environment + Infrastructure | 25 | S0 |
| E2 | Auth + User Management | 15 | S1 |
| E3 | Assignment + Rubric Setup | 20 | S1 |
| E4 | Submission Ingestion | 18 | S1 |
| E5 | Grading Pipeline | 51 | S2 |
| E6 | Student Portal | 30 | S3 |
| E7 | TA Review Dashboard | 36 | S3 |
| E8 | Export (M1 scope) | 8 | S3 |
| **Total** | | **203 points** | |

### Capacity reality check

```
Conservative (20 hrs/week, 8 weeks, 3 hrs/point): ~53 points
Optimistic   (40 hrs/week, 8 weeks, 3 hrs/point): ~107 points
With Sprint 4 buffer absorbed:                     ~120–130 points realistic
```

203 points cannot all complete at half time in 8 weeks. Sprint 4 and the
Should-priority items are the release valve. Must-priority items in E1–E5
are non-negotiable for a testable V1. E6–E7 Must items are the M1 differentiator
and must be protected in Sprint 3. Cut Should items first, then scope creep, never Must.

---

## Definition of Done

A story is complete when:

- [ ] Feature works end-to-end, not just in isolation
- [ ] Reviewed by at least one other team member (PR required)
- [ ] No TypeScript or Python type errors on CI
- [ ] Ruff and ESLint pass with no warnings
- [ ] At least one unit test covers the happy path
- [ ] Edge cases handled: empty input, bad input, missing file, expired token
- [ ] No hardcoded secrets, paths, or environment-specific values
- [ ] README or inline docs updated if setup or config changes

---

## Hard Scope Boundaries — M1

These are explicitly out of scope for M1. Do not pull them in under deadline pressure:

- Canvas LTI or grade passback API integration
- University SSO (Azure AD, Canvas OIDC) — local credentials only
- MOSS plagiarism detection — M2
- WeasyPrint PDF generation — M2
- AI content detection
- Multi-language support beyond Python
- HTML/CSS assignment grading
- Analytics or class-wide reporting
- Multi-course support
- Mobile-responsive dashboard
