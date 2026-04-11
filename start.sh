#!/bin/bash
# GuiaGoChat startup script — caro miniPC
# Usage: bash ~/guiagochat/start.sh

set -e
cd "$(dirname "$0")"

# Ensure Ollama is running
if ! pgrep -x ollama > /dev/null; then
    echo "[+] Starting Ollama..."
    nohup ollama serve > logs/ollama.log 2>&1 &
    sleep 3
fi

echo "[*] Ollama status: $(ollama list 2>/dev/null | head -2)"

# Activate venv
source venv/bin/activate

# Kill any existing guiagochat uvicorn
pkill -f "uvicorn app.main:app.*8080" 2>/dev/null || true
sleep 1

# Start FastAPI
cd backend
nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8080 > ../logs/api.log 2>&1 &
API_PID=$!
cd ..

sleep 3

# Health check
if curl -sf http://localhost:8080/health > /dev/null; then
    echo "[OK] API running on port 8080 (PID $API_PID)"
else
    echo "[ERROR] API failed to start. Check logs/api.log"
    exit 1
fi

echo "[OK] GuiaGoChat is running. Logs: logs/api.log, logs/ollama.log"
