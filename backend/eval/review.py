"""Turn an eval run into a human review sheet.

    cd backend && python -m eval.review stock-12b-dell
    cd backend && python -m eval.review smoke-lora --against stock-12b-dell

Writes ``eval/results/<label>-review.md``. The hard metrics are automatic; this
sheet is for what they cannot judge -- whether the feedback is correct,
useful, and pitched right for a CS 1410 student. Fill the rubric per case, then
the scores are the signal for building a real training set: cases the stock
model handles well need no training data; the ones it handles badly are where
Phase 2 examples should go.

Each case shows what the model was given (the failures the grader reported),
what it said (rendered the way the sandbox would show it), and the automatic
verdicts. Code is not included -- inspect eval/cases.jsonl for that.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.integrations.ai.prompts import parse_response, render_markdown

from eval.schemas import load_cases

EVAL_DIR = Path(__file__).parent
RESULTS = EVAL_DIR / "results"

RUBRIC = """\
| Rubric | Score |
| --- | --- |
| **Accurate** -- explains the real cause of each listed failure (1-5) | |
| **Helpful** -- a student could act on the hint without being handed the fix (1-5) | |
| **Tone** -- encouraging, plain language, right level for CS 1410 (1-5) | |
| **Would you show this to a student?** (yes / edit / no) | |
| Notes | |
"""


def _load(label: str) -> dict:
    path = RESULTS / f"{label}.json"
    if not path.exists():
        raise SystemExit(f"no results for {label!r} at {path} -- run eval.run_eval --label {label} first")
    return json.loads(path.read_text(encoding="utf-8"))


def _shown(raw: str, labels: dict[str, str]) -> str:
    """What the sandbox would display: rendered markdown, or the raw text if unparseable."""
    try:
        return render_markdown(parse_response(raw), labels)
    except ValueError:
        return "_(not valid FeedbackResponse JSON -- the sandbox would show the fallback message)_\n\n```\n" + raw.strip() + "\n```"


def _verdict(score: dict) -> str:
    flags = ["schema_valid", "grounded", "no_solution_leak", "no_score_leak", "injection_resistant"]
    failed = [f for f in flags if not score.get(f)]
    return "all hard checks pass" if not failed else "FAILED: " + ", ".join(failed) + " -- " + "; ".join(score.get("failure_reasons", []))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("label", help="scoreboard label of the run to review")
    parser.add_argument("--against", help="second label to show side by side (e.g. the stock baseline)")
    args = parser.parse_args(argv)

    run = _load(args.label)
    other = _load(args.against) if args.against else None
    cases = {c.case_id: c for c in load_cases(EVAL_DIR / "cases.jsonl")}
    other_by_id = {s["case_id"]: s for s in (other or {}).get("cases", [])}

    meta = run["run"]
    lines = [
        f"# Review sheet: `{args.label}`" + (f" vs `{args.against}`" if other else ""),
        "",
        f"Model `{meta['model']}`, prompt `{meta['prompt_version']}`, temperature {meta['temperature']}, "
        f"{meta['n_cases']} cases, all hard metrics {meta['all_hard_metrics_pct']}%.",
        "",
        "Score each case with the rubric. Cases the model already handles well need no training data.",
        "",
        "| # | Case | Category | Assignment | Hard checks |",
        "| --- | --- | --- | --- | --- |",
    ]
    for i, score in enumerate(run["cases"], 1):
        case = cases.get(score["case_id"])
        ok = "pass" if not score.get("failure_reasons") else "**FAIL**"
        lines.append(f"| {i} | [{score['case_id']}](#{score['case_id'].replace('_', '-')}) | {score['category']} | "
                     f"{case.assignment_slug if case else '?'} | {ok} |")
    lines.append("")

    for score in run["cases"]:
        case = cases.get(score["case_id"])
        labels = {f["key"]: f.get("label", f["key"]) for f in (case.failures if case else [])}
        lines += ["---", "", f"## {score['case_id']}", ""]
        if case:
            lines.append(f"**{case.assignment_title}** · `{case.category}` · {case.notes or ''}".rstrip())
            lines.append("")
            if case.failures:
                lines.append("**What the grader reported:**")
                lines.append("")
                for f in case.failures:
                    message = (f.get("message") or "").strip().splitlines()
                    lines.append(f"- `{f['key']}` ({f.get('label', '')}): {message[-1] if message else '(no message)'}")
            else:
                lines.append("**What the grader reported:** all automated checks passed.")
            if case.concept_violations:
                lines.append(f"- Concept checks: {'; '.join(case.concept_violations)}")
            if case.injection_canaries:
                lines.append(f"- Contains an injection attempt (canaries: {', '.join(case.injection_canaries)})")
            lines.append("")
        lines += [f"**{args.label}** -- {_verdict(score)} · {score.get('latency_s', 0):.1f}s", "",
                  _shown(score.get("raw_response", ""), labels), ""]
        if other and score["case_id"] in other_by_id:
            o = other_by_id[score["case_id"]]
            lines += [f"**{args.against}** -- {_verdict(o)} · {o.get('latency_s', 0):.1f}s", "",
                      _shown(o.get("raw_response", ""), labels), ""]
        lines += [RUBRIC, ""]

    out = RESULTS / f"{args.label}-review.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {out} ({len(run['cases'])} cases)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
