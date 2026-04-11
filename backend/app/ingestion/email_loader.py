import email
import os
from email import policy
from pathlib import Path
from app.core.vectorstore import get_or_create_collection
from app.core.config import settings


def ingest_emails(collection_name: str = "emails") -> int:
    email_dir = Path(settings.data_dir) / "emails"
    if not email_dir.exists():
        return 0

    collection = get_or_create_collection(collection_name)
    count = 0

    for filepath in email_dir.glob("*.eml"):
        with open(filepath, "rb") as f:
            msg = email.message_from_binary_file(f, policy=policy.default)

        subject = msg.get("subject", "Sin asunto")
        sender = msg.get("from", "Desconocido")
        date = msg.get("date", "")
        body = msg.get_body(preferencelist=("plain",))
        text = body.get_content() if body else ""

        doc = f"De: {sender}\nAsunto: {subject}\nFecha: {date}\n\n{text}"
        doc_id = filepath.stem

        collection.upsert(
            documents=[doc],
            metadatas=[{"source": filepath.name, "sender": sender, "subject": subject}],
            ids=[doc_id],
        )
        count += 1

    return count
