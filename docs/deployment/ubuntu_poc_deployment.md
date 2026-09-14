# Local POC Deployment (Ubuntu 24.x target; other Linux OK for light use)

This document wires the current repository into a fully functional local proof-of-concept stack. The long-term execution target is the Ubuntu 24.x / Dell workstation with Kata. The same compose file can run on other Linux hosts (e.g. a developer laptop) for backend and single-job grading smoke tests—see [Host capacity](#host-capacity).

This is not a live-student production approval document. Use synthetic, fake, or approved anonymized test code while validating the end-to-end autograder path.

## Stack

- Frontend: run separately with the existing frontend workflow; this backend POC compose file does not build or modify frontend assets.
- Backend: FastAPI on `http://localhost:8000`
- Database: one PostgreSQL instance with two databases (`autograder` for the app, `judge0` for Judge0 CE), migrated by Alembic at backend startup
- Queue/state: Redis
- Worker: Celery using the `sandbox`, `official`, and `default` queues
- Execution API: local Judge0 CE on `http://localhost:2358` (image tag `uvu-autograder-judge0:latest`)
- Isolation: Kata Containers is expected to be configured on the Ubuntu host and validated operationally outside the app container

## Files

- `docker-compose.poc.yml`: local POC stack for Postgres, Redis, Judge0, backend, and Celery worker.
- `judge0.Dockerfile`: custom Judge0 image with Python 3.11.9 and allowlisted course deps; tagged locally as `uvu-autograder-judge0:latest`.
- `scripts/init_poc_databases.sh`: POSIX `sh` script that creates the `judge0` role (`CREATEDB`) and database on first Postgres volume init. Judge0’s Rails entrypoint runs `db:create`, which requires `CREATEDB` even when the database already exists.
- `scripts/seed_judge0_language_311.sql`: registers language ID `711` after Judge0 is healthy (cannot run in `initdb` because the `languages` table does not exist yet).
- `backend/Dockerfile`: backend runtime image that installs Python dependencies, waits for Postgres, runs Alembic, and optionally seeds development data.
- `.env.example`: local POC environment template (copy to `.env.local`; do not commit real secrets).
- `backend/scripts/docker-entrypoint.sh`: backend container startup script.

## First Run

From the repository root:

```bash
cp .env.example .env.local
# Edit .env.local secrets if needed.
# On low-RAM laptops, set JUDGE0_MAX_CONCURRENT=1 (see Host capacity).

# First time (or after judge0.Dockerfile / allowlisted deps change):
docker compose --env-file .env.local -f docker-compose.poc.yml build judge0

# Day-to-day: reuses the local uvu-autograder-judge0:latest tag
docker compose --env-file .env.local -f docker-compose.poc.yml up -d --build
```

`up --build` rebuilds backend/celery when their Dockerfile or context changes; Judge0 is only rebuilt when you explicitly `build judge0` (or change its Dockerfile and force a rebuild). The Judge0 image is **local-tag only** (no registry): `uvu-autograder-judge0:latest`.

Python in `judge0.Dockerfile` is built **without** `--enable-optimizations` so POC rebuilds stay shorter. Revisit PGO later only if the Dell image needs it.

Then open:

- UI: run the existing frontend separately when needed (`NEXT_PUBLIC_API_BASE_URL=http://localhost:8000`).
- API health: `http://localhost:8000/health`
- Judge0 languages: `http://localhost:2358/languages` (should include id `711` / Python 3.11.9)

The seeded staff account is `dev.staff@uvu.edu`. The POC compose file enables mock login with `ENABLE_MOCK_LOGIN=true`; turn this off for any non-local deployment.

Stop the stack:

```bash
docker compose -f docker-compose.poc.yml down
```

### Host capacity

Capacity planning in the specs assumes the **32GB Dell** workstation (default execution-slot cap `2`). A typical developer laptop (~8GB RAM, few cores) can idle the POC stack for API work and **one grading job at a time**, but will thrash under concurrent Judge0 work, heavy pygame runs, Kata, or IDE + browser + frontend together.

On small hosts:

```bash
# in .env.local
JUDGE0_MAX_CONCURRENT=1
```

Skip Kata on laptops; use `docker-compose.kata.yml` only on the Ubuntu/Dell host.

### Volume and database caveats

- Switching from the older dual-Postgres layout to the single `postgres` service uses volume `postgres_data`. First bring-up after that change is a clean DB (re-seed).
- `scripts/init_poc_databases.sh` runs **only** on first init of an empty data volume. Changing the script does nothing until you recreate the volume, e.g. `docker compose -f docker-compose.poc.yml down -v` (destroys POC DB data).
- Compose defaults include local-only passwords (`autograder_dev_password`, `judge0_dev_password`). Override them in `.env.local` for any shared or long-lived machine.

## Optional Kata Runtime Setup

Kata is host-level infrastructure, not a FastAPI dependency. Install and register it with Docker on the Ubuntu dev machine before starting the stack:

```bash
sudo scripts/install-kata-docker-runtime-ubuntu.sh
```

The script downloads the Kata static release, installs it under `/opt/kata`, registers Docker runtime `kata-runtime`, restarts Docker, and verifies:

```bash
docker run --rm --runtime kata-runtime busybox uname -a
```

Then start the POC stack with the Kata override:

```bash
docker compose --env-file .env.local \
  -f docker-compose.poc.yml \
  -f docker-compose.kata.yml \
  up --build
```

If the dev machine uses a different Docker runtime name, set it in `.env.local`:

```bash
KATA_DOCKER_RUNTIME=kata-runtime
```

## Database Behavior

The backend container waits for `DATABASE_URL`, then runs:

```bash
alembic upgrade head
```

When `SEED_DATABASE=true`, it also runs:

```bash
python -m app.db.seed
```

The seeded data uses `backend/app/db/seeds` through `seed://...` artifact references. Those seed packages ship inside the backend image and resolve relative to `app/db/seeds`.

Judge0 uses the same Postgres container on database `judge0`. Custom language `711` is inserted by the one-shot `judge0-language-seed` service after Judge0 finishes creating its schema.

## Judge0 And Kata

The compose file starts Judge0 CE and its worker locally. The app sends zipped student work to Judge0 through the existing backend grading pipeline and deletes Judge0 submissions after result retrieval.

`judge0` and `judge0-worker` use `privileged: true`. That matches official Judge0 CE (isolate sandbox) and is expected for local POC; do not treat removing it as a simple hardening step without proving isolate still works. Long-term isolation on the Dell host is Kata (`docker-compose.kata.yml`), not dropping privileges alone.

Judge0 CE `1.13.1` is Debian Buster (EOL). `judge0.Dockerfile` retargets apt to `archive.debian.org` and builds as `USER root` during install, then switches back to `judge0`.

### Cgroups: Judge0 isolate vs modern Linux

Stock Judge0 1.13.1 ships **isolate 1.8.1**, which expects **cgroup v1** paths such as `/sys/fs/cgroup/memory/box-N/tasks`. Modern hosts (Arch with systemd ≥258, and many current kernels) run **cgroup v2 only**. Symptoms:

- API and containers look healthy
- Submissions return status **13 Internal Error** with message like `Cannot write /sys/fs/cgroup/memory/box-…/tasks: No such file or directory`

**Do not rely on** `systemd.unified_cgroup_hierarchy=0` on this Arch host: systemd **261** has removed forcing cgroup v1 (see ArchWiki *Cgroups* historical note). Mounting `/sys/fs/cgroup` into the container also does not create missing v1 controllers.

**POC workaround (enabled in `docker-compose.poc.yml`):** set

```yaml
ENABLE_PER_PROCESS_AND_THREAD_TIME_LIMIT: "true"
ENABLE_PER_PROCESS_AND_THREAD_MEMORY_LIMIT: "true"
```

on both `judge0` and `judge0-worker`. That makes Judge0 omit isolate’s `--cg` flag and use process rlimits instead, which works on cgroup v2. Isolation is weaker than cgroup accounting; fine for laptop POC, not a substitute for Kata on the Dell workstation.

**Longer-term:** upgrade to isolate v2 + Judge0 cgroup-v2 entrypoint changes (upstream PR discussion), or run on a host that still supports cgroup v1 / Kata validation path.

Verify after recreate:

```bash
# stock Python 3.8 language id 71, or custom 711 after seed
curl -sS -X POST "http://127.0.0.1:2358/submissions?base64_encoded=false&wait=true" \
  -H "Content-Type: application/json" \
  -H "X-Auth-Token: $JUDGE0_AUTH_TOKEN" \
  -d '{"source_code":"print(12345)","language_id":71}'
# expect status.description Accepted (or similar success), stdout "12345\n"
```

Kata Containers is host-level execution isolation. The repository cannot configure GRUB or prove Kata isolation from inside the FastAPI image. The optional `docker-compose.kata.yml` override requires a host Docker runtime named `kata-runtime`. Before treating the Ubuntu machine as the intended execution target, collect operational evidence on the host that:

- Docker/containerd uses the Kata-capable runtime expected by the Judge0 execution path.
- Judge0 submissions execute under the expected isolated runtime.
- `DELETE /submissions/{token}` works and deleted submissions are no longer retrievable.
- Temporary **execution** workspaces (`ag_grade_*`, Judge0 payloads) are removed after success, failure, timeout, and cancellation.
- Temporary **official review** workspaces (`workspaces/official_{run_id}/`, including per-student directories for Monaco preview) are retained ≤24h or until staff cleanup, then removed by `cleanup_expired_workspaces` or `POST .../runs/{run_id}/cleanup`.

## Environment Notes

Local POC defaults intentionally keep CORS and frontend API access on localhost. Tailscale/SSH access should be handled at the host/network layer until UVU assigns a hosted environment.

Use plain environment files for now, but do not commit real secrets. The existing tracked `backend/.env` is left unchanged for compatibility with the current development workflow.

## FERPA/Local LLM Scope

The current documentation says the technical design reduces FERPA risk, but live official grading still depends on institutional approval and direct-control requirements. Use this POC with synthetic, fake, or approved anonymized data unless UVU approval has been explicitly documented for live student data.

**Project status:** UVU Software Approval for live official grading is in progress. Local/on-prem POC use of real Canvas ZIPs is acceptable for authorized staff debugging when student-identifying data remains ephemeral only (≤24h), Postgres/logs stay aggregate-only, and exports are not committed to the repository. See [ferpa_analysis.md](../core/ferpa_analysis.md).

Local LLM credentials can be supplied through environment variables, but AI feedback for live, pseudonymous, or real student-derived code should remain disabled unless the UVU approval checklist is complete.

## Celery Beat Scheduler (Periodic Tasks)

The autograder stack utilizes **Celery Beat** to schedule periodic background tasks such as the hourly workspace cleanup (`cleanup_expired_workspaces`).

`docker-compose.poc.yml` does not include a Celery Beat service. Run Beat separately when you need periodic cleanup:

```bash
# From the backend venv / container shell:
celery -A app.integrations.celery.app beat --loglevel=info
```

Make sure the Celery Beat scheduler process is running to guarantee that temporary student workspaces and grade review exports are cleaned up after their 24-hour expiration window.
