import uuid
from app.core.vectorstore import get_or_create_collection

VALID_PHASES = ["lead", "contactado", "propuesta", "negociacion", "cerrado", "produccion", "finalizado"]
CRM_COLLECTION = "crm_deals"


def _deal_to_doc(deal: dict) -> str:
    return (
        f"Cliente: {deal['client_name']}\n"
        f"Email: {deal['email']}\n"
        f"Fase: {deal['phase']}\n"
        f"Notas: {deal['notes']}"
    )


def create_deal(client_name: str, email: str = "", phase: str = "lead", notes: str = "") -> dict:
    if phase not in VALID_PHASES:
        raise ValueError(f"Fase invalida. Opciones: {VALID_PHASES}")
    deal_id = str(uuid.uuid4())[:8]
    deal = {"id": deal_id, "client_name": client_name, "email": email, "phase": phase, "notes": notes}
    collection = get_or_create_collection(CRM_COLLECTION)
    collection.add(
        documents=[_deal_to_doc(deal)],
        metadatas=[deal],
        ids=[deal_id],
    )
    return deal


def update_phase(deal_id: str, new_phase: str) -> dict:
    if new_phase not in VALID_PHASES:
        raise ValueError(f"Fase invalida. Opciones: {VALID_PHASES}")
    collection = get_or_create_collection(CRM_COLLECTION)
    result = collection.get(ids=[deal_id])
    if not result["ids"]:
        raise ValueError(f"Deal {deal_id} no encontrado")
    meta = result["metadatas"][0]
    meta["phase"] = new_phase
    doc = _deal_to_doc(meta)
    collection.update(ids=[deal_id], documents=[doc], metadatas=[meta])
    return meta


def list_deals(phase: str | None = None) -> list[dict]:
    collection = get_or_create_collection(CRM_COLLECTION)
    if phase:
        results = collection.get(where={"phase": phase})
    else:
        results = collection.get()
    return results.get("metadatas", [])


def search_deals(query: str) -> list[dict]:
    collection = get_or_create_collection(CRM_COLLECTION)
    results = collection.query(query_texts=[query], n_results=10)
    return results.get("metadatas", [[]])[0]
