# Preserved reference doc: copied from `implementation_folder/Implementation_ideas/EP_AGv1_sprint_plan.md`.
# This file is intentionally preserved for planning context. When it conflicts with the Jaxon docs in this folder, the Jaxon docs remain the canonical M1 implementation source of truth.

# UVU Autograder v1 — Canonical Sprint Plan
## Version 3: Easton + Jaxon architecture notes + Frontend Implementation

> Target: Testable M1 by June 30, 2025
> Team: 5 developers, half time (~35–65 hrs/week total)
> Window: 8–9 weeks
> Backlog tracked in: GitHub Projects (Issues + Milestones)
> Last updated: May 7, 2025

---

## Decision Log

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Backlog tool | GitHub Projects (Issues + Milestones) | Lives in the repo|
| Data retention | Zero-retention for student submissions and grading artifacts | Structural FERPA mitigation — no student code persists |
| Database scope | Staff, courses, assignments, configs, and sanitized run metadata only | Keeps the persistent footprint small and non-sensitive |
| Execution engine | Piston (self-hosted Docker) + Kata Containers runtime | Piston API interface + VM-level kernel isolation per execution |
| VM isolation approach | Kata Containers (M1) — Firecracker evaluated for M2 | Kata = drop-in Docker runtime swap, ~4hrs backend work vs ~35hrs for Firecracker |
| AI inference | Azure OpenAI API with Zero Data Retention (ZDR) enabled | University-approved cloud inference; ZDR ensures no prompt content persisted on Microsoft infrastructure |
| Plagiarism detection | Stanford MOSS via `mosspy` | Optional staff review aid, ephemeral batch files only |
| Auth (M1) | NextAuth + Microsoft OAuth + `@uvu.edu` domain restriction | Fastest realistic path to trusted UVU identity |
| Student access | Session-based sandbox only — no persistent student records | Zero-retention by design; students use sandbox for projected feedback |
| Assignment content | Canvas-canonical | Assignment descriptions, rosters, and final grades remain in Canvas |
| Rubric/config setup | Wizard + raw `config.json` import/export | Supports guided setup and direct JSON editing without overbuilding |
| Concept policy | `Concepts Covered` progressive whitelist | Aligns AST checks and LLM feedback to course timeline |
| Output format | Staff: CSV + master ZIP of per-student HTML feedback. Students: on-screen projected feedback only | Lightweight, zero-retention-compatible |
| Hosting | Railway (M1 production) | Removes deployment ambiguity for M1; on-prem architecture remains an open discussion for M2+ |
| Hardware (dev/staging) | Dell Pro Max Tower T2, Ubuntu 24.04 LTS | See hardware section below |

---

## Hardware Reference

| Spec | Detail | Notes |
|------|--------|-------|
| CPU | Intel Core Ultra 7 265, 20 cores, up to 5.3 GHz | Sufficient for Celery worker pool + Piston containers |
| GPU | NVIDIA RTX PRO 4500 Blackwell, 32GB GDDR7 | Unused in M1 (Azure OpenAI handles inference). Reserved for local LLM evaluation in M2+ |
| System RAM | 32GB DDR5 5600 MT/s | Primary constraint for concurrent VM execution — see memory budget below |
| Storage | 2TB M.2 NVMe Gen4 SSD | Ephemeral temp space only — no student data persists |
| OS | Ubuntu 24.04 LTS | KVM-native, better kernel scheduling than Windows for server workloads |
| Network | Intel Wi-Fi 7 BE200 / wired preferred for production | University data center connection if deployed on-prem |

### Memory Budget (32GB system RAM)

```
Component                              Estimated usage
──────────────────────────────────────────────────────
Ubuntu OS + system services             ~2 GB
PostgreSQL                              ~1 GB
Redis                                   ~0.5 GB
FastAPI + Next.js processes             ~1.5 GB
Celery workers (8 × ~100MB)            ~0.8 GB
Piston API service                      ~0.5 GB
8 concurrent Kata VM executions
  × ~80MB overhead each                ~0.64 GB
──────────────────────────────────────────────────────
Total estimated peak                    ~7 GB
Available headroom                      ~25 GB
```

32GB is comfortable for M1 workloads with Kata Containers.
Firecracker (~5MB/VM overhead) would extend this further but
is not worth the implementation cost in M1.

---

## VM Isolation — Kata Containers on Piston

### Why Kata over plain Docker for student code execution

Plain Docker containers share the host kernel. A kernel exploit in student code
can escape the container. Kata Containers gives each execution its own kernel —
a kernel exploit hits a virtualized kernel, not the host. The isolation guarantee
is identical to a full VM at near-container startup speed (~500ms).

### Why Kata over Firecracker for M1

Firecracker provides the same isolation with less overhead but requires:
- Building and maintaining custom kernel + rootfs images
- Writing a Python orchestration layer from scratch (no mature client)
- Managing tap network interfaces per VM under concurrent load
- Estimated: **30–40 hours of backend work** (~10–13 story points)

Kata Containers is a one-config swap:

```bash
# Ubuntu 24.04 — total backend cost ~4 hours
sudo apt install -y kata-containers

# Configure containerd to use kata runtime
# /etc/containerd/config.toml
[plugins."io.containerd.grpc.v1.cri".containerd.runtimes.kata]
  runtime_type = "io.containerd.kata.v2"

# Piston picks up the kata runtime — zero API changes required
```

