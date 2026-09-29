"""Tender Guard - Full Analysis Pipeline Service.

Coordinates:
  1. Parsing (PDF, DOCX, TXT)
  2. Language detection & translation/normalization
  3. Clause extraction & technical parameter identification
  4. Per-requirement Hybrid Retrieval (FAISS + BM25 + RRF + Cross-Encoder)
  5. Allied graph expansion (1-hop, grouped by role, STUB nodes)
  6. Version block (latest year, amendments, supersedes)
  7. Certification / QCO block (scheme, is_compulsory_certification, legal_basis + legal_basis_verified)
  8. Merged & deduplicated Bill of Standards with evidence links
  9. Integrity checks: needs_review warnings, hidden unverified limits_text
  10. Debug tracking per request_id for /api/debug/{request_id}
"""

import re
import uuid
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session


from models.schema import Standard, StandardAmendment, Tender, ExtractedRequirement, Recommendation
from services.document_parser import extract_text
from services.multilingual import MultilingualService
from services.extractor import RequirementExtractor, TenderRequirement
from services.retrieval.pipeline import RetrievalPipeline
from services.allied_graph import AlliedGraphService
from services.citation_audit import audit_tender_citations
from services.gap_analyzer import analyze_tender_gaps
from services.clause_pack import generate_clause_pack


# In-memory debug trace store (keyed by request_id)
DEBUG_TRACES: Dict[str, Dict[str, Any]] = {}

_SHARED_RETRIEVAL_PIPELINE: Optional[RetrievalPipeline] = None


def get_shared_retrieval_pipeline() -> RetrievalPipeline:
    global _SHARED_RETRIEVAL_PIPELINE
    if _SHARED_RETRIEVAL_PIPELINE is None:
        _SHARED_RETRIEVAL_PIPELINE = RetrievalPipeline(use_neural=True)
    return _SHARED_RETRIEVAL_PIPELINE


