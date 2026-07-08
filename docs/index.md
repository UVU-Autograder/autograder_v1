# Documentation Index

> [!NOTE]
> **Purpose:** Table of contents and quick-reference index for specifications, compliance logs, schemas, and implementation guides.

---

## 🏛️ High-Level Specs & Compliance
* **[technical_specs.md](./technical_specs.md):** System architecture, stack definitions (FastAPI, Next.js, Celery, Postgres, Judge0, Kata), and core features.
* **[ferpa_analysis.md](./ferpa_analysis.md):** Privacy and compliance analysis for zero-retention student sandboxing.

## 🚀 Deployment Guides (`docs/deployment/`)
* **[ubuntu_poc_deployment.md](./deployment/ubuntu_poc_deployment.md):** Step-by-step local POC setup on Ubuntu 24.x for hypervisors and runners.
* **[kata_optimization.md](./deployment/kata_optimization.md):** Low-latency tuning strategies (Hugepages, CPU pinning, microVMs) for Kata Containers backing Judge0.

## ⚙️ Backend Specifications (`docs/backend_implementation/`)
* **[decisions.md](./backend_implementation/decisions.md):** In-depth FastAPI router splits, database locks, and AST checker paradigms.
* **[storage_and_test_plan.md](./backend_implementation/storage_and_test_plan.md):** Zero-retention validation rules and Celery task execution assertions.

## 🎨 Frontend Specifications (`docs/frontend_implementation/`)
* **[frontend_implementation.md](./frontend_implementation/frontend_implementation.md):** Next.js route maps, components, and Monaco Editor integration constraints.
* **[figma_prototype.md](./frontend_implementation/figma_prototype.md):** Prototype layouts and flow states.

## 📋 Planning & Backlog (`docs/planning/`)
* **[backlog.md](./planning/backlog.md):** Delivery milestone roadmap and sprint checklist.
* **[delivery_controls.md](./planning/delivery_controls.md):** Quality standards and acceptance rules.
