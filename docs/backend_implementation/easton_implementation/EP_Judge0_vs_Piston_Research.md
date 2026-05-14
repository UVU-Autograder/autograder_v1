# Judge0 CE vs Piston — Execution Engine Research
## UVU Autograder v1 | Prepared for Team Review

> Covers: Security posture, multi-language scaling, implementation wiring,
> and frontend integration. Recommendation at the end.

---

## Table of Contents

1. [The Surprising Common Ground](#the-surprising-common-ground)
2. [Architecture Deep Dive](#architecture-deep-dive)
3. [Security Analysis](#security-analysis)
4. [Language Coverage](#language-coverage)
5. [API Comparison](#api-comparison)
6. [FastAPI + Celery Integration](#fastapi--celery-integration)
7. [Frontend Integration with Monaco](#frontend-integration-with-monaco)
8. [Scaling Considerations](#scaling-considerations)
9. [License Analysis](#license-analysis)
10. [Decision Matrix](#decision-matrix)
11. [M1 Implementation Plan (if Judge0 chosen)](#m1-implementation-plan)

---

## The Surprising Common Ground

Before comparing them, here is the most important discovery from the
source code analysis: **both engines use the exact same underlying
sandbox binary.**

Both Piston and Judge0 CE use `isolate` — the open-source sandbox tool
developed for the International Olympiad in Informatics (IOI). `isolate`
uses Linux namespaces, cgroups, and chroot to create secure execution
environments. It is the de-facto standard tool for competitive programming
judges worldwide.

```
Piston:     Node.js API → isolate binary → student code
Judge0 CE:  Ruby on Rails API → isolate binary → student code
```

The difference between these engines is entirely in the **application
layer** — how they queue jobs, what metadata they return, and how
they expose the execution result. The sandbox security primitive is
identical.

This has a direct implication for the CVE discussion (see Security section).

---

## Architecture Deep Dive

### Piston Architecture

Piston is a Node.js API with no persistent state. Every request is
synchronous — code in, result out. No database, no queue.

```
Client
  │
  ▼
POST /api/v2/execute
  │
  ▼
Job Manager (Node.js)
  ├── Validate language + version
  ├── Write code to temp directory
  ├── Call isolate to prime sandbox
  ├── Execute code inside sandbox
  ├── Collect stdout, stderr, exit code, signal
  └── Delete sandbox directory
  │
  ▼
Response (synchronous, immediate)
```

**Job lifecycle:**

| State    | Description                                      |
|----------|--------------------------------------------------|
| READY    | Job created, files not yet written               |
| PRIMED   | Files written, isolate sandbox initialized       |
| EXECUTED | Code ran, results collected, sandbox destroyed   |

**Key configuration options:**
```env
PISTON_MAX_PROCESS_COUNT=64      # per execution
PISTON_MAX_OPEN_FILES=2048       # per execution
PISTON_MAX_FILE_SIZE=10000000    # bytes, output cap
PISTON_COMPILE_MEMORY_LIMIT=-1   # unlimited by default
PISTON_RUN_MEMORY_LIMIT=-1       # set this explicitly
PISTON_COMPILE_TIMEOUT=10000     # ms
PISTON_RUN_TIMEOUT=3000          # ms
PISTON_MAX_CONCURRENT_JOBS=64    # global parallelism cap
```

Per-language overrides are supported — you can set stricter limits
for Python than for C if needed.

---

### Judge0 CE Architecture

Judge0 is a Ruby on Rails web application with Redis for job queuing
and PostgreSQL for submission persistence. It is async by design — you
submit code, receive a token, then poll for results.

```
Client
  │
  ▼
POST /submissions                    ← submit code
  │
  ▼
Rails API → enqueue to Redis queue
  │
  ▼
Worker process dequeues job
  ├── Call isolate to set up sandbox
  ├── Compile (if compiled language)
  ├── Execute inside isolate sandbox
  ├── Collect stdout, stderr, compile_output,
  │   time, wall_time, memory, exit_code,
  │   exit_signal, status_id
  └── Persist result to PostgreSQL
  │
  ▼
GET /submissions/{token}             ← poll for result
```

**Status codes (the key differentiator over Piston):**

| ID | Description         | When it occurs                                  |
|----|---------------------|-------------------------------------------------|
| 1  | In Queue            | Job waiting for a worker                        |
| 2  | Processing          | Worker actively running the job                 |
| 3  | Accepted            | Executed successfully                           |
| 4  | Wrong Answer        | stdout != expected_output                       |
| 5  | Time Limit Exceeded | Exceeded cpu_time_limit                         |
| 6  | Compilation Error   | Compiler exited non-zero                        |
| 7  | Runtime Error SIGSEGV | Segmentation fault                            |
| 8  | Runtime Error SIGXFSZ | Output size exceeded                          |
| 9  | Runtime Error SIGFPE  | Floating point exception                      |
| 10 | Runtime Error SIGABRT | Abort signal                                  |
| 11 | Runtime Error (NZEC) | Non-zero exit code                             |
| 12 | Runtime Error (Other) | Other runtime signal                          |
| 13 | Internal Error      | Judge0 itself had a problem                     |
| 14 | Exec Format Error   | Wrong binary format (architecture mismatch)     |

For an autograder, status codes 5, 6, 7–12 are all pedagogically
meaningful and directly actionable in feedback generation. Piston
returns only raw exit code and signal — you infer these states yourself.

---

### Infrastructure Requirements Side by Side

| Component | Piston          | Judge0 CE                       |
|-----------|-----------------|----------------------------------|
| Runtime   | Node.js         | Ruby on Rails                    |
| Queue     | None (sync)     | Redis (already in our stack)     |
| Database  | None            | PostgreSQL (already in our stack)|
| isolate   | Yes (internal)  | Yes (internal)                   |
| Docker    | --privileged    | --privileged                     |
| cgroupv1  | Yes (implicit)  | Yes (explicit GRUB flag needed)  |

**Important:** Because we already run Redis and PostgreSQL for Celery
and the application database, Judge0's infrastructure dependencies
add no new services — they point at existing instances.

---

## Security Analysis

### The CVE Facts — Precise Statement

**CVE-2024-28185:** Arbitrary file write via symlink in `isolate_job.rb`.
An attacker could write to `/usr/local/bin/isolate` (root-owned binary).
**Patch:** Changed the Linux user the Rails application runs as.
**Researcher note:** "This change breaks the proof of concept because
the judge0 user does not have permission to overwrite /usr/local/bin/isolate.
However, this is the only thing preventing us from exploiting the
vulnerability." The root cause (arbitrary file write path) was not
removed from the codebase, only the specific exploit path was blocked.

**CVE-2024-29021:** SSRF-based sandbox escape via `enable_network` flag.
Allowed unsandboxed code execution as root. **Fixed in v1.13.1** by
disabling `ALLOW_ENABLE_NETWORK` by default.

**CVE-2024-28189:** Third exploit path through the `/api/tmp/environment`
script. **Patched.**

**The honest summary:** v1.13.1 patches all known working exploits.
The researcher could not find another working proof of concept but
flagged the root cause as unresolved. Production deployments at scale
with `ALLOW_ENABLE_NETWORK=false` (our config) are not currently
known to be exploitable.

---

### Why Both Engines Have --privileged

Because both use `isolate`, and `isolate` requires access to Linux
namespace and cgroup APIs that are normally restricted inside
unprivileged containers. This is the same reason Piston also requires
`--privileged`. It is not a Judge0-specific issue.

---

### Why Kata Containers Resolves This for Either Engine

```
Without Kata (plain Docker --privileged):

  Host Linux kernel
    └── Docker --privileged container
          └── isolate sandbox
               └── student code

  Container escape → direct host kernel access

─────────────────────────────────────────────

With Kata Containers:

  Host Linux kernel
    └── Kata VM (lightweight kernel isolation)
          └── Docker --privileged container
               └── isolate sandbox
                    └── student code

  Container escape → Kata VM kernel only
  Kata VM escape   → no known working exploit
```

Kata Containers is the correct architectural response to the
"root cause remains" concern the researcher raised. Any future
arbitrary write exploit in Judge0's Rails layer would land inside
a Kata VM kernel — not on the host. This is defense in depth at
the hypervisor layer.

The cgroupv1 requirement from Judge0's docs applies within the
Kata VM, not on the host. The GRUB flag changes how the VM kernel
manages cgroups — not the host kernel.

---

### Network Isolation — Critical Configuration

For both engines, `--network none` or its equivalent must be
explicitly enforced. For Judge0:

```yaml
# judge0.conf — must set explicitly
ALLOW_ENABLE_NETWORK=false    # CVE-2024-29021 was this flag being true
```

For Piston, network isolation is enforced inside the isolate sandbox
via its own namespace configuration.

---

## Language Coverage

### Judge0 CE v1.13.1 — Languages Relevant to CS Curriculum

Judge0 CE ships with 60+ languages. The subset relevant to a CS
department autograder, organized by when courses typically introduce them:

**CS 1400 / Intro (M1 scope):**

| Language     | language_id | Notes                              |
|--------------|-------------|-------------------------------------|
| Python 3.x   | 71          | Primary M1 language                |
| Python 2.7   | 70          | Legacy support if needed           |

**CS 1410 / CS 2 (M2 target):**

| Language     | language_id | Notes                              |
|--------------|-------------|-------------------------------------|
| C (GCC 9.2)  | 50          | Systems programming intro          |
| C++ (GCC 9.2)| 54          | Data structures                    |
| Java (JDK 13)| 62          | OOP courses                        |
| JavaScript   | 63          | Web development courses            |
| TypeScript   | 74          | Advanced web                       |
| Bash         | 46          | Scripting courses                  |
| SQL          | 82          | Database courses                   |
| HTML (render)| N/A         | Requires custom Judge0 Extra CE    |

**Judge0 Extra CE adds** (relevant for advanced courses):
- Rust, Go, Kotlin, Swift, Scala, R, MATLAB-compatible, Perl,
  Ruby, PHP, and many more

**Multi-file program support (language_id 89):**
Available since v1.10.0. Send a Base64-encoded ZIP with custom
`compile` and `run` bash scripts. Enables: multi-file Python modules,
C++ projects with CMake, Java packages, Django/Flask apps, etc.
This is the M3+ feature that makes Judge0 significantly more powerful
than Piston for advanced courses.

---

### Piston — Languages Relevant to CS Curriculum

Piston supports 100+ languages via its package manager. However,
language packages must be installed at deployment time and are managed
via a CLI tool. Adding a new language requires:

```bash
# Piston CLI — install a language
./cli/index.js ppman install python=3.10.0
./cli/index.js ppman install java=15.0.2
./cli/index.js ppman install cpp=10.2.0
```

Piston does NOT have multi-file project support natively. Each
submission is a single file. This is a hard ceiling for advanced
course work where students write multi-class Java applications or
multi-module Python projects.

---

### Language Support Decision Table

| Capability              | Piston          | Judge0 CE       |
|-------------------------|-----------------|-----------------|
| Python 3.x              | Yes             | Yes             |
| C / C++                 | Yes             | Yes             |
| Java                    | Yes             | Yes             |
| JavaScript              | Yes             | Yes             |
| SQL                     | No (native)     | Yes (id 82)     |
| Multi-file projects     | No              | Yes (id 89)     |
| Add new language        | CLI install     | Requires rebuild|
| language_id stability   | Version strings | Integer IDs     |
| Version pinning         | Yes             | Yes             |

---

## API Comparison

### Piston Request/Response

```python
# POST /api/v2/execute
{
    "language": "python",
    "version": "3.10.0",
    "files": [
        {"name": "solution.py", "content": "<source_code>"}
    ],
    "stdin": "test input",
    "args": [],
    "compile_timeout": 10000,   # ms
    "run_timeout": 3000,         # ms
    "compile_memory_limit": -1,
    "run_memory_limit": 128000   # bytes
}

# Response (synchronous)
{
    "language": "python",
    "version": "3.10.0",
    "run": {
        "stdout": "hello world\n",
        "stderr": "",
        "code": 0,              # exit code
        "signal": null,         # kill signal if killed
        "output": "hello world\n"
    }
}
```

**What Piston does NOT return:**
- Execution time (wall or CPU)
- Memory usage
- Compilation output (separate from run output)
- Structured status code
- Submission token for async polling

---

### Judge0 CE Request/Response

```python
# POST /submissions?wait=true
{
    "language_id": 71,              # Python 3
    "source_code": "<source_code>", # or base64 encoded
    "stdin": "test input",
    "expected_output": null,        # for autojudging
    "cpu_time_limit": 3,            # seconds
    "cpu_extra_time": 0.5,
    "wall_time_limit": 5,
    "memory_limit": 128000,         # KB
    "stack_limit": 64000,
    "max_processes_and_or_threads": 60,
    "enable_per_process_and_thread_time_limit": false,
    "enable_per_process_and_thread_memory_limit": false,
    "max_file_size": 1024,          # KB
    "enable_network": false,         # MUST BE FALSE
    "number_of_runs": 1,
    "additional_files": null,        # base64 ZIP for multi-file
    "callback_url": null             # webhook on completion
}

# Response
{
    "stdout": "hello world\n",
    "time": "0.031",                 # CPU time in seconds
    "wall_time": "0.054",            # wall time in seconds
    "memory": 4796,                  # KB used
    "stderr": null,
    "token": "8531f293...",
    "compile_output": null,          # compiler output if applicable
    "message": null,
    "exit_code": 0,
    "exit_signal": null,
    "status": {
        "id": 3,
        "description": "Accepted"
    }
}
```

**What Judge0 returns that Piston does not:**
- `time` — CPU seconds used (maps to TLE detection)
- `wall_time` — actual elapsed time
- `memory` — KB consumed during execution
- `compile_output` — separate from run output (critical for C++, Java)
- `status.id` — structured status code (see status table above)
- `exit_signal` — signal name if killed (SIGSEGV, SIGKILL, etc.)
- `message` — Judge0 internal error message if status 13

---

## FastAPI + Celery Integration

### Current plan (Piston)

```python
# app/integrations/piston/client.py
import httpx
from app.core.settings import settings

async def execute_code(language: str, version: str, code: str,
                       stdin: str = "", timeout_ms: int = 10000) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.PISTON_URL}/api/v2/execute",
            json={
                "language": language,
                "version": version,
                "files": [{"name": "solution.py", "content": code}],
                "stdin": stdin,
                "run_timeout": timeout_ms,
                "run_memory_limit": 268435456,  # 256MB in bytes
            },
            timeout=timeout_ms / 1000 + 5
        )
        result = response.json()
    return {
        "stdout": result["run"]["stdout"],
        "stderr": result["run"]["stderr"],
        "exit_code": result["run"]["code"],
        "timed_out": result["run"]["signal"] == "SIGKILL",
        "status": "timeout" if result["run"]["signal"] == "SIGKILL"
                  else ("error" if result["run"]["code"] != 0
                  else "success"),
        # No time, no memory, no structured status
    }
```

---

### Proposed (Judge0 CE)

```python
# app/integrations/judge0/client.py
import httpx
from app.core.settings import settings
from app.integrations.judge0.status import Status

LANGUAGE_MAP = {
    "python": 71,
    "python3": 71,
    "c": 50,
    "cpp": 54,
    "java": 62,
    "javascript": 63,
    "bash": 46,
    "sql": 82,
}

async def execute_code(
    language: str,
    code: str,
    stdin: str = "",
    expected_output: str | None = None,
    cpu_time_limit: float = 10.0,
    memory_limit_kb: int = 262144,   # 256MB in KB
    additional_files: str | None = None,  # base64 ZIP for multi-file
) -> dict:
    language_id = LANGUAGE_MAP.get(language.lower())
    if not language_id:
        raise ValueError(f"Unsupported language: {language}")

    payload = {
        "language_id": language_id,
        "source_code": code,
        "stdin": stdin,
        "cpu_time_limit": cpu_time_limit,
        "wall_time_limit": cpu_time_limit * 2,
        "memory_limit": memory_limit_kb,
        "enable_network": False,    # always explicit
        "max_processes_and_or_threads": 60,
    }
    if expected_output:
        payload["expected_output"] = expected_output
    if additional_files:
        payload["additional_files"] = additional_files

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.JUDGE0_URL}/submissions",
            params={"wait": "true"},     # synchronous mode for Celery
            json=payload,
            headers={"X-Auth-Token": settings.JUDGE0_AUTH_TOKEN},
            timeout=cpu_time_limit + 10,
        )
        response.raise_for_status()
        result = response.json()

    status_id = result["status"]["id"]
    return {
        "stdout": result.get("stdout", ""),
        "stderr": result.get("stderr", ""),
        "compile_output": result.get("compile_output", ""),
        "exit_code": result.get("exit_code"),
        "exit_signal": result.get("exit_signal"),
        "time_seconds": float(result.get("time") or 0),
        "wall_time_seconds": float(result.get("wall_time") or 0),
        "memory_kb": result.get("memory"),
        "status_id": status_id,
        "status_description": result["status"]["description"],
        # Derived fields for our grading pipeline
        "timed_out": status_id == 5,
        "compilation_error": status_id == 6,
        "runtime_error": status_id in range(7, 13),
        "success": status_id == 3,
        "internal_error": status_id == 13,
    }
```

---

### Celery Task — How the richer response maps to grading

```python
# app/domains/runs/tasks.py
from celery import shared_task
from app.integrations.judge0.client import execute_code
from app.domains.grading.service import run_ast_check, build_llm_feedback

@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def grade_submission_official(self, submission_id: str, assignment_config: dict):
    try:
        code = load_ephemeral_code(submission_id)

        # Step 1: AST constraint check (before execution)
        constraint_result = run_ast_check(code, assignment_config["constraints"])
        if constraint_result["blocks_execution"]:
            save_result(submission_id, status="hard_blocked",
                        constraint_result=constraint_result)
            return

        # Step 2: Execute via Judge0 — get rich metadata
        exec_result = execute_code(
            language=assignment_config["language"],
            code=code,
            stdin=assignment_config.get("stdin", ""),
            cpu_time_limit=assignment_config["resource_limits"]["time_limit"],
            memory_limit_kb=assignment_config["resource_limits"]["memory_limit"],
        )

        # Step 3: Map Judge0 status to grading pipeline state
        if exec_result["timed_out"]:
            save_result(submission_id, status="failed:timeout")
            return

        if exec_result["compilation_error"]:
            save_result(submission_id, status="failed:compile",
                        compile_output=exec_result["compile_output"])
            return

        # Step 4: Generate LLM feedback grounded in actual execution results
        # Judge0's structured status means the prompt is precise
        feedback = build_llm_feedback(
            code=code,
            stdout=exec_result["stdout"],
            stderr=exec_result["stderr"],
            status=exec_result["status_description"],
            time_seconds=exec_result["time_seconds"],
            memory_kb=exec_result["memory_kb"],
            rubric=assignment_config["rubric"],
            allowed_concepts=assignment_config["concept_set"],
        )

        # Step 5: Save — no student code persists after this function
        save_result(submission_id,
                    status="ai_complete",
                    exec_result=exec_result,
                    feedback=feedback,
                    constraint_result=constraint_result)

    except Exception as exc:
        raise self.retry(exc=exc)
    finally:
        destroy_ephemeral_workspace(submission_id)
```

---

## Frontend Integration with Monaco

### How the execution result reaches the instructor UI

The review dashboard in Next.js needs to display:
1. Student code with syntax highlighting and inline annotations
2. Test execution results (pass/fail per test)
3. Judge0 metadata (time, memory, status)
4. LLM-generated feedback per rubric criterion

Monaco handles the code display. Judge0's richer response means
each of these panels has actual data to display.

```typescript
// components/CodeReviewPane.tsx
import Editor, { DiffEditor } from "@monaco-editor/react"
import type { ExecResult } from "@/types/grading"

interface Props {
  code: string
  resubmission?: string       // previous version for diff view
  annotations: Annotation[]  // LLM inline comments
  execResult: ExecResult     // Judge0 response mapped to our types
  language: string
}

export function CodeReviewPane({
  code, resubmission, annotations, execResult, language
}: Props) {
  const [view, setView] = useState<"code" | "diff">("code")

  // Annotate the Monaco editor with LLM comments as margin decorations
  function handleEditorMount(editor: any, monaco: any) {
    const decorations = annotations.map(ann => ({
      range: new monaco.Range(ann.line, 1, ann.line, 1),
      options: {
        isWholeLine: true,
        className: ann.type === "error"
          ? "annotation-error"
          : "annotation-suggestion",
        glyphMarginClassName: `glyph-${ann.type}`,
        glyphMarginHoverMessage: { value: ann.comment },
      }
    }))
    editor.deltaDecorations([], decorations)
  }

  return (
    <div className="flex flex-col gap-3">
      {/* Execution metadata bar — Judge0 provides all of this */}
      <div className="flex gap-4 text-sm px-3 py-2 bg-gray-50 rounded border">
        <StatusBadge statusId={execResult.status_id}
                     description={execResult.status_description} />
        {execResult.time_seconds !== null && (
          <span>⏱ {execResult.time_seconds.toFixed(3)}s CPU</span>
        )}
        {execResult.memory_kb !== null && (
          <span>🧠 {(execResult.memory_kb / 1024).toFixed(1)} MB</span>
        )}
      </div>

      {/* Compile output — only visible with Judge0, not Piston */}
      {execResult.compilation_error && (
        <div className="bg-red-50 border border-red-200 rounded p-3 font-mono text-xs">
          <p className="font-medium text-red-700 mb-1">Compilation Error</p>
          <pre>{execResult.compile_output}</pre>
        </div>
      )}

      {/* Toggle: single view or diff against resubmission */}
      {resubmission && (
        <div className="flex gap-2">
          <button onClick={() => setView("code")}
            className={view === "code" ? "tab-active" : "tab"}>
            Current
          </button>
          <button onClick={() => setView("diff")}
            className={view === "diff" ? "tab-active" : "tab"}>
            Diff vs original
          </button>
        </div>
      )}

      {view === "code" ? (
        <Editor
          height="500px"
          language={language}
          value={code}
          onMount={handleEditorMount}
          options={{
            readOnly: true,
            minimap: { enabled: false },
            lineNumbers: "on",
            glyphMargin: true,    // enables margin for annotations
            folding: true,
            scrollBeyondLastLine: false,
          }}
        />
      ) : (
        <DiffEditor
          original={resubmission}
          modified={code}
          language={language}
          options={{ readOnly: true }}
        />
      )}
    </div>
  )
}
```

---

### StatusBadge component — using Judge0's structured status codes

```typescript
// components/StatusBadge.tsx
const STATUS_CONFIG = {
  3:  { label: "Accepted",           color: "green" },
  4:  { label: "Wrong Answer",       color: "red" },
  5:  { label: "Time Limit Exceeded",color: "yellow" },
  6:  { label: "Compilation Error",  color: "orange" },
  7:  { label: "Runtime Error (SIGSEGV)", color: "red" },
  8:  { label: "Output Size Exceeded", color: "yellow" },
  9:  { label: "Runtime Error (SIGFPE)", color: "red" },
  10: { label: "Runtime Error (SIGABRT)", color: "red" },
  11: { label: "Runtime Error (NZEC)", color: "red" },
  12: { label: "Runtime Error", color: "red" },
  13: { label: "Internal Error",     color: "gray" },
  14: { label: "Exec Format Error",  color: "gray" },
} as const

export function StatusBadge({
  statusId, description
}: { statusId: number; description: string }) {
  const config = STATUS_CONFIG[statusId as keyof typeof STATUS_CONFIG]
  return (
    <span className={`badge badge-${config?.color ?? "gray"}`}>
      {config?.label ?? description}
    </span>
  )
}
```

**Without Judge0:** Piston only returns an exit code (0 = success,
anything else = error) and a signal. You cannot distinguish a
compilation error from a runtime segfault from a timeout without
parsing stderr yourself. With Judge0's status codes, each failure
mode is a first-class value that the UI and LLM prompt can reference
explicitly.

---

### Student sandbox view — the projected feedback flow

```typescript
// app/sandbox/page.tsx — student-facing, zero-retention
"use client"
import { useState } from "react"

export default function SandboxPage() {
  const [result, setResult] = useState<SandboxResult | null>(null)
  const [uploading, setUploading] = useState(false)

  async function handleUpload(file: File) {
    setUploading(true)
    const formData = new FormData()
    formData.append("file", file)
    formData.append("assignment_id", assignmentId)

    const response = await fetch("/api/sandbox/submit", {
      method: "POST",
      body: formData
    })
    const job = await response.json()

    // Poll for result
    const result = await pollForResult(job.job_id)
    setResult(result)
    setUploading(false)
  }

  return (
    <div>
      {/* Zero-retention notice — required per our architecture */}
      <div className="notice">
        Your code and feedback are not saved. Results are shown
        on screen only and deleted when you leave this page.
      </div>

      <FileUpload onUpload={handleUpload} disabled={uploading} />

      {result && (
        <div className="result-panel">
          {/* Judge0 metadata is available for students too */}
          <StatusBadge statusId={result.status_id}
                       description={result.status_description} />

          {result.status_id === 6 && (
            <CompileErrorPanel output={result.compile_output} />
          )}

          <ProjectedScore score={result.projected_score}
                          maxScore={result.max_score} />

          <FeedbackPanel feedback={result.feedback}
                          warnings={result.constraint_warnings} />

          {/* Time/memory is useful feedback even for students */}
          {result.time_seconds && (
            <p className="text-sm text-gray-500">
              Ran in {result.time_seconds.toFixed(3)}s using{" "}
              {(result.memory_kb / 1024).toFixed(1)} MB
            </p>
          )}
        </div>
      )}
    </div>
  )
}
```

---

## Scaling Considerations

### Horizontal scaling — Judge0 has a clear path, Piston less so

**Piston** is stateless but scaling it horizontally means running
multiple Piston instances behind a load balancer. Each instance is
isolated — no shared queue. If instance A is saturated and instance
B is idle, there is no mechanism to route jobs between them without
external load balancing logic.

**Judge0** uses Redis as a shared job queue. Running additional
Judge0 workers is a single-line change:

```yaml
# docker-compose.yml — add a second worker with one line
services:
  judge0-server:
    image: judge0/judge0:1.13.1
    ...
  judge0-worker-1:
    image: judge0/judge0:1.13.1
    entrypoint: ["/bin/sh", "-c", "cd /judge0 && bin/resque"]
    ...
  judge0-worker-2:   # ← just duplicate this
    image: judge0/judge0:1.13.1
    entrypoint: ["/bin/sh", "-c", "cd /judge0 && bin/resque"]
    ...
```

All workers consume from the same Redis queue. Adding capacity is
adding workers. This scales cleanly as class sizes grow — a department-
wide deployment would run 4–8 workers concurrently without architecture
changes.

---

### Concurrency alignment with Celery

Both our Celery workers and Judge0 workers consume from queues. The
important constraint is not to over-saturate Judge0's execution capacity.

```python
# Correct concurrency alignment
# Celery: 8 workers
# Judge0: 8 workers
# Each Celery job makes exactly 1 Judge0 call
# → max 8 concurrent Judge0 executions → no contention

# app/integrations/celery/app.py
app.conf.worker_concurrency = 8  # matches Judge0 worker count
```

If you scale to 16 concurrent Judge0 workers (larger class), update
both: Celery concurrency and the number of Judge0 worker containers.

---

## License Analysis

| Engine     | License  | Implication                                              |
|------------|----------|----------------------------------------------------------|
| Piston     | MIT      | No restrictions. Use, modify, relicense freely.         |
| Judge0 CE  | GPL-3.0  | Copyleft. Code that *links* to or *distributes* with    |
|            |          | Judge0 may need to be GPL-3.0 compatible.               |

**Practical impact for UVU Autograder:**

Judge0 runs as a **separate service** accessed over HTTP. The autograder
backend does not link to Judge0's code — it calls its REST API over a
network boundary. This is the same relationship as calling a database
or a cloud API. GPL-3.0's copyleft clause does not propagate across
network service boundaries under standard legal interpretation.

**However:** If the plan is to eventually open-source the autograder
and bundle Judge0 in the same repository or distribution package,
that requires legal review. For UVU's internal university deployment
with no public distribution planned, GPL-3.0 presents no practical
friction.

---

## Decision Matrix

| Criterion                        | Weight | Piston | Judge0 CE |
|----------------------------------|--------|--------|-----------|
| M1 integration cost              | High   | ✅ Lower | ⚠️ Higher (rewrite) |
| Execution metadata richness      | High   | ❌ Minimal | ✅ Full (time, mem, compile) |
| Structured status codes          | High   | ❌ Exit code only | ✅ 14 statuses |
| Multi-file project support       | High   | ❌ No | ✅ Yes (language_id 89) |
| Kata Containers compatible       | High   | ✅ Yes | ✅ Yes |
| cgroupv1 GRUB flag required      | Med    | No | ⚠️ Yes (one-time setup) |
| CVE status                       | High   | No known CVEs | ✅ Patched in v1.13.1 |
| CVE root cause resolved          | Med    | N/A | ⚠️ Partially |
| Kata mitigates CVE root cause    | High   | N/A | ✅ Yes |
| Horizontal scaling               | Med    | ⚠️ External LB needed | ✅ Redis queue, add workers |
| Python SDK                       | Low    | ❌ No | ✅ pip install judge0 |
| Language count (M2+)             | Med    | 100+ | 60+ CE / more Extra CE |
| Multi-file (M3+)                 | High   | ❌ No | ✅ Yes |
| License for open source          | Low    | ✅ MIT | ⚠️ GPL-3.0 (network OK) |
| Frontend status display          | High   | ⚠️ Manual inference | ✅ First-class status codes |
| Compile error visibility         | High   | ❌ Merged into stderr | ✅ Separate compile_output |

---

## Recommendation

**Replace Piston with Judge0 CE v1.13.1 + Kata Containers.**

The core argument is not security parity (both use `isolate`, both need
`--privileged`, Kata mitigates both). The core argument is **feature
alignment with the roadmap.**

Three features Judge0 provides that Piston structurally cannot:

**1. Compile/run separation.** From M2 onward — Java, C++, TypeScript —
students will submit code that must compile before it runs. Piston merges
compile and run output into one blob. Judge0 returns `compile_output`
as a separate field. This distinction is pedagogically essential: a
student who wrote valid logic with a syntax error deserves different
feedback than one whose logic is wrong.

**2. Multi-file programs.** CS 2 assignments routinely involve multiple
files — a `BubbleSort.java` and a `Main.java`, a Python package with
`__init__.py` and `utils.py`. Judge0's language_id 89 handles this with
a custom `compile` and `run` bash script per submission. Piston has no
equivalent.

**3. Structured status codes.** The 14-status taxonomy maps directly to
actionable LLM prompt language. Instead of "exit code was 1 and stderr
contained a traceback," the prompt can say "execution status was
Runtime Error (SIGSEGV) — the program received a segmentation fault."
That precision makes the AI feedback more useful to a student.

**What it costs in M1:** One story rewrite (`E5-03`, execution engine
integration, ~4 points). The Celery task chain, AST checker, and LLM
pipeline are all unchanged. The one-time GRUB cgroupv1 flag on the
Dell T2 is a 10-minute setup item for Sprint 0. The `ALLOW_ENABLE_NETWORK=false`
configuration must be explicitly set and documented.

The trade is clear: spend 4 story points in Sprint 2 to avoid a
migration in M2 when the course curriculum demands it.

---

## M1 Implementation Plan

### Sprint 0 additions (before code)

```bash
# On the Dell T2 Ubuntu machine — one-time setup
sudo nano /etc/default/grub

# Add to GRUB_CMDLINE_LINUX:
# systemd.unified_cgroup_hierarchy=0

sudo update-grub
sudo reboot

# Verify cgroupv1 is active
stat /sys/fs/cgroup/memory
# Should exist (cgroupv1 memory controller)
```

---

### docker-compose.yml additions

```yaml
services:
  judge0-server:
    image: judge0/judge0:1.13.1
    runtime: kata-runtime           # Kata Containers VM isolation
    privileged: true                # required for isolate — safe within Kata
    volumes:
      - ./judge0.conf:/judge0.conf:ro
    ports:
      - "127.0.0.1:2358:2358"      # bind to localhost only
    depends_on:
      - db
      - redis
    restart: unless-stopped

  judge0-worker:
    image: judge0/judge0:1.13.1
    runtime: kata-runtime
    privileged: true
    entrypoint: ["/bin/sh", "-c", "cd /judge0 && bin/resque"]
    volumes:
      - ./judge0.conf:/judge0.conf:ro
    depends_on:
      - db
      - redis
    restart: unless-stopped
    deploy:
      replicas: 8                   # matches Celery concurrency
```

---

### judge0.conf — critical security settings

```ini
# judge0.conf
REDIS_URL=redis://redis:6379
POSTGRES_HOST=db
POSTGRES_USER=judge0
POSTGRES_PASSWORD=${JUDGE0_DB_PASSWORD}
POSTGRES_DB=judge0

# Security — these must be explicit
ALLOW_ENABLE_NETWORK=false          # CVE-2024-29021 mitigation
ALLOW_CUSTOM_MAX_PROCESSES_AND_OR_THREADS=false
ALLOW_CUSTOM_ENABLE_PER_PROCESS_AND_THREAD_TIME_LIMIT=false

# Authentication
AUTH_TOKEN=${JUDGE0_AUTH_TOKEN}

# Defaults that submissions can override within limits
CPU_TIME_LIMIT=10
MAX_CPU_TIME_LIMIT=15
WALL_TIME_LIMIT=20
MAX_WALL_TIME_LIMIT=30
MEMORY_LIMIT=262144                 # 256MB in KB
MAX_MEMORY_LIMIT=524288             # 512MB max
MAX_PROCESSES_AND_OR_THREADS=60

# Logging — important for audit trail
RAILS_LOG_TO_STDOUT=true
LOG_LEVEL=info
```

---

### .env additions

```env
# Judge0
JUDGE0_URL=http://judge0-server:2358
JUDGE0_AUTH_TOKEN=<generate-with-openssl-rand-hex-32>
JUDGE0_DB_PASSWORD=<generate-separately>
```

---

### Backlog story update

Replace `E5-03` in the product backlog:

```
E5-03 | Judge0 CE integration via httpx
      | - Deploy Judge0 v1.13.1 container with Kata runtime
      | - Configure judge0.conf (ALLOW_ENABLE_NETWORK=false required)
      | - Write Judge0 client in app/integrations/judge0/client.py
      | - Map language strings to language_id integers
      | - Handle all 14 status codes in grading pipeline
      | - Wire compile_output into ConstraintCheckResult/feedback
      | - Validate: timeout, compile error, runtime error,
      |             accepted — all produce correct grading outcomes
      | Points: 5 (was 4 for Piston — +1 for status code handling)
      | Priority: Must
      | Sprint: S2
```

---

*Document prepared for UVU Autograder team review.*
*Sources: Judge0 CE CHANGELOG, GitHub source analysis (DeepWiki),*
*CVE-2024-28185/29021 researcher disclosure (Tanto Security),*
*Piston ReadTheDocs, Judge0 API documentation.*
