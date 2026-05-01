# UVU Autograder v1 - Jaxon's Changes and Clarifications to Easton's Model

This document is a companion to Easton's implementation notes. It captures changes and clarifications I want to make to his model while keeping his overall direction as the baseline.

## Proposed Changes and Clarifications

- Make a clear split between Canvas assignment content and our app's grading data.
  - The assignment description should be handled in Canvas.
  - Only the rubric and test cases should live in our app.

- Rubric ingestion should initially support these input methods (M1 -> M2 plan):
  - M1: raw JSON input (paste/upload) — raw JSON uploads must be complete and validated.
  - M2: PDF upload and copy/pasted text with LLM-assisted conversion to internal format (deferred).
  - For PDF and plain-text rubric input (M2), the LLM will help convert the source material into a concrete internal format that the instructor can review and edit in the UI, and download if needed to use in other assignments.

- Test creation should eventually support both:
  - fully instructor-authored tests
  - AI-assisted test generation (deferred to M2)
  - AI-assisted test generation should support both full starter suites and smaller criterion-level suggestions.
  - Any AI-generated tests must always be manually reviewable and editable before they are used in grading.
  - Instructors should be able to dynamically execute the real pytest files on a model solution (M1: supported via editor + run).
  - Instructors can also set a template for students (M2).

- I am assuming tests live in the database and are tied to individual assignments.
  - The UI edits real pytest files.
  - Students should only see a description of the tests, not the exact test files.
  - Rubric criteria should map to tests, even if that mapping is not perfectly enforceable in the UI at first.

- Make the submission model more explicit.
  - There is one submission model.
  - Every submission counts as a version.
  - Versions live in one timeline, but are marked as either `practice` or `official`. (Practice submissions are a future feature (M2); M1 only creates `official` submissions via instructor uploads.)
  - Students may be able to upload practice attempts in M2 to get a projected grade and LLM feedback; those attempts will be saved as `practice` versions.
  - The only official submissions in M1 are the ones the instructor uploads from Canvas.
  - Instructors should be able to upload both full class ZIPs and individual files for regrades or reprocessing.

- Clarify scoring behavior.
  - Pytest results automatically deduct from the score according to test point values.
  - Normal constraint violations should flag the submission for review and surface a warning rather than automatically deducting points.
  - Security-sensitive constraints should automatically block execution.
  - The autograder should surface constraint warnings and hard-block reasons clearly to TAs, instructors, and students when appropriate.

- Student-facing feedback approach
  - Move away from PDF-centered student feedback in the long term.
  - In M1, there should be a student dashboard for released official results only.
  - In M2, the dashboard can expand to show practice submissions and projected grading attempts.
  - Students who want to should eventually be able to test their code before official submission to get a projected score; that remains a planned M2 feature.
  - `released` should mean visible to the student.

- Auth approach
  - M1 should use NextAuth with Microsoft OAuth.
  - The NextAuth callback should reject any login that does not end in `@uvu.edu`.
  - This is an interim domain-restricted login approach, not the final official UVU SSO solution.
