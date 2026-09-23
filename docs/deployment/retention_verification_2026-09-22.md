# Retention deployment verification — 2026-09-22

Read-only follow-up on the Dell host, `10.115.20.200`, at approximately
18:49–18:54 UTC. Deployed checkout: `d4d76bf`; local checkout: `2bf4739`
(the additional commit is documentation). No service restart, submission deletion,
or new grading workload was performed during this follow-up.

## Verified current state

- Backend, Celery worker, Judge0, Judge0 worker, PostgreSQL, Redis, and the independent
  cleanup worker are running. Cleanup, PostgreSQL, Redis, and Judge0 report healthy.
  Nginx and `autograder-frontend` are active. No Celery beat container is running.
- The renamed Compose project still uses the existing
  `uvu-autograder-poc_backend_data` volume at `/data`.
- `/health`, `/api/health`, `/staff/login`, and `/sandbox` return HTTP 200 through
  Nginx on port 80. This is HTTP verification; TLS remains a separate gate.
- Alembic revision is `07abfea5f302`. No official run has deadlines inconsistent
  with its original `created_at + 23 hours` / `created_at + 24 hours`.
- Cleanup heartbeat is current and healthy, with zero failed runs, zero overdue
  runs, and zero orphan errors. Aggregate official state is four deleted runs and
  one available run.
- The synthetic host-validation manifest records completion at
  `2026-09-22T04:45:45.553738+00:00`. None of its official directories or ZIPs remain.
- Through the HTTP proxy, an unauthenticated expired detail request returns 401;
  authenticated expired details, CSV, and feedback exports return 410. The same
  run's aggregate summary returns 200. Admin monitoring returns 200 and reports
  the same healthy cleanup metrics.
- Official Celery tasks have `ignore_result=True`. All inspected broker queues and
  unacknowledged-delivery counts are zero.
- Redis reports successful RDB save and AOF rewrite. The 57 current Celery result
  records are recent: 54 model-validation results and three sandbox-grading results,
  all expiring within one hour. These are other workflows' records, not evidence
  that legacy official result copies have returned. Sandbox retention remains a
  distinct lifecycle scope.
- No `ag_grade_*` execution directories remain in the backend or Celery worker's
  `/tmp` at the time of inspection.
- Fresh local frontend verification: all 50 tests in 12 files passed on `2bf4739`.
- Fresh local backend verification: all 277 tests passed on `2bf4739`, with
  `DATABASE_URL=sqlite+pysqlite:///:memory:` explicitly isolating the test database.

## Open follow-up

Judge0 contains four completed submissions (status 3), three older than 24 hours.
The oldest was created on September 17; the newest on September 22. None contains
the generated autograder runner marker or an `additional_files` bundle. This is
consistent with direct smoke submissions but does not establish their provenance.
No source, tokens, filenames, or result bodies were printed, and none was deleted
by this read-only inspection.

Investigate ownership, remove confirmed disposable remnants using the authorized
cleanup path, and ensure direct smoke-test tooling deletes its tokens in `finally`.
Keep immediate execution-cleanup acceptance open until this is resolved; official
workspace retention health does not prove Judge0 is free of retained executions.

## Next implementation milestone

Bounded official-batch scheduling remains the next main code milestone:

- Intake still calls `reserve_execution_slots(submission_count)`, so a 200-item ZIP
  cannot enter an empty queue capped at 50 waiting executions.
- `grade_official_run` still processes the batch as one Celery task. The deployed
  soft/hard limits remain 120/180 seconds, with worker concurrency two.
- Admission still falls back to process-local counters on Redis errors, so outage
  behavior and crash recovery cannot yet establish a global capacity guarantee.

Separate retained intake from bounded execution dispatch, make retries and slot
ownership recoverable, and preserve the existing retention checks. Acceptance
requires a real 200-submission run with concurrent sandbox traffic, worker/broker
recovery, and correct exports; raising queue or whole-batch timeout limits alone
does not meet that gate.
