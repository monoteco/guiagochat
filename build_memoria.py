"""
build_memoria.py - Construye la coleccion 'memoria' en ChromaDB
a partir de todos los emails. Genera fichas de:
  - Personas internas (laguiago.com)
  - Contactos externos principales
  - Resumen global del negocio
"""
import chromadb, requests, re, uuid
from collections import defaultdict

CHROMA_PATH = "./chroma_db"
MODAL_URL   = "https://hernandogerman--guiago-inference-guiagomodel-chat.modal.run"
COLLECTION  = "memoria"

INTERNAL_DOMAIN = "laguiago.com"

SKIP_PATTERNS = [
    r"noreply", r"no-reply", r"notifications?-",
    r"amazon\.", r"linkedin\.com",
    r"microsoftexchange",
    r"@mailer\.", r"@news\.", r"@email\.",
    r"facebookmail\.com",
    r"elparking", r"canva\.com", r"icontactmail",
    r"silbon", r"todoalacuenta",
    r"vmartinez",
]
SKIP_RE = re.compile("|".join(SKIP_PATTERNS), re.IGNORECASE)

def call_modal(system_msg, user_msg, max_tokens=700):
    payload = {
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user",   "content": user_msg}
        ],
        "max_tokens": max_tokens,
        "temperature": 0.2
    }
    resp = requests.post(MODAL_URL, json=payload, timeout=120)
    resp.raise_for_status()
    return resp.json()["content"].strip()

def extract_email(sender):
    if "<" in sender:
        return sender.split("<")[-1].replace(">","").strip().lower()
    return sender.strip().lower()

def build_context(items, max_chars=8000):
    text = ""
    for meta, doc in sorted(items, key=lambda x: x[0].get("fecha",""))[:40]:
        snippet = f"[{meta.get('fecha','')}] Asunto: {meta.get('asunto','')}\n{doc[:400]}\n\n"
        if len(text) + len(snippet) > max_chars:
            break
        text += snippet
    return text

# ---- Cargar emails ----
client = chromadb.PersistentClient(path=CHROMA_PATH)
col    = client.get_collection("emails")
total  = col.count()
print(f"Cargando {total} correos...", flush=True)

all_docs, all_metas = [], []
for offset in range(0, total, 500):
    res = col.get(limit=500, offset=offset, include=["documents","metadatas"])
    all_docs.extend(res["documents"])
    all_metas.extend(res["metadatas"])

# ---- Agrupar por remitente ----
by_sender  = defaultdict(list)
by_para    = defaultdict(list)   # emails recibidos por personas internas
for doc, meta in zip(all_docs, all_metas):
    sender = extract_email(meta.get("de",""))
    para   = extract_email(meta.get("para",""))
    by_sender[sender].append((meta, doc))
    if INTERNAL_DOMAIN in para:
        by_para[para].append((meta, doc))

# ---- Preparar coleccion memoria ----
try:
    client.delete_collection(COLLECTION)
    print("Coleccion 'memoria' anterior eliminada", flush=True)
except:
    pass
mem_col = client.create_collection(COLLECTION)

docs_to_add = []

# === 1. PERSONAS INTERNAS ===
SYSTEM_INTERNO = (
    "Eres un asistente CRM de GuiaGo. Analiza los correos enviados A esta persona interna "
    "de la empresa y genera una ficha de perfil que incluya: "
    "su rol en la empresa, los temas que gestiona, los contactos externos con los que interactua, "
    "y cualquier patron relevante observado. Redacta en espanol, de forma concisa y util."
)
internal_emails = {e: items for e, items in by_para.items() if INTERNAL_DOMAIN in e}
print(f"\nPersonas internas detectadas: {list(internal_emails.keys())}", flush=True)

