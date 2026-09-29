"""Tender Guard — Multi-Format Export Service (DOCX, Markdown, JSON, PDF).

Integrates Officer Review decisions:
- ACCEPT: Included in final tender clause pack.
- REJECT: Excluded from final clause pack.
- FLAG: Included with prominent "[FLAGGED FOR SUPERVISOR REVIEW]" note and officer remarks.
"""

import io
import json
from datetime import datetime
from typing import Dict, List, Any, Optional

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH


def filter_clauses_by_reviews(structured_clauses: List[Dict[str, Any]], reviews: Optional[List[Any]] = None) -> List[Dict[str, Any]]:
    """Filters structured clauses based on officer review decisions."""
    if not reviews:
        return structured_clauses

    review_map = {}
    for r in reviews:
        std_num = getattr(r, "standard_number", None) or (r.get("standard_number") if isinstance(r, dict) else None)
        action = getattr(r, "action", None) or (r.get("action") if isinstance(r, dict) else None)
        remarks = getattr(r, "remarks", None) or (r.get("remarks") if isinstance(r, dict) else None)
        if std_num:
            review_map[std_num.strip().upper()] = {
                "action": (action or "ACCEPT").upper(),
                "remarks": remarks,
            }

    filtered = []
    for clause in structured_clauses:
        std_num = clause.get("standard_number", "").strip().upper()
        rev = review_map.get(std_num)

        if rev:
            if rev["action"] == "REJECT":
                # Exclude rejected standards
                continue
            elif rev["action"] == "FLAG":
                clause_copy = dict(clause)
                clause_copy["is_flagged"] = True
                clause_copy["officer_remarks"] = rev.get("remarks")
                filtered.append(clause_copy)
            else:
                filtered.append(clause)
        else:
            filtered.append(clause)

    return filtered


def generate_pdf_clause_pack(
    tender_title: str,
    clause_pack: Dict[str, Any],
    reviews: Optional[List[Any]] = None,
) -> bytes:
    """Generates an authoritative, government-styled PDF clause pack report."""
    structured_clauses = filter_clauses_by_reviews(clause_pack.get("structured_clauses", []), reviews)
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=0.5 * inch,
        bottomMargin=0.5 * inch,
        leftMargin=0.6 * inch,
        rightMargin=0.6 * inch,
    )
    styles = getSampleStyleSheet()
    elements = []

    # Title & Metadata Header
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Heading1"],
        fontSize=15,
        leading=18,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#475569"),
    )
    section_style = ParagraphStyle(
        "SectionHeader",
        parent=styles["Heading2"],
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#1e293b"),
        spaceBefore=10,
        spaceAfter=4,
    )
    body_style = ParagraphStyle(
        "ClauseBody",
        parent=styles["Normal"],
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor("#1e293b"),
    )
    warning_style = ParagraphStyle(
        "WarningBody",
        parent=styles["Normal"],
        fontSize=8,
        leading=10.5,
        textColor=colors.HexColor("#991b1b"),
    )

    elements.append(Paragraph("TENDER SPECIFICATION CLAUSE PACK — INDIAN STANDARDS (BIS)", title_style))
    elements.append(Paragraph(f"<b>Tender Title:</b> {tender_title}", subtitle_style))
    elements.append(Paragraph(f"<b>Generated On:</b> {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')} | <b>System:</b> Tender Guard", subtitle_style))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceAfter=10, spaceBefore=6))

    if not structured_clauses:
        elements.append(Paragraph("<i>No applicable or approved Indian Standards for this specification.</i>", body_style))
    else:
        for idx, item in enumerate(structured_clauses, start=1):
            std_num = item.get("standard_number", "Standard")
            full_title = item.get("full_title", "")
            elements.append(Paragraph(f"<b>Clause {idx}: {std_num} — {full_title}</b>", section_style))

            if item.get("is_flagged"):
                elements.append(Paragraph(
                    f"⚠️ <b>[FLAGGED FOR SUPERVISOR REVIEW]</b> Officer Remark: {item.get('officer_remarks') or 'Requires review'}",
                    warning_style,
                ))

            # Conformance Table
            conf_text = item.get("conformance_clause", "")
            cert_text = item.get("certification_clause", "")
            
            table_data = [
                [Paragraph("<b>Mandatory Conformance:</b>", body_style), Paragraph(conf_text, body_style)],
            ]
            if cert_text:
                table_data.append([
                    Paragraph("<b>Certification / QCO:</b>", body_style),
                    Paragraph(cert_text, body_style),
                ])

            allied = item.get("allied_clauses", [])
            if allied:
                allied_snippets = []
                for a in allied:
                    allied_snippets.append(f"<b>{a.get('category')}:</b> {', '.join(a.get('standards', []))}")
                table_data.append([
                    Paragraph("<b>Allied Standards:</b>", body_style),
                    Paragraph("<br/>".join(allied_snippets), body_style),
                ])

            t = Table(table_data, colWidths=[1.4 * inch, 5.4 * inch])
            t.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f8fafc")),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
            ]))
            elements.append(t)
            elements.append(Spacer(1, 8))

    # Disclaimer Footer
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1"), spaceAfter=6, spaceBefore=12))
    footer_style = ParagraphStyle(
        "FooterNote",
        parent=styles["Normal"],
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor("#64748b"),
    )
    elements.append(Paragraph(
        "Tender Guard Disclaimer: Generated draft specifications for procurement tender integration. "
        "Procurement officers must verify clauses against the active BIS catalogue before issuance.",
        footer_style,
    ))

    doc.build(elements)
    return buffer.getvalue()


