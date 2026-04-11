from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.core.llm import get_llm
from app.core.vectorstore import get_or_create_collection

VALID_PHASES = [
    "lead", "contactado", "propuesta", "negociacion",
    "cerrado", "produccion", "finalizado",
]

VALID_BUSINESS_TYPES = [
    "tour_privado", "tour_grupal", "corporativo", "evento",
    "transfer", "excursion", "paquete_hotel", "otro",
]


def _retrieve_context(query: str, collection_name: str = "emails", n: int = 8) -> tuple[str, list[str]]:
    collection = get_or_create_collection(collection_name)
    results = collection.query(query_texts=[query], n_results=n)
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    sources = [m.get("source", "?") for m in metas] if metas else []
    context = "\n---\n".join(docs) if docs else "Sin contexto disponible."
    return context, sources


def simulate_response(client_email: str, client_name: str = "") -> dict:
    context, sources = _retrieve_context(client_email, n=8)

    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "Eres Carolina, responsable comercial de GuiaGo (empresa de tours y actividades en Espana). "
         "Analiza los correos de contexto para aprender el TONO y ESTILO de Carolina al responder. "
         "Luego redacta una respuesta al correo del cliente imitando ese estilo: "
         "profesional pero cercana, en espanol, con saludo y despedida. "
         "Firma como 'Carolina - GuiaGo'. "
         "Si no hay contexto suficiente, escribe una respuesta generica profesional."),
        ("human",
         "CORREOS DE REFERENCIA DE CAROLINA:\n{context}\n\n"
         "---\n"
         "CORREO DEL CLIENTE{client_label}:\n{email}\n\n"
         "Redacta la respuesta de Carolina:"),
    ])

    client_label = f" ({client_name})" if client_name else ""
    chain = prompt | get_llm() | StrOutputParser()
    answer = chain.invoke({
        "context": context,
        "email": client_email,
        "client_label": client_label,
    })

    return {"response": answer, "sources": sources}


def classify_business(text: str) -> dict:
    context, sources = _retrieve_context(text, n=5)

    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "Eres un clasificador de tipos de negocio para GuiaGo (tours y actividades). "
         "Tipos validos: {types}. "
         "Analiza el texto y los correos de referencia. "
         "Responde en formato:\n"
         "TIPO: <tipo>\n"
         "CONFIANZA: alta|media|baja\n"
         "MOTIVO: <explicacion breve>"),
        ("human",
         "Correos de referencia:\n{context}\n\n"
         "Texto a clasificar:\n{text}\n\n"
         "Clasifica el tipo de negocio:"),
    ])

    chain = prompt | get_llm() | StrOutputParser()
    raw = chain.invoke({
        "context": context,
        "text": text,
        "types": ", ".join(VALID_BUSINESS_TYPES),
    })

    parsed = _parse_classification(raw)
    return {"raw": raw, "parsed": parsed, "sources": sources}


def classify_phase(text: str) -> dict:
    context, sources = _retrieve_context(text, n=5)

    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "Eres un analista de pipeline de ventas de GuiaGo. "
         "Fases del funnel: {phases}. "
         "Analiza el texto del correo/hilo y determina en que fase se encuentra el deal. "
         "Responde en formato:\n"
         "FASE: <fase>\n"
         "CONFIANZA: alta|media|baja\n"
         "MOTIVO: <explicacion breve>\n"
         "SIGUIENTE: <que deberia hacer GuiaGo ahora>"),
        ("human",
         "Correos de referencia:\n{context}\n\n"
         "Texto/hilo a analizar:\n{text}\n\n"
         "Determina la fase:"),
    ])

    chain = prompt | get_llm() | StrOutputParser()
    raw = chain.invoke({
        "context": context,
        "text": text,
        "phases": " -> ".join(VALID_PHASES),
    })

    parsed = _parse_classification(raw)
    return {"raw": raw, "parsed": parsed, "sources": sources}


def _parse_classification(raw: str) -> dict:
    result = {}
    for line in raw.strip().split("\n"):
        line = line.strip()
        if ":" in line:
            key, _, val = line.partition(":")
            key = key.strip().lower()
            val = val.strip()
            if key in ("tipo", "fase", "confianza", "motivo", "siguiente"):
                result[key] = val
    return result
