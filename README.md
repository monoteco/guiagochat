# GuiaGo Chat - Asistente IA Interno

Backend de IA para uso interno de GuiaGo.
Combina RAG sobre datos propios, CRM, clasificacion de correos y pipeline de fine-tuning.

---

## Estado operativo (actualizado 2026-04-15)

| Componente | Estado | Detalle |
|---|---|---|
| API FastAPI | OK | Puerto 8080, `start.sh` |
| Ollama (LLM) | OK | `mistral-nemo` activo |
| ChromaDB (RAG) | OK | 3496 correos indexados |
| Enriquecimiento BD | EN CURSO | ~1699/2527 emails procesados (~67%) |
| Fine-tuning | PENDIENTE | Esperando datos de `resumen_ia`/`fase_ia` |

---

## Que hace este proyecto

- **Chat RAG**: responde preguntas sobre correos, clientes y documentos internos
- **Ingesta de datos** desde correos `.eml`, documentos `.txt` y BD SQLite
- **CRM liviano**: deals, fases comerciales y busqueda semantica
- **Simulacion**: genera borradores de respuesta al estilo GuiaGo
- **Clasificacion**: tipo de negocio y fase del embudo comercial
- **Comparacion de modelos**: evalua respuestas entre los LLM disponibles
- **Fine-tuning pipeline**: generar dataset, entrenar y exportar modelo propio

---

## Infra — miniPC "caro"

| Parametro | Valor |
|---|---|
| Host | `caro@100.103.98.125` (Tailscale) |
| Hardware | Intel Core i9-9880H, 64 GB RAM, 2 TB SSD |
| OS | Debian 13 (sin GPU) |
| SSH | Key-based (sin contrasena) |
| Python | 3.13, venv en `~/guiagochat/venv/` |
| Ollama | Nativo (no Docker) |
| API | FastAPI en `0.0.0.0:8080` |
| ChromaDB | `~/guiagochat/chroma_db/` (47 MB, 3496 docs) |
| llama.cpp | Compilado en `~/llama.cpp/build/bin/` |

---

## Modelos LLM disponibles

| Modelo | Tamano | Parametros | Calidad espanol | RAM uso | Velocidad (CPU) |
|---|---|---|---|---|---|
| **mistral-nemo** (ACTIVO) | 7.1 GB | 12B | Excelente | ~9 GB | ~18 seg/resp |
| mistral:7b-instruct-q4_K_M | 4.4 GB | 7B | Muy buena | ~6 GB | ~12 seg/resp |
| llama3.1:8b-instruct-q4_K_M | 4.9 GB | 8B | Buena | ~7 GB | ~15 seg/resp |

Para cambiar de modelo: editar `OLLAMA_MODEL` en `~/guiagochat/.env` y reiniciar con `start.sh`.

---

## Fases del embudo comercial

```
lead → contactado → propuesta → negociacion → cerrado → produccion → finalizado
```

Estas fases se usan en:
- `fase_ia` en `correosGo.db` (generado por el script de enriquecimiento)
- Endpoint `POST /api/v1/classify/phase`
- CRM: `PATCH /api/v1/crm/deals/{deal_id}/phase`

---

## Datos ingestados

| Fuente | Registros | Estado | Coleccion ChromaDB |
|---|---|---|---|
| `correosGo.db` (correos) | 3496 | Indexado | `emails` |
| `BDClientes.db` | 56 | Pendiente loader | - |
| `BDPreclientes.db` | 166 | Pendiente loader | - |
| `data/documents/` (.txt) | 0 | Vacio | `general` |
| `data/emails/` (.eml) | 0 | Vacio | `emails` |

### Schema de `correosGo.db`

```sql
CREATE TABLE correos (
    id         INTEGER PRIMARY KEY,
    mailbox    TEXT,   -- INBOX, inbox, INBOX/Sent, Elementos enviados, ...
    de         TEXT,
    para       TEXT,
    cc         TEXT,
    asunto     TEXT,
    fecha      TEXT,
    cuerpo_txt TEXT,
    account    TEXT,
    resumen_ia TEXT,   -- generado por scripts/enrich_emails.py
    fase_ia    TEXT    -- generado por scripts/enrich_emails.py
);
```

---

## Pipeline de enriquecimiento y fine-tuning

```
correosGo.db (cuerpo_txt)
        |
        v
scripts/enrich_emails.py   ← EN CURSO (mistral-nemo genera resumen_ia + fase_ia)
        |
        v
correosGo.db (resumen_ia + fase_ia poblados)
        |
        v
finetune/generate_dataset.py  ← genera train.jsonl + val.jsonl
        |
        v
finetune/train.py             ← fine-tuning con LoRA/QLoRA
        |
        v
finetune/export_to_ollama.py  ← exporta modelo entrenado a Ollama
```

### Estado actual del enriquecimiento (15 abr 2026)

```bash
# Ver progreso en tiempo real
ssh caro@100.103.98.125 'tail -5 ~/guiagochat/logs/enrich.log'
```

- Procesados: ~1699 / 2527 (67%)
- Velocidad: ~18 seg/email (una sola llamada LLM)
- Finalizacion estimada: hoy ~14:15

