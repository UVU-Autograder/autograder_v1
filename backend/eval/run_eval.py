"""Phase 0 eval runner.

    python -m eval.run_eval --endpoint lmstudio --model gemma-4-12b-it-qat --label baseline-12b

Appends one row per run to ``eval/results/scoreboard_v8.csv`` and writes the full
per-case transcript to ``eval/results/<label>.json`` so a regression can be read
back rather than re-run.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from app.integrations.ai.prompts import (
    GENERATION_TEMPERATURE,
    PROMPT_VERSIONS,
    RESPONSE_JSON_SCHEMA,
    prompt_version_for,
)

from eval.client import ChatClient
from eval.metrics import aggregate, score_case
from eval.schemas import load_cases

EVAL_DIR = Path(__file__).parent
CASES_FILE = EVAL_DIR / "cases.jsonl"
CASES_DIR = CASES_FILE
RESULTS_DIR = EVAL_DIR / "results"
# The answer metrics (prompt v8) added columns; a CSV's header is written once, so
# they start a new file and the old scoreboard.csv keeps its rows intact.
SCOREBOARD = RESULTS_DIR / "scoreboard_v8.csv"


def append_row(path: Path, row: dict) -> None:
    """Add a scoreboard row; when the columns changed, rewrite the file under the combined header."""
    rows: list[dict] = []
    fields = list(row)
    if path.exists():
        with path.open(newline="") as handle:
            reader = csv.DictReader(handle)
            rows = list(reader)
            fields = list(reader.fieldnames or []) + [k for k in row if k not in (reader.fieldnames or [])]
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, restval="")
        writer.writeheader()
        writer.writerows(rows + [row])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Score a model against the CS1410 eval set.")
    parser.add_argument("--endpoint", default="lmstudio", help="lmstudio | ollama | vllm | full URL")
    parser.add_argument("--model", required=True, help="Model id as the server reports it")
    parser.add_argument("--label", required=True, help="Scoreboard row name, e.g. baseline-12b-q4")
    parser.add_argument("--temperature", type=float, default=GENERATION_TEMPERATURE)
    parser.add_argument("--cases", type=Path, default=CASES_DIR)
    parser.add_argument("--filter", default="", help="Only run cases whose id contains this")
    parser.add_argument(
        "--prompt-version",
        choices=PROMPT_VERSIONS,
        help="Prompt to send. Default: the one the backend would use for --model (LOCAL_LLM_PROMPT_VERSIONS).",
    )
    parser.add_argument(
        "--guided",
        action="store_true",
        help="Request server-side JSON-schema enforcement. Leave OFF for a true "
        "baseline -- it masks the schema-compliance the fine-tune is meant to fix.",
    )
    args = parser.parse_args(argv)

    prompt_version = args.prompt_version or prompt_version_for(args.model)
    cases = [c for c in load_cases(args.cases) if args.filter in c.case_id]
    if not cases:
        print(f"No cases matched in {args.cases}", file=sys.stderr)
        return 1

    client = ChatClient(
        args.endpoint,
        args.model,
        temperature=args.temperature,
        json_schema=RESPONSE_JSON_SCHEMA if args.guided else None,
    )

    scores = []
    try:
        for i, case in enumerate(cases, 1):
            messages = case.messages(prompt_version)
            try:
                completion = client.complete(messages)
                score = score_case(case, completion.text, completion.latency_s)
            except Exception as exc:  # noqa: BLE001 - a dead endpoint is a failed row, not a crash
                score = score_case(case, f"<request failed: {exc}>", 0.0)
            scores.append(score)
            mark = "ok  " if score.passed else "FAIL"
            detail = "" if score.passed else f"  <- {'; '.join(score.failure_reasons)}"
            if score.answer_reasons:
                detail += f"  [answer: {'; '.join(score.answer_reasons)}]"
            if score.attack:
                detail += f"  [attack: {'OBEYED' if score.obeyed else 'resisted'}"
                detail += f", {'shown' if score.gate_ok else 'hidden by the gate'}]"
            elif not score.gate_ok:
                detail += f"  [gate would hide: {'; '.join(score.gate_reasons)}]"
            print(f"[{i:>3}/{len(cases)}] {mark} {case.case_id} ({score.latency_s:.1f}s){detail}")
    finally:
        client.close()

    summary = aggregate(scores)
    row = {
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "label": args.label,
        "model": args.model,
        "endpoint": args.endpoint,
        "prompt_version": prompt_version,
        "guided": args.guided,
        "temperature": args.temperature,
        **{k: (round(v, 2) if isinstance(v, float) else v) for k, v in summary.items()},
    }

    RESULTS_DIR.mkdir(exist_ok=True)
    append_row(SCOREBOARD, row)

    (RESULTS_DIR / f"{args.label}.json").write_text(
        json.dumps(
            {"run": row, "cases": [s.__dict__ for s in scores]},
            indent=2,
        )
    )

    print("\n--- summary " + "-" * 48)
    for key, value in summary.items():
        print(f"  {key:<28} {value:>8.2f}" if isinstance(value, float) else f"  {key:<28} {value:>8}")

    failures = [s for s in scores if not s.passed]
    print(f"\n{len(scores) - len(failures)}/{len(scores)} cases clean. Scoreboard: {SCOREBOARD}")
    if failures:
        print("\nHard-metric failures (the 100% bar):")
        for score in failures:
            print(f"  {score.case_id}: {'; '.join(score.failure_reasons)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
