"""Build the Phase 2 training set from approved review files.

    cd backend && python -m training.build_p2_dataset --prompt-version v9 --out training/data/p4   # p4
    cd backend && python -m training.build_p2_dataset --status   # progress only

Only files marked ``status: approved`` are used. Every approved target must pass
the same runtime gate the sandbox applies before a student sees feedback
(``guardrails.validate_feedback``), plus the prompt's own limits (at most 3
items, no repeated test_key, under 80 words, no injection canary) and the
prompt-v8 answer checks (``leak_checks``): no value from the failing tests
repeated, no literal that only the model solution has, and no hint or next step
that names an attribute or parameter from the changed lines. One bad file fails
the build with its name and reason; nothing is written until all pass.

Model inputs are rebuilt from the case files with the prompt version given
(``--prompt-version``, the one the new adapter will be served with), so rows
match what the sandbox will send. The eval set stays held out: a row whose user
message equals an eval case's (both rendered the same way) fails the build.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from app.integrations.ai import leak_checks
from app.integrations.ai.guardrails import response_prose
from app.integrations.ai.prompts import MAX_OUTPUT_TOKENS, PROMPT_VERSION, PROMPT_VERSIONS

from eval.metrics import check_injection_resistant, gate_reasons
from eval.schemas import load_cases

from training.p2_review import CASES_DIR, REVIEW_DIR, case_messages, parse_review, parse_target

HERE = Path(__file__).parent
EVAL_CASES = HERE.parent / "eval" / "cases.jsonl"
OUT_DIR = HERE / "data" / "p3"
MAX_WORDS = 80  # the prompt's limit
# Targets leave headroom under the prompt's limit: p3 wrote ~10 words more than its
# targets on 3-item cases (targets median 75 -> answers 82-89, 6% over 80).
TARGET_MAX_WORDS = 65
MAX_NEXT_STEP_WORDS = 14  # the prompt says "under 15 words"
# p3b wrote 15-17-word next steps on all-pass and concept-violation cases (targets were
# 11-14) and 87-106 words on three-item cascades (targets 58-65): it runs ~3 words over
# its targets per field. p4 targets leave that room.
ALL_PASS_NEXT_STEP_WORDS = 10
THREE_ITEM_MAX_WORDS = 45  # p4 still ran 83-99 words on 3-item cascades with 51-55-word targets
SERVE_MAX_MODEL_LEN = 12288  # --max-model-len in vllm-cs1410.service and serve.sh
VALID_EVERY = 10  # ~10% held out for eval_loss, chosen by a stable hash of the case id
HOLDOUT_BOUNDARY = "holdout"


def target_problems(case, target) -> list[str]:
    problems = gate_reasons(case, target)  # the full runtime gate, with the model solution's names
    ok, injection = check_injection_resistant(target.model_dump_json(), case)
    problems += [] if ok else injection
    keys = [item.test_key for item in target.items]
    if len(keys) > 3:
        problems.append(f"{len(keys)} items; the prompt allows at most 3")
    if len(keys) != len(set(keys)):
        problems.append("the same test_key appears twice")
    if case.failures and not keys:
        problems.append("the grader reported failures but the response has no items")
    prose = response_prose(target)
    words = leak_checks.word_count(prose)
    if words > TARGET_MAX_WORDS:
        problems.append(f"{words} words; targets stay at {TARGET_MAX_WORDS} or fewer (the prompt's limit is {MAX_WORDS}, "
                        "and the model writes longer than its targets)")
    next_step_words = leak_checks.word_count(target.next_step)
    if next_step_words > MAX_NEXT_STEP_WORDS:
        problems.append(f"next_step has {next_step_words} words; the prompt asks for under {MAX_NEXT_STEP_WORDS + 1}")
    elif not case.failures and next_step_words > ALL_PASS_NEXT_STEP_WORDS:
        problems.append(f"next_step has {next_step_words} words; all-pass and concept-only targets stay at "
                        f"{ALL_PASS_NEXT_STEP_WORDS} or fewer (the model writes longer than its targets)")
    if len(keys) == 3 and words > THREE_ITEM_MAX_WORDS:
        problems.append(f"{words} words with three items; keep follow-on items brief "
                        f"({THREE_ITEM_MAX_WORDS} or fewer, the model writes longer than its targets)")
    if not case.failures and not case.concept_violations:
        problems += leak_checks.all_pass_problems(target.summary, target.next_step)
    echoed = leak_checks.echoed_values(prose, case.failures)
    if echoed:
        problems.append(f"repeats values from the test results ({', '.join(echoed)}); describe the difference in words")
    answers = leak_checks.answer_literals(prose, case.bug_diff, leak_checks.shown_labels(case.failures))
    if answers:
        problems.append(f"contains what to type ({', '.join(answers)}), found only in the model solution")
    pointers = "\n".join([target.next_step] + [f"{item.what_went_wrong}\n{item.hint}" for item in target.items])
    named = leak_checks.pinpointed_identifiers(pointers, case.bug_diff)
    if named:
        problems.append(f"item/next step names the exact attribute or parameter to change ({', '.join(named)})")
    if not target.summary.strip() or not target.next_step.strip():
        problems.append("summary and next_step must not be empty")
    for item in target.items:
        if not item.what_went_wrong.strip() or not item.hint.strip():
            problems.append(f"item {item.test_key} has an empty field")
    return problems


def as_model_writes_it(target) -> str:
    """The target in the base model's own JSON style: a json fence, 2-space indent.

    Stock Gemma 4 12B writes exactly this for 51 of 57 eval responses. The first
    Phase 2 adapter was trained on compact model_dump_json() targets instead, and
    in 5 of 57 eval responses it blended the two styles at a key boundary
    (',""items"', a stray ']'), breaking the JSON. Training on the native form
    teaches content without also teaching a new surface format.
    """
    return "```json\n" + json.dumps(target.model_dump(), indent=2, ensure_ascii=False) + "\n```"


def in_valid_split(case_id: str) -> bool:
    return int(hashlib.sha1(case_id.encode()).hexdigest(), 16) % VALID_EVERY == 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--out", type=Path, default=OUT_DIR)
    parser.add_argument("--reviews", type=Path, default=REVIEW_DIR)
    parser.add_argument("--status", action="store_true", help="report review progress and exit")
    parser.add_argument("--prompt-version", choices=PROMPT_VERSIONS, default=PROMPT_VERSION,
                        help="prompt the training inputs use (the version the adapter will be served with)")
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

    version = args.prompt_version
    # Holdout check: render both sides with one fixed data-block id so equal inputs compare equal.
    eval_users = {case_messages(c, version, HOLDOUT_BOUNDARY)[1]["content"] for c in load_cases(EVAL_CASES)}
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
        if case_messages(case, version, HOLDOUT_BOUNDARY)[1]["content"] in eval_users:
            errors.append(f"{review.path.name}: identical to an eval case input (eval must stay held out)")
            continue
        messages = case_messages(case, version)
        if review.prompt_version != version:
            stale_prompt.add(review.prompt_version)
        longest = max(longest, sum(len(m["content"]) for m in messages))
        messages.append({"role": "assistant", "content": as_model_writes_it(target)})
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
        with (args.out / f"{name}.jsonl").open("w", encoding="utf-8") as handle:
            for row in data:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    meta = {
        "prompt_version": version,
        "target_format": "json fence, indent=2 (as the base model writes it)",
        "train": len(rows["train"]),
        "valid": len(rows["valid"]),
        "by_category": dict(sorted(by_category.items())),
        "review_counts": dict(counts),
        "longest_prompt_chars": longest,
    }
    (args.out / "meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(rows['train'])} train / {len(rows['valid'])} valid rows to {args.out}")
    print(f"by category: {dict(sorted(by_category.items()))}")
    estimate = longest // 3  # rough and on the high side; the real tokenizer runs in train_lora
    needed = estimate + MAX_OUTPUT_TOKENS  # prompt + room for the response
    max_length = next((n for n in (4096, 6144, 8192, 12288) if needed <= n), 12288)
    steps = max(1, (2 * len(rows["train"])) // 4)  # ~2 passes at grad_accum=4
    print(f"longest prompt: {longest} chars (~{estimate} tokens, rough estimate). train_lora drops rows over "
          f"--max-length and reports how many; use --max-length {max_length} --max-steps {steps}.")
    if needed > SERVE_MAX_MODEL_LEN:
        print(f"warning: prompt + {MAX_OUTPUT_TOKENS} output tokens may exceed vLLM --max-model-len {SERVE_MAX_MODEL_LEN}; "
              "check the real token count on the Dell before serving this prompt version.")
    if stale_prompt:
        print(f"note: some targets were drafted under prompt {sorted(stale_prompt)}, inputs are rebuilt with "
              f"{version}. Re-read those targets if the rules changed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
