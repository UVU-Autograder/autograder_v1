# Ubuntu 24.x Local POC Deployment

This document wires the current repository into a fully functional local proof-of-concept stack for the Ubuntu 24.x machine. This is not a live-student production approval document. It is intended for synthetic, fake, or approved anonymized test code while the team validates the end-to-end autograder path.

## Stack

- Frontend: run separately with the existing frontend workflow; this backend POC compose file does not build or modify frontend assets.
- Backend: FastAPI on `http://localhost:8000`
- App database: PostgreSQL, migrated by Alembic at backend startup
- Queue/state: Redis
- Worker: Celery using the `sandbox`, `official`, and `default` queues
- Execution API: local Judge0 CE on `http://localhost:2358`
- Isolation: Kata Containers is expected to be configured on the Ubuntu host and validated operationally outside the app container

## Files

- `docker-compose.poc.yml`: local POC stack for app Postgres, Judge0 Postgres, Redis, Judge0, backend, and Celery worker.
- `backend/Dockerfile`: backend runtime image that installs Python dependencies, waits for Postgres, runs Alembic, and optionally seeds development data.
- `.env.example`: local POC environment template.
- `backend/scripts/docker-entrypoint.sh`: backend container startup script.

## First Run

From the repository root:

```bash
cp .env.example .env.local
# Edit .env.local secrets if needed.
docker compose --env-file .env.local -f docker-compose.poc.yml up --build
```

Then open:

- UI: run the existing frontend separately when needed.
- API health: `http://localhost:8000/health`
- Judge0 languages: `http://localhost:2358/languages`

The seeded staff account is `dev.staff@uvu.edu`. The POC compose file enables mock login with `ENABLE_MOCK_LOGIN=true`; turn this off for any non-local deployment.

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

The seeded data uses `docs/backend_implementation/examples` through `seed://...` artifact references. Those example artifacts are copied into the backend image and resolved with `REPO_ROOT=/app`.

## Judge0 And Kata

The compose file starts Judge0 CE and its worker locally. The app sends zipped student work to Judge0 through the existing backend grading pipeline and deletes Judge0 submissions after result retrieval.

Kata Containers is host-level execution isolation. The repository cannot configure GRUB or prove Kata isolation from inside the FastAPI image. The optional `docker-compose.kata.yml` override requires a host Docker runtime named `kata-runtime`. Before treating the Ubuntu machine as the intended execution target, collect operational evidence on the host that:

- Docker/containerd uses the Kata-capable runtime expected by the Judge0 execution path.
- Judge0 submissions execute under the expected isolated runtime.
- `DELETE /submissions/{token}` works and deleted submissions are no longer retrievable.
- Temporary app workspaces are removed after success, failure, timeout, and cancellation.

## Environment Notes

Local POC defaults intentionally keep CORS and frontend API access on localhost. Tailscale/SSH access should be handled at the host/network layer until UVU assigns a hosted environment.

Use plain environment files for now, but do not commit real secrets. The existing tracked `backend/.env` is left unchanged for compatibility with the current development workflow.

## FERPA/Local LLM Scope

The current documentation says the technical design reduces FERPA risk, but live official grading still depends on institutional approval and direct-control requirements. Use this POC with synthetic, fake, or approved anonymized data unless UVU approval has been explicitly documented for live student data.

Local LLM credentials can be supplied through environment variables, but AI feedback for live, pseudonymous, or real student-derived code should remain disabled unless the UVU approval checklist is complete.

## Celery Beat Scheduler (Periodic Tasks)

The autograder stack utilizes **Celery Beat** to schedule periodic background tasks such as the hourly workspace cleanup (`cleanup_expired_workspaces`).

### Running Celery Beat in Development
In the development environment, you can run the Celery Beat scheduler in a separate terminal process:

```bash
celery -A app.integrations.celery.app beat --loglevel=info
```

### Running in Docker Compose
In production/POC compose deployments, the Celery Beat scheduler is included as a service in the docker compose configurations, using the same backend container image:

```yaml
  celery-beat:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: celery -A app.integrations.celery.app beat --loglevel=info
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - CELERY_BROKER_URL=${CELERY_BROKER_URL}
    depends_on:
      - redis
      - app-postgres
```

Make sure the Celery Beat scheduler process is running to guarantee that temporary student workspaces and grade review exports are cleaned up after their 24-hour expiration window.

