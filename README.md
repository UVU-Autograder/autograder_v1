# UVU Autograder

Utah Valley University's Autograder software. Currently preparing to serve CS 1400 and 1410 classes.

## Documentation

- [Documentation Index](docs/index.md) — central index for all architecture, specs, schemas, and modeling docs
- [Technical Specs](docs/core/technical_specs.md) — system contracts, data model, and runtime limits
- [Active Backlog](docs/planning/backlog.md) — living implementation roadmap
- [Frontend Routes](docs/implementation/frontend_implementation.md) — route contracts and UI responsibilities
- [Workstation Deployment](docs/deployment/workstation_deployment.md) — Dell workstation / Docker Compose deployment guide

Frontend mockup: https://autograder-frontend-mockup.vercel.app/

## Quick start

```bash
# Backend (from repo root)
npm run setup:backend

# Frontend dependencies
npm run install:frontend

# Run API + UI together
npm run dev
```

- API: http://127.0.0.1:8000
- UI: http://localhost:3000
- Health: http://127.0.0.1:8000/health

### Staff dev login

Use **Staff Portal Sign In** at `/staff/login` with a `@uvu.edu` address. Local/dev uses mock JWT login (`POST /auth/mock-login`), which does not verify email ownership. Institutional Microsoft authentication and explicit staff authorization are required before live deployment and are active pilot-readiness work.

## npm layout

| Path                    | Purpose                                               |
| ----------------------- | ----------------------------------------------------- |
| Root `package.json`     | Orchestration only (`concurrently` for `npm run dev`) |
| `frontend/package.json` | Next.js app — run `npm install` here for app deps     |

Do not install `next`/`react` at the repo root.

## Backend

```bash
# From repo root:
npm run openapi:generate

# Or inside backend directory:
cd backend
python -m pytest
python scripts/generate_openapi.py   # refresh docs/schemas/openapi.json
```

Set `SANDBOX_USE_CELERY=true` to dispatch real sandbox grading tasks (requires Redis/Celery/Judge0).
 
## Docker Production Stack

```bash
# Build Judge0 custom runtime image
npm run docker:build

# Launch on-prem stack (Postgres, Redis, Judge0, Celery, Backend, Cleanup)
npm run docker:up

# Launch on-prem stack with Kata microVM isolation (Linux hosts with /dev/kvm)
npm run docker:up:kata

# Stream logs or stop stack
npm run docker:logs
npm run docker:down
```

## Workstation Operating Notes

- **Workstation IP / Endpoints (`10.115.20.200`):**
  - Web UI & API (Reverse Proxy): `http://10.115.20.200` (port 80)
  - Next.js Direct: `http://10.115.20.200:3000` (managed via `autograder-frontend.service`)
  - Backend API Direct: `http://10.115.20.200:8000`
  - Health check: `http://10.115.20.200/health` or `http://10.115.20.200/api/health`
- **Default Seeded Staff User:** `dev.staff@uvu.edu` (admin role)
- **Frontend Systemd Service:**
  ```bash
  sudo systemctl status autograder-frontend
  sudo systemctl restart autograder-frontend
  ```
- **Local LLM (Ollama):** Managed via `ollama` systemd service running `qwen2.5-coder:7b` on NVIDIA GPU (port 11434).

## Frontend

```bash
cd frontend
npm run dev
npm run build
```
