# UVU Autograder v1 — Comprehensive Overview & Workflow

**Status:** Implementation Blueprint
**Target Audience:** Admins, Instructors, IAs, and Students of UVU CS 1400/1410
**Core Philosophy:** A stateless, FERPA-compliant, high-speed processing pipeline that uses AI and automated analysis to provide actionable grading support while avoiding persistent storage of student submissions and detailed student feedback.

---

## 1. System Architecture & Tech Stack

The architecture is designed to be lightweight, cost-effective, and highly secure. By functioning as a "stateless processing engine," the system avoids storing student submissions or gradebooks, eliminating the largest FERPA liabilities.

- **Frontend:** **Next.js** (Hosted on Railway). Provides the UI for both the staff grading workflow and the student sandbox workflow.
- **Backend:** **FastAPI** (Hosted on Railway). Handles async requests, routing, and prompt generation.
- **Execution Engine:** **Piston** (Dockerized on Railway). Runs student code in strictly isolated, ephemeral containers with network access disabled (`--network none`) and hard resource limits.
- **Database:** **Railway PostgreSQL**. A tiny data footprint containing only non-sensitive metadata.
- **AI Inference:** **Azure OpenAI API**. Utilizes the university's enterprise agreement to guarantee data privacy while offloading heavy LLM inference to the cloud.

---

## 2. Core Features & Capabilities

### A. "Shadow SSO" Authentication

Uses Microsoft OAuth restricted strictly to `@uvu.edu` domains. This provides instant, verified identity management without requiring a lengthy IT approval process for full Canvas LTI integration. Admins, instructors, and IAs have actual accounts stored in the database with permissions. Students sign in only for UVU-verified sandbox access, and no persistent student profile is stored beyond the active session.

- **Sandbox Rate Limiting:** Student sandbox uploads are strictly rate-limited to `5 uploads per hour` per authenticated `@uvu.edu` student to control Azure OpenAI costs and prevent spam abuse.

### B. "Concepts Covered" (Progressive Whitelisting)

Instead of a simple blacklist, the system is curriculum-aware.

- **AST Checking:** Before execution, the Python `ast` library scans the code. If a student uses a concept that hasn't been taught yet (e.g., using `sort()` in Week 2), it flags a "Future Concept Warning".
- **AI Context:** The allowed concepts list is fed into the LLM, ensuring the AI only provides hints using the programming tools the student actually knows.

### C. Zero-Retention Data Model

The database only stores operational metadata:

- `Users` (Admins, Instructors, and IAs only)
- `Courses` & `Sections`
- `Assignments` (Rubrics, Config JSONs, and Test Cases)
- _Note: Student accounts, submissions, projected runs, and detailed feedback artifacts are NOT stored persistently._

### D. In-Memory Plagiarism Detection

The system can run Stanford MOSS through the Python `mosspy` client as an optional batch-analysis step.

- **Ephemeral Input:** Student files are prepared for MOSS only from the in-memory or temporary working directory created for the current batch.
- **No Persistent Copies:** The app does not keep local copies of student code after the batch export and plagiarism pass complete.
- **Staff Review Only:** MOSS similarity output is intended for instructor/IA review as a flagging aid, not an automatic penalty system.
- **Assignment Context:** Base files, starter code, and instructor-provided support files can be excluded or marked appropriately before submission to MOSS.
- **Save Warning:** Because the similarity report is hosted externally by Stanford MOSS, the UI must prominently surface the returned URL and warn the instructor to save it before leaving the page.

### E. AI Hallucination Guardrails

The system executes a `pytest` suite against the student's code first. The raw traceback and pass/fail statuses are passed to the LLM as absolute ground truth. The LLM is strictly prompted to _explain_ the failure pedagogically and is forbidden from re-evaluating the code's correctness.

---

## 3. App Workflows

### Workflow 1: Instructor/IA Batch Grading (The Ephemeral Pipeline)

_Canvas remains the definitive source of truth for assignment descriptions, due dates, and final grades._

1.  **Ingestion:** The instructor downloads a bulk submissions ZIP from Canvas and uploads it to the Autograder.
2.  **Fail-Fast Validation:** The FastAPI backend first validates that the archive is a recognizable Canvas ZIP and rejects malformed or non-Canvas ZIPs before any grading work is queued.
3.  **Volatile Extraction:** The FastAPI backend extracts the ZIP directly into an ephemeral RAM disk or temporary directory.
4.  **Execution & AI Enrichment:** The system processes submissions concurrently. It runs AST checks, executes `pytest` in Piston, and queries Azure OpenAI for hints. Celery worker concurrency is aligned to Piston's supported container parallelism to prevent container exhaustion.
5.  **Dynamic Output:** The system instantly bundles the results into a single package:
    - A `.csv` file containing the calculated grades.
    - A `.zip` containing individual HTML feedback reports named by Canvas identifiers.
6.  **Optional Plagiarism Pass:** The system may submit the same ephemeral batch files to Stanford MOSS via `mosspy` and return the similarity report URL to staff for manual review. The UI warns the instructor to save the URL before leaving the page.
7.  **Destruction & Distribution:** The instructor downloads the results package, and the server immediately wipes the temporary directory. M1 assumes bulk grade upload/import back into Canvas is supported. Bulk feedback upload/distribution into Canvas is not committed M1 behavior and remains future research.

### Workflow 2: Student Sandbox (Ephemeral Projected Feedback)

1.  **Login:** The student signs in through Microsoft OAuth with a `@uvu.edu` account.
2.  **Selection:** The student chooses a course and assignment that has been configured by staff.
3.  **Upload:** The student uploads code for projected grading.
4.  **Execution & Feedback:** The system runs the same core grading pipeline with AST checks, `pytest`, and Azure OpenAI feedback generation.
5.  **Rate Limit Enforcement:** The backend enforces a strict limit of `5 uploads per hour` per authenticated student identity.
6.  **Projected Results:** The student sees a projected score, warnings, and feedback on screen only.
7.  **Zero-Retention Cleanup:** When processing completes or the student exits the session, the uploaded code and projected feedback artifacts are destroyed.

### Workflow 3: Assignment & Rubric Setup

1.  **Creation:** The instructor creates an assignment linked to a course.
2.  **Guided Setup or Direct JSON:** The instructor or IA can either use a basic wizard for the core assignment/rubric/config fields or paste/import a raw `config.json`.
3.  **Round-Trip Editing:** The app renders the current config in an editable interface, keeps the JSON synchronized, and allows the current `config.json` to be downloaded.
4.  **Concept Mapping:** The instructor toggles the "Concepts Covered" whitelist for that specific assignment, defining what tools the students (and the AI) are allowed to use.
5.  **Test Validation:** The instructor or IA can create a model solution and run the test cases against it inside the same Piston environment used for student code, guaranteeing environment parity.

## Future Enhancements

- Training our own LLM to give feedback more accurately and reduce costs on the long-term
- AI-assisted rubric and test case workflow
- Further Canvas integration
  - Automated bulk feedback upload/distribution into Canvas
- Persistent student-facing history or downloadable sandbox artifacts
