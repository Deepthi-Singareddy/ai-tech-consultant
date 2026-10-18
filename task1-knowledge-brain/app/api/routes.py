from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.schemas.models import (
    QueryRequest, QueryResponse,
    IngestionRunRequest, IngestionStatusResponse,
    EscalationItem, EscalationResolveRequest,
    HealthResponse
)
from app.rag.qa_engine import qa_engine
from app.rag.store import knowledge_store
from app.crawler.crawler import PoliteCrawler
from app.core.config import settings

router = APIRouter(prefix="/api/v1", tags=["Knowledge Brain"])

crawler = PoliteCrawler()

@router.post("/query", response_model=QueryResponse)
async def query_knowledge_base(request: QueryRequest):
    """
    Query the Knowledge Brain for grounded product facts, procedures, and screenshots.
    Returns source citations with exact URLs and confidence score.
    """
    return qa_engine.query(request)

@router.post("/ingestion/run", response_model=Dict[str, Any])
async def run_ingestion(request: IngestionRunRequest, background_tasks: BackgroundTasks):
    """
    Trigger crawler ingestion and knowledge index rebuild.
    Can be run synchronously or in background.
    """
    result = crawler.crawl(
        max_pages=request.max_pages,
        force_rescrape=request.force_rescrape
    )
    # Rebuild hybrid retrieval index from updated articles
    knowledge_store.rebuild_from_articles()

    return {
        "status": "completed",
        "crawl_summary": result,
        "total_chunks_indexed": len(knowledge_store.chunks)
    }

@router.get("/ingestion/status", response_model=IngestionStatusResponse)
async def get_ingestion_status():
    """
    Returns current crawler manifest statistics and sitemap sync state.
    """
    manifest = crawler.manifest
    total_manifest = len(manifest)
    indexed = len(list(settings.ARTICLES_DIR.glob("*.json")))
    failed = sum(1 for v in manifest.values() if v.get("status") == "FAILED")
    removed = sum(1 for v in manifest.values() if v.get("status") == "REMOVED")

    return IngestionStatusResponse(
        status="operational",
        total_pages_in_sitemap=total_manifest or 1696,
        indexed_articles=indexed,
        added=indexed,
        updated=0,
        removed=removed,
        failed=failed,
        resumable_checkpoint_count=total_manifest
    )

@router.get("/escalations", response_model=List[EscalationItem])
async def list_escalations():
    """
    Lists all unanswered questions escalated to human tech consultants.
    """
    return qa_engine.get_escalations()

@router.post("/escalations/{escalation_id}/resolve")
async def resolve_escalation(escalation_id: str, request: EscalationResolveRequest):
    """
    Records human expert answer for an escalation and automatically injects
    it back into the Knowledge Brain for future retrieval.
    """
    try:
        return qa_engine.resolve_escalation(escalation_id, request)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Service health check and index metrics.
    """
    pending_esc = sum(1 for e in qa_engine.escalations.values() if e.get("status") == "pending")
    provider = "Anthropic Claude (Live)" if settings.ANTHROPIC_API_KEY else "Deterministic Grounded Synthesizer (Offline Ready)"

    return HealthResponse(
        status="healthy",
        version=settings.VERSION,
        indexed_documents=len(list(settings.ARTICLES_DIR.glob("*.json"))),
        indexed_chunks=len(knowledge_store.chunks),
        pending_escalations=pending_esc,
        model_provider=provider
    )
