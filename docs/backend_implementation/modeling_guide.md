# UVU Autograder — Assignment Modeling Guide

This guide establishes the standard patterns, structures, and guidelines for modeling and seeding CS 1410 course assignments. Follow these specifications to maintain consistency across the entire course modeling cycle.

---

## 1. Directory Structure of a Seed Package

Every assignment is modeled as a package directory under `backend/app/db/seeds/<assignment_slug>/`. 

A complete seed directory must contain the following files:

```
backend/app/db/seeds/<assignment_slug>/
├── config_json.example.json   # Assignment configuration (schema v1)
├── tests.py                   # Pytest suite run by the instructor against student code
├── <model_solution_file>.py   # Instructor's reference solution (e.g. dessert.py)
└── [additional files]         # Entrypoints (e.g. dessertshop.py) or resources (data files)
```

---

## 2. Anatomy of `config_json.example.json`

The configuration file defines the execution boundary, scoring rubric, and file expectations.

```json
{
  "schema_version": 1,
  "bundle": {
    "required_files": [
      "dessert.py",
      "dessertshop.py"
    ],
    "entrypoint": "dessertshop.py",
    "file_requirements": [
      {
        "key": "dessert_py",
        "label": "Dessert Shop classes definition file",
        "requirement_type": "exact",
        "paths": ["dessert.py"]
      }
    ]
  },
  "execution": {
    "dependencies": []
  },
  "artifacts": {
    "assignment_tests": {
      "type": "pytest_file",
      "display_filename": "tests.py"
    },
    "model_solution": {
      "type": "model_solution",
      "display_filename": "dessert.py"
    },
    "data_file": {
      "type": "input_file",
      "display_filename": "data.txt"
    }
  },
  "tests": [
    {
      "key": "ds1_regression",
      "label": "DS1 class hierarchy intact",
      "points": 20,
      "extra_credit": false
    }
  ],
  "manual_rubric_items": [],
  "completion_requirements": [],
  "stdin_scenarios": []
}
```

### Key Sections:

*   **`bundle`**:
    *   `required_files`: List of files that *must* exist in the student's submission.
    *   `entrypoint`: The python file executed by the sandbox runner.
    *   `file_requirements`: Rules applied by the preflight check. `requirement_type` can be `"exact"` or `"glob"`.
*   **`artifacts`**:
    *   `pytest_file`: The instructor's tests file. Display filename *must* be `"tests.py"`.
    *   `model_solution`: The instructor's model solution. Display filename *must* match the student's expected source file (e.g., `"dessert.py"`). *Note: The grading service automatically skips copying this file to the student execution workspace to avoid overwriting student code.*
    *   `input_file`: Static asset files (e.g., CSV/TXT data files) injected into the sandbox CWD prior to execution.
*   **`tests`**:
    *   An array of scoring items. Each scoring item maps directly to a pytest marker `@pytest.mark.ag_<key>`.

---

## 3. Instructor Pytest (`tests.py`) Standards

The instructor test file is run inside the Judge0 sandbox using a custom runner. Follow these guidelines:

### A. Marker Decoration
Every test function must be decorated with a marker matching the `key` defined in `config_json.example.json`:
```python
import pytest

@pytest.mark.ag_ds1_regression
def test_something():
    assert True
```

### B. Safe Imports
Wrap imports of student code in `try/except` blocks to provide clear feedback if the student failed to define classes or files:
```python
try:
    from dessert import DessertItem, Candy, Order
except ImportError as exc:
    raise AssertionError(f"Could not import required classes: {exc}")
```

### C. Execution Verification (stdout capturing)
If the assignment requires output validation (e.g., checking a printed receipt), redirect `sys.stdout` and run the script using `runpy`:
```python
import io
import sys
import runpy

def test_main_output():
    stdout_buf = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = stdout_buf
    try:
        runpy.run_path("dessertshop.py", run_name="__main__")
    except Exception as exc:
        raise AssertionError(f"dessertshop.py execution failed: {exc}")
    finally:
        sys.stdout = old_stdout

    output = stdout_buf.getvalue()
    assert "Expected String" in output
```

---

## 4. AST Concept Whitelisting

The AST concept checker validates student source code against allowed syntax concepts.

*   **Cumulative Whitelist:** The effective concepts whitelisted for a run are `course.default_concepts ∪ assignment.module.concepts`.
*   **Module Mapping:** Concepts are defined in `seed.py` on the `Module` entity, mimicking the progression of learning objectives.
*   **Exception handling in AST Checker:** Certain keywords (like `raise StopIteration` in iterators) are exceptions to broad concepts (like `exceptions`) and are explicitly ignored by the validator in [validator.py](../../backend/app/integrations/ast_checker/validator.py) to avoid premature syntax blockers.

---

## 5. Custom Student Test Verification (e.g. DS3)

When assignments require students to author their own unit tests:

1.  **AST Verification:** Parse the student's test file (e.g., `test_dessert.py`) using `ast` in the instructor test suite to ensure they wrote the required number of test functions starting with `test_`:
    ```python
    import ast
    with open("test_dessert.py", "r", encoding="utf-8") as f:
        tree = ast.parse(f.read())
    funcs = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")]
    assert len(funcs) >= 15
    ```
2.  **Execution Verification:** Run the student's pytest file in-process using `pytest.main()`, passing a custom counter plugin to count successful assertions and ensure zero failures:
    ```python
    class StudentTestCounter:
        def __init__(self):
            self.passed_count = 0
            self.failed_count = 0
        def pytest_runtest_logreport(self, report):
            if report.when == "call":
                if report.outcome == "passed":
                    self.passed_count += 1
                elif report.outcome == "failed":
                    self.failed_count += 1

    counter = StudentTestCounter()
    exit_code = pytest.main(["-q", "test_dessert.py"], plugins=[counter])
    assert exit_code == 0
    assert counter.passed_count >= 15
    ```
