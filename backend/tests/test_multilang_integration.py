"""Regression tests for the multi-language (C/C++/web) grading plan.

Covers language/framework validation, the native Judge0 payload, nonzero-exit
reports, execution fingerprints, structured GoogleTest results, package v3 and
the Python suite synchronization route. Judge0 is always mocked.
"""
from __future__ import annotations

import base64
import copy
import io
import json
import shutil
import subprocess
import zipfile
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from pydantic import ValidationError


from app.db.base import import_domain_models
from app.db.session import SessionLocal
from app.domains.assignments import inventory
from app.domains.assignments.inventory import execution_fingerprint, inventory_status
from app.domains.assignments.schemas import AssignmentConfigV1
from app.domains.assignments.service import get_assignment_for_course
from app.domains.grading import multilang
from app.domains.grading.executor import execute_pytest_in_judge0
from app.domains.grading.multilang import RESERVED, adapter_source, parse_execution, prepare_bundle
from app.domains.grading.pipeline import GradingPipeline, SubmissionPayload
from app.domains.grading.profiles import NATIVE_RUNTIME_ID, PYTHON_RUNTIME_ID, WEB_RUNTIME_ID, runtime_id
from app.domains.grading.protocols import ExecutionRawResult
from app.domains.grading.report_contract import ValidatedManifest
from app.domains.grading.result_parser import calculate_scores, parse_pytest_json
from app.domains.grading.strategies import CppStrategy, WebDevelopmentStrategy, get_strategy
from app.domains.runs.grading_package import OfficialGradingPackage, PackageFile, package_digest
from test_grading_executor import _mock_judge0_client

import_domain_models()  # Register every mapper so this module also runs in isolation.

BACKEND_ROOT = Path(__file__).resolve().parents[1]


# --------------------------------------------------------------------------- helpers


def protocol2_report(cases: list[dict[str, Any]], *, completed: bool = True, infrastructure_error: str | None = None,
                     exit_code: int | None = None) -> str:
    """Serialize a protocol-2 envelope. ``cases`` items: nodeid, key, outcome (default passed), message."""
    collected = [{"nodeid": c["nodeid"], "markers": ["ag_" + c["key"]], "xfail": False} for c in cases]
    tests = [{"nodeid": c["nodeid"], "markers": ["ag_" + c["key"]], "xfail": False,
              "outcome": c.get("outcome", "passed"), "duration": 0.01, "message": c.get("message")} for c in cases]
    counts = {name: sum(t["outcome"] == name for t in tests) for name in ("passed", "failed", "error", "skipped")}
    if exit_code is None:
        exit_code = 0 if counts["passed"] == len(tests) else 1
    return json.dumps({
        "protocol_version": 2, "collected": collected, "tests": tests, "completed": completed,
        "summary": {"total": len(tests), "passed": counts["passed"], "failed": counts["failed"],
                    "errors": counts["error"], "skipped": counts["skipped"], "duration": 0.02, "exit_code": exit_code},
        "diagnostics": {}, "infrastructure_error": infrastructure_error,
    })


def native_config_dict(language: str = "cpp", framework: str | None = None, *, entrypoint: str | None = None,
                       keys: tuple[str, ...] = ("sort_asc", "sort_desc"), **extra: Any) -> dict[str, Any]:
    entrypoint = entrypoint or {"c": "main.c", "cpp": "main.cpp", "web": "index.html"}[language]
    config: dict[str, Any] = {
        "bundle": {"entrypoint": entrypoint, "file_requirements": [{"paths": [entrypoint]}], "language": language},
        "artifacts": {
            "suite": {"type": "test_file",
                      "display_filename": {"c": "tests.c", "cpp": "tests.cpp", "web": "tests.cjs"}[language]},
            "model": {"type": "model_solution", "display_filename": entrypoint},
        },
        "scoring_items": [{"key": key, "label": key, "points": 10 * (index + 1), "extra_credit": False}
                          for index, key in enumerate(keys)],
    }
    if framework is not None:
        config["test_framework"] = framework
    config.update(extra)
    return config


def native_config(language: str = "cpp", framework: str | None = None, **kwargs: Any) -> AssignmentConfigV1:
    return AssignmentConfigV1.model_validate(native_config_dict(language, framework, **kwargs))


def zip_entries(payload) -> dict[str, zipfile.ZipInfo]:
    archive = zipfile.ZipFile(io.BytesIO(base64.b64decode(payload.additional_files_b64)))
    return {info.filename: info for info in archive.infolist()}


def zip_member(payload, name: str) -> bytes:
    return zipfile.ZipFile(io.BytesIO(base64.b64decode(payload.additional_files_b64))).read(name)


def make_manifest(**fields: Any) -> ValidatedManifest:
    return ValidatedManifest.model_validate(fields)


GTEST_CASES = [
    {"nodeid": "SortSuite.ag_sort_asc", "key": "sort_asc"},
    {"nodeid": "SortSuite.ag_sort_desc", "key": "sort_desc", "outcome": "failed", "message": "Expected 5 but got 10"},
]


# --------------------------------------------------------------------------- 1. language validation


