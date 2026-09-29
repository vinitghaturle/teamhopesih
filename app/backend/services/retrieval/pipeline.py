"""Tender Guard - Hybrid Retrieval & Grounding Pipeline.

Combines:
  1. Multilingual Query Detection & Translation (Hindi/Marathi -> English procurement terms)
  2. Dense Semantic Vector Search (FAISS IndexFlatIP + SentenceTransformers)
  3. Sparse Lexical Search (BM25 Okapi with technical tokenization)
  4. Reciprocal Rank Fusion (RRF, k=60)
  5. Cross-Encoder Reranking (ms-marco-MiniLM-L-6-v2)
  6. Calibrated Relevance Floor & Refusal ("NO_CONFIDENT_MATCH")
  7. BM25 Degraded Mode fallback with score cutoff if neural models are unavailable.
"""

import logging
import re
import uuid
from typing import List, Dict, Any, Optional

import numpy as np

from database import SessionLocal
from models.schema import Standard
from services.retrieval.vector_store import VectorStore
from services.retrieval.bm25_store import BM25Store
from services.retrieval.hybrid_search import HybridRetriever, reciprocal_rank_fusion
from services.retrieval.embeddings import EmbeddingModel, ST_AVAILABLE
from services.retrieval.reranker import Reranker, CE_AVAILABLE
from services.retrieval.relevance_floor import evaluate_relevance_floor, RELEVANCE_FLOOR
from services.retrieval.refusal import get_refusal
from services.retrieval.qualifier_checker import QualifierConflictChecker
from services.multilingual import translate_procurement_query, detect_language


logger = logging.getLogger(__name__)

# Minimum BM25 score cutoff when running in degraded mode
BM25_SCORE_FLOOR = 3.5


class IndexedStandardDoc:
    """In-memory wrapper for standard document retrieval."""
    def __init__(self, standard: Standard):
        self.standard_id = standard.standard_id
        self.standard_number = standard.standard_number
        self.normalized_number = standard.normalized_number
        self.year = standard.year
        self.full_title = standard.full_title
        self.short_title = standard.short_title
        self.product_category = standard.product_category
        self.industry = standard.industry
        self.scheme = standard.scheme
        self.is_compulsory_certification = standard.is_compulsory_certification
        self.legal_basis = standard.legal_basis
        self.scope = standard.scope
        self.parameter_names = standard.parameter_names
        self.keywords = standard.keywords
        self.aliases = [a.get("alias") for a in standard.aliases if isinstance(a, dict)]
        self.document_url = standard.document_url
        self.source_url = standard.source_url
        self.needs_review = standard.needs_review

    def to_retrieval_text(self) -> str:
        """Compose rich search document text."""
        aliases_str = ", ".join(self.aliases)
        params_str = ", ".join(self.parameter_names)
        keywords_str = ", ".join(self.keywords)
        return (
            f"{self.standard_number} {self.full_title}. "
            f"Category: {self.product_category}. Industry: {self.industry}. "
            f"Aliases: {aliases_str}. Scope: {self.scope}. "
            f"Key Parameters: {params_str}. Keywords: {keywords_str}."
        )


