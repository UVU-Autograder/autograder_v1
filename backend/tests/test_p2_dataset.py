"""Phase 2 dataset plumbing: held-out split, review files, and the build gate.

The build gate is what keeps a bad human edit (an invented test key, a score,
a leaked canary) out of training data, so it is tested like the runtime gate.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from eval.mutations import MUTATIONS, TRAIN_MUTATIONS
from eval.schemas import load_cases
from training import build_p2_dataset
from training.p2_review import CASES_DIR, case_messages, parse_review, parse_target, render_review

EVAL_CASES = Path(__file__).resolve().parents[1] / "eval" / "cases"
SEEDS = Path(__file__).resolve().parents[1] / "app" / "db" / "seeds"


def test_train_mutations_are_held_out_from_eval():
    train_ids = [m["case_id"] for m in TRAIN_MUTATIONS]
    assert len(train_ids) == len(set(train_ids))
    assert all(i.startswith("p2_") for i in train_ids)
    assert not set(train_ids) & {m["case_id"] for m in MUTATIONS}
    eval_edits = {(m["seed"], json.dumps(m["edits"], sort_keys=True)) for m in MUTATIONS}
    for m in TRAIN_MUTATIONS:
        assert (m["seed"], json.dumps(m["edits"], sort_keys=True)) not in eval_edits, m["case_id"]


def test_p2_cases_are_generated_and_well_formed():
    from app.integrations.ai.prompts import EXECUTION_ERROR_KEY

    cases = load_cases(CASES_DIR)
    assert len(cases) >= 130, "run: python -m eval.build_cases --split train"
    assert {c.case_id for c in cases} == {m["case_id"] for m in TRAIN_MUTATIONS}, "cases are stale: rebuild them"
    for case in cases:
        config = json.loads((SEEDS / case.assignment_slug.replace("-", "_") / "config_json.example.json").read_text())
        keys = {item["key"] for item in config["scoring_items"]} | {EXECUTION_ERROR_KEY}
        assert {f["key"] for f in case.failures} <= keys, case.case_id
        assert case.bug_diff, f"{case.case_id}: reviewers need the diff"


def test_p2_inputs_never_equal_eval_inputs():
    eval_users = {case_messages(c)[1]["content"] for c in load_cases(EVAL_CASES)}
    for case in load_cases(CASES_DIR):
        assert case_messages(case)[1]["content"] not in eval_users, case.case_id


# --- review files ----------------------------------------------------------


def _case(case_id: str = "p2_lab5_rmul_recursion"):
    return next(c for c in load_cases(CASES_DIR) if c.case_id == case_id)


def _write_review(tmp_path: Path, case, body: dict, status: str = "approved") -> Path:
    draft = json.dumps({"summary": "s", "items": [], "next_step": "n"})
    text = render_review(case, draft, "fake-model", "v4", [])
    text = text.replace("status: todo", f"status: {status}")
    text = re.sub(r"```json\n.*?\n```", "```json\n" + json.dumps(body, indent=2) + "\n```", text, flags=re.S)
    path = tmp_path / f"{case.case_id}.md"
    path.write_text(text)
    return path


GOOD = {
    "summary": "Normalizing, adding, formatting and equality all work.",
    "items": [{"test_key": "mul", "what_went_wrong": "3 * m2 never finishes.", "hint": "What does the return line of __rmul__ call next?"}],
    "next_step": "Trace __rmul__ by hand for 3 * m2.",
}


def test_review_round_trip(tmp_path):
    path = _write_review(tmp_path, _case(), GOOD)
    review = parse_review(path)
    assert (review.case_id, review.status, review.prompt_version) == ("p2_lab5_rmul_recursion", "approved", "v4")
    assert parse_target(review).items[0].test_key == "mul"


def test_review_rejects_ambiguous_status(tmp_path):
    path = _write_review(tmp_path, _case(), GOOD)
    path.write_text(path.read_text().replace("status: approved", "status: approved\nstatus: todo"))
    with pytest.raises(ValueError, match="exactly one 'status:'"):
        parse_review(path)


def test_invalid_draft_gets_a_skeleton_with_the_real_keys():
    case = _case()
    text = render_review(case, "not json", "fake-model", "v4", ["schema"])
    assert '"test_key": "mul"' in text


# --- build gate ------------------------------------------------------------


@pytest.mark.parametrize(
    ("target", "reason"),
    [
        ({**GOOD, "items": [{"test_key": "made_up", "what_went_wrong": "w", "hint": "h"}]}, "unknown test_key"),
        ({**GOOD, "summary": "You scored 80%."}, "score"),
        ({**GOOD, "items": GOOD["items"] * 2}, "twice"),
        ({**GOOD, "items": []}, "no items"),
        ({**GOOD, "next_step": "word " * 160}, "words"),
        ({**GOOD, "items": [{"test_key": "mul", "what_went_wrong": "", "hint": "h"}]}, "empty field"),
    ],
)
def test_build_gate_rejects_bad_targets(target, reason):
    from app.integrations.ai.prompts import FeedbackResponse

    problems = build_p2_dataset.target_problems(_case(), FeedbackResponse.model_validate(target))
    assert any(reason in p for p in problems), problems


def test_build_writes_only_approved_rows(tmp_path):
    reviews = tmp_path / "review"
    reviews.mkdir()
    _write_review(reviews, _case(), GOOD)
    _write_review(reviews, _case("p2_ds4_all_pass_class_attr_tax"),
                  {"summary": "Everything passed.", "items": [], "next_step": "Try a new dessert type."})
    _write_review(reviews, _case("p2_lab2_placeholder"), GOOD, status="rejected")
    out = tmp_path / "out"
    assert build_p2_dataset.main(["--reviews", str(reviews), "--out", str(out)]) == 0
    rows = [json.loads(line) for name in ("train", "valid") for line in (out / f"{name}.jsonl").read_text().splitlines()]
    assert len(rows) == 2
    for row in rows:
        assert [m["role"] for m in row["messages"]] == ["system", "user", "assistant"]
    assert json.loads((out / "meta.json").read_text())["review_counts"] == {"approved": 2, "rejected": 1}


def test_build_fails_closed_on_one_bad_file(tmp_path):
    reviews = tmp_path / "review"
    reviews.mkdir()
    _write_review(reviews, _case(), {**GOOD, "summary": "Grade: B+ so far."})
    out = tmp_path / "out"
    assert build_p2_dataset.main(["--reviews", str(reviews), "--out", str(out)]) == 1
    assert not out.exists()
