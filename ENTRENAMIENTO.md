# GuiaGo Chat - Proceso de Entrenamiento

## Estado actual: FUNCIONANDO en caro

| Componente | Detalle |
|---|---|
| **Modelo** | Meta Llama 3.1 8B Instruct (quantizado Q4_K_M) |
| **Peso del modelo** | 4.9 GB en disco (original FP16 sería ~16 GB) |
| **Formato** | GGUF (via Ollama) |
| **Origen** | HuggingFace: bartowski/Meta-Llama-3.1-8B-Instruct-GGUF |
| **Servidor LLM** | Ollama nativo (CPU-only, sin GPU) |
| **Embeddings** | all-MiniLM-L6-v2 (ChromaDB default, ~80 MB) |
| **Base vectorial** | ChromaDB 1.5.7 persistente |
| **API** | FastAPI en puerto 8080 |
| **Datos ingestados** | 3496 correos de correosGo.db |
| **Velocidad respuesta** | ~1-2 min por pregunta (CPU puro, i9-9980HK) |

---

## Importante: esto NO es fine-tuning

No reentrenamos el modelo Llama. Usamos **RAG** (Retrieval Augmented Generation):
el modelo busca en tus datos y responde basandose en ellos. Esto significa que:

- No necesitas GPU potente
- Puedes actualizar los datos en caliente (sin reentrenar nada)
- El modelo nunca "alucina" con datos que no existen en tu base

---

## Modelo actual: Llama 3.1 8B Instruct Q4_K_M

- **Parametros**: 8 mil millones (8B)
- **Quantización**: Q4_K_M (4 bits, buen balance calidad/tamaño)
- **Tamaño en disco**: 4.9 GB
- **RAM en uso**: ~6-7 GB durante inferencia
- **Contexto**: 4096 tokens (configurable hasta 128K, pero consume más RAM)
- **Idiomas**: Multilingüe (español incluido, aunque mejor en inglés)
- **Velocidad**: ~5-8 tokens/segundo en i9-9980HK (CPU-only)

### Otros modelos candidatos para descargar

| Modelo | Params | Tamaño Q4 | Para qué |
|---|---|---|---|
| **Mistral 7B Instruct v0.3** | 7B | ~4.1 GB | Rápido, buen español |
| **Gemma 2 9B Instruct** | 9B | ~5.4 GB | Muy bueno en razonamiento |
| **Llama 3.1 70B Q2_K** | 70B | ~26 GB | Mucho mejor calidad, cabe en 64GB RAM (ajustado) |
| **Phi-3 Mini 3.8B** | 3.8B | ~2.2 GB | Ultra rápido, para pruebas |
| **Qwen 2.5 7B Instruct** | 7B | ~4.4 GB | Excelente multilingüe |

> Se pueden tener varios modelos instalados a la vez en Ollama.
> Para descargar desde HuggingFace (Cloudflare R2 bloqueado en la oficina):
> `curl -L -o modelo.gguf https://huggingface.co/REPO/resolve/main/ARCHIVO.gguf`
> Luego `ollama create nombre:tag -f Modelfile`

---

## Flujo de datos

```
TUS DATOS (BD, correos, docs)
        |
        v
  [INGESTA] --> trocea textos en chunks de ~3000 chars
        |
        v
  [EMBEDDINGS] --> convierte cada chunk en un vector numerico (all-MiniLM-L6-v2)
        |
        v
  [ChromaDB] --> almacena vectores + texto original (en /home/caro/guiagochat/chroma_db/)
        |
        v
  [CONSULTA] --> usuario pregunta algo
        |
        v
  [BUSQUEDA SEMANTICA] --> encuentra los 5 chunks mas relevantes
        |
        v
  [LLM (Llama 3.1 8B)] --> genera respuesta usando SOLO esos chunks como contexto
```

---

## Fuentes de datos

### 1. correosGo.db (HECHO - 3496 correos indexados)

Base de datos SQLite con correos de GuiaGo. Tabla `correos`:
- Campos: id, mailbox, de, para, cc, asunto, fecha, cuerpo_txt, account, resumen_ia, fase_ia
- Filtro: solo INBOX y Elementos enviados
- Truncado: body a 3000 chars por chunk

```bash
curl -X POST http://caro:8080/api/v1/ingest/db \
  -H 'Content-Type: application/json' \
  -d '{"collection": "emails"}'
```

### 2. BDClientes.db (PENDIENTE - 56 registros)

SQLite con clientes. Schema diferente: remitente, cuerpo, hilo, categoria.
Falta crear loader específico.

### 3. BDPreclientes.db (PENDIENTE - 166 registros)

SQLite con preclientes. Mismo schema que BDClientes.
Falta crear loader específico.

### 4. Documentos de texto (.txt)

Guardar en `data/documents/` y ejecutar:

```bash
curl -X POST http://caro:8080/api/v1/ingest/documents \
  -H 'Content-Type: application/json' -d '{}'
```

### 5. PDFs, Google Sheets, Excel (pendiente de implementar)

---

## Arranque y operación

### Arrancar todo (si caro se reinicia)

```bash
ssh caro@100.103.98.125
bash ~/guiagochat/start.sh
```

### Probar que funciona

```bash
# Health check
curl http://caro:8080/health

# Preguntar algo
curl -X POST http://caro:8080/api/v1/chat \
  -H 'Content-Type: application/json' \
  -d '{"message": "Quien es el cliente que mas correos ha enviado?", "collection": "emails"}'
```

### Ver logs

```bash
tail -f ~/guiagochat/logs/api.log
```

---

## Colecciones en ChromaDB

| Coleccion | Contenido | Estado |
|---|---|---|
| `emails` | 3496 correos de correosGo.db | ACTIVA |
| `general` | Documentos internos, procesos, FAQs | Vacía |
| `crm_deals` | Datos del CRM (clientes + fases) | Vacía |

---

## Pendiente

- [ ] Loaders para BDClientes.db y BDPreclientes.db
- [ ] Systemd service para auto-start al boot de caro
- [ ] Cron de re-ingesta periódica
- [ ] Frontend web
- [ ] Probar modelos adicionales (Mistral, Gemma 2)
- [ ] Evaluar calidad de respuestas y ajustar chunks/overlap

## Cambios (2026-04-14)
- **Modelo actual**: mistral-nemo (7.1GB, 12B params, Spanish-optimized)