@pytest.mark.parametrize("language, expected", [
    ("python", "pytest"), ("c", "io"), ("cpp", "gtest"), ("web", "jsdom"), ("javascript", "jsdom"), ("html", "jsdom"),
])
def test_framework_defaults_follow_language(language, expected):
    config = AssignmentConfigV1.model_validate({
        "bundle": {"entrypoint": "main.x", "language": language},
        "artifacts": {"t": {"type": "pytest_file" if language == "python" else "test_file"}},
        "scoring_items": [{"key": "a", "label": "A", "points": 1, "extra_credit": False}],
    })
    assert config.test_framework == expected
    assert config.bundle.language in {"python", "c", "cpp", "web"}


def test_missing_bundle_language_defaults_to_python_pytest(base_config):
    assert base_config.bundle.language == "python"
    assert base_config.test_framework == "pytest"


@pytest.mark.parametrize("language, framework", [("c", "io"), ("c", "gtest"), ("cpp", "io"), ("cpp", "gtest"), ("web", "jsdom")])
def test_compatible_frameworks_are_accepted(language, framework):
    assert native_config(language, framework).test_framework == framework


@pytest.mark.parametrize("language, framework", [
    ("python", "gtest"), ("python", "io"), ("python", "jsdom"),
    ("c", "pytest"), ("c", "jsdom"), ("cpp", "pytest"), ("cpp", "jsdom"),
    ("web", "pytest"), ("web", "io"), ("web", "gtest"),
])
def test_incompatible_framework_language_pairs_raise(language, framework):
    data = native_config_dict("cpp" if language == "python" else language, framework)
    data["bundle"]["language"] = language
    if language == "python":
        data["artifacts"]["suite"]["type"] = "pytest_file"
    with pytest.raises(ValidationError, match="incompatible with bundle.language"):
        AssignmentConfigV1.model_validate(data)


def test_unknown_framework_value_is_rejected():
    with pytest.raises(ValidationError):
        AssignmentConfigV1.model_validate(native_config_dict("cpp", "catch2"))


# --------------------------------------------------------------------------- test_file artifact schema


def test_test_file_artifact_type_is_accepted_and_round_trips():
    config = native_config("cpp")
    assert config.artifacts["suite"].type == "test_file"
    dumped = config.model_dump(mode="json")
    assert AssignmentConfigV1.model_validate(dumped) == config


def test_unknown_artifact_type_is_still_rejected():
    data = native_config_dict("cpp")
    data["artifacts"]["suite"]["type"] = "shell_script"
    with pytest.raises(ValidationError):
        AssignmentConfigV1.model_validate(data)


def test_python_assignment_still_requires_a_pytest_file_not_a_test_file():
    data = native_config_dict("cpp")
    data["bundle"] = {"entrypoint": "main.py", "language": "python"}
    with pytest.raises(ValidationError, match="pytest_file artifact is required"):
        AssignmentConfigV1.model_validate(data)


def test_only_test_file_artifacts_are_treated_as_native_test_files():
    config = native_config("cpp")
    config.artifacts["helper"] = type(config.artifacts["suite"])(type="support_file", display_filename="util.hpp")
    config.artifacts["nested"] = type(config.artifacts["suite"])(type="test_file", display_filename="deep/path/more.cpp")
    assert multilang.test_files(config) == ["tests.cpp", "more.cpp"]


# --------------------------------------------------------------------------- 2. native payload shape


@pytest.mark.parametrize("language, framework, source_name", [
    ("cpp", "gtest", "main.cpp"), ("c", "io", "main.c"),
])
def test_native_bundle_uses_multifile_language_without_source_code(tmp_path, language, framework, source_name):
    config = native_config(language, framework)
    (tmp_path / source_name).write_text("int main(){return 0;}", encoding="utf-8")
    (tmp_path / config.artifacts["suite"].display_filename).write_text("// suite", encoding="utf-8")
    payload = prepare_bundle(tmp_path, config, stdin="3\n")
    entries = zip_entries(payload)

    assert payload.language_id == 89
    assert payload.source_code is None
    assert payload.stdin == "3\n"
    assert {"compile", "run", "ag_adapter.py", "ag_config.json", source_name}.issubset(entries)
    assert entries["compile"].external_attr >> 16 & 0o111 and entries["run"].external_attr >> 16 & 0o111
    assert not entries["ag_adapter.py"].external_attr >> 16 & 0o111
    assert b"--compile" in zip_member(payload, "compile")
    assert b"ag_adapter.py" in zip_member(payload, "run")
    settings = json.loads(zip_member(payload, "ag_config.json"))
    assert settings["framework"] == framework and settings["language"] == language
    assert settings["entrypoint"] == source_name
    assert settings["test_files"] == [config.artifacts["suite"].display_filename]
    assert [item["key"] for item in settings["items"]] == ["sort_asc", "sort_desc"]
    assert zip_member(payload, "ag_adapter.py").decode() == adapter_source()


def test_web_bundle_has_run_script_but_no_compile_step(tmp_path):
    config = native_config("web", "jsdom")
    (tmp_path / "index.html").write_text("<h1>x</h1>", encoding="utf-8")
    (tmp_path / "tests.cjs").write_text("module.exports = () => {};", encoding="utf-8")
    payload = prepare_bundle(tmp_path, config)
    entries = zip_entries(payload)
    assert payload.language_id == 89 and payload.source_code is None
    assert "compile" not in entries
    assert {"run", "ag_adapter.py", "ag_config.json", "index.html"}.issubset(entries)


