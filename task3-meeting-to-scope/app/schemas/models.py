from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class RequirementItem(BaseModel):
    req_id: str
    description: str
    source_transcript_quote: str
    speaker: str = "Client"
    priority: str = "MUST_HAVE" # MUST_HAVE | SHOULD_HAVE | NICE_TO_HAVE
    feasibility: str = "CUSTOM_DEVELOPMENT" # BUILTIN_SETTING | PARTIAL_SETTING | CUSTOM_DEVELOPMENT | OUT_OF_SCOPE
    feasibility_reason: str = ""
    kb_citation_url: Optional[str] = None
    acceptance_criteria: str = ""
    estimated_hours_likely: float = 0.0

class WBSTask(BaseModel):
    task_id: str
    req_id: Optional[str] = None
    name: str
    category: str # Backend | Frontend | Configuration | QA / Acceptance | Deployment
    optimistic_hours: float
    likely_hours: float
    pessimistic_hours: float
    expected_hours_pert: float
    notes: str = ""

class ScopeOfWork(BaseModel):
    project_id: str
    project_title: str
    executive_summary: str
    client_name: str
    source_meeting: str
    requirements: List[RequirementItem]
    explicit_exclusions: List[str]
    client_responsibilities: List[str]
    wbs_tasks: List[WBSTask]
    total_hours_pert: float
    cost_usd: float
    cost_inr: float
    timeline_weeks: float
    version: int = 1
    created_at: str

class ScopeDeltaItem(BaseModel):
    req_id: str
    type: str # ADDED | MODIFIED | REMOVED | SCOPE_CREEP_WARNING
    description: str
    original_details: Optional[str] = None
    new_details: Optional[str] = None
    impact_hours: float
    notes: str

class ScopeDeltaReport(BaseModel):
    project_id: str
    baseline_meeting: str
    followup_meeting: str
    baseline_version: int
    revised_version: int
    baseline_hours: float
    revised_hours: float
    net_hour_delta: float
    baseline_cost_usd: float
    revised_cost_usd: float
    changes: List[ScopeDeltaItem]
    out_of_scope_warnings: List[str]
    summary_for_client: str

class ClientProposal(BaseModel):
    proposal_id: str
    project_id: str
    title: str
    client_name: str
    version: int
    status: str = "PENDING_APPROVAL" # PENDING_APPROVAL | APPROVED | REJECTED
    executive_summary: str
    deliverables_summary: List[str]
    exclusions: List[str]
    total_estimated_hours: float
    hourly_rate_usd: float
    total_investment_usd: float
    total_investment_inr: float
    timeline_weeks: float
    is_revised_followup: bool = False
    delta_summary: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None

class ProposalApprovalRequest(BaseModel):
    reviewer_name: str = "Lead Tech Consultant"
    notes: Optional[str] = None
    approved: bool = True
