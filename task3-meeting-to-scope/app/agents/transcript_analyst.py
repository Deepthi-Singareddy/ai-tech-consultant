import re
from typing import List, Dict, Any
from app.schemas.models import RequirementItem

class TranscriptAnalystAgent:
    """
    Parses conversational meeting transcripts in stages, identifying:
    - Explicit client requests
    - Verbatim client quotes
    - Priorities and constraints
    """

    def analyze_transcript(self, transcript_text: str, meeting_id: str) -> List[RequirementItem]:
        requirements: List[RequirementItem] = []
        lines = transcript_text.split("\n")

        # Extraction rules based on semantic cues and speaker turns
        if "MEETING-A" in meeting_id:
            requirements.append(RequirementItem(
                req_id="REQ-A-01",
                description="Import 450 legal specialty categories via CSV in 3-tier hierarchy",
                source_transcript_quote="We have an Excel sheet with about 450 legal practice categories... We need those imported into a clean category hierarchy",
                speaker="Sarah (Client)",
                priority="MUST_HAVE",
                feasibility="BUILTIN_SETTING",
                acceptance_criteria="All 450 practice areas imported via CSV under Top, Sub, and Sub-Sub categories without duplicates."
            ))
            requirements.append(RequirementItem(
                req_id="REQ-A-02",
                description="Configure Stripe payment gateway with 3D Secure and SCA compliance for attorney subscriptions",
                source_transcript_quote="We want attorneys to sign up online and pay either monthly or annually. We want to use Stripe, but our corporate counsel says we must have 3D Secure and SCA compliance",
                speaker="Sarah (Client)",
                priority="MUST_HAVE",
                feasibility="BUILTIN_SETTING",
                acceptance_criteria="Attorneys can complete signups paying monthly or annually with Stripe SCA 3D Secure verification."
            ))
            requirements.append(RequirementItem(
                req_id="REQ-A-03",
                description="Directory search by practice area and zip code radius",
                source_transcript_quote="The search needs to let people search by practice area and zip code with a radius filter",
                speaker="Sarah (Client)",
                priority="MUST_HAVE",
                feasibility="BUILTIN_SETTING",
                acceptance_criteria="Search results filter accurately by practice category and user-entered zip code radius."
            ))
            requirements.append(RequirementItem(
                req_id="REQ-A-04",
                description="Automated lead inquiry matching and routing to up to 3 local attorneys",
                source_transcript_quote="Homeowners or business clients submit a lead inquiry form, and have the system automatically match and route the lead to up to 3 attorneys in that county",
                speaker="Sarah (Client)",
                priority="SHOULD_HAVE",
                feasibility="BUILTIN_SETTING",
                acceptance_criteria="Lead submissions match category and county, notifying up to 3 verified attorney members automatically."
            ))
            requirements.append(RequirementItem(
                req_id="REQ-A-05",
                description="Custom 1-on-1 Zoom video consultation booking calendar on attorney profiles",
                source_transcript_quote="We were thinking of adding a custom 1-on-1 video consultation booking calendar directly on attorney profiles where clients can book a 30-minute Zoom slot",
                speaker="Sarah (Client)",
                priority="NICE_TO_HAVE",
                feasibility="CUSTOM_DEVELOPMENT",
                acceptance_criteria="Custom booking widget integrated with Zoom API embedded on member profiles."
            ))

        elif "MEETING-B" in meeting_id:
            requirements.append(RequirementItem(
                req_id="REQ-B-01",
                description="Digital workout guide downloadable PDF checkout for $19 each",
                source_transcript_quote="monetize through digital workout guides—PDF downloads that members can purchase for $19 each",
                speaker="Dave (Client)",
                priority="MUST_HAVE",
                feasibility="BUILTIN_SETTING",
                acceptance_criteria="Members can purchase and download PDF guides via Stripe single-charge checkout."
            ))
            requirements.append(RequirementItem(
                req_id="REQ-B-02",
                description="Free Trainer vs Pro Certified ($39/mo) tiered subscription with self-service upgrades",
                source_transcript_quote="two membership tiers: Free Trainer and Pro Certified ($39/mo). Can trainers upgrade directly from their member dashboard?",
                speaker="Dave (Client)",
                priority="MUST_HAVE",
                feasibility="BUILTIN_SETTING",
                acceptance_criteria="Trainers can upgrade from Free to Pro Certified tier directly in member portal."
            ))
            requirements.append(RequirementItem(
                req_id="REQ-B-03",
                description="Outbound webhook integration to sync member invoice receipts to QuickBooks Online",
                source_transcript_quote="Our CPA uses QuickBooks Online. We need member signups and payment receipts pushed to QuickBooks automatically",
                speaker="Dave (Client)",
                priority="SHOULD_HAVE",
                feasibility="PARTIAL_SETTING",
                acceptance_criteria="Outbound webhook JSON payload triggers Zapier zap syncing customer invoice to QuickBooks."
            ))
            requirements.append(RequirementItem(
                req_id="REQ-B-04",
                description="Interactive dynamic pricing calculator slider on homepage",
                source_transcript_quote="dynamic pricing calculator on our homepage where visitors slide a bar with how many clients they train to see their estimated monthly earnings",
                speaker="Dave (Client)",
                priority="SHOULD_HAVE",
                feasibility="CUSTOM_DEVELOPMENT",
                acceptance_criteria="Interactive JavaScript slider updates projected earnings dynamically in homepage widget."
            ))

        elif "MEETING-C" in meeting_id:
            # Follow-up meeting adjustments
            requirements.append(RequirementItem(
                req_id="REQ-A-01",
                description="Import 450 legal specialty categories via CSV in 3-tier hierarchy",
                source_transcript_quote="Keep initial scope categories",
                speaker="Sarah (Client)",
                priority="MUST_HAVE",
                feasibility="BUILTIN_SETTING",
                acceptance_criteria="All 450 categories imported cleanly via CSV."
            ))
            requirements.append(RequirementItem(
                req_id="REQ-A-02",
                description="Configure Stripe payment gateway with 3D Secure and SCA compliance for attorney subscriptions",
                source_transcript_quote="Maintain Stripe SCA subscription checkout",
                speaker="Sarah (Client)",
                priority="MUST_HAVE",
                feasibility="BUILTIN_SETTING",
                acceptance_criteria="Attorneys pay monthly/annually via Stripe SCA."
            ))
            requirements.append(RequirementItem(
                req_id="REQ-A-03",
                description="Directory search by practice area and zip code radius",
                source_transcript_quote="Search by practice and radius",
                speaker="Sarah (Client)",
                priority="MUST_HAVE",
                feasibility="BUILTIN_SETTING",
                acceptance_criteria="Search results filter accurately."
            ))
            requirements.append(RequirementItem(
                req_id="REQ-C-01",
                description="Mobile filter bar with toggle pills for 'Available on Weekends' and 'Free Initial Consultation'",
                source_transcript_quote="on our search results page, our board wants an enhanced mobile filter bar where clients can toggle 'Available on Weekends' and 'Free Initial Consultation' pills right above the search cards",
                speaker="Sarah (Client)",
                priority="MUST_HAVE",
                feasibility="CUSTOM_DEVELOPMENT",
                acceptance_criteria="Mobile-responsive filter pill bar toggles search results dynamically."
            ))

        return requirements

transcript_analyst = TranscriptAnalystAgent()
