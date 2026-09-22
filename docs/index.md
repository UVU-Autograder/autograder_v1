# Documentation Index

> [!NOTE]
> **Purpose:** Central navigation hub and table of contents for specifications, compliance analyses, implementation guides, deployment procedures, schemas, and course modeling.

Current milestone: **controlled course pilot readiness**. Start with the [active backlog](planning/backlog.md) for implementation gaps and the [delivery controls](planning/delivery_controls.md) for evidence labels and launch gates. Technical contracts state required behavior; implementation, test evidence, host verification, and institutional approval are tracked separately.

---

## 🏛️ Core Architecture & Governance (`docs/core/`)
* **[technical_specs.md](./core/technical_specs.md):** System architecture, technology stack (FastAPI, Next.js, Celery, Postgres, Judge0, Kata), data model, and execution contracts.
* **[decisions.md](./core/decisions.md):** Architectural, product, and implementation decision log with rationale.
* **[ferpa_analysis.md](./core/ferpa_analysis.md):** Privacy posture, compliance analysis, and institutional data governance for student sandboxing and official runs.

---

## 🛠️ Subsystem Specifications (`docs/implementation/`)
* **[frontend_implementation.md](./implementation/frontend_implementation.md):** Next.js route maps, information architecture, UI responsibilities, and Monaco Editor integration.
* **[storage_and_test_plan.md](./implementation/storage_and_test_plan.md):** Assignment configuration contracts, pytest scoring markers (`ag_<key>`), artifact storage abstractions, and retention lifecycles.

---

## 📐 Course & Assignment Modeling (`docs/modeling/`)
* **[cs1410_assignments_spec.md](./modeling/cs1410_assignments_spec.md):** Class structures, required files, grading rubrics, and autograding strategies for all 17 CS 1410 assignments.
* **[modeling_guide.md](./modeling/modeling_guide.md):** Authoring guidelines and best practices for modeling JSON configurations and test scripts.
* **[pygame_grading_guidelines.md](./modeling/pygame_grading_guidelines.md):** Headless execution, event/sys mocking, and manual grading strategy for Pygame coursework.

---

## 🚀 DevOps & Host Deployment (`docs/deployment/`)
* **[ubuntu_poc_deployment.md](./deployment/ubuntu_poc_deployment.md):** Local POC Docker Compose stack (Ubuntu/Dell target; laptop notes, Judge0 image build, single Postgres, capacity).
* **[kata_optimization.md](./deployment/kata_optimization.md):** Low-latency host tuning strategies (Hugepages, CPU pinning, microVMs) for Kata Containers backing Judge0.

---

## 📋 Planning & Backlog (`docs/planning/`)
* **[backlog.md](./planning/backlog.md):** Active development backlog (product features, platform gaps, ops/validation checklist, deferred items).
* **[delivery_controls.md](./planning/delivery_controls.md):** Definition of Done, verification standards, and release acceptance gates.

---

## 📄 Schemas & Artifacts (`docs/schemas/`)
* **[config_v1.schema.json](./schemas/config_v1.schema.json):** Canonical JSON Schema 2020-12 specification for app-owned assignment configurations (`config_json`).
* **[openapi.json](./schemas/openapi.json):** OpenAPI 3.0 specification for backend REST endpoints.
* **Seed packages:** Built-in assignment fixtures live under [`backend/app/db/seeds/`](../backend/app/db/seeds/) (`seed://` resolution).
