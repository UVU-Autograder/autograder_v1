# Blackwell Training Setup — LoRA on the Dell Workstation

Target: RTX PRO 4500 Blackwell (32GB GDDR7, `sm_120`), Ubuntu 24.x.

This replaces the MacBook/MLX training path in the tuning blueprint. Training and
serving both happen on the workstation, so student-derived data never leaves
university-managed hardware.

## Why this is the better posture

Keeping the corpus on one institutionally-controlled machine is a materially
stronger FERPA story than copying student-derived data to a personal laptop.
[ferpa_analysis.md](../core/ferpa_analysis.md) turns on *institutional control*,
not on how little data you store — a personal MacBook is outside that control
boundary regardless of how careful the operator is.

Two consequences worth making explicit:

- **The Dell becomes the single custody point.** Delete the MLX copies and any
  student-derived working files from the MacBook once the corpus lives here. A
  posture with two copies is worse than either single copy.
- **Document it.** "Training occurs only on UVU-managed hardware; no student
  data is processed on personal devices" is one sentence, and it is the kind of
  sentence that shortens an ATSC review considerably.

This does **not** change the §7 recommendation in the blueprint: still prefer
synthesizing training targets from a mined error taxonomy over training on real
student code. Model weights are permanent, unauditable retention no matter which
machine produces them.

## Operational note

You cannot serve and train on one 32GB card at the same time. Training will
saturate the GPU for hours. Schedule training against sandbox downtime, or
accept that the POC endpoint is down while a run is in flight.

---

## Step 0 — preflight the full suite

Before any training, prove the whole autograder works on this machine. From the
repo root over SSH:

```bash
bash scripts/preflight_dell.sh
```

