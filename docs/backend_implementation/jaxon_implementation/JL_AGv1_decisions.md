# UVU Autograder v1 - Decisions and Locked M1 Assumptions

## Decision Log

| Decision                  | Choice                                                                                                                    | Rationale                                                                                            |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| Backlog tool              | GitHub Projects (Issues + Milestones)                                                                                     | Repo-local, free, and simple                                                                         |
| Data retention            | Zero-retention for student submissions and detailed grading artifacts                                                     | Reduces FERPA risk and M1 complexity                                                                 |
| Database scope            | Store staff/course metadata, minimal student-course authorization mapping, assignments/configs/tests/artifact metadata, and sanitized run metadata only | Keeps persistent data small and non-sensitive while enabling course-level sandbox authorization      |
| Execution engine          | Judge0 CE on separate execution infrastructure                                                                            | Supports the long-term roadmap while keeping privileged execution outside the core Railway app stack |
| AI inference              | Azure OpenAI API                                                                                                          | Matches the approved university privacy posture                                                      |
| Plagiarism detection      | Stanford MOSS via `mosspy`                                                                                                | Optional staff-only review aid using ephemeral files                                                 |
| Auth (M1)                 | NextAuth + Microsoft OAuth                                                                                                | Fastest practical trusted UVU identity path                                                          |
| UVU restriction           | Reject non-`@uvu.edu` logins                                                                                              | Keeps M1 access bounded to UVU users                                                                 |
| Student access            | Session-only sandbox access with no persistent student profile; access to course listings comes from minimal enrollment authorization mapping | Preserves sandbox use without profile retention while still gating course visibility                  |
| Student course authorization source | Instructor-uploaded initial Canvas roster per course section                                                       | Limits sandbox course visibility to Canvas-listed students only                                       |
| Assignment content        | Canvas-canonical                                                                                                          | Canvas remains the source of truth for course content and grades                                     |
| Rubric/config setup       | Comprehensive instructor-facing wizard plus `config.json` import/export                                                    | Keeps the backend model canonical while making UI authoring the primary M1 workflow                  |
| Concept policy            | Progressive whitelist via `Concepts Covered`                                                                              | Aligns AST checks and LLM context to course progression                                              |
| Official output           | CSV + master ZIP of per-student HTML feedback                                                                             | Lightweight and Canvas-compatible                                                                    |
| Sandbox output            | On-screen only                                                                                                            | Preserves zero-retention and avoids downloadable artifacts                                           |
| Official rate limiting    | No sandbox-style cap                                                                                                      | Staff uploads are not student-limited                                                                |
| Sandbox rate limiting     | `5 uploads per hour` per authenticated student                                                                            | Controls abuse and Azure cost exposure                                                               |
| Artifact storage          | Hybrid                                                                                                                    | Config and metadata in Postgres; file bodies behind a storage abstraction                            |
| Frontend code editor      | Monaco Editor, locally hosted                                                                                             | Canonical editor and review surface for sandbox and staff code workflows                             |
| Workspace lifecycle       | Explicit shared integration                                                                                               | Cleanup is core zero-retention behavior, not a hidden detail                                         |
| MOSS report URL retention | Persist in `RunSummary` as safe staff-facing metadata                                                                     | Preserves the returned review link without retaining student code                                    |
| Instructor visibility     | View assigned courses, edit own sections only                                                                             | Supports cross-section visibility without cross-section editing                                      |
| IA visibility             | Assigned sections only                                                                                                    | Keeps IA access scoped to validation work                                                            |
| Student sandbox attempt history | Session-only, ephemeral; no persistent backend storage of attempts or history | Maintains zero-retention FERPA compliance; students see only in-session feedback on screen only      |
| Hosting target            | Railway-first for app services, split-host for execution                                                                  | Keeps the app stack simple while isolating privileged code execution outside Railway                 |

## Locked M1 Assumptions

- `Actors`
  - M1 actors are `admin`, `instructor`, `IA`, and `student`
  - staff accounts, roles, and access grants are stored persistently
  - student access is session-based and zero-retention
  - student sandbox authorization uses a minimal persistent mapping seeded from instructor-uploaded Canvas roster data and keyed by normalized Microsoft email plus Canvas-listed student identifier and `course_id`; this is not a full student profile

