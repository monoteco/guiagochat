from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.core.llm import get_llm
from app.core.vectorstore import get_or_create_collection

SYSTEM_PROMPT = (
    "Eres un asistente interno de GuiaGo, empresa de tours y actividades. "
    "Responde en espanol usando SOLO la informacion del contexto proporcionado. "
    "Si no tienes informacion suficiente, dilo claramente."
)


def query_rag(message: str, collection_name: str = "memoria") -> dict:
    collection = get_or_create_collection(collection_name)
    results = collection.query(query_texts=[message], n_results=10)

    context_docs = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    sources = [m.get("source", "desconocido") for m in metadatas] if metadatas else []

    context_text = "\n---\n".join(context_docs) if context_docs else "No hay documentos disponibles."

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", "Contexto:\n{context}\n\nPregunta: {question}"),
    ])

    chain = prompt | get_llm() | StrOutputParser()
    answer = chain.invoke({"context": context_text, "question": message})

    return {"answer": answer, "sources": sources}
