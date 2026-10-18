import sys
import os
from pathlib import Path
import pytest

# Add parent directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.schemas.models import QueryRequest, EscalationResolveRequest
from app.rag.qa_engine import GroundedQAEngine
from app.rag.store import HybridKnowledgeStore
from app.crawler.crawler import PoliteCrawler
from app.parser.article_parser import ArticleParser

def test_article_parser_extraction():
    sample_html = """
    <html>
        <body>
            <ul class="breadcrumb">
                <li><a href="/support/home">Home</a></li>
                <li><a href="/solutions">Solutions</a></li>
                <li>Finance > Payment Gateways</li>
            </ul>
            <h1 class="post-title">How to Set Up Stripe Payment Gateway</h1>
            <div class="article-body">
                <h2>Step 1: Connect Stripe</h2>
                <p>Navigate to Finance > Payment Gateways in the admin panel.</p>
                <img src="https://example.com/stripe.png" alt="Stripe Setup Form" />
                <p>Enter your Publishable Key and Secret Key, then click Save.</p>
            </div>
        </body>
    </html>
    """
    url = "https://support.brilliantdirectories.com/support/solutions/articles/5000682855-how-to-set-up-stripe-payment-gateway"
    parsed = ArticleParser.parse_html(sample_html, url)

    assert parsed["article_id"] == "5000682855"
    assert "Stripe" in parsed["title"]
    assert len(parsed["sections"]) >= 1
    assert len(parsed["images"]) == 1
    assert "stripe.png" in parsed["images"][0]["url"]

def test_crawler_seed_initialization():
    crawler = PoliteCrawler()
    changes = crawler.detect_sitemap_changes([
        ("https://support.brilliantdirectories.com/support/solutions/articles/5000682855-how-to-set-up-stripe-payment-gateway", "2024-04-12")
    ])
    assert "ADDED" in changes
    assert "MODIFIED" in changes

def test_qa_engine_supported_query():
    # Ensure crawler has seeded data
    crawler = PoliteCrawler()
    crawler._inject_rich_seed_knowledge()
    
    from app.rag.store import knowledge_store
    knowledge_store.rebuild_from_articles()

    qa = GroundedQAEngine()
    resp = qa.query(QueryRequest(query="How do I connect Stripe payment gateway in Brilliant Directories?"))

    assert resp.status == "answered"
    assert resp.confidence >= 0.65
    assert len(resp.sources) > 0
    assert any("stripe" in s.title.lower() for s in resp.sources)
    assert not resp.needs_escalation

def test_qa_engine_unsupported_query_abstention():
    qa = GroundedQAEngine()
    resp = qa.query(QueryRequest(query="What is the internal quantum algorithm used for warp drive navigation?"))

    # Must abstain honestly and log escalation
    assert resp.status == "insufficient_evidence"
    assert resp.confidence < 0.65
    assert resp.needs_escalation is True
    assert resp.escalation_id is not None
    assert "escalated to a senior tech consultant" in resp.answer

def test_escalation_resolution_workflow():
    qa = GroundedQAEngine()
    # Trigger an unanswerable question
    unanswerable = "How do we integrate custom biometric fingerprint scanner at member login?"
    resp = qa.query(QueryRequest(query=unanswerable))
    assert resp.needs_escalation is True
    esc_id = resp.escalation_id

    # Resolve escalation with expert answer
    res = qa.resolve_escalation(esc_id, EscalationResolveRequest(
        expert_answer="Biometric fingerprint scanning requires our custom WebAuthn FIDO2 Add-on available via developer settings.",
        expert_name="Senior Security Engineer"
    ))
    assert res["status"] == "success"

    # Now verify query returns the expert override answer!
    followup_resp = qa.query(QueryRequest(query="biometric fingerprint scanner member login"))
    assert followup_resp.status == "answered"
    assert "WebAuthn" in followup_resp.answer
