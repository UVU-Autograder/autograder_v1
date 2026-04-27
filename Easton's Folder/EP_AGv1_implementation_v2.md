# UVU_autograder_V1 — Easton's Architecture Guide & Implementation Phases

> An instructor and TA-facing autograding platform powered by a local LLM, designed for
> introductory CS courses. Submissions are graded against instructor-defined rubrics and
> constraints, with AI-generated feedback reviewed and approved by humans before release.

---

## Status

- [x] Architecture decided — local-first, no cloud inference
- [x] Stack proposal — Next.js + FastAPI + llama-server + PostgreSQL
- [x] Open-source component analysis complete (Autolab, Submitty)
- [x] Risk register drafted
- [x] Functional requirements drafted (M1)
- [ ] Config JSON schema finalized
- [ ] Product backlog written
- [ ] Repo scaffolding
- [ ] M1 build started

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Tech Stack](#tech-stack)
3. [Open-Source Components](#open-source-components)
4. [Grading Spec — config.json Schema](#grading-spec--configjson-schema)
5. [Risk Register](#risk-register)
6. [Role Definitions](#role-definitions)
7. [Functional Requirements](#functional-requirements)
8. [Milestone Roadmap](#milestone-roadmap)
9. [Open Questions](#open-questions)
10. [References](#references)

---

## Architecture Overview

### Design Philosophy

**Simplicity-first. Local-first. Human-in-the-loop.**

- No student data leaves university-controlled infrastructure
- LLM grades are always reviewed and approved by a TA or instructor before release
- Open-source components handle the heavy lifting; custom code handles the UVU-specific workflow
- FERPA compliance by design — inference runs on-premise on a local machine

### System Layers

```
Students (browser — no login in M1)
        ↓  HTTPS
   Nginx (TLS termination, rate limiting, reverse proxy)
        ↓
   Next.js — instructor/TA dashboard UI
        ↓  internal HTTP
   FastAPI — business logic, prompt engine, safety layer, audit logging
        ↓  Celery + Redis (async job queue)
   Grading pipeline:
     ├── AST constraint checker (Python ast library)
     ├── pytest test runner (autograder-sandbox and/or Piston)
     └── llama-server (local LLM — Llama 3.3 70B Q4_K_M)
        ↓
   PostgreSQL — submissions, grades, audit log, job status
```
### Hardware for our project

| Component | Hardware | Role |
|-----------|----------|------|
| Inference server | Mac Mini M3 or Mac Studio M3 Ultra, 256–512GB unified memory | llama-server, FastAPI, PostgreSQL, Redis |
| Dev machine | MacBook M2 Max, 64GB unified memory | Local development and testing |
| Network | University data center, 10GbE, static public IP | TLS termination, student access (ideal) |

> **Hardware procurement status:** Final hardware configuration is pending procurement.
> The architecture is designed to operate well across the 256–512GB memory range —
> both are viable production targets. The system scales gracefully between them:
> 256GB supports 8 concurrent grading sessions comfortably; 512GB doubles that capacity,
> enables higher-quality quantization tiers (Q8 vs Q4), and opens the option to run
> frontier-scale models (Llama 3.1 405B) for high-stakes assignments.
> See the addendum hardware memory budget analysis for full numbers.
> All resource limits and concurrency caps in this document will be tuned to match
> whichever configuration is procured.

### Hardware Scaling Reference

| Spec | 256GB (minimum viable) | 512GB (preferred) |
|------|------------------------|-------------------|
| Max concurrent grading workers | 8 | 16 |
| Recommended model | Llama 3.3 70B Q4_K_M (~40GB) | Llama 3.3 70B Q8_0 (~70GB) |
| Alternative model option | Gemma 3 27B Q4_K_M (~18GB) | Llama 3.1 405B Q3_K_M (~180GB) |
| Est. tok/s (70B) | ~15–20 | ~25 |
| 200-submission batch estimate | ~25–35 min | ~15–20 min |
| Single point of failure risk | Present — mitigated via launchd | Lower — redundancy easier to add |

### Key Architectural Decisions

**Why local LLM over GPT-4o-mini / cloud API:**
- Student code is FERPA-protected — sending it to OpenAI requires a DPA and university legal review
- Mac Mini with 256GB unified memory runs Llama 3.3 70B Q4_K_M (~40GB) comfortably within budget
- Zero per-token cost — no budget risk as class sizes scale
- No dependency on external API availability during grading runs

**Why Next.js + FastAPI over Django + Railway:**
- FastAPI's async-native design pairs cleanly with streaming LLM output
- Next.js handles the instructor/TA dashboard UI with full React component model
- Keeps the LLM pipeline in Python without pulling a full Rails/Django ORM into scope
- Railway introduces external hosting dependency, cold-start latency, and a FERPA data-transit
  risk for any student code that touches cloud infrastructure; on-prem eliminates all three

**Why Tango-inspired job queue (Celery + Redis) over synchronous grading:**
- 30 submissions submitted simultaneously must process in parallel, not sequentially
- Instructors see live status per submission as jobs complete
- Failed jobs can be retried without re-uploading
- Decouples the web request from the grading workload entirely

---

## Tech Stack

| Layer | Technology | Justification |
|-------|------------|---------------|
| Frontend | Next.js (React) | Component UI, SSR, API routes for SSO proxy |
| Backend | FastAPI (Python) | Async, OpenAI-compatible, native LLM integration |
| Inference | llama-server (llama.cpp) | Apple Silicon native, Metal acceleration, OpenAI-compatible API |
| Model | Llama 3.3 70B Q4_K_M | Best-in-class open-weight coding + reasoning |
| Job queue | Celery + Redis | Async grading jobs, retry logic, status tracking |
| Database | PostgreSQL | Relational — students, assignments, submissions, grades, audit log |
| Static analysis | Python `ast` library | Constraint checking without code execution |
| Test runner | `autograder-sandbox` (U-Michigan) or Piston | Sandboxed code execution — decision pending |
| Testing framework | `pytest` | Structured test output, easy integration with grading pipeline |
| Plagiarism | `mosspy` (MOSS wrapper) | Industry-standard similarity detection, minimal local effort |
| PDF generation | WeasyPrint | HTML-to-PDF for per-student feedback reports |
| Grade export | `openpyxl` | XLSX export for Canvas manual import |
| Canvas (M3+) | `canvasapi` Python library | Grade passback, roster sync — future builds |
| Reverse proxy | Nginx | TLS termination, rate limiting, static assets |
| Certificates | InCommon / Sectigo | University-issued TLS cert for `*.uvu.edu` — futureproofing for M3+ |

---

## Open-Source Components

### Autolab (CMU — github.com/autolab/Autolab)

**What it is:** Full course management system in Ruby on Rails with a separate grading
daemon called Tango. Not adopted wholesale (wrong language stack) but key patterns are reused.

**Reusable concepts:**

- **Tango job queue architecture** — accept grading jobs via REST, manage container pool,
  execute asynchronously, return results. Our Celery + Redis queue mirrors this pattern exactly.
  Study Tango's job schema for fields to track per grading job.
- **Assessment versioning** — every submission attempt is stored with a version number;
  instructors select which version counts for grading. Build into data model from day one
  even if M1 UI doesn't expose it.
- **Grading result schema** — Tango's results JSON structure (score, max_score, output,
  errors per test case) is a clean model for our own results format.

**What to ignore:** Rails frontend, MySQL schema, Tango daemon itself (replace with Celery).

---

### Submitty (RPI — github.com/Submitty/Submitty)

**What it is:** Full homework submission + autograding + TA grading system. PHP frontend,
Python + C++ grading core. More relevant than Autolab because the grading engine is Python.

**Reusable directly:**

- **`config.json` grading spec schema** — production-proven format for defining test cases,
  point values, resource limits. Adopted as our grading spec format (see schema section below).
- **`python_submitty_utils` package** — installable via pip. Provides file diff utilities,
  output normalization, and token comparison. Solves the whitespace/encoding false-negative
  problem without custom code.
- **Worker isolation model** — Submitty runs grading as unprivileged `submitty_daemon` user
  with no network access and OS-level limits via PAM + cgroups. More secure than Docker alone.
  Reference for the container hardening requirements below.
- **`more_autograding_examples/` directory** — real-world grading configs for Python, C++,
  Java assignments. Use as reference when writing our own test suite templates.

**What to ignore:** PHP frontend, Vagrant-based dev environment, Java-specific tooling.

---

## Grading Spec — `config.json` Schema

Adopted from Submitty's proven format with extensions for our LLM feedback layer and
constraint system. Each assignment has one `config.json` stored alongside its test files.

```json
{
  "assignment_message": "Implement bubble sort. Do not use any built-in sort functions.",
  "max_submission_size": 500000,
  "max_submissions": 20,

  "resource_limits": {
    "time_limit": 10,
    "memory_limit": 256,
    "possible_points": 100
  },

  "constraints": [
    {
      "id": "no_sorted",
      "description": "Do not use the built-in sorted() function",
      "type": "forbidden_call",
      "target": "sorted",
      "penalty": 10,
      "report_only": false
    },
    {
      "id": "no_sort_method",
      "description": "Do not use the .sort() list method",
      "type": "forbidden_attribute",
      "target": "sort",
      "penalty": 10,
      "report_only": false
    },
    {
      "id": "no_lambda_sort",
      "description": "Do not use lambda functions for sorting",
      "type": "forbidden_node",
      "target": "Lambda",
      "penalty": 5,
      "report_only": true
    },
    {
      "id": "requires_function",
      "description": "Must define a function named bubble_sort",
      "type": "required_definition",
      "target": "bubble_sort",
      "penalty": 20,
      "report_only": false
    }
  ],

  "rubric": [
    {
      "id": "correct_output",
      "title": "Correct output",
      "points": 40,
      "description": "Function returns a correctly sorted list for all test inputs"
    },
    {
      "id": "edge_cases",
      "title": "Edge case handling",
      "points": 20,
      "description": "Handles empty list, single element, and already-sorted input"
    },
    {
      "id": "code_style",
      "title": "Code style and readability",
      "points": 20,
      "description": "Meaningful variable names, appropriate comments, consistent indentation"
    },
    {
      "id": "algorithm_correctness",
      "title": "Algorithm implementation",
      "points": 20,
      "description": "Implements bubble sort algorithm correctly with nested loops"
    }
  ],

  "testcases": [
    {
      "title": "Basic sort",
      "rubric_id": "correct_output",
      "points": 20,
      "command": "pytest tests/test_basic.py -v",
      "timeout": 5,
      "display_to_student": true
    },
    {
      "title": "Edge cases",
      "rubric_id": "edge_cases",
      "points": 20,
      "command": "pytest tests/test_edge.py -v",
      "timeout": 5,
      "display_to_student": false
    }
  ]
}
```

### Constraint Types (AST-based, no execution required)

| Type | What it checks | AST node |
|------|----------------|----------|
| `forbidden_call` | Function call by name e.g. `sorted()` | `ast.Call` → `ast.Name.id` |
| `forbidden_attribute` | Method call e.g. `.sort()` | `ast.Attribute.attr` |
| `forbidden_node` | Any AST node type e.g. `Lambda` | `ast.Lambda` |
| `forbidden_import` | Import statement e.g. `import collections` | `ast.Import` / `ast.ImportFrom` |
| `required_definition` | Function or class must exist | `ast.FunctionDef.name` |

---

## Risk Register

### Security Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Malicious student code — reverse shell, fork bomb, privilege escalation | **Critical** | `--network none` at container level. Hard CPU + memory limits via cgroups. Kill entire container on timeout — not just the process inside it. Run as unprivileged non-root user. AST pre-check blocks `socket`, `subprocess`, `os.system` before execution reaches the container. |
| Student code reads other students' submissions | **Critical** | Ephemeral per-submission containers only. No shared volumes between grading jobs. Each container receives only its own submission via isolated temp directory. Container destroyed immediately after grading completes. |
| ZIP path traversal attack | **High** | Validate all member paths before any extraction. Reject any member whose resolved absolute path escapes the target directory. Use Python `zipfile` with explicit sanitization — never shell out to `unzip`. |
| Malicious content injected via rubric or constraint upload | **Medium** | Rubrics and constraints parsed as structured text/JSON only — never eval'd or exec'd. Schema validation on all uploaded config files before use. |

### Compliance Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| FERPA — student code processed externally | **Resolved by design** | All inference runs locally on the on-prem Mac Mini via llama-server. No student data transits any third-party infrastructure at any point in the pipeline. |
| Grade data released without human review | **High** | Enforced status machine: `ai_complete` → `ta_reviewed` → `approved` → `released`. No export path exists until status reaches `approved`. TA approval is a required DB field — not a UI suggestion. |
| No audit trail for grade decisions | **High** | Immutable audit log stores: AI raw output, per-criterion scores, TA override (if any), final approved grade, approving user ID, and timestamp. Append-only — no record can be edited or deleted. |

### Resource Risks — 256GB Hardware Baseline

> All memory figures assume Mac Mini M3 with 256GB unified memory.
> Limits will be revised upward when 512GB hardware becomes available.

| Risk | Severity | Mitigation |
|------|----------|------------|
| LLM + concurrent containers exhaust 256GB | **Medium** | Memory budget: Llama 3.3 70B Q4_K_M = ~40GB. OS + stack = ~12GB. 8 grading containers × 256MB = ~2GB. KV cache for 8 LLM sessions × ~7.5GB = ~60GB. Total peak: ~114GB — comfortable within 256GB. Hard cap: 8 Celery workers, 8 llama-server parallel slots. Monitor with `vm_stat` and alert at warning threshold. |
| Large submission batch causes memory spike | **Medium** | 200-submission ZIP creates 200 queued jobs. Celery concurrency cap of 8 ensures at most 8 containers run simultaneously. Remaining 192 jobs wait in Redis queue. This is correct behavior — not a bug to fix. |
| Grading throughput slower than 512GB target | **Low** | 256GB Mac Mini M3 generates ~15–20 tok/s on Llama 3.3 70B Q4_K_M. At 8 parallel slots, a 200-submission batch completes in approximately 25–35 minutes. Acceptable for batch grading — instructors do not wait at the screen. Consider Gemma 3 27B Q4_K_M (~18GB, faster) as alternative if throughput becomes a concern. |
| Single point of failure — one on-prem machine | **Medium** | Enable macOS auto-restart after power failure. Use `launchd` service files for all processes — they restart automatically on reboot. PostgreSQL data on separate volume with automated backup. Document manual recovery procedure. Evaluate second Mac Mini for M2 redundancy. |
| Infinite loop / fork bomb hangs grading worker | **High** | 10-second hard timeout enforced at Docker container level. `docker run --rm --cpus 0.5 --memory 256m`. Kill entire container after timeout — not just the pytest process. Job marked `failed:timeout`. Worker immediately freed for next queue item. |
| TEXT blob storage growth over multiple semesters | **Low** | TEXT blobs correct for M1. Plan local volume storage migration at M2. Add end-of-semester archiving job. No S3 or external storage — all data stays on-prem per FERPA posture. |

### Application Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| AI feedback contradicts actual test results | **High** | Prompt architecture enforces test result as ground truth. Prompt explicitly states the test FAILED — LLM only provides a pedagogical explanation, never re-evaluates correctness. Validate against 50 representative submissions before M1 launch. |

---

## Role Definitions

| Role | Scope | Key permissions |
|------|-------|----------------|
| **Admin** | System-wide | Create users, assign roles, view audit log, configure LLM settings |
| **Course Admin** | Course-wide | Create courses, enroll instructors/TAs, define global constraint templates |
| **Instructor** | Course section | Create assignments, define rubrics + constraints, upload submissions, review/approve grades, export grades |
| **TA** | Assigned sections | Upload submissions, review AI grades, override scores, add comments, flag for instructor — cannot release grades independently |
| **Student** | Own submissions (M1: no login) | Download report bundle via key, upload submission via key-authenticated portal |

---

## Functional Requirements

### FR-01 — Admin

- `FR-01.1` Admin can create, edit, and deactivate user accounts
- `FR-01.2` Admin can assign roles: `course_admin`, `instructor`, `ta`, `student`
- `FR-01.3` Admin can view system-wide audit log (all grade decisions, overrides, approvals)
- `FR-01.4` Admin can configure LLM endpoint, model name, and inference parameters

### FR-02 — Course Admin

- `FR-02.1` Course admin can create and configure courses
- `FR-02.2` Course admin can enroll instructors and TAs per course
- `FR-02.3` Course admin can define reusable global constraint templates
- `FR-02.4` Course admin can view aggregate grading statistics across sections

### FR-03 — Instructor

- `FR-03.1` Instructor can create assignments with name, description, and due date
- `FR-03.2` Instructor can upload a rubric document (PDF or plain text)
- `FR-03.3` Instructor can define rubric criteria with point values
- `FR-03.4` Instructor can define constraints separately from rubric criteria:
  - Forbidden function calls (e.g. `sorted()`)
  - Forbidden imports (e.g. `import collections`)
  - Forbidden AST nodes (e.g. `Lambda`)
  - Required function definitions (e.g. must define `bubble_sort`)
  - Each constraint has a penalty value and a `report_only` flag
- `FR-03.5` Instructor can upload bulk ZIP of student submissions (Canvas download format)
- `FR-03.6` Instructor can view live grading status per submission
- `FR-03.7` Instructor can review AI-generated inline comments per submission
- `FR-03.8` Instructor can override AI score per rubric criterion with justification
- `FR-03.9` Instructor can approve or reject each submission grade
- `FR-03.10` Instructor can export approved grades as CSV or XLSX
- `FR-03.11` Instructor can generate and download per-student PDF feedback reports

### FR-04 — TA

- `FR-04.1` TA can upload bulk ZIP for assigned course section
- `FR-04.2` TA can view submission list with grading status and similarity flags
- `FR-04.3` TA can review AI-generated inline comments per submission
- `FR-04.4` TA can override AI score per rubric criterion with justification
- `FR-04.5` TA can add manual comments on top of AI-generated comments
- `FR-04.6` TA can approve submission or flag for instructor review
- `FR-04.7` TA **cannot** release grades independently — instructor approval required
- `FR-04.8` TA can view constraint violation report per submission
- `FR-04.9` TA can view cross-submission similarity report (MOSS output)

### FR-05 — Grading Pipeline (system)

- `FR-05.1` System parses Canvas ZIP filename format: `lastname_studentid_assignmentname.py`
- `FR-05.2` System maps filenames to student records; flags unmatched files for manual review
- `FR-05.3` System runs AST constraint checker **before** code execution
- `FR-05.4` System executes pytest test suite in isolated container with hard resource limits:
  - Network: disabled (`--network none`)
  - CPU: 0.5 cores max (`--cpus 0.5`)
  - Memory: 256MB max (`--memory 256m`)
  - Timeout: 10 seconds (kill container — not just process)
  - User: unprivileged non-root
- `FR-05.5` System sends code + rubric criteria + test results to local LLM feedback agent
- `FR-05.6` LLM generates per-criterion comment grounded in rubric language
- `FR-05.7` LLM prompt structure ensures feedback is **consistent with** test results, never contradicts them
- `FR-05.8` System stores immutably: raw AI output, test results, constraint violations, timestamps
- `FR-05.9` Grading jobs processed asynchronously via Celery queue with Redis broker
- `FR-05.10` System displays live job status: `queued` → `running` → `complete` | `failed`
- `FR-05.11` Failed jobs can be retried without re-uploading submission
- `FR-05.12` Constraint violations are reported separately from rubric scores

### FR-06 — Student (M1 — no login)

- `FR-06.1` Instructor generates unique submission key per student per assignment
- `FR-06.2` Student receives key out-of-band (e.g. via Canvas announcement or instructor email)
- `FR-06.3` Student can download report bundle: PDF feedback + submission key via key-authenticated URL
- `FR-06.4` Student can upload submission via key-authenticated portal
- `FR-06.5` System verifies SHA-256 hash of submission on upload for integrity
- `FR-06.6` Student cannot access any other student's report or submission

---

## Milestone Roadmap

### Milestone 1 — Core grading loop (target: 6–8 weeks)

**Goal:** Instructor uploads a Canvas ZIP → LLM grades submissions → TA reviews and approves → PDF + CSV export. No student login. No Canvas API integration.

**Deliverables:**
- NextAuth.js local credential auth for admin, course admin, instructor, TA roles
- Assignment + rubric + constraint creation UI (Next.js)
- `config.json` generation from UI inputs
- Canvas ZIP upload and filename parser (FastAPI)
- AST constraint checker (Python `ast` library)
- pytest execution via autograder-sandbox (Docker, `--network none`, resource limits)
- Celery + Redis async grading queue (8 concurrent workers, 256GB budget)
- LLM feedback pipeline (llama-server, Llama 3.3 70B Q4_K_M, Metal acceleration)
- Live job status display (queued → running → complete | failed)
- TA review dashboard (submission list, detail view, score override, constraint violations)
- Instructor approval gate (required before any grade export)
- Immutable audit log (AI output vs TA decision, approver, timestamp)
- PDF report generation per student (WeasyPrint)
- CSV / XLSX grade export (openpyxl)

> **M1 auth note:** Local credentials only in M1. University SSO (Azure AD / Canvas OIDC)
> added in M3 once IT coordination is complete.

---

### Milestone 2 — Student report keys + sandbox hardening (target: 4–6 weeks post-M1)

**Goal:** Students receive and download graded feedback via key. Execution sandbox hardened to production standards. MOSS plagiarism detection integrated.

**Deliverables:**
- Submission key generation and management
- Key-authenticated student portal (no login required)
- SHA-256 submission integrity verification on upload
- Container hardening finalized: `--network none`, cgroups, non-root user, ephemeral lifecycle
- Execution engine final decision: Piston vs autograder-sandbox — implement chosen option
- MOSS plagiarism integration (`mosspy`)
- Similarity report in TA dashboard
- Local volume storage for submission files (replaces TEXT blobs, stays on-prem)
- Automated PostgreSQL backup to external volume
- End-of-semester archiving job
- `launchd` service files for all processes (auto-restart on reboot)

> **Storage note:** No S3 or external cloud storage. All submission data remains on-prem
> per FERPA posture. Local volume on the Mac Mini or a directly attached drive.

---

### Milestone 3 — Canvas integration + SSO (target: 4–6 weeks post-M2)

**Goal:** Grades flow back to Canvas. University SSO replaces local credentials. InCommon TLS cert deployed.

**Deliverables:**
- Feasibility study: LTI 1.3 Assignment and Grade Services vs CSV/XLSX upload for grade passback
- `canvasapi` grade passback to Canvas gradebook
- Canvas course + student roster sync
- Assignment sync from Canvas course shell
- University SSO via NextAuth.js (Azure AD or Canvas OIDC)
- Role claims mapped from SSO identity token
- InCommon / Sectigo TLS cert for `*.uvu.edu` (coordinate with university IT)
- Nginx production config with HSTS + CSP headers
- University data center static IP + DNS entry (coordinate with IT)
- Student login via university SSO (subject to university policy)

> **Lead time warning:** Canvas admin + university IT coordination typically takes 4–6 weeks.
> Begin those conversations at M2 kickoff — do not wait until M3 sprint starts.

---

### Milestone 4 — Analytics, scale + LLM tuning (target: post-launch, based on real usage)

**Goal:** Surface class-wide patterns. Tune LLM on UVU curriculum. Scale to multi-course. 

**Deliverables:**
- Common error pattern detection across submissions
- Class-wide misconception heatmap per assignment
- Per-student progress tracking over semester
- TA grading consistency metrics
- Assignment difficulty scoring derived from submission data
- RAG pipeline on UVU course materials (syllabi, lecture notes, past assignments)
- Fine-tune on TA-approved feedback history from M1–M3
- Benchmark Gemma 3 27B vs Llama 3.3 70B on real UVU assignment data
- Multi-course support across departments
- AI content detection plugin (open-source or Turnitin)
- HTML/CSS assignment grading support (beyond Python)
- Mobile-responsive TA dashboard

---

## Open Questions

- [ ] **Execution engine:** Piston (API, 100+ languages, easier horizontal scaling) vs autograder-sandbox (Python library, tighter Docker lifecycle control). Decision required before M1 sprint 2.
- [ ] **Canvas grade passback feasibility:** LTI 1.3 AGS vs manual CSV/XLSX upload. Requires Canvas admin + IT coordination. Initiate at M2 kickoff.
- [ ] **Constraint penalty model:** Should violations deduct from the final score automatically, or flag for TA review only? Should be instructor-configurable per assignment. Design needed before M1 FR freeze.
- [ ] **LLM hallucination guard:** Prompt must receive actual pytest output as ground truth. LLM explains failures — it does not re-evaluate correctness. Requires 50-submission validation set before M1 launch.
- [ ] **Student key distribution in M1:** Keys delivered via Canvas announcement, instructor email, or manual distribution before Canvas integration exists. Process needs to be defined before M1 go-live.
- [ ] **Multi-section TA access:** If multiple TAs grade different sections of the same course, can they see each other's grades? Access control model needs design decision-- authH vs AuthZ.
- [ ] **FERPA sign-off:** University legal review of architecture required before go-live. (probably, IDK)
- [ ] **512GB hardware timeline:** What is the current lead time estimate from procurement? This directly affects M4 planning and the LLM upgrade path.

---

## References

### Open-Source Projects

- [Autolab (CMU)](https://github.com/autolab/Autolab) — Tango job queue architecture, assessment versioning pattern
- [Submitty (RPI)](https://github.com/Submitty/Submitty) — `config.json` grading spec, `python_submitty_utils`, worker isolation model
- [autograder-sandbox (U-Michigan)](https://github.com/eecs-autograder/autograder-sandbox) — Docker-based sandboxed Python execution
- [Piston](https://github.com/engineer-man/piston) — Stateless multi-language code execution API
- [mosspy](https://github.com/soachishti/moss.py) — Python wrapper for Stanford MOSS plagiarism detection
- [llama.cpp](https://github.com/ggerganov/llama.cpp) — Local LLM inference, Apple Silicon Metal acceleration

### Academic Papers

- Liu et al. (2024). *A Fast and Accurate Machine Learning Autograder for the Breakout Assignment.* SIGCSE 2024. — Human-in-the-loop AI grading: 44% time reduction, 6% accuracy improvement.
- Alkafaween et al. (2024). *Automating Autograding: LLMs as Test Suite Generators for Introductory Programming.* — LLM-generated test suites match instructor quality on CS1 problems.

### Infrastructure

- [llama.cpp Metal build guide](https://github.com/ggerganov/llama.cpp#metal-build) — Apple Silicon inference setup
- [InCommon certificate service](https://incommon.org/certificates) — University TLS certificates via Sectigo
- [Canvas LTI 1.3 developer docs](https://developerdocs.instructure.com) — LTI launch flow and Developer Key configuration
- [NextAuth.js](https://next-auth.js.org) — SSO integration (Azure AD, Canvas OIDC, Google Workspace)

### Internal Notes

- Refer to addendum file also found in this folder.