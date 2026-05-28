# UVU Autograder v1 - Product Backlog

This file tracks M1 epics, stories, point estimates, and priorities. Sprint execution details live in [sprint_plan.md](sprint_plan.md).

1 story point ~= 2-4 hours focused work.
Priority: **Must** = M1 required · **Should** = M1 if capacity · **Won't** = post-M1

## Epic 0 - Architecture and Design (Sprint 0)

| ID    | Story                                                                 | Pts | Priority |
| ----- | --------------------------------------------------------------------- | --- | -------- |
| E0-01 | ER and class diagrams reviewed as current architecture references     | 2   | Must     |
| E0-02 | FastAPI router skeleton and prompt-boundary plan reviewed             | 2   | Must     |
| E0-03 | Staff and sandbox wireframes reviewed with shared interface contracts | 3   | Must     |
| E0-04 | Route structure and component hierarchy reviewed before Sprint 1      | 2   | Must     |
| E0-05 | Implementation action items captured for Sprint 0 signoff             | 1   | Must     |

**Epic 0 total: 10 points**

---

## Epic 1 - Environment and Infrastructure (Sprint 0)

| ID    | Story                                                                                                                                                  | Pts | Priority |
| ----- | ------------------------------------------------------------------------------------------------------------------------------------------------------ | --- | -------- |
| E1-01 | Docker Compose for local development and integration-style testing: postgres, redis, celery, fastapi, nextjs, and Judge0-compatible execution topology | 2   | Must     |
| E1-02 | FastAPI project structure with routers, schemas, services, and prompt boundaries                                                                       | 2   | Must     |
| E1-03 | Next.js project structure with App Router                                                                                                              | 2   | Must     |
| E1-04 | PostgreSQL schema + Alembic initial migration for metadata-only tables                                                                                 | 2   | Must     |
| E1-05 | Celery + Redis wiring                                                                                                                                  | 1   | Must     |
| E1-06 | Judge0 execution service reachable with documented auth, Kata isolation, and deletion strategy                                                         | 3   | Must     |
| E1-07 | Dell-workstation deployment topology documented for production services                                                                                | 1   | Must     |
| E1-08 | Monaco locally hosted in the frontend scaffold for planned M1 editor and review workflows                                                              | 2   | Must     |
| E1-09 | `.env.example`, README, CI checks                                                                                                                      | 2   | Must     |

**Epic 1 total: 17 points**

---

## Epic 2 - Auth and Identity (Sprint 1)

| ID    | Story                                                                     | Pts | Priority |
| ----- | ------------------------------------------------------------------------- | --- | -------- |
| E2-01 | Staff NextAuth Microsoft OAuth provider                                   | 2   | Must     |
| E2-02 | Staff callback rejects non-`@uvu.edu` logins                              | 1   | Must     |
| E2-03 | Role-based route protection for admin, instructor, IA, and student access | 3   | Must     |
| E2-04 | Role-based API protection                                                 | 2   | Must     |
| E2-05 | Admin manages staff roles and course access                               | 2   | Must     |
| E2-06 | Public student sandbox entry path without student authentication or persistent student profile storage | 2   | Must     |

**Epic 2 total: 12 points**

---

## Epic 3 - Assignment and Config Setup (Sprint 1)

| ID    | Story                                                                                             | Pts | Priority |
| ----- | ------------------------------------------------------------------------------------------------- | --- | -------- |
| E3-01 | Assignment creation form with course linkage and Canvas metadata                                  | 2   | Must     |
| E3-02 | Comprehensive wizard for instructor-relevant assignment/rubric/config fields                      | 3   | Must     |
| E3-03 | Wizard generates valid `config.json`                                                              | 2   | Must     |
| E3-04 | Validated `config.json` import UI                                                                 | 3   | Must     |
| E3-05 | Stored config form/view renders all instructor-relevant editable fields from the app-owned config | 3   | Must     |
| E3-06 | Current `config.json` is downloadable                                                             | 1   | Must     |
| E3-07 | Course defaults editor plus assignment concept-additions editor with merged preview               | 3   | Must     |

**Epic 3 total: 17 points**

---

## Epic 4 - Ephemeral Submission Ingestion (Sprint 1)

| ID    | Story                                                                         | Pts | Priority |
| ----- | ----------------------------------------------------------------------------- | --- | -------- |
| E4-01 | Canvas ZIP upload endpoint with size + type validation                        | 2   | Must     |
| E4-02 | Reject malformed or non-Canvas ZIPs before queueing                           | 2   | Must     |
| E4-03 | ZIP path traversal protection                                                 | 2   | Must     |
| E4-04 | Ephemeral extraction workflow in RAM or temp directory only                   | 2   | Must     |
| E4-05 | Filename parser for Canvas uploads using Canvas identifiers                   | 2   | Must     |
| E4-06 | Unmatched filename/malformed archive reporting                                | 2   | Must     |
| E4-07 | Transient official-run metadata record without persistent student submissions | 1   | Must     |

