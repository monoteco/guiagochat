import modal
import json
import requests
import chromadb
from collections import defaultdict
import re

app = modal.App("guiago-memoria")

image = modal.Image.debian_slim().pip_install(
    "chromadb>=1.0.7",
    "requests>=2.31.0",
    "protobuf>=4.25.0"
)

MODAL_INFERENCE = "https://hernandogerman--guiago-inference-guiagomodel-chat.modal.run"
SKIP_RE = re.compile(
    r"noreply|no-reply|notifications?-|amazon\.|linkedin\.com|" +
    r"microsoftexchange|@mailer\.|@news\.|@email\.|facebookmail\.com|" +
    r"elparking|canva\.com|icontactmail|silbon|todoalacuenta|vmartinez",
    re.IGNORECASE
)

def call_modal_inference(system_msg, user_msg, max_tokens=500):
    payload = {
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg}
        ],
        "max_tokens": max_tokens,
        "temperature": 0.2
    }
    try:
        resp = requests.post(MODAL_INFERENCE, json=payload, timeout=300)
        resp.raise_for_status()
        return resp.json()["content"].strip()
    except Exception as e:
        print(f"Error: {e}")
        return ""

@app.function(image=image, timeout=3600)
def build_memoria():
    import chromadb
    from collections import defaultdict
    
    print("Conectando a ChromaDB local...")
    client = chromadb.PersistentClient(path="./chroma_db")
    
    emails_col = client.get_collection("emails")
    total = emails_col.count()
    print(f"OK: {total} emails loaded")
    
    try:
        mem_col = client.get_collection("memoria")
        existing = set(mem_col.get(include=[])["ids"])
        print(f"Resuming: {len(existing)} existing docs")
    except:
        mem_col = client.create_collection("memoria")
        existing = set()
    
    docs_list = []
    for offset in range(0, total, 500):
        res = emails_col.get(limit=500, offset=offset, include=["documents", "metadatas"])
        docs_list.extend(zip(res["metadatas"], res["documents"]))
    
    by_sender = defaultdict(list)
    for meta, doc in docs_list:
        sender = meta.get("de", "").lower()
        by_sender[sender].append((meta, doc[:500]))
    
    stats = {"processed": 0, "added": 0, "skipped": 0}
    
    print("\n=== EXTERNAL CONTACTS ===")
    for sender, threads in sorted(by_sender.items()):
        if SKIP_RE.search(sender) or "@laguiago.com" in sender:
            stats["skipped"] += 1
            continue
        
        doc_id = f"ext_{sender.replace('@', '-')}"
        if doc_id in existing:
            stats["skipped"] += 1
            continue
        
        context = "\n".join([f"[{m.get('fecha','')}] {m.get('asunto','')}" for m, _ in threads[:3]])
        ficha = call_modal_inference(
            "Eres analista de relaciones. Resume este contacto.",
            context[:2000],
            max_tokens=300
        )
        
        if ficha:
            mem_col.add(
                ids=[doc_id],
                documents=[ficha],
                metadatas=[{"type": "external", "email": sender}]
            )
            stats["added"] += 1
            stats["processed"] += 1
            print(f"  [OK] {sender}")
    
    print(f"\nDONE: {stats['processed']} procesados")
    return stats

@app.local_entrypoint()
def main():
    result = build_memoria.remote()
    print(json.dumps(result, indent=2))
