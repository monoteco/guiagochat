from pathlib import Path
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent

# Load .env from home directory first
load_dotenv(Path.home() / ".env")
# Then load from project root if it exists
load_dotenv(_PROJECT_ROOT / ".env")


class Settings(BaseSettings):
    # Replicate LLM - usar modelo fine-tuned o público
    replicate_api_token: str = ""  # Se define en .env como r8_xxxxx
    replicate_model: str = "mistral-community/mistral-7b-instruct-v0.2"
    
    # ChromaDB & Datos
    chroma_persist_dir: str = "./chroma_db"
    data_dir: str = "./data"
    
    # API
    log_level: str = "INFO"
    api_host: str = "0.0.0.0"
    api_port: int = 8080

    model_config = {"env_file": str(_PROJECT_ROOT / ".env"), "extra": "ignore"}


settings = Settings()
