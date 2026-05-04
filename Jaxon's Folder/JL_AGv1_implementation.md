# UVU Autograder v1 - Jaxon's Changes and Clarifications to Easton's Model

This document is a companion to Easton's implementation notes. It captures changes and clarifications I want to make to his model while keeping his overall direction as the baseline.

## Proposed Changes and Clarifications

- Make a clear split between Canvas assignment content and our app's grading data.
  - The assignment description should be handled in Canvas.
  - Only the rubric and test cases should live in our app.

- Rubric ingestion should initially support these input methods (M1 -> M2 plan):
  - M1: both a basic wizard for core assignment/rubric/config fields and raw JSON input (paste/upload).
  - The wizard should generate valid `config.json`.
  - The app should render the current config in an editable interface and allow the `config.json` to be downloaded.
  - Raw JSON uploads must be complete and validated.
  - M2: PDF upload and copy/pasted text with LLM-assisted conversion to internal format (deferred).
  - For PDF and plain-text rubric input (M2), the LLM will help convert the source material into a concrete internal format that the instructor can review and edit in the UI, and download if needed to use in other assignments.

- Test creation should eventually support both:
  - fully instructor-authored tests
  - AI-assisted test generation (deferred to M2)
    - AI-assisted test generation should support both full starter suites and smaller criterion-level suggestions.
    - Any AI-generated tests must always be manually reviewable and editable before they are used in grading.
    - Instructors should be able to dynamically execute the real pytest files on a model solution inside the same Piston environment used for student code (M1: supported via editor + run).
    - Instructors can also set a template for students (M2).

- I am assuming tests live in the database and are tied to individual assignments.
  - The UI edits real pytest files.
  - Students should only see a description of the tests, not the exact test files.
  - Rubric criteria should map to tests, even if that mapping is not perfectly enforceable in the UI at first.

- Make the submission model more explicit.
  - M1 should not persist student submissions as application records.
  - There are two ephemeral grading paths in M1:
    - an official staff-run Canvas batch flow
    - a student sandbox flow for projected grading
  - The instructor or IA uploads an official Canvas ZIP for a single batch run.
  - The official upload path should reject malformed or non-Canvas ZIPs before they enter the grading queue.
  - The student sandbox lets a student choose an assignment, upload code, and receive projected feedback on screen.
  - The student sandbox must be rate-limited to `5 uploads per hour` per authenticated `@uvu.edu` student identity.
  - The system extracts and grades files in ephemeral working storage only.
  - Student code, intermediate artifacts, and detailed feedback are destroyed after the official export package is returned or the sandbox session ends.
  - Persistent submission timelines remain future work beyond M1.

- Clarify scoring behavior.
  - Pytest results automatically deduct from the score according to test point values.
  - Normal constraint violations should flag the submission for review and surface a warning rather than automatically deducting points.
  - Security-sensitive constraints should automatically block execution.
  - The autograder should surface constraint warnings and hard-block reasons clearly to IAs, instructors, and students when appropriate.

- Add in-memory plagiarism detection for staff review.
  - M1 can integrate Stanford MOSS through `mosspy` as an optional instructor-facing analysis step.
  - The system should prepare MOSS inputs only from the ephemeral batch workspace.
  - Student files used for plagiarism detection must not be copied into persistent storage.
  - MOSS output should be treated as a review aid for staff, not an automatic grading penalty.
  - Because Stanford MOSS hosts the report externally, the UI must prominently surface the returned URL and warn the instructor to save it before leaving the page.
  - Starter code and instructor-provided support files should be excludable from the MOSS submission set.

- Student-facing feedback approach
  - Move away from PDF-centered student feedback in the long term.
  - In M1, the official staff workflow should generate lightweight HTML files bundled into a ZIP for instructor download.
  - In M1, the student sandbox should show projected score and feedback on screen only.
  - Student sandbox results must not be downloadable or stored persistently.
  - Any persistent student-facing history can be revisited later if the retention model changes.

- Auth approach
  - M1 should use NextAuth with Microsoft OAuth.
  - The NextAuth callback should reject any login that does not end in `@uvu.edu`.
  - Staff users should have persistent roles such as admin, instructor, and IA.
  - Students may authenticate for sandbox access, but no persistent student profile should be stored beyond the active session.
  - This is an interim domain-restricted login approach, not the final official UVU SSO solution.

- Canvas-facing assumption
  - M1 assumes bulk grade upload/import back into Canvas is possible.
  - Bulk feedback upload/distribution into Canvas should be treated as future research, not committed M1 scope.

- Hosting and operational guardrails
  - Railway should be treated as the authoritative M1 hosting target for frontend, backend, PostgreSQL, Redis, Celery workers, and Piston deployment.
  - Local Docker Compose remains the development environment, not the production hosting assumption.
  - Azure OpenAI token usage should be logged as non-sensitive metadata per assignment-linked official run and per sandbox run.
  - Celery worker concurrency must be aligned to Piston's maximum supported container parallelism to avoid container exhaustion during large batches.
