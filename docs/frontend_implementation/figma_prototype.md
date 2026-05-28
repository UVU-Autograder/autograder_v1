# Roles:

This file is a prototype reference artifact, not the canonical frontend specification. Canonical M1 behavior lives in `docs/frontend_implementation/frontend_implementation.md`, `docs/planning/backlog.md`, `docs/technical_specs.md`, and `docs/backend_implementation/decisions.md`.

Prototype terminology note: this file may use `TA`; canonical implementation docs use `IA`. Treat prototype `TA` references as IA/TA prototype terminology unless the canonical docs say otherwise.

Canonical M1 auth note: staff, admin, instructor, and IA surfaces use staff authentication. The student sandbox is public and does not require student authentication, even if older prototype notes imply a shared login flow.

## Student:

- View all courses
- Submits code (upload .zip files) with maximum upload of 5 times an hour
- View rubric
- View constraints
- View feedback, numbers of test passed and failed and score

Link to figma prototype: https://www.figma.com/proto/GLPFmoiaQEM5eJjru86PFu/uvu_autograder?node-id=247-379&t=Cq3choHIglkhpbEO-1&scaling=min-zoom&content-scaling=fixed&page-id=112%3A372&starting-point-node-id=247%3A379

Note: `Code Viewer` and `Test Result` panel can be scrolled vertically in the prototype

Note:

- **Sandbox for student:** Compliant with the backend suggestion to use Monaco, I have implemented it as a read-only code viewer. I chose this approach because I believe we don't need a fully functional in-browser IDE that executes code and dynamically integrates with isolated rubrics since it will require significant infrastructure.For now, the sandbox for student provides panels for code viewer, terminal output, feedback and test result. Students cannot edit code here so they need to make changes locally and re-upload their files as needed.
  Each assignment loads its corresponding rubric configuration from the backend. When a student selects an assignment, the UI updates immediately to display the relevant requirements, and the autograder backend determines and executes the correct test suite against the submitted file.

## Admin/Instructor:

- Manage courses
- Monitoring (token limit, system limits, upload limit)
- User management tools (assign instructor, TA)
- Create courses
- Create sections
- Deactivate courses
- Deactivate sections
- Create assignments
- Rubric and constraint editing through the canonical wizard/config model
- Set a deadline for assignments
- Test-case editing through the canonical wizard/config/artifact model
- Download assignment config

Link to figma prototype: https://www.figma.com/proto/GLPFmoiaQEM5eJjru86PFu/uvu_autograder?node-id=480-890&t=tkdZgWKk1N7cqLx9-1&scaling=min-zoom&content-scaling=fixed&page-id=377%3A1357

Note:

- **Sandbox for instructor/TA:** prototype-only draft. Canonical M1 staff behavior is documented in `frontend_implementation.md` and `backlog.md`.
  Link to figma: https://www.figma.com/proto/GLPFmoiaQEM5eJjru86PFu/uvu_autograder?node-id=548-1891&t=xJAsxGnj1YOSTySS-1&scaling=min-zoom&content-scaling=fixed&page-id=60%3A122&starting-point-node-id=548%3A1891

## TA / IA Prototype Notes:

- View assigned courses and sections (grid and list view)
- View only (rubric, constraints, deadline) of each assignment
- Run test cases

Link to figma prototype: https://www.figma.com/proto/GLPFmoiaQEM5eJjru86PFu/uvu_autograder?node-id=568-2297&t=dsu440ds4eG8aJbF-1&scaling=min-zoom&content-scaling=fixed&page-id=377%3A1358
