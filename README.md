# UVU Autograder

On-prem autograder for retention-aware Python grading with a public student sandbox and staff setup/official-run workflows.

## Documentation

- [Documentation Index](docs/index.md) — central index for all architecture, specs, schemas, and modeling docs
- [Technical Specs](docs/core/technical_specs.md) — system contracts, data model, and runtime limits
- [Active Backlog](docs/planning/backlog.md) — living implementation roadmap
- [Frontend Routes](docs/implementation/frontend_implementation.md) — route contracts and UI responsibilities
- [Local POC Deployment](docs/deployment/ubuntu_poc_deployment.md) — on-prem workstation / Docker Compose setup

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

Use **Staff Portal Sign In** at `/staff/login` with a `@uvu.edu` address. Local/dev uses mock JWT login (`POST /auth/mock-login`). NextAuth + Microsoft OAuth is planned but deferred.

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
 
## Docker POC Stack

```bash
# Build Judge0 custom runtime image
npm run docker:build

# Launch on-prem stack (Postgres, Redis, Judge0, Celery, Backend)
npm run docker:up

# Stream logs or stop stack
npm run docker:logs
npm run docker:down
```

## Frontend

```bash
cd frontend
npm run dev
npm run build
```
