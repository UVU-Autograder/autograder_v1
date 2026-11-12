# System capabilities and stack

Canvas owns course content and official grades. The autograder owns grading configuration, execution, review and exports.

## Stack and code ownership

| Layer | Stack / maintained source |
| --- | --- |
| Frontend | Next.js App Router, React, TypeScript, Tailwind/Shadcn/Radix, Monaco, JSZip, WorkspaceVFS; offline development mode (`npm run dev`) with synthetic backend fixtures; [routes](../frontend/app/), [features](../frontend/features/), [dependencies](../frontend/package.json) |
| API and database | FastAPI, Pydantic v2, SQLAlchemy, Alembic; Python 3.11+, PostgreSQL (runtime), SQLite (hermetic pytest runner); [domains](../backend/app/domains/), [dependencies](../backend/requirements.txt) |
| Assignment/grading | Specification and grading engines (`GradingPipeline`), decoupled language strategies (`LanguageStrategy` for Python/C++), AST inspection, pytest, result normalization/parsing; [assignments](../backend/app/domains/assignments/), [grading](../backend/app/domains/grading/), [AST](../backend/app/integrations/ast_checker/) |
| Scheduling and cleanup | Celery/Redis transport, PostgreSQL execution tickets/dispatch records, shared-volume locks and independent dispatch/cleanup workers; [runs](../backend/app/domains/runs/) |
| Execution | Custom Judge0 Python 3.11.9 runtime (language 711), Kata/QEMU isolation; [image](../judge0.Dockerfile), [Compose](../docker-compose.yml), [Kata overlay](../docker-compose.kata.yml) |
| Local AI | vLLM, Gemma 4 12B QAT, reviewed `cs1410-p3b` LoRA; QLoRA training with PyTorch/Transformers/TRL/PEFT/bitsandbytes; [AI](guides/ai.md), [training dependencies](../backend/training/) |
| Identity and operations | Entra OIDC/PKCE, JWT, Nginx/TLS, Docker Compose, systemd, Python JSON audit logging; [auth](../backend/app/domains/auth/), [scripts](../scripts/) |
| Verification | Ruff, mypy, pytest, Alembic drift, TypeScript/ESLint, Vitest, Playwright; [checks](../scripts/run_checks.ps1), [browser tests](../frontend/e2e/) |

Generated [OpenAPI](schemas/openapi.json) and [assignment JSON Schema](schemas/config_v1.schema.json) describe interfaces; source models own their shape.

## Hierarchy and administration
 
**Course → modules → assignments**, alongside **course → sections**. Assignments are course-owned; sections scope official runs and staff grants. Admins manage courses/sections, staff roles/grants and monitoring. Course-scoped staff authorization is strictly enforced: instructors hold full read/write authority over assigned courses, IAs receive read-only setup access with 403 on mutations, and unassigned staff are denied access across courses, assignments, and artifacts. Section-scoped authority governs official runs.

Course defaults and module concepts inherit through the selected module; assignment denylists subtract concepts. Assignment configuration and instructor artifacts persist. Published master-course versions, section adoption and update notices are planned work.

## Public sandbox

Students need no account. They discover active sandbox assignments, upload/create/edit/delete their own workspace files via `WorkspaceVFS`, download their files/ZIP, and submit the current bundle. Provided assignment material is read-only; workspace file renaming is supported with real-time validation, multi-pane tab sync, and required entrypoint checks. Submission intake is governed by `SandboxIntakeEngine` ([app/domains/sandbox/intake.py](../backend/app/domains/sandbox/intake.py)), encapsulating preflight readiness checks, reference validation status, artifact refs, concept inheritance, prompt DB connection release, session quota & IP rate limit coordination, execution slot reservation, and Celery dispatch.

Results include projected scores, stdout, test/assertion outcomes, expected/actual I/O, diffs and concept warnings. Session-bound results are transient (normally one hour); queued work can be canceled. There is no persistent student attempt history or server-generated sandbox export.

