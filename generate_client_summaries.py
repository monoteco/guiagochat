import chromadb, requests, json, re
from collections import defaultdict

CHROMA_PATH = "./chroma_db"
MODAL_URL   = "https://hernandogerman--guiago-inference-guiagomodel-chat.modal.run"
MAX_CHARS_PER_CLIENT = 6000  # ~1500 tokens de contexto por cliente
TOP_N = 15

# Patrones a excluir (newsletters, internos, bots)
SKIP_PATTERNS = [
    r"laguiago\.com",
    r"noreply", r"no-reply", r"notifications?-",
    r"amazon\.", r"linkedin\.com",
    r"microsoftexchange",
    r"@mailer\.", r"@news\.", r"@email\.",
    r"elparking", r"canva\.com", r"icontactmail",
    r"silbon", r"todoalacuenta",
    r"vmartinez",
]
SKIP_RE = re.compile("|".join(SKIP_PATTERNS), re.IGNORECASE)

def call_modal(system_msg, user_msg):
    payload = {
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user",   "content": user_msg}
        ],
        "max_tokens": 600,
        "temperature": 0.2
    }
    resp = requests.post(MODAL_URL, json=payload, timeout=120)
    resp.raise_for_status()
    return resp.json()["content"].strip()

def extract_email(sender):
    if "<" in sender:
        return sender.split("<")[-1].replace(">","").strip().lower()
    return sender.strip().lower()

# ------ Cargar todos los emails ------
client = chromadb.PersistentClient(path=CHROMA_PATH)
col    = client.get_collection("emails")
total  = col.count()

print(f"Cargando {total} correos...", flush=True)
all_docs  = []
all_metas = []
batch = 500
for offset in range(0, total, batch):
    res = col.get(limit=batch, offset=offset, include=["documents","metadatas"])
    all_docs.extend(res["documents"])
    all_metas.extend(res["metadatas"])

# ------ Agrupar por remitente ------
by_sender = defaultdict(list)
for doc, meta in zip(all_docs, all_metas):
    email = extract_email(meta.get("de",""))
    if not SKIP_RE.search(email):
        by_sender[email].append((meta, doc))

# Ordenar por volumen
ranked = sorted(by_sender.items(), key=lambda x: len(x[1]), reverse=True)[:TOP_N]
print(f"Top {len(ranked)} clientes externos encontrados\n", flush=True)

# ------ Generar resúmenes ------
SYSTEM = (
    "Eres un asistente de análisis CRM de GuiaGo. "
    "Analiza los correos recibidos de un contacto externo y genera un resumen "
    "estructurado en español con: quiénes son, temas principales tratados, "
    "fechas (primera y última comunicación), oportunidades de negocio o colaboración "
    "detectadas, y estado actual de la relación. Sé concreto y útil."
)

output_lines = ["# Resúmenes de Clientes Principales - GuiaGo\n"]

for rank, (email, items) in enumerate(ranked, 1):
    count = len(items)
    # Fechas
    fechas = sorted([m.get("fecha","") for m, _ in items if m.get("fecha")])
    primera = fechas[0]  if fechas else "?"
    ultima  = fechas[-1] if fechas else "?"
    # Construir texto de correos (truncado)
    emails_text = ""
    for meta, doc in sorted(items, key=lambda x: x[0].get("fecha",""))[:30]:
        snippet = f"--- Asunto: {meta.get('asunto','')} | Fecha: {meta.get('fecha','')} ---\n{doc[:500]}\n\n"
        if len(emails_text) + len(snippet) > MAX_CHARS_PER_CLIENT:
            break
        emails_text += snippet

    user_msg = (
        f"Remitente: {email}\n"
        f"Total correos: {count}\n"
        f"Primera comunicacion: {primera}\n"
        f"Ultima comunicacion: {ultima}\n\n"
        f"CORREOS:\n{emails_text}"
    )

    print(f"[{rank}/{len(ranked)}] Procesando {email} ({count} correos)...", flush=True)
    try:
        summary = call_modal(SYSTEM, user_msg)
    except Exception as e:
        summary = f"ERROR: {e}"

    output_lines.append(f"## {rank}. {email}  ({count} correos)")
    output_lines.append(f"**Periodo:** {primera} — {ultima}\n")
    output_lines.append(summary)
    output_lines.append("\n---\n")
    print("   OK", flush=True)

print("\n===MARKDOWN_START===")
print("\n".join(output_lines))
print("===MARKDOWN_END===")
