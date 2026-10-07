# UVU Autograder

Students need feedback while they still have time to improve. Instructors need consistent grading without spending hours repeating the same checks.

The UVU Autograder is a powerful interface for both students and teachers working with programming assignments. Students can find mistakes and get help understanding them early instead of scratching their heads over confusing rubrics post-submission. Instructors can automate routine checks and spend more time reviewing work that needs their judgment.

## Features

### For students

- **Practice in your browser:** Open assignments without an account, read the instructions, and upload or create project files.
- **See what needs fixing:** Run assignment tests and view estimated scores, rubric results, error messages, and comparisons of expected and actual output.
- **Check course concepts:** The platform catches syntax errors and warns when code uses concepts outside the assignment's taught material.
- **Ask for AI hints:** A local AI assistant explains observed mistakes and suggests next steps. Its responses are fine-tuned to not give out solutions. Deterministic tests determine scores, while AI provides explanations and feedback.

### For instructors and grading assistants

- **Build assignments:** Set instructions, required files, tests, point values, manual criteria, and extra credit. Setup checks flag missing files and mismatched tests. Run your reference solution to verify your test cases and catch problems.
- **Organize course material:** Group assignments into modules and set the concepts students should use at each stage.
- **Grade Canvas submissions:** Upload a Canvas ZIP for your section. The platform groups student files, flags unrecognized entries, and queues the batch.
- **Review the results:** View class score summaries, filter submissions, inspect code and file previews, and add comments and manual scores for subjective requirements.
- **Return grades and feedback:** Once grading and manual review are complete, download a Canvas-compatible grade CSV and individual HTML feedback reports. Staff import grades and share feedback through Canvas.

### For administrators

- **Manage access:** Create or update courses and sections, add staff, and control their access.
- **University sign-in:** Microsoft sign-in identifies staff, while assigned roles determine access.
- **Manage workload:** Monitor usage, queues, and errors. Background workers limit simultaneous grading, recover interrupted jobs, and handle repeated requests. Batches support up to 200 submissions per upload.

## Privacy and security

Code execution and AI run on university hardware. Student programs run in isolated virtual machines with time and memory limits and no network access. Identifying information is removed from logs and AI inputs.

Temporary execution files are deleted after grading. Official submissions and feedback are deleted within 24 hours.

## Current status

The platform currently grades Python. CS1410 has the complete coursework (17 assignments) fully integrated. CS1400 has an example assignment, and is our next target.

The project is preparing for a course pilot. Instructor testing, university approval, and university sign-in and secure hosting checks remain open. Canvas transfers are currently manual. Direct Canvas integration, additional courses, and other programming languages are future work.

## Tech Stack

| Area | Tools | What they do |
| --- | --- | --- |
| Web application | Next.js, React, TypeScript, Monaco | Build the browser interface for students and staff. Monaco provides the code editor used in the workspace. |
| Backend and database | Python, FastAPI, PostgreSQL | FastAPI handles requests, checks staff access, and coordinates grading. PostgreSQL stores course setup, assignments, rubrics, and staff permissions. |
| Tests and code checks | Pytest, Python AST analysis | Pytest runs instructor-written tests and supplies results for scoring. AST analysis inspects Python syntax and course concepts before execution. |
| Code execution | Judge0, Kata Containers | Judge0 runs submitted programs and returns their output. Kata places the execution environment inside a virtual machine, separating it from the host. |
| Background jobs | Celery, Redis | Celery runs grading jobs in the background. Redis carries queued jobs and temporary status updates; database records track available execution capacity. Separate workers dispatch batches and clean up expired files. |
| Local AI | Gemma 4 12B, vLLM | Gemma is tuned to explain programming mistakes. vLLM serves the model on the workstation GPU so feedback can be generated locally. |
| Hosting and sign-in | Docker Compose, Nginx, Microsoft Entra | Docker Compose manages the backend services. Nginx routes browser requests to the web app and API. Entra handles university sign-in. |

## Learn more

Start with the [running guide](docs/running.md) for access, setup, and testing. The frontend can run locally with sample data.

- [System overview](docs/system.md)
- [Assignment setup](docs/guides/assignments.md)
- [Privacy requirements](docs/considerations.md)
- [Hosting and maintenance](docs/guides/workstation.md)
- [AI development](docs/guides/ai.md)
- [Autograding platform research](docs/research/autograding-platforms.md)
- [Open issues](https://github.com/UVU-Autograder/autograder_v1/issues)