- `Assignments`
  - assignments are course-linked with section-aware edit and run permissions
  - app-owned grading data includes config JSON, concept defaults and overrides, pytest-linked tests, model solution content, and student-visible test descriptions
  - grading setup is authored primarily through a comprehensive instructor-facing wizard that generates the canonical app-owned `config.json`
  - current `config.json` must remain importable, exportable, and downloadable
  - raw JSON editing is not required as a primary M1 workflow

- `Artifacts`
  - config JSON and structured assignment metadata live in Postgres
  - pytest content, model solutions, and support-file bodies are accessed through a shared storage abstraction
  - storage may be local in development and file/object-backed in production without changing the contract

- `Official batch processing`
  - instructor or IA uploads a Canvas ZIP for a single assignment run
  - official batch execution is authorized only within explicitly assigned section scope
  - malformed or non-Canvas ZIPs are rejected before queueing
  - extraction occurs only in an ephemeral temp directory or equivalent volatile workspace
  - execution is delegated to Judge0 as a Kata-backed isolated privileged service outside the main Railway app stack
  - optional MOSS submission uses only files from the current ephemeral batch workspace
  - MOSS output is a staff-facing review aid and not an automatic penalty
  - Judge0 submission and result records, plus Kata-backed execution artifacts, must be deleted or invalidated immediately after result retrieval and grading completion
  - student files, intermediate files, and detailed grading output are destroyed after export is returned
  - the system may keep sanitized run metadata such as timestamps, counts, failure summaries, Azure token usage, and the returned MOSS report URL, but never student code or detailed feedback files

- `Student sandbox processing`
  - student selects an assignment, uploads code, and receives projected score and feedback on screen
  - student-visible course listings are derived from minimal authorization mapping and may be empty when no authorized course mappings exist
  - sandbox uploads are strictly limited to `5 uploads per hour` per authenticated student identity
  - sandbox uploads are processed only in ephemeral working storage
  - sandbox execution uses the same Judge0 + Kata path with the same post-result deletion requirement
  - sandbox artifacts are destroyed on completion or session exit
  - sandbox output is not downloadable and is not stored persistently

- `Frontend tooling`
  - Monaco Editor is the canonical locally hosted code editor and review surface for M1
  - Monaco supports staff code review and sandbox editing or upload assistance in M1
  - M1 LLM feedback appears as a sandbox textbox adjacent to test results and is explanation-only; inline editor annotations are deferred to post-M1

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
  - whether IAs also receive rubric/config authoring permission remains deferred and should be finalized separately from the M1 config-model decision

- `Output`
  - official grading produces a grade CSV and a master ZIP containing per-student HTML feedback files
  - sandbox grading produces on-screen projected feedback only
  - no PDF output is generated
  - no long-term student result history is retained in M1

## Operational Defaults

- Judge0 execution uses a `10s` timeout target, `256MB` memory limit target, and network-disabled student execution.
- Kata Containers is the canonical VM-based isolation layer for Judge0 execution.
- Judge0 is hosted as a separate Kata-backed isolated privileged execution service rather than inside the main Railway app stack.
- Judge0 submission and result artifacts, plus Kata-backed execution artifacts, must be deleted or invalidated immediately after retrieval so the zero-retention contract still holds.
- Async grading failures retry up to `3` times with backoff before surfacing a permanent failure state.
- Run-status delivery contract is `GET /runs/{id}/status`, backed by Redis transient status storage.
- Staff and student clients poll `GET /runs/{id}/status` at a fixed `2s` cadence until terminal state.
- Celery concurrency must remain aligned to documented Judge0 execution capacity to avoid container exhaustion.
- Cleanup runs immediately after official export completion and after sandbox completion or session exit.
- Azure OpenAI privacy or ZDR posture must be confirmed before live grading with student code.
- Azure token usage is logged only as sanitized run metadata.

Dev or staging hardware may differ from the production host, but this does not change Railway-first M1 production assumptions.

## Sprint Calendar

```text
Sprint 0  Environment + metadata foundation
Sprint 1  Shadow SSO + assignment/config setup + ephemeral ingestion
Sprint 2  Grading pipeline + Azure OpenAI + zero-retention controls
Sprint 3  Student sandbox + instructor batch UX + export packaging
Sprint 4  Integration testing + FERPA/compliance hardening
```
