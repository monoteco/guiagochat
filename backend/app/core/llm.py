import replicate
import os
from langchain_core.runnables import Runnable
from langchain_core.callbacks import CallbackManagerForLLMRun
from app.core.config import settings


def get_llm(model: str | None = None, num_predict: int = 1024) -> Runnable:
    """
    Retorna un LLM compatible con LangChain que usa Replicate.
    """
    model = model or settings.replicate_model
    return ReplicateTextLLM(model=model, max_tokens=num_predict)


class ReplicateTextLLM(Runnable):
    """Wrapper para usar Replicate como Runnable de LangChain"""
    
    def __init__(self, model: str, max_tokens: int = 1024):
        super().__init__()
        self.model = model
        self.max_tokens = max_tokens
        # Replicate lee REPLICATE_API_TOKEN de env vars automáticamente
        self.api_token = os.getenv("REPLICATE_API_TOKEN") or settings.replicate_api_token
    
    def invoke(self, input_data, config=None) -> str:
        """Llamada síncrona compatible con LangChain"""
        prompt = self._format_input(input_data)
        return self._call_replicate(prompt)
    
    async def ainvoke(self, input_data, config=None) -> str:
        """Llamada asíncrona"""
        prompt = self._format_input(input_data)
        return self._call_replicate(prompt)
    
    def _format_input(self, input_data) -> str:
        """Extrae el prompt del input de LangChain"""
        if isinstance(input_data, dict):
            # Si es dict, usa el primer value (típicamente el prompt)
            values = [v for v in input_data.values() if isinstance(v, str)]
            return values[0] if values else str(input_data)
        return str(input_data)
    
    def _call_replicate(self, prompt: str) -> str:
        """Llamada HTTP a Replicate"""
        try:
            # Replicate client lee REPLICATE_API_TOKEN de env automáticamente
            output = replicate.run(
                self.model,
                input={
                    "prompt": prompt,
                    "max_tokens": self.max_tokens,
                    "temperature": 0.3,
                }
            )
            # Replicate retorna list[str], concatenamos
            if isinstance(output, list):
                return "".join(output)
            return str(output)
        except Exception as e:
            raise RuntimeError(f"Replicate error: {str(e)}")
    
    @property
    def InputType(self):
        return str | dict
    
    @property
    def OutputType(self):
        return str
