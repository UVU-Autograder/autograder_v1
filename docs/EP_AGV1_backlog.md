# Preserved reference doc: copied from `implementation_folder/Implementation_ideas/EP_AGV1_backlog.md`.
# This file is intentionally preserved for planning context. When it conflicts with the Jaxon docs in this folder, the Jaxon docs remain the canonical M1 implementation source of truth.

# UVU_autograder_V2 — Easton's Architecture Guide & Implementation Phases

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

# UVU_autograder_V1 — Internal Notes Addendum

> This addendum captures research, design rationale, and reference material developed
> during the architecture discussion phase. It is intended to be appended to or linked
> from `EP_AGv1_implementation_v3.md` so that context does not need to be reconstructed
> from conversation history.

---

## Table of Contents

1. [Stack Rationale — Full Argument](#stack-rationale--full-argument)
2. [Hardware Memory Budget Analysis](#hardware-memory-budget-analysis)
3. [LLM Selection — Model Comparison Notes](#llm-selection--model-comparison-notes)
4. [Quantization Reference](#quantization-reference)
5. [Local Inference Architecture Notes](#local-inference-architecture-notes)
6. [Open-Source Autograder Research](#open-source-autograder-research)
7. [Autograder Market Complaint Analysis](#autograder-market-complaint-analysis)
8. [Academic Paper Notes — Breakout Autograder (SIGCSE 2024)](#academic-paper-notes--breakout-autograder-sigcse-2024)
9. [TLS + InCommon Notes](#tls--incommon-notes)
10. [LTI 1.3 + Canvas Integration Notes](#lti-13--canvas-integration-notes)
11. [Security Architecture Notes](#security-architecture-notes)
12. [MCP Protocol Reference](#mcp-protocol-reference)

---

## Stack Rationale — Full Argument

### Why Next.js + FastAPI over Django + Railway

The team evaluated two stack proposals. The following is the full argument for the
Next.js + FastAPI + local LLM approach over Django + Railway + GPT-4o-mini.

**FERPA compliance:**
Sending student submission code to any third-party API (OpenAI, Anthropic, or otherwise)
requires a university-signed Data Processing Agreement and legal review. This is not a
minor administrative step — it can take months and may not be approved. The local inference
architecture eliminates this risk entirely by design. No student data transits any
infrastructure the university does not control.

**Cost at scale:**
GPT-4o-mini pricing at ~$0.15/1M input tokens appears cheap in isolation. At 200 students
× 10 assignments × 5 attempts × ~3,000 tokens per grading call = ~30M tokens per semester.
That is approximately $4.50 per semester at current pricing — but that figure does not
account for output tokens, retries, or feedback verbosity. More importantly, as the tool
scales to multiple courses and departments, cost scales linearly with no ceiling. Local
inference has zero marginal cost per token after hardware acquisition.

**Railway-specific concerns:**
- Introduces an external hosting dependency — if Railway has downtime during a grading run,
  the system is unavailable
- Cold start latency on Railway's hobby/pro tier adds 2–10 seconds per request, which
  compounds badly under concurrent load at submission deadlines
- Any student code that passes through Railway's infrastructure — even transiently —
  creates a data residency question that FERPA requires answering
- Railway's pricing model scales with compute usage; a large grading batch triggers
  unpredictable cost spikes

**FastAPI vs Django:**
Django is a full-stack MVC framework designed around synchronous request handling and
an integrated ORM. It is well-suited for traditional web apps but introduces friction for
an LLM pipeline that requires async-native processing, streaming responses, and tight
integration with Python ML tooling. FastAPI is async by default, generates OpenAPI docs
automatically, and its dependency injection system maps cleanly to the per-request
context (student, assignment, submission) the grading pipeline needs. The Django admin
panel advantage is real but replicable with a straightforward Next.js dashboard.

**Summary table:**

| Criterion | Next.js + FastAPI + local LLM | Django + Railway + GPT-4o-mini |
|-----------|-------------------------------|-------------------------------|
| FERPA compliance | Resolved by design | Requires DPA + legal review |
| Cost (200 students, 10 assignments) | ~$0 marginal | ~$4.50–$50/semester, scales linearly |
| Latency | None — local inference | Cold start + API round trip |
| Availability dependency | None | Railway uptime + OpenAI uptime |
| Data sovereignty | Full — stays on-prem | Partial — transits Railway + OpenAI |
| Async performance | Native (FastAPI) | Requires ASGI config (Django) |
| LLM upgrade path | Swap model file locally | API version migration |

---

## Hardware Memory Budget Analysis

### Memory Allocation — 256GB Baseline

```
Component                          Memory usage
─────────────────────────────────────────────────
Llama 3.3 70B Q4_K_M weights       ~40 GB
macOS + system processes            ~12 GB
FastAPI + Next.js + Redis + Nginx   ~4 GB
PostgreSQL                          ~2 GB
8 × grading containers × 256MB     ~2 GB
8 × LLM KV cache sessions × 7.5GB  ~60 GB (peak, all slots active)
─────────────────────────────────────────────────
Total peak estimate                 ~120 GB
Available headroom (256GB)          ~136 GB
```

At 256GB, peak concurrent load (8 grading workers + 8 LLM sessions simultaneously) uses
approximately 120GB, leaving ~136GB headroom. This is comfortable for M1 and M2 workloads.

### Memory Allocation — 512GB

```
Component                          Memory usage
─────────────────────────────────────────────────
Llama 3.3 70B Q8_0 weights          ~70 GB  (higher quality tier)
macOS + system processes            ~12 GB
FastAPI + Next.js + Redis + Nginx   ~4 GB
PostgreSQL                          ~2 GB
16 × grading containers × 256MB    ~4 GB
16 × LLM KV cache sessions × 7.5GB ~120 GB (peak)
─────────────────────────────────────────────────
Total peak estimate                 ~212 GB
Available headroom (512GB)          ~300 GB
```

At 512GB, the system can comfortably run at double the concurrency, step up to Q8 weights
for higher output quality, and still have headroom to run Llama 3.1 405B Q3_K_M (~180GB)
for high-stakes assignments where maximum model quality is warranted.

### Throughput Estimates by Hardware

| Hardware | Model | Quantization | Est. tok/s | 200-submission batch time |
|----------|-------|--------------|-----------|--------------------------|
| Mac Mini M3, 256GB | Llama 3.3 70B | Q4_K_M | ~15–20 | ~25–35 min |
| Mac Studio M3 Ultra, 512GB | Llama 3.3 70B | Q4_K_M | ~25 | ~15–20 min |
| Mac Studio M3 Ultra, 512GB | Llama 3.3 70B | Q8_0 | ~18 | ~20–28 min |
| Mac Studio M3 Ultra, 512GB | Llama 3.1 405B | Q3_K_M | ~4–5 | ~90–120 min |

All estimates assume 8 parallel Celery workers, 500-token average feedback response,
and Metal GPU offloading of all layers (`-ngl 99`).

### Key formula

```
Model size (GB) ≈ (parameters × bits per weight) ÷ 8,000,000,000

Examples:
  70B × 4.5 bits (Q4_K_M)  ÷ 8B = ~39 GB
  70B × 8 bits (Q8_0)      ÷ 8B = ~70 GB
  405B × 3.5 bits (Q3_K_M) ÷ 8B = ~177 GB
```

---

## LLM Selection — Model Comparison Notes

### Evaluated Models for Intro CS Grading

Three model families were evaluated for Python and HTML intro coursework grading:

**Llama 3.3 70B (Meta — recommended)**
- HumanEval: 88.4% (pass@1)
- Strong reasoning and instruction following (92.1% IFEval)
- 128K context window — can hold large codebases + rubric + history in one session
- Apache 2.0 compatible for academic deployment
- Largest community support — most cited in current academic literature
- Best choice for a production deployment where quality and maintainability matter

**Gemma 3 27B (Google)**
- HumanEval: ~87.8% — near-identical to Llama 70B on basic coding tasks
- Smaller footprint (~18GB Q4_K_M) — faster token generation on constrained hardware
- Stronger safety fine-tuning for educational contexts
- University may have preference for Gemma due to prior discussions
- Viable alternative if hardware procurement remains at 256GB and throughput is a concern
- Benchmark both on real UVU assignment samples before committing

**Qwen 2.5 72B (Alibaba)**
- Consistently outperforms both on pure coding benchmarks across the 70B size class
- 128K context, supports 29 programming languages
- Worth evaluating for M4 when HTML/CSS support is added
- Less community adoption in education research than Llama

### Decision for M1

Use **Llama 3.3 70B Q4_K_M** as the default. It is the most defensible choice academically,
has the largest support community for troubleshooting, and performs well on intro CS tasks.
Gemma 3 27B should be benchmarked in parallel on a sample of 50 representative UVU
submissions during M1 development. If throughput becomes a blocker on 256GB hardware,
Gemma is the natural fallback without a significant quality penalty on intro-level work.

---

## Quantization Reference

Quantization reduces the number of bits used to store each model weight, trading precision
for smaller file size and faster inference. Apple Silicon's unified memory architecture
makes this particularly effective — the model loads into the same memory pool used by the
GPU and Neural Engine with no PCIe transfer overhead.

### Quantization Tiers

| Format | Bits/weight | 70B size | Quality loss | Use case |
|--------|-------------|----------|--------------|----------|
| fp32 | 32 | ~280 GB | None | Training only |
| fp16 / bf16 | 16 | ~140 GB | Negligible | Fine-tuning, HPC |
| Q8_0 | 8 | ~70 GB | Barely perceptible | High-quality local |
| Q6_K | 6 | ~52 GB | Very small | Quality-conscious |
| **Q4_K_M** | ~4.5 | **~40 GB** | **Small** | **Default — sweet spot** |
| Q3_K_M | ~3.5 | ~30 GB | Moderate | Memory-constrained only |
| Q2_K | ~2.5 | ~22 GB | Significant | Last resort |

### Filename convention (GGUF format)

`Q4_K_M` breaks down as:
- `Q4` — 4-bit quantization base
- `_K` — k-quant method: applies different precision per layer based on sensitivity
- `_M` — medium variant (best quality/size balance within the k-quant family)

Always prefer `_K` variants over plain `Q4_0` — the quality recovery is significant at
negligible size cost. Within k-quants, `_M` is almost always the right choice.

### Metal and Apple Silicon context

Metal is Apple's low-level GPU programming API — equivalent to CUDA on NVIDIA hardware.
In llama.cpp, `-ngl 99` offloads all transformer layers to the GPU via Metal, using the
full unified memory pool. On Apple Silicon there is no PCIe transfer bottleneck between
CPU and GPU memory — the model weights sit in the shared pool and both access them directly.

The tokenizer (text → token IDs) and detokenizer (token IDs → text) run on CPU and are
not Metal-accelerated. They are also trivially fast relative to the transformer layer math.
Metal acceleration applies to the transformer forward pass — the bulk of inference compute.

---

## Local Inference Architecture Notes

### llama-server configuration for this project

```bash
./build/bin/llama-server \
  -m ./models/llama-3.3-70b-instruct-q4_k_m.gguf \
  --host 127.0.0.1 \       # bind to localhost only — not exposed externally
  --port 8080 \
  -ngl 99 \                # offload all layers to Metal GPU
  -c 8192 \                # context window per session
  --parallel 8 \           # concurrent generation slots (matches Celery worker count)
  --cont-batching          # accept new requests mid-generation — critical for throughput
```

### FastAPI → llama-server integration

llama-server exposes an OpenAI-compatible `/v1/chat/completions` endpoint. FastAPI calls
it using the standard `openai` Python client with `base_url` pointed at localhost.
This means the LLM integration code is identical to what would be used with a cloud API —
swapping models in the future requires only changing the `base_url` and model name.

```python
from openai import AsyncOpenAI

llm = AsyncOpenAI(
    base_url="http://127.0.0.1:8080/v1",
    api_key="not-needed"  # llama-server does not require auth on localhost
)
```

### Cold start behavior

Unlike a web server, llama-server takes 30–60 seconds to load model weights into memory
on startup. It must run as a persistent background service — not restarted on code changes.
Use a `launchd` plist to keep it running as a system service that survives reboots.
FastAPI and Next.js restart independently without affecting the model server.

---

## Open-Source Autograder Research

### Autolab (CMU) — Key findings

- Ruby on Rails full-stack app — not directly adoptable but patterns are reusable
- **Tango** is the grading daemon: accepts jobs via REST API, manages Docker container pool,
  executes asynchronously, returns structured results. Our Celery + Redis queue replicates
  this architecture in Python.
- Assessment versioning: every submission stored with a version number, instructor picks
  which version counts. Worth building into the PostgreSQL schema from day one even if
  the M1 UI doesn't expose version selection.
- Tango job fields to model: `submission_id`, `student_id`, `assignment_id`,
  `container_image`, `time_limit`, `memory_limit`, `status`, `stdout`, `stderr`, `score`

### Submitty (RPI) — Key findings

- PHP frontend (ignore), Python + C++ grading core (directly relevant)
- `config.json` schema is production-proven across hundreds of CS courses at RPI.
  Adopted as the grading spec format for this project with constraint extensions added.
- `python_submitty_utils` pip package: file diff, output normalization, token comparison.
  Directly solves the whitespace/encoding false-negative problem without custom code.
- Worker isolation model uses PAM + cgroups + unprivileged system user (`submitty_daemon`)
  — more secure than Docker alone. Reference implementation for our container hardening.
- `more_autograding_examples/` directory contains real Python, C++, Java grading configs.
  Use as templates when writing UVU-specific test suite configurations.

### autograder-sandbox (U-Michigan)

- Python library designed specifically for academic autograding at scale
  (supports 5,000+ students per semester at Michigan)
- Docker-native, manages container lifecycle from Python code
- Tighter control than Piston for our use case since it integrates directly into FastAPI
- Primary candidate for the M1 execution engine

### Piston

- Stateless REST API for code execution, 100+ languages
- Every run starts fresh — no state leaks between submissions
- Easier to scale horizontally if the system grows beyond one machine
- Adds a separate service to manage vs autograder-sandbox which is just a Python import
- Decision between Piston and autograder-sandbox required before M1 sprint 2

---

## Autograder Market Complaint Analysis

Research across instructor forums, academic papers, and open issue trackers identified
the following recurring complaints about existing autograding tools. These directly
inform the design decisions in this project.

### Instructor complaints

**Docker setup tax:** Gradescope requires packaging a Docker container as a zip file.
Every test suite change triggers a multi-minute image rebuild. Non-DevOps instructors
hit a hard wall before they can grade a single assignment. Our architecture eliminates
this entirely — instructors define rubrics and constraints via UI; no Docker knowledge required.

**Test suite authorship burden:** Writing comprehensive test cases for each assignment
is the single largest time cost for instructors. Inadequate test coverage produces
misleading pass/fail scores that damage student trust. The LLM-based approach reads
and reasons about code semantically, reducing but not eliminating the need for test cases.

**Inconsistent grading from output string matching:** Valid student code that produces
correct output in a different format (different whitespace, different decimal precision)
fails tests. `python_submitty_utils` output normalization addresses this directly.

**Core features behind institutional pricing:** Gradescope gates code autograding, LMS
integration, and plagiarism detection behind undisclosed enterprise contracts. Our system
is open-source and self-hosted — no per-feature licensing.

### Student complaints

**Binary pass/fail provides no learning value:** "Test 3 failed" tells a student nothing
about why their logic is wrong or how to fix it. This is the most cited complaint in
academic literature on autograders. The LLM feedback layer directly addresses this.

**False negatives destroy trust:** Correct code marked wrong due to formatting differences
measurably harms learning outcomes by reducing student engagement with feedback. Output
normalization and human TA review before release both mitigate this.

**Timeout failures with no partial credit:** Gradescope's 768MB memory limit and 10-minute
global timeout result in a score of 0 with no indication of which tests passed before
the timeout. Our per-test timeout and partial credit model preserve what the student got right.

### Security complaints (Gradescope-specific)

**Grade manipulation via results.json:** Gradescope runs student code as root with
unrestricted filesystem access. Since 2016, students can overwrite the results file to
assign themselves any grade. Known and unpatched for years. Our non-root container model
with read-only filesystem prevents this class of attack.

**Reverse shell from submitted code:** Gradescope containers have unrestricted outbound
network access. Student code can open a reverse shell to an external server, gaining root
access to the container. `--network none` at the Docker level eliminates this.

---

## Academic Paper Notes — Breakout Autograder (SIGCSE 2024)

**Citation:** Liu, E.Z. et al. (2024). *A Fast and Accurate Machine Learning Autograder
for the Breakout Assignment.* SIGCSE 2024, Portland, OR. ACM.
DOI: https://doi.org/10.1145/3626252.3630759

### What they built

A human-in-the-loop autograder for the Stanford CS1 Breakout (Python game) assignment.
Traditional unit tests fail for this assignment because it is interactive and stochastic.
They used a reinforcement learning agent (DreamGrader framework) that plays each student's
game autonomously, exposing bugs by reaching relevant game states, then records short video
clips of discovered errors for TA review.

### Results

| Grading method | Time per submission | Accuracy |
|----------------|---------------------|----------|
| Manual grading | 8 min 35s | 86.4% |
| AI + human review | 4 min 49s | 92.3% |
| AI only (no human) | — | 90.1% |

44% time reduction and 6% accuracy improvement simultaneously. Graders rated 9/10 on
willingness to recommend. Free-form feedback focused almost entirely on UI improvements
— the grading logic was well-received.

### Key finding relevant to this project

Graders who overruled the AI's predictions introduced errors — meaning the AI was
sometimes more accurate than the human override. This validates the human-in-the-loop
design: the TA review step is a safety net for the AI, but the AI is not merely a
convenience layer. Both contribute to the final grade quality.

### Relevance to UVU autograder

- Validates the human-in-the-loop architecture chosen for this project
- The training data generation approach (programmatically inject known errors into a
  reference implementation to create synthetic training sets) is reusable for calibrating
  LLM grading prompts before real student data is available
- Their biggest failure mode (missed errors due to training data gaps) does not apply to
  our LLM-based approach — the model reasons semantically, not from a fixed training distribution
- Their live deployment feedback was almost entirely about UI — confirms that review
  dashboard UX is where this project will win or lose in demo conditions
- The paper explicitly suggests that similar techniques could apply to web design assignments
  — directly in scope for the HTML/CSS support planned in M4

---

## TLS + InCommon Notes

### What InCommon is

InCommon is a federated identity and trust consortium run by Internet2 for higher education.
Most US universities are members. The certificate program partners with Sectigo (formerly
Comodo) to provide free unlimited TLS certificates to member institutions.

### Certificate types available

- OV (Organizational Validation) SSL/TLS — standard server certificates
- EV (Extended Validation) — higher assurance, green bar in some browsers
- Client certificates — for mutual TLS if needed
- Code signing certificates

All are included under the institution's annual InCommon membership fee.

### Certificate request process

1. Generate a private key and CSR on the server:
```bash
openssl req -new -newkey rsa:2048 -nodes \
  -keyout ai-tutor.key \
  -out ai-tutor.csr \
  -subj "/C=US/ST=Utah/L=Orem/O=Utah Valley University/CN=ai-tutor.uvu.edu"
```
2. Send the CSR (not the key) to university IT
3. IT submits through Sectigo Certificate Manager under the university's RAO account
4. IT receives the signed certificate chain and provides it to the developer
5. Bundle the chain: `cat server.crt InCommon_Intermediate.crt > server-bundle.crt`
6. Install bundle + private key in Nginx

> **Chain transition note:** InCommon is migrating to new intermediate CAs
> (InCommon RSA OV SSL CA 3) due to browser trust store changes. When requesting,
> ask IT to issue from the new chain to avoid early reissuance.

### Nginx TLS configuration

```nginx
server {
    listen 443 ssl;
    server_name ai-tutor.uvu.edu;

    ssl_certificate     /etc/ssl/server-bundle.crt;
    ssl_certificate_key /etc/ssl/ai-tutor.key;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers off;

    add_header Strict-Transport-Security "max-age=63072000" always;
    add_header X-Frame-Options SAMEORIGIN;   # required for Canvas iframe embedding
    add_header X-Content-Type-Options nosniff;

    proxy_buffering off;    # critical for SSE streaming token output
    proxy_cache off;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Host $host;
    }
}
```

### Similarity to Apple Developer certificates

The CSR workflow is identical to generating a CSR for Apple Gatekeeper / Developer ID
signing. The cryptographic mechanism is the same PKI model — you generate a private key
locally, submit the public half (CSR) to a CA, and receive a signed certificate back.
The difference is what the CA is vouching for: Apple's CA vouches for developer identity
(code signing), Sectigo vouches for server identity (domain ownership). The private key
workflow and the concept of a certificate chain are identical in both contexts.

---

## LTI 1.3 + Canvas Integration Notes

### What LTI 1.3 is

Learning Tools Interoperability 1.3 is the current standard for embedding external tools
inside Canvas. It uses OpenID Connect (OIDC) for authentication — Canvas acts as the
identity provider, your app acts as the tool. When a student clicks the tool in Canvas,
Canvas sends a signed JWT asserting the student's identity, role, and course context.
Your app validates the JWT and creates a session without requiring a separate login.

### OIDC launch flow summary

```
Student clicks tool in Canvas
        ↓
Canvas POSTs login hint to your oidc_initiation_url
        ↓
Your app redirects back to Canvas auth endpoint with state + nonce
        ↓
Canvas signs a JWT with student ID, name, email, role, course context
        ↓
Canvas POSTs id_token to your redirect_uri
        ↓
Your app validates JWT against Canvas public JWKs
        ↓
Session created — student is authenticated, tool loads in Canvas iframe
```

### Canvas admin setup required

Canvas admin must create a Developer Key with your tool's configuration JSON, then
deploy it to the course or account. You host a config endpoint that Canvas admin
pastes as a URL — they do not need to manually enter JSON fields.

### Safari iframe cookie issue

Safari blocks third-party cookies in iframes by default. LTI 1.3 tools embedded in Canvas
are iframes and will fail to maintain sessions in Safari without a workaround. The `ltijs`
Node library handles this automatically via the LTI Platform Storage spec (postMessage-based
cookie proxy). Do not implement session management with plain cookies in the LTI context.

### Recommended library

`ltijs` (Node/Next.js) handles: OIDC flow, nonce/state verification, JWK fetching and
caching, Safari workaround, and session management. Use it rather than implementing
JWT validation manually.

### Canvas documentation

Current canonical location: `developerdocs.instructure.com`
The older `canvas.instructure.com/doc/api` is being retired after July 1, 2026.

Key pages to read in order:
1. External Tools Introduction — placement types and overview
2. LTI Launch Overview — OIDC flow with Canvas-specific details including Safari workaround
3. Configuring LTI 1.3 — Developer Key JSON format

---

## Security Architecture Notes

### Why the on-prem model is stronger than it appears

A common assumption is that cloud = more secure than on-prem. This is accurate at the
infrastructure layer (physical security, DDoS protection, patch management) but misleading
at the application layer for this specific use case.

The cloud threat model that matters most here is data exfiltration — student code,
grades, and academic records. On-prem with the attack surface described below is more
defensible for this threat than a cloud deployment where student data transits multiple
third-party systems.

### Attack surface on the Mac Mini (production)

```
Exposed to public internet:
  - TCP 443 (Nginx) — TLS only, rate limited, WAF rules

Bound to localhost only (not reachable from network):
  - FastAPI :8000
  - Next.js :3000
  - llama-server :8080
  - PostgreSQL :5432
  - Redis :6379

Not exposed at all:
  - Model weights (filesystem only)
  - Student submission files (filesystem only)
  - Grading container filesystem (ephemeral, destroyed after job)
```

### Container security model

Each grading job runs in an ephemeral Docker container with:
- `--network none` — no inbound or outbound network access
- `--cpus 0.5` — hard CPU limit, prevents fork bombs from saturating the host
- `--memory 256m` — hard memory limit
- `--read-only` on all directories except designated output dir
- Unprivileged non-root user (UID 1000 or equivalent)
- Destroyed immediately after job completion — no state persists

AST constraint check runs **before** container launch. Submissions containing `socket`,
`subprocess`, `os.system`, `os.fork`, or `__import__` calls are flagged and can be
blocked from execution entirely at instructor's discretion.

### University IT coordination checklist

Before go-live, the following must be confirmed with IT:

- [ ] Static public IP assigned to Mac Mini NIC
- [ ] DNS entry: `autograder.uvu.edu` (or equivalent) pointing to that IP
- [ ] Firewall rule: inbound TCP 443 only, all other inbound blocked
- [ ] Mac Mini included in IT's network monitoring scope (SIEM / flow analysis)
- [ ] Physical security: machine in locked rack in data center, not an office
- [ ] InCommon certificate requested through IT's Sectigo portal

---

## MCP Protocol Reference

### What MCP is (relevant for future integrations)

MCP (Model Context Protocol) is an open standard for giving AI models structured,
bidirectional access to external tools and data sources. It is the protocol used by
Claude.ai connectors (HubSpot, Gmail, Slack, etc.).

### Relevance to this project

In M3+, if the team wants to give the LLM grading agent access to external resources
(Canvas course data, student roster, past assignment history) without hard-coding API
calls, an MCP server layer provides a clean abstraction. The grading LLM could call
a `get_student_history` tool or `get_assignment_rubric` tool via the MCP protocol rather
than having those data fetches embedded in the FastAPI prompt-building logic.

Not required for M1–M2. Worth noting as an architectural option for later phases when
the system becomes more agent-like rather than purely pipeline-like.

### Transport

JSON-RPC 2.0 over SSE (for remote servers) or stdio (for local processes). The local
llama-server does not speak MCP natively — this would be a wrapper layer in FastAPI
that presents tools to the model in the system prompt and intercepts tool_use blocks
in the LLM response.
