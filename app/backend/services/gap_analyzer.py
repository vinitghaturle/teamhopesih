"""Tender Guard — Specification Gap Check Service.

Performs data-driven requirement and testing parameter coverage analysis against
recommended standards. Reuses negation detection from repo 3 technical_patterns.py.

IMPORTANT: This evaluates topic mentions only and is strictly labeled:
"Topic coverage, not a compliance score".
"""

import re
from typing import List, Dict, Any, Optional
from services.technical_patterns import is_negated


def analyze_standard_gaps(
    tender_text: str,
    standard_number: str,
    parameter_names: List[str],
) -> Dict[str, Any]:
    """
    Compares a standard's key parameter names against the tender text.
    
    Returns:
      {
        "standard_number": "IS 1786",
        "total_topics": 4,
        "mentioned_count": 3,
        "missing_count": 1,
        "negated_count": 0,
        "coverage_percentage": 75.0,
        "coverage_label": "topic coverage, not a compliance score",
        "parameter_checks": [
            {
                "parameter_name": "0.2% Proof Stress / Yield Stress",
                "status": "mentioned" | "not_mentioned" | "negated_needs_review",
                "evidence_snippet": "...",
                "action": "...",
            }, ...
        ]
      }
    """
    if not parameter_names:
        return {
            "standard_number": standard_number,
            "total_topics": 0,
            "mentioned_count": 0,
            "missing_count": 0,
            "negated_count": 0,
            "coverage_percentage": 100.0,
            "coverage_label": "topic coverage, not a compliance score",
            "parameter_checks": [],
        }

    tender_lower = tender_text.lower()
    checks = []
    mentioned_count = 0
    negated_count = 0
    missing_count = 0

    for param in parameter_names:
        # Extract core keywords from parameter name
        cleaned_param = re.sub(r"\(.*?\)", "", param).strip()
        words = [w for w in re.split(r"[\s/,]+", cleaned_param) if len(w) > 3]

        found_match = False
        match_start = -1
        match_end = -1
        matched_text = ""

        # Check full cleaned parameter match or key word combinations
        if cleaned_param.lower() in tender_lower:
            found_match = True
            match_start = tender_lower.find(cleaned_param.lower())
            match_end = match_start + len(cleaned_param)
            matched_text = tender_text[match_start:match_end]
        else:
            # Check individual technical terms (e.g. "tensile strength", "proof stress", "elongation", "hydrostatic")
            for w in words:
                pattern = re.compile(r"\b" + re.escape(w) + r"\b", re.IGNORECASE)
                m = pattern.search(tender_text)
                if m:
                    found_match = True
                    match_start = m.start()
                    match_end = m.end()
                    matched_text = m.group(0)
                    break

        if found_match:
            # Check for negation (e.g. "not required", "excluding", "without")
            negated = is_negated(tender_text, match_start, match_end)
            
            # Extract local sentence context snippet
            snippet_start = max(0, match_start - 40)
            snippet_end = min(len(tender_text), match_end + 60)
            context = tender_text[snippet_start:snippet_end].replace("\n", " ").strip()

            if negated:
                negated_count += 1
                status = "negated_needs_review"
                action = "Parameter found with negative or exclusionary phrasing. Officer must clarify tender intent."
            else:
                mentioned_count += 1
                status = "mentioned"
                action = "Topic mentioned in tender specification; verify specific thresholds against standard limits."

            checks.append({
                "parameter_name": param,
                "status": status,
                "evidence_snippet": f"...{context}...",
                "action": action,
            })
        else:
            missing_count += 1
            checks.append({
                "parameter_name": param,
                "status": "not_mentioned",
                "evidence_snippet": None,
                "action": f"Recommended testing parameter '{param}' is not mentioned in tender. Consider adding to specification.",
            })

    total = len(parameter_names)

    return {
        "standard_number": standard_number,
        "total_count": total,
        "matched_count": mentioned_count,
        "missing_count": missing_count,
        "negated_count": negated_count,
        "coverage_ratio": f"{mentioned_count}/{total}",
        "coverage_label": "topic coverage, not a compliance score",
        "parameter_checks": checks,
    }


def analyze_tender_gaps(
    tender_text: str,
    recommended_standards: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Performs gap analysis across all recommended standards in the Bill of Standards.
    """
    gap_results = []
    for std in recommended_standards:
        std_num = std.get("standard_number", "")
        params = std.get("parameter_names") or []
        if not params and "key_testing_parameters" in std:
            params = std.get("key_testing_parameters") or []
            
        gap_res = analyze_standard_gaps(tender_text, std_num, params)
        gap_results.append(gap_res)

    return gap_results
