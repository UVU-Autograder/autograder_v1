# UVU Autograder v1 - Overall Implementation Questions

This file is the shared discussion log for unresolved implementation questions that span frontend and backend work.

Resolved decisions belong in `docs/backend_implementation/jaxon_implementation/decisions.md`.

## Workflow and Product Questions

## 1. Staff downloadability of raw submissions

Should staff be able to download raw student submission files from the system, or should the product only expose derived exports and feedback artifacts?

**Jaxon:** We shouldn't need to download code submissions, unless you can think of a reason.

**Keomony:** I don't think we need this right now, but I keep getting confused about what data will be stored and what will not. I want Dominic and Vebjørn to weigh in first.

Current tension: this affects retention language, UI affordances, and whether official-run exports are purely derived artifacts or also a route back to raw student code.

## Infrastructure and Technical Questions

## 2. Canonical Judge0 deployment narrative

Where should Judge0 run in the canonical M1 deployment story?

Current drift:

- Some docs describe a Railway-first app stack with separate execution infrastructure.
- Earlier planning artifacts used a different hosting narrative around execution.

**Jaxon:** No opinion. Need to do more research.

Current tension: we have chosen Judge0 and Kata as the execution direction, but the exact M1 deployment narrative should not be treated as finalized until the team closes this question.

## 3. Judge0 artifact-deletion contract

What is the exact canonical zero-retention requirement for Judge0-side artifacts after result handling?

Current drift:

- Some docs say Judge0 submission/result artifacts must be deleted or invalidated immediately after retrieval.
- Other docs treat cleanup more generally without locking the exact service-side contract.

**Jaxon:** No strong opinion. Need to do more research.

Current tension: zero-retention is settled, but the exact wording and verification standard for Judge0-side cleanup still need to be finalized.
