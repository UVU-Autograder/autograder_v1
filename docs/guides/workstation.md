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
- **Local AI Feedback Service:** `vllm-cs1410.service` serving Gemma 4 12B QAT (W4A16) base model + `cs1410-p3b` reviewed LoRA adapter on `127.0.0.1:8001` (host loopback only).
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

The workstation environment sets `COMPOSE_FILE=docker-compose.yml:docker-compose.kata.yml` in `.env` so standard `docker compose` invocations automatically load the Kata runtime overlay. Alternatively, use the provided wrapper script [`scripts/dc.sh`](../../scripts/dc.sh) or Bash helper for stack operations:

```bash
# Using the wrapper script:
bash scripts/dc.sh ps

# Or via Bash helper function:
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

On startup, the FastAPI application lifespan verifies that language 711 is present in Judge0, automatically seeding it into PostgreSQL if missing. If Judge0's PostgreSQL database is ever reset independently without restarting the backend, re-seed language 711 manually:
```bash
dc run --rm judge0-language-seed
# or directly via SQL:
docker exec -i uvu-autograder-postgres-1 psql -U autograder -d judge0 < scripts/seed_judge0_language_311.sql
```

Kata uses QEMU/runtime-rs and `/etc/kata-containers/runtime-rs/configuration.toml`. Preserve the overlay's non-privileged explicit capabilities and Judge0 per-process/thread rlimits. Host GRUB changes do not fix guest cgroups. Add runtime dependencies in [Judge0's image](../../judge0.Dockerfile).

## Pinned grading runtime profile (Judge0 & Kata)

The execution sandbox operates on a single pinned grading profile to ensure exact reproducibility between instructor authoring and student sandbox execution ([Issue #28](https://github.com/UVU-Autograder/autograder_v1/issues/28)):

| Parameter | Specification | Source of truth |
| --- | --- | --- |
| **Base Image** | `judge0/judge0:1.13.1` (`linux/amd64`, Debian Buster archive mirrors) | [judge0.Dockerfile](../../judge0.Dockerfile) |
| **Language ID** | `711` (`Python (3.11.9)`) | [scripts/seed_judge0_language_311.sql](../../scripts/seed_judge0_language_311.sql) |
| **Python Binary** | `/usr/local/python-3.11.9/bin/python3.11` (compiled CPython 3.11.9) | [judge0.Dockerfile](../../judge0.Dockerfile) |
| **Package Installer** | `pip==24.3.1`, `setuptools==75.8.0` | [judge0.Dockerfile](../../judge0.Dockerfile) |
| **Test Runner** | `pytest==8.4.2` | [judge0.Dockerfile](../../judge0.Dockerfile) |
| **Allowlisted Packages** | `pillow==11.3.0`, `pygame==2.6.1`, `tabulate==0.9.0` | [judge0.Dockerfile](../../judge0.Dockerfile) |
| **Memory Cap (Sandbox)** | `256 MB` (`262144 KB`), container hard limit `256 MB` | `DEFAULT_MEMORY_LIMIT` in [client.py](../../backend/app/integrations/judge0/client.py) |
| **Execution Timeouts** | Per-run `30s` (host cap `<= 60s`), wall time `20s` | `TEST_EXECUTION_TIMEOUT_SECONDS` in [docker-compose.yml](../../docker-compose.yml) |
| **Upload Payload Cap** | `50 MB` (`52,428,800 bytes`) | `MAX_UPLOAD_BYTES` in [audit_deployment_readiness.py](../../scripts/audit_deployment_readiness.py) |
| **Headless Drivers** | `SDL_VIDEODRIVER="dummy"`, `SDL_AUDIODRIVER="dummy"` | [pygame_test_helpers.py](../../backend/app/db/seeds/shared/pygame_test_helpers.py) |

## Dependency maintenance cadence and rollback runbook

Package updates, OS upgrades, and runtime adjustments must follow an explicit review cadence and verified rollback procedure:

### 1. Recurring Maintenance Cadence
- **Schedule:** Monthly review executed on the 1st of every calendar month.
- **Vulnerability Scanning:**
  - Python packages: `pip audit` against the backend virtualenv and the Judge0 runtime profile.
  - Node / Web packages: `npm audit` within `frontend/`.
  - Base OS & Containers: `docker scout cves` or `trivy image uvu-autograder-judge0:latest`.
- **Dependency Drift Guard:** Do not install unpinned packages; updates must explicitly update both `judge0.Dockerfile` and `backend/requirements.txt` with tested pin values.

### 2. Candidate Update Validation Procedure
Before deploying any dependency or runtime image change to production:
1. **Create Pre-Update Image Backup:**
   ```bash
   BACKUP_TAG="uvu-autograder-judge0:$(date +%Y%m%d)-backup"
   docker tag uvu-autograder-judge0:latest "$BACKUP_TAG"
   ```
2. **Build Candidate Image:**
   ```bash
   dc build judge0
   ```
3. **Execute Static & Runtime Contract Checks:**
   ```bash
   backend/venv/Scripts/python -m pytest backend/tests/test_judge0_custom_runtime.py
   backend/venv/Scripts/python -m pytest backend/tests/test_seed_integrity.py
   ```
4. **Execute Calibration Suite:**
   Run the full pilot calibration test suite across OOP (`ds1`), I/O (`lab1`), and Pygame (`lab6`):
   ```bash
   backend/venv/Scripts/python -m pytest backend/tests/test_grading_calibration.py
   ```
5. **Run Deployment Readiness Audit:**
   ```bash
   backend/venv/Scripts/python scripts/audit_deployment_readiness.py
   ```

### 3. Immediate Rollback Runbook
If an updated package causes subtle grading discrepancies, timeout regressions, or AST check failures:
1. **Dismount Active Containers:**
   ```bash
   dc stop judge0 judge0-worker
   ```
2. **Retag Last Known Good Image:**
   ```bash
   docker tag "$BACKUP_TAG" uvu-autograder-judge0:latest
   ```
3. **Restart Judge0 Execution Engine:**
   ```bash
   dc up -d --no-deps judge0 judge0-worker
   ```
4. **Verify Rollback Integrity:**
   ```bash
   backend/venv/Scripts/python -m pytest backend/tests/test_grading_calibration.py
   curl -fsS http://127.0.0.1:2358/languages
   ```
   Confirm language ID 711 returns healthy and all calibration manifests pass without discrepancy.

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

## Official grading-package rollout and worker coordination

When an official Canvas batch is uploaded, intake captures and validates an immutable [`grading_package`](../../backend/app/domains/runs/grading_package.py) containing rubrics, pytest harnesses, and execution parameters ([Issue #23](https://github.com/UVU-Autograder/autograder_v1/issues/23)). To prevent version drift between `backend`, `celery-worker`, `dispatch-worker`, and `cleanup-worker`, every update must follow this coordinated drain-and-rollout protocol via [rollout_grading_package.sh](../../scripts/rollout_grading_package.sh):

### 1. Intake Pause & Queue Drainage
1. **Pause External Intake:** Restrict new uploads at the Nginx reverse proxy (`sudo systemctl stop nginx` during a scheduled maintenance window) while retaining `postgres`, `redis`, `judge0`, `celery-worker`, `dispatch-worker`, and `cleanup-worker` so in-flight work finishes cleanly.
2. **Wait for Queue Drain (Never Purge Queues):** Verify that all queued/running official runs (`RunSummary.status IN ('queue', 'run')`) and active sandbox execution tickets (`ExecutionTicket.state IN ('waiting', 'active')`) reach zero:
   ```bash
   bash scripts/rollout_grading_package.sh --dry-run
   ```

### 2. Coordinated Container Rebuild & Rollout
Run the automated rollout script to back up persistent metadata, rebuild and restart `backend`, `celery-worker`, `dispatch-worker`, and `cleanup-worker` from the identical Git revision, and verify daemon health:
```bash
bash scripts/rollout_grading_package.sh --course cs1410 --assignment lab1
```

Under the hood, the script executes:
1. Pre-rollout metadata backup (`bash scripts/backup_metadata.sh --backup`).
2. Simultaneous container rebuild and restart:
   ```bash
   dc up -d --build backend celery-worker dispatch-worker cleanup-worker
   ```
3. Health verification across `http://127.0.0.1:8000/api/health`, Celery `inspect ping`, `dispatch_worker --health`, and `cleanup_worker --health`.

