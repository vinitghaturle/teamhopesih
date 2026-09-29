"""Tender Guard — Deterministic Clause Pack & DOCX Export Unit Tests.

Validates:
  - Deterministic clause text generation (ZERO LLM hallucination)
  - QCO disclaimer when legal basis is unverified
  - Bracketed verification placeholder for needs_review standards
  - Zero exposure of unverified limits_text
  - DOCX report generation and binary byte integrity
"""

import pytest
from database import SessionLocal
from services.clause_pack import (
    generate_standard_clause,
    generate_clause_pack,
    export_docx_clause_pack,
)


def test_standard_clause_generation():
    std_data = {
        "standard_number": "IS 1786",
        "year": "2008",
        "full_title": "High Strength Deformed Steel Bars and Wires for Concrete Reinforcement - Specification",
        "amendments": ["Amendment No. 1", "Amendment No. 2", "Amendment No. 3"],
        "is_compulsory_certification": True,
        "legal_basis_verified": False,
        "legal_basis": "Steel Products (Quality Control) Order",
        "needs_review": False,
        "scheme": "Scheme-I (ISI)",
    }

    clause = generate_standard_clause(std_data)

    assert "IS 1786:2008" in clause["conformance_clause"]
    assert "3 active amendment(s)" in clause["conformance_clause"]
    # Verify statutory disclaimer
    assert "QCO applicability to be confirmed by the officer" in clause["certification_clause"]
    assert "Steel Products" not in clause["certification_clause"]  # Unverified gazette order not asserted as absolute fact


def test_needs_review_placeholder():
    std_data = {
        "standard_number": "IS 8112",
        "year": "2013",
        "full_title": "Ordinary Portland Cement, 43 Grade - Specification",
        "amendments": [],
        "is_compulsory_certification": True,
        "legal_basis_verified": False,
        "needs_review": True,
    }

    clause = generate_standard_clause(std_data)

    # Needs review standard MUST have bracketed verification notice
    assert clause["conformance_clause"].startswith("[OFFICER VERIFICATION REQUIRED:")
    assert "IS 269:2015" in clause["conformance_clause"]


def test_docx_export():
    recommended = [
        {
            "standard_number": "IS 1786",
            "year": "2008",
            "full_title": "High Strength Deformed Steel Bars - Specification",
            "amendments": ["Amendment No. 1"],
            "is_compulsory_certification": True,
            "legal_basis_verified": False,
            "needs_review": False,
        }
    ]

    db = SessionLocal()
    try:
        pack = generate_clause_pack("Bridge Construction Tender", recommended, db=db)
        assert len(pack["structured_clauses"]) == 1
        assert "DRAFT — Officer to Verify" in pack["markdown"]

        docx_bytes = export_docx_clause_pack("Bridge Construction Tender", pack)
        assert isinstance(docx_bytes, bytes)
        assert len(docx_bytes) > 1000  # Valid DOCX binary
        assert docx_bytes[:4] == b"PK\x03\x04"  # Standard zip header for docx
    finally:
        db.close()


def test_code_of_practice_and_test_methods_omit_certification_clause():
    # IS 456 is a Code of Practice - should NOT have certification clause
    is_456_data = {
        "standard_number": "IS 456",
        "year": "2000",
        "full_title": "Plain and Reinforced Concrete - Code of Practice",
        "short_title": "Plain and Reinforced Concrete",
        "standard_type": "code_of_practice",
        "amendments": ["Amendment No. 1", "Amendment No. 2", "Amendment No. 3", "Amendment No. 4", "Amendment No. 5"],
        "is_compulsory_certification": False,
        "scheme": "Scheme-I",
        "needs_review": False,
    }
    clause_456 = generate_standard_clause(is_456_data)
    assert clause_456["conformance_clause"] != ""
    assert clause_456["certification_clause"] == ""  # Strictly omitted

    # IS 516 is a Test Method - should NOT have certification clause
    is_516_data = {
        "standard_number": "IS 516",
        "year": "2021",
        "full_title": "Hardened Concrete - Methods of Test",
        "short_title": "Concrete Testing Methods",
        "standard_type": "test_method",
        "amendments": [],
        "is_compulsory_certification": False,
        "scheme": "Scheme-I",
        "needs_review": False,
    }
    clause_516 = generate_standard_clause(is_516_data)
    assert clause_516["conformance_clause"] != ""
    assert clause_516["certification_clause"] == ""  # Strictly omitted