**Epic 4 total: 13 points**

---

## Epic 5 - Grading Pipeline and AI Enrichment (Sprint 2)

| ID    | Story                                                                                                                           | Pts | Priority |
| ----- | ------------------------------------------------------------------------------------------------------------------------------- | --- | -------- |
| E5-01 | AST checker for merged `Concepts Covered` whitelist enforcement                                                                 | 4   | Must     |
| E5-02 | Warning vs hard-block concept/security handling                                                                                 | 2   | Must     |
| E5-03 | Judge0 integration with Kata-backed isolation, resource limits, language mapping, structured statuses, and post-result deletion | 5   | Must     |
| E5-04 | pytest execution + output parsing + normalization                                                                               | 4   | Must     |
| E5-05 | Minimal pytest artifact management per assignment                                                                               | 3   | Must     |
| E5-06 | Keep test-to-rubric and student-visible metadata in the app-owned `config.json`, with derived `TestCase` projections when needed | 2   | Must     |
| E5-07 | Run model solution against assignment tests through Judge0                                                                      | 1   | Must     |
| E5-08 | Azure OpenAI integration with concept-context prompting and hallucination guard                                                 | 4   | Must     |
| E5-09 | Celery grading chain for official and sandbox runs                                                                              | 3   | Must     |
| E5-10 | Timeout, retry, and cleanup guarantees                                                                                          | 2   | Must     |
| E5-11 | Azure token usage logging in `run_summaries` or equivalent metadata storage                                                     | 2   | Must     |
| E5-12 | Celery worker concurrency aligned to Judge0 + Kata execution-capacity limits                                                    | 1   | Must     |

**Epic 5 total: 33 points**

---

## Epic 6 - Student Sandbox (Sprint 3)

| ID    | Story                                                                    | Pts | Priority |
| ----- | ------------------------------------------------------------------------ | --- | -------- |
| E6-01 | Student course and assignment selection UI                               | 2   | Must     |
| E6-02 | Student upload flow for projected grading                                | 3   | Must     |
| E6-03 | Sandbox rate limiter enforcing `5 uploads per hour` per sandbox session | 2   | Must     |
| E6-04 | On-screen projected score and feedback view                              | 3   | Must     |
| E6-05 | Student-facing warnings, quota messaging, and zero-retention messaging   | 2   | Must     |
| E6-06 | Session-exit and completion cleanup for sandbox results                  | 2   | Must     |
| E6-07 | Student route isolation from staff pages and export flows                | 2   | Must     |

**Epic 6 total: 16 points**

---

## Epic 7 - Instructor Batch Run UX (Sprint 3)

| ID    | Story                                                                  | Pts | Priority |
| ----- | ---------------------------------------------------------------------- | --- | -------- |
| E7-01 | Official run list with aggregate status and section-aware context      | 2   | Must     |
| E7-02 | In-session official-run detail view with counts, warnings, and failures | 2   | Must     |
| E7-03 | `GET /runs/{id}/status` live polling at `2s` cadence for per-run status | 1   | Must     |
| E7-04 | Per-student HTML preview before export                                 | 2   | Must     |
| E7-05 | Filtering for success, warning, hard-block, timeout, and parse failure | 1   | Should   |

**Epic 7 total: 8 points**

---

## Epic 8 - Export Packaging (Sprint 3)

| ID    | Story                                                                                         | Pts | Priority |
| ----- | --------------------------------------------------------------------------------------------- | --- | -------- |
| E8-01 | CSV export for Canvas-compatible grades                                                       | 2   | Must     |
| E8-02 | Per-student staff-facing feedback renderer                                                    | 2   | Must     |
| E8-03 | Feedback ZIP packaging builder for per-student HTML official-run artifacts                    | 2   | Must     |
| E8-04 | Separate CSV and feedback-ZIP download workflow with stable naming and actionable errors      | 1   | Must     |
| E8-05 | Graceful failure for malformed or unrecognized ZIP submissions                                | 2   | Must     |
| E8-06 | Documentation note: Canvas grade import assumed; automated feedback upload is out of scope for M1 | 1   | Must     |

**Epic 8 total: 10 points**

---

## Backlog Summary

| Epic      | Name                               | M1 Points      | Sprint |
| --------- | ---------------------------------- | -------------- | ------ |
| E0        | Architecture and Design            | 10             | S0     |
| E1        | Environment and Infrastructure     | 17             | S0     |
| E2        | Auth and Identity                  | 12             | S1     |
| E3        | Assignment and Config Setup        | 17             | S1     |
| E4        | Ephemeral Submission Ingestion     | 13             | S1     |
| E5        | Grading Pipeline and AI Enrichment | 33             | S2     |
| E6        | Student Sandbox                    | 16             | S3     |
| E7        | Instructor Batch Run UX            | 8              | S3     |
| E8        | Export Packaging                   | 10             | S3     |
| **Total** |                                    | **136 points** |        |
