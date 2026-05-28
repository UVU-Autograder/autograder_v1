# Frontend Implementation

Resolved product and implementation decisions live in `docs/backend_implementation/jaxon_implementation/decisions.md`.

Open discussion items live in `docs/implementation_questions.md`.

This file captures the frontend contract, route structure, and UI-surface responsibilities only.

## Canonical Frontend Route Contract

- `/sandbox`: globally visible sandbox-enabled course list
- `/sandbox/[courseId]`: assignment list for one sandbox-enabled course
- `/sandbox/[courseId]/assignments/[assignmentId]`: sandbox workspace
- `/staff/courses`: staff-visible course list
- `/staff/courses/[courseId]`: course detail with assignments
- `/staff/courses/[courseId]/concepts`: course defaults editor for `Concepts Covered`
- `/staff/courses/[courseId]/assignments/[assignmentId]/setup`: wizard-first assignment setup hub
- `/staff/courses/[courseId]/assignments/[assignmentId]/config`: advanced `config.json` surface
- `/staff/courses/[courseId]/assignments/[assignmentId]/concepts`: assignment concept additions editor plus merged effective-list preview
- `/staff/courses/[courseId]/assignments/[assignmentId]/artifacts`: assignment-owned grading assets
- `/staff/runs` and `/staff/runs/[runId]`: official-run monitoring and export workflow surfaces

## Frontend Information Architecture

- Student navigation is a distinct sandbox flow:
  - course selection
  - assignment selection within that course
  - sandbox workspace for one course-scoped assignment
- Staff navigation is organized around:
  - course list and course detail
  - assignment setup surfaces
  - official-run monitoring
  - admin access management
- Section context should appear only where it is operationally needed, such as official-run authority, run metadata, and access management.

## UI-Surface Responsibilities

- The setup wizard is the primary assignment-authoring experience.
- The `config` route is an advanced surface for import/export and direct config handling, not the default setup path.
- Course-level concepts editing owns the baseline `Concepts Covered` list for all assignments in that course.
- Assignment-level concepts editing owns additive assignment concepts only and must preview the merged effective list derived from current course defaults plus assignment additions.
- The sandbox entry surface should immediately show globally visible sandbox-enabled courses and assignments without student authentication.
- The sandbox workspace should combine Monaco, grounded feedback, explicit zero-retention messaging, visible remaining uploads, and a clear limit-reached state for backend `429` responses.
- The `/staff/runs/[runId]` surface is a preview-only review workflow in M1: staff can inspect per-student feedback, but cannot edit grades or feedback in the app.
- The `/staff/runs/[runId]` surface should expose separate download actions for the Canvas-grade CSV and the feedback ZIP.

## Frontend Constraints

- Use role-aware route groups and keep public, student, and staff areas visually and structurally distinct.
- Treat the student sandbox entry as a public sandbox flow rather than a student-authenticated route.
- Do not assume persistent student submissions, sandbox history, or raw student-code download flows in the UI.
- Do not add manual grading surfaces, grade-override controls, or feedback-editing controls to the M1 staff review UI.
- Keep route, shell, and type design compatible with `CourseSummary`, `SectionSummary`, `AssignmentSummary`, `OfficialRunStatus`, `SandboxResult`, and `StaffAccessScope`.
