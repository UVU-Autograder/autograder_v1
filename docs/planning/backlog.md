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

- Prefer completing fewer end-to-end deliverables over starting many disconnected tasks.
- Do not reintroduce purged topics without a new product decision.
- Reduce scope before weakening zero-retention, FERPA, authentication, or cleanup safeguards.

---

## Active — Product


### Manual grading UX

- [ ] Add coarse status/manual-completion filters and queue polish without introducing a bulk grading grid (runs & exports remain isolated per staff upload session).

### Student sandbox UX

- [x] Fix student sandbox sidebar (removed `mt-15` offset, aligned flush with shell header, added Problem Overview button).
- [x] Refactor problem description rendering to structured layout instead of raw text file views (implemented minimal `<ProblemOverview />` tab component).

### Expected I/O extraction and visual diff

- [x] Backend AST parsing of pytest files for convention-based expected inputs/outputs (e.g. `EXPECTED_INPUT` / `EXPECTED_OUTPUT`) — verified via unit tests in `backend/tests/test_io_parser.py`.
- [x] Expose extracted expected fields in the sandbox run results API — integrated in `runner_gen.py` & verified via contract tests.
- [x] Wire sandbox visual diff to real expected vs actual output (`VisualDiffViewer` integrated into `code-results.tsx` with Vitest unit tests).
- [x] Expose parsed expected inputs/outputs next to test items in the instructor assignment setup rubric panel (implemented via `parseExpectedIO` & `scoring-rules-section.tsx` badges).


---

## Active — Correctness / platform gaps

- [x] **Add a custom Judge0 Python runtime** — Judge0 CE `1.13.1` retains custom Python 3.11.9 image specification (`judge0.Dockerfile`), language ID `711` registered (`scripts/seed_judge0_language_311.sql`), preinstalled allowlisted dependencies (`pillow`, `pygame`, `tabulate`, `pytest`), and verified contract tests (`backend/tests/test_judge0_custom_runtime.py`).

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
- [ ] CS 1400 modeling: We do not yet have access to official course data.
