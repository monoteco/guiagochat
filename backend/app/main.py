import logging
from fastapi import FastAPI
from app.core.config import settings
from app.api.routes import router

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="GuiaGo Chat - Asistente Interno",
    version="0.1.0",
    description="CRM y asistente IA interno de GuiaGo",
)

app.include_router(router, prefix="/api/v1")


@app.get("/health")
def health():
    return {"status": "ok"}
