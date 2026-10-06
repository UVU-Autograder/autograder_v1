# Anubis: event-driven submissions and infrastructure reconciliation

Inspected 2026-10-06 from a shallow clone of [AnubisLMS/Anubis](https://github.com/AnubisLMS/Anubis), commit `894ed020997ff22235e0d4b42a6f5dd9ea14f5e7` (commit timestamp 2026-09-15). The API, webhook/submission path, Kubernetes job creation, reporting, reapers, networking and selected tests were inspected. No cluster, IDE, webhook or grading pipeline was run. The clone was removed after analysis. [Comparison and integration proposal](autograding-platforms.md).

## Architecture and actual scope

Anubis treats an assignment as a GitHub-backed development workflow: students push to assignment repositories, a webhook creates submission state, queued work launches a pipeline, and results appear in the application. The repository has a Python/Flask API, SQLAlchemy models, Redis-backed RPC/cache infrastructure, a web frontend, Kubernetes/Helm deployment and Theia IDE resources. The top-level Compose file explicitly describes itself as debugging-only. Its generated design document is dated 2021, so current source is needed to establish details rather than treating every design statement as current implementation. [Overview](https://github.com/AnubisLMS/Anubis/blob/894ed020997ff22235e0d4b42a6f5dd9ea14f5e7/README.md), [design document](https://github.com/AnubisLMS/Anubis/blob/894ed020997ff22235e0d4b42a6f5dd9ea14f5e7/docs/README.md), [debug Compose](https://github.com/AnubisLMS/Anubis/blob/894ed020997ff22235e0d4b42a6f5dd9ea14f5e7/compose.yml).

The webhook path parses repository metadata, before/after commits and branch identity. It associates repositories with assignments/users, distinguishes initialization from subsequent pushes, rejects non-default-branch pushes and checks assignment acceptance/deadline behavior before enqueuing work. It looks for existing commit submission state, while background work also addresses duplicate deliveries. The checked-in `Submission.commit` field is globally unique; that identity model should not be copied as a universal submission key across courses and repositories. [Webhook route](https://github.com/AnubisLMS/Anubis/blob/894ed020997ff22235e0d4b42a6f5dd9ea14f5e7/api/anubis/views/public/webhook.py), [repository association](https://github.com/AnubisLMS/Anubis/blob/894ed020997ff22235e0d4b42a6f5dd9ea14f5e7/api/anubis/lms/webhook.py), [models](https://github.com/AnubisLMS/Anubis/blob/894ed020997ff22235e0d4b42a6f5dd9ea14f5e7/api/anubis/models/__init__.py).

Pipeline creation launches a Kubernetes Job with a course image, submission token, Git credential, repository and exact commit. The source sets CPU/memory requests/limits outside debug mode, disables service-account-token mounting, uses a finite retry count and a completion TTL. A capacity check counts current jobs before creation and re-enqueues when over its configured ceiling. This count/check/create sequence should not be treated as atomic admission control under concurrent workers. Kubernetes resource settings help scheduling and containment, but do not establish our required Kata/VM isolation. [Job creation](https://github.com/AnubisLMS/Anubis/blob/894ed020997ff22235e0d4b42a6f5dd9ea14f5e7/api/anubis/k8s/pipeline/create.py).

Workers report build, test and panic results to a separate pipeline API guarded by a submission-token decorator. Test results carry an output type, supporting richer presentation such as a diff. This makes progress visible before the complete pipeline finishes. Authentication of the reporting worker is still different from protection of the report producer from student code: a token accessible to an untrusted process cannot alone establish grading integrity. [Reporting API](https://github.com/AnubisLMS/Anubis/blob/894ed020997ff22235e0d4b42a6f5dd9ea14f5e7/api/anubis/views/pipeline/pipeline.py), [token check](https://github.com/AnubisLMS/Anubis/blob/894ed020997ff22235e0d4b42a6f5dd9ea14f5e7/api/anubis/utils/pipeline/decorators.py).

Independent pollers and reapers inspect job state, use locks, reconcile finished/old resources and capture pipeline logs before deletion. IDE provisioning likewise has capacity checks and later reconciliation when resources initialize incompletely. This is a good example of separating “request accepted” from “external resource exists” and “external resource has been removed.” [Pipeline reconciler](https://github.com/AnubisLMS/Anubis/blob/894ed020997ff22235e0d4b42a6f5dd9ea14f5e7/api/anubis/k8s/pipeline/reap.py), [poller](https://github.com/AnubisLMS/Anubis/blob/894ed020997ff22235e0d4b42a6f5dd9ea14f5e7/api/anubis/jobs/pipeline_poller.py), [IDE initialization](https://github.com/AnubisLMS/Anubis/blob/894ed020997ff22235e0d4b42a6f5dd9ea14f5e7/api/anubis/ide/initialize.py).

Network policies distinguish IDE and submission-pipeline traffic. Pipeline jobs can reach DNS, the pipeline API and specified GitHub address ranges; student IDE policies allow public internet with exclusions. Policies are omitted in debug mode. A manifest is an intended rule, not proof of enforcement: cluster CNI, address updates, label matching and actual probes matter. [Network policy](https://github.com/AnubisLMS/Anubis/blob/894ed020997ff22235e0d4b42a6f5dd9ea14f5e7/k8s/chart/templates/network-policy.yml).

## Lessons compatible with the UVU pilot

### Reconcile external side effects independently

Our durable tickets, dispatcher and independent [cleanup worker](../../backend/app/domains/runs/cleanup_worker.py) already reflect this principle. Anubis strengthens the case for clear inventories: distinguish queued ownership, active engine work, transient files and cleanup obligations. Monitoring should show orphaned resources, overdue deletions and stale attempts, not only current queue size.

Do not replace our PostgreSQL admission with a non-atomic job count. Instead extend tests around the current lease contract: worker dies before submit, engine accepts but response is lost, result arrives after lease expiry, cleanup runs during grading, broker redelivers and database access fails. Resource deletion requests need verification; a TTL or accepted API delete is not proof that all student bytes and logs are gone.

### Typed progress can improve feedback without retaining a timeline

Anubis's build/test reporting suggests a small vocabulary for our public run status: waiting, preparing, executing, scoring and completing cleanup. Keep the server authoritative and ensure retries do not display obsolete progress. For an official batch, staff can see transient stage failures and counts. Students should receive public descriptions rather than private test names or raw infrastructure output.

Streaming each test could be helpful for long-running future courses, but adds ordering, cancellation, sanitization and stale-attempt complexity. Begin with phase transitions and bounded final diagnostics. A complete score still requires the expected-case manifest and a terminal valid result. Partial progress must never imply partial publication or successful cleanup.

### Separate capabilities and credentials

The worker/control-plane split is useful even without Kubernetes. The FastAPI staff API, scheduler, grader and cleanup worker should have only their necessary data/operations capabilities. Student code must not inherit broker/database/AI/SSO/Git credentials. Local AI should see only its already sanitized public evidence.

A future Git-based intake should fetch source in a controlled ingestion stage, then discard credentials before isolated execution. Do not put broad Git credentials in the student grading environment. Likewise, worker tokens authenticate a worker and must be inaccessible to student code if used as result attestation. Preserve current loopback listeners and gateway routing; architectural boxes alone do not enforce access.

## Larger features to evaluate only with a new scope

### GitHub submission intake

For advanced courses, commit-based submission can reduce ZIP-handling friction and reproduce exactly what was pushed. It also requires account/repository mapping, GitHub permissions, webhook authentication, deduplication, branch/deadline semantics, fetch failure recovery and retention ownership. It introduces an external provider and persistent source histories outside the workstation.

If approved, a UVU design should verify webhook signatures and delivery IDs, authorize a known installation/repository/section, identify submissions by repository plus commit plus assignment release, and materialize only the chosen source snapshot into transient storage. A push notification is an event, not permission to grade arbitrary repository URLs. The inspected handler visibly checks headers and application associations; a complete signature-validation audit was not performed, so it is not a security template to copy unchanged.

Retain Canvas ZIP as the official pilot intake. GitHub practice or official grading would need explicit product/data approval; this research does not grant it.

### Browser IDEs

Theia illustrates the benefits of preconfigured course environments, but our Monaco browser workspace already addresses many introductory editing needs. A full IDE adds persistent volumes, terminals, package installation, network access, session proxying, idle cleanup and capacity planning. It can compete with grading and AI for host resources.

Before considering a remote IDE, measure an actual learning barrier that Monaco plus download/upload cannot address. For Pygame, ask whether a remote visual preview would help enough to justify interactive graphics infrastructure. Neither a VS Code-like interface nor a Kubernetes pod automatically supplies a suitable teaching environment. A later IDE should have a separate resource budget and approved storage/network scope.

### Student analytics and attempt selection

Anubis persists identity-linked submissions, commit IDs, test results and pipeline logs, and its grading selection helper searches submission histories by passing-test count. UVU must not inherit that best-attempt policy: unequal point weights can make passing-test count differ from score, and our official input is a staff-uploaded Canvas batch rather than a longitudinal attempt ledger. [Attempt selection](https://github.com/AnubisLMS/Anubis/blob/894ed020997ff22235e0d4b42a6f5dd9ea14f5e7/api/anubis/lms/autograde.py).

Our safe initial analytics are aggregate operational counts and transient cohort diagnostics during the 23-hour review window. Persistent student progress, behavioral insights, paste tracking or mastery histories need a separate educational/privacy decision. Detailed test/build logging shown in the reporting source also conflicts with our sanitized audit contract; borrow the stage vocabulary, not the payload logging.

## Proposed verification and maintenance

Use our existing synthetic workload to exercise reconciler failures and assert that expired workers cannot publish results or recreate deleted workspaces. If typed progress is added, test event reordering and cancellation as well as success. A hypothetical GitHub pilot would additionally need duplicate/replayed/forged webhook tests, repository mismatch cases, commit fetch failures, secret exclusion and approved external retention handling. These are proposed acceptance criteria, not completed experiments.

The inspected [license](https://github.com/AnubisLMS/Anubis/blob/894ed020997ff22235e0d4b42a6f5dd9ea14f5e7/LICENSE) identifies MIT. Its deployment spans significantly more infrastructure than our workstation stack, and the old generated design document demonstrates why documentation/code parity matters. Recent commits do not establish cluster security, deployment support or operating cost. Adopt reconciliation and clear capabilities first; defer the distributed LMS/IDE product until requirements justify it.
