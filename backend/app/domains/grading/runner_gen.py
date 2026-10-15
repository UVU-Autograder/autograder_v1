"""Generate a self-contained supervised pytest runner for Judge0 and local checks."""
import functools
from pathlib import Path


@functools.lru_cache(maxsize=1)
def _load_pytest_runtime() -> str:
    return Path(__file__).with_name("resources").joinpath("pytest_runtime.py").read_text(encoding="utf-8")


def generate_runner_script(
    test_filenames: list[str],
    test_cases: dict[str, dict[str, list[str]]],
    entrypoint_module: str,
    dependencies: list[str] | None = None,
) -> str:
    runtime = _load_pytest_runtime()
    return (f"TEST_FILENAMES = {test_filenames!r}\nTEST_CASES = {test_cases!r}\n"
            f"ENTRYPOINT_MODULE = {entrypoint_module!r}\nDEPENDENCIES = {dependencies or []!r}\n" + runtime)
