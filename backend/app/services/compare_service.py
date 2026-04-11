import time
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.core.llm import get_llm
from app.core.vectorstore import get_or_create_collection
from app.core.config import settings
import requests

SYSTEM_PROMPT = (
    "Eres un asistente interno de GuiaGo, empresa de tours y actividades. "
    "Responde en espanol usando SOLO la informacion del contexto proporcionado. "
    "Si no tienes informacion suficiente, dilo claramente."
)


def list_available_models() -> list[str]:
    try:
        r = requests.get(f"{settings.ollama_base_url}/api/tags", timeout=5)
        r.raise_for_status()
        return [m["name"] for m in r.json().get("models", [])]
    except Exception:
        return []


def compare_models(message: str, collection_name: str = "emails", models: list[str] | None = None) -> dict:
    if not models:
        models = list_available_models()
    if not models:
        models = [settings.ollama_model]

    collection = get_or_create_collection(collection_name)
    results_q = collection.query(query_texts=[message], n_results=5)
    context_docs = results_q.get("documents", [[]])[0]
    metadatas = results_q.get("metadatas", [[]])[0]
    sources = [m.get("source", "?") for m in metadatas] if metadatas else []
    context_text = "\n---\n".join(context_docs) if context_docs else "Sin contexto."

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", "Contexto:\n{context}\n\nPregunta: {question}"),
    ])

    results = []
    for model_name in models:
        t0 = time.time()
        try:
            chain = prompt | get_llm(model_name) | StrOutputParser()
            answer = chain.invoke({"context": context_text, "question": message})
        except Exception as e:
            answer = f"Error: {e}"
        elapsed = round(time.time() - t0, 1)
        results.append({"model": model_name, "answer": answer, "elapsed": elapsed})

    return {"results": results, "sources": sources}
