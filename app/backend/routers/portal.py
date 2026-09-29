"""Portal Simulation Router — Exposes simulated e-Procurement Portal endpoints and widget configuration.

NOTE: Simulation / demo endpoints only.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from services.pipeline_service import TenderPipelineService
from services.portal_adapter import (
    PortalAdapterService,
    GeMBidAnalysisRequest,
    GeMAddendumResponse,
)


router = APIRouter(prefix="/api/portal", tags=["portal-simulation"])


@router.post(
    "/simulate-gem-bid",
    summary="Simulate GeM Bid Standards Verification",
    description="Processes a structured GeM/CPPP bid payload through Tender Guard, returning a standardized Buyer Specification Addendum.",
)
def simulate_gem_bid(
    payload: GeMBidAnalysisRequest,
    db: Session = Depends(get_db),
):
    """
    Simulation of Government e-Marketplace (GeM) bid ingestion.
    Maps bid categories and technical parameters to Indian Standards.
    """
    pipeline = TenderPipelineService(db=db)
    adapter = PortalAdapterService(pipeline_service=pipeline)
    return adapter.process_gem_bid(payload)


@router.get("/widget-config")
def get_widget_config():
    """
    Returns embed configuration and copyable JavaScript snippet for third-party procurement portals.
    """
    js_snippet = (
        '<!-- Tender Guard Embed Widget Snippet -->\n'
        '<div id="tender-guard-root"></div>\n'
        '<script>\n'
        '  (function() {\n'
        '    var iframe = document.createElement("iframe");\n'
        '    iframe.src = "http://localhost:3000/embed";\n'
        '    iframe.style.width = "100%";\n'
        '    iframe.style.height = "600px";\n'
        '    iframe.style.border = "1px solid #334155";\n'
        '    iframe.style.borderRadius = "8px";\n'
        '    document.getElementById("tender-guard-root").appendChild(iframe);\n'
        '  })();\n'
        '</script>'
    )
    return {
        "widget_url": "http://localhost:3000/embed",
        "api_endpoint": "http://localhost:8000/api/analyze",
        "embed_html_snippet": js_snippet,
        "supported_features": [
            "Real-time IS Standard Recommendation",
            "Stale Citation Audit",
            "Compulsory QCO Check",
            "Specification Gap Analysis",
        ],
        "is_simulation": True,
        "disclaimer": "Prototype for demonstration only. Not an official GeM / BIS production release.",
    }
