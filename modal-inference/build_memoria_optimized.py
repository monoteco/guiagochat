"""
build_memoria_optimized.py - Construye colección 'memoria' desde emails
Optimizado para ejecutarse en Modal o localmente
"""
import chromadb
import requests
import re
import sys
from collections import defaultdict
from pathlib import Path

MODAL_URL = "https://hernandogerman--guiago-inference-guiagomodel-chat.modal.run"
SKIP_RE = re.compile(
    r"noreply|no-reply|notifications?-|amazon\.|linkedin\.com|" +
    r"microsoftexchange|@mailer\.|@news\.|@email\.|facebookmail\.com|" +
    r"elparking|canva\.com|icontactmail|silbon|todoalacuenta|vmartinez",
    re.IGNORECASE
)

def call_llm(system_msg, user_msg, max_tokens=500):
    \"\"\"Llamar a Modal LLM endpoint\"\"\"
    payload = {
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg}
        ],
        "max_tokens": max_tokens,
        "temperature": 0.2
    }
    try:
        resp = requests.post(MODAL_URL, json=payload, timeout=300)
        resp.raise_for_status()
        return resp.json()["content"].strip()
    except Exception as e:
        print(f"  ❌ LLM error: {e}")
        return ""

def extract_email(sender):
    if "<" in sender:
        return sender.split("<")[-1].replace(">", "").strip().lower()
    return sender.strip().lower()

def build_memoria(chroma_path="./chroma_db"):
    \"\"\"Construir colección memoria desde emails\"\"\"
    client = chromadb.PersistentClient(path=chroma_path)
    
    # Cargar emails
    emails_col = client.get_collection("emails")
    total = emails_col.count()
    print(f"📧 Cargando {total} emails...")
    
    all_docs, all_metas = [], []
    for offset in range(0, total, 500):
        res = emails_col.get(limit=500, offset=offset, include=["documents", "metadatas"])
        all_docs.extend(res["documents"])
        all_metas.extend(res["metadatas"])
    
    # Agrupar por remitente y destinatario
    by_sender = defaultdict(list)
    by_para = defaultdict(list)
    for doc, meta in zip(all_docs, all_metas):
        sender = extract_email(meta.get("de", ""))
        para = extract_email(meta.get("para", ""))
        by_sender[sender].append((meta, doc))
        if "laguiago.com" in para:
            by_para[para].append((meta, doc))
    
    # Preparar/recuperar colección memoria
    try:
        mem_col = client.get_collection("memoria")
        existing_ids = set(mem_col.get(include=[])["ids"])
        print(f"📚 Colección memoria existe con {len(existing_ids)} docs. Reanudando...")
    except:
        mem_col = client.create_collection("memoria", metadata={"hnsw:space": "cosine"})
        existing_ids = set()
        print(f"📚 Colección memoria nueva creada")
    
    stats = {"processed": 0, "skipped": 0, "errors": 0, "new": 0}
    
    # FASE 1: Personas internas
    print("\n🔵 FASE 1: Personas Internas")
    for sender in sorted(by_para.keys()):
        threads = by_para[sender]
        doc_id = f"internal_{sender.replace('@', '-')}"
        
        if doc_id in existing_ids:
            stats["skipped"] += 1
            print(f"  [SKIP] {sender}")
            continue
        
        context = "\\n".join([
            f"[{t[0].get('fecha', '')}] {t[0].get('asunto', '')}\\n{t[1][:300]}"
            for t in threads[:5]
        ])
        
        ficha = call_llm(
            "Eres analista de negocio. Crea una ficha detallada de esta persona interna.",
            f"Emails de {sender}:\\n\\n{context[:4000]}",
            max_tokens=300
        )
        
        if ficha:
            mem_col.add(
                ids=[doc_id],
                documents=[ficha],
                metadatas=[{"tipo": "interno", "email": sender}]
            )
            stats["processed"] += 1
            stats["new"] += 1
            print(f"  ✅ {sender} ({len(threads)} emails)")
        else:
            stats["errors"] += 1
    
    # FASE 2: Contactos externos
    print("\n🟠 FASE 2: Contactos Externos")
    ext_count = 0
    for sender in sorted(by_sender.keys()):
        if SKIP_RE.search(sender) or "laguiago.com" in sender:
            continue
        
        threads = by_sender[sender]
        doc_id = f"external_{sender.replace('@', '-')}"
        
        if doc_id in existing_ids:
            stats["skipped"] += 1
            continue
        
        context = "\\n".join([
            f"[{t[0].get('fecha', '')}] {t[0].get('asunto', '')}\\n{t[1][:300]}"
            for t in threads[:3]
        ])
        
        ficha = call_llm(
            "Eres analista de relaciones. Crea una ficha de este contacto externo.",
            f"{sender} ({len(threads)} correos):\\n\\n{context[:4000]}",
            max_tokens=250
        )
        
        if ficha:
            mem_col.add(
                ids=[doc_id],
                documents=[ficha],
                metadatas={"tipo": "externo", "email": sender, "correos": len(threads)}
            )
            stats["processed"] += 1
            stats["new"] += 1
            ext_count += 1
            if ext_count % 10 == 0:
                print(f"  ✅ {ext_count} contactos externos procesados")
        else:
            stats["errors"] += 1
    
    # FASE 3: Resumen global
    print("\n🟡 FASE 3: Resumen Global")
    doc_id = "global_summary"
    if doc_id not in existing_ids:
        sample = " ".join([doc[:500] for doc, _ in zip(all_docs, all_metas) if _ % 10 == 0][:5])
        ficha = call_llm(
            "Eres CEO analizando el negocio. Haz un resumen ejecutivo.",
            f"Muestra de emails:\\n\\n{sample}",
            max_tokens=500
        )
        if ficha:
            mem_col.add(
                ids=[doc_id],
                documents=[ficha],
                metadatas=[{"tipo": "resumen"}]
            )
            stats["new"] += 1
            print(f"  ✅ Resumen global generado")
    
    print(f"\n✅ DONE: {stats['processed']} procesados, {stats['new']} nuevos, {stats['skipped']} saltados, {stats['errors']} errores")
    return stats

if __name__ == "__main__":
    chroma_path = sys.argv[1] if len(sys.argv) > 1 else "./chroma_db"
    build_memoria(chroma_path)
