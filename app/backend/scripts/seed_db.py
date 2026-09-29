"""Tender Guard - Database Seed Script (with P1 Enhancements).

Ingests the 100 real BIS standards dataset from seed_standards.json into SQLite.
Populates:
  - Standards with split QCO (is_compulsory_certification, legal_basis, legal_basis_verified=False)
  - Split key_testing_parameters (parameter_names [shown] vs limits_text [hidden unless verified])
  - needs_review flags for IS 269, IS 8112, IS 12269
  - Active amendments (source="official_dataset", verified=False)
  - Curated allied graph relationships for demo path with STUB node support (target_is_in_corpus=False, target_title="Details not in corpus")
  - Tender phrasing aliases (source="ai_drafted", verified=False)
"""

import json
import re
import sys
from pathlib import Path

# Add backend directory to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from database import engine, SessionLocal, Base
from models.schema import Standard, StandardAmendment, StandardRelationship


def normalize_is_number(num_str: str) -> str:
    """Normalize IS number string (e.g. 'IS: 14543-2024' -> 'IS 14543')."""
    if not num_str:
        return ""
    cleaned = re.sub(r'[:\-]', ' ', num_str.strip().upper())
    cleaned = re.sub(r'\s+', ' ', cleaned)
    m = re.match(r'^(IS\s*\d+)', cleaned)
    if m:
        return m.group(1).replace('IS', 'IS ').strip()
    return cleaned


def split_parameter_name_and_limits(raw_param_str: str) -> tuple[str, str]:
    """Separates parameter name from its quantitative limit string.
    Example: 'Tensile Strength (>= 500 MPa)' -> ('Tensile Strength', '>= 500 MPa')
    """
    match = re.match(r"^(.*?)\s*\((.*?)\)$", raw_param_str.strip())
    if match:
        name = match.group(1).strip()
        limits = match.group(2).strip()
        return name, limits
    return raw_param_str.strip(), ""


def derive_standard_type(title: str, category: str = "") -> str:
    """Classify standard as product_spec | code_of_practice | test_method | terminology | other."""
    t = title.lower()
    if "code of practice" in t or "practice for" in t or "guidelines" in t or "guide for" in t:
        return "code_of_practice"
    elif "method of test" in t or "methods of test" in t or "testing" in t or "sampling and test" in t or "determination of" in t:
        return "test_method"
    elif "glossary" in t or "terminology" in t or "vocabulary" in t or "symbols" in t:
        return "terminology"
    elif "specification" in t or "requirements" in t:
        return "product_spec"
    else:
        return "product_spec" if category else "other"


