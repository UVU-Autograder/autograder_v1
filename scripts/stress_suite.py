#!/usr/bin/env python3
"""Stress-test sandbox grading (Judge0) and AI feedback the way students use them.

    python3 scripts/stress_suite.py grading --levels 1,4,8,16,32,48 --json-out ~/stress-grading.json
    python3 scripts/stress_suite.py ai --levels 1,8,16,32,48 --json-out ~/stress-ai.json
    python3 scripts/stress_suite.py burst --students 40 --json-out ~/stress-burst.json
    python3 scripts/stress_suite.py judge0 --judge0-token "$JUDGE0_AUTH_TOKEN" --levels 1,2,4,8
    python3 scripts/stress_suite.py all --json-out ~/stress-all.json

Scenarios
---------
grading  N simulated students submit at the same moment (fresh sessions, synthetic
         eval cases), back off and retry on "queue full" like the sandbox UI, then
         poll status at the UI's cadence until done. Reports admission outcomes,
         time in queue vs grading, failures by category, how many runs would have
         hit the old 75 s browser give-up, the queue depth over time, and how
         accurate the "about N ahead / ~M s" estimate was.
ai       Graded runs, then N students ask for AI feedback at once. First-attempt
         outcomes (answer / busy / timeout / offline) and, with UI-style retries,
         how many students eventually got feedback and how long it took.
burst    An end-of-lab burst: M students submit, wait for results, think 10-60 s,
         then ask for AI feedback with UI-style retries.
judge0   Raw Judge0 throughput (bypassing the backend) at rising concurrency, and
         a zero-retention check: every submission is deleted and must then 404
         (re-read for up to 2.5 s, since Judge0 caches a GET for about a second).

Run it on the Dell in tmux, in a window agreed with the team: it loads the live
stack (a full grading queue blocks real students and official grading). It uses
synthetic code only and writes aggregate numbers only -- no run ids, sessions or
code -- as docs/running.md requires. Standard library only.
"""

from __future__ import annotations

import argparse
import json
import random
import statistics
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
import uuid
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gpu_sampler import Sampler, percentile, read_vllm_metrics  # noqa: E402
from mock_sandbox_load import enabled_assignments, pick_cases  # noqa: E402
from mock_sandbox_run import MockError, bundle_for, http, load_cases  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
OLD_CLIENT_GIVE_UP_S = 74.5  # the sandbox UI's polling budget before this release
NEW_CLIENT_CAP_S = 600.0  # the new UI keeps polling this long, then offers "Check again"
LEGACY_AI_FAILURE = ("Local AI assistant request timed out", "Local AI assistant is currently unreachable",
                     "An error occurred while generating AI feedback")
GUARDRAIL_TEXT = "couldn't produce hints"


def now() -> float:
    return time.monotonic()


def ui_poll_delay(attempt: int, last: dict | None) -> float:
    """The sandbox UI's polling cadence (features/assignments/api.ts)."""
    delay = (0.15, 0.25, 0.35, 0.5, 0.5, 0.5)[attempt] if attempt < 6 else (0.75 if attempt <= 12 else 1.0)
    if last and last.get("state") == "queue":
        ahead = last.get("submissions_ahead")
        if ahead is None:
            ahead = last.get("queue_position") or 0
        if ahead > 3:
            delay = max(delay, 2.0)
    return delay


def ui_backoff(attempt: int, retry_after: float | None, rng: random.Random) -> float:
    """The sandbox UI's retry backoff (features/assignments/sandbox-retry.ts)."""
    target = retry_after if retry_after and retry_after > 0 else min(30.0, 2.0 * 2 ** max(0, attempt))
    capped = min(max(target, 1.0), 60.0)
    return capped * (0.8 + 0.4 * rng.random())


def detail_of(body) -> dict:
    if isinstance(body, dict):
        detail = body.get("detail")
        if isinstance(detail, dict):
            return detail
        if isinstance(detail, str):
            return {"message": detail}
    return {}


