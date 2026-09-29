"""Tender Guard — Deterministic Clause Pack Generator & Export Service.

Generates paste-ready tender clauses using deterministic templates (ZERO LLM hallucination).
Features:
  - Conformance clauses with authoritative year and active amendments.
  - Allied graph integration grouped by role (test methods, normative refs, safety, installation).
  - Strict QCO disclaimers when legal basis is unverified.
  - Bracketed placeholders for needs_review records.
  - Zero exposure of unverified limits_text.
  - DOCX export (reusing python-docx code from repo 2 export_service.py).
  - Markdown export headed 'DRAFT — Officer to Verify'.
"""

import io
import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from models.schema import Standard
from services.allied_graph import get_allied_standards_for_standard


def generate_standard_clause(standard: Dict[str, Any], allied_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Generates deterministic clause text and structured data for a single standard.
    """
    std_num = standard.get("standard_number", "")
    year = standard.get("year", "2024")
    title = standard.get("full_title", "")
    amendments = standard.get("amendments", []) or []
    is_qco = standard.get("is_compulsory_certification", False) or standard.get("mandatory_qco", False)
    legal_verified = standard.get("legal_basis_verified", False)
    legal_basis = standard.get("legal_basis", "")
    needs_review = standard.get("needs_review", False)
    scheme = standard.get("scheme", "Scheme-I (ISI)")

    std_type = standard.get("standard_type", "product_spec")
    short_title = standard.get("short_title", "")
    product_noun = short_title if short_title else title

    # 1. Conformance Clause
    if needs_review:
        conformance_clause = (
            f"[OFFICER VERIFICATION REQUIRED: Specification for {product_noun} ({std_num}) is subject to BIS revision "
            f"and consolidation rules (e.g., IS 269:2015 covering 33/43/53 grades). Officer must confirm "
            f"applicable grade and standard edition before finalizing clause text.]"
        )
    else:
        amd_text = f", incorporating {len(amendments)} active amendment(s) ({', '.join(amendments)})" if amendments else " (latest edition)"
        conformance_clause = (
            f"The materials and workmanship for {product_noun} shall strictly conform to {std_num}:{year} "
            f"(\"{title}\"){amd_text}. The contractor/bidder shall submit valid test certificates "
            f"from a BIS-recognized laboratory for every consignment prior to acceptance."
        )

    # 2. Certification / Quality Control Clause (Only for product specifications with scheme data)
    has_scheme = bool(scheme and scheme.lower() not in ["none", "n/a", "not applicable", ""])
    if std_type == "product_spec" and has_scheme:
        if is_qco:
            if legal_verified:
                cert_clause = (
                    f"Mandatory BIS Certification: The product must carry the standard BIS Mark ({scheme}) "
                    f"in accordance with statutory Quality Control Orders ({legal_basis})."
                )
            else:
                cert_clause = (
                    f"BIS certification ({scheme}) required, QCO applicability to be confirmed by the officer. "
                    f"The bidder shall hold a valid BIS License/Certificate of Conformity at the time of bid submission."
                )
        else:
            cert_clause = (
                f"Voluntary BIS Certification ({scheme}): Products holding a valid BIS Mark shall be given "
                f"preference during technical evaluation. Uncertified products must undergo mandatory lot testing."
            )
    else:
        cert_clause = ""

    # 3. Allied & Testing Standards from Graph
    allied_clauses = []
    if allied_data and "relationships" in allied_data:
        grouped = {}
        for rel in allied_data["relationships"]:
            role = rel["role"]
            grouped.setdefault(role, []).append(rel)

        role_labels = {
            "test_method": "Testing & Sampling Standards",
            "normative_ref": "Normative References",
            "safety": "Safety & Environmental Standards",
            "installation": "Installation & Workmanship Codes",
            "related_product": "Allied Product Standards",
        }

        for role, rels in grouped.items():
            label = role_labels.get(role, role.replace("_", " ").title())
            std_items = []
            for r in rels:
                target_num = r["target_standard_number"]
                target_title = r["target_title"]
                in_corpus = r.get("target_is_in_corpus", False)
                unverified_tag = "" if in_corpus else " [unverified]"
                desc = f" — {r['description']}" if r.get("description") else ""
                std_items.append(f"{target_num} (\"{target_title}\"{unverified_tag}){desc}")
            
            allied_clauses.append({
                "category": label,
                "standards": std_items,
            })

    return {
        "standard_number": std_num,
        "full_title": title,
        "conformance_clause": conformance_clause,
        "certification_clause": cert_clause,
        "allied_clauses": allied_clauses,
        "needs_review": needs_review,
        "is_qco": is_qco,
    }


def generate_clause_pack(
    tender_title: str,
    recommended_standards: List[Dict[str, Any]],
    db: Optional[Session] = None,
) -> Dict[str, Any]:
    """
    Builds the complete deterministic Clause Pack for all recommended standards.
    """
    structured_clauses = []
    md_lines = [
        f"# DRAFT — Officer to Verify: Tender Specification Clauses",
        f"**Tender:** {tender_title}",
        f"**Generated:** {datetime.datetime.now().strftime('%d %B %Y, %I:%M %p')}",
        f"**Notice:** This document contains draft specification clauses generated by Tender Guard. "
        f"The procurement officer must review and confirm all requirements prior to issuance.\n",
        f"---",
    ]

    for idx, std in enumerate(recommended_standards, 1):
        std_num = std.get("standard_number", "")
        allied_data = None
        if db and std_num:
            try:
                allied_data = get_allied_standards_for_standard(std_num, db)
            except Exception:
                allied_data = None

        clause_item = generate_standard_clause(std, allied_data)
        structured_clauses.append(clause_item)

        md_lines.append(f"## {idx}. Technical Clause: {clause_item['standard_number']} — {clause_item['full_title']}")
        md_lines.append(f"\n### 1.1 Material Conformance & Quality Standards")
        md_lines.append(f"{clause_item['conformance_clause']}")
        
        if clause_item.get("certification_clause"):
            md_lines.append(f"\n### 1.2 BIS Certification & Quality Assurance")
            md_lines.append(f"{clause_item['certification_clause']}")

        if clause_item["allied_clauses"]:
            md_lines.append(f"\n### 1.3 Applicable Allied & Testing Standards")
            for grp in clause_item["allied_clauses"]:
                md_lines.append(f"**{grp['category']}:**")
                for s in grp["standards"]:
                    md_lines.append(f"- {s}")

        md_lines.append("\n---\n")

    markdown_text = "\n".join(md_lines)

    return {
        "header": "DRAFT — Officer to Verify",
        "tender_title": tender_title,
        "structured_clauses": structured_clauses,
        "markdown": markdown_text,
    }


def export_docx_clause_pack(
    tender_title: str,
    clause_pack: Dict[str, Any],
) -> bytes:
    """
    Generates a formatted DOCX document from the deterministic Clause Pack.
    Reuses python-docx generation logic from repo 2 export_service.py.
    """
    from docx import Document
    from docx.shared import Inches, Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH

    doc = Document()

    # Document Header Banner
    header = doc.add_heading("TENDER GUARD — TENDER SPECIFICATION CLAUSE PACK", level=1)
    for run in header.runs:
        run.font.color.rgb = RGBColor(0x1A, 0x36, 0x5D)

    sub = doc.add_paragraph("DRAFT — Officer to Verify (Statutory Disclaimers Apply)")
    for run in sub.runs:
        run.font.bold = True
        run.font.color.rgb = RGBColor(0xC5, 0x30, 0x30)

    doc.add_paragraph(f"Tender Reference / Title: {tender_title}")
    doc.add_paragraph(f"Generated On: {datetime.datetime.now().strftime('%d %B %Y, %I:%M %p')}")
    doc.add_paragraph(
        "Notice: Specifications are generated from the Bureau of Indian Standards (BIS) ground truth database. "
        "The procurement officer must independently confirm mandatory QCO applicability and statutory amendments."
    )
    doc.add_paragraph("")

    for idx, item in enumerate(clause_pack.get("structured_clauses", []), 1):
        doc.add_heading(f"Section {idx}: {item['standard_number']} — {item['full_title']}", level=2)

        doc.add_heading("1. Material Conformance Specification", level=3)
        doc.add_paragraph(item["conformance_clause"])

        if item.get("certification_clause"):
            doc.add_heading("2. BIS Certification & Statutory Compliance", level=3)
            doc.add_paragraph(item["certification_clause"])

        if item.get("allied_clauses"):
            doc.add_heading("3. Normative & Test Method References", level=3)
            for grp in item["allied_clauses"]:
                p = doc.add_paragraph()
                r_cat = p.add_run(f"{grp['category']}:\n")
                r_cat.bold = True
                for s in grp["standards"]:
                    doc.add_paragraph(s, style="List Bullet")

        doc.add_paragraph("")

    # Footer
    footer = doc.add_paragraph(
        "Generated by Tender Guard — AI Recommender of Indian Standards for Procurement Specifications. "
        "Strict Zero-Hallucination Grounding."
    )
    for run in footer.runs:
        run.font.size = Pt(8)
        run.font.color.rgb = RGBColor(0x71, 0x80, 0x96)

    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()
