"""QLoRA fine-tune for the sandbox feedback model on the Dell (RTX PRO 4500, sm_120).

    cd backend && ~/venvs/train/bin/python -m training.train_lora --max-steps 30

Defaults are the pipeline smoke run: ~20 synthetic rows, 30 steps. The output is
a standard PEFT adapter (adapter_config.json + adapter_model.safetensors) that
vLLM loads directly with --enable-lora -- no fuse, no GGUF, no MLX conversion.

Gemma 4 12B specifics baked in:
- It is "Gemma 4 Unified" (model_type gemma4_unified, transformers >= 5.10.1),
  loaded with AutoModelForMultimodalLM as the model card does. It has no vision
  or audio tower -- raw inputs go through small projections (embed_vision,
  embed_audio) straight into model.language_model.
- attn_implementation="sdpa": Gemma 4's wide global-attention heads exceed
  FlashAttention's 256 head-dim limit and fail outright.
- LoRA targets only model.language_model.layers.* projections; the multimodal
  projections are excluded. The feedback path is text-only.
- Loss on the assistant turn only (prompt/completion split), so the model learns
  the response, not to reproduce the system prompt.
"""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

HERE = Path(__file__).parent
DEFAULT_BASE = os.environ.get("TRAIN_BASE_MODEL", "/data/models/gemma4-12b-qat-bf16")

# Conventional short-name list (what vLLM and most LoRA loaders expect in
# adapter_config.json), with the vision/audio towers excluded separately so the
# adapter only touches the language model.
TARGET_MODULES = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
EXCLUDE_MODULES = r".*(?:vision|audio|embed_vision|embed_audio|multi_modal).*"


def to_prompt_completion(row: dict) -> dict:
    """{"messages": [sys, user, asst]} -> TRL conversational prompt/completion.

    TRL computes loss on the completion only for this format, which avoids
    depending on {% generation %} markers in the Gemma chat template.
    """
    messages = row["messages"]
    assert messages[-1]["role"] == "assistant", "last turn must be the target"
    return {"prompt": messages[:-1], "completion": messages[-1:]}


