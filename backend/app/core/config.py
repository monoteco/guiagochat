from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"
    chroma_persist_dir: str = "./chroma_db"
    data_dir: str = "./data"
    log_level: str = "INFO"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
