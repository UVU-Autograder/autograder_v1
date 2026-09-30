#!/usr/bin/env python3
"""Load-test sandbox AI feedback with many simulated students at once, synthetic code only.

    python3 scripts/mock_sandbox_load.py                         # levels 1,2,4,8,16
    python3 scripts/mock_sandbox_load.py --levels 1,8,32 --requests 48
    python3 scripts/mock_sandbox_load.py --json-out ~/load-$(date +%H%M).json

Run it on the Dell. Two phases:

1. Grade: submit --runs eval cases (mutated model solutions, from
   backend/eval/cases.jsonl) through the real sandbox, a few at a time, so there
   are finished runs to ask about. This part exercises Judge0, not the GPU.
2. Feedback: for each concurrency level, have that many "students" click
   "AI feedback" at the same moment, repeatedly, until --requests have been
   answered. Only the model is loaded here, so the numbers are the GPU's.

Per level it reports latency (p50 / p95 / max), throughput, how many answers
were fallback messages and why (timeout: the backend waits 30 s for the model;
guardrail: the answer failed the safety checks; unreachable / error), and, when
it can see them, vLLM's queue (running / waiting requests, generated tokens/s)
and the GPU's utilisation and power from nvidia-smi.

This hits the live stack: every request is a real grading run or a real model
call, and students using the sandbox at the same time will see the slowdown.
Run it when nobody is. It creates no accounts and stores nothing permanent;
sandbox runs expire on their own.
"""

from __future__ import annotations

import argparse
import json
import shutil
import statistics
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mock_sandbox_run import (  # noqa: E402
    MockError, bundle_for, http, is_fallback, load_cases, request_feedback, submit, wait_for_result,
)

TIMEOUT_TEXT = "timed out"
UNREACHABLE_TEXT = "unreachable"
GUARDRAIL_TEXT = "couldn't produce hints"


def fallback_kind(text: str) -> str | None:
    if not is_fallback(text):
        return None
    for kind, marker in (("timeout", TIMEOUT_TEXT), ("unreachable", UNREACHABLE_TEXT), ("guardrail", GUARDRAIL_TEXT)):
        if marker in text:
            return kind
    return "error"


def pick_cases(cases: dict[str, dict], count: int) -> list[dict]:
    """Round-robin across assignments so the prompts vary in size the way a class's would."""
    by_slug: dict[str, list[dict]] = {}
    for case in sorted(cases.values(), key=lambda c: c["case_id"]):
        by_slug.setdefault(case["assignment_slug"], []).append(case)
    picked: list[dict] = []
    while len(picked) < count and any(by_slug.values()):
        for slug in sorted(by_slug):
            if by_slug[slug] and len(picked) < count:
                picked.append(by_slug[slug].pop(0))
    return picked


def percentile(values: list[float], pct: float) -> float:
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, max(0, round(pct / 100 * (len(ordered) - 1))))]


class Sampler(threading.Thread):
    """Polls vLLM's /metrics and nvidia-smi twice a second while a level runs."""

    def __init__(self, metrics_url: str | None):
        super().__init__(daemon=True)
        self.metrics_url = metrics_url
        self.nvidia_smi = shutil.which("nvidia-smi")
        self.stop_event = threading.Event()
        self.running: list[float] = []
        self.waiting: list[float] = []
        self.kv_cache: list[float] = []
        self.gpu_util: list[float] = []
        self.gpu_power: list[float] = []

    def metrics(self) -> dict[str, float]:
        if not self.metrics_url:
            return {}
        try:
            status, text, _ = http("GET", self.metrics_url, timeout=3)
        except MockError:
            return {}
        if status != 200 or not isinstance(text, str):
            return {}
        totals: dict[str, float] = {}
        for line in text.splitlines():
            if line.startswith("vllm:"):
                name, _, value = line.rpartition(" ")
                try:
                    totals[name.split("{")[0]] = totals.get(name.split("{")[0], 0.0) + float(value)
                except ValueError:
                    pass
        return totals

    def run(self) -> None:
        while not self.stop_event.is_set():
            sample = self.metrics()
            if sample:
                self.running.append(sample.get("vllm:num_requests_running", 0))
                self.waiting.append(sample.get("vllm:num_requests_waiting", 0))
                kv = sample.get("vllm:kv_cache_usage_perc", sample.get("vllm:gpu_cache_usage_perc"))
                if kv is not None:
                    self.kv_cache.append(kv)
            if self.nvidia_smi:
                try:
                    out = subprocess.run(
                        [self.nvidia_smi, "--query-gpu=utilization.gpu,power.draw", "--format=csv,noheader,nounits"],
                        capture_output=True, text=True, timeout=3,
                    ).stdout.splitlines()[0]
                    util, power = (float(x) for x in out.split(","))
                    self.gpu_util.append(util)
                    self.gpu_power.append(power)
                except (OSError, ValueError, IndexError, subprocess.SubprocessError):
                    pass
            self.stop_event.wait(0.5)


