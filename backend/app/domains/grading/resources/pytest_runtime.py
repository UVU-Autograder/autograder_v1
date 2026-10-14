"""Embedded runtime: separates accidental console output, not deliberate tampering."""
TEST_FILENAMES = globals().get("TEST_FILENAMES", [])
TEST_CASES = globals().get("TEST_CASES", {})
ENTRYPOINT_MODULE = globals().get("ENTRYPOINT_MODULE", "main")
DEPENDENCIES = globals().get("DEPENDENCIES", [])

import importlib
import io
import json
import os
import signal
import subprocess
import sys
import tempfile
import threading
import time

LIMIT = 65536
REPORT_LIMIT = 1024 * 1024
CAPTURES = []


def clipped(text, limit=LIMIT):
    return str(text).encode("utf-8", errors="replace")[:limit].decode("utf-8", errors="ignore")


class OutputLedger:
    def __init__(self):
        self.nodeid = None
        self.counts = {}
        self.overflow = set()
        self.data = {1: bytearray(), 2: bytearray()}
        self.truncated = {1: False, 2: False}

    def add(self, fd, data):
        key = (self.nodeid, fd)
        count = self.counts.get(key, 0)
        self.counts[key] = count + len(data)
        room = max(0, LIMIT - count)
        if len(data) > room:
            self.overflow.add(self.nodeid)
            self.truncated[fd] = True
        target = self.data[fd]
        if len(data) > LIMIT - len(target):
            self.truncated[fd] = True
        target.extend(data[:LIMIT - len(target)])
        return data[:room]

    def export(self):
        return {"stdout": self.data[1].decode("utf-8", errors="ignore"),
                "stderr": self.data[2].decode("utf-8", errors="ignore"),
                "stdout_truncated": self.truncated[1], "stderr_truncated": self.truncated[2]}


LEDGER = OutputLedger()


class BoundedBytes(io.BytesIO):
    def __init__(self, fd=1):
        super().__init__()
        self.fd = fd

    def write(self, data):
        kept = LEDGER.add(self.fd, data)
        super().write(kept[:max(0, LIMIT - self.tell())])
        return len(data)


class BoundedOutput(io.TextIOWrapper):
    """Instructor output helper; never use for stdin or general-purpose storage."""
    def __init__(self, stream="stdout"):
        super().__init__(BoundedBytes(2 if stream == "stderr" else 1), encoding="utf-8",
                         errors="replace", newline="", write_through=True)

    def getvalue(self):
        return self.buffer.getvalue().decode("utf-8", errors="ignore")


class PipeBuffer:
    """Drain FD output continuously, discarding excess without a disk spool."""
    def __init__(self, read_fd, fd, account=True):
        self.read_fd, self.fd, self.account = read_fd, fd, account
        self.data = bytearray()
        self.lock = threading.Lock()
        self.finished = threading.Event()
        os.set_blocking(read_fd, False)
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def drain(self):
        with self.lock:
            while True:
                try:
                    chunk = os.read(self.read_fd, 8192)
                except BlockingIOError:
                    return
                if not chunk:
                    self.finished.set()
                    return
                kept = LEDGER.add(self.fd, chunk) if self.account else chunk
                self.data.extend(kept[:max(0, LIMIT - len(self.data))])

    def run(self):
        while not self.finished.is_set():
            self.drain()
            self.finished.wait(0.002)

    def snap(self):
        self.drain()
        with self.lock:
            result = bytes(self.data)
            self.data.clear()
            return result

    def stop(self):
        self.drain()
        self.finished.set()
        self.thread.join(timeout=1)


