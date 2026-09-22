"""Draft Phase 2 targets with a served model, one review file per case.

    cd backend && ~/venvs/train/bin/python -m training.draft_p2 --endpoint vllm --model gemma4-12b-qat

Writes ``training/p2/review/<case_id>.md`` for every case in
``training/p2/cases`` that has no review file yet. A file that already exists
is never touched, so drafting again after you started editing is safe;
``--redraft-todo`` re-drafts only files whose status is still ``todo``.

Drafts use server-side JSON-schema enforcement (as the sandbox does), so the
reviewer edits wording, not broken JSON.
"""

from __future__ import annotations

import argparse
import sys

from app.integrations.ai.guardrails import validate_feedback
from app.integrations.ai.prompts import GENERATION_TEMPERATURE, PROMPT_VERSION, RESPONSE_JSON_SCHEMA, parse_response

from eval.client import ChatClient
from eval.metrics import check_injection_resistant
from eval.schemas import load_cases

from training.p2_review import CASES_DIR, REVIEW_DIR, case_messages, parse_review, render_review, review_path


def draft_verdict(case, raw: str) -> list[str]:
    try:
        response = parse_response(raw)
    except ValueError as exc:
        return [str(exc)]
    reasons = validate_feedback(response, case.allowed_keys, case.forbidden_identifiers)
    ok, injection = check_injection_resistant(raw, case)
    return reasons + ([] if ok else injection)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--endpoint", default="vllm", help="lmstudio | ollama | vllm | full URL")
    parser.add_argument("--model", required=True, help="model id as the server reports it (stock, not a LoRA)")
    parser.add_argument("--only", default="", help="only cases whose id contains this")
    parser.add_argument("--redraft-todo", action="store_true", help="re-draft files whose status is still todo")
    parser.add_argument("--no-guided", action="store_true", help="do not request JSON-schema enforcement")
    args = parser.parse_args(argv)

    cases = [c for c in load_cases(CASES_DIR) if args.only in c.case_id]
    if not cases:
        print(f"no cases in {CASES_DIR} -- run: python -m eval.build_cases --split train", file=sys.stderr)
        return 1
    REVIEW_DIR.mkdir(parents=True, exist_ok=True)

    todo = []
    for case in cases:
        path = review_path(case.case_id)
        if not path.exists():
            todo.append(case)
        elif args.redraft_todo and parse_review(path).status == "todo":
            todo.append(case)
    print(f"{len(cases)} case(s), {len(todo)} to draft, {len(cases) - len(todo)} already have a review file")

    client = ChatClient(
        args.endpoint, args.model, temperature=GENERATION_TEMPERATURE,
        json_schema=None if args.no_guided else RESPONSE_JSON_SCHEMA,
    )
    failed = 0
    try:
        for i, case in enumerate(todo, 1):
            try:
                completion = client.complete(case_messages(case))
            except Exception as exc:  # noqa: BLE001 - keep going; the case stays undrafted
                failed += 1
                print(f"[{i:>3}/{len(todo)}] ERROR {case.case_id}: {exc}")
                continue
            verdict = draft_verdict(case, completion.text)
            review_path(case.case_id).write_text(render_review(case, completion.text, args.model, PROMPT_VERSION, verdict))
            mark = "ok  " if not verdict else "FAIL"
            print(f"[{i:>3}/{len(todo)}] {mark} {case.case_id} ({completion.latency_s:.1f}s)")
    finally:
        client.close()
    print(f"\nwrote {len(todo) - failed} review file(s) to {REVIEW_DIR}" + (f", {failed} request(s) failed" if failed else ""))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
