# UVU Autograder v1 - Implementation Questions

This file tracks only active, unresolved implementation questions that cut across multiple parts of the system.

Resolved decisions should be moved out of this file and into:

- `docs/backend_implementation/decisions.md` for product or policy decisions
- `docs/technical_specs.md` for behavior or contract details
- `docs/planning/delivery_controls.md` for Definition of Done, hard scope boundaries, and delivery controls
- `docs/planning/backlog.md` for story, backlog, or delivery-checklist work

Do not keep resolved discussion history here.
Do not add routine implementation chores here unless they still require a real team decision.

## Current Open Questions

### 1. Judge0 cleanup proof standard

What exact evidence or test procedure counts as sufficient proof that Judge0 submission/result artifacts and Kata execution state are truly destroyed after retrieval?

Why this is still open:

- we have decided that cleanup must happen immediately after verification and retrieval
- we have decided that Judge0 cleanup includes `DELETE /submissions/{token}` immediately after result retrieval and that raw Judge0 records are not mirrored into app-owned persistent storage
- we have not yet defined the exact proof standard that counts as "verified" for implementation signoff or go-live readiness

Resolution destination:
`docs/planning/backlog.md` for the proof-standard task, `docs/planning/delivery_controls.md` if the Definition of Done changes, and `technical_specs.md` if cleanup verification becomes part of the documented runtime contract

### 2. Dell workstation concurrency policy

What is the approved safe concurrency and worker-cap policy for the Dell workstation under peak load?

Provisional recommendation based on the current Dell workstation specs:

- treat RAM, host OS overhead, Docker overhead, and Kata VM overhead as the limiting factors rather than raw CPU core count
- ignore the GPU for M1 concurrency planning; it does not materially change the Judge0 + Kata execution budget
- start with a conservative execution cap of `2` concurrent Judge0 + Kata grading jobs on this machine
- treat `3` as the first benchmark target and `4` as the highest cap worth testing before go-live
- do not approve anything above `4` concurrent Judge0 + Kata jobs on this `32GB` workstation unless sustained benchmarking shows comfortable memory headroom and stable cleanup behavior
- keep queueing and backpressure enabled for all work beyond the approved execution cap
- document the final policy separately for:
  - execution-slot cap for Judge0 + Kata jobs
  - Celery worker concurrency for grading tasks
  - queue/backpressure thresholds when memory pressure rises

Why this recommendation makes sense:

- the machine has strong CPU headroom, but only `32GB` RAM for Windows, Docker, Judge0, Kata, Postgres, Redis, FastAPI, Next.js, and Celery combined
- Judge0's configured per-run memory limit does not capture the full Kata/container/runtime overhead on the host
- Easton's concern about memory bottlenecks during peak semester load is consistent with this hardware profile
- a low initial cap reduces the risk of thrashing or degraded cleanup behavior while the real benchmark data is gathered

Why this is still open:

- the docs say execution capacity is memory-bound
- the current hardware profile supports a conservative provisional recommendation of `2` concurrent jobs, with `3-4` as the benchmark range to validate
- the exact worker caps, queueing policy, and backpressure thresholds are still not documented as an approved operating rule

Resolution destination:
`decisions.md` for the operating-policy decision, and `docs/planning/backlog.md` for the required benchmarking and validation work

### 3. Azure and UVU compliance confirmation checklist

What exact Azure/UVU compliance confirmations are required before live student code can be sent to Azure OpenAI?

Why this is still open:

- the docs require privacy/ZDR and FERPA-related confirmation before live use
- the exact confirmation checklist, evidence, and approver expectations are not yet written down in one place

Resolution destination:
`decisions.md` for the approval requirements, and `docs/planning/backlog.md` for the confirmation tasks that must be completed before go-live

### 4. Real Canvas format validation target

What real Canvas export/import formats must we validate against before we can treat ZIP parsing and grade CSV re-import as dependable M1 workflows?

Why this is still open:

- the docs describe expected ZIP parsing rules and CSV export shape
- we still have not defined the exact real-world Canvas samples or format variants that must be tested before we treat those workflows as dependable

Resolution destination:
`technical_specs.md` for any finalized format/behavior rules, and `docs/planning/backlog.md` for the concrete validation matrix and acceptance tests

## Removal Rule

Remove a question from this file as soon as the team resolves it and the final wording has been moved into the appropriate backend doc.