def enabled_assignments(api: str) -> dict[str, tuple[str, str]]:
    """Sandbox-enabled assignments on this server, keyed by slug (with - and _ both accepted)."""
    status, courses, _ = http("GET", f"{api}/sandbox/courses")
    if status != 200 or not isinstance(courses, dict):
        raise MockError(f"cannot list sandbox courses at {api} (HTTP {status}: {str(courses)[:200]})")
    found: dict[str, tuple[str, str]] = {}
    for course in courses.get("courses", []):
        _, listing, _ = http("GET", f"{api}/sandbox/courses/{course['id']}/assignments")
        for assignment in (listing or {}).get("assignments", []) if isinstance(listing, dict) else []:
            for key in {assignment["id"], assignment["id"].replace("-", "_"), assignment["id"].replace("_", "-")}:
                found[key] = (course["id"], assignment["id"])
    return found


def grade_phase(api: str, cases: list[dict], assignments: dict[str, tuple[str, str]], workers: int,
                timeout: float) -> list[dict]:
    def grade(case: dict) -> dict | None:
        course_id, assignment_id = assignments[case["assignment_slug"]]
        started = time.time()
        for attempt in range(5):
            try:
                run_id, session, result_url = submit(api, course_id, assignment_id, bundle_for(case))
                break
            except MockError as exc:
                if "HTTP 503" not in str(exc) or attempt == 4:  # 503 = sandbox queue full; back off and retry
                    print(f"  {case['case_id']}: {exc}")
                    return None
                time.sleep(2 * (attempt + 1))
        try:
            result = wait_for_result(api, result_url, session, timeout)
        except MockError as exc:
            print(f"  {case['case_id']}: {exc}")
            return None
        took = time.time() - started
        print(f"  graded {case['case_id']:42} {result['projected_score']:>3}/{result['max_score']:<3} in {took:4.1f}s")
        return {"case_id": case["case_id"], "run_id": run_id, "session": session, "grade_seconds": took}

    with ThreadPoolExecutor(workers) as pool:
        return [run for run in pool.map(grade, cases) if run]


