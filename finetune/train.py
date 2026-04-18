"""
train.py — LoRA fine-tuning for Llama 3.1 8B or Mistral 7B (CPU-only).

Downloads base model from HuggingFace (requires HUGGINGFACE_TOKEN in .env for Llama 3.1),
applies LoRA adapters, trains with SFTTrainer, saves adapter to finetune/adapters/{model}/.

Usage:
  python3 finetune/train.py --model llama31   [--config finetune/config.yaml]
  python3 finetune/train.py --model mistral7b [--config finetune/config.yaml]
"""

import argparse
import json
import os
import sys
from pathlib import Path

import yaml


def load_env(env_path: Path):
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                key, _, val = line.partition("=")
                os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model",  required=True, choices=["llama31", "mistral7b"])
    parser.add_argument("--config", default="finetune/config.yaml")
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent.parent
    load_env(project_root / ".env")

    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = project_root / args.config

    with config_path.open() as f:
        cfg = yaml.safe_load(f)

    model_cfg = cfg["models"][args.model]
    train_cfg  = cfg["training"]
    ds_cfg     = cfg["dataset"]

    repo_id     = model_cfg["repo_id"]
    adapter_dir = project_root / model_cfg["adapter_dir"]
    train_file  = project_root / ds_cfg["train_file"]
    val_file    = project_root / ds_cfg["val_file"]

    hf_token = os.environ.get("HUGGINGFACE_TOKEN")
    if not hf_token and "llama" in repo_id.lower():
        print("WARNING: HUGGINGFACE_TOKEN not set. Llama 3.1 requires it. Set it in .env")

    if not train_file.exists():
        print(f"ERROR: Training file not found: {train_file}", file=sys.stderr)
        print("Run finetune/generate_dataset.py first.", file=sys.stderr)
        sys.exit(1)

    print(f"=== GuiaGo Fine-tuning: {args.model} ===")
    print(f"Base model: {repo_id}")
    print(f"Adapter output: {adapter_dir}")
    print(f"Training data: {train_file}")
    print()

    # ---- imports after env setup ----
    import torch
    from datasets import load_dataset
    from peft import LoraConfig, get_peft_model, TaskType
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        TrainingArguments,
    )
    from trl import SFTTrainer, SFTConfig

    adapter_dir.mkdir(parents=True, exist_ok=True)

    # ---- GPU / CPU detection ----
    use_gpu = torch.cuda.is_available()
    device_map = "auto" if use_gpu else "cpu"
    dtype = torch.bfloat16 if use_gpu else torch.float32
    print(f"Device: {'GPU' if use_gpu else 'CPU'} | dtype: {dtype}")

    # ---- Load tokenizer ----
    print("Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(
        repo_id,
        token=hf_token or None,
        trust_remote_code=True,
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # ---- Load base model (float32 for CPU, frozen) ----
    print(f"Loading base model (this downloads ~14-16 GB on first run)...")
    model = AutoModelForCausalLM.from_pretrained(
        repo_id,
        token=hf_token or None,
        torch_dtype=dtype,
        device_map=device_map,
        trust_remote_code=True,
    )
    model.enable_input_require_grads()

    # ---- Apply LoRA ----
    print("Applying LoRA adapter...")
    lora_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=train_cfg["lora_r"],
        lora_alpha=train_cfg["lora_alpha"],
        lora_dropout=float(train_cfg["lora_dropout"]),
        target_modules=train_cfg["target_modules"],
        bias="none",
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    # ---- Dataset ----
    print("Loading dataset...")
    data_files = {"train": str(train_file)}
    if val_file.exists():
        data_files["validation"] = str(val_file)

    raw_dataset = load_dataset("json", data_files=data_files)

    def format_messages(example):
        return {"text": tokenizer.apply_chat_template(
            example["messages"],
            tokenize=False,
            add_generation_prompt=False,
        )}

    try:
        dataset = raw_dataset.map(format_messages)
    except Exception:
        # Fallback: manual format if tokenizer lacks chat_template
        def fallback_format(example):
            parts = []
            for m in example["messages"]:
                parts.append(f"<{m['role']}>\n{m['content']}\n</{m['role']}>")
            return {"text": "\n".join(parts)}
        dataset = raw_dataset.map(fallback_format)

    # ---- Training args ----
    sft_cfg = SFTConfig(
        output_dir=str(adapter_dir),
        num_train_epochs=int(train_cfg["num_epochs"]),
        per_device_train_batch_size=int(train_cfg["batch_size"]),
        gradient_accumulation_steps=int(train_cfg["gradient_accumulation_steps"]),
        learning_rate=float(train_cfg["learning_rate"]),
        warmup_ratio=float(train_cfg["warmup_ratio"]),
        lr_scheduler_type=train_cfg["lr_scheduler"],
        save_steps=int(train_cfg["save_steps"]),
        logging_steps=int(train_cfg["logging_steps"]),
        max_seq_length=int(train_cfg["max_seq_length"]),
        fp16=False,
        bf16=use_gpu,
        use_cpu=not use_gpu,
        gradient_checkpointing=use_gpu,
        dataset_text_field="text",
        report_to="none",
        eval_strategy="steps" if val_file.exists() else "no",
        eval_steps=int(train_cfg["save_steps"]) if val_file.exists() else None,
        save_total_limit=2,
    )

    trainer = SFTTrainer(
        model=model,
        args=sft_cfg,
        train_dataset=dataset["train"],
        eval_dataset=dataset.get("validation"),
        tokenizer=tokenizer,
    )

    print("Starting training...")
    print(f"Estimated time: several hours to days on CPU. Check logs for progress.")
    trainer.train()

    print("Saving LoRA adapter...")
    trainer.model.save_pretrained(str(adapter_dir))
    tokenizer.save_pretrained(str(adapter_dir))

    # Save metadata
    meta = {
        "model": args.model,
        "base_model": repo_id,
        "adapter_dir": str(adapter_dir),
        "train_samples": len(dataset["train"]),
        "epochs": train_cfg["num_epochs"],
        "lora_r": train_cfg["lora_r"],
    }
    (adapter_dir / "guiago_meta.json").write_text(json.dumps(meta, indent=2))

    print(f"\nTraining complete! Adapter saved to: {adapter_dir}")
    print("Next: python3 finetune/export_to_ollama.py --model " + args.model)


if __name__ == "__main__":
    main()