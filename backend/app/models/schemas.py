from typing import Literal
from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    collection: str = "memoria"


class ChatResponse(BaseModel):
    answer: str
    sources: list[str] = []


class IngestRequest(BaseModel):
    collection: str = "general"


class IngestResponse(BaseModel):
    status: str
    documents_ingested: int


class CRMDeal(BaseModel):
    client_name: str
    email: str = ""
    phase: str = "lead"
    notes: str = ""


class CRMDealResponse(BaseModel):
    id: str
    client_name: str
    email: str
    phase: str
    notes: str


class CRMPhaseUpdate(BaseModel):
    phase: str


# ---------- Simulate / Classify ----------

class SimulateRequest(BaseModel):
    client_email: str
    client_name: str = ""


class SimulateResponse(BaseModel):
    response: str
    sources: list[str] = []


class ClassifyRequest(BaseModel):
    text: str


class ClassifyResponse(BaseModel):
    raw: str
    parsed: dict = {}
    sources: list[str] = []


# ---------- Comparar modelos ----------

class CompareRequest(BaseModel):
    message: str
    collection: str = "emails"
    models: list[str] = []


class ModelResult(BaseModel):
    model: str
    answer: str
    elapsed: float


class CompareResponse(BaseModel):
    results: list[ModelResult]
    sources: list[str] = []


# ---------- Fine-tuning ----------

class FinetuneDatasetResponse(BaseModel):
    status: str
    total: int = 0
    train: int = 0
    val: int = 0
    log: str = ""


class FinetuneTrainRequest(BaseModel):
    model: str  # "llama31" or "mistral7b"


class FinetuneTrainResponse(BaseModel):
    job_id: str
    pid: int
    status: str
    log_path: str = ""


class FinetuneJobStatus(BaseModel):
    job_id: str
    model: str
    pid: int = 0
    status: str
    started_at: str = ""
    log_tail: str = ""
    running: bool = False


class FinetuneExportRequest(BaseModel):
    model: str

# ---------- Informes / Documentos ----------

ReportType = Literal[
    'procedimientos',
    'negocios',
    'clientes',
    'estrategico',
    'tactico',
    'comunicacion',
    'comercial',
    'puesto_carolina',
]


class ReportRequest(BaseModel):
    report_type: ReportType


class ReportResponse(BaseModel):
    report_type: str
    content: str
    sources: list[str] = []
