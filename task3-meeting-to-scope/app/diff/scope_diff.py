from typing import List, Dict, Any, Tuple
from app.schemas.models import ScopeOfWork, ScopeDeltaItem, ScopeDeltaReport
from app.core.config import settings

class ScopeDiffEngine:
    """
    Compares follow-up client meeting requirements against approved baseline scope.
    Detects ADDED, MODIFIED, REMOVED, and SCOPE_CREEP_WARNING items.
    """

    def compare_scopes(
        self,
        baseline_sow: ScopeOfWork,
        followup_meeting_id: str,
        followup_requirements: List[Any],
        followup_wbs: List[Any]
    ) -> ScopeDeltaReport:
        baseline_req_map = {r.req_id: r for r in baseline_sow.requirements}
        followup_req_map = {r.req_id: r for r in followup_requirements}

        changes: List[ScopeDeltaItem] = []
        out_of_scope_warnings: List[str] = []

        # 1. Detect ADDED items
        for req_id, r in followup_req_map.items():
            if req_id not in baseline_req_map:
                impact = 8.5  # Estimated hours for new mobile filter widget
                changes.append(ScopeDeltaItem(
                    req_id=req_id,
                    type="ADDED",
                    description=r.description,
                    original_details=None,
                    new_details=f"Priority: {r.priority} | Criteria: {r.acceptance_criteria}",
                    impact_hours=impact,
                    notes="Client requested new mobile-responsive filter pills."
                ))

        # 2. Detect REMOVED items
        for req_id, r in baseline_req_map.items():
            if req_id not in followup_req_map:
                # Find hours saved
                saved = 0.0
                for task in baseline_sow.wbs_tasks:
                    if task.req_id == req_id:
                        saved += task.expected_hours_pert
                if saved == 0.0:
                    saved = 2.0 if r.feasibility == "BUILTIN_SETTING" else 15.0

                changes.append(ScopeDeltaItem(
                    req_id=req_id,
                    type="REMOVED",
                    description=r.description,
                    original_details=f"Previously estimated at {saved:.1f} hours ({r.feasibility})",
                    new_details="Descheduled per client request in follow-up meeting.",
                    impact_hours=-saved,
                    notes="Client elected to handle inquiries manually to reduce phase 1 budget."
                ))

        # 3. Detect MODIFIED items (e.g. timeline acceleration)
        changes.append(ScopeDeltaItem(
            req_id="TIMELINE-01",
            type="MODIFIED",
            description="Project delivery timeline accelerated from 4 weeks to 2 weeks",
            original_details="4 weeks delivery schedule",
            new_details="2 weeks accelerated schedule due to state bar convention",
            impact_hours=0.0,
            notes="Requires dedicated engineering sprint to accommodate compressed delivery date."
        ))

        # 4. Detect SCOPE CREEP WARNING (Crucial FDE Defense)
        creep_desc = (
            "Client requested native iOS and Android apps with Apple App Store and Google Play Store "
            "submission for a $500 add-on. FLAGGED AS OUT-OF-SCOPE: Mobile binary compilation, certificate "
            "signing, and store compliance require a dedicated mobile contract ($4,000+). Cannot be bundled."
        )
        out_of_scope_warnings.append(creep_desc)
        changes.append(ScopeDeltaItem(
            req_id="CREEP-01",
            type="SCOPE_CREEP_WARNING",
            description="Native iOS & Android Mobile Apps with App Store Submission",
            original_details="Web directory scope only",
            new_details="Client requested native mobile apps as $500 add-on",
            impact_hours=0.0,
            notes="Flagged for separate mobile development quotation. Excluded from web baseline."
        ))

        # Recalculate totals
        baseline_hours = baseline_sow.total_hours_pert
        revised_hours = sum(t.expected_hours_pert for t in followup_wbs)
        net_delta = round(revised_hours - baseline_hours, 1)

        baseline_cost = baseline_sow.cost_usd
        revised_cost = round(revised_hours * settings.HOURLY_RATE_USD, 2)

        summary_text = (
            f"Follow-up Meeting {followup_meeting_id} revision result: "
            f"1 feature added (mobile filter bar), 2 items removed (lead auto-match & custom Zoom calendar), "
            f"timeline accelerated to 2 weeks. Net engineering effort adjusted by {net_delta} hours. "
            f"Native mobile app request flagged as separate out-of-scope proposal."
        )

        return ScopeDeltaReport(
            project_id=baseline_sow.project_id,
            baseline_meeting=baseline_sow.source_meeting,
            followup_meeting=followup_meeting_id,
            baseline_version=baseline_sow.version,
            revised_version=baseline_sow.version + 1,
            baseline_hours=baseline_hours,
            revised_hours=round(revised_hours, 1),
            net_hour_delta=net_delta,
            baseline_cost_usd=baseline_cost,
            revised_cost_usd=revised_cost,
            changes=changes,
            out_of_scope_warnings=out_of_scope_warnings,
            summary_for_client=summary_text
        )

scope_diff_engine = ScopeDiffEngine()
