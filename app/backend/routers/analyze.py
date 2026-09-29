"""Tender Analysis Router — POST /api/analyze and GET /api/debug/{request_id}
"""

import json
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Form, File, UploadFile
from sqlalchemy.orm import Session

from database import get_db
from services.pipeline_service import TenderPipelineService, DEBUG_TRACES


router = APIRouter(prefix="/api", tags=["analysis"])


@router.post("/analyze")
async def analyze_tender(
    request: Request,
    text: Optional[str] = Form(None, description="Paste tender text or clause specifications here"),
    file: Optional[UploadFile] = File(None, description="Upload tender document (.pdf, .docx, .txt)"),
    lang: Optional[str] = Form(None, description="Optional language code (e.g. en, hi, mr)"),
    db: Session = Depends(get_db),
):
    """
    Analyzes tender specifications for applicable Indian Standards.
    
    Accepts:
      - Raw text pasted into the **text** box
      - Uploaded document (.pdf, .docx, .txt) via **file**
      - Optional language hint in **lang**
    """
    raw_text = text
    file_bytes = None
    filename = None
    language = lang

    content_type = request.headers.get("content-type", "")

    # If programmatic client sent application/json body
    if "application/json" in content_type:
        try:
            body = await request.json()
            raw_text = body.get("text") or raw_text
            language = body.get("lang") or body.get("language") or language
            filename = body.get("filename", "pasted_text.txt")
        except Exception:
            pass

    if file and file.filename:
        file_bytes = await file.read()
        filename = file.filename
        if len(file_bytes) == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    if not file_bytes and (not raw_text or not raw_text.strip()):
        raise HTTPException(
            status_code=400,
            detail="Empty input: Please provide either a tender file upload (PDF/DOCX/TXT) or text content in the 'text' box.",
        )

    pipeline_service = TenderPipelineService(db=db)
    
    try:
        result = pipeline_service.analyze_tender(
            raw_text=raw_text,
            file_bytes=file_bytes,
            filename=filename,
            force_language=language,
        )
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline analysis error: {str(e)}")


@router.get("/debug/{request_id}")
async def get_debug_trace(request_id: str):
    """
    Returns intermediate pipeline execution traces, scores, and component ranks
    for the specified request_id.
    """
    if request_id not in DEBUG_TRACES:
        raise HTTPException(
            status_code=404,
            detail=f"Debug trace for request_id '{request_id}' not found or expired.",
        )
    return DEBUG_TRACES[request_id]


@router.post("/export/docx")
async def export_docx(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Generates and downloads a formatted DOCX Clause Pack report.
    Respects Officer Review decisions (accepts included, rejects excluded, flags marked).
    """
    from fastapi.responses import Response
    from models.schema import OfficerReview
    from services.export_service import generate_docx_clause_pack

    body = await request.json()
    tender_title = body.get("tender_title", "Tender Specification")
    clause_pack = body.get("clause_pack")
    request_id = body.get("request_id")

    if not clause_pack and "text" in body:
        pipeline_service = TenderPipelineService(db=db)
        res = pipeline_service.analyze_tender(raw_text=body["text"])
        clause_pack = res.get("clause_pack", {})
        tender_title = res.get("filename", tender_title)
        request_id = res.get("request_id", request_id)

    if not clause_pack:
        raise HTTPException(status_code=400, detail="No clause pack data provided for export.")

    reviews = []
    if request_id:
        reviews = db.query(OfficerReview).filter(OfficerReview.request_id == request_id).all()

    docx_bytes = generate_docx_clause_pack(tender_title, clause_pack, reviews=reviews)
    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f'attachment; filename="tender_clause_pack.docx"',
        },
    )


@router.post("/export/pdf")
async def export_pdf(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Generates and downloads a formatted PDF Clause Pack report.
    Respects Officer Review decisions (accepts included, rejects excluded, flags marked).
    """
    from fastapi.responses import Response
    from models.schema import OfficerReview
    from services.export_service import generate_pdf_clause_pack

    body = await request.json()
    tender_title = body.get("tender_title", "Tender Specification")
    clause_pack = body.get("clause_pack")
    request_id = body.get("request_id")

    if not clause_pack and "text" in body:
        pipeline_service = TenderPipelineService(db=db)
        res = pipeline_service.analyze_tender(raw_text=body["text"])
        clause_pack = res.get("clause_pack", {})
        tender_title = res.get("filename", tender_title)
        request_id = res.get("request_id", request_id)

    if not clause_pack:
        raise HTTPException(status_code=400, detail="No clause pack data provided for export.")

    reviews = []
    if request_id:
        reviews = db.query(OfficerReview).filter(OfficerReview.request_id == request_id).all()

    pdf_bytes = generate_pdf_clause_pack(tender_title, clause_pack, reviews=reviews)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="tender_clause_pack.pdf"',
        },
    )


@router.post("/export/markdown")
async def export_markdown(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Generates and returns formatted Markdown Clause Pack text with officer reviews applied.
    """
    from fastapi.responses import PlainTextResponse
    from models.schema import OfficerReview
    from services.export_service import generate_markdown_clause_pack

    body = await request.json()
    tender_title = body.get("tender_title", "Tender Technical Specification")
    clause_pack = body.get("clause_pack")
    request_id = body.get("request_id")

    if not clause_pack and "text" in body:
        pipeline_service = TenderPipelineService(db=db)
        res = pipeline_service.analyze_tender(raw_text=body["text"])
        clause_pack = res.get("clause_pack", {})
        tender_title = res.get("filename", tender_title)
        request_id = res.get("request_id", request_id)

    if not clause_pack:
        raise HTTPException(status_code=400, detail="No clause pack data available.")

    reviews = []
    if request_id:
        reviews = db.query(OfficerReview).filter(OfficerReview.request_id == request_id).all()

    md_text = generate_markdown_clause_pack(tender_title, clause_pack, reviews=reviews)
    return PlainTextResponse(
        content=md_text,
        headers={"Content-Disposition": 'attachment; filename="clause_pack.md"'},
    )


@router.post("/export/json")
async def export_json(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Generates and returns filtered JSON Clause Pack structure with officer reviews applied.
    """
    from models.schema import OfficerReview
    from services.export_service import generate_json_clause_pack

    body = await request.json()
    tender_title = body.get("tender_title", "Tender Technical Specification")
    clause_pack = body.get("clause_pack")
    request_id = body.get("request_id")

    if not clause_pack and "text" in body:
        pipeline_service = TenderPipelineService(db=db)
        res = pipeline_service.analyze_tender(raw_text=body["text"])
        clause_pack = res.get("clause_pack", {})
        tender_title = res.get("filename", tender_title)
        request_id = res.get("request_id", request_id)

    if not clause_pack:
        raise HTTPException(status_code=400, detail="No clause pack data available.")

    reviews = []
    if request_id:
        reviews = db.query(OfficerReview).filter(OfficerReview.request_id == request_id).all()

    return generate_json_clause_pack(tender_title, clause_pack, reviews=reviews)

