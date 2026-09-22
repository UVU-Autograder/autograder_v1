# Official retention maintenance rollout

This procedure deploys the 23-hour review / 24-hour deletion lifecycle on the single
Dell host. Use synthetic fixtures for validation. Access denial is not evidence
of physical deletion; inspect both the official ZIP and directory after cleanup.
The host's clock, filesystem, and database must be available to establish that
evidence. Persistent failures remain visible and retryable.

## Preflight and maintenance

1. Connect to the campus network using Cisco AnyConnect (`campusvpn.uvu.edu`),
   then SSH to `dev@10.115.20.200`. Supply credentials at the SSH prompt; never
   put them in this document, command arguments, environment files, or evidence.
2. Identify the active checkout and Compose project from container labels. On the
   Dell these are `/home/dev/autograder_v1` and `uvu-autograder-poc`. Confirm the
   frontend systemd service's working directory before changing it.
3. Record the source commit, migration revision, image IDs, aggregate run counts
   grouped by status and original age, queue lengths, and Celery active/reserved/
   scheduled counts. Do not print task arguments, student files, result payloads,
   environment dumps, or database URLs. Preserve uncommitted host edits separately.
4. Stop the frontend and backend to close intake, stop the old `celery-beat`
   container, and let workers drain. Recheck every queue, active/reserved/scheduled
   task count, and unacknowledged broker delivery. Stop workers gracefully only
   after those counts are zero. Investigate outstanding work instead of purging
   queues or forcing worker termination.
5. Retain the previous application image for diagnosis, update the checkout to
   the reviewed revision, build the backend/worker images, and build the frontend
   while its systemd service is stopped. Do not copy ephemeral student volumes into
   a backup. Metadata/instructor backups must follow the approved backup scope.

Use the same Compose arguments throughout:

```bash
cd /home/dev/autograder_v1
DC=(docker compose --env-file .env.local -f docker-compose.yml -f docker-compose.kata.yml)
"${DC[@]}" build backend celery-worker cleanup-worker
```

Run repository-level backend tests with the full source layout mounted read-only,
a disposable database, and writable test caches. The runtime image alone omits
root-level Compose/build files referenced by repository tests. **Never run the
reset-database fixtures against the deployment database.**

```bash
"${DC[@]}" run --rm -T --no-deps --entrypoint python \
  -e DATABASE_URL=sqlite+pysqlite:///:memory: \
  -e ARTIFACT_STORAGE_DIR=/tmp/retention-tests/artifacts \
  -e RUFF_CACHE_DIR=/tmp/ruff-cache \
  -v "$PWD:/repo:ro" -e PYTHONPATH=/repo/backend -e REPO_ROOT=/repo \
  -w /repo/backend cleanup-worker -m pytest -q -p no:cacheprovider < /dev/null
```

## Migrate and reconcile

1. With intake and workers still stopped, apply the migration without seeding or
   starting an API process:

   ```bash
   "${DC[@]}" run --rm -T --no-deps --entrypoint alembic cleanup-worker upgrade head < /dev/null
   ```

2. Verify the schema is at `07abfea5f302` or a subsequent revision. Count official
   rows whose review/deletion deadlines differ from `created_at + 23 hours` and
   `created_at + 24 hours`; both counts must be zero. The rollout does not restart
   the retention clock. Existing data is classified by its original age.
3. Start `cleanup-worker` with `--no-deps` and confirm the initial reconciliation
   and heartbeat. Remove only the identified, stopped obsolete `celery-beat`
   container so it cannot resume the competing schedule. Do not remove volumes.
4. Check aggregate cleanup failures, overdue runs, and orphan errors. An unresolved
   breach needs investigation; a 410 response alone does not close it.

## Remove legacy Celery result copies

Confirm that the configured application Redis database belongs to this application;
the helper matches all `celery-task-meta-*` keys in that database. If other Celery
applications share it, establish ownership before deletion. Inspect aggregate
counts without reading or logging result payloads.

```bash
"${DC[@]}" run --rm -T --no-deps --entrypoint python backend \
  scripts/purge_legacy_task_results.py < /dev/null
"${DC[@]}" run --rm -T --no-deps --entrypoint python backend \
  scripts/purge_legacy_task_results.py --apply --confirm-quiesced-exclusive-app-db < /dev/null
```

