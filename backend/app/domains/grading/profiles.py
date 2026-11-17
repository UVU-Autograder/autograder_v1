"""Runtime identities shared by admission, frozen packages and report validation."""
from typing import Literal

Language = Literal["python", "c", "cpp", "web"]
Framework = Literal["pytest", "io", "gtest", "jsdom"]
PYTHON_RUNTIME_ID = "python-3.11.9-pytest-8.4.2-report-2"
NATIVE_RUNTIME_ID = "gcc-8.3.0-gtest-1.17.0-adapter-1-report-2"
WEB_RUNTIME_ID = "node-24.22.3-jsdom-29.1.1-esbuild-0.28.2-adapter-1-report-2"


def runtime_id(language: str) -> str:
    return {"python": PYTHON_RUNTIME_ID, "c": NATIVE_RUNTIME_ID,
            "cpp": NATIVE_RUNTIME_ID, "web": WEB_RUNTIME_ID}[language]
