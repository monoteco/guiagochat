# GuiaGo Chat - Proceso de Entrenamiento

## Importante: esto NO es fine-tuning

No reentrenamos el modelo Llama. Usamos **RAG** (Retrieval Augmented Generation):
el modelo busca en tus datos y responde basandose en ellos. Esto significa que:

- No necesitas GPU potente
- Puedes actualizar los datos en caliente (sin reentrenar nada)
- El modelo nunca "alucina" con datos que no existen en tu base

---

## Flujo de datos

```
TUS DATOS (BD, correos, docs)
        |
        v
  [INGESTA] --> trocea textos en chunks de ~1000 chars
        |
        v
  [EMBEDDINGS] --> convierte cada chunk en un vector numerico
        |
        v
  [ChromaDB] --> almacena vectores + texto original
        |
        v
  [CONSULTA] --> usuario pregunta algo
        |
        v
  [BUSQUEDA SEMANTICA] --> encuentra los 5 chunks mas relevantes
        |
        v
  [LLM (Llama 3.1)] --> genera respuesta usando SOLO esos chunks como contexto
```

---

## Fuentes de datos soportadas

### 1. Base de datos (SQL / PostgreSQL / MySQL / SQLite)

**Tu nos dices donde esta la BD** y creamos un conector que:
- Se conecta a la BD
- Extrae registros relevantes (clientes, ventas, fases, historico)
- Los convierte en documentos de texto
- Los indexa en ChromaDB

Ejemplo de lo que extraeria:

```
Cliente: Hotel Miramar
Email: info@miramar.com
Fecha alta: 2024-03-15
Fase actual: produccion
Producto: Tour privado Barcelona x20 pax
Notas: Confirmado para junio, pendiente transfer aeropuerto
Historico: lead(mar) -> contactado(mar) -> propuesta(abr) -> cerrado(may) -> produccion(may)
```

**Que necesito de ti:**
- Tipo de BD (PostgreSQL, MySQL, SQLite, MongoDB, Google Sheets...)
- Host/IP y puerto (o ruta del archivo si es SQLite)
- Nombre de la BD
- Usuario y contrasena de lectura
- Tablas principales (clientes, ventas, productos, etc.)

### 2. Correos electronicos (.eml)

- Exporta correos desde Gmail/Outlook en formato .eml
- Copialos a `data/emails/` en el miniPC
- Ejecuta la ingesta:

```bash
curl -X POST http://localhost:8000/api/v1/ingest/emails \
  -H 'Content-Type: application/json' -d '{}'
```

### 3. Documentos de texto (.txt)

Cualquier documento interno: procesos, guias, plantillas de respuesta, FAQs:

- Guardalos como .txt en `data/documents/`
- Ejecuta:

```bash
curl -X POST http://localhost:8000/api/v1/ingest/documents \
  -H 'Content-Type: application/json' -d '{}'
```

### 4. PDFs (pendiente de implementar)

Se anadira un loader de PDFs con PyMuPDF.

### 5. Google Sheets / Excel (pendiente de implementar)

Si el CRM esta en Sheets o Excel, se hara un conector especifico.

---

## Proceso paso a paso

### Paso 1: Identificar las fuentes de datos
Dime donde esta tu BD y que tablas tienen la info de:
- Clientes (nombre, email, telefono)
- Ventas/deals (producto, precio, fecha, fase)
- Historico de fases (cuando cambio cada deal de fase)
- Correos importantes (o exporta .eml)

### Paso 2: Crear el conector de BD
Creo un script `backend/app/ingestion/db_loader.py` que:
1. Se conecta a tu BD
2. Lee las tablas que nos digas
3. Genera documentos con el contexto completo de cada cliente/venta
4. Los indexa en ChromaDB

### Paso 3: Ingesta inicial
Ejecutamos la ingesta de todos los datos existentes. Esto puede tardar
unos minutos dependiendo del volumen.

### Paso 4: Ingesta periodica (cron)
Configuramos un cron job en el miniPC que re-indexe los datos
cada X horas para mantener todo actualizado:

```bash
# Ejemplo: cada 2 horas
0 */2 * * * curl -s -X POST http://localhost:8000/api/v1/ingest/db > /dev/null
```

### Paso 5: Probar consultas
```bash
# Preguntar por un cliente
curl -X POST http://localhost:8000/api/v1/chat \
  -H 'Content-Type: application/json' \
  -d '{"message": "En que fase esta el Hotel Miramar?"}'

# Pedir sugerencia de respuesta a un correo
curl -X POST http://localhost:8000/api/v1/chat \
  -H 'Content-Type: application/json' \
  -d '{"message": "El cliente Hotel Playa pide cambiar la fecha del tour. Sugiere una respuesta.", "collection": "emails"}'

# Consultar pipeline de ventas
curl -X POST http://localhost:8000/api/v1/chat \
  -H 'Content-Type: application/json' \
  -d '{"message": "Cuantos deals hay en fase de negociacion?"}'
```

---

## Colecciones en ChromaDB

Los datos se organizan en colecciones separadas:

| Coleccion     | Contenido                          |
|---------------|-------------------------------------|
| `general`   | Documentos internos, procesos, FAQs |
| `emails`    | Correos electronicos indexados       |
| `crm_deals` | Datos del CRM (clientes + fases)     |
| `db_sync`   | Datos sincronizados de tu BD         |

Puedes consultar una coleccion especifica o todas a la vez.

---

## Actualizacion de datos

| Metodo            | Frecuencia      | Como                              |
|-------------------|-----------------|-----------------------------------|
| Manual            | Cuando quieras  | `curl POST /ingest/...`         |
| Cron automatico   | Cada 2h (o lo que digas) | crontab en el miniPC     |
| Webhook           | Tiempo real     | Se puede conectar a tu sistema    |

---

## Metricas de calidad

Despues de la ingesta, podemos verificar:
- Numero de documentos indexados por coleccion
- Probar consultas de ejemplo y evaluar las respuestas
- Ajustar el tamano de chunk y overlap si las respuestas son imprecisas
- Cambiar el numero de chunks recuperados (actualmente 5)

---

## Siguiente paso

**Dime donde esta la BD de GuiaGo** (tipo, host, tablas principales)
y creo el conector `db_loader.py` para empezar la ingesta real.
