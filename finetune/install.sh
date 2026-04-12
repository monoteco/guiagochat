#!/bin/bash
# Install fine-tuning dependencies on caro (CPU-only).
# Must be run from ~/guiagochat with the venv active.
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "[1/4] Activating venv..."
source "$PROJECT_DIR/venv/bin/activate"

echo "[2/4] Installing Python fine-tuning deps..."
pip install -r "$SCRIPT_DIR/requirements.txt"

echo "[3/4] Building llama.cpp for GGUF conversion..."
cd ~
if [ ! -d "llama.cpp" ]; then
    git clone --depth 1 https://github.com/ggerganov/llama.cpp
fi
cd llama.cpp
cmake -B build -DLLAMA_NATIVE=OFF -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release -j"$(nproc)"
echo "llama.cpp built at ~/llama.cpp/build/bin/"

echo "[4/4] Creating output directories..."
mkdir -p "$PROJECT_DIR/data/finetune"
mkdir -p "$PROJECT_DIR/finetune/adapters/llama31"
mkdir -p "$PROJECT_DIR/finetune/adapters/mistral7b"
mkdir -p "$PROJECT_DIR/finetune/merged/llama31"
mkdir -p "$PROJECT_DIR/finetune/merged/mistral7b"
mkdir -p "$PROJECT_DIR/finetune/gguf"
mkdir -p "$PROJECT_DIR/logs"

echo ""
echo "=== Installation complete ==="
echo "Next steps:"
echo "  1. Set HUGGINGFACE_TOKEN in $PROJECT_DIR/.env  (required for Llama 3.1)"
echo "  2. python3 finetune/generate_dataset.py"
echo "  3. nohup python3 finetune/train.py --model mistral7b > logs/train_mistral7b.log 2>&1 &"
echo "  4. python3 finetune/export_to_ollama.py --model mistral7b"