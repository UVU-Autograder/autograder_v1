# Frontend Implementation (Locked Common Ground)

This file records what both the UI/UX PDF and Jaxon backend docs clearly align on for M1 direction.

## Shared, Locked-Down Decisions

1. **Role-aware UX exists** for at least admin/instructor/TA(IA)/student paths, with different views and capabilities per role.
2. **Course → section → assignment structure** is core to navigation and workflow organization.
3. **Staff run an official grading flow from Canvas ZIP uploads** (including bulk processing and run monitoring).
4. **Students have a sandbox flow** where they choose assignment context, submit code, and receive projected feedback in the app UI.
5. **A code workspace/review surface is required** (split-pane/editor-centric experience for code + test/feedback context).
6. **Monaco Editor is the canonical editor direction** (backend docs explicitly lock this; UI/UX direction is editor-first and compatible).
7. **Plagiarism checking is optional and staff-facing** (UI calls this out; backend docs lock optional MOSS usage for official workflows).
8. **Staff-facing export workflow is required** (grade-oriented export artifacts, with downloadable run output for official grading).
9. **Operational status visibility is required** (queue/run progress, submission state, and monitoring views).
10. **Feedback must include test-oriented signals** (pass/fail and error context, not just a single score).

## Non-Negotiable Backend Constraints Frontend Must Respect

1. **Auth boundary:** M1 backend locks to Microsoft OAuth with `@uvu.edu` restriction.
2. **Retention boundary:** zero-retention of student code and detailed artifacts after processing/session lifecycle.
3. **Sandbox output boundary:** on-screen only; no persistent student history as an M1 product feature.
4. **Official export boundary:** grade CSV + per-student HTML feedback ZIP are canonical M1 outputs.
