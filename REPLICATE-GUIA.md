# GUÍA: Subir tu modelo GuiaGo a Replicate

## PASO 1: Registrarse en Replicate
1. Abre: https://replicate.com/signin
2. Haz clic en "Sign up"
3. Elige opción: GitHub, Google, o email
4. Completa el registro

## PASO 2: Obtener tu API Token
1. Abre: https://replicate.com/account/api-tokens
2. Haz clic en "Create token"
3. Copias el token (algo como: r8_abc123xyz...)
4. **GUARDA ESTE TOKEN EN UN LUGAR SEGURO** (no lo commitees a git)

## PASO 3: Instalar Cog (herramienta de Replicate)

En PowerShell:
`powershell
# Instalar Docker primero (si no lo tienes)
# https://www.docker.com/products/docker-desktop

# Luego instalar Cog
pip install cog
`

Verifica:
`powershell
cog --version
`

## PASO 4: Preparar los archivos del modelo

YA ESTÁN LISTOS en la carpeta: replicate/

## PASO 5: Configurar repositorio en Replicate

En navegador:
1. Abre: https://replicate.com/create
2. Completa:
   - **Model name**: guiagochat-mistral7b
   - **Description**: Fine-tuned Mistral 7B for GuiaGo internal assistant
   - **Visibility**: Private (si es confidencial)
3. Haz clic en "Create model"

Copias la URL, algo como:
   https://replicate.com/TU_USERNAME/guiagochat-mistral7b

## PASO 6: Pushear el modelo desde terminal

En PowerShell (desde la raíz del proyecto):

`powershell
cd replicate/

# Login a Replicate (primera vez)
cog login
# Te pedirá el API token, lo pegas

# Push del modelo
cog push r8.io/TU_USERNAME/guiagochat-mistral7b
`

⏱️ **Toma ~10 minutos** (comprime y sube los archivos)

## PASO 7: Probar el modelo desde Swagger

1. Abre: https://replicate.com/TU_USERNAME/guiagochat-mistral7b
2. Haz clic en "Run"
3. Llena el formulario:
   - **prompt**: "¿Quiénes son nuestros mejores clientes?"
   - **temperature**: 0.7
4. Haz clic en "Run predictions"

## PASO 8: Ver costos

En: https://replicate.com/account/api-tokens
- Scrollea hasta "Usage"
- Verás: llamadas, GPU time, costo total

O desde código:
`python
import replicate

predictions = replicate.paginate(
    "list",
    limit=100,  # últimas 100 llamadas
)

total_cost = 0
for pred in predictions:
    total_cost += pred.metrics.predict_time * PRECIO_GPU
`

## PASO 9: Usar el modelo vía API

`python
import replicate

output = replicate.run(
    "TU_USERNAME/guiagochat-mistral7b:latest",
    input={
        "prompt": "¿Quiénes son nuestros clientes principales?",
        "temperature": 0.7,
    }
)

print(output)  # respuesta del modelo
`

O vía curl:

`ash
curl -X POST https://api.replicate.com/v1/predictions \
  -H "Authorization: Token r8_abc123xyz..." \
  -H "Content-Type: application/json" \
  -d '{
    "version": "URL_VERSION_DEL_MODELO",
    "input": {
      "prompt": "¿Quiénes son nuestros clientes?",
      "temperature": 0.7
    }
  }'
`

---

## TROUBLESHOOTING

**Error: "Docker not running"**
→ Inicia Docker Desktop

**Error: "cog login failed"**
→ Verifica que el token sea correcto en: https://replicate.com/account/api-tokens

**Error: "Model not found"**
→ Asegúrate de que el username sea correcto

**Tarifa muy alta**
→ Considera cambiar a GPU T4 (más barato, más lento)
   Edita cog.yaml: gpu: true → gpu: "t4"

---

## PRECIOS (ACTUALIZADO ABRIL 2026)

| GPU | Precio/seg | Tiempo típico | Costo/llamada |
|-----|-----------|---------------|---------------|
| A100 | .00014 | 30s | .0042 |
| A40 | .00003 | 60s | .0018 |
| T4 | .00005 | 120s | .0060 |
| CPU | .00001 | 300s | .0030 |

**Recomendación**: A40 (mejor balance)

---

## PRÓXIMOS PASOS DESPUÉS

1. ✅ Subir a Replicate
2. Integrar en tu frontend (Next.js, React, etc.)
3. Monitorear costos semanales
4. Opcional: Crear endpoint proxy en tu FastAPI que llame a Replicate (en lugar de local)

