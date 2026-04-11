from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    collection: str = "general"


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
