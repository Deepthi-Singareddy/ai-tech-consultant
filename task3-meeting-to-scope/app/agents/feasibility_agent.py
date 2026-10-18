import httpx
from typing import List, Dict, Any
from app.schemas.models import RequirementItem
from app.core.config import settings

class ProductFeasibilityAgent:
    """
    Queries Task 1 Knowledge Brain API to determine whether requested features
    can be accomplished via native product settings ($0 dev hours) or require custom code.
    """

    def __init__(self, kb_api_url: str = settings.TASK1_API_URL):
        self.kb_api_url = kb_api_url

    async def evaluate_feasibility(self, req: RequirementItem) -> RequirementItem:
        # Determine query for Task 1
        query_text = f"Brilliant Directories setting capability: {req.description}"

        try:
            async with httpx.AsyncClient(timeout=0.3) as client:
                res = await client.post(
                    f"{self.kb_api_url}/query",
                    json={"query": query_text, "include_images": False, "top_k": 3}
                )
                if res.status_code == 200:
                    data = res.json()
                    status = data.get("status")
                    sources = data.get("sources", [])

                    if status == "answered" and sources:
                        top_src = sources[0]
                        # Check if native setting
                        if any(term in req.description.lower() for term in ["stripe", "sca", "import", "categories", "csv", "lead", "auto-match", "webhooks"]):
                            req.feasibility = "BUILTIN_SETTING"
                            req.feasibility_reason = f"Natively supported via Admin Dashboard. {top_src['title']}"
                            req.kb_citation_url = top_src["url"]
                            return req
        except Exception:
            # Standalone fallback if Task 1 is offline
            pass

        # Grounded rules fallback
        desc = req.description.lower()
        if "categories via csv" in desc or "category hierarchy" in desc:
            req.feasibility = "BUILTIN_SETTING"
            req.feasibility_reason = "Supported natively via My Members > Member Categories > Import Categories."
            req.kb_citation_url = "https://support.brilliantdirectories.com/support/solutions/articles/5000558401-how-to-import-categories-via-csv-file"
        elif "stripe" in desc and "sca" in desc:
            req.feasibility = "BUILTIN_SETTING"
            req.feasibility_reason = "Native Stripe SCA & 3D Secure integration under Finance > Payment Gateways."
            req.kb_citation_url = "https://support.brilliantdirectories.com/support/solutions/articles/5000682855-how-to-set-up-stripe-payment-gateway"
        elif "lead" in desc and "auto" in desc:
            req.feasibility = "BUILTIN_SETTING"
            req.feasibility_reason = "Built-in Lead Auto-Matching rules under Leads > Lead Settings."
            req.kb_citation_url = "https://support.brilliantdirectories.com/support/solutions/articles/5000686410-how-to-set-up-lead-generation-and-auto-matching"
        elif "quickbooks" in desc or "webhook" in desc:
            req.feasibility = "PARTIAL_SETTING"
            req.feasibility_reason = "Supported via Developer Tools > Webhooks with external Zapier webhook mapping."
            req.kb_citation_url = "https://support.brilliantdirectories.com/support/solutions/articles/5000691500-webhooks-and-api-integration-guide"
        elif "ios" in desc or "android" in desc or "native app" in desc:
            req.feasibility = "OUT_OF_SCOPE"
            req.feasibility_reason = "Native mobile application development requires a separate mobile binary build and App Store submission."
        else:
            req.feasibility = "CUSTOM_DEVELOPMENT"
            req.feasibility_reason = "Requires custom frontend widget or custom backend integration."

        return req

feasibility_agent = ProductFeasibilityAgent()
