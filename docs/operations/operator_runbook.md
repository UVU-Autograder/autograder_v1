# UVU Autograder — Production Operator Runbook

This runbook defines operational procedures, service lifecycle controls, health verification, incident response, and troubleshooting for systems operators maintaining the **UVU Autograder** on the dedicated Dell workstation host.

---

## 1. Host Architecture & Network Boundaries

### Host Environment
- **Hardware**: Dell Pro Max Tower T2 (Intel Core Ultra 7 265, 20 physical cores, 32GB RAM, NVIDIA RTX PRO 4500 Blackwell 24GB VRAM)
- **Operating System**: Ubuntu 24.04.5 LTS
- **Deployment IP**: `10.115.20.200` (campus LAN / VPN accessible via `campusvpn.uvu.edu`)
- **Service User**: `dev` (`/home/dev/autograder_v1`)

### Port & Ingress Layout
| Port | Protocol | Binding | Service / Role |
| :--- | :--- | :--- | :--- |
| `80` | HTTP | `0.0.0.0:80` | Nginx reverse proxy (public campus access; redirects to 443 once cert installed) |
| `443` | HTTPS | `0.0.0.0:443` | Nginx TLS termination (institutional certificates) |
| `3000` | HTTP | `127.0.0.1:3000` | Next.js frontend production server (`autograder-frontend.service`) |
| `8000` | HTTP | `127.0.0.1:8000` | FastAPI backend container (host network mode) |
| `5432` | TCP | `127.0.0.1:5432` | PostgreSQL 16 (bound to localhost; no public exposure) |
| `6379` | TCP | `127.0.0.1:6379` | Redis 7 broker & queue (bound to localhost; no public exposure) |
| `2358` | HTTP | `127.0.0.1:2358` | Judge0 CE code execution sandbox (bound to localhost) |

---

## 2. Daily Health Checks & Monitoring

Execute these commands to verify operational status:

```bash
# 1. Reverse proxy & API status
curl -fsS http://127.0.0.1/health
curl -fsS http://127.0.0.1/api/health

# 2. Inspect active queue lengths and Celery worker health
docker compose exec -T backend celery -A app.core.celery inspect ping
docker compose exec -T redis redis-cli llen official
docker compose exec -T redis redis-cli llen sandbox

# 3. Judge0 CE execution service
curl -fsS http://127.0.0.1:2358/about

# 4. Check systemd frontend status
systemctl status autograder-frontend.service --no-pager
```

### In-App Monitoring Dashboard
Authenticated administrators can query real-time system metrics via the web UI at `/staff/admin/monitoring` or REST API `GET /api/staff/admin/monitoring`:
- `active_runs_count`: Ongoing test executions.
- `queued_runs_count`: Tasks waiting in Celery/Redis queues.
- `cleanup_service_healthy`: Retention worker heartbeat (true if checked in within 120s).
- `cleanup_failed_runs`: Count of runs whose cleanup encountered filesystem or database errors.
- `cleanup_overdue_runs`: Runs older than 24 hours whose workspaces still exist (SLA breach).

---

## 3. Service Lifecycle Management

### Starting Services
Start services in the following order:
```bash
# Step 1: Start Docker Compose infrastructure (Postgres, Redis, Judge0, Backend, Celery, Cleanup)
cd /home/dev/autograder_v1
docker compose --env-file .env.local -f docker-compose.yml -f docker-compose.kata.yml up -d

# Step 2: Ensure Next.js frontend systemd service is active
sudo systemctl start autograder-frontend.service

# Step 3: Ensure Nginx is running
sudo systemctl start nginx
```

### Graceful Shutdown (Maintenance Window)
To avoid interrupting student runs or official batch grading:
1. **Close Ingestion**: Stop the frontend to prevent new submissions:
   ```bash
   sudo systemctl stop autograder-frontend.service
   ```
2. **Drain Queues**: Wait until Celery finishes in-flight grading:
   ```bash
   docker compose exec -T backend celery -A app.core.celery inspect active
   ```
3. **Stop Docker Stack**:
   ```bash
   docker compose down
   ```

---

## 4. Incident Response & Troubleshooting

### Scenario A: Queue Stalls / Grading Worker Freezes
**Symptoms**: Submissions remain in `queued` or `running` state; `llen official` does not decrement.
1. Check Judge0 worker logs:
   ```bash
   docker compose logs --tail=100 judge0-workers
   ```
2. Verify Kata container runtime shims:
   ```bash
   ps aux | grep containerd-shim-kata-v2 | wc -l
   ```
3. If tasks are deadlocked due to host resource limits, restart the worker container gracefully:
   ```bash
   docker compose restart celery-worker
   ```

### Scenario B: 24-Hour Retention Alert (`cleanup_overdue_runs > 0`)
**Symptoms**: The retention worker reports runs exceeding the 24-hour physical deletion deadline.
1. Inspect the cleanup worker logs:
   ```bash
   docker compose logs --tail=100 cleanup-worker
   ```
2. Check for filesystem permission errors on the host artifact volume:
   ```bash
   ls -ld /data/workspaces /data/artifacts
   ```
3. Trigger a manual retention reconciliation sweep:
   ```bash
   docker compose exec -T cleanup-worker python -m app.domains.runs.cleanup_worker --once
   ```

### Scenario C: Microsoft Authentication Errors
**Symptoms**: Staff cannot log in via Microsoft Entra ID; returns 403 or redirect errors.
1. **"Account pending staff authorization"**:
   - The user's `@uvu.edu` email has not been provisioned by an administrator.
   - Provision them via `/staff/admin/access` or the CLI:
     ```bash
     docker compose exec -T backend python -c "from app.db.session import SessionLocal; from app.domains.auth.service import grant_staff_access; grant_staff_access(SessionLocal(), email='user@uvu.edu', role_name='instructor', course_id=1)"
     ```
2. **"Institutional Microsoft authentication is not configured"**:
   - Verify `AZURE_AD_CLIENT_ID` and `AZURE_AD_CLIENT_SECRET` are set in `/home/dev/autograder_v1/.env.local`.

---

## 5. Security & Secret Rotation

When rotating secrets:
1. **JWT Secret (`JWT_SECRET`)**:
   - Generate a minimum 32-character high-entropy secret.
   - Update `JWT_SECRET` in `.env.local`.
   - Restart backend: `docker compose restart backend`.
   - *Impact*: Invalidates existing 60-minute staff sessions; requires re-login.
2. **Database Password**:
   - Update in `.env.local` (`POSTGRES_PASSWORD` and `DATABASE_URL`).
   - Run `ALTER USER autograder WITH PASSWORD 'new-secret';` in PostgreSQL.
   - Restart the stack: `docker compose restart backend celery-worker cleanup-worker`.
3. **Azure AD Client Secret**:
   - Generate a new client secret in the Azure Portal before expiring the old one.
   - Update `AZURE_AD_CLIENT_SECRET` in `.env.local`.
   - Restart frontend service: `sudo systemctl restart autograder-frontend.service`.

---

## 6. Escalation Matrix

| Role | Contact | Responsibility |
| :--- | :--- | :--- |
| **Primary System Operator** | `dev@10.115.20.200` | Host hardware, Docker, Nginx, and systemd units |
| **Course Administrator** | `admin@uvu.edu` | Staff access grants, course configurations, manual grading |
| **Identity Services (UVU IT)** | IT Service Desk | Azure AD App Registration, client secret renewals, tenant routing |
