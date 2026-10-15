#!/usr/bin/env python3
"""Turn stress-test results into a Markdown report and an optional one-page PDF.

    python3 scripts/stress_report.py after-grading.json after-ai.json \\
        --baseline before-grading.json --gpu gpu-1530.csv --model-capacity stress-1451.json \\
        --md stress-report.md --pdf stress-report.pdf

Inputs (all aggregate, no run ids or code):
- ``scripts/stress_suite.py --json-out`` files: grading, ai, burst and judge0 scenarios.
  Several files are merged, so each scenario can come from its own run.
- ``--baseline``: an earlier stress_suite file (before the changes) for a before/after table.
- ``--gpu``: an ``nvidia-smi --query-gpu=... --format=csv -l 1`` log taken during the run.
- ``--model-capacity``: an ``eval.stress_vllm --json-out`` file (model-only capacity).

The PDF needs reportlab (``pip install reportlab``); the Markdown never does.
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
from datetime import date
from pathlib import Path

OLD_CLIENT_GIVE_UP_S = 74.5  # the browser's poll limit before this release


def load(paths: list[Path]) -> tuple[dict[str, list[dict]], list[dict]]:
    """Scenario rows merged across files, plus each file's header."""
    scenarios: dict[str, list[dict]] = {}
    headers = []
    for path in paths:
        data = json.loads(path.read_text(encoding="utf-8"))
        headers.append({k: data.get(k) for k in ("label", "started_at", "git_commit", "api")})
        for name, rows in (data.get("scenarios") or {}).items():
            scenarios.setdefault(name, []).extend(rows if isinstance(rows, list) else [rows])
    return scenarios, headers


def p(stats: dict | None, key: str = "p95") -> str:
    if not stats or stats.get(key) is None:
        return "–"
    return f"{stats[key]:g}"


def counts(d: dict | None) -> str:
    return ", ".join(f"{k} {v}" for k, v in sorted((d or {}).items())) or "–"


def gpu_summary(path: Path) -> dict:
    """Utilisation, power, temperature and clock from an nvidia-smi CSV log."""
    util, power, temp, clock = [], [], [], []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        header = [h.strip() for h in next(reader)]

        def col(name: str) -> int | None:
            return next((i for i, h in enumerate(header) if h.startswith(name)), None)

        cols = {k: col(k) for k in ("utilization.gpu", "power.draw", "temperature.gpu", "clocks.current.sm", "clocks.sm")}
        for row in reader:
            def num(key: str) -> float | None:
                i = cols.get(key)
                if i is None or i >= len(row):
                    return None
                try:
                    return float(row[i].strip().split()[0])
                except (ValueError, IndexError):
                    return None
            for key, bucket in (("utilization.gpu", util), ("power.draw", power), ("temperature.gpu", temp)):
                value = num(key)
                if value is not None:
                    bucket.append(value)
            value = num("clocks.current.sm") if cols["clocks.current.sm"] is not None else num("clocks.sm")
            if value is not None:
                clock.append(value)
    busy = [u for u in util if u > 5]
    return {
        "samples": len(util),
        "util_busy_avg": round(statistics.mean(busy), 1) if busy else None,
        "util_max": max(util) if util else None,
        "power_max_w": max(power) if power else None,
        "temp_max_c": max(temp) if temp else None,
        "sm_clock_min_busy_mhz": min((c for c, u in zip(clock, util) if u >= 50), default=None),
    }


def grading_rows(rows: list[dict]) -> list[list[str]]:
    out = [["Students", "Graded", "Not admitted", "Queue wait p50 / p95 (s)", "Total p95 (s)", "Runs/min",
            f"Over {OLD_CLIENT_GIVE_UP_S:g} s", "Grader faults", "Wait estimate error p50 / p95 (s)"]]
    for r in sorted(rows, key=lambda r: r["students"]):
        finals = r.get("finals") or {}
        out.append([
            str(r["students"]),
            f"{finals.get('complete', 0)} / {r['students']}",
            str(finals.get("not_admitted", 0)),
            f"{p(r.get('queue_wait_s'), 'p50')} / {p(r.get('queue_wait_s'))}",
            p(r.get("total_s")),
            f"{r.get('runs_per_minute', '–')}",
            str(r.get("old_client_gave_up", 0)),
            str(r.get("grader_faults", 0)),
            f"{p(r.get('eta_signed_error_s'), 'p50')} / {p(r.get('eta_signed_error_s'))}",
        ])
    return out


