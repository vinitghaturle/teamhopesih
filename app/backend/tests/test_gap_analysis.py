"""Tender Guard — Spec-Gap Analysis Unit Tests.

Validates:
  - Topic coverage calculation across parameter names
  - Distinction between mentioned, missing, and negated_needs_review
  - Negation detection logic
  - Mandatory disclaimer labeling
"""

import pytest
from services.gap_analyzer import analyze_standard_gaps, analyze_tender_gaps


def test_gap_analysis_positive_mention():
    tender_text = (
        "High strength deformed steel bars for concrete reinforcement. "
        "The steel shall have high tensile strength, elongation of 14.5%, and 0.2% proof stress."
    )
    params = [
        "0.2% Proof Stress / Yield Stress",
        "Tensile Strength",
        "Elongation at gauge length",
        "Total Elongation at maximum force",
        "Bend and Re-bend test",
    ]
    res = analyze_standard_gaps(tender_text, "IS 1786", params)

    assert res["standard_number"] == "IS 1786"
    assert res["total_count"] == 5
    assert res["matched_count"] >= 3
    assert res["coverage_ratio"] == f"{res['matched_count']}/5"
    assert res["coverage_label"] == "topic coverage, not a compliance score"
    # Ensure evidence snippet is populated for matched parameters
    matched_checks = [c for c in res["parameter_checks"] if c["status"] == "mentioned"]
    assert len(matched_checks) >= 3
    for c in matched_checks:
        assert c["evidence_snippet"] is not None


def test_gap_analysis_negation_detection():
    tender_text = (
        "Prestressed concrete components. Compressive strength must be tested. "
        "Drying shrinkage test is not required for this procurement."
    )
    params = [
        "Compressive Strength at 28 days",
        "Drying shrinkage test",
    ]
    res = analyze_standard_gaps(tender_text, "IS 12269", params)

    checks_by_param = {c["parameter_name"]: c for c in res["parameter_checks"]}

    assert checks_by_param["Compressive Strength at 28 days"]["status"] == "mentioned"
    assert checks_by_param["Drying shrinkage test"]["status"] == "negated_needs_review"
    assert res["negated_count"] == 1


def test_gap_analysis_missing_parameters_negative():
    # Negative test: tender specifies generic supply without mentioning any testing parameters
    tender_text = "Procurement of standard construction materials for warehouse renovation."
    params = [
        "0.2% Proof Stress / Yield Stress",
        "Tensile Strength",
        "Bend and Re-bend test",
    ]
    res = analyze_standard_gaps(tender_text, "IS 1786", params)

    assert res["total_count"] == 3
    assert res["matched_count"] == 0
    assert res["missing_count"] == 3
    assert res["coverage_ratio"] == "0/3"
    for check in res["parameter_checks"]:
        assert check["status"] == "not_mentioned"
        assert check["evidence_snippet"] is None