A deploy that changes the grading runner or helper, a pinned dependency, or an instructor file makes every affected assignment's reference inventory stale, and the sandbox answers uploads with HTTP 400 ("requires instructor reference validation") until each model solution is graded again. Re-validate them all from the checkout (`--dry-run` lists them first):

```bash
docker exec -i uvu-autograder-backend-1 python - --wait < backend/scripts/revalidate_references.py
```

### 3. Post-Rollout Synthetic Package Smoke Verification
Immediately after container restart (and automatically as step 4 of `scripts/rollout_grading_package.sh`), [validate_grading_package_host.py](../../backend/scripts/validate_grading_package_host.py) executes inside the deployed `backend` container:
```bash
dc exec -T backend python scripts/validate_grading_package_host.py --course cs1410 --assignment lab1
```
Confirm all boolean checks report `"passed": true`:
- `workload_drained`: No unfinished official batches or active tickets exist.
- `synthetic_fixture_matches_captured_config`: Captured `GradingPackage` matches the model assignment configuration.
- `captured_runner_submitted` & `captured_parameters_submitted`: Frozen runner source and CPU/wall/memory limits are submitted to Judge0 regardless of process-local setting overrides.
- `deleted_submission_non_retrievable` & `one_execution_deleted`: Judge0 token is deleted immediately after execution and returns HTTP `404`.
- `model_passed_captured_grading`: Model solution achieves full expected points.