def compare_rows(before: list[dict], after: list[dict]) -> list[list[str]]:
    by_level = {r["students"]: r for r in before}
    out = [["Students", "Graded (before → after)", f"Over {OLD_CLIENT_GIVE_UP_S:g} s", "Total p95 (s)", "Runs/min",
            "Grader faults"]]
    for r in sorted(after, key=lambda r: r["students"]):
        b = by_level.get(r["students"])
        if b is None:
            continue

        def pair(get):
            return f"{get(b)} → {get(r)}"

        out.append([
            str(r["students"]),
            pair(lambda x: (x.get("finals") or {}).get("complete", 0)),
            pair(lambda x: x.get("old_client_gave_up", 0)),
            pair(lambda x: p(x.get("total_s"))),
            pair(lambda x: x.get("runs_per_minute", "–")),
            pair(lambda x: x.get("grader_faults", 0)),
        ])
    return out if len(out) > 1 else []


def ai_rows(rows: list[dict]) -> list[list[str]]:
    out = [["Students", "First try", "Answer p50 / p95 (s)", "With UI retries", "Total p95 (s)", "GPU avg / max %",
            "Tokens/s", "vLLM max waiting"]]
    for r in sorted(rows, key=lambda r: r["students"]):
        gpu = "–" if r.get("gpu_util_avg") is None else f"{r['gpu_util_avg']:g} / {r.get('gpu_util_max', '–')}"
        out.append([
            str(r["students"]), counts(r.get("first_attempt")),
            f"{p(r.get('first_attempt_answer_s'), 'p50')} / {p(r.get('first_attempt_answer_s'))}",
            counts(r.get("with_retries_final")), p(r.get("with_retries_total_s")), gpu,
            f"{r['generated_tokens_per_second']:g}" if r.get("generated_tokens_per_second") else "–",
            f"{r['vllm_max_waiting']:g}" if r.get("vllm_max_waiting") is not None else "–",
        ])
    return out


def burst_rows(rows: list[dict]) -> list[list[str]]:
    out = [["Students", "Think (s)", "Graded", "Grading p95 (s)", "Feedback", "Feedback p95 (s)", "Queue depth max"]]
    for r in rows:
        think = "–".join(f"{t:g}" for t in r.get("think_seconds") or [])
        out.append([str(r["students"]), think, counts(r.get("grading_finals")), p(r.get("grading_total_s")),
                    counts(r.get("ai_finals")), p(r.get("ai_total_s")), str(r.get("max_queue_depth", "–"))])
    return out


def judge0_rows(rows: list[dict]) -> list[list[str]]:
    out = [["Concurrent", "Submissions", "Outcomes", "Latency p50 / p95 (s)", "Per min", "Deleted",
            "Gone after delete"]]
    for r in sorted(rows, key=lambda r: r["concurrent"]):
        out.append([str(r["concurrent"]), str(r["submissions"]), counts(r.get("outcomes")),
                    f"{p(r.get('latency_s'), 'p50')} / {p(r.get('latency_s'))}", str(r.get("per_minute", "–")),
                    f"{r.get('deleted', 0)} / {r['submissions']}",
                    f"{r.get('not_retrievable_after_delete', 0)} / {r['submissions']}"])
    return out


def model_rows(data: dict) -> list[list[str]]:
    out = [["In flight", "Requests", "OK", "p50 / p95 (s)", "Over 30 s", "Tokens/s", "GPU avg %"]]
    for r in data.get("levels", []):
        out.append([str(r["concurrency"]), str(r["requests"]), str(r["ok"]),
                    f"{r.get('latency_p50', '–')} / {r.get('latency_p95', '–')}", str(r.get("over_backend_limit", 0)),
                    f"{r.get('generated_tokens_per_second', '–')}", f"{r.get('gpu_util_avg', '–')}"])
    return out


