from fastapi import APIRouter, HTTPException
from app.models.schemas import (
    ChatRequest, ChatResponse,
    IngestRequest, IngestResponse,
    CRMDeal, CRMDealResponse, CRMPhaseUpdate,
)
from app.services.rag_service import query_rag
from app.services.crm_service import create_deal, update_phase, list_deals, search_deals
from app.ingestion.email_loader import ingest_emails
from app.ingestion.document_loader import ingest_documents

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    result = query_rag(req.message, req.collection)
    return ChatResponse(**result)


@router.post("/ingest/emails", response_model=IngestResponse)
def ingest_emails_endpoint(req: IngestRequest):
    count = ingest_emails(req.collection)
    return IngestResponse(status="ok", documents_ingested=count)


@router.post("/ingest/documents", response_model=IngestResponse)
def ingest_docs_endpoint(req: IngestRequest):
    count = ingest_documents(req.collection)
    return IngestResponse(status="ok", documents_ingested=count)


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