def stats(values: list[float]) -> dict:
    if not values:
        return {"n": 0, "p50": None, "p95": None, "max": None}
    return {"n": len(values), "p50": round(statistics.median(values), 2),
            "p95": round(percentile(values, 95), 2), "max": round(max(values), 2)}


def post_run(api: str, course_id: str, assignment_id: str, bundle: bytes) -> tuple[int, object, dict]:
    boundary = f"----stress{uuid.uuid4().hex}"
    body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"bundle\"; filename=\"submission.zip\"\r\n"
            f"Content-Type: application/zip\r\n\r\n").encode() + bundle + f"\r\n--{boundary}--\r\n".encode()
    return http("POST", f"{api}/sandbox/courses/{course_id}/assignments/{assignment_id}/runs", body=body,
                headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}, timeout=90)


class QueueDepth(threading.Thread):
    """Samples the scheduler's waiting count (from status responses) once a second."""

    def __init__(self) -> None:
        super().__init__(daemon=True)
        self.latest: int | None = None
        self.timeline: list[tuple[float, int]] = []
        self.stop_event = threading.Event()
        self.started_at = now()

    def observe(self, status: dict) -> None:
        waiting = (status.get("backpressure") or {}).get("current_waiting")
        if isinstance(waiting, int):
            self.latest = waiting

    def run(self) -> None:
        while not self.stop_event.is_set():
            if self.latest is not None:
                self.timeline.append((round(now() - self.started_at, 1), self.latest))
            self.stop_event.wait(1.0)

    def stop(self) -> None:
        self.stop_event.set()
        self.join()


def student_grading_run(api: str, case: dict, assignment: tuple[str, str], seed: int,
                        depth: QueueDepth | None, max_seconds: float) -> dict:
    """One student: submit (retrying a full queue like the UI), then poll to the end."""
    rng = random.Random(seed)
    course_id, assignment_id = assignment
    bundle = bundle_for(case)
    t0 = now()
    outcome: dict = {"admission_codes": [], "admission_retries": 0}
    created = None
    for attempt in range(40):
        try:
            status, body, headers = post_run(api, course_id, assignment_id, bundle)
        except MockError:
            outcome["admission_codes"].append("network_error")
            time.sleep(ui_backoff(attempt, None, rng))
            outcome["admission_retries"] += 1
            continue
        if status == 202 and isinstance(body, dict):
            outcome["admission_codes"].append("202")
            created = (body, headers.get("X-Sandbox-Session") or headers.get("x-sandbox-session")
                       or body.get("sandbox_session"))
            break
        detail = detail_of(body)
        code = detail.get("code") or str(status)
        outcome["admission_codes"].append(code)
        if status == 503 and code in ("queue_full", "busy", "503") and now() - t0 < 300:
            outcome["admission_retries"] += 1
            time.sleep(ui_backoff(attempt, detail.get("retry_after_seconds"), rng))
            continue
        outcome.update(final="not_admitted", total_s=round(now() - t0, 2))
        return outcome
    if created is None:
        outcome.update(final="not_admitted", total_s=round(now() - t0, 2))
        return outcome

    run, session = created
    t_admit = now()
    outcome["admission_wait_s"] = round(t_admit - t0, 2)
    first_eta = None
    aheads: list[int] = []
    t_run = None
    last: dict | None = run.get("initial_status")
    poll_errors = 0
    attempt = 0
    while True:
        if now() - t_admit > max_seconds:
            outcome.update(final="still_pending", total_s=round(now() - t0, 2))
            return outcome
        try:
            status, body, _ = http("GET", f"{api}{run['status_url']}", timeout=30)
        except MockError:
            status, body = 0, None
        if status == 200 and isinstance(body, dict):
            poll_errors = 0
            last = body
            if depth is not None:
                depth.observe(body)
            state = body.get("state")
            if state == "queue":
                if body.get("submissions_ahead") is not None:
                    aheads.append(body["submissions_ahead"])
                if first_eta is None and body.get("eta_seconds") is not None:
                    first_eta = body["eta_seconds"]
            elif t_run is None:
                t_run = now()
            if state in ("complete", "failure"):
                t_done = now()
                outcome.update(
                    final=state,
                    failure_category=body.get("failure_category") if state == "failure" else None,
                    grader_fault=bool(body.get("grader_fault")),
                    queue_wait_s=round((t_run or t_done) - t_admit, 2),
                    grading_s=round(t_done - (t_run or t_done), 2),
                    total_s=round(t_done - t0, 2),
                    old_client_gave_up=(t_done - t_admit) > OLD_CLIENT_GIVE_UP_S,
                    first_eta_s=first_eta,
                    ahead_first=aheads[0] if aheads else None,
                    ahead_increases=sum(1 for a, b in zip(aheads, aheads[1:]) if b > a),
                    status_poll_errors=outcome.get("status_poll_errors", 0),
                    run_id=run["run_id"], session=session, result_url=run["result_url"],
                )
                return outcome
        elif status == 404:
            outcome.update(final="lost", total_s=round(now() - t0, 2))
            return outcome
        else:
            poll_errors += 1
            outcome["status_poll_errors"] = outcome.get("status_poll_errors", 0) + 1
            if poll_errors > 8:
                outcome.update(final="poll_failed", total_s=round(now() - t0, 2))
                return outcome
            time.sleep(ui_backoff(poll_errors - 1, None, rng))
            continue
        time.sleep(ui_poll_delay(attempt, last))
        attempt += 1


