"""
GuiaGo - Modal Inference Service
Serves mistralai/Mistral-7B-Instruct-v0.3 + LoRA adapter via HTTP endpoint.

Deploy:  python -m modal deploy modal_guiago.py
Test:    python -m modal run modal_guiago.py
"""

import os
from typing import Optional

import modal
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# App & infrastructure
# ---------------------------------------------------------------------------

app = modal.App("guiago-inference")

# Persistent volume: caches the 14 GB base model so it is not re-downloaded
# on every cold start.
model_cache_vol = modal.Volume.from_name("guiago-model-cache", create_if_missing=True)

BASE_MODEL      = "mistralai/Mistral-7B-Instruct-v0.3"
MODEL_CACHE_DIR = "/model-cache"
ADAPTER_DIR     = "/adapter"

# Container image: Python 3.11 + ML deps + local LoRA adapter baked in
image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "torch>=2.2.0",
        "transformers>=4.40.0",
        "peft>=0.11.0",
        "accelerate>=0.30.0",
        "safetensors>=0.4.3",
        "huggingface-hub>=0.23.0",
        "bitsandbytes>=0.43.0",
        "fastapi[standard]>=0.115.0",
    )
    .add_local_dir(
        local_path="finetune_output/mistral7b",
        remote_path=ADAPTER_DIR,
    )
)


# ---------------------------------------------------------------------------
# Request / response schemas
# ---------------------------------------------------------------------------

class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[Message]
    max_tokens: Optional[int] = 512
    temperature: Optional[float] = 0.3


class ChatResponse(BaseModel):
    content: str


# ---------------------------------------------------------------------------
# Inference class
# ---------------------------------------------------------------------------

@app.cls(
    gpu="A10G",
    image=image,
    volumes={MODEL_CACHE_DIR: model_cache_vol},
    secrets=[modal.Secret.from_name("huggingface-token")],
    timeout=600,
    scaledown_window=300,

)
@modal.concurrent(max_inputs=4)
class GuiaGoModel:

    @modal.enter()
    def load_model(self):
        import torch
        from peft import PeftModel
        from transformers import AutoModelForCausalLM, AutoTokenizer

        hf_token = os.environ.get("HF_TOKEN")

        print(f"Loading tokenizer from {BASE_MODEL}...")
        self.tokenizer = AutoTokenizer.from_pretrained(
            BASE_MODEL,
            cache_dir=MODEL_CACHE_DIR,
            token=hf_token,
        )
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        print("Loading base model (first run downloads ~14 GB, then cached)...")
        base_model = AutoModelForCausalLM.from_pretrained(
            BASE_MODEL,
            cache_dir=MODEL_CACHE_DIR,
            token=hf_token,
            torch_dtype=torch.float16,
            device_map="auto",
        )

        print("Applying LoRA adapter from", ADAPTER_DIR)
        self.model = PeftModel.from_pretrained(base_model, ADAPTER_DIR)
        self.model.eval()

        model_cache_vol.commit()
        print("Model ready!")

    @modal.fastapi_endpoint(method="POST")
    def chat(self, request: ChatRequest) -> ChatResponse:
        import torch

        prompt = self._build_prompt(request.messages)

        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=3000,
        ).to("cuda")

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=request.max_tokens,
                temperature=request.temperature,
                do_sample=(request.temperature > 0),
                pad_token_id=self.tokenizer.eos_token_id,
                repetition_penalty=1.1,
            )

        new_tokens = outputs[0][inputs["input_ids"].shape[1]:]
        response_text = self.tokenizer.decode(new_tokens, skip_special_tokens=True)

        return ChatResponse(content=response_text.strip())

    def _build_prompt(self, messages: list[Message]) -> str:
        system_content = ""
        turns = []

        for msg in messages:
            if msg.role == "system":
                system_content = msg.content
            else:
                turns.append(msg)

        parts = []
        for i, msg in enumerate(turns):
            if msg.role == "user":
                text = msg.content
                if i == 0 and system_content:
                    text = f"{system_content}\n\n{text}"
                parts.append(f"<s>[INST] {text} [/INST]")
            elif msg.role == "assistant":
                parts.append(f" {msg.content} </s>")

        return "".join(parts)


# ---------------------------------------------------------------------------
# Local entrypoint for quick test
# ---------------------------------------------------------------------------

@app.local_entrypoint()
def main():
    model = GuiaGoModel()
    req = ChatRequest(
        messages=[
            Message(role="system", content="Eres GuiaGo, asistente interno de gestion."),
            Message(role="user",   content="Cuales son las fases del proceso de produccion?"),
        ]
    )
    resp = model.chat.remote(req)
    print("Respuesta:", resp.content)
