"""Unit tests for Phase 1 Data & Schema."""

import json
import pytest
from database import SessionLocal
from models.schema import Standard, StandardAmendment, StandardRelationship


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_standards_count_and_real_ids(db_session):
    """Test that all 100 standards are loaded and have real BIS standard IDs (no IS-DEMO)."""
    standards = db_session.query(Standard).all()
    assert len(standards) == 100
    for s in standards:
        assert s.standard_id.startswith("BIS-STD-")
        assert not s.standard_number.startswith("IS-DEMO")
        assert s.standard_number.startswith("IS") or s.standard_number.startswith("SP")
        assert s.document_url.startswith("http")
        assert s.source_url.startswith("http")


def test_field_completeness(db_session):
    """Verify critical metadata completeness across the corpus."""
    standards = db_session.query(Standard).all()
    qco_count = sum(1 for s in standards if s.mandatory_qco)
    assert qco_count >= 80, f"Expected at least 80% QCO coverage, got {qco_count}"

    params_count = sum(1 for s in standards if len(s.key_testing_parameters) > 0)
    assert params_count == 100, "All standards must have key testing parameters populated"

    scope_count = sum(1 for s in standards if s.scope and len(s.scope) > 20)
    assert scope_count == 100, "All standards must have rich scope definitions"


def test_amendments_and_supersedes(db_session):
    """Verify amendments tracking and predecessor records."""
    amendments = db_session.query(StandardAmendment).all()
    assert len(amendments) >= 140
    for amd in amendments:
        assert amd.amendment_number >= 1
        assert amd.source == "official_dataset"
        assert amd.verified is False  # Grounding rule


def test_allied_relationships_provenance(db_session):
    """Verify relationship roles and provenance flags."""
    relationships = db_session.query(StandardRelationship).all()
    assert len(relationships) >= 70

    valid_roles = {
        "normative_ref",
        "test_method",
        "terminology",
        "safety",
        "installation",
        "related_product",
        "supersedes",
    }
    for rel in relationships:
        assert rel.role in valid_roles
        assert rel.source in ("official_dataset", "ai_drafted")
        assert rel.verified is False  # Human verification required before setting True


def test_aliases_tagging(db_session):
    """Verify aliases tagging with source='ai_drafted' and verified=False."""
    standards = db_session.query(Standard).all()
    for s in standards:
        aliases = s.aliases
        for a in aliases:
            assert a.get("source") == "ai_drafted"
            assert a.get("verified") is False
