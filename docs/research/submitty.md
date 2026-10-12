# Submitty: grading phases and staff review

Inspected 2026-10-06 from a shallow clone of [Submitty/Submitty](https://github.com/Submitty/Submitty), commit `df165f676c2d892adfd1343ac82e6ee490b07152` (commit timestamp 2026-10-02). Source inspection only; no services, graders or upstream tests were executed. The clone was removed before cloning PrairieLearn. Comparison and integration proposal tracked in `autograding-platforms.md`.

## What the source actually implements

Submitty spans course management, submission collection, automatic grading and staff grading. The PHP application is only one part: Python shippers/workers coordinate execution, while the C++ grading subsystem configures, compiles, runs and validates assignments. PostgreSQL and course filesystem state sit alongside that machinery. Calling it a PHP/Python backend with Docker workers omits a substantial grading implementation and operational surface.

The execution path is configurable. `Testcase` selects `ContainerNetwork` when `autograding_method` is `docker`; otherwise it selects `JailedSandbox`. The abstract execution-environment class handles preparation, permitted file copying, grading phases and directory lockdown. Containers initially use no network; explicit container-network construction supports assignments that need communicating processes. This is useful for systems/networking courses, but it is not evidence that every deployment has equivalent isolation. [Testcase selection](https://github.com/Submitty/Submitty/blob/df165f676c2d892adfd1343ac82e6ee490b07152/autograder/autograder/testcase.py), [execution environment](https://github.com/Submitty/Submitty/blob/df165f676c2d892adfd1343ac82e6ee490b07152/autograder/autograder/execution_environments/secure_execution_environment.py), [container networking](https://github.com/Submitty/Submitty/blob/df165f676c2d892adfd1343ac82e6ee490b07152/autograder/autograder/execution_environments/container_network.py).

An assignment is a structured grading program rather than just a test file. The example configs express compilation, execution commands, expected files, validators, points, hidden cases and optional release of hidden details. The configuration loader calculates visible points separately and normalizes defaults. Validators can have deduction fractions, allowing multiple checks to contribute to one case. A compilation problem is therefore representable independently from an output mismatch. [Configuration implementation](https://github.com/Submitty/Submitty/blob/df165f676c2d892adfd1343ac82e6ee490b07152/grading/load_config_json.cpp), [Python example](https://github.com/Submitty/Submitty/blob/df165f676c2d892adfd1343ac82e6ee490b07152/more_autograding_examples/python_simple_homework/config/config.json), [hidden-test example](https://github.com/Submitty/Submitty/blob/df165f676c2d892adfd1343ac82e6ee490b07152/more_autograding_examples/cpp_hidden_tests/config/config.json).

The scheduler models jobs and compatible workers separately. Workers advertise capabilities, and the first-come-first-served scheduler selects idle compatible workers with queue ordering. Job JSON loading explicitly tolerates incomplete queue files. This is a reminder that scheduling correctness includes filesystem and process failure behavior, not just an in-memory queue. It is not a reason to replace our database tickets with queue files. [Scheduler](https://github.com/Submitty/Submitty/blob/df165f676c2d892adfd1343ac82e6ee490b07152/autograder/autograder/scheduler.py), [scheduler tests](https://github.com/Submitty/Submitty/blob/df165f676c2d892adfd1343ac82e6ee490b07152/autograder/tests/test_scheduler.py).

Staff grading has richer semantics than entering a number and comment. A graded component records selected reusable marks, custom points/messages, grader identity and the submission version. The controller checks permission to save marks, restricts custom marks for some graders, and supports verification state. Separate grade-inquiry routes implement permission-checked discussion and resolution. These are concrete workflow models, not merely attractive interface features. [Graded component](https://github.com/Submitty/Submitty/blob/df165f676c2d892adfd1343ac82e6ee490b07152/site/app/models/gradeable/GradedComponent.php), [grading controller](https://github.com/Submitty/Submitty/blob/df165f676c2d892adfd1343ac82e6ee490b07152/site/app/controllers/grading/ElectronicGraderController.php), [grade inquiries](https://github.com/Submitty/Submitty/blob/df165f676c2d892adfd1343ac82e6ee490b07152/site/app/controllers/student/GradeInquiryController.php).

The inspected core paths establish file-based validation and course grading. They do not establish a ready-to-use Canvas synchronization contract for our use case. We should not equate a course platform, CSV interoperability or external integration claims with safe Canvas write-back. Similarly, tool command support does not prove a fully configured static-analysis/Valgrind workflow for every course. Those capabilities would require assignment-specific configuration and further deployment validation.

## Lessons for UVU

### Make diagnostic phases explicit

Our pytest path already separates packaging, execution and score calculation. Submitty shows how much clearer the product becomes when those distinctions survive into feedback. A submission with a missing required file, an import error, a runtime crash and a failed assertion should produce different explanations and different staff actions. Today our Judge0 mapping classifies several runtime-error statuses as timeouts. Improving that classification is immediately useful without adding another grading engine.

A modest phase model could be `prepare`, `collect`, `execute`, `score`, `review`, `export`. Each phase needs a stable outcome and an actor responsible for remediation. A broken instructor test should request staff action; a failed assertion should explain a student-facing requirement. Do not automatically treat either as zero points. See the [current Judge0 mapping](../../backend/app/integrations/judge0/client.py) and [grading executor](../../backend/app/domains/grading/executor.py).

### Treat visibility as a server contract

Submitty distinguishes hidden test scoring from release of details. Our current config has no comparable visibility field. If instructors want practice diagnostics and a separate official test set, explicitly define which cases run in each context and which fields students receive. Filtering only the React display is insufficient: expected output, test names, traceback source and AI prompts all need the same projection.

For UVU, a useful starting point is an optional public diagnostic label and an explicit detail policy per scoring item, defaulting to current behavior. A hidden test cannot remain secret merely because its source is omitted from an HTTP response: our runner imports student code into the same Python process as pytest and carries grading files in the execution bundle. Confidentiality and score integrity need an execution-boundary design before we promise genuinely secret tests. Hiding details in feedback and isolating test secrets are different requirements.

### Improve manual consistency before adding new course systems

Our unified `scoring_items` already supports manual criteria and rubric groups. Reusable instructor-authored marks could sit on that model: each mark has a stable key, description, feedback text and an explicit scoring effect. Staff could select a common mark and add a specific comment. Preserve explicit completion: an untouched item is not equivalent to zero, and export still requires every manual item to be reviewed.

Rubric definitions are instructor assets and can persist. Student selections, comments, reviewer assignments and revision details belong in the existing official workspace and expire with it. An optimistic revision check on saves would prevent two IAs silently replacing each other's work. A review lease can help navigation, but the server still needs a stale-write check. Adopt the consistency mechanism without importing a permanent student grading ledger.

### Keep tool scoring subordinate to course intent

Submitty's command and validator system makes specialized grading extensible. UVU should first improve our pytest helpers for exact text, normalized text, numeric tolerance, structural assertions and concept diagnostics. Any lint or style requirement should be instructor-visible, calibrated against seed solutions and disabled by default. A broad style tool should not penalize valid introductory code merely because it disagrees with an industrial convention.

For future compiled courses, phase-specific compilation and sanitizer/memory checks would make sense. They would require a new runtime profile, isolation evidence and explicit scoring rules. Pygame still needs our manual visual criteria; headless state assertions do not establish visual quality.

## What to avoid adopting

Replacing our platform with Submitty would introduce overlapping course content, student identities, version histories, grade inquiries and a larger operational stack. Those features may be valuable at university scale, but conflict with our anonymous sandbox and 24-hour official retention boundary unless scope changes. The examined PHP controller is also very large: copying its breadth would concentrate permissions and grading rules in one module. Our existing domain separation is a better starting point for incremental work.

Do not copy jailed or Docker execution settings over the current Kata/QEMU contract. Also avoid generic shell-command authoring in a first improvement: a typed set of pytest capabilities is easier to validate and maintain. Capability-aware scheduling matters only when we have heterogeneous execution profiles; two slots on one workstation do not justify a distributed shipper architecture.

## Recommended experiment and acceptance evidence

Use one synthetic Dessert Shop assignment and one Pygame assignment to prototype rubric marks plus phase-specific diagnostics. Have two staff reviewers grade the same deliberately ambiguous examples independently. Compare disagreement, save conflicts and time spent entering repeated feedback. Verify that changing rubric definitions during an official run does not change that run, that concurrent saves reject stale revisions, and that selected marks disappear with official detail at cleanup.

For feedback visibility, build serialization tests before UI work: one hidden failure should never appear in student JSON, HTML, stdout summaries or AI input. A second experiment should attempt test/result tampering inside the execution boundary before any stronger confidentiality or integrity claim. These are proposed experiments, not checks performed in this research.

## Maintenance and reuse

The inspected [license](https://github.com/Submitty/Submitty/blob/df165f676c2d892adfd1343ac82e6ee490b07152/LICENSE.md) identifies BSD-3-Clause, with separate [third-party licensing](https://github.com/Submitty/Submitty/blob/df165f676c2d892adfd1343ac82e6ee490b07152/LICENSE-THIRD-PARTY.md). This records upstream metadata; it does not settle UVU's ownership or reuse review. Prefer independently implemented patterns and small interoperability experiments over vendoring the platform. The snapshot's recent commit concerns withdrawn-student navigation, illustrating the edge cases that accumulate when a grader becomes a course system; recency alone is not a maintenance guarantee.