def test_trusted_harness_files_cannot_be_shadowed_by_submission_content(tmp_path):
    config = native_config("cpp", "gtest")
    (tmp_path / "main.cpp").write_text("int main(){}", encoding="utf-8")
    (tmp_path / "ag_adapter.py").write_text("raise SystemExit('student adapter')", encoding="utf-8")
    payload = prepare_bundle(tmp_path, config)
    archive = zipfile.ZipFile(io.BytesIO(base64.b64decode(payload.additional_files_b64)))
    infos = [info for info in archive.infolist() if info.filename == "ag_adapter.py"]
    # Reserved submission names are omitted; only the trusted adapter is packaged.
    assert {info.filename for info in archive.infolist()[-4:]} == {"ag_adapter.py", "ag_config.json", "run", "compile"}
    assert len(infos) == 1
    assert archive.read(infos[0]).decode() == adapter_source()
    assert b"student adapter" not in archive.read(infos[0])


@pytest.mark.parametrize("name", ["run", "compile", "ag_adapter.py", "AG_CONFIG.JSON", "ag_object_1234.o", "ag_program"])
def test_static_analysis_rejects_reserved_harness_filenames(tmp_path, name):
    config = native_config("cpp", "gtest")
    (tmp_path / "main.cpp").write_text("int main(){}", encoding="utf-8")
    (tmp_path / name).write_text("x", encoding="utf-8")
    outcome = CppStrategy().static_analysis(tmp_path, config, allowed_concepts=[])
    assert not outcome.passed
    assert outcome.failure_category == "missing_required_file"


def test_static_analysis_accepts_clean_native_and_web_submissions(tmp_path):
    (tmp_path / "main.cpp").write_text("int main(){}", encoding="utf-8")
    assert CppStrategy().static_analysis(tmp_path, native_config("cpp"), None).passed
    web = tmp_path / "web"
    web.mkdir()
    (web / "index.html").write_text("<p>x</p>", encoding="utf-8")
    assert WebDevelopmentStrategy().static_analysis(web, native_config("web"), None).passed


@pytest.mark.parametrize("strategy", [CppStrategy(), WebDevelopmentStrategy()])
def test_strategies_only_accept_multifile_language_89(tmp_path, strategy):
    language = strategy.language_name
    config = native_config(language)
    (tmp_path / config.bundle.entrypoint).write_text("x", encoding="utf-8")
    assert strategy.prepare_bundle(tmp_path, config, support_artifacts={}, language_id=89).language_id == 89
    assert strategy.prepare_bundle(tmp_path, config, support_artifacts={}).language_id == 89
    for wrong in (50, 54, 71):
        with pytest.raises(ValueError, match="language 89"):
            strategy.prepare_bundle(tmp_path, config, support_artifacts={}, language_id=wrong)
    assert strategy.compile_command() is None
    assert strategy.test_command().command == "run"


def test_registry_routes_c_cpp_and_web_to_multilang_strategies():
    assert isinstance(get_strategy("c"), CppStrategy)
    assert isinstance(get_strategy("cpp"), CppStrategy)
    assert isinstance(get_strategy("web"), WebDevelopmentStrategy)


def test_runtime_identities_and_reserved_names():
    assert runtime_id("python") == PYTHON_RUNTIME_ID
    assert runtime_id("c") == runtime_id("cpp") == NATIVE_RUNTIME_ID
    assert runtime_id("web") == WEB_RUNTIME_ID
    assert len({PYTHON_RUNTIME_ID, NATIVE_RUNTIME_ID, WEB_RUNTIME_ID}) == 3
    assert {"compile", "run", "ag_adapter.py", "ag_config.json", "ag_program"} <= set(RESERVED)


def test_judge0_client_sends_no_source_code_for_language_89():
    from app.integrations.judge0.client import Judge0Client, Judge0SubmissionError
    import asyncio

    class Capture(Judge0Client):
        def __init__(self) -> None:  # no network
            self.bodies: list[dict] = []

    async def scenario() -> None:
        client = Capture()
        with pytest.raises(Judge0SubmissionError):
            await client.create_submission(None, 71, additional_files_b64="eA==")
        with pytest.raises(Judge0SubmissionError):
            await client.create_submission(None, 89)

    asyncio.run(scenario())


# --------------------------------------------------------------------------- 3. nonzero assertion exits


async def _pytest_run(tmp_path, client):
    with patch("app.domains.grading.executor.create_judge0_client", return_value=client):
        return await execute_pytest_in_judge0(tmp_path, test_filenames=["tests.py"], test_cases={},
                                              entrypoint_module="main", language_id=71, cpu_time_limit=10.0)


