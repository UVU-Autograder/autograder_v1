"""Find the model server's capacity: real feedback prompts at rising concurrency, straight to vLLM.

    cd backend && ~/venvs/train/bin/python -m eval.stress_vllm --model cs1410-p3
    cd backend && ~/venvs/train/bin/python -m eval.stress_vllm --model cs1410-p3 --levels 32,64,96 --duration 120
    cd backend && ~/venvs/train/bin/python -m eval.stress_vllm --model cs1410-p3 --levels 48 --duration 600   # soak

Every request is exactly what the sandbox sends: the eval cases rendered with
``prompts.build_messages``, guided JSON with the response schema, the serving
temperature and ``MAX_OUTPUT_TOKENS``. Bypassing the backend measures the GPU
alone; ``scripts/mock_sandbox_load.py`` measures the same thing end to end, and
the gap between them is the backend's cost.

Each level keeps N requests in flight for --duration seconds. Per level it
reports latency (p50 / p95 / max), how many took longer than the backend's 30 s
limit (those students would get "request timed out"), requests/s, errors,
vLLM's queue (running / waiting, preemptions, KV cache %) and the GPU
(utilisation, power, temperature, lowest SM clock, throttle reasons). It stops
early once p95 is past twice the limit, since higher levels only queue more.

Synthetic code only. It loads the live model server: run it in an agreed
window, never during training.
"""

from __future__ import annotations

import argparse
import itertools
import json
import statistics
import sys
import threading
import time
from pathlib import Path

from app.integrations.ai.prompts import RESPONSE_JSON_SCHEMA, build_messages, parse_response

from eval.client import ChatClient
from eval.schemas import load_cases

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from gpu_sampler import QUEUE_GPU_HEADER, Sampler, percentile, queue_gpu_cells, read_vllm_metrics  # noqa: E402

CASES_FILE = Path(__file__).parent / "cases.jsonl"
BACKEND_TIMEOUT_S = 30.0  # app.integrations.llm.client.LocalLLMClient default


def sandbox_prompts() -> list[list[dict[str, str]]]:
    return [
        build_messages(
            assignment_title=case.assignment_title,
            requirements=case.requirements,
            allowed_concepts=case.allowed_concepts,
            failures=case.failures,
            concept_violations=case.concept_violations,
            student_code=case.student_code,
            code_files=case.code_files or None,
            passing_labels=case.passing_labels or None,
        )
        for case in load_cases(CASES_FILE)
    ]


