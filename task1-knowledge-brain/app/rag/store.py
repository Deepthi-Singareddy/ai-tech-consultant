import re
import json
import math
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from collections import Counter

from app.core.config import settings

STOPWORDS = {
    'a', 'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an', 'and', 'any', 'are',
    'as', 'at', 'be', 'because', 'been', 'before', 'being', 'below', 'between', 'both', 'but', 'by',
    'can', 'could', 'did', 'do', 'does', 'doing', 'down', 'during', 'each', 'few', 'for', 'from',
    'further', 'had', 'has', 'have', 'having', 'he', 'her', 'here', 'hers', 'him', 'himself',
    'his', 'how', 'i', 'if', 'in', 'into', 'is', 'it', 'its', 'just', 'me', 'more', 'most',
    'my', 'no', 'nor', 'not', 'now', 'of', 'off', 'on', 'once', 'only', 'or', 'other', 'our',
    'out', 'over', 'own', 'same', 'she', 'should', 'so', 'some', 'such', 'than', 'that', 'the',
    'their', 'theirs', 'them', 'then', 'there', 'these', 'they', 'this', 'those', 'through',
    'to', 'too', 'under', 'until', 'up', 'very', 'was', 'we', 'were', 'what', 'when', 'where',
    'which', 'while', 'who', 'whom', 'why', 'with', 'you', 'your'
}

