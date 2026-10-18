from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException
from app.orchestrator import orchestrator
from app.schemas.models import (
    ScopeOfWork, ClientProposal, ScopeDeltaReport, ProposalApprovalRequest
)
import httpx
from app.core.config import settings

router = APIRouter(prefix="/api/v1", tags=["Meeting to Scope of Work"])

@router.get("/transcripts")
async def list_transcripts():
    """
    Returns available role-played meeting transcripts (Meeting A, B, C).
    """
    return orchestrator.get_transcripts()

@router.post("/transcripts/{meeting_id}/process")
async def process_meeting_transcript(meeting_id: str):
    """
    Runs multi-agent pipeline: Transcript Analyst -> Feasibility (Task 1) -> WBS Estimator -> Scope Architect -> Proposal.
    """
    try:
        return await orchestrator.process_transcript(meeting_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/scope/diff")
async def process_followup_diff(followup_meeting_id: str = "MEETING-C", baseline_project_id: str = "PROJ-MEETING-A"):
    """
    Compares follow-up meeting against baseline SOW. Detects ADDED, MODIFIED, REMOVED, and SCOPE_CREEP_WARNING.
    """
    try:
        return await orchestrator.process_followup_meeting(followup_meeting_id, baseline_project_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/proposals/{proposal_id}/approve")
async def approve_client_proposal(proposal_id: str, request: ProposalApprovalRequest):
    """
    Enforces Human-in-the-Loop review & signoff before proposals reach the client.
    """
    try:
        return orchestrator.approve_proposal(proposal_id, request)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/proposals")
async def list_proposals():
    """
    List all generated client proposals and their current approval status.
    """
    return list(orchestrator.proposals.values())

@router.get("/health")
async def health_check():
    """
    Service health check and Task 1 connectivity check.
    """
    kb_online = False
    try:
        async with httpx.AsyncClient(timeout=1.5) as client:
            r = await client.get(f"{settings.TASK1_API_URL}/health")
            kb_online = (r.status_code == 200)
    except Exception:
        kb_online = False

    return {
        "status": "healthy",
        "service": "Task 3: Meeting to Scope of Work (Python)",
        "task1_knowledge_brain_connected": kb_online,
        "hourly_rate_usd": settings.HOURLY_RATE_USD
    }
