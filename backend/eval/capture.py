"""Turn a real sandbox run into a frozen eval case.

Two inputs, both easy to produce once the stack is up locally:

    # A: straight from the running API
    python -m eval.capture --run-id <id> --code path/to/submission.py \
        --case-id ds2_missing_next --category single_failure

    # B: from a saved SandboxRunResultResponse payload
    python -m eval.capture --result-json result.json --code submission.py \
        --case-id ds2_missing_next --category single_failure

Writes to ``eval/cases.jsonl``. Review the emitted case by hand before
committing it -- `forbidden_identifiers` is auto-guessed from the student code
and usually needs a trim, and this is also your FERPA checkpoint.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import httpx

from eval.schemas import EvalCase, load_cases, save_cases

CASES_FILE = Path(__file__).parent / "cases.jsonl"
_DEF_RE = re.compile(r"^\s*(?:def|class)\s+([A-Za-z_]\w*)", re.M)


def _fetch(api: str, run_id: str) -> dict:
    response = httpx.get(f"{api.rstrip('/')}/sandbox/runs/{run_id}/result", timeout=30)
    response.raise_for_status()
    return response.json()


def _failures_from_result(result: dict) -> list[dict]:
    """SandboxRunResultResponse.test_summaries -> the failure dicts the prompt expects.

    Only failing items are forwarded: the closed set handed to the model is what
    `check_grounded` later holds it to.
    """
    failures = []
    for item in result.get("test_summaries", []):
        if item.get("status") != "failed":
            continue
        failures.append(
            {
                "key": item.get("key") or item["label"].lower().replace(" ", "_"),
                "label": item.get("label", ""),
                "message": item.get("message"),
                "your_value": item.get("your_value"),
                "expected_value": item.get("expected_value"),
                "expected_input": item.get("expected_input"),
            }
        )
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Freeze a sandbox run into an eval case.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--run-id", help="Fetch from a running backend")
    source.add_argument("--result-json", type=Path, help="A saved result payload")
    parser.add_argument("--api", default="http://127.0.0.1:8000", help="Backend base URL")
    parser.add_argument("--code", type=Path, required=True, help="The submission file")
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--category", required=True)
    parser.add_argument("--assignment-slug", default="")
    parser.add_argument("--title", default="")
    parser.add_argument("--requirements", type=Path, help="desc.md for this assignment")
    args = parser.parse_args(argv)

    result = (
        json.loads(args.result_json.read_text())
        if args.result_json
        else _fetch(args.api, args.run_id)
    )
    code = args.code.read_text()

    case = EvalCase(
        case_id=args.case_id,
        category=args.category,
        assignment_slug=args.assignment_slug,
        assignment_title=args.title or args.assignment_slug,
        requirements=args.requirements.read_text() if args.requirements else "",
        allowed_concepts=[],
        failures=_failures_from_result(result),
        concept_violations=[
            w["message"] for w in result.get("warnings", []) if "concept" in w.get("code", "")
        ],
        student_code=code,
        forbidden_identifiers=sorted(set(_DEF_RE.findall(code))),
        notes="captured from sandbox run; reviewed by hand: NO",
    )

    cases = load_cases(CASES_FILE) if CASES_FILE.is_file() else []
    cases = [c for c in cases if c.case_id != case.case_id] + [case]
    save_cases(cases, CASES_FILE)

    print(f"saved {case.case_id} to {CASES_FILE}")
    print(f"  failures: {len(case.failures)}  forbidden_identifiers: {case.forbidden_identifiers}")
    print("\nBefore committing:")
    print("  1. Trim forbidden_identifiers to symbols the assignment actually requires.")
    print("  2. Confirm student_code carries no name, UVU ID, or Canvas identifier.")
    print("  3. Flip the notes line to 'reviewed by hand: YES'.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
