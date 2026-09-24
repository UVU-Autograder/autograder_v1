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
#   --existing-stack  check the stack that is already running: never build, recreate,
#                     stop, or install anything. Turned on automatically when the
#                     compose project is already up (e.g. the live Dell deployment).
#   --rebuild         opt out of that: rebuild and restart a stack that is running
#   --model-dir DIR   volume that will hold model weights (default: $HF_HOME or /data)

set -uo pipefail

INSTALL_KATA=0
USE_KATA=1
SKIP_FRONTEND=0
SKIP_GPU=0
KEEP_UP=0
EXISTING=0
REBUILD=0
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
    --existing-stack) EXISTING=1 ;;
    --rebuild) REBUILD=1 ;;
    --model-dir) MODEL_DIR="$2"; shift ;;
    -h|--help) sed -n '2,28p' "$0"; exit 0 ;;
    *) echo "unknown flag: $1" >&2; exit 2 ;;
  esac
  shift
done

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT" || exit 2

if [ -f docker-compose.yml ]; then
  COMPOSE_FILE=docker-compose.yml
else
  echo "no docker-compose.yml in $REPO_ROOT" >&2
  exit 2
fi

if [ $EXISTING -eq 1 ] && [ $REBUILD -eq 1 ]; then
  echo "--existing-stack and --rebuild are mutually exclusive" >&2
  exit 2
fi
STACK_RUNNING=0
docker compose -f "$COMPOSE_FILE" ps -q 2>/dev/null | grep -q . && STACK_RUNNING=1
AUTO_EXISTING=0
if [ $STACK_RUNNING -eq 1 ] && [ $REBUILD -eq 0 ] && [ $EXISTING -eq 0 ]; then
  EXISTING=1
  AUTO_EXISTING=1
fi
# A stack that was up when we started is left up, even after --rebuild.
[ $STACK_RUNNING -eq 1 ] && KEEP_UP=1

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
echo "compose: $COMPOSE_FILE"
if [ $EXISTING -eq 1 ]; then
  echo "mode: EXISTING STACK -- checks only; nothing is built, recreated, stopped, or installed$([ $AUTO_EXISTING -eq 1 ] && echo ' (auto: stack already running; pass --rebuild to override)')"
else
  echo "mode: build -- docker compose up --build, then $([ $KEEP_UP -eq 1 ] && echo 'leave running' || echo 'down')"
fi

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
  warn "model dir $MODEL_DIR not creatable. Create it once: sudo mkdir -p $MODEL_DIR && sudo chown $(whoami): $MODEL_DIR
        (or pass --model-dir to another large volume)"
fi
root_free=$(df -BG --output=avail / | tail -1 | tr -dc 0-9)
[ "${root_free:-0}" -ge 30 ] && pass "free disk at /: ${root_free}GB (docker images)" \
  || warn "only ${root_free}GB free at / -- docker images and build cache live here"

if [ $STACK_RUNNING -eq 1 ]; then
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

TRAIN_PY=$(command -v python3.13 || command -v python3.12 || true)
if [ -n "$TRAIN_PY" ]; then
  pass "$(basename "$TRAIN_PY") available for the training venv"
  "$TRAIN_PY" -c 'import ensurepip' 2>/dev/null ||
    warn "venv support missing: sudo apt install $(basename "$TRAIN_PY")-venv"
else
  warn "need python3.12+ for the training venv: sudo apt install python3.12 python3.12-venv"
fi

# ---------------------------------------------------------------- cgroups
stage "2. cgroups (Judge0 isolate)"

cgroup_fs=$(stat -fc %T /sys/fs/cgroup 2>/dev/null)
# Since 6bb6e41 the compose file runs Judge0 in rlimit mode (no isolate --cg),
# which works on cgroup v2. Count the flags on judge0 + judge0-worker.
rlimit_flags=$(grep -cE 'ENABLE_PER_PROCESS_AND_THREAD_(TIME|MEMORY)_LIMIT: "true"' "$COMPOSE_FILE")
if [ "$cgroup_fs" = "cgroup2fs" ] && [ "$rlimit_flags" -ge 4 ]; then
  warn "cgroup v2 host; Judge0 runs in rlimit mode (ENABLE_PER_PROCESS_AND_THREAD_*_LIMIT) so no GRUB change or reboot
        is needed if stage 5 passes. Limits are per-process rather than cgroup-accounted -- acceptable with Kata's VM
        boundary, weaker without it. See docs/deployment/workstation_deployment.md (Cgroups section)."
elif [ "$cgroup_fs" = "cgroup2fs" ]; then
  fail "cgroup-v2" "host is on cgroup v2 and Judge0 rlimit mode is not enabled in $COMPOSE_FILE. Either set
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
  elif [ $INSTALL_KATA -eq 1 ] && [ $EXISTING -eq 1 ]; then
    warn "kata-runtime not usable, but --install-kata is ignored in existing-stack mode (the installer
        rewrites Kata config the running stack may depend on). Re-run with --rebuild to allow it."
    USE_KATA=0
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

