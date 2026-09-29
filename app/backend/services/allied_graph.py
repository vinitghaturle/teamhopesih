"""Allied Standards Graph Service.

Traverses 1-hop relationships in the standard_relationships table,
groups them by role, and generates STUB nodes for standards outside the corpus.
"""

from typing import Dict, List, Any
from sqlalchemy.orm import Session
from models.schema import Standard, StandardRelationship


ROLE_MAPPING = {
    "normative_ref": "normative_references",
    "test_method": "test_methods",
    "terminology": "terminology_and_glossary",
    "safety": "safety_standards",
    "installation": "installation_codes",
    "related_product": "related_products",
    "supersedes": "superseded_standards",
}


class AlliedGraphService:
    """Provides 1-hop allied graph expansion for recommended Indian Standards."""

    def __init__(self, db: Session):
        self.db = db

    def get_allied_standards(self, standard_id: str) -> Dict[str, List[Dict[str, Any]]]:
        """Fetches 1-hop allied standards grouped by role with STUB node support."""
        relationships = (
            self.db.query(StandardRelationship)
            .filter(StandardRelationship.source_standard_id == standard_id)
            .all()
        )

        grouped: Dict[str, List[Dict[str, Any]]] = {
            "normative_references": [],
            "test_methods": [],
            "terminology_and_glossary": [],
            "safety_standards": [],
            "installation_codes": [],
            "related_products": [],
            "superseded_standards": [],
        }

        for rel in relationships:
            group_key = ROLE_MAPPING.get(rel.role, "related_products")
            
            # Check if target standard exists in corpus database
            target_std = (
                self.db.query(Standard)
                .filter(Standard.normalized_number == rel.target_standard_number)
                .first()
            )

            is_in_corpus = rel.target_is_in_corpus and (target_std is not None)
            
            source_label = "official_dataset" if (is_in_corpus and rel.verified) else ("ai_drafted" if is_in_corpus else "model_memory")
            is_verified = bool(is_in_corpus and rel.verified)

            node = {
                "standard_number": rel.target_standard_number,
                "title": target_std.full_title if (target_std and target_std.full_title) else (rel.target_title or "Details not in corpus"),
                "is_in_corpus": is_in_corpus,
                "role": rel.role,
                "description": rel.description or "",
                "is_stub": not is_in_corpus,
                "provenance": {
                    "source": source_label,
                    "verified": is_verified,
                },
                "source": source_label,
                "verified": is_verified,
            }

            if target_std:
                node["standard_id"] = target_std.standard_id
                node["year"] = target_std.year
                node["status"] = target_std.status

            grouped[group_key].append(node)

        # Remove empty groups for clean response, or keep all keys present
        return grouped


def get_allied_standards_for_standard(standard_number: str, db: Session) -> Dict[str, Any]:
    """Helper to fetch allied standards using standard_number or standard_id."""
    std = db.query(Standard).filter(
        (Standard.standard_number == standard_number) |
        (Standard.normalized_number == standard_number) |
        (Standard.standard_id == standard_number)
    ).first()

    if not std:
        return {"relationships": []}

    relationships = (
        db.query(StandardRelationship)
        .filter(StandardRelationship.source_standard_id == std.standard_id)
        .all()
    )

    items = []
    for rel in relationships:
        target_std = (
            db.query(Standard)
            .filter(Standard.normalized_number == rel.target_standard_number)
            .first()
        )
        is_in_corpus = rel.target_is_in_corpus and (target_std is not None)
        title = target_std.full_title if (target_std and target_std.full_title) else (rel.target_title or "Details not in corpus")

        items.append({
            "target_standard_number": rel.target_standard_number,
            "target_title": title,
            "role": rel.role,
            "description": rel.description or "",
            "target_is_in_corpus": is_in_corpus,
        })

    return {"relationships": items}
