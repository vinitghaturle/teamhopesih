"""Portal Adapter Interface — Simulation of Public Procurement Portal Integration.

NOTE: Strictly a simulation/mock interface for demonstration purposes.
Does NOT connect to live Government e-Marketplace (GeM) or CPPP production systems.

Simulates:
1. Ingesting a GeM Bid / RFP payload
2. Mapping category & technical specs into Tender Guard analysis format
3. Generating standards recommendations, gap analysis, and deterministic clause pack
4. Translating results into a GeM-compatible Buyer Specification Addendum payload
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class GeMBidItemSimulation(BaseModel):
    item_id: str = Field(..., description="Simulated GeM item line ID", example="ITEM-8492")
    category_name: str = Field(..., description="GeM product category", example="Pipes and Fittings")
    item_title: str = Field(..., description="Item description / specification", example="Supply of HDPE pipes for water supply project")
    quantity: int = Field(1000, description="Quantity")
    delivery_location: str = Field("New Delhi", description="Consignee state/location")
    raw_specifications: str = Field(
        ...,
        description="Pasted technical parameter specifications or tender text",
        example="High density polyethylene pipes PN 10 PE-100 conforming to BIS standards with ISI certification.",
    )


class GeMBidAnalysisRequest(BaseModel):
    bid_number: str = Field(..., description="Simulated GeM bid number", example="GEM/2026/B/948210")
    buyer_department: str = Field("Municipal Engineering Department", example="Central Public Works Department")
    tender_title: str = Field("Civil Works and Water Pipeline Infrastructure", example="Water Supply Augmentation Project")
    items: List[GeMBidItemSimulation]


class GeMAddendumResponse(BaseModel):
    bid_number: str
    is_simulation: bool = True
    simulation_notice: str = "SIMULATION DEMO ONLY: Not connected to live GeM/CPPP production servers."
    recommended_standards_count: int
    standards_summary: List[Dict[str, Any]]
    gem_clause_block: str
    audit_findings: List[Dict[str, Any]]


class PortalAdapterService:
    """Adapter translating between simulated portal data contracts and Tender Guard."""

    def __init__(self, pipeline_service):
        self.pipeline = pipeline_service

    def transform_gem_bid_to_text(self, bid: GeMBidAnalysisRequest) -> str:
        """Converts structured GeM bid items into unified analysis text."""
        sections = [
            f"TENDER NOTICE: {bid.tender_title}",
            f"BID NUMBER: {bid.bid_number}",
            f"BUYER DEPARTMENT: {bid.buyer_department}",
            "",
            "TECHNICAL SPECIFICATION CLAUSES:",
        ]
        for idx, item in enumerate(bid.items, start=1):
            sections.append(f"Item #{idx} ({item.category_name} - {item.item_title}):")
            sections.append(f"{item.raw_specifications}")
            sections.append("")

        return "\n".join(sections)

    def process_gem_bid(self, bid: GeMBidAnalysisRequest) -> Dict[str, Any]:
        """Runs end-to-end analysis on simulated GeM bid and returns portal-formatted payload."""
        unified_text = self.transform_gem_bid_to_text(bid)
        analysis_result = self.pipeline.analyze_tender(
            raw_text=unified_text,
            filename=f"GeM_Bid_{bid.bid_number.replace('/', '_')}.txt",
        )

        stds = analysis_result.get("bill_of_standards", [])
        clause_pack = analysis_result.get("clause_pack", {})
        audit_results = analysis_result.get("audit_results", [])

        summary_list = []
        for s in stds:
            summary_list.append({
                "standard_number": s.get("standard_number"),
                "full_title": s.get("full_title"),
                "latest_year": s.get("version", {}).get("latest_year"),
                "is_compulsory_certification": s.get("is_compulsory_certification"),
                "standard_type": s.get("standard_type"),
            })

        return {
            "bid_number": bid.bid_number,
            "buyer_department": bid.buyer_department,
            "tender_title": bid.tender_title,
            "is_simulation": True,
            "simulation_notice": "SIMULATION DEMO ONLY: Prototype demonstrated for Smart India Hackathon (SIH 2026). Not affiliated with or connected to live GeM / CPPP production portals.",
            "recommended_standards_count": len(stds),
            "standards_summary": summary_list,
            "gem_clause_block": clause_pack.get("markdown", ""),
            "audit_findings": audit_results,
            "raw_analysis": analysis_result,
        }
