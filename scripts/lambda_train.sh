#!/bin/bash
# Lambda Labs one-liner setup + training
# Usage: bash -c "$(curl -s https://raw.githubusercontent.com/monoteco/guiagochat/main/scripts/lambda_train.sh)" -- mistral7b

# Exit on error
set -e

MODEL=${1:-mistral7b}
echo "=== GuiaGo Fine-tuning on Lambda Labs ==="
echo "Model: $MODEL"

# Install dependencies (if needed)
pip install -q torch transformers datasets peft trl pyyaml requests huggingface-hub --upgrade

# Clone repo
cd /tmp
[ -d guiagochat ] && rm -rf guiagochat
git clone https://github.com/monoteco/guiagochat.git
cd guiagochat

# Download dataset (pre-generated train.jsonl + val.jsonl)
# Assumed to be uploaded to /mnt/data or passed via wget/scp
echo "Expecting dataset at ./data/finetune/train.jsonl"
if [ ! -f "data/finetune/train.jsonl" ]; then
    echo "ERROR: dataset not found. Upload data/finetune/*.jsonl first"
    exit 1
fi

# Run training with GPU-optimized config
echo "Starting training..."
python3 finetune/train.py --model $MODEL --config finetune/config_lambda.yaml

# Save adapter
echo "Training complete. Adapter saved to: finetune/adapters/$MODEL/"
ls -lah finetune/adapters/$MODEL/

# (Optional) Export to GGUF if llama.cpp installed
# bash scripts/export_to_ollama.py --model $MODEL

echo "Done. Download the adapter folder to merge locally."