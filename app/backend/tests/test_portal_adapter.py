"""Tests for Portal Adapter Simulation and GeM Bid Processing."""

import pytest
from fastapi.testclient import TestClient
from database import init_db
from main import app

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    init_db()


def test_gem_bid_simulation_endpoint():
    payload = {
        "bid_number": "GEM/2026/B/10042-TEST",
        "buyer_department": "Public Works Department Delhi",
        "tender_title": "Construction of Concrete Pavement",
        "items": [
            {
                "item_id": "ITEM-1",
                "category_name": "Cement & Concrete",
                "item_title": "43 Grade Ordinary Portland Cement",
                "quantity": 500,
                "delivery_location": "New Delhi",
                "raw_specifications": "Ordinary Portland Cement 43 Grade conforming to IS 8112:1989.",
            }
        ],
    }

    res = client.post("/api/portal/simulate-gem-bid", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["bid_number"] == "GEM/2026/B/10042-TEST"
    assert data["is_simulation"] is True
    assert "SIMULATION DEMO ONLY" in data["simulation_notice"]
    assert "gem_clause_block" in data
    assert len(data["standards_summary"]) > 0


def test_widget_config_endpoint():
    res = client.get("/api/portal/widget-config")
    assert res.status_code == 200
    data = res.json()
    assert data["is_simulation"] is True
    assert "iframe" in data["embed_html_snippet"]
    assert "http://localhost:3000/embed" in data["widget_url"]
