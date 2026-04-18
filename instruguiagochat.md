# Instrucciones - GuiaGo Chat API

**URL**: `http://100.103.98.125:8080`  
**Documentación interactiva**: `http://100.103.98.125:8080/docs`  
**Estado**: ✅ FUNCIONANDO (API + Ollama + ChromaDB)

---

## 1. Inicio Rápido

### 1.1 — Health Check (¿funciona?)

```bash
curl http://100.103.98.125:8080/health
# Respuesta: {"status":"ok"}
```

### 1.2 — El endpoint de CHAT (ventana tipo ChatGPT)

**SÍ, existe**: POST `/chat`

Envía un mensaje y recibes respuesta basada en los correos indexados:

```bash
curl -X POST http://100.103.98.125:8080/api/v1/chat \
  -H 'Content-Type: application/json' \
  -d '{
    "message": "¿Quién es el cliente que más correos ha enviado?",
    "collection": "emails"
  }'
```

**Respuesta típica**:
```json
{
  "message": "...",
  "response": "Basándome en los correos indexados...",
  "sources": [
    "email_id_123",
    "email_id_456"
  ],
  "model": "mistral-guiago:7b-q4_K_M"
}
```

---

## 2. Arquitectura de la API

```
┌────────────────────────────────────────┐
│ FastAPI Server (puerto 8080)           │
├────────────────────────────────────────┤
│ Routes:                                │
│  ├─ /chat                 ← CHAT RAG  │
│  ├─ /ingest/*             ← Ingesta   │
│  ├─ /simulate/*            ← IA tools │
│  ├─ /classify/*            ← Análisis │
│  ├─ /compare               ← Modelos  │
│  ├─ /crm/*                 ← CRM      │
│  ├─ /finetune/*            ← ML jobs  │
│  ├─ /reports/*             ← Informes │
│  └─ /models                ← Info     │
└────────────────────────────────────────┘
         ↓
┌────────────────────────────────────────┐
│ Services Layer                         │
├────────────────────────────────────────┤
│ ├─ rag_service.py          ← RAG      │
│ ├─ simulate_service.py      ← Resp.  │
│ ├─ crm_service.py           ← CRM    │
│ ├─ compare_service.py       ← Modelos│
│ ├─ finetune_service.py      ← Jobs   │
│ └─ reports_service.py       ← Reports│
└────────────────────────────────────────┘
         ↓
┌────────────────────────────────────────┐
│ Backends                               │
├────────────────────────────────────────┤
│ ├─ Ollama (LLM) :11434               │
│ │   └─ mistral-guiago:7b-q4_K_M      │
│ ├─ ChromaDB (vector DB)              │
│ │   └─ colecciones: emails, general  │
│ └─ SQLite (CRM)                      │
└────────────────────────────────────────┘
```

---

## 3. Acceso a la Documentación Interactiva

Abre en el navegador:  
**`http://100.103.98.125:8080/docs`**

Verás:
- ✅ Lista de todos los endpoints
- ✅ Esquemas de request/response
- ✅ Botón "Try it out" para probar sin curl
- ✅ Ejemplos de respuestas

---

## 4. Endpoints Principales

### 🔵 4.1 — CHAT RAG (ventana de chat)

**Endpoint**: `POST /api/v1/chat`

**Descripción**: Envía un mensaje y obtén respuesta basada en los datos indexados (correos). El LLM busca automáticamente los fragmentos relevantes y responde.

**Request**:
```json
{
  "message": "¿Qué servicios vende GuiaGo?",
  "collection": "emails"  // o "general", "crm_deals"
}
```

**Response**:
```json
{
  "message": "¿Qué servicios vende GuiaGo?",
  "response": "Según los correos, GuiaGo ofrece servicios de turismo...",
  "sources": ["email_5234", "email_8901"],
  "model": "mistral-guiago:7b-q4_K_M"
}
```

**Ejemplo curl**:
```bash
curl -X POST http://100.103.98.125:8080/api/v1/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"¿Cuáles son los clientes principales?","collection":"emails"}'
```

**Tiempo de respuesta**: 3-10 minutos (CPU i9)  
**Uso**: Chat histórico sobre correos, análisis de patrones, preguntas sobre datos

---

### 📥 4.2 — INGESTA (cargar datos)

#### 4.2.1 — Ingestar correos (.eml)

**Endpoint**: `POST /api/v1/ingest/emails`

```bash
curl -X POST http://100.103.98.125:8080/api/v1/ingest/emails \
  -H 'Content-Type: application/json' \
  -d '{"collection": "emails"}'
```

Busca archivos `.eml` en `data/emails/` y los indexa.

#### 4.2.2 — Ingestar documentos (.txt)

