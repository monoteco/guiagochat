from langchain_ollama import ChatOllama
from app.core.config import settings

_instances: dict[str, ChatOllama] = {}


def get_llm(model: str | None = None) -> ChatOllama:
    model = model or settings.ollama_model
    if model not in _instances:
        _instances[model] = ChatOllama(
            base_url=settings.ollama_base_url,
            model=model,
            temperature=0.3,
        )
    return _instances[model]
