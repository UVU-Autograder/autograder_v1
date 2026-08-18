#!/usr/bin/env python3
"""Comprehensive End-to-End Pipeline Verification Script.
Tests:
1. CS 1400: Partial submission (5/25) -> Tests report -> Socratic AI feedback
2. CS 1400: Perfect submission (25/25) -> Full score -> Congratulatory AI feedback
3. CS 1400: Empty file submission -> 0 score -> Actionable Socratic AI hints
4. CS 1410: Missing required file preflight validation -> Clear error message -> AI feedback
5. CS 1410: Lab 1 with all required files & custom runtime -> Complete state & AI feedback
"""

import io
import json
import time
import urllib.request
import urllib.error
import zipfile
from PIL import Image

BASE_URL = "http://127.0.0.1:8000"


def log(section, msg):
    print(f"[{section}] {msg}")


def make_zip(file_dict: dict[str, str | bytes]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for fname, content in file_dict.items():
            if isinstance(content, str):
                zf.writestr(fname, content)
            else:
                zf.writestr(fname, content)
    return buf.getvalue()


def make_dummy_jpeg() -> bytes:
    img = Image.new("RGB", (10, 10), color="blue")
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


def poll_run(status_url: str, max_seconds: int = 25) -> dict:
    start = time.time()
    while time.time() - start < max_seconds:
        time.sleep(0.8)
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


def request_ai_feedback(run_id: str, session_id: str) -> dict:
    req = urllib.request.Request(
        f"{BASE_URL}/sandbox/runs/{run_id}/ai-feedback",
        data=b"{}",
        headers={
            "Content-Type": "application/json",
            "X-Sandbox-Session": session_id,
        },
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def run_test_scenario(
    title: str,
    course_id: str,
    assignment_id: str,
    files: dict,
    expected_score: int = None,
    expected_state: str = "complete",
):
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
        assert score == expected_score, f"Expected score {expected_score}, got {score}"

    log("AI", "Requesting AI Feedback from Local Model...")
    t0 = time.time()
    ai_resp = request_ai_feedback(run_id, session_id)
    dt = time.time() - t0

    model = ai_resp.get("model")
    feedback = ai_resp.get("ai_feedback", "")
    log("AI SUCCESS", f"Model: {model} (Response time: {dt:.2f}s)")
    log("AI PREVIEW", feedback[:250].replace("\n", " ") + "...")

    assert len(feedback) > 50, "Feedback should not be empty"
    assert "⚠️ Local AI assistant" not in feedback, "Feedback returned an error fallback"
    return result, ai_resp


def main():
    print("Starting Comprehensive End-to-End Autograder & Local LLM Verification...")

    # ----------------------------------------------------
    # SCENARIO 1: CS 1400 Partial Submission (5/25 points)
    # ----------------------------------------------------
    partial_code = """
# Author: Jane Student (ID: U10987654)
# Email: jane.student@uvu.edu

def add_numbers(a, b):
    return a + b

def reverse_words(sentence):
    # Intentional bug: reverse entire sentence instead of words
    return sentence[::-1]

def count_vowels(text):
    # Incomplete
    return 0
"""
    run_test_scenario(
        title="CS 1400: Partial Submission (5/25 pts) with PII in header",
        course_id="cs1400",
        assignment_id="simple-python-functions",
        files={"student_functions.py": partial_code},
        expected_score=5,
        expected_state="complete",
    )

    # ----------------------------------------------------
    # SCENARIO 2: CS 1400 100% Correct Submission (25/25 points)
    # ----------------------------------------------------
    perfect_code = """
def add_numbers(a, b):
    return a + b

def reverse_words(sentence):
    return " ".join(word[::-1] for word in sentence.split(" "))

def count_vowels(text):
    return sum(1 for ch in text.lower() if ch in "aeiou")
"""
    run_test_scenario(
        title="CS 1400: Perfect Submission (25/25 pts)",
        course_id="cs1400",
        assignment_id="simple-python-functions",
        files={"student_functions.py": perfect_code},
        expected_score=25,
        expected_state="complete",
    )

    # ----------------------------------------------------
    # SCENARIO 3: CS 1400 Empty File Submission (0/25 points)
    # ----------------------------------------------------
    run_test_scenario(
        title="CS 1400: Empty Student File (0/25 pts)",
        course_id="cs1400",
        assignment_id="simple-python-functions",
        files={"student_functions.py": "# empty file\n"},
        expected_score=0,
        expected_state="complete",
    )

    # ----------------------------------------------------
    # SCENARIO 4: CS 1410 Missing Required File Preflight Failure
    # ----------------------------------------------------
    print("\n" + "=" * 70)
    log("SCENARIO", "CS 1410 Lab 1: Missing Required File (bears2.py)")
    print("=" * 70)
    run_meta, session_id = submit_sandbox_run(
        course_id="cs1410",
        assignment_id="lab-1-image-processing",
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

    ai_resp = request_ai_feedback(run_meta["run_id"], session_id)
    log("AI ON FAILURE", ai_resp["ai_feedback"][:200].replace("\n", " ") + "...")
    assert (
        "bears2" in ai_resp["ai_feedback"].lower()
        or "missing" in ai_resp["ai_feedback"].lower()
        or "file" in ai_resp["ai_feedback"].lower()
    )

    # ----------------------------------------------------
    # SCENARIO 5: CS 1410 Lab 1 with All Required Files & Custom Runtime (Pillow/Pygame)
    # ----------------------------------------------------
    dummy_jpeg = make_dummy_jpeg()
    bears2_code = """
from PIL import Image

def load_image(filepath):
    return Image.open(filepath)

def grayscale(image):
    return image.convert("L")

def negative(image):
    return image
"""
    bears3_code = """
from PIL import Image

def composite(base, overlay):
    return base
"""
    run_test_scenario(
        title="CS 1410 Lab 1: All Required Files with Pillow Runtime",
        course_id="cs1410",
        assignment_id="lab-1-image-processing",
        files={
            "bears2.py": bears2_code,
            "bears3.py": bears3_code,
            "bears2.jpg": dummy_jpeg,
            "bears3.jpg": dummy_jpeg,
        },
        expected_state="complete",
    )

    print("\n" + "=" * 70)
    print("🎉 ALL 5 COMPREHENSIVE END-TO-END PIPELINE SCENARIOS PASSED PERFECTLY!")
    print("=" * 70)


if __name__ == "__main__":
    main()