**On the Dell the stack is normally already running** (it's the live deployment),
so the script switches itself to **existing-stack mode**: it checks what is running
and never builds, recreates, stops, or reinstalls anything — no `.env.local`
changes, no Kata installer, no `docker compose down`. The report's `mode:` line
says which mode ran. Two side effects to know about: the model-solution checks
overwrite each assignment's "validation status" in the staff UI with the
preflight's run, and the sandbox check spends one upload from a fresh session's
quota.

On a machine with nothing running it builds and starts the stack instead. Useful
flags there: `--install-kata` (run the Kata installer if the runtime is missing),
`--keep-up` (don't stop the stack afterwards). `--rebuild` forces a rebuild of a
stack that is already up — don't use it on the Dell without the person who
deployed it.

It runs nine independent stages — host, cgroups, Kata, stack up, end-to-end
stack checks, backend tests, frontend build, GPU/training stack, teardown — and
writes `preflight-report-<timestamp>.txt`. The end-to-end stage
(`scripts/preflight_stack.py`) runs a real Python + pytest submission through
Judge0, verifies `DELETE /submissions/{token}`, grades every seeded model
solution through Celery → Judge0 → scoring via the existing
`validate-model-solution` endpoint, and round-trips one sandbox upload.

Two things it will likely flag on a fresh Ubuntu 24.04 box:

- **cgroup v2.** Ubuntu 24.04 defaults to v2 and stock Judge0 1.13.x's `isolate`
  expects v1. The compose file already runs Judge0 in rlimit mode to cope, so this
  is a WARN; stage 5's real submission is the verdict. Only if that fails does the
  GRUB fallback below apply — the script prints it but never edits GRUB itself.
- **Kata.** `--install-kata` runs `scripts/install-kata-docker-runtime-ubuntu.sh`
  under sudo if the runtime is missing. Without the flag it warns and continues on
  the default Docker runtime.

### Switching the host to cgroup v1 (over SSH) — fallback only

**You probably don't need this.** Since commit `6bb6e41`, `docker-compose.yml`
runs Judge0 in rlimit mode (`ENABLE_PER_PROCESS_AND_THREAD_TIME_LIMIT` /
`_MEMORY_LIMIT: "true"` on `judge0` and `judge0-worker`), which skips isolate's
cgroup accounting and works on cgroup v2. The preflight reports that as a WARN,
not a FAIL. Limits become per-process rather than per-sandbox — acceptable
behind Kata's VM boundary, weaker without it (see the Cgroups section of
[workstation_deployment.md](workstation_deployment.md)), which also records Judge0
under Kata verified end to end on this Dell with cgroup v2 as-is.

Only switch the host to v1 if stage 5's Judge0 submission still fails in rlimit
mode, or if you later want cgroup-accounted limits on the non-Kata path. Ubuntu
24.04's systemd 255 still honours the flag below, and this Dell's
`6.17.0-*-oem` kernel is built with `CONFIG_MEMCG_V1=y` and `CONFIG_CPUSETS_V1=y`,
so v1 controllers would be available; the Arch/systemd 261 limitation in that doc
does not apply here. Check any other kernel before relying on it:
`grep -E 'CONFIG_MEMCG_V1|CONFIG_CPUSETS_V1' /boot/config-$(uname -r)`.

Note the change is **armed for the next reboot, whoever triggers it** (an update,
another user). Don't leave the drop-in in place unless you mean to switch. And
this is a remote reboot with other people possibly logged in (`who`) — coordinate
before rebooting, then read the safety checks.

**Before you reboot**, confirm the machine can come back without you in the room:

```bash
lsblk -f | grep -i crypto_LUKS
```

If that prints anything, the disk is encrypted and the reboot will stop at a
passphrase prompt on the physical console. Don't reboot remotely without someone
at the machine or remote unlock set up. Also check nobody else is using the box
(`who`) and that you have a fallback (physical access or iDRAC/out-of-band).

**Apply** — a drop-in file, so the main `/etc/default/grub` is untouched and undo
is one `rm`:

```bash
echo 'GRUB_CMDLINE_LINUX="$GRUB_CMDLINE_LINUX systemd.unified_cgroup_hierarchy=0"' | sudo tee /etc/default/grub.d/99-cgroup-v1.cfg
```

```bash
sudo update-grub
```

```bash
sudo grep -c "systemd.unified_cgroup_hierarchy=0" /boot/grub/grub.cfg
```

`grub.cfg` is root-only on this box, hence `sudo`. The count must be non-zero
before you reboot (one per boot entry — 5 on this Dell) — it means the flag
actually made it into the generated boot config.

```bash
sudo reboot
```

**Verify** after reconnecting (allow a couple of minutes):

```bash
stat -fc %T /sys/fs/cgroup && docker info --format 'cgroup v{{.CgroupVersion}}, driver {{.CgroupDriver}}' && grep -o 'systemd.unified_cgroup_hierarchy=0' /proc/cmdline
```

Expect `tmpfs`, then `cgroup v1`, then the flag echoed back. Then re-run the
preflight.

**Undo** (before rebooting, no reboot needed; the count should drop to 0):

```bash
sudo rm /etc/default/grub.d/99-cgroup-v1.cfg && sudo update-grub && sudo grep -c "systemd.unified_cgroup_hierarchy=0" /boot/grub/grub.cfg
```

If you already rebooted into v1, add `&& sudo reboot` to return to v2.

**Leave `/etc/docker/daemon.json` alone.** Some guides say to write
`{"exec-opts": ["native.cgroupdriver=cgroupfs"]}` into it. Docker picks the
right driver for v1 without that, and *overwriting* the file deletes the
`kata-runtime` registration the Kata install script merged in. If you ever do
need to change it, merge rather than replace, and keep `runtimes` intact.

**Kata caveat.** With the Kata override on, Judge0's `isolate` runs inside the
Kata VM, and its cgroups come from the *guest* kernel — the host GRUB flag
doesn't control them. The host flag still matters for the non-Kata path and for
Kata's own host-side cgroup handling, but whether `isolate` works under Kata is
decided by the guest. That's why the preflight treats stage 5's real submission as
the verdict, not the cgroup stage. If submissions pass on the default runtime
and fail under Kata, the fix is in the Kata guest configuration, not GRUB.

The backend test stage runs in a throwaway container on in-memory SQLite. That
matters: the suite's `reset_database` fixture calls `drop_all()` on whatever
`DATABASE_URL` points at, so running pytest inside the live backend container
would wipe the seeded database.

Keep three environments separate: the API image (Docker), `~/venvs/train`
(torch cu129 + bitsandbytes), and `~/venvs/serve` (vLLM, which pins its own
torch). Mixing train and serve is how torch gets bumped out from under
bitsandbytes. Run order for the smoke training run is in
[backend/training/README.md](../../backend/training/README.md).

The GPU-only check can also run on its own:

```bash
python3 scripts/preflight_training_gpu.py --dir /data
```

## Step 1 — the software stack

`sm_120` is new enough that the default wheels are wrong in a way that passes
every import check and then fails at the first real matmul.

**The trap: `cu128` is not enough.** A `torch 2.10.0+cu128` build lacks working
Blackwell cuBLAS kernels and dies with `CUBLAS_STATUS_EXECUTION_FAILED` once
training starts. Use `cu129`.

```bash
sudo apt install -y python3.13 python3.13-venv
python3.13 -m venv ~/venvs/train && source ~/venvs/train/bin/activate
```

```bash
pip install torch==2.11.0 --index-url https://download.pytorch.org/whl/cu129
```

```bash
pip install "transformers==5.5.3" "trl==0.23.1" "bitsandbytes==0.49.2" peft accelerate datasets huggingface_hub
```

Known-good combination on 32GB Blackwell, from a Gemma 4 QLoRA run on an RTX 5090
(same `sm_120`, same 32GB):

| Component | Version |
| --- | --- |
| Python | 3.13 |
| torch | 2.11.0+cu129 |
| transformers | 5.5.3 |
| trl | 0.23.1 |
| bitsandbytes | 0.49.2 |
| peft LoRA | r=8, alpha=16 |

Re-run the preflight after installing. The `bitsandbytes NF4 forward` check is
the one that matters — bitsandbytes `sm_120` support landed late, and an import
that succeeds tells you nothing about whether the kernels run.

### Optional: Unsloth

Stock PyPI Unsloth lacked Blackwell kernels for Gemma 4's hybrid attention; the
Studio installer ships custom ones and reported ~22GB for the **31B** at
`seq_length=512`. Worth trying for the speed and memory savings:

```bash
curl -fsSL unsloth.ai/install.sh | sh
```

Treat it as an optimization, not a dependency — plain `peft` + `trl` works.

## Step 2 — Hugging Face access

Gemma repos are **gated**. You must accept the license on the model page with the
account whose token you use, or the download 401s.

1. Visit `https://huggingface.co/google/gemma-4-12B-it-qat-q4_0-unquantized` and
   accept the terms.
2. Create a read token at `https://huggingface.co/settings/tokens`.

```bash
curl -LsSf https://hf.co/cli/install.sh | bash
```

```bash
hf auth login
```

## Step 3 — put the cache on the right disk

Workstation root partitions are routinely too small for this. Point `HF_HOME` at
the large volume *before* downloading, or you will fill `/` at 80%.

```bash
echo 'export HF_HOME=/data/hf' >> ~/.bashrc && source ~/.bashrc && mkdir -p /data/hf
```

## Step 4 — download the base model

Check the size first:

```bash
hf download google/gemma-4-12B-it-qat-q4_0-unquantized --dry-run
```

Then pull it (~24GB, bf16 safetensors):

```bash
hf download google/gemma-4-12B-it-qat-q4_0-unquantized --local-dir /data/models/gemma4-12b-qat-bf16
```

**Why the `-unquantized` repo and not the GGUF:** you cannot train a GGUF, and
this repo is the QAT weights de-quantized to bf16 — fine-tune it, then requantize
to `q4_0` and you land back on the grid QAT was trained for. Using plain
`google/gemma-4-12B-it` instead throws that away.

`bitsandbytes` quantizes to NF4 in VRAM at load time, so ~24GB on disk becomes
~7GB resident. You do not need a pre-quantized checkpoint.

## Step 5 — the Gemma 4 attention gotcha

Gemma 4's hybrid attention uses 512-dim global layers. FlashAttention supports
head dimensions up to 256, so it fails outright. Force SDPA:

```python
model = AutoModelForCausalLM.from_pretrained(
    "/data/models/gemma4-12b-qat-bf16",
    attn_implementation="sdpa",          # NOT flash_attention_2 — 512-dim global layers
    dtype=torch.bfloat16,
    quantization_config=BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    ),
)
```

## Step 6 — VRAM budget

| Item | 12B QLoRA @ seq 2048 |
| --- | --- |
| NF4 base weights | ~7 GB |
| LoRA params + optimizer (r=8) | <1 GB |
| Activations, grad checkpointing on | ~6–10 GB |
| Fragmentation + CUDA context | ~2 GB |
| **Total** | **~16–20 GB of 32 GB** |

Comfortable. Raise `seq_length` before raising rank if you have headroom —
truncated targets hurt more than low-rank adapters do.

**On the 31B:** the ~22GB figure circulating for 31B QLoRA on 32GB cards is at
`seq_length=512`. Your prompts run 4–6K tokens, and activation memory scales with
sequence length, so 31B at a usable `seq_length` will not fit. 12B remains the
right target — and it is also what you want to serve for 50 concurrent students.

## Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| `CUBLAS_STATUS_EXECUTION_FAILED` | torch wheel has no `sm_120` kernels | Reinstall `torch==2.11.0+cu129`; confirm with the preflight's arch-list check |
| "CUDA driver error: out of memory" with 25GB+ free | Triton kernel launch failure on `sm_120` | `TORCHDYNAMO_DISABLE=1 UNSLOTH_COMPILE_DISABLE=1` as an interim workaround |
| Errors persist after a correct reinstall | Stale compiled kernels | `rm -rf /tmp/unsloth_compiled_cache/` |
| `FlashAttention forward only supports head dimension at most 256` | Gemma 4 hybrid attention | `attn_implementation="sdpa"` |
| bitsandbytes import fine, forward pass fails | `sm_120` kernels missing | Pin `bitsandbytes==0.49.2` against a `cu129` torch; do not let another package bump torch to `cu130` |
| 401 on download | Gated repo | Accept the license on the model page with the token's account |

## After training

The deployment path is unchanged from the blueprint — and gets simpler when
training and serving share a machine, since vLLM serves the adapter directly
with no merge, no GGUF conversion, and no quantization drift:

```bash
vllm serve google/gemma-4-12B-it-qat-w4a16-ct --max-model-len 8192 --gpu-memory-utilization 0.90 --enable-lora --lora-modules cs1410=/data/adapters/cs1410 --max-lora-rank 16
```

Training with `peft` here rather than MLX also removes the adapter-format
conversion seam flagged in the blueprint — `peft` writes exactly what vLLM
expects.

Re-run the Phase 0 eval against the served endpoint before shipping:

```bash
cd backend && python -m eval.run_eval --endpoint vllm --model cs1410 --label lora-v1
```
