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

### Manual grading (in-app grader workflow)

**Done (do not reopen as the Active goal):**
- [x] Backend `POST …/manual-grades` persists rubric scores/comments for a student in an official run.
- [x] Saving regenerates Canvas-grade CSV and per-student feedback ZIP from current `manual_results`.

**Active goal:** a staff grader can complete manual rubric grading entirely inside the official-run UI (find student → see auto results + manual items → enter scores/comments → save → see updated totals and exports). Sheet/tab UI stubs exist but are **not yet a shippable grader workflow**.

#### Backend implementation plan

- [ ] Confirm run-details payload always exposes `manual_results` keys from `config_json.manual_rubric_items` (including zero-score / unscored state) after official grading and on run-details fetch.
- [ ] Ensure saved scores update the staff-facing student detail totals (auto + manual) consistently with CSV export math (`manual_score_sum`).
- [ ] Harden validation: unknown keys, over-max scores, missing run workspace, section-scoped auth (already required) with clear 4xx messages for the UI.
- [ ] Add/extend API tests for: save → CSV row reflects new total; save → feedback HTML includes manual scores/comments; empty-manual-item assignments remain no-ops.
- [ ] Document auto vs manual ground truth: pytest/`test_results` are never overwritten by manual edits; manual items only contribute via `manual_results`.

#### Frontend implementation plan

- [ ] Official run page: discoverable path to grade (student list → student detail → manual rubric entry) without relying on dead-end chrome.
- [ ] Show auto test summary beside editable manual rubric items for the selected student.
- [ ] Score + comment controls bound to existing `manual-grades` API; disable save while in flight; surface errors.
- [ ] After save, refresh selected student + list totals so the grader sees updated score without a full page reload / re-export dance.
- [ ] Empty state when the assignment has no `manual_rubric_items` (“nothing to grade manually”).
- [ ] Smoke the flow against a seeded assignment that defines manual rubric items (e.g. lab1).

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
- [x] Align JWT token lifespan with the 5-minute inactivity window (`JWT_EXPIRATION_MINUTES` default `5`).
- [x] Sliding JWT expiration refreshed on request activity (`x-refresh-token` + frontend store update).

---

## Active — Correctness / platform gaps

Completed platform fixes (kept for history; do not reopen without a regression):

- [x] **Section-scoped staff authorization** — course/section grants on official ingest and run routes.
- [x] **Queue admission** — global waiting-job warn-at-`40` / reject-at-`50`, plus fair official/sandbox scheduling into the execution-slot cap.
- [x] **Preflight before student grading** — strict config/artifact/`ag_<key>` preflight for sandbox and official student pipelines.
- [x] **Unify effective Concepts Covered** — `course.default_concepts ∪ assignment.module.concepts` (per-assignment additions removed).
- [x] **Official run status** — sanitized counters, queue position, and ETA band for official runs.

Follow-up (docs/schemas only; not a runtime gap):

- [ ] Regenerate `docs/schemas/config_v1.schema.json` and `docs/schemas/openapi.json` so they match current Pydantic models (dropped `support_artifacts` / `output_artifacts` / config-level `concepts`).

Future Platform Hardening & Scalability:

- [x] **Isolate Student Pytest Execution (Sandbox Security)** — Move student pytest execution into a separate subprocess/process rather than running in-process via `pytest.main()` inside the instructor's test suite, preventing namespace pollution, global state poisoning, or hook-hijacking.
- [ ] **Fine-Grained AST Whitelisting & Custom Constraints** — Extend the AST validator to support restricting specific method calls (e.g., blocking built-in `.sort()` or `sorted()`) and specific keywords on a per-assignment configuration basis.
- [ ] **Configuration Schema Versioning & Migration Pipeline** — Establish strict JSON schema validation for `config_json` and an automatic DB sync/migration pathway to safely handle schema changes without breaking existing assignment records.
- [x] **Test-Level Timeout Enforcement** — Inject `pytest-timeout` or a similar timeout mechanism inside the student execution runner to prevent single test infinite loops from hanging the entire Judge0 pipeline execution.
- [x] **Close AST Validator Import Bypasses** — Block `importlib` and other dynamic namespace/attribute traversal methods (`getattr`, etc.) to prevent evasion of the import security blacklist.
- [ ] **Headless Event Mocking for Pygame Tests** — Design testing patterns or helper fixtures for Pygame grading that programmatically inject mock events into Pygame's queue to validate interactive game states under headless drivers.

---

## Active — CS1410 course modeling

