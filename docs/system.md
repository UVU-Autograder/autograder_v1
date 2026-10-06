# System capabilities and stack

Canvas owns course content and official grades. The autograder owns grading configuration, execution, review and exports.

## Stack and code ownership

| Layer | Stack / maintained source |
| --- | --- |
| Frontend | Next.js App Router, React, TypeScript, Tailwind/Shadcn/Radix, Monaco, JSZip; offline development mode (`npm run dev`) with synthetic backend fixtures; [routes](../frontend/app/), [features](../frontend/features/), [dependencies](../frontend/package.json) |
| API and database | FastAPI, Pydantic v2, SQLAlchemy, Alembic; Python 3.11+, PostgreSQL, SQLite development mode; [domains](../backend/app/domains/), [dependencies](../backend/requirements.txt) |
| Assignment/grading | Specification and grading engines, AST inspection, pytest, result normalization/parsing; [assignments](../backend/app/domains/assignments/), [grading](../backend/app/domains/grading/), [AST](../backend/app/integrations/ast_checker/) |
| Scheduling and cleanup | Celery/Redis transport, PostgreSQL execution tickets/dispatch records, shared-volume locks and independent dispatch/cleanup workers; [runs](../backend/app/domains/runs/) |
| Execution | Custom Judge0 Python 3.11.9 runtime (language 711), Kata/QEMU isolation; [image](../judge0.Dockerfile), [Compose](../docker-compose.yml), [Kata overlay](../docker-compose.kata.yml) |
| Local AI | vLLM, Gemma 4 12B QAT, reviewed `cs1410-p2c` LoRA; QLoRA training with PyTorch/Transformers/TRL/PEFT/bitsandbytes; [AI](guides/ai.md), [training dependencies](../backend/training/) |
| Identity and operations | Entra OIDC/PKCE, JWT, Nginx/TLS, Docker Compose, systemd, Python JSON audit logging; [auth](../backend/app/domains/auth/), [scripts](../scripts/) |
| Verification | Ruff, mypy, pytest, Alembic drift, TypeScript/ESLint, Vitest, Playwright; [checks](../scripts/run_checks.ps1), [browser tests](../frontend/e2e/) |

Generated [OpenAPI](schemas/openapi.json) and [assignment JSON Schema](schemas/config_v1.schema.json) describe interfaces; source models own their shape.

## Hierarchy and administration
 
**Course → modules → assignments**, alongside **course → sections**. Assignments are course-owned; sections scope official runs and staff grants. Admins manage courses/sections, staff roles/grants and monitoring. Course-scoped staff authorization is strictly enforced: instructors hold full read/write authority over assigned courses, IAs receive read-only setup access with 403 on mutations, and unassigned staff are denied access across courses, assignments, and artifacts. Section-scoped authority governs official runs.

Course defaults and module concepts inherit through the selected module; assignment denylists subtract concepts. Assignment configuration/history and instructor artifacts persist. Published master-course versions, section adoption and update notices are planned work.

## Public sandbox

Students need no account. They discover active sandbox assignments, upload/create/edit/delete their own workspace files, download their files/ZIP, and submit the current bundle. Provided assignment material is read-only; workspace file renaming is supported with real-time validation, multi-pane tab sync, and required entrypoint checks.

Results include projected scores, stdout, test/assertion outcomes, expected/actual I/O, diffs and concept warnings. Session-bound results are transient (normally one hour); queued work can be canceled. There is no persistent student attempt history or server-generated sandbox export.

AI receives sanitized code and grounded failures, validates its complete response before streaming, and falls back when unavailable/invalid. It explains; it never changes grades or supplies solutions. Assignment markdown summaries are rendered for students in the problem overview, sanitized and truncated to 1,000 characters for AI prompts (`PROMPT_VERSION = "v7"`), and kept in sync with automated scoring requirements.

## Assignment setup and scoring

Staff use the wizard/artifact editors to configure bundles, automated/manual items and models, run preflight, and validate reference solutions. CS1410 has 17 packages; CS1400 uses `simple-python-functions`. Pygame combines headless tests with manual visual criteria.

Canonical `assignment_configs.config` includes bundle paths/globs, pytest/model/support artifacts, unified scoring items, concept policy, completion thresholds, dependencies and rubric groups; instructor-authored markdown/HTML instructions persist on `assignments.description`. Stable scoring keys map to `ag_<key>` markers; all tests sharing a key must pass for its points. Extra credit can exceed the base total; completion thresholds are separate. Database scoring rows are derived projections.

Student runs receive pytest/support assets, excluding model solutions. AST checks detect syntax, blocked constructs and concept policy; pytest determines correctness. [Authoring](guides/assignments.md) links models, examples and helpers.

## Official grading and review

Staff select a granted section and upload a Canvas ZIP. Safe extraction groups student files, normalizes Canvas/version suffixes, reports unmatched files and resolves collisions by keeping the larger file. Runs snapshot grading setup/artifacts/manual criteria.

Review provides counters, cohort histogram/filters, read-only files, isolated HTML previews, manual scores and item/overall comments. Every manual item must be completed before export. Outputs are a Canvas-grade CSV and per-student HTML `feedback.zip`; comments appear in HTML. Staff import/distribute these manually. There is no Canvas write-back or official AI.

## Scheduling, status and limits

Durable tickets, checkpoints and ownership leases support bounded admission, fairness, restart recovery and duplicate avoidance. Status exposes `queue`, `run`, `complete`, `failure`, counts and coarse errors. Admin monitoring covers capacity, aggregate usage and dispatcher/cleanup failures.

| Default | Limit |
| --- | --- |
| Bundle | 50MiB; 100 files |
| Official intake | 200 submissions/upload; 1,000 unfinished host-wide |
| Waiting executions | Warn at 40; cap 50. Full capacity rejects new sandbox intake; valid official batches may remain retained |
| Active executions | 2; higher concurrency needs host measurements |
| Judge0 | 30-second grading timeout, 256MiB memory target, student networking disabled |
| Sandbox quota | Compose: 5 uploads/hour/session; bare Python defaults differ |

The target is 50 active users with queued grading. Deployment is single-host with reconciliation/restarts, not automatic host failover. Cloud/load balancing and additional languages remain future work.

## Staff identity, administration and access
 
Entra verifies university identity; active staff provisioning/grants supply authority. Backend checks tenant/issuer/audience, binds Azure OID, and issues JWTs. JWT and UI inactivity defaults are 60 minutes, with sliding token refresh (`x-refresh-token`), cross-tab session tracking (`useSyncExternalStore`), and sign-in redirects. Production/Microsoft mode disables mock login and rejects default secrets. Nginx enforces longest-prefix routing (`/api/auth/microsoft/`) directly to Next.js (`127.0.0.1:3000`) ahead of general `/api/` routing to FastAPI (`127.0.0.1:8000`), while internal services operate under strict loopback isolation (`127.0.0.1`).
 
Routes are grouped under `/sandbox`, `/staff/login`, `/staff/courses` and `/staff/admin`. Section authorization precedes expired-run responses. Process-wide audit logging scrubs PII and exception tracebacks across all framework loggers, emitting structured `"auth.access_denied"` records on 401/403 events. [Considerations](considerations.md) owns privacy/retention; [Running](running.md) owns access/testing.
