"""Standards Catalogue & Sample Tenders Router.

Provides:
  - GET /api/standards (search and filter by category/sector)
  - GET /api/sample-tenders (retrieve sample tenders for testing)
"""

import json
from pathlib import Path
from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from database import get_db
from models.schema import Standard, StandardAmendment

router = APIRouter(prefix="/api", tags=["standards"])

BASE_DIR = Path(__file__).resolve().parent.parent
SAMPLE_DIR = BASE_DIR / "data" / "sample_tenders"


@router.get("/standards")
def list_standards(
    search: Optional[str] = Query(None, description="Search standard number or title"),
    category: Optional[str] = Query(None, description="Filter by product category"),
    db: Session = Depends(get_db),
):
    query = db.query(Standard)
    if search:
        s = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Standard.standard_number.ilike(s),
                Standard.full_title.ilike(s),
                Standard.short_title.ilike(s),
                Standard.scope.ilike(s),
            )
        )
    if category:
        query = query.filter(Standard.product_category.ilike(f"%{category.strip()}%"))

    standards = query.order_by(Standard.standard_number.asc()).all()

    results = []
    for std in standards:
        amendments = [f"Amendment No. {a.amendment_number}" for a in std.amendments] if std.amendments else []
        results.append({
            "standard_id": std.standard_id,
            "standard_number": std.standard_number,
            "normalized_number": std.normalized_number,
            "standard_type": std.standard_type,
            "year": std.year,
            "full_title": std.full_title,
            "short_title": std.short_title,
            "product_category": std.product_category,
            "industry": std.industry,
            "scheme": std.scheme,
            "is_compulsory_certification": std.is_compulsory_certification,
            "status": std.status,
            "scope": std.scope,
            "amendments_count": len(amendments),
            "amendments": amendments,
            "needs_review": std.needs_review,
            "document_url": std.document_url,
        })
    return results


@router.get("/sample-tenders")
def get_sample_tenders():
    samples = []
    if SAMPLE_DIR.exists():
        for f in sorted(SAMPLE_DIR.glob("*.txt")):
            text = f.read_text(encoding="utf-8")
            samples.append({
                "id": f.stem,
                "name": f.stem.replace("_", " ").title(),
                "filename": f.name,
                "text": text,
            })
    return samples
