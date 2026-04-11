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
pkill -f "uvicorn app.main:app" 2>/dev/null || true
sleep 1

# Find a free port starting from 8080
PORT=8080
while ss -ltn 2>/dev/null | grep -q ":${PORT} " || lsof -i :${PORT} > /dev/null 2>&1; do
    PORT=$((PORT + 1))
done
echo "[*] Using port $PORT"

# Start FastAPI
cd backend
nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port $PORT > ../logs/api.log 2>&1 &
API_PID=$!
cd ..

sleep 3

# Health check
if curl -sf http://localhost:${PORT}/health > /dev/null; then
    echo "[OK] API running on port $PORT (PID $API_PID)"
    echo "     Open: http://$(hostname -I | awk '{print $1}'):${PORT}/"
else
    echo "[ERROR] API failed to start. Check logs/api.log"
    exit 1
fi

echo "[OK] GuiaGoChat is running. Logs: logs/api.log, logs/ollama.log"
