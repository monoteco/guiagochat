# GuiaGo Chat - Asistente IA Interno

Backend de IA para uso interno de GuiaGo.
Combina RAG sobre datos propios, utilidades de CRM, simulacion/clasificacion de correos y jobs de fine-tuning.

## Que hace este proyecto

- Chat con contexto (RAG) usando ChromaDB + Ollama.
- Ingesta de datos desde:
  - correos `.eml`
  - documentos `.txt`
  - base SQLite `correosGo.db`
- CRM liviano para crear deals, mover fases y buscar por similitud.
- Simulacion de respuestas comerciales con estilo interno.
- Clasificacion de tipo de negocio y fase comercial.
- Comparacion de respuestas entre modelos disponibles en Ollama.
- Pipeline de fine-tuning (generar dataset, entrenar, exportar) ejecutado como jobs en background.

## Integraciones externas

### Telegram

No existe integracion con Telegram en este repositorio.

Se revisaron patrones de codigo y no hay referencias a:
- `telegram`
- `api.telegram.org`
- `chat_id`
- `sendMessage`
- `-1003897327460`

Si necesitas enviar mensajes a Telegram, hoy tendria que implementarse desde cero.

## Stack

- FastAPI
- LangChain
- Ollama
- ChromaDB
- Pydantic
- Docker Compose

## Estructura del repo

```text
guiagochat/
|-- backend/
|   |-- Dockerfile
|   |-- requirements.txt
|   `-- app/
|       |-- main.py                # App FastAPI, /health y static index
|       |-- api/
|       |   `-- routes.py          # Endpoints /api/v1/*
|       |-- core/
|       |   |-- config.py          # Settings y .env
|       |   |-- llm.py             # Cliente LLM (Ollama)
|       |   `-- vectorstore.py     # Chroma collections
|       |-- ingestion/
|       |   |-- email_loader.py    # Ingesta de .eml
|       |   |-- document_loader.py # Ingesta de .txt con chunking
|       |   `-- db_loader.py       # Ingesta de correosGo.db
|       |-- models/
|       |   `-- schemas.py         # Modelos request/response
|       |-- services/
|       |   |-- rag_service.py
|       |   |-- crm_service.py
|       |   |-- simulate_service.py
|       |   |-- compare_service.py
|       |   `-- finetune_service.py
|       `-- static/
|           `-- index.html
|-- data/
|   |-- documents/
|   `-- emails/
|-- finetune/
|   |-- config.yaml
|   |-- generate_dataset.py
|   |-- train.py
|   `-- export_to_ollama.py
|-- logs/
|-- docker-compose.yml
|-- start.sh
`-- README.md
```

## Flujo funcional

1. Se ingesta informacion en una coleccion de Chroma.
2. En una consulta, se recuperan chunks relevantes por similitud.
3. El contexto recuperado se pasa al modelo en Ollama.
4. Se devuelve respuesta + fuentes.

En paralelo, el modulo CRM guarda deals en otra coleccion y permite operar fases del pipeline comercial.

## Endpoints principales

Base API: `/api/v1`

- `POST /chat`
- `POST /ingest/documents`
- `POST /ingest/emails`
- `POST /ingest/db`
- `POST /simulate/response`
- `POST /classify/business`
- `POST /classify/phase`
- `POST /compare`
- `GET /models`
- `POST /crm/deals`
- `PATCH /crm/deals/{deal_id}/phase`
- `GET /crm/deals`
- `GET /crm/deals/search?q=...`
- `POST /finetune/dataset`
- `POST /finetune/train`
- `GET /finetune/jobs`
- `GET /finetune/jobs/{job_id}`
- `POST /finetune/export`

Adicional:
- `GET /health`
- `GET /` (sirve `backend/app/static/index.html`)

## Setup rapido (Docker)

```bash
git clone https://github.com/monoteco/guiagochat.git
cd guiagochat
cp .env.example .env
docker compose up -d
```

Descargar modelo (primera vez):

```bash
docker exec guiagochat-ollama ollama pull llama3.1:8b-instruct-q4_K_M
```

Verificar:

```bash
curl http://localhost:8000/health
```

## Ejecucion local con start.sh

`start.sh` esta pensado para Linux (miniPC). Hace:

- levanta Ollama si no esta corriendo
- activa venv
- arranca FastAPI en un puerto libre empezando por `8080`
- valida `/health`

Uso:

```bash
bash ~/guiagochat/start.sh
```

## Ingesta de datos

Documentos `.txt` en `data/documents`:

```bash
curl -X POST http://localhost:8000/api/v1/ingest/documents \
  -H 'Content-Type: application/json' \
  -d '{"collection":"general"}'
```

Correos `.eml` en `data/emails`:

```bash
curl -X POST http://localhost:8000/api/v1/ingest/emails \
  -H 'Content-Type: application/json' \
  -d '{"collection":"emails"}'
```

Base SQLite `data/correosGo.db`:

```bash
curl -X POST http://localhost:8000/api/v1/ingest/db \
  -H 'Content-Type: application/json' \
  -d '{"collection":"emails"}'
```

## CRM phases

`lead -> contactado -> propuesta -> negociacion -> cerrado -> produccion -> finalizado`

## Notas operativas

- `docker-compose.yml` publica la API en `8000`.
- `start.sh` arranca por defecto desde `8080` (o siguiente libre).
- `finetune_service.py` guarda jobs en `data/finetune/jobs.json` y logs en `logs/`.

## Documento complementario

Para detalles de entrenamiento/modelos y estado operativo, ver `ENTRENAMIENTO.md`.
