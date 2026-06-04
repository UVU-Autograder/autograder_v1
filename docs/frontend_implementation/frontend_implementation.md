# Frontend Implementation

This file captures the frontend contract, route structure, and UI-surface responsibilities only. [figma_prototype.md](figma_prototype.md) is reference material.

## Frontend Route Contract

- `/sandbox`: globally visible sandbox-enabled course list
- `/sandbox/[courseId]`: assignment list for one sandbox-enabled course
- `/sandbox/[courseId]/assignments/[assignmentId]`: sandbox workspace
- `/staff/admin/courses`: admin course management
- `/staff/admin/sections`: admin section management
- `/staff/admin/access`: admin staff, role, and course/section access management
- `/staff/admin/monitoring`: admin-only token usage, upload-limit, and worker/capacity monitoring
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
- The student sandbox flow is public for M1 and does not require student authentication, student profile storage, or roster-derived authorization.
- Staff navigation is organized around:
  - admin-only course, section, access, and monitoring surfaces
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
- The sandbox entry surface should immediately show globally visible sandbox-enabled courses and assignments.
- The sandbox workspace is upload-first in M1: students upload one ZIP/project bundle for the selected assignment, then see a sanitized file tree, read-only Monaco preview, rubric details, assignment constraints, terminal/output information where available, test results with passed/failed counts, projected score, grounded feedback, explicit zero-retention messaging, visible remaining uploads, and a clear limit-reached state for backend `429` responses.
- The sandbox workspace does not support loose multi-file drag-and-drop or in-browser code editing in M1.
- The assignment artifacts surface owns pytest files, model solution files, and support files through the backend `assignment_artifacts` storage-reference model.
- Admin monitoring is admin-only in M1 and should summarize Azure token usage, sandbox upload-limit state, and worker/capacity status without exposing student code or detailed student artifacts.
- The `/staff/runs/[runId]` surface is a preview-only review workflow in M1: staff can inspect derived results, per-student feedback, and ephemeral read-only Monaco previews while available, but cannot edit grades or feedback in the app.
- The `/staff/runs/[runId]` surface should expose separate download actions for the Canvas-grade CSV and the feedback ZIP.

## Frontend Constraints

- Use role-aware route groups and keep public, student, and staff areas visually and structurally distinct.
- Treat the student sandbox entry as a public sandbox flow rather than a student-authenticated route.
- Use `IA` as the canonical assistant role label in implementation docs. Older prototype assistant-role labels are non-canonical.
- Use `ZIP/project bundle` for the M1 multi-file upload contract.
- Treat Monaco as a read-only preview surface in M1, not an in-browser IDE.
- Do not assume persistent student submissions, sandbox history, or raw student-code download flows in the UI.
- Do not add manual grading surfaces, grade-override controls, or feedback-editing controls to the M1 staff review UI.
- Keep route, shell, and type design compatible with `CourseSummary`, `SectionSummary`, `AssignmentSummary`, `OfficialRunStatus`, `SandboxResult`, and `StaffAccessScope`.
