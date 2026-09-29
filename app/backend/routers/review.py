"""Officer Review Router — Persists procurement officer accept, reject, and flag decisions.
"""

from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models.schema import OfficerReview


router = APIRouter(prefix="/api", tags=["review"])


class ReviewSubmission(BaseModel):
    request_id: str
    standard_number: str
    action: str  # "ACCEPT" | "REJECT" | "FLAG"
    remarks: Optional[str] = None
    officer_name: Optional[str] = "Procurement Officer"


class ReviewResponse(BaseModel):
    id: int
    request_id: str
    standard_number: str
    action: str
    remarks: Optional[str]
    officer_name: str
    updated_at: str


@router.post("/review", response_model=ReviewResponse)
def submit_officer_review(
    payload: ReviewSubmission,
    db: Session = Depends(get_db),
):
    """
    Records or updates a procurement officer's review decision for a standard.
    
    Actions:
      - ACCEPT: Officer approves inclusion in tender document
      - REJECT: Standard is omitted from final clause pack exports
      - FLAG: Marked for supervisor review or clarification
    """
    action_upper = payload.action.upper()
    if action_upper not in ("ACCEPT", "REJECT", "FLAG"):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid action '{payload.action}'. Must be 'ACCEPT', 'REJECT', or 'FLAG'.",
        )

    clean_std = payload.standard_number.strip().upper()

    existing = (
        db.query(OfficerReview)
        .filter(
            OfficerReview.request_id == payload.request_id,
            OfficerReview.standard_number == clean_std,
        )
        .first()
    )

    if existing:
        existing.action = action_upper
        existing.remarks = payload.remarks
        existing.officer_name = payload.officer_name or "Procurement Officer"
        existing.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        target_record = existing
    else:
        new_review = OfficerReview(
            request_id=payload.request_id,
            standard_number=clean_std,
            action=action_upper,
            remarks=payload.remarks,
            officer_name=payload.officer_name or "Procurement Officer",
        )
        db.add(new_review)
        db.commit()
        db.refresh(new_review)
        target_record = new_review

    return ReviewResponse(
        id=target_record.id,
        request_id=target_record.request_id,
        standard_number=target_record.standard_number,
        action=target_record.action,
        remarks=target_record.remarks,
        officer_name=target_record.officer_name,
        updated_at=target_record.updated_at.isoformat(),
    )


@router.get("/reviews/{request_id}", response_model=List[ReviewResponse])
def get_officer_reviews(
    request_id: str,
    db: Session = Depends(get_db),
):
    """
    Retrieves all officer review actions recorded for a given analysis request_id.
    """
    reviews = (
        db.query(OfficerReview)
        .filter(OfficerReview.request_id == request_id)
        .order_by(OfficerReview.updated_at.desc())
        .all()
    )
    return [
        ReviewResponse(
            id=r.id,
            request_id=r.request_id,
            standard_number=r.standard_number,
            action=r.action,
            remarks=r.remarks,
            officer_name=r.officer_name,
            updated_at=r.updated_at.isoformat(),
        )
        for r in reviews
    ]
