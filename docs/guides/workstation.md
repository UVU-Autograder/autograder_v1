# Operate the on-prem workstation

For web access/local frontend testing, use [Running](../running.md). For workstation changes, use authorized SSH access, the active checkout/account/env file and a drained maintenance window. The reported Dell address is `10.115.20.200`; confirm installed services rather than assuming templates are live.

## Prepare configuration

The Linux host needs Docker/Compose, `/dev/kvm`, Kata, Node/npm and Nginx; AI additionally needs its [GPU environment](ai.md). Preserve existing credentials/volumes. For first setup, copy [.env.example](../../.env.example) to `.env.local`, replacing development credentials.

### Verified Host Environment (Dell Precision 5860)

The dedicated on-prem workstation (`10.115.20.200`, hostname `CET-D24728`) operates with the following verified hardware, system, and network specifications:

- **Host Model:** Dell Precision 5860 Tower (`CET-D24728`).
- **Operating System & Kernel:** Ubuntu 24.04 LTS (kernel `6.17.0-1032-oem x86_64`).
- **Accelerator / GPU:** NVIDIA RTX PRO 4500 Blackwell (32,623 MiB / 32 GB VRAM).
  - VRAM allocation: ~30.6 GB allocated to KV cache and model weights (`vllm-cs1410.service`), ~1.5 GB free.
- **Local AI Feedback Service:** `vllm-cs1410.service` serving Gemma 4 12B QAT (W4A16) base model + `cs1410-p2c` reviewed LoRA adapter on `127.0.0.1:8001` (host loopback only).
- **Network Listeners & Perimeter:**
  - External Listeners (`0.0.0.0`): Nginx reverse proxy (`:80`) and OpenSSH (`:22`).
  - Internal Loopback Listeners (`127.0.0.1`): FastAPI backend (`:8000`), Next.js frontend (`:3000`), vLLM (`:8001`), Judge0 (`:2358`), PostgreSQL (`:5432`), Redis (`:6379`).
  - Network isolation: External connection attempts directly to `:8000` or `:3000` are actively refused; all application traffic is required to route through Nginx.
- **Storage & Volume Layout:**
  - Host filesystem `/data`: dedicated storage for base LLM model weights (`/data/models/gemma4-12b-qat-w4a16`) and LoRA adapters (`/data/models/adapters/`).
  - Docker Named Volumes:
    - `uvu-autograder_backend_data`: mounted at `/data` in backend and worker containers for instructor artifacts (`/data/artifacts`), zero-retention workspaces (`/data/workspaces`), and retention manifests (`/data/retention`).
    - `uvu-autograder_postgres_data`: persistent PostgreSQL 16 database storage (`/var/lib/postgresql/data`).
    - `uvu-autograder_redis_data`: persistent Redis 7 AOF store (`/data`).
- **Active Checkout & Runtime User:**
  - Path: `/home/dev/autograder_v1` on branch `dev`.
  - Service user: `dev` (uid 1003, gid 1003, groups: `sudo`, `docker`, `ollama`).

| Setting | Host-network requirement |
| --- | --- |
| `DATABASE_URL` | Application PostgreSQL at `127.0.0.1:5432`; match initialized credentials |
| `REDIS_URL`, `CELERY_BROKER_URL` | `redis://127.0.0.1:6379/0` |
| `JUDGE0_URL`, token | `http://127.0.0.1:2358`; matching service token |
| `ARTIFACT_STORAGE_DIR`, `SANDBOX_USE_CELERY` | `/data/artifacts`, `true` |
| Production identity | `ENVIRONMENT=production`, `AUTH_PROVIDER=microsoft`, mock disabled, non-default JWT secret and institutional Entra configuration |

Define this Bash helper from the checkout; use it for every stack operation:

```bash
dc() { docker compose --env-file .env.local -f docker-compose.yml -f docker-compose.kata.yml "$@"; }
```

Kata guests also use host-gateway PostgreSQL/Redis bindings (default `172.17.0.1`); verify merged bindings/firewall. Production internal services must remain restricted.

## Install Kata and start infrastructure

The [installer](../../scripts/install-kata-docker-runtime-ubuntu.sh) registers Kata and restarts Docker. For initial provisioning:

```bash
sudo bash scripts/install-kata-docker-runtime-ubuntu.sh
docker run --rm --runtime kata-runtime busybox uname -a
dc build judge0
dc up -d --build
dc ps
```

