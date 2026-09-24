#!/usr/bin/env bash
# Install or update the vllm-cs1410 systemd service on the Dell.
#
#   bash backend/training/install_vllm_service.sh p2c            # serve training/output/p2c as cs1410-p2c
#   bash backend/training/install_vllm_service.sh p2c --dry-run  # show every step; change nothing
#
# 1. Promotes the adapter: copies training/output/<name> to
#    /data/models/adapters/cs1410-<name> with a PROVENANCE.json (git commit,
#    weights sha256, dataset meta), so retraining or cleaning the checkout cannot
#    change what is being served. A different adapter already at that path is
#    kept as <path>.bak-<timestamp>.
# 2. Renders vllm-cs1410.service from the template in this directory and
#    installs it to /etc/systemd/system (sudo), enabled at boot.
# 3. (Re)starts it and waits until it answers on 127.0.0.1:8001.
#
# Run as the account that owns the models and venvs (dev), not as root; it asks
# for sudo only for the systemd steps.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"
UNIT=vllm-cs1410
UNIT_PATH="/etc/systemd/system/$UNIT.service"
PORT=8001
MODEL="${SERVE_BASE_MODEL:-/data/models/gemma4-12b-qat-w4a16}"
VLLM="${VLLM_BIN:-$HOME/venvs/serve/bin/vllm}"
ADAPTERS="${ADAPTERS_DIR:-/data/models/adapters}"