def feedback_level(api: str, runs: list[dict], concurrency: int, total: int, metrics_url: str | None) -> dict:
    sampler = Sampler(metrics_url)
    before = sampler.metrics()
    sampler.start()
    outcomes: list[dict] = []
    lock = threading.Lock()
    counter = iter(range(total))

    def student() -> None:
        while True:
            with lock:
                index = next(counter, None)
            if index is None:
                return
            run = runs[index % len(runs)]
            started = time.time()
            try:
                answer = request_feedback(api, run["run_id"], run["session"], timeout=120)
                outcome = {"seconds": time.time() - started, "kind": fallback_kind(answer["ai_feedback"])}
            except MockError as exc:
                outcome = {"seconds": time.time() - started, "kind": "http_error", "detail": str(exc)[:200]}
            with lock:
                outcomes.append(outcome)

    started = time.time()
    threads = [threading.Thread(target=student) for _ in range(concurrency)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    wall = time.time() - started
    sampler.stop_event.set()
    sampler.join()
    after = sampler.metrics()

    seconds = [o["seconds"] for o in outcomes]
    kinds: dict[str, int] = {}
    for outcome in outcomes:
        if outcome["kind"]:
            kinds[outcome["kind"]] = kinds.get(outcome["kind"], 0) + 1
    generated = after.get("vllm:generation_tokens_total", 0) - before.get("vllm:generation_tokens_total", 0)
    prompted = after.get("vllm:prompt_tokens_total", 0) - before.get("vllm:prompt_tokens_total", 0)
    return {
        "concurrency": concurrency,
        "requests": len(outcomes),
        "ok": len(outcomes) - sum(kinds.values()),
        "fallbacks": kinds,
        "wall_seconds": round(wall, 2),
        "requests_per_second": round(len(outcomes) / wall, 2) if wall else None,
        "latency_p50": round(statistics.median(seconds), 2) if seconds else None,
        "latency_p95": round(percentile(seconds, 95), 2) if seconds else None,
        "latency_max": round(max(seconds), 2) if seconds else None,
        "generated_tokens_per_second": round(generated / wall, 1) if after and wall else None,
        "prompt_tokens_per_request": round(prompted / len(outcomes)) if after and outcomes else None,
        "vllm_max_running": max(sampler.running, default=None),
        "vllm_max_waiting": max(sampler.waiting, default=None),
        "kv_cache_max_pct": round(100 * max(sampler.kv_cache), 1) if sampler.kv_cache else None,
        "gpu_util_avg": round(statistics.mean(sampler.gpu_util), 1) if sampler.gpu_util else None,
        "gpu_util_max": max(sampler.gpu_util, default=None),
        "gpu_power_max_w": max(sampler.gpu_power, default=None),
        "errors": [o["detail"] for o in outcomes if o["kind"] == "http_error"][:5],
    }


def show(value, fmt: str = "{}") -> str:
    return "-" if value is None else fmt.format(value)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--api", default="http://127.0.0.1:8000", help="backend base URL")
    parser.add_argument("--metrics", default="http://127.0.0.1:8001/metrics",
                        help="vLLM metrics URL (Dell loopback); 'none' to skip")
    parser.add_argument("--runs", type=int, default=16, help="distinct graded runs to ask about (default 16)")
    parser.add_argument("--grade-workers", type=int, default=4, help="grading uploads in flight at once (default 4)")
    parser.add_argument("--levels", default="1,2,4,8,16", help="concurrent students per level (default 1,2,4,8,16)")
    parser.add_argument("--requests", type=int, default=0,
                        help="feedback requests per level (default: 3x the level, at least 8)")
    parser.add_argument("--timeout", type=float, default=300, help="seconds to wait for each grading run")
    parser.add_argument("--json-out", type=Path, help="also write the results here")
    args = parser.parse_args(argv)

    levels = [int(x) for x in args.levels.split(",") if x.strip()]
    if not levels or min(levels) < 1 or max(levels) > 64:
        sys.exit("--levels must be between 1 and 64")
    api = args.api.rstrip("/")
    metrics_url = None if args.metrics.lower() == "none" else args.metrics
    if metrics_url and not Sampler(metrics_url).metrics():
        print(f"(vLLM metrics not readable at {metrics_url}; queue and token columns will be blank)")
        metrics_url = None
    if not shutil.which("nvidia-smi"):
        print("(nvidia-smi not found; GPU columns will be blank. Run this on the Dell.)")

    try:
        assignments = enabled_assignments(api)
        usable = {k: c for k, c in load_cases().items() if c["assignment_slug"] in assignments}
        if not usable:
            sys.exit(f"none of the eval cases' assignments are sandbox-enabled here ({', '.join(sorted(assignments)) or 'none'})")
        cases = pick_cases(usable, args.runs)
        slugs = sorted({c["assignment_slug"] for c in cases})
        print(f"Phase 1: grading {len(cases)} synthetic submissions across {len(slugs)} assignments, "
              f"{args.grade_workers} at a time")
        runs = grade_phase(api, cases, assignments, args.grade_workers, args.timeout)
    except MockError as exc:
        sys.exit(str(exc))
    if not runs:
        sys.exit("no run finished grading; nothing to ask for feedback on")
    grade_times = [r["grade_seconds"] for r in runs]
    print(f"  {len(runs)} graded; median {statistics.median(grade_times):.1f}s, max {max(grade_times):.1f}s\n")

    print("Phase 2: AI feedback under load")
    header = (f"{'students':>8} {'reqs':>5} {'ok':>4} {'fallback':>18} {'p50 s':>6} {'p95 s':>6} {'max s':>6} "
              f"{'req/s':>6} {'gen tok/s':>9} {'run/wait':>9} {'KV %':>5} {'GPU avg/max %':>13} {'W max':>6}")
    print(header)
    results = []
    for level in levels:
        total = args.requests or max(8, 3 * level)
        r = feedback_level(api, runs, level, total, metrics_url)
        results.append(r)
        fallbacks = ",".join(f"{k}:{v}" for k, v in sorted(r["fallbacks"].items())) or "0"
        run_wait = (f"{show(r['vllm_max_running'], '{:.0f}')}/{show(r['vllm_max_waiting'], '{:.0f}')}"
                    if r["vllm_max_running"] is not None else "-")
        gpu = (f"{show(r['gpu_util_avg'])}/{show(r['gpu_util_max'], '{:.0f}')}" if r["gpu_util_avg"] is not None else "-")
        print(f"{level:>8} {r['requests']:>5} {r['ok']:>4} {fallbacks:>18} {show(r['latency_p50']):>6} "
              f"{show(r['latency_p95']):>6} {show(r['latency_max']):>6} {show(r['requests_per_second']):>6} "
              f"{show(r['generated_tokens_per_second']):>9} {run_wait:>9} {show(r['kv_cache_max_pct']):>5} "
              f"{gpu:>13} {show(r['gpu_power_max_w'], '{:.0f}'):>6}")
        for error in r["errors"]:
            print(f"         error: {error}")

    print("\nReading it: p95 near 30 s or any 'timeout' fallbacks means students at that level would get")
    print("'request timed out' instead of hints. 'wait' above 0 means vLLM was queueing requests.")
    if args.json_out:
        args.json_out.expanduser().write_text(json.dumps(
            {"api": api, "graded_runs": len(runs), "grade_seconds": grade_times, "levels": results}, indent=2))
        print(f"wrote {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
