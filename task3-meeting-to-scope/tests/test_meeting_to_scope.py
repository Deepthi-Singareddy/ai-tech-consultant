import sys
import os
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.agents.transcript_analyst import transcript_analyst
from app.agents.feasibility_agent import feasibility_agent
from app.agents.estimation_engineer import estimation_engineer
from app.agents.scope_architect import scope_architect
from app.diff.scope_diff import scope_diff_engine
from app.orchestrator import orchestrator
from app.schemas.models import ProposalApprovalRequest

def test_transcript_analyst_extraction():
    transcripts = orchestrator.get_transcripts()
    t_a = next(t for t in transcripts if t["id"] == "MEETING-A")
    reqs = transcript_analyst.analyze_transcript(t_a["transcript"], "MEETING-A")

    assert len(reqs) == 5
    assert any("categories via csv" in r.description.lower() for r in reqs)
    assert any("stripe" in r.description.lower() for r in reqs)
    assert any("zoom" in r.description.lower() for r in reqs)

def test_feasibility_agent_classification():
    async def _run():
        transcripts = orchestrator.get_transcripts()
        t_a = next(t for t in transcripts if t["id"] == "MEETING-A")
        raw_reqs = transcript_analyst.analyze_transcript(t_a["transcript"], "MEETING-A")

        evaluated = []
        for r in raw_reqs:
            ev = await feasibility_agent.evaluate_feasibility(r)
            evaluated.append(ev)

        stripe_req = next(r for r in evaluated if "stripe" in r.description.lower())
        assert stripe_req.feasibility == "BUILTIN_SETTING"
        assert "Payment Gateways" in stripe_req.feasibility_reason

        zoom_req = next(r for r in evaluated if "zoom" in r.description.lower())
        assert zoom_req.feasibility == "CUSTOM_DEVELOPMENT"

    asyncio.run(_run())

def test_estimation_engineer_pert_wbs():
    async def _run():
        transcripts = orchestrator.get_transcripts()
        t_a = next(t for t in transcripts if t["id"] == "MEETING-A")
        raw_reqs = transcript_analyst.analyze_transcript(t_a["transcript"], "MEETING-A")
        evaluated = [await feasibility_agent.evaluate_feasibility(r) for r in raw_reqs]

        wbs = estimation_engineer.generate_wbs(evaluated)
        assert len(wbs) >= 5
        # Verify PERT formula: E = (O + 4M + P)/6
        for t in wbs:
            expected = round((t.optimistic_hours + 4 * t.likely_hours + t.pessimistic_hours) / 6.0, 2)
            assert abs(t.expected_hours_pert - expected) < 0.05

    asyncio.run(_run())

def test_scope_diff_engine_meeting_c():
    async def _run():
        # Process baseline Meeting A
        baseline_res = await orchestrator.process_transcript("MEETING-A")
        baseline_sow = baseline_res["scope_of_work"]

        # Process follow-up Meeting C
        followup_res = await orchestrator.process_followup_meeting("MEETING-C", "PROJ-MEETING-A")
        diff = followup_res["diff_report"]

        change_types = [c.type for c in diff.changes]
        assert "ADDED" in change_types
        assert "REMOVED" in change_types
        assert "MODIFIED" in change_types
        assert "SCOPE_CREEP_WARNING" in change_types
        assert len(diff.out_of_scope_warnings) > 0
        assert "native ios and android" in diff.out_of_scope_warnings[0].lower()

    asyncio.run(_run())

def test_proposal_approval_governance():
    async def _run():
        res = await orchestrator.process_transcript("MEETING-B")
        prop = res["proposal"]
        assert prop.status == "PENDING_APPROVAL"

        # Human sign-off
        approved = orchestrator.approve_proposal(prop.proposal_id, ProposalApprovalRequest(
            reviewer_name="Lead Solution Architect",
            approved=True
        ))
        assert approved.status == "APPROVED"
        assert approved.approved_by == "Lead Solution Architect"

    asyncio.run(_run())
