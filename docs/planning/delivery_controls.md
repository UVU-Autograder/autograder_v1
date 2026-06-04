# UVU Autograder v1 - Delivery Controls

This file defines static acceptance gates for completing the M1 checklist. Product decisions live in [decisions.md](../backend_implementation/decisions.md), runtime contracts live in [technical_specs.md](../technical_specs.md), frontend contracts live in [frontend_implementation.md](../frontend_implementation/frontend_implementation.md), and M1 deliverables live in [backlog.md](backlog.md).

## Definition of Done

A checklist item is complete when:

- [ ] feature works end to end, not just in isolation
- [ ] reviewed in a pull request by at least one teammate
- [ ] no TypeScript or Python type errors on CI
- [ ] Ruff and ESLint pass
- [ ] at least one unit or integration test covers the happy path
- [ ] risk-based tests cover high-risk paths for the feature: unit, integration, cleanup, FERPA/privacy, or stress coverage as appropriate
- [ ] edge cases handled: bad input, malformed ZIP, unsafe ZIP path, missing required bundle file, ambiguous entrypoint, unmatched filename, non-UVU login, timeout, cleanup failure, sandbox exit cleanup
- [ ] no hardcoded secrets or environment-specific values
- [ ] docs updated if setup or behavior changed
- [ ] zero-retention cleanup is verified for any item that touches student code or student-facing grading artifacts
- [ ] cleanup-touching work includes automated cleanup test evidence and Dell-workstation spot-check evidence
- [ ] multi-file official and sandbox behavior is covered when the item touches ZIP/project bundle intake, validation, preview, or grading

## Risk-Based Testing Matrix

Use this matrix to decide the minimum test shape for M1 work:

| Area | Required coverage |
| --- | --- |
| Upload and parsing | Unit tests for ZIP safety, malformed archives, assignment-config bundle validation, and identifier mapping |
| Grading execution | Integration tests for AST checks, Judge0/Kata execution, timeout handling, and cleanup |
| Student sandbox | End-to-end test for public assignment selection, ZIP/project bundle upload, quota state, results, preview, and cleanup |
| Official runs | End-to-end test for Canvas ZIP ingest, multi-file submission bundles, run status, preview, exports, and cleanup |
| Compliance-sensitive paths | Regression checks that persistent storage and logs do not contain student code, identifiers, filenames, tracebacks, or detailed feedback |
| Stress and capacity | Dell-workstation validation for current M1 service targets and documented worker caps |

## Launch-Blocking Signoff Gates

- Cleanup proof must show Judge0 deletion, non-retrievability after deletion, ephemeral workspace removal, and Kata execution-state cleanup through automated tests plus a sanitized Dell-workstation spot-check log.
- Cleanup spot-check notes should be brief and dated: reviewer, app commit, synthetic workload, Judge0 deletion/non-retrievability result, workspace cleanup result, Kata runtime evidence, resource observations, and outcome. Do not include student code, filenames, identifiers, raw tracebacks, detailed outputs, raw Judge0 payloads, secrets, or auth tokens.
- Judge0 deletion must be enabled and verifiable before live official or live student-derived workflows are allowed.
- Capacity-sensitive work must respect the approved M1 cap of `2` concurrent Judge0/Kata execution slots unless stability-first benchmark evidence approves a higher cap.
- Benchmark evidence must use mixed synthetic workloads and pass cleanup, no-crash, queue/backpressure, and service-target checks before a cap of `3` or `4` is approved.
- Live-code Azure feedback must remain disabled until written UVU approval and Azure resource/privacy confirmation are complete.
- M1 validation must use only fake/synthetic data or completely anonymized data with no retained re-identification map.
- Canvas ZIP ingest and grade CSV export are dependable M1 workflows only after the synthetic fixture and completely anonymized sample validation matrix passes.

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
- any M1 plagiarism checker implementation or external plagiarism-report workflow
- loose multi-file drag-and-drop upload outside the ZIP/project bundle contract
- in-browser code editing or IDE behavior beyond read-only Monaco preview
- PDF feedback generation
- multi-language support beyond Python
- analytics or class-wide reporting