# Curated allied relationships for demo & prominent standards
# Tagged source="official_dataset", verified=False
CURATED_ALLIED_RELATIONSHIPS = [
    # IS 14543 (Packaged Drinking Water)
    {
        "source": "IS 14543",
        "target": "IS 10500",
        "role": "normative_ref",
        "desc": "Baseline drinking water chemical and microbiological specifications.",
    },
    {
        "source": "IS 14543",
        "target": "IS 13428",
        "role": "related_product",
        "desc": "Packaged Natural Mineral Water standard.",
    },
    {
        "source": "IS 14543",
        "target": "IS 15410",
        "role": "normative_ref",
        "desc": "Plastic packaging containers specification for drinking water.",
    },
    # IS 1786 (High strength deformed steel bars and wires / TMT)
    {
        "source": "IS 1786",
        "target": "IS 1608",
        "role": "test_method",
        "desc": "Metallic materials - Tensile testing at room temperature.",
    },
    {
        "source": "IS 1786",
        "target": "IS 456",
        "role": "normative_ref",
        "desc": "Code of practice for plain and reinforced concrete.",
    },
    {
        "source": "IS 1786",
        "target": "IS 2062",
        "role": "related_product",
        "desc": "Hot rolled medium and high tensile structural steel standard.",
    },
    # IS 4984 (HDPE Pipes for water supply)
    {
        "source": "IS 4984",
        "target": "IS 7634 (Part 2)",
        "role": "installation",
        "desc": "Code of practice for laying and jointing of polyethylene pipes.",
    },
    {
        "source": "IS 4984",
        "target": "IS 4985",
        "role": "related_product",
        "desc": "Unplasticized PVC pipes for potable water supplies.",
    },
    {
        "source": "IS 4984",
        "target": "IS 2530",
        "role": "test_method",
        "desc": "Methods of test for polyethylene molding materials and polyethylene compounds.",
    },
    # IS 694 (PVC Insulated Cables)
    {
        "source": "IS 694",
        "target": "IS 10810",
        "role": "test_method",
        "desc": "Methods of test for cables.",
    },
    {
        "source": "IS 694",
        "target": "IS 1554 (Part 1)",
        "role": "related_product",
        "desc": "PVC insulated (heavy duty) electric cables for working voltages up to 1100 V.",
    },
    {
        "source": "IS 694",
        "target": "IS 732",
        "role": "installation",
        "desc": "Code of practice for electrical wiring installations.",
    },
    # IS 269 (Ordinary Portland Cement)
    {
        "source": "IS 269",
        "target": "IS 4031",
        "role": "test_method",
        "desc": "Methods of physical tests for hydraulic cement.",
    },
    {
        "source": "IS 269",
        "target": "IS 456",
        "role": "normative_ref",
        "desc": "Plain and Reinforced Concrete - Code of Practice.",
    },
    {
        "source": "IS 269",
        "target": "IS 1489",
        "role": "related_product",
        "desc": "Portland Pozzolana Cement specification.",
    },
    # IS 10500 (Drinking Water)
    {
        "source": "IS 10500",
        "target": "IS 3025",
        "role": "test_method",
        "desc": "Methods of sampling and test (physical and chemical) for water and wastewater.",
    },
    {
        "source": "IS 10500",
        "target": "IS 1622",
        "role": "test_method",
        "desc": "Methods for sampling and microbiological examination of water.",
    },
    # IS 15410 (Plastic packaging containers for water)
    {
        "source": "IS 15410",
        "target": "IS 9845",
        "role": "test_method",
        "desc": "Determination of overall migration of constituents of plastics materials into food simulants.",
    },
    {
        "source": "IS 15410",
        "target": "IS 14543",
        "role": "normative_ref",
        "desc": "Packaged drinking water product specification.",
    },
    # IS 16102 (Self-Ballasted LED Lamps)
    {
        "source": "IS 16102 (Part 1)",
        "target": "IS 16102 (Part 2)",
        "role": "related_product",
        "desc": "Self-ballasted LED lamps - Part 2: Performance requirements.",
    },
    {
        "source": "IS 16102 (Part 1)",
        "target": "IS 15885",
        "role": "safety",
        "desc": "Lamp controlgear safety requirements.",
    },
]

CURATED_ALIASES = {
    "IS 269": ["OPC", "Ordinary Portland Cement", "OPC 43 Grade", "OPC 53 Grade", "33 Grade Cement", "Civil Construction Cement"],
    "IS 1786": ["TMT Bars", "Thermo-Mechanically Treated Bars", "High Yield Strength Deformed Bars", "HYSD Bars", "Fe 500D Rebar", "Fe 550D TMT", "Steel Reinforcement Bars"],
    "IS 4984": ["HDPE Pipe", "High Density Polyethylene Pipe", "PE-100 Pipe", "PE-80 Pipe", "Water Distribution Pipe", "Polyethylene Pressure Pipe"],
    "IS 14543": ["Packaged Drinking Water", "Bottled Drinking Water", "Purified Water Jars 20L", "Drinking Water Cans", "Reverse Osmosis Treated Water"],
    "IS 10500": ["Potable Water", "Drinking Water Supply", "Raw Water Quality", "Municipal Water Supply"],
    "IS 694": ["PVC Wire", "Single Core Copper Wire", "Flexible Cable", "Building Wire", "FR PVC Insulated Wire", "FRLS Cable"],
    "IS 1554": ["Armoured Cable", "LT Power Cable", "Underground Power Cable", "Heavy Duty PVC Cable", "1.1 kV Cable"],
    "IS 2062": ["Structural Steel", "MS Angles", "MS Channels", "MS Beams", "Hot Rolled Steel Plates", "Fe 410 Steel"],
    "IS 1239": ["GI Pipe", "Galvanized Iron Pipe", "Mild Steel Tubes", "MS Pipe for Plumbing", "Water & Gas Tubes"],
    "IS 4985": ["UPVC Pipe", "Rigid PVC Pipe", "Plumbing PVC Pipe", "PVC Potable Water Line"],
    "IS 13252": ["IT Equipment Safety", "Information Technology Equipment", "Server Safety Standard", "Computer Power Supply Safety"],
    "IS 16102": ["Self-Ballasted LED Lamps", "LED Bulb", "General Lighting LED", "LED Safety Standards"],
    "IS 7318": ["Welding Approval", "Welder Qualification", "Manual Metal Arc Welding Code", "Weld Procedure Specification (WPS)"],
    "IS 15410": ["Plastic Water Bottles", "Water Jars 20L", "PET Containers for Water", "Water Packaging Materials"],
}

