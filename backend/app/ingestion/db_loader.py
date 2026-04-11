import sqlite3
from pathlib import Path
from app.core.vectorstore import get_or_create_collection
from app.core.config import settings


USEFUL_MAILBOXES = (
    "INBOX", "inbox",
    "Elementos enviados", "elementos enviados",
    "INBOX/Sent", "enviados_auto",
)

DB_FILENAME = "correosGo.db"


def ingest_db(collection_name: str = "db_sync") -> int:
    db_path = Path(settings.data_dir) / DB_FILENAME
    if not db_path.exists():
        raise FileNotFoundError(f"No se encuentra {db_path}")

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    collection = get_or_create_collection(collection_name)
    count = 0

    cur.execute(
        "SELECT id, mailbox, de, para, cc, asunto, fecha, cuerpo_txt, "
        "account, resumen_ia, fase_ia "
        "FROM correos "
        "WHERE cuerpo_txt IS NOT NULL AND LENGTH(cuerpo_txt) > 10"
    )

    batch_docs = []
    batch_metas = []
    batch_ids = []
    BATCH_SIZE = 100

    for row in cur:
        mailbox = row["mailbox"] or ""
        if not any(mailbox.lower().startswith(m.lower()) for m in USEFUL_MAILBOXES):
            continue

        account = row["account"] or ""
        de = row["de"] or ""
        para = row["para"] or ""
        asunto = row["asunto"] or ""
        fecha = row["fecha"] or ""
        cuerpo = row["cuerpo_txt"] or ""
        resumen = row["resumen_ia"] or ""
        fase = row["fase_ia"] or ""

        # Truncar cuerpo a 3000 chars para chunks manejables
        cuerpo_truncado = cuerpo[:3000]

        doc = (
            f"Cuenta: {account}\n"
            f"Carpeta: {mailbox}\n"
            f"De: {de}\n"
            f"Para: {para}\n"
            f"Asunto: {asunto}\n"
            f"Fecha: {fecha}\n"
        )
        if resumen:
            doc += f"Resumen IA: {resumen}\n"
        if fase:
            doc += f"Fase IA: {fase}\n"
        doc += f"\n{cuerpo_truncado}"

        meta = {
            "source": f"correosGo.db#{row['id']}",
            "account": account,
            "mailbox": mailbox,
            "de": de[:200],
            "para": para[:200],
            "asunto": asunto[:200],
            "fecha": fecha,
        }

        batch_docs.append(doc)
        batch_metas.append(meta)
        batch_ids.append(f"correo_{row['id']}")
        count += 1

        if len(batch_docs) >= BATCH_SIZE:
            collection.upsert(
                documents=batch_docs,
                metadatas=batch_metas,
                ids=batch_ids,
            )
            batch_docs, batch_metas, batch_ids = [], [], []

    if batch_docs:
        collection.upsert(
            documents=batch_docs,
            metadatas=batch_metas,
            ids=batch_ids,
        )

    conn.close()
    return count
