"""Tender Guard — Stale-Citation Audit Service.

Detects and extracts all Indian Standard citations from tender texts and performs
authoritative metadata lookups in the BIS database to determine validity status:
  - CURRENT: Matches active standard year with no pending amendments.
  - AMENDED: Active standard with published amendments to be incorporated.
  - YEAR_OUTDATED: Tender cites a superseded/older edition year.
  - SUPERSEDED: Standard has been withdrawn and replaced by another IS.
  - NEEDS_REVIEW: Ambiguity or revision consolidation exists in corpus (e.g. IS 269/8112/12269).
  - NOT_IN_CORPUS: Citation is not present in local database ("cannot verify", never guessed).
"""

import re
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from models.schema import Standard


# Regex pattern to match Indian Standard citations
# Matches "IS 456", "IS:456-2000", "IS 1786:1985", "IS 1786 (Part 1)", "IS 8112 & IS 12269"
IS_CITATION_PATTERN = re.compile(
    r"\b(?:IS|is|Is)\s*[:\-]?\s*(?P<num>\d+)(?:\s*(?:\((?:Part|part|Pt\.?)\s*(?P<part1>\d+)\)|Part\s*(?P<part2>\d+)))?(?:\s*[:\-]\s*(?P<year>\d{4}))?",
    re.IGNORECASE,
)


def extract_citations_from_text(text: str) -> List[Dict[str, Any]]:
    """
    Extracts all IS standard citations from raw tender text with optional part and year.
    """
    citations = []
    seen = set()

    for match in IS_CITATION_PATTERN.finditer(text):
        num = match.group("num")
        part = match.group("part1") or match.group("part2")
        year = match.group("year")
        raw = match.group(0).strip()

        std_num = f"IS {num}"
        if part:
            norm_num = f"IS {num} Part {part}"
            full_std_num = f"IS {num} (Part {part})"
        else:
            norm_num = f"IS {num}"
            full_std_num = f"IS {num}"

        key = (full_std_num, year)
        if key in seen:
            continue
        seen.add(key)

        citations.append({
            "raw_citation": raw,
            "standard_number": full_std_num,
            "base_number": std_num,
            "part": part,
            "cited_year": year,
            "normalized_number": norm_num,
        })

    return citations