def generate_docx_clause_pack(
    tender_title: str,
    clause_pack: Dict[str, Any],
    reviews: Optional[List[Any]] = None,
) -> bytes:
    """Generates formatted DOCX file bytes."""
    from services.clause_pack import export_docx_clause_pack
    structured_clauses = filter_clauses_by_reviews(clause_pack.get("structured_clauses", []), reviews)
    filtered_pack = dict(clause_pack)
    filtered_pack["structured_clauses"] = structured_clauses
    return export_docx_clause_pack(tender_title, filtered_pack)


def generate_markdown_clause_pack(
    tender_title: str,
    clause_pack: Dict[str, Any],
    reviews: Optional[List[Any]] = None,
) -> str:
    """Generates formatted Markdown clause pack string."""
    structured_clauses = filter_clauses_by_reviews(clause_pack.get("structured_clauses", []), reviews)
    lines = [
        f"# TECHNICAL SPECIFICATION CLAUSE PACK — INDIAN STANDARDS (BIS)",
        f"**Tender:** {tender_title}",
        f"**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')} | **System:** Tender Guard",
        "",
        "---",
        "",
    ]
    for idx, c in enumerate(structured_clauses, start=1):
        lines.append(f"### Clause {idx}: {c.get('standard_number')} — {c.get('full_title')}")
        if c.get("is_flagged"):
            lines.append(f"> ⚠️ **[FLAGGED FOR SUPERVISOR REVIEW]** Officer Remark: {c.get('officer_remarks') or 'Requires review'}")
            lines.append("")
        lines.append(f"- **Mandatory Conformance:** {c.get('conformance_clause')}")
        if c.get("certification_clause"):
            lines.append(f"- **Certification / Scheme:** {c.get('certification_clause')}")
        if c.get("allied_clauses"):
            for a in c.get("allied_clauses"):
                lines.append(f"- **Allied Standards ({a.get('category')}):** {', '.join(a.get('standards', []))}")
        lines.append("")

    lines.append("---")
    lines.append("*All clauses must be verified by the procurement officer against the active BIS catalogue before issuance.*")
    return "\n".join(lines)


def generate_json_clause_pack(
    tender_title: str,
    clause_pack: Dict[str, Any],
    reviews: Optional[List[Any]] = None,
) -> Dict[str, Any]:
    """Generates structured JSON representation for API consumption."""
    structured_clauses = filter_clauses_by_reviews(clause_pack.get("structured_clauses", []), reviews)
    return {
        "tender_title": tender_title,
        "generated_at": datetime.utcnow().isoformat(),
        "total_approved_clauses": len(structured_clauses),
        "clauses": structured_clauses,
        "disclaimer": "All clauses must be verified by the procurement officer against the active BIS catalogue before issuance.",
    }
