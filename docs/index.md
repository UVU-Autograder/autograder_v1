# Documentation Index

> [!NOTE]
> **Purpose:** Table of contents and quick-reference index for specifications, compliance logs, schemas, and implementation guides.

---

## High-Level Specs & Compliance
* **[technical_specs.md](./technical_specs.md):** System architecture, stack definitions (FastAPI, Next.js, Celery, Postgres, Judge0, Kata), and core features.
* **[ferpa_analysis.md](./ferpa_analysis.md):** Privacy and compliance analysis for retention-aware sandboxing and official runs.

## Deployment Guides (`docs/deployment/`)
* **[ubuntu_poc_deployment.md](./deployment/ubuntu_poc_deployment.md):** Step-by-step local POC setup on Ubuntu 24.x for hypervisors and runners.
* **[kata_optimization.md](./deployment/kata_optimization.md):** Low-latency tuning strategies (Hugepages, CPU pinning, microVMs) for Kata Containers backing Judge0.

## Backend Specifications (`docs/backend_implementation/`)
* **[decisions.md](./backend_implementation/decisions.md):** Product and implementation decisions.
* **[storage_and_test_plan.md](./backend_implementation/storage_and_test_plan.md):** Assignment config, artifacts, pytest scoring, and retention cleanup.
* **[pygame_grading_guidelines.md](./backend_implementation/pygame_grading_guidelines.md):** Headless execution, event mocking, and manual grading strategy for Pygame coursework.
* **Seed packages:** Built-in assignment fixtures live under [`backend/app/db/seeds/`](../backend/app/db/seeds/) (`seed://` resolution).

## Frontend Specifications (`docs/frontend_implementation/`)
* **[frontend_implementation.md](./frontend_implementation/frontend_implementation.md):** Next.js route maps, components, and Monaco Editor integration constraints. Mockup: https://autograder-frontend-mockup.vercel.app/
* **[figma_prototype.md](./frontend_implementation/figma_prototype.md):** Prototype layouts and flow states.

## Planning & Backlog (`docs/planning/`)
* **[cs1410_assignments_spec.md](./planning/cs1410_assignments_spec.md):** Complete class structures, required files, grading rubrics, and autograding strategies for all 17 CS 1410 assignments.
* **[backlog.md](./planning/backlog.md):** Active development backlog (product, platform gaps, ops/validation, deferred).
* **[delivery_controls.md](./planning/delivery_controls.md):** Definition of Done and acceptance gates.
* **Meeting minutes (historical):** [05_28_meeting.md](./planning/meetings_minutes/05_28_meeting.md), [06_04_meeting.md](./planning/meetings_minutes/06_04_meeting.md)
