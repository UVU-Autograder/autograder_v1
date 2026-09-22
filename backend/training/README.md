# Training — pipeline smoke run on the Dell

Proves **train → serve → eval** works on the RTX PRO 4500 Blackwell (`sm_120`)
before any real dataset exists. The adapter this produces is throwaway: 20
synthetic rows, 30 steps. Success means every stage runs and a scoreboard row
gets written — not that the model got better.

All of this runs on the Dell over SSH. Student-derived data never leaves it.

| File | Role |
| --- | --- |
| `make_smoke_dataset.py` | 24 synthetic rows (DS1 / DS3 / Lab 2) → `data/smoke/{train,valid}.jsonl`. Built through `prompts.build_messages` so the prompt is byte-identical to eval and serving. |
| `train_lora.py` | QLoRA (NF4, bf16 compute, SDPA attention) → PEFT adapter in `output/smoke/`. |
| `requirements-train.txt` | `~/venvs/train` — pinned sm_120 stack. |
| `requirements-serve.txt` | `~/venvs/serve` — vLLM, kept apart so it can't bump torch under bitsandbytes. |

`data/` and `output/` are gitignored.

## 0. Preflight first

From the repo root:

```bash
bash scripts/preflight_dell.sh
```

With the Dell's stack already running this is read-only (existing-stack mode —
see `docs/deployment/blackwell_training_setup.md`). Paste the
`preflight-report-*.txt` back. Don't train until it's green (or every WARN is
understood).

## 1. Training venv

```bash
python3.12 -m venv ~/venvs/train
```

```bash
~/venvs/train/bin/pip install torch==2.11.0 --index-url https://download.pytorch.org/whl/cu129
```

```bash
~/venvs/train/bin/pip install -r backend/training/requirements-train.txt
```

```bash
~/venvs/train/bin/python scripts/preflight_training_gpu.py --dir /data
```

`torch built with sm_120 kernels`, `bf16 matmul on device`, and `bitsandbytes NF4
forward` must all PASS.

## 2. Weights

Accept the Gemma license on the model page with your HF account first — the repos
are gated.

```bash
export HF_HOME=/data/hf && hf auth login
```

```bash
hf download google/gemma-4-12B-it-qat-q4_0-unquantized --local-dir /data/models/gemma4-12b-qat-bf16
```

```bash
hf download google/gemma-4-12B-it-qat-w4a16-ct --local-dir /data/models/gemma4-12b-qat-w4a16
```

The first is the training base (QAT weights in bf16). The second is the serving
base. Same underlying QAT weights, so the adapter trained on one loads on the other.

## 3. Train

```bash
cd backend && ~/venvs/train/bin/python -m training.make_smoke_dataset
```

```bash
~/venvs/train/bin/python -m training.train_lora --base /data/models/gemma4-12b-qat-bf16 --max-steps 30
```

Paste back the `training summary` JSON it prints — peak VRAM and the loss numbers
are what matter. Expect peak VRAM well under 32GiB.

Stop anything else on the GPU first (`nvidia-smi`). Training and vLLM can't share
the card. The autograder stack itself is CPU-only and can stay up.

## 4. Serve

```bash
python3.12 -m venv ~/venvs/serve && ~/venvs/serve/bin/pip install -r backend/training/requirements-serve.txt
```

```bash
~/venvs/serve/bin/vllm serve /data/models/gemma4-12b-qat-w4a16 --served-model-name gemma4-12b-qat --port 8001 --max-model-len 8192 --gpu-memory-utilization 0.90 --enable-lora --lora-modules cs1410-smoke=backend/training/output/smoke --max-lora-rank 16 --limit-mm-per-prompt '{"image":0,"audio":0}'
```

Port 8001 because the autograder backend owns 8000. Paste back the `Maximum
concurrency for 8192 tokens per request` line from startup.

**Don't add `--chat-template`, `--reasoning-parser` or
`--default-chat-template-kwargs`** even though vLLM's Gemma 4 recipe uses them.
The adapter was trained on prompts rendered with the checkpoint's own template
and defaults (`train_lora` prints what that template opens the model turn with);
serving with a different template would feed the model a format it wasn't
trained on.

If vLLM refuses LoRA for this architecture, merge the adapter into the bf16
base instead and serve that (24GB of weights still fits at `--max-model-len 8192`):

```bash
~/venvs/train/bin/python -c "from transformers import AutoModelForMultimodalLM as M; from peft import PeftModel; m = PeftModel.from_pretrained(M.from_pretrained('/data/models/gemma4-12b-qat-bf16', dtype='bfloat16'), 'backend/training/output/smoke').merge_and_unload(); m.save_pretrained('/data/models/cs1410-smoke-merged')"
```

```bash
~/venvs/train/bin/python -c "from transformers import AutoProcessor; AutoProcessor.from_pretrained('/data/models/gemma4-12b-qat-bf16').save_pretrained('/data/models/cs1410-smoke-merged')"
```


If vLLM refuses LoRA on the compressed-tensors base, serve the bf16 training base
instead for the smoke run (`vllm serve /data/models/gemma4-12b-qat-bf16 ...`,
same flags) and note it — that's a finding, not a failure.

## 5. Score it

In a second SSH session, from `backend/`. The train venv already has the harness's
only dependencies (`pydantic`, `httpx`):

```bash
~/venvs/train/bin/python -m eval.run_eval --endpoint http://127.0.0.1:8001/v1 --model gemma4-12b-qat --label stock-12b-dell
```

```bash
~/venvs/train/bin/python -m eval.run_eval --endpoint http://127.0.0.1:8001/v1 --model cs1410-smoke --label smoke-lora
```

Paste back `eval/results/scoreboard.csv`. Two rows, same server, same prompt
version: that's the comparison every future adapter gets measured against.

## Troubleshooting

See the table in `docs/deployment/blackwell_training_setup.md`. The short version:
`CUBLAS_STATUS_EXECUTION_FAILED` → wrong torch wheel; "out of memory" with free
VRAM → Triton on sm_120 (`TORCHDYNAMO_DISABLE=1`); FlashAttention head-dim error →
something overrode `attn_implementation="sdpa"`.
