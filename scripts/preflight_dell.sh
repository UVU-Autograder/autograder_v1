#!/usr/bin/env bash
# Full-suite preflight for the Dell workstation (Ubuntu 24.x, RTX PRO 4500 Blackwell).
#
# Run from the repo root over SSH:
#
#   bash scripts/preflight_dell.sh --install-kata --keep-up
#
# Stages run independently so one failure never hides the rest:
#   host -> cgroups -> kata -> stack up -> stack checks -> backend tests
#   -> frontend build -> gpu/ml -> teardown
#
# Writes preflight-report-<timestamp>.txt (gitignored). Secrets are never
# printed. Paste the report back for triage.
#
# Flags:
#   --install-kata    install Kata via scripts/install-kata-docker-runtime-ubuntu.sh if missing (sudo)
#   --no-kata         run the stack on the default Docker runtime even if Kata works
#   --skip-frontend   skip npm ci / lint / build
#   --skip-gpu        skip GPU and training-stack checks
#   --keep-up         leave the stack running afterwards (default: docker compose down)
#   --model-dir DIR   volume that will hold model weights (default: $HF_HOME or /data)

set -uo pipefail

INSTALL_KATA=0
USE_KATA=1
SKIP_FRONTEND=0
SKIP_GPU=0
KEEP_UP=0
MODEL_DIR="${HF_HOME:-/data}"
TRAIN_VENV="${TRAIN_VENV:-$HOME/venvs/train}"
REQUIRED_FREE_GB=100
PORTS=(5432 6379 2358 8000 3000 8001)

while [ $# -gt 0 ]; do
  case "$1" in
    --install-kata) INSTALL_KATA=1 ;;
    --no-kata) USE_KATA=0 ;;
    --skip-frontend) SKIP_FRONTEND=1 ;;
    --skip-gpu) SKIP_GPU=1 ;;
    --keep-up) KEEP_UP=1 ;;
    --model-dir) MODEL_DIR="$2"; shift ;;
    -h|--help) sed -n '2,24p' "$0"; exit 0 ;;
    *) echo "unknown flag: $1" >&2; exit 2 ;;
  esac
  shift
done

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT" || exit 2

STAMP="$(date +%Y%m%d-%H%M%S)"
REPORT="$REPO_ROOT/preflight-report-$STAMP.txt"
exec > >(tee -a "$REPORT") 2>&1

PASS=0; WARN=0; FAIL=0
FAILED_CHECKS=()

pass() { PASS=$((PASS+1)); printf '  PASS  %s\n' "$*"; }
warn() { WARN=$((WARN+1)); printf '  WARN  %s\n' "$*"; }
fail() { FAIL=$((FAIL+1)); FAILED_CHECKS+=("$1"); printf '  FAIL  %s\n' "$*"; }
stage() { printf '\n=== %s ===\n' "$*"; }
have() { command -v "$1" >/dev/null 2>&1; }

echo "UVU Autograder preflight -- $(date -Is)"
echo "host=$(hostname) user=$(whoami) repo=$REPO_ROOT"
echo "git: $(git rev-parse --abbrev-ref HEAD 2>/dev/null) @ $(git rev-parse --short HEAD 2>/dev/null)$(git diff --quiet 2>/dev/null || echo ' (dirty)')"

# ---------------------------------------------------------------- host
stage "1. host"

if [ -r /etc/os-release ]; then
  . /etc/os-release
  case "${VERSION_ID:-}" in
    24.*) pass "OS: $PRETTY_NAME" ;;
    *) warn "OS: ${PRETTY_NAME:-unknown} (targeted Ubuntu 24.x)" ;;
  esac
fi
echo "        kernel $(uname -r), $(nproc) cores, $(free -g | awk '/Mem:/{print $2}')GiB RAM"

if have docker; then
  pass "docker $(docker --version | awk '{print $3}' | tr -d ,)"
  if docker compose version >/dev/null 2>&1; then
    pass "docker compose $(docker compose version --short)"
  else
    fail "docker-compose-plugin" "docker compose plugin missing: sudo apt install docker-compose-plugin"
  fi
  if docker info >/dev/null 2>&1; then
    pass "docker daemon reachable as $(whoami)"
  else
    fail "docker-access" "cannot talk to docker daemon: sudo usermod -aG docker $(whoami) && re-login"
  fi
