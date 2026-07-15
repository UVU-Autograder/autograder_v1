import sys
import os
import json
import subprocess
from pathlib import Path
import pytest
from pydantic import ValidationError

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.domains.assignments.schemas import TestItemConfig
from app.domains.sandbox.schemas import SandboxRubricItem
from app.domains.grading.runner_gen import generate_runner_script


def test_test_item_config_validation():
    # 1. Valid config with inputs/outputs
    config = TestItemConfig(
        key="t1",
        label="Test 1",
        points=10,
        extra_credit=False,
        inputs=["2\n3", "4\n5"],
        outputs=["5", "9"],
    )
    assert config.inputs == ["2\n3", "4\n5"]

    # 2. Invalid config with mismatched lengths
    with pytest.raises(ValidationError):
        TestItemConfig(
            key="t2",
            label="Test 2",
            points=10,
            extra_credit=False,
            inputs=["2\n3"],
            outputs=["5", "9"],
        )

    # 3. Invalid config with missing outputs
    with pytest.raises(ValidationError):
        TestItemConfig(
            key="t3",
            label="Test 3",
            points=10,
            extra_credit=False,
            inputs=["2\n3"],
        )


def test_sandbox_rubric_item_fields():
    # SandboxRubricItem can contain inputs/outputs
    item = SandboxRubricItem(
        key="t1",
        label="Test 1",
        points=10,
        extra_credit=False,
        inputs=["2"],
        outputs=["4"],
    )
    assert item.inputs == ["2"]
    assert item.outputs == ["4"]


def test_runner_generation_syntax():
    test_cases = {
        "t1": {
            "inputs": ["1", "2"],
            "outputs": ["2", "4"],
        }
    }
    script = generate_runner_script(["test_main.py"], test_cases, "main")
    assert "TEST_CASES = " in script
    assert "ENTRYPOINT_MODULE = " in script
    assert "pytest_generate_tests" in script
    assert "run_case" in script


def test_runner_execution_passing(tmp_path):
    # 1. Write student entrypoint: main.py
    # Simple addition program
    student_main = tmp_path / "main.py"
    student_main.write_text(
        "a = int(input())\nb = int(input())\nprint(a + b)\n",
        encoding="utf-8"
    )

    # 2. Write pytest file: test_main.py
    test_main = tmp_path / "test_main.py"
    test_main.write_text(
        "import pytest\n"
        "@pytest.mark.ag_t1\n"
        "def test_add(case_input, case_output, run_case):\n"
        "    run_case()\n",
        encoding="utf-8"
    )

    # 3. Generate runner.py
    test_cases = {
        "t1": {
            "inputs": ["2\n3", "10\n20"],
            "outputs": ["5", "30"],
        }
    }
    runner_code = generate_runner_script(["test_main.py"], test_cases, "main")
    runner_file = tmp_path / "runner.py"
    runner_file.write_text(runner_code, encoding="utf-8")

    # 4. Run runner.py in subprocess
    env = dict(os.environ)
    env["PYTHONPATH"] = str(tmp_path)
    result = subprocess.run(
        [sys.executable, str(runner_file)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 0
    assert "---AUTOGRADER_RESULTS---" in result.stdout
    _, _, json_part = result.stdout.partition("---AUTOGRADER_RESULTS---")

    outcomes = json.loads(json_part.strip())
    assert outcomes["summary"]["total"] == 2
    assert outcomes["summary"]["passed"] == 2
    assert outcomes["summary"]["failed"] == 0
    
    # Check individual outcomes
    tests = outcomes["tests"]
    assert len(tests) == 2
    assert tests[0]["outcome"] == "passed"
    assert "ag_t1" in tests[0]["markers"]
    assert tests[1]["outcome"] == "passed"


def test_runner_execution_failing(tmp_path):
    # 1. Write student entrypoint: main.py
    # Buggy student program that prints wrong values
    student_main = tmp_path / "main.py"
    student_main.write_text(
        "a = int(input())\nb = int(input())\nprint(a - b)\n",  # Bug here: subtracts instead of adds
        encoding="utf-8"
    )

    # 2. Write pytest file: test_main.py
    test_main = tmp_path / "test_main.py"
    test_main.write_text(
        "import pytest\n"
        "@pytest.mark.ag_t1\n"
        "def test_add(case_input, case_output, run_case):\n"
        "    run_case()\n",
        encoding="utf-8"
    )

    # 3. Generate runner.py
    test_cases = {
        "t1": {
            "inputs": ["5\n3", "10\n4"],
            "outputs": ["8", "14"],
        }
    }
    runner_code = generate_runner_script(["test_main.py"], test_cases, "main")
    runner_file = tmp_path / "runner.py"
    runner_file.write_text(runner_code, encoding="utf-8")

    # 4. Run runner.py in subprocess
    env = dict(os.environ)
    env["PYTHONPATH"] = str(tmp_path)
    result = subprocess.run(
        [sys.executable, str(runner_file)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=env,
    )

    # Note: exit_code may be non-zero since a test failed, but runner prints results json
    assert "---AUTOGRADER_RESULTS---" in result.stdout
    _, _, json_part = result.stdout.partition("---AUTOGRADER_RESULTS---")

    outcomes = json.loads(json_part.strip())
    assert outcomes["summary"]["total"] == 2
    assert outcomes["summary"]["passed"] == 0
    assert outcomes["summary"]["failed"] == 2
    
    tests = outcomes["tests"]
    assert len(tests) == 2
    assert tests[0]["outcome"] == "failed"
    assert "AssertionError" in tests[0]["message"]
    assert tests[1]["outcome"] == "failed"
    assert "AssertionError" in tests[1]["message"]
    assert tests[0]["actual"].strip() == "2"
    assert tests[0]["expected"].strip() == "8"
