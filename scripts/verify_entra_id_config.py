#!/usr/bin/env python3
"""verify_entra_id_config.py — Pre-deployment Microsoft Entra ID verification.

Verifies:
  1. Azure AD settings in the active .env / environment.
  2. Outbound HTTPS reachability from host to login.microsoftonline.com.
  3. Tenant OpenID discovery metadata retrieval.
  4. Public JWKS signing key retrieval and parsing.
  5. Token validation configuration readiness.

Usage:
  python scripts/verify_entra_id_config.py [path/to/.env] [--strict]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def parse_env_file(path: Path) -> dict[str, str]:
    env = {}
    if not path.is_file():
        return env
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip("'\"")
    return env


def main() -> int:
    parser = argparse.ArgumentParser(description="Pre-deployment Microsoft Entra ID verification.")
    parser.add_argument("--env-file", dest="env_file_opt", help="Path to .env file (optional flag)")
    parser.add_argument("env_file", nargs="?", default=None, help="Path to .env file (positional)")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with code 1 if institutional credentials are unconfigured or placeholders.",
    )
    args = parser.parse_args()

    chosen_file = args.env_file_opt or args.env_file or str(REPO_ROOT / ".env")
    env_path = Path(chosen_file)
    file_vars = parse_env_file(env_path)
    active_env = {**file_vars, **os.environ}

    print("=== UVU Autograder - Microsoft Entra ID Configuration Verifier ===")
    print(f"Inspecting configuration from: {env_path}\n")

    auth_provider = active_env.get("AUTH_PROVIDER", "mock")
    environment = active_env.get("ENVIRONMENT", "development")
    next_public_auth = active_env.get("NEXT_PUBLIC_AUTH_PROVIDER", "")
    client_id = active_env.get("AZURE_AD_CLIENT_ID", "")
    tenant_id = active_env.get("AZURE_AD_TENANT_ID", "")
    client_secret = active_env.get("AZURE_AD_CLIENT_SECRET", "")

    print(f"  AUTH_PROVIDER              : {auth_provider}")
    print(f"  ENVIRONMENT                : {environment}")
    print(f"  NEXT_PUBLIC_AUTH_PROVIDER  : {next_public_auth or '(unset)'}")
    print(f"  AZURE_AD_CLIENT_ID         : {client_id or '(not configured)'}")
    print(f"  AZURE_AD_TENANT_ID         : {tenant_id or '(not configured - defaults to common)'}")
    print(f"  AZURE_AD_CLIENT_SECRET     : {'[CONFIGURED]' if client_secret else '(not configured)'}")
    print("")

    effective_tenant = tenant_id if (tenant_id and "change-me" not in tenant_id) else "common"
    discovery_url = f"https://login.microsoftonline.com/{effective_tenant}/v2.0/.well-known/openid-configuration"

    print("[1/3] Probing Microsoft OpenID Discovery Endpoint...")
    print(f"      URL: {discovery_url}")
    jwks_uri = None
    try:
        req = urllib.request.Request(discovery_url, headers={"User-Agent": "UVU-Autograder-Verifier/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status == 200:
                discovery_data = json.loads(resp.read().decode("utf-8"))
                jwks_uri = discovery_data.get("jwks_uri")
                issuer = discovery_data.get("issuer")
                if not jwks_uri or not isinstance(jwks_uri, str):
                    print("      [ERROR] Discovery document missing valid 'jwks_uri'")
                    return 1
                print("      [OK] Reachable (HTTP 200)")
                print(f"      - Token Issuer: {issuer}")
                print(f"      - JWKS URI    : {jwks_uri}")
            else:
                print(f"      [ERROR] HTTP error: {resp.status}")
                return 1
    except (urllib.error.URLError, json.JSONDecodeError, ValueError) as err:
        print(f"      [ERROR] Discovery probe failed: {err}")
        print("        Ensure host has outbound HTTPS access (port 443) to login.microsoftonline.com.")
        return 1

    print("\n[2/3] Fetching and Validating Public JWKS Keys...")
    print(f"      URL: {jwks_uri}")
    try:
        req = urllib.request.Request(jwks_uri, headers={"User-Agent": "UVU-Autograder-Verifier/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status == 200:
                jwks_data = json.loads(resp.read().decode("utf-8"))
                keys = jwks_data.get("keys", [])
                print(f"      [OK] Retrieved {len(keys)} public signing key(s)")
                key_ids = [k.get("kid", "unknown") for k in keys[:3]]
                print(f"      - Sample Key IDs: {', '.join(key_ids)}")
            else:
                print(f"      [ERROR] Failed to fetch JWKS: HTTP {resp.status}")
                return 1
    except (urllib.error.URLError, json.JSONDecodeError, ValueError) as err:
        print(f"      [ERROR] JWKS fetch failed: {err}")
        return 1

    print("\n[3/3] Evaluating Institutional Pilot Readiness...")
    warnings = []
    if auth_provider != "microsoft":
        warnings.append(f"AUTH_PROVIDER is '{auth_provider}' (must be 'microsoft' for institutional logins).")
    if next_public_auth and auth_provider == "microsoft" and next_public_auth != "microsoft":
        warnings.append(f"NEXT_PUBLIC_AUTH_PROVIDER is '{next_public_auth}' (should match AUTH_PROVIDER='microsoft').")
    if not client_id or "change-me" in client_id:
        warnings.append("AZURE_AD_CLIENT_ID is empty or placeholder (requires UVU IT App Registration).")
    if not tenant_id or "change-me" in tenant_id:
        warnings.append("AZURE_AD_TENANT_ID is empty or placeholder (requires UVU Institutional Tenant ID).")
    if not client_secret or "change-me" in client_secret:
        warnings.append("AZURE_AD_CLIENT_SECRET is empty or placeholder.")

    if warnings:
        print("  [WARN] Pending Institutional Credentials:")
        for w in warnings:
            print(f"     - {w}")
        print("\n  Network and Microsoft discovery infrastructure: VERIFIED OK.")
        print("  Action: Request App Registration from UVU IT using docs/operations/public_internet_access_plan.md.")
        if args.strict:
            return 1
    else:
        print("  [OK] All credentials configured and discovery endpoints verified.")
        print("  Ready for institutional Microsoft Entra ID logins!")

    return 0


if __name__ == "__main__":
    sys.exit(main())
