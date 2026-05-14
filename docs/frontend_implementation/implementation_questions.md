# Implementation Questions (UI/UX PDF vs Jaxon Backend Docs)

This file captures unresolved differences between:

- `frontend_implementation/UVU_autograder_UI_UX.pdf`
- `backend_implementation/jaxon_implementation/JL_AGv1_decisions.md`
- `backend_implementation/jaxon_implementation/JL_AGv1_technical_specs.md`
- `backend_implementation/jaxon_implementation/JL_AGv1_backlog.md`

## Open Questions

1. **Auth flow: form login or Microsoft OAuth only?**  
    The UI/UX PDF shows `username/password` login boxes, while backend docs lock M1 to `NextAuth + Microsoft OAuth` with `@uvu.edu` restriction.
   **Jaxon**: The current idea is to use Microsoft OAuth until IT authorizes official UVU login.

2. **Student identity persistence: are students stored as accounts?**  
    The UI/UX PDF includes “add people (TA) and students,” but backend docs lock M1 to session-only student access with no persistent student profile.
   **Jaxon**: Until we integrate with Canvas, we don't need students to have accounts. They only "log in" to authenticate. We are storing the minimal amount of student information.

3. **Sandbox rate limit policy: 200 uploads, or 5/hour?**  
    The UI/UX PDF mentions “Set limitation (200 uploads),” while backend docs lock sandbox to `5 uploads per hour` per authenticated student and no sandbox-style cap for official staff runs.
   **Jaxon**: Let's stick with 5 uploads per hour unless you have a reason to do this.

4. **TA/IA permissions: can they CRUD assignments and grading setup?**  
   The UI/UX PDF TA views include broad assignment actions (including CRUD language), while backend permission docs scope IA privileges to assigned sections and more limited grading authority.
   **Jaxon**: We need to decide whether just teachers can edit assignment rubrics or if IAs can as well.

5. **Attempt/history UX in sandbox: in-session only, or retained history?**  
   The UI/UX PDF proposes attempt/history visibility; backend docs lock zero-retention and no long-term student result history. Clarify whether this is strictly session-lifetime UI state only.
   **Jaxon**: We are not retaining attempt history on either side. We can't store student data.

6. **Result override workflow: is manual score/feedback override in M1 scope?**  
   The UI/UX PDF includes TA “override feedback, grade,” but backend docs do not explicitly lock an override model in M1.
   **Jaxon**: We need to lock in an override model for the future.

7. **Downloadability of raw submissions: allowed for staff, or disallowed by retention/security policy?**  
   The UI/UX PDF includes “download zip files/code submission.” Backend docs lock export outputs to grade CSV + per-student HTML feedback ZIP and strict cleanup of student artifacts.
   **Jaxon**: We shouldn't need to download code submissions, unless you can think of a reason.

8. **Rubric authoring source of truth: UI rubric editor vs config/test-case model?**  
   The UI/UX PDF emphasizes rubric editing screens; backend docs lock a wizard + raw `config.json` + `TestCase` artifact model. Clarify which frontend rubric UI is canonical for M1.
   **Jaxon**: Frontend rubric editor changes the backend config and test cases. I think this should be M1 unless it's too difficult.

9. **Inline LLM code annotations: M1 commitment or post-M1 enhancement?**  
   The UI/UX PDF proposes inline annotations in split-pane review; backend docs mention future annotation support with Monaco, but M1 lock is less explicit.
   **Jaxon**: Not sure if we should do this for M1 or not.

## Clarification Notes for Frontend Team

- **Framework/language baseline (PDF p.7):** Use **Next.js + React + TypeScript** for M1. HTML/CSS are output/styling layers, but implementation should be TS/TSX (not plain JS pages).
- **Validation baseline (PDF p.7):** Prefer schema validation (for example Zod) for frontend form/input validation.
- **Retention baseline (PDF p.3):** “History/attempts before session end” is session-lifetime UI only. Do not implement persistent student attempt history for M1.
- **Download baseline (PDF p.6):** Do not add direct student-code download UX by default in M1; canonical export remains staff grade CSV + HTML feedback ZIP.
