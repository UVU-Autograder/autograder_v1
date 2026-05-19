# UVU Autograder v1 - Decisions and Locked M1 Assumptions

This file is the canonical home for resolved product and implementation decisions.

Open questions live in `docs/implementation_questions.md`.

## Decision Log

| Decision | Choice | Rationale |
| --- | --- | --- |
| Backlog tool | GitHub Projects (Issues + Milestones) | Repo-local, free, and simple |
| Data retention | Zero-retention for student submissions and detailed grading artifacts | Reduces FERPA risk and M1 complexity |
| Database scope | Store staff/course metadata, minimal student-course authorization mapping, assignments/configs, lightweight artifact metadata, derived test projections when needed, and sanitized run metadata only | Keeps persistent data small and non-sensitive |
| Execution stack | Judge0 CE with Kata Containers isolation | Locks the execution engine and isolation model without freezing the final hosting narrative |
| AI inference | Azure OpenAI API | Matches the approved university privacy posture |
| Plagiarism detection | Optional Stanford MOSS via `mosspy` | Staff-only review aid using ephemeral files |
| Auth (M1) | NextAuth + Microsoft OAuth | Fastest practical trusted UVU identity path |
| UVU restriction | Reject non-`@uvu.edu` logins | Keeps M1 access bounded to UVU users |
| Student access model | Session-only sandbox access with minimal course authorization mapping | Preserves sandbox use without persistent student profiles |
| Student authorization source | Instructor-uploaded Canvas roster from a course-level staff workflow | Limits sandbox course visibility to Canvas-listed students |
| Assignment content source | Canvas-canonical | Canvas remains the source of truth for course content and grades |
| Assignment ownership | Course-shared assignment setup | Keeps canonical config and grading assets shared while section scope stays focused on access and runs |
| Config authoring model | Wizard-first with canonical app-owned `config.json` | Keeps backend ownership clear while supporting guided UI authoring |
| Raw config handling | Advanced-only import/export/edit support | Preserves config round-trip support without competing with the main wizard flow |
| Concept policy | Progressive whitelist via `Concepts Covered` | Aligns AST checks and LLM context to course progression |
| Sandbox output | On-screen only | Preserves zero-retention and avoids downloadable sandbox artifacts |
| Official rate limiting | No sandbox-style cap | Staff uploads are not student-limited |
| Sandbox rate limiting | `5 uploads per hour` per authenticated student | Controls abuse and Azure cost exposure |
| Official export shape | Two separate staff downloads: Canvas-grade CSV and per-student HTML feedback ZIP | Keeps M1 exports explicit without introducing a combined package or Canvas feedback distribution |
| Canvas feedback distribution | Out of scope for M1 | Avoids Canvas bulk feedback upload complexity in the first milestone |
| Official review workflow | Preview-only before export | Staff can inspect results and plagiarism state without introducing in-app grade or feedback edits |
| Manual or non-code grading | Out of scope for M1 | Avoids adding persistent review state, grade overrides, and hybrid manual workflows to the zero-retention model |
| Artifact storage | Hybrid | Config and metadata in Postgres; file bodies behind a storage abstraction |
| Frontend editor | Monaco Editor, locally hosted | Canonical editor and review surface for M1 |
| Workspace lifecycle | Explicit shared integration | Cleanup is core zero-retention behavior, not a hidden detail |
| MOSS handling | Active-session-only review aid, not persistent `RunSummary` metadata | Avoids dead links and keeps the canonical run model minimal |
| Permission baseline | M1 actors are `admin`, `instructor`, `IA`, and `student`, with section-scoped staff access | Locks the role model around course-shared setup and section-scoped run authority |
| IA assignment-config authority | Read-only in M1 | Keeps role-based authorization simple while letting IAs run and review official workflows in assigned sections |
| Student history | No persistent sandbox attempt history | Maintains zero-retention FERPA alignment |
| Run summary shape | Minimal aggregate metadata only | Avoids freezing lifecycle timestamps into the canonical product model |
| Hosting target | Railway-first for app services | Keeps the app stack target clear without freezing the final execution-host narrative |

## Locked M1 Assumptions

- `Actors`
  - M1 actors are `admin`, `instructor`, `IA`, and `student`
  - staff accounts, roles, and access grants are stored persistently
  - student access is session-based and zero-retention
  - student sandbox authorization uses a minimal persistent mapping keyed by normalized Microsoft email plus course linkage; this is not a full student profile

