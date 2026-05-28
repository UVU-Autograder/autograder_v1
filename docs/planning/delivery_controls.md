# UVU Autograder v1 - Delivery Controls

This file defines static delivery controls for completing the M1 checklist. Product decisions live in [decisions.md](../backend_implementation/decisions.md), runtime contracts live in [technical_specs.md](../technical_specs.md), frontend contracts live in [frontend_implementation.md](../frontend_implementation/frontend_implementation.md), and M1 deliverables live in [backlog.md](backlog.md).

## Review Cadence

- Review [backlog.md](backlog.md) weekly against actual student availability.
- Keep assigned work small enough for a student developer to complete in a focused day when possible.
- Reassign work when exams, jobs, vacations, illness, or specialist bottlenecks reduce capacity.
- Prefer completing fewer end-to-end deliverables over starting many disconnected tasks.
- Reduce scope before weakening zero-retention, FERPA, authentication, authorization, or cleanup safeguards.

## Definition of Done

A checklist item is complete when:

- [ ] feature works end to end, not just in isolation
- [ ] reviewed in a pull request by at least one teammate
- [ ] no TypeScript or Python type errors on CI
- [ ] Ruff and ESLint pass
- [ ] at least one unit or integration test covers the happy path
- [ ] edge cases handled: bad input, malformed ZIP, unmatched filename, non-UVU login, timeout, cleanup failure, sandbox exit cleanup
- [ ] no hardcoded secrets or environment-specific values
- [ ] docs updated if setup or behavior changed
- [ ] zero-retention cleanup is verified for any item that touches student code or student-facing grading artifacts

## Hard Scope Boundaries - M1

These are explicitly out of scope for M1. Do not pull them in under deadline pressure:

- official university SSO integration beyond staff Microsoft OAuth + `@uvu.edu` domain restriction
- Canvas LTI or grade passback API integration
- automated Canvas feedback attachment, upload, or distribution
- manual or non-code grading workflows
- in-app grade override or feedback editing workflows for official review
- persistent student history, saved projected runs, or resubmission timelines
- downloadable student sandbox artifacts
- LLM-assisted PDF/text rubric conversion
- AI-assisted test generation
- inline in-editor LLM annotation markers for Monaco code review surfaces
- student plagiarism detection
- PDF feedback generation
- multi-language support beyond Python
- analytics or class-wide reporting