def audit_tender_citations(text: str, db: Session) -> Dict[str, Any]:
    """
    Performs comprehensive stale-citation audit on all detected IS references.
    
    Returns:
      {
        "cited_standards_detected": ["IS 8112:1989", "IS 456:1978", ...],
        "audit_results": [
            {
                "citation": "IS 8112:1989",
                "standard_number": "IS 8112",
                "status": "NEEDS_REVIEW" | "YEAR_OUTDATED" | "SUPERSEDED" | "AMENDED" | "CURRENT" | "NOT_IN_CORPUS",
                "cited_year": "1989",
                "latest_year": "2013",
                "full_title": "...",
                "active_amendments": ["Amendment No. 1", ...],
                "superseded_by": "IS 269:2015" or None,
                "audit_finding": "...",
                "action_required": "...",
                "needs_review": True/False,
            }, ...
        ],
        "summary": "...",
      }
    """
    extracted = extract_citations_from_text(text)
    cited_list = [c["raw_citation"] for c in extracted]

    audit_results = []
    stale_count = 0
    needs_review_count = 0
    not_in_corpus_count = 0

    from services.retrieval.qualifier_checker import QualifierConflictChecker

    for c in extracted:
        std_num = c["standard_number"]
        base_num = c["base_number"]
        cited_year = c["cited_year"]

        # Database lookup by standard_number or normalized_number
        record = db.query(Standard).filter(
            (Standard.standard_number == std_num) |
            (Standard.normalized_number == std_num) |
            (Standard.standard_number == base_num) |
            (Standard.normalized_number == base_num)
        ).first()

        if not record:
            not_in_corpus_count += 1
            audit_results.append({
                "citation": c["raw_citation"],
                "standard_number": std_num,
                "status": "NOT_IN_CORPUS",
                "cited_year": cited_year,
                "latest_year": None,
                "full_title": None,
                "active_amendments": [],
                "superseded_by": None,
                "provenance": {"source": "model_memory", "verified": False},
                "audit_finding": "Citation not found in local ground truth database (cannot verify, not guessed).",
                "action_required": "Officer must manually verify standard validity on the official BIS portal (services.bis.gov.in).",
                "needs_review": False,
            })
            continue

        latest_year = record.year
        amendments = [f"Amendment No. {a.amendment_number}" for a in record.amendments] if record.amendments else []
        is_cement_group = record.standard_number in ("IS 269", "IS 8112", "IS 12269")
        is_needs_review = bool(record.needs_review or is_cement_group)

        # Check for citation-vs-requirement qualifier conflict (e.g. HDPE in text vs IS 4985 uPVC)
        checker = QualifierConflictChecker([record])
        has_qualifier_conflict, qualifier_reason = checker.check_conflicts(text, record)

        # Determine authoritative status
        replacement = None
        replacement_needs_review = False
        conflict_note = None

        # Conflict notes for dataset differences
        if record.standard_number == "IS 4151":
            conflict_note = "Dataset records IS 4151 edition as 2020 (Protective Helmets for Two Wheeler Riders)."
        elif record.standard_number == "IS 1786":
            conflict_note = "Dataset records Ministry of Steel Quality Control Order (2012 / 2020 revision note)."

        if has_qualifier_conflict:
            status = "CITATION_MISMATCH"
            finding = f"CITATION_MISMATCH: {qualifier_reason}"
            action = f"Specification qualifiers conflict with cited standard {record.standard_number}. Verify correct product specification."
            replacement_needs_review = True
        elif is_needs_review:
            needs_review_count += 1
            replacement_needs_review = True
            if cited_year and latest_year and cited_year != latest_year:
                status = "YEAR_OUTDATED"
            else:
                status = "NEEDS_REVIEW"
            finding = "our records conflict; confirm on the official BIS page"
            action = "Procurement officer must verify the applicable standard edition and grade directly on services.bis.gov.in."
            replacement = "IS 269:2015" if is_cement_group else None

        elif record.superseded_by or (cited_year and latest_year and cited_year != latest_year):
            stale_count += 1
            status = "SUPERSEDED"
            replacement = record.superseded_by or f"{record.standard_number}:{latest_year}"
            amd_note = f" (incorporating {len(amendments)} active amendments)" if amendments else ""
            finding = f"Tender cites {c['raw_citation']}, which has been superseded by {replacement}{amd_note}."
            action = f"Replace citation with active standard {replacement}."

        elif len(amendments) > 0:
            status = "AMENDED"
            finding = f"Standard {record.standard_number}:{latest_year} is active with {len(amendments)} published amendment(s)."
            action = f"Include standard {record.standard_number}:{latest_year} with explicit requirement for amendments: {', '.join(amendments)}."

        else:
            status = "CURRENT"
            finding = f"Standard {record.standard_number}:{latest_year} is the current active edition with no pending amendments."
            action = "Citation is current and valid."

        # Provenance for cited metadata
        provenance = {
            "source": "official_dataset" if getattr(record, "is_verified", False) else "model_memory",
            "verified": bool(getattr(record, "is_verified", False)),
        }

        audit_results.append({
            "citation": c["raw_citation"],
            "standard_number": record.standard_number,
            "status": status,
            "cited_year": cited_year,
            "latest_year": latest_year,
            "full_title": record.full_title,
            "active_amendments": amendments,
            "superseded_by": replacement,
            "replacement": replacement,
            "replacement_needs_review": replacement_needs_review,
            "conflict_note": conflict_note,
            "provenance": provenance,
            "audit_finding": finding,
            "warning": finding,
            "action_required": action,
            "needs_review": is_needs_review,
        })

    summary = (
        f"Audited {len(extracted)} standard citation(s): "
        f"{sum(1 for r in audit_results if r['status'] == 'CURRENT')} current, "
        f"{sum(1 for r in audit_results if r['status'] == 'AMENDED')} amended, "
        f"{stale_count} stale/outdated, "
        f"{needs_review_count} requiring manual review, "
        f"{not_in_corpus_count} unverified (not in corpus)."
    )

    return {
        "cited_standards_detected": cited_list,
        "audit_results": audit_results,
        "summary": summary,
        "stale_count": stale_count,
        "needs_review_count": needs_review_count,
        "not_in_corpus_count": not_in_corpus_count,
    }
