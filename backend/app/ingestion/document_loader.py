from pathlib import Path
from app.core.vectorstore import get_or_create_collection
from app.core.config import settings


def ingest_documents(collection_name: str = "general") -> int:
    doc_dir = Path(settings.data_dir) / "documents"
    if not doc_dir.exists():
        return 0

    collection = get_or_create_collection(collection_name)
    count = 0

    for filepath in doc_dir.glob("*.txt"):
        text = filepath.read_text(encoding="utf-8")
        chunks = _split_text(text, chunk_size=1000, overlap=200)

        for i, chunk in enumerate(chunks):
            doc_id = f"{filepath.stem}_{i}"
            collection.upsert(
                documents=[chunk],
                metadatas=[{"source": filepath.name, "chunk": i}],
                ids=[doc_id],
            )
            count += 1

    return count


def _split_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
    return chunks
