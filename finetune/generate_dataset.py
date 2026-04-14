"""
generate_dataset.py — Build fine-tuning JSONL pairs from correosGo.db.

Three pair types:
  1. resumen  — email body → resumen_ia  (summary pairs)
  2. fase     — email body → fase_ia     (phase classification)
  3. respuesta — INBOX email → matched Sent reply

Output: data/finetune/train.jsonl  +  data/finetune/val.jsonl
Format: {"messages": [{"role":"system",...},{"role":"user",...},{"role":"assistant",...}]}

Usage:
  python3 finetune/generate_dataset.py [--config finetune/config.yaml]
"""

import argparse
import json
import re
import sqlite3
import sys
from pathlib import Path
from random import Random

import yaml


# ── helpers ──────────────────────────────────────────────────────────────────

def normalize_subject(subject: str) -> str:
    """Strip Re:/Fwd: prefixes and whitespace for thread matching."""
    s = re.sub(r"^\s*(Re|Fwd|Fw|RE|FWD|FW)\s*:\s*", "", subject or "", flags=re.IGNORECASE)
    return s.strip().lower()


def truncate(text: str, max_chars: int) -> str:
    if text and len(text) > max_chars:
        return text[:max_chars] + "…"
    return text or ""


def build_message(system: str, user: str, assistant: str) -> dict:
    return {"messages": [
        {"role": "system",    "content": system},
        {"role": "user",      "content": user},
        {"role": "assistant", "content": assistant},
    ]}


# ── pair generators ───────────────────────────────────────────────────────────

def generate_summary_pairs(conn, system_prompt: str, min_len: int, max_len: int) -> list:
    rows = conn.execute(
        "SELECT asunto, cuerpo_txt, resumen_ia FROM correos "
        "WHERE resumen_ia IS NOT NULL AND resumen_ia != '' "
        "  AND cuerpo_txt IS NOT NULL AND cuerpo_txt != ''",
    ).fetchall()
    pairs = []
    for asunto, cuerpo_txt, resumen_ia in rows:
        body = truncate(cuerpo_txt, max_len)
        if len(body) < min_len:
            continue
        user_msg = f"Asunto: {asunto or '(sin asunto)'}\n\n{body}"
        pairs.append(build_message(
            system_prompt,
            f"Resume el siguiente correo en español de forma concisa:\n\n{user_msg}",
            resumen_ia.strip(),
        ))
    return pairs


def generate_phase_pairs(conn, system_prompt: str, min_len: int, max_len: int) -> list:
    rows = conn.execute(
        "SELECT asunto, cuerpo_txt, fase_ia FROM correos "
        "WHERE fase_ia IS NOT NULL AND fase_ia != '' "
        "  AND cuerpo_txt IS NOT NULL AND cuerpo_txt != ''",
    ).fetchall()
    pairs = []
    for asunto, cuerpo_txt, fase_ia in rows:
        body = truncate(cuerpo_txt, max_len)
        if len(body) < min_len:
            continue
        user_msg = f"Asunto: {asunto or '(sin asunto)'}\n\n{body}"
        pairs.append(build_message(
            system_prompt,
            f"Clasifica la fase del embudo de ventas de GuiaGo para este correo. "
            f"Responde solo con la fase:\n\n{user_msg}",
            fase_ia.strip(),
        ))
    return pairs


def generate_reply_pairs(conn, system_prompt: str, min_len: int, max_len: int) -> list:
    inbox = conn.execute(
        "SELECT id, asunto, de, cuerpo_txt, fecha FROM correos "
        "WHERE mailbox IN ('INBOX', 'Inbox', 'inbox') "
        "  AND cuerpo_txt IS NOT NULL AND cuerpo_txt != ''",
    ).fetchall()
    sent_rows = conn.execute(
        "SELECT asunto, cuerpo_txt FROM correos "
        "WHERE mailbox IN ('Sent', 'Enviados', 'Sent Items', '[Gmail]/Sent Mail') "
        "  AND cuerpo_txt IS NOT NULL AND cuerpo_txt != ''",
    ).fetchall()

    sent_by_subject: dict[str, list[str]] = {}
    for s_asunto, s_cuerpo_txt in sent_rows:
        key = normalize_subject(s_asunto)
        if key:
            sent_by_subject.setdefault(key, []).append(s_cuerpo_txt)

    pairs = []
    for _, asunto, de, cuerpo_txt, fecha in inbox:
        key = normalize_subject(asunto)
        if not key or key not in sent_by_subject:
            continue
        body = truncate(cuerpo_txt, max_len)
        if len(body) < min_len:
            continue
        # Use first matching sent reply
        reply = truncate(sent_by_subject[key][0], max_len)
        if len(reply) < min_len:
            continue
        user_msg = (
            f"Correo recibido de: {de or 'desconocido'}\n"
            f"Asunto: {asunto or '(sin asunto)'}\n"
            f"Fecha: {fecha or ''}\n\n"
            f"{body}"
        )
        pairs.append(build_message(
            system_prompt,
            f"Eres Carolina de GuiaGo. Redacta una respuesta profesional al siguiente correo recibido:\n\n{user_msg}",
            reply.strip(),
        ))
    return pairs


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="finetune/config.yaml")
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = Path(__file__).resolve().parent.parent / args.config

    with config_path.open() as f:
        cfg = yaml.safe_load(f)

    ds_cfg = cfg["dataset"]
    db_path    = Path(__file__).resolve().parent.parent / ds_cfg["db_path"]
    output_dir = Path(__file__).resolve().parent.parent / ds_cfg["output_dir"]
    train_file = Path(__file__).resolve().parent.parent / ds_cfg["train_file"]
    val_file   = Path(__file__).resolve().parent.parent / ds_cfg["val_file"]
    val_split  = float(ds_cfg.get("val_split", 0.1))
    min_len    = int(ds_cfg.get("min_body_length", 50))
    max_len    = int(ds_cfg.get("max_body_length", 3000))
    system_prompt = cfg["system_prompt"].strip()

    if not db_path.exists():
        print(f"ERROR: Database not found: {db_path}", file=sys.stderr)
        sys.exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Connecting to {db_path}...")
    conn = sqlite3.connect(db_path)

    print("Generating summary pairs...")
    summary_pairs = generate_summary_pairs(conn, system_prompt, min_len, max_len)
    print(f"  Summary pairs: {len(summary_pairs)}")

    print("Generating phase classification pairs...")
    phase_pairs = generate_phase_pairs(conn, system_prompt, min_len, max_len)
    print(f"  Phase pairs: {len(phase_pairs)}")

    print("Generating reply pairs...")
    reply_pairs = generate_reply_pairs(conn, system_prompt, min_len, max_len)
    print(f"  Reply pairs: {len(reply_pairs)}")

    conn.close()

    all_pairs = summary_pairs + phase_pairs + reply_pairs
    Random(42).shuffle(all_pairs)

    total = len(all_pairs)
    val_count = max(1, int(total * val_split))
    train_count = total - val_count

    print(f"Total pairs: {total}")
    print(f"Train split: {train_count} → {train_file}")
    print(f"Val split:   {val_count} → {val_file}")

    def write_jsonl(path: Path, records: list):
        with path.open("w", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

    write_jsonl(train_file, all_pairs[:train_count])
    write_jsonl(val_file,   all_pairs[train_count:])

    print(f"Dataset saved: train={train_count}, val={val_count}")


if __name__ == "__main__":
    main()