**Endpoint**: `POST /api/v1/ingest/documents`

```bash
curl -X POST http://100.103.98.125:8080/api/v1/ingest/documents \
  -H 'Content-Type: application/json' \
  -d '{"collection": "general"}'
```

Busca archivos `.txt` en `data/documents/` y los indexa en la colección especificada.

#### 4.2.3 — Ingestar base de datos SQLite

**Endpoint**: `POST /api/v1/ingest/db`

```bash
curl -X POST http://100.103.98.125:8080/api/v1/ingest/db \
  -H 'Content-Type: application/json' \
  -d '{"collection": "emails"}'
```

Carga `data/correosGo.db` (3,496 correos) en la colección especificada.

---

### 🤖 4.3 — SIMULACIÓN & CLASIFICACIÓN (IA tools)

#### 4.3.1 — Simular respuesta comercial

**Endpoint**: `POST /api/v1/simulate/response`

Genera una respuesta profesional a un cliente basada en el historial.

```bash
curl -X POST http://100.103.98.125:8080/api/v1/simulate/response \
  -H 'Content-Type: application/json' \
  -d '{
    "client_email": "cliente@example.com",
    "client_name": "Juan Pérez"
  }'
```

**Respuesta**:
```json
{
  "client_name": "Juan Pérez",
  "email": "cliente@example.com",
  "response": "Estimado Juan, muchas gracias por tu consulta..."
}
```

#### 4.3.2 — Clasificar tipo de negocio

**Endpoint**: `POST /api/v1/classify/business`

Analiza un texto y clasifica el tipo de negocio/oportunidad.

```bash
curl -X POST http://100.103.98.125:8080/api/v1/classify/business \
  -H 'Content-Type: application/json' \
  -d '{"text": "Hola, necesito un viaje para 20 personas a Cancún en julio"}'
```

**Respuesta**:
```json
{
  "text": "Hola, necesito un viaje...",
  "classification": "Viaje corporativo / Grupo",
  "confidence": 0.92
}
```

#### 4.3.3 — Clasificar fase comercial

**Endpoint**: `POST /api/v1/classify/phase`

Determina en qué etapa del embudo comercial está el cliente.

```bash
curl -X POST http://100.103.98.125:8080/api/v1/classify/phase \
  -H 'Content-Type: application/json' \
  -d '{"text": "Adjunto presupuesto para tu revisión..."}'
```

**Respuesta**:
```json
{
  "text": "Adjunto presupuesto...",
  "phase": "propuesta",
  "description": "Cliente en etapa de propuesta / presupuestación"
}
```

---

### 🔀 4.4 — COMPARAR MODELOS

**Endpoint**: `POST /api/v1/compare`

Compara respuestas entre el modelo fine-tuned y otros modelos.

```bash
curl -X POST http://100.103.98.125:8080/api/v1/compare \
  -H 'Content-Type: application/json' \
  -d '{
    "message": "¿Qué servicios ofrece GuiaGo?",
    "collection": "emails",
    "models": ["mistral-guiago:7b-q4_K_M", "llama3.1"]
  }'
```

**Respuesta**:
```json
{
  "message": "...",
  "models": {
    "mistral-guiago:7b-q4_K_M": "Respuesta modelo fine-tuned...",
    "llama3.1": "Respuesta modelo base..."
  }
}
```

**Get disponibles**:
```bash
curl http://100.103.98.125:8080/api/v1/models
```

---

### 📋 4.5 — CRM (gestión de clientes)

#### 4.5.1 — Crear deal

**Endpoint**: `POST /api/v1/crm/deals`

```bash
curl -X POST http://100.103.98.125:8080/api/v1/crm/deals \
  -H 'Content-Type: application/json' \
  -d '{
    "client_name": "Acme Corp",
    "email": "contact@acme.com",
    "phase": "propuesta",
    "notes": "Viaje para 50 personas, presupuesto €50k"
  }'
```

**Respuesta**:
```json
{
  "id": 123,
  "client_name": "Acme Corp",
  "email": "contact@acme.com",
  "phase": "propuesta",
  "notes": "Viaje para 50 personas...",
  "created_at": "2026-04-18T13:00:00Z"
}
```

#### 4.5.2 — Mover fase

**Endpoint**: `PATCH /api/v1/crm/deals/{deal_id}/phase`

```bash
curl -X PATCH http://100.103.98.125:8080/api/v1/crm/deals/123/phase \
  -H 'Content-Type: application/json' \
  -d '{"phase": "negociacion"}'
```

#### 4.5.3 — Listar deals

**Endpoint**: `GET /api/v1/crm/deals`

```bash
curl http://100.103.98.125:8080/api/v1/crm/deals
```

#### 4.5.4 — Buscar por similitud

