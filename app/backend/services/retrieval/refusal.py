"""Fixed, explicit refusal responses (Zero Hallucination).
"""

from typing import Dict, Any

REFUSAL_RESPONSES = {
    "en": {
        "out_of_scope": {
            "answer": "This tender specification is outside what Tender Guard covers. Tender Guard matches technical requirements to public Bureau of Indian Standards (BIS) product specifications, certification schemes (Scheme-I/CRS), and testing codes. It does not answer general questions or non-standard procurement queries.",
            "limitation": "Query is outside the scope of Indian Standards, product compliance, and BIS certification.",
            "status": "NO_CONFIDENT_MATCH",
        },
        "insufficient_evidence": {
            "answer": "No confident match found in the indexed BIS corpus. Tender Guard only recommends from the authoritative indexed set of Indian Standards (titles, scopes, mandatory QCOs, testing parameters). Any retrieved items are below the relevance confidence threshold and are not confirmed.",
            "limitation": "No indexed BIS standard supports a grounded answer to this requirement.",
            "status": "NO_CONFIDENT_MATCH",
        },
        "not_in_database": {
            "answer": "The referenced standard was identified from the tender, but its detailed specifications are not currently indexed in this 100-standard prototype corpus. Please consult www.bis.gov.in for the official publication.",
            "limitation": "Identified standard is not in the indexed prototype corpus.",
            "status": "NOT_IN_CORPUS",
        },
    },
    "hi": {
        "out_of_scope": {
            "answer": "यह निविदा विनिर्देश Tender Guard के दायरे से बाहर है। Tender Guard तकनीकी आवश्यकताओं को सार्वजनिक भारतीय मानक (BIS) विनिर्देशों से जोड़ता है।",
            "limitation": "प्रश्न भारतीय मानकों और BIS प्रमाणन के दायरे से बाहर है।",
            "status": "NO_CONFIDENT_MATCH",
        },
        "insufficient_evidence": {
            "answer": "अनुक्रमित BIS सामग्री में कोई पुष्ट मानक नहीं मिला। Tender Guard केवल अनुक्रमित भारतीय मानकों से सिफारिश करता है।",
            "limitation": "इस आवश्यकता का समर्थन करने वाला कोई अनुक्रमित BIS मानक नहीं है।",
            "status": "NO_CONFIDENT_MATCH",
        },
        "not_in_database": {
            "answer": "मानक पहचाना गया लेकिन यह प्रोटोटाइप डेटाबेस में अनुक्रमित नहीं है।",
            "limitation": "पहचाना गया मानक डेटाबेस में उपलब्ध नहीं है।",
            "status": "NOT_IN_CORPUS",
        },
    },
}


def get_refusal(reason: str, language: str = "en") -> Dict[str, str]:
    """Get fixed refusal text for a given reason and language."""
    lang_dict = REFUSAL_RESPONSES.get(language, REFUSAL_RESPONSES["en"])
    return lang_dict.get(reason, lang_dict["insufficient_evidence"])