@pytest.mark.anyio
async def test_status_11_with_complete_report_still_scores_partial_credit(tmp_path):
    report = protocol2_report([
        {"nodeid": "tests.py::test_a", "key": "a"},
        {"nodeid": "tests.py::test_b", "key": "b", "outcome": "failed", "message": "AssertionError: 1 != 2"},
    ])
    client = _mock_judge0_client(submission_result={"status": {"id": 11}, "stdout": report, "exit_code": 1})
    outcome = await _pytest_run(tmp_path, client)

    assert outcome.success is True
    assert outcome.failure_category is None
    assert outcome.pytest_result is not None and outcome.pytest_result.failed == 1
    config = AssignmentConfigV1.model_validate({
        "bundle": {"entrypoint": "main.py"}, "artifacts": {"t": {"type": "pytest_file"}},
        "scoring_items": [{"key": "a", "label": "A", "points": 4, "extra_credit": False},
                          {"key": "b", "label": "B", "points": 6, "extra_credit": False}],
    })
    score, details = calculate_scores(outcome.pytest_result, config.scoring_items)
    assert score == 4
    assert [d["passed"] for d in details] == [True, False]
    client.delete_submission.assert_awaited_once_with("tok-1")


@pytest.mark.anyio
@pytest.mark.parametrize("stdout", ["", "Traceback (most recent call last):\nAssertionError", "[  PASSED  ] 1 test."])
async def test_status_11_without_a_report_is_an_invalid_report_not_a_pass(tmp_path, stdout):
    client = _mock_judge0_client(submission_result={"status": {"id": 11}, "stdout": stdout})
    outcome = await _pytest_run(tmp_path, client)
    assert outcome.success is False
    assert outcome.failure_category == "invalid_runner_report"


@pytest.mark.anyio
async def test_status_11_with_incomplete_report_is_rejected(tmp_path):
    report = protocol2_report([{"nodeid": "tests.py::test_a", "key": "a"}], completed=False)
    client = _mock_judge0_client(submission_result={"status": {"id": 11}, "stdout": report})
    outcome = await _pytest_run(tmp_path, client)
    assert outcome.success is False
    assert outcome.failure_category == "invalid_runner_report"


@pytest.mark.anyio
@pytest.mark.parametrize("status_id, category", [(5, "timeout"), (7, "resource_limit_exceeded")])
async def test_other_judge0_failures_still_win_over_a_complete_report(tmp_path, status_id, category):
    report = protocol2_report([{"nodeid": "tests.py::test_a", "key": "a"}])
    client = _mock_judge0_client(submission_result={"status": {"id": status_id}, "stdout": report})
    outcome = await _pytest_run(tmp_path, client)
    assert outcome.success is False
    assert outcome.failure_category == category


@pytest.fixture
def cpp_pipeline_inputs(tmp_path):
    suite = tmp_path / "artifacts" / "tests.cpp"
    suite.parent.mkdir()
    suite.write_text("// gtest suite", encoding="utf-8")
    return {"suite": f"file://{suite.as_posix()}"}


def _pipeline(config, refs, **kwargs):
    return GradingPipeline(config=config, artifact_refs=refs, allowed_concepts=[], **kwargs)


def _patch_judge0(monkeypatch, raw: ExecutionRawResult):
    calls: list[Any] = []

    async def fake(payload):
        calls.append(payload)
        return raw

    monkeypatch.setattr("app.domains.grading.pipeline.execute_payload_in_judge0", fake)
    return calls


@pytest.mark.anyio
async def test_native_pipeline_scores_status_11_with_complete_report(monkeypatch, cpp_pipeline_inputs):
    calls = _patch_judge0(monkeypatch, ExecutionRawResult(
        stdout=protocol2_report(GTEST_CASES), exit_code=1, status_id=11))
    report = await _pipeline(native_config("cpp", "gtest"), cpp_pipeline_inputs).evaluate(
        SubmissionPayload.from_files({"main.cpp": b"int add(){return 1;}"}))

    assert report.success is True
    assert report.failure_category is None
    assert report.score == 10
    assert report.max_score == 30
    assert [r["passed"] for r in report.test_results] == [True, False]
    assert calls[0].language_id == 89 and calls[0].source_code is None
    assert "tests.cpp" in zip_entries(calls[0])


@pytest.mark.anyio
async def test_native_pipeline_status_11_with_console_only_output_fails_closed(monkeypatch, cpp_pipeline_inputs):
    _patch_judge0(monkeypatch, ExecutionRawResult(
        stdout="[  PASSED  ] SortSuite.ag_sort_asc\n[  PASSED  ] SortSuite.ag_sort_desc\n", exit_code=1, status_id=11))
    report = await _pipeline(native_config("cpp", "gtest"), cpp_pipeline_inputs).evaluate(
        SubmissionPayload.from_files({"main.cpp": b"int add(){return 1;}"}))
    assert report.success is False
    assert report.score == 0
    assert report.failure_category == "invalid_runner_report"


@pytest.mark.anyio
async def test_native_pipeline_status_5_is_a_timeout_even_with_a_report(monkeypatch, cpp_pipeline_inputs):
    _patch_judge0(monkeypatch, ExecutionRawResult(stdout=protocol2_report(GTEST_CASES), status_id=5))
    report = await _pipeline(native_config("cpp", "gtest"), cpp_pipeline_inputs).evaluate(
        SubmissionPayload.from_files({"main.cpp": b"int add(){return 1;}"}))
    assert report.success is False
    assert report.failure_category == "timeout"


