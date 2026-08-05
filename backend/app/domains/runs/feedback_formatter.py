"""Pedagogical feedback HTML presentation layer.

Formats student test execution details, AST warnings, manual rubric scores, and comments
into a self-contained, clean HTML feedback package for staff downloads and Canvas exports.
"""
from __future__ import annotations

from html import escape
from typing import TYPE_CHECKING

from app.domains.runs.service import manual_score_sum

if TYPE_CHECKING:
    from app.domains.grading.engine import GradingResult


def generate_pedagogical_feedback_html(
    student_identifier: str,
    result: GradingResult,
    manual_results: dict | None = None,
    overall_comment: str = "",
) -> str:
    """Generate a clean HTML pedagogical feedback page for the student."""
    safe_student_identifier = escape(str(student_identifier))
    tests_html = ""
    for test in result.test_results:
        status_color = "#16a34a" if test.get("passed") else "#dc2626"
        status_text = "PASSED" if test.get("passed") else "FAILED"
        safe_label = escape(str(test.get("label", test.get("key", "Test Case"))))

        sub_tests_html = ""
        sub_tests = test.get("test_results", [])
        if sub_tests:
            sub_tests_html += "<ul style='margin-top: 5px; margin-bottom: 0; padding-left: 20px; font-size: 0.9em; color: #4b5563;'>"
            for sub in sub_tests:
                sub_status = sub.get("outcome", "failed")
                sub_status_color = "#16a34a" if sub_status == "passed" else "#dc2626"
                safe_nodeid = escape(str(sub.get("nodeid", "Test Function")))
                safe_sub_status = escape(str(sub_status).upper())
                sub_tests_html += f"<li>{safe_nodeid} - <strong style='color: {sub_status_color};'>{safe_sub_status}</strong>"
                if sub.get("message"):
                    safe_message = escape(str(sub.get("message")))
                    sub_tests_html += f"<br/><pre style='font-size: 0.85em; color: #374151; background: #f3f4f6; padding: 5px; border-radius: 3px; overflow-x: auto;'>{safe_message}</pre>"
                sub_tests_html += "</li>"
            sub_tests_html += "</ul>"

        tests_html += f"""
        <div style="border: 1px solid #e5e7eb; padding: 15px; margin-bottom: 12px; border-radius: 8px; background-color: #ffffff; box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);">
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #f3f4f6; padding-bottom: 8px; margin-bottom: 8px;">
                <h3 style="margin: 0; font-size: 1.1em; color: #1f2937;">{safe_label}</h3>
                <span style="color: {status_color}; font-weight: bold; font-size: 0.9em; background-color: {status_color}15; padding: 2px 8px; border-radius: 4px;">{status_text}</span>
            </div>
            <p style="margin: 4px 0; font-size: 0.95em; color: #374151;"><strong>Points:</strong> {test.get('points_awarded', 0)} / {test.get('points', 0)}</p>
            {sub_tests_html}
        </div>
        """

    warnings_html = ""
    if result.warnings:
        warnings_html += "<h2 style='color: #d97706; border-bottom: 2px solid #fcd34d; padding-bottom: 5px;'>Warnings</h2>"
        for w in result.warnings:
            safe_code = escape(str(w.get("code", "")))
            safe_message = escape(str(w.get("message", "")))
            warnings_html += f"""
            <div style="border-left: 4px solid #f59e0b; background-color: #fffbeb; padding: 12px; margin-bottom: 12px; border-radius: 4px; box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);">
                <p style="margin: 0; color: #b45309; font-weight: bold;">{safe_code}</p>
                <p style="margin: 4px 0 0 0; color: #78350f; font-size: 0.9em;">{safe_message}</p>
            </div>
            """

    overall_failure_html = ""
    if not result.success and result.failure_message:
        safe_category = escape(str(result.failure_category))
        safe_failure_message = escape(str(result.failure_message))
        overall_failure_html = f"""
        <div style="border-left: 4px solid #dc2626; background-color: #fef2f2; padding: 15px; margin-bottom: 20px; border-radius: 4px;">
            <h3 style="margin: 0 0 5px 0; color: #991b1b;">Grading Execution Failed</h3>
            <p style="margin: 0; color: #7f1d1d; font-size: 0.95em;"><strong>Category:</strong> {safe_category}</p>
            <p style="margin: 5px 0 0 0; color: #7f1d1d; font-size: 0.95em;">{safe_failure_message}</p>
        </div>
        """

    total_score = result.score + manual_score_sum(manual_results)

    manual_html = ""
    if manual_results:
        manual_blocks = [
            "<h2 style='border-bottom: 2px solid #e5e7eb; padding-bottom: 5px; margin-top: 30px; margin-bottom: 15px;'>Manual Grading Criteria</h2>"
        ]
        for key, item in manual_results.items():
            score_val = item.get("score")
            score_text = f"{score_val} / {item.get('points')}" if score_val is not None else f"Pending / {item.get('points')}"
            status_color = "#16a34a" if score_val is not None else "#d97706"
            safe_label = escape(str(item.get("label", key)))
            safe_comments = escape(str(item.get("comments", "")))
            comments_block = ""
            if safe_comments:
                comments_block = f"<p style='margin: 8px 0 0 0; font-size: 0.9em; color: #4b5563; font-style: italic; border-left: 3px solid #cbd5e1; padding-left: 8px;'>Comments: {safe_comments}</p>"

            manual_blocks.append(f"""
            <div style="border: 1px solid #e5e7eb; padding: 15px; margin-bottom: 12px; border-radius: 8px; background-color: #ffffff; box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);">
                <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #f3f4f6; padding-bottom: 8px; margin-bottom: 8px;">
                    <h3 style="margin: 0; font-size: 1.1em; color: #1f2937;">{safe_label}</h3>
                    <span style="color: {status_color}; font-weight: bold; font-size: 0.9em; background-color: {status_color}15; padding: 2px 8px; border-radius: 4px;">{score_text}</span>
                </div>
                {comments_block}
            </div>
            """)
        manual_html = "".join(manual_blocks)

    overall_comment_html = ""
    if overall_comment:
        overall_comment_html = f"""
        <h2 style="border-bottom: 2px solid #e5e7eb; padding-bottom: 5px; margin-top: 30px;">Instructor Feedback</h2>
        <p style="white-space: pre-wrap; color: #374151;">{escape(overall_comment)}</p>
        """

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Autograder Feedback - {safe_student_identifier}</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; padding: 25px; background-color: #f9fafb; color: #111827; }}
            .container {{ max-width: 800px; margin: 0 auto; background: #ffffff; padding: 30px; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06); }}
            h1 {{ margin-top: 0; color: #111827; border-bottom: 2px solid #e5e7eb; padding-bottom: 10px; font-size: 1.75em; }}
            h2 {{ color: #1f2937; font-size: 1.4em; margin-top: 25px; }}
            pre {{ background-color: #f3f4f6; padding: 12px; border-radius: 6px; overflow-x: auto; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; border: 1px solid #e5e7eb; }}
            .summary-card {{ background: linear-gradient(135deg, #1f2937, #111827); color: #ffffff; padding: 20px; border-radius: 8px; margin-bottom: 25px; display: flex; justify-content: space-between; align-items: center; }}
            .summary-card h2 {{ margin: 0; color: #ffffff; font-size: 1.25em; }}
            .summary-card .score {{ font-size: 2em; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Autograder Feedback</h1>
            <div class="summary-card">
                <div>
                    <h2>Pedagogical Report</h2>
                    <p style="margin: 5px 0 0 0; opacity: 0.8; font-size: 0.9em;">Student: {safe_student_identifier}</p>
                </div>
                <div class="score">{total_score} / {result.max_score}</div>
            </div>
            
            {overall_failure_html}
            
            {warnings_html}
            
            <h2 style="border-bottom: 2px solid #e5e7eb; padding-bottom: 5px; margin-bottom: 15px;">Test Cases</h2>
            {tests_html}
            
            {manual_html}
            {overall_comment_html}
        </div>
    </body>
    </html>
    """
