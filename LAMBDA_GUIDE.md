# Lambda Labs Fine-tuning Guide

## Overview
- **Cost**: €3-5 total
- **Time**: ~3-4 hours (including upload/download)
- **Result**: Adapter LoRA (~100MB) that you''ll merge locally with the base model

## PASO 1: Preparar datos (LOCAL)

### 1.1 Generar dataset en caro
```bash
ssh caro@100.103.98.125 ''
  cd ~/guiagochat
  source venv/bin/activate
  python3 finetune/generate_dataset.py
''
# Produces: data/finetune/train.jsonl (2MB) + val.jsonl (250KB)
```

### 1.2 Descargar archivos a tu PC
```bash
# En Windows PowerShell
scp -r caro@100.103.98.125:~/guiagochat/data/finetune .\data\
# O manualmente: SSH → caro → copiar archivos via SCP/WinSCP
```

### 1.3 Crear archivo .tar.gz con dataset
```bash
cd c:\path\to\guiagochat
# En PowerShell (requiere 7-Zip o WSL):
tar -czf guiagochat_dataset.tar.gz data/finetune/ finetune/config_lambda.yaml finetune/train.py
```

---

## PASO 2: Registrarse en Lambda Labs

### 2.1 Crear cuenta
1. Ir a https://lambdalabs.com
2. Crear cuenta gratis (correo + pwd)
3. **Importante**: Añadir método de pago (tarjeta crédito/débito)
   - No se cobra nada hasta que alquiles una máquina
   - El crédito inicial es €0

### 2.2 Generar SSH key (una sola vez)
```bash
# En PowerShell o WSL:
ssh-keygen -t ed25519 -f ~/.ssh/lambda_key -N ""

# Copiar contenido de la clave pública:
cat ~/.ssh/lambda_key.pub
# Salida: ssh-ed25519 AAAAB3NzaC1... user@host
```

### 2.3 Añadir SSH key a Lambda Labs
1. Dashboard → Settings → SSH Keys
2. Paste el contenido de `lambda_key.pub`
3. Nombre: "guiagochat"
4. Save

---

## PASO 3: Alquilar máquina

### 3.1 Elegir instancia
1. Dashboard → "Launch Instance"
2. Seleccionar:
   - **GPU**: RTX 4090 (recomendado) o RTX 6000 ADA
   - **Region**: US (más barato)
   - **OS**: Ubuntu 22.04 LTS
3. Click "Launch" → **Costo: €0.45/hora**

### 3.2 Conectar SSH
```bash
# Lambda Labs muestra la IP de la máquina (ej: 216.105.211.42)
ssh -i ~/.ssh/lambda_key ubuntu@216.105.211.42

# Verifica GPU:
nvidia-smi
# Debe mostrar: RTX 4090 con 24GB VRAM
```

---

## PASO 4: Subir dataset a Lambda Labs

### 4.1 Subir archivo tar.gz (en sesión SSH)
```bash
# Desde tu PC (PowerShell):
scp -i ~/.ssh/lambda_key guiagochat_dataset.tar.gz ubuntu@216.105.211.42:/home/ubuntu/

# En Lambda Labs (en la sesión SSH):
tar -xzf guiagochat_dataset.tar.gz
ls -la data/finetune/
# Debe mostrar: train.jsonl val.jsonl
```

---

## PASO 5: Entrenar modelo

### 5.1 Instalar dependencias (en Lambda Labs)
```bash
# En la sesión SSH de Lambda Labs:
ubuntu@lambda:~$ cd /home/ubuntu
ubuntu@lambda:~$ git clone https://github.com/monoteco/guiagochat.git
ubuntu@lambda:~$ cd guiagochat

# Instalar PyTorch + deps
pip install torch transformers datasets peft trl pyyaml requests huggingface-hub --upgrade

# (Optional) Login a Hugging Face para descargar modelos gated
# huggingface-cli login
# paste token from https://huggingface.co/settings/tokens
```

### 5.2 Lanzar entrenamiento
```bash
# En Lambda Labs SSH:
cd ~/guiagochat
python3 finetune/train.py --model mistral7b --config finetune/config_lambda.yaml

# Expected output:
# Loading base model...
# Applying LoRA adapter...
# Starting training...
#   0%|          | 0/555 [00:00<?, ?it/s]
# 
# Progreso cada few minutos, termina en ~2-3h
```

### 5.3 Monitorear entrenamiento (en otra terminal)
```bash
# En otra ventana terminal (nueva sesión SSH):
ssh -i ~/.ssh/lambda_key ubuntu@216.105.211.42
tail -f ~/guiagochat/logs/train.log
```

---

## PASO 6: Descargar adapter

### 6.1 Esperar a que termine entrenamiento
```bash
# En logs verás:
# Training complete! Adapter saved to: finetune/adapters/mistral7b/
```

