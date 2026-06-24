# UVU Autograder v1

On-prem autograder for zero-retention Python grading with a public student sandbox and staff setup/official-run workflows.

## Documentation

- [Technical specs](docs/technical_specs.md) — system contracts, data model, runtime limits
- [M1 backlog](docs/planning/backlog.md) — delivery checklist
- [Frontend routes](docs/frontend_implementation/frontend_implementation.md)
- [OpenAPI schema](docs/schemas/openapi.json)
- [Ubuntu 24.x local POC deployment](docs/ubuntu_poc_deployment.md)

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

Use **Staff Portal Sign In** at `/staff/login` with a `@uvu.edu` address. Local dev uses mock JWT login (`POST /auth/mock-login`). Microsoft OAuth is planned post-M1.

## npm layout

| Path | Purpose |
|------|---------|
| Root `package.json` | Orchestration only (`concurrently` for `npm run dev`) |
| `frontend/package.json` | Next.js app — run `npm install` here for app deps |

Do not install `next`/`react` at the repo root.

## Backend

```bash
cd backend
python -m pytest
python scripts/generate_openapi.py   # refresh docs/schemas/openapi.json
```

Set `SANDBOX_USE_CELERY=true` to dispatch real sandbox grading tasks (requires Redis/Celery/Judge0).

## Frontend

```bash
cd frontend
npm run dev
npm run build
```
