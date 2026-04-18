# Guía Paso a Paso: Subir a Replicate

## ANTES DE EMPEZAR

✅ Verificar que tienes:
- Docker instalado (https://www.docker.com/products/docker-desktop)
- Python 3.11+
- Carpeta adapters en: c:\Users\germa\Downloads\development\GuiaGo\guiagochat\finetune_output\mistral7b\

---

## PASO 1: Crear cuenta en Replicate (5 min)

1. Abre: https://replicate.com/signin
2. Haz clic en "Sign up"
3. Elige: GitHub, Google, o Email
4. Completa los datos
5. Verifica tu email

---

## PASO 2: Obtener API Token (2 min)

1. Logeate en: https://replicate.com
2. Ve a: https://replicate.com/account/api-tokens
3. Haz clic en "Create token"
4. Copia el token (ejemplo: r8_abc123xyz...)

✅ IMPORTANTE: Guarda este token en un lugar seguro (password manager)

---

## PASO 3: Instalar Cog (herramienta de Replicate)

En PowerShell (como admin):

\\\powershell
# Instalar pip si no lo tienes
python -m pip install --upgrade pip

# Instalar Cog
pip install cog

# Verificar
cog --version
\\\

Espera a que termine (2-3 minutos).

---

## PASO 4: Copiar adaptador a la carpeta replicate

En PowerShell:

\\\powershell
cd c:\Users\germa\Downloads\development\GuiaGo\guiagochat\replicate

# Copiar los archivos del adapter
Copy-Item "..\finetune_output\mistral7b" -Destination "adapters\mistral7b" -Recurse -Force

# Verificar
ls adapters\mistral7b
# Debería ver: adapter_config.json, adapter_model.bin, README.md, ...
\\\

---

## PASO 5: Build local (opcional, para probar)

En PowerShell:

\\\powershell
cd c:\Users\germa\Downloads\development\GuiaGo\guiagochat\replicate

# Build (esto descarga las librerías y prepara el contenedor)
cog build

# Tarda 10-15 minutos la primera vez...
\\\

Si funciona, verás:
\\\
Successfully built model
\\\

---

## PASO 6: Crear repositorio en Replicate

En navegador:

1. Abre: https://replicate.com/create
2. Completa:
   - **Model name**: guiagochat-mistral7b
   - **Description**: Fine-tuned Mistral 7B for GuiaGo internal assistant
   - **Visibility**: Private
3. Haz clic en "Create model"

Verás la URL de tu modelo:
\\\
https://replicate.com/TU_USERNAME/guiagochat-mistral7b
\\\

Copia este username.

---

## PASO 7: Logearse en Cog

En PowerShell:

\\\powershell
cog login

# Te pedirá el API token que copiaste antes
# Pégalo aquí:
\\\

Si funciona:
\\\
Authenticated successfully
\\\

---

## PASO 8: PUSH del modelo a Replicate

En PowerShell, desde la carpeta replicate:

\\\powershell
cd c:\Users\germa\Downloads\development\GuiaGo\guiagochat\replicate

cog push r8.io/TU_USERNAME/guiagochat-mistral7b
\\\

Reemplaza TU_USERNAME con tu usuario de Replicate.

⏱️ Toma 15-30 minutos (comprime y sube los archivos a internet)

Durante el proceso verás:
\\\
[1/4] Building model...
[2/4] Uploading...
[3/4] Publishing...
[4/4] Done!
\\\

Si ve errores en "Cog login", prueba esto:

\\\powershell
cog login --token r8_abc123xyz...
\\\

---

## PASO 9: Probar el modelo

Una vez subido (espera a que Replicate termine el procesamiento, ~5 min):

1. Abre tu modelo: https://replicate.com/TU_USERNAME/guiagochat-mistral7b
2. Haz clic en "Run"
3. En el formulario:
   - **prompt**: "¿Quiénes son nuestros mejores clientes?"
   - **temperature**: 0.7
   - **max_tokens**: 512
4. Haz clic en "Run predictions"

⏱️ Espera ~60 segundos en GPU A40 (por defecto)

---

## PASO 10: Ver API key y costos

Para usar vía API:

En tu modelo (https://replicate.com/TU_USERNAME/guiagochat-mistral7b):
- Haz clic en "API"
- Verás ejemplos de curl y Python
- Copia la URL del modelo

Para ver costos:

https://replicate.com/account/api-tokens
- Scrollea hasta "Usage"
- Verás total de llamadas y gasto

---

## PASO 11: Usar el modelo vía API (Python)

\\\python
import replicate

# Instala primero:
# pip install replicate

output = replicate.run(
    'TU_USERNAME/guiagochat-mistral7b:latest',
    input={
        'prompt': '¿Qué servicios vende GuiaGo?',
        'temperature': 0.7,
        'max_tokens': 512,
    },
    api_token='r8_abc123xyz...'  # Tu token de Replicate
)

print(output)
\\\

---

## PASO 12: Integrar en tu FastAPI (backend)

En backend/app/services/ crea un archivo nuevo: replicate_service.py

\\\python
import replicate
import os

REPLICATE_TOKEN = os.environ.get('REPLICATE_API_TOKEN')
MODEL_NAME = 'TU_USERNAME/guiagochat-mistral7b:latest'

def query_replicate(prompt: str, temperature: float = 0.7) -> str:
    output = replicate.run(
        MODEL_NAME,
        input={
            'prompt': prompt,
            'temperature': temperature,
            'max_tokens': 512,
        },
        api_token=REPLICATE_TOKEN
    )
    return output
\\\

Luego en routes.py:

\\\python
@router.post('/chat/replicate')
def chat_replicate(req: ChatRequest):
    response = query_replicate(req.message)
    return ChatResponse(
        message=req.message,
        response=response,
        model='mistral-guiago:replicate'
    )
\\\

---

## TROUBLESHOOTING

| Error | Solución |
|-------|----------|
| "Docker not running" | Inicia Docker Desktop |
| "cog: command not found" | Reinstala: pip install cog |
| "Authentication failed" | Verifica el token en https://replicate.com/account/api-tokens |
| "Model not found" | Espera 5-10 min después de push (Replicate procesa) |
| "Timeout" | Usa GPU A100 (más rápido) en lugar de T4 |

---

## COSTOS ESTIMADOS

Usando **A40** (por defecto):

| Caso | Llamadas/mes | Costo/mes |
|------|-------------|----------|
| Prototipo | 10 | .02 |
| Testing | 100 | .18 |
| Producción ligera | 1,000 | .80 |
| Producción media | 10,000 |  |
| Producción alta | 100,000 |  |

Para cambiar a GPU diferente, edita cog.yaml:

\\\yaml
build:
  gpu: "a100"  # o "t4", "v100"
\\\

Luego: \cog push ...\

---

## PRÓXIMOS PASOS

✅ Modelo subido a Replicate  
→ Probar API desde Python o curl  
→ Integrar en FastAPI (crear endpoint /chat/replicate)  
→ Monitorear costos semanales  
→ Opcional: Frontend que llame a Replicate

---

**¡Listo! Tu modelo está en la nube y listo para escalar.** 🚀
