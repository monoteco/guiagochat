# Replicate Integration (Deprecated)

## Overview
GuiaGo Chat was previously deployed on **Replicate** as a fine-tuned Mistral-7B model with LoRA adapter.

> **Status**: ⚠️ DEPRECATED - Replaced by Modal.com inference endpoint

## Specifications

### Model
- **Base**: Mistral-7B-Instruct-v0.3
- **Fine-tuning**: LoRA (rank=8, ~27MB adapter)
- **Training Data**: 4,932 email pairs from GuiaGo dataset
- **Purpose**: Customer analysis, document generation, commercial classification

### API Parameters
- **prompt** (string): Question or message to the assistant
- **temperature** (0.1-2.0): Creativity control (default: 0.7)
- **top_p** (0.0-1.0): Nucleus sampling (default: 0.9)
- **max_tokens** (1-2048): Max output tokens (default: 512)

### Pricing
- **A100 GPU**: \.0042/call (~30s response)
- **A40 GPU**: \.0018/call (~60s response)
- **T4 GPU**: \.0060/call (~120s response)

## Migration to Modal.com

The project has migrated from Replicate to **Modal.com** for inference:
- **Endpoint**: \https://hernandogerman--guiago-inference-guiagomodel-chat.modal.run\
- **Model**: Same Mistral-7B + LoRA adapter
- **Timeout**: 300 seconds
- **Max Tokens**: 500 (optimized for speed)
- **Retry Logic**: 3 attempts with exponential backoff

**Reason**: Modal allows running long-running tasks (like \uild_memoria.py\) without overwhelming local servers.

## Legacy Code
The original Replicate implementation files have been archived:
- \cog.yaml\: Cog configuration for Replicate builds
- \predict.py\: Predictor class for Replicate API
- \equirements.txt\: Dependencies for Replicate runtime

See \.backupfiles/\ for historical reference.

## Usage Example (Replicate - Legacy)

\\\python
import replicate

output = replicate.run(
    'monoteco/guiagochat-mistral7b:latest',
    input={
        'prompt': '¿Quiénes son nuestros mejores clientes?',
        'temperature': 0.7,
        'max_tokens': 512,
    }
)
print(output)
\\\

## Current Recommendation
Use **Modal.com** endpoint via \ackend/app/core/llm.py\ for all inference needs.
