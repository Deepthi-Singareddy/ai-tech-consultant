from typing import Optional
from app.schemas.models import ScopeOfWork, ClientProposal
from app.core.config import settings

class ProposalExecutiveAgent:
    """
    Compiles client-ready proposals incorporating scope, investment, timeline,
    and governance guardrails.
    """

    def generate_proposal(self, sow: ScopeOfWork, delta_summary: Optional[str] = None) -> ClientProposal:
        proposal_id = f"PROP-{sow.project_id}-V{sow.version}"
        deliverables = [f"{r.req_id}: {r.description} ({r.feasibility})" for r in sow.requirements]

        return ClientProposal(
            proposal_id=proposal_id,
            project_id=sow.project_id,
            title=f"Technical Project Proposal: {sow.project_title}",
            client_name=sow.client_name,
            version=sow.version,
            status="PENDING_APPROVAL",
            executive_summary=sow.executive_summary,
            deliverables_summary=deliverables,
            exclusions=sow.explicit_exclusions,
            total_estimated_hours=sow.total_hours_pert,
            hourly_rate_usd=settings.HOURLY_RATE_USD,
            total_investment_usd=sow.cost_usd,
            total_investment_inr=sow.cost_inr,
            timeline_weeks=sow.timeline_weeks,
            is_revised_followup=(sow.version > 1),
            delta_summary=delta_summary,
            approved_by=None,
            approved_at=None
        )

proposal_executive = ProposalExecutiveAgent()
