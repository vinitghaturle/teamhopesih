"""Tender Guard — Comprehensive API Smoke Test Suite.

Exercises all endpoints:
  - GET /
  - GET /api/health
  - GET /api/standards
  - POST /api/analyze (English, Hindi, Marathi, File simulation)
  - POST /api/review
  - GET /api/reviews/{request_id}
  - POST /api/export/docx
  - POST /api/export/pdf
  - POST /api/export/markdown
  - POST /api/export/json
  - POST /api/portal/simulate-gem-bid
  - GET /api/portal/widget-config
  - GET /api/debug/{request_id}
"""

import sys
import json
from fastapi.testclient import TestClient

# Add app/backend to sys.path
sys.path.insert(0, "app/backend")

from database import init_db
from main import app

client = TestClient(app)


def run_smoke_tests():
    print("=" * 60)
    print("  TENDER GUARD — END-TO-END SMOKE TEST SUITE")
    print("=" * 60)

    # 1. Root & Health Check
    print("\n[1/12] Testing GET / and GET /api/health ...")
    r = client.get("/")
    assert r.status_code == 200, f"Root failed: {r.status_code}"
    print("  [OK] GET / => 200 OK")

    r = client.get("/api/health")
    assert r.status_code == 200, f"Health failed: {r.status_code}"
    health_data = r.json()
    assert health_data["status"] == "healthy"
    print(f"  [OK] GET /api/health => 200 OK (Standards in DB: {health_data['database']['standards_count']}, Neural: {health_data['models']['neural_ready']})")

    # 2. Standards Catalogue
    print("\n[2/12] Testing GET /api/standards ...")
    r = client.get("/api/standards?search=cement")
    assert r.status_code == 200
    stds = r.json()
    assert len(stds) > 0
    print(f"  [OK] GET /api/standards?search=cement => 200 OK ({len(stds)} records found)")

    # 3. Analyze Tender (English text)
    print("\n[3/12] Testing POST /api/analyze (English text) ...")
    sample_spec = (
        "1. High strength deformed steel bars conforming to IS 1786:1985 Grade Fe 415.\n"
        "2. Structural concrete mix proportioning conforming to IS 456:1978.\n"
        "3. Ordinary Portland Cement 43 Grade conforming to IS 8112:1989."
    )
    r = client.post("/api/analyze", data={"text": sample_spec})
    assert r.status_code == 200, f"Analyze failed: {r.text}"
    res = r.json()
    req_id = res["request_id"]
    assert len(res["bill_of_standards"]) > 0
    assert len(res["audit_results"]) > 0
    assert "clause_pack" in res
    print(f"  [OK] POST /api/analyze => 200 OK (Req ID: {req_id}, Recommended: {len(res['bill_of_standards'])}, Stale Citations: {len(res['audit_results'])})")

    # 4. Analyze Tender (Hindi query)
    print("\n[4/12] Testing POST /api/analyze (Hindi text) ...")
    r_hi = client.post("/api/analyze", data={"text": "सरकारी भवन के निर्माण के लिए 43 ग्रेड साधारण पोर्टलैंड सीमेंट"})
    assert r_hi.status_code == 200
    assert r_hi.json()["detected_language"] in ("hi", "auto")
    print(f"  [OK] POST /api/analyze (Hindi) => 200 OK (Detected: {r_hi.json()['detected_language']})")

    # 5. Analyze Tender (Marathi query)
    print("\n[5/12] Testing POST /api/analyze (Marathi text) ...")
    r_mr = client.post("/api/analyze", data={"text": "शासकीय कार्यालयासाठी पॅक केलेले पिण्याचे पाणी जार पुरवठा"})
    assert r_mr.status_code == 200
    assert r_mr.json()["detected_language"] in ("mr", "auto")
    print(f"  [OK] POST /api/analyze (Marathi) => 200 OK (Detected: {r_mr.json()['detected_language']})")

    # 6. Officer Review Submission
    print("\n[6/12] Testing POST /api/review ...")
    r_rev = client.post(
        "/api/review",
        json={
            "request_id": req_id,
            "standard_number": "IS 456",
            "action": "ACCEPT",
            "remarks": "Approved design standard.",
        },
    )
    assert r_rev.status_code == 200
    print(f"  [OK] POST /api/review => 200 OK (Action: {r_rev.json()['action']} for {r_rev.json()['standard_number']})")

    # 7. Get Officer Reviews
    print("\n[7/12] Testing GET /api/reviews/{request_id} ...")
    r_get_rev = client.get(f"/api/reviews/{req_id}")
    assert r_get_rev.status_code == 200
    assert len(r_get_rev.json()) > 0
    print(f"  [OK] GET /api/reviews/{req_id} => 200 OK ({len(r_get_rev.json())} reviews found)")

    # 8. Export DOCX
    print("\n[8/12] Testing POST /api/export/docx ...")
    r_docx = client.post(
        "/api/export/docx",
        json={"tender_title": "Highway Tender", "clause_pack": res["clause_pack"], "request_id": req_id},
    )
    assert r_docx.status_code == 200
    assert len(r_docx.content) > 1000
    print(f"  [OK] POST /api/export/docx => 200 OK ({len(r_docx.content)} bytes)")

    # 9. Export PDF
    print("\n[9/12] Testing POST /api/export/pdf ...")
    r_pdf = client.post(
        "/api/export/pdf",
        json={"tender_title": "Highway Tender", "clause_pack": res["clause_pack"], "request_id": req_id},
    )
    assert r_pdf.status_code == 200
    assert r_pdf.content.startswith(b"%PDF")
    print(f"  [OK] POST /api/export/pdf => 200 OK ({len(r_pdf.content)} bytes PDF)")

    # 10. Export Markdown and JSON
    print("\n[10/12] Testing POST /api/export/markdown and /api/export/json ...")
    r_md = client.post(
        "/api/export/markdown",
        json={"tender_title": "Highway Tender", "clause_pack": res["clause_pack"], "request_id": req_id},
    )
    assert r_md.status_code == 200
    assert "INDIAN STANDARDS" in r_md.text

    r_json = client.post(
        "/api/export/json",
        json={"tender_title": "Highway Tender", "clause_pack": res["clause_pack"], "request_id": req_id},
    )
    assert r_json.status_code == 200
    assert "clauses" in r_json.json()
    print("  [OK] POST /api/export/markdown & /api/export/json => 200 OK")

    # 11. Portal Adapter Simulation
    print("\n[11/12] Testing POST /api/portal/simulate-gem-bid & GET /api/portal/widget-config ...")
    r_portal = client.post(
        "/api/portal/simulate-gem-bid",
        json={
            "bid_number": "GEM/2026/B/90123-SMOKE",
            "buyer_department": "Municipal Works",
            "tender_title": "Water Pipeline Laying",
            "items": [
                {
                    "item_id": "ITEM-1",
                    "category_name": "Piping",
                    "item_title": "uPVC Pipes",
                    "quantity": 100,
                    "delivery_location": "Delhi",
                    "raw_specifications": "Unplasticized PVC pipes for potable water conforming to IS 4985.",
                }
            ],
        },
    )
    assert r_portal.status_code == 200
    assert r_portal.json()["is_simulation"] is True

    r_widget = client.get("/api/portal/widget-config")
    assert r_widget.status_code == 200
    print("  [OK] POST /api/portal/simulate-gem-bid & GET /api/portal/widget-config => 200 OK")

    # 12. Debug Endpoint Trace
    print("\n[12/12] Testing GET /api/debug/{request_id} ...")
    r_dbg = client.get(f"/api/debug/{req_id}")
    assert r_dbg.status_code == 200
    dbg_data = r_dbg.json()
    assert "stages" in dbg_data
    print(f"  [OK] GET /api/debug/{req_id} => 200 OK (Stages tracked: {list(dbg_data['stages'].keys())})")

    print("\n" + "=" * 60)
    print("  ALL 12 API SMOKE TESTS PASSED SUCCESSFULLY (100% HEALTHY)")
    print("=" * 60)


if __name__ == "__main__":
    run_smoke_tests()