Firecracker remains the M2 upgrade path once M1 is stable and the team has
bandwidth for the infrastructure work.

### Security properties with Kata

| Property | Value |
|----------|-------|
| Kernel isolation | Each execution gets its own Linux kernel |
| Network | Disabled at the Piston config level |
| Memory limit | 256MB per execution (Piston resource limit) |
| Timeout | 10 seconds, kills entire VM |
| Filesystem | Read-only except designated output |
| Persistence | VM destroyed immediately after execution |
| Host kernel exposure | None — kernel exploit stays inside the VM |

---

## Azure OpenAI — FERPA Compliance Path

Azure OpenAI is the correct choice for M1 for two reasons that the standard OpenAI
API cannot match:

**Zero Data Retention (ZDR):** Azure OpenAI supports a configurable mode where
prompt content is not logged, stored, or used for model training. With ZDR enabled,
student code that transits the API leaves no persistent trace on Microsoft's
infrastructure. This must be explicitly requested and confirmed in the Azure portal.

**FERPA Business Associate Agreement:** Microsoft maintains a FERPA BAA for Azure
services for educational institutions. UVU's existing Microsoft 365 / Azure EDU
enterprise agreement almost certainly covers Azure OpenAI API calls under that BAA.
Confirm with UVU IT before Sprint 2 begins — this is a single email, not a
procurement process.

**Action item:** Confirm ZDR is enabled on the Azure OpenAI deployment and verify
that UVU's Microsoft enterprise agreement covers API calls under their FERPA BAA.
Owner: TBD. Due: before Sprint 2 (May 21).

### Azure OpenAI prompt structure

```python
# Hallucination guard — test result is always ground truth
# LLM explains failures, never re-evaluates correctness

FEEDBACK_PROMPT = """
You are a teaching assistant for an introductory Python course.

Concepts the student is allowed to use in this assignment:
{allowed_concepts}

The following test {status}. This is factual — do not question it.
Your job is to explain WHY it likely {status_verb} based on the code,
and give a constructive hint without revealing the solution.

Test: {test_name}
Result: {status}
Output: {stderr}
Rubric criterion: {criterion_description}
Student code:
{student_code}
"""

# Token usage logged to run_summaries — not student code or feedback content
```

---

## Team Structure + Sprint 0 Parallel Track

Sprint 0 runs two workstreams simultaneously for 2 weeks:

```
May 7 – May 20 (Sprint 0, 2 weeks)
├── Easton + Jaxon (backend track)
│     Class diagram + backend architecture skeleton
│     - Entity-relationship diagram (Lucidchart)
│     - Class diagram covering all domain models
│     - FastAPI router skeleton with typed request/response schemas
│     - SQLAlchemy model definitions matching the DB schema
│     - Celery task structure documented
│     - Prompt integration boundaries defined
│     - Architecture ADR (Architecture Decision Record) written
│
└── Dev C + Dev D + Dev E (frontend track)
      UI/UX proposal + frontend skeleton
      - Wireframes for all staff views (Figma or equivalent)
      - Wireframes for student sandbox view
      - Next.js App Router scaffold
      - Component hierarchy defined
      - Design system / Tailwind config established
      - Routing structure matching role-based access plan
      - Placeholder pages for all Sprint 1–3 features
```

**Merge point:** End of week 2 (May 20). Both tracks present to the full team.
Backend architecture and frontend component hierarchy must be agreed before
Sprint 1 begins. This is the single most important alignment checkpoint in the
project — do not start Sprint 1 until both tracks have signed off on the shared
interface contracts (API request/response shapes, URL structure, component props).

---

## Sprint Calendar

```
May 7  ─────────────────────────────────────────────────── Jun 30
   │                                                           │
   ├── Sprint 0 ──┤  May 7  – May 20  (2 weeks)  Architecture + UI/UX skeleton [PARALLEL]
   ├── Sprint 1 ──┤  May 21 – Jun 3   (2 weeks)  Auth + assignment setup + ephemeral ingestion
   ├── Sprint 2 ──┤  Jun 4  – Jun 17  (2 weeks)  Grading pipeline + Azure OpenAI + Kata
   ├── Sprint 3 ──┤  Jun 18 – Jun 24  (1 week)   Student sandbox + batch UX + export
   └── Sprint 4 ──┘  Jun 25 – Jun 30  (1 week)   Integration testing + FERPA hardening
```