The [entrypoint](../../backend/scripts/docker-entrypoint.sh) waits for DB readiness, migrates and optionally seeds; the language-seed service registers 711. DB initialization scripts run only on empty volumes. Changing env passwords does not update existing database roles.

Kata uses QEMU/runtime-rs and `/etc/kata-containers/runtime-rs/configuration.toml`. Preserve the overlay's non-privileged explicit capabilities and Judge0 per-process/thread rlimits. Host GRUB changes do not fix guest cgroups. Add runtime dependencies in [Judge0's image](../../judge0.Dockerfile).

## Build and start the frontend and proxy

Set `frontend/.env.local` before building: approved Microsoft auth/app settings, `NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000` and `INTERNAL_BACKEND_URL=http://127.0.0.1:8000`.

```bash
npm --prefix frontend install
npm --prefix frontend run build
sudo systemctl daemon-reload
sudo systemctl enable --now autograder-frontend.service
sudo nginx -t
```

First install/adapt the [frontend unit](../../scripts/autograder-frontend.service) for the real user, checkout and npm path, and install the reviewed [HTTP](../../scripts/nginx/autograder-http.conf)/[TLS](../../scripts/nginx/autograder-tls.conf) proxy asset. Reload Nginx only after validation. Register the actual `/api/auth/microsoft/callback` origin with Entra; provision institutional DNS/certificates for live use.

The bundled proxy routes Next.js auth routes directly to Next.js, and internal services (FastAPI `:8000`, Next.js `:3000`, vLLM `:8001`, PostgreSQL `:5432`, Redis `:6379`, Judge0 `:2358`) bind strictly to `127.0.0.1` under host networking with verified loopback isolation, ensuring all external traffic passes through Nginx.

## Check health and monitor

```bash
curl -fsS http://127.0.0.1/api/health
curl -fsS http://127.0.0.1:2358/languages
dc exec -T backend celery -A app.integrations.celery.app inspect ping
dc exec -T dispatch-worker python -m app.domains.runs.dispatch_worker --health
dc exec -T cleanup-worker python -m app.domains.runs.cleanup_worker --health
systemctl status autograder-frontend.service --no-pager
```

Expect health, language 711, worker replies and daemon heartbeats. Admin monitoring shows durable unfinished work and cleanup/capacity failures. Inspect `ss -lntp`, runtime fields/VM processes and sanitized logs when diagnosing exposure or execution failures.

[Preflight](../../scripts/preflight_stack.py) exercises real synthetic grading and changes validation/session state; [host preflight](../../scripts/preflight_dell.sh) may build/start/stop services. Review mode before running against an existing host.

## Update or stop safely

Close intake at the proxy/API; retain DB, broker, runner and cleanup while grading drains. Check active/reserved jobs and durable unfinished counts; do not purge queues. Back up permitted data, record revision/image/migration, then update/migrate/restart and repeat synthetic health/grading/export/cleanup checks before reopening.

For a drained shutdown use `dc down` without `-v`. Prefer forward fixes; older retention guards or restoring student artifacts can re-expose expired data.

## Back up and restore

[Bash](../../scripts/backup_metadata.sh) and [PowerShell](../../scripts/backup_metadata.ps1) allowlist persistent metadata (`alembic_version`, `roles`, `users`, `courses`, `staff_access`, `sections`, `modules`, `assignments`, `assignment_configs`, `assignment_config_history`, `assignment_artifacts`, `scoring_items`) while strictly excluding ephemeral runs, workspaces, and student code (FERPA boundary).

Instructor test artifacts are extracted directly from Compose's named volume `backend_data` (`/data/artifacts` inside the `backend` container), falling back to `${REPO_ROOT}/data/artifacts` in local environments. Database operations respect `POSTGRES_USER` and `POSTGRES_DB` configuration overrides.

For a verified backup:

```bash
bash scripts/backup_metadata.sh --backup --output-dir /approved/metadata-backup
bash scripts/backup_metadata.sh --restore /approved/metadata-backup
```

PowerShell uses `-Backup -OutputDir <Path>` or `-RestoreDir <Path>`. Always test restores on an isolated matching schema. Schedule, frequency, retention, and offsite disaster recovery ownership remain documented in the backlog.

[Dispatch](../../backend/scripts/validate_dispatch_host.py) and [retention](../../backend/scripts/validate_retention_host.py) validators own synthetic batch/failure/outage procedures. Review CLI/phase order, keep manifests and run permission checks as the application user. They are maintenance tests, not daily health checks.
