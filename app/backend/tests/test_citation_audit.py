"""Tender Guard — Stale-Citation Audit Unit & Integration Tests.

Validates:
  - Regex extraction across diverse syntax ("IS 456", "IS:456-2000", "IS 1786:1985", "IS 8112 & IS 12269")
  - Accurate status mapping: CURRENT, AMENDED, YEAR_OUTDATED, SUPERSEDED, NEEDS_REVIEW, NOT_IN_CORPUS
  - Full audit of stale_construction_tender.txt fixture
"""

import pytest
from pathlib import Path

from database import SessionLocal
from services.citation_audit import extract_citations_from_text, audit_tender_citations

BASE_DIR = Path(__file__).resolve().parent.parent
SAMPLE_DIR = BASE_DIR / "data" / "sample_tenders"


def test_regex_extraction_varieties():
    sample_text = (
        "Project requires compliance with IS 456:1978 and IS:1786-2008 for reinforcement. "
        "Also refer to IS 16102 (Part 1) and IS 8112 & IS 12269 for cement mixing."
    )
    extracted = extract_citations_from_text(sample_text)
    cited_numbers = [c["standard_number"] for c in extracted]

    assert "IS 456" in cited_numbers
    assert "IS 1786" in cited_numbers
    assert "IS 16102 (Part 1)" in cited_numbers
    assert "IS 8112" in cited_numbers
    assert "IS 12269" in cited_numbers


def test_audit_stale_construction_tender():
    stale_file = SAMPLE_DIR / "stale_construction_tender.txt"
    assert stale_file.exists(), f"Missing fixture file {stale_file}"

    text = stale_file.read_text(encoding="utf-8")
    db = SessionLocal()
    try:
        res = audit_tender_citations(text, db)
        
        assert len(res["cited_standards_detected"]) >= 5
        results_by_std = {r["standard_number"]: r for r in res["audit_results"]}

        # IS 456:1978 should be SUPERSEDED (db year is 2000)
        assert "IS 456" in results_by_std
        is456 = results_by_std["IS 456"]
        assert is456["status"] == "SUPERSEDED"
        assert is456["cited_year"] == "1978"
        assert is456["latest_year"] == "2000"
        assert is456["replacement"] == "IS 456:2000"

        # IS 1786:1985 should be SUPERSEDED (db year is 2008)
        assert "IS 1786" in results_by_std
        is1786 = results_by_std["IS 1786"]
        assert is1786["status"] == "SUPERSEDED"
        assert is1786["cited_year"] == "1985"
        assert is1786["latest_year"] == "2008"
        assert is1786["replacement"] == "IS 1786:2008"

        # IS 8112:1989 should be YEAR_OUTDATED with replacement_needs_review
        assert "IS 8112" in results_by_std
        is8112 = results_by_std["IS 8112"]
        assert is8112["status"] == "YEAR_OUTDATED"
        assert is8112["replacement_needs_review"] is True
        assert "records conflict" in is8112["warning"]

        # IS 2925:1984 (not in 100-standard corpus) should be NOT_IN_CORPUS
        assert "IS 2925" in results_by_std
        is2925 = results_by_std["IS 2925"]
        assert is2925["status"] == "NOT_IN_CORPUS"
        assert is2925["latest_year"] is None

        # Summary check
        assert res["stale_count"] >= 2
        assert res["needs_review_count"] >= 1
        assert res["not_in_corpus_count"] >= 1
    finally:
        db.close()


def test_citation_vs_requirement_mismatch():
    """Validates that citing uPVC standard IS 4985 in an HDPE requirement triggers CITATION_MISMATCH."""
    text = "Supply of Polyethylene pipes (HDPE) for drinking water supply distribution networks conforming to IS 4985:2021."
    db = SessionLocal()
    try:
        res = audit_tender_citations(text, db)
        assert len(res["audit_results"]) == 1
        audit_item = res["audit_results"][0]
        assert audit_item["standard_number"] == "IS 4985"
        assert audit_item["status"] == "CITATION_MISMATCH"
        assert "HDPE" in audit_item["audit_finding"] or "hdpe" in audit_item["audit_finding"].lower()
    finally:
        db.close()

