from typing import List
from datetime import datetime, timezone
from app.schemas.models import RequirementItem, WBSTask, ScopeOfWork
from app.core.config import settings

class ScopeArchitectAgent:
    """
    Synthesizes the formal Scope of Work (SOW):
    - Delineates In-Scope vs. Explicit Out-of-Scope Exclusions
    - Establishes acceptance criteria and client prerequisites
    """

    def build_scope_of_work(
        self,
        project_id: str,
        project_title: str,
        client_name: str,
        meeting_id: str,
        requirements: List[RequirementItem],
        wbs_tasks: List[WBSTask],
        version: int = 1
    ) -> ScopeOfWork:
        total_hours = sum(t.expected_hours_pert for t in wbs_tasks)
        cost_usd = round(total_hours * settings.HOURLY_RATE_USD, 2)
        cost_inr = round(cost_usd * settings.USD_TO_INR, 2)

        # Standard Exclusions to eliminate scope creep
        exclusions = [
            "Native mobile app compilation and submission to Apple App Store / Google Play Store.",
            "Third-party API subscription costs (Stripe processing fees, Zapier plan fees, Google Maps API quota).",
            "Custom video streaming or video server hosting infrastructure.",
            "Ongoing manual data entry beyond the agreed initial 450-category CSV import."
        ]

        # Client responsibilities
        client_responsibilities = [
            "Provide production Stripe API keys with administrator access.",
            "Deliver validated CSV file containing specialty categories adhering to standard column templates.",
            "Provide DNS access or configure domain A-records / MX records to designated endpoints.",
            "Participate in user acceptance testing (UAT) signoff within 5 business days of delivery."
        ]

        timeline_weeks = round(max(2.0, total_hours / 18.0), 1)

        summary = (
            f"Implementation scope for {client_name} based on technical discovery ({meeting_id}). "
            f"The project encompasses {len(requirements)} core functional requirements optimized "
            f"for high performance and zero-overhead native product configuration where feasible."
        )

        return ScopeOfWork(
            project_id=project_id,
            project_title=project_title,
            executive_summary=summary,
            client_name=client_name,
            source_meeting=meeting_id,
            requirements=requirements,
            explicit_exclusions=exclusions,
            client_responsibilities=client_responsibilities,
            wbs_tasks=wbs_tasks,
            total_hours_pert=round(total_hours, 1),
            cost_usd=cost_usd,
            cost_inr=cost_inr,
            timeline_weeks=timeline_weeks,
            version=version,
            created_at=datetime.now(timezone.utc).isoformat()
        )

scope_architect = ScopeArchitectAgent()