> Note: Sprint 3 and Sprint 4 are compressed to 1 week each because Sprint 0
> is now 2 weeks (matching the team's architecture + UI/UX parallel tracks).
> This is intentional — Sprint 0 de-risks Sprints 1–3 by resolving architectural
> ambiguity before any feature work begins.

---

## Sprint 0 — Architecture + UI/UX Skeleton
### May 7 – May 20 (2 weeks, parallel tracks)

### Backend track (Easton + Jaxon)

**Goal:** Canonical backend architecture decided, documented, and skeletonized.
Every backend developer knows the shape of every model, service, and API endpoint
before Sprint 1 begins.

**Deliverables:**

- [ ] Entity-relationship diagram — all tables, relationships, cardinalities (Lucidchart)
- [ ] Class diagram — domain models, service classes, Celery tasks (Lucidchart)
- [ ] PostgreSQL schema finalized + Alembic initial migration:
  - `users`, `roles`, `courses`, `sections`, `assignments`,
    `assignment_configs`, `concept_sets`, `assignment_artifacts`,
    `run_summaries`
- [ ] FastAPI router skeleton — all endpoints stubbed with typed schemas, no logic
- [ ] SQLAlchemy model definitions matching schema
- [ ] Celery task structure defined — official grading chain + sandbox chain
- [ ] Prompt integration boundaries documented — where Azure OpenAI calls happen,
  what goes in, what comes out, how hallucination guard is enforced
- [ ] Architecture Decision Record written for: execution isolation, zero-retention,
  Azure OpenAI ZDR, Kata Containers, Railway setup
- [ ] Docker Compose: `postgres`, `redis`, `celery`, `fastapi`, `nextjs`, `piston`
- [ ] Kata Containers configured as Piston's container runtime
- [ ] Piston running locally with Kata runtime, executes Hello World Python
- [ ] Celery + Redis wiring — hello world task fires end to end
- [ ] `.env.example` documents all required variables including Azure OpenAI settings
- [ ] Seed script: 1 course, 1 assignment, 1 config.json, 1 concept set, 1 model solution

**Exit criteria:**
FastAPI skeleton starts with no import errors. All endpoint stubs return 501.
Piston executes Python via Kata runtime. Celery task completes. ER diagram and
class diagram reviewed and approved by full team.

---

### Frontend track (Bjorn + Keomary + Dominic)

**Goal:** UI/UX fully wireframed and the Next.js skeleton matches the wireframes.
Frontend developers know the component hierarchy, routing, and design system
before Sprint 1 begins.

**Deliverables:**

- [ ] Wireframes for all staff views:
  - Login page
  - Admin: user + role management
  - Instructor/IA: assignment list, assignment creation, config wizard,
    config JSON editor, Concepts Covered checklist, Canvas ZIP upload,
    official run list, run detail view, result preview, export download
- [ ] Wireframes for student sandbox view:
  - Assignment selector, upload form, projected feedback view,
    zero-retention messaging
- [ ] Wireframes reviewed and approved by Easton + Jaxon before Sprint 1
- [ ] Next.js App Router scaffold (TypeScript)
- [ ] Tailwind config + design tokens established
- [ ] Component hierarchy documented
- [ ] Routing structure: all role-based routes stubbed with placeholder pages
- [ ] Shared layout components: nav, sidebar, role-aware header
- [ ] Auth flow pages: login, redirect, error
- [ ] README section: how to run frontend locally

**Exit criteria:**
`npm run dev` starts Next.js. All routes load without errors (placeholder content
acceptable). Wireframes approved. Component hierarchy agreed with backend team.

---

## Sprint 1 — Auth + Assignment Setup + Ephemeral Ingestion
### May 21 – June 3 (2 weeks, full team)

**Goal:** UVU users can authenticate, staff can configure assignments, and Canvas
ZIP uploads are parsed into transient official runs without persisting student code.

**Deliverables:**

- [ ] NextAuth Microsoft OAuth provider configured
- [ ] OAuth callback rejects any login not ending in `@uvu.edu`
- [ ] Role-based route protection (Next.js middleware)
- [ ] Role-based API protection (FastAPI dependency injection)
- [ ] Admin: staff account management (create, edit, deactivate, assign roles)
- [ ] Student sign-in path — session only, no persistent student records created
- [ ] Assignment creation form: name, course linkage, due date, Canvas metadata
- [ ] Config wizard: captures core rubric/config fields, generates valid `config.json`
- [ ] Raw `config.json` paste/import with validation and error display
- [ ] Stored config editor — renders editable fields from current `config.json`
- [ ] `config.json` download by staff
- [ ] Concepts Covered checklist UI seeded from course timeline defaults
- [ ] Instructor override for assignment-specific concept selections
- [ ] Canvas ZIP upload endpoint with size + type validation
- [ ] Non-Canvas or unrecognized ZIPs rejected before queueing
- [ ] ZIP path traversal protection before any extraction
- [ ] ZIP extraction in RAM or ephemeral temp directory only — never to persistent storage
- [ ] Canvas filename parser maps files to Canvas-provided identifiers
- [ ] Unmatched filename + malformed archive reporting in staff UI
- [ ] Transient official-run record created: assignment link, uploader, timestamps,
  file counts only — no student code, no submission content

**Exit criteria:**
Instructor signs in with `@uvu.edu`. Non-UVU login is rejected. Instructor creates
an assignment via wizard or raw JSON import, confirms Concepts Covered, downloads
the resulting `config.json`, uploads a Canvas ZIP, and the system parses the archive
into a transient official run without storing student code as persistent records.

---

## Sprint 2 — Grading Pipeline + Azure OpenAI + Kata Hardening
### June 4 – June 17 (2 weeks, full team)

**Goal:** The system grades an official run and a sandbox upload end to end using
ephemeral files, Kata-isolated Piston execution, AST concept enforcement, and
Azure OpenAI feedback generation.

> **Important:** Spend the first 2 days of Sprint 2 validating Azure OpenAI
> prompt output against sample submissions before wiring into the Celery chain.
> Confirm ZDR is active on the Azure deployment before any student data is sent.

**Deliverables:**

- [ ] AST checker enforces `Concepts Covered` progressive whitelist before execution
- [ ] AST checker detects future-concept usage and records warnings per result
- [ ] Security-sensitive AST findings can hard-block execution when configured
- [ ] Allowed concepts context injected into Azure OpenAI prompt
- [ ] Kata Containers hardening validated:
  - network disabled inside each execution VM
  - memory limit 256MB enforced
  - 10-second timeout kills entire VM (not just process)
  - non-root user inside VM
  - VM destroyed immediately after execution
- [ ] Piston integration via `httpx` async POST to `/api/v2/execute`
- [ ] pytest execution via Piston — student code + test file
- [ ] pytest output parser — structured pass/fail per test with stdout/stderr
- [ ] `python_submitty_utils` output normalization on pytest results
- [ ] Minimal test artifact management:
  - upload/edit pytest files per assignment
  - link each test to one primary rubric criterion
  - store student-visible description per test
  - upload and validate model solution inside Piston
- [ ] Azure OpenAI integration:
  - rubric-context + allowed-concepts prompting
  - hallucination guard: test result is ground truth, LLM explains only
  - prompt validated against sample submissions before chain integration
- [ ] Azure token usage logged to `run_summaries` as non-sensitive metadata
- [ ] Celery grading chain: AST → Piston (Kata) → Azure OpenAI
  - supports both official runs and sandbox runs
  - worker concurrency aligned to Piston container parallelism
- [ ] Run status endpoint: `GET /runs/{id}/status` from Redis
- [ ] Live status polling in staff and student views (2-second interval)
- [ ] Failed jobs retry up to 3 times with backoff
- [ ] Timeout marks `failed:timeout`, frees worker immediately
- [ ] Cleanup destroys: extracted student files, generated code artifacts,
  temporary feedback files after each official or sandbox run

**Exit criteria:**
Official batch covers: 1 future-concept warning, 1 hard-block, 1 timeout,
1 correct, 1 broken. Hard-block files do not execute. Warning cases execute and
surface warnings. System produces structured results, generates HTML feedback,
returns export package, and destroys all temporary student artifacts after the
request concludes. Separately: student uploads code in sandbox, sees projected
feedback, artifacts destroyed on session exit.

---

## Sprint 3 — Student Sandbox + Batch UX + Export
### June 18 – June 24 (1 week, full team)

**Goal:** Student sandbox works end to end. Staff can monitor runs, inspect
results, and download CSV + HTML feedback ZIP. Export is clean and ephemeral.

**Student sandbox deliverables:**
- [ ] Student course and assignment selection UI
- [ ] Student upload flow for supported file formats
- [ ] Sandbox rate limiter: 5 uploads per hour per authenticated student identity
- [ ] On-screen projected score view
- [ ] On-screen projected feedback view with warnings and test summaries
- [ ] Zero-retention messaging — students explicitly informed results are not saved
- [ ] Session-exit and completion cleanup for sandbox results
- [ ] Student route isolation from staff pages and export flows

**Instructor batch UX deliverables:**
- [ ] Official run list: assignment, uploader, start/end time, aggregate status
- [ ] In-session run detail: processing counts, per-student pass/fail,
  warning and hard-block summaries, unmatched filename failures
- [ ] Per-student HTML feedback preview before export
- [ ] Filter by: success, warning, hard-block, timeout, parse failure
- [ ] MOSS report URL surfaced prominently with explicit instructor save warning
- [ ] Warning displayed: detailed official results destroyed after export

**Export packaging deliverables:**
- [ ] CSV export for Canvas-compatible grades
- [ ] HTML feedback renderer — individual student files
- [ ] Master ZIP builder — all student HTML files in one archive
- [ ] Download: CSV + feedback ZIP in one instructor workflow
- [ ] Export naming: assignment identifier + run timestamp
- [ ] Export fails safely with actionable errors if packaging is incomplete
- [ ] Docs note: Canvas grade import assumed, bulk feedback upload is future research

**Exit criteria:**
Student signs in, selects assignment, uploads code, sees projected feedback,
loses access on session exit. Instructor runs official batch, monitors progress,
previews one student result, downloads CSV + HTML ZIP, verifies no student files
remain on server after completion.

---

## Sprint 4 — Integration Testing + FERPA/Compliance Hardening
### June 25 – June 30 (1 week)

**Goal:** Validate the full M1 workflow under realistic conditions and verify
zero-retention guarantees. Not a feature sprint — slip from Sprint 3 absorbs here.

**Activities:**
- [ ] End-to-end official-run test: 30–50 realistic submissions
- [ ] End-to-end student sandbox test: selection, upload, feedback, cleanup
- [ ] Validate OAuth: `@uvu.edu` succeeds, non-UVU rejected
- [ ] Validate role access: admin/instructor/IA/student routes all respect checks
- [ ] Validate Kata isolation: network access from inside execution blocked
- [ ] Validate ZIP path traversal: malicious ZIP rejected before extraction
- [ ] Validate hard-block: configured findings stop execution
- [ ] Validate timeout: `while True: pass` frees worker in < 15s
- [ ] Validate cleanup:
  - extracted official files deleted after request completion
  - sandbox artifacts deleted after session exit
  - temporary HTML feedback files deleted after packaging
  - no student code in persistent storage
- [ ] Validate MOSS: uses only ephemeral files, no local copies retained
- [ ] Confirm Azure ZDR is active — verify in Azure portal, document proof
- [ ] Export validation: CSV totals match rubric config and pytest results
- [ ] Smoke test on Railway production deployment
- [ ] `launchd` / systemd service files for all processes on Dell T2
- [ ] README updated with deployment and operating notes
- [ ] Demo walkthrough recorded — full workflow in under 5 minutes
- [ ] Tag `v0.1.0-alpha` on repo
- [ ] Fix bugs surfaced during testing (no new features)

**Exit criteria (M1 done):**
Teammate unfamiliar with codebase can complete without assistance:
sign in → create/open assignment → configure via wizard or JSON → confirm
Concepts Covered → upload Canvas ZIP → monitor grading → download CSV + ZIP →
verify no student files remain. Student sandbox path also completes cleanly.
Demo video covers the complete happy path.

---

## Tech Stack Reference

### Full Stack

| Layer | Technology | Version | Role |
|-------|------------|---------|------|
| Frontend | Next.js | 14.x (App Router) | Staff dashboard + student sandbox UI |
| UI language | TypeScript | 5.x | Type safety across frontend |
| Auth | NextAuth.js | 5.x | Microsoft OAuth + `@uvu.edu` restriction |
| Backend | FastAPI | 0.110.x | API, business logic, prompt engine |
| Backend language | Python | 3.11+ | Grading pipeline, AST checks, export |
| Task queue | Celery | 5.3.x | Async official + sandbox grading jobs |
| Message broker | Redis | 7.x | Celery broker + transient job state |
| Database | PostgreSQL | 16.x | Non-sensitive metadata only |
| ORM | SQLAlchemy | 2.x | DB access from FastAPI |
| Migrations | Alembic | 1.13.x | Schema versioning |
| Containerization | Docker + Compose | 25.x | Dev environment + Piston service |
| AI inference | Azure OpenAI API | current approved | Feedback generation (ZDR required) |
| Plagiarism | mosspy | current | Optional MOSS submission, ephemeral only |
| Grade export | openpyxl + zipfile | standard | CSV + HTML feedback ZIP |
| Code highlighting | Prism.js | 1.29.x | Result preview in staff + student views |

### Grading Pipeline

| Component | Technology | Role |
|-----------|------------|------|
| Static analysis | Python `ast` (stdlib) | Concepts Covered whitelist enforcement |
| VM isolation | Kata Containers | VM-level kernel isolation per execution |
| Execution engine | Piston (self-hosted) | Sandboxed code execution, Kata runtime |
| HTTP client | httpx | FastAPI → Piston async REST |
| Test framework | pytest | Official + sandbox test execution |
| Output normalization | python_submitty_utils | Whitespace/encoding normalization |
| HTML output | Server-side templating | Per-student feedback file generation |
| Config authoring | Wizard + JSON editor | Round-trip assignment config |
| PDF/text rubric ingestion | Deferred | M2 |
| Firecracker | Deferred | M2 upgrade path for Kata Containers |

### Infrastructure

| Component | M1 Location | Note |
|-----------|-------------|------|
| PostgreSQL | Railway | Metadata only — no student submissions |
| Redis | Railway | Celery broker + transient status |
| Piston + Kata | Railway Docker | Requires `--privileged` — document for IT |
| Azure OpenAI | UVU Azure tenant | ZDR must be confirmed before student data sent |
| Next.js | Railway | Production frontend |
| FastAPI + Celery | Railway | Production API and workers |
| Dell T2 (Ubuntu) | Dev/staging | Local development and pre-production testing |

> **On-prem vs Railway:** Railway is the M1 production target per team consensus.
> The Dell T2 running Ubuntu is the dev/staging machine. On-prem production
> hosting is an open architectural discussion for M2+. The zero-retention model
> and Kata Container isolation apply equally in both environments.

---

## Open-Source Components

### Used in M1

| Component | Source | How used |
|-----------|--------|----------|
| Piston | engineer-man/piston | Self-hosted execution engine — REST API, stateless |
| Kata Containers | kata-containers/kata-containers | VM-level isolation runtime for Piston |
| python_submitty_utils | Submitty/Submitty | Output normalization, token diff |
| NextAuth.js | nextauthjs/next-auth | Microsoft OAuth + domain restriction |
| mosspy | soachishti/moss.py | Optional MOSS plagiarism wrapper |

### Architectural patterns borrowed

| Source | Pattern |
|--------|---------|
| Autolab / Tango (CMU) | Job queue architecture → Celery + Redis |
| Autolab / Tango (CMU) | Submission versioning model |
| Submitty (RPI) | config.json grading spec format |
| Submitty (RPI) | Worker isolation model → Kata/Piston hardening |

### Evaluated, deferred, or replaced

| Component | Status | Reason |
|-----------|--------|--------|
| Firecracker | M2 candidate | ~35hrs backend work vs ~4hrs for Kata — wrong tradeoff for M1 timeline |
| llama-server / local LLM | M2 candidate | Azure OpenAI with ZDR is the approved M1 path; local LLM revisited when GPU is needed |
| WeasyPrint | Not used | HTML feedback output replaces PDF entirely |
| Django | Not used | Sync-first ORM conflicts with async FastAPI pipeline |

---

## Functional Requirements

### FR-01 — Admin / Identity

| ID | Requirement | Sprint |
|----|-------------|--------|
| FR-01.1 | Admin can create, edit, and deactivate staff accounts | S1 |
| FR-01.2 | Admin can assign roles: admin, instructor, ia | S1 |
| FR-01.3 | Admin can maintain staff access by course or section | S1 |
| FR-01.4 | Student can authenticate via Microsoft OAuth with `@uvu.edu` without creating a persistent profile | S1 |

### FR-02 — Instructor / IA

| ID | Requirement | Sprint |
|----|-------------|--------|
| FR-02.1 | Instructor or IA can create assignments with name, course linkage, due date, Canvas metadata | S1 |
| FR-02.2 | Instructor or IA can use a wizard to generate valid `config.json` | S1 |
| FR-02.3 | Instructor or IA can paste or import a validated raw `config.json` | S1 |
| FR-02.4 | Instructor or IA can edit stored config and download current `config.json` | S1 |
| FR-02.5 | Instructor or IA can set or override a Concepts Covered checklist per assignment | S1 |
| FR-02.6 | Instructor or IA can upload a bulk Canvas ZIP for official grading | S1 |
| FR-02.7 | Instructor or IA can manage pytest artifacts and validate model solution inside Piston | S2 |
| FR-02.8 | Instructor or IA can monitor official-run status and inspect in-session results | S3 |
| FR-02.9 | Instructor or IA can optionally run MOSS for an official run and review the returned URL | S3 |
| FR-02.10 | Instructor or IA can download a grade CSV and a master ZIP of per-student HTML feedback | S3 |

### FR-03 — Student Sandbox

| ID | Requirement | Sprint |
|----|-------------|--------|
| FR-03.1 | Student can sign in via Microsoft OAuth with `@uvu.edu` | S1 |
| FR-03.2 | Student can select a course and assignment for sandbox use | S3 |
| FR-03.3 | Student can upload code for projected grading | S3 |
| FR-03.4 | Student can view projected score, warnings, and feedback on screen | S3 |
| FR-03.5 | Student projected results are destroyed on completion or session exit | S3 |
| FR-03.6 | Student cannot access staff workflow pages or export artifacts | S3 |
| FR-03.7 | Student sandbox uploads are rate-limited to 5 per hour per identity | S3 |

### FR-04 — Ephemeral Official Processing

| ID | Requirement | Sprint |
|----|-------------|--------|
| FR-04.1 | System parses Canvas uploads into a transient official run | S1 |
| FR-04.2 | System extracts ZIP only into RAM or ephemeral temp directory | S1 |
| FR-04.3 | System rejects ZIP path traversal attempts before extraction | S1 |
| FR-04.4 | System does not create persistent student submission records | S1 |
| FR-04.5 | System runs AST concept checks before execution | S2 |
| FR-04.6 | System executes pytest via Piston (Kata runtime) with resource limits | S2 |
| FR-04.7 | System sends code, test results, and allowed-concepts context to Azure OpenAI | S2 |
| FR-04.8 | System generates HTML feedback files per student using Canvas identifiers | S2 |
| FR-04.9 | System can submit ephemeral official run to MOSS via mosspy | S3 |
| FR-04.10 | System destroys student files and artifacts after each request | S2 |
| FR-04.11 | Official grading jobs run asynchronously via Celery | S2 |
| FR-04.12 | System rejects malformed or non-Canvas ZIPs before queueing | S1 |
| FR-04.13 | System logs Azure token usage as non-sensitive metadata | S2 |

---

## Non-Functional Requirements

### Performance

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-P1 | ZIP upload acceptance | < 2s for files up to 50MB |
| NFR-P2 | Concurrent grading | 8 submissions simultaneously |
| NFR-P3 | 200-submission batch | < 40 min |
| NFR-P4 | Status polling | < 200ms |
| NFR-P5 | Export packaging | < 2 min for 200 submissions |
| NFR-P6 | Student sandbox latency | Fast enough to feel interactive |
| NFR-P7 | Azure token usage | Measurable per run in non-sensitive metadata |

### Security

| ID | Requirement |
|----|-------------|
| NFR-S1 | Piston executes student code with network access disabled (Kata VM level) |
| NFR-S2 | Piston memory (256MB) and timeout (10s) limits enforced at VM level via Kata |
| NFR-S3 | Kata VMs destroyed immediately after execution — no state persists |
| NFR-S4 | ZIP extraction validates all paths before any file is written |
| NFR-S5 | All app endpoints require valid session except auth entrypoints and health checks |
| NFR-S6 | OAuth callback rejects non-`@uvu.edu` accounts |
| NFR-S7 | Student artifacts stored only in ephemeral working space during runs |
| NFR-S8 | Cleanup routines remove artifacts immediately after run completion |
| NFR-S9 | MOSS integration uses only ephemeral files — no additional persistent copies |
| NFR-S10 | Sandbox rate limiting enforced by authenticated identity, not IP only |
| NFR-S11 | Piston requires `--privileged` Docker flag — documented for IT security review |

### Compliance

| ID | Requirement |
|----|-------------|
| NFR-C1 | No student submission content retained in persistent storage |
| NFR-C2 | Student code and feedback artifacts destroyed after request or session exit |
| NFR-C3 | Only non-sensitive metadata stored in PostgreSQL |
| NFR-C4 | Azure OpenAI Zero Data Retention confirmed active before any student data sent |
| NFR-C5 | Azure OpenAI usage covered under UVU's Microsoft FERPA BAA — confirmed with IT |
| NFR-C6 | MOSS results are staff-facing only — no persistent local storage of similarity data |

---

## Product Backlog

1 story point ≈ 2–4 hours focused work.
Priority: **Must** = M1 required · **Should** = M1 if capacity · **Won't** = post-M1

### Epic 1 — Environment and Infrastructure (Sprint 0)

| ID | Story | Pts | Priority | Owner |
|----|-------|-----|----------|-------|
| E1-01 | Docker Compose: postgres, redis, celery, fastapi, nextjs, piston | 2 | Must | Easton/Jaxon |
| E1-02 | FastAPI project structure with routers, schemas, services, prompt boundaries | 2 | Must | Easton/Jaxon |
| E1-03 | Next.js App Router scaffold (TypeScript) | 2 | Must | Frontend team |
| E1-04 | PostgreSQL schema + Alembic initial migration (metadata tables only) | 2 | Must | Easton/Jaxon |
| E1-05 | Celery + Redis wiring | 1 | Must | Easton/Jaxon |
| E1-06 | Piston running with Kata Containers runtime, executes Python test | 2 | Must | Easton/Jaxon |
| E1-07 | `.env.example`, README, GitHub Actions CI (lint + type check) | 2 | Must | All |
| E1-08 | Seed script: course, assignment, config.json, concept set, model solution | 1 | Must | Easton/Jaxon |

**Epic 1 total: 14 points**

---

### Epic 0 — Architecture + Design (Sprint 0, parallel track)

| ID | Story | Pts | Priority | Owner |
|----|-------|-----|----------|-------|
| E0-01 | ER diagram — all tables, relationships, cardinalities (Lucidchart) | 3 | Must | Easton/Jaxon |
| E0-02 | Class diagram — domain models, services, Celery tasks (Lucidchart) | 3 | Must | Easton/Jaxon |
| E0-03 | FastAPI router skeleton — all endpoints stubbed, typed schemas | 3 | Must | Easton/Jaxon |
| E0-04 | Prompt integration boundaries documented | 2 | Must | Easton/Jaxon |
| E0-05 | Architecture Decision Record written | 2 | Must | Easton/Jaxon |
| E0-06 | UI/UX wireframes — all staff views | 4 | Must | Frontend team |
| E0-07 | UI/UX wireframes — student sandbox view | 2 | Must | Frontend team |
| E0-08 | Component hierarchy + routing structure documented | 2 | Must | Frontend team |
| E0-09 | Tailwind config + design system tokens | 2 | Must | Frontend team |
| E0-10 | All role-based routes stubbed with placeholder pages | 2 | Must | Frontend team |

**Epic 0 total: 25 points**

---

### Epic 2 — Auth and Identity (Sprint 1)

| ID | Story | Pts | Priority |
|----|-------|-----|----------|
| E2-01 | NextAuth Microsoft OAuth provider configured | 2 | Must |
| E2-02 | Callback rejects non-`@uvu.edu` logins | 1 | Must |
| E2-03 | Role-based route protection: admin, instructor, IA, student | 3 | Must |
| E2-04 | Role-based API protection (FastAPI dependency) | 2 | Must |
| E2-05 | Admin manages staff roles and course access | 2 | Must |
| E2-06 | Student sandbox sign-in path — no persistent student profile | 2 | Must |

**Epic 2 total: 12 points**

---

### Epic 3 — Assignment and Config Setup (Sprint 1)

| ID | Story | Pts | Priority |
|----|-------|-----|----------|
| E3-01 | Assignment creation form with course linkage and Canvas metadata | 2 | Must |
| E3-02 | Config wizard for core assignment/rubric/config fields | 3 | Must |
| E3-03 | Wizard generates valid `config.json` | 2 | Must |
| E3-04 | Validated raw `config.json` paste/import UI | 3 | Must |
| E3-05 | Stored config editor renders editable fields from JSON | 3 | Must |
| E3-06 | Current `config.json` downloadable | 1 | Must |
| E3-07 | Concepts Covered checklist seeded from course defaults | 3 | Must |

**Epic 3 total: 17 points**

---

### Epic 4 — Ephemeral Submission Ingestion (Sprint 1)

| ID | Story | Pts | Priority |
|----|-------|-----|----------|
| E4-01 | Canvas ZIP upload endpoint with size + type validation | 2 | Must |
| E4-02 | Reject malformed or non-Canvas ZIPs before queueing | 2 | Must |
| E4-03 | ZIP path traversal protection | 2 | Must |
| E4-04 | Ephemeral extraction in RAM or temp directory only | 2 | Must |
| E4-05 | Filename parser for Canvas uploads using Canvas identifiers | 2 | Must |
| E4-06 | Unmatched filename / malformed archive reporting | 2 | Must |
| E4-07 | Transient official-run metadata record — no persistent student submissions | 1 | Must |

**Epic 4 total: 13 points**

---

### Epic 5 — Grading Pipeline and AI Enrichment (Sprint 2)

| ID | Story | Pts | Priority |
|----|-------|-----|----------|
| E5-01 | AST checker for Concepts Covered whitelist enforcement | 4 | Must |
| E5-02 | Warning vs hard-block concept/security handling | 2 | Must |
| E5-03 | Piston integration via httpx with Kata runtime confirmed | 4 | Must |
| E5-04 | pytest execution + output parsing + normalization | 4 | Must |
| E5-05 | Minimal pytest artifact management per assignment | 3 | Must |
| E5-06 | Link tests to rubric criteria + student-visible descriptions | 2 | Must |
| E5-07 | Model solution validation runs inside Piston | 1 | Must |
| E5-08 | Azure OpenAI integration: concept-context prompting + hallucination guard | 4 | Must |
| E5-09 | Celery grading chain: official and sandbox runs | 3 | Must |
| E5-10 | Timeout, retry, and cleanup guarantees | 2 | Must |
| E5-11 | Azure token usage logged in run_summaries | 2 | Must |
| E5-12 | Celery worker concurrency aligned to Piston limits | 1 | Must |
| E5-13 | Optional MOSS integration via mosspy (ephemeral files only) | 3 | Should |

**Epic 5 total: 35 points**

---

### Epic 6 — Student Sandbox (Sprint 3)

| ID | Story | Pts | Priority |
|----|-------|-----|----------|
| E6-01 | Student course and assignment selection UI | 2 | Must |
| E6-02 | Student upload flow for projected grading | 3 | Must |
| E6-03 | Sandbox rate limiter: 5 uploads per hour per authenticated student | 2 | Must |
| E6-04 | On-screen projected score and feedback view | 3 | Must |
| E6-05 | Zero-retention messaging visible to students | 2 | Must |
| E6-06 | Session-exit and completion cleanup for sandbox results | 2 | Must |
| E6-07 | Student route isolation from staff pages and export flows | 2 | Must |

**Epic 6 total: 16 points**

---

### Epic 7 — Instructor Batch Run UX (Sprint 3)

| ID | Story | Pts | Priority |
|----|-------|-----|----------|
| E7-01 | Official run list with aggregate status and timestamps | 2 | Must |
| E7-02 | In-session run detail view with counts, warnings, failures | 2 | Must |
| E7-03 | Live polling for per-run status | 1 | Must |
| E7-04 | Per-student HTML preview before export | 2 | Must |
| E7-05 | Filter by success, warning, hard-block, timeout, parse failure | 1 | Should |
| E7-06 | MOSS report URL surfaced prominently with save warning | 1 | Must |

**Epic 7 total: 9 points**

---

### Epic 8 — Export Packaging (Sprint 3)

| ID | Story | Pts | Priority |
|----|-------|-----|----------|
| E8-01 | CSV export for Canvas-compatible grades | 2 | Must |
| E8-02 | Individual student HTML feedback renderer | 2 | Must |
| E8-03 | Master ZIP builder for HTML feedback package | 2 | Must |
| E8-04 | Instructor download workflow with stable naming + actionable errors | 1 | Must |
| E8-05 | Graceful failure for malformed or incomplete packaging | 2 | Must |
| E8-06 | Docs note: Canvas grade import assumed, feedback upload is future research | 1 | Must |

**Epic 8 total: 10 points**

---

## Backlog Summary

| Epic | Name | M1 Points | Sprint | Owner |
|------|------|-----------|--------|-------|
| E0 | Architecture + Design | 25 | S0 | Parallel tracks |
| E1 | Environment + Infrastructure | 14 | S0 | Easton/Jaxon + Frontend |
| E2 | Auth and Identity | 12 | S1 | All |
| E3 | Assignment and Config Setup | 17 | S1 | All |
| E4 | Ephemeral Submission Ingestion | 13 | S1 | All |
| E5 | Grading Pipeline and AI Enrichment | 35 | S2 | All |
| E6 | Student Sandbox | 16 | S3 | All |
| E7 | Instructor Batch Run UX | 9 | S3 | All |
| E8 | Export Packaging | 10 | S3 | All |
| **Total** | | **151 points** | | |

### Capacity reality check

```
Conservative (35 hrs/week, 8 weeks, 3 hrs/point): ~93 points
Optimistic   (65 hrs/week, 8 weeks, 3 hrs/point): ~173 points
With Sprint 4 buffer absorbed:                     ~185–195 points realistic
```

151 points sits comfortably inside the realistic range for a 5-developer team.
The Sprint 0 parallel track front-loads architectural decisions, reducing rework
risk in Sprints 1–3. Protect Epics 1–5 above all else. Cut E5-13 (MOSS) and
E7-05 (filtering polish) before cutting zero-retention guarantees.

---

## Definition of Done

A story is complete when:

- [ ] Feature works end to end, not just in isolation
- [ ] Reviewed by at least one teammate (PR required)
- [ ] No TypeScript or Python type errors on CI
- [ ] Ruff and ESLint pass with no warnings
- [ ] At least one unit or integration test covers the happy path
- [ ] Edge cases handled: bad input, malformed ZIP, non-UVU login, timeout, cleanup failure
- [ ] No hardcoded secrets or environment-specific values
- [ ] Docs updated if setup or behavior changed
- [ ] Zero-retention: no story that touches student data is done until cleanup is verified

---

## Hard Scope Boundaries — M1

Explicitly out of scope. Do not pull in under deadline pressure:

- Canvas LTI or grade passback API integration
- Automated bulk feedback upload into Canvas
- Persistent student submission history or resubmission timelines
- Downloadable student sandbox artifacts
- LLM-assisted PDF/text rubric conversion
- AI-assisted test generation
- PDF feedback generation
- Multi-language support beyond Python
- Analytics or class-wide reporting
- Official university SSO beyond Microsoft OAuth + `@uvu.edu` restriction
- Firecracker (M2 upgrade path for Kata Containers)
- Local LLM inference (M2 — NVIDIA GPU on prod machine available when needed)

---

## Action Items

| Item | Owner | Due |
|------|-------|-----|
| Rubric PDF ingestion — extract 4 assignment rubrics via pdfplumber, import to config.json | TBD | Before Sprint 2 (Jun 4) |
| ER diagram + class diagram reviewed and approved by full team | Easton + Jaxon | End of Sprint 0 (May 20) |
| Wireframes reviewed and approved by Easton + Jaxon | Frontend team | End of Sprint 0 (May 20) |
