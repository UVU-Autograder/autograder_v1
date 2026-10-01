# Training and serving tools

Use the [AI guide](../../docs/guides/ai.md) for environment setup, serving/evaluation, reviewed targets, training, promotion and rollback. Use the [workstation guide](../../docs/guides/workstation.md) before host preflight; it describes side effects and database isolation.

| Tool/file | Purpose |
| --- | --- |
| `make_smoke_dataset.py` | Small synthetic pipeline dataset; its output is a smoke test, not a quality claim |
| `train_lora.py` | QLoRA training; inspect `--help`, lengths and emitted summary before changing defaults |
| `draft_p2.py` / `build_p2_dataset.py` | Draft reviewed targets and build only approved guardrail-valid examples |
| `p2/review/` | Versioned synthetic target reviews and provenance |
| `requirements-train.txt` / `requirements-serve.txt` | Separate pinned GPU environments |
| `serve.sh` | Temporary tmux comparison service; do not run alongside systemd on the same port |
| `install_vllm_service.sh` | Dry-run/install adapter promotion with provenance and rendered systemd service |
| `vllm-cs1410.service` | Installer template, not a unit to copy without rendering |

`data/` and `output/` are gitignored working artifacts. Keep synthetic evaluation separate from training. Student code/corpora require the [institutional data constraints](../../docs/considerations.md#ai-data-and-future-changes); do not transfer them to personal devices or commit them as fixtures.