for email, items in internal_emails.items():
    count = len(items)
    print(f"  [INTERNO] {email} ({count} correos recibidos)...", flush=True)
    ctx = build_context(items)
    user_msg = f"Persona: {email}\nCorreos recibidos: {count}\n\nEMAILS:\n{ctx}"
    try:
        summary = call_modal(SYSTEM_INTERNO, user_msg)
    except Exception as e:
        summary = f"Error: {e}"
    docs_to_add.append({
        "id":   f"persona_{email}",
        "doc":  f"FICHA DE PERSONA INTERNA: {email}\n\n{summary}",
        "meta": {"tipo": "persona_interna", "email": email, "n_correos": count}
    })
    print("     OK", flush=True)

# === 2. CONTACTOS EXTERNOS PRINCIPALES ===
SYSTEM_EXTERNO = (
    "Eres un asistente CRM de GuiaGo. Analiza los correos recibidos de este contacto externo "
    "y genera una ficha que incluya: quienes son, que quieren o proponen, "
    "oportunidades de negocio o colaboracion, y estado de la relacion. "
    "Redacta en espanol, de forma concisa y util."
)
external = [
    (e, items) for e, items in by_sender.items()
    if INTERNAL_DOMAIN not in e and not SKIP_RE.search(e)
]
external_ranked = sorted(external, key=lambda x: len(x[1]), reverse=True)  # todos los contactos reales
print(f"\nContactos externos a procesar: {len(external_ranked)}", flush=True)

for email, items in external_ranked:
    count = len(items)
    fechas = sorted([m.get("fecha","") for m, _ in items if m.get("fecha")])
    primera, ultima = (fechas[0] if fechas else "?"), (fechas[-1] if fechas else "?")
    print(f"  [EXTERNO] {email} ({count} correos)...", flush=True)
    ctx = build_context(items)
    user_msg = (
        f"Remitente: {email}\nTotal correos: {count}\n"
        f"Primera comunicacion: {primera}\nUltima comunicacion: {ultima}\n\nEMAILS:\n{ctx}"
    )
    try:
        summary = call_modal(SYSTEM_EXTERNO, user_msg)
    except Exception as e:
        summary = f"Error: {e}"
    docs_to_add.append({
        "id":   f"contacto_{email}",
        "doc":  f"FICHA DE CONTACTO EXTERNO: {email}\n\nPeriodo: {primera} - {ultima}\n\n{summary}",
        "meta": {"tipo": "contacto_externo", "email": email, "n_correos": count,
                 "primera": primera, "ultima": ultima}
    })
    print("     OK", flush=True)

# === 3. RESUMEN GLOBAL DEL NEGOCIO ===
print("\n  [GLOBAL] Generando resumen del negocio...", flush=True)
SYSTEM_GLOBAL = (
    "Eres un analista de negocio. A partir de una muestra de correos empresariales de GuiaGo "
    "(empresa de tours y actividades en Espana), genera un resumen ejecutivo que incluya: "
    "principales areas de actividad, tipos de contactos y relaciones, oportunidades detectadas, "
    "y patrones relevantes del negocio. Redacta en espanol."
)
# Muestra representativa: 1 de cada 20 emails
sample = [doc for doc in all_docs[::10]][:120]
sample_text = "\n---\n".join(s[:300] for s in sample)
try:
    global_summary = call_modal(SYSTEM_GLOBAL, f"MUESTRA DE CORREOS:\n{sample_text}", max_tokens=800)
except Exception as e:
    global_summary = f"Error: {e}"
docs_to_add.append({
    "id":   "resumen_global_negocio",
    "doc":  f"RESUMEN GLOBAL DE GUIAGO\n\n{global_summary}",
    "meta": {"tipo": "resumen_global"}
})
print("     OK", flush=True)

# === Insertar todo en ChromaDB ===
print(f"\nInsertando {len(docs_to_add)} documentos en coleccion 'memoria'...", flush=True)
mem_col.add(
    ids       = [d["id"] for d in docs_to_add],
    documents = [d["doc"] for d in docs_to_add],
    metadatas = [d["meta"] for d in docs_to_add],
)
print(f"Coleccion 'memoria' creada con {mem_col.count()} documentos.", flush=True)
print("DONE", flush=True)
