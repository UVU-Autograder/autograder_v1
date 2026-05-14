# UVU Autograder v1 - Decisions and Locked M1 Assumptions

> This file is part of the canonical Jaxon-authored M1 implementation baseline. Preserved Easton reference docs in this folder are useful context but non-authoritative when they conflict with the choices here.

## Decision Log

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Backlog tool | GitHub Projects (Issues + Milestones) | Repo-local, free, and simple |
| Data retention | Zero-retention for student submissions and detailed grading artifacts | Reduces FERPA risk and M1 complexity |
| Database scope | Store staff, courses, sections, assignments, configs, concepts, tests, artifact metadata, and sanitized run metadata only | Keeps persistent data small and non-sensitive |
| Execution engine | Piston on Railway | Sandboxed execution with explicit resource limits |
| AI inference | Azure OpenAI API | Matches the approved university privacy posture |
| Plagiarism detection | Stanford MOSS via `mosspy` | Optional staff-only review aid using ephemeral files |
| Auth (M1) | NextAuth + Microsoft OAuth | Fastest practical trusted UVU identity path |
| UVU restriction | Reject non-`@uvu.edu` logins | Keeps M1 access bounded to UVU users |
| Student access | Session-only sandbox access with no persistent student profile | Preserves sandbox use without retention |
| Assignment content | Canvas-canonical | Canvas remains the source of truth for course content and grades |
| Rubric/config setup | Wizard plus raw `config.json` import/export | Supports guided setup and direct JSON editing |
| Concept policy | Progressive whitelist via `Concepts Covered` | Aligns AST checks and LLM context to course progression |
| Official output | CSV + master ZIP of per-student HTML feedback | Lightweight and Canvas-compatible |
| Sandbox output | On-screen only | Preserves zero-retention and avoids downloadable artifacts |
| Official rate limiting | No sandbox-style cap | Staff uploads are not student-limited |
| Sandbox rate limiting | `5 uploads per hour` per authenticated student | Controls abuse and Azure cost exposure |
| Artifact storage | Hybrid | Config and metadata in Postgres; file bodies behind a storage abstraction |
| Workspace lifecycle | Explicit shared integration | Cleanup is core zero-retention behavior, not a hidden detail |
| MOSS report URL retention | Persist in `RunSummary` as safe staff-facing metadata | Preserves the returned review link without retaining student code |
| Instructor visibility | View assigned courses, edit own sections only | Supports cross-section visibility without cross-section editing |
| IA visibility | Assigned sections only | Keeps IA access scoped to validation work |
| Hosting target | Railway-first for M1 | Keeps deployment assumptions simple |

## Locked M1 Assumptions

- `Actors`
  - M1 actors are `admin`, `instructor`, `IA`, and `student`
  - staff accounts, roles, and access grants are stored persistently
  - student access is session-based and zero-retention

- `Assignments`
  - assignments are course-linked with section-aware edit and run permissions
  - app-owned grading data includes config JSON, concept defaults and overrides, pytest-linked tests, model solution content, and student-visible test descriptions
  - staff may create or edit grading setup through either a basic wizard or direct `config.json`
  - current `config.json` must remain viewable, editable, and downloadable

- `Artifacts`
  - config JSON and structured assignment metadata live in Postgres
  - pytest content, model solutions, and support-file bodies are accessed through a shared storage abstraction
  - storage may be local in development and file/object-backed in production without changing the contract

- `Official batch processing`
  - instructor or IA uploads a Canvas ZIP for a single assignment run
  - official batch execution is authorized only within explicitly assigned section scope
  - malformed or non-Canvas ZIPs are rejected before queueing
  - extraction occurs only in an ephemeral temp directory or equivalent volatile workspace
  - optional MOSS submission uses only files from the current ephemeral batch workspace
  - MOSS output is a staff-facing review aid and not an automatic penalty
  - student files, intermediate files, and detailed grading output are destroyed after export is returned
  - the system may keep sanitized run metadata such as timestamps, counts, failure summaries, Azure token usage, and the returned MOSS report URL, but never student code or detailed feedback files

- `Student sandbox processing`
  - student selects an assignment, uploads code, and receives projected score and feedback on screen
  - sandbox uploads are strictly limited to `5 uploads per hour` per authenticated student identity
  - sandbox uploads are processed only in ephemeral working storage
  - sandbox artifacts are destroyed on completion or session exit
  - sandbox output is not downloadable and is not stored persistently

- `Concepts Covered`
  - M1 uses a progressive whitelist, not a blacklist
  - future-concept usage can surface warnings
  - security-sensitive findings can hard-block execution
  - allowed concepts are injected into the LLM prompt context

- `Permissions`
  - admins manage staff accounts, roles, and access grants
  - instructors can view grading setup across assigned courses
  - instructors may edit grading setup and launch official runs only in sections explicitly assigned to them
  - IAs can view and validate grading only in assigned sections and may launch official runs only where that section grant allows it

- `Output`
  - official grading produces a grade CSV and a master ZIP containing per-student HTML feedback files
  - sandbox grading produces on-screen projected feedback only
  - no PDF output is generated
  - no long-term student result history is retained in M1

## Operational Defaults

- Piston execution uses a `10s` timeout, `256MB` memory limit, and no network access.
- Async grading failures retry up to `3` times with backoff before surfacing a permanent failure state.
- Celery concurrency must remain aligned to documented Piston parallelism to avoid container exhaustion.
- Cleanup runs immediately after official export completion and after sandbox completion or session exit.
- Azure token usage is logged only as sanitized run metadata.

## Sprint Calendar

```text
Sprint 0  Environment + metadata foundation
Sprint 1  Shadow SSO + assignment/config setup + ephemeral ingestion
Sprint 2  Grading pipeline + Azure OpenAI + zero-retention controls
Sprint 3  Student sandbox + instructor batch UX + export packaging
Sprint 4  Integration testing + FERPA/compliance hardening
```