# Records with known ambiguity needing review
NEEDS_REVIEW_STANDARDS = {"IS 269", "IS 8112", "IS 12269"}


def seed_database():
    """Populate SQLite database from seed_standards.json."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    seed_file = BASE_DIR / "data" / "seed_standards.json"
    if not seed_file.exists():
        print(f"Error: Seed file not found at {seed_file}")
        return

    with open(seed_file, "r", encoding="utf-8") as f:
        standards_data = json.load(f)

    print(f"Loaded {len(standards_data)} standards from JSON.")

    standards_count = 0
    amendments_count = 0
    relationships_count = 0

    std_lookup_by_norm = {}
    std_lookup_by_num = {}

    for item in standards_data:
        std_num = item.get("standard_number", "").strip()
        norm_num = normalize_is_number(std_num)

        # Aliases
        aliases_list = []
        matching_curated = CURATED_ALIASES.get(norm_num, [])
        for a in matching_curated:
            aliases_list.append({"alias": a, "source": "ai_drafted", "verified": False})

        short_title = item.get("short_title", "").strip()
        if short_title and short_title not in matching_curated:
            aliases_list.append({"alias": short_title, "source": "ai_drafted", "verified": False})

        # Key testing parameters split: parameter_names (shown) vs limits_text (hidden unless verified)
        raw_params = item.get("key_testing_parameters", [])
        param_names = []
        limits_texts = []
        for p in raw_params:
            p_name, p_lim = split_parameter_name_and_limits(str(p))
            param_names.append(p_name)
            limits_texts.append(p_lim)

        # QCO & Legal basis split
        mandatory_qco = bool(item.get("mandatory_qco", False))
        legal_src = item.get("legal_source", {})
        legal_basis = legal_src.get("gazette_order") if isinstance(legal_src, dict) else str(legal_src)

        # Needs review check
        needs_review = any(nr in norm_num or nr in std_num for nr in NEEDS_REVIEW_STANDARDS)

        std = Standard(
            standard_id=item.get("standard_id"),
            standard_number=std_num,
            normalized_number=norm_num,
            part=item.get("part"),
            section=item.get("section"),
            year=str(item.get("year", "2024")),
            full_title=item.get("full_title", ""),
            short_title=short_title or std_num,
            product_category=item.get("product_category", "General"),
            industry=item.get("industry", "General Industry"),
            scheme=item.get("scheme", "Scheme-I (ISI)"),
            certification_route=item.get("certification_route", "Mandatory Scheme-I"),
            standard_type=derive_standard_type(item.get("full_title", ""), item.get("product_category", "")),
            is_compulsory_certification=mandatory_qco,
            mandatory_qco=mandatory_qco,
            legal_basis=legal_basis,
            legal_basis_verified=False,  # Hard rule: strictly False
            status=item.get("status", "active"),
            publication_date=item.get("publication_date"),
            revision_date=item.get("revision_date"),
            supersedes=item.get("supersedes"),
            superseded_by=item.get("superseded_by"),
            scope=item.get("scope", ""),
            key_testing_parameters_json=json.dumps(raw_params),
            parameter_names_json=json.dumps(param_names),
            limits_text_json=json.dumps(limits_texts),
            materials_json=json.dumps(item.get("materials", [])),
            keywords_json=json.dumps(item.get("keywords", [])),
            aliases_json=json.dumps(aliases_list),
            document_url=item.get("document_url", "https://www.services.bis.gov.in"),
            source_url=item.get("source_url", "https://www.bis.gov.in"),
            source_type=item.get("source_type", "official_portal"),
            source_date=item.get("source_date"),
            retrieved_at=item.get("retrieved_at"),
            legal_source_json=json.dumps(legal_src),
            verification_status=item.get("verification_status", "unverified"),
            verification_note=item.get("verification_note"),
            legal_source_verified=bool(item.get("legal_source_verified", False)),
            needs_review=needs_review,
            is_verified=False,  # Hard rule: strictly False unless confirmed
        )
        db.add(std)
        std_lookup_by_norm[norm_num] = std.standard_id
        std_lookup_by_num[std_num] = (std.standard_id, std.full_title)
        standards_count += 1

        # Process amendments from dataset
        amendments_raw = item.get("amendments", [])
        if isinstance(amendments_raw, list):
            for idx, amd in enumerate(amendments_raw, start=1):
                if isinstance(amd, dict):
                    amd_num = amd.get("amendment_number", idx)
                    amd_yr = amd.get("year")
                    amd_notes = amd.get("notes") or amd.get("description")
                else:
                    amd_num = idx
                    amd_yr = None
                    amd_notes = str(amd)

                amendment_obj = StandardAmendment(
                    standard_id=std.standard_id,
                    amendment_number=amd_num,
                    year=str(amd_yr) if amd_yr else None,
                    notes=amd_notes,
                    source="official_dataset",
                    verified=False,
                )
                db.add(amendment_obj)
                amendments_count += 1

    db.commit()

    # Process Relationships
    # 1. Supersedes relationships from dataset
    for item in standards_data:
        std_id = item.get("standard_id")
        std_num = item.get("standard_number", "").strip()
        supersedes_raw = item.get("supersedes")
        if supersedes_raw:
            # Check if superseded target exists in corpus
            target_norm = normalize_is_number(supersedes_raw)
            in_corpus = target_norm in std_lookup_by_norm
            target_title = std_lookup_by_num.get(supersedes_raw, (None, "Details not in corpus"))[1] if in_corpus else "Details not in corpus"

            rel = StandardRelationship(
                source_standard_id=std_id,
                source_standard_number=std_num,
                target_standard_number=supersedes_raw,
                target_title=target_title,
                target_is_in_corpus=in_corpus,
                role="supersedes",
                description=f"Superseded by {std_num}",
                source="official_dataset",
                verified=False,
            )
            db.add(rel)
            relationships_count += 1

    # 2. Curated Allied Relationships for Demo Path with STUB support
    for rel_data in CURATED_ALLIED_RELATIONSHIPS:
        src_raw = rel_data["source"]
        src_norm = normalize_is_number(src_raw)
        src_id = std_lookup_by_norm.get(src_norm)

        if not src_id:
            # Find partial match
            for n_k, s_id in std_lookup_by_norm.items():
                if src_norm in n_k or n_k in src_norm:
                    src_id = s_id
                    break

        if src_id:
            tgt_raw = rel_data["target"]
            tgt_norm = normalize_is_number(tgt_raw)
            in_corpus = tgt_norm in std_lookup_by_norm
            
            # STUB node handling: If not in corpus, title is strictly "Details not in corpus"
            target_title = std_lookup_by_num.get(tgt_raw, (None, None))[1] if in_corpus else "Details not in corpus"

            rel = StandardRelationship(
                source_standard_id=src_id,
                source_standard_number=src_raw,
                target_standard_number=tgt_raw,
                target_title=target_title,
                target_is_in_corpus=in_corpus,
                role=rel_data["role"],
                description=rel_data.get("desc"),
                source="official_dataset",
                verified=False,
            )
            db.add(rel)
            relationships_count += 1

    db.commit()
    db.close()

    print(f"Database seeded successfully:")
    print(f"  - Standards: {standards_count}")
    print(f"  - Amendments: {amendments_count}")
    print(f"  - Relationships: {relationships_count}")


if __name__ == "__main__":
    seed_database()
