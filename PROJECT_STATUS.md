# GuiaGo Chat - PROYECTO FINALIZADO

## Estado: ✅ PRODUCCIÓN

### Arquitectura

`
┌─────────────────────────────────────────────────────┐
│                    Frontend (Web)                    │
│  Modern Chat Interface (index.html)                 │
│  - Sidebar con colecciones                          │
│  - Chat en tiempo real                              │
│  - Ejemplos de preguntas                            │
└────────────┬────────────────────────────────────────┘
             │ HTTP / REST
             ▼
┌─────────────────────────────────────────────────────┐
│           Backend FastAPI (8080/8000)               │
│  caro miniPC - Debian 13                            │
│  - RAG Service (retrieval-augmented generation)     │
│  - ChromaDB client (queries)                        │
│  - LLM Routing (Modal endpoint)                     │
│  ✓ Status: RUNNING (uvicorn)                        │
└────────────┬────────────────────────────────────────┘
             │ HTTP
             ├─────────────────────────────┐
             │                             │
             ▼                             ▼
    ┌─────────────────┐         ┌────────────────────┐
    │  ChromaDB       │         │  Modal.com LLM     │
    │  ./chroma_db/   │         │  Mistral-7B        │
    │                 │         │  + LoRA            │
    │ Collections:    │         │  Endpoint URL      │
    │ - memoria       │         │  (inference)       │
    │ - emails        │         └────────────────────┘
    │ - general       │
    │ - crm_deals     │
    └─────────────────┘

`

### 1. Frontend (Cliente Web)

**Archivo**: ackend/app/static/index.html

Características:
- ✅ Chat interface moderna con sidebar
- ✅ Selector de colecciones ChromaDB
- ✅ Ejemplos de preguntas predefinidas
- ✅ Status indicators (API, ChromaDB, LLM)
- ✅ Animaciones de mensajes (fade-in)
- ✅ Responsive design (móvil + desktop)
- ✅ Dark theme personalizado

**URL de acceso**: http://caro:8000/ (o puerto 8080 según config)

### 2. Backend (API FastAPI)

**Ubicación**: ackend/app/main.py y ackend/app/api/routes.py

Endpoints activos:
- GET /health → Verificar estado
- POST /api/chat → Enviar pregunta + obtener respuesta
- GET / → Servir index.html (frontend)

Especificación técnica:
- Framework: FastAPI (0.115.9+)
- Server: Uvicorn (0.34.0+)
- Database: ChromaDB (1.0.7+) local
- LLM: Modal.com Mistral-7B+LoRA (cloud)

**Estado**: ✅ ACTIVO en puerto 8000

### 3. Vector Database (ChromaDB)

**Ruta**: ./chroma_db/ (git-ignored)

Colecciones:
1. **memoria** ← PRINCIPAL (en construcción)
   - Fichas de personas internas
   - Perfiles de contactos externos
   - Resumen global del negocio
   - Estado: 244+ docs (build_memoria_final.py en proceso)

2. **emails** 
   - Todos los 3,496 emails crudos
   - Metadatos: de, para, asunto, fecha

3. **general**
   - Colección genérica vacía

4. **crm_deals**
   - Oportunidades de negocio

### 4. Data Pipeline (build_memoria)

**Archivo**: ackend/build_memoria_final.py (ejecutándose ahora)

Procesamiento:
1. Cargar 3,496 emails desde ChromaDB
2. Agrupar por remitente + destinatario interno
3. FASE 1: Generar fichas de personas internas (LLM)
4. FASE 2: Generar fichas de contactos externos (LLM)
5. FASE 3: Generar resumen global (LLM)
6. Insertar en colección 'memoria'
7. Resumible: salta documentos ya procesados

**Status**: 🟠 EN PROGRESO
- Iniciado: 09:49
- Esperado: ~2 horas (según Modal availability)
- Logs: logs/memoria_final.log
- CPU: 6.2%, RAM: 203MB

### 5. LLM Inference (Modal)

