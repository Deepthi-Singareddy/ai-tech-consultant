import os
import json
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional

from app.core.config import settings
from app.rag.store import knowledge_store
from app.schemas.models import (
    QueryRequest, QueryResponse, SourceCitation, ImageReference,
    EscalationItem, EscalationResolveRequest
)

class GroundedQAEngine:
    """
    RAG Question-Answering Engine enforcing:
    1. Grounding in retrieved documentation only
    2. Exact URL citations
    3. Multimodal image / screenshot attribution
    4. Strict confidence thresholds & human expert escalations
    """

    def __init__(self):
        self.escalations_path = settings.ESCALATIONS_FILE
        self.escalations: Dict[str, Dict[str, Any]] = self._load_escalations()

    def _load_escalations(self) -> Dict[str, Dict[str, Any]]:
        if self.escalations_path.exists():
            try:
                with open(self.escalations_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"[QAEngine] Error loading escalations: {e}")
        return {}

    def _save_escalations(self):
        try:
            with open(self.escalations_path, 'w', encoding='utf-8') as f:
                json.dump(self.escalations, f, indent=2)
        except Exception as e:
            print(f"[QAEngine] Error saving escalations: {e}")

    def query(self, req: QueryRequest) -> QueryResponse:
        start_time = time.perf_counter()
        query_text = req.query.strip()

        # 1. Retrieve hybrid chunks
        raw_chunks = knowledge_store.hybrid_search(query_text, top_k=req.top_k)

        # 2. Compute confidence score
        if not raw_chunks:
            confidence = 0.0
        else:
            top_rel = raw_chunks[0]["relevance"]
            avg_rel = sum(c["relevance"] for c in raw_chunks) / len(raw_chunks)
            confidence = round(0.7 * top_rel + 0.3 * avg_rel, 3)

        # 3. Check Abstention Threshold
        if confidence < settings.CONFIDENCE_THRESHOLD or not raw_chunks:
            esc_id = f"ESC-{uuid.uuid4().hex[:8].upper()}"
            self.escalations[esc_id] = {
                "id": esc_id,
                "query": query_text,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "reason": f"Low retrieval confidence ({confidence:.2f} < {settings.CONFIDENCE_THRESHOLD:.2f}) or missing documentation",
                "status": "pending",
                "expert_answer": None,
                "resolved_by": None,
                "resolved_at": None
            }
            self._save_escalations()

            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return QueryResponse(
                query=query_text,
                answer=(
                    f"The current Brilliant Directories documentation does not contain sufficient verified details "
                    f"to answer this question accurately. To prevent inaccurate guidance, this query has been escalated "
                    f"to a senior tech consultant for human verification (Ticket ID: {esc_id})."
                ),
                status="insufficient_evidence",
                confidence=confidence,
                sources=[],
                images=[],
                needs_escalation=True,
                escalation_id=esc_id,
                model_used=settings.DEFAULT_MODEL,
                latency_ms=latency_ms
            )

        # 4. Format Sources & Citations
        citations: List[SourceCitation] = []
        all_images: List[ImageReference] = []

        seen_urls = set()
        for c in raw_chunks:
            img_refs = [
                ImageReference(
                    url=im.get("url", ""),
                    alt_text=im.get("alt_text", ""),
                    caption=im.get("caption", ""),
                    section_context=im.get("section_context", ""),
                    visual_description=im.get("visual_description", "")
                )
                for im in c.get("images", [])
            ]

            citations.append(SourceCitation(
                article_id=c["article_id"],
                title=c["title"],
                url=c["url"],
                category=c.get("category", "General"),
                section_heading=c.get("heading"),
                snippet=c["snippet"],
                relevance=c["relevance"],
                images=img_refs if req.include_images else []
            ))

            if req.include_images:
                for img in img_refs:
                    if img.url and img.url not in seen_urls:
                        seen_urls.add(img.url)
                        all_images.append(img)

        # 5. Generate Grounded Answer
        answer_text = self._synthesize_answer(query_text, raw_chunks, citations)
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

        return QueryResponse(
            query=query_text,
            answer=answer_text,
            status="answered",
            confidence=confidence,
            sources=citations,
            images=all_images,
            needs_escalation=False,
            escalation_id=None,
            model_used=settings.DEFAULT_MODEL,
            latency_ms=latency_ms
        )

    def _synthesize_answer(self, query: str, chunks: List[Dict[str, Any]], citations: List[SourceCitation]) -> str:
        """
        Synthesizes a grounded answer from retrieved context.
        If ANTHROPIC_API_KEY is present, calls Claude; otherwise generates clean,
        deterministic synthesis directly referencing the cited sections.
        """
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if api_key and api_key.startswith("sk-ant"):
            try:
                import anthropic
                client = anthropic.Anthropic(api_key=api_key)
                
                context_str = "\n\n".join([
                    f"[Source: {c['title']} | URL: {c['url']}]\n{c['text']}"
                    for c in chunks
                ])
                
                prompt = (
                    f"You are the Brilliant Directories AI Tech Consultant. Answer the customer query strictly "
                    f"using the provided verified documentation snippets. Cite the exact titles and steps. "
                    f"If screenshots are referenced, describe the UI navigation path clearly.\n\n"
                    f"Documentation Context:\n{context_str}\n\n"
                    f"Customer Query: {query}\n\nAnswer:"
                )
                
                msg = client.messages.create(
                    model=settings.DEFAULT_MODEL,
                    max_tokens=800,
                    temperature=0.0,
                    messages=[{"role": "user", "content": prompt}]
                )
                return msg.content[0].text
            except Exception as e:
                print(f"[QAEngine] Claude API call failed ({e}). Using deterministic grounded synthesizer.")

        # Deterministic Grounded Synthesis Fallback
        primary = chunks[0]
        answer_parts = []
        answer_parts.append(f"Based on the official Brilliant Directories documentation ({primary['title']}):\n")

        # Synthesize procedural instructions from the most relevant section
        lines = [line.strip() for line in primary['text'].split('\n') if line.strip() and not line.startswith('Category:') and not line.startswith('Section:')]
        clean_content = "\n".join(lines[1:8])
        answer_parts.append(clean_content)

        # Include screenshot guidance if present
        if primary.get("images"):
            top_img = primary["images"][0]
            if top_img.get("visual_description"):
                answer_parts.append(f"\n\n**Visual UI Guide**: {top_img['visual_description']}")

        # Primary source citation
        answer_parts.append(f"\n\n**Source Reference**: [{primary['title']}]({primary['url']})")

        return "\n".join(answer_parts)

    def get_escalations(self) -> List[EscalationItem]:
        items = []
        for v in self.escalations.values():
            items.append(EscalationItem(**v))
        return sorted(items, key=lambda x: x.timestamp, reverse=True)

    def resolve_escalation(self, escalation_id: str, req: EscalationResolveRequest) -> Dict[str, Any]:
        if escalation_id not in self.escalations:
            raise KeyError(f"Escalation {escalation_id} not found")

        item = self.escalations[escalation_id]
        item["status"] = "resolved"
        item["expert_answer"] = req.expert_answer
        item["resolved_by"] = req.expert_name
        item["resolved_at"] = datetime.now(timezone.utc).isoformat()
        self._save_escalations()

        # Ingest into the retrieval store immediately
        knowledge_store.add_expert_override(
            query=item["query"],
            expert_answer=req.expert_answer,
            author=req.expert_name,
            source_url=req.supporting_url
        )

        return {
            "status": "success",
            "message": f"Escalation {escalation_id} resolved and indexed into Knowledge Brain.",
            "escalation": item
        }

qa_engine = GroundedQAEngine()