def findings(scenarios: dict[str, list[dict]]) -> list[str]:
    """Plain statements the numbers support; nothing is claimed for scenarios that did not run."""
    notes = []
    grading = sorted(scenarios.get("grading", []), key=lambda r: r["students"])
    clean = [r for r in grading if (r.get("finals") or {}).get("complete") == r["students"] and not r.get("grader_faults")]
    if grading:
        top = clean[-1]["students"] if clean else None
        notes.append(f"Grading: every run completed with no grader faults up to {top} simultaneous students."
                     if top else "Grading: no tested level completed every run without a grader fault.")
        slow = [r for r in grading if r.get("old_client_gave_up")]
        if slow:
            worst = max(slow, key=lambda r: r["old_client_gave_up"])
            notes.append(f"At {worst['students']} students, {worst['old_client_gave_up']} runs took longer than "
                         f"{OLD_CLIENT_GIVE_UP_S:g} s, where the old browser stopped waiting; the new one keeps "
                         "polling for 10 minutes and offers Check again.")
        errors = [r["eta_signed_error_s"] for r in grading if (r.get("eta_signed_error_s") or {}).get("n")]
        if errors:
            p95 = max(e["p95"] for e in errors)
            notes.append(f"Wait estimates err long: at the 95th percentile they over-state the wait by up to {p95:g} s "
                         "(mostly the first runs after a quiet period, before timings exist).")
    ai = sorted(scenarios.get("ai", []), key=lambda r: r["students"])
    if ai:
        ok = [r for r in ai if set((r.get("first_attempt") or {})) == {"answer"}]
        if ok:
            notes.append(f"AI feedback: every first request answered up to {ok[-1]['students']} simultaneous students.")
        busy = [r for r in ai if (r.get("first_attempt") or {}).get("ai_busy")]
        if busy:
            r = busy[0]
            notes.append(f"At {r['students']} students some first requests got \"busy, retrying\" "
                         f"({r['first_attempt']['ai_busy']}); with the UI's retries the final result was "
                         f"{counts(r.get('with_retries_final'))}.")
    for r in scenarios.get("judge0", []):
        if r.get("not_retrievable_after_delete", 0) < r["submissions"]:
            notes.append(f"Judge0 at {r['concurrent']} concurrent: "
                         f"{r['submissions'] - r.get('not_retrievable_after_delete', 0)} submissions were still "
                         "retrievable after delete (zero-retention check failed).")
    return notes


def md_table(rows: list[list[str]]) -> str:
    if not rows:
        return ""
    lines = ["| " + " | ".join(rows[0]) + " |", "|" + "---|" * len(rows[0])]
    lines += ["| " + " | ".join(r) + " |" for r in rows[1:]]
    return "\n".join(lines)


def build(args) -> tuple[str, list[tuple[str, list[list[str]] | list[str]]], str]:
    scenarios, headers = load(args.results)
    sections: list[tuple[str, list[list[str]] | list[str]]] = [("Findings", findings(scenarios))]
    if scenarios.get("grading"):
        sections.append(("Grading under load (Judge0 through the full sandbox path)", grading_rows(scenarios["grading"])))
        if args.baseline:
            before, _ = load([args.baseline])
            rows = compare_rows(before.get("grading", []), scenarios["grading"])
            if rows:
                sections.append((f"Before and after ({args.baseline.name})", rows))
    if scenarios.get("ai"):
        sections.append(("AI feedback under load (end to end)", ai_rows(scenarios["ai"])))
    if scenarios.get("burst"):
        sections.append(("End-of-lab burst: submit, think, ask for feedback", burst_rows(scenarios["burst"])))
    if scenarios.get("judge0"):
        sections.append(("Judge0 directly (throughput and zero retention)", judge0_rows(scenarios["judge0"])))
    if args.model_capacity:
        sections.append(("Model capacity (vLLM only)", model_rows(json.loads(args.model_capacity.read_text()))))
    if args.gpu:
        g = gpu_summary(args.gpu)
        sections.append(("GPU during the run", [["Samples", "Busy avg %", "Max %", "Power max (W)", "Temp max (°C)",
                                                 "Min SM clock while busy (MHz)"],
                                                [str(g["samples"]), str(g["util_busy_avg"]), str(g["util_max"]),
                                                 str(g["power_max_w"]), str(g["temp_max_c"]),
                                                 str(g["sm_clock_min_busy_mhz"])]]))
    labels = ", ".join(sorted({h["label"] for h in headers if h.get("label")})) or "stress run"
    commits = ", ".join(sorted({h["git_commit"] for h in headers if h.get("git_commit")})) or "unknown"
    started = min((h["started_at"] for h in headers if h.get("started_at")), default=str(date.today()))
    subtitle = (f"{labels} · {started[:10]} · commit {commits} · synthetic submissions only; results are aggregate "
                "(no run ids, sessions or code)")
    return args.title, sections, subtitle


