# GuiaGo Chat - Asistente IA Interno

Sistema de gestion interna con IA para GuiaGo: CRM con fases de venta, prediccion de respuestas de correo y base de conocimiento interna.

## Stack

- **LLM**: Ollama (Llama 3.1 8B quantizado) - corre en CPU
- **Vector DB**: ChromaDB (embeddings locales)
- **Backend**: FastAPI + LangChain
- **Infra**: Docker Compose

## Requisitos

- Docker y Docker Compose
- 8GB+ RAM disponible (el modelo usa ~5GB)

## Setup rapido en el miniPC

```bash
# 1. Clonar
git clone https://github.com/monoteco/guiagochat.git
cd guiagochat

# 2. Configurar
cp .env.example .env

# 3. Levantar servicios
docker compose up -d

# 4. Descargar el modelo (solo la primera vez, ~4.5GB)
docker exec guiagochat-ollama ollama pull llama3.1:8b-instruct-q4_K_M

# 5. Verificar
curl http://localhost:8000/health
```

## API Endpoints

### Chat (RAG)
```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H 'Content-Type: application/json' \
  -d '{"message": "En que fase esta el cliente X?"}'
```

### CRM - Crear deal
```bash
curl -X POST http://localhost:8000/api/v1/crm/deals \
  -H 'Content-Type: application/json' \
  -d '{"client_name": "Hotel Miramar", "email": "info@miramar.com", "phase": "lead"}'
```

### CRM - Listar deals por fase
```bash
curl http://localhost:8000/api/v1/crm/deals?phase=negociacion
```

### CRM - Actualizar fase
```bash
curl -X PATCH http://localhost:8000/api/v1/crm/deals/{deal_id}/phase \
  -H 'Content-Type: application/json' \
  -d '{"phase": "propuesta"}'
```

### Ingestar documentos
```bash
# Copiar archivos .txt a data/documents/ y .eml a data/emails/
curl -X POST http://localhost:8000/api/v1/ingest/documents -H 'Content-Type: application/json' -d '{}'
curl -X POST http://localhost:8000/api/v1/ingest/emails -H 'Content-Type: application/json' -d '{}'
```

## Fases del CRM

lead -> contactado -> propuesta -> negociacion -> cerrado -> produccion -> finalizado

## Estructura

```
guiagochat/
├── backend/
│   ├── app/
│   │   ├── api/          # Rutas FastAPI
│   │   ├── core/         # Config, LLM, VectorStore
│   │   ├── ingestion/    # Carga de emails y documentos
│   │   ├── models/       # Schemas Pydantic
│   │   └── services/     # RAG y CRM
│   ├── Dockerfile
│   └── requirements.txt
├── data/                  # (gitignored) emails y documentos
├── logs/                  # (gitignored)
├── docker-compose.yml
└── .env.example
```