ENV_FILE=""
if [ -f .env ]; then
  ENV_FILE=".env"
elif [ -f .env.local ]; then
  ENV_FILE=".env.local"
fi

COMPOSE=(docker compose)
if [ -n "$ENV_FILE" ]; then
  COMPOSE+=(--env-file "$ENV_FILE")
fi
COMPOSE+=(-f "$COMPOSE_FILE")

if [ $EXISTING -eq 1 ]; then
  # Match the override set to what is actually running, so ps/run see the same config.
  j0=$(docker compose -f "$COMPOSE_FILE" ps -q judge0 2>/dev/null)
  j0_runtime=$([ -n "$j0" ] && docker inspect --format '{{.HostConfig.Runtime}}' "$j0")
  if [ "$j0_runtime" = "${KATA_DOCKER_RUNTIME:-kata-runtime}" ]; then
    USE_KATA=1
    COMPOSE+=(-f docker-compose.kata.yml)
    echo "        running Judge0 is under $j0_runtime"
  else
    USE_KATA=0
    warn "running Judge0 is on runtime '${j0_runtime:-none}', not Kata (no VM isolation)"
  fi
elif [ $USE_KATA -eq 1 ]; then
  COMPOSE+=(-f docker-compose.kata.yml)
  echo "        stack will run Judge0 under kata-runtime"
else
  warn "stack will run Judge0 on the default Docker runtime (no VM isolation)"
fi

# ---------------------------------------------------------------- stack up
if [ $EXISTING -eq 1 ]; then
  stage "4. existing stack (read-only: no env file changes, no up/build)"
else
  stage "4. stack up"
fi

if [ $EXISTING -eq 1 ]; then
  if [ -n "$ENV_FILE" ] && [ -f "$ENV_FILE" ]; then
    pass "found $ENV_FILE (not modified)"
    if grep -q 'network_mode: "host"' "$COMPOSE_FILE" &&
       grep -qE '^(DATABASE_URL|REDIS_URL|CELERY_BROKER_URL|JUDGE0_URL)=[^#]*(//|@)(postgres|app-postgres|redis|judge0):' "$ENV_FILE"; then
      warn "$ENV_FILE uses compose service names with a host-networked backend; works only if something else
        resolves them. Worth checking with whoever deployed the stack."
    fi
  else
    warn "no env file -- the running stack was started on compose defaults (dev passwords)"
  fi
elif [ -z "$ENV_FILE" ] && [ $STACK_RUNNING -eq 1 ]; then
  # New random secrets would not match the password baked into the existing
  # Postgres volume and lock the backend out. Rebuild on the same defaults.
  warn "no env file and the stack was already running: NOT generating one (new secrets would not match
        the existing database volume). Rebuilding on compose defaults."
  COMPOSE=(docker compose -f "$COMPOSE_FILE")
  [ $USE_KATA -eq 1 ] && COMPOSE+=(-f docker-compose.kata.yml)
elif [ -z "$ENV_FILE" ]; then
  ENV_FILE=".env"
  COMPOSE_FILE="$COMPOSE_FILE" ENV_FILE="$ENV_FILE" python3 - <<'PY'
import os, re, secrets
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
if 'network_mode: "host"' in Path(os.environ["COMPOSE_FILE"]).read_text():
    for key in ("DATABASE_URL", "REDIS_URL", "CELERY_BROKER_URL", "JUDGE0_URL"):
        text = re.sub(
            rf"^({key}=[\w+]+://(?:[^@/\s]*@)?)(postgres|app-postgres|redis|judge0)(:\d+)",
            r"\g<1>127.0.0.1\g<3>",
            text,
            flags=re.M,
        )
Path(os.environ["ENV_FILE"]).write_text(text)
PY
  chmod 600 "$ENV_FILE"
  pass "generated $ENV_FILE with random secrets (mode 600, gitignored)"
else
  pass "using existing $ENV_FILE"
  grep -qE '^(POSTGRES_PASSWORD|JWT_SECRET|JUDGE0_AUTH_TOKEN)=(change-me|replace)' "$ENV_FILE" &&
    warn "$ENV_FILE still has placeholder secrets from .env.example"
  if grep -q 'network_mode: "host"' "$COMPOSE_FILE" &&
     grep -qE '^(DATABASE_URL|REDIS_URL|CELERY_BROKER_URL|JUDGE0_URL)=[^#]*(//|@)(postgres|app-postgres|redis|judge0):' "$ENV_FILE"; then
    fail "env-hosts" "$ENV_FILE uses compose service names (postgres/redis/judge0), but backend and celery-worker run
        with network_mode: host where those don't resolve. Use 127.0.0.1 in DATABASE_URL, REDIS_URL,
        CELERY_BROKER_URL and JUDGE0_URL (or delete $ENV_FILE and let this script regenerate it)."
  fi
