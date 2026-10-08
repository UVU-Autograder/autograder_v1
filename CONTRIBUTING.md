# Contributing to the UVU Autograder

Thank you for your interest in contributing to the UVU Autograder! This project provides isolated execution, AST inspection, local AI-assisted code feedback, and grading for introductory computer science coursework.

---

## 🏛️ Guiding Principles

1. **Student Privacy & FERPA:** Real student submissions, Canvas archives, student IDs, and personal identifiable information (PII) must **never** be committed to Git or stored in persistent test fixtures. All test fixtures and calibration manifests use synthetic or fully anonymized data.
2. **Execution Isolation:** All untrusted user code execution must remain isolated within Judge0 sandbox microVMs or containers with memory, CPU, process, and network limits.
3. **Reproducibility:** The grading engine runs against a pinned custom Python runtime (`judge0.Dockerfile`). Tooling and dependency changes must be validated against pilot regression manifests.

---

## 🛠️ Prerequisites

- **Docker & Docker Compose** (v2.20+)
- **Python** 3.11+ (Python 3.11.9 recommended for runtime parity)
- **Node.js** 20+ and **npm** 10+
- **Git**

---

## 🚀 Quickstart: Local Development

### 1. Clone & Configure Environment

```bash
git clone https://github.com/UVU-Autograder/autograder_v1.git
cd autograder_v1

# Copy template environment file
cp .env.example .env
```

The default `.env.example` comes pre-configured for local development with:
- `AUTH_PROVIDER=mock` (bypasses Microsoft Entra SSO for local development)
- `ENVIRONMENT=development`
- `ENABLE_MOCK_LOGIN=true`
- Internal service ports bound safely to `127.0.0.1`

### 2. Run with Docker Compose

To start the full stack (PostgreSQL, Redis, Judge0, Celery worker, Backend API):

```bash
docker compose up --build
```

Access the services:
- **Frontend App:** http://localhost:3000
- **Backend API Docs:** http://localhost:8000/docs
- **API Health Check:** http://localhost:8000/api/health
- **Judge0 Sandbox:** http://localhost:2358/about

### 3. Running Standalone Services (Optional)

#### Backend:
```bash
cd backend
python -m venv venv

# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

#### Frontend:
```bash
cd frontend
npm install
npm run dev
```

---

## 🧪 Testing & Verification

Always run test suites before submitting a pull request:

### Backend Tests
```bash
cd backend
python -m pytest tests/
```

### Frontend Tests & Type Checking
```bash
cd frontend
npm test
npm run build
```

### Automated Preflight Checks
Run the unified repository check script:

- **Linux / macOS:**
  ```bash
  ./scripts/run_checks.sh
  ```
- **Windows (PowerShell):**
  ```powershell
  .\scripts\run_checks.ps1
  ```

### Deployment & Release Readiness Audits
```bash
python scripts/audit_deployment_readiness.py
python scripts/audit_release_readiness.py
```

---

## 📐 Code Style & Formatting

### Python
- **Linter & Formatter:** [Ruff](https://github.com/astral-sh/ruff)
  ```bash
  cd backend
  ruff check .
  ruff format --check .
  ```
- **Type Checking:** Strict type hints across all domain logic.

### Frontend
- **Framework:** Next.js (App Router), Tailwind CSS, TypeScript.
- **Linter:** ESLint
  ```bash
  cd frontend
  npm run lint
  ```

### API Schema Parity
If you add or modify FastAPI router endpoints, regenerate the OpenAPI schema to maintain frontend client parity:
```bash
python backend/scripts/generate_openapi.py
```

---

## 🔀 Pull Request Process

1. Create a descriptive feature branch: `git checkout -b feature/my-enhancement` or `fix/issue-description`.
2. Ensure all tests and lint checks pass cleanly.
3. Do not stage credentials, `.env` files, or student data.
4. Reference the relevant issue number in your pull request description (e.g., `Closes #123`).
5. Open a Pull Request on GitHub against `main`.
