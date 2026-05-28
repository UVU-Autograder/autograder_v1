# UVU Autograder v1 - Decisions and Current M1 Assumptions

This file tracks the current product and implementation decisions for the Jaxon backend plan.

Open questions live in `docs/implementation_questions.md`.

## Decision Log

| Decision | Choice | Rationale |
| --- | --- | --- |
| Backlog tool | GitHub Projects (Issues + Milestones) | Repo-local, free, and simple |
| Data retention | Zero-retention for student submissions and detailed grading artifacts | Reduces FERPA risk and M1 complexity |
| Database scope | Store staff/course metadata, assignments/configs, lightweight artifact metadata, derived test projections when needed, and sanitized run metadata only | Keeps persistent data small and non-sensitive |
| Execution stack | Judge0 CE with Kata Containers isolation | Captures the current execution engine and isolation model used in the M1 plan |
| AI inference | Azure OpenAI API | Matches the approved university privacy posture |
| Plagiarism detection | Out of scope for M1 | Avoids sending live student code to an external plagiarism service before institutional approval; future work should prefer a local or otherwise approved tool |
| Auth (M1) | Staff uses NextAuth + Microsoft OAuth; student sandbox access requires no student authentication | Keeps staff workflows tied to trusted UVU identity while avoiding student-specific sandbox identity handling |
| UVU restriction | Reject non-`@uvu.edu` staff logins | Keeps staff/admin access bounded to UVU users |
| Student access model | Session-only sandbox access to globally visible sandbox-enabled assignments | Avoids student-specific schedule or roster lookups in the sandbox flow |
| Sandbox visibility source | `sandbox_enabled` assignment visibility only | Keeps sandbox availability assignment-driven rather than roster-driven |
| Assignment content source | Canvas-managed | Canvas remains the source of truth for course content and grades |
| Assignment ownership | Course-shared assignment setup | Keeps the main grading config and grading assets shared while section scope stays focused on access and runs |
| Config authoring model | Wizard-first with app-owned `config.json` | Keeps backend ownership clear while supporting guided UI authoring |
| Raw config handling | Advanced-only import/export/edit support | Preserves config round-trip support without competing with the main wizard flow |
| Concept policy | Progressive whitelist via `Concepts Covered` | Aligns AST checks and LLM context to course progression |
| Sandbox output | On-screen only | Preserves zero-retention and avoids downloadable sandbox artifacts |
| Official rate limiting | No sandbox-style cap | Staff uploads are not student-limited |
| Sandbox rate limiting | `5 uploads per hour` per sandbox session | Controls abuse and Azure cost exposure without requiring student identity |
| Official raw submission downloads | Out of scope for M1 | Derived artifacts plus in-app Monaco/JSON review are sufficient |
| Official export shape | Two separate staff downloads: Canvas-grade CSV and per-student HTML feedback ZIP | Keeps M1 exports explicit without introducing a combined package or Canvas feedback distribution |
| Canvas feedback distribution | Out of scope for M1 | Avoids Canvas bulk feedback upload complexity in the first milestone |
| Official review workflow | Preview-only before export | Staff can inspect grading results without introducing in-app grade or feedback edits |
| Manual or non-code grading | Out of scope for M1 | Avoids adding persistent review state, grade overrides, and hybrid manual workflows to the zero-retention model |
| Artifact storage | Hybrid | Config and metadata in Postgres; file bodies behind a storage abstraction |
| Frontend editor | Monaco Editor, locally hosted | Planned editor and review surface for M1 |
| Workspace lifecycle | Explicit shared integration | Cleanup is core zero-retention behavior, not a hidden detail |
| Permission baseline | M1 actors are `admin`, `instructor`, `IA`, and `student`, with section-scoped staff access | Defines the current role model around course-shared setup and section-scoped run authority |
| IA assignment-config authority | Read-only in M1 | Keeps role-based authorization simple while letting IAs run and review official workflows in assigned sections |
| Student history | No persistent sandbox attempt history | Maintains zero-retention FERPA alignment |
| Run summary shape | Minimal aggregate metadata only | Avoids freezing lifecycle timestamps into the current product model |
| Logging posture | Persistent logs and run metadata are aggregate-only and non-identifying; sensitive debug traces are short-lived only | Reduces the risk of recreating education records through operational data |
| Execution-artifact retention | Judge0 submission/result artifacts and Kata execution state are destroyed immediately after verification and retrieval | Makes zero-retention explicit at the execution-service boundary |
| Hosting target | M1 runs locally/on-prem on the Dell workstation | Judge0 + Kata depends on the local Docker and hardware/containerization model, so Railway-style hosted deployment is not viable for the current implementation |
| Capacity planning | Concurrency is memory-bound and benchmarked on the Dell workstation before launch | Prevents peak-load overcommit on limited hardware |

## Current M1 Assumptions

- `Actors`
  - M1 actors are `admin`, `instructor`, `IA`, and `student`
  - staff accounts, roles, and access grants are stored persistently
  - student access is session-based and zero-retention
  - staff actors authenticate through Microsoft OAuth restricted to `@uvu.edu`
  - student sandbox access does not require a student-specific identity record or roster-derived authorization mapping

