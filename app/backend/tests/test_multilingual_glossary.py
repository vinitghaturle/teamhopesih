"""Tests for Multilingual Glossary (>=150 terms) and Provider Fallback Chain."""

import pytest
from services.multilingual import MultilingualService, PROCUREMENT_GLOSSARY, detect_language, translate_procurement_query


def test_procurement_glossary_term_count():
    assert len(PROCUREMENT_GLOSSARY) >= 150, f"Expected >= 150 terms, found {len(PROCUREMENT_GLOSSARY)}"


def test_multilingual_language_detection():
    service = MultilingualService()
    
    # English
    assert service.detect_language("Supply of TMT steel bars Fe 500D") == "en"
    
    # Hindi
    assert service.detect_language("सरकारी भवन के निर्माण के लिए 43 ग्रेड साधारण पोर्टलैंड सीमेंट") == "hi"
    
    # Marathi
    assert service.detect_language("शासकीय कार्यालयासाठी पॅक केलेले पिण्याचे पाणी पुरवठा") == "mr"


def test_multilingual_translation_chain():
    service = MultilingualService()
    
    # Hindi query translation
    hi_query = "सरकारी भवन के निर्माण के लिए साधारण पोर्टलैंड सीमेंट 43 ग्रेड"
    translated_hi = service.translate_query(hi_query)
    assert "Ordinary Portland Cement" in translated_hi or "cement" in translated_hi.lower()
    
    # Marathi query translation
    mr_query = "शासकीय कार्यालयासाठी पॅक केलेले पिण्याचे पाणी जार पुरवठा"
    translated_mr = service.translate_query(mr_query)
    assert "drinking water" in translated_mr.lower() or "packaged" in translated_mr.lower()


def test_provider_status_structure():
    service = MultilingualService()
    status = service.get_provider_status()
    assert "mode" in status
    assert "glossary_terms_count" in status
    assert status["glossary_terms_count"] >= 150
    assert "hi" in status["supported_languages"]
    assert "mr" in status["supported_languages"]