Once verified, reopen public intake (`sudo systemctl start nginx`). For a drained shutdown, use `dc down` without `-v`. Prefer forward fixes; older retention guards or restoring student artifacts can re-expose expired data.

## Failure tolerance and disaster recovery runbook

The autograder operates on a single on-premise workstation (`10.115.20.200`, `CET-D24728`). Operators follow these recovery objectives and procedures to restore service after process, database, AI, or power interruptions while strictly preserving the FERPA zero-retention boundary ([Issue #27](https://github.com/UVU-Autograder/autograder_v1/issues/27)):

### Recovery Objectives (RTO / RPO)

| Failure Domain | Recovery Time Objective (RTO) | Recovery Point Objective (RPO) | FERPA & Operational Impact |
| --- | --- | --- | --- |
| **Worker / Broker Process Crash** | `<= 5 minutes` (automated via Docker `restart: unless-stopped`) | `0` (durable PostgreSQL `OfficialDispatch` + Redis AOF) | In-flight official batches resume from last committed student checkpoint; expired sandbox tickets return retry prompt |
| **Local AI Service (`vllm-cs1410.service`) Outage** | `0 minutes` (immediate graceful degradation) | `0` (stateless inference) | Deterministic pytest + AST grading and official exports continue normally; sandbox AI panel displays a temporary unavailable notice |
| **Host Reboot / Power Outage** | `<= 15 minutes` (automated systemd + Compose startup) | `0` for committed DB state | Systemd and Docker restart all services on boot; `cleanup-worker` purges any expired workspaces immediately on startup |
| **Database Corruption / Disk Failure** | `<= 2 hours` (schema migration + metadata restore) | `<= 24 hours` (daily `02:00` cron backup + pre-rollout snapshots) | Course, rubric, and instructor test artifacts restored; zero student PII stored in backups (interrupted official batches are re-uploaded from Canvas) |

### 1. Worker and Broker Crash Recovery
- **Automated Restart:** `redis`, `backend`, `celery-worker`, `dispatch-worker`, `cleanup-worker`, `judge0`, and `judge0-worker` run with `restart: unless-stopped` and bounded JSON logging (`50m` max, 5 files). Redis persists state with Append-Only File (`--appendonly yes`).
- **Ticket & Dispatch Reconciliation:**
  - If `celery-worker` or `redis` crashes mid-run, `ExecutionTicket` leases expire automatically (`expires_at`), preventing leaked capacity slots.
  - `dispatch-worker` reconciles durable `OfficialDispatch` rows in PostgreSQL and resumes any unfinished official batch from its committed workspace checkpoint without duplicating completed student submissions.
- **Manual Verification & Recovery:**
  ```bash
  dc ps
  dc restart redis celery-worker dispatch-worker
  dc exec -T backend celery -A app.integrations.celery.app inspect ping
  dc exec -T dispatch-worker python -m app.domains.runs.dispatch_worker --health
  ```

### 2. Database Failure and FERPA-Compliant Metadata Restore
[backup_metadata.sh](../../scripts/backup_metadata.sh) and [backup_metadata.ps1](../../scripts/backup_metadata.ps1) allowlist only persistent system and course metadata (`alembic_version`, `roles`, `users`, `courses`, `staff_access`, `sections`, `modules`, `assignments`, `assignment_configs`, `assignment_artifacts`, `audit_records`) and instructor-owned test fixtures (`/data/artifacts`), strictly excluding ephemeral runs, student submissions, execution logs, workspaces, and broker payloads.

- **Scheduled Backup Cadence:** Run daily at `02:00` local time via host cron and before every deployment rollout, retaining 30 days of snapshots in `/data/backups/metadata`:
  ```bash
  bash scripts/backup_metadata.sh --backup --output-dir /data/backups/metadata_$(date +%Y%m%d)
  ```
- **Isolated Schema Verification & Restore Procedure:**
  1. Verify backup manifest integrity (`manifest.json` must confirm `"ferpa_compliant": true` and `"backup_scope": "metadata_only"`).
  2. Recreate or migrate the target PostgreSQL database to the matching Alembic revision (`dc up -d postgres backend`).
  3. Restore persistent metadata and instructor artifacts:
     ```bash
     bash scripts/backup_metadata.sh --restore /data/backups/metadata_YYYYMMDD
     ```
  4. Verify schema parity and synthetic package grading before reopening intake:
     ```bash
     dc exec -T backend python scripts/validate_grading_package_host.py --course cs1410 --assignment lab1
     ```

### 3. Local AI Outage (`vllm-cs1410.service` / Ollama) Graceful Degradation
- **Decoupled Architecture:** Deterministic grading (`GradingEngine` via Judge0 + AST analysis) and official batch exports never depend on the local LLM service (`127.0.0.1:8001`).
- **Graceful Fallback Contract:** When `vllm-cs1410.service` is stopped, unreachable (`httpx.ConnectError`), or overloaded (`httpx.TimeoutException`), [`LocalLLMClient`](../../backend/app/integrations/llm/client.py) logs a warning and returns a safe, student-friendly unavailable notice while preserving full deterministic test results and scores.
- **Service Recovery:**
  ```bash
  sudo systemctl restart vllm-cs1410.service
  systemctl status vllm-cs1410.service --no-pager
  curl -fsS http://127.0.0.1:8001/v1/models
  ```

### 4. Power Outage and Host Reboot Recovery
- **Autostart Configuration:** Ensure host-level units are enabled across reboots:
  ```bash
  sudo systemctl enable docker.service nginx.service autograder-frontend.service vllm-cs1410.service
  ```
- **Post-Reboot Verification Checklist:** After an unexpected power loss or host reboot:
  1. Confirm KVM device and Kata runtime availability (`docker run --rm --runtime kata-runtime busybox uname -a`).
  2. Confirm all Compose containers recovered (`dc ps`) and language ID `711` is registered (`curl -fsS http://127.0.0.1:2358/languages`).
  3. Confirm `cleanup-worker` completed its initial sweep of any workspaces that expired during the power outage (`dc exec -T cleanup-worker python -m app.domains.runs.cleanup_worker --health`).
  4. Confirm API and frontend health (`curl -fsS http://127.0.0.1/api/health`).

## 50-active-user capacity benchmark and execution slot tuning

The platform's bounded execution concurrency and queue admission model ([Issue #26](https://github.com/UVU-Autograder/autograder_v1/issues/26)) was benchmarked on the Dell Precision 5860 Tower (`10.115.20.200`, `CET-D24728`, NVIDIA RTX PRO 4500 Blackwell 32GB VRAM, Intel Xeon W-series, 32GB RAM).

### 1. Benchmark Execution and Results

Two independent load scenarios were run against the live stack:

#### A. AI Feedback Concurrency (`scripts/mock_sandbox_load.py --stream --levels 1,4,8,16,32,50`)
- **Levels 1 to 32 Active Students:**
  - 100% successful feedback generation with **0 fallbacks, 0 timeouts, and 0 KV-cache preemptions**.
  - Latency p95 scaled gracefully: `3.13s` (1 student) → `4.65s` (16 students) → `7.15s` (32 students).
  - Model generation throughput reached `595 tokens/sec`.
  - KV-cache memory allocation peaked at `31.2%` with zero preemptions or cache thrashing.
- **Level 50 Active Students (Burst Threshold):**
  - Admitted the configured maximum of 40 simultaneous requests (16 active execution slots + 24 in-flight waiting slots) with `6.07s` p95 response latency.
  - Excess requests (110 attempts across retries) were rejected cleanly with HTTP 503 `ai_busy` (`retry_after_seconds: 10`), verifying graceful degradation without host OOM or GPU driver stalls.
  - GPU telemetry: Power capped safely at 203W (within the 200W/210W target), temperature remained between 46°C and 65°C, and core frequency remained stable (`2370–2587 MHz`).

#### B. Grading Submission Intake (`scripts/stress_suite.py grading --levels 1,4,8,16,32,50`)
- **Throughput & Queue Latencies (at `JUDGE0_MAX_CONCURRENT=2`):**
  - **1 student:** p95 queue wait `0.02s`, total p95 `1.36s` (44.1 runs/min).
  - **4 students:** p95 queue wait `4.72s`, total p95 `11.05s` (21.7 runs/min).
  - **8 students:** p95 queue wait `16.54s`, total p95 `22.17s` (21.6 runs/min).
  - **16 students:** p95 queue wait `35.84s`, total p95 `38.46s` (22.2 runs/min).
  - **32 students:** p95 queue wait `68.31s`, total p95 `77.33s` (24.5 runs/min).
  - **50 students:** Queue depth peaked at 46 (within the `FULL_QUEUE_THRESHOLD = 50` limit); all 50 submissions admitted and completed without dropped jobs or worker crashes; p95 queue wait `120.62s`, total p95 `130.79s` (21.9 runs/min).

### 2. Concurrency Cap Tuning Analysis (2 vs. 4 vs. 6+ Slots)

- **Bottleneck Identification:** At `JUDGE0_MAX_CONCURRENT=2`, grading throughput is capped at ~22 runs/min. Under a simultaneous 50-student lab burst, queue drain time reaches ~130 seconds.
- **Host Resource Profiling:**
  - Host CPU: Intel Core Ultra 7 265 with 20 hardware cores (8 Performance cores + 12 Efficient cores). During the 50-user peak load, CPU was **88.5% idle** with a load average of `1.06`.
  - Host RAM: 32 GB DDR5 total with **19.6 GB free/available**.
  - Each Kata microVM (`judge0-worker`) consumes ~500MB–1GB RAM and 1 vCPU during pytest execution.

#### Should Concurrency Be Higher Than 4?
- **4 Slots (Recommended Baseline):**
  - Uses 4 of the 8 physical Performance cores.
  - Doubles throughput to ~40–44 runs/min; cuts peak 50-student queue drain time from ~130s to ~65s.
  - Consumes ~3–4 GB RAM, safely within the 19.6 GB available headroom with zero CPU contention.
- **6 Slots (High-Throughput Sweet Spot):**
  - Allocates 6 of the 8 Performance cores to Kata execution VMs, leaving 2 P-cores + 12 E-cores dedicated to the host OS, Nginx, Celery, PostgreSQL, Redis, and vLLM token generation.
  - Scales throughput to ~55–60 runs/min, clearing a 50-student lab burst in ~45–50 seconds.
  - Consumes ~4.5–6 GB RAM, leaving >13 GB available.
- **8+ Slots (Diminishing Returns & Contention):**
  - Exceeds the 8 physical Performance cores, forcing Kata QEMU worker threads to context-switch across E-cores.
  - Single-threaded Python pytest suites and AST checkers suffer jitter and increased execution wall time when scheduled on E-cores.
  - Multiplies `virtiofsd` file descriptor and IPC overhead, alongside PostgreSQL/Redis polling contention. Concurrency should **not** exceed 6 slots on this host topology.

### 3. Pipeline Parameters for Faster, More Efficient Grading

Beyond execution slot count, four key parameters across the stack directly optimize end-to-end grading speed and queue efficiency:

1. **`JUDGE0_MAX_CONCURRENT` (Workstation Execution Slots):**
   - Configured in `.env.local` and `.env.example`: `JUDGE0_MAX_CONCURRENT=6`.
   - Automatically provisions 6 `judge0-worker` replicas via Docker Compose (`deploy: replicas: ${JUDGE0_MAX_CONCURRENT:-6}`), sets Celery worker pool size (`worker_concurrency`), and adjusts the active ticket ceiling in [`queue_admission.py`](../../backend/app/domains/runs/queue_admission.py).
2. **`FULL_QUEUE_THRESHOLD` & `HIGH_LOAD_THRESHOLD` ([`queue_admission.py`](../../backend/app/domains/runs/queue_admission.py)):**
   - Configured: `HIGH_LOAD_THRESHOLD = 50`, `FULL_QUEUE_THRESHOLD = 75`.
   - With 6 execution slots draining work at ~55–60 runs/min, `FULL_QUEUE_THRESHOLD = 75` accommodates full multi-section lab cohorts without turning away students with HTTP 503 `queue_full` retries.
3. **Interactive Sandbox Timeout Bounds ([`docker-compose.yml`](../../docker-compose.yml)):**
   - Configured: `CPU_TIME_LIMIT: "30"`, `WALL_TIME_LIMIT: "40"`, `MAX_WALL_TIME_LIMIT: "45"`.
   - Normal student pytest suites complete in 1.5s–4.0s; timeout bounds guarantee runaway student loops are terminated cleanly before blocking queue throughput.
4. **AI Feedback Concurrency Limits ([`ai_capacity.py`](../../backend/app/domains/sandbox/ai_capacity.py)):**
   - Configured in settings and Docker Compose: `ai_max_concurrent = 20`, `ai_max_waiting = 30` (50 total admitted).
   - The 50-user benchmark demonstrated that GPU KV-cache allocation peaked at only 31.2% with zero cache evictions or preemptions, accommodating an entire 50-student cohort requesting simultaneous AI hints without any 503 `ai_busy` backpressure.

[Dispatch](../../backend/scripts/validate_dispatch_host.py) and [retention](../../backend/scripts/validate_retention_host.py) validators own synthetic batch/failure/outage procedures. Review CLI/phase order, keep manifests and run permission checks as the application user. They are maintenance tests, not daily health checks.

## Host verification and fault recovery validation (Issue #25)

The production Dell Precision 5860 Tower (`CET-D24728`, Ubuntu 24.04 LTS, Intel Core Ultra 7 265, 32GB RAM, NVIDIA RTX PRO 4500 Blackwell 32GB) underwent dated, commit-specific verification across microVM isolation, batch throughput, interruption recovery, and zero-retention compliance ([Issue #25](https://github.com/UVU-Autograder/autograder_v1/issues/25)).

### 1. Kata microVM Isolation & Boundary Proofs
- **Kernel Separation:** Execution was confirmed running in an independent guest Linux kernel (`6.18.35-202` inside Kata vs. host `6.17.0-1032-oem`), isolated by hardware KVM acceleration (`accel=kvm`).
- **Resource Caps:** MicroVM hypervisor envelopes were verified in `/etc/kata-containers/runtime-rs/configuration.toml` (`default_vcpus = 2`, `default_memory = 2048` MB, `virtio-fs`), with Judge0 per-box `isolate` boundaries strictly capping memory to 256MB, CPU time to 30.0s, wall time to 20.0s, and thread count to 60.
- **MicroVM Process Boundaries:** All 6 `judge0-worker` containers operate under `runtime: kata-runtime`, with dedicated `containerd-shim-kata-v2`, `virtiofsd`, and `qemu-system-x86_64` process isolation per slot.

### 2. 200-Submission Batch Capacity & Concurrent Sandbox Execution
- **Batch Processing:** 200 synthetic submissions were processed through the official pipeline via [`validate_dispatch_host.py`](../../backend/scripts/validate_dispatch_host.py) against CS 1400 `m1-lab1` (`completed: 200`, total batch duration: `1454.13s`).
- **Concurrent Sandbox Throughput:** A concurrent sandbox submission was dispatched mid-batch; it completed cleanly in `20.03s` with score 10/10 while the official queue remained fully active.
- **Export Artifacts:** Official grades export (`grades.csv`, 200 rows) and student feedback bundles (`feedback.zip`, 200 items) were compiled in `0.0085s` packaging time and verified with zero dropped jobs.
- **Post-Run Teardown:** Cleaned up via `validate_dispatch_host.py cleanup`, confirming `physical_absence: true` with zero orphaned workspace directories or archive artifacts.

### 3. Fault & Interruption Recovery Mid-Batch
- **Celery Worker Crash Recovery:** Restarted `celery-worker` mid-batch; worker reconnected to Redis within 1s and resumed grading the active submission without ticket or slot leakage.
- **Dispatch Worker Restart:** Restarted `dispatch-worker` mid-batch; dispatcher cleanly re-evaluated in-flight tickets, published next tasks, and maintained 5s health sweeps (`healthy: true, publish_failures: 0`).
- **Judge0 Execution Worker Crash Recovery:** Restarted `judge0-worker` during active test execution; the interrupted job was safely trapped, reported as `cleanup_failure`, checkpointed, and the remaining batch proceeded without deadlocks or stalled queues.
- **Slot & Ticket Audit:** Audited `ExecutionTicket` table in PostgreSQL; confirmed zero orphaned tickets or deadlocks across all runs.

### 4. Zero-Retention Compliance
- **Submission Deletion:** Verified through [`validate_grading_package_host.py`](../../backend/scripts/validate_grading_package_host.py) and live Celery traces that every completed submission payload is immediately deleted via `DELETE /submissions/[TOKEN]` (subsequent queries return HTTP 404).
- **Cleanup Worker Reconciliation:** Executed [`validate_retention_host.py`](../../backend/scripts/validate_retention_host.py) across simulated 23h review expiry, 24h hard deletion, permission failure quarantine, and recovery. All 14 retention and cleanup assertions passed, leaving zero dangling files or orphaned workspaces.

## Operational support roles and responsibilities

Formal operational support roles ensure clear accountability across workstation infrastructure, curriculum configuration, and instructional workflows:

### 1. Host & Infrastructure Administrator
- **Primary Contact:** Host Administrator (`dev@10.115.20.200`, host user `dev`).
- **Core Responsibilities:**
  - **Workstation & Hardware Telemetry:** Physical hardware oversight for Dell Precision 5860 Tower (`CET-D24728`, IP `10.115.20.200`). Continuous monitoring of thermal metrics, cooling fans, and GPU power consumption (`nvidia-smi`) on the NVIDIA RTX PRO 4500 Blackwell (32GB VRAM), ensuring sustained power ceilings (≤210W) and stable operating temperatures (<65°C).
  - **Kata Containers & Kernel Lifecycle:** Maintenance and tuning of Kata Containers runtime-rs (`/etc/kata-containers/runtime-rs/configuration.toml`), `/dev/kvm` hardware virtualization permissions, and QEMU isolation parameters. Evaluation and testing of host OS kernel updates against guest microVM compatibility.
  - **Local AI Service Maintenance:** Administration of `vllm-cs1410.service` on internal loopback `127.0.0.1:8001`. Manages storage and versioning for Gemma 4 12B QAT base model weights (`/data/models/gemma4-12b-qat-w4a16`) and reviewed LoRA adapter weights (`/data/models/adapters/`).
  - **Data Persistence & Disaster Backups:** Oversight of daily `02:00` cron snapshot execution ([`backup_metadata.sh`](../../scripts/backup_metadata.sh)), validating metadata archive integrity in `/data/backups/metadata` and strictly maintaining FERPA zero-retention boundaries.
  - **Network & Ingress Security:** Management of Nginx reverse proxy routing, TLS termination, Microsoft Entra ID OAuth integrations, and strict loopback listener enforcement (`127.0.0.1` for backend, frontend, vLLM, Judge0, PostgreSQL, and Redis).

### 2. Course Coordinators (CS 1400 & CS 1410)
- **Primary Contacts:** Lead Course Coordinators for CS 1400 (Intro to Programming) and CS 1410 (Object-Oriented Programming).
- **Core Responsibilities:**
  - **Assignment & Test Configuration:** Authoring and maintaining assignment grading packages, pytest test harnesses, AST syntactic inspection constraints, and rubric point allocations.
  - **Reference Inventory Validation:** Execution of model reference solution validation ([`revalidate_references.py`](../../backend/scripts/revalidate_references.py)) before publishing assignments, ensuring all reference implementations score 100% under Kata microVM execution.
  - **Scoring & Rubric Calibration:** Calibrating automated scoring tiers, AST rules, manual rubric point bounds, and reusable 1-click comment snippets for course grading staff.
  - **Rollout Coordination:** Scheduling grading package deployment windows ([`rollout_grading_package.sh`](../../scripts/rollout_grading_package.sh)) and coordinating major assignment updates with the Host Administrator.

### 3. Teaching Assistants (TAs) and Instructional Assistants (IAs)
- **Primary Contacts:** Course Teaching Assistants and Lab Instructional Assistants.
- **Core Responsibilities:**
  - **First-Line Student Guidance:** Assisting students with sandbox test results, troubleshooting preflight file naming errors (e.g., missing mandatory submission files), and clarifying Socratic AI feedback without leaking reference solutions.
  - **Live Queue Monitoring:** Observing sandbox admission rates, queue wait times, and system notices during scheduled lab sessions and peak submission windows.
  - **Manual Rubric Adjudication:** Reviewing student test breakdowns, applying 1-click comment snippets, and entering manual rubric adjustments via the instructor interface ([`update_student_manual_grades`](../../backend/app/domains/runs/router.py#L541-L550)).
  - **FERPA Zero-Retention Awareness:** Upholding student data privacy guidelines: never downloading student source code to personal machines, never saving student artifacts outside approved Canvas gradebook exports, and respecting the ephemeral 24-hour workspace retention window.
  - **Anomaly Escalation:** Immediate reporting of unexpected sandbox grading errors, timeout loops, or test harness defects to the appropriate Course Coordinator and Host Administrator.

## Emergency incident response playbooks

The following runbooks provide immediate remediation procedures for common operational interruptions:

### Playbook 1: Immediate Ingestion Halt & Queue Drainage
Use this playbook when a critical issue (e.g., malformed assignment suite, grading bug, or security risk) requires stopping incoming traffic without aborting in-flight submissions.

1. **Halt External Ingestion at Nginx:**
   ```bash
   sudo systemctl stop nginx
   ```
2. **Verify In-Flight Workload Drainage:**
   Ensure background workers complete pending queue items without terminating mid-execution:
   ```bash
   bash scripts/rollout_grading_package.sh --dry-run
   ```
   Or inspect Celery worker queues directly:
   ```bash
   dc exec -T backend celery -A app.integrations.celery.app inspect active
   ```
3. **Keep Supporting Daemons Active:**
   Maintain `postgres`, `redis`, `judge0`, `celery-worker`, `dispatch-worker`, and `cleanup-worker` until active tickets reach zero.
4. **Resume Ingestion After Resolution:**
   ```bash
   sudo systemctl start nginx
   curl -fsS http://127.0.0.1/api/health
   ```

### Playbook 2: Service Restart & Worker Recovery
Use this playbook when background worker processes (Celery, dispatch, or cleanup) stall, disconnect from Redis, or fail health sweeps.

1. **Inspect Service State:**
   ```bash
   dc ps
   ```
2. **Restart Worker Daemons:**
   ```bash
   dc restart celery-worker dispatch-worker cleanup-worker
   ```
3. **Verify Health Probes & Ping Heartbeats:**
   ```bash
   dc exec -T backend celery -A app.integrations.celery.app inspect ping
   dc exec -T dispatch-worker python -m app.domains.runs.dispatch_worker --health
   dc exec -T cleanup-worker python -m app.domains.runs.cleanup_worker --health
   curl -fsS http://127.0.0.1:8000/api/health
   ```

### Playbook 3: Local AI Service (`vllm-cs1410.service`) Outage & Graceful Degradation
Use this playbook when AI feedback generates 503 `ai_busy` backpressure errors, fails to generate tokens, or the Socratic AI panel displays an unavailable notice.

1. **Verify Deterministic Grading Continuity:**
   Deterministic grading (pytest test suite + AST analysis via Judge0) is architecturally decoupled from the LLM service and continues operating without interruption.
2. **Inspect Host GPU & Daemon Telemetry:**
   ```bash
   nvidia-smi
   systemctl status vllm-cs1410.service --no-pager
   journalctl -u vllm-cs1410.service -n 50 --no-pager
   ```
3. **Restart the Local AI Daemon:**
   ```bash
   sudo systemctl restart vllm-cs1410.service
   ```
4. **Verify Model Inference Endpoint:**
   ```bash
   curl -fsS http://127.0.0.1:8001/v1/models
   ```
   Confirm that the active base model and LoRA adapter respond with HTTP 200.

### Playbook 4: MicroVM Hypervisor / Sandbox Lockup Escalation
Use this playbook if executions hang beyond configured timeout bounds (30s CPU / 40s wall time) or if Kata microVMs fail to launch.

1. **Verify KVM Device & Kata Isolation Health:**
   ```bash
   docker run --rm --runtime kata-runtime busybox uname -a
   ls -la /dev/kvm
   ```
2. **Inspect Active QEMU Hypervisor Processes:**
   ```bash
   ps aux | grep -E "qemu-system-x86_64|virtiofsd"
   ```
3. **Restart Judge0 Execution Pool:**
   ```bash
   dc restart judge0-worker judge0
   ```
4. **Re-Verify Judge0 Language Registration:**
   ```bash
   curl -fsS http://127.0.0.1:2358/languages
   ```
   If language ID 711 (`Python (3.11.9)`) is missing, re-seed:
   ```bash
   docker exec -i uvu-autograder-postgres-1 psql -U autograder -d judge0 < scripts/seed_judge0_language_311.sql
   ```

### Playbook 5: Database Disaster Recovery & Metadata Restoration
Use this playbook to recover from database corruption, container volume failure, or accidental administrative deletion.

1. **Inspect and Verify Available Snapshots:**
   ```bash
   ls -la /data/backups/metadata
   ```
   Verify that `manifest.json` confirms `"ferpa_compliant": true` and `"backup_scope": "metadata_only"`.
2. **Initialize Fresh Database Volume & Bring Up Infrastructure:**
   ```bash
   dc up -d postgres backend
   ```
3. **Execute Metadata Restore Script:**
   ```bash
   bash scripts/backup_metadata.sh --restore /data/backups/metadata_YYYYMMDD
   ```
4. **Re-Validate Assignment Reference Inventory:**
   ```bash
   docker exec -i uvu-autograder-backend-1 python - --wait < backend/scripts/revalidate_references.py
   dc exec -T backend python scripts/validate_grading_package_host.py --course cs1410 --assignment lab1
   ```

### Incident Escalation & Response Matrix

| Severity Level | Definition / Criteria | Response SLA | Primary Responder | Escalation Contacts |
| --- | --- | --- | --- | --- |
| **Severity 1 (Critical)** | Entire platform unavailable; network isolation compromised; potential FERPA exposure risk. | `< 15 minutes` | Host & Infrastructure Administrator | Course Coordinators, Department Chair |
| **Severity 2 (High / Degraded)** | Sandboxes queuing above high-load threshold; AI service degraded; single worker failure. | `< 1 hour` | Host & Infrastructure Administrator | Course Coordinators, TAs / IAs |
| **Severity 3 (Standard / Minor)** | Non-blocking UI defect; single student syntax anomaly; non-critical test harness inquiry. | Next business day | Course Coordinators / TAs | Host & Infrastructure Administrator |
