# UVU Autograder v1 - Backlog Index

> Target: Testable M1 for zero-retention grading with staff `@uvu.edu` authentication and globally visible student sandbox access
> Team: 5 developers, half time (~35-65 hrs/week total)
> Window: 8-9 weeks
> Backlog tracked in: GitHub Projects (Issues + Milestones)
> Last updated: May 4, 2026

This file is the planning front door for the current Jaxon implementation track. Canonical product decisions, runtime behavior, and frontend surface contracts live in the linked source-of-truth docs rather than being duplicated here.

## Source Of Truth

- [decisions.md](../backend_implementation/jaxon_implementation/decisions.md) - product, policy, and M1 assumption decisions
- [technical_specs.md](../backend_implementation/jaxon_implementation/technical_specs.md) - backend/system behavior, data contracts, runtime limits, and deployment shape
- [frontend_implementation.md](../frontend_implementation/frontend_implementation.md) - routes, UI surfaces, and frontend constraints
- [sprint_plan.md](sprint_plan.md) - sprint goals, deliverables, deferrals, activities, and exit criteria
- [product_backlog.md](product_backlog.md) - epics, stories, priorities, and point totals
- [sprint_plan.md](sprint_plan.md#action-items) - action items, Definition of Done, and M1 scope boundaries

Supporting note: `docs/backend_implementation/easton_implementation/ClassFlow_diagram.md` remains an older working artifact. The current diagram set for implementation lives in `docs/backend_implementation/jaxon_implementation/diagrams/`.

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

## Capacity Reality Check

```text
Conservative (35 hrs/week, 8 weeks, 3 hrs/point): ~93 points
Optimistic   (65 hrs/week, 8 weeks, 3 hrs/point): ~173 points
With Sprint 4 buffer absorbed:                     ~185-195 points realistic
```

With the student sandbox restored to M1 and the operational hardening stories added, the backlog remains above the conservative delivery line but inside the realistic range for a 5-developer team. If priorities tighten:

- protect Epics 1-5 as the core shared platform and grading path
- protect the Must stories in Epic 6 before adding staff UX polish
- cut staff filtering polish before cutting zero-retention guarantees or config round-trip behavior
