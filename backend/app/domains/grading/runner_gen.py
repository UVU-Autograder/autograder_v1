"""Runner script generator for Judge0 pytest execution.

Produces a self-contained Python script string that can be submitted as
``source_code`` to Judge0.  The generated script:

1. Redirects ``sys.stdout`` to a buffer while pytest runs, preventing
   student ``print()`` calls from corrupting the structured output.
2. Uses a lightweight custom pytest plugin (registered via ``pytest.main``'s
   ``plugins`` kwarg) that hooks ``pytest_runtest_makereport`` to collect
   outcomes and ``ag_*`` markers.
3. After the run, restores ``sys.stdout`` and prints a JSON payload preceded
   by a delimiter line so the result parser can reliably locate it.
"""

from __future__ import annotations

import textwrap


def generate_runner_script(test_filenames: list[str]) -> str:
    """Generate the ``runner.py`` source code string.

    The generated script depends only on ``pytest`` (which is pre-installed
    in the Judge0 Python image) and the Python standard library.

    Args:
        test_filenames: List of test file names to pass to ``pytest.main()``,
            e.g. ``["assignment_tests.py"]``.

    Returns:
        A complete, self-contained Python source string ready for Judge0.
    """
    # Serialise the filename list as a Python literal.
    filenames_literal = repr(test_filenames)

    script = textwrap.dedent(
        f"""\
        \"\"\"Auto-generated pytest runner for the autograder sandbox.\"\"\"

        import io
        import json
        import sys
        import time

        import pytest

        # ------------------------------------------------------------------ #
        # Constants                                                          #
        # ------------------------------------------------------------------ #

        RESULTS_DELIMITER = "---AUTOGRADER_RESULTS---"
        TEST_FILENAMES = {filenames_literal}


        # ------------------------------------------------------------------ #
        # Custom pytest plugin                                               #
        # ------------------------------------------------------------------ #

        class AutograderPlugin:
            \"\"\"Collects per-test outcomes and ag_* markers.\"\"\"

            def __init__(self):
                self.results = []
                self._call_outcomes = {{}}

            # We only care about the "call" phase (not setup/teardown).
            def pytest_runtest_makereport(self, item, call):
                if call.when == "call":
                    self._call_outcomes[item.nodeid] = call
                elif call.when == "setup" and call.excinfo is not None:
                    # Setup failure – record so we still report the test.
                    self._call_outcomes.setdefault(item.nodeid, call)

            def pytest_runtest_logreport(self, report):
                if report.when != "call" and not (
                    report.when == "setup" and report.failed
                ):
                    return

                markers = []
                # item.iter_markers is available on the report's node id,
                # but the simplest approach is to parse own_markers from the
                # item stored on the report.
                if hasattr(report, "keywords"):
                    for key in report.keywords:
                        if isinstance(key, str) and key.startswith("ag_"):
                            markers.append(key)

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
                }})


        # ------------------------------------------------------------------ #
        # Main execution                                                     #
        # ------------------------------------------------------------------ #

        def main():
            plugin = AutograderPlugin()

            # Redirect stdout so student prints don't corrupt our JSON output.
            real_stdout = sys.stdout
            captured = io.StringIO()
            sys.stdout = captured

            start = time.monotonic()
            exit_code = pytest.main(
                ["-x", "--tb=short", "-q", "--no-header"] + TEST_FILENAMES,
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
