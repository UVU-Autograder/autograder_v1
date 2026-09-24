#!/usr/bin/env bash
# Serve the base model, plus any LoRA adapters, with vLLM on :8001 in tmux session "vllm".
#
#   bash backend/training/serve.sh              # base model only (served as gemma4-12b-qat)
#   bash backend/training/serve.sh p2 p2b       # + training/output/p2 as cs1410-p2, p2b as cs1410-p2b
#
# Works from any directory: adapter paths are absolute. It refuses to start if an
# adapter directory has no adapter_config.json or a "vllm" session already exists,
# then waits until the server answers and prints the models it serves. Stop it with
#   tmux kill-session -t vllm
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODEL="${SERVE_BASE_MODEL:-/data/models/gemma4-12b-qat-w4a16}"
VLLM="${VLLM_BIN:-$HOME/venvs/serve/bin/vllm}"
LOG="${VLLM_LOG:-/data/vllm.log}"
PORT=8001

loras=()
for name in "$@"; do
  dir="$HERE/output/$name"
  if [[ ! -f "$dir/adapter_config.json" ]]; then
    echo "no adapter at $dir (adapter_config.json missing)" >&2
    exit 1
  fi
  loras+=("cs1410-$name=$dir")
done

if tmux has-session -t vllm 2>/dev/null; then
  echo "tmux session 'vllm' already exists. Stop it first: tmux kill-session -t vllm" >&2
  exit 1
fi
if command -v systemctl >/dev/null && systemctl is-active --quiet vllm-cs1410 2>/dev/null; then
  echo "the vllm-cs1410 service is serving :$PORT. Evaluate against it directly, or stop it" >&2
  echo "first to serve other adapters here: sudo systemctl stop vllm-cs1410" >&2
  exit 1
fi

args=(serve "$MODEL" --served-model-name gemma4-12b-qat --port "$PORT" --max-model-len 8192
      --gpu-memory-utilization 0.90 --limit-mm-per-prompt '{"image":0,"audio":0}')
if ((${#loras[@]})); then
  args+=(--enable-lora --max-lora-rank 16 --lora-modules "${loras[@]}")
fi
printf -v cmd '%q ' "$VLLM" "${args[@]}"
# No nvcc on the Dell: FlashInfer's sampler would try to JIT-compile and crash.
tmux new-session -d -s vllm "VLLM_USE_FLASHINFER_SAMPLER=0 $cmd 2>&1 | tee $(printf '%q' "$LOG")"

echo "starting vLLM in tmux session 'vllm' (log: $LOG); waiting for it to answer..."
for _ in $(seq 1 120); do
  if models=$(curl -sf "http://127.0.0.1:$PORT/v1/models"); then
    echo "up on :$PORT, serving:"
    python3 -c 'import json, sys; print("\n".join("  " + m["id"] for m in json.load(sys.stdin)["data"]))' <<<"$models"
    exit 0
  fi
  if ! tmux has-session -t vllm 2>/dev/null; then
    echo "vLLM exited during startup. Last lines of $LOG:" >&2
    tail -n 25 "$LOG" >&2
    exit 1
  fi
  sleep 5
done
echo "not answering after 10 minutes; check the log: tail -f $LOG" >&2
exit 1
