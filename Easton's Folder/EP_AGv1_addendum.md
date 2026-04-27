# UVU_autograder_V1 — Internal Notes Addendum

> This addendum captures research, design rationale, and reference material developed
> during the architecture discussion phase. It is intended to be appended to or linked
> from `EP_AGv1_implementation_v3.md` so that context does not need to be reconstructed
> from conversation history.

---

## Table of Contents

1. [Stack Rationale — Full Argument](#stack-rationale--full-argument)
2. [Hardware Memory Budget Analysis](#hardware-memory-budget-analysis)
3. [LLM Selection — Model Comparison Notes](#llm-selection--model-comparison-notes)
4. [Quantization Reference](#quantization-reference)
5. [Local Inference Architecture Notes](#local-inference-architecture-notes)
6. [Open-Source Autograder Research](#open-source-autograder-research)
7. [Autograder Market Complaint Analysis](#autograder-market-complaint-analysis)
8. [Academic Paper Notes — Breakout Autograder (SIGCSE 2024)](#academic-paper-notes--breakout-autograder-sigcse-2024)
9. [TLS + InCommon Notes](#tls--incommon-notes)
10. [LTI 1.3 + Canvas Integration Notes](#lti-13--canvas-integration-notes)
11. [Security Architecture Notes](#security-architecture-notes)
12. [MCP Protocol Reference](#mcp-protocol-reference)

---

## Stack Rationale — Full Argument

### Why Next.js + FastAPI over Django + Railway

The team evaluated two stack proposals. The following is the full argument for the
Next.js + FastAPI + local LLM approach over Django + Railway + GPT-4o-mini.

**FERPA compliance:**
Sending student submission code to any third-party API (OpenAI, Anthropic, or otherwise)
requires a university-signed Data Processing Agreement and legal review. This is not a
minor administrative step — it can take months and may not be approved. The local inference
architecture eliminates this risk entirely by design. No student data transits any
infrastructure the university does not control.

**Cost at scale:**
GPT-4o-mini pricing at ~$0.15/1M input tokens appears cheap in isolation. At 200 students
× 10 assignments × 5 attempts × ~3,000 tokens per grading call = ~30M tokens per semester.
That is approximately $4.50 per semester at current pricing — but that figure does not
account for output tokens, retries, or feedback verbosity. More importantly, as the tool
scales to multiple courses and departments, cost scales linearly with no ceiling. Local
inference has zero marginal cost per token after hardware acquisition.

**Railway-specific concerns:**
- Introduces an external hosting dependency — if Railway has downtime during a grading run,
  the system is unavailable
- Cold start latency on Railway's hobby/pro tier adds 2–10 seconds per request, which
  compounds badly under concurrent load at submission deadlines
- Any student code that passes through Railway's infrastructure — even transiently —
  creates a data residency question that FERPA requires answering
- Railway's pricing model scales with compute usage; a large grading batch triggers
  unpredictable cost spikes

**FastAPI vs Django:**
Django is a full-stack MVC framework designed around synchronous request handling and
an integrated ORM. It is well-suited for traditional web apps but introduces friction for
an LLM pipeline that requires async-native processing, streaming responses, and tight
integration with Python ML tooling. FastAPI is async by default, generates OpenAPI docs
automatically, and its dependency injection system maps cleanly to the per-request
context (student, assignment, submission) the grading pipeline needs. The Django admin
panel advantage is real but replicable with a straightforward Next.js dashboard.

**Summary table:**

| Criterion | Next.js + FastAPI + local LLM | Django + Railway + GPT-4o-mini |
|-----------|-------------------------------|-------------------------------|
| FERPA compliance | Resolved by design | Requires DPA + legal review |
| Cost (200 students, 10 assignments) | ~$0 marginal | ~$4.50–$50/semester, scales linearly |
| Latency | None — local inference | Cold start + API round trip |
| Availability dependency | None | Railway uptime + OpenAI uptime |
| Data sovereignty | Full — stays on-prem | Partial — transits Railway + OpenAI |
| Async performance | Native (FastAPI) | Requires ASGI config (Django) |
| LLM upgrade path | Swap model file locally | API version migration |

---

## Hardware Memory Budget Analysis

### Memory Allocation — 256GB Baseline

```
Component                          Memory usage
─────────────────────────────────────────────────
Llama 3.3 70B Q4_K_M weights       ~40 GB
macOS + system processes            ~12 GB
FastAPI + Next.js + Redis + Nginx   ~4 GB
PostgreSQL                          ~2 GB
8 × grading containers × 256MB     ~2 GB
8 × LLM KV cache sessions × 7.5GB  ~60 GB (peak, all slots active)
─────────────────────────────────────────────────
Total peak estimate                 ~120 GB
Available headroom (256GB)          ~136 GB
```

At 256GB, peak concurrent load (8 grading workers + 8 LLM sessions simultaneously) uses
approximately 120GB, leaving ~136GB headroom. This is comfortable for M1 and M2 workloads.

### Memory Allocation — 512GB

```
Component                          Memory usage
─────────────────────────────────────────────────
Llama 3.3 70B Q8_0 weights          ~70 GB  (higher quality tier)
macOS + system processes            ~12 GB
FastAPI + Next.js + Redis + Nginx   ~4 GB
PostgreSQL                          ~2 GB
16 × grading containers × 256MB    ~4 GB
16 × LLM KV cache sessions × 7.5GB ~120 GB (peak)
─────────────────────────────────────────────────
Total peak estimate                 ~212 GB
Available headroom (512GB)          ~300 GB
```

At 512GB, the system can comfortably run at double the concurrency, step up to Q8 weights
for higher output quality, and still have headroom to run Llama 3.1 405B Q3_K_M (~180GB)
for high-stakes assignments where maximum model quality is warranted.

### Throughput Estimates by Hardware

| Hardware | Model | Quantization | Est. tok/s | 200-submission batch time |
|----------|-------|--------------|-----------|--------------------------|
| Mac Mini M3, 256GB | Llama 3.3 70B | Q4_K_M | ~15–20 | ~25–35 min |
| Mac Studio M3 Ultra, 512GB | Llama 3.3 70B | Q4_K_M | ~25 | ~15–20 min |
| Mac Studio M3 Ultra, 512GB | Llama 3.3 70B | Q8_0 | ~18 | ~20–28 min |
| Mac Studio M3 Ultra, 512GB | Llama 3.1 405B | Q3_K_M | ~4–5 | ~90–120 min |

All estimates assume 8 parallel Celery workers, 500-token average feedback response,
and Metal GPU offloading of all layers (`-ngl 99`).

### Key formula

```
Model size (GB) ≈ (parameters × bits per weight) ÷ 8,000,000,000

Examples:
  70B × 4.5 bits (Q4_K_M)  ÷ 8B = ~39 GB
  70B × 8 bits (Q8_0)      ÷ 8B = ~70 GB
  405B × 3.5 bits (Q3_K_M) ÷ 8B = ~177 GB
```

---

## LLM Selection — Model Comparison Notes

### Evaluated Models for Intro CS Grading

Three model families were evaluated for Python and HTML intro coursework grading:

**Llama 3.3 70B (Meta — recommended)**
- HumanEval: 88.4% (pass@1)
- Strong reasoning and instruction following (92.1% IFEval)
- 128K context window — can hold large codebases + rubric + history in one session
- Apache 2.0 compatible for academic deployment
- Largest community support — most cited in current academic literature
- Best choice for a production deployment where quality and maintainability matter

**Gemma 3 27B (Google)**
- HumanEval: ~87.8% — near-identical to Llama 70B on basic coding tasks
- Smaller footprint (~18GB Q4_K_M) — faster token generation on constrained hardware
- Stronger safety fine-tuning for educational contexts
- University may have preference for Gemma due to prior discussions
- Viable alternative if hardware procurement remains at 256GB and throughput is a concern
- Benchmark both on real UVU assignment samples before committing

**Qwen 2.5 72B (Alibaba)**
- Consistently outperforms both on pure coding benchmarks across the 70B size class
- 128K context, supports 29 programming languages
- Worth evaluating for M4 when HTML/CSS support is added
- Less community adoption in education research than Llama

### Decision for M1

Use **Llama 3.3 70B Q4_K_M** as the default. It is the most defensible choice academically,
has the largest support community for troubleshooting, and performs well on intro CS tasks.
Gemma 3 27B should be benchmarked in parallel on a sample of 50 representative UVU
submissions during M1 development. If throughput becomes a blocker on 256GB hardware,
Gemma is the natural fallback without a significant quality penalty on intro-level work.

---

## Quantization Reference

Quantization reduces the number of bits used to store each model weight, trading precision
for smaller file size and faster inference. Apple Silicon's unified memory architecture
makes this particularly effective — the model loads into the same memory pool used by the
GPU and Neural Engine with no PCIe transfer overhead.

### Quantization Tiers

| Format | Bits/weight | 70B size | Quality loss | Use case |
|--------|-------------|----------|--------------|----------|
| fp32 | 32 | ~280 GB | None | Training only |
| fp16 / bf16 | 16 | ~140 GB | Negligible | Fine-tuning, HPC |
| Q8_0 | 8 | ~70 GB | Barely perceptible | High-quality local |
| Q6_K | 6 | ~52 GB | Very small | Quality-conscious |
| **Q4_K_M** | ~4.5 | **~40 GB** | **Small** | **Default — sweet spot** |
| Q3_K_M | ~3.5 | ~30 GB | Moderate | Memory-constrained only |
| Q2_K | ~2.5 | ~22 GB | Significant | Last resort |

### Filename convention (GGUF format)

`Q4_K_M` breaks down as:
- `Q4` — 4-bit quantization base
- `_K` — k-quant method: applies different precision per layer based on sensitivity
- `_M` — medium variant (best quality/size balance within the k-quant family)

Always prefer `_K` variants over plain `Q4_0` — the quality recovery is significant at
negligible size cost. Within k-quants, `_M` is almost always the right choice.

### Metal and Apple Silicon context

Metal is Apple's low-level GPU programming API — equivalent to CUDA on NVIDIA hardware.
In llama.cpp, `-ngl 99` offloads all transformer layers to the GPU via Metal, using the
full unified memory pool. On Apple Silicon there is no PCIe transfer bottleneck between
CPU and GPU memory — the model weights sit in the shared pool and both access them directly.

The tokenizer (text → token IDs) and detokenizer (token IDs → text) run on CPU and are
not Metal-accelerated. They are also trivially fast relative to the transformer layer math.
Metal acceleration applies to the transformer forward pass — the bulk of inference compute.

---

## Local Inference Architecture Notes

### llama-server configuration for this project

```bash
./build/bin/llama-server \
  -m ./models/llama-3.3-70b-instruct-q4_k_m.gguf \
  --host 127.0.0.1 \       # bind to localhost only — not exposed externally
  --port 8080 \
  -ngl 99 \                # offload all layers to Metal GPU
  -c 8192 \                # context window per session
  --parallel 8 \           # concurrent generation slots (matches Celery worker count)
  --cont-batching          # accept new requests mid-generation — critical for throughput
```

### FastAPI → llama-server integration

llama-server exposes an OpenAI-compatible `/v1/chat/completions` endpoint. FastAPI calls
it using the standard `openai` Python client with `base_url` pointed at localhost.
This means the LLM integration code is identical to what would be used with a cloud API —
swapping models in the future requires only changing the `base_url` and model name.

```python
from openai import AsyncOpenAI

llm = AsyncOpenAI(
    base_url="http://127.0.0.1:8080/v1",
    api_key="not-needed"  # llama-server does not require auth on localhost
)
```

### Cold start behavior

Unlike a web server, llama-server takes 30–60 seconds to load model weights into memory
on startup. It must run as a persistent background service — not restarted on code changes.
Use a `launchd` plist to keep it running as a system service that survives reboots.
FastAPI and Next.js restart independently without affecting the model server.

---

## Open-Source Autograder Research

### Autolab (CMU) — Key findings

- Ruby on Rails full-stack app — not directly adoptable but patterns are reusable
- **Tango** is the grading daemon: accepts jobs via REST API, manages Docker container pool,
  executes asynchronously, returns structured results. Our Celery + Redis queue replicates
  this architecture in Python.
- Assessment versioning: every submission stored with a version number, instructor picks
  which version counts. Worth building into the PostgreSQL schema from day one even if
  the M1 UI doesn't expose version selection.
- Tango job fields to model: `submission_id`, `student_id`, `assignment_id`,
  `container_image`, `time_limit`, `memory_limit`, `status`, `stdout`, `stderr`, `score`

### Submitty (RPI) — Key findings

- PHP frontend (ignore), Python + C++ grading core (directly relevant)
- `config.json` schema is production-proven across hundreds of CS courses at RPI.
  Adopted as the grading spec format for this project with constraint extensions added.
- `python_submitty_utils` pip package: file diff, output normalization, token comparison.
  Directly solves the whitespace/encoding false-negative problem without custom code.
- Worker isolation model uses PAM + cgroups + unprivileged system user (`submitty_daemon`)
  — more secure than Docker alone. Reference implementation for our container hardening.
- `more_autograding_examples/` directory contains real Python, C++, Java grading configs.
  Use as templates when writing UVU-specific test suite configurations.

### autograder-sandbox (U-Michigan)

- Python library designed specifically for academic autograding at scale
  (supports 5,000+ students per semester at Michigan)
- Docker-native, manages container lifecycle from Python code
- Tighter control than Piston for our use case since it integrates directly into FastAPI
- Primary candidate for the M1 execution engine

### Piston

- Stateless REST API for code execution, 100+ languages
- Every run starts fresh — no state leaks between submissions
- Easier to scale horizontally if the system grows beyond one machine
- Adds a separate service to manage vs autograder-sandbox which is just a Python import
- Decision between Piston and autograder-sandbox required before M1 sprint 2

---

## Autograder Market Complaint Analysis

Research across instructor forums, academic papers, and open issue trackers identified
the following recurring complaints about existing autograding tools. These directly
inform the design decisions in this project.

### Instructor complaints

**Docker setup tax:** Gradescope requires packaging a Docker container as a zip file.
Every test suite change triggers a multi-minute image rebuild. Non-DevOps instructors
hit a hard wall before they can grade a single assignment. Our architecture eliminates
this entirely — instructors define rubrics and constraints via UI; no Docker knowledge required.

**Test suite authorship burden:** Writing comprehensive test cases for each assignment
is the single largest time cost for instructors. Inadequate test coverage produces
misleading pass/fail scores that damage student trust. The LLM-based approach reads
and reasons about code semantically, reducing but not eliminating the need for test cases.

**Inconsistent grading from output string matching:** Valid student code that produces
correct output in a different format (different whitespace, different decimal precision)
fails tests. `python_submitty_utils` output normalization addresses this directly.

**Core features behind institutional pricing:** Gradescope gates code autograding, LMS
integration, and plagiarism detection behind undisclosed enterprise contracts. Our system
is open-source and self-hosted — no per-feature licensing.

### Student complaints

**Binary pass/fail provides no learning value:** "Test 3 failed" tells a student nothing
about why their logic is wrong or how to fix it. This is the most cited complaint in
academic literature on autograders. The LLM feedback layer directly addresses this.

**False negatives destroy trust:** Correct code marked wrong due to formatting differences
measurably harms learning outcomes by reducing student engagement with feedback. Output
normalization and human TA review before release both mitigate this.

**Timeout failures with no partial credit:** Gradescope's 768MB memory limit and 10-minute
global timeout result in a score of 0 with no indication of which tests passed before
the timeout. Our per-test timeout and partial credit model preserve what the student got right.

### Security complaints (Gradescope-specific)

**Grade manipulation via results.json:** Gradescope runs student code as root with
unrestricted filesystem access. Since 2016, students can overwrite the results file to
assign themselves any grade. Known and unpatched for years. Our non-root container model
with read-only filesystem prevents this class of attack.

**Reverse shell from submitted code:** Gradescope containers have unrestricted outbound
network access. Student code can open a reverse shell to an external server, gaining root
access to the container. `--network none` at the Docker level eliminates this.

---

## Academic Paper Notes — Breakout Autograder (SIGCSE 2024)

**Citation:** Liu, E.Z. et al. (2024). *A Fast and Accurate Machine Learning Autograder
for the Breakout Assignment.* SIGCSE 2024, Portland, OR. ACM.
DOI: https://doi.org/10.1145/3626252.3630759

### What they built

A human-in-the-loop autograder for the Stanford CS1 Breakout (Python game) assignment.
Traditional unit tests fail for this assignment because it is interactive and stochastic.
They used a reinforcement learning agent (DreamGrader framework) that plays each student's
game autonomously, exposing bugs by reaching relevant game states, then records short video
clips of discovered errors for TA review.

### Results

| Grading method | Time per submission | Accuracy |
|----------------|---------------------|----------|
| Manual grading | 8 min 35s | 86.4% |
| AI + human review | 4 min 49s | 92.3% |
| AI only (no human) | — | 90.1% |

44% time reduction and 6% accuracy improvement simultaneously. Graders rated 9/10 on
willingness to recommend. Free-form feedback focused almost entirely on UI improvements
— the grading logic was well-received.

### Key finding relevant to this project

Graders who overruled the AI's predictions introduced errors — meaning the AI was
sometimes more accurate than the human override. This validates the human-in-the-loop
design: the TA review step is a safety net for the AI, but the AI is not merely a
convenience layer. Both contribute to the final grade quality.

### Relevance to UVU autograder

- Validates the human-in-the-loop architecture chosen for this project
- The training data generation approach (programmatically inject known errors into a
  reference implementation to create synthetic training sets) is reusable for calibrating
  LLM grading prompts before real student data is available
- Their biggest failure mode (missed errors due to training data gaps) does not apply to
  our LLM-based approach — the model reasons semantically, not from a fixed training distribution
- Their live deployment feedback was almost entirely about UI — confirms that review
  dashboard UX is where this project will win or lose in demo conditions
- The paper explicitly suggests that similar techniques could apply to web design assignments
  — directly in scope for the HTML/CSS support planned in M4

---

## TLS + InCommon Notes

### What InCommon is

InCommon is a federated identity and trust consortium run by Internet2 for higher education.
Most US universities are members. The certificate program partners with Sectigo (formerly
Comodo) to provide free unlimited TLS certificates to member institutions.

### Certificate types available

- OV (Organizational Validation) SSL/TLS — standard server certificates
- EV (Extended Validation) — higher assurance, green bar in some browsers
- Client certificates — for mutual TLS if needed
- Code signing certificates

All are included under the institution's annual InCommon membership fee.

### Certificate request process

1. Generate a private key and CSR on the server:
```bash
openssl req -new -newkey rsa:2048 -nodes \
  -keyout ai-tutor.key \
  -out ai-tutor.csr \
  -subj "/C=US/ST=Utah/L=Orem/O=Utah Valley University/CN=ai-tutor.uvu.edu"
```
2. Send the CSR (not the key) to university IT
3. IT submits through Sectigo Certificate Manager under the university's RAO account
4. IT receives the signed certificate chain and provides it to the developer
5. Bundle the chain: `cat server.crt InCommon_Intermediate.crt > server-bundle.crt`
6. Install bundle + private key in Nginx

> **Chain transition note:** InCommon is migrating to new intermediate CAs
> (InCommon RSA OV SSL CA 3) due to browser trust store changes. When requesting,
> ask IT to issue from the new chain to avoid early reissuance.

### Nginx TLS configuration

```nginx
server {
    listen 443 ssl;
    server_name ai-tutor.uvu.edu;

    ssl_certificate     /etc/ssl/server-bundle.crt;
    ssl_certificate_key /etc/ssl/ai-tutor.key;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers off;

    add_header Strict-Transport-Security "max-age=63072000" always;
    add_header X-Frame-Options SAMEORIGIN;   # required for Canvas iframe embedding
    add_header X-Content-Type-Options nosniff;

    proxy_buffering off;    # critical for SSE streaming token output
    proxy_cache off;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Host $host;
    }
}
```

### Similarity to Apple Developer certificates

The CSR workflow is identical to generating a CSR for Apple Gatekeeper / Developer ID
signing. The cryptographic mechanism is the same PKI model — you generate a private key
locally, submit the public half (CSR) to a CA, and receive a signed certificate back.
The difference is what the CA is vouching for: Apple's CA vouches for developer identity
(code signing), Sectigo vouches for server identity (domain ownership). The private key
workflow and the concept of a certificate chain are identical in both contexts.

---

## LTI 1.3 + Canvas Integration Notes

### What LTI 1.3 is

Learning Tools Interoperability 1.3 is the current standard for embedding external tools
inside Canvas. It uses OpenID Connect (OIDC) for authentication — Canvas acts as the
identity provider, your app acts as the tool. When a student clicks the tool in Canvas,
Canvas sends a signed JWT asserting the student's identity, role, and course context.
Your app validates the JWT and creates a session without requiring a separate login.

### OIDC launch flow summary

```
Student clicks tool in Canvas
        ↓
Canvas POSTs login hint to your oidc_initiation_url
        ↓
Your app redirects back to Canvas auth endpoint with state + nonce
        ↓
Canvas signs a JWT with student ID, name, email, role, course context
        ↓
Canvas POSTs id_token to your redirect_uri
        ↓
Your app validates JWT against Canvas public JWKs
        ↓
Session created — student is authenticated, tool loads in Canvas iframe
```

### Canvas admin setup required

Canvas admin must create a Developer Key with your tool's configuration JSON, then
deploy it to the course or account. You host a config endpoint that Canvas admin
pastes as a URL — they do not need to manually enter JSON fields.

### Safari iframe cookie issue

Safari blocks third-party cookies in iframes by default. LTI 1.3 tools embedded in Canvas
are iframes and will fail to maintain sessions in Safari without a workaround. The `ltijs`
Node library handles this automatically via the LTI Platform Storage spec (postMessage-based
cookie proxy). Do not implement session management with plain cookies in the LTI context.

### Recommended library

`ltijs` (Node/Next.js) handles: OIDC flow, nonce/state verification, JWK fetching and
caching, Safari workaround, and session management. Use it rather than implementing
JWT validation manually.

### Canvas documentation

Current canonical location: `developerdocs.instructure.com`
The older `canvas.instructure.com/doc/api` is being retired after July 1, 2026.

Key pages to read in order:
1. External Tools Introduction — placement types and overview
2. LTI Launch Overview — OIDC flow with Canvas-specific details including Safari workaround
3. Configuring LTI 1.3 — Developer Key JSON format

---

## Security Architecture Notes

### Why the on-prem model is stronger than it appears

A common assumption is that cloud = more secure than on-prem. This is accurate at the
infrastructure layer (physical security, DDoS protection, patch management) but misleading
at the application layer for this specific use case.

The cloud threat model that matters most here is data exfiltration — student code,
grades, and academic records. On-prem with the attack surface described below is more
defensible for this threat than a cloud deployment where student data transits multiple
third-party systems.

### Attack surface on the Mac Mini (production)

```
Exposed to public internet:
  - TCP 443 (Nginx) — TLS only, rate limited, WAF rules

Bound to localhost only (not reachable from network):
  - FastAPI :8000
  - Next.js :3000
  - llama-server :8080
  - PostgreSQL :5432
  - Redis :6379

Not exposed at all:
  - Model weights (filesystem only)
  - Student submission files (filesystem only)
  - Grading container filesystem (ephemeral, destroyed after job)
```

### Container security model

Each grading job runs in an ephemeral Docker container with:
- `--network none` — no inbound or outbound network access
- `--cpus 0.5` — hard CPU limit, prevents fork bombs from saturating the host
- `--memory 256m` — hard memory limit
- `--read-only` on all directories except designated output dir
- Unprivileged non-root user (UID 1000 or equivalent)
- Destroyed immediately after job completion — no state persists

AST constraint check runs **before** container launch. Submissions containing `socket`,
`subprocess`, `os.system`, `os.fork`, or `__import__` calls are flagged and can be
blocked from execution entirely at instructor's discretion.

### University IT coordination checklist

Before go-live, the following must be confirmed with IT:

- [ ] Static public IP assigned to Mac Mini NIC
- [ ] DNS entry: `autograder.uvu.edu` (or equivalent) pointing to that IP
- [ ] Firewall rule: inbound TCP 443 only, all other inbound blocked
- [ ] Mac Mini included in IT's network monitoring scope (SIEM / flow analysis)
- [ ] Physical security: machine in locked rack in data center, not an office
- [ ] InCommon certificate requested through IT's Sectigo portal

---

## MCP Protocol Reference

### What MCP is (relevant for future integrations)

MCP (Model Context Protocol) is an open standard for giving AI models structured,
bidirectional access to external tools and data sources. It is the protocol used by
Claude.ai connectors (HubSpot, Gmail, Slack, etc.).

### Relevance to this project

In M3+, if the team wants to give the LLM grading agent access to external resources
(Canvas course data, student roster, past assignment history) without hard-coding API
calls, an MCP server layer provides a clean abstraction. The grading LLM could call
a `get_student_history` tool or `get_assignment_rubric` tool via the MCP protocol rather
than having those data fetches embedded in the FastAPI prompt-building logic.

Not required for M1–M2. Worth noting as an architectural option for later phases when
the system becomes more agent-like rather than purely pipeline-like.

### Transport

JSON-RPC 2.0 over SSE (for remote servers) or stdio (for local processes). The local
llama-server does not speak MCP natively — this would be a wrapper layer in FastAPI
that presents tools to the model in the system prompt and intercepts tool_use blocks
in the LLM response.
