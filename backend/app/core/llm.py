from langchain_ollama import ChatOllama
from app.core.config import settings


def get_llm(model: str | None = None, num_predict: int = 512) -> ChatOllama:
    model = model or settings.ollama_model
    return ChatOllama(
        base_url=settings.ollama_base_url,
        model=model,
        temperature=0.3,
        num_predict=num_predict,
    )
