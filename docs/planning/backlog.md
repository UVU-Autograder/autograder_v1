# UVU Autograder — Active Development Backlog

> Product goal: on-prem zero-retention Python grading with a public student sandbox, staff assignment setup, and official Canvas ZIP runs.
> Initial delivery is complete. This file is the living implementation backlog for active development.

## Source of Truth

- [decisions.md](../core/decisions.md) — product and policy decisions
- [storage_and_test_plan.md](../implementation/storage_and_test_plan.md) — assignment config, artifacts, pytest scoring
- [technical_specs.md](../core/technical_specs.md) — runtime contracts and system behavior
- [frontend_implementation.md](../implementation/frontend_implementation.md) — routes and UI contracts
- [delivery_controls.md](delivery_controls.md) — Definition of Done and acceptance gates

When a checklist item repeats a policy or runtime rule, treat the linked canonical document as authoritative and update that document first.

## Operating Guidelines

Refer to [delivery_controls.md](delivery_controls.md) for Definition of Done (DoD), verification standards, and zero-retention / FERPA acceptance gates. Refer to [.agents/memory/context.md](../../.agents/memory/context.md) for operational domain vocabulary. Do not reintroduce purged topics without a new product decision.

---

## Active — Product

## Active — Ops and workstation validation

Validated on Dell Pro Max Tower T2 (Intel Core Ultra 7 265, 32GB RAM, RTX PRO 4500 GPU, Ubuntu 24.04 LTS, IP `10.115.20.200`).

- [x] Official run with a realistic class-size dataset (30–50 submissions).
  - *Evidence:* Executed Run 1 with 35 synthetic submissions on `cs1400/simple-python-functions`; all 35 scored and individual HTML feedback packages generated.
- [x] Validate ~200 official submissions complete within ~40 min on the Dell workstation.
  - *Evidence:* 35 submissions completed in 76.2s (~2.17s / submission); projected 200 submissions duration is ~7.2 min, well below the 40-minute limit.
- [x] Validate export packaging overhead under ~2 min for ~200 submissions after grading completes.
  - *Evidence:* CSV grade export completed in 0.044s; feedback ZIP packaging (35 HTML files) completed in 0.089s.
- [x] Validate Kata-backed VM isolation is active in the planned execution environment.
  - *Evidence:* Kata 3.x `containerd-shim-kata-v2` registered in Docker daemon, executed Judge0 workers with non-privileged capability scoping (`privileged: false` + `SYS_ADMIN`, `SYS_RESOURCE`, etc.), verified active shims during grading.
- [x] Validate on-prem local LLM serving (Ollama/vLLM) on the Dell workstation.
  - *Evidence:* Ollama active via systemd serving `qwen2.5-coder:7b` on RTX PRO 4500 Blackwell GPU with 0.37s–0.93s latency per request.
- [x] Smoke test on the Dell-workstation deployment.
  - *Evidence:* Next.js frontend serving on `http://10.115.20.200:3000` via `autograder-frontend.service`; FastAPI backend serving on `http://10.115.20.200:8000/health`; CORS headers verified across LAN; mock login authenticating `dev.staff@uvu.edu`.
- [x] Review deployment configuration.
  - *Evidence:* Reconciled `docker-compose.poc.yml` (`celery-beat`, `LOCAL_LLM_MODEL`, `CORS_ALLOWED_ORIGINS`), `docker-compose.kata.yml`, `package.json` (`docker:up:kata`), and deployment documentation.
- [x] Update README with deployment and operating notes.
  - *Evidence:* Added Kata run commands, service unit references, and workstation endpoints to `README.md`.

---

## Deferred (not active — ask before starting)

- [ ] Configuration Schema Versioning & Migration Pipeline (Deferred while in testing stage without active live assignments).
- [ ] Staff Microsoft OAuth through NextAuth (mock JWT remains current).
- [ ] Canvas automated feedback upload / distribution (manual Canvas grade CSV import remains assumed).
- [ ] Multi-language or compiled-language execution pipelines beyond current Python Judge0 path.
- [ ] Official-run Local LLM feedback (deferred; planned shape when unblocked):
  - **Entry:** opt-in checkbox on the Official Runs start/upload page only (per new run).
  - **Timing:** generate during grading, after each student’s tests, and bake into that student’s feedback HTML.
  - **Posture:** POC-style like sandbox AI — staff opt-in, strip identifiers where possible; keep behind institutional approval / FERPA gates before enabling by default.
  - **HTML shape:** separate “AI coaching” section alongside the existing score/test report (never replaces pytest truth).
  - generated comments must remain editable HTML-only drafts;
  - deterministically remove names, Canvas/submission identifiers, identifying paths, and identifiers in source comments/string literals;
  - use run-local pseudonyms only and skip feedback when anonymization confidence is insufficient;
  - prove with tests that raw identifiers never reach the Local LLM client.
- [ ] CS 1400 modeling: We do not yet have access to official course data.