else
  fail "docker" "docker not installed"
fi

mkdir -p "$MODEL_DIR" 2>/dev/null || true
if [ -d "$MODEL_DIR" ]; then
  free_gb=$(df -BG --output=avail "$MODEL_DIR" | tail -1 | tr -dc 0-9)
  if [ "${free_gb:-0}" -ge "$REQUIRED_FREE_GB" ]; then
    pass "free disk at $MODEL_DIR: ${free_gb}GB"
  else
    fail "disk" "only ${free_gb}GB free at $MODEL_DIR (need ${REQUIRED_FREE_GB}GB for weights + checkpoints); use --model-dir"
  fi
else
  warn "model dir $MODEL_DIR not creatable; pass --model-dir to a large volume (sudo mkdir + chown)"
fi
root_free=$(df -BG --output=avail / | tail -1 | tr -dc 0-9)
[ "${root_free:-0}" -ge 30 ] && pass "free disk at /: ${root_free}GB (docker images)" \
  || warn "only ${root_free}GB free at / -- docker images and build cache live here"

if docker compose -f docker-compose.poc.yml ps -q 2>/dev/null | grep -q .; then
  echo "        autograder stack already running -- skipping port-conflict check"
else
  busy=()
  for port in "${PORTS[@]}"; do
    ss -ltnH "sport = :$port" 2>/dev/null | grep -q . && busy+=("$port")
  done
  if [ ${#busy[@]} -eq 0 ]; then
    pass "ports free: ${PORTS[*]}"
  else
    fail "ports" "ports already in use: ${busy[*]} (check: sudo ss -ltnp)"
  fi
fi

if have node; then
  node_major=$(node -v | tr -d v | cut -d. -f1)
  [ "$node_major" -ge 20 ] && pass "node $(node -v)" || fail "node" "node $(node -v) too old for Next 16; need >= 20"
else
  [ $SKIP_FRONTEND -eq 1 ] && warn "node not installed (frontend skipped)" \
    || fail "node" "node not installed; install Node 20+ (e.g. via nvm) or pass --skip-frontend"
fi

if have python3.13; then
  pass "python3.13 available (training venv)"
else
  warn "python3.13 missing -- needed for the training venv: sudo add-apt-repository ppa:deadsnakes/ppa && sudo apt install python3.13 python3.13-venv"
fi

# ---------------------------------------------------------------- cgroups
stage "2. cgroups (Judge0 isolate)"

cgroup_fs=$(stat -fc %T /sys/fs/cgroup 2>/dev/null)
# Since 6bb6e41 the compose file runs Judge0 in rlimit mode (no isolate --cg),
# which works on cgroup v2. Count the flags on judge0 + judge0-worker.
rlimit_flags=$(grep -cE 'ENABLE_PER_PROCESS_AND_THREAD_(TIME|MEMORY)_LIMIT: "true"' docker-compose.poc.yml)
if [ "$cgroup_fs" = "cgroup2fs" ] && [ "$rlimit_flags" -ge 4 ]; then
  warn "cgroup v2 host; Judge0 runs in rlimit mode (ENABLE_PER_PROCESS_AND_THREAD_*_LIMIT) so no GRUB change or reboot
        is needed if stage 5 passes. Limits are per-process rather than cgroup-accounted -- acceptable with Kata's VM
        boundary, weaker without it. See docs/deployment/ubuntu_poc_deployment.md (Cgroups section)."
elif [ "$cgroup_fs" = "cgroup2fs" ]; then
  fail "cgroup-v2" "host is on cgroup v2 and Judge0 rlimit mode is not enabled in docker-compose.poc.yml. Either set
        ENABLE_PER_PROCESS_AND_THREAD_TIME_LIMIT/MEMORY_LIMIT=\"true\" on judge0 + judge0-worker, or switch the host to
        cgroup v1 (reboots; walkthrough in docs/deployment/blackwell_training_setup.md):
          echo 'GRUB_CMDLINE_LINUX=\"\$GRUB_CMDLINE_LINUX systemd.unified_cgroup_hierarchy=0\"' | sudo tee /etc/default/grub.d/99-cgroup-v1.cfg
          sudo update-grub && sudo reboot"
elif [ "$cgroup_fs" = "tmpfs" ]; then
  pass "cgroup v1 (hybrid/legacy) -- compatible with Judge0 isolate"
else
  warn "unrecognised cgroup fs type: ${cgroup_fs:-none}"
fi

# ---------------------------------------------------------------- kata
stage "3. kata containers"

kata_ok() {
  docker info --format '{{json .Runtimes}}' 2>/dev/null | grep -q '"kata-runtime"' &&
    timeout 120 docker run --rm --runtime kata-runtime busybox uname -r >/tmp/kata-uname.$$ 2>&1
}

if [ ! -e /dev/kvm ]; then
  fail "kvm" "/dev/kvm missing -- enable VT-x/AMD-V in BIOS. Kata cannot run."
  USE_KATA=0
else
  pass "/dev/kvm present ($(grep -cE 'vmx|svm' /proc/cpuinfo) cores report virt flags)"
  if kata_ok; then
    pass "kata-runtime registered and boots a VM (guest kernel $(cat /tmp/kata-uname.$$))"
  elif [ $INSTALL_KATA -eq 1 ]; then
    echo "        kata-runtime missing or broken -- installing (sudo will prompt)"
    if sudo "$REPO_ROOT/scripts/install-kata-docker-runtime-ubuntu.sh" && kata_ok; then
      pass "kata-runtime installed and boots a VM (guest kernel $(cat /tmp/kata-uname.$$))"
    else
      fail "kata-install" "Kata install/verify failed -- see output above"
      USE_KATA=0
    fi
  else
    warn "kata-runtime not usable; re-run with --install-kata. Continuing on the default runtime."
    USE_KATA=0
  fi
fi
rm -f /tmp/kata-uname.$$

COMPOSE=(docker compose --env-file .env.local -f docker-compose.poc.yml)
if [ $USE_KATA -eq 1 ]; then
  COMPOSE+=(-f docker-compose.kata.yml)
  echo "        stack will run Judge0 under kata-runtime"
else
  warn "stack will run Judge0 on the default Docker runtime (no VM isolation)"
fi

# ---------------------------------------------------------------- stack up
stage "4. stack up"

if [ ! -f .env.local ]; then
  python3 - <<'PY'
import re, secrets
from pathlib import Path

text = Path(".env.example").read_text()
pg = secrets.token_hex(16)
values = {
    "POSTGRES_PASSWORD": pg,
    "JUDGE0_AUTH_TOKEN": secrets.token_hex(16),
    "JWT_SECRET": secrets.token_hex(32),
}
for key, value in values.items():
    text = re.sub(rf"^{key}=.*$", f"{key}={value}", text, flags=re.M)
text = re.sub(
    r"^DATABASE_URL=(\w[\w+]*://[^:]+:)[^@]*@",
    lambda m: f"DATABASE_URL={m.group(1)}{pg}@",
    text,
    flags=re.M,
)
# backend + celery-worker run with network_mode: host, where compose service
# names (postgres, redis, judge0) do not resolve. Point them at published ports.
if 'network_mode: "host"' in Path("docker-compose.poc.yml").read_text():
    for key in ("DATABASE_URL", "REDIS_URL", "CELERY_BROKER_URL", "JUDGE0_URL"):
        text = re.sub(
            rf"^({key}=[\w+]+://(?:[^@/\s]*@)?)(postgres|app-postgres|redis|judge0)(:\d+)",
            r"\g<1>127.0.0.1\g<3>",
            text,
            flags=re.M,
        )
Path(".env.local").write_text(text)
PY
  chmod 600 .env.local
  pass "generated .env.local with random secrets (mode 600, gitignored)"
else
  pass "using existing .env.local"
  grep -qE '^(POSTGRES_PASSWORD|JWT_SECRET|JUDGE0_AUTH_TOKEN)=(change-me|replace)' .env.local &&
    warn ".env.local still has placeholder secrets from .env.example"
  if grep -q 'network_mode: "host"' docker-compose.poc.yml &&
     grep -qE '^(DATABASE_URL|REDIS_URL|CELERY_BROKER_URL|JUDGE0_URL)=[^#]*(//|@)(postgres|app-postgres|redis|judge0):' .env.local; then
    fail "env-hosts" ".env.local uses compose service names (postgres/redis/judge0), but backend and celery-worker run
        with network_mode: host where those don't resolve. Use 127.0.0.1 in DATABASE_URL, REDIS_URL,
        CELERY_BROKER_URL and JUDGE0_URL (or delete .env.local and let this script regenerate it)."
  fi
fi

echo "        building and starting (first build takes several minutes)..."
if "${COMPOSE[@]}" up -d --build >/tmp/compose-up.$$ 2>&1; then
  pass "docker compose up"
else
  fail "compose-up" "docker compose up failed:"
  tail -40 /tmp/compose-up.$$ | sed 's/^/          /'
fi
rm -f /tmp/compose-up.$$

deadline=$((SECONDS + 300))
while [ $SECONDS -lt $deadline ]; do
  unhealthy=$("${COMPOSE[@]}" ps --format '{{.Service}} {{.State}} {{.Health}}' 2>/dev/null |
    awk '$2!="running" || ($3!="" && $3!="healthy")')
  [ -z "$unhealthy" ] && break
  sleep 5
done
"${COMPOSE[@]}" ps --format 'table {{.Service}}\t{{.State}}\t{{.Health}}' 2>/dev/null | sed 's/^/        /'
if [ -z "${unhealthy:-}" ]; then
  pass "all services running/healthy"
else
  fail "services-healthy" "not healthy after 5 min: $(echo "$unhealthy" | awk '{print $1}' | tr '\n' ' ')"
  for svc in $(echo "$unhealthy" | awk '{print $1}'); do
    echo "        --- last 50 log lines: $svc"
    "${COMPOSE[@]}" logs --tail 50 "$svc" 2>&1 | sed 's/^/          /'
  done
fi

while read -r svc _state code; do
  [ -z "$svc" ] && continue
  if [ "$code" = "0" ]; then
    pass "one-shot $svc completed"
  else
    fail "oneshot-$svc" "$svc exited with code $code:"
    "${COMPOSE[@]}" logs --tail 30 "$svc" 2>&1 | sed 's/^/          /'
  fi
done < <("${COMPOSE[@]}" ps -a --status exited --format '{{.Service}} {{.State}} {{.ExitCode}}' 2>/dev/null)

for svc in judge0 judge0-worker; do
  cid=$("${COMPOSE[@]}" ps -q "$svc" 2>/dev/null)
  if [ -n "$cid" ]; then
    runtime=$(docker inspect --format '{{.HostConfig.Runtime}}' "$cid")
    if [ $USE_KATA -eq 1 ] && [ "$runtime" != "kata-runtime" ]; then
      fail "kata-in-use" "$svc is on runtime '$runtime', expected kata-runtime"
    else
      pass "$svc runtime: $runtime"
    fi
  fi
done

# ---------------------------------------------------------------- stack checks
stage "5. end-to-end stack checks"

if python3 scripts/preflight_stack.py --json-out "preflight-stack-$STAMP.json"; then
  pass "stack checks (details above)"
else
  fail "stack-checks" "one or more end-to-end checks failed (details above)"
  echo "        --- celery-worker log tail"
  "${COMPOSE[@]}" logs --tail 40 celery-worker 2>&1 | sed 's/^/          /'
fi

# ---------------------------------------------------------------- backend tests
stage "6. backend test suite"

# The suite's reset_database fixture calls drop_all() on whatever DATABASE_URL
# points at. Run it in a throwaway container with a clean env on in-memory
# SQLite -- never against the live stack's Postgres.
if "${COMPOSE[@]}" run --rm --no-deps -T --entrypoint "" backend \
    env -i PATH=/usr/local/bin:/usr/bin:/bin HOME=/tmp PYTHONPATH=/app \
    DATABASE_URL=sqlite+pysqlite:///:memory: \
    python -m pytest -q -p no:cacheprovider >/tmp/pytest.$$ 2>&1; then
  pass "pytest: $(tail -1 /tmp/pytest.$$)"
else
  fail "pytest" "pytest failed: $(tail -1 /tmp/pytest.$$)"
  grep -E '^(FAILED|ERROR)' /tmp/pytest.$$ | head -30 | sed 's/^/          /'
fi
rm -f /tmp/pytest.$$

# ---------------------------------------------------------------- frontend
stage "7. frontend"

if [ $SKIP_FRONTEND -eq 1 ]; then
  warn "frontend skipped (--skip-frontend)"
elif have npm; then
  (
    cd frontend || exit 1
    export NEXT_PUBLIC_API_BASE_URL=http://localhost:8000 NEXT_TELEMETRY_DISABLED=1
    npm ci --no-audit --no-fund >/tmp/npm-ci.$$ 2>&1 || { tail -20 /tmp/npm-ci.$$; exit 11; }
    npm run lint >/tmp/npm-lint.$$ 2>&1 || { tail -30 /tmp/npm-lint.$$; exit 12; }
    npm run build >/tmp/npm-build.$$ 2>&1 || { tail -40 /tmp/npm-build.$$; exit 13; }
  )
  case $? in
    0) pass "npm ci + lint + build" ;;
    11) fail "npm-ci" "npm ci failed (output above)" ;;
    12) fail "npm-lint" "npm run lint failed (output above)" ;;
    13) fail "npm-build" "npm run build failed (output above)" ;;
    *) fail "frontend" "frontend stage failed" ;;
  esac
  rm -f /tmp/npm-ci.$$ /tmp/npm-lint.$$ /tmp/npm-build.$$
