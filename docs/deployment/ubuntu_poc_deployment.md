# Local POC & Workstation Deployment (Ubuntu 24.04 LTS / Dell Workstation)

This document wires the current repository into a fully functional local proof-of-concept stack. The long-term execution target is the **Dell Pro Max Tower T2 (Intel Core Ultra 7 265, 20 cores / 40 threads, 32GB RAM, NVIDIA RTX PRO 4500 Blackwell, Ubuntu 24.04.5 LTS)** with Kata Containers. The same compose file can run on other Linux hosts (e.g. a developer laptop) for backend and single-job grading smoke tests—see [Host capacity](#host-capacity).

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

Capacity planning in the specs is benchmarked on the Dell workstation (execution-slot cap `2-4`). A typical developer laptop (~8GB RAM, few cores) can idle the POC stack for API work and **one grading job at a time**, but will thrash under concurrent Judge0 work, heavy pygame runs, Kata, or IDE + browser + frontend together.

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

The script downloads the Kata static release, installs it under `/opt/kata`, links the Rust runtime shim (`/opt/kata/runtime-rs/bin/containerd-shim-kata-v2`) to `/usr/local/bin` and `/usr/bin`, installs an editable config at `/etc/kata-containers/runtime-rs/configuration.toml`, registers Docker runtime `kata-runtime`, restarts Docker, and verifies:

```bash
docker run --rm --runtime kata-runtime busybox uname -a
```

> [!IMPORTANT]
> **Do not run Judge0 with `privileged: true` under `kata-runtime`.** Kata responds to the
> privileged flag by hot-plugging every host `/dev` entry into the guest, which fails on this
> workstation with `get host path failed (os error 2)` (NVMe + ~20 snap loop devices).
> `privileged_without_host_devices = true` does **not** fix this: it is a containerd-CRI /
> CRI-O option with no equivalent under standalone Docker Engine, and is not a field in Kata's
> config schema — writing it to `configuration.toml` is silently discarded (confirmed on this
> host by inspecting the shim's parsed `Runtime` struct). `docker-compose.kata.yml` instead
> sets `privileged: false` with an explicit `cap_add` list, which is verified working.

> [!NOTE]
> `runtime-rs` reads `/etc/kata-containers/runtime-rs/configuration.toml`. The
> `/etc/kata-containers/configuration.toml` path belongs to the deprecated Go runtime and is
> ignored. Confirm which file is live before relying on any host tuning:
> ```bash
> sudo journalctl -u containerd --since "2 minutes ago" --no-pager | grep "load configuration from"
> ```

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

### Networking under Kata (required)

Docker's embedded DNS (`127.0.0.11`) does not reach into a Kata guest — the VM has its own
kernel and loopback, so Compose service names do not resolve. Two consequences, both already
handled but easy to reintroduce:

1. **Judge0 containers** need `extra_hosts` in `docker-compose.kata.yml` so `postgres` and
   `redis` resolve to the host gateway:
   ```yaml
   extra_hosts:
     - "postgres:host-gateway"
     - "redis:host-gateway"
   ```
   Without this, Judge0 boots but fails `db:create` with
   `could not translate host name "postgres" to address`, never passes its healthcheck, and
   blocks everything with `depends_on: judge0: service_healthy`.

2. **`backend` and `celery-worker` use `network_mode: "host"`**, so they are outside the
   Compose network entirely and service names never resolve for them. `extra_hosts` does not
   help here (host-network containers use the host's own `/etc/hosts`). Their `.env.local`
   values must use published ports on loopback:
   ```bash
   DATABASE_URL=postgresql+psycopg://autograder:<password>@127.0.0.1:5432/autograder
   REDIS_URL=redis://127.0.0.1:6379/0
   CELERY_BROKER_URL=redis://127.0.0.1:6379/0
   JUDGE0_URL=http://127.0.0.1:2358
   ```
   Note `.env.example` ships the container-network hostnames (`@postgres:5432`, `redis://redis`,
   `http://judge0:2358`), which **will not work** on this deployment. Symptom is
   `failed to resolve host 'postgres'` in the backend logs and nothing listening on port 8000.

Backend startup also runs Alembic migrations and seeding, so `:8000` refuses connections for a
while after `docker compose up` returns. Wait before concluding it failed.

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

Upstream Judge0 CE uses `privileged: true` for its isolate sandbox, and `docker-compose.poc.yml` keeps that for the plain (runc) POC path. **The Kata path does not**: `docker-compose.kata.yml` overrides it to `privileged: false` plus an explicit `cap_add` list, because privileged mode makes Kata fail to start the container at all (see the Kata section above). This was verified working end to end — submissions return `Accepted` on stock language 71 and custom 711, with pytest/Pillow/pygame imports intact.

If a capability turns out to be missing for some workload, add the specific capability rather than reverting to `privileged: true`, which does not function under Kata on this host.

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

> [!IMPORTANT]
> **Keep these enabled on the Dell workstation too — including on the Kata path.** Forcing
> cgroup v1 on the host via GRUB does work on Ubuntu 24.04.5 (systemd 255.4, below the ≥258
> threshold where forcing was removed), but it does not help here: isolate runs *inside* the
> Kata guest, which boots its own kernel with `cgroup_no_v1=all
> systemd.unified_cgroup_hierarchy=1` baked into the shipped runtime-rs config. The guest is
> cgroup-v2-only regardless of the host hierarchy, so the rlimits fallback is required on any
> Kata host, not just on cgroup-v2-only ones like Arch.

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

On the Dell Pro Max Tower T2 workstation with the **NVIDIA RTX PRO 4500 Blackwell GPU**, the recommended model is **`qwen2.5-coder:7b`** (VRAM footprint ~4.7 GB) or **`qwen2.5-coder:14b`** (~9 GB VRAM) served via Ollama (`LOCAL_LLM_ENDPOINT=http://127.0.0.1:11434/v1`). The default `qwen2.5:3b` remains a low-RAM CPU fallback.

## Celery Beat Scheduler (Periodic Tasks)

The autograder stack utilizes **Celery Beat** to schedule periodic background tasks such as the hourly workspace cleanup (`cleanup_expired_workspaces`).

`docker-compose.poc.yml` includes a `celery-beat` service that mirrors `celery-worker`'s
environment and dependencies, running Beat with its schedule file on the persistent
`backend_data` volume (`--schedule=/data/celerybeat-schedule`). It starts with the rest of the
stack — no separate process to remember.

Confirm it is scheduling:

```bash
docker compose -f docker-compose.poc.yml -f docker-compose.kata.yml logs celery-beat --tail 30
# expect: "Scheduler: Sending due task cleanup_expired_workspaces"
```

The cleanup task is hourly, so a freshly started stack will only show the startup banner until
the first interval elapses. Since the zero-retention contract depends on this task, verify an
actual dispatch — not just that the container is up — before treating retention as enforced.
