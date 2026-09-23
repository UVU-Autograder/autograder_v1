# Bounded official dispatch rollout and host verification — 2026-09-23

Verification report on Dell workstation (`10.115.20.200`) executed on 2026-09-23 between 16:11 and 16:50 UTC.
Deployed commit: `50330ecbeb86b8706994cd3881863b1e6afe8ba5` (`codex/bounded-official-dispatch`).
Database schema revision: `a82bd9410e21`.

## Deployment and service status

- Container services running and healthy under `docker compose --env-file .env.local -f docker-compose.yml -f docker-compose.kata.yml`:
  - `uvu-autograder-backend-1` (Image: `7bd2201225f1`, host networking)
  - `uvu-autograder-celery-worker-1` (Image: `dacbccc6338b`)
  - `uvu-autograder-cleanup-worker-1` (Image: `7cb13855c796`, healthy)
  - `uvu-autograder-dispatch-worker-1` (Image: `9c937db5baa3`, healthy)
  - `uvu-autograder-judge0-1` (Image: `2c725f7f7d82`, healthy)
  - `uvu-autograder-judge0-worker-1` (Image: `2c725f7f7d82`)
  - `uvu-autograder-postgres-1` (Image `postgres:16-alpine`, healthy)
  - `uvu-autograder-redis-1` (Image `redis:7-alpine`, healthy)
- Host systemd services active:
  - `nginx.service` (reverse proxy on port 80 routing `/api` and `/health` to FastAPI and pages to Next.js)
  - `autograder-frontend.service` (Next.js serving on port 3000)
- Endpoints verified through port 80:
  - `/health` -> 200 OK
  - `/api/health` -> 200 OK
  - `/sandbox` -> 200 OK
  - `/api/staff/admin/monitoring` -> 200 OK, reporting `dispatch_service_healthy: true`, `cleanup_service_healthy: true`, `waiting_executions: 0`, `active_executions: 0`

## Workload verification: 200-submission batch

Executed synthetic 200-submission official run (Run 9) using `backend/scripts/validate_dispatch_host.py` on assignment `cs1400/simple-python-functions`:

- **Execution duration:** 1351.44 seconds (~22.5 minutes), well below the 40-minute (2400s) SLA gate.
- **Completion rate:** 200 / 200 submissions scored (100% completion, 0 failures, 0 timeouts).
- **Concurrent sandbox grading:** Concurrent sandbox submission submitted during the run completed in 20.05 seconds, validating execution fairness and capacity sharing within the 2-active / 50-waiting slot limits.
- **Export packaging:** 200-row CSV generated and 200 individual HTML feedback reports packaged into `feedback.zip` in 0.0068 seconds, well below the 2-minute (120s) packaging gate.
- **Physical retention cleanup:** Verified physical absence of workspace and archive files upon deletion (`cleanup` phase confirmed `physical_absence: true`).

## Resiliency and fault-tolerance verification

1. **Worker restart during active grading (Run 10):**
   - Prepared 10-submission run.
   - Restarted `celery-worker` and `dispatch-worker` containers concurrently while grading was active (`state: run`, 1 completed).
   - Both workers resumed reconciliation; remaining submissions were dispatched and graded.
   - Completed all 10 submissions in 72.08 seconds (10 CSV rows, 10 feedback files, 0 failures, 0 duplicates).
   - Post-run cleanup confirmed physical absence.

2. **Broker interruption during active grading (Run 11):**
   - Prepared 10-submission run.
   - Injected Redis outage by pausing the `redis` container for 5 seconds while grading was active (`state: run`, 1 completed), then unpausing.
   - Workers reconnected, reconciled ticket leases and queues, and resumed dispatching.
   - Completed all 10 submissions in 70.15 seconds (10 CSV rows, 10 feedback files, 0 failures, 0 duplicates).
   - Post-run cleanup confirmed physical absence.

## Judge0 execution-retention follow-up

- Investigated the four retained completed Judge0 submissions observed during the 2026-09-22 inspection (tokens `57b24362-2285-4528-bf03-14c0f25f5861`, `d1d6b22d-3967-48b7-9a78-a0d59e5f38f1`, `ab5ff200-fe1d-4453-9a2b-dfce6a9f7339`, `245fd738-ea1a-4db2-951c-a363b4fe0773`).
- Established provenance: Disposable setup preflight / smoke test snippets (`print(12345)`, `import sys; print(sys.version)`, etc.) from initial host provisioning; contained no student code, student identifiers, or attached file bundles.
- Removed all four records using the authorized `DELETE /submissions/{token}` Judge0 API.
- Confirmed post-cleanup table state: 0 submissions in Judge0 database.
- Confirmed application runtime behavior: `execute_pytest_in_judge0` always executes `delete_submission` in its `finally` block, ensuring zero residual executions in Judge0.
