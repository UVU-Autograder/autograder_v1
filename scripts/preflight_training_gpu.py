#!/usr/bin/env python3
"""Verify a Blackwell (sm_120) box can actually run QLoRA before you commit to it.

Run this BEFORE the 24GB model download and before building a dataset.  Every
check here corresponds to a failure mode that otherwise shows up hours later as
a misleading error -- most notoriously `CUBLAS_STATUS_EXECUTION_FAILED` from a
torch build that has no sm_120 kernels, and "CUDA driver error: out of memory"
with 25GB free from a Triton kernel-launch failure.

    python3 scripts/preflight_training_gpu.py

Exit code 0 means the stack is sane. Non-zero means fix what it printed first.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys

# Minimum free disk for: 24GB bf16 base + adapters + merged fp16 + a GGUF export.
REQUIRED_FREE_GB = 100
REQUIRED_VRAM_GB = 30  # RTX PRO 4500 Blackwell reports ~32

results: list[tuple[bool, str, str]] = []


def check(ok: bool, label: str, detail: str = "") -> bool:
    results.append((ok, label, detail))
    return ok


def main() -> int:
    parser = argparse.ArgumentParser(description="sm_120 training-stack preflight")
    parser.add_argument("--dir", default=".", help="Volume that will hold weights and checkpoints")
    args = parser.parse_args()

    # --- driver -----------------------------------------------------------
    if shutil.which("nvidia-smi") is None:
        check(False, "nvidia-smi present", "install the NVIDIA driver first")
        return report()

    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,driver_version",
             "--format=csv,noheader"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        name, memory, driver = (part.strip() for part in out.split(",")[:3])
        vram_gb = int(memory.split()[0]) / 1024
        check(True, "GPU detected", f"{name}, {vram_gb:.0f}GiB, driver {driver}")
        check(
            vram_gb >= REQUIRED_VRAM_GB,
            f"VRAM >= {REQUIRED_VRAM_GB}GiB",
            f"found {vram_gb:.0f}GiB",
        )
    except Exception as exc:  # noqa: BLE001
        check(False, "nvidia-smi query", str(exc))
        return report()

    # --- torch ------------------------------------------------------------
    try:
        import torch
    except ImportError:
        check(False, "torch importable", "see docs/guides/ai.md")
        return report()

    check(True, "torch version", torch.__version__)
    check(torch.cuda.is_available(), "torch.cuda.is_available()")

    if not torch.cuda.is_available():
        return report()

    capability = torch.cuda.get_device_capability(0)
    arch = f"sm_{capability[0]}{capability[1]}"
    check(True, "compute capability", arch)

    compiled = torch.cuda.get_arch_list()
    check(
        arch in compiled,
        f"torch built with {arch} kernels",
        f"built for: {', '.join(compiled)}"
        + ("" if arch in compiled else "  <-- THIS IS THE cu128-vs-cu129 TRAP"),
    )

    cuda_version = getattr(torch.version, "cuda", None)
    check(
        cuda_version is not None and tuple(int(x) for x in cuda_version.split(".")[:2]) >= (12, 9),
        "CUDA runtime >= 12.9",
        f"torch.version.cuda = {cuda_version}",
    )

    # --- the check that actually catches the broken builds ----------------
    # A matmul in bf16 on device is what fails with CUBLAS_STATUS_EXECUTION_FAILED
    # when the wheel lacks sm_120 kernels. Import-time checks all pass.
    try:
        a = torch.randn(512, 512, device="cuda", dtype=torch.bfloat16)
        torch.matmul(a, a).float().sum().item()
        torch.cuda.synchronize()
        check(True, "bf16 matmul on device", "real kernels present")
    except Exception as exc:  # noqa: BLE001
        check(False, "bf16 matmul on device", f"{type(exc).__name__}: {exc}")

    # --- quantization stack ----------------------------------------------
    try:
        import bitsandbytes

        check(True, "bitsandbytes version", bitsandbytes.__version__)
        try:
            from bitsandbytes.nn import Linear4bit

            layer = Linear4bit(256, 256, compute_dtype=torch.bfloat16).cuda()
            x = torch.randn(4, 256, device="cuda", dtype=torch.bfloat16)
            layer(x).float().sum().item()
            torch.cuda.synchronize()
            check(True, "bitsandbytes NF4 forward", "QLoRA path works on this GPU")
        except Exception as exc:  # noqa: BLE001
            check(
                False,
                "bitsandbytes NF4 forward",
                f"{type(exc).__name__}: {exc}  <-- sm_120 support is the usual cause",
            )
    except ImportError:
        check(False, "bitsandbytes importable", "required for QLoRA")

    for package in ("transformers", "trl", "peft", "accelerate"):
        try:
            module = __import__(package)
            check(True, f"{package} version", getattr(module, "__version__", "?"))
        except ImportError:
            check(False, f"{package} importable")

    # --- disk -------------------------------------------------------------
    free_gb = shutil.disk_usage(args.dir).free / 1024**3
    check(
        free_gb >= REQUIRED_FREE_GB,
        f"free disk >= {REQUIRED_FREE_GB}GB",
        f"{free_gb:.0f}GB available at {args.dir}",
    )

    return report()


def report() -> int:
    width = max(len(label) for _, label, _ in results) + 2
    print()
    for ok, label, detail in results:
        print(f"  {'PASS' if ok else 'FAIL'}  {label:<{width}} {detail}")
    failed = [label for ok, label, _ in results if not ok]
    print()
    if failed:
        print(f"{len(failed)} check(s) failed: {', '.join(failed)}")
        print("See docs/guides/ai.md")
        return 1
    print("Stack looks good. Safe to download the base model and start training.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
