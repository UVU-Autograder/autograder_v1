# Implementation Questions

This file captures unresolved inconsistencies between:

- `backend_implementation/jaxon_implementation/`
- `backend_implementation/easton_implementation/` (excluding `EP_archive/`)

Assumed baseline for this sweep:

- **Judge0 is canonical** for implementation.
- **Easton `EP_AGV1_backlog.md` is superseded** and not used for M1 decisions.
- Easton `EP_AGv1_sprint_plan_v3.md` is treated as active and equal-weight with Jaxon docs.

---

## Locked Common Ground (No Longer Open)

These are now treated as aligned and resolved:

- Judge0 + Kata execution path is canonical.
- Zero-retention is a hard product boundary.
- Azure OpenAI (with privacy/ZDR constraints) is the M1 inference path.
- Microsoft OAuth + `@uvu.edu` restriction is the M1 auth model.
- Role model for M1 is `admin`, `instructor`, `IA`, `student`.
- Output model for M1 is staff `CSV + HTML ZIP`, student sandbox on-screen only.

---

## 1. Where should Judge0 run in canonical M1 deployment?

**Current drift**

- Jaxon docs: Railway-first app stack + separate execution infrastructure.
- Easton sprint v3: Railway M1 target with execution service assumptions written around privileged Docker runtime on the same hosting narrative.

**Question to resolve**

- Is Judge0 deployment for M1 documented as:
  - separate dedicated execution infrastructure (Jaxon style),
  - or Railway-hosted privileged execution service in the same platform narrative?

---

## 2. What is the canonical frontend code-view tooling contract?

**Current drift**

- Jaxon docs lock Monaco as canonical.
- Easton sprint v3 tooling tables still emphasize Prism.js for highlighting.

**Question to resolve**

- Is Monaco required for M1 code-edit/review surfaces, with Prism optional for static previews only?

---

## 3. What is the minimum canonical M1 schema at Sprint 0?

**Current drift**

- Jaxon technical specs explicitly include `staff_access`, `assignment_concept_overrides`, `assignment_artifacts`, `test_cases`, and `run_summaries`.
- Easton sprint v3 Sprint-0 schema list includes `assignment_artifacts` and `run_summaries`, but omits `staff_access`, `assignment_concept_overrides`, and `test_cases` in that specific early schema contract.

**Question to resolve**

- Should Sprint 0 require the full Jaxon-style schema from day one, or allow phased introduction of the omitted tables with explicit milestone ownership?

---

## 4. What is the exact IA permission boundary in M1?

**Current drift**

- Jaxon permission matrix is granular: IA is section-scoped, has limited grading-setup authority by default, and MOSS access is delegated-only.
- Easton sprint v3 FR-02 groups Instructor and IA together for many capabilities without the same explicit default restrictions.

**Question to resolve**

- Should IA permissions follow Jaxon’s strict-by-default matrix, or should IA be functionally equivalent to instructor in assignment/config workflows?

---

## 5. What is the required Judge0 artifact-deletion contract?

**Current drift**

- Jaxon docs explicitly require deletion or invalidation of Judge0 submission/result artifacts immediately after retrieval, in addition to local ephemeral cleanup.
- Easton sprint v3 describes cleanup and zero-retention clearly, but does not define the same Judge0-service-side deletion contract in equivalent detail.

**Question to resolve**

- Is explicit Judge0 submission/result artifact deletion (or invalidation) a mandatory acceptance criterion for both official and sandbox runs?

---

## 6. What is the canonical run-status delivery contract?

**Current drift**

- Easton sprint v3 specifies `GET /runs/{id}/status` backed by Redis and a 2-second polling cadence.
- Jaxon docs specify async pipeline/status tracking behavior but do not lock polling interval or a single status endpoint contract at that precision.

**Question to resolve**

- Should M1 standardize on the Easton status endpoint + polling cadence, or define a broader status contract that allows alternate delivery mechanisms?

---
