"""
export_to_ollama.py — Merge LoRA adapter, convert to GGUF, register in Ollama.

Pipeline:
  1. Load base model + LoRA adapter → merge → save merged HF model
  2. Convert merged HF model → GGUF f16  (llama.cpp convert_hf_to_gguf.py)
  3. Quantize GGUF f16 → Q4_K_M          (llama.cpp llama-quantize)
  4. Write Modelfile + ollama create

Requires:
  - llama.cpp cloned and built at ~/llama.cpp
  - Ollama running on localhost

Usage:
  python3 finetune/export_to_ollama.py --model llama31   [--config finetune/config.yaml]
  python3 finetune/export_to_ollama.py --model mistral7b [--config finetune/config.yaml]
"""

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml


def run(cmd: list, **kwargs):
    print(f"$ {' '.join(str(c) for c in cmd)}")
    result = subprocess.run(cmd, **kwargs)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed (exit {result.returncode})")
    return result


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

    model_cfg   = cfg["models"][args.model]
    repo_id     = model_cfg["repo_id"]
    adapter_dir = project_root / model_cfg["adapter_dir"]
    merged_dir  = project_root / model_cfg["merged_dir"]
    gguf_f16    = project_root / model_cfg["gguf_file"].replace("q4_K_M", "f16")
    gguf_q4     = project_root / model_cfg["gguf_file"]
    ollama_name = model_cfg["ollama_name"]

    hf_token = os.environ.get("HUGGINGFACE_TOKEN")

    # Locate llama.cpp
    llama_cpp_dir = Path.home() / "llama.cpp"
    if not llama_cpp_dir.exists():
        print(f"ERROR: llama.cpp not found at {llama_cpp_dir}", file=sys.stderr)
        print("Run finetune/install.sh first.", file=sys.stderr)
        sys.exit(1)

    convert_script = llama_cpp_dir / "convert_hf_to_gguf.py"
    quantize_bin   = llama_cpp_dir / "build" / "bin" / "llama-quantize"

    gguf_f16.parent.mkdir(parents=True, exist_ok=True)
    merged_dir.mkdir(parents=True, exist_ok=True)

    # ── Step 1: Merge LoRA adapter → HF model ──
    print(f"=== Step 1: Merging LoRA adapter into base model ===")
    if not adapter_dir.exists():
        print(f"ERROR: Adapter not found: {adapter_dir}", file=sys.stderr)
        print("Train the model first with finetune/train.py", file=sys.stderr)
        sys.exit(1)

    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer

    print(f"Loading tokenizer from {adapter_dir} ...")
    tokenizer = AutoTokenizer.from_pretrained(str(adapter_dir), token=hf_token or None)

    print(f"Loading base model {repo_id} ...")
    base_model = AutoModelForCausalLM.from_pretrained(
        repo_id,
        token=hf_token or None,
        torch_dtype=torch.float32,
        device_map="cpu",
    )

    print("Loading LoRA adapter and merging...")
    peft_model = PeftModel.from_pretrained(base_model, str(adapter_dir))
    merged_model = peft_model.merge_and_unload()

    print(f"Saving merged model to {merged_dir} ...")
    merged_model.save_pretrained(str(merged_dir), safe_serialization=True)
    tokenizer.save_pretrained(str(merged_dir))
    print("Merge complete.")

    # ── Step 2: Convert to GGUF f16 ──
    print(f"\n=== Step 2: Converting to GGUF f16 ===")
    venv_python = project_root / "venv" / "bin" / "python3"
    run([
        str(venv_python), str(convert_script),
        str(merged_dir),
        "--outfile", str(gguf_f16),
        "--outtype", "f16",
    ])
    print(f"GGUF f16 saved to {gguf_f16}")

    # ── Step 3: Quantize to Q4_K_M ──
    print(f"\n=== Step 3: Quantizing to Q4_K_M ===")
    run([str(quantize_bin), str(gguf_f16), str(gguf_q4), "Q4_K_M"])
    print(f"GGUF Q4_K_M saved to {gguf_q4}")

    # Clean up f16 (save space)
    gguf_f16.unlink(missing_ok=True)

    # ── Step 4: Register in Ollama ──
    print(f"\n=== Step 4: Registering in Ollama as '{ollama_name}' ===")
    modelfile_content = (
        f"FROM {gguf_q4}\n"
        f"SYSTEM \"{cfg['system_prompt'].strip()}\"\n"
        f"PARAMETER temperature 0.7\n"
        f"PARAMETER top_p 0.9\n"
        f"PARAMETER stop \"<|eot_id|>\"\n"
    )
    modelfile_path = gguf_q4.parent / f"Modelfile_{args.model}"
    modelfile_path.write_text(modelfile_content)

    run(["ollama", "create", ollama_name, "-f", str(modelfile_path)])
    print(f"\n=== Export complete! ===")
    print(f"Model '{ollama_name}' is now available in Ollama.")
    print(f"Test it: ollama run {ollama_name}")


if __name__ == "__main__":
    main()