@pytest.mark.anyio
async def test_native_pipeline_compile_status_6_is_a_compilation_error(monkeypatch, cpp_pipeline_inputs):
    _patch_judge0(monkeypatch, ExecutionRawResult(
        compile_output="main.cpp:1:1: error: nope\nld: failed", status_id=6, exit_code=1))
    report = await _pipeline(native_config("cpp", "gtest"), cpp_pipeline_inputs).evaluate(
        SubmissionPayload.from_files({"main.cpp": b"bad"}))
    assert report.success is False
    assert report.failure_category == "compilation_error"
    assert report.compiler_errors == ["main.cpp:1:1: error: nope", "ld: failed"]


# --------------------------------------------------------------------------- 5. genuine GoogleTest results


def test_gtest_scoring_uses_structured_report_markers_and_ignores_console_text():
    config = native_config("cpp", "gtest")
    # The report says sort_asc failed and sort_desc passed; console text claims the opposite.
    report = protocol2_report([
        {"nodeid": "SortSuite.ag_sort_asc", "key": "sort_asc", "outcome": "failed", "message": "Failure"},
        {"nodeid": "SortSuite.ag_sort_desc", "key": "sort_desc"},
    ])
    parsed = parse_execution(ExecutionRawResult(stdout=report, stderr=(
        "[  PASSED  ] SortSuite.ag_sort_asc\n[  FAILED  ] SortSuite.ag_sort_desc\n"), exit_code=1, status_id=11), config)

    assert parsed.success is True
    assert parsed.score == 20  # sort_desc only
    assert {r["key"]: r["passed"] for r in parsed.test_results} == {"sort_asc": False, "sort_desc": True}


@pytest.mark.parametrize("stdout", [
    "[==========] Running 2 tests\n[  PASSED  ] SortSuite.ag_sort_asc\n[  PASSED  ] SortSuite.ag_sort_desc\n",
    "[  PASSED  ] 2 tests.\n",
    "[  FAILED  ] SortSuite.ag_sort_asc\n",
])
def test_gtest_console_markers_alone_never_produce_a_score(stdout):
    parsed = parse_execution(ExecutionRawResult(stdout=stdout, exit_code=0, status_id=3), native_config("cpp", "gtest"))
    assert parsed.success is False
    assert parsed.score == 0
    assert parsed.test_results == []
    assert parsed.failure_category == "invalid_runner_report"


def test_console_text_around_a_valid_report_invalidates_the_report():
    report = protocol2_report(GTEST_CASES)
    for stdout in ("[  PASSED  ] SortSuite.ag_sort_asc\n" + report, report + "\n[  PASSED  ] extra\n"):
        parsed = parse_execution(ExecutionRawResult(stdout=stdout, exit_code=0), native_config("cpp", "gtest"))
        assert parsed.success is False and parsed.score == 0


def test_forged_passing_text_in_a_failure_message_cannot_award_points():
    config = native_config("cpp", "gtest", keys=("sort_asc",))
    report = protocol2_report([{"nodeid": "SortSuite.ag_sort_asc", "key": "sort_asc", "outcome": "failed",
                                "message": "[  PASSED  ] SortSuite.ag_sort_asc"}])
    parsed = parse_execution(ExecutionRawResult(stdout=report, exit_code=1, status_id=11), config)
    assert parsed.score == 0 and parsed.test_results[0]["passed"] is False


def test_report_must_match_the_expected_manifest_inventory():
    config = native_config("cpp", "gtest")
    manifest = make_manifest(language="cpp", framework="gtest", runtime_id=NATIVE_RUNTIME_ID, fingerprint="a" * 64,
                                 cases=[{"nodeid": "SortSuite.ag_sort_asc", "markers": ["ag_sort_asc"], "xfail": False},
                                        {"nodeid": "SortSuite.ag_sort_desc", "markers": ["ag_sort_desc"], "xfail": False}])
    manifest_dict = manifest.model_dump(mode="json")
    ok = parse_execution(ExecutionRawResult(stdout=protocol2_report(GTEST_CASES), exit_code=1, status_id=11),
                         config, manifest_dict)
    assert ok.success and ok.score == 10
    missing = parse_execution(ExecutionRawResult(stdout=protocol2_report(GTEST_CASES[:1]), exit_code=0),
                              config, manifest_dict)
    assert not missing.success and missing.failure_category == "invalid_runner_report"


def test_infrastructure_error_report_is_not_scored():
    report = protocol2_report([], completed=False, infrastructure_error="RuntimeError: GoogleTest discovery failed.",
                              exit_code=3)
    parsed = parse_execution(ExecutionRawResult(stdout=report, exit_code=0), native_config("cpp", "gtest"))
    assert parsed.success is False and parsed.score == 0
    assert parsed.failure_category == "infrastructure_error"


def test_guest_adapter_discovers_and_reads_gtest_through_structured_channels_only():
    source = adapter_source()
    assert "--gtest_list_tests" in source and "--gtest_output=xml:" in source
    assert "ET.parse(destination)" in source
    # No console scraping: the adapter never inspects the "[  PASSED  ]" / "[  FAILED  ]" banners.
    assert "[  PASSED" not in source and "[  FAILED" not in source and "[ RUN" not in source
    assert "ag_<rubric_key>" in source  # tests must be named for rubric keys