fi

# ---------------------------------------------------------------- gpu / ml
stage "8. gpu / training stack"

if [ $SKIP_GPU -eq 1 ]; then
  warn "gpu skipped (--skip-gpu)"
elif ! have nvidia-smi; then
  fail "nvidia-driver" "nvidia-smi not found -- install the NVIDIA driver (RTX Enterprise branch)"
else
  nvidia-smi --query-gpu=name,memory.total,driver_version,compute_cap --format=csv,noheader | sed 's/^/        /'
  gpu_procs=$(nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader)
  if [ -n "$gpu_procs" ]; then
    warn "GPU already in use -- training and vLLM serving cannot share 32GB:"
    echo "$gpu_procs" | sed 's/^/          /'
  else
    pass "GPU idle"
  fi
  if [ -x "$TRAIN_VENV/bin/python" ]; then
    if "$TRAIN_VENV/bin/python" scripts/preflight_training_gpu.py --dir "$MODEL_DIR"; then
      pass "training stack (torch/bitsandbytes on sm_120)"
    else
      fail "training-stack" "scripts/preflight_training_gpu.py failed (details above)"
    fi
  else
    warn "no training venv at $TRAIN_VENV yet. Create it with:
          python3.13 -m venv $TRAIN_VENV && $TRAIN_VENV/bin/pip install -r backend/training/requirements-train.txt"
  fi
  [ -n "${HF_HOME:-}" ] && pass "HF_HOME=$HF_HOME" || warn "HF_HOME unset -- model downloads will land in ~/.cache/huggingface"
fi

# ---------------------------------------------------------------- teardown
stage "9. teardown"
if [ $KEEP_UP -eq 1 ]; then
  echo "        --keep-up: stack left running. Stop with: ${COMPOSE[*]} down"
else
  "${COMPOSE[@]}" down >/dev/null 2>&1 && echo "        stack stopped (volumes kept)"
fi

# ---------------------------------------------------------------- summary
printf '\n=== summary ===\n  %d pass, %d warn, %d fail\n' "$PASS" "$WARN" "$FAIL"
if [ $FAIL -gt 0 ]; then
  printf '  failed: %s\n' "${FAILED_CHECKS[*]}"
fi
echo "  report: $REPORT"
[ $FAIL -eq 0 ]