- `Assignments`
  - assignments are course-linked and course-shared in M1
  - section scope affects official runs and staff access rather than assignment setup ownership
  - grading data currently centers on the app-owned `config.json`, course-level `Concepts Covered` defaults, assignment-level concept additions, pytest-linked tests, and model solution content
  - `Concepts Covered` is enforced through a runtime merge of course defaults plus assignment additions in M1
  - grading setup is authored primarily through a comprehensive instructor-facing wizard
  - current `config.json` must remain importable, exportable, and downloadable
  - any persisted `TestCase` rows are derived projections for querying/UI only and must never become a second editable grading model

- `Artifacts`
  - config JSON lives in Postgres as the primary grading definition
  - artifact metadata stays lightweight and file bodies remain behind the storage abstraction
  - pytest content, model solutions, and support-file bodies are accessed through a shared storage abstraction
  - current M1 storage is local/on-prem behind the storage abstraction; the abstraction stays in place so future backing stores can change without rewriting the contract

- `Official batch processing`
  - instructor or IA uploads a Canvas ZIP for a single assignment run
  - official batch execution is authorized only within explicitly assigned section scope
  - malformed or non-Canvas ZIPs are rejected before queueing
  - extraction occurs only in an ephemeral temp directory or equivalent volatile workspace
  - official-run review is preview-only in M1 and does not support in-app grade overrides or feedback edits
  - official-run downloads are exposed as two separate staff actions: Canvas-grade CSV and per-student HTML feedback ZIP
  - the system does not expose a raw student-submission download path in M1
  - Judge0 submission/result records are deleted from Judge0 immediately after retrieval rather than being mirrored into app-owned persistent storage
  - student files, intermediate files, and detailed grading output are destroyed after the official workflow completes
  - the system may keep sanitized run metadata such as counts, coarse failure categories, and Azure token usage, but never student code, filenames, identifiers, detailed failure text, detailed feedback files, or persisted plagiarism-report references

- `Student sandbox processing`
  - any sandbox user can open the sandbox and browse globally visible sandbox-enabled courses and assignments
  - student selects a course, then an assignment, uploads code, and receives projected score and feedback on screen
  - sandbox uploads are strictly limited to `5 uploads per hour` per sandbox session
  - the sandbox workspace must show remaining uploads in the current window and a clear limit-reached state when the cap is hit
  - sandbox uploads are processed only in ephemeral working storage
  - sandbox artifacts are destroyed on completion or session exit
  - sandbox output is not downloadable and is not stored persistently

- `Frontend tooling`
  - Monaco Editor is the planned locally hosted code editor and review surface for M1
  - Monaco supports staff code review and sandbox editing or upload assistance in M1
  - M1 sandbox feedback is presented adjacent to grounded test results rather than as in-editor grading annotations
  - sandbox UX must surface remaining uploads, limit-reached messaging, and friendly handling of rate-limit failures

- `Concepts Covered`
  - M1 uses a progressive whitelist, not a blacklist
  - course defaults are authored at the course level
  - assignments store additive concept entries only; they do not remove course defaults in M1
  - the effective allow-list is computed at runtime as `course defaults + assignment additions`
  - the merged list is ordered with course defaults first and assignment additions after, with duplicate concepts removed automatically
  - future-concept usage can surface warnings
  - security-sensitive findings can hard-block execution
  - allowed concepts are injected into LLM prompt context

- `Permissions`
  - admins manage staff accounts, roles, and access grants
  - instructors can view grading setup across assigned courses
  - instructors may edit grading setup and launch official runs only in sections explicitly assigned to them
  - IAs are section-scoped in M1, may view grading setup in assigned sections, and may launch official runs only where their grant allows it
  - IAs do not receive assignment-config or rubric authoring authority in M1

- `Hosting and operations`
  - the current M1 deployment plan runs locally/on-prem on the Dell workstation
  - the current M1 stack includes Next.js, FastAPI, Postgres, Redis, Celery, and Judge0 on that host
  - Judge0 runs locally in Docker with Kata Containers isolation on that workstation
  - Railway or similar hosted app deployment is not part of the M1 plan because the Judge0 + Kata execution path depends on the local Docker and hardware/containerization setup
  - queueing and backpressure are preferred over raising concurrency beyond the workstation's tested memory-safe limits

## Operational Defaults

- Judge0 execution uses a `10s` timeout target, `256MB` memory limit target, and network-disabled student execution.
- Kata Containers is the planned VM-based isolation layer for Judge0 execution.
- Cleanup must satisfy the zero-retention contract across local and external execution artifacts.
- Judge0 submission/result artifacts and Kata-backed execution state are destroyed immediately after verification and retrieval.
- Judge0 submission/result records are deleted through `DELETE /submissions/{token}` immediately after retrieval and are not retained in app-owned Postgres.
- Persistent logs must not retain student code, filenames, student identifiers, raw tracebacks, or detailed failure text.
- Any sensitive debug traces that are temporarily enabled for operations must be short-lived, aggressively rotated, and purged within `24h`.
- Async grading failures retry up to `3` times with backoff before surfacing a permanent failure state.
- Run-status delivery contract is `GET /runs/{id}/status`, backed by Redis transient status storage.
- Staff and student clients poll `GET /runs/{id}/status` at a fixed `2s` cadence until terminal state.
- Celery concurrency must remain at or below the Dell workstation's documented memory-tested Judge0 capacity.
- Cleanup runs immediately after official workflow completion and after sandbox completion or session exit.
- Azure OpenAI privacy or ZDR posture must be confirmed before live grading with student code.
- Azure token usage is logged only as sanitized run metadata.
