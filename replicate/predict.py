# Predictor para GuiaGo Mistral-7B Fine-tuned Model en Replicate
import os
import torch
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
import cog

class Predictor(cog.Predictor):
    def setup(self) -> None:
        # Modelo base
        BASE_MODEL_ID = 'mistralai/Mistral-7B-Instruct-v0.3'
        ADAPTER_PATH = '/src/adapters/mistral7b'
        
        print('[*] Cargando modelo base...')
        
        # Tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            BASE_MODEL_ID,
            trust_remote_code=True,
            padding_side='left'
        )
        
        # Modelo
        self.model = AutoModelForCausalLM.from_pretrained(
            BASE_MODEL_ID,
            torch_dtype=torch.float16,
            device_map='auto',
            trust_remote_code=True,
            load_in_8bit=True,
        )
        
        # LoRA adapter
        if Path(ADAPTER_PATH).exists():
            print('[*] Cargando LoRA...')
            self.model = PeftModel.from_pretrained(
                self.model,
                ADAPTER_PATH,
                is_trainable=False
            )
            self.model = self.model.merge_and_unload()
        
        self.model.eval()
        print('[OK] Modelo listo')

    @cog.input('prompt', type=str)
    @cog.input('temperature', type=float, default=0.7)
    @cog.input('top_p', type=float, default=0.9)
    @cog.input('max_tokens', type=int, default=512)
    def predict(
        self,
        prompt: str,
        temperature: float = 0.7,
        top_p: float = 0.9,
        max_tokens: int = 512,
    ) -> str:
        
        SYSTEM_PROMPT = '''Eres un asistente interno de GuiaGo.
Conoces el historial de correos, clientes y procesos de venta.
Responde en español, de forma profesional y concisa.'''
        
        messages = [
            {'role': 'system', 'content': SYSTEM_PROMPT},
            {'role': 'user', 'content': prompt},
        ]
        
        prompt_text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )
        
        inputs = self.tokenizer(
            prompt_text,
            return_tensors='pt',
            truncation=True,
            max_length=2048,
        ).to(self.model.device)
        
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id,
            )
        
        response = self.tokenizer.decode(
            outputs[0][inputs['input_ids'].shape[-1]:],
            skip_special_tokens=True
        )
        
        return response.strip()
