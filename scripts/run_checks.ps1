# UVU Autograder - Unified Quality & Verification Checks (PowerShell)
# Usage: .\scripts\run_checks.ps1

$ErrorActionPreference = "Stop"
$RepoRoot = (Get-Item $PSScriptRoot).Parent.FullName
Write-Host "=== Running UVU Autograder Quality Checks ===" -ForegroundColor Cyan
Write-Host "Repository root: $RepoRoot`n"

# 1. Determine Python executable (venv or system)
$Python = if (Test-Path "$RepoRoot\backend\venv\Scripts\python.exe") {
    "$RepoRoot\backend\venv\Scripts\python.exe"
} else {
    "python"
}

# 2. Backend Linting (Ruff)
Write-Host "--> [1/6] Backend Linting (ruff)..." -ForegroundColor Yellow
Push-Location "$RepoRoot\backend"
try {
    & $Python -m ruff check app tests
    if ($LASTEXITCODE -ne 0) { throw "Ruff linting failed." }
    Write-Host "  Ruff check passed.`n" -ForegroundColor Green
} finally {
    Pop-Location
}

# 3. Backend Unit Tests
Write-Host "--> [2/6] Backend Unit Tests (pytest)..." -ForegroundColor Yellow
Push-Location "$RepoRoot\backend"
try {
    & $Python -m pytest tests/unit -q
    if ($LASTEXITCODE -ne 0) { throw "Backend pytest unit tests failed." }
    Write-Host "  Backend unit tests passed.`n" -ForegroundColor Green
} finally {
    Pop-Location
}

# 4. Database Migration Schema Drift Check
Write-Host "--> [3/6] Database Schema Drift Check (alembic check)..." -ForegroundColor Yellow
Push-Location "$RepoRoot\backend"
$TempDb = "$RepoRoot\backend\check_drift_tmp.db"
try {
    if (Test-Path $TempDb) { Remove-Item $TempDb -Force }
    $env:DATABASE_URL = "sqlite+pysqlite:///$TempDb"
    & $Python -m alembic upgrade head | Out-Null
    & $Python -m alembic check
    if ($LASTEXITCODE -ne 0) { throw "Alembic check detected unmigrated schema drift." }
    Write-Host "  Schema drift check passed (0 drift).`n" -ForegroundColor Green
} finally {
    if (Test-Path $TempDb) { Remove-Item $TempDb -Force }
    $env:DATABASE_URL = ""
    Pop-Location
}

# 5. Frontend Type Check
Write-Host "--> [4/6] Frontend Type Check (tsc)..." -ForegroundColor Yellow
Push-Location "$RepoRoot\frontend"
try {
    npm run type-check
    if ($LASTEXITCODE -ne 0) { throw "Frontend type check failed." }
    Write-Host "  TypeScript check passed.`n" -ForegroundColor Green
} finally {
    Pop-Location
}

# 6. Frontend Linting (ESLint)
Write-Host "--> [5/6] Frontend Linting (eslint)..." -ForegroundColor Yellow
Push-Location "$RepoRoot\frontend"
try {
    npm run lint
    if ($LASTEXITCODE -ne 0) { throw "Frontend linting failed." }
    Write-Host "  ESLint check passed.`n" -ForegroundColor Green
} finally {
    Pop-Location
}

# 7. Frontend Tests (Vitest)
Write-Host "--> [6/6] Frontend Unit Tests (vitest)..." -ForegroundColor Yellow
Push-Location "$RepoRoot\frontend"
try {
    npm run test
    if ($LASTEXITCODE -ne 0) { throw "Frontend unit tests failed." }
    Write-Host "  Frontend tests passed.`n" -ForegroundColor Green
} finally {
    Pop-Location
}

Write-Host "=== All Quality Checks Passed Successfully! ===" -ForegroundColor Green
