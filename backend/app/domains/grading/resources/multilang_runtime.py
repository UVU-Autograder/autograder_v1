"""Guest-only supervisor for native and DOM tests; never execute submissions on the API host."""
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import tempfile
import threading
import time
import xml.etree.ElementTree as ET

LIMIT = 65536
REPORT_LIMIT = 1024 * 1024
compare_outputs = globals()["compare_outputs"]
WEB_RUNNER_SOURCE = globals()["WEB_RUNNER_SOURCE"]
ROOT = Path.cwd().resolve()
CONFIG = json.loads((ROOT / "ag_config.json").read_text())


def run(command, *, stdin="", timeout=30):
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, start_new_session=True)
    buffers = [bytearray(), bytearray()]
    overflow = [False, False]

    def stop():
        # killpg/SIGKILL exist only on POSIX guests; resolve them dynamically.
        killpg = getattr(os, "killpg", None)
        sigkill = getattr(signal, "SIGKILL", None)
        try:
            if killpg is None or sigkill is None:
                raise AttributeError("killpg")
            killpg(process.pid, sigkill)
        except (ProcessLookupError, AttributeError):
            process.kill()

    def drain(index, stream):
        while chunk := stream.read(4096):
            remaining = max(0, LIMIT - len(buffers[index]))
            buffers[index].extend(chunk[:remaining])
            if len(chunk) > remaining:
                overflow[index] = True
                stop()

    readers = [threading.Thread(target=drain, args=(i, stream), daemon=True)
               for i, stream in enumerate((process.stdout, process.stderr))]
    for reader in readers:
        reader.start()
    assert process.stdin is not None  # stdin=PIPE above
    try:
        process.stdin.write(stdin.encode())
        process.stdin.close()
    except BrokenPipeError:
        pass
    timed_out = False
    try:
        process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        stop()
        process.wait()
    finally:
        # Descendants must not keep capture pipes or processes alive after a case.
        stop()
        for reader in readers:
            reader.join(timeout=2)
    return {"stdout": buffers[0].decode("utf-8", errors="replace"),
            "stderr": buffers[1].decode("utf-8", errors="replace"),
            "exit_code": process.returncode, "timeout": timed_out,
            "stdout_truncated": overflow[0], "stderr_truncated": overflow[1]}


def compile_native():
    tests = set(CONFIG["test_files"])
    sources = sorted(p for p in ROOT.rglob("*") if p.suffix in {".c", ".cpp", ".cc", ".cxx"})
    objects = []
    for source in sources:
        relative = source.relative_to(ROOT).as_posix()
        output = "ag_object_" + hashlib.sha256(relative.encode()).hexdigest()[:16] + ".o"
        is_c = source.suffix == ".c"
        command = ["gcc-8" if is_c else "g++-8", "-std=c11" if is_c else "-std=c++17",
                   "-Wall", "-Wextra", "-O2", "-I.", "-I/usr/local/include", "-c", relative, "-o", output]
        if CONFIG["framework"] == "gtest" and relative not in tests and relative == CONFIG["entrypoint"]:
            command.insert(1, "-Dmain=autograder_student_main")
        result = run(command)
        if result["exit_code"] != 0 or result["timeout"] or result["stdout_truncated"] or result["stderr_truncated"]:
            sys.stderr.write(result["stdout"] + result["stderr"])
            return 1
        objects.append(output)
    if not objects:
        sys.stderr.write("No native source files were found.\n")
        return 1
    command = ["g++-8" if CONFIG["framework"] == "gtest" or CONFIG["language"] == "cpp" else "gcc-8",
               *objects, "-o", "ag_program"]
    if CONFIG["framework"] == "gtest":
        command.extend(["-L/usr/local/lib", "-lgtest_main", "-lgtest", "-pthread"])
    result = run(command)
    sys.stderr.write(result["stdout"] + result["stderr"])
    return 0 if result["exit_code"] == 0 and not any(result[k] for k in ("timeout", "stdout_truncated", "stderr_truncated")) else 1


def case(nodeid, key, **values):
    return {"nodeid": nodeid, "markers": ["ag_" + key], "xfail": False, **values}


def io_tests():
    collected, results = [], []
    for item in CONFIG["items"]:
        if item["item_type"] == "manual":
            continue
        for index, (given, expected) in enumerate(zip(item["inputs"], item["outputs"])):
            entry = case(f"io::{item['key']}[{index}]", item["key"])
            collected.append(entry)
            start = time.monotonic()
            raw = run([str(ROOT / "ag_program")], stdin=given, timeout=5)
            if raw["timeout"] or raw["exit_code"] not in (0,) or raw["stdout_truncated"] or raw["stderr_truncated"]:
                raise RuntimeError("Native program stopped, timed out, or exceeded the output limit.")
            passed = compare_outputs(raw["stdout"], expected, item["comparison_mode"], item["tolerance"])
            results.append({**entry, "outcome": "passed" if passed else "failed",
                            "duration": time.monotonic() - start,
                            "actual": raw["stdout"], "expected": expected, "expected_input": given,
                            "message": None if passed else "Output did not match the expected value."})
    return collected, results


