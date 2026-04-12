from fastapi import APIRouter, HTTPException
from app.models.schemas import (
    ChatRequest, ChatResponse,
    IngestRequest, IngestResponse,
    CRMDeal, CRMDealResponse, CRMPhaseUpdate,
    SimulateRequest, SimulateResponse,
    ClassifyRequest, ClassifyResponse,
    CompareRequest, CompareResponse,
    FinetuneDatasetResponse, FinetuneTrainRequest, FinetuneTrainResponse,
    FinetuneJobStatus, FinetuneExportRequest,
)
from app.services.rag_service import query_rag
from app.services.crm_service import create_deal, update_phase, list_deals, search_deals
from app.services.simulate_service import simulate_response, classify_business, classify_phase
from app.services.compare_service import compare_models, list_available_models
from app.services.finetune_service import (
    generate_dataset, start_training, get_training_status, list_jobs, start_export,
)
from app.ingestion.email_loader import ingest_emails
from app.ingestion.document_loader import ingest_documents
from app.ingestion.db_loader import ingest_db

router = APIRouter()


# ---------- Chat genérico ----------

@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    result = query_rag(req.message, req.collection)
    return ChatResponse(**result)


# ---------- Ingesta ----------

@router.post("/ingest/emails", response_model=IngestResponse)
def ingest_emails_endpoint(req: IngestRequest):
    count = ingest_emails(req.collection)
    return IngestResponse(status="ok", documents_ingested=count)


@router.post("/ingest/documents", response_model=IngestResponse)
def ingest_docs_endpoint(req: IngestRequest):
    count = ingest_documents(req.collection)
    return IngestResponse(status="ok", documents_ingested=count)


@router.post("/ingest/db", response_model=IngestResponse)
def ingest_db_endpoint(req: IngestRequest):
    count = ingest_db(req.collection or "emails")
    return IngestResponse(status="ok", documents_ingested=count)


# ---------- Simular / Clasificar ----------

@router.post("/simulate/response", response_model=SimulateResponse)
def simulate_response_endpoint(req: SimulateRequest):
    result = simulate_response(req.client_email, req.client_name)
    return SimulateResponse(**result)


@router.post("/classify/business", response_model=ClassifyResponse)
def classify_business_endpoint(req: ClassifyRequest):
    result = classify_business(req.text)
    return ClassifyResponse(**result)


@router.post("/classify/phase", response_model=ClassifyResponse)
def classify_phase_endpoint(req: ClassifyRequest):
    result = classify_phase(req.text)
    return ClassifyResponse(**result)


# ---------- Comparar modelos ----------

@router.post("/compare", response_model=CompareResponse)
def compare_endpoint(req: CompareRequest):
    result = compare_models(req.message, req.collection, req.models or None)
    return CompareResponse(**result)


@router.get("/models")
def get_models():
    return {"models": list_available_models()}


# ---------- CRM ----------

@router.post("/crm/deals", response_model=CRMDealResponse)
def create_deal_endpoint(deal: CRMDeal):
    try:
        result = create_deal(deal.client_name, deal.email, deal.phase, deal.notes)
        return CRMDealResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/crm/deals/{deal_id}/phase", response_model=CRMDealResponse)
def update_deal_phase(deal_id: str, update: CRMPhaseUpdate):
    try:
        result = update_phase(deal_id, update.phase)
        return CRMDealResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/crm/deals")
def get_deals(phase: str | None = None):
    return list_deals(phase)


@router.get("/crm/deals/search")
def search_deals_endpoint(q: str):
    return search_deals(q)


# ---------- Fine-tuning ----------

@router.post("/finetune/dataset", response_model=FinetuneDatasetResponse)
def finetune_dataset_endpoint():
    try:
        result = generate_dataset()
        return FinetuneDatasetResponse(**result)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/finetune/train", response_model=FinetuneTrainResponse)
def finetune_train_endpoint(req: FinetuneTrainRequest):
    if req.model not in ("llama31", "mistral7b"):
        raise HTTPException(status_code=400, detail="model must be 'llama31' or 'mistral7b'")
    result = start_training(req.model)
    return FinetuneTrainResponse(**result)


@router.get("/finetune/jobs")
def finetune_jobs_endpoint():
    return list_jobs()


@router.get("/finetune/jobs/{job_id}", response_model=FinetuneJobStatus)
def finetune_job_status_endpoint(job_id: str):
    try:
        result = get_training_status(job_id)
        return FinetuneJobStatus(**result)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/finetune/export")
def finetune_export_endpoint(req: FinetuneExportRequest):
    if req.model not in ("llama31", "mistral7b"):
        raise HTTPException(status_code=400, detail="model must be 'llama31' or 'mistral7b'")
    result = start_export(req.model)
    return result