Verify queues/unacknowledged deliveries and unrelated keys are preserved. Run Redis
`BGSAVE`, wait for completion with `rdb_last_bgsave_status=ok`, then, if AOF is
enabled, run `BGREWRITEAOF` and wait for completion with
`aof_last_bgrewrite_status=ok`. Check the persistence directory/manifest for leftover
superseded files; do not remove unknown files. A successful in-memory key deletion
does not by itself remove the old records from disk. Preserve other databases and
unrelated keys. Never use `FLUSHDB`, `FLUSHALL`, or volume deletion for this rollout.

## Synthetic host validation

`backend/scripts/validate_retention_host.py` operates on the real deployment database
and volume, creating only tagged synthetic summaries and fixture files. Choose an
explicit existing **synthetic assignment ID**. It refuses root execution because
root would bypass the permission-failure test. Its manifest is in the retention
control directory, outside deletable workspaces. Do not overwrite a previous
manifest; use `--state-file` to run a separate validation.

Run the script using the cleanup-worker image and deployment configuration, with
the current script bind-mounted read-only if it is newer than the image:

```bash
validate_retention() {
  "${DC[@]}" run --rm -T --no-deps --entrypoint python \
    -v "$PWD/backend/scripts/validate_retention_host.py:/app/scripts/validate_retention_host.py:ro" \
    cleanup-worker scripts/validate_retention_host.py "$@" < /dev/null
}
```

1. Keep intake and Celery stopped. Stop `cleanup-worker`, then run `prepare
   --assignment-id <synthetic-id>`. This creates fresh, expired, overdue/unwritable,
   and orphaned official fixtures, plus unrelated sentinel files. Never age or
   alter existing user runs to simulate expiry.
2. Stop the idle Judge0 services and Redis for the dependency-outage test; preserve
   their containers and volumes. Start only `cleanup-worker` with `--no-deps`.
   Run `check-failure` after its startup sweep. It verifies physical deletion of
   expired files and the orphan, preservation of fresh/unrelated files, a real
   partial-deletion failure, sanitized durable failure metadata, and a visible
   overdue breach. Record that Celery and Redis are stopped during this check.
3. Stop cleanup, run `release-failure`, restart cleanup, and run `check-recovery`.
   This proves startup recovery of the durable failed deletion and a healthy
   heartbeat while the broker remains unavailable.
4. Pause cleanup, run `prepare-outage`, stop PostgreSQL, and unpause cleanup. After
   the next sweep, run `check-outage`: the synthetic files must remain and the
   heartbeat must report unhealthy. Restart PostgreSQL, wait for its health check,
   then check the next cleanup sweep with `check-outage-recovery`.
5. Restore Redis and Judge0; keep staff intake closed. Start the new backend and
   verify authorized expired detail/export requests return 410, unauthorized
   requests authenticate first, aggregate summaries remain available, and admin
   monitoring reflects cleanup health. Verify synthetic manual cleanup returns
   200 and repeat cleanup succeeds. Verify new official tasks suppress result
   storage. Use a synthetic Judge0 execution to verify token deletion separately.
6. Run `finish` to clean all validation-owned files and sentinel files. The tagged
   aggregate summaries and sanitized manifest remain as evidence. Confirm no
   synthetic official files remain and the original fresh run has retained its
   original deadlines.

Do not close an acceptance item if its check was skipped. This procedure does not
substitute for full browser acceptance, a 200-submission capacity run, or immediate
execution cleanup tests across every timeout/cancellation path.

## Reopen and recovery

Start the updated Celery worker and frontend systemd service. Confirm backend,
frontend, Judge0, worker queues, and cleanup health, and record the deployed commit,
host date/configuration, commands, aggregate results, and any limitations in a
sanitized evidence report. Confirm there is no running hourly Celery cleanup job.

If deployment fails, keep intake closed and retain cleanup/reconciliation where
possible. Prefer a forward fix. Do not downgrade the retention schema or restore
old student ZIPs, workspaces, Celery results, or persistence files. Reopening an
older API that lacks the expiry guard would re-expose retained data; an image
rollback alone is therefore not an approved recovery for this milestone.