AI receives sanitized code and grounded failures, validates its complete response before streaming, and falls back when unavailable/invalid. It explains; it never changes grades or supplies solutions. Assignment markdown summaries are rendered for students in the problem overview, sanitized and truncated to 1,000 characters for AI prompts (`PROMPT_VERSION = "v8"`), and kept in sync with automated scoring requirements.

## Assignment setup and scoring

Staff use General & Files, Tests & Rubric, and Model Solution to configure bundles, automated/manual items and reference files, run preflight, and validate reference solutions. Instructors can create/edit supported source/text reference files in the browser or upload files; [authoring](guides/assignments.md#model-solution-files) covers file naming, separate file/setup saves and current limitations. An interactive AI test assistant assists instructors in drafting pytest test suites from assignment requirements. CS1410 has 17 packages; CS1400 has 44 course assignments across 14 modules. Execution strategies decouple language runners (`python` with pytest, `cpp` with compiler diagnostics); product grading for the pilot remains Python. Pygame combines headless tests with manual visual criteria.

Canonical `assignment_configs.config` includes bundle paths/globs, language specification, pytest/model/support artifacts, unified scoring items, completion requirements ("Pass at least X of Y" objectives), concept policy, dependencies and rubric groups; instructor-authored markdown/HTML instructions persist on `assignments.description`. Stable scoring keys map to `ag_<key>` markers; all tests sharing a key must pass for its points. Completion requirements (`completion_requirements`) allow specifying objectives where students must pass at least *M* of *N* designated test cases. Extra credit can exceed the base total. Scoring items are defined directly within configuration JSON (`config["scoring_items"]`), with manual criteria supporting reusable instructor comment templates for streamlined grading feedback.

Reference validation writes a server-managed `validated_test_manifest` (`inventory_status`: `missing` / `stale` / `ready`). Sandbox and official intake reject uploads while inventory is not `ready` (without consuming session quota). Runner changes, dependency pin changes, or instructor artifact edits mark inventory stale until the model solution is re-validated in Judge0.

Student runs receive pytest/support assets, excluding model solutions. AST checks detect syntax, blocked constructs and concept policy; pytest determines correctness. Incomplete or mismatched reports are handled under official review below. [Authoring](guides/assignments.md) links models, examples and helpers.

## Official grading and review

Staff select a granted section and upload a Canvas ZIP. Pure `CanvasArchiveParser` extracts student files without database dependencies, normalizes Canvas/version suffixes, reports unmatched files, and records filename collisions (default keep: larger file). Staff must acknowledge unmatched entries and collisions before export. Incomplete/mismatched automated reports set `requires_adjudication` with `score=None`; exports stay gated until adjudication finishes, all required manual items are complete, and intake ambiguities are acknowledged. Before dispatch readiness, intake captures a versioned [grading package](../backend/app/domains/runs/grading_package.py): configuration/version, effective concepts, description, pytest/support bytes, generated runner, fallback helper and effective execution limits/dependency declarations. Required grading assets, filenames and digests are validated before admission. Model bytes, credentials and storage paths are excluded.

Official workers and the development mock runner evaluate submissions through `GradingPipeline` using that package; subsequent assignment edits cannot change a queued batch's rubric, files or requested execution parameters. A missing/corrupt/unsupported package fails the run before execution and cannot produce exports. Package and temporary files expire with the official workspace. Runtime images and installed dependency versions are not pinned by this mechanism; upgrades require draining batches and follow the [rollout checks](running.md#official-package-rollout-and-smoke-check).

Review provides counters, cohort histogram/filters, read-only files, isolated HTML previews, manual scores with 1-click comment snippet insertion, and item/overall comments. Outputs are a Canvas-grade CSV and per-student HTML `feedback.zip`; comments appear in HTML. Staff import/distribute these manually. There is no Canvas write-back or official AI.

## Integrity and trust boundaries

Host isolation, scoring integrity and grading reproducibility are separate properties:

| Property | What the system provides today | What it does not claim |
| --- | --- | --- |
| Host isolation | Judge0 inside Kata/QEMU; student networking disabled | Protection against every in-guest process trick |
| Result completeness | Versioned report contract, expected-test inventory, fail-closed parse, bounded diagnostics | Authentication of an untrusted same-process producer |
| Reproducibility | Package frozen at official admission; pinned Python 3.11.9 profile (language 711) | That queued batches survive host image upgrades without a drained rollout |

The Python grading path runs instructor tests and student imports in a supervised interpreter inside the VM, isolating report storage in system temporary directories and scrubbing execution target parameters from process arguments and environment. Schema validation rejects incomplete, duplicate or malformed reports and routes them to adjudication. AST concept checks are pedagogical, not an anti-tampering boundary. Full in-guest IPC boundary separation across student classes remains deferred ([#65](https://github.com/UVU-Autograder/autograder_v1/issues/65)).

`is_private` scoring items redact labels, I/O and assertion detail across sandbox API, HTML feedback and AI inputs. Treat **execution selection**, **feedback detail visibility** and **test-source secrecy** as independent; stripping a UI field does not protect another channel, and the same-process harness cannot promise secret-test confidentiality from arbitrary student code.

Deferred product follow-ups (tracked in Issues, not parallel docs): instructor scoring hints ([#39](https://github.com/UVU-Autograder/autograder_v1/issues/39)), comparison modes ([#43](https://github.com/UVU-Autograder/autograder_v1/issues/43)), reusable rubric comments ([#41](https://github.com/UVU-Autograder/autograder_v1/issues/41)).

## Scheduling, status and limits

Durable tickets, checkpoints and ownership leases support bounded admission, fairness, restart recovery and duplicate avoidance. Status exposes `queue`, `run`, `complete`, `failure`, counts and coarse errors. Admin monitoring covers capacity, dispatcher/cleanup failures, and zero-PII sandbox activity dashboards (system-wide at `/staff/admin/activity`, course-scoped at `/staff/courses/{courseId}/activity`) built from hashed session aggregates in `run_summaries`.

| Default | Limit |
| --- | --- |
| Bundle | 50MiB; 100 files |
| Official intake | 200 submissions/upload; 1,000 unfinished host-wide |
| Waiting executions | Warn at 40; cap 50. Full capacity rejects new sandbox intake; valid official batches may remain retained |
| Active executions | 2; higher concurrency needs host measurements |
| Judge0 | 30-second grading timeout, 256MiB memory target, student networking disabled |
| Sandbox quota | Compose default: 20 uploads/hour/session (`SANDBOX_UPLOAD_LIMIT`); bare Python settings default is effectively uncapped |

The target is 50 active users with queued grading. Deployment is single-host with reconciliation/restarts, not automatic host failover. Cloud/load balancing and additional languages remain future work (with C, C++, and HTML/CSS/JavaScript next on the docket for language implementation after Python).

## Staff identity, administration and access
 
Entra verifies university identity; active staff provisioning/grants supply authority. Backend checks tenant/issuer/audience, binds Azure OID, and issues JWTs. JWT and UI inactivity defaults are 60 minutes, with sliding token refresh (`x-refresh-token`), cross-tab session tracking (`useSyncExternalStore`), and sign-in redirects. Production/Microsoft mode disables mock login and rejects default secrets. Nginx enforces longest-prefix routing (`/api/auth/microsoft/`) directly to Next.js (`127.0.0.1:3000`) ahead of general `/api/` routing to FastAPI (`127.0.0.1:8000`), while internal services operate under strict loopback isolation (`127.0.0.1`).
 
Routes are grouped under `/sandbox`, `/staff/login`, `/staff/courses` and `/staff/admin`. Section authorization precedes expired-run responses. Process-wide audit logging scrubs PII and exception tracebacks across all framework loggers, emitting structured `"auth.access_denied"` records on 401/403 events. [Considerations](considerations.md) owns privacy/retention; [Running](running.md) owns access/testing.
