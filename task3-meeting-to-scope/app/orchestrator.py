import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

from app.agents.transcript_analyst import transcript_analyst
from app.agents.feasibility_agent import feasibility_agent
from app.agents.estimation_engineer import estimation_engineer
from app.agents.scope_architect import scope_architect
from app.agents.proposal_executive import proposal_executive
from app.diff.scope_diff import scope_diff_engine
from app.schemas.models import ScopeOfWork, ClientProposal, ScopeDeltaReport, ProposalApprovalRequest

class MultiAgentScopeOrchestrator:
    """
    Coordinates multi-agent execution pipeline:
    Transcript Analyst -> Feasibility (Task 1) -> WBS Estimator -> Scope Architect -> Proposal Executive -> Diff Engine
    """

    def __init__(self):
        self.transcripts_file = Path(__file__).parent / "transcripts" / "transcripts.json"
        self.projects: Dict[str, ScopeOfWork] = {}
        self.proposals: Dict[str, ClientProposal] = {}
        self.diff_reports: Dict[str, ScopeDeltaReport] = {}
        self._load_transcripts()

    def _load_transcripts(self) -> List[Dict[str, Any]]:
        if self.transcripts_file.exists():
            with open(self.transcripts_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

    def get_transcripts(self) -> List[Dict[str, Any]]:
        return self._load_transcripts()

    async def process_transcript(self, meeting_id: str) -> Dict[str, Any]:
        transcripts = self._load_transcripts()
        matched = next((t for t in transcripts if t["id"] == meeting_id), None)
        if not matched:
            raise KeyError(f"Meeting {meeting_id} not found")

        transcript_text = matched["transcript"]
        client_name = matched["client_name"]
        project_title = matched["title"]
        project_id = f"PROJ-{meeting_id}"

        # 1. Transcript Analyst Agent
        raw_reqs = transcript_analyst.analyze_transcript(transcript_text, meeting_id)

        # 2. Product Feasibility Agent (calls Task 1 API)
        evaluated_reqs = []
        for r in raw_reqs:
            evaluated = await feasibility_agent.evaluate_feasibility(r)
            evaluated_reqs.append(evaluated)

        # 3. Estimation Engineer Agent (3-point PERT WBS)
        wbs_tasks = estimation_engineer.generate_wbs(evaluated_reqs)

        # 4. Scope Architect Agent
        sow = scope_architect.build_scope_of_work(
            project_id=project_id,
            project_title=project_title,
            client_name=client_name,
            meeting_id=meeting_id,
            requirements=evaluated_reqs,
            wbs_tasks=wbs_tasks,
            version=1
        )
        self.projects[project_id] = sow

        # 5. Proposal Executive Agent
        proposal = proposal_executive.generate_proposal(sow)
        self.proposals[proposal.proposal_id] = proposal

        return {
            "project_id": project_id,
            "scope_of_work": sow,
            "proposal": proposal
        }

    async def process_followup_meeting(self, followup_meeting_id: str, baseline_project_id: str) -> Dict[str, Any]:
        if baseline_project_id not in self.projects:
            # Process baseline first if not in memory
            await self.process_transcript("MEETING-A")

        baseline_sow = self.projects[baseline_project_id]

        transcripts = self._load_transcripts()
        matched = next((t for t in transcripts if t["id"] == followup_meeting_id), None)
        if not matched:
            raise KeyError(f"Follow-up meeting {followup_meeting_id} not found")

        transcript_text = matched["transcript"]

        # Run pipeline for follow-up
        followup_reqs = transcript_analyst.analyze_transcript(transcript_text, followup_meeting_id)
        evaluated_followup = []
        for r in followup_reqs:
            evaluated = await feasibility_agent.evaluate_feasibility(r)
            evaluated_followup.append(evaluated)

        followup_wbs = estimation_engineer.generate_wbs(evaluated_followup)

        # Run Scope Diff Engine
        diff_report = scope_diff_engine.compare_scopes(
            baseline_sow=baseline_sow,
            followup_meeting_id=followup_meeting_id,
            followup_requirements=evaluated_followup,
            followup_wbs=followup_wbs
        )
        self.diff_reports[baseline_project_id] = diff_report

        # Build revised SOW V2
        revised_sow = scope_architect.build_scope_of_work(
            project_id=baseline_project_id,
            project_title=f"{baseline_sow.project_title} (Revised Scope)",
            client_name=baseline_sow.client_name,
            meeting_id=followup_meeting_id,
            requirements=evaluated_followup,
            wbs_tasks=followup_wbs,
            version=2
        )
        self.projects[baseline_project_id] = revised_sow

        # Generate revised proposal
        revised_proposal = proposal_executive.generate_proposal(
            revised_sow,
            delta_summary=diff_report.summary_for_client
        )
        self.proposals[revised_proposal.proposal_id] = revised_proposal

        return {
            "baseline_project_id": baseline_project_id,
            "diff_report": diff_report,
            "revised_sow": revised_sow,
            "revised_proposal": revised_proposal
        }

    def approve_proposal(self, proposal_id: str, req: ProposalApprovalRequest) -> ClientProposal:
        if proposal_id not in self.proposals:
            raise KeyError(f"Proposal {proposal_id} not found")

        prop = self.proposals[proposal_id]
        if req.approved:
            prop.status = "APPROVED"
            prop.approved_by = req.reviewer_name
            prop.approved_at = datetime.now(timezone.utc).isoformat()
        else:
            prop.status = "REJECTED"

        return prop

orchestrator = MultiAgentScopeOrchestrator()
