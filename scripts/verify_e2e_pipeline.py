#!/usr/bin/env python3
"""Comprehensive End-to-End Pipeline Verification Script.
Tests:
1. CS 1400 m1-lab1: Partial submission (6/10) -> Tests report -> Socratic AI feedback from Gemma 4 12B
2. CS 1400 m1-lab1: Perfect submission (10/10) -> Full score -> Congratulatory AI feedback
3. CS 1400 m1-lab1: Empty file submission (2/10) -> Initial scaffolding Socratic AI hints
4. CS 1410 lab1: Missing required file preflight validation -> Clear error message -> AI feedback
5. CS 1410 lab1: Lab 1 with all required files & custom Pillow runtime -> Complete state & AI feedback
"""

import argparse
import io
import json
import os
import sys
import time
import urllib.request
import urllib.error
import zipfile
from PIL import Image

BASE_URL = os.environ.get("BASE_URL", "http://10.115.20.200/api")


def log(section, msg):
    print(f"[{section}] {msg}")


def make_zip(file_dict: dict[str, str | bytes]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for fname, content in file_dict.items():
            if isinstance(content, str):
                zf.writestr(fname, content.encode("utf-8"))
            else:
                zf.writestr(fname, content)
    return buf.getvalue()


def make_dummy_jpeg() -> bytes:
    # 20x20 image with two distinct colors so len(set(pixels)) > 1 passes non-triviality check
    img = Image.new("RGB", (20, 20), color="blue")
    for x in range(10):
        for y in range(10):
            img.putpixel((x, y), (255, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def submit_sandbox_run(
    course_id: str, assignment_id: str, zip_bytes: bytes, stdin_text: str = None
) -> tuple[dict, str]:
    boundary = "----WebKitFormBoundaryE2ETest"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="bundle"; filename="submission.zip"\r\n'
        f"Content-Type: application/zip\r\n\r\n"
    ).encode("utf-8") + zip_bytes
    if stdin_text:
        body += (
            f'\r\n--{boundary}\r\nContent-Disposition: form-data; name="stdin"\r\n\r\n{stdin_text}'
        ).encode("utf-8")
    body += f"\r\n--{boundary}--\r\n".encode("utf-8")

    req = urllib.request.Request(
        f"{BASE_URL}/sandbox/courses/{course_id}/assignments/{assignment_id}/runs",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        session_id = resp.headers.get("X-Sandbox-Session")
        data = json.loads(resp.read().decode("utf-8"))
        return data, session_id


def poll_run(status_url: str, max_seconds: int = 30) -> dict:
    start = time.time()
    while time.time() - start < max_seconds:
        time.sleep(1.0)
        req = urllib.request.Request(f"{BASE_URL}{status_url}")
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            state = data.get("state")
            if state in ("complete", "failure"):
                return data
    raise TimeoutError(f"Run {status_url} timed out after {max_seconds}s")


def get_run_result(result_url: str, session_id: str) -> dict:
    req = urllib.request.Request(
        f"{BASE_URL}{result_url}",
        headers={"X-Sandbox-Session": session_id},
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def request_ai_feedback(run_id: str, session_id: str) -> tuple[dict, float]:
    req = urllib.request.Request(
        f"{BASE_URL}/sandbox/runs/{run_id}/ai-feedback",
        data=b"{}",
        headers={
            "Content-Type": "application/json",
            "X-Sandbox-Session": session_id,
        },
        method="POST",
    )
    t0 = time.time()
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    dt = time.time() - t0
    return data, dt


def run_test_scenario(
    title: str,
    course_id: str,
    assignment_id: str,
    files: dict,
    expected_score: int | list[int] | tuple[int, ...] = None,
    expected_state: str = "complete",
) -> tuple[dict, dict, float]:
    print("\n" + "=" * 70)
    log("SCENARIO", title)
    print("=" * 70)

    zip_bytes = make_zip(files)
    run_meta, session_id = submit_sandbox_run(course_id, assignment_id, zip_bytes)
    run_id = run_meta["run_id"]
    log("SUBMIT", f"Created run {run_id}, session {session_id}")

    status = poll_run(run_meta["status_url"])
    log("POLL", f"Final run state: {status.get('state')}")
    assert status.get("state") == expected_state, (
        f"Expected state {expected_state}, got {status.get('state')} with message: {status.get('message')}"
    )

    result = get_run_result(run_meta["result_url"], session_id)
    score = result.get("projected_score")
    max_score = result.get("max_score")
    log("RESULT", f"Projected Score: {score}/{max_score}")
    if expected_score is not None:
        if isinstance(expected_score, (list, tuple, set)):
            assert score in expected_score, f"Expected score in {expected_score}, got {score}"
        else:
            assert score == expected_score, f"Expected score {expected_score}, got {score}"

    log("AI", "Requesting AI Feedback from Local Model (Gemma 4 12B)...")
    ai_resp, dt = request_ai_feedback(run_id, session_id)

    model = ai_resp.get("model")
    feedback = ai_resp.get("ai_feedback", "")
    log("AI SUCCESS", f"Model: {model} (Response time: {dt:.2f}s)")
    log("AI PREVIEW", feedback[:250].replace("\n", " ") + "...")

    assert len(feedback) > 50, "Feedback should not be empty"
    assert "⚠️ Local AI assistant" not in feedback, "Feedback returned an error fallback"
    return result, ai_resp, dt


def main():
    global BASE_URL
    parser = argparse.ArgumentParser(description="Comprehensive End-to-End Autograder & Local LLM Verification")
    parser.add_argument(
        "--base-url",
        default=os.environ.get("BASE_URL", "http://10.115.20.200/api"),
        help="Base URL for Autograder API (default: http://10.115.20.200/api)",
    )
    args, _ = parser.parse_known_args()
    BASE_URL = args.base_url.rstrip("/")

    print("=" * 70)
    print(f"Starting Comprehensive End-to-End Autograder & Local LLM Verification")
    print(f"Target API Endpoint: {BASE_URL}")
    print("=" * 70)

    summary_results = []

    # ----------------------------------------------------
    # SCENARIO 1: CS 1400 Partial Submission (6/10 points)
    # ----------------------------------------------------
    partial_code = """# Author: Jane Student (ID: U10987654)
# Email: jane.student@uvu.edu

# Declaring two numbers for addition
num1 = 10
num2 = 20

# Incomplete: forgot to calculate sum and print output
"""
    r1, ai1, dt1 = run_test_scenario(
        title="CS 1400 m1-lab1: Partial Submission (6/10 pts) with PII in header",
        course_id="cs1400",
        assignment_id="m1-lab1",
        files={"sum_two_numbers.py": partial_code},
        expected_score=6,
        expected_state="complete",
    )
    # FERPA privacy assertion: student PII in code header must not leak in AI feedback
    assert "U10987654" not in ai1.get("ai_feedback", "")
    assert "jane.student@uvu.edu" not in ai1.get("ai_feedback", "")
    summary_results.append(("CS 1400 m1-lab1 Partial", f"{r1.get('projected_score')}/{r1.get('max_score')}", ai1.get("model"), f"{dt1:.2f}s", "PASS"))

    # ----------------------------------------------------
    # SCENARIO 2: CS 1400 100% Correct Submission (10/10 points)
    # ----------------------------------------------------
    perfect_code = """# Sum of two numbers program
num1 = 10
num2 = 20
total = num1 + num2
print(f"The sum of {num1} and {num2} is {total}.")
"""
    r2, ai2, dt2 = run_test_scenario(
        title="CS 1400 m1-lab1: Perfect Submission (10/10 pts)",
        course_id="cs1400",
        assignment_id="m1-lab1",
        files={"sum_two_numbers.py": perfect_code},
        expected_score=10,
        expected_state="complete",
    )
    summary_results.append(("CS 1400 m1-lab1 Perfect", f"{r2.get('projected_score')}/{r2.get('max_score')}", ai2.get("model"), f"{dt2:.2f}s", "PASS"))

    # ----------------------------------------------------
    # SCENARIO 3: CS 1400 Empty File Submission (Placeholder)
    # ----------------------------------------------------
    r3, ai3, dt3 = run_test_scenario(
        title="CS 1400 m1-lab1: Empty Student File Placeholder",
        course_id="cs1400",
        assignment_id="m1-lab1",
        files={"sum_two_numbers.py": ""},
        expected_score=(0, 2),  # 2/10 in active rubric (0 syntax errors, 0/4 on functionality)
        expected_state="complete",
    )
    summary_results.append(("CS 1400 m1-lab1 Empty", f"{r3.get('projected_score')}/{r3.get('max_score')}", ai3.get("model"), f"{dt3:.2f}s", "PASS"))

    # ----------------------------------------------------
    # SCENARIO 4: CS 1410 Missing Required File Preflight Failure
    # ----------------------------------------------------
    print("\n" + "=" * 70)
    log("SCENARIO", "CS 1410 lab1: Missing Required File (bears2.py)")
    print("=" * 70)
    run_meta, session_id = submit_sandbox_run(
        course_id="cs1410",
        assignment_id="lab1",
        zip_bytes=make_zip({"wrong_file.py": "pass"}),
    )
    status = poll_run(run_meta["status_url"])
    log("STATUS", f"Status message: {status.get('message')}")
    assert status.get("state") == "failure"
    assert "bears2.py" in status.get("message", "")
    log(
        "VALIDATION",
        "Verified: Preflight validation correctly reported missing required file bears2.py",
    )

    ai4, dt4 = request_ai_feedback(run_meta["run_id"], session_id)
    log("AI ON FAILURE", ai4["ai_feedback"][:200].replace("\n", " ") + "...")
    assert (
        "bears2" in ai4["ai_feedback"].lower()
        or "missing" in ai4["ai_feedback"].lower()
        or "file" in ai4["ai_feedback"].lower()
    )
    summary_results.append(("CS 1410 lab1 Preflight Missing File", "0/0 (Failure)", ai4.get("model"), f"{dt4:.2f}s", "PASS"))

    # ----------------------------------------------------
    # SCENARIO 5: CS 1410 Lab 1 with All Required Files & Custom Runtime (Pillow)
    # ----------------------------------------------------
    dummy_jpeg = make_dummy_jpeg()
    bears2_code = """from PIL import Image

filename = 'bears_copy.jpg'
filepath = f"./{filename}"
file_out = 'bears2.jpg'
file_out_path = f"./{file_out}"

orig = Image.open(filepath)
orig.convert("L").save(file_out_path)
"""
    bears3_code = """from PIL import Image

def composite(base, overlay):
    return base
"""
    r5, ai5, dt5 = run_test_scenario(
        title="CS 1410 lab1: All Required Files with Pillow Runtime",
        course_id="cs1410",
        assignment_id="lab1",
        files={
            "bears2.py": bears2_code,
            "bears3.py": bears3_code,
            "bears2.jpg": dummy_jpeg,
            "bears3.jpg": dummy_jpeg,
        },
        expected_score=60,  # 60/100 autograded pytest points (40 pts are manual visual inspection)
        expected_state="complete",
    )
    summary_results.append(("CS 1410 lab1 Custom Pillow Runtime", f"{r5.get('projected_score')}/{r5.get('max_score')}", ai5.get("model"), f"{dt5:.2f}s", "PASS"))

    print("\n" + "=" * 70)
    print("🎉 ALL 5 COMPREHENSIVE END-TO-END PIPELINE SCENARIOS PASSED PERFECTLY!")
    print("=" * 70)
    print(f"\n{'Scenario':<40} {'Score':<15} {'Model':<15} {'Latency':<10} {'Status':<10}")
    print("-" * 90)
    for name, sc, mdl, lat, st in summary_results:
        print(f"{name:<40} {sc:<15} {mdl:<15} {lat:<10} {st:<10}")
    print("=" * 70)


if __name__ == "__main__":
    main()
