# UVU Autograder — Active Development Backlog

> Product goal: on-prem zero-retention Python grading with a public student sandbox, staff assignment setup, and official Canvas ZIP runs.
> Initial delivery is complete. This file is the living implementation backlog for active development.

## Source Of Truth

- [decisions.md](../backend_implementation/decisions.md) — product and policy decisions
- [storage_and_test_plan.md](../backend_implementation/storage_and_test_plan.md) — assignment config, artifacts, pytest scoring
- [technical_specs.md](../technical_specs.md) — runtime contracts and system behavior
- [frontend_implementation.md](../frontend_implementation/frontend_implementation.md) — routes and UI contracts
- [delivery_controls.md](delivery_controls.md) — Definition of Done and acceptance gates

When a checklist item repeats a policy or runtime rule, treat the linked canonical document as authoritative and update that document first.

## Operating Guidelines

- Prefer completing fewer end-to-end deliverables over starting many disconnected tasks.
- Do not mark workstation / Kata / capacity items complete without Dell-workstation evidence (access still pending).
- Do not reintroduce purged topics without a new product decision.
- Reduce scope before weakening zero-retention, FERPA, authentication, or cleanup safeguards.

---

## Active — Product

### Manual grading (in progress)

- [ ] Complete staff official-review manual rubric scoring and comments end to end.
- [ ] Ensure regenerated Canvas-grade CSV and feedback ZIP reflect manual scores.
- [ ] Document and harden the boundary between auto test results (ground truth) and manual rubric items.

### Official review UX

- [ ] Per-student feedback preview before export (keep scope **broad** — exact UX still undecided).
- [ ] Ephemeral read-only Monaco previews for official submissions while temporary files remain (≤24h or until cleanup).
- [ ] Filtering by success, warning, hard-block, timeout, and parse failure (or equivalent coarse categories).

### Sandbox Local LLM (in development)

- [ ] Wire Local LLM for **sandbox** runs only.
- [ ] Send submission source (+ grounded test/AST context) only when the payload is **not personally traceable** (no student PII/identifiers).
- [ ] Inject allowed-concepts context into the prompt.
- [ ] Generate rubric-context explanations without re-grading correctness (hallucination guard: tests remain ground truth).
- [ ] Degrade under high load: grounded test results first; delay/skip/mark AI unavailable as needed.
- [ ] Show auto-populated LLM feedback beside sandbox test results.
- [ ] Log Local LLM token usage in non-sensitive run metadata.
- [ ] Rotate/purge any temporary sensitive debug traces within 24h if enabled.

### Expected I/O extraction and visual diff

- [ ] Backend AST parsing of pytest files for convention-based expected inputs/outputs (e.g. `EXPECTED_INPUT` / `EXPECTED_OUTPUT`).
- [ ] Expose extracted expected fields in the sandbox run results API.
- [ ] Wire sandbox visual diff to real expected vs actual output (custom `VisualDiffViewer` already exists; do not require `react-diff-viewer`).
- [ ] Expose parsed expected inputs/outputs next to test items in the instructor assignment setup rubric panel.

### Session / auth hardening

- [x] Client-side 5-minute inactivity logout for staff (mouse/keyboard/scroll).
- [ ] Align JWT token lifespan with the 5-minute inactivity window.
- [ ] Enable sliding JWT expiration refreshed on request activity.

---

## Active — Correctness / platform gaps

Documented policy vs current code — these are intentional fix items:

- [ ] **Section-scoped staff authorization** — enforce course/section grants on official ingest and run routes (today many routes only check `require_staff`).
- [ ] **Queue admission** — implement global waiting-job warn-at-`40` / reject-at-`50`, plus fair official/sandbox scheduling into the execution-slot cap (today official ingest has no admission gate).
- [ ] **Preflight before student grading** — run strict config/artifact/`ag_<key>` preflight for sandbox and official student pipelines (today only model-solution validation calls it).
- [ ] **Unify effective Concepts Covered** — course defaults + assignment additions only for **both** sandbox and official (today sandbox also merges module concepts).
- [ ] **Official run status** — return real sanitized counters, queue position, and ETA band for official runs (today numeric official status is largely Postgres zeros).

---

## Active — Ops and workstation validation

Waiting on real Dell workstation access. Do not mark complete without host evidence.

- [ ] Official run with a realistic class-size dataset (30–50 submissions).
- [ ] Validate ~200 official submissions complete within ~40 min on the Dell workstation.
- [ ] Validate export packaging overhead under ~2 min for ~200 submissions after grading completes.
- [ ] Validate Kata-backed VM isolation is active in the planned execution environment.
- [ ] Smoke test on the Dell-workstation deployment.
- [ ] Review deployment configuration.
- [ ] Update README with deployment and operating notes.
- [ ] Record a demo walkthrough.

---

## Current product (done — do not reopen as tasks)

Present-tense capabilities of the shipped initial delivery (non-exhaustive):

- Local stack: FastAPI, Next.js, Postgres, Redis/Celery path, Judge0 integration, Compose harness.
- Staff mock JWT login (`@uvu.edu`); role model admin / instructor / IA; public sandbox.
- Assignment wizard + app-owned `config_json`; artifacts (pytest / model solution / support); Concepts Covered.
- Canvas ZIP ingest via thin router + `ingest_official_canvas_zip`; grading via `run_grading_pipeline` + `execute_pytest_in_judge0`.
- Official exports: Canvas-grade CSV + per-student feedback ZIP; ephemeral official workspaces ≤24h or until staff cleanup.
- Sandbox ZIP upload, quota, preview, grounded results, zero-retention messaging.
- Client 5-minute staff inactivity logout.
- Frontend mockup on Vercel: https://autograder-frontend-mockup.vercel.app/

Judge0 default CPU time limit in settings is **30s** (256MB memory; network-disabled student execution). Execution-slot cap remains `2` until Dell benchmarks approve otherwise.

---

## Deferred (not active — ask before starting)

- [ ] Staff Microsoft OAuth through NextAuth (mock JWT remains current).
- [ ] Canvas automated feedback upload / distribution (manual Canvas grade CSV import remains assumed).
- [ ] Multi-language or compiled-language execution pipelines beyond current Python Judge0 path.
- [ ] Local LLM on official runs or other non-sandbox surfaces.