class RetrievalPipeline:
    def __init__(self, use_neural: bool = True):
        self.documents: List[IndexedStandardDoc] = []
        self.doc_map: Dict[str, IndexedStandardDoc] = {}
        self.vector_store: Optional[VectorStore] = None
        self.bm25_store: Optional[BM25Store] = None
        self.embedder: Optional[EmbeddingModel] = None
        self.reranker: Optional[Reranker] = None
        self.hybrid_retriever: Optional[HybridRetriever] = None
        self.is_degraded_mode: bool = False
        self._load_corpus(use_neural=use_neural)

    def _load_corpus(self, use_neural: bool = True):
        """Load standards from SQLite database and index them."""
        db = SessionLocal()
        try:
            db_standards = db.query(Standard).all()
            self.documents = [IndexedStandardDoc(s) for s in db_standards]
            self.doc_map = {d.standard_id: d for d in self.documents}
        finally:
            db.close()

        if not self.documents:
            logger.warning("No standards found in database to index.")
            return

        # 1. Initialize BM25 Lexical Store
        self.bm25_store = BM25Store(self.documents)

        # 2. Attempt Dense Semantic Store (FAISS + SentenceTransformers)
        if use_neural and ST_AVAILABLE:
            try:
                self.embedder = EmbeddingModel()
                if self.embedder.model is not None:
                    texts = [d.to_retrieval_text() for d in self.documents]
                    embeddings = self.embedder.encode(texts)
                    self.vector_store = VectorStore()
                    self.vector_store.add(embeddings, self.documents)
                    logger.info("Dense vector index initialized with %d standards.", len(self.documents))
            except Exception as e:
                logger.warning("Dense embeddings initialization failed: %s. Falling back to BM25 degraded mode.", e)
                self.vector_store = None
                self.embedder = None
                self.is_degraded_mode = True

        if self.vector_store is None:
            self.is_degraded_mode = True

        # 3. Attempt Cross-Encoder Reranker
        if use_neural and CE_AVAILABLE:
            try:
                self.reranker = Reranker()
            except Exception as e:
                logger.warning("Reranker initialization failed: %s.", e)
                self.reranker = None

        # 4. Initialize Hybrid Retriever
        self.hybrid_retriever = HybridRetriever(
            embedder=self.embedder,
            vector_store=self.vector_store,
            bm25_store=self.bm25_store,
            rrf_k=60,
        )

        # 5. Initialize Qualifier Conflict Checker
        self.qualifier_checker = QualifierConflictChecker(self.documents)


    def extract_exact_citations(self, query: str) -> List[str]:
        """Detect explicit IS citations in query (e.g. 'IS 4984', 'IS:14543-2024', 'IS 8112:1989')."""
        matches = re.findall(r"\b(?:IS|is|Is)\s*[:\-]?\s*(\d+)", query)
        citations = [f"IS {num}" for num in matches]
        return citations

    def search(
        self,
        query: str,
        top_k: int = 5,
        relevance_floor: float = RELEVANCE_FLOOR,
        language: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Perform hybrid search, reranking, relevance floor check, and refusal gating."""
        req_id = request_id or str(uuid.uuid4())
        
        if not query or not query.strip():
            return {
                "request_id": req_id,
                "status": "NO_CONFIDENT_MATCH",
                "verdict": "empty_query",
                "original_query": query,
                "translated_query": query,
                "detected_language": "en",
                "results": [],
                "refusal": get_refusal("out_of_scope", "en"),
                "is_degraded_mode": self.is_degraded_mode,
            }

        # Multilingual Translation & Normalization
        translated_query, detected_lang = translate_procurement_query(query)
        active_lang = language or detected_lang

        # Check explicit standard citations in original and translated query
        citations = self.extract_exact_citations(query) + self.extract_exact_citations(translated_query)
        citations = list(set(citations))
        
        has_identifier_match = False
        matched_standards_by_citation = []

        if citations:
            for cit in citations:
                for doc in self.documents:
                    if cit.upper() in doc.standard_number.upper() or cit.upper() == doc.normalized_number.upper():
                        has_identifier_match = True
                        matched_standards_by_citation.append(doc)

        # 1. Retrieve Candidates via Hybrid RRF (Dense + Sparse) using translated query
        candidates_raw = self.hybrid_retriever.search(translated_query, top_k=max(top_k * 2, 10))

        if not candidates_raw and not matched_standards_by_citation:
            return {
                "request_id": req_id,
                "status": "NO_CONFIDENT_MATCH",
                "verdict": "below_floor",
                "original_query": query,
                "translated_query": translated_query,
                "detected_language": active_lang,
                "results": [],
                "refusal": get_refusal("insufficient_evidence", active_lang),
                "is_degraded_mode": self.is_degraded_mode,
            }

        # In Degraded Mode: check BM25 scores
        if self.is_degraded_mode and not has_identifier_match:
            bm25_matches = self.bm25_store.search(translated_query, top_k=3)
            top_bm25_score = bm25_matches[0][1] if bm25_matches else 0.0
            if top_bm25_score < BM25_SCORE_FLOOR:
                return {
                    "request_id": req_id,
                    "status": "NO_CONFIDENT_MATCH",
                    "verdict": "below_floor",
                    "relevance_reason": f"Top lexical BM25 score ({top_bm25_score:.2f}) is below confidence cutoff ({BM25_SCORE_FLOOR:.2f}).",
                    "original_query": query,
                    "translated_query": translated_query,
                    "detected_language": active_lang,
                    "results": [],
                    "refusal": get_refusal("insufficient_evidence", active_lang),
                    "is_degraded_mode": True,
                }

        # Format retrieved candidate items
        retrieved_items = []
        for doc, rrf_score, rank_info in candidates_raw:
            sem_sim = None
            if self.embedder is not None and self.vector_store is not None:
                try:
                    q_emb = self.embedder.encode_query(translated_query)
                    doc_emb = self.embedder.encode([doc.to_retrieval_text()])
                    sem_sim = float(np.dot(q_emb[0], doc_emb[0]))
                except Exception:
                    sem_sim = None

            retrieved_items.append({
                "document": doc,
                "rrf_score": rrf_score,
                "dense_rank": rank_info.get("dense_rank"),
                "bm25_rank": rank_info.get("bm25_rank"),
                "semantic_similarity": sem_sim,
            })

        # 2. Evaluate Relevance Floor (Zero-Hallucination Gate)
        floor_eval = evaluate_relevance_floor(
            retrieved_items=retrieved_items,
            floor=relevance_floor,
            has_exact_identifier_match=has_identifier_match,
        )

        if floor_eval["decision"] == "below_floor":
            top_raw_score = None
            if self.reranker is not None and not self.is_degraded_mode and retrieved_items:
                try:
                    top_scores = self.reranker.score(translated_query, [retrieved_items[0]["document"].to_retrieval_text()])
                    if top_scores:
                        top_raw_score = float(top_scores[0])
                except Exception:
                    top_raw_score = -10.0

            return {
                "request_id": req_id,
                "status": "NO_CONFIDENT_MATCH",
                "verdict": "below_floor",
                "relevance_reason": floor_eval["reason"],
                "original_query": query,
                "translated_query": translated_query,
                "detected_language": active_lang,
                "results": [],
                "top_candidate_score": top_raw_score,
                "refusal": get_refusal("insufficient_evidence", active_lang),
                "is_degraded_mode": self.is_degraded_mode,
            }

        # 3. Cross-Encoder Reranking
        docs_to_rerank = [item["document"] for item in retrieved_items[:10]]
        if self.reranker is not None and not self.is_degraded_mode:
            rerank_texts = [d.to_retrieval_text() for d in docs_to_rerank]
            rerank_scores = self.reranker.score(translated_query, rerank_texts)
        else:
            rerank_scores = [item["rrf_score"] for item in retrieved_items[:10]]

        # Combine and sort final candidates
        final_results = []
        for idx, item in enumerate(retrieved_items[:10]):
            r_score = rerank_scores[idx] if idx < len(rerank_scores) else 0.0
            doc = item["document"]
            
            # Match strength band (calibrated on golden set)
            if item.get("semantic_similarity") is not None:
                sim = item["semantic_similarity"]
                if sim >= 0.60 or has_identifier_match:
                    match_band = "HIGH"
                elif sim >= 0.42:
                    match_band = "MEDIUM"
                else:
                    match_band = "LOW"
            else:
                match_band = "HIGH" if (item.get("bm25_rank") or 99) <= 2 else "MEDIUM"

            final_results.append({
                "standard_id": doc.standard_id,
                "standard_number": doc.standard_number,
                "year": doc.year,
                "full_title": doc.full_title,
                "short_title": doc.short_title,
                "product_category": doc.product_category,
                "scheme": doc.scheme,
                "is_compulsory_certification": doc.is_compulsory_certification,
                "legal_basis": doc.legal_basis,
                "needs_review": doc.needs_review,
                "match_strength": match_band,
                "dense_rank": item.get("dense_rank"),
                "bm25_rank": item.get("bm25_rank"),
                "rrf_score": item.get("rrf_score"),
                "rerank_score": r_score,
                "source_excerpt": doc.scope[:280] + "..." if len(doc.scope) > 280 else doc.scope,
                "source_field": "scope",
                "document_url": doc.document_url,
                "source_url": doc.source_url,
            })

        # Sort by rerank score descending
        final_results = sorted(final_results, key=lambda x: -x["rerank_score"])[:top_k]

        # 4. Qualifier Conflict Check (e.g. drainage vs potable water, industrial vs 2-wheeler)
        top_doc = self.doc_map.get(final_results[0]["standard_id"]) if final_results else None
        has_conflict, conflict_reason = False, None
        if top_doc and not has_identifier_match and hasattr(self, "qualifier_checker") and self.qualifier_checker:
            has_conflict, conflict_reason = self.qualifier_checker.check_conflicts(translated_query, top_doc)

        final_status = "CLOSE_BUT_NOT_EXACT" if has_conflict else "MATCH_FOUND"
        verdict = "qualifier_conflict" if has_conflict else floor_eval["decision"]
        reason = conflict_reason if has_conflict else floor_eval["reason"]

        for res in final_results:
            res["has_qualifier_conflict"] = has_conflict
            res["conflict_warning"] = conflict_reason if has_conflict else None

        return {
            "request_id": req_id,
            "status": final_status,
            "verdict": verdict,
            "relevance_reason": reason,
            "original_query": query,
            "translated_query": translated_query,
            "detected_language": active_lang,
            "results": final_results,
            "is_degraded_mode": self.is_degraded_mode,
        }
