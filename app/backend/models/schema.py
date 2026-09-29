"""Tender Guard - SQLAlchemy Database Models.

Dataset Validation Rules:
- Any added dataset fields (aliases, relations, parameters) are tagged source="ai_drafted", verified=False.
- Only confirmed records have verified=True.
- Zero fake/fictional IS-DEMO records allowed.
"""

from datetime import datetime
import json
from sqlalchemy import (
    Column,
    String,
    Integer,
    Boolean,
    Float,
    Text,
    DateTime,
    ForeignKey,
    Enum,
)
from sqlalchemy.orm import relationship
from database import Base


class Standard(Base):
    """Authoritative Indian Standard (BIS) metadata."""
    __tablename__ = "standards"

    standard_id = Column(String(64), primary_key=True, index=True)  # e.g., "BIS-STD-001"
    standard_number = Column(String(128), index=True, nullable=False)  # e.g., "IS 14543"
    normalized_number = Column(String(128), index=True, nullable=False)  # e.g., "IS 14543" normalized
    part = Column(String(64), nullable=True)
    section = Column(String(64), nullable=True)
    year = Column(String(32), nullable=False)  # e.g., "2024"
    full_title = Column(Text, nullable=False)
    short_title = Column(String(256), nullable=False)
    product_category = Column(String(256), index=True, nullable=False)
    industry = Column(String(256), nullable=False)
    scheme = Column(String(128), nullable=False)  # e.g., "Scheme-I (ISI)"
    certification_route = Column(Text, nullable=False)
    standard_type = Column(String(64), default="product_spec", nullable=False)  # product_spec | code_of_practice | test_method | terminology | other
    
    # QCO / Compulsory Certification Split
    is_compulsory_certification = Column(Boolean, default=False, index=True, nullable=False)
    mandatory_qco = Column(Boolean, default=False, index=True, nullable=False)  # alias for backwards compatibility
    legal_basis = Column(Text, nullable=True)
    legal_basis_verified = Column(Boolean, default=False, nullable=False)
    
    status = Column(String(64), default="active", nullable=False)
    publication_date = Column(String(64), nullable=True)
    revision_date = Column(String(64), nullable=True)
    supersedes = Column(Text, nullable=True)
    superseded_by = Column(Text, nullable=True)
    scope = Column(Text, nullable=False)
    
    # Key Testing Parameters Split: parameter_names (shown) vs limits_text (hidden unless verified)
    key_testing_parameters_json = Column(Text, default="[]", nullable=False)
    parameter_names_json = Column(Text, default="[]", nullable=False)
    limits_text_json = Column(Text, default="[]", nullable=False)
    materials_json = Column(Text, default="[]", nullable=False)
    keywords_json = Column(Text, default="[]", nullable=False)
    aliases_json = Column(Text, default="[]", nullable=False)  # [{'alias': '...', 'source': 'ai_drafted', 'verified': false}]
    
    # Official Citations & Evidence URLs
    document_url = Column(Text, nullable=False)
    source_url = Column(Text, nullable=False)
    source_type = Column(String(128), nullable=False)
    source_date = Column(String(64), nullable=True)
    retrieved_at = Column(String(64), nullable=True)
    legal_source_json = Column(Text, nullable=True)
    verification_status = Column(String(128), default="unverified")
    verification_note = Column(Text, nullable=True)
    legal_source_verified = Column(Boolean, default=False)
    
    # Integrity & Flagging
    needs_review = Column(Boolean, default=False, index=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)  # Hard rule: strictly False unless confirmed

    # Relationships
    amendments = relationship("StandardAmendment", back_populates="standard", cascade="all, delete-orphan")
    outgoing_relationships = relationship(
        "StandardRelationship",
        foreign_keys="StandardRelationship.source_standard_id",
        back_populates="source_standard",
        cascade="all, delete-orphan",
    )

    @property
    def legal_source(self) -> dict:
        try:
            return json.loads(self.legal_source_json or "{}")
        except Exception:
            return {}

    @property
    def key_testing_parameters(self) -> list:
        try:
            return json.loads(self.key_testing_parameters_json or "[]")
        except Exception:
            return []

    @property
    def parameter_names(self) -> list:
        try:
            return json.loads(self.parameter_names_json or "[]")
        except Exception:
            return []

    @property
    def limits_text(self) -> list:
        try:
            return json.loads(self.limits_text_json or "[]")
        except Exception:
            return []

    @property
    def materials(self) -> list:
        try:
            return json.loads(self.materials_json or "[]")
        except Exception:
            return []

    @property
    def keywords(self) -> list:
        try:
            return json.loads(self.keywords_json or "[]")
        except Exception:
            return []

    @property
    def aliases(self) -> list:
        try:
            return json.loads(self.aliases_json or "[]")
        except Exception:
            return []