def run_level(args, prompts: list, concurrency: int, metrics_url: str | None) -> dict:
    sampler = Sampler(metrics_url)
    before = read_vllm_metrics(metrics_url)
    outcomes: list[dict] = []
    lock = threading.Lock()
    order = itertools.cycle(range(len(prompts)))
    stop_at = time.time() + args.duration

    def worker() -> None:
        client = ChatClient(args.endpoint, args.model, timeout=args.timeout,
                            json_schema=None if args.no_guided else RESPONSE_JSON_SCHEMA)
        try:
            while time.time() < stop_at:
                with lock:
                    index = next(order)
                started = time.perf_counter()
                try:
                    completion = client.complete(prompts[index])
                    try:
                        parse_response(completion.text)
                        valid = True
                    except ValueError:
                        valid = False
                    outcome = {"seconds": completion.latency_s, "ok": True, "valid": valid,
                               "completion_tokens": completion.completion_tokens}
                except Exception as exc:  # noqa: BLE001 - an error under load is a data point
                    outcome = {"seconds": time.perf_counter() - started, "ok": False, "error": f"{type(exc).__name__}: {exc}"[:200]}
                with lock:
                    outcomes.append(outcome)
                if not outcome["ok"]:
                    time.sleep(1)  # don't hammer a server that is refusing or failing
        finally:
            client.close()

    sampler.start()
    started = time.time()
    threads = [threading.Thread(target=worker) for _ in range(concurrency)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    wall = time.time() - started
    sampler.stop()
    after = read_vllm_metrics(metrics_url)

    done = [o for o in outcomes if o["ok"]]
    seconds = [o["seconds"] for o in done]
    return {
        "concurrency": concurrency,
        "requests": len(outcomes),
        "ok": len(done),
        "errors": len(outcomes) - len(done),
        "schema_invalid": sum(not o["valid"] for o in done),
        "over_backend_limit": sum(s > BACKEND_TIMEOUT_S for s in seconds),
        "wall_seconds": round(wall, 1),
        "requests_per_second": round(len(done) / wall, 2) if wall else None,
        "latency_p50": round(statistics.median(seconds), 2) if seconds else None,
        "latency_p95": round(percentile(seconds, 95), 2) if seconds else None,
        "latency_max": round(max(seconds), 2) if seconds else None,
        "mean_completion_tokens": round(statistics.mean(o["completion_tokens"] for o in done)) if done else None,
        **sampler.summary(before, after, wall, len(outcomes)),
        "error_samples": [o["error"] for o in outcomes if not o["ok"]][:3],
    }


def show(value, fmt: str = "{}") -> str:
    return "-" if value is None else fmt.format(value)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--endpoint", default="vllm", help="vllm (127.0.0.1:8001/v1) or a full URL")
    parser.add_argument("--model", required=True, help="served model name, e.g. cs1410-p3 or gemma4-12b-qat")
    parser.add_argument("--levels", default="1,4,8,16,32,64,96,128", help="requests in flight per level")
    parser.add_argument("--duration", type=float, default=60, help="seconds per level (default 60)")
    parser.add_argument("--timeout", type=float, default=180, help="client timeout per request (default 180)")
    parser.add_argument("--metrics", default="http://127.0.0.1:8001/metrics", help="vLLM metrics URL; 'none' to skip")
    parser.add_argument("--no-guided", action="store_true", help="skip JSON-schema decoding (the sandbox uses it)")
    parser.add_argument("--keep-going", action="store_true", help="run every level even past saturation")
    parser.add_argument("--json-out", type=Path, help="also write the results here")
    args = parser.parse_args(argv)

    levels = [int(x) for x in args.levels.split(",") if x.strip()]
    if not levels or min(levels) < 1 or max(levels) > 256:
        sys.exit("--levels must be between 1 and 256")
    metrics_url = None if args.metrics.lower() == "none" else args.metrics
    if metrics_url and not read_vllm_metrics(metrics_url):
        print(f"(vLLM metrics not readable at {metrics_url}; queue columns will be blank)")
        metrics_url = None
    prompts = sandbox_prompts()
    print(f"{len(prompts)} sandbox prompts -> {args.model} at {args.endpoint}, {args.duration:.0f} s per level\n")
    print(f"{'in flight':>9} {'reqs':>5} {'err':>4} {'>30s':>5} {'p50 s':>6} {'p95 s':>6} {'max s':>6} {'req/s':>6} "
          f"{QUEUE_GPU_HEADER}")
    results = []
    for level in levels:
        r = run_level(args, prompts, level, metrics_url)
        results.append(r)
        print(f"{level:>9} {r['requests']:>5} {r['errors']:>4} {r['over_backend_limit']:>5} {show(r['latency_p50']):>6} "
              f"{show(r['latency_p95']):>6} {show(r['latency_max']):>6} {show(r['requests_per_second']):>6} "
              f"{queue_gpu_cells(r)}")
        for error in r["error_samples"]:
            print(f"          error: {error}")
        if r["ok"] == 0:
            print("\nstopping: no request succeeded at this level; is the model server up and is --model right?")
            break
        if not args.keep_going and r["latency_p95"] is not None and r["latency_p95"] > 2 * BACKEND_TIMEOUT_S:
            print(f"\nstopping: p95 is over {2 * BACKEND_TIMEOUT_S:.0f} s, so higher levels would only queue more "
                  "(--keep-going to run them anyway)")
            break

    print("\nReading it: the capacity is the highest level with '>30s' at 0 and no errors. Past it, req/s stops")
    print("rising while p95 climbs. 'wait' > 0 means requests queued in vLLM; 'preempt' > 0 means the KV cache")
    print("ran out; a throttle reason other than '-' means the GPU slowed itself (power cap or heat).")
    if args.json_out:
        args.json_out.expanduser().write_text(json.dumps(
            {"model": args.model, "endpoint": args.endpoint, "duration_s": args.duration,
             "guided": not args.no_guided, "prompts": len(prompts), "levels": results}, indent=2))
        print(f"wrote {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