def summarize_grading(level: int, results: list[dict], wall: float, depth: QueueDepth) -> dict:
    finals = Counter(r.get("final") for r in results)
    codes = Counter(code for r in results for code in r["admission_codes"])
    done = [r for r in results if r.get("final") in ("complete", "failure")]
    categories = Counter(r["failure_category"] for r in done if r.get("failure_category"))
    eta_signed = [r["first_eta_s"] - r["queue_wait_s"] for r in done
                  if r.get("first_eta_s") is not None and r.get("queue_wait_s") is not None]
    eta_errors = [abs(e) for e in eta_signed]
    return {
        "students": level,
        "finals": dict(finals),
        "admission_codes": dict(codes),
        "admission_retries": sum(r["admission_retries"] for r in results),
        "admission_wait_s": stats([r["admission_wait_s"] for r in results if "admission_wait_s" in r]),
        "queue_wait_s": stats([r["queue_wait_s"] for r in done]),
        "grading_s": stats([r["grading_s"] for r in done]),
        "total_s": stats([r["total_s"] for r in done]),
        "runs_per_minute": round(len(done) / wall * 60, 1) if wall else None,
        "failure_categories": dict(categories),
        "grader_faults": sum(1 for r in done if r.get("grader_fault")),
        "old_client_gave_up": sum(1 for r in done if r.get("old_client_gave_up")),
        "status_poll_errors": sum(r.get("status_poll_errors", 0) for r in results),
        "eta_abs_error_s": stats(eta_errors),
        # Positive: the estimate shown was longer than the actual wait (over-promised wait).
        "eta_signed_error_s": stats(eta_signed),
        "ahead_increases": sum(r.get("ahead_increases", 0) for r in done),
        "max_queue_depth": max((w for _, w in depth.timeline), default=None),
        "queue_depth_timeline": depth.timeline[::max(1, len(depth.timeline) // 120)],
        "wall_s": round(wall, 1),
    }


def grading_level(api: str, cases: list[dict], assignments: dict, level: int, seed: int,
                  max_seconds: float) -> tuple[dict, list[dict]]:
    depth = QueueDepth()
    depth.start()
    started = now()
    picks = [cases[i % len(cases)] for i in range(level)]
    with ThreadPoolExecutor(max_workers=level) as pool:
        futures = [pool.submit(student_grading_run, api, case, assignments[case["assignment_slug"]],
                               seed * 1000 + i, depth, max_seconds) for i, case in enumerate(picks)]
        results = [f.result() for f in futures]
    wall = now() - started
    depth.stop()
    return summarize_grading(level, results, wall, depth), results


def print_grading(row: dict) -> None:
    f = row["finals"]
    print(f"  {row['students']:>3} students: done {f.get('complete', 0) + f.get('failure', 0):>3}"
          f" | not admitted {f.get('not_admitted', 0)} | pending {f.get('still_pending', 0)} | lost {f.get('lost', 0)}"
          f" | retries {row['admission_retries']:>3} | queue p50/p95 {row['queue_wait_s']['p50']}/{row['queue_wait_s']['p95']} s"
          f" | total p95 {row['total_s']['p95']} s | {row['runs_per_minute']} runs/min"
          f" | >75 s {row['old_client_gave_up']} | faults {row['grader_faults']} | depth max {row['max_queue_depth']}")


def ai_attempt(api: str, run: dict, timeout: float = 120) -> dict:
    started = now()
    try:
        status, body, headers = http("POST", f"{api}/sandbox/runs/{run['run_id']}/ai-feedback",
                                     headers={"X-Sandbox-Session": run["session"]}, timeout=timeout)
    except MockError:
        return {"kind": "network_error", "seconds": round(now() - started, 2)}
    seconds = round(now() - started, 2)
    if status == 200 and isinstance(body, dict):
        text = body.get("ai_feedback", "")
        if any(marker in text for marker in LEGACY_AI_FAILURE):
            return {"kind": "legacy_failure_text", "seconds": seconds}
        return {"kind": "guardrail_fallback" if GUARDRAIL_TEXT in text else "answer", "seconds": seconds}
    detail = detail_of(body)
    return {"kind": detail.get("code") or f"http_{status}", "seconds": seconds,
            "retry_after": detail.get("retry_after_seconds") or headers.get("Retry-After")}


def student_ai(api: str, run: dict, retries: int, seed: int) -> dict:
    """One student asking for feedback, retrying busy/slow answers like the UI."""
    rng = random.Random(seed)
    started = now()
    attempts = []
    for attempt in range(retries + 1):
        result = ai_attempt(api, run)
        attempts.append(result["kind"])
        if result["kind"] in ("answer", "guardrail_fallback"):
            break
        if result["kind"] not in ("ai_busy", "ai_timeout", "ai_error", "legacy_failure_text", "grading_not_complete",
                                  "http_502", "http_503", "http_504", "network_error"):
            break
        if attempt < retries:
            retry_after = result.get("retry_after")
            time.sleep(ui_backoff(attempt + 1, float(retry_after) if retry_after else None, rng))
    return {"first": attempts[0], "final": attempts[-1], "attempts": len(attempts),
            "first_seconds": None, "total_s": round(now() - started, 2)}


def ai_level(api: str, runs: list[dict], level: int, retries: int, seed: int, metrics_url: str | None) -> dict:
    sampler = Sampler(metrics_url)
    before = read_vllm_metrics(metrics_url)
    sampler.start()
    started = now()
    picks = [runs[i % len(runs)] for i in range(level)]
    with ThreadPoolExecutor(max_workers=level) as pool:
        firsts = list(pool.map(lambda r: ai_attempt(api, r), picks))
    first_wall = now() - started
    with ThreadPoolExecutor(max_workers=level) as pool:
        retried = list(pool.map(lambda pair: student_ai(api, pair[1], retries, seed * 1000 + pair[0]),
                                enumerate(picks)))
    wall = now() - started
    sampler.stop()
    after = read_vllm_metrics(metrics_url)
    answers = [r["seconds"] for r in firsts if r["kind"] in ("answer", "guardrail_fallback")]
    return {
        "students": level,
        "first_attempt": dict(Counter(r["kind"] for r in firsts)),
        "first_attempt_answer_s": stats(answers),
        "first_attempt_wall_s": round(first_wall, 1),
        "with_retries_final": dict(Counter(r["final"] for r in retried)),
        "with_retries_total_s": stats([r["total_s"] for r in retried if r["final"] in ("answer", "guardrail_fallback")]),
        "with_retries_attempts": stats([float(r["attempts"]) for r in retried]),
        **sampler.summary(before, after, wall, len(firsts) + sum(r["attempts"] for r in retried)),
    }


def print_ai(row: dict) -> None:
    print(f"  {row['students']:>3} students: first try {row['first_attempt']} | answer p50/p95 "
          f"{row['first_attempt_answer_s']['p50']}/{row['first_attempt_answer_s']['p95']} s | with retries "
          f"{row['with_retries_final']} (p95 {row['with_retries_total_s']['p95']} s) | GPU avg "
          f"{row.get('gpu_util_avg')}% | vLLM wait max {row.get('vllm_max_waiting')}")


def graded_pool(api: str, cases: list[dict], assignments: dict, size: int, seed: int) -> list[dict]:
    """Grade `size` synthetic submissions a few at a time; keep the ones AI can use."""
    pool_runs: list[dict] = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(student_grading_run, api, cases[i % len(cases)],
                               assignments[cases[i % len(cases)]["assignment_slug"]], seed + i, None, 600)
                   for i in range(size)]
        for future in futures:
            result = future.result()
            if result.get("final") == "complete" or (result.get("final") == "failure" and not result.get("grader_fault")):
                pool_runs.append(result)
    return pool_runs


def burst(api: str, cases: list[dict], assignments: dict, students: int, retries: int, seed: int,
          metrics_url: str | None, think: tuple[float, float]) -> dict:
    sampler = Sampler(metrics_url)
    before = read_vllm_metrics(metrics_url)
    sampler.start()
    depth = QueueDepth()
    depth.start()
    started = now()

    def one(i: int) -> dict:
        rng = random.Random(seed * 1000 + i)
        case = cases[i % len(cases)]
        graded = student_grading_run(api, case, assignments[case["assignment_slug"]], seed * 1000 + i, depth, 600)
        record = {"grading_final": graded.get("final"), "grading_total_s": graded.get("total_s"),
                  "grader_fault": graded.get("grader_fault", False)}
        if graded.get("final") not in ("complete", "failure") or graded.get("grader_fault"):
            return record
        time.sleep(rng.uniform(*think))
        ai = student_ai(api, graded, retries, seed * 1000 + i)
        record.update(ai_final=ai["final"], ai_attempts=ai["attempts"], ai_total_s=ai["total_s"])
        return record

    with ThreadPoolExecutor(max_workers=students) as pool:
        records = list(pool.map(one, range(students)))
    wall = now() - started
    depth.stop()
    sampler.stop()
    after = read_vllm_metrics(metrics_url)
    got_feedback = [r for r in records if r.get("ai_final") in ("answer", "guardrail_fallback")]
    return {
        "students": students,
        "think_seconds": list(think),
        "grading_finals": dict(Counter(r["grading_final"] for r in records)),
        "grading_total_s": stats([r["grading_total_s"] for r in records if r.get("grading_total_s") is not None]),
        "grader_faults": sum(1 for r in records if r.get("grader_fault")),
        "ai_finals": dict(Counter(r.get("ai_final") for r in records if "ai_final" in r)),
        "ai_total_s": stats([r["ai_total_s"] for r in got_feedback]),
        "ai_attempts": stats([float(r["ai_attempts"]) for r in records if "ai_attempts" in r]),
        "students_with_feedback": len(got_feedback),
        "max_queue_depth": max((w for _, w in depth.timeline), default=None),
        "wall_s": round(wall, 1),
        **sampler.summary(before, after, wall, len(records)),
    }


PYTEST_PROGRAM = (
    "import pytest, sys\n"
    "def _t():\n    assert sum(range(10)) == 45\n"
    "print('ok', pytest.__version__, sys.version_info[:2])\n"
)


def judge0_request(method: str, url: str, token: str, body: dict | None = None) -> tuple[int, object]:
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(url, data=data, method=method, headers={
        "Content-Type": "application/json", "X-Auth-Token": token, "X-Auth-User": token})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            raw = response.read().decode() or "{}"
            return response.status, json.loads(raw)
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode()[:200]
    except (urllib.error.URLError, TimeoutError) as exc:
        return 0, str(exc)


def judge0_one(base: str, token: str, language: int) -> dict:
    started = now()
    status, body = judge0_request("POST", f"{base}/submissions?base64_encoded=false", token,
                                  {"source_code": PYTEST_PROGRAM, "language_id": language,
                                   "cpu_time_limit": 10, "wall_time_limit": 20})
    if status not in (200, 201) or not isinstance(body, dict) or "token" not in body:
        return {"outcome": f"submit_{status}", "seconds": round(now() - started, 2)}
    sub = body["token"]
    result_status = None
    while now() - started < 120:
        status, body = judge0_request("GET", f"{base}/submissions/{sub}?base64_encoded=false&fields=status", token)
        if status == 200 and isinstance(body, dict):
            sid = (body.get("status") or {}).get("id")
            if sid not in (1, 2):  # In Queue, Processing
                result_status = (body.get("status") or {}).get("description")
                break
        time.sleep(0.5)
    seconds = round(now() - started, 2)
    deleted, del_status = False, None
    for _ in range(5):
        del_status, _ = judge0_request("DELETE", f"{base}/submissions/{sub}", token)
        if del_status in (200, 204):
            deleted = True
            break
        time.sleep(1)
    # Judge0 serves a cached GET for about a second after DELETE; re-read like
    # validate_grading_package_host.py before counting the submission as retained.
    gone = False
    for _ in range(5):
        gone_status, _ = judge0_request("GET", f"{base}/submissions/{sub}?fields=status", token)
        if gone_status == 404:
            gone = True
            break
        time.sleep(0.5)
    return {"outcome": result_status or "timeout", "seconds": seconds, "deleted": deleted,
            "delete_status": del_status, "gone_after_delete": gone}


def judge0_level(base: str, token: str, language: int, level: int, rounds: int) -> dict:
    started = now()
    with ThreadPoolExecutor(max_workers=level) as pool:
        results = list(pool.map(lambda _: judge0_one(base, token, language), range(level * rounds)))
    wall = now() - started
    accepted = [r["seconds"] for r in results if r["outcome"] == "Accepted"]
    return {
        "concurrent": level,
        "submissions": len(results),
        "outcomes": dict(Counter(r["outcome"] for r in results)),
        "latency_s": stats(accepted),
        "per_minute": round(len(accepted) / wall * 60, 1) if wall else None,
        "deleted": sum(1 for r in results if r.get("deleted")),
        "not_retrievable_after_delete": sum(1 for r in results if r.get("gone_after_delete")),
        "wall_s": round(wall, 1),
    }


def git_commit() -> str | None:
    try:
        return subprocess.run(["git", "-C", str(REPO), "rev-parse", "--short", "HEAD"], capture_output=True,
                              text=True, timeout=5).stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("scenario", choices=["grading", "ai", "burst", "judge0", "all"])
    parser.add_argument("--api", default="http://127.0.0.1:8000", help="backend base URL")
    parser.add_argument("--levels", default="", help="comma-separated concurrency levels for the scenario")
    parser.add_argument("--students", type=int, default=40, help="students in the burst scenario")
    parser.add_argument("--think", default="10,60", help="burst think time range in seconds, e.g. 10,60")
    parser.add_argument("--ai-pool", type=int, default=24, help="graded runs to ask for AI feedback about")
    parser.add_argument("--ai-retries", type=int, default=3, help="UI-style retries per AI request")
    parser.add_argument("--max-poll-seconds", type=float, default=NEW_CLIENT_CAP_S)
    parser.add_argument("--metrics", default="http://127.0.0.1:8001/metrics", help="vLLM metrics URL; 'none' to skip")
    parser.add_argument("--judge0-url", default="http://127.0.0.1:2358")
    parser.add_argument("--judge0-token", default="", help="Judge0 auth token (JUDGE0_AUTH_TOKEN)")
    parser.add_argument("--judge0-language", type=int, default=71)
    parser.add_argument("--judge0-rounds", type=int, default=3, help="submissions per concurrent slot")
    parser.add_argument("--seed", type=int, default=1410)
    parser.add_argument("--label", default="", help="a name for this run in the report, e.g. baseline")
    parser.add_argument("--json-out", type=Path, help="write aggregate results here")
    args = parser.parse_args(argv)

    api = args.api.rstrip("/")
    metrics_url = None if args.metrics.lower() == "none" else args.metrics
    if metrics_url and not read_vllm_metrics(metrics_url):
        metrics_url = None
    custom_levels = [int(x) for x in args.levels.split(",") if x.strip()]
    report: dict = {
        "tool": "stress_suite", "version": 1, "label": args.label,
        "started_at": datetime.now(UTC).isoformat(timespec="seconds"), "git_commit": git_commit(),
        "api": api, "seed": args.seed, "scenarios": {},
    }
    run_all = args.scenario == "all"

    if args.scenario in ("grading", "ai", "burst") or run_all:
        try:
            assignments = enabled_assignments(api)
        except MockError as exc:
            sys.exit(str(exc))
        usable = {k: c for k, c in load_cases().items() if c["assignment_slug"] in assignments}
        if not usable:
            sys.exit("none of the eval cases' assignments are sandbox-enabled on this server")
        cases = pick_cases(usable, len(usable))

    if args.scenario == "judge0" or (run_all and args.judge0_token):
        if not args.judge0_token:
            sys.exit("--judge0-token is required for the judge0 scenario")
        levels = custom_levels or [1, 2, 4, 8]
        print(f"judge0: raw submissions at {levels} concurrent, {args.judge0_rounds} per slot")
        rows = []
        for level in levels:
            row = judge0_level(args.judge0_url.rstrip("/"), args.judge0_token, args.judge0_language, level,
                               args.judge0_rounds)
            rows.append(row)
            print(f"  {level:>3} concurrent: {row['outcomes']} | p50/p95 {row['latency_s']['p50']}/"
                  f"{row['latency_s']['p95']} s | {row['per_minute']}/min | deleted {row['deleted']}/"
                  f"{row['submissions']} | gone after delete {row['not_retrievable_after_delete']}")
        report["scenarios"]["judge0"] = rows

    if args.scenario == "grading" or run_all:
        levels = (custom_levels if not run_all else []) or [1, 4, 8, 16, 32, 48]
        print(f"grading: {len(cases)} synthetic cases, levels {levels}")
        rows = []
        for i, level in enumerate(levels):
            row, _ = grading_level(api, cases, assignments, level, args.seed + i, args.max_poll_seconds)
            rows.append(row)
            print_grading(row)
        report["scenarios"]["grading"] = rows

    if args.scenario == "ai" or run_all:
        levels = (custom_levels if not run_all else []) or [1, 8, 16, 32, 48]
        print(f"ai: grading a pool of {args.ai_pool} runs first")
        runs = graded_pool(api, cases, assignments, args.ai_pool, args.seed)
        if not runs:
            sys.exit("no graded runs to ask for feedback about")
        rows = []
        for i, level in enumerate(levels):
            row = ai_level(api, runs, level, args.ai_retries, args.seed + i, metrics_url)
            rows.append(row)
            print_ai(row)
        report["scenarios"]["ai"] = rows

    if args.scenario == "burst" or run_all:
        low, high = (float(x) for x in args.think.split(","))
        print(f"burst: {args.students} students submit, think {low:.0f}-{high:.0f} s, then ask for feedback")
        row = burst(api, cases, assignments, args.students, args.ai_retries, args.seed, metrics_url, (low, high))
        print(f"  graded {row['grading_finals']} (p95 {row['grading_total_s']['p95']} s) | feedback {row['ai_finals']}"
              f" (p95 {row['ai_total_s']['p95']} s) | queue depth max {row['max_queue_depth']}")
        report["scenarios"]["burst"] = row

    report["finished_at"] = datetime.now(UTC).isoformat(timespec="seconds")
    if args.json_out:
        args.json_out.expanduser().write_text(json.dumps(report, indent=2))
        print(f"wrote {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