**Endpoint**: `GET /api/v1/crm/deals/search?q=...`

```bash
curl "http://100.103.98.125:8080/api/v1/crm/deals/search?q=Acme"
```

---

### ⚙️ 4.6 — FINE-TUNING (entrenar modelos)

#### 4.6.1 — Generar dataset

**Endpoint**: `POST /api/v1/finetune/dataset`

```bash
curl -X POST http://100.103.98.125:8080/api/v1/finetune/dataset \
  -H 'Content-Type: application/json' \
  -d '{"model": "mistral7b"}'
```

Genera `data/finetune/train.jsonl` + `val.jsonl` desde `correosGo.db`.

#### 4.6.2 — Iniciar training

**Endpoint**: `POST /api/v1/finetune/train`

```bash
curl -X POST http://100.103.98.125:8080/api/v1/finetune/train \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "mistral7b",
    "config": "finetune/config_lambda.yaml"
  }'
```

**Respuesta**:
```json
{
  "job_id": "job_abc123",
  "model": "mistral7b",
  "status": "queued"
}
```

#### 4.6.3 — Ver status del job

**Endpoint**: `GET /api/v1/finetune/jobs/{job_id}`

```bash
curl http://100.103.98.125:8080/api/v1/finetune/jobs/job_abc123
```

---

### 📊 4.7 — INFORMES AUTOMÁTICOS

**Endpoints**: `POST /api/v1/reports/{tipo}`

Genera informes profesionales en PDF y PPTX sobre los datos.

#### Listar tipos disponibles:

```bash
curl http://100.103.98.125:8080/api/v1/reports
```

**Respuesta**:
```json
[
  {
    "report_type": "procedimientos",
    "title": "Manual de Procedimientos"
  },
  {
    "report_type": "negocios",
    "title": "Manual de Negocios"
  },
  {
    "report_type": "clientes",
    "title": "Estudio de Clientes"
  },
  {
    "report_type": "estrategico",
    "title": "Plan Estrategico"
  },
  {
    "report_type": "tactico",
    "title": "Plan Tactico (90 dias)"
  },
  {
    "report_type": "comunicacion",
    "title": "Analisis de Comunicacion"
  },
  {
    "report_type": "comercial",
    "title": "Informe Comercial"
  },
  {
    "report_type": "puesto_carolina",
    "title": "Descripcion Puesto de Trabajo - Carolina"
  }
]
```

#### Generar informe específico:

```bash
curl -X POST http://100.103.98.125:8080/api/v1/reports/procedimientos \
  -H 'Content-Type: application/json' \
  -d '{}'
```

**Respuesta** (20-30 líneas de contenido):
```json
{
  "report_type": "procedimientos",
  "content": "# Manual de Procedimientos GuiaGo\n\n## 1. Proceso de Captación...",
  "sources": ["email_123", "email_456", ...]
}
```

**⏱️ Tiempo**: ~5-10 min por informe (depende de CPU)

---

## 5. Colecciones en ChromaDB

| Colección | Contenido | Estado | Uso |
|-----------|-----------|--------|-----|
| `emails` | 3,496 correos (correosGo.db) | ✅ ACTIVA | Chat histórico, análisis |
| `general` | Documentos internos (.txt) | ⏳ Vacía | Procedures, FAQs |
| `crm_deals` | Datos del CRM estructurados | ⏳ Vacía | Análisis de deals |

**En /chat**: especifica qué colección usar con el parámetro `collection`.

---

## 6. Características del LLM

### Modelo actual en producción:

```
Nombre:          mistral-guiago:7b-q4_K_M
Base:            Mistral 7B Instruct v0.3
Parámetros:      7 mil millones
Tamaño:          4.4 GB (cuantizado Q4)
Fine-tune:       LoRA (27MB adapter)
Idioma:          Español + Inglés
Velocidad:       5-8 tokens/seg (CPU i9)
Contexto:        512 tokens max (en reportes)
Backend:         Ollama (puerto 11434)
```

### Capacidades:

✅ RAG sobre correos  
✅ Resúmenes de textos  
✅ Clasificación comercial  
✅ Generación de respuestas  
✅ Análisis de patrones  
✅ Redacción de documentos profesionales

---

## 7. Ejemplos Prácticos

### Caso 1: Preguntar sobre un cliente

```bash
curl -X POST http://100.103.98.125:8080/api/v1/chat \
  -H 'Content-Type: application/json' \
  -d '{
    "message": "¿Cuántos correos ha enviado el cliente Acme Corp?",
    "collection": "emails"
  }'
```

### Caso 2: Generar respuesta a un cliente

```bash
curl -X POST http://100.103.98.125:8080/api/v1/simulate/response \
  -H 'Content-Type: application/json' \
  -d '{
    "client_name": "Juan Pérez",
    "client_email": "juan@example.com"
  }'
```

