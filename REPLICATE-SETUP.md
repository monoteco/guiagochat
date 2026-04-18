# Replicate Setup - GuiaGo Chat

## Paso 1: Crear cuenta en Replicate (si no tienes)

1. Ve a https://replicate.com/
2. Haz click en "Sign up" 
3. Usa GitHub OAuth o correo
4. Confirma tu email

## Paso 2: Obtener API Token

1. Ir a https://replicate.com/account/api-tokens
2. Haz click en "Create a new token"
3. Copia el token (comienza con 8_)
4. **Guárdalo en lugar seguro** - no lo compartas

## Paso 3: Configurar .env local

En ~/.env (o .env en raíz del proyecto):

`ash
REPLICATE_API_TOKEN=r8_YOUR_TOKEN_HERE
REPLICATE_MODEL=mistral-community/mistral-7b-instruct-v0.2
`

## Paso 4: Instalar dependencias

`ash
cd ~/guiagochat
source venv/bin/activate
pip install -r backend/requirements.txt
`

## Paso 5: Reiniciar FastAPI

En caro:
`ash
cd ~/guiagochat
bash start.sh
`

Localmente:
`ash
cd c:\...\guiagochat
python -m uvicorn app.main:app --app-dir backend
`

## Verificar que funciona

`ash
curl http://localhost:8080/health
curl -X POST http://localhost:8080/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hola, ¿cómo estás?"}'
`

## Costos en Replicate

- Mistral 7B: ~.00005 / token (input), .00015 / token (output)
- Ejemplo: informe de 1000 tokens ≈ .20
- Presupuesto recomendado: -50/mes para testing

## Modelos alternativos

Si Mistral no funciona bien:
- meta-llama/llama2-70b: .00065 / token
- meta-llama/llama-2-70b-chat: chat-optimized
- openai/gpt-4: mucho más caro

## Troubleshooting

### Error: "API token invalid"
- Verifica que .env esté en la raíz del proyecto
- Revisa que REPLICATE_API_TOKEN comience con 8_
- Token puede haber expirado: genera uno nuevo

### Error: "Model not found"
- Confirma que el modelo existe: https://replicate.com/mistral-community/mistral-7b-instruct-v0.2
- Algunos modelos requieren acceso especial

### Error: "Rate limited"
- Espera 60 segundos
- Sube el presupuesto o reduce concurrencia