def gtest_tests(directory):
    listing = run([str(ROOT / "ag_program"), "--gtest_list_tests"])
    if listing["exit_code"] != 0 or listing["timeout"] or listing["stdout_truncated"]:
        raise RuntimeError("GoogleTest discovery failed.")
    collected = []
    suite = ""
    for line in listing["stdout"].splitlines():
        name = line.split("#", 1)[0].strip()
        if not name:
            continue
        if not line[0].isspace():
            suite = name.rstrip(".")
            continue
        match = re.fullmatch(r"(?:DISABLED_)?ag_([a-z][a-z0-9_]*)(?:/\d+)?", name)
        if match is None:
            raise RuntimeError("GoogleTest names must use ag_<rubric_key>.")
        entry = case(suite + "." + name, match[1])
        if "DISABLED_" in name or "DISABLED_" in suite:
            entry["xfail"] = True
        collected.append(entry)
    destination = directory / "gtest.xml"
    raw = run([str(ROOT / "ag_program"), "--gtest_output=xml:" + str(destination)])
    if raw["exit_code"] not in (0, 1) or raw["timeout"] or raw["stdout_truncated"] or raw["stderr_truncated"]:
        raise RuntimeError("GoogleTest execution did not complete.")
    if not destination.is_file() or destination.stat().st_size > REPORT_LIMIT:
        raise RuntimeError("GoogleTest report is missing or too large.")
    inventory = {entry["nodeid"]: entry for entry in collected}
    results = []
    for result in ET.parse(destination).getroot().iter("testcase"):
        nodeid = result.attrib.get("classname", "") + "." + result.attrib.get("name", "")
        if nodeid not in inventory:
            raise RuntimeError("GoogleTest report membership mismatch.")
        failures = result.findall("failure")
        skipped = result.attrib.get("status") == "notrun" or result.find("skipped") is not None
        results.append({**inventory[nodeid], "outcome": "skipped" if skipped else "failed" if failures else "passed",
                        "duration": float(result.attrib.get("time", "0")),
                        "message": "\n".join(f.attrib.get("message", "Assertion failed") for f in failures)[:2000] or None})
    return collected, results


def main():
    if len(sys.argv) == 2 and sys.argv[1] == "--compile":
        return compile_native()
    start = time.monotonic()
    collected, tests = [], []
    error = None
    try:
        with tempfile.TemporaryDirectory(prefix=".ag_report_") as directory:
            if CONFIG["framework"] == "io":
                collected, tests = io_tests()
            elif CONFIG["framework"] == "gtest":
                collected, tests = gtest_tests(Path(directory))
            else:
                (ROOT / "ag_web_runner.cjs").write_text(WEB_RUNNER_SOURCE)
                destination = Path(directory) / "web.json"
                raw = run(["/opt/autograder/node/bin/node", "ag_web_runner.cjs", str(destination)])
                if raw["exit_code"] not in (0, 1) or raw["timeout"] or raw["stdout_truncated"] or raw["stderr_truncated"]:
                    raise RuntimeError("Web runner did not complete.")
                if not destination.is_file() or destination.stat().st_size > REPORT_LIMIT:
                    raise RuntimeError("Web runner report is missing or too large.")
                data = json.loads(destination.read_text())
                collected, tests = data["collected"], data["tests"]
        if not collected or len(collected) > 512:
            raise RuntimeError("Expected between 1 and 512 test cases.")
        markers = {"ag_" + item["key"] for item in CONFIG["items"] if item["item_type"] != "manual"}
        if markers != {marker for entry in collected for marker in entry["markers"]}:
            raise RuntimeError("Test cases do not match the automated rubric keys.")
    except Exception as exc:
        error = (type(exc).__name__ + ": " + str(exc))[:2000]
        collected, tests = [], []
    completed = error is None
    counts = {key: sum(t["outcome"] == key for t in tests) for key in ("passed", "failed", "error", "skipped")}
    exit_code = 3 if error else 1 if counts["failed"] or counts["error"] or counts["skipped"] else 0
    payload = {"protocol_version": 2, "collected": collected, "tests": tests, "completed": completed,
               "summary": {"total": len(tests), **{k: counts[v] for k, v in
                           (("passed", "passed"), ("failed", "failed"), ("errors", "error"), ("skipped", "skipped"))},
                           "duration": time.monotonic() - start, "exit_code": exit_code},
               "diagnostics": {}, "infrastructure_error": error}
    encoded = json.dumps(payload, allow_nan=False)
    if len(encoded.encode()) > REPORT_LIMIT:
        raise RuntimeError("Grading report exceeds its limit.")
    print(encoded)
    return 0  # The complete envelope, rather than stdout text or process status, owns case outcomes.


if __name__ == "__main__":
    sys.exit(main())