def write_md(path: Path, title: str, sections, subtitle: str) -> None:
    parts = [f"# {title}", "", subtitle, ""]
    for heading, body in sections:
        parts += [f"## {heading}", ""]
        if body and isinstance(body[0], list):
            parts += [md_table(body), ""]
        else:
            parts += [f"- {line}" for line in body] + [""]
    path.write_text("\n".join(parts), encoding="utf-8")


def write_pdf(path: Path, title: str, sections, subtitle: str) -> None:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    green, ink, muted, rule = (colors.HexColor(c) for c in ("#275D38", "#1F2328", "#57606A", "#D0D7DE"))
    h1 = ParagraphStyle("t", fontName="Helvetica-Bold", fontSize=16, leading=19, textColor=ink)
    sub = ParagraphStyle("s", fontName="Helvetica", fontSize=8, leading=10, textColor=muted)
    h2 = ParagraphStyle("h", fontName="Helvetica-Bold", fontSize=10, leading=12, textColor=green, spaceBefore=6,
                        spaceAfter=3)
    body = ParagraphStyle("b", fontName="Helvetica", fontSize=8.4, leading=10.6, textColor=ink)
    cell = ParagraphStyle("c", parent=body, fontSize=7.4, leading=9)
    head = ParagraphStyle("hd", parent=cell, fontName="Helvetica-Bold", textColor=colors.white)

    width = letter[0] - 1.2 * inch
    story = [Paragraph(title, h1), Spacer(1, 2), Paragraph(subtitle, sub)]
    for heading, rows in sections:
        story.append(Paragraph(heading, h2))
        if rows and isinstance(rows[0], list):
            data = [[Paragraph(str(c), head if i == 0 else cell) for c in row] for i, row in enumerate(rows)]
            table = Table(data, colWidths=[width / len(rows[0])] * len(rows[0]), hAlign="LEFT")
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), green), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LINEBELOW", (0, 1), (-1, -1), 0.4, rule),
                ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 3),
            ]))
            story.append(table)
        else:
            story += [Paragraph(f"• {line}", body) for line in rows]
    SimpleDocTemplate(str(path), pagesize=letter, leftMargin=0.6 * inch, rightMargin=0.6 * inch,
                      topMargin=0.5 * inch, bottomMargin=0.5 * inch, title=title).build(story)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("results", nargs="+", type=Path, help="stress_suite --json-out files")
    parser.add_argument("--baseline", type=Path, help="an earlier stress_suite file for before/after")
    parser.add_argument("--gpu", type=Path, help="nvidia-smi CSV log from the run")
    parser.add_argument("--model-capacity", type=Path, help="eval.stress_vllm --json-out file")
    parser.add_argument("--title", default="Sandbox stress test: grading and AI feedback")
    parser.add_argument("--md", type=Path, default=Path("stress-report.md"))
    parser.add_argument("--pdf", type=Path, help="also write a PDF (needs reportlab)")
    args = parser.parse_args(argv)

    title, sections, subtitle = build(args)
    write_md(args.md, title, sections, subtitle)
    print(f"wrote {args.md}")
    if args.pdf:
        try:
            write_pdf(args.pdf, title, sections, subtitle)
        except ImportError:
            print("reportlab is not installed; skipped the PDF (pip install reportlab)")
            return 1
        print(f"wrote {args.pdf}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
