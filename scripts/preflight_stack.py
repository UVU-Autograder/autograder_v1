#!/usr/bin/env python3
"""End-to-end checks against a running autograder stack.

Stdlib only, so it runs on the Dell host without a venv. Normally invoked by
``scripts/preflight_dell.sh`` after ``docker compose up``; can be run alone:

    python3 scripts/preflight_stack.py --api http://127.0.0.1:8000 --judge0 http://127.0.0.1:2358

What it proves, in order:

1. API is up (``/health``).
2. Judge0 actually executes Python *with pytest importable* -- this is the check
   that catches cgroup v2 / isolate failures, which pass every healthcheck.
3. Judge0 ``DELETE /submissions/{token}`` works (the retention contract).
4. Every seeded assignment's model solution scores full marks through the real
   Celery -> Judge0 -> runner -> result_parser path, via the existing
   ``validate-model-solution`` endpoint.
5. One sandbox upload round-trips through intake, rate limiting, and grading.

Exit code 0 only if nothing FAILed.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import sys
import time
import urllib.error
import urllib.request
import uuid
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SEEDS_DIR = REPO_ROOT / "backend" / "app" / "db" / "seeds"

results: list[dict] = []


def record(stage: str, status: str, label: str, detail: str = "") -> None:
    results.append({"stage": stage, "status": status, "check": label, "detail": detail})
    print(f"  {status:<4}  [{stage}] {label}" + (f" -- {detail}" if detail else ""), flush=True)


# --- tiny HTTP helper ------------------------------------------------------


def http(
    method: str,
    url: str,
    *,
    body: bytes | None = None,
    headers: dict[str, str] | None = None,
    timeout: float = 30,
) -> tuple[int, dict | str, dict[str, str]]:
    request = urllib.request.Request(url, data=body, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8", "replace")
            status, resp_headers = response.status, dict(response.headers)
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", "replace")
        status, resp_headers = exc.code, dict(exc.headers or {})
    try:
        return status, json.loads(raw) if raw else {}, resp_headers
    except json.JSONDecodeError:
        return status, raw, resp_headers


def http_json(method: str, url: str, payload: dict | None = None, headers: dict | None = None, timeout: float = 30):
    all_headers = {"Content-Type": "application/json", **(headers or {})}
    body = json.dumps(payload).encode() if payload is not None else None
    return http(method, url, body=body, headers=all_headers, timeout=timeout)


def multipart(fields: dict[str, tuple[str, bytes, str]]) -> tuple[bytes, str]:
    boundary = f"----preflight{uuid.uuid4().hex}"
    parts = []
    for name, (filename, data, content_type) in fields.items():
        parts.append(
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"; "
            f"filename=\"{filename}\"\r\nContent-Type: {content_type}\r\n\r\n".encode()
            + data
            + b"\r\n"
        )
    parts.append(f"--{boundary}--\r\n".encode())
    return b"".join(parts), f"multipart/form-data; boundary={boundary}"


def read_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if path.exists():
        for line in path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                values[key.strip()] = value.strip()
    return values


# --- stages ----------------------------------------------------------------


def check_api(api: str) -> bool:
    try:
        status, body, _ = http("GET", f"{api}/health", timeout=10)
    except Exception as exc:  # noqa: BLE001
        record("api", "FAIL", "GET /health", f"{type(exc).__name__}: {exc}")
        return False
    ok = status == 200 and isinstance(body, dict) and body.get("status") == "ok"
    record("api", "PASS" if ok else "FAIL", "GET /health", f"HTTP {status} {body}")
    return ok


def check_judge0(judge0: str, token: str, language_id: int) -> None:
    headers = {"X-Auth-Token": token} if token else {}
    try:
        status, languages, _ = http("GET", f"{judge0}/languages", headers=headers, timeout=15)
    except Exception as exc:  # noqa: BLE001
        record("judge0", "FAIL", "GET /languages", f"{type(exc).__name__}: {exc}")
        return
    python = [lang for lang in languages if isinstance(lang, dict) and lang.get("id") == language_id] if isinstance(languages, list) else []
    record(
        "judge0",
        "PASS" if python else "FAIL",
        f"language {language_id} (JUDGE0_LANGUAGE_ID) available",
        python[0].get("name", "") if python else f"HTTP {status} -- did judge0-language-seed run?",
    )

    source = "import sys, pytest\nprint('preflight-ok', sys.version.split()[0], pytest.__version__)\n"
    status, created, _ = http_json(
        "POST",
        f"{judge0}/submissions?base64_encoded=false&wait=false",
        {"source_code": source, "language_id": language_id},
        headers,
    )
    submission = created.get("token") if isinstance(created, dict) else None
    if not submission:
        record("judge0", "FAIL", "create submission", f"HTTP {status} {created}")
        return

    deadline, result = time.time() + 60, {}
    while time.time() < deadline:
        _, result, _ = http(
            "GET",
            f"{judge0}/submissions/{submission}?base64_encoded=false"
            "&fields=status,stdout,stderr,message,compile_output",
            headers=headers,
        )
        if isinstance(result, dict) and result.get("status", {}).get("id", 0) >= 3:
            break
        time.sleep(1)

    status_obj = result.get("status", {}) if isinstance(result, dict) else {}
    stdout = (result.get("stdout") or "").strip() if isinstance(result, dict) else ""
    if status_obj.get("id") == 3 and "preflight-ok" in stdout:
        record("judge0", "PASS", "execute Python + import pytest", stdout)
    else:
        detail = f"status={status_obj.get('description', status_obj)}"
        for field in ("message", "stderr", "compile_output"):
            value = result.get(field) if isinstance(result, dict) else None
            if value:
                detail += f" {field}={str(value).strip()[:300]!r}"
        hint = ""
        if "cgroup" in detail.lower() or status_obj.get("id") in (13, None):
            hint = (
                "  <-- typical of cgroup v2: confirm ENABLE_PER_PROCESS_AND_THREAD_*_LIMIT is set on "
                "judge0 + judge0-worker, see the cgroups stage of preflight_dell.sh"
            )
        record("judge0", "FAIL", "execute Python + import pytest", detail + hint)

    status, _, _ = http("DELETE", f"{judge0}/submissions/{submission}", headers=headers)
    if status not in (200, 204):
        record("judge0", "FAIL", "DELETE submission", f"HTTP {status} (is ENABLE_SUBMISSION_DELETE set?)")
        return
    after, _, _ = http("GET", f"{judge0}/submissions/{submission}?fields=status", headers=headers)
    record(
        "judge0",
        "PASS" if after == 404 else "FAIL",
        "deleted submission is gone",
        f"GET after delete -> HTTP {after}",
    )


def staff_token(api: str, email: str) -> str | None:
    status, body, _ = http_json("POST", f"{api}/auth/mock-login", {"email": email})
    token = body.get("access_token") if isinstance(body, dict) else None
    if token:
        record("auth", "PASS", f"mock-login as {email}")
    elif status == 403:
        # A deployed stack may legitimately turn mock login off; that is a skip, not a fault.
        record(
            "auth",
            "WARN",
            f"mock-login as {email}",
            "disabled on this stack (ENABLE_MOCK_LOGIN) -- staff model-solution checks skipped",
        )
    else:
        record("auth", "FAIL", f"mock-login as {email}", f"HTTP {status} {body}")
    return token


def check_model_solutions(api: str, token: str, concurrency: int, timeout_s: float) -> None:
    auth = {"Authorization": f"Bearer {token}"}
    status, courses, _ = http("GET", f"{api}/staff/courses", headers=auth)
    if status != 200 or not isinstance(courses, dict):
        record("grading", "FAIL", "list courses", f"HTTP {status} {courses}")
        return

    targets: list[tuple[str, str]] = []
    for course in courses.get("courses", []):
        status, listing, _ = http("GET", f"{api}/staff/courses/{course['id']}/assignments", headers=auth)
        if status != 200 or not isinstance(listing, dict):
            record("grading", "FAIL", f"list assignments for {course['id']}", f"HTTP {status}")
            continue
        targets += [(course["id"], a["id"]) for a in listing.get("assignments", [])]

    if not targets:
        record("grading", "FAIL", "seeded assignments present", "none found -- did SEED_DATABASE run?")
        return
    record("grading", "PASS", "seeded assignments present", f"{len(targets)} found")

    def base(course_id: str, assignment_id: str) -> str:
        return f"{api}/staff/courses/{course_id}/assignments/{assignment_id}"

    passed = 0
    for start in range(0, len(targets), concurrency):
        batch = targets[start : start + concurrency]
        started: dict[tuple[str, str], float] = {}
        for course_id, assignment_id in batch:
            status, body, _ = http_json("POST", f"{base(course_id, assignment_id)}/validate-model-solution", None, auth)
            if status != 200:
                hint = " -- backend can't reach Redis/Celery? check: docker compose logs backend" if status >= 500 else ""
                record("grading", "FAIL", f"{course_id}/{assignment_id}", f"enqueue HTTP {status} {str(body)[:200]}{hint}")
                continue
            started[(course_id, assignment_id)] = time.time()

        pending = dict(started)
        while pending:
            for key in list(pending):
                course_id, assignment_id = key
                _, body, _ = http("GET", f"{base(course_id, assignment_id)}/validation-status", headers=auth)
                state = body.get("status") if isinstance(body, dict) else None
                elapsed = time.time() - pending[key]
                if state in ("success", "complete", "failure"):
                    score, max_score = body.get("score", 0), body.get("max_score", 0)
                    ok = state != "failure" and max_score > 0 and score == max_score
                    if ok:
                        passed += 1
                    detail = f"{score}/{max_score} in {elapsed:.0f}s"
                    if not ok and body.get("errors"):
                        detail += " -- " + " | ".join(str(e) for e in body["errors"])[:500]
                    record("grading", "PASS" if ok else "FAIL", f"model solution {course_id}/{assignment_id}", detail)
                    del pending[key]
                elif elapsed > timeout_s:
                    record(
                        "grading",
                        "FAIL",
                        f"model solution {course_id}/{assignment_id}",
                        f"still '{state}' after {timeout_s:.0f}s -- is celery-worker running?",
                    )
                    del pending[key]
            if pending:
                time.sleep(2)

    record(
        "grading",
        "PASS" if passed == len(targets) else "FAIL",
        "all model solutions at full score",
        f"{passed}/{len(targets)}",
    )


def check_sandbox(api: str, seed: str, timeout_s: float) -> None:
    status, courses, _ = http("GET", f"{api}/sandbox/courses")
    if status != 200 or not isinstance(courses, dict):
        record("sandbox", "FAIL", "list sandbox courses", f"HTTP {status}")
        return

    target = None
    for course in courses.get("courses", []):
        _, listing, _ = http("GET", f"{api}/sandbox/courses/{course['id']}/assignments")
        for assignment in (listing or {}).get("assignments", []) if isinstance(listing, dict) else []:
            if assignment["id"] == seed:
                target = (course["id"], assignment)
    if target is None:
        record("sandbox", "WARN", f"sandbox-enabled assignment '{seed}'", "not found; skipped sandbox round-trip")
        return
    course_id, assignment = target

    seed_dir = SEEDS_DIR / seed
    config = json.loads((seed_dir / "config_json.example.json").read_text())
    filenames = [
        a["display_filename"]
        for a in config.get("artifacts", {}).values()
        if a.get("type") == "model_solution" and a.get("display_filename")
    ]
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for name in filenames:
            archive.write(seed_dir / name, arcname=name)

    body, content_type = multipart({"bundle": ("preflight.zip", buffer.getvalue(), "application/zip")})
    status, created, headers = http(
        "POST",
        f"{api}/sandbox/courses/{course_id}/assignments/{assignment['id']}/runs",
        body=body,
        headers={"Content-Type": content_type},
    )
    if status != 202 or not isinstance(created, dict):
        record("sandbox", "FAIL", "upload bundle", f"HTTP {status} {str(created)[:300]}")
        return
    session = headers.get("X-Sandbox-Session") or headers.get("x-sandbox-session") or created.get("sandbox_session")
    quota_after = created.get("upload_quota", {}).get("remaining")
    quota_before = assignment.get("upload_quota", {}).get("remaining")
    record("sandbox", "PASS", "upload accepted (202)", f"run_id={created.get('run_id')}")
    decremented = quota_after is not None and quota_before is not None and quota_after < quota_before
    record(
        "sandbox",
        "PASS" if decremented else "WARN",
        "rate-limit quota decremented",
        f"{quota_before} -> {quota_after}" + ("" if decremented else " (Redis rate limiter may be falling back)"),
    )

    deadline = time.time() + timeout_s
    while time.time() < deadline:
        status, result, _ = http("GET", f"{api}{created['result_url']}", headers={"X-Sandbox-Session": session or ""})
        if status == 200:
            ok = result.get("state") == "complete" and result.get("projected_score") == result.get("max_score")
            record(
                "sandbox",
                "PASS" if ok else "FAIL",
                f"sandbox grade of {seed} model solution",
                f"state={result.get('state')} {result.get('projected_score')}/{result.get('max_score')}",
            )
            return
        if status != 409:
            record("sandbox", "FAIL", "fetch result", f"HTTP {status} {str(result)[:300]}")
            return
        time.sleep(2)
    record("sandbox", "FAIL", "fetch result", f"not ready after {timeout_s:.0f}s")


def main(argv: list[str] | None = None) -> int:
    env = read_env_file(REPO_ROOT / ".env.local")
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--api", default="http://127.0.0.1:8000")
    parser.add_argument("--judge0", default="http://127.0.0.1:2358")
    parser.add_argument(
        "--language-id",
        type=int,
        default=int(os.environ.get("JUDGE0_LANGUAGE_ID") or env.get("JUDGE0_LANGUAGE_ID", "711")),
        help="Judge0 language the backend grades with (711 = custom Python 3.11.9)",
    )
    parser.add_argument("--judge0-token", default=os.environ.get("JUDGE0_AUTH_TOKEN") or env.get("JUDGE0_AUTH_TOKEN", "judge0-testing-token"))
    parser.add_argument("--staff-email", default="dev.staff@uvu.edu")
    parser.add_argument("--concurrency", type=int, default=int(env.get("JUDGE0_MAX_CONCURRENT", "2")))
    parser.add_argument("--timeout", type=float, default=180.0, help="Per-assignment seconds")
    parser.add_argument("--sandbox-seed", default="ds2")
    parser.add_argument("--json-out", type=Path, help="Write machine-readable results here")
    args = parser.parse_args(argv)

    if check_api(args.api):
        check_judge0(args.judge0, args.judge0_token, args.language_id)
        token = staff_token(args.api, args.staff_email)
        if token:
            check_model_solutions(args.api, token, max(1, args.concurrency), args.timeout)
        check_sandbox(args.api, args.sandbox_seed, args.timeout)
    else:
        check_judge0(args.judge0, args.judge0_token, args.language_id)

    failed = [r for r in results if r["status"] == "FAIL"]
    summary = {
        "pass": sum(r["status"] == "PASS" for r in results),
        "warn": sum(r["status"] == "WARN" for r in results),
        "fail": len(failed),
    }
    if args.json_out:
        args.json_out.write_text(json.dumps({"summary": summary, "results": results}, indent=2))
    print(f"\nstack checks: {summary['pass']} pass, {summary['warn']} warn, {summary['fail']} fail")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
