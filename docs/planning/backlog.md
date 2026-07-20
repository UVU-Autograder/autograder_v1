# UVU Autograder — Active Development Backlog

> Product goal: on-prem zero-retention Python grading with a public student sandbox, staff assignment setup, and official Canvas ZIP runs.
> Initial delivery is complete. This file is the living implementation backlog for active development.

## Source Of Truth

- [decisions.md](../core/decisions.md) — product and policy decisions
- [storage_and_test_plan.md](../implementation/storage_and_test_plan.md) — assignment config, artifacts, pytest scoring
- [technical_specs.md](../core/technical_specs.md) — runtime contracts and system behavior
- [frontend_implementation.md](../implementation/frontend_implementation.md) — routes and UI contracts
- [delivery_controls.md](delivery_controls.md) — Definition of Done and acceptance gates

When a checklist item repeats a policy or runtime rule, treat the linked canonical document as authoritative and update that document first.

## Operating Guidelines

- Prefer completing fewer end-to-end deliverables over starting many disconnected tasks.
- Do not mark workstation / Kata / capacity items complete without Dell-workstation evidence (access still pending).
- Do not reintroduce purged topics without a new product decision.
- Reduce scope before weakening zero-retention, FERPA, authentication, or cleanup safeguards.

---

## Active — Product

### Manual grading UX

- [ ] Add coarse status/manual-completion filters and queue polish without introducing a bulk grading grid.
- [ ] Add explicit same-student edit conflict detection if multiple API processes or simultaneous graders become a requirement (current v1 is last-write-wins).

### Expected I/O extraction and visual diff

- [x] Backend AST parsing of pytest files for convention-based expected inputs/outputs (e.g. `EXPECTED_INPUT` / `EXPECTED_OUTPUT`).
- [x] Expose extracted expected fields in the sandbox run results API.
- [x] Wire sandbox visual diff to real expected vs actual output (custom `VisualDiffViewer` already exists; do not require `react-diff-viewer`).
- [ ] Expose parsed expected inputs/outputs next to test items in the instructor assignment setup rubric panel.

---

## Active — Correctness / platform gaps

- [ ] **Add a custom Judge0 Python runtime** — Judge0 CE `1.13.1` remains the latest stable release, but language ID `71` is Python 3.8.1. Choose the course-supported Python version (3.11+ required by current modeled code), then:
  - retain Judge0 CE `1.13.1` and build a custom compiler/runtime image containing the selected Python version;
  - install `pytest` plus the allowlisted `pillow`, `pygame`, and `tabulate` packages into that exact interpreter;
  - register a new, non-`71` language ID whose run command targets that interpreter, then update `JUDGE0_LANGUAGE_ID`;
  - seed and test the language mapping against a disposable Judge0 database before migrating the deployed instance;
  - smoke-test `sys.version`, every allowlisted import, multi-file execution, and submission deletion. Until then, the runner intentionally fails fast on the incompatible image.
- [ ] **Fine-Grained AST Whitelisting & Custom Constraints** — Extend the AST validator to support restricting specific method calls (e.g., blocking built-in `.sort()` or `sorted()`) and specific keywords on a per-assignment configuration basis.

---

## Active — CS1410 course modeling

Goal: fully model UVU **CS 1410** in the database from the local (gitignored) source tree [`cs1410/`](../../cs1410/) — modules, assignments, Concepts Covered, pytest, model solutions, support artifacts, and seed. Specs live in `cs1410/m*/overview.md` and `cs1410/m*/**/desc.md`. Real `submissions/` are **local-only** (reference when authoring tests/model solutions; also used later for testing/LLM training). Do **not** commit, seed, or persist student identifiers from that tree.

The course skeleton and deep models for lab1, DS1–DS10, and lab6 are complete.

### Modeling constraints

- **Image / hard-to-check parts:** pytest what is feasible; pixel/visual correctness → **manual rubric for now** (visual-diff later if useful).
- **Concepts Covered:** map module learning objectives onto the **existing AST concept vocabulary**; store on **`Module.concepts`** (not per-assignment additions). Non-mappable LOs (e.g. “online readiness”) stay out of Concepts Covered.
For each remaining assignment, author `backend/app/db/seeds/<slug>/`, wire config/artifacts, pass preflight and model validation, and smoke the sandbox.

### Remaining labs

- [ ] `lab2`, `lab3` (m2)
- [ ] `lab4`, `lab5` (m3)
- [ ] `lab7` (m11)
- [ ] For any image/visual lab parts: same rule as lab1 — pytest feasible checks; manual for computationally awkward pixel criteria.

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

## Deferred (not active — ask before starting)

- [ ] Configuration Schema Versioning & Migration Pipeline (Deferred while in testing stage without active live assignments).
- [ ] Staff Microsoft OAuth through NextAuth (mock JWT remains current).
- [ ] Sandbox Local LLM feedback. (Deferred)
  - Send submission source (+ grounded test/AST context) only when payload is not personally traceable.
  - Generate rubric-context explanations without re-grading (hallucination guard).
  - Degrade under high load; log token usage in non-sensitive run metadata.
- [ ] Canvas automated feedback upload / distribution (manual Canvas grade CSV import remains assumed).
- [ ] Multi-language or compiled-language execution pipelines beyond current Python Judge0 path.
- [ ] Official-run Local LLM feedback. Before approval:
  - generated comments must remain editable HTML-only drafts and never replace pytest truth;
  - deterministically remove names, Canvas/submission identifiers, identifying paths, and identifiers in source comments/string literals;
  - use run-local pseudonyms only and skip feedback when anonymization confidence is insufficient;
  - prove with tests that raw identifiers never reach the Local LLM client.
