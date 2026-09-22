"""Build the Phase 2 training set from approved review files.

    cd backend && python -m training.build_p2_dataset            # write training/data/p2
    cd backend && python -m training.build_p2_dataset --status   # progress only

Only files marked ``status: approved`` are used. Every approved target must pass
the same runtime gate the sandbox applies before a student sees feedback
(``guardrails.validate_feedback``), plus the prompt's own limits (at most 3
items, no repeated test_key, under 150 words, no injection canary). One bad file
fails the build with its name and reason; nothing is written until all pass.

Model inputs are rebuilt from the case files with the current prompt module,
so rows match what the sandbox sends today. The eval set stays held out: a row
whose user message equals an eval case's fails the build.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from app.integrations.ai.guardrails import response_prose, validate_feedback
from app.integrations.ai.prompts import PROMPT_VERSION

from eval.metrics import check_injection_resistant
from eval.schemas import load_cases

from training.p2_review import CASES_DIR, REVIEW_DIR, case_messages, parse_review, parse_target

HERE = Path(__file__).parent
EVAL_CASES = HERE.parent / "eval" / "cases"
OUT_DIR = HERE / "data" / "p2"
MAX_WORDS = 150
VALID_EVERY = 10  # ~10% held out for eval_loss, chosen by a stable hash of the case id


def target_problems(case, target) -> list[str]:
    problems = validate_feedback(target, case.allowed_keys, case.forbidden_identifiers)
    ok, injection = check_injection_resistant(target.model_dump_json(), case)
    problems += [] if ok else injection
    keys = [item.test_key for item in target.items]
    if len(keys) > 3:
        problems.append(f"{len(keys)} items; the prompt allows at most 3")
    if len(keys) != len(set(keys)):
        problems.append("the same test_key appears twice")
    if case.failures and not keys:
        problems.append("the grader reported failures but the response has no items")
    words = len(response_prose(target).split())
    if words > MAX_WORDS:
        problems.append(f"{words} words; the prompt asks for under {MAX_WORDS}")
    if not target.summary.strip() or not target.next_step.strip():
        problems.append("summary and next_step must not be empty")
    for item in target.items:
        if not item.what_went_wrong.strip() or not item.hint.strip():
            problems.append(f"item {item.test_key} has an empty field")
    return problems


def in_valid_split(case_id: str) -> bool:
    return int(hashlib.sha1(case_id.encode()).hexdigest(), 16) % VALID_EVERY == 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--out", type=Path, default=OUT_DIR)
    parser.add_argument("--reviews", type=Path, default=REVIEW_DIR)
    parser.add_argument("--status", action="store_true", help="report review progress and exit")
    args = parser.parse_args(argv)

    cases = {c.case_id: c for c in load_cases(CASES_DIR)}
    reviews, errors = [], []
    for path in sorted(args.reviews.glob("*.md")):
        try:
            review = parse_review(path)
        except ValueError as exc:
            errors.append(f"{path.name}: {exc}")
            continue
        if review.case_id not in cases:
            errors.append(f"{path.name}: no case file for {review.case_id} in {CASES_DIR}")
            continue
        reviews.append(review)

    counts = Counter(r.status for r in reviews)
    undrafted = len(cases) - len(reviews)
    print(f"{len(cases)} cases: {counts['approved']} approved, {counts['rejected']} rejected, "
          f"{counts['todo']} to review, {undrafted} not drafted yet")
    if args.status:
        for e in errors:
            print(f"  ! {e}")
        return 1 if errors else 0

    eval_users = {case_messages(c)[1]["content"] for c in load_cases(EVAL_CASES)}
    rows: dict[str, list[dict]] = {"train": [], "valid": []}
    by_category: Counter[str] = Counter()
    stale_prompt = set()
    longest = 0
    for review in reviews:
        if review.status != "approved":
            continue
        case = cases[review.case_id]
        try:
            target = parse_target(review)
        except ValueError as exc:
            errors.append(f"{review.path.name}: {exc}")
            continue
        problems = target_problems(case, target)
        if problems:
            errors.append(f"{review.path.name}: " + "; ".join(problems))
            continue
        messages = case_messages(case)
        if messages[1]["content"] in eval_users:
            errors.append(f"{review.path.name}: identical to an eval case input (eval must stay held out)")
            continue
        if review.prompt_version != PROMPT_VERSION:
            stale_prompt.add(review.prompt_version)
        longest = max(longest, sum(len(m["content"]) for m in messages))
        messages.append({"role": "assistant", "content": target.model_dump_json()})
        rows["valid" if in_valid_split(case.case_id) else "train"].append({"messages": messages})
        by_category[case.category] += 1

    if errors:
        print(f"\n{len(errors)} problem(s); fix these files and rebuild (nothing written):")
        for e in errors:
            print(f"  ! {e}")
        return 1
    if not rows["train"]:
        print("no approved reviews yet -- nothing to write")
        return 1
    if not rows["valid"]:  # tiny early builds: still give the trainer an eval_loss
        rows["valid"].append(rows["train"].pop())

    args.out.mkdir(parents=True, exist_ok=True)
    for name, data in rows.items():
        with (args.out / f"{name}.jsonl").open("w") as handle:
            for row in data:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    meta = {
        "prompt_version": PROMPT_VERSION,
        "train": len(rows["train"]),
        "valid": len(rows["valid"]),
        "by_category": dict(sorted(by_category.items())),
        "review_counts": dict(counts),
        "longest_prompt_chars": longest,
    }
    (args.out / "meta.json").write_text(json.dumps(meta, indent=2) + "\n")
    print(f"wrote {len(rows['train'])} train / {len(rows['valid'])} valid rows to {args.out}")
    print(f"by category: {dict(sorted(by_category.items()))}")
    print(f"longest prompt: {longest} chars (~{longest // 3} tokens); train with --max-length 4096 so none are dropped")
    if stale_prompt:
        print(f"note: some targets were drafted under prompt {sorted(stale_prompt)}, inputs are rebuilt with "
              f"{PROMPT_VERSION}. Re-read those targets if the rules changed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
