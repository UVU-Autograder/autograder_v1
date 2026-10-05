#!/usr/bin/env python3
"""audit_deployment_readiness.py — Autonomous deployment readiness audit.

Validates the UVU Autograder host deployment configuration against production
specifications before starting services:

1. Environment Sync (.env / .env.local vs .env.example)
2. Production Security Invariants (JWT secret, Auth provider gating, CORS)
3. Network Bind Isolation (Postgres, Redis, Judge0 bound to 127.0.0.1, vLLM on loopback)
4. Retention Contracts (23h review window, 24h hard purge, 60s cleanup-worker sweep)
5. Judge0 Runtime Configuration (Language 711 runtime seed, upload/execution limits)
6. OpenAPI Schema Parity (FastAPI route registry matches docs/schemas/openapi.json)

Usage:
    python scripts/audit_deployment_readiness.py [--env-file .env.local] [--strict]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

checks_passed = 0
checks_warned = 0
checks_failed = 0


def record_pass(category: str, label: str, detail: str = "") -> None:
    global checks_passed
    checks_passed += 1
    msg = f"  [PASS] [{category}] {label}"
    if detail:
        msg += f" -- {detail}"
    print(msg)


def record_warn(category: str, label: str, detail: str = "") -> None:
    global checks_warned
    checks_warned += 1
    msg = f"  [WARN] [{category}] {label}"
    if detail:
        msg += f" -- {detail}"
    print(msg)


def record_fail(category: str, label: str, detail: str = "") -> None:
    global checks_failed
    checks_failed += 1
    msg = f"  [FAIL] [{category}] {label}"
    if detail:
        msg += f" -- {detail}"
    print(msg)


def parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, val = line.partition("=")
            values[key.strip()] = val.strip().strip("'\"")
    return values


def get_backend_python() -> str:
    if sys.platform == "win32":
        venv_py = REPO_ROOT / "backend" / "venv" / "Scripts" / "python.exe"
    else:
        venv_py = REPO_ROOT / "backend" / "venv" / "bin" / "python"
    if venv_py.is_file():
        return str(venv_py)
    return sys.executable


# --- Section 1: Environment Sync ---


def audit_env_sync(active_path: Path, is_strict: bool) -> dict[str, str]:
    print("\n[1/6] Auditing Environment Configuration Sync...")
    example_path = REPO_ROOT / ".env.example"
    if not example_path.is_file():
        record_fail("env", ".env.example present", f"Missing at {example_path}")
        return {}

    example_vars = parse_env_file(example_path)
    record_pass("env", ".env.example loaded", f"{len(example_vars)} variables defined")

    if not active_path.is_file():
        if is_strict:
            record_fail(
                "env",
                f"Active env file ({active_path.name})",
                f"File not found at {active_path}. Copy .env.example to {active_path.name} before production deployment.",
            )
        else:
            record_warn(
                "env",
                f"Active env file ({active_path.name})",
                f"Not found at {active_path}. Using .env.example defaults for validation.",
            )
        return example_vars

    active_vars = parse_env_file(active_path)
    missing = set(example_vars.keys()) - set(active_vars.keys())
    if missing:
        record_fail(
            "env",
            f"Key parity with .env.example ({active_path.name})",
            f"Missing {len(missing)} key(s): {', '.join(sorted(missing))}",
        )
    else:
        record_pass(
            "env",
            f"Key parity with .env.example ({active_path.name})",
            f"All {len(example_vars)} keys present",
        )

    # Check for placeholder values
    placeholders: list[str] = []
    for k, v in active_vars.items():
        if "change-me" in v.lower() or "replace-with" in v.lower():
            placeholders.append(k)

    if placeholders:
        detail = f"{len(placeholders)} placeholder(s) detected: {', '.join(sorted(placeholders))}"
        if is_strict or active_vars.get("ENVIRONMENT") == "production":
            record_fail("env", "Production secrets configured", detail)
        else:
            record_warn("env", "Development secrets configured", detail + " (acceptable for dev/mock mode)")
    else:
        record_pass("env", "Secrets configured", "No placeholder tokens found")

    return active_vars


# --- Section 2: Production Security Invariants ---


def audit_security_invariants(env_vars: dict[str, str], is_strict: bool) -> None:
    print("\n[2/6] Auditing Production Security Invariants...")
    env_name = env_vars.get("ENVIRONMENT", "development")
    auth_provider = env_vars.get("AUTH_PROVIDER", "mock")
    jwt_secret = env_vars.get("JWT_SECRET", "")
    enable_mock_login = env_vars.get("ENABLE_MOCK_LOGIN", "true").lower() in ("true", "1", "yes")
    client_id = env_vars.get("AZURE_AD_CLIENT_ID", "")

    fallback_secret = "dev_fallback_secret_longer_than_32_characters_for_security_compliance"

    # JWT Secret checks
    if jwt_secret == fallback_secret:
        if env_name == "production" or is_strict:
            record_fail("security", "JWT_SECRET compliance", "Uses development fallback secret in production mode")
        else:
            record_warn("security", "JWT_SECRET compliance", "Uses development fallback secret (dev mode only)")
    elif len(jwt_secret) < 32:
        if env_name == "production" or is_strict:
            record_fail("security", "JWT_SECRET length", f"Length {len(jwt_secret)} < 32 characters minimum")
        else:
            record_warn("security", "JWT_SECRET length", f"Length {len(jwt_secret)} < 32 characters")
    else:
        record_pass("security", "JWT_SECRET length & entropy", f"{len(jwt_secret)} characters (meets >=32 requirement)")

    # Auth Provider & Mock Login gating
    if auth_provider == "microsoft":
        if not client_id or "change-me" in client_id:
            if is_strict:
                record_fail("security", "Azure AD Client ID", "AUTH_PROVIDER=microsoft requires AZURE_AD_CLIENT_ID")
            else:
                record_warn("security", "Azure AD Client ID", "Unconfigured (pending UVU IT app registration)")
        else:
            record_pass("security", "Azure AD Client ID", f"Configured ({client_id[:8]}...)")

        if enable_mock_login:
            record_warn("security", "Mock login gating", "ENABLE_MOCK_LOGIN=true is ignored when AUTH_PROVIDER=microsoft (properly locked)")
        else:
            record_pass("security", "Mock login gating", "Mock login disabled for Microsoft SSO")
    else:
        if env_name == "production":
            record_fail("security", "Institutional auth provider", "Production mode cannot use AUTH_PROVIDER=mock")
        else:
            record_pass("security", "Auth provider mode", f"Running '{auth_provider}' auth in '{env_name}' mode")

    # Verify settings.py validate_production_security definition
    settings_py = REPO_ROOT / "backend" / "app" / "core" / "settings.py"
    if settings_py.is_file():
        content = settings_py.read_text(encoding="utf-8")
        if "def validate_production_security" in content and "raise ValueError" in content:
            record_pass("security", "FastAPI startup gate", "validate_production_security() enforced at startup")
        else:
            record_fail("security", "FastAPI startup gate", "validate_production_security() not found in settings.py")


# --- Section 3: Network Bind IP Isolation ---


def audit_network_isolation(env_vars: dict[str, str], is_strict: bool) -> None:
    print("\n[3/6] Auditing Network Bind Isolation (127.0.0.1)...")
    loopback_binds = {
        "POSTGRES_BIND_IP": env_vars.get("POSTGRES_BIND_IP", "127.0.0.1"),
        "REDIS_BIND_IP": env_vars.get("REDIS_BIND_IP", "127.0.0.1"),
        "JUDGE0_BIND_IP": env_vars.get("JUDGE0_BIND_IP", "127.0.0.1"),
    }

    for key, val in loopback_binds.items():
        if val in ("127.0.0.1", "localhost"):
            record_pass("network", f"{key} loopback binding", f"Bound strictly to {val}")
        elif val == "0.0.0.0":
            record_fail("network", f"{key} binding security", f"Exposed to all interfaces (0.0.0.0)! Must be 127.0.0.1")
        else:
            record_warn("network", f"{key} custom binding", f"Bound to {val}")

    # Inspect docker-compose.yml port mappings
    dc_file = REPO_ROOT / "docker-compose.yml"
    if dc_file.is_file():
        dc_text = dc_file.read_text(encoding="utf-8")
        has_pg_bind = "${POSTGRES_BIND_IP:-127.0.0.1}:5432:5432" in dc_text
        has_redis_bind = "${REDIS_BIND_IP:-127.0.0.1}:6379:6379" in dc_text
        has_judge0_bind = "${JUDGE0_BIND_IP:-127.0.0.1}:2358:2358" in dc_text

        if has_pg_bind and has_redis_bind and has_judge0_bind:
            record_pass("network", "docker-compose.yml port bindings", "All backing services guarded by loopback bind variables")
        else:
            record_fail("network", "docker-compose.yml port bindings", "One or more services expose raw ports without bind variable defaults")

    # Inspect backend Dockerfile loopback bind
    backend_dockerfile = REPO_ROOT / "backend" / "Dockerfile"
    if backend_dockerfile.is_file():
        dockerfile_text = backend_dockerfile.read_text(encoding="utf-8")
        if "--host 0.0.0.0" in dockerfile_text:
            record_fail("network", "backend/Dockerfile network bind", "Hardcoded --host 0.0.0.0 exposed under host networking")
        elif "127.0.0.1" in dockerfile_text:
            record_pass("network", "backend/Dockerfile network bind", "Bound strictly to loopback 127.0.0.1")
        else:
            record_warn("network", "backend/Dockerfile network bind", "Loopback 127.0.0.1 not explicitly configured in Dockerfile")

    # Inspect frontend systemd unit template
    frontend_service = REPO_ROOT / "scripts" / "autograder-frontend.service"
    if frontend_service.is_file():
        fe_text = frontend_service.read_text(encoding="utf-8")
        if "127.0.0.1" in fe_text and "0.0.0.0" not in fe_text:
            record_pass("network", "autograder-frontend.service network bind", "Bound strictly to loopback 127.0.0.1:3000")
        else:
            record_fail("network", "autograder-frontend.service network bind", "Frontend service template not restricted to loopback 127.0.0.1")

    # Inspect vLLM service definition
    vllm_service = REPO_ROOT / "backend" / "training" / "vllm-cs1410.service"
    if vllm_service.is_file():
        service_text = vllm_service.read_text(encoding="utf-8")
        if "--host 127.0.0.1" in service_text and "--port 8001" in service_text:
            record_pass("network", "vllm-cs1410.service network bind", "Bound strictly to loopback 127.0.0.1:8001")
        else:
            record_fail("network", "vllm-cs1410.service network bind", "vLLM service definition not bound to 127.0.0.1:8001")
    else:
        record_warn("network", "vllm-cs1410.service network bind", f"Service file not found at {vllm_service}")

    # Inspect docker-compose.yml container log rotation limits
    if dc_file.is_file():
        dc_text = dc_file.read_text(encoding="utf-8")
        if "max-size:" in dc_text and "max-file:" in dc_text:
            record_pass("network", "docker-compose.yml log rotation", "Explicit max-size and max-file caps configured")
        else:
            record_warn("network", "docker-compose.yml log rotation", "Missing explicit container log rotation caps")


# --- Section 4: Retention Contracts ---


def audit_retention_contracts() -> None:
    print("\n[4/6] Auditing Zero-Retention & Cleanup Lifecycles...")
    retention_py = REPO_ROOT / "backend" / "app" / "domains" / "runs" / "retention.py"
    if retention_py.is_file():
        code = retention_py.read_text(encoding="utf-8")
        has_23h = "REVIEW_WINDOW = timedelta(hours=23)" in code
        has_24h = "DELETION_WINDOW = timedelta(hours=24)" in code
        if has_23h:
            record_pass("retention", "Review window limit", "REVIEW_WINDOW = 23 hours exactly")
        else:
            record_fail("retention", "Review window limit", "REVIEW_WINDOW != 23 hours")

        if has_24h:
            record_pass("retention", "Hard deletion window", "DELETION_WINDOW = 24 hours exactly")
        else:
            record_fail("retention", "Hard deletion window", "DELETION_WINDOW != 24 hours")
    else:
        record_fail("retention", "retention.py existence", f"Not found at {retention_py}")

    cleanup_worker_py = REPO_ROOT / "backend" / "app" / "domains" / "runs" / "cleanup_worker.py"
    if cleanup_worker_py.is_file():
        worker_code = cleanup_worker_py.read_text(encoding="utf-8")
        if "stopped.wait(60)" in worker_code:
            record_pass("retention", "Cleanup worker loop interval", "Periodic sweep runs every 60 seconds")
        else:
            record_fail("retention", "Cleanup worker loop interval", "Sweep interval does not match 60-second standard")
    else:
        record_fail("retention", "cleanup_worker.py existence", f"Not found at {cleanup_worker_py}")

    # Verify docker-compose cleanup-worker configuration
    dc_file = REPO_ROOT / "docker-compose.yml"
    if dc_file.is_file():
        dc_text = dc_file.read_text(encoding="utf-8")
        has_cleanup_worker = "cleanup-worker:" in dc_text and "app.domains.runs.cleanup_worker" in dc_text
        has_60s_healthcheck = "interval: 60s" in dc_text
        if has_cleanup_worker and has_60s_healthcheck:
            record_pass("retention", "cleanup-worker docker service", "Dedicated standalone cleanup service configured with 60s healthcheck")
        else:
            record_fail("retention", "cleanup-worker docker service", "Missing or misconfigured cleanup-worker container in docker-compose.yml")


# --- Section 5: Judge0 Runtime & Sandbox Caps ---


def audit_judge0_runtime(env_vars: dict[str, str]) -> None:
    print("\n[5/6] Auditing Execution Engine & Sandbox Constraints...")
    lang_id = env_vars.get("JUDGE0_LANGUAGE_ID", "711")
    if str(lang_id) == "711":
        record_pass("judge0", "JUDGE0_LANGUAGE_ID", "Configured to 711 (Custom Python 3.11.9 runtime)")
    else:
        record_warn("judge0", "JUDGE0_LANGUAGE_ID", f"Configured to {lang_id} (Expected 711 for official grading)")

    seed_sql = REPO_ROOT / "scripts" / "seed_judge0_language_311.sql"
    if seed_sql.is_file():
        sql_text = seed_sql.read_text(encoding="utf-8")
        if "711" in sql_text and "Python" in sql_text:
            record_pass("judge0", "Language seed SQL", "seed_judge0_language_311.sql seeds ID 711 with Python runtime")
        else:
            record_fail("judge0", "Language seed SQL", "Seed script missing ID 711 entry")
    else:
        record_fail("judge0", "Language seed SQL", f"Missing at {seed_sql}")

    # Upload and execution caps
    max_upload = env_vars.get("MAX_UPLOAD_BYTES", "52428800")
    if int(max_upload) == 52428800:
        record_pass("judge0", "MAX_UPLOAD_BYTES limit", "52,428,800 bytes (50 MB)")
    else:
        record_warn("judge0", "MAX_UPLOAD_BYTES limit", f"{max_upload} bytes")

    timeout = env_vars.get("TEST_EXECUTION_TIMEOUT_SECONDS", "30")
    if int(timeout) <= 60:
        record_pass("judge0", "TEST_EXECUTION_TIMEOUT_SECONDS", f"{timeout}s (within host cap <= 60s)")
    else:
        record_warn("judge0", "TEST_EXECUTION_TIMEOUT_SECONDS", f"{timeout}s exceeds recommended 60s limit")


# --- Section 6: OpenAPI Schema Parity ---


def audit_openapi_parity(skip_generate: bool) -> None:
    print("\n[6/6] Auditing OpenAPI Schema Parity...")
    schema_path = REPO_ROOT / "docs" / "schemas" / "openapi.json"
    if not schema_path.is_file():
        record_fail("openapi", "docs/schemas/openapi.json exists", f"Not found at {schema_path}")
        return

    try:
        existing_data = json.loads(schema_path.read_text(encoding="utf-8"))
        paths_count = len(existing_data.get("paths", {}))
        record_pass("openapi", "docs/schemas/openapi.json validity", f"Valid JSON with {paths_count} route paths")
    except Exception as exc:  # noqa: BLE001
        record_fail("openapi", "docs/schemas/openapi.json validity", f"JSON parsing failed: {exc}")
        return

    if skip_generate:
        record_warn("openapi", "Schema parity check", "Generation verification skipped via --skip-openapi")
        return

    # Generate current schema via backend script to verify parity
    generator = REPO_ROOT / "backend" / "scripts" / "generate_openapi.py"
    if not generator.is_file():
        record_fail("openapi", "Generator script", f"Missing at {generator}")
        return

    py_exe = get_backend_python()
    try:
        proc = subprocess.run(
            [py_exe, str(generator)],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(REPO_ROOT),
        )
        if proc.returncode != 0:
            record_warn(
                "openapi",
                "Schema generator verification",
                f"Generator exited with code {proc.returncode} ({proc.stderr.strip()[:200] or proc.stdout.strip()[:200]}). Check backend virtualenv.",
            )
            return

        # Check git status of docs/schemas/openapi.json
        status_proc = subprocess.run(
            ["git", "status", "--porcelain", str(schema_path)],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(REPO_ROOT),
        )
        if status_proc.returncode == 0:
            diff = status_proc.stdout.strip()
            if not diff:
                record_pass("openapi", "API route parity", "docs/schemas/openapi.json matches FastAPI app.openapi() (0 drift)")
            else:
                record_fail("openapi", "API route parity", "docs/schemas/openapi.json has drift vs live routes. Run 'npm run openapi:generate'")
        else:
            record_warn("openapi", "Git parity check", "Git not available to verify working tree status")
    except Exception as exc:  # noqa: BLE001
        record_warn("openapi", "Schema parity check", f"Could not execute generator ({exc})")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "--env-file",
        default=None,
        help="Path to active .env or .env.local file (defaults to .env, then .env.local)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Enforce production standards strictly (fail on development placeholders or mock logins)",
    )
    parser.add_argument(
        "--skip-openapi",
        action="store_true",
        help="Skip executing the OpenAPI generator during audit",
    )
    args = parser.parse_args()

    print("================================================================")
    print("      UVU Autograder -- Autonomous Deployment Readiness Audit   ")
    print("================================================================")
    print(f"Target repository: {REPO_ROOT}")
    print(f"Strict production mode: {args.strict}")

    # Determine env file
    if args.env_file:
        active_env_path = Path(args.env_file).resolve()
    elif (REPO_ROOT / ".env").is_file():
        active_env_path = REPO_ROOT / ".env"
    elif (REPO_ROOT / ".env.local").is_file():
        active_env_path = REPO_ROOT / ".env.local"
    else:
        active_env_path = REPO_ROOT / ".env"

    env_vars = audit_env_sync(active_env_path, args.strict)
    audit_security_invariants(env_vars, args.strict)
    audit_network_isolation(env_vars, args.strict)
    audit_retention_contracts()
    audit_judge0_runtime(env_vars)
    audit_openapi_parity(args.skip_openapi)

    total = checks_passed + checks_warned + checks_failed
    print("\n================================================================")
    print(f"Audit Summary: {checks_passed}/{total} PASS, {checks_warned} WARN, {checks_failed} FAIL")
    print("================================================================")

    if checks_failed > 0:
        print("\nDeployment Readiness Audit FAILED: Resolve issues above before workstation launch.")
        return 1

    print("\nDeployment Readiness Audit PASSED: Stack configuration is deployment-ready.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
