# Bounded official dispatch rollout and host validation

This procedure updates the Dell workstation from whole-batch grading to durable
submission dispatch. It requires a drained maintenance window because the task
signature, execution reservation authority, and database schema change together.
Use only synthetic fixtures for validation. Keep the cleanup worker running
throughout; the new dispatcher is separate from cleanup.

## Quiesce and inspect

Connect through Cisco AnyConnect, then SSH to `dev@10.115.20.200`. Never put SSH,
database, or API credentials in command arguments, files in this repository, or
evidence. Work in `/home/dev/autograder_v1` and use the same Compose overlays for
every step:

```bash
DC=(docker compose --env-file .env.local -f docker-compose.yml -f docker-compose.kata.yml)
```

1. Record the old commit, Alembic revision, container health, sanitized aggregate
   run counts by state, queue lengths (`official`, `sandbox`, `default`, `unacked`),
   and Celery active/reserved/scheduled counts. Never print task arguments.
2. Stop `autograder-frontend` and the `backend` container to close intake.
   Leave Redis, PostgreSQL, Judge0, and cleanup running. Let Celery drain to
   zero active/reserved/scheduled tasks and all four broker queues to zero.
   Stop the Celery worker gracefully. Do not purge queues or kill live grading.
3. Ensure no official run remains `queue` or `run`. If one does, recover or
   resolve it with the old code before migration. The migration intentionally
   leaves existing run rows unchanged; tokenless old broker deliveries are
   ignored by the new worker.
4. Keep a rollback reference to the old commit/image. Back up only approved
   metadata and instructor-owned assets; exclude student workspaces/exports.

## Deploy

1. Update the clean checkout to the reviewed revision. Build `backend`,
   `celery-worker`, `dispatch-worker`, and `cleanup-worker`. Build the frontend
   while its systemd service is stopped. Do not replace volumes.
2. Apply Alembic revision `a82bd9410e21` using a one-off backend image with
   seeding disabled and stdin closed. Confirm the new `execution_tickets`,
   `official_dispatches`, and aggregate `export_packaging_seconds` fields exist.
3. Start Celery with its configured `sandbox,official,default` queues, then start
   `dispatch-worker`. Confirm `python -m app.domains.runs.dispatch_worker --health`
   succeeds and admin monitoring reports a healthy dispatcher, zero waiting,
   and zero active executions. Confirm cleanup heartbeat still reports healthy.
4. Start backend, then `autograder-frontend`. Check `/health`, `/api/health`,
   mock staff sign-in in the development deployment, official status, and
   sandbox upload through the reverse proxy. Verify the browser run page and
   admin monitoring card. The 50 waiting cap does not block retained official
   intake; the default retained limits are 200 per upload and 1,000 unfinished.

Do not start the dispatcher until the migration has completed. When rolling
back, first stop intake, drain both queues and active work, stop the dispatcher
and new worker, and return to the old commit/image. Avoid a schema downgrade
while new run records exist. Restore the previous code with the additive schema
left in place, then decide on data migration after inspecting aggregate state.

## Synthetic workload and evidence

The host script runs inside the new backend image using the shared `/data`
volume and seeded `cs1400/simple-python-functions` assignment. Its manifest
contains only a run ID, a count, and timestamps; its output contains aggregate
counts and timing. It does not print task arguments, code, student filenames,
identifiers, or feedback. Use one-off containers with `-T` and `< /dev/null`.

```bash
"${DC[@]}" run --rm -T --no-deps --entrypoint python backend \
  scripts/validate_dispatch_host.py prepare --count 200 < /dev/null
"${DC[@]}" run --rm -T --no-deps --entrypoint python backend \
  scripts/validate_dispatch_host.py watch --timeout-seconds 2400 < /dev/null
"${DC[@]}" run --rm -T --no-deps --entrypoint python backend \
  scripts/validate_dispatch_host.py cleanup < /dev/null
```

If SSH disconnects, run `check` and then `watch` against the existing manifest;
do not create a second run. Verify 200 terminal results, 200 CSV rows, 200 HTML
feedback files, total duration under 40 minutes, export packaging under two
minutes, a concurrent sandbox completion, capacity at or below two active and
50 waiting, and no remaining synthetic official files after cleanup. Record
the commit, migration, image IDs, workload, timing, aggregate outcome, and
sanitized log/health observations. Also inject a reversible Redis interruption
and a worker restart during separate synthetic runs, verify recovery and no
duplicate exports, and verify physical retention cleanup. A local mocked 200
run proves code paths but does not close the Dell benchmark.

The institutional approval, Entra authentication, TLS, and direct-port
hardening gates remain separate from this dispatcher rollout.