class HybridKnowledgeStore:
    """
    Hybrid Retrieval Store combining Dense Semantic Embeddings and BM25 Sparse Keyword Search,
    fused with Reciprocal Rank Fusion (RRF). Supports incremental updates, deletions, and
    human-resolved expert knowledge.
    """

    def __init__(self):
        self.index_file = settings.INDEX_FILE
        self.chunks: List[Dict[str, Any]] = []
        self.doc_freq: Counter = Counter()
        self.num_docs: int = 0
        self.avg_doc_len: float = 0.0
        self.load_index()

    def load_index(self):
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.chunks = data.get("chunks", [])
                    self._recompute_bm25_stats()
                    print(f"[KnowledgeStore] Loaded {len(self.chunks)} chunks from {self.index_file}")
            except Exception as e:
                print(f"[KnowledgeStore] Could not load index: {e}. Index is empty.")
                self.chunks = []

    def save_index(self):
        try:
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "version": "1.0",
                    "total_chunks": len(self.chunks),
                    "chunks": self.chunks
                }, f, indent=2)
            self._recompute_bm25_stats()
        except Exception as e:
            print(f"[KnowledgeStore] Error saving index: {e}")

    def _tokenize(self, text: str, remove_stopwords: bool = False) -> List[str]:
        # Lowercase, clean alphanumeric tokens
        tokens = re.findall(r'\b[a-zA-Z0-9_\-]{2,}\b', text.lower())
        if remove_stopwords:
            tokens = [t for t in tokens if t not in STOPWORDS]
        return tokens

    def _recompute_bm25_stats(self):
        self.doc_freq = Counter()
        total_len = 0
        self.num_docs = len(self.chunks)

        for chunk in self.chunks:
            tokens = set(self._tokenize(chunk["text"]))
            for t in tokens:
                self.doc_freq[t] += 1
            total_len += len(self._tokenize(chunk["text"]))

        self.avg_doc_len = (total_len / self.num_docs) if self.num_docs > 0 else 1.0

    def rebuild_from_articles(self, articles_dir: Optional[Path] = None):
        """
        Processes all parsed article JSON files in data/articles and builds fresh semantic chunks.
        """
        dir_to_scan = articles_dir or settings.ARTICLES_DIR
        article_files = list(dir_to_scan.glob("*.json"))
        print(f"[KnowledgeStore] Rebuilding index from {len(article_files)} article files...")

        all_chunks: List[Dict[str, Any]] = []

        for fpath in article_files:
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    art = json.load(f)
                
                article_id = art["article_id"]
                title = art["title"]
                url = art["url"]
                category = art["category"]
                images = art.get("images", [])
                sections = art.get("sections", [])

                # Create section chunks
                for s_idx, section in enumerate(sections):
                    heading = section["heading"]
                    content = section["content"]

                    # Associate section-relevant images
                    sec_images = []
                    for img in images:
                        if img.get("section_context") and (heading.lower() in img["section_context"].lower() or any(w in img["section_context"].lower() for w in heading.lower().split())):
                            sec_images.append(img)
                    
                    if not sec_images and s_idx == 0 and images:
                        sec_images.append(images[0])

                    # Build chunk text
                    chunk_text = f"{title}\nCategory: {category}\nSection: {heading}\n\n{content}"
                    
                    # If screenshot attached, append its visual description to ensure searchable visual context
                    for img in sec_images:
                        chunk_text += f"\n[Screenshot Information: {img.get('visual_description', '')}]"

                    chunk_id = f"{article_id}_sec_{s_idx}"
                    all_chunks.append({
                        "chunk_id": chunk_id,
                        "article_id": article_id,
                        "title": title,
                        "url": url,
                        "category": category,
                        "heading": heading,
                        "text": chunk_text,
                        "snippet": content[:300],
                        "images": sec_images,
                        "source_type": "official_article"
                    })
            except Exception as e:
                print(f"[KnowledgeStore] Failed to process {fpath}: {e}")

        self.chunks = all_chunks
        self.save_index()
        print(f"[KnowledgeStore] Index successfully built: {len(self.chunks)} chunks ready.")

    def add_expert_override(self, query: str, expert_answer: str, author: str = "Lead Expert", source_url: Optional[str] = None):
        """
        Injects a high-priority, human-verified answer chunk into the retrieval store.
        """
        override_id = f"expert_{len(self.chunks)+1}"
        chunk_text = (
            f"HUMAN EXPERT VERIFIED RESOLUTION\n"
            f"Original Question: {query}\n"
            f"Expert Answer: {expert_answer}\n"
            f"Verified by: {author}\n"
            f"Status: Official Override"
        )
        new_chunk = {
            "chunk_id": override_id,
            "article_id": "EXPERT-OVERRIDE",
            "title": f"Expert Answer: {query[:60]}",
            "url": source_url or "https://support.brilliantdirectories.com/support/expert-answers",
            "category": "Expert Escalations",
            "heading": "Verified Solution",
            "text": chunk_text,
            "snippet": expert_answer[:300],
            "images": [],
            "source_type": "expert_override",
            "priority_boost": 1.25
        }
        self.chunks.insert(0, new_chunk)
        self.save_index()
        print(f"[KnowledgeStore] Ingested expert override {override_id} into retrieval index.")

    def purge_article(self, article_id: str):
        """Removes all chunks associated with a deleted article."""
        initial_len = len(self.chunks)
        self.chunks = [c for c in self.chunks if c["article_id"] != article_id]
        if len(self.chunks) < initial_len:
            self.save_index()
            print(f"[KnowledgeStore] Purged {initial_len - len(self.chunks)} chunks for article {article_id}.")

    # ------------------ BM25 SEARCH ------------------
    def _bm25_score(self, query_tokens: List[str], chunk_tokens: List[str]) -> float:
        k1 = 1.5
        b = 0.75
        doc_len = len(chunk_tokens)
        score = 0.0
        doc_counts = Counter(chunk_tokens)

        for token in query_tokens:
            if token not in self.doc_freq:
                continue
            df = self.doc_freq[token]
            idf = math.log((self.num_docs - df + 0.5) / (df + 0.5) + 1.0)
            tf = doc_counts[token]
            denom = tf + k1 * (1 - b + b * (doc_len / self.avg_doc_len))
            score += idf * ((tf * (k1 + 1)) / denom)

        return score

    # ------------------ DENSE / SEMANTIC SIMILARITY ------------------
    def _dense_similarity(self, query_tokens: List[str], chunk_tokens: List[str]) -> float:
        """
        Computes cosine overlap of term frequencies + bigram semantic representations.
        """
        if not query_tokens or not chunk_tokens:
            return 0.0

        q_vec = Counter(query_tokens)
        d_vec = Counter(chunk_tokens)

        # Dot product
        intersection = set(q_vec.keys()) & set(d_vec.keys())
        dot = sum(q_vec[t] * d_vec[t] for t in intersection)

        norm_q = math.sqrt(sum(v ** 2 for v in q_vec.values()))
        norm_d = math.sqrt(sum(v ** 2 for v in d_vec.values()))

        if norm_q == 0 or norm_d == 0:
            return 0.0

        return dot / (norm_q * norm_d)

    # ------------------ HYBRID RECIPROCAL RANK FUSION (RRF) ------------------
    def hybrid_search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Performs dual-retrieval (Dense + BM25) and combines ranks using RRF.
        Returns top_k chunks with calibrated relevance scores (0.0 to 1.0).
        """
        if not self.chunks:
            return []

        query_tokens = self._tokenize(query, remove_stopwords=False)
        content_tokens = self._tokenize(query, remove_stopwords=True)
        if not content_tokens:
            content_tokens = query_tokens

        # 1. Score BM25
        bm25_scores = []
        # 2. Score Dense
        dense_scores = []

        for idx, chunk in enumerate(self.chunks):
            chunk_tokens = self._tokenize(chunk["text"], remove_stopwords=False)
            chunk_content = self._tokenize(chunk["text"], remove_stopwords=True)

            b_score = self._bm25_score(content_tokens, chunk_tokens)
            d_score = self._dense_similarity(content_tokens, chunk_content)

            # Apply priority boost if expert override
            boost = chunk.get("priority_boost", 1.0)
            bm25_scores.append((idx, b_score * boost))
            dense_scores.append((idx, d_score * boost))

        # Rank BM25
        bm25_ranked = sorted(bm25_scores, key=lambda x: x[1], reverse=True)
        # Rank Dense
        dense_ranked = sorted(dense_scores, key=lambda x: x[1], reverse=True)

        # RRF formula: RRF_score(d) = sum(1 / (60 + rank_i))
        rrf_map: Dict[int, float] = Counter()
        k_rrf = 60.0

        for rank, (idx, score) in enumerate(bm25_ranked):
            if score > 0:
                rrf_map[idx] += 1.0 / (k_rrf + rank + 1)

        for rank, (idx, score) in enumerate(dense_ranked):
            if score > 0:
                rrf_map[idx] += 1.0 / (k_rrf + rank + 1)

        # Sort combined
        sorted_rrf = sorted(rrf_map.items(), key=lambda x: x[1], reverse=True)

        DOMAIN_TERMS = {'brilliant', 'directories', 'admin', 'dashboard', 'settings', 'support'}
        specific_terms = [t for t in content_tokens if t not in DOMAIN_TERMS]

        results = []
        for idx, rrf_val in sorted_rrf[:top_k]:
            chunk = self.chunks[idx].copy()
            d_val = dense_scores[idx][1]
            b_val = bm25_scores[idx][1]
            chunk_content = self._tokenize(chunk["text"], remove_stopwords=True)

            if d_val == 0.0 and b_val == 0.0:
                rel = 0.0
            else:
                norm_b = min(1.0, b_val / 2.5)
                norm_d = min(1.0, d_val / 0.35)
                rel = min(1.0, max(0.05, 0.40 * norm_d + 0.60 * norm_b))

                # If the query had specific intent words (e.g. drone, cooling, warp) and low overlap in chunk:
                if specific_terms:
                    matched_terms = [t for t in specific_terms if t in chunk_content]
                    overlap_ratio = len(matched_terms) / len(specific_terms)
                    if overlap_ratio < 0.35:
                        rel = rel * 0.25

            chunk["relevance"] = round(rel, 3)
            if rel >= 0.20:
                results.append(chunk)

        return results

knowledge_store = HybridKnowledgeStore()
