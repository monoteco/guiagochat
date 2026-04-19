from pathlib import Path
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent

# Cargar .env desde el home directory primero
load_dotenv(Path.home() / ".env")
# Luego desde la raíz del proyecto si existe
load_dotenv(_PROJECT_ROOT / ".env")


class Settings(BaseSettings):
    # Modal inference endpoint
    modal_endpoint_url: str = "https://hernandogerman--guiago-inference-guiagomodel-chat.modal.run"

    # Ollama LLM (fallback local)
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "mistral-guiago:7b-q4_K_M"

    # ChromaDB & Datos
    chroma_persist_dir: str = "./chroma_db"
    data_dir: str = "./data"

    # API
    log_level: str = "INFO"
    api_host: str = "0.0.0.0"
    api_port: int = 8080

    model_config = {"env_file": str(_PROJECT_ROOT / ".env"), "extra": "ignore"}


settings = Settings()