def load_model_and_tokenizer(base: str, quantize: bool = True):
    """Load the checkpoint in NF4 (QLoRA). ``quantize=False`` is for CPU checks only."""
    import torch
    from transformers import (
        AutoModelForCausalLM,
        AutoModelForMultimodalLM,
        AutoTokenizer,
        BitsAndBytesConfig,
    )

    kwargs: dict = {"attn_implementation": "sdpa", "dtype": torch.bfloat16 if quantize else torch.float32}
    if quantize:
        kwargs["quantization_config"] = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_use_double_quant=True,
        )
        kwargs["device_map"] = {"": 0}
    # Gemma 4 Unified registers under the multimodal-LM auto class (per the model
    # card); plain causal-LM checkpoints fall through to the second loader.
    errors = []
    for loader in (AutoModelForMultimodalLM, AutoModelForCausalLM):
        try:
            model = loader.from_pretrained(base, **kwargs)
            print(f"loaded {type(model).__name__} via {loader.__name__}")
            break
        except (ValueError, KeyError) as exc:
            errors.append(f"{loader.__name__}: {str(exc).splitlines()[0]}")
    else:
        raise SystemExit(
            "no transformers auto class can load this checkpoint -- is transformers too old for its "
            "model_type? (Gemma 4 12B needs >= 5.10.1)\n  " + "\n  ".join(errors)
        )

    tokenizer = AutoTokenizer.from_pretrained(base)
    if tokenizer.chat_template is None:
        from transformers import AutoProcessor

        tokenizer.chat_template = AutoProcessor.from_pretrained(base).chat_template
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    return model, tokenizer


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="QLoRA fine-tune (Gemma 4 12B QAT, sm_120)")
    parser.add_argument("--base", default=DEFAULT_BASE, help="bf16 checkpoint dir (qat-q4_0-unquantized)")
    parser.add_argument("--data", type=Path, default=HERE / "data" / "smoke")
    parser.add_argument("--out", type=Path, default=HERE / "output" / "smoke")
    parser.add_argument("--max-steps", type=int, default=30)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--rank", type=int, default=8)
    parser.add_argument("--alpha", type=int, default=16)
    parser.add_argument("--max-length", type=int, default=2048)
    parser.add_argument("--grad-accum", type=int, default=4)
    args = parser.parse_args(argv)

    import torch
    import transformers
    import trl
    from datasets import load_dataset
    from peft import LoraConfig
    from trl import SFTConfig, SFTTrainer

    for split in ("train", "valid"):
        if not (args.data / f"{split}.jsonl").exists():
            raise SystemExit(f"missing {args.data}/{split}.jsonl -- run: python -m training.make_smoke_dataset")

    dataset = load_dataset(
        "json",
        data_files={"train": str(args.data / "train.jsonl"), "validation": str(args.data / "valid.jsonl")},
    ).map(to_prompt_completion, remove_columns=["messages"])

    started = time.time()
    torch.cuda.reset_peak_memory_stats()
    model, tokenizer = load_model_and_tokenizer(args.base)
    # No explicit prepare_model_for_kbit_training: SFTTrainer runs it for 4-bit
    # models (and it upcasts non-4-bit weights -- here mainly the ~1B-param
    # embedding table -- to fp32, ~+2GB; there are no per-layer embeddings).
    print(f"base loaded in {time.time() - started:.0f}s, {torch.cuda.memory_allocated() / 1024**3:.1f}GiB resident")

    lora = LoraConfig(
        r=args.rank,
        lora_alpha=args.alpha,
        lora_dropout=0.05,
        target_modules=TARGET_MODULES,
        exclude_modules=EXCLUDE_MODULES,
        bias="none",
        task_type="CAUSAL_LM",
    )
    config = SFTConfig(
        output_dir=str(args.out / "checkpoints"),
        max_steps=args.max_steps,
        per_device_train_batch_size=1,
        per_device_eval_batch_size=1,
        gradient_accumulation_steps=args.grad_accum,
        learning_rate=args.lr,
        lr_scheduler_type="cosine",
        # warmup_ratio was removed in transformers 5.x; ~10% of steps, explicitly.
        warmup_steps=max(1, args.max_steps // 10),
        bf16=True,
        gradient_checkpointing=True,
        gradient_checkpointing_kwargs={"use_reentrant": False},
        max_length=args.max_length,
        completion_only_loss=True,
        packing=False,
        logging_steps=1,
        eval_strategy="steps",
        eval_steps=max(1, args.max_steps // 3),
        save_strategy="no",
        report_to="none",
        seed=1410,
    )
    trainer = SFTTrainer(
        model=model,
        args=config,
        train_dataset=dataset["train"],
        eval_dataset=dataset["validation"],
        processing_class=tokenizer,
        peft_config=lora,
    )
    trainer.model.print_trainable_parameters()
    adapted = [name for name, _ in trainer.model.named_modules() if name.endswith(".lora_A")]
    adapted_count = len(adapted)
    leaked = [name for name in adapted if ".layers." not in name or any(t in name for t in ("vision", "audio", "multi_modal"))]
    if leaked:
        raise SystemExit(f"LoRA attached to non-language modules: {leaked[:5]}")
    print(f"LoRA attached to {adapted_count} language-model projections")

    result = trainer.train()
    metrics = trainer.evaluate()
    args.out.mkdir(parents=True, exist_ok=True)
    trainer.model.save_pretrained(str(args.out))
    tokenizer.save_pretrained(str(args.out))

    losses = [e["loss"] for e in trainer.state.log_history if "loss" in e]
    summary = {
        "base": args.base,
        "prompt_version": json.loads((args.data / "meta.json").read_text()).get("prompt_version")
        if (args.data / "meta.json").exists()
        else None,
        "steps": result.global_step,
        "train_loss_first": losses[0] if losses else None,
        "train_loss_last": losses[-1] if losses else None,
        "eval_loss": metrics.get("eval_loss"),
        "peak_vram_gib": round(torch.cuda.max_memory_allocated() / 1024**3, 2),
        "wall_seconds": round(time.time() - started),
        "lora": {
            "r": args.rank,
            "alpha": args.alpha,
            "target_modules": TARGET_MODULES,
            "exclude_modules": EXCLUDE_MODULES,
            "adapted_modules": adapted_count,
        },
        "versions": {"torch": torch.__version__, "transformers": transformers.__version__, "trl": trl.__version__},
        "gpu": torch.cuda.get_device_name(0),
    }
    (args.out / "training_summary.json").write_text(json.dumps(summary, indent=2))
    print("\n--- training summary (paste this back) ---")
    print(json.dumps(summary, indent=2))
    print(f"\nadapter saved to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