class StandardAmendment(Base):
    """Active Amendments for an Indian Standard."""
    __tablename__ = "standard_amendments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    standard_id = Column(String(64), ForeignKey("standards.standard_id"), index=True, nullable=False)
    amendment_number = Column(Integer, nullable=False)  # e.g., 1, 2, 3
    year = Column(String(32), nullable=True)
    notes = Column(Text, nullable=True)
    source = Column(String(64), default="official_dataset", nullable=False)
    verified = Column(Boolean, default=False, nullable=False)

    standard = relationship("Standard", back_populates="amendments")


class StandardRelationship(Base):
    """Allied Standards Graph Relationships.
    
    Roles:
      - normative_ref: Mandatory referenced standard (e.g. general concrete code IS 456 for design)
      - test_method: Standard specifying testing procedures (e.g. IS 516 for compressive strength)
      - terminology: Glossary and definition standards
      - safety: Safety practices and codes
      - installation: Code of practice for laying/installation
      - related_product: Complementary or alternative product standard
      - supersedes: Historical predecessor standard
    """
    __tablename__ = "standard_relationships"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_standard_id = Column(String(64), ForeignKey("standards.standard_id"), index=True, nullable=False)
    source_standard_number = Column(String(128), nullable=False)
    target_standard_number = Column(String(128), index=True, nullable=False)
    target_title = Column(Text, nullable=True)
    target_is_in_corpus = Column(Boolean, default=True, nullable=False)  # False -> STUB node
    role = Column(String(64), nullable=False)  # normative_ref | test_method | terminology | safety | installation | related_product | supersedes
    description = Column(Text, nullable=True)
    source = Column(String(64), default="official_dataset", nullable=False)  # "official_dataset" or "ai_drafted"
    verified = Column(Boolean, default=False, nullable=False)  # Hard rule: False unless verified by human

    source_standard = relationship("Standard", foreign_keys=[source_standard_id], back_populates="outgoing_relationships")


class Tender(Base):
    """Procurement tender documents submitted for analysis."""
    __tablename__ = "tenders"

    id = Column(String(64), primary_key=True, index=True)
    title = Column(String(512), nullable=False)
    raw_text = Column(Text, nullable=False)
    filename = Column(String(256), nullable=True)
    detected_language = Column(String(32), default="en")
    translated_text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    requirements = relationship("ExtractedRequirement", back_populates="tender", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="tender", cascade="all, delete-orphan")


class ExtractedRequirement(Base):
    """Discrete requirement items extracted from tender text."""
    __tablename__ = "extracted_requirements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tender_id = Column(String(64), ForeignKey("tenders.id"), index=True, nullable=False)
    item_index = Column(Integer, nullable=False)
    clause_text = Column(Text, nullable=False)
    category = Column(String(128), nullable=True)
    key_entities_json = Column(Text, default="[]")

    tender = relationship("Tender", back_populates="requirements")
    recommendations = relationship("Recommendation", back_populates="requirement")


class Recommendation(Base):
    """Standard recommendations for tender requirements with full evidence audit."""
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tender_id = Column(String(64), ForeignKey("tenders.id"), index=True, nullable=False)
    requirement_id = Column(Integer, ForeignKey("extracted_requirements.id"), nullable=True)
    standard_id = Column(String(64), ForeignKey("standards.standard_id"), index=True, nullable=False)
    
    # Qualitative match strength band: HIGH, MEDIUM, LOW (no fake percentages)
    match_strength = Column(String(32), nullable=False)  # HIGH | MEDIUM | LOW | NO_CONFIDENT_MATCH
    
    # Component Ranks & Scores for transparency
    dense_rank = Column(Integer, nullable=True)
    bm25_rank = Column(Integer, nullable=True)
    rrf_score = Column(Float, nullable=True)
    rerank_score = Column(Float, nullable=True)
    
    # Grounding & Traceability Evidence
    justification = Column(Text, nullable=False)
    source_excerpt = Column(Text, nullable=False)
    source_field = Column(String(128), nullable=False)
    
    # Officer Review Workflow
    review_decision = Column(String(32), default="pending", nullable=False)  # pending | accept | reject | flag
    review_remarks = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tender = relationship("Tender", back_populates="recommendations")
    requirement = relationship("ExtractedRequirement", back_populates="recommendations")
    standard = relationship("Standard")


class OfficerReview(Base):
    """Officer Review Actions persisted per analysis request and standard.
    
    Actions:
      - ACCEPT: Procurement officer approves standard inclusion
      - REJECT: Procurement officer excludes standard from final tender clause pack
      - FLAG: Marked for supervisor review or clarification
    """
    __tablename__ = "officer_reviews"

    id = Column(Integer, primary_key=True, autoincrement=True)
    request_id = Column(String(64), index=True, nullable=False)
    standard_number = Column(String(128), index=True, nullable=False)
    action = Column(String(32), nullable=False)  # ACCEPT | REJECT | FLAG
    remarks = Column(Text, nullable=True)
    officer_name = Column(String(128), default="Procurement Officer", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