def install_capture():
    import _pytest.capture as capture
    original = (capture.SysCapture, capture.SysCaptureBinary, capture.FDCapture, capture.FDCaptureBinary)

    class BoundedSys:
        EMPTY_BUFFER = ""
        binary = False

        def __init__(self, fd):
            self.fd, self.name = fd, "stderr" if fd == 2 else "stdout"
            self.old = getattr(sys, self.name)
            self.stream = BoundedOutput(self.name)
            CAPTURES.append(self)

        def start(self):
            setattr(sys, self.name, self.stream)

        resume = start

        def suspend(self):
            setattr(sys, self.name, self.old)

        def snap(self):
            data = self.stream.buffer.getvalue()
            self.stream.buffer.seek(0)
            self.stream.buffer.truncate(0)
            return data if self.binary else data.decode("utf-8", errors="ignore")

        def flush(self):
            self.stream.flush()

        def done(self):
            self.suspend()
            CAPTURES.remove(self)
            self.stream.close()

        def writeorg(self, data):
            # The ledger already retained it; replay would double-count output.
            pass

    class BoundedSysBinary(BoundedSys):
        EMPTY_BUFFER = b""
        binary = True

    class BoundedFD(BoundedSys):
        def __init__(self, fd):
            self.fd, self.name = fd, "stderr" if fd == 2 else "stdout"
            self.old = getattr(sys, self.name)
            self.saved = os.dup(fd)
            read_fd, self.write_fd = os.pipe()
            self.pipe = PipeBuffer(read_fd, fd)
            self.stream = io.TextIOWrapper(os.fdopen(os.dup(self.write_fd), "wb", buffering=0),
                                           encoding="utf-8", errors="replace", newline="", write_through=True)
            CAPTURES.append(self)

        def start(self):
            os.dup2(self.write_fd, self.fd)
            setattr(sys, self.name, self.stream)

        resume = start

        def suspend(self):
            self.flush()
            os.dup2(self.saved, self.fd)
            setattr(sys, self.name, self.old)

        def flush(self):
            self.stream.flush()
            self.pipe.drain()

        def snap(self):
            self.flush()
            data = self.pipe.snap()
            return data if self.binary else data.decode("utf-8", errors="ignore")

        def done(self):
            self.suspend()
            self.stream.close()
            os.close(self.write_fd)
            self.pipe.stop()
            os.close(self.pipe.read_fd)
            os.close(self.saved)
            CAPTURES.remove(self)

    class BoundedFDBinary(BoundedFD):
        EMPTY_BUFFER = b""
        binary = True

    capture.SysCapture = lambda fd, **kw: original[0](fd, **kw) if fd == 0 else BoundedSys(fd)
    capture.SysCaptureBinary = lambda fd, **kw: original[1](fd, **kw) if fd == 0 else BoundedSysBinary(fd)
    capture.FDCapture = lambda fd, **kw: original[2](fd, **kw) if fd == 0 else BoundedFD(fd)
    capture.FDCaptureBinary = lambda fd, **kw: original[3](fd, **kw) if fd == 0 else BoundedFDBinary(fd)
    capture.SysCapture.EMPTY_BUFFER = ""
    capture.SysCaptureBinary.EMPTY_BUFFER = b""
    capture.FDCapture.EMPTY_BUFFER = ""
    capture.FDCaptureBinary.EMPTY_BUFFER = b""
    return BoundedFD


def flush_captures():
    for capture in list(CAPTURES):
        capture.flush()


def failed_payload(message):
    return {"protocol_version": 2, "collected": [], "tests": [], "completed": False,
            "summary": {"total": 0, "passed": 0, "failed": 0, "errors": 0, "skipped": 0,
                        "duration": 0.0, "exit_code": 3},
            "diagnostics": LEDGER.export(), "infrastructure_error": clipped(message, 2000)}


def encode_payload(payload):
    encoded = json.dumps(payload, ensure_ascii=True, allow_nan=False).encode("utf-8")
    if len(encoded) > REPORT_LIMIT:
        for test in payload["tests"]:
            for field in ("actual", "expected", "expected_input", "message"):
                test[field] = None
        payload["diagnostics"].update(stdout="", stderr="", stdout_truncated=True, stderr_truncated=True)
        encoded = json.dumps(payload, ensure_ascii=True, allow_nan=False).encode("utf-8")
    if len(encoded) > REPORT_LIMIT:
        encoded = json.dumps(failed_payload("Report exceeds its structural limit.")).encode("utf-8")
    return encoded