---

## Estructura del repo

```
guiagochat/
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py                  # App FastAPI, /health y static
│       ├── api/
│       │   └── routes.py            # Todos los endpoints /api/v1/*
│       ├── core/
│       │   ├── config.py            # Settings (.env via pydantic)
│       │   ├── llm.py               # Cliente Ollama
│       │   └── vectorstore.py       # ChromaDB collections
│       ├── ingestion/
│       │   ├── email_loader.py      # Ingesta .eml
│       │   ├── document_loader.py   # Ingesta .txt con chunking
│       │   └── db_loader.py         # Ingesta correosGo.db
│       ├── models/
│       │   └── schemas.py           # Pydantic request/response
│       ├── services/
│       │   ├── rag_service.py       # Chat RAG
│       │   ├── crm_service.py       # Deals y fases
│       │   ├── simulate_service.py  # Borradores de respuesta
│       │   ├── compare_service.py   # Comparar modelos
│       │   └── finetune_service.py  # Jobs de fine-tuning
│       └── static/
│           └── index.html
├── data/
│   ├── documents/                   # .txt para ingestar
│   └── emails/                      # .eml para ingestar
├── finetune/
│   ├── config.yaml                  # Config del pipeline
│   ├── generate_dataset.py          # Genera train.jsonl / val.jsonl
│   ├── train.py                     # Fine-tuning LoRA
│   └── export_to_ollama.py          # Exporta modelo a Ollama
├── scripts/
│   └── enrich_emails.py             # Pobla resumen_ia y fase_ia en BD
├── logs/                            # api.log, enrich.log, train.log
├── docker-compose.yml
├── start.sh                         # Arranque Ollama + FastAPI
└── README.md
```

---

## Endpoints principales

Base: `http://caro:8080/api/v1`

| Metodo | Endpoint | Funcion |
|---|---|---|
| POST | `/chat` | Chat RAG sobre una coleccion |
| POST | `/ingest/documents` | Ingestar .txt de data/documents |
| POST | `/ingest/emails` | Ingestar .eml de data/emails |
| POST | `/ingest/db` | Ingestar correosGo.db |
| POST | `/simulate/response` | Borrador de respuesta comercial |
| POST | `/classify/business` | Tipo de negocio del correo |
| POST | `/classify/phase` | Fase del embudo comercial |
| POST | `/compare` | Comparar respuesta entre modelos |
| GET | `/models` | Listar modelos Ollama disponibles |
| POST | `/crm/deals` | Crear deal |
| PATCH | `/crm/deals/{id}/phase` | Mover fase |
| GET | `/crm/deals` | Listar deals |
| GET | `/crm/deals/search?q=` | Buscar por similitud |
| POST | `/finetune/dataset` | Generar dataset JSONL |
| POST | `/finetune/train` | Lanzar job de training |
| GET | `/finetune/jobs` | Listar jobs |
| GET | `/finetune/jobs/{id}` | Estado de un job |
| POST | `/finetune/export` | Exportar modelo entrenado |
| GET | `/health` | Health check |

---

## Operacion diaria

### Arrancar (si caro se reinicia)

```bash
ssh caro@100.103.98.125 'bash ~/guiagochat/start.sh'
```

### Probar RAG

```bash
curl -s -X POST http://caro:8080/api/v1/chat \
  -H 'Content-Type: application/json' \
  -d '{"message": "quien envia mas correos?", "collection": "emails"}'
```

### Ver logs

```bash
ssh caro@100.103.98.125 'tail -f ~/guiagochat/logs/api.log'
ssh caro@100.103.98.125 'tail -f ~/guiagochat/logs/enrich.log'
```

### Monitorear enriquecimiento

```bash
ssh caro@100.103.98.125 'grep "checkpoint" ~/guiagochat/logs/enrich.log | tail -3'
```

---

## Setup desde cero (Docker)

```bash
git clone https://github.com/monoteco/guiagochat.git
cd guiagochat
cp .env.example .env      # editar con rutas y modelo
docker compose up -d
docker exec guiagochat-ollama ollama pull mistral-nemo
curl http://localhost:8000/health
```

---

## Proximos pasos

| Prioridad | Tarea | Estado |
|---|---|---|
| 1 | Terminar enriquecimiento BD (`resumen_ia`/`fase_ia`) | EN CURSO — hoy ~14:15 |
| 2 | Ejecutar `generate_dataset.py` y validar pares | PENDIENTE |
| 3 | Lanzar fine-tuning con `train.py` | PENDIENTE |
| 4 | Loaders para BDClientes.db y BDPreclientes.db | PENDIENTE |
| 5 | Systemd service para auto-start al boot | PENDIENTE |
| 6 | Cron de re-ingesta periodica de correos nuevos | PENDIENTE |
| 7 | Frontend web mejorado | PENDIENTE |

---

## Integraciones externas

### Telegram: NO existe

Busqueda exhaustiva confirma cero referencias a `telegram`, `chat_id`, `sendMessage` o `-1003897327460` en este repositorio. Si se necesita en el futuro, debe implementarse desde cero.