- `Assignments`
  - assignments are course-linked and course-shared in M1
  - section scope affects roster workflows, official runs, and staff access rather than assignment setup ownership
  - canonical grading data centers on the app-owned `config.json`, concept defaults and overrides, pytest-linked tests, and model solution content
  - grading setup is authored primarily through a comprehensive instructor-facing wizard
  - current `config.json` must remain importable, exportable, and downloadable
  - any persisted `TestCase` rows are derived projections for querying/UI only and must never become a second editable grading model

- `Artifacts`
  - config JSON lives in Postgres as the canonical grading definition
  - artifact metadata stays lightweight and file bodies remain behind the storage abstraction
  - pytest content, model solutions, and support-file bodies are accessed through a shared storage abstraction
  - storage may be local in development and file/object-backed in production without changing the contract

- `Official batch processing`
  - instructor or IA uploads a Canvas ZIP for a single assignment run
  - official batch execution is authorized only within explicitly assigned section scope
  - malformed or non-Canvas ZIPs are rejected before queueing
  - extraction occurs only in an ephemeral temp directory or equivalent volatile workspace
  - optional MOSS submission uses only files from the current ephemeral batch workspace
  - MOSS output is a staff-facing review aid for the active official-run session and not an automatic penalty
  - official-run review is preview-only in M1 and does not support in-app grade overrides or feedback edits
  - official-run downloads are exposed as two separate staff actions: Canvas-grade CSV and per-student HTML feedback ZIP
  - student files, intermediate files, and detailed grading output are destroyed after the official workflow completes
  - the system may keep sanitized run metadata such as counts, failure summaries, and Azure token usage, but never student code, detailed feedback files, or persisted MOSS references

- `Student sandbox processing`
  - student selects a course, then an assignment, uploads code, and receives projected score and feedback on screen
  - student-visible course listings are derived from minimal authorization mapping and may be empty when no authorized course mappings exist
  - sandbox uploads are strictly limited to `5 uploads per hour` per authenticated student identity
  - the sandbox workspace must show remaining uploads in the current window and a clear limit-reached state when the cap is hit
  - sandbox uploads are processed only in ephemeral working storage
  - sandbox artifacts are destroyed on completion or session exit
  - sandbox output is not downloadable and is not stored persistently

- `Frontend tooling`
  - Monaco Editor is the canonical locally hosted code editor and review surface for M1
  - Monaco supports staff code review and sandbox editing or upload assistance in M1
  - M1 sandbox feedback is presented adjacent to grounded test results rather than as in-editor grading annotations
  - sandbox UX must surface remaining uploads, limit-reached messaging, and friendly handling of rate-limit failures

- `Concepts Covered`
  - M1 uses a progressive whitelist, not a blacklist
  - course defaults and assignment overrides are both allow-list based in the simplified M1 model
  - future-concept usage can surface warnings
  - security-sensitive findings can hard-block execution
  - allowed concepts are injected into LLM prompt context

- `Permissions`
  - admins manage staff accounts, roles, and access grants
  - instructors can view grading setup across assigned courses
  - instructors may edit grading setup and launch official runs only in sections explicitly assigned to them
  - IAs are section-scoped in M1, may view grading setup in assigned sections, and may launch official runs only where their grant allows it
  - IAs do not receive assignment-config or rubric authoring authority in M1

## Operational Defaults

- Judge0 execution uses a `10s` timeout target, `256MB` memory limit target, and network-disabled student execution.
- Kata Containers is the canonical VM-based isolation layer for Judge0 execution.
- Cleanup must satisfy the zero-retention contract across local and external execution artifacts.
- Async grading failures retry up to `3` times with backoff before surfacing a permanent failure state.
- Run-status delivery contract is `GET /runs/{id}/status`, backed by Redis transient status storage.
- Staff and student clients poll `GET /runs/{id}/status` at a fixed `2s` cadence until terminal state.
- Celery concurrency must remain aligned to documented Judge0 execution capacity to avoid exhaustion.
- Cleanup runs immediately after official workflow completion and after sandbox completion or session exit.
- Azure OpenAI privacy or ZDR posture must be confirmed before live grading with student code.
- Azure token usage is logged only as sanitized run metadata.