def test_guest_adapter_reports_case_outcomes_in_the_envelope_not_the_process_status():
    source = adapter_source()
    assert "return 0  # The complete envelope" in source
    assert '"protocol_version": 2' in source
    assert parse_pytest_json(protocol2_report(GTEST_CASES)).passed == 1


# --------------------------------------------------------------------------- 6. script timing (web runner)


def test_web_runner_waits_for_document_load_before_returning_the_page():
    source = (BACKEND_ROOT / "app" / "domains" / "grading" / "resources" / "web_runner.cjs").read_text(encoding="utf-8")
    assert "readyState === 'complete'" in source
    assert "addEventListener('load'" in source
    assert "runScripts: 'dangerously'" in source
    # Module scripts are bundled and deferred so they have run by the time `load` fires.
    assert "setAttribute('defer'" in source
    assert "unhandled-exception" in source


@pytest.mark.skipif(shutil.which("node") is None, reason="node is not installed on this host")
def test_web_runner_is_syntactically_valid_javascript(tmp_path):
    # jsdom/esbuild live only in the Judge0 guest image, so the browser-timing behavior itself is not
    # exercisable here; syntax validation still catches breakage before an image build.
    runner = tmp_path / "web_runner.cjs"
    runner.write_text(multilang.RESOURCES.joinpath("web_runner.cjs").read_text(encoding="utf-8"), encoding="utf-8")
    result = subprocess.run(["node", "--check", str(runner)], capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr


@pytest.mark.anyio
async def test_web_pipeline_scores_jsdom_report(monkeypatch, tmp_path):
    suite = tmp_path / "tests.cjs"
    suite.write_text("module.exports = () => {};", encoding="utf-8")
    report = protocol2_report([
        {"nodeid": "tests.cjs::heading", "key": "sort_asc"},
        {"nodeid": "tests.cjs::click", "key": "sort_desc", "outcome": "failed", "message": "AssertionError"},
    ])
    _patch_judge0(monkeypatch, ExecutionRawResult(stdout=report, exit_code=1, status_id=11))
    result = await _pipeline(native_config("web"), {"suite": f"file://{suite.as_posix()}"}).evaluate(
        SubmissionPayload.from_files({"index.html": b"<h1>Hi</h1>"}))
    assert result.success and result.score == 10


# --------------------------------------------------------------------------- 4. fingerprint invalidation


def _fingerprint_with(db, assignment, mutate=None) -> str:
    original = copy.deepcopy(assignment.config.config)
    try:
        if mutate is not None:
            config = copy.deepcopy(original)
            mutate(config)
            assignment.config.config = config
        return execution_fingerprint(db, assignment)
    finally:
        assignment.config.config = original


def _make_native(language: str, framework: str):
    def mutate(config: dict) -> None:
        entrypoint = {"c": "main.c", "cpp": "main.cpp"}[language]
        config["bundle"] = {"entrypoint": entrypoint, "file_requirements": [{"paths": [entrypoint]}], "language": language}
        config["test_framework"] = framework
        for item in config["scoring_items"]:
            if item.get("item_type", "pytest") == "pytest" and item.get("inputs") is None:
                item["inputs"], item["outputs"] = ["1"], ["1"]
    return mutate


@pytest.fixture
def seeded(reset_database):
    with SessionLocal() as db:
        assignment = get_assignment_for_course(db, "cs1400", "simple-python-functions")
        assert assignment is not None
        yield db, assignment
        db.rollback()


def test_fingerprint_is_stable_and_matches_the_seeded_manifest(seeded):
    db, assignment = seeded
    first = execution_fingerprint(db, assignment)
    assert first == execution_fingerprint(db, assignment)
    assert inventory_status(db, assignment) == "ready"


def test_fingerprint_changes_with_comparison_mode(seeded):
    db, assignment = seeded
    base = execution_fingerprint(db, assignment)
    changed = _fingerprint_with(db, assignment, lambda c: c["scoring_items"][0].update(comparison_mode="exact"))
    assert changed != base


def test_fingerprint_changes_with_tolerance(seeded):
    db, assignment = seeded
    base = _fingerprint_with(db, assignment, lambda c: c["scoring_items"][0].update(comparison_mode="numeric_tolerance", tolerance=0.1))
    changed = _fingerprint_with(db, assignment, lambda c: c["scoring_items"][0].update(comparison_mode="numeric_tolerance", tolerance=0.2))
    assert changed != base
    assert base != execution_fingerprint(db, assignment)


def test_fingerprint_changes_with_assignment_level_comparison_default(seeded):
    db, assignment = seeded

    def inherit(mode: str):
        def mutate(config: dict) -> None:
            for item in config["scoring_items"]:  # items without their own setting inherit the default
                item.pop("comparison_mode", None)
                item.pop("tolerance", None)
            config["comparison_mode"] = mode
        return mutate

    base = _fingerprint_with(db, assignment, inherit("normalized"))
    assert _fingerprint_with(db, assignment, inherit("exact")) != base


def test_stale_manifest_is_reported_after_a_comparison_change(seeded):
    db, assignment = seeded
    assignment.config.config = {**assignment.config.config,
                                "scoring_items": [{**assignment.config.config["scoring_items"][0], "comparison_mode": "regex"},
                                                  *assignment.config.config["scoring_items"][1:]]}
    assert inventory_status(db, assignment) == "stale"


def test_fingerprint_changes_with_framework_and_language(seeded):
    db, assignment = seeded
    python = execution_fingerprint(db, assignment)
    c_io = _fingerprint_with(db, assignment, _make_native("c", "io"))
    c_gtest = _fingerprint_with(db, assignment, _make_native("c", "gtest"))
    cpp_io = _fingerprint_with(db, assignment, _make_native("cpp", "io"))
    cpp_gtest = _fingerprint_with(db, assignment, _make_native("cpp", "gtest"))
    assert len({python, c_io, c_gtest, cpp_io, cpp_gtest}) == 5


def test_fingerprint_changes_with_runtime_identity(seeded):
    db, assignment = seeded
    base = _fingerprint_with(db, assignment, _make_native("cpp", "gtest"))
    with patch.object(inventory, "runtime_id", return_value="gcc-9.9.9-gtest-9-adapter-1-report-2"):
        changed = _fingerprint_with(db, assignment, _make_native("cpp", "gtest"))
        python_changed = execution_fingerprint(db, assignment)
    assert changed != base
    assert python_changed != execution_fingerprint(db, assignment)


def test_fingerprint_changes_with_adapter_source_for_native_but_not_python(seeded):
    db, assignment = seeded
    python = execution_fingerprint(db, assignment)
    native = _fingerprint_with(db, assignment, _make_native("cpp", "gtest"))
    with patch.object(inventory, "adapter_source", return_value="# changed adapter"):
        assert _fingerprint_with(db, assignment, _make_native("cpp", "gtest")) != native
        assert execution_fingerprint(db, assignment) == python


def test_fingerprint_changes_with_pytest_runner_but_not_native(seeded):
    db, assignment = seeded
    python = execution_fingerprint(db, assignment)
    native = _fingerprint_with(db, assignment, _make_native("cpp", "gtest"))
    with patch.object(inventory, "generate_runner_script", return_value="# changed runner"):
        assert execution_fingerprint(db, assignment) != python
        assert _fingerprint_with(db, assignment, _make_native("cpp", "gtest")) == native


def test_fallback_helper_only_affects_pytest_fingerprints(seeded):
    db, assignment = seeded
    python = execution_fingerprint(db, assignment)
    native = _fingerprint_with(db, assignment, _make_native("c", "io"))
    with patch.object(inventory, "load_fallback_helper", return_value=b"different helper"):
        assert execution_fingerprint(db, assignment) != python
        assert _fingerprint_with(db, assignment, _make_native("c", "io")) == native


# --------------------------------------------------------------------------- package v3


def _native_payload(**overrides: Any) -> dict[str, Any]:
    config = native_config("cpp", "gtest", keys=("sort_asc",))
    suite = b"// instructor gtest suite"
    payload: dict[str, Any] = {
        "version": 3, "assignment_id": 1, "config_version": 1, "config": config.model_dump(mode="json"),
        "concepts": [], "description": None,
        "files": {"tests.cpp": PackageFile.from_bytes(suite).model_dump()},
        "pytest_filenames": [], "runner_source": adapter_source(), "fallback_helper": None,
        "expected_manifest": make_manifest(
            language="cpp", framework="gtest", runtime_id=NATIVE_RUNTIME_ID, fingerprint="b" * 64,
            cases=[{"nodeid": "SortSuite.ag_sort_asc", "markers": ["ag_sort_asc"], "xfail": False}],
        ).model_dump(mode="json"),
        "execution_parameters": {"language_id": 89, "cpu_time_limit": 30.0, "wall_time_limit": 45.0,
                                 "memory_limit": 262144, "preinstalled_dependencies": []},
    }
    payload.update(overrides)
    return payload


def _validate(payload: dict[str, Any]) -> OfficialGradingPackage:
    return OfficialGradingPackage.model_validate({**payload, "digest": package_digest(payload)})


def test_native_package_v3_is_accepted_without_a_fallback_helper_or_pytest_files():
    package = _validate(_native_payload())
    assert package.version == 3
    assert package.fallback_helper is None
    assert package.pytest_filenames == []
    assert package.execution_parameters.language_id == 89
    assert package.preloaded_artifacts().files == {"tests.cpp": b"// instructor gtest suite"}


def test_package_versions_other_than_3_are_rejected():
    for version in (1, 2, 4):
        with pytest.raises(ValidationError):
            _validate(_native_payload(version=version))


def test_native_package_with_fallback_helper_is_rejected():
    helper = PackageFile.from_bytes(b"helpers").model_dump()
    with pytest.raises(ValidationError, match="invalid execution inputs"):
        _validate(_native_payload(fallback_helper=helper))


@pytest.mark.parametrize("language_id", [50, 54, 71, 88, 90])
def test_native_package_with_non_89_language_id_is_rejected(language_id):
    parameters = {**_native_payload()["execution_parameters"], "language_id": language_id}
    with pytest.raises(ValidationError, match="invalid execution inputs"):
        _validate(_native_payload(execution_parameters=parameters))


def test_package_runtime_profile_must_match_the_config():
    payload = _native_payload()
    wrong_framework = make_manifest(
        language="cpp", framework="io", runtime_id=NATIVE_RUNTIME_ID, fingerprint="b" * 64,
        cases=[{"nodeid": "x", "markers": ["ag_sort_asc"], "xfail": False}]).model_dump(mode="json")
    with pytest.raises(ValidationError, match="runtime profile mismatch"):
        _validate({**payload, "expected_manifest": wrong_framework})
    wrong_language = make_manifest(
        language="web", framework="jsdom", runtime_id=WEB_RUNTIME_ID, fingerprint="b" * 64,
        cases=[{"nodeid": "x", "markers": ["ag_sort_asc"], "xfail": False}]).model_dump(mode="json")
    with pytest.raises(ValidationError, match="runtime profile mismatch"):
        _validate({**payload, "expected_manifest": wrong_language})


def test_manifest_rejects_a_runtime_id_from_another_language():
    with pytest.raises(ValidationError, match="Unsupported runtime profile"):
        make_manifest(language="cpp", framework="gtest", runtime_id=PYTHON_RUNTIME_ID, fingerprint="b" * 64,
                          cases=[{"nodeid": "x", "markers": ["ag_a"], "xfail": False}])


def test_package_digest_still_binds_native_inputs():
    payload = _native_payload()
    forged = {**payload, "runner_source": "# forged runner"}
    with pytest.raises(ValidationError, match="digest mismatch"):
        OfficialGradingPackage.model_validate({**forged, "digest": package_digest(payload)})


def test_reserved_harness_names_cannot_be_instructor_filenames():
    from app.domains.runs.grading_package import execution_filename

    for name in ("run", "compile", "ag_adapter.py", "ag_config.json"):
        with pytest.raises(ValueError, match="reserved"):
            execution_filename("suite", name)
    assert execution_filename("suite", "tests.cpp") == "tests.cpp"


# --------------------------------------------------------------------------- sync-tests route


SYNC_URL = "/staff/courses/cs1400/assignments/simple-python-functions/sync-tests"

SYNC_SOURCE = (
    "COMPARISON_MODE = 'normalized'\n"
    "@pytest.mark.ag_greet\n"
    "def test_greet():\n"
    "    COMPARISON_MODE = 'exact'\n"
    "    INPUTS = ['Ada\\n']\n"
    "    OUTPUTS = ['Hello, Ada\\n']\n"
    "@pytest.mark.ag_plain\n"
    "def test_plain():\n"
    "    pass\n"
)


def test_sync_tests_route_returns_items_without_unset_fields(client, admin_headers):
    response = client.post(SYNC_URL, headers=admin_headers, json={"source": SYNC_SOURCE})
    assert response.status_code == 200
    items = {item["key"]: item for item in response.json()["items"]}
    assert items["greet"] == {"key": "greet", "inputs": ["Ada\n"], "outputs": ["Hello, Ada\n"], "comparison_mode": "exact"}
    # Module defaults apply to every marker, but nothing is invented for undeclared fields.
    assert items["plain"] == {"key": "plain", "comparison_mode": "normalized"}


def test_sync_tests_route_reports_invalid_source_as_422(client, admin_headers):
    conflict = SYNC_SOURCE + "@pytest.mark.ag_greet\ndef test_again():\n    COMPARISON_MODE = 'regex'\n"
    for source in ("def broken(:\n", conflict):
        response = client.post(SYNC_URL, headers=admin_headers, json={"source": source})
        assert response.status_code == 422


def test_sync_tests_route_requires_staff_and_a_known_assignment(client, admin_headers, student_token):
    assert client.post(SYNC_URL, json={"source": "x = 1"}).status_code in {401, 403}
    assert client.post(SYNC_URL, headers={"Authorization": f"Bearer {student_token}"},
                       json={"source": "x = 1"}).status_code in {401, 403}
    missing = SYNC_URL.replace("simple-python-functions", "does-not-exist")
    assert client.post(missing, headers=admin_headers, json={"source": "x = 1"}).status_code == 404


def test_sync_tests_route_is_limited_to_python_suites(client, admin_headers, db_session):
    assignment = get_assignment_for_course(db_session, "cs1400", "simple-python-functions")
    assert assignment is not None
    assignment.language = "cpp"
    db_session.commit()
    response = client.post(SYNC_URL, headers=admin_headers, json={"source": SYNC_SOURCE})
    assert response.status_code == 422
    assert "Python" in response.json()["detail"]


def test_sync_tests_route_never_executes_submitted_source(client, admin_headers, tmp_path):
    marker = tmp_path / "executed.txt"
    source = (f"open({marker.as_posix()!r}, 'w').write('x')\n"
              "@pytest.mark.ag_safe\ndef test_safe():\n    TOLERANCE = __import__('os').system('echo hi')\n")
    response = client.post(SYNC_URL, headers=admin_headers, json={"source": source})
    assert response.status_code == 200
    assert not marker.exists()
    assert response.json()["items"] == [{"key": "safe"}]
