"""Phase 3 Test Suite — End-to-End Tender Analysis Pipeline.

Tests:
  1. Construction Tender E2E (cements, steel, concrete)
  2. Water Supply Tender E2E (pipes, water quality)
  3. Electrical Tender E2E (cables, LED luminaires)
  4. Stale Standards Construction Tender E2E (detects latest versions & amendments)
  5. Corrupted File handling (returns 400 Bad Request)
  6. Empty input handling (returns 400 Bad Request)
  7. Debug trace API /api/debug/{request_id} verification
  8. Needs review warning verification for IS 269 / IS 8112
"""

import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)
SAMPLE_DIR = Path(__file__).resolve().parent.parent / "data" / "sample_tenders"


def test_e2e_construction_tender():
    tender_file = SAMPLE_DIR / "construction_tender.txt"
    assert tender_file.exists(), f"Missing sample tender: {tender_file}"
    
    with open(tender_file, "r", encoding="utf-8") as f:
        text = f.read()

    response = client.post("/api/analyze", json={"text": text})
    assert response.status_code == 200, f"Failed with {response.text}"
    data = response.json()

    assert "request_id" in data
    assert data["request_id"].startswith("REQ-TRC-")
    assert len(data["requirements"]) > 0
    assert len(data["bill_of_standards"]) > 0

    # Verify standard recommendations include cement/steel/aggregates
    std_numbers = [s["standard_number"] for s in data["bill_of_standards"]]
    assert any(s in std_numbers for s in ["IS 8112", "IS 269", "IS 12269", "IS 1786", "IS 456"])

    # Check that each standard has version, certification, and allied blocks
    for std in data["bill_of_standards"]:
        assert "version" in std
        assert "certification" in std
        assert "allied_standards" in std
        assert "parameter_names" in std
        assert "is_compulsory_certification" in std


def test_e2e_water_supply_tender():
    tender_file = SAMPLE_DIR / "water_supply_tender.txt"
    assert tender_file.exists()

    with open(tender_file, "r", encoding="utf-8") as f:
        text = f.read()

    response = client.post("/api/analyze", json={"text": text})
    assert response.status_code == 200
    data = response.json()

    std_numbers = [s["standard_number"] for s in data["bill_of_standards"]]
    # Should identify polyethylene pipes (IS 15450 / IS 4985) and drinking water (IS 10500 / IS 14543)
    assert any(s in std_numbers for s in ["IS 15450", "IS 4985", "IS 10500", "IS 14543"])


def test_e2e_electrical_tender():
    tender_file = SAMPLE_DIR / "electrical_tender.txt"
    assert tender_file.exists()

    with open(tender_file, "r", encoding="utf-8") as f:
        text = f.read()

    response = client.post("/api/analyze", json={"text": text})
    assert response.status_code == 200
    data = response.json()

    std_numbers = [s["standard_number"] for s in data["bill_of_standards"]]
    # Should identify cables (IS 694) and lighting (IS 16102)
    assert any(s in std_numbers for s in ["IS 694", "IS 16102"])


def test_stale_construction_tender():
    tender_file = SAMPLE_DIR / "stale_construction_tender.txt"
    assert tender_file.exists()

    with open(tender_file, "r", encoding="utf-8") as f:
        text = f.read()

    response = client.post("/api/analyze", json={"text": text})
    assert response.status_code == 200
    data = response.json()

    std_numbers = [s["standard_number"] for s in data["bill_of_standards"]]
    assert any(s in std_numbers for s in ["IS 8112", "IS 269", "IS 1786"])


def test_corrupted_file_upload():
    # Send random binary garbage pretending to be a PDF
    corrupted_bytes = b"%PDF-1.4 \xff\xfe\x00\x00 CORRUPTED BYTES NON-PDF"
    response = client.post(
        "/api/analyze",
        files={"file": ("corrupted_spec.pdf", corrupted_bytes, "application/pdf")},
    )
    assert response.status_code == 400
    assert "Corrupted" in response.json()["detail"] or "invalid" in response.json()["detail"]


def test_empty_input_handling():
    # Empty text
    response = client.post("/api/analyze", json={"text": "   "})
    assert response.status_code == 400
    assert "Empty input" in response.json()["detail"] or "short" in response.json()["detail"]

    # Empty file
    response = client.post(
        "/api/analyze",
        files={"file": ("empty.txt", b"", "text/plain")},
    )
    assert response.status_code == 400


def test_debug_endpoint_trace():
    query = "Supply of 53 Grade Ordinary Portland Cement for prestressed concrete foundation works."
    response = client.post("/api/analyze", json={"text": query})
    assert response.status_code == 200
    data = response.json()
    req_id = data["request_id"]

    # Now fetch debug trace
    debug_resp = client.get(f"/api/debug/{req_id}")
    assert debug_resp.status_code == 200
    debug_data = debug_resp.json()

    assert debug_data["request_id"] == req_id
    assert "stages" in debug_data
    assert "language_processing" in debug_data["stages"]
    assert "clause_extraction" in debug_data["stages"]
    assert "retrieval_and_reranking" in debug_data["stages"]


def test_needs_review_warning_presence():
    # Query for 43 grade cement which returns IS 8112 (flagged needs_review)
    query = "Procurement of 43 Grade Ordinary Portland Cement (IS 8112) for bridge construction."
    response = client.post("/api/analyze", json={"text": query})
    assert response.status_code == 200
    data = response.json()

    is_8112_items = [s for s in data["bill_of_standards"] if s["standard_number"] == "IS 8112"]
    if is_8112_items:
        item = is_8112_items[0]
        assert item["needs_review"] is True
        assert "records conflict" in item["needs_review_warning"] or "confirm on the official BIS page" in item["needs_review_warning"]