def child_main(report_path):
    payload = None
    try:
        for dependency in DEPENDENCIES:
            mod = {"pillow": "PIL"}.get(dependency.lower(), dependency)
            try:
                importlib.import_module(mod)
            except ImportError as exc:
                raise RuntimeError(f"Missing required preinstalled dependency: {dependency}") from exc
        import pytest
        if pytest.__version__ != "8.4.2":
            raise RuntimeError("Grading requires pinned pytest 8.4.2.")
        fd_capture = install_capture()
        sys.modules["autograder_capture"] = sys.modules["__main__"]

        def timeout_handler(signum, frame):
            raise TimeoutError("Test case execution timed out (5s limit).")

        class Plugin:
            def __init__(self):
                self.collected, self.reports, self.collection_failed = [], {}, False

            @pytest.hookimpl(trylast=True)
            def pytest_configure(self, config):
                class QuietOutput(io.StringIO):
                    def write(self, text):
                        return len(text)
                reporter = config.pluginmanager.getplugin("terminalreporter")
                if reporter:
                    reporter._tw._file = QuietOutput()

            def pytest_collection_finish(self, session):
                self.collected = [{"nodeid": item.nodeid,
                    "markers": sorted({m.name for m in item.iter_markers() if m.name.startswith("ag_")}),
                    "xfail": item.get_closest_marker("xfail") is not None} for item in session.items]
                if len(self.collected) > 512:
                    raise RuntimeError("Assignment exceeds 512 cases.")

            def pytest_collectreport(self, report):
                if report.failed:
                    self.collection_failed = True

            @pytest.hookimpl(wrapper=True)
            def pytest_runtest_protocol(self, item, nextitem):
                flush_captures()
                LEDGER.nodeid = item.nodeid
                if hasattr(signal, "alarm"):
                    signal.signal(signal.SIGALRM, timeout_handler)
                    signal.alarm(5)
                try:
                    return (yield)
                finally:
                    if hasattr(signal, "alarm"):
                        signal.alarm(0)
                    flush_captures()
                    LEDGER.nodeid = None

            def pytest_runtest_logreport(self, report):
                self.reports.setdefault(report.nodeid, []).append(report)

            def pytest_generate_tests(self, metafunc):
                for marker in metafunc.definition.iter_markers():
                    data = TEST_CASES.get(marker.name.removeprefix("ag_"))
                    if data and data.get("inputs"):
                        metafunc.parametrize("case_input,case_output", list(zip(data["inputs"], data["outputs"])))
                        break

            @pytest.fixture
            def bounded_output(self):
                return BoundedOutput

            @pytest.fixture
            def run_case(self, monkeypatch, capsys, request):
                def run():
                    params = getattr(getattr(request.node, "callspec", None), "params", {})
                    if "case_input" not in params or "case_output" not in params:
                        pytest.fail("Test case parameters are missing.")
                    monkeypatch.setattr(sys, "stdin", io.StringIO(params["case_input"]))
                    if ENTRYPOINT_MODULE in sys.modules:
                        importlib.reload(sys.modules[ENTRYPOINT_MODULE])
                    else:
                        importlib.import_module(ENTRYPOINT_MODULE)
                    actual = capsys.readouterr().out
                    request.node.user_properties.extend([("actual", actual), ("expected", params["case_output"]),
                                                         ("expected_input", params["case_input"])])
                    def normalize(value):
                        return "\n".join(line.strip() for line in value.splitlines() if line.strip())
                    assert normalize(actual) == normalize(params["case_output"])
                return run

        plugin = Plugin()
        os.environ.update(PYTEST_DISABLE_PLUGIN_AUTOLOAD="1", SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
        start = time.monotonic()
        outer = [fd_capture(1), fd_capture(2)]
        for capture in outer:
            capture.start()
        try:
            exit_code = int(pytest.main(["--tb=short", "-q", "--no-header", "--disable-warnings", "--confcutdir=."] + TEST_FILENAMES,
                                       plugins=[plugin]))
        finally:
            for capture in outer:
                capture.done()
        tests = []
        for case in plugin.collected:
            reports = plugin.reports.get(case["nodeid"], [])
            phases = {r.when for r in reports}
            failures = [r.when for r in reports if r.failed]
            terminal = "teardown" in phases and ("call" in phases or any(r.when == "setup" and (r.failed or r.skipped) for r in reports))
            if not terminal:
                continue
            skipped = any(r.skipped or hasattr(r, "wasxfail") for r in reports) or case["xfail"]
            overflow = case["nodeid"] in LEDGER.overflow
            outcome = "error" if any(p != "call" for p in failures) else "failed" if failures or overflow else "skipped" if skipped else "passed"
            props = dict(pair for r in reports for pair in r.user_properties)
            actual = props.get("actual")
            if actual is None:
                actual = next((text for r in reports for name, text in r.sections if "stdout" in name.lower()), None)
            tests.append({**case, "outcome": outcome, "duration": float(sum(r.duration for r in reports)),
                "message": "Output exceeded 64 KiB. Check for excessive printing or a loop." if overflow else next((clipped(str(r.longrepr), 2000) for r in reports if r.failed), None),
                "actual": clipped(actual) if actual is not None else None,
                "expected": clipped(props["expected"]) if "expected" in props else None,
                "expected_input": clipped(props["expected_input"]) if "expected_input" in props else None,
                "failure_category": "output_limit_exceeded" if overflow else None,
                "phase_failures": failures, "output_truncated": overflow})
        if any(t["outcome"] != "passed" for t in tests) and exit_code == 0:
            exit_code = 1
        payload = {"protocol_version": 2, "collected": plugin.collected, "tests": tests,
            "summary": {"total": len(tests), "passed": sum(t["outcome"] == "passed" for t in tests),
                "failed": sum(t["outcome"] == "failed" for t in tests), "errors": sum(t["outcome"] == "error" for t in tests),
                "skipped": sum(t["outcome"] == "skipped" for t in tests), "duration": float(time.monotonic() - start), "exit_code": exit_code},
            "completed": not plugin.collection_failed and exit_code in (0, 1) and len(tests) == len(plugin.collected) and None not in LEDGER.overflow,
            "diagnostics": LEDGER.export(), "infrastructure_error": None}
    except BaseException as exc:
        payload = failed_payload("Runner unavailable: " + type(exc).__name__ + ": " + clipped(exc, 1000))
    finally:
        with open(report_path + ".tmp", "wb") as stream:
            stream.write(encode_payload(payload or failed_payload("Runner terminated without a report.")))
        os.replace(report_path + ".tmp", report_path)


def supervisor_main():
    with tempfile.TemporaryDirectory(prefix=".ag_report_", dir=".") as directory:
        report_path = os.path.join(directory, "results.json")
        process = subprocess.Popen([sys.executable, os.path.abspath(__file__), "--ag-child", report_path],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=sys.stdin)
        readers = [PipeBuffer(process.stdout.fileno(), 1, account=False), PipeBuffer(process.stderr.fileno(), 2, account=False)]
        try:
            process.wait(timeout=35)
            if not os.path.isfile(report_path) or os.path.getsize(report_path) > REPORT_LIMIT:
                payload = encode_payload(failed_payload("Child produced no bounded report."))
            else:
                with open(report_path, "rb") as stream:
                    payload = stream.read(REPORT_LIMIT + 1)
            sys.stdout.buffer.write(payload)
            sys.stdout.flush()
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
            sys.stdout.buffer.write(encode_payload(failed_payload("Child exceeded its wall-time limit.")))
        finally:
            for reader in readers:
                reader.stop()
            process.stdout.close()
            process.stderr.close()


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--ag-child":
        child_main(sys.argv[2])
    else:
        supervisor_main()
