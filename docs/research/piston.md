# Piston: a narrow execution API and explicit runtime profiles

Inspected 2026-10-06 from a shallow clone of [engineer-man/piston](https://github.com/engineer-man/piston), commit `de2b365ac759670a3a0d13ea208a0869a92c7e64` (commit timestamp 2026-07-31). No engine, runtime package or upstream test was executed. The clone was removed before cloning Anubis. [Comparison and integration proposal](autograding-platforms.md).

## What Piston provides

Piston accepts a language, version, files, arguments, stdin and execution limits. It returns separate compilation/execution results, including stdout/stderr, exit code, signal, status, memory and CPU/wall time. Runtime aliases and version matching simplify callers, while package definitions manage installation and launch commands. It does not interpret course requirements, decide rubric points, manage manual review or export Canvas grades. Those remain application responsibilities. [Execution API](https://github.com/engineer-man/piston/blob/de2b365ac759670a3a0d13ea208a0869a92c7e64/api/src/api/v2.js), [runtime implementation](https://github.com/engineer-man/piston/blob/de2b365ac759670a3a0d13ea208a0869a92c7e64/api/src/runtime.js).

The source uses Isolate boxes with cgroups, process/file limits, wall and CPU time, optional memory bounds and network separation. Compilation and execution have separate limits; after successful compilation the code creates another box and transfers submission artifacts into it before running. A process-local capacity counter and waiting queue bound active execution within that process. This does not provide a durable course-job queue or host failover. [Job implementation](https://github.com/engineer-man/piston/blob/de2b365ac759670a3a0d13ea208a0869a92c7e64/api/src/job.js).

Important source defaults include networking disabled, 64 concurrent jobs, compile/run memory limits of `-1`, and a small stdout/stderr buffer limit. “Supports memory limits” therefore should not be mistaken for “uses a safe finite memory limit by default.” Per-language overrides and request parameters alter behavior. The streaming WebSocket path also handles output differently from the accumulated HTTP path, so equivalent limits across both would need verification. [Configuration](https://github.com/engineer-man/piston/blob/de2b365ac759670a3a0d13ea208a0869a92c7e64/api/src/config.js), [API and WebSocket paths](https://github.com/engineer-man/piston/blob/de2b365ac759670a3a0d13ea208a0869a92c7e64/api/src/api/v2.js).

The checked-in Compose deployment sets `privileged: true` and publishes port 2000. The Dockerfile builds a pinned Isolate revision and uses a Node 15/Buster base. These are concrete deployment choices, not evidence that Piston cannot be hardened or that it has a particular exploitable flaw. They do establish that its default checked-in topology is different from our approved Kata/QEMU boundary and requires its own maintenance review. [Compose](https://github.com/engineer-man/piston/blob/de2b365ac759670a3a0d13ea208a0869a92c7e64/docker-compose.yaml), [Dockerfile](https://github.com/engineer-man/piston/blob/de2b365ac759670a3a0d13ea208a0869a92c7e64/api/Dockerfile).

The package installer checks downloaded archive SHA-256 against index metadata before installation. Execution routes and package install/delete routes share the same API module. A checksum protects consistency with that index; it does not independently establish a trusted publisher or package safety. Runtime management must be an administrative boundary if used in a public-facing grader. [Package installation](https://github.com/engineer-man/piston/blob/de2b365ac759670a3a0d13ea208a0869a92c7e64/api/src/package.js).

## High-value lessons for UVU

### Preserve precise execution outcomes

Our Judge0 status map currently calls several runtime signals/nonzero exits timeouts. Piston's explicit `code`, `signal`, `status`, `cpu_time` and `wall_time` demonstrate a better diagnostic envelope. Map timeout, memory exhaustion when reliably reported, output limit, process failure, import/compilation failure, engine error and malformed test result separately. Leave a failure as `unknown_execution_failure` when the engine cannot establish its cause; do not infer out-of-memory merely from SIGKILL.

This improves fairness as well as messaging: a staff configuration problem should hold grade publication, while a known student runtime failure can receive the instructor-defined outcome. Keep raw engine metadata transient and expose sanitized categories to operations. Version the public result contract and update generated OpenAPI/client types together when implementation work begins.

### Introduce one approved runtime profile before multiple languages

Our [custom image](../../judge0.Dockerfile) builds Python 3.11.9 and installs pytest, Pillow, Pygame and tabulate without version pins. Assignment dependency validation checks package names against an allowlist, but a name alone does not identify the installed behavior. Define a `python-cs1410` profile with actual image digest, language ID, exact packages, runner protocol, locale and enforced resource ceilings. A health check should execute a synthetic capability probe, not merely confirm that Judge0 answers HTTP.

Pin tested package versions and keep an update/calibration process so pinning does not mean indefinite staleness. Attach the effective profile to an instructor release and official run snapshot. If a later course requires C/C++ or Java, add a separately calibrated profile; keep selection staff-controlled and treat memory units carefully. Piston uses bytes, while our Judge0 adapter uses kilobytes, making a generic adapter without unit normalization hazardous.

### Bound output without losing the result record

Our stdout contains both test feedback and the structured grading payload. A runaway print can exhaust memory, bury the record or cause engine truncation. Set distinct limits for student stdout/stderr, per-case messages, total feedback and machine-result data. Prefer a control channel or protected result artifact separate from student output. If that is unavailable, cap capture at the runner and validate engine framing, while documenting the remaining same-process integrity limitation.

Show a truncation indicator and preserve the diagnostic category. Do not use an extremely small engine output limit that cuts off otherwise valid grading JSON. Test multi-byte text, binary/invalid encodings, huge assertions and large collections. The purpose is usable bounded feedback, not copying Piston's numeric defaults.

### Keep our durable scheduler above any engine

The engine's local concurrent-job limit should never replace [our admission and ticket system](../../backend/app/domains/runs/queue_admission.py). A future adapter should take an admitted execution lease, run under the host ceiling and return an engine-neutral outcome. It must reject results from expired ownership tokens, support cancellation, and track disposal even on network errors. Multiple independent concurrency limits need coordinated budgets rather than multiplying capacity accidentally.

Piston invokes cleanup in `finally`, but its HTTP handler calls `res.send()` in the preceding try path. Do not infer from the nearby cleanup comment that the client waits for verified cleanup before observing success. Our [executor](../../backend/app/domains/grading/executor.py) makes cleanup failure override its returned outcome; preserve and verify that stronger lifecycle rule if experimenting with another engine. Cancellation and orphan cleanup also need host-side reconciliation, not just a finally block.

## Adoption judgment

Piston is worth considering for a future multi-language playground or an isolated engine comparison. There is no demonstrated benefit to replacing our Python Judge0/Kata deployment now. We would still need the same assignment configs, scheduler, result validation, manual review, staff grants, exports and retention workers, while acquiring a new deployment and cleanup contract.

The inspected README says public hosted API access changed to require authorization in February 2026. More fundamentally, our present data boundary excludes sending submissions to an external execution service. A self-hosted synthetic experiment would be the relevant option, and neither README availability nor an access token would change that policy. [Hosted API and operation documentation](https://github.com/engineer-man/piston/blob/de2b365ac759670a3a0d13ea208a0869a92c7e64/README.md).

The repository includes targeted scripts for fork/process abuse, networking, runaway output, allocation and file persistence. Their presence suggests useful categories for our own synthetic isolation acceptance tests; it does not prove either system passes those checks. A complete engine comparison would measure startup, compile/run latency, memory accounting, cancellation and verified data disposal under the same host workload, with isolation constraints held explicit. No throughput benchmark was performed here.

## Proposed experiment and reuse

First implement richer outcomes and a documented Python runtime profile using Judge0. Measure whether those changes eliminate misleading failures and improve reference-model reproducibility. Only if a course actually needs another language should a separate synthetic Piston/Kata-compatible feasibility experiment be proposed, with restricted administrative routes, finite resource limits and complete cleanup evidence. Retain two host execution slots until measurement supports another limit.

The [root license](https://github.com/engineer-man/piston/blob/de2b365ac759670a3a0d13ea208a0869a92c7e64/LICENSE) contains MIT text. Runtime packages and Isolate are additional components whose provenance must be considered separately before reuse. This report recommends patterns and a conditional experiment, not adoption of its default deployment.