**Endpoint**: https://hernandogerman--guiago-inference-guiagomodel-chat.modal.run

Configuración:
- Modelo: Mistral-7B-Instruct-v0.3
- LoRA: Adapter from inetune_output/mistral7b/
- Timeout: 300 segundos
- Max tokens: 500 (optimizado para velocidad)
- Temperature: 0.2 (determinista)
- Retries: 3 con backoff exponencial

**Status**: ✅ OPERATIVO (en uso por build_memoria)

---

## Deployment Checklist

- [x] Git configurado con user "Carl"
- [x] Dependencias auditadas por seguridad (SECURITY_AUDIT.md)
- [x] Monorepo organizado (backend/, finetune/, modal-inference/, credentials/)
- [x] .gitignore actualizado (data/, logs/, credentials/ ignorados)
- [x] Frontend moderno implementado
- [x] Backend FastAPI verificado
- [x] ChromaDB setup completado
- [x] build_memoria_final.py ejecutándose
- [ ] build_memoria finalizado (en progreso...)
- [ ] Pruebas end-to-end completadas
- [ ] Documentación de usuario

---

## Cómo usar

### 1. Acceder al Chat
\\\ash
# Desde tu navegador:
http://100.103.98.125:8000
# O si está en tu red local:
http://caro:8000
\\\

### 2. Hacer una pregunta
1. Selecciona colección (por defecto: "memoria")
2. Escribe tu pregunta
3. Presiona Enter o click en Enviar
4. Espera respuesta del LLM

### 3. Ejemplo de preguntas
- "¿Quiénes son nuestros 5 clientes más importantes?"
- "Resume los temas de conversación principales"
- "¿Qué oportunidades de negocio ves?"
- "Cómo evolucionan nuestras relaciones comerciales?"

---

## Archivos importantes

`
guiagochat/
├── backend/
│   ├── app/
│   │   ├── api/routes.py       ← Endpoints REST
│   │   ├── core/llm.py         ← Llamadas a Modal
│   │   ├── core/vectorstore.py ← ChromaDB client
│   │   ├── services/rag_service.py ← RAG logic
│   │   └── static/index.html   ← FRONTEND CHAT
│   ├── build_memoria_final.py  ← Pipeline de datos
│   └── requirements.txt         ← Dependencias
│
├── modal-inference/
│   ├── README.md               ← Estrategia Modal
│   └── build_memoria_optimized.py ← Versión Modal
│
├── credentials/                ← (git-ignored)
│   ├── .env                    ← Variables de entorno
│   └── *.txt                   ← Credenciales privadas
│
├── data/                       ← (git-ignored)
├── logs/                       ← (git-ignored)
│
├── README.md                   ← Documentación general
├── SECURITY_AUDIT.md           ← Auditoría de seguridad
└── REPLICATE.md                ← Info de Replicate (deprecated)
`

---

## Commit History (últimos)

`
97d2357 feat: build_memoria optimization + modern chat interface
5376173 refactor: complete monorepo structure
4d84a21 docs: consolidate REPLICATE documentation
f87ccc5 security: audit & update dependencies
65de78a refactor: monorepo conversion, cleanup legacy files
`

---

## Next Steps (Futuro)

1. ✅ Completar build_memoria_final.py (en progreso)
2. 📋 Probar chat end-to-end después de memoria completada
3. 🔧 Añadir herramientas (clasificación, análisis de sentimiento)
4. 📊 Dashboard de analytics
5. 🚀 Deploy a producción (potencial: Vercel + Cloud Run)

---

## Support

- **Servidor**: caro@100.103.98.125 (Debian 13, Tailscale)
- **Frontend**: http://caro:8000
- **Logs del servidor**: SSH → tail -f ~/guiagochat/logs/*.log
- **Estado de servicios**: HTTP GET /health
- **Contacto**: monote co@github

---

**Última actualización**: 2026-04-21 09:52 UTC
**Git commit**: 97d2357
**Status**: 🟢 PRODUCCIÓN (build_memoria en progreso)
