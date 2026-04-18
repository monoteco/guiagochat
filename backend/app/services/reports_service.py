from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.core.llm import get_llm
from app.core.vectorstore import get_or_create_collection

# Queries usadas para recuperar contexto relevante de ChromaDB por tipo de informe
_REPORT_QUERIES = {
    "procedimientos": [
        "proceso de venta pasos flujo trabajo procedimiento",
        "como se gestiona presupuesto contrato cliente",
        "seguimiento post-venta incidencia reclamacion",
    ],
    "negocios": [
        "servicios tours actividades productos GuiaGo",
        "tarifas precios temporada oferta",
        "proveedores colaboradores alianzas",
    ],
    "clientes": [
        "perfil cliente tipo negocio sector empresa",
        "frecuencia compra volumen facturacion cliente habitual",
        "quejas satisfaccion feedback cliente",
    ],
    "estrategico": [
        "oportunidad mercado crecimiento expansion",
        "competencia diferenciacion ventaja",
        "objetivo anual meta largo plazo",
    ],
    "tactico": [
        "accion campana correo seguimiento proximas semanas",
        "cliente pendiente propuesta presupuesto enviar",
        "tarea inmediata reunion llamada",
    ],
    "comunicacion": [
        "tono comunicacion formal informal respuesta correo",
        "tiempo respuesta frecuencia contacto cliente",
        "patron comunicacion quien escribe mas",
    ],
    "comercial": [
        "ventas cerradas deals ganados perdidos",
        "embudo comercial fases lead oportunidad",
        "facturacion ingresos temporada",
    ],
}

_REPORT_PROMPTS = {
    "procedimientos": (
        "Eres un consultor de organizacion empresarial. "
        "Basandote EXCLUSIVAMENTE en los correos y datos de GuiaGo del contexto, "
        "redacta un MANUAL DE PROCEDIMIENTOS estructurado con: "
        "1) Proceso de captacion de clientes, "
        "2) Proceso de presupuestacion y contratacion, "
        "3) Proceso de ejecucion del servicio, "
        "4) Proceso de seguimiento post-venta. "
        "Usa el formato: titulo, descripcion, pasos numerados, responsable. "
        "Si no hay informacion suficiente para alguna seccion, indicalo."
    ),
    "negocios": (
        "Eres un consultor de estrategia empresarial. "
        "Basandote EXCLUSIVAMENTE en el contexto de GuiaGo, "
        "redacta un MANUAL DE NEGOCIOS con: "
        "1) Descripcion de la empresa y propuesta de valor, "
        "2) Catalogo de servicios y productos, "
        "3) Modelo de ingresos y tarifas, "
        "4) Canales de venta y distribucion, "
        "5) Socios y proveedores clave. "
        "Sé concreto con datos reales del contexto."
    ),
    "clientes": (
        "Eres un analista de negocio. "
        "Basandote EXCLUSIVAMENTE en los correos y datos del contexto, "
        "genera un ESTUDIO DE CLIENTES con: "
        "1) Segmentos de clientes identificados, "
        "2) Clientes mas activos y su perfil, "
        "3) Patrones de compra y frecuencia, "
        "4) Necesidades y puntos de dolor detectados, "
        "5) Oportunidades de upselling/fidelizacion. "
        "Incluye ejemplos concretos del contexto."
    ),
    "estrategico": (
        "Eres un director de estrategia. "
        "Basandote EXCLUSIVAMENTE en el contexto de GuiaGo, "
        "elabora un PLAN ESTRATEGICO con: "
        "1) Analisis de situacion actual (DAFO resumido), "
        "2) Objetivos estrategicos a 12 meses, "
        "3) Mercados y segmentos a desarrollar, "
        "4) Ventajas competitivas a potenciar, "
        "5) Riesgos y mitigaciones. "
        "Basa cada punto en evidencias del contexto."
    ),
    "tactico": (
        "Eres un director comercial. "
        "Basandote EXCLUSIVAMENTE en el contexto de GuiaGo, "
        "genera un PLAN TACTICO para los proximos 90 dias con: "
        "1) Acciones comerciales prioritarias, "
        "2) Clientes a contactar urgentemente y motivo, "
        "3) Propuestas pendientes de cierre, "
        "4) Campanas de comunicacion recomendadas, "
        "5) KPIs de seguimiento. "
        "Ordena por prioridad e impacto."
    ),
    "comunicacion": (
        "Eres un analista de comunicacion empresarial. "
        "Basandote EXCLUSIVAMENTE en los correos del contexto, "
        "genera un ANALISIS DE COMUNICACION con: "
        "1) Patrones de comunicacion por canal, "
        "2) Tono y estilo predominante, "
        "3) Tiempo medio de respuesta estimado, "
        "4) Temas mas frecuentes en la comunicacion, "
        "5) Recomendaciones para mejorar la comunicacion con clientes. "
        "Usa ejemplos reales del contexto."
    ),
    "comercial": (
        "Eres un analista comercial. "
        "Basandote EXCLUSIVAMENTE en los datos del contexto de GuiaGo, "
        "genera un INFORME COMERCIAL con: "
        "1) Resumen de actividad comercial reciente, "
        "2) Estado del pipeline de ventas, "
        "3) Clientes activos vs inactivos, "
        "4) Analisis por temporada o periodo, "
        "5) Recomendaciones comerciales inmediatas. "
        "Incluye cifras y nombres concretos del contexto."
    ),
}


def _fetch_context(report_type: str, n_results: int = 8) -> tuple[str, list[str]]:
    """Recupera contexto de ChromaDB para el tipo de informe."""
    collection = get_or_create_collection("emails")
    queries = _REPORT_QUERIES[report_type]

    all_docs: list[str] = []
    all_sources: list[str] = []

    for q in queries:
        results = collection.query(query_texts=[q], n_results=n_results)
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        for doc, meta in zip(docs, metas):
            if doc not in all_docs:
                all_docs.append(doc)
                all_sources.append(meta.get("source", "correo"))

    context = "\n---\n".join(all_docs) if all_docs else "No hay datos disponibles."
    return context, list(dict.fromkeys(all_sources))


def generate_report(report_type: str) -> dict:
    """Genera un informe del tipo especificado usando RAG sobre los emails."""
    if report_type not in _REPORT_PROMPTS:
        raise ValueError(f"Tipo de informe desconocido: {report_type}")

    context, sources = _fetch_context(report_type)
    system_prompt = _REPORT_PROMPTS[report_type]

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "Datos disponibles:\n{context}\n\nGenera el informe completo."),
    ])

    chain = prompt | get_llm() | StrOutputParser()
    content = chain.invoke({"context": context})

    return {"report_type": report_type, "content": content, "sources": sources}