fi

if [ $EXISTING -eq 0 ]; then
  echo "        building and starting (first build takes several minutes)..."
  if "${COMPOSE[@]}" up -d --build >/tmp/compose-up.$$ 2>&1; then
    pass "docker compose up"
  else
    fail "compose-up" "docker compose up failed:"
    tail -40 /tmp/compose-up.$$ | sed 's/^/          /'
  fi
  rm -f /tmp/compose-up.$$
fi

# A running stack gets 30s to report healthy; a fresh one gets 5 minutes.
deadline=$((SECONDS + $([ $EXISTING -eq 1 ] && echo 30 || echo 300)))
while [ $SECONDS -lt $deadline ]; do
  svc_states=$("${COMPOSE[@]}" ps --format '{{.Service}} {{.State}} {{.Health}}' 2>/dev/null)
  unhealthy=$(echo "$svc_states" | awk 'NF && ($2!="running" || ($3!="" && $3!="healthy"))')
  running_count=$(echo "$svc_states" | awk 'NF' | wc -l)
  [ -z "$unhealthy" ] && [ "$running_count" -gt 0 ] && break
  sleep 5
done
"${COMPOSE[@]}" ps --format 'table {{.Service}}\t{{.State}}\t{{.Health}}' 2>/dev/null | sed 's/^/        /'
if [ "${running_count:-0}" -eq 0 ]; then
  # An empty list used to count as "healthy" -- it means nothing is running.
  fail "services-healthy" "no services running for this compose project"
elif [ -z "${unhealthy:-}" ]; then
  pass "all $running_count services running/healthy"
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

stack_env=()
if [ $EXISTING -eq 1 ] && [ -n "${j0:-}" ]; then
  # DELETE needs the live Judge0's AUTHZ_TOKEN; a freshly generated .env.local
  # would not match it (that was the 403). Read it from the container; never print it.
  live_token=$(docker inspect --format '{{range .Config.Env}}{{println .}}{{end}}' "$j0" |
    sed -n 's/^AUTHZ_TOKEN=//p')
  [ -n "$live_token" ] && stack_env=(env "JUDGE0_AUTH_TOKEN=$live_token")
fi
if ${stack_env[@]+"${stack_env[@]}"} python3 scripts/preflight_stack.py --json-out "preflight-stack-$STAMP.json"; then
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
# The checkout is mounted at /repo so tests that read repo-root files
# (docker-compose.yml, judge0.Dockerfile, pyproject.toml ruff config) see them;
# the image only contains backend/. Runs as the invoking user, so nothing it
# writes ends up root-owned. One-off container; live services untouched.
echo "        testing this checkout's code with the backend image's dependencies"
if "${COMPOSE[@]}" run --rm --no-deps -T --entrypoint "" \
    --user "$(id -u):$(id -g)" -v "$REPO_ROOT:/repo" -w /repo/backend backend \
    env -i PATH=/usr/local/bin:/usr/bin:/bin HOME=/tmp PYTHONPATH=/repo/backend \
    PYTHONDONTWRITEBYTECODE=1 DATABASE_URL=sqlite+pysqlite:///:memory: \
    python -m pytest -q -p no:cacheprovider >/tmp/pytest.$$ 2>&1; then
  pass "pytest: $(tail -1 /tmp/pytest.$$)"
else
  fail "pytest" "pytest failed: $(tail -1 /tmp/pytest.$$)"
  grep -E '^(FAILED|ERROR)' /tmp/pytest.$$ | head -30 | sed 's/^/          /'
fi
rm -f /tmp/pytest.$$

# ---------------------------------------------------------------- frontend
stage "7. frontend"

if systemctl list-unit-files autograder-frontend.service >/dev/null 2>&1 &&
   systemctl list-unit-files autograder-frontend.service | grep -q autograder-frontend; then
  if systemctl is-active --quiet autograder-frontend.service; then
    pass "autograder-frontend.service active (Next.js behind nginx)"
  else
    fail "frontend-service" "autograder-frontend.service is not active: systemctl status autograder-frontend"
  fi
fi
if [ $SKIP_FRONTEND -eq 1 ]; then
  warn "frontend build skipped (--skip-frontend)"
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
          ${TRAIN_PY:-python3.12} -m venv $TRAIN_VENV && $TRAIN_VENV/bin/pip install -r backend/training/requirements-train.txt
        (install torch from the cu129 index first -- see backend/training/README.md)"
  fi
  [ -n "${HF_HOME:-}" ] && pass "HF_HOME=$HF_HOME" || warn "HF_HOME unset -- model downloads will land in ~/.cache/huggingface"
fi

# ---------------------------------------------------------------- teardown
stage "9. teardown"
if [ $EXISTING -eq 1 ]; then
  echo "        existing-stack mode: stack left exactly as found"
elif [ $KEEP_UP -eq 1 ]; then
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
