"""Runner script generator for Judge0 pytest execution.

Produces a self-contained Python script string that can be submitted as
``source_code`` to Judge0.  The generated script:

1. Redirects ``sys.stdout`` to a buffer while pytest runs, preventing
   student ``print() !!`` calls from corrupting the structured output.
2. Uses a lightweight custom pytest plugin (registered via ``pytest.main``'s
   ``plugins`` kwarg) that hooks ``pytest_runtest_makereport`` to collect
   outcomes and ``ag_*`` markers.
3. Automatically parametrizes tests using `pytest_generate_tests` if they match
   the configured input/output test cases.
4. Exposes a `run_case` fixture to mock stdin/stdout dynamically.
5. After the run, restores ``sys.stdout`` and prints a JSON payload preceded
   by a delimiter line so the result parser can reliably locate it.
"""

from __future__ import annotations

import textwrap


def generate_runner_script(
    test_filenames: list[str],
    test_cases: dict[str, dict[str, list[str]]],
    entrypoint_module: str,
    dependencies: list[str] | None = None,
) -> str:
    """Generate the ``runner.py`` source code string.

    The generated script depends only on ``pytest`` (which is pre-installed
    in the Judge0 Python image) and the Python standard library.

    Args:
        test_filenames: List of test file names to pass to ``pytest.main()``,
            e.g. ``["assignment_tests.py"]``.
        test_cases: Dict mapping test marker keys (e.g. "t1") to their inputs
            and outputs.
        entrypoint_module: Stem of the student entrypoint file, e.g. "main".
        dependencies: Preinstalled packages the assignment requires.

    Returns:
        A complete, self-contained Python source string ready for Judge0.
    """
    filenames_literal = repr(test_filenames)
    test_cases_literal = repr(test_cases)
    entrypoint_literal = repr(entrypoint_module)
    dependencies_literal = repr(dependencies or [])
    joiner = '"\\n"'

    script = textwrap.dedent(
        f"""\
        \"\"\"Auto-generated pytest runner for the autograder sandbox.\"\"\"

        import io
        import importlib
        import json
        import os
        import sys
        import time
        import signal

        # ------------------------------------------------------------------ #
        # Constants & Signal Setup                                           #
        # ------------------------------------------------------------------ #

        RESULTS_DELIMITER = "---AUTOGRADER_RESULTS---"
        TEST_FILENAMES = {filenames_literal}
        TEST_CASES = {test_cases_literal}
        ENTRYPOINT_MODULE = {entrypoint_literal}
        DEPENDENCIES = {dependencies_literal}
        DEPENDENCY_IMPORTS = {{"pillow": "PIL"}}

        def runtime_failure(message: str) -> None:
            payload = {{
                "tests": [],
                "summary": {{
                    "total": 0,
                    "passed": 0,
                    "failed": 0,
                    "errors": 1,
                    "duration": 0.0,
                    "exit_code": 2,
                }},
                "infrastructure_error": message,
            }}
            print(RESULTS_DELIMITER)
            print(json.dumps(payload))
            raise SystemExit(0)

        if sys.version_info < (3, 11):
            runtime_failure(
                "Judge0 Python 3.11+ is required; found "
                + ".".join(str(part) for part in sys.version_info[:3])
            )

        for dependency in DEPENDENCIES:
            import_name = DEPENDENCY_IMPORTS.get(dependency.lower(), dependency)
            try:
                importlib.import_module(import_name)
            except ImportError:
                runtime_failure(
                    f"Required preinstalled dependency '{{dependency}}' is unavailable."
                )

        import pytest

        class TimeoutException(Exception):
            pass

        def timeout_handler(signum: int, frame: object) -> None:
            raise TimeoutException("Test case execution timed out (5s limit).")


        # ------------------------------------------------------------------ #
        # Custom pytest plugin                                               #
        # ------------------------------------------------------------------ #

        class AutograderPlugin:
            \"\"\"Collects per-test outcomes, markers, hooks, and fixtures.\"\"\"

            def __init__(self):
                self.results = []

            def pytest_runtest_setup(self, item: pytest.Item) -> None:
                if hasattr(signal, "alarm"):
                    signal.signal(signal.SIGALRM, timeout_handler)
                    signal.alarm(5)
                
                # Check for EXPECTED_OUTPUT / EXPECTED_INPUT on item.obj or item.module
                obj = getattr(item, "obj", None)
                mod = getattr(item, "module", None)
                exp = getattr(obj, "EXPECTED_OUTPUT", None)
                if exp is None and mod is not None:
                    exp = getattr(mod, "EXPECTED_OUTPUT", None)
                if exp is None:
                    exp = getattr(obj, "EXPECTED", None)
                if exp is not None:
                    item.user_properties.append(("expected", str(exp)))

                inp = getattr(obj, "EXPECTED_INPUT", None)
                if inp is None and mod is not None:
                    inp = getattr(mod, "EXPECTED_INPUT", None)
                if inp is None:
                    inp = getattr(obj, "INPUT", None)
                if inp is not None:
                    item.user_properties.append(("expected_input", str(inp)))

            def pytest_runtest_teardown(self, item: pytest.Item) -> None:
                if hasattr(signal, "alarm"):
                    signal.alarm(0)

            def pytest_generate_tests(self, metafunc):
                marker_key = None
                if hasattr(metafunc, "definition") and hasattr(metafunc.definition, "own_markers"):
                    for marker in metafunc.definition.own_markers:
                        if marker.name.startswith("ag_"):
                            marker_key = marker.name[3:]
                            break
                if marker_key and marker_key in TEST_CASES:
                    case_data = TEST_CASES[marker_key]
                    inputs = case_data.get("inputs") or []
                    outputs = case_data.get("outputs") or []
                    if inputs and outputs:
                        metafunc.parametrize("case_input,case_output", list(zip(inputs, outputs)))

            @pytest.fixture
            def run_case(self, monkeypatch, capsys, request):
                case_input = None
                case_output = None
                if hasattr(request.node, "callspec") and request.node.callspec is not None:
                    case_input = request.node.callspec.params.get("case_input")
                    case_output = request.node.callspec.params.get("case_output")
                    
                def _run():
                    if case_input is None or case_output is None:
                        pytest.fail("Test case parameters 'case_input' or 'case_output' are missing.")
                    
                    import io
                    import sys
                    import importlib
                    
                    # 1. Mock stdin
                    monkeypatch.setattr('sys.stdin', io.StringIO(case_input))
                    
                    # 2. Import / Reload student entrypoint
                    if ENTRYPOINT_MODULE in sys.modules:
                        importlib.reload(sys.modules[ENTRYPOINT_MODULE])
                    else:
                        importlib.import_module(ENTRYPOINT_MODULE)
                        
                    # 3. Capture stdout
                    captured = capsys.readouterr()
                    actual = captured.out
                    
                    # 4. Compare with whitespace normalization
                    def normalize(s):
                        return {joiner}.join(line.strip() for line in s.splitlines() if line.strip())
                        
                    try:
                        assert normalize(actual) == normalize(case_output)
                    except AssertionError as e:
                        request.node.user_properties.append(("actual", actual))
                        request.node.user_properties.append(("expected", case_output))
                        raise e
                    
                return _run

            def pytest_runtest_logreport(self, report):
                if report.when != "call" and not (
                    report.when == "setup" and report.failed
                ):
                    return

                markers = []
                if hasattr(report, "keywords"):
                    for key in report.keywords:
                        if isinstance(key, str) and key.startswith("ag_"):
                            markers.append(key)

                actual = None
                expected = None
                expected_input = None
                if hasattr(report, "user_properties"):
                    props = dict(report.user_properties)
                    actual = props.get("actual")
                    expected = props.get("expected")
                    expected_input = props.get("expected_input")

                if actual is None and hasattr(report, "sections"):
                    for sec_name, sec_text in report.sections:
                        if "stdout" in sec_name.lower():
                            actual = sec_text
                            break

                message = None
                if report.failed:
                    longrepr = str(report.longrepr) if report.longrepr else None
                    if longrepr and len(longrepr) > 2000:
                        longrepr = longrepr[:1997] + "..."
                    message = longrepr

                self.results.append({{
                    "nodeid": report.nodeid,
                    "outcome": report.outcome,
                    "markers": sorted(markers),
                    "duration": round(report.duration, 6),
                    "message": message,
                    "actual": actual,
                    "expected": expected,
                    "expected_input": expected_input,
                }})


        # ------------------------------------------------------------------ #
        # Main execution                                                     #
        # ------------------------------------------------------------------ #

        def main():
            os.environ["SDL_VIDEODRIVER"] = "dummy"
            os.environ["SDL_AUDIODRIVER"] = "dummy"

            plugin = AutograderPlugin()

            # Redirect stdout so student prints don't corrupt our JSON output.
            real_stdout = sys.stdout
            captured = io.StringIO()
            sys.stdout = captured

            start = time.monotonic()
            exit_code = pytest.main(
                ["--tb=short", "-q", "--no-header"] + TEST_FILENAMES,
                plugins=[plugin],
            )
            elapsed = round(time.monotonic() - start, 6)

            # Restore stdout before we print our results.
            sys.stdout = real_stdout

            passed = sum(1 for r in plugin.results if r["outcome"] == "passed")
            failed = sum(1 for r in plugin.results if r["outcome"] == "failed")
            errors = sum(1 for r in plugin.results if r["outcome"] == "error")

            payload = {{
                "tests": plugin.results,
                "summary": {{
                    "total": len(plugin.results),
                    "passed": passed,
                    "failed": failed,
                    "errors": errors,
                    "duration": elapsed,
                    "exit_code": int(exit_code),
                }},
            }}

            print(RESULTS_DELIMITER)
            print(json.dumps(payload))


        if __name__ == "__main__":
            main()
        """
    )

    return script
