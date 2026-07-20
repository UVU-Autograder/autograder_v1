# Frontend Implementation

This file captures the frontend contract, route structure, and UI-surface responsibilities only.

Frontend mockup preview: https://autograder-frontend-mockup.vercel.app/

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
- `/staff/courses/[courseId]/assignments/[assignmentId]/artifacts`: assignment-owned grading assets
- `/staff/courses/[courseId]/assignments/[assignmentId]/runs` and `/staff/courses/[courseId]/assignments/[assignmentId]/runs/[runId]`: official-run monitoring and export workflow surfaces (nested under the assignment)

## Frontend Information Architecture

- Student navigation is a distinct sandbox flow:
  - course selection
  - assignment selection within that course
  - sandbox workspace for one course-scoped assignment
- The student sandbox flow is public and does not require student authentication, student profile storage, or roster-derived authorization.
- Staff assignment lists intentionally call `/sandbox/courses/{courseId}/assignments` for a student-parity view of sandbox-enabled assignments.
- Staff navigation is organized around:
  - admin-only course, section, access, and monitoring surfaces
  - course list and course detail
  - assignment setup surfaces
  - official-run monitoring
  - admin access management
- Section context should appear only where it is operationally needed, such as official-run authority, run metadata, and access management.
- Staff sessions use mock JWT login today (`@uvu.edu`). NextAuth + Microsoft OAuth is deferred. Client-side 5-minute inactivity logout, backend JWT lifespan (default 5 minutes), and sliding refresh via `x-refresh-token` are implemented.

## UI-Surface Responsibilities

- The setup wizard is the assignment grading setup surface; staff treat `config_json` as an internal detail, not a user-facing editor.
- The wizard writes the backend-owned `assignment_configs.config_json`.
- Course-level concepts editing owns the baseline `Concepts Covered` list for all assignments in that course. Effective whitelist at runtime is course defaults ∪ the assignment's module concepts (no per-assignment concept editor).
- The sandbox entry surface should immediately show globally visible sandbox-enabled courses and assignments.
- The sandbox workspace is upload-first: students upload one ZIP/project bundle for the selected assignment, then see a sanitized file tree, read-only Monaco preview, rubric details, assignment constraints, terminal/output information where available, test results with passed/failed counts, projected score, grounded feedback, explicit retention messaging, visible remaining uploads, and a clear limit-reached state for backend `429` responses.
- Sandbox Local LLM feedback (in development) appears beside test results for sandbox runs only, explanation-only, and only for non-personally-traceable code payloads.
- Expected I/O visual diff in the sandbox is an active backlog item (custom `VisualDiffViewer` exists; wire to real expected fields from the API).
- The sandbox workspace does not support loose multi-file drag-and-drop.
- The assignment artifacts surface owns one or more pytest files, model solution files, and support files through the backend `assignment_artifacts` storage-reference model.
- UI-visible "test cases" are scoring items from the assignment setup/config, not separate physical test files.
- Admin monitoring is admin-only and should summarize local LLM token usage, sandbox upload-limit state, and worker/capacity status without exposing student code or detailed student artifacts.
- The `/staff/courses/[courseId]/assignments/[assignmentId]/runs/[runId]` surface supports official review and export: derived results, per-student feedback, ephemeral Monaco previews while files remain (≤24h or until cleanup), separate CSV and feedback-ZIP downloads. **In-app manual rubric grading** (usable end-to-end grader workflow) remains active backlog even though the backend save/export-regeneration path exists.
- Active review UX backlog (keep wording broad where undecided): per-student feedback preview, Monaco previews, and result filtering.

## Frontend Constraints

- Use role-aware route groups and keep public, student, and staff areas visually and structurally distinct.
- Treat the student sandbox entry as a public sandbox flow rather than a student-authenticated route.
- Use `IA` as the canonical assistant role label in implementation docs. Older prototype assistant-role labels are non-canonical.
- Use `ZIP/project bundle` for the multi-file upload contract.
- Treat Monaco as a read-only preview surface, not an in-browser IDE.
- Do not assume persistent student submissions, sandbox history, or raw student-code download flows in the UI.
- Keep route, shell, and type design compatible with `CourseSummary`, `SectionSummary`, `AssignmentSummary`, `OfficialRunStatus`, `SandboxResult`, and `StaffAccessScope`.