class TenderPipelineService:
    def __init__(self, db: Session, retrieval_pipeline: Optional[RetrievalPipeline] = None):
        self.db = db
        self.retrieval = retrieval_pipeline or get_shared_retrieval_pipeline()
        self.multilingual = MultilingualService()
        self.extractor = RequirementExtractor()
        self.allied_graph = AlliedGraphService(db)


    def analyze_tender(
        self,
        raw_text: Optional[str] = None,
        file_bytes: Optional[bytes] = None,
        filename: Optional[str] = None,
        force_language: Optional[str] = None,
    ) -> Dict[str, Any]:
        request_id = f"REQ-TRC-{uuid.uuid4().hex[:12].upper()}"
        debug_trace: Dict[str, Any] = {
            "request_id": request_id,
            "filename": filename or "pasted_text.txt",
            "stages": {},
        }

        # Stage 1: Document Parsing
        if file_bytes and filename:
            doc_text = extract_text(file_bytes, filename)
        elif raw_text and raw_text.strip():
            doc_text = raw_text.strip()
        else:
            raise ValueError("No tender content provided. Please upload a file or enter text.")

        if len(doc_text.strip()) < 10:
            raise ValueError("Tender text is too short to analyze.")

        debug_trace["stages"]["document_parsing"] = {
            "raw_text_length": len(doc_text),
            "char_preview": doc_text[:200],
        }

        # Stage 2: Language Detection & Normalization
        lang = force_language or self.multilingual.detect_language(doc_text)
        translated_text = self.multilingual.translate_query(doc_text, source_lang=lang)
        
        debug_trace["stages"]["language_processing"] = {
            "detected_language": lang,
            "is_multilingual": lang != "en",
            "normalized_char_preview": translated_text[:200],
        }

        # Stage 3: Requirement Clause Extraction
        clauses: List[TenderRequirement] = self.extractor.extract_clauses(translated_text)
        debug_trace["stages"]["clause_extraction"] = {
            "total_clauses": len(clauses),
            "clauses": [c.to_dict() for c in clauses],
        }

        # Stage 4: Per-Requirement Hybrid Retrieval & Grounding
        analyzed_requirements: List[Dict[str, Any]] = []
        retrieval_debug: List[Dict[str, Any]] = []
        
        # Standards aggregation map for Bill of Standards: std_number -> aggregated dict
        bill_of_standards_map: Dict[str, Dict[str, Any]] = {}

        for clause in clauses:
            clause_dict = clause.to_dict()
            clause_text = clause.text

            # Run hybrid retrieval with calibrated floor
            search_res = self.retrieval.search(clause_text, top_k=3)
            status = search_res["status"]
            retrieved_items = search_res.get("results", [])

            req_debug_entry = {
                "clause_id": clause_dict["id"],
                "clause_text": clause_text,
                "status": status,
                "dense_rankings": search_res.get("debug", {}).get("dense_ranks", []),
                "bm25_rankings": search_res.get("debug", {}).get("bm25_ranks", []),
                "rrf_fused": search_res.get("debug", {}).get("rrf_ranks", []),
                "rerank_scores": search_res.get("debug", {}).get("rerank_scores", []),
            }
            retrieval_debug.append(req_debug_entry)

            matched_standards_for_req: List[Dict[str, Any]] = []

            if status in ("MATCH_FOUND", "CLOSE_BUT_NOT_EXACT") and retrieved_items:
                for item in retrieved_items:
                    std_id = item.get("standard_id")
                    std_record = None
                    if std_id:
                        std_record = self.db.query(Standard).filter(Standard.standard_id == std_id).first()
                    if not std_record:
                        std_num = item.get("standard_number")
                        std_record = self.db.query(Standard).filter(
                            (Standard.normalized_number == std_num) | (Standard.standard_number == std_num)
                        ).first()
                    
                    if not std_record:
                        continue

                    # Assemble Version Block
                    amendments = (
                        self.db.query(StandardAmendment)
                        .filter(StandardAmendment.standard_id == std_record.standard_id)
                        .order_by(StandardAmendment.amendment_number.asc())
                        .all()
                    )
                    version_block = {
                        "latest_year": std_record.year,
                        "latest_year_provenance": {"source": "official_dataset", "verified": True},
                        "status": std_record.status,
                        "publication_date": std_record.publication_date,
                        "revision_date": std_record.revision_date,
                        "supersedes": std_record.supersedes,
                        "superseded_by": std_record.superseded_by,
                        "amendments_count": len(amendments),
                        "amendments": [
                            {
                                "amendment_number": a.amendment_number,
                                "year": a.year,
                                "notes": a.notes,
                                "verified": a.verified,
                                "provenance": {
                                    "source": "official_dataset" if a.verified else "ai_drafted",
                                    "verified": bool(a.verified),
                                },
                            }
                            for a in amendments
                        ],
                    }

                    # Assemble Certification / QCO Block (never expose unverified legal_basis as verified fact)
                    cert_block = {
                        "scheme": std_record.scheme,
                        "certification_route": std_record.certification_route,
                        "is_compulsory_certification": std_record.is_compulsory_certification,
                        "legal_basis": std_record.legal_basis if std_record.legal_basis_verified else None,
                        "legal_basis_verified": std_record.legal_basis_verified,
                        "legal_basis_unverified_note": std_record.legal_basis if not std_record.legal_basis_verified else None,
                        "provenance": {
                            "source": "official_dataset" if std_record.legal_basis_verified else "ai_drafted",
                            "verified": bool(std_record.legal_basis_verified),
                        },
                    }

                    # Assemble 1-Hop Allied Standards Graph (with STUB nodes)
                    allied_block = self.allied_graph.get_allied_standards(std_record.standard_id)

                    clean_std_number = re.sub(r"\s+", " ", std_record.normalized_number).strip()

                    # Needs review warning text
                    needs_review_warning = None
                    if std_record.standard_number in ("IS 269", "IS 8112", "IS 12269"):
                        needs_review_warning = "our records conflict; confirm on the official BIS page"
                    elif std_record.needs_review:
                        needs_review_warning = (
                            f"Standard {clean_std_number} requires official review. "
                            f"{std_record.verification_note or 'our records conflict; confirm on the official BIS page'}"
                        )

                    is_exact = (status == "MATCH_FOUND")
                    match_band = item.get("confidence_band", "HIGH") if is_exact else "CLOSE_BUT_NOT_EXACT"

                    std_match_payload = {
                        "standard_id": std_record.standard_id,
                        "standard_number": clean_std_number,
                        "standard_type": getattr(std_record, "standard_type", "product_spec"),
                        "full_title": std_record.full_title,
                        "title_provenance": {"source": "official_dataset", "verified": bool(std_record.is_verified)},
                        "short_title": std_record.short_title,
                        "product_category": std_record.product_category,
                        "industry": std_record.industry,
                        "is_exact_match": is_exact,
                        "qualifier_warning": search_res.get("relevance_reason") if not is_exact else None,
                        "match_strength": match_band,
                        "dense_rank": item.get("dense_rank"),
                        "bm25_rank": item.get("bm25_rank"),
                        "scope_excerpt": std_record.scope,
                        "document_url": std_record.document_url,
                        "parameter_names": std_record.parameter_names,  # limits_text omitted unless verified
                        "needs_review": bool(std_record.needs_review or std_record.standard_number in ("IS 269", "IS 8112", "IS 12269")),
                        "needs_review_warning": needs_review_warning,
                        "version": version_block,
                        "certification": cert_block,
                        "allied_standards": allied_block,
                    }

                    matched_standards_for_req.append(std_match_payload)

                    # Aggregate into Bill of Standards only if it is an exact confident match
                    if is_exact:
                        if clean_std_number not in bill_of_standards_map:
                            bill_of_standards_map[clean_std_number] = {
                                "standard_id": std_record.standard_id,
                                "standard_number": clean_std_number,
                                "standard_type": getattr(std_record, "standard_type", "product_spec"),
                                "full_title": std_record.full_title,
                                "title_provenance": {"source": "official_dataset", "verified": bool(std_record.is_verified)},
                                "short_title": std_record.short_title,
                                "product_category": std_record.product_category,
                                "industry": std_record.industry,
                                "is_compulsory_certification": std_record.is_compulsory_certification,
                                "version": version_block,
                                "certification": cert_block,
                                "allied_standards": allied_block,
                                "parameter_names": std_record.parameter_names,
                                "needs_review": bool(std_record.needs_review or std_record.standard_number in ("IS 269", "IS 8112", "IS 12269")),
                                "needs_review_warning": needs_review_warning,
                                "referenced_by_requirements": [
                                    {
                                        "requirement_id": clause_dict["id"],
                                        "clause_text": clause_text,
                                        "category": clause_dict["category"],
                                    }
                                ],
                            }
                        else:
                            bill_of_standards_map[clean_std_number]["referenced_by_requirements"].append({
                                "requirement_id": clause_dict["id"],
                                "clause_text": clause_text,
                                "category": clause_dict["category"],
                            })

            clause_result = {
                "id": clause_dict["id"],
                "clause_text": clause_text,
                "category": clause_dict["category"],
                "technical_entities": clause.entities,
                "status": status,
                "matched_standards": matched_standards_for_req,
            }
            analyzed_requirements.append(clause_result)

        debug_trace["stages"]["retrieval_and_reranking"] = retrieval_debug

        # Stage 5: Stale-Citation Audit (Phase 4 USP)
        audit_payload = audit_tender_citations(doc_text, self.db)
        cited_standards = audit_payload.get("cited_standards_detected", [])
        audit_results = audit_payload.get("audit_results", [])
        debug_trace["stages"]["stale_citation_audit"] = audit_payload

        # Stage 6: Specification Topic Gap Check (Phase 4 USP)
        recommended_stds_list = list(bill_of_standards_map.values())
        gap_results = analyze_tender_gaps(doc_text, recommended_stds_list)
        debug_trace["stages"]["gap_analysis"] = gap_results

        # Stage 7: Deterministic Clause Pack Generation (Phase 4 USP)
        tender_title = filename or "Tender Technical Specification"
        clause_pack = generate_clause_pack(tender_title, recommended_stds_list, db=self.db)
        debug_trace["stages"]["clause_pack"] = {
            "total_clauses": len(clause_pack.get("structured_clauses", [])),
            "has_markdown": bool(clause_pack.get("markdown")),
        }

        DEBUG_TRACES[request_id] = debug_trace

        matched_count = sum(1 for r in analyzed_requirements if r.get("status") == "MATCH_FOUND")
        close_count = sum(1 for r in analyzed_requirements if r.get("status") == "CLOSE_BUT_NOT_EXACT")
        unmatched_count = sum(1 for r in analyzed_requirements if r.get("status") == "NO_CONFIDENT_MATCH")
        stale_count = sum(1 for a in audit_results if a.get("status") in ("SUPERSEDED", "AMENDED", "YEAR_OUTDATED"))

        summary_block = {
            "total_clauses": len(clauses),
            "matched_clauses": matched_count,
            "close_matches": close_count,
            "unmatched_clauses": unmatched_count,
            "stale_citations_detected": stale_count,
            "distinct_standards_recommended": len(recommended_stds_list),
        }

        # Prepare final response payload
        response = {
            "request_id": request_id,
            "filename": filename or "pasted_text.txt",
            "tender_title": tender_title,
            "detected_language": lang,
            "is_translated": lang != "en",
            "is_degraded_mode": not getattr(self.retrieval, "neural_available", True),
            "total_clauses_analyzed": len(clauses),
            "summary": summary_block,
            "requirements": analyzed_requirements,
            "bill_of_standards": recommended_stds_list,
            # Populated Phase 4 Fields
            "cited_standards_detected": cited_standards,
            "audit_results": audit_results,
            "audit_summary": audit_payload.get("audit_summary", f"{len(cited_standards)} citations detected in tender text."),
            "gap_results": gap_results,
            "clause_pack": clause_pack,
        }

        return response