usage() { echo "usage: bash backend/training/install_vllm_service.sh <adapter> [--dry-run]" >&2; exit 2; }
[[ $# -ge 1 && $# -le 2 ]] || usage
NAME="$1"
DRY=0
if [[ $# -eq 2 ]]; then [[ "$2" == --dry-run ]] || usage; DRY=1; fi
[[ "$NAME" =~ ^[A-Za-z0-9_.-]+$ ]] || { echo "adapter name must be letters, digits, '.', '_' or '-'" >&2; exit 2; }

SRC="$HERE/output/$NAME"
DEST="$ADAPTERS/cs1410-$NAME"
SERVED="cs1410-$NAME"

say() { printf '%s\n' "$*"; }
run() { if ((DRY)); then say "  [dry-run] $*"; else "$@"; fi }
die() { say "error: $*" >&2; exit 1; }

# --- checks: refuse before changing anything --------------------------------
[[ $EUID -ne 0 ]] || die "run as the dev account, not root (it uses sudo where needed)"
[[ -f "$SRC/adapter_config.json" ]] || die "no adapter at $SRC (adapter_config.json missing)"
[[ -f "$SRC/adapter_model.safetensors" ]] || die "no weights at $SRC/adapter_model.safetensors"
[[ -f "$MODEL/config.json" ]] || die "base model not found at $MODEL"
[[ -x "$VLLM" ]] || die "vllm not found at $VLLM"
if command -v tmux >/dev/null && tmux has-session -t vllm 2>/dev/null; then
  die "the tmux vLLM session from serve.sh is running on :$PORT. Stop it first: tmux kill-session -t vllm"
fi
service_active=0
if command -v systemctl >/dev/null && systemctl is-active --quiet "$UNIT" 2>/dev/null; then service_active=1; fi
if ((service_active == 0)) && command -v ss >/dev/null && ss -ltnH "sport = :$PORT" | grep -q .; then
  die "something else is already listening on :$PORT: $(ss -ltnpH "sport = :$PORT" 2>/dev/null | head -1)"
fi

# --- 1. promote the adapter -------------------------------------------------
say "adapter: $SRC -> $DEST"
if [[ -d "$DEST" ]] && cmp -s "$SRC/adapter_model.safetensors" "$DEST/adapter_model.safetensors"; then
  say "  already promoted (identical weights); keeping it"
else
  run mkdir -p "$ADAPTERS"
  if [[ -e "$DEST" ]]; then
    backup="$DEST.bak-$(date +%Y%m%d-%H%M%S)"
    say "  a different adapter is at $DEST; keeping it as $backup"
    run mv "$DEST" "$backup"
  fi
  run cp -a "$SRC" "$DEST"
  commit="$(git -C "$REPO" rev-parse HEAD 2>/dev/null || echo unknown)"
  weights_sha="$(sha256sum "$SRC/adapter_model.safetensors" 2>/dev/null | cut -d' ' -f1 || shasum -a 256 "$SRC/adapter_model.safetensors" | cut -d' ' -f1)"
  meta="$HERE/data/p2/meta.json"
  provenance=$(python3 - "$NAME" "$SRC" "$commit" "$weights_sha" "$meta" <<'PY'
import json, sys, datetime, pathlib
name, src, commit, sha, meta = sys.argv[1:]
m = pathlib.Path(meta)
print(json.dumps({
    "served_as": f"cs1410-{name}",
    "promoted_at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
    "source": src,
    "git_commit": commit,
    "adapter_weights_sha256": sha,
    "dataset_meta_at_promotion": json.loads(m.read_text()) if m.exists() else None,
}, indent=2))
PY
)
  if ((DRY)); then
    say "  [dry-run] write $DEST/PROVENANCE.json:"; say "$provenance" | sed 's/^/      /'
  else
    printf '%s\n' "$provenance" > "$DEST/PROVENANCE.json"
  fi
fi

# --- 2. render and install the unit -----------------------------------------
rendered="$(mktemp)"
trap 'rm -f "$rendered"' EXIT
sed -e "s|@ADAPTER_NAME@|$SERVED|g" -e "s|@ADAPTER_DIR@|$DEST|g" -e "s|@MODEL@|$MODEL|g" \
    -e "s|@VLLM@|$VLLM|g" -e "s|@USER@|$(id -un)|g" -e "s|@GROUP@|$(id -gn)|g" \
    -e "s|@HOME@|$HOME|g" -e "s|@REPO@|$REPO|g" "$HERE/$UNIT.service" > "$rendered"
if grep -q '@[A-Z_]*@' "$rendered"; then die "unfilled placeholder in the rendered unit: $(grep -o '@[A-Z_]*@' "$rendered" | head -1)"; fi
if ((DRY)); then
  say "unit that would be installed at $UNIT_PATH:"; sed 's/^/      /' "$rendered"
fi
say "installing $UNIT_PATH (sudo)"
run sudo install -m 0644 -o root -g root "$rendered" "$UNIT_PATH"
run sudo systemctl daemon-reload
run sudo systemctl enable "$UNIT"

# --- 3. (re)start and wait ---------------------------------------------------
if ((service_active)); then say "restarting $UNIT"; run sudo systemctl restart "$UNIT"
else say "starting $UNIT"; run sudo systemctl start "$UNIT"; fi
if ((DRY)); then say "[dry-run] would wait for http://127.0.0.1:$PORT/v1/models to list $SERVED"; exit 0; fi

say "waiting for vLLM to answer (first start takes about a minute)..."
for _ in $(seq 1 120); do
  if models=$(curl -sf "http://127.0.0.1:$PORT/v1/models"); then
    ids=$(python3 -c 'import json, sys; print("\n".join(m["id"] for m in json.load(sys.stdin)["data"]))' <<<"$models")
    say "up on 127.0.0.1:$PORT, serving:"; say "$ids" | sed 's/^/  /'
    grep -qx "$SERVED" <<<"$ids" || die "$SERVED is not in the model list"
    cat <<EOF

Done. The service starts at boot and restarts on failure.
  status:   systemctl status $UNIT
  logs:     journalctl -u $UNIT -f
  stop:     sudo systemctl stop $UNIT      (before training: vLLM holds 90% of the GPU)
  start:    sudo systemctl start $UNIT
Autograder settings (Jaxon, in the stack's env file):
  LOCAL_LLM_ENDPOINT=http://127.0.0.1:$PORT/v1
  LOCAL_LLM_MODEL=$SERVED
EOF
    exit 0
  fi
  if systemctl is-failed --quiet "$UNIT"; then
    say "$UNIT failed to start. Last log lines:" >&2
    sudo journalctl -u "$UNIT" -n 40 --no-pager >&2 || true
    exit 1
  fi
  sleep 5
done
die "not answering after 10 minutes; check: journalctl -u $UNIT -f"
