#!/bin/bash
# run_pipeline.sh — Full fine-tuning pipeline: generate → train → export
# Usage: bash finetune/run_pipeline.sh [llama31|mistral7b]

set -e

MODEL="${1:-mistral7b}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

LOG_DIR="$PROJECT_DIR/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/finetune_${MODEL}.log"

cd "$PROJECT_DIR"
source venv/bin/activate

echo "=== GuiaGo Fine-tuning Pipeline: $MODEL ===" | tee "$LOG_FILE"
echo "Log: $LOG_FILE"
echo ""

echo "[1/3] Generating dataset..." | tee -a "$LOG_FILE"
python3 finetune/generate_dataset.py 2>&1 | tee -a "$LOG_FILE"

echo "" | tee -a "$LOG_FILE"
echo "[2/3] Training with LoRA (this will take hours/days)..." | tee -a "$LOG_FILE"
python3 finetune/train.py --model "$MODEL" 2>&1 | tee -a "$LOG_FILE"

echo "" | tee -a "$LOG_FILE"
echo "[3/3] Exporting to Ollama..." | tee -a "$LOG_FILE"
python3 finetune/export_to_ollama.py --model "$MODEL" 2>&1 | tee -a "$LOG_FILE"

echo "" | tee -a "$LOG_FILE"
echo "=== Pipeline complete for $MODEL ===" | tee -a "$LOG_FILE"