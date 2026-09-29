"""Unit & Integration tests for Phase 2 Hybrid Retrieval & Grounding."""

import pytest
from services.retrieval.pipeline import RetrievalPipeline
from services.retrieval.relevance_floor import evaluate_relevance_floor, RELEVANCE_FLOOR
from services.retrieval.refusal import get_refusal
from services.multilingual import detect_language, translate_procurement_query


@pytest.fixture(scope="module")
def retrieval_pipeline():
    return RetrievalPipeline(use_neural=True)


def test_single_standard_retrieval(retrieval_pipeline):
    """Test precise single standard retrieval for high-demand procurement categories."""
    res = retrieval_pipeline.search("Thermo-Mechanically Treated TMT steel reinforcement bars Fe 500D", top_k=3)
    assert res["status"] == "MATCH_FOUND"
    assert len(res["results"]) > 0
    top_std = res["results"][0]["standard_number"]
    assert "IS 1786" in top_std


def test_multilingual_hindi_retrieval(retrieval_pipeline):
    """Test Hindi procurement query detection, translation, and retrieval."""
    hindi_query = "पेयजल आपूर्ति के लिए उच्च घनत्व पॉलीथीन पाइप की आपूर्ति"
    t_query, lang = translate_procurement_query(hindi_query)
    assert lang == "hi"
    assert "High Density Polyethylene" in t_query or "drinking water" in t_query

    res = retrieval_pipeline.search(hindi_query, top_k=3)
    assert res["status"] == "MATCH_FOUND"
    top_std = res["results"][0]["standard_number"]
    assert "IS 15450" in top_std or "IS 4984" in top_std or "IS 4985" in top_std


def test_multilingual_marathi_retrieval(retrieval_pipeline):
    """Test Marathi procurement query detection and retrieval."""
    marathi_query = "शासकीय कार्यालयासाठी 20 लिटर पॅक केलेले पिण्याचे पाणी पुरवठा"
    res = retrieval_pipeline.search(marathi_query, top_k=3)
    assert res["status"] == "MATCH_FOUND"
    top_std = res["results"][0]["standard_number"]
    assert "IS 14543" in top_std or "IS 15410" in top_std


def test_zero_hallucination_refusal(retrieval_pipeline):
    """Test that out-of-corpus queries strictly return NO_CONFIDENT_MATCH."""
    out_queries = [
        "Hiring of certified scrum masters and agile coaches for enterprise cloud migration",
        "Procurement of office pantry tea bags, roasted coffee beans, and sugar cubes",
        "Design and fabrication of NASA deep space satellite ion propulsion thruster nozzles",
    ]
    for q in out_queries:
        res = retrieval_pipeline.search(q, top_k=3)
        assert res["status"] == "NO_CONFIDENT_MATCH"
        assert res["results"] == []
        assert "refusal" in res
        assert res["refusal"]["status"] == "NO_CONFIDENT_MATCH"


def test_explicit_citation_exemption(retrieval_pipeline):
    """Test that explicit IS citations are recognized and exempted from semantic floor."""
    res = retrieval_pipeline.search("Tender conforming to IS 4151 for safety helmets", top_k=3)
    assert res["status"] == "MATCH_FOUND"
    assert res["verdict"] == "exempt_identifier_match"
    top_std = res["results"][0]["standard_number"]
    assert "IS 4151" in top_std
