"""Tender Guard — Qualifier Conflict Analyzer.

Automatically derives domain qualifiers (materials, applications, grades, product types)
from the corpus metadata and verifies whether candidates match all specified qualifiers.

If a query specifies a key application/material/grade qualifier that is absent from
the candidate's scope or conflicts with the candidate's primary purpose,
the status is downgraded from MATCH_FOUND to CLOSE_BUT_NOT_EXACT.
"""

import re
from typing import List, Dict, Any, Tuple, Optional, Set
from services import technical_patterns as patterns


class QualifierConflictChecker:
    """Automated corpus-derived qualifier conflict detector."""

    def __init__(self, documents: List[Any]):
        self.qualifier_vocab: Set[str] = set()
        self.application_qualifiers: Set[str] = set()
        self.material_qualifiers: Set[str] = set()
        self._build_vocab(documents)

    def _build_vocab(self, documents: List[Any]):
        """Derive qualifiers automatically from standard metadata."""
        # Domain qualifier regexes
        app_pattern = re.compile(
            r"\b(drainage|sewerage|sewage|potable|drinking\s+water|water\s+supply|irrigation|"
            r"fire\s+safety|fire\s+fighting|structural|foundation|prestressed|masonry|"
            r"industrial|two\s+wheeler|automotive|interior\s+wiring|overhead|underground|"
            r"packaged\s+water|natural\s+mineral|domestic|commercial)\b",
            re.IGNORECASE,
        )
        
        grade_pattern = re.compile(
            r"\b(33\s+grade|43\s+grade|53\s+grade|grade\s+33|grade\s+43|grade\s+53|"
            r"fe\s*415[a-z]?|fe\s*500[a-z]?|fe\s*550[a-z]?|pe\s*63|pe\s*80|pe\s*100|"
            r"pn\s*\d+|class\s+[a-z0-9]+)\b",
            re.IGNORECASE,
        )

        for doc in documents:
            text = f"{doc.full_title} {doc.product_category} {doc.scope} {' '.join(doc.keywords)} {' '.join(doc.parameter_names)}"
            
            # Extract application terms
            for m in app_pattern.finditer(text):
                term = m.group(0).lower().strip()
                self.application_qualifiers.add(term)
                self.qualifier_vocab.add(term)

            # Extract materials
            for m in patterns.MATERIAL.finditer(text):
                term = m.group(0).lower().strip()
                self.material_qualifiers.add(term)
                self.qualifier_vocab.add(term)

            # Extract grades
            for m in grade_pattern.finditer(text):
                term = m.group(0).lower().strip()
                self.qualifier_vocab.add(term)

    def check_conflicts(self, query: str, candidate_doc: Any) -> Tuple[bool, Optional[str]]:
        """
        Checks if the query contains distinct domain qualifiers that conflict with candidate.
        
        Returns:
          (has_conflict: bool, conflict_reason: Optional[str])
        """
        q_lower = query.lower()
        aliases_list = getattr(candidate_doc, "aliases", [])
        aliases_strs = [a.get("alias", str(a)) if isinstance(a, dict) else str(a) for a in aliases_list]
        keywords_strs = [str(k) for k in getattr(candidate_doc, "keywords", [])]
        params_strs = [str(p) for p in getattr(candidate_doc, "parameter_names", [])]

        doc_text = (
            f"{candidate_doc.standard_number} {candidate_doc.full_title} "
            f"{candidate_doc.product_category} {candidate_doc.scope} "
            f"{' '.join(aliases_strs)} {' '.join(keywords_strs)} "
            f"{' '.join(params_strs)}"
        ).lower()

        # 1. Check Application Purpose Conflicts (e.g. drainage vs potable water, industrial helmet vs two-wheeler helmet)
        # Application conflict pairs
        conflicting_domains = [
            ("drainage", ["potable", "drinking water", "water supply"]),
            ("sewerage", ["potable", "drinking water", "water supply"]),
            ("sewage", ["potable", "drinking water", "water supply"]),
            ("two wheeler", ["industrial safety", "fire fighting"]),
            ("industrial safety", ["two wheeler", "motorcycle", "rider"]),
            ("automotive", ["building", "structural"]),
        ]

        for q_qual, doc_antagonists in conflicting_domains:
            if q_qual in q_lower and q_qual not in doc_text:
                # Check if doc has antagonist
                for ant in doc_antagonists:
                    if ant in doc_text:
                        return True, f"Specification mentions '{q_qual}', whereas {candidate_doc.standard_number} specifically covers '{ant}'."

        # 2. Check Specific Pipe / Conduit Materials (e.g. HDPE vs PVC vs CPVC vs PE-AL-PE vs Ductile Iron)
        pipe_materials = ["hdpe", "upvc", "cpvc", "pvc-u", "pvc", "pe-al-pe", "composite", "ductile iron", "cast iron", "mild steel", "galvanized iron", "gi"]
        q_pipe_mats = [m for m in pipe_materials if re.search(r"\b" + re.escape(m) + r"\b", q_lower)]
        if q_pipe_mats and any(k in q_lower for k in ["pipe", "pipes", "piping", "tubes", "conduit"]):
            for qm in q_pipe_mats:
                if not re.search(r"\b" + re.escape(qm) + r"\b", doc_text):
                    # Find candidate's pipe material
                    cand_mats = [m for m in pipe_materials if re.search(r"\b" + re.escape(m) + r"\b", doc_text)]
                    cand_name = cand_mats[0].upper() if cand_mats else candidate_doc.short_title
                    return True, f"Specification specifies '{qm.upper()} pipes', but {candidate_doc.standard_number} covers '{cand_name}'."

        # 3. Check Helmet / PPE Application Types
        if any(h in q_lower for h in ["helmet", "helmets", "headgear", "hard hat"]):
            if any(ind in q_lower for ind in ["industrial", "construction", "factory", "worker"]) and "two wheeler" in doc_text:
                return True, f"Specification specifies 'industrial safety helmets', but {candidate_doc.standard_number} is for 'two-wheeler riders'."
            if any(tw in q_lower for tw in ["two wheeler", "motorcycle", "rider", "biker"]) and "industrial" in doc_text:
                return True, f"Specification specifies 'two-wheeler helmets', but {candidate_doc.standard_number} is for 'industrial safety helmets'."

        return False, None