### Caso 3: Generar informe de procedimientos

```bash
curl -X POST http://100.103.98.125:8080/api/v1/reports/procedimientos \
  -H 'Content-Type: application/json' \
  -d '{}'

# Descarga los archivos generados:
# c:\Users\germa\Downloads\development\GuiaGo\guiagochat\reports_output\
#   ├─ procedimientos.md
#   └─ procedimientos.pptx
```

### Caso 4: Crear deal en CRM

```bash
curl -X POST http://100.103.98.125:8080/api/v1/crm/deals \
  -H 'Content-Type: application/json' \
  -d '{
    "client_name": "FutureTours Ltd",
    "email": "info@futuretours.com",
    "phase": "lead",
    "notes": "Contacto en LinkedIn, interés en viajes corporativos"
  }'
```

---

## 8. Troubleshooting

| Problema | Solución |
|----------|----------|
| "Connection refused" | Verificar: `curl http://100.103.98.125:8080/health` |
| "Timeout" | Informe tarda 10+ min. Usar `--connect-timeout 900` |
| "Model not found" | `curl http://100.103.98.125:8080/api/v1/models` |
| "Collection empty" | Primero ingestar: `/ingest/db` o `/ingest/documents` |
| "LLM not responding" | SSH a caro: `tail -f ~/guiagochat/logs/api.log` |

---

## 9. Integración con Frontend

### Para construir una ventana de chat:

1. **GET** `/reports` → listar tipos (opcional, para UI)
2. **POST** `/chat` → enviar mensaje + colección
3. **POST** `/reports/{tipo}` → generar documentos

### Stack recomendado:

```
Frontend (React/Vue)
    ↓
FastAPI @ http://100.103.98.125:8080/api/v1
    ↓
├─ Ollama LLM (puerto 11434)
├─ ChromaDB (vector search)
└─ SQLite (metadata)
```

---

## 10. Seguridad & Rate Limiting

⚠️ **Actual**: Sin autenticación ni rate limiting  
📌 **TODO**: Agregar JWT tokens si se expone públicamente

---

## 11. Documentación de API

**Swagger UI**: http://100.103.98.125:8080/docs  
**ReDoc**: http://100.103.98.125:8080/redoc

Ambas muestran:
- ✅ Todos los endpoints
- ✅ Parámetros requeridos/opcionales
- ✅ Esquemas de response
- ✅ Botón "Try it out" para testing interactivo

---

## 12. Resumen de Endpoints

```
┌─────────────────────────────────────────────────┐
│ CHAT RAG (ventana de chat)                      │
├─────────────────────────────────────────────────┤
│ POST /chat                                      │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│ INGESTA                                         │
├─────────────────────────────────────────────────┤
│ POST /ingest/emails                             │
│ POST /ingest/documents                          │
│ POST /ingest/db                                 │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│ IA TOOLS (simulación, clasificación)            │
├─────────────────────────────────────────────────┤
│ POST /simulate/response                         │
│ POST /classify/business                         │
│ POST /classify/phase                            │
│ POST /compare                                   │
│ GET  /models                                    │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│ CRM                                             │
├─────────────────────────────────────────────────┤
│ POST   /crm/deals                               │
│ PATCH  /crm/deals/{id}/phase                    │
│ GET    /crm/deals                               │
│ GET    /crm/deals/search?q=...                  │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│ FINE-TUNING (entrenar modelos)                  │
├─────────────────────────────────────────────────┤
│ POST /finetune/dataset                          │
│ POST /finetune/train                            │
│ GET  /finetune/jobs                             │
│ GET  /finetune/jobs/{id}                        │
│ POST /finetune/export                           │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│ INFORMES (generación automática)                │
├─────────────────────────────────────────────────┤
│ GET    /reports                                 │
│ POST   /reports/procedimientos                  │
│ POST   /reports/negocios                        │
│ POST   /reports/clientes                        │
│ POST   /reports/estrategico                     │
│ POST   /reports/tactico                         │
│ POST   /reports/comunicacion                    │
│ POST   /reports/comercial                       │
│ POST   /reports/puesto_carolina                 │
└─────────────────────────────────────────────────┘
```

---

## 13. Próximas Features

- [ ] Autenticación JWT
- [ ] Rate limiting
- [ ] WebSocket para chat en tiempo real (vs polling)
- [ ] Carga de archivos (PDF, Excel)
- [ ] Exportación de datos (JSON, CSV)
- [ ] Dashboard de métricas
- [ ] Admin panel (gestión de colecciones)

---

**Versión**: 1.0  
**Última actualización**: 18-04-2026  
**Estado**: ✅ Producción  
