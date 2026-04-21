#!/bin/bash
while ! grep -q DONE ~/guiagochat/logs/build_memoria.log 2>/dev/null; do sleep 30; done
curl -s -X POST "https://api.telegram.org/bot8598707490:AAHBvc_hkN3MzkT8Oyp8F2t8tGOppTKd2Co/sendMessage" --data-urlencode "chat_id=1788924354" --data-urlencode "text=GuiaGo: build_memoria.py terminado. Coleccion memoria lista en ChromaDB."
