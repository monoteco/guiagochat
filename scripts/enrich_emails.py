#!/usr/bin/env python3
"""
enrich_emails.py - Populate resumen_ia and fase_ia in correosGo.db
using the local Ollama LLM (mistral-nemo).

Processes INBOX emails in batches, resumable (skips already processed).
Logs progress to stdout (redirect to logs/enrich.log when launching).

Usage:
  cd ~/guiagochat && source venv/bin/activate
  nohup python3 scripts/enrich_emails.py > logs/enrich.log 2>&1 &
  tail -f logs/enrich.log
"""

import sqlite3
import json
import sys
import logging
from pathlib import Path

import requests

# ── config ──────────────────────────────────────────────────────────────────
DB_PATH        = Path(__file__).resolve().parent.parent / "data" / "correosGo.db"
OLLAMA_URL     = "http://localhost:11434/api/chat"
MODEL          = "mistral-nemo"
BATCH_SIZE     = 5
MAX_BODY_CHARS = 2000
INBOX_BOXES    = ("INBOX", "inbox")
VALID_PHASES   = {"lead", "contactado", "propuesta", "negociacion",
                  "cerrado", "produccion", "finalizado"}
PHASES_STR     = ", ".join(sorted(VALID_PHASES))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)


# ── llm helpers ──────────────────────────────────────────────────────────────

def ask_ollama(prompt: str, max_tokens: int = 200) -> str:
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "options": {"num_predict": max_tokens, "temperature": 0.2},
        "stream": False,
    }
    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=180)
        resp.raise_for_status()
        return resp.json()["message"]["content"].strip()
    except Exception as e:
        log.warning("Ollama error: %s", e)
        return ""


def make_resumen_prompt(asunto: str, cuerpo: str) -> str:
    return (
        "Resume en 1-2 frases en espanol este correo de negocio. "
        "Solo el resumen, sin introduccion:\n\n"
        f"Asunto: {asunto}\n\n{cuerpo[:MAX_BODY_CHARS]}"
    )


def make_fase_prompt(asunto: str, cuerpo: str) -> str:
    return (
        "Clasifica la fase comercial de GuiaGo de este correo. "
        f"Responde SOLO con una de estas palabras: {PHASES_STR}\n\n"
        f"Asunto: {asunto}\n\n{cuerpo[:MAX_BODY_CHARS]}"
    )


def normalize_fase(raw: str) -> str:
    candidate = raw.lower().strip().split()[0] if raw.strip() else ""
    return candidate if candidate in VALID_PHASES else "lead"


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    if not DB_PATH.exists():
        log.error("DB not found: %s", DB_PATH)
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    placeholders = ",".join("?" * len(INBOX_BOXES))
    total = conn.execute(
        f"SELECT COUNT(*) FROM correos WHERE mailbox IN ({placeholders}) "
        "AND cuerpo_txt IS NOT NULL AND cuerpo_txt != ''",
        INBOX_BOXES,
    ).fetchone()[0]

    pending = conn.execute(
        f"SELECT COUNT(*) FROM correos WHERE mailbox IN ({placeholders}) "
        "AND cuerpo_txt IS NOT NULL AND cuerpo_txt != '' "
        "AND (resumen_ia IS NULL OR resumen_ia = '')",
        INBOX_BOXES,
    ).fetchone()[0]

    log.info("INBOX emails total=%d  pending=%d", total, pending)

    processed = 0
    errors = 0

    while True:
        rows = conn.execute(
            f"SELECT id, asunto, cuerpo_txt FROM correos "
            f"WHERE mailbox IN ({placeholders}) "
            "AND cuerpo_txt IS NOT NULL AND cuerpo_txt != '' "
            "AND (resumen_ia IS NULL OR resumen_ia = '') "
            f"LIMIT {BATCH_SIZE}",
            INBOX_BOXES,
        ).fetchall()

        if not rows:
            break

        for row in rows:
            rid    = row["id"]
            asunto = row["asunto"] or ""
            cuerpo = row["cuerpo_txt"]

            log.info("[%d/%d] id=%d  asunto=%.60s", processed + 1, pending, rid, asunto)

            resumen = ask_ollama(make_resumen_prompt(asunto, cuerpo), max_tokens=150)
            if not resumen:
                resumen = "(sin resumen)"
                errors += 1

            fase_raw = ask_ollama(make_fase_prompt(asunto, cuerpo), max_tokens=10)
            fase     = normalize_fase(fase_raw)

            conn.execute(
                "UPDATE correos SET resumen_ia=?, fase_ia=? WHERE id=?",
                (resumen, fase, rid),
            )
            conn.commit()
            processed += 1

        log.info("checkpoint: processed=%d errors=%d", processed, errors)

    log.info("DONE. processed=%d errors=%d", processed, errors)
    conn.close()


if __name__ == "__main__":
    main()
