"""Tests for Officer Review workflow persistence and Multi-Format Exports (PDF, DOCX, Markdown, JSON)."""

import pytest
from fastapi.testclient import TestClient
from database import SessionLocal, init_db
from models.schema import OfficerReview
from main import app
from services.export_service import (
    generate_pdf_clause_pack,
    generate_docx_clause_pack,
    generate_markdown_clause_pack,
    generate_json_clause_pack,
)

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    init_db()


def test_officer_review_persistence():
    req_id = "REQ-TEST-REV-001"
    
    # 1. Submit ACCEPT decision
    res = client.post(
        "/api/review",
        json={
            "request_id": req_id,
            "standard_number": "IS 456",
            "action": "ACCEPT",
            "remarks": "Approved general concrete design code.",
            "officer_name": "Executive Engineer",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["action"] == "ACCEPT"
    assert data["standard_number"] == "IS 456"

    # 2. Submit FLAG decision on another standard
    res = client.post(
        "/api/review",
        json={
            "request_id": req_id,
            "standard_number": "IS 8112",
            "action": "FLAG",
            "remarks": "Check consolidation with IS 269 before finalizing.",
            "officer_name": "Executive Engineer",
        },
    )
    assert res.status_code == 200
    assert res.json()["action"] == "FLAG"

    # 3. Fetch reviews for request_id
    res = client.get(f"/api/reviews/{req_id}")
    assert res.status_code == 200
    reviews = res.json()
    assert len(reviews) == 2
    std_numbers = [r["standard_number"] for r in reviews]
    assert "IS 456" in std_numbers
    assert "IS 8112" in std_numbers


def test_export_respects_review_rejection_and_flagging():
    sample_clause_pack = {
        "header": "Technical Specification Clauses",
        "tender_title": "Reinforced Concrete Highway Tender",
        "structured_clauses": [
            {
                "standard_number": "IS 456",
                "full_title": "Code of practice for plain and reinforced concrete",
                "conformance_clause": "Concrete shall conform to IS 456:2000.",
                "certification_clause": "",
                "allied_clauses": [],
                "needs_review": False,
            },
            {
                "standard_number": "IS 1786",
                "full_title": "High strength deformed steel bars and wires for concrete reinforcement",
                "conformance_clause": "Steel reinforcement shall conform to IS 1786:2008.",
                "certification_clause": "Material shall bear standard ISI mark under Scheme-I.",
                "allied_clauses": [],
                "needs_review": False,
            },
            {
                "standard_number": "IS 8112",
                "full_title": "43 grade ordinary Portland cement",
                "conformance_clause": "Cement shall conform to IS 8112:2013.",
                "certification_clause": "Cement bags shall bear mandatory ISI mark.",
                "allied_clauses": [],
                "needs_review": True,
            },
        ],
        "markdown": "Sample MD",
    }

    mock_reviews = [
        {"standard_number": "IS 456", "action": "ACCEPT", "remarks": "Approved"},
        {"standard_number": "IS 1786", "action": "REJECT", "remarks": "Excluded per contractor request"},
        {"standard_number": "IS 8112", "action": "FLAG", "remarks": "Verify 43 grade vs 53 grade"},
    ]

    # JSON Export verification
    json_export = generate_json_clause_pack("Test Tender", sample_clause_pack, reviews=mock_reviews)
    clauses = json_export["clauses"]
    stds_in_export = [c["standard_number"] for c in clauses]
    assert "IS 456" in stds_in_export
    assert "IS 1786" not in stds_in_export, "Rejected standard IS 1786 must be excluded from final export"
    assert "IS 8112" in stds_in_export
    flagged_clause = next(c for c in clauses if c["standard_number"] == "IS 8112")
    assert flagged_clause.get("is_flagged") is True
    assert flagged_clause.get("officer_remarks") == "Verify 43 grade vs 53 grade"

    # Markdown Export verification
    md_export = generate_markdown_clause_pack("Test Tender", sample_clause_pack, reviews=mock_reviews)
    assert "IS 456" in md_export
    assert "IS 1786" not in md_export
    assert "[FLAGGED FOR SUPERVISOR REVIEW]" in md_export

    # DOCX Export verification
    docx_bytes = generate_docx_clause_pack("Test Tender", sample_clause_pack, reviews=mock_reviews)
    assert len(docx_bytes) > 1000

    # PDF Export verification
    pdf_bytes = generate_pdf_clause_pack("Test Tender", sample_clause_pack, reviews=mock_reviews)
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF")
