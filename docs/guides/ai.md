# Serve, evaluate and train local AI

Sandbox feedback uses Gemma 4 12B QAT plus `cs1410-p2c`; `gemma4-12b-qat` is the base rollback. Grading remains pytest-based. [Data requirements](../considerations.md#ai-data-and-future-changes) govern training and feedback.

## Feedback contract

[Shared prompts](../../backend/app/integrations/ai/prompts.py) and [guardrails](../../backend/app/integrations/ai/guardrails.py) own live/eval/training parity. Input caps are 10,000 characters/file, 16,000 total code and 800/failure message. Responses explain grounded failures without scores/solutions; full validation precedes streaming. Invalid/unavailable AI yields fallback. Reviewed targets are synthetic seed mutations; preserve [provenance](../../backend/training/p2/review/) and held-out separation.

## Operate the model service

From the Linux checkout:

```bash
bash backend/training/install_vllm_service.sh p2c --dry-run
bash backend/training/install_vllm_service.sh p2c
systemctl status vllm-cs1410.service --no-pager
curl -fsS http://127.0.0.1:8001/v1/models
```

Requires `backend/training/output/p2c` (resolved by the installer), `/data/models/gemma4-12b-qat-w4a16` and `~/venvs/serve/bin/vllm`. The [installer](../../backend/training/install_vllm_service.sh) promotes weights with provenance/backups and renders the service; do not copy its unit template directly.

Backend settings are `LOCAL_LLM_ENDPOINT=http://127.0.0.1:8001/v1`, `LOCAL_LLM_MODEL=cs1410-p2c`. To use base rollback, change the model to `gemma4-12b-qat` and recreate affected Compose containers using the [workstation context](workstation.md); restart alone does not apply env changes. Restore an older adapter from the installer's backup with vLLM stopped, then re-evaluate.

Temporary comparisons use `bash backend/training/serve.sh p2b p2c`; stop systemd first, and stop its tmux session before restarting systemd. Keep checkpoint templates/defaults unchanged.

## Prepare GPU environments

On university-controlled hardware, keep API, training and serving environments separate. From the repository root:

```bash
python3.12 -m venv ~/venvs/train
~/venvs/train/bin/pip install torch==2.11.0 --index-url https://download.pytorch.org/whl/cu129
~/venvs/train/bin/pip install -r backend/training/requirements-train.txt
python3.12 -m venv ~/venvs/serve
~/venvs/serve/bin/pip install -r backend/training/requirements-serve.txt
~/venvs/train/bin/python scripts/preflight_training_gpu.py --dir /data
```

Repository pins cover Blackwell kernels; vLLM can otherwise replace training torch. Inspect `nvidia-smi`; stop serving before GPU training. Accept the model license and authenticate with `~/venvs/train/bin/hf auth login`, then:

```bash
~/venvs/train/bin/hf download google/gemma-4-12B-it-qat-q4_0-unquantized --local-dir /data/models/gemma4-12b-qat-bf16
~/venvs/train/bin/hf download google/gemma-4-12B-it-qat-w4a16-ct --local-dir /data/models/gemma4-12b-qat-w4a16
```

Training uses bf16 QAT weights with NF4; serving uses w4a16. Keep the loader's SDPA path and serving sampler settings from maintained scripts.

## Build, train and evaluate

From `backend/`, using the training venv:

```bash
source ~/venvs/train/bin/activate
python -m eval.build_cases --split train
python -m training.draft_p2 --model gemma4-12b-qat
python -m training.build_p2_dataset --status
python -m training.build_p2_dataset
python -m training.train_lora --help
python -m eval.run_eval --endpoint http://127.0.0.1:8001/v1 --model cs1410-p2c --label adapter-current --guided
```

Draft while serving; review/approve targets before the strict builder. Choose a new training output, inspect `--lengths-only`, then set reviewed lengths/hyperparameters; defaults are a smoke recipe. Serve/evaluate the candidate before promotion.

[Eval tooling](../../backend/eval/README.md) owns cases/metrics; [training tools](../../backend/training/README.md) own CLI details. Compare models under matching cases/prompt/decoding; unguided checks native schema ability, guided matches production. Hard checks do not replace staff review of diagnosis/helpfulness.

For failures, inspect `journalctl -u vllm-cs1410 -n 50 --no-pager` and the earlier EngineCore error. Re-run GPU kernel preflight for torch/NF4 failures; verify absolute adapter paths and model-license access. AI downtime must leave grading usable.

## Sandbox load and end-to-end verification

Test live sandbox grading and feedback without student data using synthetic eval cases:

```bash
# Exercise a single synthetic case end to end (standard library only)
python scripts/mock_sandbox_run.py --list
python scripts/mock_sandbox_run.py CASE_ID --api http://10.115.20.200/api

# Load-test concurrent student feedback on the workstation (levels 1, 2, 4, 8, 16)
python scripts/mock_sandbox_load.py --levels 1,2,4,8,16 --requests 48
```

The load tester grades synthetic runs through Judge0, then triggers simultaneous AI feedback requests, reporting p50/p95/max latency, throughput, fallback causes (timeout at 30s limit, guardrail, unreachable), vLLM queue depth, KV cache utilization, and GPU metrics via `nvidia-smi`.