### 6.2 Descargar adapter a tu PC
```bash
# En tu PC PowerShell:
mkdir .\finetune_output
scp -i ~/.ssh/lambda_key -r ubuntu@216.105.211.42:/home/ubuntu/guiagochat/finetune/adapters/mistral7b ./finetune_output/

# También descarga el archivo guiago_meta.json
scp -i ~/.ssh/lambda_key ubuntu@216.105.211.42:/home/ubuntu/guiagochat/finetune/adapters/mistral7b/guiago_meta.json ./finetune_output/
```

---

## PASO 7: Apagar máquina Lambda Labs

### 7.1 Terminar instancia (para no seguir gastando)
1. Dashboard → Instances → Tu máquina
2. Click "Terminate" (no se puede recuperar, pero ya descargaste el adapter)
3. **Costo total**: horas_usadas × €0.45

---

## PASO 8: Exportar adapter a GGUF (LOCAL en tu PC)

### 8.1 Preparar ambiente local
```bash
# En tu PC:
cd c:\path\to\guiagochat

# Copiar adapter descargado:
copy .\finetune_output\mistral7b\* .\finetune\adapters\mistral7b\

# Instalar dependencias para merge
pip install peft torch transformers bitsandbytes
```

### 8.2 Convertir a GGUF
```bash
# Si tienes llama.cpp compilado (en caro):
python3 finetune/export_to_ollama.py --model mistral7b

# Si no, usar script simple de merge:
python3 << ''EOF''
from peft import PeftModel, PeftConfig
from transformers import AutoModelForCausalLM, AutoTokenizer

adapter_path = "finetune/adapters/mistral7b"
base_model_id = "mistralai/Mistral-7B-Instruct-v0.3"

config = PeftConfig.from_pretrained(adapter_path)
model = AutoModelForCausalLM.from_pretrained(base_model_id, load_in_8bit=False, device_map="auto")
model = PeftModel.from_pretrained(model, adapter_path)

merged = model.merge_and_unload()
merged.save_pretrained("finetune/merged/mistral7b")

tokenizer = AutoTokenizer.from_pretrained(base_model_id)
tokenizer.save_pretrained("finetune/merged/mistral7b")

print("Merged model saved to finetune/merged/mistral7b/")
EOF''
```

---

## PASO 9: Registrar en Ollama (en caro)

### 9.1 Copiar modelo a caro
```bash
# Desde tu PC:
scp -r c:\path\to\guiagochat\finetune\merged\mistral7b caro@100.103.98.125:~/guiagochat/finetune/merged/

# En caro SSH:
cd ~/guiagochat/finetune/merged/mistral7b

# Crear Modelfile para Ollama:
cat > Modelfile << ''MODELFILE''
FROM mistralai/Mistral-7B-Instruct-v0.3
ADAPTER ./adapter_config.json
ADAPTER ./adapter_model.bin
MODELFILE''

# Registrar en Ollama:
ollama create mistral-guiago -f Modelfile

# Probar:
ollama run mistral-guiago "¿Cuál es la diferencia entre prospecto y cliente?"
```

### 9.2 Configurar API para usar el modelo fine-tuneado
```bash
# En caro, editar .env:
OLLAMA_MODEL=mistral-guiago  # Cambiar de mistral-nemo a mistral-guiago

# Reiniciar API:
pkill -f "uvicorn" || true
cd ~/guiagochat && bash start.sh
```

---

## Resumen de costes

| Paso | Coste |
|------|-------|
| Registro Lambda Labs | €0 |
| Alquilar RTX 4090 × 3.5h | €1.575 |
| Storage temporal | €0 |
| Transferencia de datos | €0 (dentro US) |
| **Total** | **~€1.60** |

Mucho más barato que esperar 61 horas en CPU.

---

## Troubleshooting

### "Out of Memory" en Lambda Labs
- Reduce `batch_size` a 4 en config_lambda.yaml
- Reduce `max_seq_length` a 512

### "CUDA out of memory" durante download de modelo
- Usa bitsandbytes: `load_in_8bit=True` en train.py

### SSH timeout
- En PowerShell: `ssh -o ServerAliveInterval=60 ...`

### Modelo no entrena (loss no baja)
- Aumenta `learning_rate` a 5.0e-4
- Aumenta `num_epochs` a 2-3

---

## Prueba rápida después (RAG)

Una vez registrado en Ollama, testea el modelo:

```bash
# En caro:
curl -X POST http://localhost:8080/query \
  -H "Content-Type: application/json" \
  -d ''{"question": "¿Cuáles son nuestras fases de venta?"}''

# Debe responder usando RAG + modelo fine-tuneado
```

---

**Tiempo total**: ~4-5 horas
**Costo total**: ~€1.60-2
**Resultado**: Modelo fine-tuneado + RAG operativo en caro