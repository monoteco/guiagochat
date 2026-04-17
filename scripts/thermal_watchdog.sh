#!/bin/bash
# Thermal watchdog: pausa/reanuda train.py segun temperatura del CPU
# Limites: pausa >85C, reanuda <70C
TEMP_PAUSE=85
TEMP_RESUME=70
LOG=~/guiagochat/logs/thermal.log
PAUSED=0

while true; do
    MAX_TEMP=$(cat /sys/class/thermal/thermal_zone*/temp 2>/dev/null | sort -n | tail -1)
    MAX_TEMP=$((MAX_TEMP / 1000))
    PID=$(pgrep -f "train.py" | head -1)
    TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")

    if [ -z "$PID" ]; then
        echo "$TIMESTAMP  [WATCHDOG] train.py no encontrado, esperando..." >> "$LOG"
        sleep 30
        continue
    fi

    if [ "$PAUSED" -eq 0 ] && [ "$MAX_TEMP" -ge "$TEMP_PAUSE" ]; then
        echo "$TIMESTAMP  [WATCHDOG] PAUSA - CPU ${MAX_TEMP}C >= ${TEMP_PAUSE}C  PID=$PID" >> "$LOG"
        kill -STOP "$PID"
        PAUSED=1
    elif [ "$PAUSED" -eq 1 ] && [ "$MAX_TEMP" -le "$TEMP_RESUME" ]; then
        echo "$TIMESTAMP  [WATCHDOG] REANUDA - CPU ${MAX_TEMP}C <= ${TEMP_RESUME}C  PID=$PID" >> "$LOG"
        kill -CONT "$PID"
        PAUSED=0
    else
        echo "$TIMESTAMP  [WATCHDOG] OK - CPU ${MAX_TEMP}C  PID=$PID  paused=$PAUSED" >> "$LOG"
    fi

    sleep 30
done