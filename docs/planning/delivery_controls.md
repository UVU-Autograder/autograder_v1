# UVU Autograder — Delivery Controls

This file defines acceptance gates for active development. Product decisions live in [decisions.md](../backend_implementation/decisions.md), runtime contracts in [technical_specs.md](../technical_specs.md), frontend contracts in [frontend_implementation.md](../frontend_implementation/frontend_implementation.md), and the living backlog in [backlog.md](backlog.md).

## Definition of Done

A checklist item is complete when:

- [ ] feature works end to end, not just in isolation
- [ ] reviewed in a pull request by at least one teammate
- [ ] no TypeScript or Python type errors on CI
- [ ] Ruff and ESLint pass
- [ ] at least one unit or integration test covers the happy path
- [ ] risk-based tests cover high-risk paths for the feature: unit, integration, cleanup, FERPA/privacy, or stress coverage as appropriate
- [ ] edge cases handled where relevant: bad input, malformed ZIP, unsafe ZIP path, missing required bundle file, ambiguous entrypoint, unmatched filename, non-UVU login, timeout, cleanup failure, sandbox exit cleanup
- [ ] no hardcoded secrets or environment-specific values
- [ ] docs updated if setup or behavior changed
- [ ] zero-retention / retention-window cleanup is verified for any item that touches student code or student-facing grading artifacts
- [ ] cleanup-touching work includes automated cleanup test evidence; Dell-workstation spot-check evidence when the change affects on-prem execution
- [ ] multi-file official and sandbox behavior is covered when the item touches ZIP/project bundle intake, validation, preview, or grading

## Risk-Based Testing Matrix

| Area                       | Required coverage                                                                                                                        |
| -------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| Upload and parsing         | Unit tests for ZIP safety, malformed archives, assignment-config bundle validation, and identifier mapping                               |
| Grading execution          | Integration tests for AST checks, Judge0/Kata execution, timeout handling, and cleanup                                                   |
| Student sandbox            | End-to-end test for public assignment selection, ZIP/project bundle upload, quota state, results, preview, and cleanup                   |
| Official runs              | End-to-end test for Canvas ZIP ingest, multi-file submission bundles, run status, preview, exports, and cleanup                          |
| Compliance-sensitive paths | Regression checks that persistent storage and logs do not contain student code, identifiers, filenames, tracebacks, or detailed feedback |
| Stress and capacity        | Dell-workstation validation for service targets, worker caps, queue admission at `40`/`50`, and AI degradation under load                |

## Launch-Blocking Signoff Gates

- Cleanup proof must show Judge0 deletion, non-retrievability after deletion, ephemeral workspace removal, and Kata execution-state cleanup through automated tests plus a sanitized Dell-workstation spot-check log (when Dell access is available).
- Cleanup spot-check notes should be brief and dated: reviewer, app commit, synthetic workload, Judge0 deletion/non-retrievability result, workspace cleanup result, Kata runtime evidence, resource observations, and outcome. Do not include student code, filenames, identifiers, raw tracebacks, detailed outputs, raw Judge0 payloads, secrets, or auth tokens.
- Judge0 deletion must be enabled and verifiable before live official or live student-derived workflows are allowed.
- Capacity-sensitive work must respect the approved cap of `2` concurrent Judge0/Kata execution slots unless stability-first benchmark evidence approves a higher cap.
- Benchmark evidence must use mixed synthetic workloads and pass cleanup, no-crash, queue/backpressure, and service-target checks before a cap of `3` or `4` is approved.
- The intended global waiting execution queue rejects new intake at `50` queued jobs, warns at `40`, and preserves the approved execution-slot cap (implementation is an active backlog item).
- Do not approve `8` concurrent Judge0/Kata execution slots from RAM estimates alone.
- Sandbox Local LLM may process student **code** only when the payload is not personally traceable (no student PII/identifiers). Official-run AI is deferred.
- Prefer fake/synthetic or completely anonymized validation data until institutional live-data posture is confirmed for a given workflow.
- Canvas ZIP ingest and grade CSV export are dependable for live courses only after synthetic fixture validation and Dell-host confidence.

## Current product boundaries

In scope for active development (see backlog):

- Manual grading on official review (in progress)
- Sandbox Local LLM (PII-safe; sandbox only)
- Official review UX improvements (preview, Monaco, filtering)
- Platform gap fixes (section auth, queue admission, preflight, concepts unify, run status)
- Dell workstation validation

Explicitly not in the living product plan (do not pull in without a new decision):

- Canvas LTI or grade passback API integration
- Automated Canvas feedback attachment, upload, or distribution (deferred note only)
- Persistent student history, saved projected runs, or resubmission timelines
- Downloadable student sandbox artifacts
- LLM-assisted PDF/text rubric conversion or AI-assisted test generation
- Inline in-editor LLM annotation markers for Monaco
- Loose multi-file drag-and-drop outside the ZIP/project bundle contract
- PDF feedback generation
- Analytics or class-wide reporting
- Responsive design for mobile devices as a launch requirement
