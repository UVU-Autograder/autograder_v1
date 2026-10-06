# UVU Autograder

An on-prem Python autograder for UVU coursework. Students test code in a public sandbox; staff configure assignments, grade Canvas batches, review manual items and export grades/feedback. Pytest determines scores; local AI explains sandbox failures.

CS1410 has 17 seed assignments; CS1400 has a placeholder. The system is preparing for a controlled course pilot.

## Start here

[Running](docs/running.md) covers the three testing workflows:

- Access the full on-prem stack.
- Run frontend checks locally while the workstation is unavailable.
- Run a local frontend against the real on-prem backend.

| Reference | Contents |
| --- | --- |
| [System](docs/system.md) | Complete stack, capabilities, hierarchy and code map |
| [Considerations](docs/considerations.md) | Data boundaries, access and approval requirements |
| [Workstation](docs/guides/workstation.md) | Workstation setup, health, updates and recovery |
| [Assignments](docs/guides/assignments.md) | Authoring and seed validation |
| [AI](docs/guides/ai.md) | Serving, evaluation, training and rollback |
| [Backlog](docs/planning/backlog.md) | Detailed next steps and unanswered questions |
| [Autograding platform research](docs/research/autograding-platforms.md) | Six source reviews and a detailed improvement proposal grounded in our architecture |

After the planned GitHub Issues/Projects transfer, replace the backlog link with actual tracker links and remove the local backlog.
