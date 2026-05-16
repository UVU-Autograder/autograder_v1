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
   
   **Keomony**: Thanks for pointing this out. It seems Microsoft OAuth has a different action and interface than the form login. I'll modify it using myUVU log in sample:
    
    ```text
        +----------------------+
        | School Email         |
        | [______________]     |
        |                      |
        | Continue             |
        +----------------------+
    ```


2. **Student identity persistence: are students stored as accounts?**  
    The UI/UX PDF includes “add people (TA) and students,” but backend docs lock M1 to session-only student access with no persistent student profile.

   **Jaxon**: Until we integrate with Canvas, we don't need students to have accounts. They only "log in" to authenticate. We are storing the minimal amount of student information.

   **Keomony**: what I had in mind is that not all students can access the course autograder. Let's say:
       - Student A registers for CS1400 which will use autograder, so after log-in, the student will see CS 1400 on the dashboard where s/he can click on it, select assignment number and upload the zip files to check codes. 
       - Student B register for CS 2300 which doesn't use autograder, so after log-in, the dahsboard is blank.

   So, I am thinking of is: 
    Students will authenticate using Microsoft OAuth, but we will not implement full persistent student accounts/profiles.
    However, the system still requires minimal authorization data to determine which courses a student can access. After login, the backend can check the student’s Microsoft email/ID against a lightweight course-enrollment mapping (e.g., authorized student list for each course).
    
    This allows:    
    * students enrolled in supported courses to see those courses on their dashboard
    * students not enrolled in supported courses to see an empty dashboard
    
    We will store only the minimal information necessary for authentication and course authorization, not long-term student profiles or persistent submission history. Maybe we'll only store something like this:

    ```text
    `Minimal table:
    
    authorized_students (
        email,
        course_id
    )

 
    or imported roster:
    
   `course_enrollment (
        microsoft_oid,
        course_id
    )
    ```
       

3. **Sandbox rate limit policy: 200 uploads, or 5/hour?**  
    The UI/UX PDF mentions “Set limitation (200 uploads),” while backend docs lock sandbox to `5 uploads per hour` per authenticated student and no sandbox-style cap for official staff runs.

   **Jaxon**: Let's stick with 5 uploads per hour unless you have a reason to do this.

   **Keomony**: I am okay with whatever the backend want. I only put this because I once read Jaxon's documentation and see "200 uploads" and "5 uploads per hour" are both mentioned. So, I just include them both as reference. 

4. **TA/IA permissions: can they CRUD assignments and grading setup?**  
   The UI/UX PDF TA views include broad assignment actions (including CRUD language), while backend permission docs scope IA privileges to assigned sections and more limited grading authority.
   **Jaxon**: We need to decide whether just teachers can edit assignment rubrics or if IAs can as well.

5. **Attempt/history UX in sandbox: in-session only, or retained history?**  
   The UI/UX PDF proposes attempt/history visibility; backend docs lock zero-retention and no long-term student result history. Clarify whether this is strictly session-lifetime UI state only.

   **Jaxon**: We are not retaining attempt history on either side. We can't store student data.

   **Keomony** This is what we want to clarify with the backend as well. I understand that due to FERPA, we don't store students information or grades. However, when I do research for the UI part, it seems that we can do this even though our program is session-based. We can collect monitoring and analytics by storing lightweight metadata in the database or logs during each submission. We only need a temporary records. So far, we have 2 options:

    1. Strict Session-Only UI State: No backend persistence for attempts. React state or server session memory only. Attempts disappear after refresh/logout. 

    2. Temporary Backend Storage: we'll temporarily store submissions/results to process grading, but we'll implement auto-delete later so that there is no permanent history page or no historical     analytics.
       Example:
       Upload ZIP
        → backend grades it
        → result shown
        → deleted after set hours

   So, I'll need to ask the UI/UX team members as well as backend team members which one they prefer. OR we can just not implememnt it and only allow student to see the latest submission. This feature is optional as I don't think it is that important. We can just get rid of it if it doesn't align with what we had envision our project to be. 
       

6. **Result override workflow: is manual score/feedback override in M1 scope?**  
   The UI/UX PDF includes TA “override feedback, grade,” but backend docs do not explicitly lock an override model in M1.

   **Jaxon**: We need to lock in an override model for the future.

   **Keomony**: oh okay. I will double check the M1 scope. If override isn't in M1 scope, then we can just forget about it for now and keep it for the future. 

7. **Downloadability of raw submissions: allowed for staff, or disallowed by retention/security policy?**  
   The UI/UX PDF includes “download zip files/code submission.” Backend docs lock export outputs to grade CSV + per-student HTML feedback ZIP and strict cleanup of student artifacts.

   **Jaxon**: We shouldn't need to download code submissions, unless you can think of a reason.

    **Keomony**: I think you are right. We may not need this, but I'll ask Dominic and Vebjørn if they think we need it, or if they have any suggestions. The thing is I keep getting confused about what data will be stored and what not. So that is why I somwhow mix up the featues. But currently, this feature is only what I considered to include. I don't think it is being used for now.   
    
8. **Rubric authoring source of truth: UI rubric editor vs config/test-case model?**  
   The UI/UX PDF emphasizes rubric editing screens; backend docs lock a wizard + raw `config.json` + `TestCase` artifact model. Clarify which frontend rubric UI is canonical for M1.
   **Jaxon**: Frontend rubric editor changes the backend config and test cases. I think this should be M1 unless it's too difficult.
    *Keomony**: I honestly am not sure about this. But from what chatGPT said, it suggests to choose backend model so it is simpler and safer? This is what is says:

    `
    If you choose UI as canonical (what your team suggests):

        - Instructor edits rubric in UI
        - Backend updates config.json + test cases automatically
        - UI drives everything
        
        ✔ Better UX
        ❌ More engineering complexity (validation, syncing, schema enforcement)`


    `If you choose backend model as canonical (spec-aligned default):

        Rubric is defined in config.json / TestCase
        UI is just a wizard that writes that format
        Backend always controls final structure
        
        ✔ Simpler + safer for M1
        ✔ Matches “locked backend model” wording
        ❌ Slightly less flexible UI`

    I think Dominic or Vebjørn may need to step in and help addressing this question.

  

9. **Inline LLM code annotations: M1 commitment or post-M1 enhancement?**  
   The UI/UX PDF proposes inline annotations in split-pane review; backend docs mention future annotation support with Monaco, but M1 lock is less explicit.

   **Jaxon**: Not sure if we should do this for M1 or not.
    **Keomony** Okay. I will go over M1 scope again to see what should be included and what not. So far, this is what my code checking panel looks like:
    <img src="/home/kmary/km/uvu_autograder/uvu_autograder_github/autograder_v1/docs/frontend_implementation/code_checker_wireframe.png" alt= "Code Checking Panel Wireframe from Figma" width="500" >


## Clarification Notes for Frontend Team

- **Framework/language baseline (PDF p.7):** Use **Next.js + React + TypeScript** for M1. HTML/CSS are output/styling layers, but implementation should be TS/TSX (not plain JS pages).
- **Validation baseline (PDF p.7):** Prefer schema validation (for example Zod) for frontend form/input validation.
- **Retention baseline (PDF p.3):** “History/attempts before session end” is session-lifetime UI only. Do not implement persistent student attempt history for M1.
- **Download baseline (PDF p.6):** Do not add direct student-code download UX by default in M1; canonical export remains staff grade CSV + HTML feedback ZIP.
