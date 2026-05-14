# Implementation Questions

This file captures the remaining inconsistencies I found across:

- `implementation_folder/jaxon_implementation/`
- `implementation_folder/easton_implementation/`
- `backend/`

`implementation_folder/easton_implementation/EP_archive/` was intentionally ignored for this sweep.
For Easton's sprint-planning input, only `implementation_folder/easton_implementation/EP_AGv1_sprint_plan_v3.md` is considered active here.

For the purposes of this file, Easton and Jaxon are treated as equal planning inputs. The goal is not to pick a winner implicitly, but to identify where the repo still needs explicit reconciliation before implementation work accelerates.

---

## Working Baseline Already Reflected in the Repo

Some decisions no longer look meaningfully open because they already appear repeatedly in the implementation materials and related repo changes:

- `Judge0` is the execution engine
- `Kata Containers` is the VM-based isolation layer
- `Azure OpenAI` is the active inference path
- `Monaco Editor` is part of the intended frontend experience
- `zero-retention` remains a core product constraint

The questions below focus on what still needs a conscious repo-wide cleanup or product decision.
Execution-engine selection is intentionally not one of those questions; `Judge0` is treated as settled.

---

## 1. Should local-first hosting remain part of the implementation-facing architecture?

**Current drift**

- Easton’s architecture materials still describe a local-first or self-hosted operational model in several places.
- Jaxon implementation materials and the backend/testing setup assume Railway-hosted app services with separate Judge0 infrastructure.
- The backend skeleton and testing harness do not reflect a local-first deployment baseline.

**Why this matters**

If local-first hosting remains in implementation-facing docs without being clearly demoted, infrastructure work can split between two incompatible deployment stories.

**Question to resolve**

- Should local-first hosting be:
  - removed from implementation-facing docs,
  - preserved as a future or fallback deployment path,
  - or kept as a co-equal supported M1 deployment option?

**Recommended direction**

- Treat local-first hosting as reference or future-path material unless you want to reopen the settled Railway plus separate Judge0 infrastructure decision.

---

## 2. Should Monaco be scoped to both student and staff flows, or staff-first?

**Current drift**

- Jaxon implementation materials treat Monaco as a core M1 dependency.
- Easton’s materials focus more on Prism/result preview and do not center Monaco.
- The backend is unaffected, but frontend sprint scope is affected directly.

**Why this matters**

This changes Sprint 0 scaffolding, component hierarchy, and how ambitious the sandbox UI is in M1.

**Question to resolve**

- Is Monaco for:
  - staff review only in M1,
  - both sandbox and staff flows in M1,
  - or a locally hosted dependency that starts minimal but is present in both paths?

**Recommended direction**

- Keep Monaco available across both paths, but keep M1 expectations modest: editing, syntax highlighting, inspection, and future annotation support.

---

## 3. Is the human approval gate rejected, deferred, or partially retained?

**Current drift**

- Easton’s architecture materials include human approval before release.
- Jaxon implementation materials do not require an approval gate in M1.
- This impacts data retention, run states, and staff workflow complexity.

**Why this matters**

This changes:

- the run state machine
- whether reviewed results persist longer
- whether “released” is a required official workflow state

**Question to resolve**

- Should M1:
  - have no required approval gate,
  - have an optional review step,
  - or require staff approval before exports are considered final?

**Recommended direction**

- If zero-retention and simplified M1 delivery remain top priorities, keep approval workflow optional or deferred rather than required.

---

## 4. What is the final role model for implementation?

**Current drift**

- Jaxon implementation materials use: `admin`, `instructor`, `IA`, `student`
- Easton’s broader architecture materials use: `admin`, `course_admin`, `instructor`, `TA`, `student`
- Some planning language in Easton’s sprint materials still carries the broader role vocabulary

**Why this matters**

This directly affects:

- DB models
- auth policies
- route protection
- UI wording

**Question to resolve**

- Which role vocabulary should implementation use everywhere?

**Recommended direction**

- Freeze one role model before backend auth work becomes executable.

---

## 5. What output model is actually implementable in M1?

**Current drift**

- Jaxon implementation materials center on CSV + HTML ZIP + on-screen sandbox feedback.
- Easton’s architecture materials still include PDF/XLSX-style outputs in places.
- Easton sprint v3 is closer to HTML ZIP output, but mixed export language still exists in the repo.

**Why this matters**

This affects export services, templates, UI expectations, and storage assumptions.

**Question to resolve**

- Should M1 outputs be:
  - CSV + HTML ZIP + on-screen sandbox only,
  - CSV/XLSX + PDF,
  - or a mixed model with some older formats preserved?

**Recommended direction**

- Keep the lighter HTML ZIP + CSV model unless there is a clear requirement for heavier formats in M1.

---

## 6. Should persistent audit logging remain out of scope?

**Current drift**

- Easton’s architecture materials assume persistent audit logs, AI raw output, and approval history.
- Jaxon implementation materials keep persistent storage limited to sanitized metadata and core course/config entities.
- The backend skeleton currently aligns more with sanitized metadata than with full audit retention.

**Why this matters**

This is a major FERPA and storage-boundary decision.

**Question to resolve**

- Should M1 persist:
  - only sanitized metadata,
  - sanitized metadata plus workflow audit entries,
  - or detailed review/audit artifacts?

**Recommended direction**

- Keep detailed audit retention out of M1 unless a compliance or grading-appeal requirement explicitly forces it.

---
