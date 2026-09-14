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

Waiting on real Dell workstation access. Do not mark complete without host evidence.

- [ ] Official run with a realistic class-size dataset (30–50 submissions).
- [ ] Validate ~200 official submissions complete within ~40 min on the Dell workstation.
- [ ] Validate export packaging overhead under ~2 min for ~200 submissions after grading completes.
- [ ] Validate Kata-backed VM isolation is active in the planned execution environment.
- [ ] Validate on-prem local LLM serving (Ollama/vLLM) on the Dell workstation.
- [ ] Smoke test on the Dell-workstation deployment.
- [ ] Review deployment configuration.
- [ ] Update README with deployment and operating notes.

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
