# GuiaGo Chat - Modelo en Replicate

**Modelo Fine-tuned de Mistral-7B para GuiaGo**

## Descripción

Modelo especializado en:
- Análisis de correos históricos
- Respuestas a preguntas sobre clientes
- Generación de documentos profesionales
- Clasificación comercial

## Uso

\\\python
import replicate

output = replicate.run(
    'TU_USERNAME/guiagochat-mistral7b:latest',
    input={
        'prompt': '¿Quiénes son nuestros mejores clientes?',
        'temperature': 0.7,
        'max_tokens': 512,
    }
)
print(output)
\\\

## Parámetros

- **prompt**: Pregunta o mensaje (string)
- **temperature**: 0.1-2.0 (por defecto 0.7)
- **top_p**: 0.0-1.0 (por defecto 0.9)
- **max_tokens**: 1-2048 (por defecto 512)

## Especificaciones Técnicas

- **Modelo base**: Mistral-7B-Instruct-v0.3
- **Fine-tuning**: LoRA (8 rank, 27MB)
- **Dataset**: 4,932 pares (correos GuiaGo)
- **GPU recomendada**: A40 (60s respuesta) o A100 (30s)
- **Costo aprox**: \.0018 USD/llamada (A40)

## Costos

- A100: \.0042/llamada (~30s)
- A40: \.0018/llamada (~60s)
- T4: \.0060/llamada (~120s)
