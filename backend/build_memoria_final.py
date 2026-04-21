import chromadb
import requests
import re
import sys
from collections import defaultdict

MODAL_URL = "https://hernandogerman--guiago-inference-guiagomodel-chat.modal.run"
SKIP_RE = re.compile(r"noreply|no-reply|notifications?-|amazon\.|linkedin\.com|microsoftexchange|@mailer\.|@news\.|@email\.|facebookmail\.com|elparking|canva\.com|icontactmail|silbon|todoalacuenta|vmartinez", re.IGNORECASE)

def call_llm(system_msg, user_msg, max_tokens=500):
    payload = {"messages": [{"role": "system", "content": system_msg}, {"role": "user", "content": user_msg}], "max_tokens": max_tokens, "temperature": 0.2}
    try:
        resp = requests.post(MODAL_URL, json=payload, timeout=300)
        resp.raise_for_status()
        return resp.json()["content"].strip()
    except Exception as e:
        print(f"  Error LLM: {e}")
        return ""

def extract_email(sender):
    if "<" in sender:
        return sender.split("<")[-1].replace(">", "").strip().lower()
    return sender.strip().lower()

def build_memoria(chroma_path="./chroma_db"):
    client = chromadb.PersistentClient(path=chroma_path)
    emails_col = client.get_collection("emails")
    total = emails_col.count()
    print(f"Cargando {total} emails...")
    
    all_docs, all_metas = [], []
    for offset in range(0, total, 500):
        res = emails_col.get(limit=500, offset=offset, include=["documents", "metadatas"])
        all_docs.extend(res["documents"])
        all_metas.extend(res["metadatas"])
    
    by_sender = defaultdict(list)
    by_para = defaultdict(list)
    for doc, meta in zip(all_docs, all_metas):
        sender = extract_email(meta.get("de", ""))
        para = extract_email(meta.get("para", ""))
        by_sender[sender].append((meta, doc))
        if "laguiago.com" in para:
            by_para[para].append((meta, doc))
    
    try:
        mem_col = client.get_collection("memoria")
        existing_ids = set(mem_col.get(include=[])["ids"])
        print(f"Memoria existe con {len(existing_ids)} docs. Reanudando...")
    except:
        mem_col = client.create_collection("memoria", metadata={"hnsw:space": "cosine"})
        existing_ids = set()
        print("Memoria nueva creada")
    
    stats = {"processed": 0, "skipped": 0, "errors": 0, "new": 0}
    
    print("\nFASE 1: Personas Internas")
    for sender in sorted(by_para.keys()):
        threads = by_para[sender]
        doc_id = f"internal_{sender.replace('@', '-')}"
        if doc_id in existing_ids:
            stats["skipped"] += 1
            continue
        context = "\n".join([f"[{t[0].get('fecha', '')}] {t[0].get('asunto', '')}\n{t[1][:300]}" for t in threads[:5]])
        ficha = call_llm("Eres analista de negocio. Crea una ficha detallada de esta persona interna.", f"Emails de {sender}:\n\n{context[:4000]}", max_tokens=300)
        if ficha:
            mem_col.add(ids=[doc_id], documents=[ficha], metadatas=[{"tipo": "interno", "email": sender}])
            stats["processed"] += 1
            stats["new"] += 1
            print(f"OK {sender} ({len(threads)} emails)")
        else:
            stats["errors"] += 1
    
    print("\nFASE 2: Contactos Externos")
    ext_count = 0
    for sender in sorted(by_sender.keys()):
        if SKIP_RE.search(sender) or "laguiago.com" in sender:
            continue
        threads = by_sender[sender]
        doc_id = f"external_{sender.replace('@', '-')}"
        if doc_id in existing_ids:
            stats["skipped"] += 1
            continue
        context = "\n".join([f"[{t[0].get('fecha', '')}] {t[0].get('asunto', '')}\n{t[1][:300]}" for t in threads[:3]])
        ficha = call_llm("Eres analista de relaciones. Crea una ficha de este contacto externo.", f"{sender} ({len(threads)} correos):\n\n{context[:4000]}", max_tokens=250)
        if ficha:
            mem_col.add(ids=[doc_id], documents=[ficha], metadatas=[{"tipo": "externo", "email": sender, "correos": len(threads)}])
            stats["processed"] += 1
            stats["new"] += 1
            ext_count += 1
            if ext_count % 20 == 0:
                print(f"OK {ext_count} externos")
        else:
            stats["errors"] += 1
    
    print(f"\nDONE: {stats['processed']} procesados, {stats['new']} nuevos, {stats['skipped']} saltados")
    return stats

if __name__ == "__main__":
    build_memoria("./chroma_db")