Goal: fully model UVU **CS 1410** in the database from the local (gitignored) source tree [`cs1410/`](../../cs1410/) — modules, assignments, Concepts Covered, pytest, model solutions, support artifacts, and seed. Specs live in `cs1410/m*/overview.md` and `cs1410/m*/**/desc.md`. Real `submissions/` are **local-only** (reference when authoring tests/model solutions; also used later for testing/LLM training). Do **not** commit, seed, or persist student identifiers from that tree.

### Decisions (grill-locked)

- **Phasing:** (1) full course **skeleton**, then (2) pytest + model solution (+ `config_json` / artifacts) **per assignment**.
- **Submissions:** gitignored; agent/dev reference only for authoring — not DB seed content.
- **Image / hard-to-check parts:** pytest what is feasible; pixel/visual correctness → **manual rubric for now** (visual-diff later if useful).
- **Concepts Covered:** map module learning objectives onto the **existing AST concept vocabulary**; store on **`Module.concepts`** (not per-assignment additions). Non-mappable LOs (e.g. “online readiness”) stay out of Concepts Covered.
- **Enforced whitelist:** `course.default_concepts ∪ assignment.module.concepts` (shipped; supersedes “course + assignment additions only”).
- **Skeleton delivery:** expand [`seed.py`](../../backend/app/db/seed.py) (or a dedicated seed module it calls); seed artifact files live under [`backend/app/db/seeds/`](../../backend/app/db/seeds/).
- **Deep-phase order:** Dessert Shop **`ds1`→`ds10` first**, then remaining labs. **`lab-1-image-processing` is already partially seeded** — complete/gap-fill, do not recreate from scratch.

### Inventory (from `cs1410/`)

| Module | Assignments |
| ------ | ----------- |
| m1 | lab1 *(partially modeled as `lab-1-image-processing`)* |
| m2 | lab2, lab3 |
| m3 | ds1, lab4, lab5 |
| m4 | ds2 |
| m5 | ds3 |
| m6 | ds4 |
| m7 | ds5 *(note: `ui.py` support file present)* |
| m8 | ds6, lab6 |
| m9 | ds7 |
| m10 | ds8 |
| m11 | ds9, lab7 |
| m12 | ds10 |

### Prerequisite — Concepts Covered enforcement

- [x] Change `effective_allowed_concepts` to **course defaults ∪ module concepts** (assignment additions unused for 1410).
- [x] Update sandbox catalog / official paths / tests and sync [decisions.md](../backend_implementation/decisions.md) + [technical_specs.md](../technical_specs.md) + agent memory vocabulary.
- [x] Map each `m1`–`m12` overview LO → AST concept ids; document unmapped LOs.
- [x] Draft global CS1410 Assignments Specification (cs1410_assignments_spec.md) mapping all 17 assignments.

### Phase A — Course skeleton (seed)

- [x] Replace the stub single-module `cs1410` seed with **12 modules** aligned to `cs1410/m1`–`m12` (names + `Module.concepts` from the LO→AST map).
- [x] Set course `default_concepts` to the shared baseline used across early modules (keep progressive detail on modules).
- [x] Create **all remaining assignments** (labs + DS) with stable slugs/titles from `desc.md`, linked to the correct module, `sandbox_enabled` as appropriate, language `python`.
- [x] Keep / extend existing `lab-1-image-processing` seed under [`backend/app/db/seeds/lab_1_image_processing/`](../../backend/app/db/seeds/lab_1_image_processing/) rather than duplicating.
- [x] Ensure section + staff access grants still seed for local/dev.
- [x] Skeleton acceptance: every inventory row exists in DB; missing deep artifacts are OK until Phase B.

### Phase B — Deep model per assignment (pytest, model solution, config, artifacts)

For **each** assignment below: author the package under `backend/app/db/seeds/<slug>/`, wire seed artifacts + `config_json`, pass preflight, run model-solution validation, sandbox smoke. Use `desc.md` as spec; peek at local `submissions/` only as authoring reference.

**B0 — Finish lab1 (already partial)**

- [x] Gap-fill `lab-1-image-processing`: model solution, support images/starter as needed, pytest for auto-checkable behavior.
- [x] Encode pixel-correctness / subjective image quality as **manual** rubric items (not hard auto-fail).
- [x] Confirm Concepts Covered come from module (not assignment additions).

**B0.1 — Autograding Pipeline Repairs**

- [x] Implement multi-file AST validation checking all student `.py` files inside the ZIP submission.
- [x] Remove the `-x` stop-on-first-failure flag from dynamic pytest execution.
- [x] Configure dummy SDL drivers for headless Pygame support inside the Judge0 sandbox.
- [x] Add dynamic execution verification for Lab 1 scripts inside `tests.py`.

**B0.2 — Schema Cleanup & AST Hardening**

