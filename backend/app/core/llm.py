from langchain_ollama import ChatOllama
from app.core.config import settings


def get_llm(model: str | None = None, num_predict: int = 1024):
    """
    Retorna un LLM compatible con LangChain usando Ollama.
    """
    model = model or settings.ollama_model
    return ChatOllama(
        model=model,
        base_url=settings.ollama_base_url,
        num_predict=num_predict,
        temperature=0.3,
    )
