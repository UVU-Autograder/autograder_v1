"""QLoRA fine-tune for the sandbox feedback model on the Dell (RTX PRO 4500, sm_120).

    cd backend && ~/venvs/train/bin/python -m training.train_lora --max-steps 30

Defaults are the pipeline smoke run: ~20 synthetic rows, 30 steps. The output is
a standard PEFT adapter (adapter_config.json + adapter_model.safetensors) that
vLLM loads directly with --enable-lora -- no fuse, no GGUF, no MLX conversion.

Gemma 4 specifics baked in:
- attn_implementation="sdpa": the 512-dim global attention layers exceed
  FlashAttention's 256 head-dim limit and fail outright.
- LoRA targets only language-model projections. Gemma 4 is multimodal; adapting
  the vision/audio towers wastes memory and the feedback path is text-only.
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

# Full-match regex handed to peft: every attention/MLP projection whose path does
# not run through a vision or audio tower.
TARGET_MODULES = (
    r"^(?!.*(?:vision|audio|embed_vision|embed_audio|multi_modal)).*"
    r"\.(?:q_proj|k_proj|v_proj|o_proj|gate_proj|up_proj|down_proj)$"
)


def to_prompt_completion(row: dict) -> dict:
    """{"messages": [sys, user, asst]} -> TRL conversational prompt/completion.

    TRL computes loss on the completion only for this format, which avoids
    depending on {% generation %} markers in the Gemma chat template.
    """
    messages = row["messages"]
    assert messages[-1]["role"] == "assistant", "last turn must be the target"
    return {"prompt": messages[:-1], "completion": messages[-1:]}


def load_model_and_tokenizer(base: str):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

    quant = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )
    kwargs = dict(
        quantization_config=quant,
        dtype=torch.bfloat16,
        attn_implementation="sdpa",
        device_map={"": 0},
    )
    try:
        model = AutoModelForCausalLM.from_pretrained(base, **kwargs)
    except (ValueError, KeyError) as exc:
        # Multimodal checkpoints may only register the image-text-to-text head.
        from transformers import AutoModelForImageTextToText

        print(f"AutoModelForCausalLM rejected the checkpoint ({exc}); using AutoModelForImageTextToText")
        model = AutoModelForImageTextToText.from_pretrained(base, **kwargs)

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
    from peft import LoraConfig, prepare_model_for_kbit_training
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
    model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=True)
    print(f"base loaded in {time.time() - started:.0f}s, {torch.cuda.memory_allocated() / 1024**3:.1f}GiB resident")

    lora = LoraConfig(
        r=args.rank,
        lora_alpha=args.alpha,
        lora_dropout=0.05,
        target_modules=TARGET_MODULES,
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
        warmup_ratio=0.1,
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
        "lora": {"r": args.rank, "alpha": args.alpha, "target_modules": TARGET_MODULES},
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