- [x] Delete `support_artifacts` configuration properties from config schemas and seeding logic.
- [x] Delete `output_artifacts` configuration properties from config schemas and seeding logic.
- [x] Delete `concepts` additions and drop the unused `AssignmentConcept` database table.
- [x] Harden AST preflight decorator matcher to support alternate import patterns.

**B1 — Dessert Shop chain first (`ds1`→`ds10`)**

- [x] `ds1` (m3) — inheritance skeleton / class hierarchy.
- [x] `ds2` (m4) — using classes in main.
- [x] `ds3` (m5) — test cases with pytest.
- [x] `ds4` (m6) — abstraction, abstract base classes, tax attributes, and subclass cost formulas.
- [x] `ds5` (m7) — console application prompt methods and input validation retries.
- [ ] `ds6` (m8)
- [ ] `ds7` (m9)
- [ ] `ds8` (m10)
- [ ] `ds9` (m11)
- [ ] `ds10` (m12)
- [ ] Cross-assignment consistency: shared package/module names, progressive APIs, and scoring keys stay coherent across the DS series.

**B2 — Remaining labs**

- [ ] `lab2`, `lab3` (m2)
- [ ] `lab4`, `lab5` (m3)
- [ ] `lab6` (m8)
- [ ] `lab7` (m11)
- [ ] For any image/visual lab parts: same rule as lab1 — pytest feasible checks; manual for computationally awkward pixel criteria.

### Phase C — Verification (no real student PII in CI)

- [ ] Seed + preflight green for every modeled assignment.
- [ ] Model-solution validation task passes per deep-modeled assignment.
- [ ] Sandbox create-run smoke on at least one lab and one DS assignment.
- [ ] Optional local-only: build **anonymized** Canvas ZIPs from `submissions/` for official-run capacity tests (never commit raw trees).

### Phase D — Remaining Autograder Risks & Mitigations

We will address the remaining modeling challenges with the following strategies:
1. **PytestCollectionWarning for TestItemConfig:** Rename the Pydantic schema model `TestItemConfig` to `ScoringItemConfig` or set `__test__ = False` to prevent pytest from attempting to collect it as a test class.
2. **DS6 `__str__` format fragility:** Ensure tests do not assert exact string formats. Test assertions should verify structure only (e.g. check string length > 0 and presence of subclass name).
3. **Lab 6 (Pygame) unpredictability:** Allow student-provided assets to load by preserving and extracting all files in the submission ZIP. Use `SDL_VIDEODRIVER=dummy` and signal-based timeouts for headless runs, and implement AST checks for `pygame.Rect` usage.
4. **DS7 `packaging.py` name collision:** Ensure the sandbox adds the student workspace directory to `sys.path` first (`sys.path.insert(0, "")`) so it overrides any system-wide packages.
5. **DS8 `PayType` enum vs literal divergence:** Design all unit test assertions to interact via the string signatures of `get_pay_type()` and `set_pay_type()`, avoiding direct imports of `PayType` itself.
6. **DS10 regression depth:** Break down regression checks into distinct pytest function definitions with targeted marks instead of a single brittle assertion pipeline.
7. **Judge0 python version requirement:** Ensure sandbox nodes execute under Python 3.10+ to support `match/case` syntax.

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
- Staff session: 5-minute JWT lifespan + sliding `x-refresh-token` refresh; client 5-minute inactivity logout.
- Assignment wizard + app-owned `config_json`; artifacts (pytest / model solution / support); Concepts Covered via course ∪ module.
- Canvas ZIP ingest via thin router + `ingest_official_canvas_zip`; grading via `run_grading_pipeline` + `execute_pytest_in_judge0`.
- Official exports: Canvas-grade CSV + per-student feedback ZIP; ephemeral official workspaces ≤24h or until staff cleanup.
- Official manual-grade API can persist scores and regenerate exports (in-app grader UX still Active).
- Sandbox ZIP upload, quota, preview, grounded results, zero-retention messaging.
- Seed packages under `backend/app/db/seeds/` resolved via `seed://`.
- Frontend mockup on Vercel: https://autograder-frontend-mockup.vercel.app/

Judge0 default CPU time limit in settings is **30s** (256MB memory; network-disabled student execution). Execution-slot cap remains `2` until Dell benchmarks approve otherwise.

---

## Deferred (not active — ask before starting)

- [ ] Staff Microsoft OAuth through NextAuth (mock JWT remains current).
- [ ] Canvas automated feedback upload / distribution (manual Canvas grade CSV import remains assumed).
- [ ] Multi-language or compiled-language execution pipelines beyond current Python Judge0 path.
- [ ] Local LLM on official runs or other non-sandbox surfaces.
