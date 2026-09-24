"""CPU check that the completion-only-logits trainer matches the stock SFTTrainer.

    cd backend && ~/venvs/train/bin/python -m training.check_completion_logits

Builds a tiny random Llama (no download, no GPU) with the real TRL collator and
LoRA + gradient checkpointing, then asserts that loss and gradients from
train_lora.completion_logits_trainer equal the stock SFTTrainer's on the same
batch, that logits are kept only for the response, and that train + evaluate
run. Takes a few seconds.
"""

from __future__ import annotations

import random
import tempfile

VOCAB = 512


def main() -> int:
    import torch
    from datasets import Dataset
    from peft import LoraConfig
    from tokenizers import Tokenizer, models
    from transformers import LlamaConfig, LlamaForCausalLM, PreTrainedTokenizerFast
    from trl import SFTConfig, SFTTrainer

    from training.train_lora import completion_logits_trainer

    random.seed(0)
    tokenizer = PreTrainedTokenizerFast(
        tokenizer_object=Tokenizer(models.WordLevel({f"t{i}": i for i in range(VOCAB)}, unk_token="t3")),
        pad_token="t0", eos_token="t1", bos_token="t2", unk_token="t3",
    )

    def row() -> dict:
        n_prompt, n_response = random.randint(30, 60), random.randint(4, 9)
        ids = [random.randint(4, VOCAB - 1) for _ in range(n_prompt + n_response)] + [1]
        return {"input_ids": ids, "completion_mask": [0] * n_prompt + [1] * (n_response + 1)}

    data = Dataset.from_list([row() for _ in range(12)])

    def make(trainer_class, **extra):
        torch.manual_seed(0)
        model = LlamaForCausalLM(LlamaConfig(
            vocab_size=VOCAB, hidden_size=32, intermediate_size=64, num_hidden_layers=2,
            num_attention_heads=4, num_key_value_heads=2, pad_token_id=0, eos_token_id=1, bos_token_id=2,
        ))
        config = SFTConfig(
            output_dir=tempfile.mkdtemp(), max_steps=3, per_device_train_batch_size=2, per_device_eval_batch_size=2,
            gradient_accumulation_steps=2, learning_rate=1e-3, completion_only_loss=True, packing=False,
            max_length=128, logging_steps=1, eval_strategy="no", save_strategy="no", report_to="none",
            gradient_checkpointing=True, gradient_checkpointing_kwargs={"use_reentrant": False},
            use_cpu=True, seed=1410, **extra,
        )
        lora = LoraConfig(r=4, lora_alpha=8, target_modules=["q_proj", "v_proj"], task_type="CAUSAL_LM")
        return trainer_class(model=model, args=config, train_dataset=data, eval_dataset=data.select(range(4)),
                             processing_class=tokenizer, peft_config=lora)

    stock = make(SFTTrainer)
    ours = make(completion_logits_trainer(SFTTrainer), prediction_loss_only=True)
    batch = next(iter(stock.get_train_dataloader()))

    def grads(trainer):
        return torch.cat([p.grad.flatten() for p in trainer.model.parameters() if p.grad is not None])

    supervised = (batch["labels"][:, 1:] != -100).sum()
    for num_items in (None, supervised):
        for trainer in (stock, ours):
            trainer.model.train()
            trainer.model.zero_grad()
        stock_loss = stock.compute_loss(stock.model, dict(batch), num_items_in_batch=num_items)
        our_loss = ours.compute_loss(ours.model, dict(batch), num_items_in_batch=num_items)
        stock_loss.backward()
        our_loss.backward()
        assert torch.allclose(stock_loss, our_loss, atol=1e-5), (stock_loss.item(), our_loss.item())
        assert torch.allclose(grads(stock), grads(ours), atol=1e-6), "gradients differ"
        print(f"num_items_in_batch={num_items}: loss {our_loss.item():.6f} matches, gradients match")

    with torch.no_grad():
        _, outputs = ours.compute_loss(ours.model, dict(batch), return_outputs=True)
    first = int((batch["labels"] != -100).any(0).nonzero()[0])
    length = batch["input_ids"].shape[1]
    assert outputs.logits.shape[1] == length - first + 1
    print(f"logits kept for {outputs.logits.shape[1]} of {length} positions")

    result = ours.train()
    metrics = ours.evaluate()
    print(f"OK: train ({result.global_step} steps) and evaluate (eval_loss {metrics['eval_loss']:.4f}) run")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
