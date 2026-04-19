import json
import requests
from typing import Any, Iterator, List, Optional

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.outputs import ChatGeneration, ChatResult

from app.core.config import settings


class ModalChatModel(BaseChatModel):
    """LangChain-compatible wrapper for the Modal inference endpoint."""

    endpoint_url: str
    max_tokens: int = 1024
    temperature: float = 0.3

    @property
    def _llm_type(self) -> str:
        return "modal_guiago"

    def _convert_messages(self, messages: List[BaseMessage]) -> list:
        result = []
        for msg in messages:
            if isinstance(msg, SystemMessage):
                result.append({"role": "system", "content": msg.content})
            elif isinstance(msg, HumanMessage):
                result.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                result.append({"role": "assistant", "content": msg.content})
        return result

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> ChatResult:
        payload = {
            "messages": self._convert_messages(messages),
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }
        resp = requests.post(
            self.endpoint_url,
            json=payload,
            timeout=120,
        )
        resp.raise_for_status()
        content = resp.json()["content"]
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=content))])


def get_llm(model: str | None = None, num_predict: int = 1024):
    return ModalChatModel(
        endpoint_url=settings.modal_endpoint_url,
        max_tokens=num_predict,
        temperature=0.3,
    )