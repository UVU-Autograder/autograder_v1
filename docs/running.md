# Access and test the system

Choose one of these three workflows. New clones need Git, npm and Node 22.12+ within 22.x (or Node 24+). The [frontend manifest](../frontend/package.json) owns dependencies.

## Access the full on-prem stack

The reported workstation is `10.115.20.200`. DNS/TLS and institutional SSO remain [open deployment work](planning/backlog.md).

For the reported LAN HTTP configuration, open `http://10.115.20.200/sandbox` or `/staff/login`; API health is `http://10.115.20.200/api/health` and the API explorer is `/api/docs`. The host runs the UI, API, database, workers, Judge0/Kata and local AI; browser access needs no local services.

Use synthetic test assignments/sections for testing. [Workstation](guides/workstation.md) covers SSH/service access and recovery.

## Run frontend checks locally

From the cloned repository root:

```bash
npm --prefix frontend install
npm --prefix frontend run type-check
npm --prefix frontend run lint
npm --prefix frontend test
npm --prefix frontend run dev
```

Open `http://localhost:3000`; stop with Ctrl+C. Types, lint and Vitest component/unit tests need no backend, Python, Docker or GPU. In development mode, the frontend automatically serves offline synthetic fixtures (`npm --prefix frontend run dev`), showing a `Mock API` badge in the navbar and populating representative courses, assignments, instant sandbox executions, AI coaching, and staff review screens. To connect to a live backend instead, run `npm --prefix frontend run dev:live` (`NEXT_PUBLIC_MOCK_API=false`). Mock mode is strictly locked off in production builds.

Use the frontend command above: root `npm run dev` starts a local backend as well.

## Use a local frontend with the on-prem backend

Install frontend dependencies as above. Create `frontend/.env.local` with the on-prem API URL and active auth mode. For the reported LAN HTTP proxy:

```dotenv
NEXT_PUBLIC_API_BASE_URL=http://10.115.20.200/api
INTERNAL_BACKEND_URL=http://10.115.20.200/api
NEXT_PUBLIC_AUTH_PROVIDER=microsoft
```

Then run `npm --prefix frontend run dev` and open `http://localhost:3000`. Restart after env edits; rebuild when using a production build.

Both your browser and Next.js server must reach the backend. Confirm CORS allows your exact local origin.

Staff SSO needs approved frontend `AZURE_AD_CLIENT_ID`, `AZURE_AD_TENANT_ID` and applicable `AZURE_AD_CLIENT_SECRET` settings, plus a registered `http://localhost:3000/api/auth/microsoft/callback` matching [Entra's redirect rules](https://learn.microsoft.com/en-us/entra/identity-platform/reply-url). Match the backend's approved auth mode; keep secrets out of `NEXT_PUBLIC_*` and Git. Public sandbox access does not need staff SSO.

These are real shared-host requests: uploads consume quotas and staff edits change shared setup. Use a designated synthetic test course/section.

## Additional checks

| Check | Command from repository root |
| --- | --- |
| Frontend production build | `npm --prefix frontend run build` |
| Backend test suite | `pytest backend/tests -q` (with `backend/venv` active) |
| Browser regression suite | `npm run test:e2e`; first install Chromium with `npx playwright install chromium` from `frontend/` |
| Full repository gate | `npm install`, `npm run setup:backend`, then `npm run check` |
| Static deployment audit | `npm run check:deployment` with backend Python environment active |
| Synthetic sandbox run | `python scripts/mock_sandbox_run.py CASE_ID --api http://10.115.20.200/api` |
| AI feedback load test | `python scripts/mock_sandbox_load.py` on host with vLLM active |


The existing [Playwright configuration](../frontend/playwright.config.ts) starts/reuses a local Python API; it is not a frontend-only or shared-host test runner. Full checks need Python 3.11+ and isolated test configuration. Backend fixtures reset tables: never point pytest at the on-prem database.

Activate `backend/venv` before direct Python commands: `backend\venv\Scripts\Activate.ps1` in PowerShell or `source backend/venv/bin/activate` in Bash. Regenerate changed contracts with `python backend/scripts/generate_schema.py` and `python backend/scripts/generate_openapi.py` (or `npm run openapi:generate`); use Alembic migrations for database changes.

## Verify a release

Record commit/configuration, commands, results and limitations using synthetic data. Exercise permissions/SSO, archive rejection, model/scoring failures/timeouts, AI fallback, manual/export gating, immediate Judge0 deletion and 23h/24h cleanup/recovery. Validate 200 submissions plus sandbox work within 40 minutes, exports within two minutes, Kata isolation and persistent-only restore. Detailed launch actions remain in the backlog.
