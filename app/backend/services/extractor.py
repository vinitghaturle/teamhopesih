"""Requirement Extractor — deterministic extraction of clauses and technical specs.
"""

import re
from typing import List, Dict, Any
from services import technical_patterns as patterns


class TenderRequirement:
    def __init__(self, index: int, text: str, category: str = "General Specification"):
        self.index = index
        self.text = text
        self.category = category
        self.entities: Dict[str, List[str]] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": f"REQ-{self.index:03d}",
            "text": self.text,
            "category": self.category,
            "entities": self.entities,
        }


class RequirementExtractor:
    """Extracts discrete technical requirements and specifications from tender text."""

    def __init__(self):
        # Header/metadata lines to skip when segmenting requirements
        self.skip_patterns = [
            re.compile(r"^(?:tender\s+notice|tender\s+reference|scope\s+of\s+work|table\s+of\s+contents|earnest\s+money|estimated\s+cost|completion\s+period)\b", re.IGNORECASE),
            re.compile(r"^(?:section|annexure|schedule|part|chapter)\s+[0-9IVXLCDM]+\s*$", re.IGNORECASE),
        ]

    def extract_clauses(self, raw_text: str) -> List[TenderRequirement]:
        """Splits raw tender text into discrete requirement clauses."""
        lines = [l.strip() for l in raw_text.splitlines() if l.strip()]
        
        clauses: List[str] = []
        current_category = "General Specification"
        current_buffer: List[str] = []

        for line in lines:
            # Check if this line is a category/section header (e.g., "2.1 STRUCTURAL REQUIREMENTS", "3. ELECTRICAL INSTALLATIONS")
            header_match = re.match(r"^(?:\d+\.|\d+\.\d+\s+)?([A-Z\s]{4,40})(?::|$)", line)
            if header_match and len(line) < 60 and not line.endswith("."):
                candidate_category = header_match.group(1).strip().title()
                if any(k in candidate_category.lower() for k in ["structural", "electrical", "civil", "plumbing", "pipe", "safety", "fire", "quality", "water", "lighting", "mechanical", "cables"]):
                    current_category = candidate_category
                    if current_buffer:
                        clauses.append((" ".join(current_buffer), current_category))
                        current_buffer = []
                    continue

            # Check if line is a bullet or numbered item
            bullet_match = re.match(r"^(?:[-*•–—]|(?:\d+\.|\d+\.\d+|\([a-z0-9]+\))\s+)(.*)$", line)
            if bullet_match:
                if current_buffer:
                    clauses.append((" ".join(current_buffer), current_category))
                    current_buffer = []
                content = bullet_match.group(1).strip()
                if content:
                    current_buffer.append(content)
            else:
                # If paragraph sentence
                if current_buffer and (line.startswith("The ") or line.startswith("All ") or line.startswith("Supply ") or line.startswith("Procurement ")):
                    clauses.append((" ".join(current_buffer), current_category))
                    current_buffer = [line]
                else:
                    current_buffer.append(line)

        if current_buffer:
            clauses.append((" ".join(current_buffer), current_category))

        # Filter and normalize clauses
        requirements: List[TenderRequirement] = []
        req_idx = 1

        for clause_text, category in clauses:
            cleaned = clause_text.strip()
            # Clean leading numbers/bullets
            cleaned = re.sub(r"^(?:[-*•–—]|(?:\d+\.|\d+\.\d+|\([a-z0-9]+\))\s+)", "", cleaned).strip()

            if len(cleaned) < 15:
                continue

            # Skip non-technical boilerplate
            if any(p.search(cleaned) for p in self.skip_patterns):
                continue

            req = TenderRequirement(index=req_idx, text=cleaned, category=category)
            
            # Extract key technical entities
            req.entities = self._extract_entities(cleaned)
            requirements.append(req)
            req_idx += 1

        # If document had no bullets or headers, treat entire text or paragraphs as requirements
        if not requirements and raw_text.strip():
            paragraphs = [p.strip() for p in raw_text.split("\n\n") if len(p.strip()) > 20]
            if not paragraphs:
                paragraphs = [raw_text.strip()]
            for idx, p in enumerate(paragraphs, start=1):
                req = TenderRequirement(index=idx, text=p, category="General Specification")
                req.entities = self._extract_entities(p)
                requirements.append(req)

        return requirements

    def _extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extracts technical parameters and terms."""
        entities: Dict[str, List[str]] = {}

        # Materials
        materials = patterns.MATERIAL.findall(text)
        if materials:
            entities["materials"] = list(set(m.upper() for m in materials))

        # Voltages
        voltages = [m.group(0) for m in patterns.VOLTAGE.finditer(text)]
        if voltages:
            entities["voltages"] = voltages

        # Pressures
        pressures = [m.group(0) for m in patterns.PRESSURE.finditer(text)]
        if pressures:
            entities["pressures"] = pressures

        # Dimensions
        dimensions = [m.group(0) for m in patterns.DIMENSION.finditer(text)]
        if dimensions:
            entities["dimensions"] = dimensions

        # Standards cited
        stds = patterns.IS_CITATION_PATTERN.findall(text)
        if stds:
            formatted = []
            for num, part, yr in stds:
                s = f"IS {num}"
                if part:
                    s += f" (Part {part})"
                if yr:
                    s += f":{yr}"
                formatted.append(s)
            entities["cited_standards"] = formatted

        return entities
