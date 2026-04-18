# GuiaGo Chat - Asistente IA Interno

Backend de IA para uso interno de GuiaGo.
Combina RAG sobre datos propios, CRM, clasificacion de correos y pipeline de fine-tuning.

---

## Estado operativo (actualizado 2026-04-18)

| Componente | Estado | Detalle |
|---|---|---|
| API FastAPI | OK | Puerto 8080 en `caro`, `start.sh` |
| Ollama (LLM) | OK | `mistral-nemo` activo |
| ChromaDB (RAG) | OK | 3496 correos indexados |
| Enriquecimiento BD | COMPLETADO | 2522/2522 emails con `resumen_ia` + `fase_ia` |
| Dataset fine-tuning | GENERADO | 4932 pares (train=4439, val=493) |
| Fine-tuning | EN CURSO | Lambda Labs A10 GPU — ~32 min |
| Adapter LoRA | PENDIENTE | Se descarga al terminar training |
| Modelo `mistral-guiago` | PENDIENTE | Registro en Ollama tras descarga |

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

---

## Modelos LLM disponibles

| Modelo | Tamano | Parametros | Calidad espanol | RAM uso | Velocidad (CPU) |
|---|---|---|---|---|---|
| **mistral-nemo** (ACTIVO) | 7.1 GB | 12B | Excelente | ~9 GB | ~18 seg/resp |
| mistral:7b-instruct-q4_K_M | 4.4 GB | 7B | Muy buena | ~6 GB | ~12 seg/resp |
| llama3.1:8b-instruct-q4_K_M | 4.9 GB | 8B | Buena | ~7 GB | ~15 seg/resp |
| **mistral-guiago** (PROXIMO) | ~5 GB | 7B LoRA | Especifico GuiaGo | ~6 GB | ~12 seg/resp |

Para cambiar de modelo: editar `OLLAMA_MODEL` en `~/guiagochat/.env` y reiniciar con `start.sh`.

---

## Fases del embudo comercial

```
lead → contactado → propuesta → negociacion → cerrado → produccion → finalizado
```

---

## Pipeline de enriquecimiento y fine-tuning

```
correosGo.db (cuerpo_txt)
        |
        v
scripts/enrich_emails.py       COMPLETADO — 2522/2522 emails
        |
        v
correosGo.db (resumen_ia + fase_ia poblados)
        |
        v
finetune/generate_dataset.py   COMPLETADO — 4932 pares en data/finetune/
        |
        v
finetune/train.py              EN CURSO — Lambda Labs A10 GPU (~32 min)
        |
        v
finetune/export_to_ollama.py   PENDIENTE — exporta adapter a Ollama
```

---

## Fine-tuning en Lambda Labs (GPU cloud)

El entrenamiento en CPU en `caro` causaba sobrecalentamiento (apagones a 88 C).
Se mueve a Lambda Labs con GPU A10 (24 GB VRAM) a $1.29/h.

### Configuracion (`finetune/config_lambda.yaml`)

| Parametro | Valor |
|---|---|
| Modelo base | `mistralai/Mistral-7B-Instruct-v0.3` |
| LoRA r | 8 |
| batch_size | 1 |
| gradient_accumulation | 16 |
| max_seq_length | 512 |
| num_epochs | 1 |
| bf16 | True (auto-detectado) |

### Comandos de monitoreo

```bash
# Ver progreso del training en Lambda
ssh ubuntu@64.181.231.152 "tail -5 ~/guiagochat/logs/train.log"

# Comprobar que sigue vivo
ssh ubuntu@64.181.231.152 "ps aux | grep train.py | grep -v grep"
```

### Cuando termine el training

```bash
# 1. Descargar adapter LoRA a local
scp -r ubuntu@64.181.231.152:/home/ubuntu/guiagochat/finetune/adapters/mistral7b ./finetune_output/

# 2. Subir adapter a caro
scp -r ./finetune_output/mistral7b caro@100.103.98.125:~/guiagochat/finetune/adapters/

# 3. En caro: registrar en Ollama
ssh caro@100.103.98.125 'cd ~/guiagochat && source venv/bin/activate && python3 finetune/export_to_ollama.py --model mistral7b'

# 4. Activar modelo nuevo
ssh caro@100.103.98.125 "sed -i 's/OLLAMA_MODEL=.*/OLLAMA_MODEL=mistral-guiago/' ~/guiagochat/.env"
ssh caro@100.103.98.125 'bash ~/guiagochat/start.sh'

# 5. Terminar instancia Lambda (para de cobrar)
# Dashboard Lambda Labs → Instances → Terminate
```

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
│       └── services/
│           ├── rag_service.py       # Chat RAG
│           ├── crm_service.py       # Deals y fases
│           ├── simulate_service.py  # Borradores de respuesta
│           ├── compare_service.py   # Comparar modelos
│           └── finetune_service.py  # Jobs de fine-tuning
├── data/
│   ├── documents/                   # .txt para ingestar
│   ├── emails/                      # .eml para ingestar
│   └── finetune/                    # train.jsonl + val.jsonl (4932 pares)
├── finetune/
│   ├── config.yaml                  # Config CPU (caro)
│   ├── config_lambda.yaml           # Config GPU (Lambda Labs)
│   ├── generate_dataset.py          # Genera train.jsonl / val.jsonl
│   ├── train.py                     # Fine-tuning LoRA (auto GPU/CPU)
│   └── export_to_ollama.py          # Exporta modelo a Ollama
├── scripts/
│   ├── enrich_emails.py             # Pobla resumen_ia y fase_ia en BD
│   ├── thermal_watchdog.sh          # Pausa training si CPU >= 88 C
│   └── lambda_train.sh              # Setup y training en Lambda Labs
├── logs/                            # api.log, enrich.log, train.log
├── LAMBDA_GUIDE.md                  # Guia completa de fine-tuning en GPU cloud
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
ssh caro@100.103.98.125 'tail -f ~/guiagochat/logs/train.log'
```

---

## Proximos pasos

| Prioridad | Tarea | Estado |
|---|---|---|
| 1 | Terminar training en Lambda Labs | EN CURSO (~32 min desde lanzamiento) |
| 2 | Descargar adapter LoRA de Lambda a local | PENDIENTE — ver seccion GPU arriba |
| 3 | Subir adapter a caro y registrar en Ollama | PENDIENTE |
| 4 | Activar `mistral-guiago` en `.env` y probar | PENDIENTE |
| 5 | Terminar instancia Lambda Labs (evitar coste) | PENDIENTE |
| 6 | Loaders para BDClientes.db y BDPreclientes.db | PENDIENTE |
| 7 | Systemd service para auto-start en caro | PENDIENTE |
| 8 | Cron de re-ingesta periodica de correos nuevos | PENDIENTE |
| 9 | Frontend web mejorado | PENDIENTE |

---

## Integraciones externas

### Telegram: NO existe

Cero referencias a `telegram`, `chat_id` o `sendMessage` en este repositorio.
Si se necesita en el futuro, debe implementarse desde cero.