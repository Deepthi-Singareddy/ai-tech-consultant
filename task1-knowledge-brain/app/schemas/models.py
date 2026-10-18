from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class ImageReference(BaseModel):
    url: str
    alt_text: str = ""
    caption: str = ""
    section_context: str = ""
    visual_description: str = ""

class SourceCitation(BaseModel):
    article_id: str
    title: str
    url: str
    category: str = "General"
    section_heading: Optional[str] = None
    snippet: str
    relevance: float = Field(..., ge=0.0, le=1.0)
    images: List[ImageReference] = []

class QueryRequest(BaseModel):
    query: str = Field(..., min_length=2, description="The customer or system question")
    include_images: bool = Field(True, description="Whether to include relevant screenshots in the response")
    top_k: int = Field(5, ge=1, le=10, description="Max number of source chunks to retrieve")

class QueryResponse(BaseModel):
    query: str
    answer: str
    status: str = Field("answered", description="'answered' | 'insufficient_evidence' | 'escalated'")
    confidence: float = Field(..., ge=0.0, le=1.0)
    sources: List[SourceCitation] = []
    images: List[ImageReference] = []
    needs_escalation: bool = False
    escalation_id: Optional[str] = None
    model_used: str = "claude-3-5-sonnet-20241022"
    latency_ms: float = 0.0

class IngestionRunRequest(BaseModel):
    force_rescrape: bool = False
    max_pages: Optional[int] = None
    sample_only: bool = False

class IngestionStatusResponse(BaseModel):
    status: str
    total_pages_in_sitemap: int
    indexed_articles: int
    added: int
    updated: int
    removed: int
    failed: int
    last_run_timestamp: Optional[str] = None
    resumable_checkpoint_count: int = 0

class EscalationItem(BaseModel):
    id: str
    query: str
    timestamp: str
    reason: str
    status: str = "pending" # pending | resolved
    expert_answer: Optional[str] = None
    resolved_by: Optional[str] = None
    resolved_at: Optional[str] = None

class EscalationResolveRequest(BaseModel):
    expert_answer: str = Field(..., min_length=5, description="Ground truth answer from human expert")
    expert_name: str = "Human Lead Consultant"
    supporting_url: Optional[str] = None

class HealthResponse(BaseModel):
    status: str = "healthy"
    version: str = "1.0.0"
    indexed_documents: int
    indexed_chunks: int
    pending_escalations: int
    model_provider: str
